# Decisión D-MT-001 — Multi-turno confirmado

**Tipo**: decision
**Fecha**: 2026-04-24

## Qué

El sistema soporta **múltiples convocatorias en paralelo** (multi-turno). Una convocatoria es un proceso de oposición independiente: criterios pinned propios, ranking propio, cierre propio.

## Por qué

CMadrid no hace una sola oposición al año. Pueden tener:
- Una convocatoria de bomberos conductores en abril.
- Otra de bomberos especialistas en junio.
- Otra de relevo de plantilla en septiembre.

Si modeláramos una sola convocatoria global, el sistema sería **monouso** — útil para esta demo, inútil después. Multi-turno es lo que hace que la herramienta valga más allá del piloto.

## Dónde aplica

- `prisma/schema.prisma` — modelo `Convocatoria` (o equivalente) con FK desde `Attempt`, `CriteriaVersion`, `Candidate`
- Todos los endpoints de close, ranking, scoring tienen que aceptar `convocatoriaId` como parámetro
- Pantallas admin: selector de convocatoria activa visible en todo momento

## Cómo aplicarlo

- **Cada `Attempt` pertenece a UNA `Convocatoria`** — no se mueven entre convocatorias.
- **Cada `Convocatoria` tiene su propia `criteria_version` pinned**. No se comparten criterios entre convocatorias salvo que se elija explícitamente al crearla.
- **El cierre se hace por convocatoria**, no global. Cada acta SHA256 firma una convocatoria.
- **El ranking se calcula por convocatoria**. Un candidato puede estar en varias.

## Aprendido

- Multi-turno **NO es multi-tenant**. Una convocatoria es un proceso dentro de la misma organización (CMadrid). Multi-tenant sería separar CMadrid de otra ciudad — eso lo hace el sistema padre, no esta capa.
- El tipo de relación más correcto: `Organization 1—* Convocatoria 1—* Attempt`.

## Cuándo se invalidaría

Si CMadrid solo necesitara una convocatoria por contrato y descartara el resto. No es el caso — el director técnico ya confirmó el modelo en las conversaciones previas al sprint.
