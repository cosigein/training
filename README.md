# Training

Sistema de evaluación de candidatos a conductor de camión de bomberos para CMadrid (oposición pública).

> **Estado del repo:** recién creado. Aquí viven los **documentos del proyecto**. El código aún no se ha subido — eso ocurre durante el sprint, en este mismo repo.

---

## Contexto en una pantalla

- **Cliente:** CMadrid (cuerpo de bomberos de la Comunidad de Madrid).
- **Modelo:** oposición pública. Los candidatos compiten por un número fijo de plazas. La decisión APTO / NO APTO se emite al **cierre de la convocatoria**, según ranking final.
- **Sprint:** 14 días. Demo con CMadrid el lunes **11 de mayo de 2026**.
- **Equipo:** 4 personas — Antonio (director técnico), Jesús (backend), Alejandro (frontend), Joel (simulador + QA).
- **Stack:** TypeScript + Node 20 + Express + Prisma 6 + PostgreSQL 17 + Redis + BullMQ + React 18 + Vite + Tailwind 4 + Zustand + React Query.

---

## Lo primero que tenés que leer (según quién seas)

| Si sos | Empezá por | Después |
|---|---|---|
| **Antonio** | [`docs/team/antonio.md`](docs/team/antonio.md) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) |
| **Jesús** | [`docs/team/jesus.md`](docs/team/jesus.md) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) (§Backend, §Modelo de datos) |
| **Alejandro** | [`docs/team/alejandro.md`](docs/team/alejandro.md) | [`docs/PAPER-MAESTRO.md`](docs/PAPER-MAESTRO.md) (§Frontend, §Decisiones de UI) |
| **Joel** | [`docs/team/joel-day1-en.md`](docs/team/joel-day1-en.md) | [`docs/team/joel-en.md`](docs/team/joel-en.md) (full role) |

> El **paper maestro** es la referencia técnica completa (~3500 líneas). No hace falta leerlo entero el día 1; usalo como fuente de verdad cuando tengas dudas.

---

## Documentos disponibles

```
docs/
├── PAPER-MAESTRO.md             ← referencia técnica completa (todo el equipo)
├── DOCUMENTO-EJECUTIVO.md       ← visión ejecutiva (interna)
├── PROPUESTA-COMERCIAL.md       ← propuesta para CMadrid (no compartir aún)
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
- **Trabajo en feature branches cortas** (`feat/<area>-<descripcion>`, `fix/...`, `chore/...`). Vida útil objetivo: < 1 día.
- **PRs:** 1 review obligatoria de otro dev antes de merge. Self-merge prohibido.
- **Daily:** 09:30 (Europe/Madrid). 15 minutos. Inflexible.
- **Conventional commits** en cada commit (`feat:`, `fix:`, `chore:`, `docs:`).
- **Detalle completo:** [CONTRIBUTING.md](CONTRIBUTING.md).

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

## Confidencialidad

Este repo es **privado**. Los datos de CMadrid son confidenciales bajo NDA. No comentar el proyecto fuera del equipo, no subir capturas a redes ni a herramientas externas (incluidos pastebins, gists públicos, ChatGPT con copy/paste de datos reales).

---

**Si tenés cualquier duda el día 1, preguntá a Antonio. No pierdas tiempo intentando descifrar algo solo.**
