# Inventario training (cosigein/training)

**Fecha de auditoría:** 2026-05-01  
**Repo:** Flask/SQLAlchemy, Python 3.12  
**Tamaño total:** ~8000 líneas código, 13 blueprints, 9 modelos core, 3 migraciones  

---

## 1. Stack y dependencias

### Versiones reales
- **Python 3.12** (runtime)
- **Flask 3** (framework)
- **SQLAlchemy ≥2.0** + **Flask-SQLAlchemy** + **Alembic** (vía Flask-Migrate)
- **PostgreSQL 17** + **PostGIS 3.5** (geospatial, GeoAlchemy2)
- **Redis 7-alpine** (cache, broker Celery, SocketIO)
- **Celery** (workers asincronos, sin config activa aún)

### Auth & Seguridad
- **Flask-JWT-Extended** + cookies (JWT_TOKEN_LOCATION = ["cookies"])
- **Flask-Login** (sesión web)
- **Flask-WTF** + **wtforms** (CSRF protect, forms)
- **Flask-Talisman** (CSP, secure headers)
- **Flask-Limiter** (rate-limit)
- **Flask-CORS**
- **Authlib** + **cryptography** + **email-validator**

### Datos & Serialización
- **Marshmallow** + **marshmallow-sqlalchemy**
- **pydantic**
- **cuid2** (UUIDs alternativos)

### Observabilidad & Reportes
- **Loguru** (logging central)
- **Sentry SDK**
- **prometheus-flask-exporter**
- **WeasyPrint** (PDF generation)
- **OpenPyXL** (Excel)
- **httpx**, **boto3** (cloud)

### Frontend (SSR)
- **Jinja2** (templates)
- **CSS tokenizado** (no Tailwind, no compilación)
- **Babel** (i18n: es/en)

### Testing (dev)
- **pytest** + **pytest-flask** + **pytest-cov**
- **factory-boy** (fixtures)
- **playwright** (E2E, owner Joel)
- **black**, **ruff**, **mypy**, **isort**, **pre-commit**
- **k6** (load testing)

**Candidates riesgo:**
- Celery sin inicialización (scaffolding vacío)
- SocketIO sin implementación
- Playwright tests arquitectura undefined (Joel owns)
- 23 prints() en código de producto (violation de estándares)

---

## 2. Entrypoints

### Scripts de bootstrap & DB
- **`wsgi.py`**: WSGI entry (Flask app factory)
- **`celery_worker.py`**: Celery worker entry (vacío)
- **`setup_db.py`**: init DB schema
- **`reset_db.py`**: drop + recreate (dev only)
- **`seed_geofences.py`**: load geofence fixtures
- **`import_data.py`**: seed/migration de datos
- **`pytest.ini`**: pytest config minimal

### Docker compose
- **PostgreSQL 17 + PostGIS** en puerto 5435 (training-db)
- **Redis 7-alpine** en puerto 6380 (training-redis)
- Health checks: 5s interval, 10 retries

### Run (dev)
```bash
python wsgi.py                        # Flask dev server
celery -A celery_worker worker        # Celery workers (vacío)
celery -A celery_worker beat -l info  # Scheduler (vacío)
```

---

## 3. Blueprints (rutas)

13 blueprints, 2690 líneas total código.

