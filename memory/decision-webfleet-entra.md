# Decisión D-WF-001 — Webfleet entra al sistema

**Tipo**: decision
**Fecha**: 2026-04-24

## Qué

Integramos **Webfleet de Bridgestone** como fuente externa de telemetría para complementar los datos de los sensores propios.

## Por qué

CMadrid ya paga Webfleet para su flota de bomberos. Ignorarlo y depender solo de nuestros sensores sería:

- **Costoso operativamente**: instalar y mantener nuestro hardware en cada vehículo cuando ya hay otro reportando.
- **Frágil técnicamente**: una sola fuente. Si nuestro IMU falla, perdemos telemetría — con Webfleet de respaldo, degradamos elegantemente.
- **Comercialmente raro**: el cliente preguntaría por qué duplicamos algo que ya tiene.

## Dónde aplica

- `packages/ingestion/webfleet/` — cliente HTTP + normalizer + sync service + event mapper
- `apps/worker/src/jobs/webfleetSync.ts` — orquestación con BullMQ
- `prisma/schema.prisma` — tabla `SessionExternalEvent`
- Ver detalle técnico: [`docs/PAPER-MAESTRO-TRAINING-V6.md`](../docs/PAPER-MAESTRO-TRAINING-V6.md) §A6 (Plan de Migración v2)

## Cómo aplicarlo

- **4 capas obligatorias**: Client / Normalizer / SyncService / EventMapper. No mezclar.
- **Cuota**: 14.400 requests/día. Umbrales en Redis con alertas a 70%, 85%, 95%.
- **Circuit breaker** en el client. Si Webfleet cae, se degrada a sensores propios sin caer todo el sistema.
- Los datos de Webfleet llegan con `source = 'webfleet'` y `confidence` calculado contra GPS + IMU (ver invariante #5 en [`arquitectura-invariantes.md`](arquitectura-invariantes.md)).

## Aprendido / AVISOS

- **El usuario CMadrid en Webfleet tiene una tilde en el nombre.** URL encoding UTF-8 obligatorio. Si pasás el username como string sin encodear, el API responde 401 sin pista del por qué.
- **Acceso ya autorizado por Bridgestone para el sprint** — coordinación informal, ver acuerdo con Antonio.

## Cuándo se invalidaría

Si Bridgestone cambia su modelo de licencia o cierra el API público, habría que reevaluar. No es probable en el horizonte del sprint.
