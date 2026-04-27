# Training
## Documento ejecutivo — qué es, cómo funciona, qué entrega

---

| | |
|---|---|
| **Versión** | 4.0 |
| **Fecha** | 27 de abril de 2026 |
| **Audiencia** | Cliente (CMadrid) · Equipo de gestión interno (no técnico) |
| **Carácter** | No técnico — orientado a uso real |
| **Estado del proyecto al 27/04/2026** | Documento de **propuesta y diseño**. El código aún no está construido: el sprint de implementación arranca el martes 28/04 y la demo está programada para el lunes 11/05. Cifras económicas, SLA y plazos del plan de despliegue son **propuestas de partida** sujetas a contrato. |
| **Para Dirección de la empresa** | El caso de negocio (coste interno, modelo económico, exit plan, plan de contingencia, exposición legal) está en `MEMO-DIRECCION-INTERNO.md` — documento separado por confidencialidad. |
| **Cambio principal v3 → v4** | Tras review adversarial, se incorporan al documento aspectos legales y operativos críticos para producción: privacidad y GDPR, cierre de convocatoria con acta y doble validación, derecho de recurso del candidato, sistema de notificaciones, redundancia de captura de datos. Nada de esto cambia el modelo del sistema — son refinamientos que el cliente y la dirección deben conocer antes de la reunión. |

---

## Tabla de contenidos

1. Qué es Training
2. Cómo funciona — visión general
3. El modelo de evaluación: oposición, no examen escolar
4. Qué ve cada usuario
5. Qué decide el sistema y qué no
6. Cómo se calcula el resultado
7. Ejemplos reales
8. Privacidad y datos personales (GDPR)
9. Cierre de convocatoria — proceso reforzado
10. Recursos y derechos del candidato
11. Notificaciones automáticas
12. Realidad del sistema — sin maquillaje
13. El equipo — quién hace qué
14. Estado actual y siguientes pasos

---

# 1. Qué es Training

Training es un sistema **automático y autónomo** de evaluación competitiva de conducción para candidatos a conductor de camión.

A diferencia de la evaluación tradicional —basada en la observación subjetiva de un instructor— Training **mide, califica y clasifica sin intervención humana**, combinando dos fuentes de datos: el dispositivo **Doback Elite** instalado en el camión y la plataforma **Webfleet** del cliente.

Lo importante: Training **no decide individualmente** si un candidato es apto. Genera una **nota por cada ruta** y un **puesto en el ranking acumulado** de la convocatoria. La decisión apto / no apto se emite al cierre de la convocatoria, en función del puesto final y del número de plazas disponibles.

```
        ┌──────────────────────────────────────┐
        │                                      │
        │   El alumno conduce una ruta real    │
        │            ↓                         │
        │   El sistema mide y le pone NOTA     │
        │            ↓                         │
        │   La nota actualiza el RANKING de    │
        │   toda la convocatoria               │
        │            ↓                         │
        │   Al cierre, los X primeros del      │
        │   ranking obtienen plaza             │
        │                                      │
        └──────────────────────────────────────┘
```

El responsable existe en el sistema como **revisor de información**, no como juez. Ve la matriz, el ranking, los detalles. Pero **no califica, no modifica y no sobreescribe**.

**A quién sirve:**

- Cuerpos de bomberos que evalúan candidatos a conductor en procesos de oposición pública.
- En este momento: **CMadrid (Comunidad de Madrid)**, con unos 265 candidatos compitiendo por un número fijo de plazas.

**Qué problema resuelve:**

- Hacer la evaluación de oposiciones **objetiva, consistente y trazable**.
- Generar un **ranking en tiempo casi real** que el cliente pidió expresamente.
- Procesar convocatorias grandes sin cuello de botella humano.
- Generar evidencia objetiva para reclamaciones, auditorías y procesos legales.

---

# 2. Cómo funciona — visión general

El proceso completo, desde que un alumno se sube al camión hasta que conoce su puesto, sigue siempre los mismos pasos.

### Paso 1 — El alumno se identifica y selecciona ruta

Pasa su tarjeta personal por el lector de la cabina. El sistema lo reconoce. Selecciona qué ruta va a hacer.

> Esta es **la única interacción humana** durante el proceso. Todo lo posterior es automático.

### Paso 2 — El alumno conduce

Mientras conduce, dos fuentes registran información en paralelo:

