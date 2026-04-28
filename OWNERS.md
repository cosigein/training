# Owners

> **Cómo se lee este archivo:** "todos pueden proponer un cambio, pero **una sola persona aprueba el merge**". Si tu PR toca un recurso de la columna izquierda, necesita la review de la persona de la columna derecha. Sin excepciones.

---

## Recursos compartidos del repo

| Recurso | Dueño (review obligatoria) | Quién puede proponer cambios |
|---|---|---|
| `requirements.txt` · `requirements-dev.txt` | **Jesús** | Quien necesita una dependencia nueva la propone en el PR |
| `app/__init__.py` · `app/extensions.py` · `app/config.py` (factory + ext + config) | **Jesús** | Cualquiera; Antonio review obligatoria |
| `migrations/` · `migrations/script.py.mako` (Alembic) | **Jesús** | Solo Jesús edita; otros proponen vía issue |
| `app/models/*.py` (modelos SQLAlchemy) | **Jesús** | Solo Jesús edita; otros proponen vía issue |
| `.env.example` (fuente única de verdad de variables) | **Jesús** | Quien necesita una variable nueva añade aquí + en el PR |
| `app/middleware/` (auth, audit, JWT handlers) | **Jesús** | Cualquiera; Antonio review obligatoria |
| `app/utils/decorators.py` (`require_role`, `require_org`) | **Jesús** | Cualquiera; Antonio review obligatoria |
| `app/blueprints/<área>/routes.py` y `services.py` (resto del backend, salvo blueprints reservados a Antonio) | **Jesús** | Jesús edita |
| `app/templates/` (base.html, errors, macros, settings) | **Alejandro** | Alejandro edita; Joel toca solo `data-testid` con su convención |
| `app/blueprints/<área>/templates/` (templates por blueprint) | **Alejandro** | Alejandro edita |
| `app/static/css/tokens.css` · `app/static/css/{reset,base}.css` · `app/static/css/components/*.css` (design system) | **Alejandro** | Alejandro decide |
| `app/blueprints/admin/` (cuando se incorpore scoring simulator y cierre de convocatoria) | **Antonio** | Antonio edita; Alejandro entrega componentes base; Joel escribe E2E |
| `app/services/webfleet/` y `app/workers/webfleet_worker.py` (cuando existan — ingesta Webfleet + sync periódico) | **Antonio** define el contrato + **Jesús** orquesta Celery | Antonio define qué llama, Jesús cómo se programa |
| `docs/SIMULATOR-USER-GUIDE.md` (cuando se cree) | **Antonio** | Doc para admin CMadrid (español castellano, 1-2 páginas) |
| `tests/` · `tests/conftest.py` · tests E2E con Playwright | **Joel** | Joel edita; Jesús revisa fixtures que tocan modelos |
| `setup_db.py` · `seed_geofences.py` · `import_data.py` | **Joel** ejecuta y mantiene; **Jesús** revisa coherencia con modelos | Joel edita; Jesús review obligatoria |
| `.github/workflows/*` (CI/CD) | **Joel** | Joel edita; cuando un cambio de Jesús/Alejandro rompa CI, lo arregla quien lo rompió |
| `RBAC-FIX-PLAN.md` | **Antonio** | Plan vivo; cualquiera puede actualizar el progreso pero Antonio aprueba cambios de scope |
| `docs/` (cualquier `.md`) | **Antonio** | Cualquiera edita; Antonio mergea |
| `README.md` · `CONTRIBUTING.md` · `OWNERS.md` · `CLAUDE.md` | **Antonio** | Cualquiera propone, Antonio mergea |
| `memory/*.md` (decisiones D-XXX, invariantes) | **Antonio** | Cualquiera propone; Antonio mergea decisiones nuevas |

---

## Antonio — review **obligatoria** en estos archivos

Independientemente del dueño técnico, Antonio (director técnico) tiene que aprobar cualquier PR que toque:

