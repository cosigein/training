# Cómo contribuimos / How we contribute

> 🇪🇸 Equipo de 4 personas, sprint corto. Estas reglas existen para que **nadie pierda tiempo** y para que **nada se rompa por sorpresa**.
>
> 🇬🇧 *4-person team, short sprint. These rules exist so **nobody wastes time** and **nothing breaks by surprise**. Joel: a short English summary lives at the bottom of this file.*

> **Antes de hacer un PR**, leé también [OWNERS.md](OWNERS.md) — define quién aprueba qué archivo. Sin eso este doc queda en el aire.

---

## 1. Branch strategy

- **`main`** es la rama principal. Está protegida — todo entra por Pull Request.
- Trabajo en **feature branches cortas** (objetivo: < 1 día de vida).
- Convenciones de nombre con **namespace por área**:
  - `feat/<area>-<descripcion-corta>` — feature nueva.
  - `fix/<area>-<descripcion-corta>` — bug fix.
  - `chore/<descripcion>` — config, CI, dependencias.
  - `docs/<descripcion>` — solo documentación.

**Áreas reservadas (para que dos PRs no se confundan):**
- `wf` → Antonio (webfleet)
- `be` → Jesús (backend)
- `fe` → Alejandro (frontend)
- `qa` → Joel (tests + CI + simulator)
- `cross` → cambios que cruzan áreas (revisar con Antonio antes)

Ejemplos:
- `feat/be-auth-jwt-cookies`
- `feat/fe-matrix-virtualized`
- `feat/qa-e2e-login-flow`
- `feat/wf-circuit-breaker`
- `chore/cross-clean-pycache`

> Si una rama lleva >2 días abierta, partila en algo más chico.

---

## 2. Pull Requests

- **1 review obligatoria** de otro dev antes de hacer merge. Self-merge prohibido.
- **Algunos archivos exigen 2 reviews** (dueño técnico + Antonio). Lista en [OWNERS.md](OWNERS.md) sección "Antonio — review obligatoria":
  - `migrations/` (cualquier migración Alembic)
  - `app/middleware/` (auth, audit, JWT handlers)
  - `app/utils/decorators.py` (`require_role`, `require_org`)
  - `app/__init__.py`, `app/extensions.py`, `app/config.py`
  - `requirements.txt`, `requirements-dev.txt`
  - `.github/workflows/`
  - Endpoints en `admin/`, `reports/`, `uploads/`, y cualquier ruta de cierre de convocatoria, simulación de scoring, o export legal
- El reviewer no es solo un sello — si veés algo raro, comentalo.
- PRs pequeños (< 300 líneas) se revisan en minutos. PRs grandes se revisan tarde y mal: si tu cambio crece, partilo.
- **Squash merge** por defecto. El historial de `main` debe ser legible.
- **CI verde** antes de merge. Si CI falla, el PR no entra (se arregla, no se ignora).

### Plantilla de descripción del PR

```
## Qué cambia
<una frase>

## Por qué
<motivación / issue que resuelve>

## Cómo se prueba
<pasos manuales o tests automáticos>

## Riesgos
<qué puede romperse, qué no se cubre>
```

---

## 3. Conventional commits