| Blueprint | Prefix | Líneas | Auth | Roles | Descripción |
|---|---|---|---|---|---|
| **admin** | `/admin` | 444 | @require_role | ADMIN | Gestión org, usuarios, convocatorias |
| **auth** | `/auth` | 131 | jwt + login | PUBLIC + USER | Login, refresh, logout, password reset |
| **sessions** | `/sessions` | 209 | @require_role | ADMIN/MANAGER | Recorridos: list, detail, gps, DELETE (admin-only) |
| **vehicles** | `/vehicles` | 76 | @require_role | ADMIN/MANAGER (read) / ADMIN (write) | Flota: CRUD |
| **events** | `/events` | 52 | @require_role | ADMIN/MANAGER | Eventos: list, acknowledge |
| **kiosko** | `/kiosko` | 144 | @require_org | PUBLIC | Kiosko alumno: RFID tap, check-in |
| **uploads** | `/uploads` | 55 | @require_role | ADMIN | Ingesta datos: file upload |
| **mobile_api** | `/api/v1` | 250 | @jwt_required | STUDENT (read-only) | API móvil iOS |
| **alumno_portal** | `/alumno` | 427 | @require_org | STUDENT | Portal alumno: intentos, resultados, GDPR |
| **manager** | `/manager` | 812 | @require_role | ADMIN/MANAGER | Dashboard manager: ranking, auditoría, convocatorias |
| **student** | `/student` | 40 | @require_role | STUDENT | Perfil estudiante |
| **system** | `/` | 50 | public + auth | MIXED | Health, settings, notfound |
| **events** (legacy) | `/events` | 52 | — | — | Legacy, overlaps con training domain |

**Deuda RBAC:** ver RBAC-FIX-PLAN.md. Manager y admin ven/pueden lo mismo (roto). 3 endpoints sin @require_role decorador (status: plan in progress).

---

## 4. Modelos (datos)

### 9 archivos modelos, ~1300 líneas

| Modelo | Tabla | Rel. Clave | Índices | Multi-tenancy |
|---|---|---|---|---|
| **User** (auth.py) | `User` | Organization, Attempt, Enrollment, Convocatoria | email (unique), organizationId | Sí (org FK, require_org midware) |
| **Organization** (auth.py) | `Organization` | User, Vehicle, Attempt, Convocatoria, Enrollment | apiKey (unique) | Root tenant |
| **OrganizationConfig** | `OrganizationConfig` | Organization (1:1) | organizationId (unique FK) | Cascada |
| **Vehicle** (vehicle.py) | `vehicle`, `Fleet`, MaintenanceRecord | Organization, Telemetry | — | Sí (org FK) |
| **Attempt** (session.py) | `Attempt` | Session, User (student/uploader), Organization | attemptId, studentId, organizationId | Sí |
| **Session** (session.py) | `Session` | Vehicle, Attempt, Organization | sessionId, organizationId | Sí |
| **Convocatoria** (training.py) | `Convocatoria` | Organization, Enrollment, Ranking | uq_convocatoria_name_per_org, closureInitiatedBy (FK User) | Sí (org FK) |
| **Enrollment** (training.py) | `Enrollment` | Convocatoria, User (student), Organization | uq_enrollment_one_per_student_per_convocatoria | Sí |
| **Ranking** (training.py) | `Ranking` | Convocatoria, Attempt, Enrollment, User | ix_ranking_convocatoria_snapshot (convocatoriaId, snapshotAt) | Sí (FK cascade) |
| **AttemptEvent** (training.py) | `AttemptEvent` | Attempt, Organization | ix_attemptevent_attempt_ts (attemptId, timestamp), ix_attemptevent_type | Sí |
| **TrainingAuditLog** (training.py) | `TrainingAuditLog` | User (actor), Organization | ix_traininglog_action_ts, ix_traininglog_resource | Sí (insert-only) |
| **RfidCard** (training.py) | `RfidCard` | User (student), Organization | ix_rfid_uid_active_unique (partial index, unique si active=true) | Sí |
| **GdprDataExport, GdprForgetRequest** (training.py) | — | User, Organization | — | Sí |
| **Event**, **Alert**, **AuditLog** (legacy) | — | — | — | Parcial (legacy) |

**Multi-tenancy:** Implementado vía `organizationId` FK + middleware `require_org` (app/middleware/). Aislamiento: DB-level via FK + app-level via quey filters en blueprints.

