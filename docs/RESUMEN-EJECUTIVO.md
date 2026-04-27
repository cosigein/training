# Training

## Resumen ejecutivo del proyecto — qué se construye, cómo, cuándo

| | |
|---|---|
| **Versión** | 2.0 — actualizada |
| **Fecha** | 27 de abril de 2026 |
| **Audiencia** | Dirección · Cliente · Equipo de gestión |
| **Carácter** | Resumen ejecutivo no técnico |

## Tabla de contenidos

1. Qué es Training
2. Cómo funciona — visión general
3. El modelo de evaluación: oposición pública, no examen escolar
4. Qué decide el sistema y qué decide CMadrid
5. El equipo y los roles
6. Hoja de ruta hasta la demo del 11 de mayo
7. Lo que ya está construido al 27 de abril
8. Riesgos identificados y plan de contingencia
9. Próximos hitos críticos
10. Documentación disponible

---

# 1. Qué es Training

Training es un sistema **automático de evaluación competitiva** para candidatos a conductor de camión de bomberos en oposición pública española. Su propósito es **reemplazar la evaluación tradicional** —subjetiva, ejercida por un instructor humano observando desde el asiento del copiloto durante el examen práctico de conducción— por una combinación de sensores físicos en el camión, cálculo algorítmico de la nota y un ranking acumulado con trazabilidad legal.

A diferencia de otros sistemas de evaluación, Training **no decide individualmente** si un candidato es apto o no apto. Genera una **nota por cada ruta conducida** y mantiene un **puesto en el ranking acumulado** de la convocatoria. La decisión final apto / no apto se emite al cierre de la convocatoria, en función del puesto final y del número de plazas disponibles.

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   El alumno conduce una ruta real                    │
   │            ↓                                         │
   │   Sensores (Doback Elite + Webfleet) capturan        │
   │            ↓                                         │
   │   El sistema calcula la NOTA de la ruta (0–10)       │
   │            ↓                                         │
   │   La nota actualiza el RANKING de la convocatoria    │
   │            ↓                                         │
   │   Al cierre de la convocatoria, CMadrid emite        │
   │   APTO / NO APTO según ranking + plazas              │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

**A quién sirve:**

- Cuerpos de bomberos públicos españoles que evalúan a sus candidatos a conductor de camión mediante oposición.
- En este momento: **CMadrid** (Cuerpo de Bomberos de la Comunidad de Madrid), con unos 265 candidatos por convocatoria.

**Qué problema resuelve:**

- Hacer la evaluación **objetiva, consistente y trazable**, sin depender del criterio variable de un instructor humano.
- Detectar errores de conducción que un humano puede pasar por alto.
- Generar evidencia objetiva en caso de reclamación o auditoría administrativa.
- Procesar convocatorias grandes sin cuello de botella humano.
- Cumplir con los requisitos legales de la oposición pública española (LPACAP, GDPR, derecho de recurso administrativo).

---

# 2. Cómo funciona — visión general

El proceso completo, desde que un alumno se sube al camión hasta que la convocatoria se cierra y emite veredictos, sigue siempre los mismos pasos. **Cinco de los siete pasos son completamente automáticos.**

## Paso 1 — El alumno se identifica y selecciona ruta

El alumno sube al camión y pasa su tarjeta personal por el lector instalado en la cabina. El sistema reconoce quién es. En la pantalla del kiosko selecciona qué ruta va a realizar.

> Esta es **la única interacción humana** durante el proceso operativo. Todo lo posterior es automático.

## Paso 2 — El alumno conduce

Mientras conduce, **dos fuentes de información** registran lo que ocurre en paralelo:

- **Doback Elite**, el dispositivo propio instalado en cada camión, registra los movimientos físicos del vehículo: aceleraciones longitudinales (frenadas, arranques), aceleraciones laterales (giros), estabilidad general. Doback Elite también registra GPS propio — esto es importante de cara a la redundancia.
- **Webfleet**, la plataforma de gestión de flotas que CMadrid tiene contratada con Bridgestone, aporta una capa adicional: posición GPS, velocidad, eventos de comportamiento de conducción (swerving, harsh braking, speeding, idling), tiempos, KPIs configurables.

Las dos fuentes se complementan. El sistema cruza ambas y resuelve discrepancias automáticamente.

## Paso 3 — El intento se cierra

Cuando termina la ruta —o cuando otro alumno pasa su tarjeta para empezar la suya— el intento se cierra automáticamente. El sistema reúne los datos de Doback Elite y Webfleet correspondientes a esa ventana de tiempo.

