# Equipo y áreas

**Tipo**: contexto
**Fecha**: 2026-04-28

## Quién hace qué

| Persona | Rol | Área (branch namespace) | Responsabilidad principal |
|---|---|---|---|
| **Antonio Hermoso** | Director técnico | `wf` | Webfleet, simulator, decisiones de arquitectura, comunicación con CMadrid |
| **Jesús** | Backend | `be` | API, Prisma, BullMQ, scoring engine |
| **Alejandro** | Frontend | `fe` | React, design system, todas las pantallas |
| **Joel** | QA + CI | `qa` | Playwright E2E, GitHub Actions, endpoint snapshot, seeds |

## Reglas operativas

- **Daily 09:30 (Europe/Madrid)**, 15 min, inflexible.
- **Comunicación con CMadrid: ÚNICAMENTE Antonio.** Nadie del equipo habla directo con cliente sin pasar por él.
- **Branch namespace por persona** — ver [`CONTRIBUTING.md`](../CONTRIBUTING.md) §1 y [`OWNERS.md`](../OWNERS.md).
- **Antonio aprueba obligatoriamente** cualquier PR que toque `prisma/schema.prisma`, middleware, CI, `package.json` raíz, docker-compose, o endpoints de `/close/*`, `/scoring/simulate`, `/gdpr/*`, `/admin/*`.

## Reuniones recurrentes

- **Daily** — 09:30 Madrid, todos los días laborables del sprint.
- **Demo cliente** — 11/05/2026 (fin del sprint).

## Dónde aplica

A todo el repo. Si dudás de quién toca un archivo, ver [`OWNERS.md`](../OWNERS.md). Si la duda persiste, preguntar a Antonio en chat.