**Invariantes clave (PDF-bound):**
- Convocatoria: cierre requiere 2 admins, ventana de 24h reversa
- Ranking: insert-only (never UPDATE/DELETE)
- TrainingAuditLog: insert-only + sin auth failure → acción falla
- RfidCard: índice único parcial (solo 1 activa per uid)

---

## 5. Servicios y workers

### `app/services/` (7 archivos, ~0 líneas implementación)

- **pipeline/** — scaffolding (vacío)
- **alert_service.py** — vacío
- **kpi_calculator.py** — vacío
- **map_matching.py** — vacío
- **pdf_engine.py** — vacío
- **stability_processor.py** — vacío

**Invocación:** No hay, scheduled tasks son cron en docs, no en app.

### `app/workers/` (3 archivos, ~100 líneas)

- **ingestion_worker.py** — scaffolding
- **report_worker.py** — scaffolding
- **ranking_worker.py** — Celery task (WIP), genera ranking snapshots
- **beat_schedule.py** — Celery beat config (empty)

**Colas:** No configuradas. Celery broker = Redis, pero sin tareas reales.

### `app/sockets/` (4 archivos, 0 líneas)

- **alerts/**, **command_center/**, **vehicle/**, **general/** — todos scaffolding vacío
- SocketIO registrado en extensions.py pero sin handlers

---

## 6. Tests

### Estructura
```
tests/
├── conftest.py          (2KiB, fixtures vacío, TODO por Joel)
├── api/
│   ├── __init__.py
│   └── test_mobile_api.py
└── smoke/
    └── test_health.py
```

- **Archivos test:** 3 (`test_mobile_api.py`, `test_health.py`)
- **Coverage real:** ~5% estimado (solo smoke tests, API mobile básico)
- **pytest.ini:** mínimal config
- **Fixtures:** factory-boy installed, conftest vacío

**Gaps:** 
- No tests integration (blueprints, auth, RBAC)
- No tests unit (models, services)
- Playwright E2E no escrito (Joel owns, CI undefined)
- Coverage tracking disabled

---

## 7. Frontend (Jinja + CSS)

### Templates
- **36 archivos `.html`** en `app/templates/`
- **base.html** (5KiB) — layout principal, sidebar (sin gating de rol aún)
- **Blueprint-específicas:** admin/, auth/, manager/, alumno_portal/, kiosko/, student/, alumno/
- **Macros, errors, settings** — subdirs organizados

**Rol gating:** 
- `base.html` sidebar NO tiene `{% if current_user.role %}` (BROKEN, plan RBAC-FIX-PLAN.md)
- Manager VE admin items (regresión)

### CSS
- **8 archivos**, ~82 KiB (tokenizado + components)
- **tokens.css** (1.7KiB) — vars CSS (colores, espaciado)
- **base.css**, **reset.css**, **layout.css**
- **alumno.css, kiosko.css, manager.css** (30+ KiB cada uno, muy densas)
- **components/** — button, card, form, table, badge, alert, nav (modular)

**Setup:** No bundler (SSR). CSS served static, loaded en base.html.

---

## 8. Migraciones Alembic

### Versiones
- **1 migración actual:** `migrations/versions/591f975d7c95_add_audit_request_gdpr_models.py`
- **Fecha:** recent (durante este sprint, mayo 2026)
- **Contenido:** Audit requests + GDPR tables (GdprDataExport, GdprForgetRequest, AuditRequest)

### Drift potencial
- 1 tabla legacy sin migración explícita: `conductores` (Driver, FK hardcodeado a `User` sin ON DELETE definido en migration)
- ServiceHistory tabla mencionada en PAPER-MAESTRO pero no creada aún
- Revision history: v1 = 591f975... (single revision visible)

---

## 9. Documentación viva

### En `docs/`
| Archivo | Líneas | Intención |
|---|---|---|
| **PAPEL-MAESTRO.md** | 4315 | Ref. técnica completa (diseño PDF, fase 1 vs 2, invariantes GDPR) |
| **DOCUMENTO-EJECUTIVO.md** | 624 | Visión ejecutiva (SLAs, features demo vs fase 2) |
| **PROPUESTA-CMADRID.md** | 753 | Propuesta comercial (escrow, GDPR art. 22, operaciones) |
| **MOBILE-API.md** | ~400 | API iOS snapshot |
| **OPERATIONS.md, OPERATIONS-VPS.md** | ~350 | Incidentes, secretos, rollback |
| **LEAD-DASHBOARD.md** | ~400 | Dashboard manager UI (spec) |
| **SETUP-LOCAL.md** | ~200 | Dev environment setup |
| **STATE-2026-04-29.md** | ~350 | Status sprint actual |
| **STYLE-GUIDE-MANAGER.md** | ~300 | UX guidelines manager portal |
| **team/*** | ~4000 | Roles equipo (Antonio, Jesús, Alejandro, Joel) |

### En `memory/`
- **README.md** — índice decisiones D-XXX (business, invariantes, no TODOs)
- **decision-ios-platform-rule.md** — Swift-only client (veto permanente macOS/Vision/cross-platform)
- Otros: arquitectura, modelo oposición, invariantes legales (GDPR art. 22)

### En repo root
- **CLAUDE.md** — estado + stack + invariantes (leer primero, 400 líneas)
- **README.md** — desactualizado (sigue diciendo TS/Node)
- **RBAC-FIX-PLAN.md** — plan vivo de rol separation (CRÍTICO, leer antes de tocar routes.py)
- **CONTRIBUTING.md** — branches, PRs, DoR/DoD (targets stack viejo, aplicar espíritu)
- **OWNERS.md** — permisos merge (idem, paths legacy)
- **TRAINING-ROADMAP.md** — MVP checklist y fase 2

---

## 10. Señales de deuda téctica

### Conteos
- **print()**: 23 instancias en código de producto (`grep "print("` app/blueprints/*/routes.py app/workers/* app/scheduler.py)
- **except Exception sin manejo**: 10 (scheduler, pipeline, workers, blueprints)
- **SQL crudo** (text(), execute()): 3 (minimal, mostly init)
- **TODO/FIXME comentarios**: 3 en código Python
  - `ranking_service.py:53` — "TODO Tarea 12" (audit field placeholder)
  - `conftest.py` — "TODO Joel: cuando montés CI..."

### TOP-10 archivos por deuda (heurístico: print + except + TODO + líneas)

1. **manager/routes.py** (812 líneas) — 4 except Exception, 2 print aprox, hard-coded mock ranking data
2. **alumno_portal/routes.py** (427 líneas) — 1 except Exception, mock GDPR export placeholder
3. **kiosko/routes.py** (144 líneas) — 1 except Exception
4. **auth/routes.py** (131 líneas) — pwd reset pendiente implementar
5. **sessions/routes.py** (209 líneas) — 1 except Exception
6. **mobile_api/routes.py** (250 líneas) — 4 jwt handlers, schemas pero no tests
7. **app/scheduler.py** — 2 except Exception, Celery beat setup incompleto
8. **workers/ranking_worker.py** — 2 except Exception, generator lógica sin tests
9. **admin/routes.py** (444 líneas) — convocatoria_service.py separated (good), but mock rankings
10. **extensions.py** — SocketIO + Celery scaffolding sin registro de tasks

### Hardcoded GDPR art. 22 safeguard
- **Invariante legal firmada:** sistema NO decide automáticamente APTO/NO_APTO → admin debe hacer doble validación
- **Implementación:** Convocatoria.finalRankingSnapshot manual, closureInitiatedBy + closureConfirmedBy (2 admins distintos)
- **Riesgo:** Si logica de ranking_worker genera APTO sin intervención, salta invariante

### Imports no usados (spot checks)
- `from app.models import ...` sin usar en algunos test files
- Controllers legacy imports: `Driver`, `OperationalKey` (no FK relations en training domain)

---

## 11. Riesgos top-5 a primera vista

### 1. **RBAC roto (regresión crítica)**
- **Síntoma:** Manager puede borrar sesiones de admin, ve admin items en sidebar
- **Causa:** `base.html` sin gating rol + 3 endpoints sin `@require_role` decorator
- **Impacto:** Violación GDPR segregación + data loss
- **Fix:** RBAC-FIX-PLAN.md (2–3 horas, prioritario antes de demo)
- **Status:** Plan vivo, no aplicado aún

### 2. **Services/Workers/Sockets scaffolding vacío**
- **Síntoma:** Celery workers no registrados, pipeline.py empty, SocketIO handlers missing
- **Causa:** Reescritura TS→Python en progreso, sprint tight (14 días)
- **Impacto:** Real-time features (alerts, WebSocket) no funcional, batch jobs sin automación
- **Fix:** Fase 2 (post-demo), o descope features dependent
- **Status:** Esperando implementation Jesús/Antonio

### 3. **print() en código de producto (23 instancias)**
- **Síntoma:** Violación estándar (Loguru central esperado)
- **Causa:** Legacy copy-paste del stack viejo, falta code review
- **Impacto:** Logs no centralizados, imposible audit trail
- **Fix:** grep + replace en PR, update pre-commit
- **Status:** No urgente demo pero breach quality gate

### 4. **1 migración Alembic para full domain (Training)**
- **Síntoma:** Schema versionado una sola vez en mayo 2026
- **Causa:** Domain training agregado completo en una migración
- **Impacto:** Si hay rollback / hotfix, toda la tabla training desaparece
- **Fix:** Partir migración por modelo (Convocatoria, Enrollment, Ranking, etc.), migrar ante cambios
- **Status:** Structural OK si no cambia schema, riesgo en iteraciones

### 5. **Auth handlers en middleware sin tests E2E**
- **Síntoma:** JWT_COOKIE_CSRF_PROTECT, require_org, jwt_required handlers custom
- **Causa:** Playwright tests not implemented (Joel owns, CI missing)
- **Impacto:** CSRF bypass, org isolation hole si require_org falla
- **Fix:** test_auth.py E2E (Joel) + mutation test de CSRF headers
- **Status:** Blocker antes de producción CMadrid

---

## Resumen ejecutivo (<200 palabras)

**Training** es reescritura Flask/Python del stack legacy TS/Node (dobackv2). **Tamaño:** ~8K líneas código, 13 blueprints, 9 modelos core, 1 migración. **Equipo 4 personas, sprint 14 días (demo 11/05/2026 Madrid).**

**Stack:** Flask 3 + SQLAlchemy 2 + PostgreSQL 17 + PostGIS + Redis + Celery (scaffolding vacío). **Auth:** JWT-cookies + Flask-Login, 2 roles (ADMIN/MANAGER/STUDENT).

**Blueprints:** admin, auth, sessions, vehicles, events, kiosko, uploads, mobile_api, alumno_portal, manager, student, system. **Modelos:** User, Org, Vehicle, Session, Attempt, Convocatoria, Enrollment, Ranking, TrainingAuditLog, RfidCard, GDPR tables.

**Tests:** 3 test files, ~5% coverage (smoke + mobile API). **Docs:** PAPER-MAESTRO (ref técnica), CLAUDE.md (stack), RBAC-FIX-PLAN (roto, priority fix).

**Top riesgos:** 
1. RBAC regresión (manager borra sesiones admin)
2. Services/workers vacío (no real-time, no automation)
3. 23 print() en código (logs no centralizados)
4. 1 migración Alembic (rollback risk)
5. Auth handlers sin E2E tests (CSRF/org bypass)

**Estado:** Funcional demo, pero deuda técnica clara antes producción. Fix RBAC = 3h priority.
