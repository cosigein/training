# Memo interno — Dirección

**Para:** Dirección · Antonio Hermoso (firma)
**De:** Antonio Hermoso · Director técnico
**Fecha:** 27 de abril de 2026
**Asunto:** Sprint Training (CMadrid) · 14 días, demo 11/05 — caso de negocio

> ⚠️ **Este documento es estrictamente interno.** No se comparte con CMadrid, no se sube como adjunto a propuesta comercial, no circula fuera de Dirección. La propuesta hacia el cliente es `PROPUESTA-COMERCIAL.md`. La visión funcional es `DOCUMENTO-EJECUTIVO.md`.

---

## 1. Por qué arrancamos el sprint mañana

Modelo de oposición pública para CMadrid (cuerpo de bomberos, ~265 candidatos por convocatoria). Es:
- Un caso de uso **acotado** (no es un producto genérico).
- Un cliente **público y solvente** (cuerpo de bomberos de la Comunidad de Madrid).
- Una entrada a un mercado **replicable** (ver §6).

La demo del 11/05 es la palanca para firmar contrato. Sin demo no hay firma; sin firma no hay ingresos.

## 2. Estado contractual con CMadrid (HOY)

> 🚧 *Sección a completar antes de mandar este memo a Dirección. Las preguntas son las que la Dirección va a hacer.*

| Pregunta | Estado actual |
|---|---|
| ¿Hay carta de intenciones firmada? | __PENDIENTE — Antonio confirma__ |
| ¿Hay propuesta económica entregada? | NO. Se entrega esta semana junto con la demo. |
| ¿Hay acuerdo verbal de adjudicación condicional al éxito de la demo? | __PENDIENTE — Antonio confirma__ |
| ¿Hay contrato marco de DobackSoft con CMadrid sobre el que apoyarse? | __PENDIENTE — Antonio confirma__ |
| ¿Cuál es el riesgo de que CMadrid no firme tras la demo? | Medio. Sin firma, lo construido queda como base reutilizable (ver §5). |

## 3. Coste interno del compromiso

| Concepto | Cálculo | Coste |
|---|---|---|
| Sprint (14 días naturales, ~9 días laborables efectivos por persona, 4 personas) | 9 × 4 = **36 días-hombre** | __COMPLETAR__ |
| Fase 2 (mayo–julio 2026, ~8 semanas con dedicación parcial) | 4 × 8 × 0.6 = **~19 semanas-hombre** equivalente | __COMPLETAR__ |
| Hardware Doback Elite (X dispositivos) + instalación | __COMPLETAR__ | __COMPLETAR__ |
| Infraestructura (VPS staging + producción · 12 meses) | __COMPLETAR__ | __COMPLETAR__ |
| Coste de oportunidad: lo que el equipo NO está haciendo | __COMPLETAR — qué se pausa__ | __COMPLETAR__ |
| **TOTAL estimado pre-firma** | | **__COMPLETAR__** |

## 4. Modelo de ingresos propuesto a CMadrid

Detalle completo en `PROPUESTA-COMERCIAL.md` §8.bis.1. Resumen:

```
   1. SETUP INICIAL (pago único)
      Hito 1: __COMPLETAR €__ a la firma del contrato.
      Hito 2: __COMPLETAR €__ tras cutover validado.

   2. SUSCRIPCIÓN MENSUAL
      __COMPLETAR €/mes__ (mantenimiento + soporte L-V 09:00-18:30 + backups + cron ranking).

   3. POR CONVOCATORIA REAL CERRADA
      __COMPLETAR €/convocatoria__ (cuota Webfleet + storage 12m + acta firmada).
```

> Importes a cerrar bilateralmente entre el 11/05 y la firma. El jefe de bomberos de CMadrid (en el otro lado) ya avisó: sin cifras concretas no entra en Intervención. **Hay que llegar a la reunión del 11/05 con un rango propuesto.**

## 5. Plan B si CMadrid no firma

