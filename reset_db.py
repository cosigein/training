"""reset_db.py — Borra la BD, la recrea desde cero y repobla con datos base.

Pasos:
  1. DROP DATABASE + CREATE DATABASE (conexión a 'postgres')
  2. CREATE EXTENSION pgcrypto, postgis (necesarias para gen_random_uuid() y geofences)
  3. db.create_all()  (crea tablas directamente desde los modelos SQLAlchemy)
  4. flask db stamp head  (marca alembic_version al head para que migraciones futuras funcionen)
  5. setup_db seed     (org CMadrid + usuarios base)

Uso:
    python reset_db.py
"""
import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

# ─── Helpers de conexión ─────────────────────────────────────────────────────

def _parse_db_url(url: str):
    """Devuelve (base_url_sin_dbname, dbname)."""
    # postgresql://user:pass@host[:port]/dbname
    base, dbname = url.rsplit("/", 1)
    return base, dbname


def _connect_postgres(base_url: str):
    """Conecta al DB 'postgres' del mismo server."""
    conn = psycopg2.connect(f"{base_url}/postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


# ─── Paso 1: drop + create ───────────────────────────────────────────────────

def drop_and_create(db_url: str) -> str:
    base_url, dbname = _parse_db_url(db_url)

    print(f"\n[1/4] Conectando a 'postgres' en {base_url}…")
    conn = _connect_postgres(base_url)
    cur = conn.cursor()

    print(f"      Terminando conexiones activas a '{dbname}'…")
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid();",
        (dbname,),
    )

    print(f"      DROP DATABASE IF EXISTS {dbname}…")
    cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')

    print(f"      CREATE DATABASE {dbname}…")
    cur.execute(f'CREATE DATABASE "{dbname}"')

    cur.close()
    conn.close()
    print(f"      Base de datos '{dbname}' recreada.")
    return dbname


# ─── Paso 2: extensiones ─────────────────────────────────────────────────────

def create_extensions(db_url: str):
    print("\n[2/4] Creando extensiones (pgcrypto, postgis)…")
    base_url, dbname = _parse_db_url(db_url)
    conn = psycopg2.connect(f"{base_url}/{dbname}")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    for ext in ("pgcrypto", "postgis"):
        cur.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
        print(f"      ✓ {ext}")
    cur.close()
    conn.close()


# ─── Paso 3: crear tablas desde modelos ──────────────────────────────────────

def _find_head_revision() -> str:
    """Devuelve el revision ID del head actual sin usar Alembic.

    Busca el archivo .py en migrations/versions/ cuyo `revision`
    no aparece como `down_revision` de ningún otro archivo.
    """
    import re
    versions_dir = os.path.join(os.path.dirname(__file__), "migrations", "versions")
    revisions: dict[str, str] = {}   # revision_id -> filename
    down_revisions: set[str] = set()

    for fname in os.listdir(versions_dir):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        path = os.path.join(versions_dir, fname)
        content = open(path).read()
        rev_m = re.search(r"^revision\s*=\s*['\"]([a-f0-9]+)['\"]", content, re.MULTILINE)
        down_m = re.search(r"^down_revision\s*=\s*(.+)$", content, re.MULTILINE)
        if not rev_m:
            continue
        rev_id = rev_m.group(1)
        revisions[rev_id] = fname
        if down_m:
            raw = down_m.group(1).strip()
            # puede ser string, None, o tuple
            found = re.findall(r"['\"]([a-f0-9]+)['\"]", raw)
            down_revisions.update(found)

    heads = [rid for rid in revisions if rid not in down_revisions]
    if len(heads) == 1:
        return heads[0]
    if len(heads) > 1:
        # Múltiples heads — tomar el último por nombre de archivo (timestamp)
        return sorted(heads, key=lambda r: revisions[r])[-1]
    raise RuntimeError("No se encontró ningún head en migrations/versions/")


def _stamp_version_direct(db_url: str, revision: str):
    """Escribe alembic_version directamente con psycopg2, sin cargar Alembic."""
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS alembic_version "
        "(version_num VARCHAR(32) NOT NULL, "
        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
    )
    cur.execute("DELETE FROM alembic_version")
    cur.execute("INSERT INTO alembic_version VALUES (%s)", (revision,))
    cur.close()
    conn.close()


def create_tables(db_url: str):
    """Crea todas las tablas directamente desde los modelos SQLAlchemy.

    Más robusto que `flask db upgrade` para un reset: no depende del estado
    de la cadena de migraciones. Escribe alembic_version directo a la BD
    para que `flask db migrate` funcione correctamente en el futuro.
    """
    print("\n[3/4] Creando tablas desde modelos SQLAlchemy (db.create_all)…")
    from app import create_app
    from app.extensions import db

    # Importar todos los modelos para que SQLAlchemy los registre en metadata
    import app.models.auth          # noqa: F401
    import app.models.vehicle       # noqa: F401
    import app.models.session       # noqa: F401
    import app.models.training      # noqa: F401

    app = create_app()
    with app.app_context():
        db.create_all()
    print("      Tablas creadas.")

    head = _find_head_revision()
    _stamp_version_direct(db_url, head)
    print(f"      ✓ alembic_version = {head}")


# ─── Paso 4-5: seeds ─────────────────────────────────────────────────────────

def run_setup_seed():
    print("\n[4/4] Seed base (org + usuarios)…")
    from setup_db import setup_database
    setup_database()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Reset completo de la base de datos.")
    args = parser.parse_args()

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost/doback_dev"
    )

    print("=" * 60)
    print("  RESET COMPLETO DE BASE DE DATOS")
    print(f"  Target: {db_url}")
    print("  ESTO BORRA TODOS LOS DATOS EXISTENTES.")
    print("=" * 60)

    confirm = input("\n¿Confirmar reset? [s/N] ").strip().lower()
    if confirm not in ("s", "si", "sí", "y", "yes"):
        print("Cancelado.")
        sys.exit(0)

    drop_and_create(db_url)
    create_extensions(db_url)
    create_tables(db_url)
    run_setup_seed()

    print("\n" + "=" * 60)
    print("  Reset completo. BD lista.")
    print("=" * 60)


if __name__ == "__main__":
    main()