- **Doback Elite**, el dispositivo propio instalado en cada camión, registra los movimientos físicos del vehículo y aporta GPS propio como redundancia.
- **Webfleet**, la plataforma de gestión de flotas que CMadrid tiene contratada con Bridgestone, aporta posición GPS, velocidad, eventos de comportamiento de conducción y KPIs configurables.

### Paso 3 — El intento se cierra

Cuando termina la ruta —o cuando otro alumno pasa su tarjeta— el intento se cierra automáticamente.

### Paso 4 — El sistema procesa (automático)

Sin intervención humana, el sistema limpia los datos, identifica eventos relevantes, calcula la **nota** entre 0 y 10 según las reglas configuradas por el cliente, y genera la explicación granular.

### Paso 5 — El intento queda fijado

Su nota es final. **No hay decisión apto / no apto en este punto** — solo nota.

### Paso 6 — El ranking se actualiza (a la mañana siguiente)

Cada noche, el sistema recalcula el ranking de la convocatoria. A las 6:00 AM del día siguiente, el ranking actualizado está publicado.

### Paso 7 — El alumno consulta

El alumno entra a su portal y ve su nota, su puesto, si está dentro o fuera del corte provisional, y el detalle pedagógico de cada intento.

> Si discrepa con un resultado, **puede solicitar formalmente una auditoría** desde su portal. Es un derecho reconocido. La sección 10 detalla cómo.

### Paso 8 — Cierre de la convocatoria (proceso formal con acta)

Cuando llega la fecha publicada, **dos administradores distintos** deben confirmar el cierre. El sistema genera un **acta PDF con sello de integridad SHA256** que contiene el ranking final, los aptos y los no aptos. Solo entonces se emiten las decisiones APTO / NO_APTO. La **firma digital cualificada** del acta (eIDAS / FirmaProfesional) se incorpora en Fase 2 antes del cutover real.

> Detalle del proceso de cierre en sección 9.

---

# 3. El modelo de evaluación: oposición, no examen escolar

Training **no es un examen del carnet de conducir** (donde sacás 7+ y aprobás). Es una **OPOSICIÓN PÚBLICA**: hay un número fijo de plazas, los candidatos compiten entre sí, y entran los mejores.

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   El sistema NO emite "apto/no apto" por ruta.       │
   │                                                      │
   │   El sistema emite UNA NOTA por ruta.                │
   │   El sistema mantiene UN RANKING acumulado.          │
   │   La decisión APTO/NO_APTO se emite AL CIERRE        │
   │     de la convocatoria, según ranking final          │
   │     y número de plazas publicado.                    │
   │                                                      │
   │   Las notas son INMUTABLES.                          │
   │   El ranking es PROVISIONAL hasta el cierre.         │
   │   Al cierre, todo queda DEFINITIVO.                  │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

## 3.1 Cómo se construye el ranking

| Elemento | Decisión |
|---|---|
| **Cómo se combinan las notas** | Media simple de las rutas completadas. |
| **Pesos por ruta** | En V1 todas las rutas pesan igual. El sistema está preparado para pesos diferentes en V2. |
| **Ruta no completada por el candidato** | Cuenta como 0. |
| **Ruta abortada por fallo técnico** | NO cuenta. Admin marca el caso. |
| **Plazas** | Número entero fijo, decidido por el cliente al crear la convocatoria, público desde el día 1. |
| **Empates** | Cascada de 4 criterios, auditable. |

## 3.2 Cuándo se actualiza el ranking

El ranking se recalcula **una vez al día, a las 6:00 AM**. La razón: actualizaciones en tiempo real generan ansiedad sin información útil. Una actualización diaria es viva y estable a la vez.

## 3.3 Qué ve el alumno

```
   ┌────────────────────────────────────────────────────┐
   │   TU PROGRESO EN LA CONVOCATORIA 2026-A            │
   │                                                    │
   │   Rutas completadas: 3 de 4                        │
   │   Tu nota media:     7.4 / 10                      │
   │                                                    │
   │   Tu puesto provisional: 74 de 200                 │
   │   Plazas: 50                                       │
   │                                                    │
   │   ▲ Estás DENTRO del corte provisional             │
   │     (provisional — el ranking final solo se        │
   │      conoce al cierre de la convocatoria)          │
   └────────────────────────────────────────────────────┘
```

