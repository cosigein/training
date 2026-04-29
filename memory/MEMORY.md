# Índice de memoria — Training

> Para el formato y reglas, ver [README.md](README.md).

---

## Decisiones de negocio

- [Webfleet entra al sistema](decision-webfleet-entra.md) — D-WF-001, sincronización con flota CMadrid
- [Scoring configurable](decision-scoring-configurable.md) — D-SCR-001, 4 familias (estabilidad/velocidad/ruta/conducción)
- [Multi-turno confirmado](decision-multi-turno.md) — D-MT-001, soporte para varias convocatorias en paralelo

## Decisiones de implementación / frontend

- [Frontend con dos layouts](decision-frontend-dual-layout.md) — D-FE-001, top-nav nuevo `/manager/*` vs sidebar viejo `DOBACKSOFT` en `/sessions/` y `/admin/*` — pendiente decisión Alejandro+Antonio antes 09/05

## Equipo y proceso

- [Equipo y áreas](equipo.md) — Antonio, Jesús, Alejandro, Joel — quién toca qué
- [Cliente CMadrid](contexto-cmadrid.md) — Bomberos Comunidad de Madrid, oposición pública, demo 11/05/2026

## Arquitectura

- [Invariantes del sistema](arquitectura-invariantes.md) — Las 9 reglas que NO se rompen, pase lo que pase
- [Modelo de oposición pública](modelo-oposicion-publica.md) — Ranking acumulado, plazas limitadas, APTO/NO_APTO solo al cierre

## Gotchas

- [Gotchas del sprint](gotchas-sprint.md) — 13 trampas no obvias del código y del entorno (FLASK_CONFIG vs FLASK_ENV, db.create_all() y enums, redis del VPS sin auth, AirPlay :5000, etc.)

## Snapshots del proyecto

- [STATE 2026-04-29](../docs/STATE-2026-04-29.md) — foto fija al cierre de día 2 del sprint: tareas hechas/pendientes, frontend findings, riesgos vivos, owners

## Operativa

- [SETUP-LOCAL](../docs/SETUP-LOCAL.md) — onboarding local en 10-15 minutos
- [OPERATIONS-VPS](../docs/OPERATIONS-VPS.md) — estado real del VPS (systemd, nginx, postgres host, comandos de troubleshooting)

## Convenciones

- _(El equipo añade convenciones propias durante el sprint. Las oficiales viven en [`CONTRIBUTING.md`](../CONTRIBUTING.md) y [`OWNERS.md`](../OWNERS.md))_

## Acuerdos externos

_Acuerdos verbales con CMadrid, Bridgestone u otros stakeholders que necesitan estar por escrito._
