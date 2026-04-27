# Invariantes del sistema — Las 9 reglas no negociables

**Tipo**: arquitectura
**Fecha**: 2026-04-28

> Estas son las **9 invariantes** que no se rompen jamás. Si una decisión técnica las pone en riesgo, la decisión se revierte — no la invariante.

---

## 1. Idempotencia

Cualquier endpoint o job se puede llamar N veces con el mismo input y produce el mismo resultado. No hay efectos acumulativos por re-ejecución.

**Por qué**: BullMQ reintenta jobs. Webfleet puede mandar el mismo evento dos veces. CI puede correr la misma migración dos veces. Si no es idempotente, los datos se corrompen silenciosamente.

## 2. Reproducibilidad

Dado el mismo input + mismos criterios + mismo dataset, el output del scoring es **bit-a-bit idéntico**, hoy o dentro de 5 años.

**Por qué**: GDPR art. 22 obliga a poder explicar la decisión al candidato. Si no podemos reproducir el cálculo, no podemos defenderlo.

## 3. Inmutabilidad del attempt cerrado

Un `attempt` cerrado **no se modifica jamás**. Ni puntuación, ni timestamps, ni metadatos. Si hay que rehacer, se crea uno nuevo y se referencia al anterior.

**Por qué**: la oposición exige trazabilidad legal. Modificar un attempt cerrado es manipular evidencia.

## 4. Versionado pinned al CREAR

Cuando un `attempt` se crea, se hace **snapshot del `criteria_version` vigente**. Si los criterios cambian después, ese attempt se sigue evaluando con la versión vieja.

**Por qué**: equidad legal. Si cambiamos criterios a mitad de convocatoria, los candidatos que ya hicieron attempts no pueden ser evaluados con criterios distintos a los que regían cuando hicieron la prueba.

## 5. `source` y `confidence` ortogonales

Cada dato persistido lleva DOS metadatos:
- `source`: de dónde viene (sensor IMU, GPS, Webfleet, manual)
- `confidence`: cuán fiable es (0-1, basado en redundancia o validación)

Son **independientes**: un dato de Webfleet puede tener confidence 1.0 si está validado contra GPS, o 0.3 si llega solo y huele raro.

**Por qué**: el scoring tiene que poder degradar elegantemente cuando una fuente falla. Sin esto, una caída de Webfleet hace que todo el sistema parezca inútil aunque tengamos GPS+IMU.

## 6. Inmutabilidad del ranking

Una vez calculado el ranking de cierre, no se recalcula. Si llegan datos tardíos, se ignoran o se procesan en una nueva convocatoria.

**Por qué**: la decisión APTO/NO_APTO se comunica oficialmente. Recalcular invalidaría comunicaciones legales ya hechas.

## 7. Decisión solo al cierre

El sistema **NO evalúa APTO/NO_APTO durante el proceso**. Solo calcula scores. La decisión binaria sale al cerrar la convocatoria.

**Por qué**: legal. La administración no puede comunicar resultados parciales en una oposición pública.

## 8. Doble validación + acta SHA256

El cierre de convocatoria requiere **dos validaciones humanas independientes** y produce un **acta firmada con SHA256** del ranking + criterios + dataset.

**Por qué**: equivalente al "doble llave" de procesos críticos. Y el acta hash es prueba criptográfica para impugnaciones.

## 9. `criteria_version` pinned al CREAR (no al evaluar)

(Refuerzo de la #4): el pin pasa al **crear** el attempt, no al evaluar. Esto evita que un cambio de criterios entre creación y evaluación afecte al cálculo.

**Por qué**: si se pinea al evaluar, hay una ventana de tiempo entre que se crea el attempt y se procesa donde un cambio de criterios afecta al resultado. Pinear al crear cierra esa ventana.

---

## Cómo aplicar

- Si una PR pone en riesgo una invariante, **se bloquea**, no se discute.
- Si querés cuestionar una invariante, abrí un issue con etiqueta `cuestionar-invariante` — se discute con Antonio + el dueño técnico del área afectada.
- En code review, mencionar explícitamente cuál invariante está protegiendo el cambio.

## Dónde aplica

- `packages/scoring/` — invariantes 2, 4, 9
- `apps/api/src/services/attempts/` — invariantes 1, 3, 4, 9
- `apps/api/src/routes/close.*` — invariantes 6, 7, 8
- `apps/worker/src/jobs/webfleetSync.ts` — invariantes 1, 5
- `prisma/schema.prisma` — invariantes 3, 4 (campos `closed_at`, `criteria_version`)
