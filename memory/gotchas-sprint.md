# Gotchas — Training sprint

> Cosas que costaron tiempo y no son obvias del código. Si descubrís una nueva, **agregala acá** y enlazala desde `MEMORY.md`.

Última actualización: 2026-04-29.

---

## G-001 — `FLASK_CONFIG` (no `FLASK_ENV`) elige el config

`app/__init__.py:17` hace:
```python
config_name = os.environ.get("FLASK_CONFIG", "default")
```

→ Si solo seteás `FLASK_ENV=production`, **NO se activa** `ProductionConfig`. Hay que setear `FLASK_CONFIG=production`. `FLASK_ENV` y `FLASK_DEBUG` solo afectan al CLI de Flask y al reloader/debugger del werkzeug.

## G-002 — `db.create_all()` NO actualiza enums existentes

Si agregás un valor a un Enum (ej. `UserRole.STUDENT`), Postgres NO refleja el cambio. Tirás:
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum userrole: "STUDENT"
```

Soluciones:
- Drop+create de la BD (Opción A de `MIGRATION-NOTES.md`) — limpio si no hay datos importantes.
- `ALTER TYPE userrole ADD VALUE 'STUDENT'` manual (Opción B).
- Cuando se active Alembic, generar migración explícita.

## G-003 — `setup_db.py` usa `db.create_all()`, NO Alembic

El proyecto tiene `migrations/` con `env.py` y `alembic.ini`, pero NO `migrations/versions/`. **Hoy nadie usa Alembic**. Schema lo gestiona `db.create_all()` desde `setup_db.py`.

→ Cuando alguien decida activar Alembic en serio, va a tener que:
1. `flask db init` (regenerar) o stamp manual.
2. Generar la migración inicial con el estado actual.
3. Coordinar con el equipo el corte.

## G-004 — `:5000` ocupado por AirPlay Receiver en macOS

Mac tiene `ControlCenter` listening en `*:5000` (AirPlay Receiver). Pero la app Flask bindea a `127.0.0.1:5000` específicamente — así que **no hay colisión real**, solo confusión visual al hacer `lsof -i :5000`.

Si igual molesta: System Settings → General → AirDrop & Handoff → AirPlay Receiver = OFF.

## G-005 — User `training` en VPS Postgres no tenía `CREATEDB`

Drop+create de la BD del VPS fallaba con "permission denied to create database". Solución (29/04, ya aplicada):
```bash
sudo -u postgres psql -c "ALTER ROLE training CREATEDB;"
```

## G-006 — Redis del VPS requiere password (compartido con DobackSoft)

`dobacksoft-redis` (único redis en `:6379`) tiene `--requirepass`. Training NO conoce el password (es secret de DobackSoft). Resultado:
- `flask_limiter` cae a fallback de memoria
- `flask_caching` cae a fallback
- `flask_socketio.message_queue` no usa cola (sin multi-worker)
- **App funciona, NO tira errores en log**

→ Cuando arranque tarea 9 (cron daily-ranking), levantar `training-redis` dedicado en `:6381`.

## G-007 — App Flask + SocketIO + reloader spawnea 2 procesos

Cuando matás `python wsgi.py` con `kill <PID>`, el padre respawnea al child porque el reloader del werkzeug está activo. Solución:
```bash
pkill -TERM -u <user> -f "python wsgi.py"
```

(En production con systemd ya no aplica — Restart=always cubre esto).

## G-008 — `host="0.0.0.0"` en `wsgi.py` NO aporta detrás de nginx

Alguien del equipo dejó `host="0.0.0.0"` en `wsgi.py` sin commit (visible en `git diff` del 29/04). El cambio se revirtió porque:
- nginx hace proxy a `127.0.0.1:5000` → bindear a 0.0.0.0 no aporta acceso adicional.
- Con `FLASK_DEBUG=1` activo + 0.0.0.0 + firewall mal configurado = riesgo (debugger PIN expuesto).

Si Joel/QA necesita acceso al `:5000` directo desde otra máquina, **mejor port-forward SSH**:
```bash
ssh -L 5000:127.0.0.1:5000 dobacksoft-vps
```

## G-009 — `setup_db.py` referencia BD `doback_dev` como fallback

Línea 22:
```python
db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/doback_dev")
```

Si tu `.env` no tiene `DATABASE_URL`, intenta crear `doback_dev` con user `postgres`. Esto es **legacy del proyecto viejo** y va a fallar en el setup actual. Asegurate de tener `DATABASE_URL` en tu `.env`.

## G-010 — Branch divergente sin checkout explícito

El 29/04, sin que nadie hiciera `git checkout`, el local de Antonio terminó parado en `docs/joel-onboarding-complete` (no en `main`). Causó un `git pull --ff-only` fallido porque la rama actual diverge de `origin/main`.

→ Antes de cualquier `git pull`, **siempre verificá** con `git branch --show-current` o `git status -sb`.

## G-011 — VPS comparte cluster Postgres con otro proyecto

En el VPS hay:
- Postgres del **HOST** (`127.0.0.1:5432`) — usado por Training (`training`) y posiblemente otros (ver `pg_database`).
- Container `dobacksoft-db` (`127.0.0.1:5433`) — usado por DobackSoft V3.

→ Cualquier `DROP DATABASE` desde el VPS debe verificar **a qué cluster** está apuntando antes de ejecutar. Training usa `5432`, DobackSoft `5433`.

## G-012 — El `JWT_SECRET` se cae a `SECRET_KEY` si no está

`app/config.py:12`:
```python
JWT_SECRET_KEY = os.environ.get("JWT_SECRET", SECRET_KEY)
```

Si `JWT_SECRET` no está en `.env`, JWT firma con `SECRET_KEY`. **Funciona**, pero:
- Cualquiera con SECRET_KEY puede forjar tokens.
- Rotar SECRET_KEY invalida tokens y sesiones a la vez.

→ En production declarar JWT_SECRET dedicado (en VPS ya está, 29/04).

## G-013 — Eventlet deprecation warnings al arrancar

Aparece este warning **en cada arranque**:
```
EventletDeprecationWarning: Eventlet is deprecated. ... we strongly recommend against using it for new projects.
```

Es esperado. Migrar a asyncio/uvicorn es decisión arquitectónica de días, post-sprint.