Lo que sí ve: su puesto, total de plazas, nota media, dentro/fuera del corte. Lo que no ve: umbral numérico exacto, notas/nombres de otros candidatos. Mostrar el umbral genera falsa seguridad o alarma — "dentro / fuera del corte provisional" es informativo y honesto.

---

# 4. Qué ve cada usuario

## 4.1 El alumno

- **Dashboard de rutas**, su progreso en la convocatoria, historial completo, detalle pedagógico de cada intento, evolución cualitativa.
- **Solicitud de auditoría** si discrepa con un resultado concreto.
- **Solicitud de export de sus datos personales** (derecho GDPR — sección 8).

**No ve** datos crudos, gráficas técnicas, su nota mientras conduce, ni los puestos / notas de otros candidatos.

## 4.2 El responsable / instructor

**Su rol es de consulta, no de decisión.** Lo que ve:

- **El ranking de la convocatoria** completo.
- **La matriz** (alumnos × rutas).
- **Filtros e indicadores de atención** (alumnos en riesgo, intentos pendientes de auditoría).
- **Detalle de cada intento**: mapa, eventos, desglose granular del cálculo.
- **Solicitudes de auditoría** que los alumnos hayan presentado.

**No califica, no modifica, no sobreescribe.** Su única intervención es **resolver auditorías** cuando los alumnos las solicitan. Frecuencia esperada: <1% de los intentos.

## 4.3 El administrador

Configura el sistema:

- **Convocatorias**: crear, definir fecha de cierre, número de plazas, ruta principal de desempate.
- **Cierre de convocatoria**: proceso formal de tres pasos con doble validación (sección 9).
- **Rutas, RFID, kioskos, usuarios**.
- **Reglas de evaluación**: ver la versión activa, consultar versiones anteriores.
- **Simulador**: prueba cualquier cambio sin tocar producción.
- **Solicitudes GDPR**: gestiona exportes de datos y peticiones de borrado de candidatos.

## 4.4 La cabina del camión (kiosko)

Pantalla simple, estrictamente operativa. Sin teclado, modo oscuro permanente, funciona sin conexión, **nunca muestra notas**.

---

# 5. Qué decide el sistema y qué no

## 5.1 Lo que el sistema NO decide

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   El sistema NO decide:                              │
   │     ▶ Qué umbrales aplican                           │
   │     ▶ Cuántos puntos vale cada infracción            │
   │     ▶ Cuántas plazas hay disponibles                 │
   │     ▶ Qué peso tiene cada familia                    │
   │                                                      │
   │   Esas decisiones son del CLIENTE.                   │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

## 5.2 Lo que el sistema SÍ hace — autónomamente

Una vez configuradas las reglas, **el sistema actúa solo**: captura datos, aplica reglas, calcula nota, actualiza ranking, emite la decisión APTO / NO_APTO al cierre de la convocatoria.

Como elementos de calidad y trazabilidad: versionado inmutable de reglas, auditoría por intento, trazabilidad granular de cada penalización.

## 5.3 Simulador — la pieza clave para el cliente

El **simulador** permite tomar una versión de reglas, modificar parámetros, aplicarla a la convocatoria completa y ver el resultado: cuántos candidatos se mueven en el ranking, cuántos cruzan el corte. **Todo sin tocar nada en producción.**

> Esto le permite al cliente preguntar: *"¿qué pasa si subo el umbral de exceso de velocidad de 10 a 15 km/h? ¿quién entraría que ahora no entra?"* — y verlo de un vistazo antes de aplicarlo.

---

# 6. Cómo se calcula el resultado

Cuatro etapas, todas automáticas:

1. **Captura**: Doback Elite + Webfleet generan datos en paralelo.
2. **Detección de eventos**: el sistema identifica frenadas bruscas, excesos, desviaciones, aceleraciones laterales. Cada evento queda marcado con tipo, momento, fuente y nivel de confianza.
3. **Cálculo de la nota del intento**: aplica las reglas del cliente, calcula entre 0 y 10, genera explicación granular regla por regla.
4. **Actualización del ranking** (nocturna): recalcula la nota media de cada candidato, reordena, aplica desempates, determina el corte provisional.

Al cierre formal: se calcula el ranking final una última vez, se emiten las decisiones, se genera el acta.

---

# 7. Ejemplos reales

