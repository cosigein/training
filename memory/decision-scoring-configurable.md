# Decisión D-SCR-001 — Scoring continuo y configurable

**Tipo**: decision
**Fecha**: 2026-04-24

## Qué

El scoring es **continuo de 0 a 100** (no por categorías), con **un punto de corte único** para la decisión APTO/NO_APTO al cierre. La fórmula tiene **4 familias de variables ponderables y configurables**.

## Por qué

CMadrid pidió el sistema, pero la fórmula exacta de scoring **NO la define el cliente al detalle**. La definimos nosotros, con la condición de que sea:
- **Configurable** (sin recompilar) para poder ajustar pesos durante el piloto.
- **Versionada y pinned al crear el attempt** (invariante #4).
- **Defendible** ante una auditoría: cada variable tiene unidades, fuente, y rango razonable.

Scoring por categorías (APTO en cada cosa por separado) lo descartamos porque sufre el problema clásico: un candidato regular en todo gana al excelente con una flaqueza puntual. Eso no es lo que queremos premiar para conducir un camión de bomberos.

## Las 4 familias

| Familia | Peso por defecto | De qué se nutre |
|---|---:|---|
| **Estabilidad** | 40% | IMU (acelerómetro, giroscopio), eventos de inestabilidad detectados |
| **Velocidad** | 30% | GPS + Webfleet, contraste con límites de vía |
| **Ruta** | 15% | GPS + map-matching, desviaciones, tiempos de tramo |
| **Conducción** | 15% | Frenazos, aceleraciones bruscas, comportamiento general |

**Total: 100%**. Los pesos son configurables — pero la suma siempre 100.

## Dónde aplica

- `packages/scoring/` — engine completo
- `apps/api/src/routes/scoring.simulate.ts` — endpoint de simulación (Antonio)
- `apps/web/src/pages/admin/ScoringSimulator.tsx` — pantalla admin (Antonio)
- `prisma/schema.prisma` — modelo `CriteriaVersion` con los 17 campos configurables

## Cómo aplicarlo

- **17 campos configurables** distribuidos en las 4 familias. Detalle en [`docs/PAPER-MAESTRO-TRAINING-V6.md`](../docs/PAPER-MAESTRO-TRAINING-V6.md) §Scoring Spec v1.
- **Versionado inmutable**: cada cambio de configuración crea un `CriteriaVersion` nuevo. Los anteriores nunca se borran.
- **Pin al CREAR** el attempt (invariante #4). Si se cambia mitad sprint, los attempts viejos se evalúan con la versión vieja.
- **Punto de corte**: un único umbral 0-100 que separa APTO de NO_APTO. Lo define CMadrid al cierre — antes solo se calcula el score.

## Aprendido

- La idea inicial era "el cliente nos dice la fórmula". **No la sabe**, y es razonable que no la sepa — por eso nos contratan.
- La pregunta que hace la decisión clara: "¿este sistema sirve si el cliente cambia los pesos mañana?" Si sí, está bien diseñado.

## Cuándo se invalidaría

Si CMadrid presenta una fórmula oficial impuesta por normativa estatal de oposiciones de bomberos. No existe a fecha de hoy. Si apareciera, el sistema versionado nos permite migrar sin perder data.
