# SETUP LOCAL — Training (sprint CMadrid)

> Onboarding paso-a-paso para levantar el repo en tu máquina, en 10-15 minutos.
> Si algo no funciona, **NO improvises** — preguntá en el chat o leé `STATE-2026-04-29.md`.

Última verificación end-to-end: **2026-04-29** (Antonio).

---

## 0. Pre-requisitos

| Herramienta | Versión | Cómo verifico |
|---|---|---|
| Python | **3.12.x** | `python3 --version` |
| Docker Desktop | cualquier | `docker ps` |
| Git | cualquier | `git --version` |
| Editor | tu preferido | — |

> **Importante:** Python 3.13+ todavía no está validado contra todas las dependencias (eventlet en particular). Si tu sistema tiene 3.14, usá `pyenv` o `brew install python@3.12` y apuntá el venv ahí.

---

## 1. Clonar el repo

```bash
git clone https://github.com/cosigein/training.git
cd training
git checkout main
```

---

## 2. Levantar Postgres + Redis (Docker)

El repo trae un `docker-compose.yml` que levanta:
- Postgres 17 + PostGIS en `localhost:5435`
- Redis 7 en `localhost:6380`

```bash
docker compose up -d
docker ps --filter name=training-
```

Tendrías que ver `training-db` y `training-redis` con status `healthy`.

> **¿Por qué puertos 5435 / 6380?** Para no colisionar con otros proyectos que ya usan 5432 / 6379. Si no tenés conflictos, podés cambiarlos en `docker-compose.yml`, pero entonces actualizá `.env` también.

---

## 3. Crear el venv y deps

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Si ves un `EventletDeprecationWarning` al final, **es esperado** (nota técnica más abajo).

---

## 4. Configurar `.env`

Hay un `.env.example` (vacío hoy — pendiente de poblar). Mientras tanto, copiá esto en `.env`:

```env
FLASK_ENV=development
FLASK_APP=wsgi.py
APP_ENV=development
FLASK_CONFIG=default

DATABASE_URL=postgresql://training:training@localhost:5435/training_dev
DATABASE_URL_TEST=postgresql://training:training@localhost:5435/training_test

REDIS_URL=redis://localhost:6380/0

SECRET_KEY=<generá uno: python -c "import secrets; print(secrets.token_urlsafe(64))">
JWT_SECRET=<generá otro distinto al de arriba>
```

> **NUNCA commitear `.env`.** Está en `.gitignore` por una razón. Si necesitás compartir secrets con el equipo, usá un canal privado.

---

## 5. Crear schema + seed base

```bash
python setup_db.py
```

Esto crea las tablas (con `db.create_all()`, no usa Alembic todavía) y siembra:
- 1 organización: `CMadrid`
- 5 usuarios:
  | Email | Password | Rol |
  |---|---|---|
  | `super@cmadrid.com` | `super123` | `SUPER_ADMIN` |
  | `admin@cmadrid.com` | `admin123` | `ADMIN` |
  | `manager@cmadrid.com` | `manager123` | `MANAGER` |
  | `alumno1@cmadrid.com` | `alumno123` | `STUDENT` |
  | `alumno2@cmadrid.com` | `alumno123` | `STUDENT` |
- 2 tarjetas RFID demo

`setup_db.py` es **idempotente** — podés correrlo varias veces, no duplica nada.

---

## 6. (Opcional) Seed demo para ver el dashboard manager con contenido

```bash
python seed_demo.py
```

Crea 11 alumnos sintéticos, 2 convocatorias OPEN, 11 enrollments y ~49 attempts con scores variados (3.0-9.6) y `dataQuality` HIGH/MEDIUM/LOW. Útil para iterar UI y ranking sin mocks.

`seed_demo.py` también es **idempotente**.

---

## 7. Levantar la app

```bash
python wsgi.py
```

Por default escucha en `127.0.0.1:5000`. Abrí http://127.0.0.1:5000 — te redirige a `/auth/login`.

> **Aviso macOS:** `:5000` puede estar tomado por **AirPlay Receiver** (`ControlCenter`). Es solo en `*:5000`, no afecta a `127.0.0.1:5000`. Si igual te molesta, apagá AirPlay Receiver en Preferencias del Sistema → General → AirDrop & Handoff.

---

## 8. Reset rápido de la BD

Si la BD se ensucia o quedó en estado raro:

```bash
PGPASSWORD=training psql -h localhost -p 5435 -U training -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='training_dev' AND pid <> pg_backend_pid();" \
  -c "DROP DATABASE IF EXISTS training_dev;" \
  -c "CREATE DATABASE training_dev OWNER training;"
python setup_db.py
python seed_demo.py   # opcional
```

> **Backup primero** si tenés algo que conservar:
> ```bash
> PGPASSWORD=training pg_dump -h localhost -p 5435 -U training -d training_dev | gzip > /tmp/training_dev_$(date +%s).sql.gz
> ```

---

## 9. Tests

```bash
pytest                 # tests Python
playwright test        # E2E (owner: Joel)
```

> Hoy `tests/conftest.py` está vacío y no hay tests escritos. Joel arranca los E2E en los próximos días.

---

## 10. Comandos útiles

```bash
# Migraciones (cuando el equipo arranque a usar Alembic — hoy no)
flask db upgrade
flask db migrate -m "add_x_to_y"

# Workers Celery (scaffolding por completar — hoy no funciona)
celery -A celery_worker worker -l info
celery -A celery_worker beat -l info

# Inspeccionar la DB
PGPASSWORD=training psql -h localhost -p 5435 -U training -d training_dev
```

---

## Troubleshooting

### "psycopg2 cannot connect"
- ¿Está Docker arriba? `docker ps`
- ¿Puerto correcto en `.env`? Debe coincidir con el del compose (5435 por default).

### "ModuleNotFoundError"
- ¿Activaste el venv? `source .venv/bin/activate`
- ¿Instalaste deps? `pip install -r requirements.txt -r requirements-dev.txt`

### "invalid input value for enum userrole: 'STUDENT'"
- El enum de Postgres tiene los valores viejos. Reset: ver §8.

### "ya existe Organization 'CMadrid'"
- Es idempotencia funcionando, no es error. Ignorar.

### Login devuelve 400 al hacer POST manual con curl
- Es CSRF protect funcionando. Para tests con curl tenés que tomar el token del form GET primero. Para uso normal por browser no te afecta.

### El frontend se ve "raro" o "diferente entre páginas"
- **No es bug tuyo, es estado actual del proyecto.** Hay dos layouts (top-nav nuevo en `/manager/*`, sidebar viejo en `/sessions/`, `/admin/*`, `/vehicles/*`, `/events/*`). Ver `STATE-2026-04-29.md` §Frontend.

---

## Lectura previa al primer commit

Antes de mandar tu primer PR, leé en orden:
1. [`CLAUDE.md`](../CLAUDE.md) — convenciones del repo, roles, qué tocar y qué no
2. [`CONTRIBUTING.md`](../CONTRIBUTING.md) — flujo de PRs (caveat: stack desactualizado, leer con criterio)
3. [`OWNERS.md`](../OWNERS.md) — quién aprueba qué (mismo caveat)
4. [`RBAC-FIX-PLAN.md`](../RBAC-FIX-PLAN.md) — antes de tocar cualquier `routes.py` o `base.html`
5. [`STATE-2026-04-29.md`](STATE-2026-04-29.md) — snapshot del proyecto al cierre de hoy