## 7.1 Caso 1 — Buen candidato a media convocatoria

**Juan Pérez.** 3 de 4 rutas completadas. Notas: 8.8, 8.2, 7.9.

Resultado del sistema (automático): nota media 8.30. Puesto 18 de 200. Plazas: 50.

Lo que Juan ve: *"Has completado 3 de 4 rutas. Tu nota media es 8.30. Estás en el puesto 18 de 200. Plazas: 50. **Estás dentro del corte provisional.** El ranking final solo se conoce al cierre 15/06/26."*

Juan sabe que va bien. Pero si en su última ruta saca 4, su media baja y su puesto puede caer. La incertidumbre es real hasta el cierre.

## 7.2 Caso 2 — Candidato en zona de corte

**María García.** 4 de 4 rutas completadas. Nota media: 6.625. Puesto provisional: 49 de 200.

María entra por los pelos. **Pero su puesto no es definitivo**: a medida que más candidatos terminen sus rutas, su puesto puede subir o bajar. Hasta que la convocatoria no cierre, no es apta.

## 7.3 Caso 3 — Datos incompletos por fallo de Webfleet

**Pedro López.** Webfleet cayó 5 minutos en mitad de una ruta. **Doback Elite siguió capturando**, incluyendo GPS propio.

El sistema **no se paraliza**: calcula la nota con los datos disponibles, marca el intento con calidad de datos "media", y emite el resultado normal. Pedro puede solicitar una auditoría si lo considera necesario, pero el resultado se emitió y entra al ranking.

> Esto es importante para dirección y cliente: la **redundancia de Doback Elite garantiza continuidad** ante fallos puntuales de Webfleet.

---

# 8. Privacidad y datos personales (GDPR)

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   Training maneja datos personales de candidatos     │
   │   en proceso de oposición pública.                   │
   │                                                      │
   │   GDPR aplica plenamente.                            │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

## 8.1 Roles GDPR

- **Data Controller**: CMadrid (decide qué datos se procesan y para qué).
- **Data Processor**: el equipo de Training (procesamos en nombre de CMadrid).
- **DPO (Delegado de Protección de Datos)**: a confirmar con CMadrid antes del cutover a producción.

## 8.2 Política de retención

| Tipo de dato | Retención |
|---|---|
| Datos crudos del sensor (raw_samples) | 12 meses |
| Datos crudos de Webfleet | 12 meses |
| Intentos cerrados (notas, eventos, score) | Indefinido (evidencia legal de oposición pública) |
| Datos personales del candidato (nombre, DNI, email) | Mientras dure el proceso + plazos legales aplicables |
| Anonimización | Tras 5 años o cuando aplique legalmente |

## 8.3 Derechos del candidato

El sistema implementa de serie los derechos GDPR:

- **Right to access** (derecho de acceso): el candidato solicita un export completo de sus datos desde su portal. El sistema genera un ZIP con todo lo que tenemos sobre él (datos personales + intentos + samples + auditorías) y se lo entrega por email cuando está listo. La URL expira a los 7 días.
- **Right to be forgotten** (derecho al olvido): el candidato solicita borrado. **El procesamiento es manual** (administrador con justificación) y **acotado por el marco legal**: no se borra evidencia de intentos cerrados mientras la convocatoria sea legalmente cuestionable. Tras los plazos legales, se anonimiza.
- **Right to rectification**: a través del mecanismo formal de auditoría (sección 10).

## 8.4 Aviso de privacidad

Pantalla obligatoria en la inscripción del candidato. El texto se redacta conjuntamente con CMadrid (no lo inventamos nosotros).

## 8.5 Audit log de acciones sensibles

Toda acción crítica (export de datos, borrado, cambio de rol, cierre de convocatoria, reversa) queda registrada en un **audit log** con: quién actuó, cuándo, sobre qué, desde qué IP. Es trazabilidad obligatoria.

---

# 9. Cierre de convocatoria — proceso reforzado

El cierre de una convocatoria es **el acto más sensible del sistema**. Decide quién entra a trabajar como bombero. Por eso el proceso de cierre fue diseñado con varios niveles de seguridad.

## 9.1 Proceso de cierre — tres pasos obligatorios