## Paso 4 — El sistema procesa (automático)

Sin intervención humana, el sistema:

- Limpia los datos: alinea timestamps, detecta gaps, valida la integridad de la información.
- Identifica **eventos relevantes**: frenadas bruscas, excesos de velocidad, desviaciones de ruta, aceleraciones laterales fuertes.
- Calcula la **nota** entre 0 y 10 aplicando las reglas configuradas por el cliente.
- Genera la **explicación**: el desglose granular de cómo llegó a esa nota, regla por regla.

## Paso 5 — El resultado se cierra y queda fijado

El intento queda **cerrado e inmutable**. Su nota es final. Aparece en la matriz del responsable y en el portal del alumno automáticamente.

## Paso 6 — El responsable consulta (lectura)

El responsable —instructor o examinador asignado a la convocatoria— accede a la matriz, donde ve a todos los alumnos y sus rutas. Puede entrar al detalle de cualquier intento para revisar la información: ruta sobre el mapa, eventos detectados, nota desglosada, calidad de los datos.

> El responsable **no modifica notas individuales**. Su rol es de supervisión informativa. La nota la emite el sistema; la decisión final apto / no apto la toma CMadrid al cierre de la convocatoria.

## Paso 7 — El alumno consulta su resultado

El alumno entra a su portal y ve su nota, su puesto en el ranking acumulado y, una vez cerrada la convocatoria, el resultado final apto / no apto.

> Si el alumno no está conforme, **puede solicitar formalmente una auditoría de la ruta**. La sección sobre derechos del candidato lo detalla en la documentación funcional completa.

---

# 3. El modelo de evaluación: oposición pública, no examen escolar

Esta es **la diferencia más importante** que hay que entender antes de leer cualquier otra parte del documento. Training NO funciona como un examen escolar, donde cada alumno aprueba o suspende según su nota individual. Training funciona como una **oposición pública**: hay un número fijo de plazas, los candidatos compiten entre sí, y solo los mejor clasificados consiguen plaza.

| Aspecto | Examen escolar | Oposición pública (Training) |
|---|---|---|
| Criterio de aprobación | Nota mínima individual | Ranking + plazas disponibles |
| Decisión | Por intento o por examen | Solo al cierre de convocatoria |
| Quién decide | El sistema | CMadrid, con doble validación administrativa |
| Visibilidad de competidores | Irrelevante | Central (el alumno ve su puesto) |
| Recurso | Sobre la nota propia | Recurso administrativo formal LPACAP |

Este modelo tiene implicaciones legales fuertes que afectan a toda la arquitectura del sistema: versionado inmutable de las reglas usadas en cada intento, acta firmada con hash SHA256 al cierre, ventana de 24 horas para reverso por error administrativo, audit log completo de toda acción crítica.

---

# 4. Qué decide el sistema y qué decide CMadrid

Esta separación de responsabilidades es **crítica desde el punto de vista legal** (cumplimiento del artículo 22 del Reglamento General de Protección de Datos europeo, que exige que las decisiones que afectan a las personas tengan una revisión humana significativa).

## Lo que decide el sistema (automático)

- Si la captura de datos de un intento es válida o si hay calidad insuficiente.
- La nota individual de cada intento, entre 0 y 10.
- El puesto del alumno en el ranking acumulado de la convocatoria.
- Si un evento del kiosko es atribuible al intento actual o al siguiente.

## Lo que decide CMadrid (humano)

- La configuración inicial de las reglas de evaluación (umbrales, pesos por familia, criterios de desempate).
- La gestión de la convocatoria: cuándo abre, cuándo cierra, cuántas plazas hay.
- **La decisión final apto / no apto** al cierre de cada convocatoria, mediante un proceso administrativo de tres pasos con doble validación administrativa (dos administradores distintos).
- La resolución de auditorías solicitadas por candidatos.
- La evaluación y respuesta a recursos administrativos formales.

> El sistema captura, mide y calcula. CMadrid configura, supervisa y decide. Esa separación es lo que hace defendible el proceso ante un eventual recurso administrativo o jurisdiccional.

---

# 5. El equipo y los roles

| Rol | Persona | Qué construye | Idioma |
|---|---|---|---|
| Director técnico · enlace con cliente · Webfleet ingestion | **Antonio Hermoso** | Integración con Webfleet · arquitectura · única voz hacia CMadrid | Español |
| Backend completo | **Jesús** | API + worker + schema Prisma + autenticación + cierre de convocatoria | Español |
| Frontend completo | **Alejandro** | Cuatro portales (admin, manager, alumno, kiosko) · ~32 pantallas · design system | Español |
| Simulador + QA + tests E2E + seed data + CI/CD | **Joel** | Pruebas automáticas · datos de demo · simulador de cambios de regla | Inglés |