Lo que NO se pierde:
- **Código del sistema** queda en el repo `cosigein/training`. Reutilizable para otros cuerpos (Barcelona, Valencia, Sevilla, parques provinciales — ver §6).
- **Conocimiento de dominio** (modelo de oposición, GDPR, recurso administrativo) → IP de la empresa.
- **Webfleet integration** → reutilizable en el resto del producto DobackSoft (clientes que usan Webfleet en flota general).

Lo que SÍ se pierde:
- 36 días-hombre + hardware Doback Elite preparado para CMadrid.
- Tiempo del director técnico durante el sprint.

**Punto de no retorno:** si no hay carta de intenciones firmada antes del 04/05 (semana de la demo), considerar pausar Fase 2 hasta tener compromiso por escrito.

## 6. Pipeline comercial — ¿es replicable?

Sí, en otros cuerpos de bomberos públicos españoles que usen oposición:
- Madrid (CMadrid) — actual.
- Cataluña (Bombers Generalitat).
- Comunidad Valenciana.
- País Vasco (SUF).
- Andalucía (Junta).
- Cuerpos provinciales (Diputaciones).

Cada uno con su propia convocatoria, calendario y reglas — pero el **mismo modelo de oposición** y misma plataforma. Una vez validado con CMadrid, el ciclo de venta se acorta.

**Mercado adyacente:** otros cuerpos de seguridad pública (policía local con vehículos, ambulancias, ITV) con la misma necesidad de evaluación trazable.

## 7. Riesgos legales — exposición de la empresa

| Riesgo | Mitigación actual | Acción pendiente |
|---|---|---|
| Recurso administrativo de candidato impugnando un cierre | Versionado inmutable + acta SHA256 + audit log + revisión humana significativa al cierre (GDPR art. 22 cubierto) | Validar con asesor legal de CMadrid + redactar cláusula de responsabilidad en contrato |
| Responsabilidad civil si el sistema falla durante una convocatoria | __PENDIENTE — confirmar póliza RC profesional__ | Contratar / extender RC antes de Fase 3 |
| Acuerdo Bridgestone (Webfleet) | __PENDIENTE — verificar contrato existente o negociar__ | Cerrar acuerdo escrito antes del cutover |
| GDPR: somos Data Processor de datos sensibles (geolocalización + evaluación profesional) | DPA estándar + cláusulas en contrato | DPO de CMadrid debe firmar antes del 11/05 |
| Bus factor del equipo | 4 personas, plan de contingencia documentado, code escrow | Documentar reemplazo si Antonio o Jesús caen |

## 8. Plan de contingencia — bus factor

Equipo de 4 sin redundancia real. Si cae uno:

| Persona | Cae enfermo 3-5 días | Cae 1-2 semanas |
|---|---|---|
| **Antonio** | Equipo sigue, comunicación con cliente pausa | Detener proyecto, escalar a Dirección. CMadrid se notifica. |
| **Jesús** | Sprint tambalea pero sigue | Detener Fase 2, replanificar |
| **Alejandro** | Sprint sigue, Antonio cubre frontend mínimo | Contratar freelance React 1 mes |
| **Joel** | Tests se pausan, demo viable | QA externalizado para validar antes del cutover |

## 9. Decisiones que necesito de Dirección antes del kickoff de mañana

1. ✅ / ❌ **Aprobar arranque del sprint** asumiendo el coste de §3.
2. **Importes para los 3 componentes del modelo económico** (§4) — al menos un rango.
3. **Confirmar póliza RC profesional** o disparar contratación.
4. **Confirmar acuerdo con Bridgestone (Webfleet)** o disparar negociación.
5. **Decidir si proseguimos con Fase 2 si CMadrid no ha firmado carta de intenciones para el 04/05** o esperamos compromiso.

## 10. Reunión propuesta

**Hoy lunes 27/04, 30 minutos antes del kickoff de mañana.**
- Antonio expone los 5 puntos del §9.
- Dirección decide go / no-go con condiciones.

Si la reunión no sucede hoy, se asume **go default** y los puntos del §9 se completan por escrito durante la primera semana del sprint.

---

**Antonio Hermoso · Director técnico**
27 de abril de 2026
