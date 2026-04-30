# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado del repositorio (CRÍTICO — leer primero)

Repo del sprint **Training**: sistema de evaluación competitiva para conductores de camión de bomberos · cliente **CMadrid** (Cuerpo de Bomberos de la Comunidad de Madrid · oposición pública).

- **Sprint:** 14 días naturales · martes 28/04/2026 → lunes 11/05/2026 · **demo en Madrid el 11/05** (Antonio viaja).
- **Equipo (4 personas, Córdoba):**
  - **Antonio Hermoso** (director técnico, Webfleet, integración) — GitHub: `hermoso92`.
  - **Jesús** (backend) — GitHub: `Eldur4023`.
  - **Alejandro** (frontend / templates / UI).
  - **Joel** (simulator + QA + CI) — escribe y consume docs en inglés.
- **Reescritura deliberada:** Training es la **reescritura en Flask/Python** del producto previo `dobackv2-main` (TS/Node/React). El proyecto viejo se ignora explícitamente en `.gitignore` y aparece como **referencia de comportamiento** en docs de migración (ej: `RBAC-FIX-PLAN.md`). Cuando el código actual hace una cosa "distinta a `dobackv2`", asumir que `dobackv2-main` es la fuente de verdad de paridad funcional, salvo que un doc o decisión D-XXX diga lo contrario.
- **Confidencial:** datos CMadrid bajo NDA. **No subir capturas, fixtures reales, ni datos de producción a herramientas externas** (pastebins, gists públicos, ChatGPT con copy/paste de datos reales, etc.).

## Stack actual

Lenguaje y runtime: **Python 3.12** · entorno con `.venv`.

Backend / web framework:
- **Flask 3** (factory pattern en `app/__init__.py`) con blueprints.
- **SQLAlchemy 2.0** + **Flask-SQLAlchemy** + **Alembic** (vía `Flask-Migrate`) para esquema y migraciones.
- **GeoAlchemy2** + PostGIS para geofences y datos espaciales.
- **PostgreSQL** + **Redis** (broker + cache + rate-limit + cola de SocketIO).
- **Celery** para workers asíncronos (`app/workers/*` — scaffolding por completar).
- **Flask-SocketIO** para tiempo real (`app/sockets/*` — scaffolding por completar).

Auth / seguridad:
- **Flask-JWT-Extended** con tokens en **cookies** (`JWT_TOKEN_LOCATION = ["cookies"]`) + CSRF protect.
- **Flask-Login** para gestión de sesión web.
- **Flask-WTF** + **wtforms** + **flask-talisman** + **flask-limiter** + **flask-cors**.
- **Authlib** + **cryptography** + **email-validator**.

Datos y serialización: **Marshmallow** + **marshmallow-sqlalchemy** + **pydantic** + **cuid2**.

UI: **Jinja2** server-side rendering. CSS tokenizado en `app/static/css/{tokens,reset,base}.css` + componentes en `app/static/css/components/*.css` (button, card, form, table, badge, alert, nav). **No hay React ni bundler en runtime** — todo SSR clásico.

Observabilidad: **Loguru** + **Sentry** (`sentry-sdk[flask]`) + **prometheus-flask-exporter**.

Otras dependencias activas: **WeasyPrint** (PDFs), **OpenPyXL** (Excel), **httpx**, **boto3**, **Babel** (i18n `es`/`en`).

Tests: **pytest** + **playwright** (E2E, owner Joel). `tests/conftest.py` está vacío todavía.

> **OJO:** `README.md`, `CONTRIBUTING.md`, `OWNERS.md` y partes de `memory/` siguen describiendo el stack **viejo** (TypeScript / Node / Express / Prisma / pnpm / Vite / Tailwind). Eso es texto desactualizado que aún no se ha podido alinear con la realidad del código. Si tenés que decidir entre lo que dice un doc y lo que dice el código → **el código gana**, y si la divergencia es relevante avisá a Antonio.

## Estructura del repo