Cada commit en `main` (después del squash) debe seguir [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: …` — nueva funcionalidad
- `fix: …` — corrección de bug
- `docs: …` — solo documentación
- `chore: …` — config, build, dependencias
- `refactor: …` — refactor sin cambio funcional
- `test: …` — solo tests

> No firmar commits con co-autores de IA. Sin "Co-Authored-By".

---

## 4. Code review — qué pedimos

Cuando revisás el PR de otro:

- ¿Hace lo que dice que hace?
- ¿Tiene tests donde corresponde?
- ¿Rompe alguna invariante (ver `docs/PAPER-MAESTRO.md` §9)?
- ¿El nombre del commit/PR refleja el cambio?
- ¿Hay deuda escondida (TODO, console.log, código muerto)?
- ¿El cambio respeta los límites entre packages/apps?

No es necesario que el código sea perfecto — necesario que sea **honesto** (hace lo que dice, sin sorpresas).

## 4.bis Definition of Ready — cuándo una tarea está lista para empezar

Antes de mover una tarea a "in progress" en tu rama, asegurate de que cumple TODO esto:

- [ ] **Acceptance criteria escritos** (qué tiene que hacer el código para considerarse hecho).
- [ ] **Pequeña** — se puede terminar y mergear en menos de 1 día. Si no, partila.
- [ ] **Dependencias identificadas y resueltas** — si necesitás un endpoint de Jesús o un componente de Alejandro, está disponible o lo está al final del día.
- [ ] **Dueño asignado** (vos mismo si lo agarrás).
- [ ] **Sabe a qué issue padre pertenece** (etiqueta `role:*` correspondiente).

Si una tarea no cumple los 5, **no arranques con ella** — abrila como issue nueva o pediselo a Antonio en el daily.

> Esto es complemento del Definition of Done: DoR es "cuándo empiezo", DoD es "cuándo cierro". Ambos previenen trabajo que no sirve.

---

## 5. Estructura del repo

Monolito Flask/Python con blueprints. Ver `CLAUDE.md` §"Estructura del repo" para el árbol completo.

**Stack consolidado:**
- **Lenguaje y entorno:** Python 3.12, virtualenv en `.venv`.
- **Framework web:** Flask 3 (factory pattern en `app/__init__.py`) + 11 blueprints (`auth`, `vehicles`, `sessions`, `events`, `geofences`, `uploads`, `kpis`, `reports`, `admin`, `system`, `telemetry`).
- **Datos:** SQLAlchemy 2.0 + Alembic (vía Flask-Migrate) + GeoAlchemy2 + PostgreSQL/PostGIS.
- **Async:** Celery (workers en `app/workers/`) + Redis (broker + cache + rate-limit) + Flask-SocketIO (sockets en `app/sockets/`).
- **Auth:** Flask-JWT-Extended con tokens en cookies + CSRF + Flask-Login + Talisman + Limiter.
- **UI:** Jinja2 SSR + CSS tokenizado en `app/static/css/{tokens,reset,base}.css` + componentes en `app/static/css/components/*.css`.
- **Calidad:** dependencias en `requirements.txt` y `requirements-dev.txt`. Lint/format del equipo se acuerda en daily si hace falta (no hay pre-commit definido todavía).

**Reescritura desde `dobackv2-main`:** este repo reescribe en Flask el producto previo TS/React. `dobackv2-main` se ignora en `.gitignore` y aparece como referencia de paridad funcional en docs de migración (ej: `RBAC-FIX-PLAN.md`). Ver `CLAUDE.md` para más contexto.

## 5.bis Política de breaking changes durante el sprint

Si tu cambio rompe algo de otra persona (renombrar un endpoint, cambiar shape de respuesta, mover un componente):

1. **Avisás ANTES** — chat del equipo + comentario en el issue del afectado.
2. **Mergeás el cambio + el fix del consumidor en el mismo PR**, o coordinás dos PRs back-to-back en menos de 1 hora.
3. **Si no podés coordinar el back-to-back**, abrís un PR pequeño primero que mantiene compatibilidad temporal (ambos shapes funcionan), después tu cambio real, después el cleanup.

**No permitido:** mergear y "ya verá el otro mañana cuando le rompa". Bloquea al equipo y consume horas que no tenemos.

## 5.ter Endpoint freeze diario

Cada noche, un job en CI extrae los endpoints estables de los blueprints registrados en `app/__init__.py` (recorriendo `app.url_map`) y commitea `docs/api-snapshot.md` con el diff posteado en el chat del equipo.

- Joel monta y mantiene el cron desde el día 2.
- Alejandro y Joel solo escriben código contra el snapshot vigente.
- Cambios deliberados durante el día = PR de Jesús + aviso en chat con `@Alejandro @Joel`.

## 5.quater Convención `data-testid` (Alejandro pone, Joel usa)

Formato: `data-testid="<portal>-<pantalla>-<elemento>"`

Ejemplos: `manager-matrix-row-3` · `kiosko-rfid-prompt` · `admin-close-step1-button-confirm`

- Alejandro los pone al crear o editar un componente.
- Si Alejandro renombra uno → coordina con Joel ANTES de mergear.
- Sin `data-testid` no hay E2E posible — Joel puede bloquear merge si una pantalla nueva no los tiene.

## 5.quinquies Naming de migraciones Alembic

El script de Alembic (`migrations/script.py.mako`) genera el archivo con timestamp automático. Lo que controlamos es el mensaje del migrate:

```bash
flask db migrate -m "<verbo>_<modelo>"
# ejemplos: add_role_column_user, init_base_models, modify_session_score_audit
```

Una migración por PR. Si tenés que renombrar / squash una migración antes de mergear, hacelo dentro del propio PR.

---

## 6. Daily

- **09:30 (Europe/Madrid). 15 minutos.** Inflexible.
- Formato: cada uno responde 3 preguntas — qué hice ayer, qué hago hoy, qué me bloquea.
- Si te bloquea algo > 2 horas durante el día, no esperes al daily de mañana — escalá en el chat.

---

## 7. Issues

- Cada persona tiene un issue principal con su scope (etiqueta `role:antonio`, `role:jesus`, `role:alejandro`, `role:joel`).
- Los entregables se trackean como sub-tareas (checkbox list dentro del issue) o como issues hijos enlazados.
- Si descubrís trabajo nuevo durante el sprint que NO está en tu issue, abrís un issue nuevo y lo etiquetás. **No hacés trabajo invisible.**
- Cierre de issue solo al merge del PR que lo resuelve.

---

## 8. Calidad — no negociables

- **Sin `print(...)` en código de producto.** Usar Loguru (configurado vía `app/extensions.py` / `app/__init__.py`).
- **Sin `# type: ignore`** salvo casos justificados con comentario `# type: ignore  # <razón>`.
- **Sin `__pycache__/` ni `*.pyc` commiteados.** Ya están en `.gitignore`. Si aparecen en un PR, removerlos del index antes de mergear (`git rm -r --cached ...`).
- **Sin secrets en el repo.** Variables sensibles van por `.env` (ignorado) o secret manager. `.env.example` es la fuente de verdad de qué variables existen.
- **CSRF + JWT cookies:** no servir mutaciones por GET; no desactivar `JWT_COOKIE_CSRF_PROTECT` salvo en `TestingConfig`.
- **Sin commits a `main`.** Siempre PR.

---

## 9. Si algo se rompe

- **Staging roto:** quien lo rompió, lo arregla antes de irse.
- **CI rojo:** no merges hasta que esté verde. Si te urge, hablá con Antonio.
- **Producción rota** (durante demo o cierre real): chat del equipo + ping directo a Antonio.

---

## 10. Comunicación

- Decisiones técnicas se documentan en el PR o en `docs/`.
- Acuerdos verbales que afectan a más de uno se anotan por escrito (chat o issue) — si no está escrito, no existió.
- Cualquier comunicación con CMadrid pasa **únicamente** por Antonio.

---

**Si tenés una duda sobre estas reglas, preguntá. Si una regla te parece tonta para tu caso, también preguntá — vale más cambiar la regla que ignorarla.**

---

## 🇬🇧 Quick reference for Joel (English summary)

| Rule | TL;DR |
|---|---|
| **Branches** | `feat/qa-<description>` for your work · short-lived (<1 day) · off `main`. |
| **PRs** | 1 review required · 2 reviews if you touch `migrations/`, `app/middleware/`, `app/utils/decorators.py`, `requirements*.txt`, CI, or `admin/`/`reports/`/`uploads/` endpoints (Antonio mandatory). |
| **Squash merge.** | One commit per PR on `main`. |
| **Conventional commits** | `feat:`, `fix:`, `chore:`, `docs:`, `test:`. No AI co-authors. |
| **CI must be green** before merge. If you break CI, fix it. Don't ignore it. |
| **Code review** | Look for: does it work? does it have tests? does it break a project invariant? |
| **No `print(...)`** in product code. Use Loguru (set up in `app/extensions.py`). |
| **No `# type: ignore`** without a justified `# type: ignore  # <reason>` comment. |
| **No `__pycache__/` or `*.pyc`** committed — already in `.gitignore`. |
| **No secrets** in the repo. Use `.env` (ignored). |
| **No commits to `main`** — always PR. |
| **Daily** at 09:30 sharp (CET). 15 min. You speak last, in English, 3 sentences. |
| **Data-testid** convention: `<portal>-<screen>-<element>`. Alejandro puts them; you use them in E2E. |
| **Endpoint freeze**: `docs/api-snapshot.md` is auto-generated nightly by your CI job (Joel owns the cron). Only test against the snapshot. |
| **Breaking changes**: if you break someone else's code, you coordinate the fix in the same PR. Don't push & forget. |
| **Owners**: see `OWNERS.md` — every shared file has one approver. |
| **Issues**: tag your work with `role:joel`. Track sub-tasks as a checklist inside the issue. |

If you don't understand a rule, ask Antonio. The rule may be wrong — better to change it than ignore it.