```
   PASO 1 — PREVIEW
   ─────────────────
   Un administrador solicita un preview del cierre.
   El sistema le muestra:
     - Ranking final simulado
     - Lista de candidatos APTO (los X primeros)
     - Lista de candidatos NO_APTO
     - Advertencias (candidatos sin completar todas las rutas, etc.)
   Esto NO modifica nada. Solo lectura.

   PASO 2 — INICIO
   ────────────────
   Un administrador (#1) inicia el cierre.
   Confirma escribiendo el nombre exacto de la convocatoria.
   El estado pasa de OPEN → CLOSING.
   La convocatoria queda en estado intermedio.

   PASO 3 — CONFIRMACIÓN POR SEGUNDO ADMIN
   ───────────────────────────────────────
   Un administrador DISTINTO al primero (#2) confirma.
   El sistema VALIDA que sea una persona diferente.
   Confirma escribiendo el nombre exacto.
   El sistema entonces:
     - Calcula el ranking final
     - Genera las decisiones APTO/NO_APTO
     - Genera el ACTA PDF con hash SHA256 de integridad
     - Marca la convocatoria como CLOSED
     - Publica el resultado en el portal del alumno
       (cada candidato ve su outcome al iniciar sesión)
```

**Sobre la notificación a los candidatos:** la publicación en el portal se realiza inmediatamente al cierre. La **notificación por email automática** al conjunto de candidatos de la convocatoria (~265 en el escenario CMadrid de producción) —recordatorio activo, no esperar a que entren al portal— se entrega **en Fase 2** junto con el resto del sistema de notificaciones (sección 14.3, F1). En el cutover real con CMadrid, este sistema estará operativo antes de cerrar la primera convocatoria de producción.

**Por qué doble admin:** una sola persona escribiendo el nombre y confirmando es insuficiente para una decisión que afecta a cientos de candidatos en oposición pública. Doble validación es estándar en este tipo de procesos.

## 9.2 Acta de cierre

Al cerrar, el sistema genera automáticamente un **acta PDF** que contiene:

- Nombre de la convocatoria, fecha de cierre, plazas.
- Identidad de los dos admins involucrados.
- Ranking final completo.
- Listado de aptos con sus notas medias.
- Listado de no aptos.
- Hash SHA256 al pie del documento como huella de integridad.

El acta se guarda como **artefacto inmutable**. En **fase 2** se incorpora firma digital cualificada (FirmaProfesional o equivalente) y firma por una comisión de tres, conforme a normativa de oposiciones públicas españolas.

## 9.3 Ventana de reversa de 24 horas

Tras el cierre, hay una **ventana de 24 horas** durante la cual un super-administrador puede solicitar la reversión por error administrativo. Requiere:

- Justificación obligatoria de al menos 50 caracteres.
- Queda registrada en el audit log.

Pasadas las 24 horas, la convocatoria pasa a estado **LOCKED**: el ranking, las decisiones APTO/NO_APTO y el acta del cierre quedan inmutables. Ningún UPDATE sobre estos datos pasa, ni de admin, ni de super-admin, ni del propio sistema. **La única adición legalmente permitida tras LOCKED son las enmiendas (`OutcomeAmendment`) derivadas de un recurso administrativo resuelto por comisión externa, descrito en §10.3.** Estas enmiendas no modifican el outcome original (que queda como evidencia) sino que se agregan al expediente del candidato.

---

# 10. Recursos y derechos del candidato

## 10.1 Auditoría de un intento (durante la convocatoria abierta)

El alumno puede solicitar formalmente una auditoría de un intento concreto desde su portal. Indica qué intento y por qué. El responsable asignado revisa la información, y puede:

1. Confirmar el resultado original (auditoría queda registrada).
2. Crear una **reevaluación**: un intento nuevo vinculado al original. **El intento original no se modifica nunca**. La reevaluación reemplaza al original a efectos del ranking.

**Frecuencia esperada:** menos del 1% de los intentos. Es un derecho excepcional, no una rutina.

## 10.2 Auditoría tras el cierre (post-cierre, fase 2)

Si un alumno descubre algo después del cierre (ejemplo: detecta una incidencia que no había visto antes), **puede presentar una queja formal** a través del sistema. Esa queja:

- Se registra como evidencia.
- **NO modifica el outcome** ni el ranking final.
- Sirve como **soporte legal** si el candidato decide presentar un recurso administrativo formal.

## 10.3 Recurso del candidato sobre el ranking final