```
app/
├── __init__.py              # Flask factory, registro de blueprints
├── config.py                # Dev / Testing / Production configs
├── extensions.py            # db, migrate, jwt, socketio, login, csrf, limiter, cors, ...
├── blueprints/              # 12 blueprints, cada uno con routes.py + services.py + templates/
│   ├── auth/        ── /auth
│   ├── vehicles/    ── /vehicles
│   ├── sessions/    ── /sessions      (recorridos del alumno)
│   ├── events/      ── /events
│   ├── geofences/   ── /geofences
│   ├── uploads/     ── /uploads
│   ├── kpis/        ── /kpis
│   ├── reports/     ── /reports
│   ├── admin/       ── /admin
│   ├── manager/     ── /manager       (UI manager-facing: dashboard, matriz,
│   │                                    ranking, alumno, intento, auditoría,
│   │                                    convocatorias — gateado con
│   │                                    @require_role([MANAGER, ADMIN]).
│   │                                    Hoy sirve mock data hardcodeado;
│   │                                    pendiente conectar a SQLAlchemy.)
│   ├── system/      ── /
│   └── telemetry/   ── /telemetry
├── models/                  # SQLAlchemy: Organization, User, Vehicle, Session, Geofence, Event,
│                            # IngestionJob, AuditLog, KPI, Report, Alert, Notification, ...
├── middleware/              # audit.py, jwt_handlers.py (resto: scaffolding vacío)
├── services/                # alert / kpi_calculator / map_matching / pdf_engine / stability — VACÍOS hoy
├── sockets/                 # alerts / command_center / vehicle / general — VACÍOS hoy
├── workers/                 # ingestion_worker / report_worker / beat_schedule — VACÍOS hoy
├── utils/
│   ├── decorators.py        # ⚠ require_role([...]) — único punto de chequeo de rol (ver §RBAC)
│   └── security.py
├── static/css/              # tokens.css, reset.css, base.css, components/*.css
└── templates/               # base.html, errors/, macros/, settings.html, kpis/

migrations/                  # Alembic
tests/                       # conftest.py (vacío)
docs/                        # README/PAPER/OPERATIONS/PROPUESTA/team/* — docs de planificación
memory/                      # decisiones D-XXX, invariantes, contexto humano del equipo
RBAC-FIX-PLAN.md             # ⚠ plan vivo — leer antes de tocar app/blueprints/*/routes.py
wsgi.py                      # entry de WSGI
celery_worker.py             # entry de Celery (vacío hoy)
import_data.py               # script de seed/migración de datos
seed_geofences.py            # seeding de geofences
setup_db.py                  # init de DB
```

## Documentos clave (orden de lectura)

1. `README.md` — entry point del repo y mapa de docs por audiencia. **Su sección "Stack" está desactualizada** (sigue diciendo TS/Node).
2. `RBAC-FIX-PLAN.md` — plan vivo de separación de roles ADMIN vs MANAGER. **Leer antes de tocar cualquier `routes.py` o `base.html`.**
3. `docs/RESUMEN-EJECUTIVO.md` — visión del proyecto en 10 min (válida).
4. `docs/PAPER-MAESTRO.md` — referencia técnica completa. Muchas secciones describen el diseño TS/Node original — **vale como referencia funcional, no como guía de implementación literal**.
5. `docs/PROPUESTA-CMADRID.md` — SLA, GDPR, escrow para CMadrid (válido).
6. `docs/OPERATIONS.md` — incidentes, rollback, secretos, DR.
7. `docs/team/{antonio,jesus,alejandro,joel-en}.md` — quién hace qué.
8. `OWNERS.md` — **quién aprueba qué archivo. Su lista de paths sensibles está pensada para el stack viejo (`prisma/schema.prisma`, `apps/api/...`); aplicar el espíritu, no la letra (ver §PRs abajo).**
9. `CONTRIBUTING.md` — branches, PRs, DoR/DoD. Mismo caveat que `OWNERS.md`.
10. `memory/MEMORY.md` — índice de decisiones de negocio, invariantes y contexto del cliente.

## Invariantes legales y de producto (NO romper)

- **GDPR art. 22:** el sistema NO decide automáticamente APTO / NO APTO. CMadrid lo decide al cierre formal de cada convocatoria con doble validación administrativa. Ver `memory/arquitectura-invariantes.md` y `memory/modelo-oposicion-publica.md`.
- **Multi-turno** (D-MT-001): soporte para varias convocatorias en paralelo.
- **Webfleet** (D-WF-001): fuente de telemetría de la flota CMadrid.
- **Scoring configurable** (D-SCR-001): 4 familias (estabilidad / velocidad / ruta / conducción).
- Áreas legalmente sensibles → **review obligatoria de Antonio**: cualquier endpoint de cierre de convocatoria, simulación de scoring, exports/reports legales (`reports/`), administración (`admin/`), audit log, y todo lo que toque `app/middleware/jwt_handlers.py` o `app/utils/decorators.py`.

