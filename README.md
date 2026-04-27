# Training

## ⚡ ¿Quién sos? — abre tu doc en 5 segundos

| Si sos / If you are | Abrí ESTE archivo / Open THIS file |
|---|---|
| **Antonio** | [`docs/team/antonio.md`](docs/team/antonio.md) (ES) |
| **Jesús** | [`docs/team/jesus.md`](docs/team/jesus.md) (ES) |
| **Alejandro** | [`docs/team/alejandro.md`](docs/team/alejandro.md) (ES) |
| **Joel** | [`docs/team/joel-day1-en.md`](docs/team/joel-day1-en.md) — **start here, EN** |
| Anyone else | This repo is confidential. Stop reading. |

**Kickoff / When we start:** martes 28 de abril de 2026, 09:00 (Europe/Madrid).
**Demo CMadrid:** lunes 11 de mayo de 2026.

---

🇪🇸 Sistema de evaluación de candidatos a conductor de camión de bomberos para CMadrid (oposición pública).
🇬🇧 *Evaluation system for fire-truck driver candidates at CMadrid (Spanish public competitive examination).*

> **Estado del repo:** recién creado. Aquí viven los **documentos del proyecto**. El código aún no se ha subido — eso ocurre durante el sprint, en este mismo repo.
> *Repo state: just created. Only project documents live here. Code lands during the sprint.*

---

## Contexto en una pantalla

- **Cliente:** CMadrid (cuerpo de bomberos de la Comunidad de Madrid). Está en Madrid.
- **Equipo:** 4 personas trabajando desde **Córdoba** (Andalucía). El equipo viaja a Madrid solo para la demo del 11/05.
- **Modelo:** oposición pública. Los candidatos compiten por un número fijo de plazas. La decisión APTO / NO APTO se emite al **cierre de la convocatoria**, según ranking final.
- **Sprint:** 14 días. Demo con CMadrid el lunes **11 de mayo de 2026**.
- **Roles:** Antonio (director técnico), Jesús (backend), Alejandro (frontend), Joel (simulador + QA).
- **Stack:** TypeScript + Node 20 + Express + Prisma 6 + PostgreSQL 17 + Redis + BullMQ + React 18 + Vite + Tailwind 4 + Zustand + React Query.

---

## Después del doc de tu rol — qué leer y qué issue trackeás