Un candidato declarado NO_APTO puede ejercer **recurso administrativo** sobre el ranking final completo (no solo sobre un intento). Esto es un derecho legal en oposiciones públicas españolas (Ley 39/2015 LPACAP).

El sistema **soportará** este proceso —en Fase 2, antes del primer cutover real con CMadrid— de la siguiente manera:

- **Plazo legal**: 30 días naturales desde la publicación oficial del ranking final (1 mes según LPACAP).
- **Procesamiento**: el recurso lo gestiona una **comisión externa** (no el administrador del sistema).
- **Exportación de evidencia**: el sistema **exportará** un paquete completo de evidencia del candidato (todos sus intentos + samples + score breakdown + criteria_version + audit logs) para que la comisión pueda revisarlo. Endpoint dedicado, autenticado.
- **Resolución del recurso**: si la comisión resuelve favorablemente al candidato, un super-administrador registra el resultado en el sistema. Esto **no reabre la convocatoria** (que sigue cerrada irrevocablemente) sino que genera un **outcome amendment** vinculado al outcome original. Ambos —original + amendment— quedan en el histórico.
- **Acta de la comisión**: el PDF firmado de la comisión se persiste con SHA256, equivalente al acta del cierre.
- **Adjudicación de plazas**: si un recurso aprueba a un candidato que originalmente fue NO_APTO, **se adjudica una plaza adicional fuera del cupo original**. Es práctica habitual en oposiciones públicas españolas y debe acordarse legalmente con CMadrid antes del cutover.

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   Línea de tiempo de un recurso administrativo:     │
   │                                                      │
   │   Día 0     Cierre + acta + LOCKED tras 24h          │
   │   Día 1-30  Plazo legal del candidato para recurrir  │
   │   Día N     Candidato presenta recurso               │
   │   Día N+x   Comisión resuelve (acta firmada)         │
   │   Día N+x+1 SUPER_ADMIN registra resolución          │
   │             en el sistema (outcome amendment)        │
   │   Convocatoria sigue LOCKED — pero ahora hay UN      │
   │   amendment para ese candidato, visible en histórico │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

> Este mecanismo se entrega plenamente operativo en Fase 2 (semana 6-8 post-demo), **antes del primer cutover real con CMadrid**. En la demo del 11/05 se explica conceptualmente; el endpoint y el modelo de amendment se implementan después.

---

# 11. Notificaciones automáticas

El sistema notifica a los actores en momentos clave del proceso. **Disponibilidad explícita por fase:**

| Quién recibe | Cuándo | Qué | Disponible en |
|---|---|---|---|
| **Manager** | Alumno solicita auditoría | Indicador en su dashboard | V1 (demo) |
| **Manager** | Alumno solicita auditoría | Email automático | **Fase 2** |
| **Alumno** | Manager resuelve su auditoría | Indicador al iniciar sesión | V1 (demo) |
| **Alumno** | Manager resuelve su auditoría | Email automático | **Fase 2** |
| **Admin** | Fecha de cierre se acerca (3 días antes) | Banner en dashboard | V1 (demo) |
| **Admin** | Fecha de cierre se acerca | Email recordatorio | **Fase 2** |
| **Admin secundario** | Admin primario inicia cierre | Indicador en dashboard | V1 (demo) |
| **Admin secundario** | Admin primario inicia cierre | Email "tienes cierre pendiente" | **Fase 2** |
| **TODOS los candidatos** | Convocatoria cerrada | Outcome publicado en portal (al iniciar sesión) | V1 (demo) |
| **TODOS los candidatos** | Convocatoria cerrada | Email automático con outcome | **Fase 2** |
| **Alumno** | Su data export está listo | Listado en panel "Mis solicitudes GDPR" del portal | V1 (demo) |
| **Alumno** | Su data export está listo | Email con link al ZIP | **Fase 2** |

**Resumen:**

- **V1 (lo que se ve en demo del 11/05):** todas las notificaciones operan dentro del portal — banners, indicadores, panels. El usuario ve su estado al iniciar sesión.
- **Fase 2 (semana 3-4 post-demo, antes del cutover real):** se incorpora la capa de email automático con SendGrid (o equivalente), templates, gestión de bounces y rate limiting. Push y SMS se exploran tras Fase 2.