## RBAC (lectura obligatoria antes de tocar `routes.py` o `base.html`)

Estado actual: **roto** (ver `RBAC-FIX-PLAN.md`). Manager y admin ven y pueden lo mismo. Manager puede borrar sesiones del admin. Hay un fix planificado en una rama dedicada.

Reglas firmes:
- **2 roles:** `ADMIN` y `MANAGER`. `User.role` es un Enum → comparar contra `current_user.role.value` (string `"ADMIN"` / `"MANAGER"`).
- **Único punto de chequeo:** decorador `@require_role([...])` en `app/utils/decorators.py:6`. NO reinventar.
- `@require_role` ya llama a `jwt_required()` y `require_org` adentro — **no encadenar los tres decoradores**, basta con uno.
- **Sidebar y backend siempre alineados:** si agregás un ítem visible para MANAGER, el endpoint también tiene que estar en la lista de roles permitidos. Y al revés.
- **Cada endpoint nuevo lleva un decorador de rol explícito.** No "se asume que MANAGER puede" — se escribe.
- No mezclar `@require_role(...)` con `if user.role == ...` adentro de la view — duplica lógica y se desincroniza.
- Tabla canónica de qué ve cada rol → `RBAC-FIX-PLAN.md` §1 (matriz UI + matriz endpoints).

## Convenciones de trabajo (las que afectan a Claude)

### Branches
Namespace por área: `feat/<area>-<desc>` · `fix/<area>-<desc>` · `chore/<desc>` · `docs/<desc>`.

Áreas:
- `wf` — Antonio (Webfleet, integración).
- `be` — Jesús (backend Flask, modelos, blueprints, workers).
- `fe` — Alejandro (templates Jinja, CSS, UX).
- `qa` — Joel (tests, Playwright, CI, simulator).
- `cross` — cruza áreas, coordinar con Antonio.

Vida útil < 1 día. Si crece, partir.

### PRs
- **1 review obligatoria.** **2 reviews** (dueño técnico + Antonio) si el PR toca cualquiera de:
  - `migrations/` — cualquier migración Alembic.
  - `app/middleware/` — auth handlers, audit, JWT.
  - `app/utils/decorators.py` — `require_role`, `require_org`.
  - `app/__init__.py`, `app/extensions.py`, `app/config.py`.
  - `requirements.txt`, `requirements-dev.txt`.
  - `.github/workflows/`.
  - Endpoints en `admin/`, `reports/`, `uploads/`, o cualquier ruta de cierre / simulación de scoring / export legal.
- **Squash merge** por defecto.
- CI verde antes de merge. Si CI falla, se arregla, no se ignora.
- Plantilla del body: `## Qué cambia / ## Por qué / ## Cómo se prueba / ## Riesgos`.
- **`main` está protegida — todo entra por PR.** Históricamente entraron pushes directos a `main` antes de proteger la rama; eso ya no es aceptable.