> El equipo trabaja desde **Córdoba** (Andalucía). El cliente, CMadrid, está en Madrid (400 km al norte). Solo viajamos a Madrid para la demo del 11 de mayo.

---

# 6. Hoja de ruta hasta la demo del 11 de mayo

```
SEMANA 1 — INFRAESTRUCTURA Y CORE
─────────────────────────────────
Mar 28/04   Kickoff con todo el equipo + scaffolding compartido
            (pnpm + workspaces + Prisma + Docker)
Mié 29/04   Schema Prisma base + autenticación JWT + endpoints /health
Jue 30/04   Webfleet client v0 (mock estable) + autenticación refinada
            + base del frontend + retrospectiva de fin de semana
Vie 01/05   Festivo (Día del Trabajador)


SEMANA 2 — INTEGRACIÓN, CIERRE Y SIMULADOR
──────────────────────────────────────────
Lun 04/05   Webfleet real contra sandbox CMadrid
            Normalización + detección + scoring (paquetes puros)
            Componente Matrix con datos mock
Mar 05/05   Ranking + ConvocatoriaCloseAct
            Vista del responsable con datos reales
Mié 06/05   Endpoints de cierre en tres pasos + cron de ranking nocturno
            Modal de Override y de Reevaluación
Jue 07/05   Acta PDF (Puppeteer + SHA256) + kiosko completo
            Pair Jesús + Joel sobre el simulador
Vie 08/05   Datos seed completos + validación E2E + status update CMadrid
            + retrospectiva pre-demo


CIERRE — DEMO
─────────────
Sáb 09/05   Tortura del kiosko (voluntario, escenarios extremos)
            + grabación del screencast Plan C
Dom 10/05   Ensayo demo (tres pasadas completas)
Lun 11/05   REUNIÓN CMADRID — DEMO en Madrid
```

---

# 7. Lo que ya está construido al 27 de abril

| Categoría | Estado |
|---|---|
| **Repositorio** | `cosigein/training` privado · rama `main` protegida · una review obligatoria · dos reviews para archivos críticos (schema Prisma, middleware de auth, package.json raíz, CI, docker-compose) |
| **Documentación** | Once documentos del proyecto · nueve PDFs entregables · OWNERS.md y CONTRIBUTING.md cerrados |
| **Issues** | Seis issues abiertos en GitHub con Definition of Done en comentarios |
| **Convenciones del sprint** | Branch namespace por área (`wf` Antonio, `be` Jesús, `fe` Alejandro, `qa` Joel) · Conventional commits · squash merge · endpoint freeze diario · convención de `data-testid` · Definition of Ready |
| **Decisiones técnicas firmes** | pnpm + workspaces · monorepo (`apps/{api,worker,web}` + `packages/*`) · TypeScript strict · Prisma 6 + PostgreSQL 17 · Redis + BullMQ · Winston · React 18 + Vite + Tailwind 4 + Zustand + React Query · Playwright |
| **Operations runbook** | Severidad de incidentes · proceso de respuesta · rollback (Prisma + deploy) · gestión de secretos · disaster recovery (RTO < 4h, RPO < 1h) · soporte post-cutover |
| **Plan B operativo de la demo** | Cuatro escenarios de fallo concretos con respuesta para cada uno · screencast pregrabado como Plan C |
| **Plan de contingencia del equipo** | Documentado por persona si cae 3-5 días o 1-2 semanas |

**Lo que se cierra esta noche o mañana temprano** (no bloquea a Dirección):

- Invitar a Jesús, Alejandro y Joel al repositorio en GitHub.
- Crear el chat del equipo (Slack / Discord / Teams).
- Conseguir un fixture real de Webfleet o el contacto técnico de Bridgestone.

---

# 8. Riesgos identificados y plan de contingencia

## 8.1 — DobackSoft V3 sin director técnico durante 74 días

> **El riesgo más caro del proyecto.** Mientras el director técnico está dedicado a Training (sprint + Fase 2), DobackSoft V3 — el producto madre, fuente de caja actual, en pleno cutover de Pipeline Audit Phase 2 — se queda sin dirección técnica del 28/04 al ~12/07.