```
   ▶ migrations/                       (cambios al esquema de datos vía Alembic)
   ▶ app/models/*.py                   (definición SQLAlchemy de los modelos)
   ▶ app/middleware/                   (auth, audit, JWT handlers, multi-tenant, CSRF)
   ▶ app/utils/decorators.py           (require_role, require_org — RBAC)
   ▶ app/__init__.py                   (factory, registro de blueprints)
   ▶ app/extensions.py                 (db, jwt, socketio, login, csrf, limiter, ...)
   ▶ app/config.py                     (Dev/Test/Prod config, JWT cookies, secrets)
   ▶ requirements.txt · requirements-dev.txt   (dependencias)
   ▶ .github/workflows/                (CI/CD pipeline)
   ▶ Cualquier endpoint en
     app/blueprints/admin/
     app/blueprints/reports/
     app/blueprints/uploads/
     o cualquier ruta de cierre de convocatoria, simulación de scoring, export legal
     (flujos legalmente sensibles)
```

Esto significa: **2 reviews** en estos PRs (el dueño técnico + Antonio).

---

## Convenciones que afectan a varios dueños

### Convención de `data-testid` (Alejandro pone, Joel usa)

Formato: `data-testid="<portal>-<pantalla>-<elemento>"`

Ejemplos:
- `data-testid="manager-matrix-row-3"`
- `data-testid="kiosko-rfid-prompt"`
- `data-testid="admin-close-step1-button-confirm"`

Reglas:
- Alejandro pone los `data-testid` cuando crea o edita un componente.
- Joel los usa en E2E tests.
- Si Alejandro quiere renombrar uno → coordina con Joel ANTES de mergear (no después: rompe los tests).
- Sin `data-testid` no hay test E2E posible — Joel puede bloquear merge si una pantalla nueva no los tiene.

### Naming de migraciones Alembic (Jesús)

El timestamp del archivo lo genera Alembic. Lo que controlamos es el mensaje del migrate:

```bash
flask db migrate -m "<verbo>_<modelo>"
```

Ejemplos:
- `init_base_models`
- `add_convocatoria_status`
- `modify_session_score_audit`
- `add_role_column_user`

**Regla:** una migración por PR. Si tenés que renombrar / squash una migración antes de mergear, hacelo dentro del propio PR. Una vez en `main`, no se reescribe — se añade una migración nueva.

### Branch namespace por persona

Formato: `<tipo>/<area>-<descripcion>`

Áreas reservadas:
- `wf` → trabajo de Antonio (webfleet)
- `be` → trabajo de Jesús (backend)
- `fe` → trabajo de Alejandro (frontend)
- `qa` → trabajo de Joel (tests + CI + simulator)
- `cross` → cambios que cruzan áreas (revisar con Antonio antes)

Ejemplos:
- `feat/be-auth-jwt-cookies`
- `feat/fe-matrix-virtualized`
- `feat/qa-e2e-login-flow`
- `feat/wf-circuit-breaker`
- `chore/cross-clean-pycache`

---

## Política de breaking changes durante el sprint

Si tu cambio rompe algo de otra persona (renombrar un endpoint, cambiar shape de respuesta, mover un componente):

1. **Avisás ANTES** — chat del equipo + comentario en el issue del afectado.
2. **Mergeás el cambio + el fix del consumidor en el mismo PR**, o coordinás dos PRs back-to-back en menos de 1 hora.
3. **Si no podés coordinar el back-to-back**, abrís un PR pequeño primero que mantiene compatibilidad temporal (ambos shapes funcionan), después tu cambio real, después el cleanup.

**Lo que NO está permitido:** mergear y "ya verá Alejandro mañana cuando le rompa". Eso bloquea al equipo y consume horas que no tenemos.

---

## Endpoint freeze diario

Cada noche, un job en CI commitea automáticamente `docs/api-snapshot.md` con el listado de endpoints estables (path, método, blueprint, decoradores de rol).

- **Joel** monta y mantiene el cron desde el día 2: recorre `app.url_map` de la app Flask y serializa a Markdown (incluyendo el rol requerido por endpoint).
- Si el snapshot cambia respecto al día anterior, se mergea como commit `chore(qa): api-snapshot YYYY-MM-DD` y se postea el diff en el chat del equipo.
- Alejandro y Joel solo escriben código contra el snapshot vigente.
- Cambios deliberados durante el día = PR de Jesús + aviso explícito en chat con `@Alejandro @Joel`.

---

## Si dudás sobre quién es dueño de algo

Preguntá en el chat. Una respuesta de Antonio en chat queda como decisión documentada.

Si la duda se repite, abrí un PR que añade la fila correspondiente a este `OWNERS.md`.