### Commits
- **Conventional commits:** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`. Mensajes como `"a"`, `"no funcionaba perdon :("`, `"ya se pueden borrar rutas!!!!!!"` (que aparecieron en el historial inicial) **no se aceptan más**.
- **Sin `Co-Authored-By` ni atribución a IA** (regla del usuario y de `CONTRIBUTING.md` §3).

### Naming
- Migraciones Alembic: el script de Alembic (`migrations/script.py.mako`) genera nombres con timestamp. **Una migración por PR.** Mensaje del migrate: `<verbo>_<modelo>` (ej: `add_role_column_user`, `init_base_models`). Si tenés que renombrar/squash una migración antes de merge, hacelo dentro del propio PR.
- `data-testid` (Alejandro pone en templates Jinja, Joel usa en Playwright): `<portal>-<pantalla>-<elemento>` (ej: `manager-sessions-row-3`, `admin-uploads-submit`). Sin `data-testid` Joel puede bloquear merge.

### Endpoint freeze
`docs/api-snapshot.md` se autogenera cada noche a partir de los blueprints registrados en `app/__init__.py` (cron de Joel desde día 2). Alejandro y Joel **solo escriben código contra el snapshot vigente**. Cambios deliberados intra-día = PR de Jesús + aviso a `@Alejandro @Joel`.

### Calidad — no negociables
- **Sin `print(...)` en producto.** Logger central (Loguru) configurado en `app/extensions.py` y/o `app/__init__.py`.
- **Sin `# type: ignore`** salvo justificado con comentario `# type: ignore  # <razón concreta>`.
- **Sin secrets en repo.** `.env` está ignorado. Usar `.env.example` como plantilla.
- **Sin `__pycache__/` ni `*.pyc` commiteados.** Ya están en `.gitignore`. Si aparecen en un PR, hay que removerlos antes de mergear (`git rm -r --cached app/blueprints/*/__pycache__ app/models/__pycache__ ...`).
- **Sin commits a `main` — siempre PR.**
- **CSRF + JWT cookies:** no servir endpoints que muten estado vía GET, no desactivar `JWT_COOKIE_CSRF_PROTECT` salvo en tests (`TestingConfig`).

### Comunicación con CMadrid
**Solo Antonio.** Cualquier comunicación al cliente pasa únicamente por él.

## Cliente nativo Apple — regla permanente (D-IOS-001)

El cliente nativo Apple del backend Training vive en `/Users/antoniohermoso/IOS/Dobacksoft Training` (repo git separado). Tiene **scope cerrado**:

- **Plataformas IN:** iPhone, iPad, Apple Watch.
- **Plataformas OUT:** macOS (sin Mac Catalyst), visionOS / Vision Pro, ningún otro target.
- **Frameworks IN:** Swift puro + SwiftUI + Apple frameworks (URLSession, Keychain, WatchKit, UserNotifications, Combine, async/await).
- **Frameworks OUT:** React Native, Flutter, Capacitor, Cordova, KMM, Mac Catalyst, cualquier herramienta cross-platform. **100% nativo, sin excepciones.**
- **Web NO se replica:** el portal Jinja sigue siendo el cliente principal de MANAGER/ADMIN. La app móvil consume `/api/v1/*` read-only. NO duplicamos funcionalidad operacional pesada en móvil.

Si alguien (Antonio incluido) propone macOS / Vision / cross-platform, la respuesta es: "ver `memory/decision-ios-platform-rule.md` y `architecture/ios-platform-rule` en engram". Cambiar la regla requiere revertir esa decisión explícitamente.

Detalle vivo: [`memory/decision-ios-platform-rule.md`](memory/decision-ios-platform-rule.md).

## Comandos del proyecto (referencia rápida)

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# DB
flask db upgrade                      # aplicar migraciones
flask db migrate -m "add_x_to_y"      # generar nueva migración
python setup_db.py                    # init local
python seed_geofences.py              # cargar geofences base
python import_data.py                 # importar fixture/seed de datos

# Run
python wsgi.py                        # dev server
celery -A celery_worker worker -l info
celery -A celery_worker beat -l info  # scheduler

# Tests
pytest
playwright test                       # E2E (owner: Joel)
```

> **Antes de inventar comandos**, leer este bloque o preguntar. Si una sección de scaffolding está vacía (`app/services/`, `app/sockets/`, `app/workers/`), el comando puede no funcionar todavía — eso es esperado.

## Memoria del proyecto

`memory/` es la memoria **humana persistente del equipo** (decisiones D-XXX, invariantes, contexto de negocio). **No es engram.** Cuando se documente una decisión nueva durante el sprint, añadir un `.md` en `memory/` y enlazarlo desde `memory/MEMORY.md`.

Engram (memoria del agente) sigue activa por separado vía el protocolo del CLAUDE.md global del usuario.

## Idioma

- Antonio, Jesús, Alejandro → **español rioplatense (voseo)**.
- Joel → **inglés**. Sus docs (`docs/team/joel-day1-en.md`, `docs/team/joel-en.md`) están en inglés. Mantener.
- Los docs operativos del cliente (CMadrid) van en **español castellano formal** — no rioplatense.
- Mensajes de error en UI / Flash / `flash(...)` → castellano formal (los lee el usuario final del cuerpo de bomberos).
