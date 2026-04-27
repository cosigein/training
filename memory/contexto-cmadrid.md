# Contexto del cliente — CMadrid

**Tipo**: contexto
**Fecha**: 2026-04-28

## Qué es Training

Sistema de **evaluación de candidatos a conductor de camión de bomberos** para la **Comunidad de Madrid**, dentro de una **oposición pública**.

## Modelo de oposición pública (CRÍTICO)

Esto cambia decisiones técnicas profundas. Si no lo entendés, vas a diseñar mal:

1. **Plazas limitadas y conocidas de antemano.** Por ejemplo: 12 plazas, 240 candidatos.
2. **Ranking acumulado.** Cada candidato hace varios `attempt`. El ranking se calcula sobre el agregado, no sobre el último.
3. **Decisión APTO / NO_APTO solo al cierre de convocatoria.** No durante. Esto es legal, no técnico — la administración no puede comunicar el resultado antes de cerrar el proceso.
4. **Sistema 100% automático.** El manager **solo lee**, no decide nada. La decisión la hace la máquina con criterios pinned.
5. **Alumno puede pedir auditoría.** Si un candidato pide revisión humana (GDPR art. 22), hay que poder reconstruir exactamente cómo se calculó su scoring con los criterios del momento del attempt.

## Por qué importa al código

- **Inmutabilidad del attempt cerrado** — una vez cerrado, no se modifica jamás.
- **Versionado pinned al CREAR** — los criterios de scoring se snapshot al crear el attempt, no al evaluarlo. Si cambian a mitad de convocatoria, los attempts viejos se evalúan con los criterios viejos.
- **Doble validación + acta SHA256** — el cierre de convocatoria firma criptográficamente el ranking final.
- **Reproducibilidad** — todo cálculo tiene que ser reproducible años después con los mismos inputs.

Para el detalle, ver [`arquitectura-invariantes.md`](arquitectura-invariantes.md).

## Calendario

- **Demo del sistema funcionando**: 11/05/2026
- **Sprint de implementación**: 14 días (hasta la demo)
- Equipo de 4 personas trabajando desde Córdoba

## Comunicación con CMadrid

- **Único canal**: Antonio Hermoso.
- Nadie del equipo escribe, llama o presenta directamente al cliente.
- Si el cliente pide algo "rápido" en chat al equipo (ej. WhatsApp), redirigir a Antonio.

## Stakeholders externos relevantes

- **CMadrid (Bomberos)** — cliente final.
- **Bridgestone (Webfleet)** — proveedor de telemetría de la flota. Acceso vía API ya autorizado para el sprint.

## Dónde aplica

A todo el sistema, especialmente:
- Scoring engine (`packages/scoring/`)
- Endpoints de cierre (`apps/api/src/routes/close.*`)
- Lógica de attempts (`apps/api/src/services/attempts/`)
- Auditoría (`apps/api/src/routes/gdpr.*`, `/admin/*`)

## Aprendido

Si en cualquier momento alguien sugiere "que el manager apruebe manualmente", **eso rompe el modelo**. El sistema es 100% automático por diseño legal y técnico. El manager **solo consulta**.