| Si sos | Tu issue principal | Issues compartidos | Después de tu doc, leé |
|---|---|---|---|
| **Antonio** | [#2 Webfleet ingestion](https://github.com/cosigein/training/issues/2) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) — completo |
| **Jesús** | [#3 Backend completo](https://github.com/cosigein/training/issues/3) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) (§Backend + §Modelo de datos) — solo si tenés tiempo |
| **Alejandro** | [#4 Frontend completo](https://github.com/cosigein/training/issues/4) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) (§Frontend + §Decisiones de UI) — solo si tenés tiempo |
| **Joel** | [#5 Simulator + QA + CI](https://github.com/cosigein/training/issues/5) | [#1](https://github.com/cosigein/training/issues/1) · [#6](https://github.com/cosigein/training/issues/6) | [`docs/team/joel-en.md`](docs/team/joel-en.md) (full role, EN) — for days 2+ |

> Cada issue tiene un **Definition of Done** como comentario o en el body — checklist de qué tiene que estar terminado para cerrarlo.
>
> Si descubrís trabajo que no cabe en tu issue principal, **abrís un issue nuevo** con la label `role:<vos>` y lo enlazás. No hacés trabajo invisible.
>
> El **paper maestro** es la referencia técnica completa (~3500 líneas). No hace falta leerlo entero el día 1; usalo como fuente de verdad cuando tengas dudas. *The master paper is in Spanish — Joel: Antonio will translate any specific section you need.*

---

## Documentos disponibles

```
README.md                        ← este documento (entry point)
CONTRIBUTING.md                  ← branch strategy, PRs, conventions
OWNERS.md                        ← quién aprueba qué archivo (LEER antes del primer PR)

docs/
├── PAPER-MAESTRO.md             ← referencia técnica completa (todo el equipo)
├── DOCUMENTO-EJECUTIVO.md       ← visión ejecutiva no técnica (cliente + gestión)
├── PROPUESTA-COMERCIAL.md       ← propuesta para CMadrid (no compartir aún)
├── MEMO-DIRECCION-INTERNO.md    ← caso de negocio (interno, solo Dirección)
└── team/
    ├── antonio.md               ← qué hace Antonio en estos 14 días
    ├── jesus.md                 ← qué hace Jesús
    ├── alejandro.md             ← qué hace Alejandro
    ├── joel-day1-en.md          ← Joel: primeras horas (EN)
    └── joel-en.md               ← Joel: rol completo (EN)
```

---

## Cómo trabajamos (regla corta)

- **Branch principal:** `main`. Protegida — todo entra por PR.
- **Trabajo en feature branches cortas** con **namespace por área**: `feat/be-...` (Jesús), `feat/fe-...` (Alejandro), `feat/qa-...` (Joel), `feat/wf-...` (Antonio Webfleet), `chore/cross-...` (cambios cross-team). Vida útil objetivo: < 1 día.
- **PRs:** 1 review obligatoria; **2 reviews si tocás `prisma/schema.prisma`, middleware de auth, `package.json` raíz, CI o `docker-compose`** (Antonio mandatory).
- **Daily:** 09:30 (Europe/Madrid). 15 minutos. Inflexible.
- **Conventional commits** en cada commit (`feat:`, `fix:`, `chore:`, `docs:`).
- **Quién aprueba qué:** ver [`OWNERS.md`](OWNERS.md). Sin esto los 4 chocamos.
- **Detalle completo:** [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Próximos pasos (orden cronológico)

1. **Ahora (antes de empezar):** cada persona del equipo lee su doc individual (link arriba).
2. **Día 1 — kickoff con Antonio:** lectura silenciosa del paper maestro (las secciones que aplican a cada uno) + Q&A.
3. **Día 1, fin de mañana:** primer commit de cada persona en una rama `chore/setup-<nombre>` con su archivo de bienvenida en `docs/onboarding/<nombre>.md` para validar el flujo de PR.
4. **Día 1, tarde:** se levanta la base del backend y del frontend en este repo. A partir de ese momento empezamos a tener código.
5. **Cada viernes 17:00:** demo interna del progreso de la semana.

---

## Issues y seguimiento

El trabajo del sprint está distribuido en **issues de GitHub** en este repo. Cada persona tiene un issue principal con su scope y issues hijos por entregable. Mirá la pestaña [Issues](../../issues) y filtrá por la etiqueta de tu rol (`role:antonio`, `role:jesus`, `role:alejandro`, `role:joel`).

---

## FAQ del día 1 — preguntas que probablemente vas a tener

**🇪🇸 Estas son las preguntas que detectamos al simular cómo lo lee cada miembro del equipo. Si todavía tenés dudas después, preguntale a Antonio.**

### "¿Qué tengo que tener instalado al llegar al kickoff?"

Solo 3 cosas, y NO incluye clonar el repo ni `npm install`:
- Node 20 LTS (`node --version` debe imprimir v20.x.x).
- Docker Desktop (debe arrancar).
- Aceptar la invitación al repo en GitHub (te llega cuando Antonio te invite).

Si llegás mañana sin alguno de estos, **no hay drama**: en los primeros 15 minutos del kickoff los instalamos juntos. El kickoff arranca a las 09:00, dura 1 hora, y después scaffolding compartido — durante ese tiempo se nivela el setup.

**No clones el repo, no instales dependencias del proyecto, no crees carpetas.** El scaffolding lo hacemos los 4 en pantalla compartida para que nadie quede con una versión distinta.

### "¿Tengo que leer el paper maestro entero antes de venir?"

**No.** El paper son ~3500 líneas. La lectura silenciosa de 30 minutos durante el kickoff es lo único obligatorio del día 1: cada uno lee solo las secciones que aplican a su rol (tu doc individual te dice cuáles). El resto se consulta como referencia cuando aparezca una duda concreta durante el sprint.

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

### "¿Qué hago si no entiendo algo de mi propio doc?"

1. Buscalo en el glosario (cada doc tiene uno al principio).
2. Buscalo en `docs/PAPER-MAESTRO.md` con Cmd+F / Ctrl+F.
3. Si sigue sin estar claro, preguntale a Antonio en el daily o por DM. **Es mejor pregunta tonta que código equivocado.**

---

## Confidencialidad

Este repo es **privado**. Los datos de CMadrid son confidenciales bajo NDA. No comentar el proyecto fuera del equipo, no subir capturas a redes ni a herramientas externas (incluidos pastebins, gists públicos, ChatGPT con copy/paste de datos reales).

---

**Si tenés cualquier duda el día 1, preguntá a Antonio. No pierdas tiempo intentando descifrar algo solo.**

> *Antonio: tu checklist personal pre-kickoff vive en [`docs/team/antonio.md` §12](docs/team/antonio.md). El resto del equipo no necesita verlo.*
