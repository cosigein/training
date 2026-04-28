# Training

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Sistema de evaluación competitiva                              │
│   para conductores de camión de bomberos                         │
│                                                                  │
│   Cliente:   CMadrid · Cuerpo de Bomberos de la Comunidad        │
│              de Madrid                                           │
│                                                                  │
│   Equipo:    4 personas · Córdoba (Andalucía)                    │
│   Sprint:    14 días · martes 28/04/2026 → lunes 11/05/2026      │
│   Demo:      lunes 11 de mayo · CMadrid · Madrid                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

🇪🇸 Sistema de evaluación de candidatos a conductor de camión de bomberos para CMadrid (oposición pública).
🇬🇧 *Evaluation system for fire-truck driver candidates at CMadrid (Spanish public competitive examination).*

> **Estado del repositorio:** docs + código del producto en el mismo repo. La base Flask/Python ya está scaffoldeada y el sprint avanza features sobre esa base. *Repo state: docs + product code in the same repo. The Flask/Python base is scaffolded; the sprint builds features on top.*

---

## ⚡ Quick start — abre tu doc en 5 segundos

| Si sos / If you are | Abrí ESTE archivo / Open THIS file | Idioma |
|:---|:---|:---:|
| **Antonio** · director técnico | [`docs/team/antonio.md`](docs/team/antonio.md) | 🇪🇸 |
| **Jesús** · backend | [`docs/team/jesus.md`](docs/team/jesus.md) | 🇪🇸 |
| **Alejandro** · frontend | [`docs/team/alejandro.md`](docs/team/alejandro.md) | 🇪🇸 |
| **Joel** · simulator + QA | [`docs/team/joel-day1-en.md`](docs/team/joel-day1-en.md) — **start here** | 🇬🇧 |
| **Dirección · Stakeholder · Cliente** | [`docs/RESUMEN-EJECUTIVO.md`](docs/RESUMEN-EJECUTIVO.md) — visión del proyecto en 10 minutos | 🇪🇸 |
| Anyone else | This repo is confidential. Stop reading. | — |

---

## Tabla de contenidos