> Antes del primer cutover real con CMadrid, **toda la columna "Fase 2" debe estar operativa**. No habrá cierre de convocatoria de producción sin sistema de email funcional con gestión de bounces — un email no entregado en una oposición pública puede invalidar el plazo de recurso del candidato.

---

# 12. Realidad del sistema — sin maquillaje

## 12.1 Doble fuente de datos: redundancia

**Doback Elite incluye GPS propio**, además del sensor inercial. Si Webfleet se cae, el sistema **sigue funcionando** con los datos del propio dispositivo. La redundancia degrada la riqueza de KPIs (perdemos los KPIs específicos de Webfleet) pero **no la operación**.

## 12.2 Los datos no siempre son perfectos

Cada intento lleva una etiqueta de **calidad de datos** (alta, media, baja). El sistema **detecta y comunica** las situaciones imperfectas, no las maquilla.

## 12.3 Los resultados son finales — con excepciones regladas

```
   Por defecto, las notas son DEFINITIVAS.

   El ranking es PROVISIONAL hasta el cierre de la convocatoria.
   Al cierre, queda DEFINITIVO de forma irrevocable (tras 24h).

   Excepciones al carácter definitivo:
     - Auditoría solicitada por el alumno (durante la convocatoria)
     - Reversa por super-admin en ventana de 24h post-cierre
     - Recurso administrativo sobre el ranking final (post-cierre)

   Cada una de estas excepciones queda trazada y firmada.
```

## 12.4 Las reglas pueden cambiar — sin afectar el pasado

Una nueva versión de reglas no afecta a los intentos ya evaluados. Antes de activar una nueva versión, el simulador permite ver su impacto en el ranking completo. Cada versión queda guardada de forma inmutable.

> Refinamiento técnico: las versiones de las reglas se **fijan al ABRIR** cada intento, no al cerrar. Esto garantiza que un cambio mid-día no afecta a alumnos en mitad de su prueba.

## 12.5 Lo que el sistema NO sustituye

- No sustituye la formación. Evalúa, no enseña.
- No garantiza que un candidato apto sea bueno en cualquier circunstancia. Garantiza que cumple los criterios definidos por el cliente.
- No reemplaza el juicio del cliente para casos atípicos: por eso existen el simulador, la auditoría y el recurso administrativo.

---

# 13. El equipo — quién hace qué

| Persona | Rol | Responsabilidad principal |
|---|---|---|
| **Antonio Hermoso** | Director técnico · Cliente · Webfleet | Lidera la arquitectura del sistema y la relación directa con CMadrid. Implementa la integración con Webfleet. Coordina al equipo. |
| **Jesús** | Responsable de backend | Desarrolla la lógica del sistema: captura, detección, motor de cálculo, motor de ranking, persistencia, GDPR, audit log, sync con Doback Elite. |
| **Alejandro** | Responsable de frontend | Desarrolla todas las pantallas: portal del alumno, vista del responsable, portal del administrador (incluyendo el flujo reforzado de cierre de convocatoria), pantalla de la cabina del camión. |
| **Joel** | Responsable del simulador | Se encarga **exclusivamente** del simulador de reglas con dimensión ranking: el endpoint que ejecuta simulaciones, la pantalla del administrador donde el cliente las usa, los datos de prueba para que las simulaciones sean significativas, y la documentación de uso para el cliente. |

**Tamaño del equipo:** 4 personas. **Modalidad:** dedicación intensiva durante el sprint actual de 14 días.

---

# 14. Estado actual y siguientes pasos

## 14.1 Lo que ya está construido

- Procesamiento completo de datos: desde Doback Elite y Webfleet hasta el cierre del intento.
- Integración con Webfleet con redundancia desde Doback Elite.
- Detección automática de los cuatro tipos de evento principales.
- Motor de cálculo de nota configurable.
- Versionado inmutable de las reglas con pinning al abrir el intento.
- Las cuatro vistas de usuario.
- El simulador de reglas con impacto en ranking.
- La cabina del camión con tarjeta RFID, modo oscuro y funcionamiento sin conexión.
- Etiqueta de calidad de datos por intento.
- Mecanismo de auditoría a petición del alumno.
- **Cierre de convocatoria reforzado** (preview + doble admin + acta PDF + ventana de reversa de 24h).
- **GDPR**: política de retención, derecho de acceso, audit log de acciones sensibles.

