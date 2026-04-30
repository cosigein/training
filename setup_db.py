import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

from app import create_app
from app.extensions import db
from datetime import datetime
from app.models.auth import User, Organization, UserRole
from app.models.vehicle import Vehicle
from app.models.training import RfidCard
# Import all models to ensure they are registered
from app.models import session, vehicle, auth, event, training

def create_database_if_not_exists():
    print("🔍 Verificando existencia de la base de datos...")
    # Obtenemos la URL de la DB de la env o usamos el default
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/doback_dev")
    
    # Parseamos la URL para conectar a 'postgres' y crear la db objetivo
    # Formato esperado: postgresql://user:pass@host:port/dbname
    try:
        base_url, db_name = db_url.rsplit('/', 1)
        root_url = f"{base_url}/postgres"
        
        conn = psycopg2.connect(root_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Verificar si la base existe
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"🏗️  La base de datos '{db_name}' no existe. Creándola...")
            cur.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Base de datos '{db_name}' creada.")
        else:
            print(f"ℹ️  La base de datos '{db_name}' ya existe.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Nota: No se pudo verificar/crear la DB automáticamente: {e}")
        print("Asegúrate de que los credenciales en DATABASE_URL sean correctos y el usuario tenga permisos de CREATEDB.")

def get_or_create_org(name, **defaults):
    org = Organization.query.filter_by(name=name).first()
    if org:
        print(f"ℹ️  Organización '{name}' ya existe.")
        return org
    org = Organization(name=name, **defaults)
    db.session.add(org)
    db.session.flush()
    print(f"✅ Organización '{name}' creada.")
    return org


def get_or_create_rfid_card(uid, student, org_id):
    card = RfidCard.query.filter_by(uid=uid, organizationId=org_id, active=True).first()
    if card:
        print(f"ℹ️  Tarjeta RFID '{uid}' ya existe.")
        return card
    card = RfidCard(
        uid=uid,
        organizationId=org_id,
        assignedTo=student.id if student else None,
        assignedAt=datetime.utcnow() if student else None,
        active=True,
    )
    db.session.add(card)
    db.session.flush()
    label = student.email if student else "(libre)"
    print(f"✅ Tarjeta RFID '{uid}' creada → {label}.")
    return card


def get_or_create_user(email, name, password, role, org_id):
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"ℹ️  Usuario {email} ya existe.")
        return user
    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password, method="pbkdf2:sha256"),
        role=role,
        organizationId=org_id,
        status="ACTIVE"
    )
    db.session.add(user)
    db.session.flush()
    print(f"✅ Usuario {email} creado (clave: {password}).")
    return user


def setup_database():
    create_database_if_not_exists()

    app = create_app()
    with app.app_context():
        print("🛠️  Creando todas las tablas...")
        db.create_all()
        print("✅ Tablas creadas con éxito.")

        print("🌱 Sembrando datos iniciales (idempotente)...")
        org = get_or_create_org("CMadrid", apiKey="demo-key", formacionHabilitada=False)

        get_or_create_user("super@cmadrid.com",    "Super Admin CMadrid", "super123",   UserRole.SUPER_ADMIN, org.id)
        get_or_create_user("admin@cmadrid.com",    "Admin CMadrid",       "admin123",   UserRole.ADMIN,       org.id)
        get_or_create_user("manager@cmadrid.com",  "Manager CMadrid",     "manager123", UserRole.MANAGER,     org.id)
        alumno1 = get_or_create_user("alumno1@cmadrid.com", "Alumno Uno", "alumno123",  UserRole.STUDENT, org.id)
        alumno2 = get_or_create_user("alumno2@cmadrid.com", "Alumno Dos", "alumno123",  UserRole.STUDENT, org.id)

        # Tarjetas RFID de prueba (UIDs estilo Mifare 4-bytes)
        get_or_create_rfid_card("04:A1:B2:C3", alumno1, org.id)
        get_or_create_rfid_card("04:D4:E5:F6", alumno2, org.id)

        db.session.commit()
        print("🚀 Seed listo.")

if __name__ == "__main__":
    setup_database()