1. [Qué es Training](#qué-es-training)
2. [Documentos disponibles](#documentos-disponibles)
3. [Mapa de docs por audiencia](#mapa-de-docs-por-audiencia)
4. [Después del doc de tu rol — qué leer y qué issue trackeás](#después-del-doc-de-tu-rol--qué-leer-y-qué-issue-trackeás)
5. [Cómo trabajamos](#cómo-trabajamos-regla-corta)
6. [Próximos pasos](#próximos-pasos-orden-cronológico)
7. [Issues y seguimiento](#issues-y-seguimiento)
8. [FAQ del día 1](#faq-del-día-1--preguntas-que-probablemente-vas-a-tener)
9. [Confidencialidad](#confidencialidad)

---

## Qué es Training

Training es un sistema **automático y autónomo** de evaluación competitiva para candidatos a conductor de camión de bomberos en oposición pública española. Reemplaza la evaluación tradicional —subjetiva, ejercida por un instructor humano observando desde el copiloto— por sensores físicos en el camión, scoring algorítmico y un ranking acumulado con trazabilidad legal.

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   El alumno conduce una ruta real                    │
   │            ↓                                         │
   │   Sensores (Doback Elite + Webfleet) capturan        │
   │            ↓                                         │
   │   El sistema calcula NOTA de la ruta (0–10)          │
   │            ↓                                         │
   │   La nota actualiza el RANKING de la convocatoria    │
   │            ↓                                         │
   │   Al cierre de la convocatoria, CMadrid emite        │
   │   APTO / NO APTO según ranking + plazas disponibles  │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

**Punto clave legal:** el sistema NO decide automáticamente APTO / NO APTO. CMadrid lo decide al cierre formal de cada convocatoria con doble validación administrativa. Esto cumple **GDPR art. 22** (revisión humana significativa).

### Contexto en una pantalla

| | |
|:---|:---|
| **Cliente** | CMadrid (cuerpo de bomberos de la Comunidad de Madrid) |
| **Modelo** | Oposición pública · ranking + plazas fijas · decisión al cierre |
| **Equipo** | 4 personas trabajando desde Córdoba (Andalucía) |
| **Sprint** | 14 días naturales · 9 días laborables (festivo 01/05) |
| **Demo** | Lunes 11 de mayo de 2026 en Madrid (Antonio viaja) |
| **Stack** | Python 3.12 · Flask 3 · SQLAlchemy 2 · Alembic · GeoAlchemy2 · PostgreSQL + PostGIS · Redis · Celery · Flask-SocketIO · JWT en cookies · Jinja2 SSR · Marshmallow + pydantic · Loguru · Sentry · Playwright |

---

## Documentos disponibles

```
README.md                            ← este documento (entry point)
CONTRIBUTING.md                      ← branches, PRs, conventions, DoR/DoD
OWNERS.md                            ← quién aprueba qué archivo (LEER antes del primer PR)

docs/
├── 📘 RESUMEN-EJECUTIVO.md           ← visión del proyecto en 10 min · stakeholders
├── 📕 PAPER-MAESTRO.md               ← referencia técnica completa (~4300 líneas)
├── 📗 DOCUMENTO-EJECUTIVO.md         ← visión funcional no técnica (cliente + gestión)
├── 📙 PROPUESTA-CMADRID.md           ← descripción del servicio para CMadrid (SLA, GDPR, escrow)
├── 📔 OPERATIONS.md                  ← incidentes, rollback, secretos, DR, soporte post-cutover
└── team/
    ├── antonio.md                    ← qué hace Antonio en el sprint
    ├── jesus.md                      ← qué hace Jesús
    ├── alejandro.md                  ← qué hace Alejandro
    ├── joel-day1-en.md               ← Joel: primeras horas (EN)
    └── joel-en.md                    ← Joel: rol completo (EN)
```

---

## Mapa de docs por audiencia

| Si sos / Si necesitás | Empezá por | Después, si querés profundidad |
|:---|:---|:---|
| **Miembro del equipo** | Tu doc en `docs/team/` | `OWNERS.md` + `CONTRIBUTING.md` antes de tu primer PR |
| **Dirección · Stakeholder** | `docs/RESUMEN-EJECUTIVO.md` (10 min) | Conversaciones internas de empresa (cobertura de agenda, RC, contratos) se cierran fuera de este repositorio. |
| **Cliente CMadrid** | `docs/DOCUMENTO-EJECUTIVO.md` | `docs/PROPUESTA-CMADRID.md` para SLA, GDPR, escrow |
| **Auditor · Nuevo en el repo** | `docs/RESUMEN-EJECUTIVO.md` + este README | `docs/PAPER-MAESTRO.md` solo cuando dudes de algo concreto |

---

## Después del doc de tu rol — qué leer y qué issue trackeás

| Si sos | Tu issue principal | Issues compartidos | Después de tu doc, leé |
|:---|:---|:---|:---|
| **Antonio** | [#2 Webfleet ingestion](https://github.com/cosigein/training/issues/2) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) — completo |
| **Jesús** | [#3 Backend completo](https://github.com/cosigein/training/issues/3) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) (§Backend + §Modelo de datos) — solo si tenés tiempo |
| **Alejandro** | [#4 Frontend completo](https://github.com/cosigein/training/issues/4) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) (§Frontend + §Decisiones de UI) — solo si tenés tiempo |
| **Joel** | [#5 Simulator + QA + CI](https://github.com/cosigein/training/issues/5) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/team/joel-en.md`](docs/team/joel-en.md) (full role, EN) — for days 2+ |

> Cada issue tiene un **Definition of Done** como comentario o en el body — checklist de qué tiene que estar terminado para cerrarlo.
>
> Si descubrís trabajo que no cabe en tu issue principal, **abrís un issue nuevo** con la label `role:<vos>` y lo enlazás. No hacés trabajo invisible.
>
> El **paper maestro** es la referencia técnica completa (~4300 líneas). No hace falta leerlo entero el día 1; usalo como fuente de verdad cuando tengas dudas. *The master paper is in Spanish — Joel: Antonio will translate any specific section you need.*

---

## Cómo trabajamos (regla corta)

### Branch principal y branches de trabajo

- **`main`** está protegida — todo entra por Pull Request.
- **Trabajo en feature branches cortas** con namespace por área:
  - `feat/wf-...` — Antonio (Webfleet)
  - `feat/be-...` — Jesús (backend)
  - `feat/fe-...` — Alejandro (frontend)
  - `feat/qa-...` — Joel (tests + CI + simulator)
  - `chore/cross-...` — cambios cross-team
- **Vida útil de rama:** menos de 1 día.

### Pull Requests

- **1 review obligatoria** del equipo.
- **2 reviews** (dueño técnico + Antonio) si tocás `migrations/`, `app/middleware/`, `app/utils/decorators.py`, `app/__init__.py` · `extensions.py` · `config.py`, `requirements*.txt`, `.github/workflows/`, o endpoints en `admin/` · `reports/` · `uploads/`.
- **Squash merge** por defecto.
- **CI verde** antes de merge.

### Convenciones que evitan colisiones

- **Conventional commits:** `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- **Endpoint freeze diario:** un cron de Joel autogenera `docs/api-snapshot.md` cada noche desde los blueprints registrados en `app/__init__.py`. Alejandro y Joel codean contra ese snapshot.
- **Convención `data-testid`:** `<portal>-<pantalla>-<elemento>` (Alejandro pone en templates Jinja, Joel usa en Playwright).
- **Naming de migraciones Alembic:** mensaje del migrate `<verbo>_<modelo>` (ej: `add_role_column_user`, `init_base_models`). Una migración por PR.
- **Daily standup:** 09:30 sharp Europe/Madrid · 15 min · inflexible · Joel habla último en inglés (3 frases).
- **Definition of Ready** + **Definition of Done** en `CONTRIBUTING.md`.
- **Quién aprueba qué:** `OWNERS.md`. Sin esto los 4 chocamos.

> **Detalle completo:** [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Próximos pasos (orden cronológico)

> El scaffolding Flask/Python ya está en `main` (factory en `app/__init__.py` + 11 blueprints + modelos SQLAlchemy + Alembic). El sprint construye features sobre esa base.

1. **Cada persona** lee su doc individual + `OWNERS.md` + `CONTRIBUTING.md` antes de su primer PR.
2. **Daily a las 09:30** (Europe/Madrid · 15 min · inflexible · Joel habla último en inglés, 3 frases).
3. **Trabajo del día** según el issue principal de cada uno (ver tabla "Después del doc de tu rol"). Branches cortas con namespace de área (`feat/wf-...`, `feat/be-...`, `feat/fe-...`, `feat/qa-...`).
4. **Cada viernes 17:30:** retrospectiva semanal del equipo + status update al cliente.
5. **Demo CMadrid:** lunes 11 de mayo en Madrid (Antonio viaja).

---

## Issues y seguimiento

El trabajo del sprint está distribuido en **6 issues de GitHub** en este repo, todos con Definition of Done. Cada persona tiene un issue principal con su scope; los issues hijos se abren conforme aparece trabajo nuevo.

[**Ver pestaña Issues** →](../../issues)

Filtrá por la etiqueta de tu rol para ver solo los que te aplican:
- [`role:antonio`](../../issues?q=is%3Aissue+label%3Arole%3Aantonio)
- [`role:jesus`](../../issues?q=is%3Aissue+label%3Arole%3Ajesus)
- [`role:alejandro`](../../issues?q=is%3Aissue+label%3Arole%3Aalejandro)
- [`role:joel`](../../issues?q=is%3Aissue+label%3Arole%3Ajoel)

---

## FAQ del día 1 — preguntas que probablemente vas a tener

> 🇪🇸 Estas son las preguntas que detectamos al simular cómo lo lee cada miembro del equipo. Si todavía tenés dudas después, preguntale a Antonio.

### "¿Qué tengo que tener instalado para arrancar?"

- ✅ **Python 3.12** (`python --version` debe imprimir `3.12.x`).
- ✅ **PostgreSQL 16+** con extensión **PostGIS** (geofences usan tipos espaciales).
- ✅ **Redis** (broker de Celery + cola SocketIO + cache + rate-limit).
- ✅ **Aceptar la invitación al repo** en GitHub.

Setup local típico:

```bash
git clone git@github.com:cosigein/training.git && cd training
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                # rellenar SECRET_KEY, DATABASE_URL, REDIS_URL, JWT_SECRET
flask db upgrade
python setup_db.py && python seed_geofences.py
python wsgi.py                      # dev server
```

Si algo falla, preguntale a Antonio o a Jesús — vale más perder 5 minutos preguntando que pelear con el setup una hora.

### "¿Tengo que leer el paper maestro entero antes de venir?"

**No.** El paper son ~4300 líneas. La lectura silenciosa de 30 minutos durante el kickoff es lo único obligatorio del día 1: cada uno lee solo las secciones que aplican a su rol (tu doc individual te dice cuáles). El resto se consulta como referencia cuando aparezca una duda concreta durante el sprint.

### "¿Qué pasa si me bloquea algo y no hay chat del equipo todavía?"

El chat del equipo lo crea Antonio antes del kickoff (puede ser la víspera o la misma mañana). Hasta que exista:
- DM directo a Antonio en tu canal personal con él.
- O esperá al kickoff de las 09:00 — tenemos una hora juntos para resolver dudas.

### "¿Y si Antonio se demora la mañana del kickoff?"

Plan de contingencia (si Antonio no está a las 09:15 y nadie sabe nada de él):

1. **No empieces a codear nada.** El kickoff existe para alinearnos.
2. **Cada uno relee su doc de rol con calma** (~30 min).
3. **Hablan entre los 3:** repasen quién hace qué la primera semana, qué dependencias tienen entre ustedes, qué dudas comunes.
4. **Si Antonio sigue sin aparecer a las 10:30**, llamen a su teléfono (Antonio se los pasa por DM antes del martes). Si no contesta, escalan a Dirección por el canal que Antonio les indique.
5. **Si todo eso falla**, el equipo sigue las instrucciones de su doc individual hasta tener noticias. Mejor avanzar lento que parar.

### "¿Quién decide cuando hay un conflicto técnico entre Jesús y Alejandro?"

Antonio. Si Antonio no está disponible y bloquea, **el más afectado por la decisión decide y lo documenta** en el chat — Antonio puede revertirlo después si discrepa, sin drama.

### "¿Qué pasa si rompo algo en `main`?"

`main` está protegida — no podés hacer push directo. Solo entra por PR con review. Si tu PR rompe CI, lo arreglás antes de mergear. Si ya está mergeado y rompe staging, **el que rompió, arregla, antes de irse de la oficina**. Eso es regla del proceso.

> Para incidentes operativos durante una convocatoria real, ver [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

### "¿Qué hago si no entiendo algo de mi propio doc?"

1. Buscalo en el glosario (cada doc tiene uno al principio).
2. Buscalo en `docs/PAPER-MAESTRO.md` con `Cmd+F` / `Ctrl+F`.
3. Si sigue sin estar claro, preguntale a Antonio en el daily o por DM. **Es mejor pregunta tonta que código equivocado.**

---

## Confidencialidad

Este repo es **privado**. Los datos de CMadrid son confidenciales bajo NDA. No comentar el proyecto fuera del equipo, no subir capturas a redes ni a herramientas externas (incluidos pastebins, gists públicos, ChatGPT con copy/paste de datos reales).

---

**Si tenés cualquier duda el día 1, preguntá a Antonio. No pierdas tiempo intentando descifrar algo solo.**

> *Antonio: tu checklist personal pre-kickoff vive en [`docs/team/antonio.md` §12](docs/team/antonio.md). El resto del equipo no necesita verlo.*