Recomendación de partida: designar un suplente interino con autoridad de decisión técnica para V3 durante esos 74 días. Decisión que requiere a Dirección antes del jueves 30 de abril.

## 8.2 — Riesgos legales con mitigación actual

| Riesgo | Mitigación actual | Acción pendiente |
|---|---|---|
| Recurso administrativo de un candidato impugnando un cierre | Versionado inmutable de las reglas + acta PDF firmada con SHA256 + audit log completo + revisión humana significativa al cierre (cumplimiento GDPR art. 22) | Validación con asesor legal de CMadrid antes del cutover |
| Responsabilidad civil si el sistema falla durante una convocatoria | Pendiente confirmar póliza RC profesional vigente | Decisión de Dirección antes del cutover de Fase 3 (octubre 2026) |
| Acuerdo escrito con Bridgestone (Webfleet) | Pendiente verificar contrato existente o negociar | Cerrar acuerdo escrito antes del cutover real |
| Cumplimiento GDPR (somos Data Processor de datos sensibles) | DPA estándar + cláusulas de protección de datos en contrato con CMadrid | DPO de CMadrid debe firmar el documento de protección antes del cutover |
| Bus factor del equipo | Cuatro personas con plan documentado, code escrow para CMadrid | Plan de reemplazo si Antonio o Jesús caen |

## 8.3 — Riesgos operativos no obvios

- **Webfleet sandbox de CMadrid probablemente no existe.** Las flotas públicas españolas con Webfleet (Bridgestone) típicamente solo tienen producción con datos reales, no sandbox separado. Si esto se confirma esta semana, hay bloqueo legal de NDA + GDPR antes del lunes 04 de mayo, y el sprint perdería la integración real durante una semana entera. Plan de mitigación: negociar export anonimizado de un período histórico para usar como fixture.
- **Equipo de cuatro personas sin redundancia real.** El plan de contingencia documenta qué hacer si cae cada persona durante 3-5 días o durante 1-2 semanas, pero no elimina el riesgo de bus factor.

---

# 9. Próximos hitos críticos

```
HOY · LUNES 27/04
   ▶ Mandar al jefe el bundle dirección
   ▶ Mandar a CMadrid los PDFs ejecutivo + descripción del servicio
   ▶ Invitar al equipo al repositorio
   ▶ Crear el chat del equipo

MAÑANA · MARTES 28/04
   ▶ Kickoff 09:00 con todo el equipo en Córdoba
   ▶ Scaffolding compartido entre 11:00 y 13:00
   ▶ Primer commit de cada miembro del equipo

MIÉRCOLES 29/04
   ▶ Schema Prisma base + autenticación + endpoints /health funcionando

JUEVES 30/04
   ▶ Webfleet client v0 (mock estable) operando
   ▶ Retrospectiva de la primera semana
   ▶ DEADLINE de respuesta de Dirección a las decisiones operativas

LUNES 04/05
   ▶ Webfleet real contra sandbox CMadrid
   ▶ Inicio de los paquetes de detection / scoring / ranking

VIERNES 08/05
   ▶ Validación end-to-end completa del sistema
   ▶ Retrospectiva de la segunda semana + preparación de la demo

LUNES 11/05
   ▶ DEMO con CMadrid en Madrid
```

---

# 10. Documentación disponible

| Documento | Para qué sirve | Tiempo de lectura |
|---|---|---|
| **Este resumen** | Vista ejecutiva del proyecto en una sola lectura | 10 minutos |
| Bundle para Dirección | Panel de control para Dirección durante el viaje, con las decisiones que requieren respuesta | 8 minutos |
| Memo Dirección (interno) | Detalle de los riesgos no obvios, plan de contingencia, decisiones que necesitan respuesta | 15 minutos |
| Documento Ejecutivo | Visión funcional completa del sistema, qué entrega, cómo funciona | 25 minutos |
| Descripción del servicio para CMadrid | Lo que ve el cliente: SLA, GDPR, escrow, formación, hardware, términos contractuales | 20 minutos |
| Operations runbook | Cómo opera el equipo ante incidentes, rollback, secretos, disaster recovery, soporte post-cutover | 15 minutos |
| Paper Maestro técnico | Referencia técnica completa del sistema (3500 líneas) | Lectura por secciones según necesidad |

---

**Documento creado el 27 de abril de 2026.**
**Antonio Hermoso · Director técnico**
**Córdoba · Andalucía**

> *Este documento está pensado para leer una sola vez y consultarse después. Si necesitás profundidad sobre algún punto específico, los documentos especializados están listados en la sección 10.*