## 14.2 Lo que falta — y depende del cliente

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   La definición FINAL de las reglas de evaluación    │
   │   y los parámetros de la convocatoria.               │
   │                                                      │
   │   Decisiones del cliente:                            │
   │     - Umbrales exactos por tipo de infracción        │
   │     - Pesos de cada familia                          │
   │     - Número de plazas por convocatoria              │
   │     - Cuál es la "ruta principal" para desempates    │
   │     - Fecha de cierre de cada convocatoria           │
   │     - Texto del aviso de privacidad GDPR             │
   │     - DPO (Delegado de Protección de Datos)          │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

## 14.3 Lo que falta — pulido técnico y legal (Fase 2)

Estas piezas **no entran en la demo del 11/05** pero **deben estar listas antes del cutover real a producción**. Cada una con dueño y fecha objetivo:

| # | Item | Dueño | Fecha objetivo |
|---|---|---|---|
| F1 | Sistema de notificaciones por email | Antonio + Jesús | Semana 3-4 post-demo |
| F2 | Subroles administrativos granulares (OPERATIONS / RULES) — `SUPER_ADMIN` ya disponible en V1 | Jesús | Semana 4 post-demo |
| F3 | Acta firmable digitalmente con firma cualificada | Jesús + Joel | Semana 5 post-demo |
| F4 | Manager asignado a convocatorias específicas | Jesús + Alejandro | Semana 4-5 post-demo |
| F5 | Auditoría tras cierre (queja formal sin modificar resultado) | Jesús | Semana 5-6 post-demo |
| F6 | Recurso administrativo del candidato sobre ranking final | Antonio (con asesor legal CMadrid) | Semana 6-8 post-demo |

## 14.4 Próximos pasos concretos

| Fecha | Hito |
|---|---|
| **11 de mayo de 2026** | Reunión con el cliente. Sistema funcionando con datos reales en una convocatoria demo: ranking, simulador, cierre reforzado, los 4 portales. |
| **Mayo 2026** | Definición conjunta con el cliente de las reglas de evaluación finales y los parámetros de la primera convocatoria real. Inicio de Fase 2 (notificaciones, subroles, etc.). |
| **Mayo–Julio 2026** | Pulido técnico y legal de Fase 2. Integración del recurso administrativo. Coordinación legal con CMadrid (DPO, aviso de privacidad, formato del acta). |
| **Julio 2026** | Despliegue gradual en producción, convocatoria por convocatoria, en paralelo con el sistema actual. |
| **Octubre 2026** | Sistema nuevo plenamente operativo. Sistema anterior retirado. |

## 14.5 Riesgos a vigilar

1. **Plazos.** La fecha del 11 de mayo es ajustada. Lo que se mostrará es un sistema funcionando end-to-end con una convocatoria demo, no la versión definitiva con todos los matices legales pulidos. Los elementos de Fase 2 (notificaciones, recurso, etc.) llegan **después**.

2. **Definición del cliente.** Si CMadrid tarda en definir reglas, parámetros de convocatoria, DPO o texto de privacidad, el plazo de cutover se mueve.

3. **Dependencia de Webfleet.** Doback Elite proporciona redundancia para el GPS, pero algunos KPIs de comportamiento provienen exclusivamente de Webfleet. Una caída prolongada degrada la riqueza de datos sin parar la operación.

4. **Marco legal del recurso administrativo.** Hay que coordinar con asesor legal de CMadrid el procedimiento exacto. Sin esto cerrado, no se puede ir a producción real.

---

## Cierre

Training es un sistema **autónomo en su operación, riguroso en su modelo de oposición, transparente en sus decisiones y conforme con los marcos legales aplicables**. Está diseñado para evaluar y clasificar sin intervención humana en el camino, generando un ranking trazable y auditable que culmina en una decisión final irrevocable al cierre de cada convocatoria, respaldada por un acta firmada y un audit log completo.

La parte técnica está resuelta. Lo que queda por delante es, en gran medida, una conversación operativa con el cliente sobre los criterios concretos de evaluación, los parámetros de cada convocatoria y los aspectos legales (DPO, aviso de privacidad, formato del acta, procedimiento del recurso).

El equipo está listo para esa conversación.

---

*Este documento es la versión ejecutiva del sistema. Para detalle técnico de implementación, existe documentación interna específica del equipo de desarrollo.*
