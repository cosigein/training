# Modelo de oposición pública

**Tipo**: contexto
**Fecha**: 2026-04-28

## Qué

Una **oposición pública española** es un proceso administrativo regulado por la Ley 39/2015 (LPACAP) en el que la administración selecciona a sus empleados públicos siguiendo principios de **igualdad, mérito y capacidad** (art. 103.3 Constitución).

Lo que distingue una oposición de un proceso de selección normal:

1. **Plazas limitadas y conocidas de antemano.** Se publican en el BOE/BOCM antes del proceso.
2. **Ranking acumulado.** El candidato no aprueba o suspende — saca una **nota**, y la nota se compara con las de los demás. Solo entran los N mejores (donde N = número de plazas).
3. **Criterios públicos e inmutables durante el proceso.** Una vez convocada, no se pueden cambiar las reglas a mitad. Si se cambian, hay que repetir el proceso.
4. **Decisión solo al cierre.** Hasta que termina la última prueba, **nadie tiene la plaza**, aunque vaya el primero por mucho margen.

## Por qué importa al sistema

Estas características no son adornos — **son la razón de que el código se diseñe como se diseña**:

| Característica del proceso | Invariante técnica que la implementa |
|---|---|
| Criterios inmutables durante el proceso | Invariante #4: `criteria_version` pinned al crear |
| Decisión solo al cierre | Invariante #7: el sistema solo calcula scores, no APTO/NO_APTO |
| Trazabilidad legal | Invariante #2: reproducibilidad bit-a-bit |
| Ranking final firmado | Invariante #8: doble validación + acta SHA256 |
| Derecho a revisión humana (GDPR art. 22) | Endpoint `/gdpr/audit` que reconstruye el cálculo del attempt |

Ver [`arquitectura-invariantes.md`](arquitectura-invariantes.md) para el detalle de las 9 invariantes.

## El "pero" del manager

Mucha gente del equipo va a tener la tentación natural de pensar:

> *"¿Y si el manager puede aprobar manualmente al final?"*

**No.** El manager **lee y consulta**, no decide. La decisión la toma el sistema con criterios pinned. Si el manager pudiera aprobar manualmente:

- Rompe la igualdad: dos candidatos con el mismo score, distinto trato.
- Rompe el GDPR art. 22: la decisión deja de ser "automática" pero tampoco es "humana revisada con criterios públicos".
- Es legalmente impugnable: cualquier candidato no admitido puede pedir el algoritmo y demostrar que se aplicó arbitrariamente.

El **único punto humano** del sistema es:

1. La **doble validación al cierre** — dos personas confirman que el cálculo final es el correcto. No deciden quién entra; solo firman que el algoritmo se aplicó bien.
2. La **auditoría a petición del candidato** (GDPR) — un humano explica al candidato por qué su score fue X. No cambia el resultado; solo lo justifica.

## Dónde aplica

- A todo el sistema. Si una decisión técnica entra en conflicto con esto, gana esto.
- Particularmente al diseño de:
  - Pantallas de manager (solo lectura, sin botones de decisión sobre candidatos)
  - Endpoint de cierre (`apps/api/src/routes/close.*`)
  - Auditoría GDPR (`apps/api/src/routes/gdpr.*`)

## Aprendido

- Si alguien pregunta "¿pero y si el cliente quiere…?" la respuesta es: el cliente **es la administración pública**. Lo que pueda querer está acotado por la ley. No le podemos dar herramientas para violarla.
- Esto NO es un sistema de RRHH. Es un sistema de oposición pública. Distinto contexto legal.

## Referencias legales

- Constitución española, art. 103.3 (mérito y capacidad)
- Ley 39/2015 LPACAP — procedimiento administrativo común
- RGPD art. 22 — derecho a no ser sometido a decisiones automatizadas sin revisión humana
