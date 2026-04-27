# Sistema Training v1
## Paper Maestro del Equipo — Versión 6 (DEFINITIVA)

---

| | |
|---|---|
| **Versión** | 6.0 |
| **Fecha** | 27 de abril de 2026 |
| **Autor** | Antonio Hermoso — Director técnico |
| **Para** | Antonio · Jesús · Alejandro · Joel |
| **Estado** | **Documento de planificación obligatorio.** Punto de partida del equipo para llegar al **11 de mayo de 2026** (reunión CMadrid). **A día de hoy (27/04/2026) el código del sistema no está construido**: este paper describe el sistema **objetivo**, no el sistema vigente. La auditoría adversarial fue **documental**, no contra código. Las cifras económicas, hitos de Fase 2 y plazos de despliegue (jul/oct 2026) son **propuestas internas**, sujetas a contrato firmado con CMadrid. |
| **Cambio crítico v4 → v5** | Modelo de evaluación: del modelo "escolar" al modelo "OPOSICIÓN" (ranking acumulado, plazas limitadas, decisión final al cierre). Decisiones D14-D21. |
| **Cambio crítico v5 → v6** | **Cuatro decisiones firmes nuevas tras review adversarial (D22-D25):** (1) cierre de convocatoria reforzado con doble validación, preview obligatorio y acta PDF; (2) GDPR/privacidad incorporada como decisión arquitectónica; (3) sync Doback Elite ↔ backend cerrado por completo; (4) `criteria_version` pinned al **ABRIR** el attempt (no al cerrar). Adicionalmente: nueva §17 con **plan legal/operativo de Fase 2** (notificaciones, recurso del candidato, subroles admin, manager asignado a convocatoria, auditoría post-cierre, acta firmable digitalmente) — cada item con dueño y fecha objetivo. |

---

## ¿Quién sos y qué leés?

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Si NUNCA viste el proyecto antes (Joel, Alejandro, Jesús):     │
│  → leé TODO en orden, no saltés                                 │
│                                                                  │
│  ANTONIO     → §1 a §7 + §11 + Anexo A                          │
│  JESÚS       → §1 a §6 + §8 + §11 + §12 + Anexo C               │
│  ALEJANDRO   → §1 a §6 + §9 + §11 + §12 + Anexos C, D           │
│  JOEL        → §1 a §6 + §10 + §11 + §12 + Anexo C COMPLETO     │
│                                                                  │
│  TODOS DEBEN LEER: §11 (Fase 1 vs 2) y §13 (decisiones firmes)  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Reglas de lectura:**
- Si una decisión está marcada **FIRME**, no se reabre sin acuerdo de los 4.
- Si encontrás algo que no entendés, buscá primero en el **Glosario (Anexo D)** antes de preguntar.
- Si encontrás algo que está mal o falta, decilo en el kickoff. **Después del kickoff, todo lo escrito es ley.**

---

# 1. ¿Qué es esto? — el contexto en 5 minutos

## 1.1 Lo más importante que tenés que saber

Antonio Hermoso lleva un año construyendo solo un sistema llamado **DobackSoft V3**: una plataforma de telemetría vehicular con 12+ módulos. El cliente real es **CMadrid Bomberos** (Comunidad de Madrid). Pagan por UN módulo: **Training** (evaluación de candidatos a conductor de camión de bomberos).

El resto de los módulos son scope sin nadie que pague.

```
┌──────────────────────────────────────────────────────────────┐
│  DOBACKSOFT V3 (lo que existe HOY)                           │
│                                                              │
│  · 92 modelos en base de datos                               │
│  · 12+ módulos: Telemetría, Estabilidad, IA, Geofences,     │
│    Operaciones, Reportes, Admin, TRAINING, etc.              │
│  · Backend Node.js + Express + Prisma + Postgres + Redis     │
│  · Frontend React + Vite + Tailwind + MUI                    │
│  · 1 cliente que paga: CMadrid                               │
│  · Equipo: 1 persona (Antonio)                               │
└──────────────────────────────────────────────────────────────┘
```

**El problema:** mantener 12 módulos con 1 persona para servir 1 módulo a 1 cliente es insostenible. Hay que cortar.

## 1.2 La decisión que ya está tomada

```
   ┌──────────────────────────────────────────────────────┐
   │   ★ Sacamos el módulo Training del monolito          │
   │   ★ Lo construimos en un REPO NUEVO                  │
   │   ★ Reusamos lo validado del actual                  │
   │   ★ Tiramos el resto                                 │
   │   ★ Ahora somos 4: Antonio, Jesús, Alejandro, Joel   │
   │   ★ 14 días hasta demo con cliente: 11/05/2026       │
   └──────────────────────────────────────────────────────┘
```

## 1.3 Modelo de evaluación: oposición, no examen

Esto es la pieza más importante para entender el sistema. **Training NO es un examen del carnet de conducir** (donde sacás 7+ y aprobás). Es una **OPOSICIÓN PÚBLICA**: hay un número fijo de plazas, los candidatos compiten entre sí por esas plazas, y entran los mejores.

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   El sistema NO emite "apto/no apto" por intento.    │
   │                                                      │
   │   El sistema emite UNA NOTA por intento.             │
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

Esto cambia muchas cosas que están detalladas a lo largo del paper (modelo de Attempt, pantallas, simulador, schema). Si te encontrás con una contradicción, **gana el modelo oposición**.

## 1.4 Lo que se descartó (y por qué)

| Propuesta | De quién | Por qué se rechazó |
|---|---|---|
| Reescribir TODO en Python/Flask | Jesús (anterior plan) | Migrar 140 modelos y 12 módulos a otro lenguaje no resuelve el problema, lo traduce. 8-12 meses. No tenemos eso. |
| Frontend nuevo en Vue 3 | Alejandro (anterior plan) | El equipo ya domina React. Cambiar framework no aporta valor en V1. La parte de **producto/UX** del documento de Alejandro SÍ se rescata y vive en §9. |
| Modelo de evaluación "escolar" | Iteración v1-v4 | Reemplazado por modelo oposición tras consulta con el cliente. Las notas son individuales pero la decisión es competitiva. |

**Estas decisiones quedan firmes.** No se reabren.

## 1.5 Tu rol en una línea

```
   ANTONIO     → Arquitecto + cliente CMadrid + Webfleet (código)
   JESÚS       → Backend completo (api + worker + packages + ranking)
   ALEJANDRO   → Frontend completo (4 portales + pantalla ranking)
   JOEL        → QA + Tests E2E + Demo data + Demo readiness
                 + simulador con dimensión RANKING (es el upgrade)
```

Detalle exhaustivo en §7-§10.

---

# 2. ¿Quién es CMadrid y qué necesita?

## 2.1 El cliente

```
   CMadrid Bomberos
   ─────────────────
   · Cuerpo de bomberos de la Comunidad de Madrid
   · Necesita evaluar candidatos a conductor de camión
     en procesos de OPOSICIÓN PÚBLICA
   · ~265 candidatos por convocatoria
   · 10-30 candidatos concurrentes en pico
   · Cada convocatoria tiene un NÚMERO FIJO DE PLAZAS
   · Los X primeros del ranking obtienen plaza
   · Tiene una flota de camiones de prueba
   · Tiene Webfleet contratado (sistema externo de GPS y KPIs)
   · Paga por: Training
```

## 2.2 El proceso de evaluación (cómo funciona la realidad física)

```
   ┌───────────────────────────────────────────────────────────┐
   │                                                           │
   │  1. Un candidato (alumno) se sube a un camión             │
   │  2. Pasa su tarjeta RFID por el lector del camión         │
   │     (kiosko)                                              │
   │  3. Selecciona qué ruta va a evaluar (ej: Ruta A urbana)  │
   │  4. Conduce la ruta                                       │
   │     - Doback Elite (sensor instalado en el camión)        │
   │       captura aceleraciones, frenadas, giros, GPS propio  │
   │     - Webfleet (plataforma externa) captura GPS, KPIs     │
   │       de comportamiento, eventos                          │
   │  5. Termina la ruta (pasa la tarjeta de nuevo o entra     │
   │     otro alumno)                                          │
   │  6. El sistema procesa los datos del intento:             │
   │     - Detecta eventos                                     │
   │     - Calcula NOTA del intento (0-10)                     │
   │     - Genera explicación granular                         │
   │     - NO emite apto/no apto                               │
   │  7. Esa noche, el sistema actualiza el RANKING            │
   │     de la convocatoria con todos los intentos del día     │
   │  8. A la mañana siguiente (6:00 AM), ranking publicado    │
   │     - El alumno ve su nota, su puesto provisional         │
   │     - Si discrepa, puede pedir auditoría                  │
   │  9. Al cierre de la convocatoria (fecha publicada):       │
   │     - Admin confirma cierre                               │
   │     - Ranking final irrevocable                           │
   │     - Los X primeros: APTO. El resto: NO_APTO             │
   │                                                           │
   └───────────────────────────────────────────────────────────┘
```

Cada vuelta del proceso para un candidato y una ruta = un **ATTEMPT** (intento). Una **CONVOCATORIA** agrupa 200+ candidatos y N rutas obligatorias. El **RANKING** es el ordenamiento competitivo dentro de una convocatoria.

## 2.3 Los 4 actores del sistema

| Actor | Quién es | Qué hace | Qué ve |
|---|---|---|---|
| **Conductor en cabina** (alumno) | Candidato a bombero | Conduce el camión durante su evaluación | Solo: quién está siendo evaluado y desde cuándo. **NO ve nota.** |
| **Alumno** (mismo candidato, fuera de cabina) | El mismo, en su casa/tablet | Consulta sus resultados | Notas de cada ruta + puesto provisional + dentro/fuera del corte + detalle pedagógico |
| **Manager** (instructor / examinador) | Bombero veterano que supervisa | Supervisa la convocatoria. **Solo lectura.** | Ranking de la convocatoria, matriz, detalle de attempts, solicitudes de auditoría |
| **Admin** | Personal técnico de CMadrid | Configura el sistema, **cierra convocatorias** | Convocatorias, rutas, RFID, kioskos, scoring versionado, simulador |

## 2.4 Reglas del cliente — NO NEGOCIABLES

```
   ▶ El kiosko NO puede mostrar notas en tiempo real
     (el conductor no debe saber su nota mientras conduce)

   ▶ Multi-turno automático con RFID
     (un mismo camión, varios alumnos durante el día)

   ▶ Webfleet manda en velocidad y ruta (DEFAULT)
     Sensor (Doback Elite) manda en estabilidad (DEFAULT)
     Doback Elite tiene GPS PROPIO como REDUNDANCIA

   ▶ Cuando cambia una regla de scoring,
     los attempts viejos NO se reprocesan automáticamente
     (auditabilidad legal)

   ▶ Las NOTAS son inmutables una vez emitidas
     El RANKING es provisional hasta el cierre
     Al cierre, ranking + decisiones quedan IRREVOCABLES

   ▶ El manager NO modifica nada
     Excepción: solicitudes formales de auditoría del alumno
     (frecuencia esperada <1% de los intentos)

   ▶ El alumno NO ve telemetría cruda
     Ve infracciones contextualizadas en lenguaje pedagógico
     Ve su puesto pero NO los puestos/notas de otros
     Ve "dentro/fuera del corte" pero NO el umbral exacto

   ▶ El RANKING se publica una vez al día (6:00 AM)
     NO se actualiza en tiempo real instantáneo

   ▶ El CIERRE de convocatoria es una acción ADMINISTRATIVA
     Admin confirma manualmente cuando llega la fecha publicada
     CLOSED puede revertirse solo por SUPER_ADMIN dentro de las 24h
     siguientes (con justificación obligatoria). Tras esa ventana,
     LOCKED es irrevocable. Excepción legal post-LOCKED: OutcomeAmendment
     por recurso administrativo resuelto (Fase 2)
```

---

# 3. Nuestra decisión arquitectónica

## 3.1 Lo que vamos a construir

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   ★ UN REPO NUEVO llamado "training"                         │
   │   ★ Monolito modular (NO microservicios)                     │
   │                                                              │
   │   ★ Tres aplicaciones, mismo repo:                           │
   │       · API (Express)                                        │
   │       · Worker (procesamiento async + ranking nocturno)      │
   │       · Web (React SPA con 4 portales)                       │
   │                                                              │
   │   ★ Reusa lo validado de DobackSoft V3:                      │
   │       · Schema Prisma de Training (11 modelos base)          │
   │       · Detector de eventos (StabilityProcessor)             │
   │       · Cliente Webfleet (con sus gotchas conocidos)         │
   │                                                              │
   │   ★ Tira lo que no aplica de DobackSoft V3:                  │
   │       · IA / RAG / FleetMind                                 │
   │       · Geofencing complejo                                  │
   │       · Map-matching (Valhalla, TomTom)                      │
   │       · Command Center                                       │
   │       · Cron jobs operativos                                 │
   │                                                              │
   │   ★ Añade conceptos NUEVOS de v5:                            │
   │       · Convocatoria (con plazas, fecha cierre, ruta princ.) │
   │       · Ranking (snapshot diario + ranking final)            │
   │       · Cierre de convocatoria (proceso administrativo)      │
   │       · Estados de attempt: abandoned vs aborted_technical   │
   │                                                              │
   └──────────────────────────────────────────────────────────────┘
```

## 3.2 Stack — DECISIÓN FIRME

| Capa | Lo que usamos | Lo que NO usamos |
|---|---|---|
| Lenguaje backend | TypeScript + Node 20 | ✗ Python / Flask |
| Web framework | Express 4 | ✗ Fastify / Koa |
| ORM | Prisma 6 | ✗ SQLAlchemy / TypeORM |
| Base de datos | PostgreSQL 17 | ✗ MongoDB |
| Cola async | BullMQ + Redis | ✗ Celery / Kafka |
| Frontend | React 18 + Vite + Tailwind 4 | ✗ Vue / Nuxt |
| Estado FE | Zustand + React Query | ✗ Redux |
| Mapas | Leaflet (envuelto en wrapper propio) | ✗ Google Maps |
| Charts | Chart.js | ✗ Recharts |
| PDF | Puppeteer (servidor) | ✗ DOM-to-PDF |
| Tests | Jest · Vitest · Playwright | — |

```
   ┌────────────────────────────────────────────────────┐
   │ ¿POR QUÉ ESTE STACK?                               │
   │                                                    │
   │ Porque los 4 lo dominamos (o lo aprendemos rápido).│
   │ Cada tecnología nueva = curva de aprendizaje =     │
   │ tiempo que NO tenemos.                             │
   │                                                    │
   │ Si en algún punto alguien propone cambiarlo,       │
   │ la respuesta por defecto es NO.                    │
   └────────────────────────────────────────────────────┘
```

---

# 4. El sistema de un vistazo

## 4.1 Diagrama maestro

```
                       ┌────────────────────────────────────┐
                       │       FRONTEND (React SPA)         │
                       │ ┌───────┬────────┬──────────────┐  │
                       │ │Manager│ Alumno │    Admin     │  │
                       │ │+Rank  │+Estado │+Cierre conv. │  │
                       │ └───┬───┴───┬────┴──────┬───────┘  │
                       │     │       │           │          │
                       │     └───┬───┴────┬──────┘          │
                       │         │        │                 │
                       │     ┌───▼────────▼───┐             │
                       │     │     KIOSKO     │             │
                       │     │ (offline-first)│             │
                       │     └────────────────┘             │
                       └─────────────┬──────────────────────┘
                                     │ HTTPS / JWT
                                     ▼
                       ┌────────────────────────────────────┐
                       │         API (Express)              │
                       │  ┌──────────────────────────────┐  │
                       │  │  Auth · Routes · Audit       │  │
                       │  └──────────────────────────────┘  │
                       └─────┬────────────────────────┬─────┘
                             │                        │
            ┌────────────────▼─────┐    ┌────────────▼──────┐
            │    PACKAGES (puros)  │    │      WORKER       │
            │  ┌────────────────┐  │    │   (BullMQ jobs)   │
            │  │   ingestion    │  │    │ - ingest async    │
            │  │   normalization│  │◄───┤ - sync Webfleet   │
            │  │   detection    │  │    │ - generar PDFs    │
            │  │   scoring      │  │    │ - RANKING NOCTURNO│
            │  │   ranking      │  │    │   (cron 6:00 AM)  │
            │  │   reporting    │  │    └─────────┬─────────┘
            │  └────────────────┘  │              │
            └──────────┬───────────┘              │
                       │                          │
                       └──────────┬───────────────┘
                                  ▼
                       ┌────────────────────────┐
                       │  PostgreSQL  +  Redis  │
                       └────────────────────────┘
                                  │
                                  ▼
                       ┌────────────────────────┐
                       │  Webfleet (externo)    │
                       │  Doback Elite (sensor) │
                       └────────────────────────┘
```

## 4.2 Conceptos centrales

El sistema gira alrededor de **TRES conceptos** anidados:

```
   CONVOCATORIA
       │  ─ contiene candidatos, rutas obligatorias, plazas, fecha cierre
       │  ─ tiene un RANKING que evoluciona durante el proceso
       │  ─ se CIERRA en una fecha y emite resultados finales
       │
       ▼
   ATTEMPT (intento)
       │  ─ una vuelta de un candidato en una ruta
       │  ─ tiene NOTA inmutable
       │  ─ NO tiene decisión apto/no_apto
       │  ─ pertenece a UNA convocatoria
       │
       ▼
   EVENTO
          ─ situación detectada durante el intento
            (frenada brusca, exceso, desviación, etc.)
          ─ tiene source y confidence
```

### 4.2.1 La Convocatoria

Una **Convocatoria** representa un proceso de oposición concreto. Tiene:

```
   convocatoria = {
     id, nombre,
     fecha_inicio,
     fecha_cierre        ← fecha pública de cierre
     plazas              ← número entero (publicado)
     rutas[]             ← rutas obligatorias para todos
     ruta_principal_id   ← ruta usada como criterio 1 de desempate
     candidatos[]        ← inscritos
     status              ← OPEN | CLOSING | CLOSED
     closed_at           ← timestamp de cierre (si CLOSED)
     closed_by           ← admin que confirmó el cierre
     ranking_final[]     ← snapshot definitivo (si CLOSED)
   }
```

### 4.2.2 El Attempt

Un **Attempt** es una unidad inmutable. Modelo actualizado en v5 (sin `decision`):

```
   attempt = {
     IDENTIDAD
     · enrollment_id (v6: inscripción concreta del candidato), vehiculo_id, ruta_id
     · convocatoria_id        (denormalizado para queries de ranking)
     · ventana de tiempo

     DATOS
     · samples crudos (sensor + Webfleet)
     · samples normalizados
     · eventos detectados

     VERSIONADO
     · normalizer_version
     · detector_version
     · criteria_version

     RESULTADO
     · score (0-10)           ← NOTA del intento
     · score_audit (granular)
     · data_quality (high/medium/low)
     · ─ NO HAY decision     ← v5: la decisión es de la CONVOCATORIA
     · ─ NO HAY override_by  ← v5: el manager no modifica notas

     ESTADO
     · status                 ← v5: CON ESTADOS NUEVOS
     · frozen_at

     REEVALUACIÓN
     · parent_attempt_id      ← cuando viene de una auditoría
     · audit_request_id       ← qué auditoría motivó la reevaluación
   }
```

**Estados del attempt en v5:**

```
   OPEN                  En curso
   PROCESSING            Datos llegaron, procesando
   PENDING_DATA_REVIEW   Normalization rechazó (data_quality severamente baja)
   CLOSED                Nota emitida, frozen_at populado
   ABANDONED             Candidato no completó (cuenta como 0 en ranking)
   ABORTED_TECHNICAL     Fallo técnico (NO cuenta en ranking, debe repetir)
```

### 4.2.3 El Ranking

El **Ranking** es el ordenamiento de candidatos dentro de una convocatoria:

```
   ranking_snapshot = {
     id, convocatoria_id,
     calculated_at        ← cuándo se calculó (cron 6:00 AM)
     is_final             ← false durante la convocatoria, true al cierre
     entries[]: [
       {
         enrollment_id,     (v6: ranking opera sobre Enrollment, no Student)
         puesto,
         nota_media,        ← media simple de las rutas
         rutas_completadas, ← cuántas hizo
         rutas_total,       ← cuántas debe hacer
         dentro_del_corte,  ← bool: puesto <= plazas
         tiebreak_key,      ← clave usada para desempate
       },
       ...
     ]
   }
```

Se generan **snapshots diarios** durante la convocatoria. Al cierre se genera el **snapshot final** con `is_final = true` que queda inmutable.

## 4.3 El pipeline de procesamiento

```
   ARCHIVO TXT (sensor)      WEBFLEET API
        │                          │
        └────────────┬─────────────┘
                     │
                     ▼
           ┌─────────────────┐
           │   INGESTION     │  Recibe crudo. Hash. Idempotente.
           │   (idempotente) │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   raw_samples   │  Persistido por attempt
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  NORMALIZATION  │  Saneamiento, gaps, calidad de datos
           │                 │  RECHAZA si está roto → PENDING_DATA_REVIEW
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   DETECTION     │  StabilityProcessor PURO
           │   (puro)        │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │     events      │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │    SCORING      │  Motor configurable + score_audit
           │    (puro)       │  EMITE NOTA 0-10 (NO decisión)
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   FREEZE        │  Snapshot inmutable del attempt
           │   ATTEMPT       │  status = CLOSED
           └────────┬────────┘
                    │
                    ▼ (cada noche a las 6:00 AM)
           ┌─────────────────┐
           │   RANKING JOB   │  Recalcula ranking de la convocatoria
           │   (cron diario) │  Genera ranking_snapshot
           └─────────────────┘

           Al cierre de convocatoria (manual por admin):
           ┌─────────────────┐
           │  CIERRE CONV.   │  Snapshot final + decisiones APTO/NO_APTO
           │  (irrevocable)  │  para todos los candidatos
           └─────────────────┘
```

## 4.4 Los invariantes del sistema

| # | Invariante | Implementación |
|---|---|---|
| 1 | **Idempotencia de ingest** | UNIQUE(attempt_id, source, source_hash). Re-upload = no-op. |
| 2 | **Reproducibilidad** | Comando `replay <attempt_id>` rerun normalize+detect+score con versiones pinned. |
| 3 | **Inmutabilidad de attempt cerrado** | Constraint DB: si frozen_at != null, ningún UPDATE. Para corregir → nuevo attempt con parent. |
| 4 | **Versionado pinned** | normalizer_version, detector_version, criteria_version. Cambios no afectan attempts cerrados. |
| 5 | **Fuente declarada + Confianza** | source ∈ {sensor, webfleet}, confidence ∈ {high, low}. Ortogonales. |
| 6 (v5) | **Inmutabilidad del ranking final** | Constraint: si convocatoria.status = CLOSED, ranking_snapshots is_final no se reescribe. |
| 7 (v5) | **Decisión solo al cierre** | El attempt NO tiene `decision`. La decisión APTO/NO_APTO vive en `candidate_outcome` de la convocatoria, generada al cierre. |
| 8 (v6) | **Cierre con doble validación + acta** | El cierre de convocatoria requiere `closing_admin_id` Y `confirming_admin_id` (dos personas distintas) + preview obligatorio + generación de acta PDF persistida. Sin los tres: no hay cierre. |
| 9 (v6) | **`criteria_version` pinned al ABRIR** | Cuando se crea un attempt, el sistema captura `criteria_version_active` y la pinned. Activar nueva versión NO afecta attempts ya creados (estén OPEN, PROCESSING o CLOSED). Solo afecta a attempts creados a partir de ese momento. |

**Cualquier PR que rompa uno de estos 9 invariantes se rechaza.**

---


# 5. El plan de 14 días

## 5.1 Verdad incómoda

```
   ┌──────────────────────────────────────────────────────────┐
   │  En 14 días NO se construye un sistema completo.         │
   │  Se construye un MVP DEMOABLE END-TO-END.                │
   │                                                          │
   │  Vamos a presentar al cliente PRODUCTO REAL VISIBLE,     │
   │  no diapositivas.                                        │
   └──────────────────────────────────────────────────────────┘
```

## 5.2 Qué TIENE que estar funcionando para el 11/05

```
   ✓ Login funcionando para los 3 roles
   ✓ Subir archivo del sensor → normaliza → procesa → NOTA
   ✓ Sync con Webfleet → trae datos → mezcla con sensor
   ✓ Detector genera eventos sobre datos reales con confidence
   ✓ Motor de scoring + score_audit detallado
   ✓ data_quality calculado por attempt
   ✓ MATRIZ del manager con datos reales (5-10 alumnos)
   ✓ RANKING de la convocatoria visible al manager       ← v5
   ✓ Estado del alumno: puesto + dentro/fuera del corte  ← v5
   ✓ Vista del examinador: mapa + timeline + score breakdown
   ✓ Reevaluación: crear attempt nuevo apuntando al original
   ✓ Solicitud de auditoría desde portal alumno          ← v5
   ✓ Portal del alumno: historial + detalle pedagógico
   ✓ Kiosko con dark mode + estado visible
   ✓ Admin: scoring versionado read-only
   ✓ Admin: cierre de convocatoria (con confirmación)    ← v5
   ✓ Admin: SIMULADOR con dimensión de ranking           ← v5 upgrade
```

## 5.3 Qué NO tiene que estar para el 11/05 (fase 2)

```
   ✗ Offline-first robusto del kiosko (puede ser online-only)
   ✗ Constructor avanzado de reglas (solo lectura)
   ✗ Cutover por cohorte (después)
   ✗ PDFs definitivos (queda mock)
   ✗ Edge cases de Webfleet (cuotas, retries elaborados)
   ✗ i18n completo (es-ES alcanza)
   ✗ Tests E2E exhaustivos (solo críticos)
   ✗ Hardware RFID definitivo (simulamos con teclado)
   ✗ Modelo de confianza continuo (V1 es binario)
   ✗ Pesos por ruta editables (V1 todos = 1.0)
```

## 5.4 Calendario día por día

```
SEMANA 1 — INFRAESTRUCTURA Y BACKEND CORE
─────────────────────────────────────────

LUNES (DÍA 1) — KICKOFF
[ALL]  09:00 Reunión kickoff de 1h. Lectura silenciosa. Q&A.
[ANT]  10:30 Crear repo "training" en GitHub. Permisos.
[JES]  11:00 npm init monorepo + workspaces. Skeleton apps + 8 packages
             (incluyendo packages/ranking).
[ALE]  11:00 Skeleton apps/web Vite + Tailwind. Tokens diseño.
[JOEL] 11:00 Setup CI/CD (GitHub Actions). Setup Playwright.

MARTES (DÍA 2)
[ANT]  Investigar fixtures Webfleet reales.
[JES]  Schema Prisma con: 11 modelos training base + Convocatoria
       expandida + Attempt sin decision + estados nuevos +
       Ranking snapshots + CandidateOutcome + AuditRequest.
       Migración inicial. /health.
[ALE]  AuthContext + páginas login (3 roles + kiosko pairing).
       Layouts base.
[JOEL] Configurar staging deploy auto. Datos seed iniciales:
       1 convocatoria con 5 alumnos, 2 rutas.

MIÉRCOLES (DÍA 3)
[ANT]  packages/ingestion/webfleet: client + auth con tilde.
[JES]  Auth completo + middlewares + endpoints CRUD básicos
       de Convocatoria.
[ALE]  Login funcionando + routing protegido. Wrapper <MapViewer>.
[JOEL] Test E2E #1: login los 3 roles.

JUEVES (DÍA 4)
[ANT]  Webfleet: SyncService + EventMapper con confidence.
[JES]  Package normalization (alineación, gaps, data_quality).
       Tests determinísticos.
[ALE]  Componente <Matrix> con datos mock. Virtualización.
[JOEL] Datos seed v2: 10 alumnos, 4 rutas, 5 attempts vacíos.
       Test E2E #2: subir archivo → attempt creado.

VIERNES (DÍA 5)
[ANT]  Documentar interfaz Webfleet para Jesús.
[JES]  Extraer detection a packages/detection (PURO).
       Endpoint POST /attempts/:id/upload (idempotente).
[ALE]  Estructura vista examinador.
[JOEL] Test E2E #3: Webfleet sync mockeado → events generados.
       Demo interna 18h.

SEMANA 2 — RANKING, CIERRE, KIOSKO Y PULIDO
───────────────────────────────────────────

LUNES (DÍA 8)
[ANT]  Webfleet en staging real (sandbox CMadrid).
[JES]  Motor scoring + score_audit + endpoint /close
       (normalize + detect + score + freeze).
       packages/ranking: cálculo de media + ordenamiento +
       desempate (cascada 4 criterios).
[ALE]  Conectar matriz datos reales + filtros.
[JOEL] Test E2E #4: cerrar attempt → matriz refleja nota.
       Datos seed v3: convocatoria con 30 attempts cerrados
       de varias rutas para ranking realista.

MARTES (DÍA 9)
[ANT]  Datos reales CMadrid en staging.
[JES]  Cron job ranking nocturno (BullMQ + cron repeatable).
       Endpoint GET /convocatorias/:id/ranking (último snapshot).
       Endpoint POST /attempts/:id/audit-request.
       Endpoint POST /attempts/:id/reevaluate.
[ALE]  Vista examinador completa con datos reales.
       Pantalla NUEVA: Ranking del manager (M5 — ver §9.4).
[JOEL] Test E2E #5: ranking se calcula y refleja en pantalla
       manager con datos seed.

MIÉRCOLES (DÍA 10)
[ANT]  Pulir Webfleet edge cases mínimos.
[JES]  Endpoints admin: rutas CRUD, RFID, scoring read-only.
       Endpoints cierre 3-pasos: /close/preview, /close/initiate,
       /close/confirm, /close/abort, /close/reverse (ver §8.7).
       Lógica de ConvocatoriaCloseAct + CandidateOutcome al cierre.
[ALE]  Portal alumno: dashboard + historial + detalle pedagógico.
       Pantalla NUEVA en alumno: "Tu progreso en la convocatoria"
       (puesto, media, dentro/fuera del corte).
[JOEL] Test E2E #6: solicitud de auditoría + reevaluación.

JUEVES (DÍA 11)
[ANT]  Soporte ad-hoc al equipo.
[JES]  Endpoint POST /scoring/simulate con dimensión RANKING:
       devuelve, además del impacto en notas, el reordenamiento
       del ranking completo y los candidatos que cambian de
       lado del corte.
[ALE]  KIOSKO completo. Dark mode. RFID simulado.
       5 mecanismos defensivos básicos.
       Pantalla NUEVA admin: cierre de convocatoria con
       confirmación irrevocable.
[JOEL] SIMULADOR end-to-end: pantalla admin que llama el
       endpoint, muestra reordenamiento del ranking, exports.
       Test E2E #7: simulación con cambio de threshold,
       ranking se reordena visualmente.

VIERNES (DÍA 12)
[ANT]  Backup completo. Validación end-to-end.
[JES]  Pulido y bug fixes. Datos seed completos para demo
       (1 convocatoria con 50 alumnos, ranking realista,
       attempts variados).
[ALE]  Pulido visual. Wake-lock kiosko. Admin scoring view.
[JOEL] Pasada COMPLETA del checklist Anexo C aplicable.

SÁBADO (DÍA 13) — TORTURA DEL KIOSKO
[ALL]  Cortar wifi. Apagar dispositivo. Doble RFID.
       Cada falla → arreglar o documentar.
[JOEL] Lidera. Documenta. Decide qué entra al playbook.

DOMINGO (DÍA 14) — ENSAYO DEMO
[ALL]  3 pasadas completas en staging.
       Plan B: screencast como fallback.

LUNES (DÍA 15) — REUNIÓN CMADRID 11/05/2026
```

## 5.5 Reglas de ejecución del sprint

```
   ▶ Daily de 15 minutos a las 9:30 AM. Inflexible.
   ▶ Si bloqueado >2h, escalar al chat del equipo.
   ▶ Cada commit pusheado y desplegado a staging automático.
   ▶ El que rompe staging, lo arregla antes de irse.
   ▶ Nada de "lo dejo para mañana".
   ▶ Trabajo en main con feature branches cortas (<1 día).
   ▶ PR de un dev requiere 1 review de OTRO dev.
   ▶ Joel revisa la calidad de demo cada viernes.
```

---

# 6. Roles del equipo — overview

| Persona | Rol | Foco principal |
|---|---|---|
| **Antonio Hermoso** | Director técnico + cliente + Webfleet (dev) | Arquitectura · Comunicación CMadrid · Cliente Webfleet en código · Decisiones |
| **Jesús** | Backend lead | apps/api · apps/worker · packages (excepto Webfleet) · Schema Prisma · **packages/ranking** · cron nocturno · cierre convocatoria |
| **Alejandro** | Frontend lead | apps/web completo · 4 portales · UX · Wrappers · Pantalla ranking · Pantalla cierre convocatoria · Estado del alumno en convocatoria · Tests Vitest |
| **Joel** | Simulador (dueño exclusivo) + QA | **Simulador end-to-end con dimensión ranking** (es la pieza más vendible al cliente). Tests E2E. Datos seed. Demo readiness. Día 13 tortura kiosko. |

---


# 7. PARA ANTONIO — Webfleet + Arquitectura + Cliente

## 7.1 Tu rol

Sos el **director técnico**. Eso significa 3 cosas a la vez:

```
   1. ARQUITECTO
      Tomás las decisiones de diseño que afectan a más de 1 persona.
      Aprobás (o rechazás) cambios estructurales.

   2. INTERFAZ CON EL CLIENTE
      Sos la única voz hacia CMadrid durante estos 14 días.
      Comunicás expectativas, fechas, scope.

   3. DEV CONTRIBUTOR — DUEÑO DE WEBFLEET
      Tu código vive en packages/ingestion/webfleet/.
```

## 7.2 Tu territorio de código

```
   training/
   ├── packages/
   │   └── ingestion/
   │       └── webfleet/        ← TU CÓDIGO
   │           ├── client.ts        cliente HTTP de Webfleet
   │           ├── normalizer.ts    convierte respuesta cruda
   │           ├── syncService.ts   orquesta sync periódico + on-demand
   │           ├── eventMapper.ts   convierte eventos Webfleet a Event
   │                                interno con confidence assignment
   │           ├── circuitBreaker.ts cuotas, retries
   │           └── tests/           fixtures + tests determinísticos
   │
   └── apps/worker/src/jobs/
       └── webfleetSync.ts          ← TU CÓDIGO (orquestación)
```

## 7.3 El gotcha crítico de Webfleet

```
   ┌──────────────────────────────────────────────────────┐
   │ El username de CMadrid en Webfleet TIENE TILDE.      │
   │ Si no codificás la URL en UTF-8, todos los requests  │
   │ vuelven 401/403 sin explicación clara.               │
   │                                                      │
   │ TODO request a Webfleet:                             │
   │   const url = encodeURI(...)                         │
   │                                                      │
   │ Reproducirlo cuesta días de debug si te olvidás.     │
   └──────────────────────────────────────────────────────┘
```

## 7.4 Cuota Webfleet — circuit breaker desde día 1

CMadrid tiene cuota de **14.400 requests/día**. Sin circuit breaker, podés agotarla en 30 minutos por un bug.

```
   Implementación obligatoria:

   Redis key: webfleet:quota:YYYYMMDD
   - Incrementa en cada request
   - TTL = 24h auto-expira
   - Si > 11.520 (80%) → log warning + alerta
   - Si > 14.000 (97%) → rechazar nuevos syncs
   - Si Webfleet responde 429 → backoff exponencial mínimo 60s
```

## 7.5 Tu interfaz con Jesús

Webfleet es un package. Jesús lo consume desde apps/worker y apps/api:

```typescript
// packages/ingestion/webfleet/index.ts
export interface WebfleetSyncResult {
  attempt_id: string;
  raw_samples_count: number;
  events_count: number;
  data_freshness: 'fresh' | 'stale' | 'missing';
  fetched_at: Date;
}

export async function syncAttempt(
  attempt_id: string,
  options: { force?: boolean }
): Promise<WebfleetSyncResult>;

export async function getQuotaStatus(): Promise<{
  used: number;
  limit: number;
  resets_at: Date;
}>;
```

Si cambiás la interfaz, le avisás a Jesús.

## 7.6 Decisiones que SOLO vos podés tomar

```
   - Reabrir cualquier decisión firme (D1-D21)
   - Aceptar o rechazar features fuera de scope
   - Comunicación con CMadrid (cualquier email/llamada)
   - Aprobar PRs estructurales
   - Decidir si cancelamos o postponemos la demo del 11/05
   - Onboarding/offboarding del equipo
```

## 7.7 Tu calendario 14 días

```
DÍA  TAREA
───  ────────────────────────────────────────────
1    Kickoff + crear repo + permisos
2    Investigar fixtures Webfleet reales
3    packages/ingestion/webfleet: client + auth con tilde
4    SyncService + EventMapper + confidence assignment
5    Documentar interfaz pública para Jesús
8    Webfleet en staging real (sandbox CMadrid)
9    Coordinar fixture grande con cliente
10   Pulir Webfleet edge cases mínimos
11   Soporte ad-hoc + doc cliente
12   Backup + validación end-to-end
13   Tortura kiosko (con el equipo)
14   Conducir ensayo demo
```

---

# 8. PARA JESÚS — Backend completo

## 8.1 Tu rol

```
   ┌──────────────────────────────────────────────────────┐
   │  TU TERRITORIO                                       │
   │                                                      │
   │  · apps/api          — toda la API REST              │
   │  · apps/worker       — todos los jobs async          │
   │  · packages/domain   — tipos puros                   │
   │  · packages/ingestion/parser — parser archivos       │
   │  · packages/normalization — saneamiento              │
   │  · packages/detection     — detector eventos         │
   │  · packages/scoring       — motor scoring            │
   │  · packages/ranking       — motor ranking (NUEVO v5) │
   │  · packages/reporting     — PDFs, exports            │
   │  · packages/shared        — logger, config, prisma   │
   │  · prisma/schema.prisma   — schema y migraciones     │
   │                                                      │
   │  NO TOCÁS:                                           │
   │  · packages/ingestion/webfleet — es de Antonio       │
   │  · apps/web — es de Alejandro                        │
   └──────────────────────────────────────────────────────┘
```

## 8.2 Lo que tenés que entender ANTES de codear

**Hay 7 invariantes arquitectónicas que NO podés romper.**

```
1. IDEMPOTENCIA DE INGEST
   Mismo archivo entrando 2 veces ≠ samples duplicados.
   Hash SHA256 + UNIQUE(attempt_id, source, source_hash).

2. REPRODUCIBILIDAD
   Comando `replay <attempt_id>` rerun con versiones pinned.

3. INMUTABILIDAD DEL ATTEMPT CERRADO
   Si frozen_at != null, ningún UPDATE pasa.
   Para corregir → attempt nuevo con parent_attempt_id.

4. VERSIONADO PINNEADO
   Cada attempt cierra con normalizer_version, detector_version,
   criteria_version.

5. FUENTE DECLARADA + CONFIANZA (ortogonales)
   source ∈ {sensor, webfleet}. confidence ∈ {high, low}.

6. INMUTABILIDAD DEL RANKING FINAL  (NUEVO v5)
   Si convocatoria.status = CLOSED, ranking_snapshot is_final = true
   no se puede modificar. UPDATE bloqueado por constraint DB.

7. DECISIÓN SOLO AL CIERRE  (NUEVO v5)
   Attempt NO tiene `decision`.
   La decisión APTO/NO_APTO vive en candidate_outcome,
   generada por el cierre de convocatoria.
```

## 8.3 Schema Prisma — modelos críticos (actualizados v5)

> **Nota editorial sobre las relaciones Prisma (v6 fix R4)**
>
> Los bloques `prisma` de esta sección documentan **el contrato del schema** y las decisiones críticas (constraints, índices, partial uniques, triggers). Para mantener legibilidad, las **relaciones inversas escalares** (`attempt Attempt @relation(fields: [attempt_id], references: [id])` en cada modelo hijo) **se omiten cuando son simétricas y triviales** — Prisma exige declararlas en ambos lados, y la implementación las añade sistemáticamente.
>
> **Reglas para Jesús al implementar:**
>
> - Donde un modelo hijo tenga `<modelo>_id String`, agregar el campo de relación correspondiente: `<modelo> <Modelo> @relation(fields: [<modelo>_id], references: [id])`.
> - Donde un modelo padre declare `<hijos> <Modelo>[]`, asegurarse de que el lado opuesto tenga el campo de relación pareado (mismo nombre de relation si tiene `@relation("Nombre")`).
> - Las relaciones que SÍ están declaradas explícitamente en este doc tienen un motivo (relación nombrada, ambigüedad, FK opcional). Esas no se simplifican.
> - Modelos con relaciones inversas implícitas: `Attempt` (samples, events, score_audit), `Route` ↔ `Attempt`, `Vehicle` ↔ `Attempt`, `Kiosko` ↔ `Attempt`, `User` ↔ `Student`, `Student` ↔ `Enrollment` y `RfidCard`, `AuditRequest` ↔ `Enrollment`.
>
> Si la convención de "documentar lo no-trivial" se siente confusa al implementar: declará TODAS las relaciones de manera explícita en el `schema.prisma` real, sin omisiones. El doc es la spec arquitectónica, no la copia literal del schema.

### 8.3.1 User & Auth (con SUPER_ADMIN — v6 fix tras review)

```prisma
model User {
  id                          String   @id @default(cuid())
  email                       String   @unique
  password_hash               String
  role                        UserRole
  organization_id             String
  privacy_consent_accepted_at DateTime?     // GDPR — login bloqueado si null para rol ALUMNO
  privacy_notice_version      String?       // qué versión del aviso aceptó
  created_at                  DateTime @default(now())
}

enum UserRole {
  SUPER_ADMIN     // único rol que puede ejecutar /close/reverse y aprobar GDPR forget
  ADMIN           // operaciones diarias + cierre (initiate / confirm)
  MANAGER         // solo lectura + resolución de auditorías
  ALUMNO          // candidato
}
```

**Reglas de role en V1 (fix tras review adversarial):**

- En el seed de bootstrap del sistema **debe existir al menos UN `SUPER_ADMIN`** + dos `ADMIN` distintos.
- Sin esos tres usuarios pre-creados, el cierre de convocatoria es inejecutable.
- F2 (subroles más finos: `ADMIN_OPERATIONS / ADMIN_RULES`) sigue en Fase 2; `SUPER_ADMIN` se introduce ya en V1 porque D22 lo requiere para reversa.
- El healthcheck `/health/deep` falla si la organización no tiene los 3 actores requeridos.

### 8.3.2 Convocatoria — modelo expandido (v5 + v6 cierre reforzado)

```prisma
model Convocatoria {
  id               String   @id @default(cuid())
  name             String
  description      String?
  starts_at        DateTime
  closes_at        DateTime              // fecha de cierre publicada
  plazas           Int                   // número de plazas (público)
  status           ConvocatoriaStatus    @default(OPEN)

  // CIERRE REFORZADO (NUEVO v6)
  closing_initiated_at  DateTime?         // cuándo admin inició el cierre (entra a CLOSING)
  closing_admin_id      String?           // primer admin que inicia el cierre
  confirming_admin_id   String?           // segundo admin que confirma (debe ser != closing_admin_id)
  closed_at             DateTime?         // cuándo se ejecutó el cierre definitivo
  acta_pdf_url          String?           // path al acta PDF generada
  reversal_window_until DateTime?         // closed_at + 24h. Después: irrevocable.
  reversed_at           DateTime?         // si super-admin revirtió en la ventana
  reversed_by           String?           // user_id del super-admin que revirtió
  reversal_reason       String?           // justificación obligatoria

  ruta_principal_id String?               // nullable hasta antes del primer ranking publicado
  ruta_principal   Route?    @relation("RutaPrincipal", fields: [ruta_principal_id], references: [id])
  // INVARIANTE: si convocatoria.status pasa de OPEN a CLOSING o CLOSED, ruta_principal_id debe ser != null
  // Service-level: bloquear primer ranking_snapshot si ruta_principal_id es null
  // Editable solo mientras status = OPEN y aún no se publicó el primer ranking

  // Relaciones — v6 fix R3 (propagación tras refactor Enrollment)
  rutas             ConvocatoriaRuta[]
  enrollments       Enrollment[]                              // back-ref de Enrollment.convocatoria
  attempts          Attempt[]                                 // back-ref de Attempt.convocatoria
  ranking_snapshots RankingSnapshot[]                         // back-ref de RankingSnapshot.convocatoria
  outcomes          CandidateOutcome[]                        // back-ref de CandidateOutcome.convocatoria
  close_acts        ConvocatoriaCloseAct[]                    // v6 fix R3-S2: ahora múltiples actas posibles (VIGENTE + VOIDED)
  organization_id   String

  @@index([status])
  @@index([reversal_window_until])
}

enum ConvocatoriaStatus {
  OPEN       // En curso, ranking actualizable
  CLOSING    // Admin inició cierre, esperando confirmación de segundo admin
  CLOSED     // Cerrada (puede revertirse en ventana de 24h por super-admin)
  LOCKED     // Cerrada irrevocablemente (pasaron las 24h)
}

// tabla pivote para rutas de la convocatoria
model ConvocatoriaRuta {
  convocatoria_id String
  ruta_id         String
  peso            Float   @default(1.0)  // V1 siempre 1.0, V2 configurable

  convocatoria Convocatoria @relation(fields: [convocatoria_id], references: [id])
  ruta         Route        @relation(fields: [ruta_id], references: [id])

  @@id([convocatoria_id, ruta_id])
}
```

### 8.3.3 Route & Vehicle (con peso latente)

```prisma
model Route {
  id              String   @id @default(cuid())
  name            String
  description     String
  geometry        Json     // GeoJSON polyline
  organization_id String

  attempts        Attempt[]
  convocatorias   ConvocatoriaRuta[]
  como_principal  Convocatoria[]    @relation("RutaPrincipal")
}

model Vehicle {
  id              String   @id @default(cuid())
  plate           String
  organization_id String
}
```

### 8.3.4 Student & Enrollment & RFID (refactor v6 tras review)

**Cambio crítico tras review:** separar al **humano** (`Student`) de su **inscripción** a una convocatoria concreta (`Enrollment`). Un mismo candidato puede inscribirse en distintas convocatorias a lo largo del tiempo (2026-A, 2026-B, etc.) sin duplicar User ni perder histórico GDPR.

```prisma
// El humano. Hay UNA fila por candidato físico, viva durante años.
model Student {
  id              String   @id @default(cuid())
  user_id         String   @unique
  // sin convocatoria_id aquí — ahora vive en Enrollment
  organization_id String

  enrollments     Enrollment[]
  rfid_cards      RfidCard[]   // un candidato puede tener múltiples cards a lo largo del tiempo
}

// La inscripción de un Student a UNA convocatoria.
// Es la unidad que entra al ranking.
model Enrollment {
  id               String   @id @default(cuid())
  student_id       String
  convocatoria_id  String
  enrolled_at      DateTime @default(now())
  withdrawn_at     DateTime?            // si el candidato se retira antes del cierre
  organization_id  String

  student          Student      @relation(fields: [student_id], references: [id])
  convocatoria     Convocatoria @relation(fields: [convocatoria_id], references: [id])
  attempts         Attempt[]            // back-ref de Attempt.enrollment
  outcome          CandidateOutcome?    // back-ref de CandidateOutcome.enrollment
  ranking_entries  RankingEntry[]       // v6 fix R3: back-ref de RankingEntry.enrollment

  @@unique([student_id, convocatoria_id])
  @@index([convocatoria_id])
  @@index([student_id])
}

// Tarjeta RFID — historizada para permitir reasignación entre convocatorias
// v6 fix: SIN @unique en uid (Prisma DSL no soporta partial unique).
//         La unicidad parcial se enforza con migration raw — ver abajo.
model RfidCard {
  id              String   @id @default(cuid())
  uid             String                   // ID físico del lector RFID
  assigned_to     String?                  // student_id (nullable cuando libre)
  assigned_at     DateTime?
  revoked_at      DateTime?
  active          Boolean  @default(true)
  organization_id String

  student         Student? @relation(fields: [assigned_to], references: [id])

  @@index([assigned_to])
  @@index([uid])
  @@index([uid, active, revoked_at])     // soporte al constraint parcial
}
```

**Migration raw obligatoria (Postgres):**

```sql
-- En la migration que crea RfidCard, agregar al final:
CREATE UNIQUE INDEX rfid_card_uid_active_unique
  ON "RfidCard" (uid)
  WHERE active = true AND revoked_at IS NULL;
```

**Regla:** en cualquier momento, una misma `RfidCard.uid` puede tener **a lo sumo UNA** fila activa (active=true, revoked_at IS NULL). Inserts de un nuevo registro con el mismo uid mientras hay otro activo son rechazados por la DB. Reasignar una tarjeta requiere primero `UPDATE active=false, revoked_at=now()` en la fila vieja, después INSERT nueva.

**Fuente de verdad ÚNICA para "¿quién es esta tarjeta?"** es esta tabla, NO un campo en Student.

**Consecuencia para attempts y ranking:** `Attempt.student_id` se renombra a `Attempt.enrollment_id`. El ranking opera sobre `Enrollment[]`, no sobre `Student[]`. GDPR data export del Student incluye TODAS sus enrollments.

### 8.3.5 Kiosko

```prisma
model Kiosko {
  id              String   @id @default(cuid())
  name            String
  vehicle_id      String?
  pairing_token   String?
  paired_at       DateTime?
  last_seen_at    DateTime?
  organization_id String
}
```

### 8.3.6 Attempt — cambios v5 + v6

**Cambio crítico v6:** `criteria_version`, `normalizer_version` y `detector_version` se pinned **al CREAR el attempt**, no al cerrar. Esto evita que un cambio de reglas mid-camino afecte a attempts en curso.

```prisma
model Attempt {
  id                  String   @id @default(cuid())
  enrollment_id       String                   // v6 fix: FK a Enrollment, no a Student
  vehicle_id          String
  route_id            String
  convocatoria_id     String                   // denormalizado para queries de ranking
  kiosko_id           String?
  organization_id     String

  started_at          DateTime
  ended_at            DateTime?

  status              AttemptStatus @default(OPEN)

  // Versionado pinned AL CREAR (v6) — no al cerrar
  normalizer_version  String
  detector_version    String
  criteria_version    String

  // Resultado (poblados al cerrar)
  score               Float?         // nota 0-10
  stability_family_score Float?      // v6 fix: agregado de ScoreAudit family=estabilidad
                                     // populado por scoring al cerrar; lo usa tiebreak #3
  data_quality        DataQuality?
  data_quality_metrics Json?

  // ✗ NO tiene `decision` — vive en CandidateOutcome al cierre

  // Sync Doback Elite (NUEVO v6)
  awaiting_doback_data Boolean @default(false)
  doback_sync_attempts Int     @default(0)
  doback_synced_at     DateTime?

  // Auditoría — v6 fix R3-C2: AMBOS lados de las dos relaciones nombradas
  audit_request_id          String?
  audit_request             AuditRequest?  @relation("AttemptOriginatedByAudit", fields: [audit_request_id], references: [id])
  // back-ref de AuditRequest.original_attempt (que apunta a este Attempt)
  audit_requests_as_original AuditRequest[] @relation("OriginalAttemptOfAudit")

  // Reevaluación
  parent_attempt_id   String?
  parent              Attempt?  @relation("AttemptHistory", fields: [parent_attempt_id], references: [id])
  children            Attempt[] @relation("AttemptHistory")

  // Inmutabilidad
  frozen_at           DateTime?

  // Relaciones
  raw_samples         RawSample[]
  normalized_samples  NormalizedSample[]
  events              Event[]
  score_audit         ScoreAudit[]

  enrollment          Enrollment   @relation(fields: [enrollment_id], references: [id])
  convocatoria        Convocatoria @relation(fields: [convocatoria_id], references: [id])

  @@index([enrollment_id])
  @@index([convocatoria_id])
  @@index([frozen_at])
  @@index([awaiting_doback_data])
}

enum AttemptStatus {
  OPEN                       // En curso (kiosko activo)
  PROCESSING                 // Datos llegando, procesando
  AWAITING_DOBACK_DATA       // Cerrado en kiosko, esperando sync de Doback Elite
  PENDING_DATA_REVIEW        // Normalization rechazó
  PENDING_TECHNICAL_REVIEW   // v6 fix: ABORTED técnico inminente al cierre, decisión admin
  PENDING_CRITERIA_REVIEW    // v6 fix: kiosko offline con criteria_version stale al sincronizar
  CLOSED                     // Nota emitida, frozen
  ABANDONED                  // Candidato no completó (cuenta como 0)
  ABORTED_TECHNICAL          // Fallo del sistema (NO cuenta)
  INTERRUPTED_BY_OTHER_CARD  // v6 fix: otra tarjeta cerró el attempt antes del 80% — NO cuenta
                             // (no penaliza al candidato víctima)
}

enum DataQuality {
  HIGH
  MEDIUM
  LOW
}
```

### 8.3.7 Samples (sin cambios)

```prisma
model RawSample {
  id              String   @id @default(cuid())
  attempt_id      String
  source          SampleSource
  source_hash     String
  timestamp       DateTime
  payload         Json
  organization_id String

  @@unique([attempt_id, source, source_hash])
  @@index([attempt_id, timestamp])
}

model NormalizedSample {
  id              String   @id @default(cuid())
  attempt_id      String
  timestamp       DateTime
  ax              Float?
  ay              Float?
  az              Float?
  speed           Float?
  lat             Float?
  lng             Float?
  interpolated    Boolean   @default(false)
  source_ref      String?
  organization_id String

  @@index([attempt_id, timestamp])
}

enum SampleSource {
  SENSOR
  WEBFLEET
}
```

### 8.3.8 Event (sin cambios mayores)

```prisma
model Event {
  id                String      @id @default(cuid())
  attempt_id        String
  type              EventType
  timestamp         DateTime
  duration_ms       Int?
  severity          Float
  source            EventSource
  confidence        Confidence
  confidence_score  Float?      // 0..1, oculto V1, listo V2
  confidence_reason String?
  payload           Json
  organization_id   String

  @@index([attempt_id])
  @@index([type])
}

enum EventType {
  FRENADA_BRUSCA
  ACELERACION_LATERAL
  EXCESO_VELOCIDAD
  DESVIACION_RUTA
}

enum EventSource {
  SENSOR
  WEBFLEET
}

enum Confidence {
  HIGH
  LOW
}
```

### 8.3.9 Scoring versionado

```prisma
model CriteriaVersion {
  id          String   @id @default(cuid())
  version     String   @unique
  active      Boolean  @default(false)
  rules       Json
  created_by  String
  created_at  DateTime @default(now())
  notes       String?
  organization_id String
}
```

### 8.3.10 Score Audit

```prisma
model ScoreAudit {
  id                 String   @id @default(cuid())
  attempt_id         String
  rule_id            String
  rule_version       String
  family             String
  value_observed     Float
  threshold          Float
  triggered          Boolean
  weight             Float
  contribution       Float
  evidence_event_ids String[]
  computed_at        DateTime @default(now())
  organization_id    String

  @@index([attempt_id])
}
```

### 8.3.11 Ranking — NUEVO en v5

```prisma
model RankingSnapshot {
  id                String   @id @default(cuid())
  convocatoria_id   String
  calculated_at     DateTime @default(now())
  is_final          Boolean  @default(false)  // true solo al cierre
  total_candidates  Int
  total_plazas      Int

  // v6 fix R2-S2: campos de invalidación tras reversa
  voided_at         DateTime?              // null = vigente; populado = invalidado
  voided_by         String?                // user_id del SUPER_ADMIN
  voided_reason     String?                // mismo reason del /close/reverse

  entries           RankingEntry[]
  organization_id   String

  convocatoria      Convocatoria @relation(fields: [convocatoria_id], references: [id])

  @@index([convocatoria_id, calculated_at])
  @@index([convocatoria_id, is_final])
  @@index([voided_at])
}

model RankingEntry {
  id                  String   @id @default(cuid())
  snapshot_id         String
  enrollment_id       String                       // v6 fix R3: ranking opera sobre Enrollment, no Student
  puesto              Int
  nota_media          Float
  rutas_completadas   Int
  rutas_total         Int
  dentro_del_corte    Boolean
  tiebreak_key        String   // hash auditable de los 4 criterios

  snapshot            RankingSnapshot @relation(fields: [snapshot_id], references: [id])
  enrollment          Enrollment      @relation(fields: [enrollment_id], references: [id])

  @@unique([snapshot_id, enrollment_id])
  @@index([snapshot_id, puesto])
  @@index([enrollment_id])
}
```

### 8.3.12 Candidate Outcome — v5 + v6 fix multi-convocatoria

Genera la decisión final al cierre de la convocatoria. Una fila por **enrollment** (= candidato × convocatoria).

```prisma
model CandidateOutcome {
  id                  String   @id @default(cuid())
  enrollment_id       String   @unique           // v6 fix: una decisión por inscripción
  convocatoria_id     String                     // denormalizado para queries
  decision            Decision
  puesto_final        Int
  nota_media_final    Float
  rutas_completadas   Int
  decided_at          DateTime @default(now())

  // v6 fix R2-S2: invalidación tras reversa
  superseded_at       DateTime?                  // populado si reverse en ventana 24h
  superseded_by       String?                    // user_id del SUPER_ADMIN
  superseded_reason   String?

  organization_id     String

  enrollment          Enrollment   @relation(fields: [enrollment_id], references: [id])
  convocatoria        Convocatoria @relation(fields: [convocatoria_id], references: [id])
  amendments          OutcomeAmendment[]         // v6: F6 — recursos legales (Fase 2)

  @@index([convocatoria_id])
}

enum Decision {
  APTO
  NO_APTO
}
```

### 8.3.13 Audit Request — v5 + v6 fix relación

Cuando un alumno solicita auditoría de un intento. Una solicitud puede generar **a lo sumo UN** attempt nuevo (la reevaluación).

```prisma
model AuditRequest {
  id                    String   @id @default(cuid())
  original_attempt_id   String                          // attempt sobre el que se solicita auditoría
  enrollment_id         String                          // quién solicita (la inscripción del candidato)
  reason                String                          // texto del alumno (≥30 chars)
  status                AuditStatus @default(PENDING)
  reviewed_by           String?                         // user_id del manager
  reviewed_at           DateTime?
  resolution            String?                         // texto de la resolución (≥30 chars si != PENDING)
  filed_after_close     Boolean  @default(false)        // v6 fix F5: queja formal post-cierre
  organization_id       String

  // Relación 1-a-1 hacia el attempt resultante (puede ser null si CONFIRMED o REJECTED)
  // Esta es la única dirección de la relación. La back-reference vive en Attempt.audit_request_id
  // bajo el nombre "AttemptOriginatedByAudit" (ver §8.3.6).
  attempts              Attempt[] @relation("AttemptOriginatedByAudit")

  // Lookup hacia el attempt original (relación nombrada, back-ref en Attempt.audit_requests_as_original)
  original_attempt      Attempt   @relation("OriginalAttemptOfAudit", fields: [original_attempt_id], references: [id])

  @@index([original_attempt_id])
  @@index([enrollment_id])
  @@index([status])
}

enum AuditStatus {
  PENDING
  REVIEWING
  CONFIRMED       // auditoría confirma resultado original (sin reevaluación)
  REEVALUATED     // generó un attempt nuevo
  REJECTED        // v6 fix: solicitud sin mérito documentada — original se mantiene
  POST_CLOSE      // v6 fix F5: solicitud presentada tras cierre — solo evidencia, no modifica
}
```

**Nota sobre las dos relaciones Attempt ↔ AuditRequest:**

- `Attempt.audit_request_id` → `AuditRequest` (relación nombrada `AttemptOriginatedByAudit`): apunta a la auditoría QUE GENERÓ a este attempt (porque es una reevaluación).
- `AuditRequest.original_attempt_id` → `Attempt` (relación nombrada `OriginalAttemptOfAudit`): apunta al attempt SOBRE EL QUE SE PIDIÓ la auditoría.
- Son dos relaciones distintas con nombres distintos. Prisma compila limpio.

### 8.3.14 ConvocatoriaCloseAct — Acta del cierre (NUEVO v6)

Documento generado al cerrar una convocatoria. Es la pieza legal que avala el resultado.

```prisma
model ConvocatoriaCloseAct {
  id                String   @id @default(cuid())
  convocatoria_id   String                    // v6 fix R3-S1: SIN @unique (puede haber múltiples
                                              // actas por convocatoria: VIGENTE + VOIDED tras reverse).
                                              // Unicidad parcial vía migration raw — ver abajo.
  generated_at      DateTime @default(now())
  closing_admin_id  String                    // quién inició
  confirming_admin_id String                  // quién confirmó
  ranking_snapshot_id String                  // snapshot que se congeló
  total_candidatos  Int
  total_aptos       Int
  total_no_aptos    Int
  pdf_url           String                    // path en object storage (S3/MinIO)
  pdf_sha256        String                    // hash del PDF como prueba de inmutabilidad
  status            CloseActStatus  @default(VIGENTE)  // v6 fix R2-S2

  organization_id   String

  convocatoria      Convocatoria @relation(fields: [convocatoria_id], references: [id])

  @@index([convocatoria_id])
}

enum CloseActStatus {
  VIGENTE          // acta válida del cierre actual
  VOIDED           // anulada por reversa en ventana 24h (queda como evidencia)
}
```

El acta se genera con Puppeteer al ejecutar el cierre. Contiene: nombre de convocatoria, fecha, admins involucrados, ranking final completo, listado de aptos, listado de no aptos, y el hash SHA256 al pie como huella de integridad.

**Persistencia del PDF:** object storage con WORM retention (write-once-read-many). El path en `pdf_url` apunta al storage backend (S3 / MinIO en self-host). Backup automático del bucket al menos una vez al día. **No se almacena en filesystem local del contenedor**, que se pierde al redeploy.

**Reversa de un cierre y act voided:** si SUPER_ADMIN ejecuta `/close/reverse` dentro de 24h, este registro pasa a `status = VOIDED` y queda como evidencia auditiva. **No se borra**. Si la convocatoria se cierra de nuevo más tarde, se genera una NUEVA fila `ConvocatoriaCloseAct` con su propio PDF y SHA256. Pueden coexistir múltiples actas con la misma `convocatoria_id` — solo UNA con `status = VIGENTE`. Constraint parcial (raw migration):

```sql
CREATE UNIQUE INDEX close_act_one_vigente_per_convocatoria
  ON "ConvocatoriaCloseAct" (convocatoria_id)
  WHERE status = 'VIGENTE';
```

### 8.3.15 AuditLog — Audit log de acciones administrativas (NUEVO v6)

Registro de toda acción administrativa sensible.

```prisma
model AuditLog {
  id              String   @id @default(cuid())
  actor_id        String                  // user_id de quien actuó
  actor_role      UserRole
  action          AuditAction             // qué hizo
  target_type     String                  // "Convocatoria", "Attempt", "User", etc.
  target_id       String                  // id del objeto afectado
  details         Json                    // contexto: campos antes/después, motivo, etc.
  ip_address      String?
  user_agent      String?
  organization_id String
  created_at      DateTime @default(now())

  @@index([actor_id])
  @@index([action, created_at])
  @@index([target_type, target_id])
}

enum AuditAction {
  CONVOCATORIA_CREATE
  CONVOCATORIA_EDIT
  CONVOCATORIA_CLOSE_INITIATE
  CONVOCATORIA_CLOSE_CONFIRM
  CONVOCATORIA_CLOSE_ABORT          // v6 fix R3-C3
  CONVOCATORIA_CLOSE_REVERSE
  ATTEMPT_OVERRIDE_VIA_AUDIT
  ATTEMPT_RECATEGORIZE_TECHNICAL
  CRITERIA_VERSION_ACTIVATE
  STUDENT_DATA_EXPORT
  STUDENT_DATA_EXPORT_DOWNLOAD      // v6 fix R3: log de DESCARGA del ZIP
  STUDENT_DATA_DELETE
  STUDENT_DATA_FORGET_APPROVE       // v6 fix R3: SUPER_ADMIN aprueba forget
  STUDENT_DATA_ANONYMIZE            // v6 fix R3: anonimización efectiva (post-LOCKED + plazo)
  OUTCOME_AMENDMENT_REGISTER        // v6 fix R3: F6 — recurso administrativo
  RFID_ASSIGN
  RFID_REVOKE
  USER_ROLE_CHANGE
}
```

Cada acción crítica del backend escribe en `AuditLog` antes de retornar al cliente. Si el `INSERT AuditLog` falla, la acción falla — no hay acción sin trazabilidad.

### 8.3.16 GdprDataExport — Solicitudes GDPR (NUEVO v6)

Right-to-access del candidato sobre sus datos personales.

```prisma
model GdprDataExport {
  id              String   @id @default(cuid())
  student_id      String
  requested_at    DateTime @default(now())
  status          GdprStatus @default(PENDING)
  generated_at    DateTime?
  export_url      String?            // ZIP con todos los datos del alumno
  expires_at      DateTime?          // URL expira a las 7 días
  organization_id String

  @@index([student_id, status])
}

enum GdprStatus {
  PENDING
  GENERATING
  READY
  EXPIRED
  ERROR
}
```

El export incluye: datos personales del candidato, todos sus attempts (raw_samples + normalized + events + score_audit), todas sus solicitudes de auditoría, su outcome final si aplica. Se entrega como ZIP descargable durante 7 días.

## 8.4 Endpoints — catálogo completo (con NUEVOS de v5 y v6)

```
═══════════════════════════════════════════════════════════
AUTH (sin cambios)
═══════════════════════════════════════════════════════════
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /auth/me
POST   /auth/csrf-token

═══════════════════════════════════════════════════════════
CONVOCATORIAS  (v5 + cierre reforzado v6)
═══════════════════════════════════════════════════════════
GET    /convocatorias                       listado
GET    /convocatorias/:id                   detalle
POST   /convocatorias                       crear (admin)
                                            body: {name, closes_at, plazas,
                                                   ruta_principal_id, rutas_ids[]}
                                            ruta_principal_id OPCIONAL al crear (puede asignarse después)
                                            VALIDADO obligatorio antes del primer ranking publicado
                                            (chequeo service-side, no en POST)
PATCH  /convocatorias/:id                   editar (solo si OPEN)

────  CIERRE REFORZADO (NUEVO v6) — flujo de tres pasos  ────

POST   /convocatorias/:id/close/preview     PASO 1: admin solicita preview
                                            → { ranking_final_simulado,
                                                aptos_count, no_aptos_count,
                                                advertencias[] }

POST   /convocatorias/:id/close/initiate    PASO 2: admin inicia cierre
                                            (status OPEN → CLOSING)
                                            registra closing_admin_id
                                            body: {confirmation_text: "<nombre exacto>"}

POST   /convocatorias/:id/close/confirm     PASO 3: SEGUNDO admin confirma
                                            (status CLOSING → CLOSED)
                                            VALIDA: confirming_admin_id != closing_admin_id
                                            Genera acta PDF, popula CandidateOutcome[]
                                            body: {confirmation_text: "<nombre exacto>"}

POST   /convocatorias/:id/close/abort       v6 fix R3-C3: cancela CLOSING → OPEN
                                            Auth: closing_admin_id (el que inició)
                                            O cualquier SUPER_ADMIN
                                            body: {reason: <obligatorio, mín 30 chars>}
                                            Solo válido si status = CLOSING

POST   /convocatorias/:id/close/reverse     Ventana 24h post-CLOSED
                                            Solo SUPER_ADMIN
                                            body: {reason: <obligatorio, mín 50 chars>}
                                            Después de 24h: rechazado

GET    /convocatorias/:id/acta              Descargar acta PDF
                                            Solo si status = CLOSED o LOCKED

GET    /convocatorias/:id/ranking           ranking actual (último snapshot)
GET    /convocatorias/:id/ranking/history   listado de snapshots
GET    /convocatorias/:id/outcomes          decisiones finales (solo CLOSED/LOCKED)

═══════════════════════════════════════════════════════════
GDPR / PRIVACIDAD  (NUEVOS v6)
═══════════════════════════════════════════════════════════
POST   /students/me/data-export             ALUMNO solicita export de sus datos
                                            → genera ZIP en background, email cuando ready
GET    /students/me/data-exports            ALUMNO lista sus solicitudes
GET    /gdpr/exports/:id/download           descarga ZIP (autenticado)
                                            v6 fix R3: backend valida
                                              export.student_id == auth.user.student_id
                                              (excepto SUPER_ADMIN)
                                            URL firmada expira 7d
                                            Cada descarga → AuditLog STUDENT_DATA_EXPORT_DOWNLOAD
POST   /students/me/forget-request          ALUMNO solicita borrado
                                            (procesa admin, no auto)
GET    /admin/gdpr/forget-requests          admin lista pendientes
POST   /admin/gdpr/forget-requests/:id/approve  admin aprueba (con justificación)

═══════════════════════════════════════════════════════════
ATTEMPTS
═══════════════════════════════════════════════════════════
POST   /attempts                            crear
                                            v6: pinned criteria_version,
                                            normalizer_version, detector_version
                                            (las activas EN ESE MOMENTO)
POST   /attempts/:id/upload                 subir archivo sensor
POST   /attempts/:id/sync-webfleet          sync Webfleet
POST   /attempts/:id/close                  detect+score+freeze
                                            (las versiones ya están pinned desde la creación)
GET    /attempts/:id                        detalle
GET    /attempts/:id/audit                  score_audit granular
POST   /attempts/:id/audit-request          ALUMNO solicita auditoría
                                            body: {reason}
POST   /attempts/:id/reevaluate             MANAGER crea reevaluación
                                            body: {audit_request_id, reason}
GET    /attempts                            listado paginado

═══════════════════════════════════════════════════════════
DOBACK ELITE — sync (NUEVO v6)
═══════════════════════════════════════════════════════════
POST   /doback/upload                       Doback Elite POST datos crudos
                                            body: {attempt_id, samples_blob,
                                                   device_id, signature}
                                            Auth: device JWT (pairing token)
                                            → marca attempt.doback_synced_at = now()

GET    /doback/attempts/awaiting-sync       Doback Elite GET attempts pendientes
                                            (en caso de que el dispositivo esté
                                            desconectado y necesite saber qué subir
                                            al reconectar)
                                            Auth: device JWT

═══════════════════════════════════════════════════════════
AUDITORÍAS  (NUEVOS v5)
═══════════════════════════════════════════════════════════
GET    /audit-requests                      listado para manager
GET    /audit-requests/:id                  detalle
PATCH  /audit-requests/:id                  manager actualiza status
                                            body: {status, resolution}

═══════════════════════════════════════════════════════════
MATRIZ
═══════════════════════════════════════════════════════════
GET    /matrix?convocatoria=X               datos para matriz

═══════════════════════════════════════════════════════════
ALUMNOS — endpoints "me" (auth.user.student_id implícito) + admin/manager
═══════════════════════════════════════════════════════════

# Endpoints que usa el alumno para SUS PROPIOS datos:
GET    /students/me                         detalle propio
GET    /students/me/history                 historial propio
GET    /students/me/attempts/:aid           detalle pedagógico (validar pertenencia)
GET    /students/me/evolution               módulo evolución propio
GET    /students/me/standings               progreso en TODAS sus convocatorias activas
                                            (v6 fix R3: PLURAL — multi-enrollment soportado)
                                            → Array<{
                                                convocatoria_id,
                                                convocatoria_name,
                                                puesto, nota_media,
                                                dentro_del_corte,
                                                total_candidatos, plazas
                                              }>
                                            Si solo hay 1 enrollment activo, array con 1 elemento.

# Endpoints que usa MANAGER/ADMIN para inspeccionar a un alumno concreto:
GET    /students/:id                        detalle (rol ≥ MANAGER)
GET    /students/:id/history                historial (rol ≥ MANAGER)
GET    /students/:id/attempts/:aid          detalle pedagógico (rol ≥ MANAGER)
GET    /students/:id/evolution              evolución (rol ≥ MANAGER)
# NO existe /students/:id/standing — el ranking es del manager,
# ver /convocatorias/:id/ranking. Esto evita enumeration de IDs.

═══════════════════════════════════════════════════════════
RUTAS
═══════════════════════════════════════════════════════════
GET    /routes                              CRUD
POST   /routes
PATCH  /routes/:id
DELETE /routes/:id
GET    /routes/:id/cohort-stats             análisis convocatoria
                                            (renombrado: ahora es por convocatoria)

═══════════════════════════════════════════════════════════
RFID
═══════════════════════════════════════════════════════════
GET    /rfid                                listado tarjetas
POST   /rfid                                registrar
POST   /rfid/:id/assign                     asignar a alumno
DELETE /rfid/:id/assign                     desasignar
DELETE /rfid/:id                            desactivar

═══════════════════════════════════════════════════════════
SCORING + SIMULADOR (con dimensión RANKING — UPGRADE v5)
═══════════════════════════════════════════════════════════
GET    /scoring/versions                    listado
GET    /scoring/versions/:id                detalle
POST   /scoring/versions                    crea (admin)
POST   /scoring/versions/:id/activate       activa

POST   /scoring/simulate                    SIMULADOR (mejorado v5)
                                            body: {
                                              criteria_overrides: {...},
                                              convocatoria_id: string
                                            }
                                            →
                                            {
                                              attempts_simulated: [...],
                                              ranking_original: [...],
                                              ranking_simulado: [...],
                                              candidatos_que_cruzan_corte: [
                                                { id, dirección: 'entra'|'sale' }
                                              ],
                                              summary: {
                                                cambios_decision_total: int,
                                                attempts_afectados: int,
                                                diff_nota_media: float
                                              }
                                            }

═══════════════════════════════════════════════════════════
KIOSKO
═══════════════════════════════════════════════════════════
POST   /kiosko/pair                         pairing inicial
POST   /kiosko/rfid-tap                     registrar tap RFID
GET    /kiosko/state                        estado actual
POST   /kiosko/sync                         sync de eventos pendientes
POST   /kiosko/heartbeat                    kiosko vivo

═══════════════════════════════════════════════════════════
ADMIN — Kioskos
═══════════════════════════════════════════════════════════
GET    /admin/kioskos                       listado
DELETE /admin/kioskos/:id/pair              revoca pairing

═══════════════════════════════════════════════════════════
HEALTH
═══════════════════════════════════════════════════════════
GET    /health
GET    /health/deep                         DB + Redis + Webfleet
```

## 8.5 packages/ranking — el nuevo motor (v5)

`packages/ranking` es **PURO** (no toca DB). Recibe los attempts y la configuración de la convocatoria. Devuelve un ordenamiento.

```typescript
// packages/ranking/index.ts

interface RankingInput {
  convocatoria: {
    id: string;
    plazas: number;
    rutas: { id: string; peso: number }[];
    ruta_principal_id: string | null;
    closes_at_iso: string;        // v6 fix R3: incluido para sorteo
  };
  enrollments: {                  // v6 fix R3: enrollments, no candidates
    id: string;                   // enrollment_id
    student_id: string;           // referencia al humano (para audit log)
    attempts: Array<{
      route_id: string;
      score: number | null;       // null si no completado
      status: AttemptStatus;
      data_quality: DataQuality | null;
      stability_family_score: number | null;
    }>;
  }[];
}

interface RankingOutput {
  entries: Array<{
    enrollment_id: string;        // v6 fix R3: enrollment, no candidato
    puesto: number;
    nota_media: number;
    rutas_completadas: number;
    rutas_total: number;
    dentro_del_corte: boolean;
    tiebreak_key: string;
  }>;
}

export function computeRanking(input: RankingInput): RankingOutput;
```

**Lógica de la cascada de desempate (V1, refinada tras review):**

```
   1° Mejor nota en ruta_principal_id
      Si ALGUNO de los empatados NO completó la ruta principal,
      este criterio se SALTA para esos candidatos y se aplica el
      criterio 2 directamente entre todos los empatados.
      Esto se documenta en el tiebreak_key persistido.

   2° Menor TASA de attempts con data_quality = LOW
      Cálculo: count(attempts WHERE data_quality = LOW)
             ÷ count(attempts WHERE data_quality IS NOT NULL)
      Es decir: PROPORCIÓN, no número absoluto.
      Esto evita que un candidato que abandonó muchas rutas
      (ABANDONED no tiene data_quality) gane el desempate sobre
      uno que las completó pero con calidad media.
      Si el divisor es 0 (candidato sin ningún attempt CLOSED), salta a #3.

   3° Mejor nota promedio en familia "estabilidad"
      Solo considera attempts CLOSED del candidato.

   4° Sorteo determinista
      Semilla = SHA256(convocatoria_id + enrollment_id + closes_at_iso)
      Incluir closes_at_iso evita que el sorteo sea predecible
      antes de que se anuncie la fecha de cierre.
      Usar enrollment_id (no student_id) garantiza que el sorteo
      es estable POR INSCRIPCIÓN — un mismo humano en dos
      convocatorias distintas tiene sorteos independientes.
      Documentado y auditable.
```

## 8.6 Cron job ranking nocturno

```typescript
// apps/worker/src/jobs/rankingCron.ts

// BullMQ repeatable job, cron pattern: "0 6 * * *" (6:00 AM diario)
// Para cada convocatoria con status = OPEN:
//   1. Recoger todos los attempts cerrados con status CLOSED
//   2. Llamar packages/ranking.computeRanking
//   3. Persistir RankingSnapshot + RankingEntry[]
//   4. is_final = false (será true solo al cierre)
```

## 8.7 Cierre de convocatoria — flujo de 3 pasos

> **El endpoint legacy `POST /convocatorias/:id/close` (single-step) NO se implementa.** Fue reemplazado en v6 por el flujo reforzado de 3 pasos descrito en D22 y en el catálogo de endpoints (§8.4). Pseudocódigo abajo.

### 8.7.1 `POST /convocatorias/:id/close/preview` — solo lectura

```typescript
// apps/api/src/routes/convocatorias/closePreview.ts

POST /convocatorias/:id/close/preview
// Auth: ADMIN (cualquiera)
// Lógica:
// 1. SELECT convocatoria; validar status = OPEN
// 2. Calcular ranking final SIMULADO (computeRanking con attempts CLOSED actuales)
// 3. Calcular advertencias: candidatos sin completar todas las rutas,
//    auditorías pendientes, attempts en PENDING_*_REVIEW, etc.
// 4. RETURN { ranking_final_simulado, aptos_count, no_aptos_count, advertencias[] }
//    NO PERSISTE nada. Idempotente.
```

### 8.7.2 `POST /convocatorias/:id/close/initiate` — primer admin

```typescript
POST /convocatorias/:id/close/initiate
// Auth: ADMIN
// Body: { confirmation_text }
// Lógica:
// 1. Validar confirmation_text === convocatoria.name
// 2. UPDATE atómico:
//      UPDATE convocatoria
//      SET status='CLOSING', closing_admin_id=$me, closing_initiated_at=NOW()
//      WHERE id=$id AND status='OPEN'
//      RETURNING *;
//    Si filas afectadas = 0 → 409 (otro admin ganó el race)
// 3. Insertar AuditLog: CONVOCATORIA_CLOSE_INITIATE
// 4. RETURN convocatoria actualizada
```

### 8.7.3 `POST /convocatorias/:id/close/confirm` — segundo admin

```typescript
POST /convocatorias/:id/close/confirm
// Auth: ADMIN + RE-AUTH (re-introducir contraseña)
// Body: { confirmation_text, password }
// Lógica:
// 1. Re-validar contraseña del usuario
// 2. SELECT convocatoria; validar status = CLOSING
// 3. VALIDAR auth.user.id !== convocatoria.closing_admin_id  (si igual → 403)
// 4. Validar confirmation_text === convocatoria.name
// 5. Transacción:
//    a. Calcular ranking final (computeRanking)
//    b. INSERT RankingSnapshot { is_final: true, ... }
//    c. Para cada Enrollment:
//         INSERT CandidateOutcome { enrollment_id, decision, puesto, ... }
//    d. Generar acta PDF con Puppeteer; calcular SHA256
//    e. Persistir el PDF en object storage; INSERT ConvocatoriaCloseAct
//    f. UPDATE convocatoria
//         SET status='CLOSED', closed_at=NOW(),
//             confirming_admin_id=$me,
//             reversal_window_until=$now_plus_24h_wallclock_madrid
//    g. Insertar AuditLog: CONVOCATORIA_CLOSE_CONFIRM
//    h. Encolar job notifications.convocatoria_closed (Fase 2)
// 6. RETURN { acta_url, candidate_outcomes_count }
//
// Constraint DB activado en este punto (v6 fix R3-S3, refinado):
//
//   TRIGGER ranking_snapshot_immutability:
//     Rechaza UPDATE de cualquier campo de RankingSnapshot DONDE is_final=true,
//     EXCEPTO los campos `voided_at`, `voided_by`, `voided_reason`
//     (que sí se actualizan durante /close/reverse).
//
//   TRIGGER convocatoria_closed_immutability:
//     Rechaza UPDATE de Convocatoria DONDE status='LOCKED' (sin excepciones).
//     Para status='CLOSED', rechaza UPDATE de campos "value-bearing"
//     (closes_at, plazas, ruta_principal_id, name) PERO permite UPDATE
//     de los campos del flujo de cierre/reversa: status, reversed_at,
//     reversed_by, reversal_reason, closing_admin_id, closing_initiated_at,
//     confirming_admin_id, closed_at, reversal_window_until.
//
//   TRIGGER candidate_outcome_immutability:
//     Rechaza UPDATE de campos "value-bearing" (decision, puesto_final,
//     nota_media_final). PERMITE UPDATE de superseded_at/_by/_reason
//     (campos de reversa).
//
//   Estos triggers son consistentes entre sí: el reverse del §8.7.4
//   solo toca los campos explícitamente permitidos.
```

### 8.7.4 `POST /convocatorias/:id/close/reverse` — SUPER_ADMIN, 24h

```typescript
POST /convocatorias/:id/close/reverse
// Auth: SUPER_ADMIN (sí o sí)
// Body: { reason }  // mínimo 50 chars
// Lógica:
// 1. SELECT convocatoria; validar status = CLOSED y NOW < reversal_window_until
// 2. Validar reason.length >= 50
// 3. Transacción:
//    a. UPDATE RankingSnapshot SET voided_at=NOW(), voided_by=$me, voided_reason=$reason
//       WHERE convocatoria_id=$id AND is_final=true AND voided_at IS NULL
//    b. UPDATE CandidateOutcome
//         SET superseded_at=NOW(), superseded_by=$me, superseded_reason=$reason  // v6 fix R3
//       WHERE convocatoria_id=$id AND superseded_at IS NULL
//    c. UPDATE ConvocatoriaCloseAct SET status='VOIDED'
//       WHERE convocatoria_id=$id AND status='VIGENTE'
//    d. UPDATE convocatoria
//         SET status='OPEN',
//             reversed_at=NOW(),
//             reversed_by=$me,
//             reversal_reason=$reason,
//             closing_admin_id=NULL,
//             closing_initiated_at=NULL,
//             confirming_admin_id=NULL,
//             closed_at=NULL,
//             reversal_window_until=NULL
//    e. AuditLog: CONVOCATORIA_CLOSE_REVERSE
// 4. NOTA: las rows VOIDED quedan como evidencia. Nunca se borran.
//          Si la convocatoria se cierra de nuevo, se generan filas
//          NUEVAS (snapshot, outcomes, acta) — no se modifican las viejas.
```

### 8.7.5 `POST /convocatorias/:id/close/abort` — cancelar cierre en CLOSING (v6 fix R3-C3)

```typescript
POST /convocatorias/:id/close/abort
// Auth: ADMIN que sea closing_admin_id, O cualquier SUPER_ADMIN
// Body: { reason }   // mínimo 30 chars
// Lógica:
// 1. SELECT convocatoria; validar status = CLOSING
// 2. Validar:
//    a. auth.user.id === convocatoria.closing_admin_id, O
//    b. auth.user.role === 'SUPER_ADMIN'
// 3. UPDATE atómico:
//      UPDATE convocatoria
//      SET status='OPEN',
//          closing_admin_id=NULL,
//          closing_initiated_at=NULL
//      WHERE id=$id AND status='CLOSING'
//      RETURNING *;
//    Si filas afectadas = 0 → 409 (alguien más ya hizo abort/confirm)
// 4. AuditLog: CONVOCATORIA_CLOSE_ABORT
//    detail: { reason, previous_closing_admin_id }
// 5. RETURN convocatoria actualizada
```

### 8.7.6 Cron de transición CLOSED → LOCKED

```typescript
// apps/worker/src/jobs/lockClosedConvocatorias.ts
// Cron pattern: */15 * * * *  (cada 15 min, TZ='Europe/Madrid')

UPDATE convocatoria
SET status = 'LOCKED'
WHERE status = 'CLOSED' AND reversal_window_until < NOW();

// Tras LOCKED: ningún endpoint /close/reverse acepta. Inmutable absoluto.
// Excepción: F6 (Fase 2) — OutcomeAmendment puede agregarse a una LOCKED.
```

## 8.8 Tu calendario 14 días

```
DÍA  TAREA
───  ────────────────────────────────────────────
1    Setup repo, monorepo, workspaces (8 packages)
2    Schema Prisma completo (con Convocatoria expandida,
     Attempt sin decision, RankingSnapshot, CandidateOutcome,
     AuditRequest) + migración + /health
3    Auth (3 roles) + middlewares + CRUD básico Convocatoria
4    Package normalization + tests
5    Detector extraído (PURO) + endpoint upload (idempotente)
8    Motor scoring + score_audit + endpoint /close
     packages/ranking + lógica desempate
9    Cron ranking nocturno + endpoint /convocatorias/:id/ranking
     Endpoints audit-request + reevaluate
10   Endpoints admin (rutas, RFID, scoring read-only)
     Endpoints cierre completos: /close/preview, /close/initiate,
     /close/confirm, /close/abort, /close/reverse + ConvocatoriaCloseAct +
     CandidateOutcome (ver §8.7)
11   Endpoint /scoring/simulate con dimensión ranking completo
12   Datos seed completos + verificación end-to-end
13-14 Soporte demo y bug fixes
```

## 8.9 Criterios de "tu trabajo está bien hecho"

```
   ✓ Tests determinísticos en normalization, detection, scoring, ranking
   ✓ Comando `replay <attempt_id>` reproduce score exacto
   ✓ Subir mismo archivo 2 veces no duplica samples
   ✓ Cerrar attempt e intentar mutarlo falla con error claro
   ✓ Cambiar criteria_version no afecta attempts cerrados
   ✓ Ranking nocturno corre y persiste snapshot
   ✓ Cierre de convocatoria emite CandidateOutcome para todos
   ✓ Convocatoria cerrada NO se puede reabrir (DB constraint)
   ✓ Simulator devuelve ranking_original + ranking_simulado
     + candidatos_que_cruzan_corte
   ✓ AttemptStatus distingue ABANDONED vs ABORTED_TECHNICAL
   ✓ Cero console.log en producción
   ✓ Cero `: any` nuevos sin justificación
   ✓ requireOrg en TODOS los endpoints excepto los públicos
```

---


# 9. PARA ALEJANDRO — Frontend completo

## 9.1 Tu rol

```
   ┌──────────────────────────────────────────────────────┐
   │  TU TERRITORIO                                       │
   │                                                      │
   │  apps/web/ ENTERO:                                   │
   │  · 4 portales: Manager, Alumno, Admin, Kiosko        │
   │  · Pantallas v5 nuevas: Ranking, Estado del alumno,  │
   │    Cierre de convocatoria, Audit request             │
   │  · Wrappers: <MapViewer>, <Timeline>, <Matrix>,      │
   │    <Ranking>, <ScoreBreakdown>, <ConfidenceBadge>    │
   │  · Estado global (Zustand + React Query)             │
   │  · Tests Vitest + tests críticos Playwright          │
   │                                                      │
   │  NO TOCÁS:                                           │
   │  · backend (apps/api, apps/worker, packages)         │
   │  · prisma/schema.prisma                              │
   └──────────────────────────────────────────────────────┘
```

## 9.2 Reglas no negociables

```
   1. TODAS las URLs en config/api.ts (no hardcodear)
   2. React Query SIEMPRE para datos del servidor
   3. Zustand SOLO para estado UI / kiosko offline
   4. Componentes <500 líneas
   5. Wrappers para librerías externas
   6. Dark mode kiosko REQUISITO
   7. Eventos low confidence se MUESTRAN, no se esconden
   8. Audit request del alumno con justificación obligatoria
   9. TypeScript strict, cero `any` sin justificar
   10. Notas son inmutables. Manager NO modifica notas (solo audit).
```

## 9.3 Estructura de carpetas (con pantallas v5)

```
training/apps/web/
├── src/
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginAdmin.tsx
│   │   │   ├── LoginManager.tsx
│   │   │   └── LoginAlumno.tsx
│   │   │
│   │   ├── manager/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ConvocatoriaList.tsx
│   │   │   ├── Matrix.tsx                    ← M4
│   │   │   ├── Ranking.tsx                   ← M5 NUEVO v5
│   │   │   ├── AttemptDetail.tsx             ← M6 (era M5)
│   │   │   ├── AuditRequestModal.tsx         ← M7 NUEVO v5
│   │   │   ├── StudentProfile.tsx
│   │   │   └── RouteAnalysis.tsx
│   │   │
│   │   ├── alumno/
│   │   │   ├── Dashboard.tsx                 ← incluye estado convocatoria
│   │   │   ├── History.tsx
│   │   │   ├── AttemptPedagogical.tsx
│   │   │   ├── AuditRequestForm.tsx          ← NUEVO v5
│   │   │   └── Evolution.tsx
│   │   │
│   │   ├── admin/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Convocatorias.tsx             ← v5 expandido
│   │   │   ├── ConvocatoriaEditor.tsx        ← v5 con plazas, fecha cierre
│   │   │   ├── ConvocatoriaClose.tsx         ← NUEVO v5
│   │   │   ├── Routes.tsx
│   │   │   ├── RouteEditor.tsx
│   │   │   ├── RfidCards.tsx
│   │   │   ├── Kioskos.tsx
│   │   │   ├── KioskoPairing.tsx
│   │   │   ├── ScoringVersions.tsx
│   │   │   ├── ScoringSimulator.tsx          ← v5 con ranking dimension
│   │   │   └── Users.tsx
│   │   │
│   │   └── kiosko/
│   │       ├── Pairing.tsx
│   │       ├── Idle.tsx
│   │       ├── Active.tsx
│   │       ├── Recovery.tsx
│   │       └── AdminPanel.tsx
│   │
│   ├── components/
│   │   ├── MapViewer/
│   │   ├── Timeline/
│   │   ├── Matrix/
│   │   ├── Ranking/                          ← NUEVO v5
│   │   ├── StandingCard/                     ← NUEVO v5 (estado alumno)
│   │   ├── ScoreBreakdown/
│   │   ├── ConfidenceBadge/
│   │   ├── DataQualityBadge/
│   │   ├── AuditRequestModal/                ← NUEVO v5
│   │   └── ui/
│   │
│   ├── stores/
│   │   ├── auth.store.ts
│   │   ├── ui.store.ts
│   │   └── kiosko.store.ts
│   │
│   ├── api/
│   │   ├── attempts.ts
│   │   ├── students.ts
│   │   ├── convocatorias.ts                  ← NUEVO v5
│   │   ├── ranking.ts                        ← NUEVO v5
│   │   ├── audit.ts                          ← NUEVO v5
│   │   ├── matrix.ts
│   │   ├── routes.ts
│   │   └── ...
│   │
│   ├── config/
│   │   └── api.ts
│   │
│   └── App.tsx
```

## 9.4 PORTAL MANAGER — pantallas

### M1 — Login Manager

`POST /auth/login` con `role: MANAGER`. Estados: idle/submitting/error.

### M2 — Dashboard Manager

```
   ┌─────────────────────────────────────────────────────┐
   │ Hola, Carlos │ notif (3) │ logout                   │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  CONVOCATORIAS ACTIVAS                              │
   │  ┌──────────────────┐  ┌──────────────────┐         │
   │  │ Convocatoria 26-A│  │ Convocatoria 26-B│         │
   │  │ 200 candidatos   │  │ 150 candidatos   │         │
   │  │ Plazas: 50       │  │ Plazas: 30       │         │
   │  │ Cierre: 15/06/26 │  │ Cierre: 30/06/26 │         │
   │  │ ⚠ 3 auditorías   │  │                  │         │
   │  │ [VER MATRIZ]     │  │ [VER MATRIZ]     │         │
   │  │ [VER RANKING]    │  │ [VER RANKING]    │         │
   │  └──────────────────┘  └──────────────────┘         │
   │                                                     │
   │  AUDITORÍAS PENDIENTES                              │
   │  ┌─────────────────────────────────────────┐        │
   │  │ Juan P. · Ruta A · solicitud 14/05      │        │
   │  │ Maria G. · Ruta C · solicitud 13/05     │        │
   │  └─────────────────────────────────────────┘        │
   │                                                     │
   └─────────────────────────────────────────────────────┘
```

### M3 — Lista de Convocatorias

`GET /convocatorias`. Filtros: open/closing/closed. Click → M4 (Matrix).

### M4 — La Matriz (alumno × ruta)

Sin cambios mayores respecto a v4, pero cada celda muestra **solo nota**, no APTO/NO_APTO.

```
   ┌───────────────────────────────────────────────────────────────┐
   │ Convocatoria 2026-A · 200 candidatos · Plazas: 50            │
   │ [Ver RANKING ▶]  Filtros: ...                                │
   ├───────────────────────────────────────────────────────────────┤
   │              RUTA-A    RUTA-B    RUTA-C    RUTA-D             │
   │            ┌────────┬────────┬────────┬────────┐              │
   │  Alumno1   │ 8.8 HQ │ 7.2    │ — pend │ — no   │              │
   │            ├────────┼────────┼────────┼────────┤              │
   │  Alumno2   │ 6.5    │ 7.0    │ 5.8    │ 7.2    │              │
   │            │  HQ    │  HQ    │ LQ ⚠   │  HQ    │              │
   │            ├────────┼────────┼────────┼────────┤              │
   │  Alumno3   │ —      │ — pend │ —      │ —      │              │
   │            └────────┴────────┴────────┴────────┘              │
   │                                                               │
   │  Click celda  → Vista del Examinador (M6)                     │
   │  Click fila   → Perfil del Alumno                             │
   │  Click columna→ Análisis de Ruta                              │
   └───────────────────────────────────────────────────────────────┘
```

### M5 — Ranking (NUEVO v5) — ★ pieza visual clave para el cliente

```
   ┌──────────────────────────────────────────────────────────────────┐
   │ Ranking · Convocatoria 2026-A                                    │
   │ Plazas: 50 · Total candidatos: 200                               │
   │ Última actualización: 14/05/26 06:00                             │
   │ Estado: PROVISIONAL                                              │
   │                                                                  │
   │ Filtros: [solo dentro del corte ▾] [solo con auditoría ▾] ...    │
   ├──────────────────────────────────────────────────────────────────┤
   │                                                                  │
   │ PUESTO  CANDIDATO          NOTA   RUTAS    AUDITORÍAS  CORTE     │
   │ ─────   ────────           ────   ─────    ──────────  ─────     │
   │   1     Juan Pérez         8.86   4 / 4    —           ✓ DENTRO  │
   │   2     Pedro López        8.45   4 / 4    —           ✓ DENTRO  │
   │   3     María García       8.21   4 / 4    1 ⚠         ✓ DENTRO  │
   │   ...                                                            │
   │  49     Ana Romero         6.63   4 / 4    —           ✓ DENTRO  │
   │  50     Diego Fernández    6.50   3 / 4    —           ✓ DENTRO  │
   │ ─────────────────────────  CORTE PROVISIONAL  ─────────────────  │
   │  51     Luis Castro        6.45   4 / 4    —           ✗ FUERA   │
   │  52     Carla Soto         6.40   3 / 4    —           ✗ FUERA   │
   │   ...                                                            │
   │ 200     Marta Bello        2.10   1 / 4    —           ✗ FUERA   │
   │                                                                  │
   │ Click fila → perfil del alumno                                   │
   │ Click "auditoría" → ver detalle de la solicitud                  │
   └──────────────────────────────────────────────────────────────────┘
```

**Interactividad:**
- Click fila → Perfil del alumno (no su Detalle del Examinador)
- Click ⚠ (auditoría) → modal con auditoría pendiente
- Auto-refresh cada 60s (pero el dato de fondo se recalcula 1x/día)
- Indicador "Estado: PROVISIONAL" hasta el cierre. Tras el cierre: "Estado: FINAL".

### M6 — Vista del Examinador (detalle de attempt) — sin override

Cambio importante v5: **NO hay botón "SOBREESCRIBIR VEREDICTO"**. El manager ve la información completa pero no modifica.

```
   ┌──────────────────────────────────────────────────────────────┐
   │ ← volver  │  Juan Pérez · Ruta A · 14/05 09:32 · 8.8        │
   │           │  data_quality: HIGH ✓   detector: v1.3           │
   │           │  criteria: v2.1                                  │
   ├──────────────────────────────────────────────────────────────┤
   │                                                              │
   │  ┌──────────────────────┐  ┌──────────────────────────────┐  │
   │  │     <MapViewer>      │  │  <ScoreBreakdown>            │  │
   │  │   ruta + eventos     │  │  Estabilidad   3.4/4.0       │  │
   │  └──────────────────────┘  │  Velocidad     2.7/3.0       │  │
   │                            │  Ruta          1.4/1.5       │  │
   │                            │  Conducción    1.2/1.5       │  │
   │                            │  ──────────────────          │  │
   │                            │  TOTAL         8.8 / 10      │  │
   │                            └──────────────────────────────┘  │
   │                                                              │
   │  ┌─────────────────────────────────────────────────────────┐ │
   │  │  <Timeline> unificado (sensor + Webfleet)               │ │
   │  └─────────────────────────────────────────────────────────┘ │
   │                                                              │
   │  Si el alumno solicitó AUDITORÍA de este intento:            │
   │  ┌─────────────────────────────────────────────────────┐    │
   │  │ Solicitud de auditoría - 14/05 17:32                │    │
   │  │ Razón del alumno:                                   │    │
   │  │ "Hubo un atasco en la rotonda no previsible..."     │    │
   │  │ [REVISAR Y RESPONDER]                               │    │
   │  └─────────────────────────────────────────────────────┘    │
   │                                                              │
   │  [VOLVER A MATRIZ]                                           │
   │  (sin botones de override)                                   │
   └──────────────────────────────────────────────────────────────┘
```

### M7 — Audit Request Modal (NUEVO v5)

```
   ┌─────────────────────────────────────────────┐
   │ Auditoría — solicitada por Juan Pérez       │
   ├─────────────────────────────────────────────┤
   │                                             │
   │ Intento: Ruta A · 14/05 09:32 · nota 6.8    │
   │                                             │
   │ Razón del alumno:                           │
   │ ┌──────────────────────────────────────┐   │
   │ │ Hubo un atasco en la rotonda no       │   │
   │ │ previsible que me forzó a frenar      │   │
   │ │ varias veces.                          │   │
   │ └──────────────────────────────────────┘   │
   │                                             │
   │ Tu resolución:                              │
   │ ( ) Confirmar la nota original              │
   │ ( ) Crear reevaluación                      │
   │ ( ) Rechazar la solicitud (sin mérito)      │
   │     v6 fix R3: mapea a AuditStatus.REJECTED │
   │                                             │
   │ Justificación de tu decisión (obligatoria): │
   │ ┌──────────────────────────────────────┐   │
   │ │ Texto libre...                        │   │
   │ └──────────────────────────────────────┘   │
   │                                             │
   │ [CANCELAR]              [CONFIRMAR]         │
   └─────────────────────────────────────────────┘
```

Si el manager elige "Crear reevaluación" → POST /attempts/:id/reevaluate. Crea attempt nuevo con parent_attempt_id y audit_request_id.

### M8 — Perfil del Alumno

Sin cambios mayores. Muestra historial + evolución.

### M9 — Análisis de Ruta

Sin cambios mayores. Análisis de la ruta en toda la convocatoria.

## 9.5 PORTAL ALUMNO — pantallas

### A1 — Login Alumno

`POST /auth/login` con `role: ALUMNO`.

### A2 — Dashboard del Alumno (con StandingCard NUEVO v5)

```
   ┌─────────────────────────────────────────────────────┐
   │ Hola Juan,                                          │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  ┌─────────────────────────────────────────────┐   │
   │  │  TU PROGRESO EN LA CONVOCATORIA 2026-A      │   │ ← <StandingCard>
   │  │                                             │   │   NUEVO v5
   │  │  Rutas completadas: 3 de 4                  │   │
   │  │  Tu nota media:     7.4 / 10                │   │
   │  │                                             │   │
   │  │  Tu puesto provisional: 74 de 200           │   │
   │  │  Plazas: 50                                 │   │
   │  │                                             │   │
   │  │  ▼ Estás FUERA del corte provisional        │   │
   │  │    (provisional — el ranking final solo     │   │
   │  │     se conoce al cierre 15/06/26)           │   │
   │  └─────────────────────────────────────────────┘   │
   │                                                     │
   │  TUS RUTAS                                          │
   │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │
   │  │ Ruta A     │ │ Ruta B     │ │ Ruta C     │       │
   │  │ 8.8 / 10   │ │ 7.2 / 10   │ │ 5.8 / 10   │       │
   │  │ HQ ✓       │ │ HQ ✓       │ │ MQ         │       │
   │  │ último 25/4│ │ último 23/4│ │ último 23/4│       │
   │  │ [VER]      │ │ [VER]      │ │ [VER]      │       │
   │  └────────────┘ └────────────┘ └────────────┘       │
   │  ┌────────────┐                                     │
   │  │ Ruta D     │                                     │
   │  │ — pendiente│                                     │
   │  └────────────┘                                     │
   │                                                     │
   └─────────────────────────────────────────────────────┘
```

> NO se muestra "APTO" ni "NO_APTO" en ninguna ruta. Solo nota.

### A3 — Historial de Attempts

```
   ┌────────────────────────────────────────────────────────┐
   │ Tu historial completo                                  │
   ├────────────────────────────────────────────────────────┤
   │ FECHA       RUTA   NOTA   CALIDAD    AUDITORÍA         │
   │ ──────────────────────────────────────────────────     │
   │ 25/04 09:32 Ruta A 8.8    ✓ alta     —                 │
   │ 23/04 11:15 Ruta C 7.1    ✓ alta     ↻ reev de 5.8     │
   │ 23/04 10:00 Ruta C 5.8    ◐ media    Confirmada        │
   │ 20/04 09:00 Ruta B 7.6    ✓ alta     —                 │
   └────────────────────────────────────────────────────────┘
```

### A4 — Detalle Pedagógico

Idéntico a v4. **NO** muestra telemetría cruda. Botón nuevo: **"Solicitar auditoría"** (abre A5).

### A5 — Audit Request Form (NUEVO v5)

```
   ┌─────────────────────────────────────────────┐
   │ Solicitar auditoría                         │
   ├─────────────────────────────────────────────┤
   │                                             │
   │ Intento: Ruta C · 23/04 10:00 · nota 5.8    │
   │                                             │
   │ Razón (obligatoria, mínimo 30 caracteres):  │
   │ ┌──────────────────────────────────────┐   │
   │ │ Hubo un atasco en la rotonda no       │   │
   │ │ previsible que me forzó a frenar.     │   │
   │ └──────────────────────────────────────┘   │
   │                                             │
   │ Tu solicitud será revisada por un manager.  │
   │ Te notificaremos cuando haya resolución.    │
   │                                             │
   │ [CANCELAR]              [ENVIAR]            │
   └─────────────────────────────────────────────┘
```

### A6 — Módulo de Evolución

Sin cambios. Indicadores cualitativos ruta a ruta.

## 9.6 PORTAL ADMIN — pantallas

### D1 — Login Admin

### D2 — Dashboard Admin

```
   ┌─────────────────────────────────────────────────────┐
   │ Admin Dashboard                                     │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  CONVOCATORIAS                  ESTADO SISTEMA      │
   │  ┌──────────────────┐          ┌─────────────────┐  │
   │  │ 2026-A · OPEN    │          │ API: ✓          │  │
   │  │   Cierre 15/06   │          │ DB: ✓           │  │
   │  │   195/200 tienen │          │ Webfleet: 22%   │  │
   │  │   3+ rutas       │          │ uso cuota       │  │
   │  ├──────────────────┤          └─────────────────┘  │
   │  │ 2026-B · OPEN    │                                │
   │  │   Cierre 30/06   │          KIOSKOS               │
   │  └──────────────────┘          [4 listados]         │
   │                                                     │
   │  AUDITORÍAS PENDIENTES                              │
   │  ⚠ 3 solicitudes sin resolver                       │
   │                                                     │
   │  [Convocatorias] [Rutas] [RFID] [Kioskos]           │
   │  [Scoring] [Simulador] [Usuarios]                   │
   │                                                     │
   └─────────────────────────────────────────────────────┘
```

### D3 — CRUD Convocatorias (expandido v5)

```
   ┌────────────────────────────────────────────────────────┐
   │ Convocatorias                       [+ NUEVA CONV.]    │
   ├────────────────────────────────────────────────────────┤
   │ NOMBRE        STATUS  PLAZAS  CANDIDATOS  CIERRE       │
   │ ────────────────────────────────────────────────       │
   │ 2026-A        OPEN    50      200         15/06/26     │
   │ 2026-B        OPEN    30      150         30/06/26     │
   │ 2025-Q4       CLOSED  80      300         15/12/25     │
   └────────────────────────────────────────────────────────┘
```

Click → D4 (editor).

### D4 — Editor de Convocatoria (NUEVO v5)

```
   ┌──────────────────────────────────────────────────────┐
   │ Editar Convocatoria 2026-A                           │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │ Nombre [_2026-A_______________________]              │
   │ Inicio [01/04/2026]                                  │
   │ Cierre [15/06/2026]   ← público para los candidatos  │
   │                                                      │
   │ Plazas (entero) [_50_]   ← público desde el día 1    │
   │                                                      │
   │ Rutas obligatorias:                                  │
   │   ☑ Ruta A · Urbana centro                           │
   │   ☑ Ruta B · Carretera nacional                      │
   │   ☑ Ruta C · Mixta con rotonda                       │
   │   ☑ Ruta D · Polígono industrial                     │
   │                                                      │
   │ Ruta principal (criterio 1 de desempate):            │
   │   (•) Ruta A    ( ) Ruta B    ( ) Ruta C    ( ) Ruta D│
   │                                                      │
   │ Status: OPEN   [BOTÓN DE CIERRE — solo si fecha ya]  │
   │                                                      │
   │ [CANCELAR]                  [GUARDAR]                │
   └──────────────────────────────────────────────────────┘
```

### D5 — Cierre de Convocatoria (REESCRITO v6: flujo de 3 pasos)

El cierre es **un proceso secuencial** que la pantalla representa como tres estados distintos. La misma URL muestra UNO de los tres estados según el `convocatoria.status` y el rol del admin que entra.

#### D5-A — Estado "OPEN" — paso 1: Preview

Lo ve cualquier ADMIN cuando `convocatoria.status === 'OPEN'`. Es **solo lectura**.

```
   ┌──────────────────────────────────────────────────────┐
   │ Cerrar Convocatoria 2026-A — Paso 1 de 3 (PREVIEW)   │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  Fecha de cierre publicada: 15/06/2026 23:59 (Madrid)│
   │  Estado: OPEN                                        │
   │                                                      │
   │  RESUMEN DEL CIERRE PROVISIONAL                      │
   │  · 198 / 200 candidatos completaron las 4 rutas      │
   │  · 2 candidatos no completaron — sus rutas faltantes │
   │    contarán como 0                                   │
   │  · 0 auditorías pendientes                           │
   │                                                      │
   │  IMPACTO                                             │
   │  · 50 candidatos pasarían a APTO                     │
   │  · 150 candidatos pasarían a NO_APTO                 │
   │                                                      │
   │  [VER ranking final simulado ▾]                      │
   │                                                      │
   │  ────────────────────────────────────────            │
   │                                                      │
   │  Si querés iniciar el cierre formal, vas a necesitar │
   │  que un SEGUNDO admin distinto a vos lo confirme     │
   │  después.                                            │
   │                                                      │
   │  [CANCELAR]                  [INICIAR CIERRE — paso 2]│
   └──────────────────────────────────────────────────────┘
```

Endpoint llamado al renderizar: `POST /convocatorias/:id/close/preview` (idempotente, solo simula).

#### D5-B — Estado "CLOSING" — paso 2: confirmación del segundo admin

Estado de la convocatoria: `CLOSING`. El primer admin (`closing_admin_id`) ya inició el cierre. Cualquier ADMIN entra y ve este estado:

```
   ┌──────────────────────────────────────────────────────┐
   │ Cerrar Convocatoria 2026-A — Paso 2 de 3 (CONFIRMAR) │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  Estado: CLOSING                                     │
   │  Iniciado por: María García (admin) hace 12 minutos  │
   │  Iniciado a las: 15/06/2026 09:32 (Madrid)           │
   │                                                      │
   │  ⚠ Este cierre necesita un SEGUNDO admin para        │
   │    confirmarse. María García NO puede confirmar      │
   │    su propio cierre.                                 │
   │                                                      │
   │  Si vos sos María García:                            │
   │     [VOLVER]  (esperá a que otro admin confirme)     │
   │                                                      │
   │  Si vos sos otro admin:                              │
   │                                                      │
   │     RESUMEN (idéntico al paso 1)                     │
   │     · 50 APTO · 150 NO_APTO · 0 auditorías pendientes│
   │                                                      │
   │     [VER ranking final simulado ▾]                   │
   │                                                      │
   │     Para confirmar, re-introducí tu CONTRASEÑA       │
   │     y escribí el nombre exacto de la convocatoria:   │
   │                                                      │
   │     Contraseña: [________________]                   │
   │     Nombre:     [2026-A___________]                  │
   │                                                      │
   │     [CANCELAR EL CIERRE]    [CONFIRMAR CIERRE]       │
   │     (revoca paso 1)         (ejecuta el cierre)      │
   └──────────────────────────────────────────────────────┘
```

Endpoint llamado al confirmar: `POST /convocatorias/:id/close/confirm` con re-auth obligatoria. El backend valida `auth.user.id !== convocatoria.closing_admin_id`. Cancelar el paso 1 vuelve al estado OPEN (admin abandona el cierre); endpoint dedicado `POST /convocatorias/:id/close/abort` (solo el iniciador o un super-admin).

#### D5-C — Estado "CLOSED" — paso 3: ventana de reversa de 24h

Estado: `CLOSED` y `now < reversal_window_until`. Solo `SUPER_ADMIN` ve botón de reversa; `ADMIN` y `MANAGER` ven solo lectura del acta.

```
   ┌──────────────────────────────────────────────────────┐
   │ Convocatoria 2026-A — CERRADA                        │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │  Estado: CLOSED                                      │
   │  Cerrada por: María García (initiate) +              │
   │              Carlos Soto (confirm)                   │
   │  Cerrada el: 15/06/2026 09:47 (Madrid)               │
   │  ACTA: [DESCARGAR PDF · SHA256: a1b2c3...]           │
   │                                                      │
   │  Resultado:                                          │
   │  · 50 APTO · 150 NO_APTO                             │
   │                                                      │
   │  ────────────────────────────────────────            │
   │                                                      │
   │  ⚠ VENTANA DE REVERSA                                │
   │  Esta convocatoria pasa a LOCKED (irrevocable        │
   │  absoluto) en: 23h 13m                               │
   │                                                      │
   │  Hasta entonces, un SUPER_ADMIN puede revertir el    │
   │  cierre por error administrativo (con justificación  │
   │  obligatoria de mín. 50 caracteres).                 │
   │                                                      │
   │  [Solo SUPER_ADMIN ve este botón:]                   │
   │     [SOLICITAR REVERSA]                              │
   └──────────────────────────────────────────────────────┘
```

Pasadas las 24h: el bloque "ventana de reversa" desaparece, el estado pasa a `LOCKED`, y el sistema bloquea cualquier UPDATE futuro a esta convocatoria.

#### Resumen de qué endpoints llama D5

| Estado | Botón | Endpoint | Quién puede |
|---|---|---|---|
| OPEN | "Iniciar cierre" | `POST /close/initiate` | ADMIN |
| CLOSING | "Confirmar cierre" | `POST /close/confirm` | ADMIN ≠ initiator + re-auth |
| CLOSING | "Cancelar cierre" | `POST /close/abort` | initiator o SUPER_ADMIN |
| CLOSED (<24h) | "Solicitar reversa" | `POST /close/reverse` | SUPER_ADMIN + razón ≥50 chars |
| CLOSED (≥24h) | — | (auto-transición a LOCKED por cron) | — |

### D6 — CRUD Rutas

Sin cambios mayores.

### D7 — Editor de Ruta (con mapa)

Sin cambios.

### D8 — RFID

Sin cambios.

### D9 — Kioskos + D10 Pairing

Sin cambios.

### D11 — Listado Scoring (read-only V1)

Sin cambios.

### D12 — SIMULADOR DE SCORING (UPGRADE crítico v5)

Ahora simula impacto en el RANKING completo, no solo notas individuales.

```
   ┌──────────────────────────────────────────────────────┐
   │ Simulador de Scoring · Convocatoria 2026-A           │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │ Versión base: [v2.1 (activa) ▾]                      │
   │ Aplicar a:    [Convocatoria 2026-A ▾]                │
   │                                                      │
   │ Modificar reglas:                                    │
   │ ┌──────────────────────────────────────────────┐    │
   │ │ Familia   Regla              Original  Nuevo │    │
   │ │──────────────────────────────────────────────│    │
   │ │ Estab.    frenada threshold  8.0       10.0  │    │
   │ │ Estab.    frenada peso       0.4       0.4   │    │
   │ │ Velocidad exceso threshold   10kh      10kh  │    │
   │ │ Velocidad exceso peso        0.3       0.3   │    │
   │ └──────────────────────────────────────────────┘    │
   │                                                      │
   │ [SIMULAR]                                            │
   │                                                      │
   │ ──────────────────────────────────                   │
   │                                                      │
   │ RESULTADO:                                           │
   │                                                      │
   │ ┌─────────────────────────────────────────────┐     │
   │ │ IMPACTO EN NOTAS                            │     │
   │ │  Attempts afectados: 87                     │     │
   │ │  Diferencia media: +0.45 pts                │     │
   │ │                                             │     │
   │ │ IMPACTO EN RANKING                          │     │
   │ │  Candidatos que CAMBIAN de lado del corte:  │     │
   │ │   → 5 entran en plaza (subieron de puesto)  │     │
   │ │   → 5 salen de plaza (bajaron de puesto)    │     │
   │ │                                             │     │
   │ │  Movimientos del top 50:                    │     │
   │ │   - Mayor subida: Pedro M. (+12 puestos)    │     │
   │ │   - Mayor caída: Laura B. (-8 puestos)      │     │
   │ │                                             │     │
   │ │ [VER LISTADO COMPLETO]   [EXPORTAR CSV]     │     │
   │ │                                             │     │
   │ │ [DESCARTAR]   [GUARDAR COMO NUEVA VERSIÓN]  │     │
   │ └─────────────────────────────────────────────┘     │
   │                                                      │
   │ ⚠ Activar la nueva versión NO reprocesa los          │
   │   attempts ya cerrados. Solo afecta a futuros.       │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

**Esto es lo más vendible al cliente.** Joel es el dueño exclusivo (§10).

### D13 — Gestión Usuarios

Sin cambios.

## 9.7 KIOSKO — pantallas

Sin cambios respecto a v4. Las 6 pantallas (K1 Pairing, K2 Idle, K3 Active, K4 Recovery, K5 AdminPanel, K6 Logs) y los 5 mecanismos defensivos siguen siendo idénticos. La cabina del camión NO se entera del modelo de oposición — sigue mostrando solo nombre + duración + estado.

## 9.8 Tu calendario 14 días

```
DÍA  TAREA
───  ────────────────────────────────────────────
1    Setup Vite + Tailwind + tokens
2    Layouts base 3 portales + login pages
3    Login funcionando + routing protegido
4    Wrapper <MapViewer> + <Matrix> con mock
5    Estructura vista examinador (M6 sin datos)
8    Conectar matriz datos reales + filtros
9    Vista examinador completa (M6) + ScoreBreakdown
     PANTALLA RANKING (M5) NUEVA con datos reales
10   Modal AuditRequest (M7) + Portal alumno (A2 con
     StandingCard, A3, A4, A5, A6)
11   KIOSKO completo + Pantalla cierre convocatoria (D5)
12   D3, D4, D6-D13 (admin) + pulido visual
13   TORTURAR kiosko con Joel
14   Pulido final + ensayo demo
```

## 9.9 Reglas frontend que NO se rompen

```
   ✓ TODAS las URLs en config/api.ts
   ✓ React Query para datos del servidor
   ✓ Zustand para estado UI / kiosko offline
   ✓ Tailwind classes (sin inline styles)
   ✓ Componentes <500 líneas
   ✓ TypeScript strict, cero `any` sin justificar
   ✓ Wrappers para librerías externas (Leaflet, Chart.js)
   ✓ Tests Vitest críticos: matriz, ranking, score breakdown,
     audit request modal, kiosko store
   ✓ Tests Playwright críticos del flujo completo
   ✓ Dark mode kiosko REQUISITO
   ✓ Eventos low confidence visibles, no escondidos
   ✓ data_quality del attempt visible en M4 y M6
   ✓ StandingCard del alumno usa /students/me/standings (v6 fix R3: plural multi-enrollment)
   ✓ Sin telemetría cruda en portal alumno
   ✓ Manager NO modifica notas (solo audit request)
   ✓ Cierre de convocatoria con confirmación de texto explícita
   ✓ Simulador muestra impacto en ranking, no solo notas
```

---


# 10. PARA JOEL — Simulador (con dimensión Ranking) + QA + Demo Engineer

## 10.1 Tu rol

```
   ┌──────────────────────────────────────────────────────┐
   │  TU ROL: SIMULADOR + QA + Demo Engineer              │
   │                                                      │
   │  Sos NUEVO. Eso es ventaja: testear desde fuera te   │
   │  obliga a entender cómo se usa, no solo cómo está    │
   │  construido.                                         │
   │                                                      │
   │  Tu trabajo en 14 días:                              │
   │                                                      │
   │  1. SIMULADOR end-to-end (DUEÑO EXCLUSIVO):          │
   │     - Endpoint backend con dimensión RANKING         │
   │     - Pantalla admin (D12) que llama al endpoint     │
   │     - Datos de prueba que hagan las simulaciones     │
   │       significativas                                 │
   │     - Documentación de uso para el cliente           │
   │                                                      │
   │  2. Tests E2E (Playwright) del flujo completo        │
   │  3. Datos seed realistas para la demo                │
   │  4. CI/CD GitHub Actions + staging deploy            │
   │  5. Demo readiness — viernes a viernes               │
   │  6. Día 13: torturar el kiosko a propósito           │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

**Por qué este rol:**
- El simulador con dimensión ranking es **la pieza más vendible al cliente**. Que el dueño exclusivo sea alguien dedicado garantiza calidad.
- Liberás a Jesús y Alejandro de QA → 30% más de velocidad del equipo principal.
- Datos seed realistas son CRÍTICOS para que la demo sea creíble.
- Tests E2E son lo primero que se sacrifica si no tiene dueño dedicado.
- Aprendés el sistema desde la perspectiva del usuario.

## 10.2 Tu territorio — el simulador

El simulador atraviesa backend y frontend. Tu trabajo es **integrar** las piezas y ser su dueño:

```
   training/
   │
   ├── apps/api/src/routes/
   │   └── scoring.simulate.ts       ← ENDPOINT (Joel implementa,
   │                                     Jesús apoya con la lógica
   │                                     puramente computacional)
   │
   ├── packages/scoring/
   │   └── simulate.ts               ← LÓGICA PURA del simulador
   │                                     (Joel + Jesús pair)
   │
   ├── apps/web/src/pages/admin/
   │   └── ScoringSimulator.tsx      ← PANTALLA D12 (Joel implementa,
   │                                     Alejandro apoya con
   │                                     componentes UI)
   │
   ├── seed/
   │   └── simulation-fixtures.ts    ← Datos para que el simulador
   │                                     sea significativo
   │
   └── docs/
       └── SIMULATOR-USER-GUIDE.md   ← Doc de uso para el cliente
```

## 10.3 Cómo funciona el simulador

```
   Input:
     - convocatoria_id
     - criteria_overrides (qué thresholds/pesos cambiar)

   Proceso:
     1. Tomar todos los attempts cerrados de esa convocatoria
     2. Para cada attempt: recalcular el score con las reglas
        modificadas (sin tocar el original)
     3. Construir un ranking simulado con los scores nuevos
     4. Comparar ranking original vs simulado
     5. Identificar candidatos que cruzan el corte

   Output:
     {
       attempts_simulated: [...],
       ranking_original: [...],
       ranking_simulado: [...],
       candidatos_que_cruzan_corte: [
         { id, nombre, dirección: 'entra'|'sale',
           puesto_original, puesto_simulado }
       ],
       summary: {
         attempts_afectados: int,
         diff_nota_media: float,
         decisiones_que_cambiarían: int
       }
     }
```

## 10.4 Por qué este simulador es crítico

```
   Para el cliente:
   - "¿Qué pasa si subo el threshold de exceso de velocidad?"
   - "¿Qué pasa si bajo el peso de la familia ruta?"
   - "¿Cuántos candidatos cambiarían de plaza?"

   Sin simulador: el cliente cambia y reza.
   Con simulador: el cliente prueba sin riesgo, ve impacto,
   decide informado.
```

## 10.5 Otros entregables (además del simulador)

### Tests E2E (Playwright)

```
e2e/
├── manager/
│   ├── login.spec.ts
│   ├── matriz.spec.ts
│   ├── ranking.spec.ts            ← NUEVO v5
│   ├── examinador.spec.ts
│   └── auditoria.spec.ts          ← NUEVO v5
├── alumno/
│   ├── dashboard-con-standing.spec.ts ← NUEVO v5
│   ├── historial.spec.ts
│   ├── pedagogico.spec.ts
│   └── solicitar-auditoria.spec.ts    ← NUEVO v5
├── admin/
│   ├── convocatorias.spec.ts      ← NUEVO v5
│   ├── cerrar-convocatoria.spec.ts ← NUEVO v5
│   └── simulador.spec.ts          ← lo testeás vos mismo
├── kiosko/
│   ├── pairing.spec.ts
│   ├── flujo-rfid.spec.ts
│   └── recovery.spec.ts
└── flujo-completo.spec.ts
```

### Datos seed

Para que la demo sea creíble:

```
   Cohorte demo:
   - 1 convocatoria "2026-DEMO" con 50 candidatos, 10 plazas
   - 4 rutas (urbana, carretera, mixta, polígono)
   - 50 RFID cards asignadas
   - Distribución de attempts:
     · 35 candidatos con 4/4 rutas completadas
     · 10 candidatos con 3/4 rutas
     · 5 candidatos con 2/4 rutas
   - Notas variadas: media de la convocatoria ~6.8
   - 8 attempts con reevaluación (parent_attempt_id +
     audit_request_id) — derivados de auditorías confirmadas
   - 3 attempts en pending_data_review
   - 2 attempts ABORTED_TECHNICAL (a repetir)
   - 5 solicitudes de auditoría (3 pendientes, 2 resueltas)
   - 1 ranking snapshot reciente
```

### CI/CD

```
.github/workflows/ci.yml         lint + tsc + tests + build
.github/workflows/deploy-staging.yml  auto-deploy a staging
```

### Demo Readiness — doc semanal

`docs/DEMO-READINESS.md` actualizado cada viernes a las 17:00.

## 10.6 Tu calendario 14 días

```
DÍA  TAREA
───  ────────────────────────────────────────────
1    Setup CI/CD GitHub Actions + Playwright
2    Configurar staging deploy + datos seed iniciales
3    Test E2E #1 (login)
4    Datos seed v2 (10 alumnos, 4 rutas) + Test #2
5    Test E2E #3 + datos seed v3 (con eventos Webfleet)
8    Test E2E #4 (cerrar attempt + matriz)
     Pair con Jesús: lógica simulator (packages/scoring/simulate.ts)
9    Test E2E #5 (ranking) + datos seed para ranking
10   Test E2E #6 (auditoría)
     Empezar pantalla SIMULADOR (D12) con Alejandro
11   SIMULADOR end-to-end completo + docs de uso
     Test E2E #7 (simulador con cambio de threshold)
12   Pasada COMPLETA del checklist Anexo C aplicable
13   TORTURA del kiosko (LIDERÁS)
14   Soporte ensayo demo
```

## 10.7 Criterios de "tu trabajo está bien hecho"

```
   ✓ Simulador devuelve impacto en ranking en <2s para 100 attempts
   ✓ Pantalla D12 muestra el reordenamiento del top con candidatos
     que cruzan el corte
   ✓ Documentación de uso para el cliente clara y breve (1 página)
   ✓ 8+ tests E2E pasando en CI
   ✓ Datos seed creíbles (no "Test User 01")
   ✓ CI/CD funcionando
   ✓ Auto-deploy a staging en cada merge a main
   ✓ Demo Readiness actualizado cada viernes
   ✓ Día 13 ejecutado, fallos documentados
```

---

# 11. FASE 1 vs FASE 2 — la verdad incómoda (TODOS LEEN ESTO)

## 11.1 El error invisible

```
   ┌──────────────────────────────────────────────────────────┐
   │  El patrón humano es siempre el mismo:                   │
   │                                                          │
   │  demo sale bien → cliente felicita → equipo se relaja → │
   │  tratamos el sistema como "casi terminado" →             │
   │  entran datos reales → REVIENTA                          │
   │                                                          │
   │  Esta sección existe para que ESO NO PASE.               │
   └──────────────────────────────────────────────────────────┘
```

## 11.2 La diferencia brutal

| | FASE 1 (los 14 días) | FASE 2 (lo serio) |
|---|---|---|
| **Duración** | 14 días | 4-8 semanas post-demo |
| **Objetivo** | Cliente sale confiando | Sistema sobrevive datos reales |
| **Dataset** | Convocatoria demo (50 candidatos) | Convocatorias reales (200+ candidatos) |
| **Webfleet** | Fixtures + 1 sync exitoso | Cuotas, retries, outages reales |
| **Kiosko** | Online OK, offline básico | Offline-first robusto, hardware real |
| **Scoring** | 4 familias funcionando | Tunear umbrales con datos reales |
| **Ranking** | Cron diario, confianza, estable | Validado con cohortes reales, edge cases |
| **Cierre de convocatoria** | Ejecuta, pero no en producción | Validación final con CMadrid antes |
| **Cutover** | No aplica | Sombra → convocatoria por convocatoria |
| **PDFs** | Mock | Definitivos |
| **Tests E2E** | Críticos | Exhaustivos |
| **Monitoring** | Logs locales | Sentry, métricas, alertas |

## 11.3 La regla mental

```
   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   │   SI LA DEMO SALE BIEN, NO BAJAMOS LA GUARDIA.           │
   │                                                          │
   │   La fase 2 es donde se gana o se pierde el sistema.     │
   │                                                          │
   │   El día 15 (post-demo), el equipo se reúne 1 hora       │
   │   a planificar la fase 2 con la misma seriedad que       │
   │   se planificó esto.                                     │
   │                                                          │
   │   No "ya está, ahora pulimos".                           │
   │   Es: "ahora viene lo serio de verdad".                  │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
```

---

# 12. Reglas no negociables

## 12.1 Las 7 invariantes arquitectónicas

```
┌──────────────────────────────────────────────────────────────┐
│   1. Idempotencia de ingest                                  │
│   2. Reproducibilidad de attempts                            │
│   3. Inmutabilidad del attempt cerrado                       │
│   4. Versionado pinneado (normalizer + detector + criteria)  │
│   5. Fuente declarada + Confianza (ortogonales)              │
│   6. Inmutabilidad del ranking final  (NUEVO v5)             │
│   7. Decisión solo al cierre de convocatoria  (NUEVO v5)     │
│                                                              │
│   Cualquier PR que rompa una se rechaza.                     │
└──────────────────────────────────────────────────────────────┘
```

## 12.2 Las 5 reglas de proceso

```
┌──────────────────────────────────────────────────────────────┐
│   8.  Lógica de dominio NO en handlers HTTP (va a packages)  │
│   9.  normalization, detection, scoring y ranking NO tocan DB│
│   10. Webfleet encapsulado (solo packages/ingestion/webfleet)│
│   11. URLs API SOLO en config/api.ts                         │
│   12. Logger Winston/utils, NO console.log                   │
└──────────────────────────────────────────────────────────────┘
```

## 12.3 Lo que NO va a pasar (no se reabre)

```
┌──────────────────────────────────────────────────────────────┐
│   ✗ Python, Flask, SQLAlchemy, Celery                        │
│   ✗ Vue, Nuxt, Pinia                                         │
│   ✗ Microservicios                                           │
│   ✗ Big Bang cutover                                         │
│   ✗ Hardcodear URLs en componentes                           │
│   ✗ console.log en producción                                │
│   ✗ Manager modificando notas (solo via audit request)       │
│   ✗ Apto/no apto por intento (es por convocatoria al cierre) │
│   ✗ Ranking en tiempo real instantáneo (1x al día)           │
│   ✗ Cierre de convocatoria automático sin confirmación       │
│   ✗ Reabrir convocatoria una vez cerrada                     │
│   ✗ Telemetría cruda en portal alumno                        │
│   ✗ Scores visibles en kiosko                                │
└──────────────────────────────────────────────────────────────┘
```

---

# 13. Decisiones tomadas

## 13.1 Decisiones heredadas v1-v4 (vigentes)

## D1 — DB compartida o separada con DobackSoft actual

**DECISIÓN: DB nueva, separada.**

## D2 — Retención de samples crudos

**DECISIÓN: 12 meses. Configurable por organización en V2.**

## D3 — DobackSoft Fleet

**DECISIÓN: Deprecación formal. Fin de vida 2026-10-27.**

## D4 — Lector RFID

**DECISIÓN: USB-HID emulando teclado. Demo con teclado físico.**

## D5 — Formato de archivos del sensor

**DECISIÓN: Formato actual de DobackSoft V3.**

## D6 — Hosting del repo

**DECISIÓN: GitHub org actual. Repo "training". Privado.**

## D7 — Routing del cutover

**DECISIÓN: Routing en backend por header de cohorte. Reverse proxy Nginx.**

## D8 — Modelo de confianza

**DECISIÓN: Binario `{high, low}` para V1, con campo `confidence_score: Float?` oculto.**

## D9 — Capa de normalization

**DECISIÓN: Package separado desde día 4 (semana 1).**

## D10 — Reevaluación

**DECISIÓN: `parent_attempt_id` en schema desde primera migración.**

## D11 — Data quality global del attempt

**DECISIÓN: Campo `data_quality: HIGH | MEDIUM | LOW` + métricas.**

## D12 — Simulador de scoring

**DECISIÓN: Endpoint y pantalla admin desde V1.**

## D13 — Joel como dueño exclusivo del simulador + QA

**DECISIÓN: Joel se ocupa del simulador end-to-end + tests E2E + datos seed + CI/CD.**

## 13.2 Decisiones nuevas v5 — modelo oposición

## D14 — Modelo de evaluación: oposición, no escolar

**DECISIÓN: Modelo oposición.**
- El sistema emite NOTA por intento, NO decisión APTO/NO_APTO.
- La decisión APTO/NO_APTO se emite al cierre de la convocatoria, según ranking final + plazas.
- Las notas son inmutables. El ranking es provisional hasta el cierre.

## D15 — Agregación de notas

**DECISIÓN: MEDIA SIMPLE de las rutas completadas.**
- Comparable entre convocatorias.
- No premia inconsistencia.
- En V2 se permite media ponderada con campo `peso` ya en schema.

## D16 — Pesos por ruta

**DECISIÓN: V1 todas las rutas peso 1.0. Schema preparado para pesos diferentes.**
- Campo `peso: Float (default 1.0)` en `ConvocatoriaRuta`.
- V1 NO expone UI. Cuando CMadrid lo pida, se activa sin tocar lógica.

## D17 — Rutas no completadas (criterios concretos tras review)

**DECISIÓN: Distinción automática con criterios DB-encoded, no interpretables.**
- `ABANDONED` (candidato no completó) → cuenta como 0 en ranking.
- `ABORTED_TECHNICAL` (fallo del sistema) → NO cuenta. Admin puede recategorizar manualmente si discrepa, con audit log y justificación obligatoria.

### Criterios automáticos para ABORTED_TECHNICAL (refinado v6)

Un attempt se marca ABORTED_TECHNICAL si CUALQUIERA de estos predicados se cumple. Si NINGUNO se cumple pero el candidato no completó, va a ABANDONED.

```
   PREDICADOS DE FALLO TÉCNICO (cualquiera dispara ABORTED_TECHNICAL):

   1. DOBACK_ELITE_NO_DATA
      attempt.awaiting_doback_data = true Y han pasado >24h del started_at
      sin que llegue data del dispositivo.

   2. DOBACK_SAMPLE_LOSS
      Doback Elite envió datos PERO menos del 60% de la ventana
      [started_at, ended_at] tiene samples válidos.

   3. WEBFLEET_NO_DATA_AND_NO_GPS_BACKUP
      Webfleet retornó vacío Y Doback Elite tampoco aportó GPS.
      (es decir: NO HAY GPS de ninguna fuente)

   4. RFID_KIOSKO_DISCREPANCY
      El kiosko reporta tap RFID pero el backend no encuentra
      RfidCard activa con ese UID en el momento del tap.

   5. KIOSKO_LOST_AT_CRITICAL_PHASE
      El kiosko quedó offline >30min mientras el attempt estaba OPEN
      Y al recuperar conexión, los samples locales tienen gap >5min
      con los de Doback Elite/Webfleet (no se pueden alinear).

   ABANDONED se aplica SI:
   - El candidato no completó la ruta (ended_at en kiosko sin alcanzar
     trayectoria mínima Y la ruta NO se cerró por tap de otra tarjeta)
   - Y NINGÚN predicado técnico arriba se cumple.

   INTERRUPTED_BY_OTHER_CARD se aplica SI (v6 fix R2-S4):
   - La ruta se cerró porque OTRA tarjeta RFID entró antes del 80%
     del recorrido del candidato actual.
   - Este estado NO cuenta en el ranking del candidato víctima
     (no se penaliza al inocente).
   - Para mitigar abuso: el segundo tap requiere "wait period" en
     el kiosko (mín 5s sin actividad del primer alumno) antes de
     aceptar la nueva tarjeta. Si el primer alumno toca un botón
     "estoy aún en la ruta" durante esos 5s, el segundo tap se ignora.

   ESCALADO POST-CIERRE INMINENTE:
   Si un attempt entra a ABORTED_TECHNICAL y la convocatoria del
   candidato cierra en menos de 72h, el sistema NO marca
   ABORTED_TECHNICAL automáticamente — entra en estado
   PENDING_TECHNICAL_REVIEW y notifica al admin para decisión
   manual urgente (extender closes_at, permitir repetir, o
   aceptar como ABORTED).
```

**Implementación:** función pura `classifyIncomplete(attempt, samples_metrics, second_tap_metadata) → ABANDONED | ABORTED_TECHNICAL | INTERRUPTED_BY_OTHER_CARD | PENDING_TECHNICAL_REVIEW` en `packages/domain/`. Tests determinísticos con fixtures.

## D18 — Plazas

**DECISIÓN: Entero fijo, definido por convocatoria, público desde el día 1.**
- Campo `plazas: Int` en Convocatoria, NOT NULL al crear.

## D19 — Empates: cascada de 4 criterios

**DECISIÓN:**
1. Mejor nota en ruta_principal_id (admin la marca al crear convocatoria).
2. Menor número de attempts con data_quality = LOW.
3. Mejor nota promedio en familia "estabilidad".
4. Sorteo determinista con semilla = SHA256(convocatoria_id + enrollment_id + closes_at_iso) — ver §8.5 para algoritmo canónico.

Configurable en V2. Default razonable y auditable.

## D20 — Visibilidad del puesto al alumno

**DECISIÓN:**
- ✓ Su puesto absoluto (74/200).
- ✓ Total de plazas (50).
- ✓ Su nota media acumulada.
- ✓ Si está dentro o fuera del corte provisional.
- ✗ NO ve el umbral numérico.
- ✗ NO ve los demás puestos / notas / nombres.

Razón: el umbral numérico cambia y genera falsa seguridad o alarma. "Dentro / fuera del corte provisional" es informativo y honesto.

## D21 — Actualización del ranking + cierre de convocatoria (versión refinada por D22)

**DECISIÓN:**
- Recálculo **una vez al día, a las 6:00 AM hora de Madrid (Europe/Madrid)**.
- Cierre de convocatoria: ver **D22** (cierre reforzado).
- Excepción: recálculo final inmediato al cierre (no espera al cron).

## D21.1 — Timezone y DST (NUEVO v6 fix tras review)

**DECISIÓN: toda la lógica de fechas usa la zona `Europe/Madrid` con DST.**

```
   STORAGE
   ─ Toda fecha persistida en DB es UTC (timestamptz).

   PROCESAMIENTO
   ─ El cron BullMQ se configura con TZ='Europe/Madrid' explícito,
     no con cron pattern UTC. Así "0 6 * * *" siempre dispara a las
     6:00 AM hora de Madrid, automáticamente en CET o CEST según
     fecha del año.

   PRESENTACIÓN
   ─ El frontend renderiza todas las fechas en hora de Madrid usando
     `date-fns-tz` o `Intl.DateTimeFormat({ timeZone: 'Europe/Madrid' })`.

   VENTANA DE REVERSA — definición precisa
   ─ `reversal_window_until = closed_at + 24 horas (wall-clock)`
     en hora local Madrid.
   ─ Implementación: persistir como `closed_at_utc + 24h` Y guardar
     `reversal_deadline_madrid` como string ISO con offset, calculado
     una sola vez al cerrar usando luxon o equivalente.
   ─ En el cambio CET→CEST de marzo: la ventana puede ser efectivamente
     23h en UTC, pero 24h en wall-clock local. El admin que ve en su
     UI "ventana cierra en X horas" siempre ve la cuenta correcta
     porque se renderiza con `Europe/Madrid`.
   ─ En el cambio CEST→CET de octubre: análogo, 25h efectivas en UTC.

   FECHAS DE CONVOCATORIA
   ─ `closes_at` se interpreta como `23:59:59 hora Madrid` del día
     publicado, salvo que el admin especifique otra hora explícita.
   ─ Esto se documenta en el editor de convocatoria.
```

**Por qué wall-clock y no UTC estricto:** el candidato y el admin razonan en hora local. Una ventana de "24 horas" que termina a las 03:00 AM por DST sería incomprensible.

## 13.3 Decisiones críticas v6 — tras review adversarial

## D22 — Cierre de convocatoria REFORZADO (NUEVO v6)

**DECISIÓN: Cierre con tres pasos, doble admin, acta y ventana de reversa.**

```
   FLUJO DE CIERRE (3 pasos obligatorios):

   PASO 1 — PREVIEW
   admin solicita /close/preview
   sistema devuelve simulación: ranking final, aptos, no aptos
   advertencias (candidatos sin completar todas las rutas, etc.)
   Esto NO modifica nada. Solo lectura.

   PASO 2 — INITIATE
   admin (#1) llama /close/initiate
   confirma escribiendo el nombre exacto de la convocatoria
   estado pasa de OPEN → CLOSING
   se registra closing_admin_id

   PASO 3 — CONFIRM
   admin DISTINTO (#2) llama /close/confirm
   sistema VALIDA confirming_admin_id != closing_admin_id
   confirma escribiendo el nombre exacto
   sistema:
     - calcula ranking final
     - genera CandidateOutcome[] para todos los candidatos
     - genera ConvocatoriaCloseAct (PDF firmado con SHA256)
     - estado pasa CLOSING → CLOSED
     - registra reversal_window_until = now + 24h

   VENTANA DE REVERSA (24 horas)
   solo SUPER_ADMIN puede /close/reverse
   requiere justificación obligatoria (≥50 caracteres)
   queda registrada en AuditLog
   tras 24h: estado pasa CLOSED → LOCKED (irrevocable absoluto)
```

**Por qué:** una sola persona escribiendo el nombre y confirmando es insuficiente para una decisión que afecta a 200 candidatos en oposición pública. Doble admin + ventana de gracia + acta legal = trazabilidad completa.

## D23 — GDPR / Privacidad como decisión arquitectónica (NUEVO v6)

**DECISIÓN:** GDPR no es opcional ni "fase 2". Está en V1.

```
   ELEMENTOS GDPR EN V1:

   ▶ Política de retención
     - raw_samples: 12 meses (D2)
     - attempts cerrados: indefinido (evidencia legal de oposición)
     - anonimización tras 5 años o cuando aplique legalmente

   ▶ Aviso de privacidad
     Pantalla obligatoria al inscribirse el candidato
     Texto generado con CMadrid (no inventado por nosotros)

   ▶ Right to access
     Endpoint /students/me/data-export
     ZIP con todos los datos personales del candidato
     Generación async, email cuando ready, expira a 7 días

   ▶ Right to be forgotten (acotado por marco legal)
     Endpoint /students/me/forget-request
     Procesa SUPER_ADMIN manualmente (no automático)
     Comportamiento por estado de la convocatoria del candidato:
       OPEN     → SOLO anonimización de PII (nombre/DNI/email a hash)
                  El candidato sigue ocupando su puesto en el ranking
                  bajo identificador anonimizado ("Candidato #74").
                  Sus attempts NO se borran (son evidencia legal).
       CLOSED/LOCKED + plazo de recurso ABIERTO (≤30 días)
                → SOLICITUD QUEUED. Comunicación formal al candidato
                  citando base legal LPACAP de retención. GDPR art. 12
                  exige respuesta en ≤1 mes — el sistema responde con
                  DENIED_LEGAL_BASIS antes de los 30 días.
       LOCKED + plazo recurso CERRADO + sin recurso pendiente
                → Anonimización de PII permitida.
                  Attempts y CandidateOutcome quedan con id anonimizado.
                  Acta de cierre conservada (es documento público).
       Tras 5 años (D2) → anonimización completa por cron, sin
                          intervención del candidato.

   ▶ Forget durante OPEN — efectos en el ranking
     - El candidato NO se elimina del ranking durante OPEN.
     - Su PII se reemplaza por hash; ranking muestra "Candidato #X".
     - El total_candidatos NO cambia → no se renumeran los puestos.
     - El cron nocturno usa candidato_id (cuid) como clave estable;
       anonimización solo afecta los campos de display.

   ▶ Roles GDPR
     Data Controller: CMadrid (decide qué se procesa y por qué)
     Data Processor: nosotros (procesamos en su nombre)
     DPO: a confirmar con CMadrid antes del cutover

   ▶ Audit log de acciones sensibles
     Tabla AuditLog registra exports, downloads, deletes, role changes,
     anonimización (con timestamp y actor)
```

**Por qué:** estamos manejando datos personales sensibles de candidatos a oposición pública. Sin GDPR explícito, CMadrid puede ser sancionado, y nosotros como processor también.

## D24 — Sync Doback Elite ↔ backend cerrado completo (NUEVO v6)

**DECISIÓN:** Flujo definido, sin ambigüedad.

```
   FLUJO PHYSICAL → BACKEND:

   1. Doback Elite captura datos durante el attempt (sensor + GPS propio)
   2. Cuando el attempt se cierra en el kiosko:
        - kiosko notifica a Doback Elite (señal local: BLE / serial / WiFi LAN)
        - kiosko marca attempt.awaiting_doback_data = true
        - attempt entra a status AWAITING_DOBACK_DATA
   3. Doback Elite POST a /doback/upload con el blob de samples
        - autenticado con device JWT (pairing token de larga vida)
        - firmado con clave del dispositivo
   4. Backend recibe, valida firma, persiste raw_samples,
      marca attempt.doback_synced_at = now() y attempt.awaiting_doback_data = false
   5. Si todo llega → attempt.status pasa a PROCESSING

   REINTENTO Y FALLBACK:
   - Cron cada 10 minutos busca attempts con awaiting_doback_data=true
   - Pinging suave a Doback Elite (vía device JWT)
   - Si pasa 24h sin sync → attempt.status = ABORTED_TECHNICAL
     (admin recibe alerta, candidato tendrá que repetir)

   AUTENTICACIÓN DEL DISPOSITIVO:
   - Cada Doback Elite tiene device_id + pairing_token
   - Pairing inicial: admin lo configura en /admin/devices
   - El token vive en el firmware (secret seguro)
   - Tras pairing, Doback Elite puede hablar con backend
```

**Por qué:** sin este flujo cerrado, Jesús no puede implementar el endpoint de upload con confianza. Antonio coordina con el equipo de firmware Doback Elite (es producto interno) para que el comportamiento físico coincida con esta especificación.

## D25 — `criteria_version` pinned al ABRIR el attempt (NUEVO v6)

**DECISIÓN:** El pinning de las versiones ocurre al CREAR el attempt, no al cerrar.

```
   ANTES (v5, problema):
   POST /attempts → crea con versiones nullable
   ... (kiosko activo, candidato conduce)
   ... admin activa criteria v2.2 a las 14:00
   ... candidato termina a las 14:30
   POST /attempts/:id/close → ¿qué versión usar?

   AHORA (v6, decisión):
   POST /attempts → captura criteria_active, normalizer_active,
                    detector_active EN ESE MOMENTO
                    → atributos NOT NULL en el attempt
   ... admin activa criteria v2.2 a las 14:00
   ... candidato termina a las 14:30
   POST /attempts/:id/close → usa las versiones que el attempt
                              ya tenía pinned al abrir

   CONSECUENCIA:
   Cambios de criteria mid-día NO afectan attempts en curso.
   Solo afectan a attempts CREADOS después del cambio.
```

**Por qué:** sin esto, dos attempts del mismo día del mismo alumno pueden tener criterios distintos según cuándo termina cada uno. Caos legal y de auditabilidad.

### D25.1 — Cómo se respeta D25 cuando el kiosko está offline (fix tras review)

El kiosko opera offline (D-kiosko). Si crea attempts sin conexión, no puede leer la `criteria_version` activa "en este momento" del backend. Resolución:

```
   1. Al hacer pairing inicial (K1) y en cada heartbeat exitoso, el kiosko
      cachea localmente:
        criteria_version_id_active
        criteria_version_active_since (timestamp)
        normalizer_version_id_active
        detector_version_id_active

   2. Cuando el kiosko crea un attempt offline, lo encola en IndexedDB con
      las versiones que tenía cacheadas en ese momento.

   3. Al re-sincronizar con el backend, el kiosko envía el attempt junto con
      kiosko_version_cache_at (timestamp del último heartbeat exitoso).

   4. El backend valida: ¿la versión criteria_active en el momento real
      del attempt (started_at) era la misma que el kiosko envió?
        - SI: pinned como llegó.
        - NO: ATTEMPT marcado en estado PENDING_CRITERIA_REVIEW.
              Admin debe decidir manualmente si:
                a) usar la versión del kiosko (lo que el candidato vivió)
                b) usar la versión activa al started_at (lo más reciente)
              La decisión queda en AuditLog con justificación.

   5. Para minimizar (4): ANTES de activar una nueva criteria_version,
      el sistema valida que no haya kioskos OPEN sin sincronizar
      desde la activación previa. Si los hay → activación bloqueada
      hasta que sincronicen o el admin fuerce.

   ACTIVACIÓN DE NUEVA CRITERIA — flow atómico:

   POST /scoring/versions/:id/activate
     1. SELECT FOR UPDATE convocatorias OPEN
     2. SELECT FOR UPDATE kioskos con last_heartbeat < ahora-5min
     3. Si hay kioskos no sincronizados:
          → respuesta 409 con lista de kioskos pendientes
          → admin debe forzar (con audit) o esperar sync
     4. UPDATE criteria_version SET active=true (nueva), active=false (vieja)
     5. COMMIT
     6. Push a kioskos online (heartbeat next) refresca cache
```

**Por qué:** sin esto, el invariante #9 (criteria_version pinned al abrir) se rompe silenciosamente cuando el kiosko queda offline 30 minutos durante una activación de criteria. Es el caso real del primer día de oposición con conexión spotty.

## Resumen de decisiones

```
   D1-D13:  ver §13.1 (decisiones v1-v4)
   D14-D21: ver §13.2 (modelo oposición v5)
   D22-D25: ver §13.3 (críticas adversariales v6)

   D22: Cierre reforzado (3 pasos + doble admin + acta + ventana 24h)
   D23: GDPR como decisión arquitectónica V1
   D24: Sync Doback Elite ↔ backend completo y trazado
   D25: criteria_version pinned al ABRIR

   Las 25 decisiones quedan firmes.
```

---

# 14. La reunión con CMadrid (11/05/2026)

## 14.1 Qué les vamos a mostrar

```
   ▶ Sistema funcionando, no diapositivas
   ▶ Datos reales de una convocatoria demo (50 candidatos)
   ▶ Pipeline completo: sensor + Webfleet → nota
   ▶ Manager consultando la matriz
   ▶ Manager consultando el RANKING DE LA CONVOCATORIA  ← ★
   ▶ Examinador revisando un attempt
   ▶ Solicitud de auditoría desde el portal alumno
   ▶ Reevaluación creada desde la auditoría
   ▶ Score breakdown granular (cada regla explicada)
   ▶ Alumno consultando su STANDING en la convocatoria
     (puesto + nota media + dentro/fuera del corte)  ← ★
   ▶ Kiosko simulando RFID
   ▶ Admin viendo el versionado de scoring
   ▶ Admin SIMULANDO un cambio de regla y viendo
     reordenamiento del ranking + candidatos que cruzan corte ← ★★
   ▶ Admin cerrando una convocatoria (en sandbox) ← ★
```

## 14.2 El mensaje a CMadrid en 5 frases

```
   1. "Construimos un sistema NUEVO, autónomo y orientado
       al modelo de OPOSICIÓN que pediste."

   2. "El sistema emite NOTAS por intento. La decisión APTO
       o NO APTO se emite al cierre de la convocatoria,
       según ranking final + plazas que vos publicaste."

   3. "Lo que están viendo HOY funciona end-to-end con
       datos reales. Es la base."

   4. "El SIMULADOR te permite probar cualquier cambio
       de regla y ver cómo se reordena el ranking ANTES
       de aplicarlo en producción."

   5. "En las 4-8 semanas siguientes endurecemos contra
       datos reales: kiosko offline robusto, cuotas
       Webfleet, cutover gradual, PDFs definitivos."
```

## 14.3 Qué NO les vamos a decir

```
   ✗ "Tiramos todo y empezamos de cero"
   ✗ "El sistema anterior estaba mal"
   ✗ "Vamos a Python/Flask"
   ✗ "Vue / nuevo framework"
   ✗ Detalles arquitectónicos profundos
   ✗ "Esto ya está terminado"
```

## 14.4 Qué les preguntamos / confirmamos

```
   ▶ "¿Confirmás los criterios de empate que propusimos?"
   ▶ "¿Cuál es la ruta principal para desempates?"
   ▶ "¿Cuántas plazas tiene la próxima convocatoria real?"
   ▶ "¿Cuándo es la próxima convocatoria de candidatos?"
   ▶ "¿Hay rutas o reglas que quieran cambiar?"
   ▶ "¿Necesitan integración con sistemas internos?"
```

## 14.5 Checklist 24h antes

```
   ☐ Demo en staging funciona end-to-end sin errores
   ☐ Datos seed cargados (convocatoria demo realista)
   ☐ Backup de la DB antes de demo
   ☐ Script de presentación rehearsed
   ☐ Plan B (segundo entorno + screencast como fallback)
   ☐ Laptop principal cargada + cable de respaldo
   ☐ Conexión a internet probada en el lugar
   ☐ Tarjeta RFID o teclado para simular RFID
   ☐ Kiosko ya torturado (día 13)
   ☐ Resumen 1 página impreso
   ☐ Documento ejecutivo en PDF para entregar al cliente
```

---

# 15. Antes de empezar — checklist final

## Para Antonio
```
   ☐ Crear repo "training" en GitHub
   ☐ Configurar permisos
   ☐ Comunicar a CMadrid fecha de demo (11/05/2026)
   ☐ Bloquear backlog DobackSoft Fleet
   ☐ Mandar este paper a Jesús, Alejandro, Joel 24h antes
   ☐ Preparar reunión kickoff lunes 9:00 AM
   ☐ Conseguir fixtures Webfleet realistas
   ☐ Preparar 8 preguntas con respuestas propuestas para
     llevar a CMadrid (modelo oposición)
```

## Para Jesús
```
   ☐ Leer paper completo (especialmente §1-§6, §8, Anexo C)
   ☐ Identificar las 7 invariantes y entenderlas
   ☐ Tener acceso al schema actual + StabilityProcessor
   ☐ Tener acceso a fixtures reales del sensor
   ☐ Confirmar dedicación 100% durante 14 días
```

## Para Alejandro
```
   ☐ Leer paper completo (especialmente §1-§6, §9, §11)
   ☐ Aceptar React (no Vue) sin reabrirlo
   ☐ Conseguir un lector RFID USB-HID o teclado
   ☐ Repasar las pantallas nuevas v5 (Ranking, StandingCard,
     AuditRequestModal, Cierre de Convocatoria)
   ☐ Confirmar dedicación 100% durante 14 días
```

## Para Joel
```
   ☐ Leer paper completo (TODO, especialmente §10 y Anexo C)
   ☐ Tener acceso a GitHub Actions
   ☐ Setup local de Playwright + node 20
   ☐ Entender el simulador con dimensión ranking (es tu pieza)
   ☐ Confirmar dedicación 100% durante 14 días
```

## Reunión kickoff (Día 1, lunes 9:00 AM)

```
   AGENDA (60 minutos)
   ───────────────────
   00:00 - 00:05   Antonio: contexto y por qué este doc
   00:05 - 00:30   Lectura silenciosa del paper en grupo
   00:30 - 00:50   Preguntas y discusión (NO REAPERTURA,
                   solo aclaraciones)
   00:50 - 00:55   Cada uno dice qué va a hacer hoy
   00:55 - 01:00   Antonio: "Empezamos. Daily mañana 9:30."
```

---

# 16. Cierre

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   En 14 días tenemos una demo end-to-end con datos reales    │
│   de una convocatoria, ranking funcional y simulador con     │
│   dimensión de ranking, funcionando frente al cliente.       │
│                                                              │
│   No es un sistema completo. Es una BASE REAL VISIBLE        │
│   sobre la que construimos en las semanas siguientes.        │
│                                                              │
│   El éxito de este sprint NO se mide en código bonito        │
│   ni en cobertura de tests. Se mide en UNA cosa:             │
│                                                              │
│      ¿El cliente sale de la reunión confiando que            │
│      vamos en la dirección correcta?                         │
│                                                              │
│   Si sí, ganamos la fase 1.                                  │
│   La fase 2 empieza el día 15.                               │
│                                                              │
│                                  — Antonio                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

# 17. Plan legal y operativo de Fase 2 (NUEVO v6)

Tras el review adversarial v6, hay 6 elementos que **no entran en el sprint demo** pero **deben estar listos antes del cutover real a producción**. Cada uno con dueño, fase y fecha objetivo.

```
   IMPORTANTE: Esta lista no es "deuda técnica nice-to-have".
   Es lo MÍNIMO requerido para operar la primera convocatoria
   real con CMadrid en producción. Sin estos, no se hace cutover.
```

## 17.1 Tabla maestra de Fase 2

| # | Item | Dueño principal | Fase | Fecha objetivo | Bloquea producción? |
|---|---|---|---|---|---|
| **F1** | Sistema de notificaciones (email + templates) | Antonio + Jesús | Fase 2 sprint 1 | Semana 3-4 post-demo | Sí |
| **F2** | Subroles admin (OPERATIONS / RULES) — `SUPER_ADMIN` ya en V1 | Jesús | Fase 2 sprint 1 | Semana 4 post-demo | No (V1 ya tiene SUPER_ADMIN) |
| **F3** | Acta PDF firmable digitalmente | Jesús + Joel | Fase 2 sprint 2 | Semana 5 post-demo | Sí |
| **F4** | Manager asignado a convocatoria | Jesús + Alejandro | Fase 2 sprint 2 | Semana 4-5 post-demo | No (V1 admin único como manager) |
| **F5** | Auditoría tras cierre (queja formal read-only) | Jesús | Fase 2 sprint 2 | Semana 5-6 post-demo | Sí (legal) |
| **F6** | Recurso del candidato sobre ranking final | Antonio (con asesor legal CMadrid) | Fase 2 sprint 3 | Semana 6-8 post-demo | Sí (legal) |

## 17.2 F1 — Sistema de notificaciones

**Dueño:** Antonio (diseño) + Jesús (implementación).
**Fecha:** semana 3-4 post-demo.

**Qué incluye:**
- Worker BullMQ `notifications` con cola dedicada.
- Templates de email mínimos:
  - `audit_request_received` — manager
  - `audit_request_resolved` — alumno
  - `convocatoria_closing_initiated` — admins
  - `convocatoria_closed` — TODOS los candidatos
  - `data_export_ready` — alumno
- Provider: SendGrid o equivalente. Config por env.
- Schema: `User.email_verified`, `NotificationPreferences`.
- Rate limiting: máximo 1 email por usuario por hora (excepto cierre de convocatoria).

**Por qué bloquea producción:** sin notificación, los candidatos no se enteran de su outcome al cierre. Inaceptable para una oposición pública.

## 17.3 F2 — Subroles admin granulares (v6 fix: scope reducido)

**Dueño:** Jesús.
**Fecha:** semana 4 post-demo.

**Aclaración tras review:** `SUPER_ADMIN` ya está en V1 (ver §8.3.1) porque D22 lo requiere para reversa de cierre. Lo que F2 añade es la **granularidad adicional dentro del rol ADMIN** (operaciones diarias vs gestión de reglas).

**Qué incluye (lo que NO está en V1):**
- Sub-distinción dentro de `ADMIN`:
  - `ADMIN_OPERATIONS` — CRUD diario (rutas, RFID, kioskos, usuarios)
  - `ADMIN_RULES` — gestión de scoring + simulador
- Migración: campo `admin_subrole` en User (nullable, solo para rol ADMIN).
- Middleware `requireAdminSubrole(subrole)` para endpoints que lo requieran.
- Audit log de promociones/degradaciones de subrol.

**Lo que YA está en V1 (no hace falta esperar a F2):**
- `SUPER_ADMIN` como rol completo, separado de ADMIN.
- Permisos exclusivos del SUPER_ADMIN: reversa de cierre, aprobación GDPR forget, registro de OutcomeAmendment (F6).
- Validación en `/health/deep`: la organización debe tener ≥1 SUPER_ADMIN + ≥2 ADMIN.

**Por qué F2 ya no bloquea producción tan duro como antes:** la pieza crítica (SUPER_ADMIN) está en V1. F2 mejora la **higiene operativa** (que un admin que solo gestiona rutas no pueda activar versiones de scoring) pero el sistema funciona sin ella. Reclasificado como **deseable, no bloqueante**.

## 17.4 F3 — Acta PDF firmable digitalmente

**Dueño:** Jesús + Joel.
**Fecha:** semana 5 post-demo.

**Qué incluye:**
- Mejorar el acta v6 (que es PDF con SHA256) hacia firma digital cualificada.
- Integración con servicio de firma electrónica (FirmaProfesional, Viafirma, equivalente).
- Acta firmada por SUPER_ADMIN o por una comisión de tres.
- Almacenamiento del acta firmada como artefacto inmutable + hash en blockchain timestamping (opcional).

**Por qué bloquea producción:** una oposición pública en España suele requerir acta firmada por comisión, no solo PDF con hash.

## 17.5 F4 — Manager asignado a convocatoria

**Dueño:** Jesús (backend) + Alejandro (UI).
**Fecha:** semana 4-5 post-demo.

**Qué incluye:**
- Tabla pivote `ConvocatoriaManager` (convocatoria_id, user_id).
- Manager solo ve y resuelve auditorías de las convocatorias asignadas.
- Admin asigna managers a convocatorias.
- Audit log de asignaciones.

**Por qué NO bloquea producción:** V1 puede operar con un único manager (que ve todo). Se vuelve imprescindible cuando entran múltiples managers.

## 17.6 F5 — Auditoría tras cierre

**Dueño:** Jesús.
**Fecha:** semana 5-6 post-demo.

**Qué incluye:**
- Endpoint `POST /attempts/:id/audit-request` permite solicitudes incluso si convocatoria está CLOSED/LOCKED.
- Pero la solicitud queda con `status = POST_CLOSE`, no genera reevaluación que afecte el ranking.
- Se almacena como **queja formal**: evidencia para procesos legales posteriores (recurso del candidato).
- El sistema NO permite modificar el outcome a través de esta vía.
- Solo SUPER_ADMIN, en escenario muy extremo y con acta legal, puede reabrir parcialmente para una corrección. Esto queda fuera del flow normal.

**Por qué bloquea producción:** los candidatos tienen derecho de queja incluso post-cierre. Sin canalizarlo, lo van a hacer fuera del sistema.

## 17.7 F6 — Recurso del candidato sobre ranking final

**Dueño:** Antonio (coordinación legal con CMadrid).
**Fecha:** semana 6-8 post-demo.

**Por qué bloquea producción:** la ventana de reversa de 24h del cierre (D22) **no es suficiente** para procesar un recurso administrativo en oposición pública española. La Ley 39/2015 (LPACAP) prevé plazos de **un mes para recurso de alzada / recurso de reposición**. Un recurso aprobado a los 28 días debe poder modificar el outcome, pero el sistema en V1 marca la convocatoria como `LOCKED` (irrevocable absoluto) tras 24h. Sin este mecanismo, una resolución legal favorable al candidato no puede ejecutarse en el sistema.

### Qué incluye

**Tabla de mecanismos:**

| Mecanismo | Plazo | Quién lo gestiona | Efecto en convocatoria | Estado de la convocatoria |
|---|---|---|---|---|
| Auditoría de intento | Durante `OPEN` | Manager (resuelve) | Crea reevaluación que reemplaza al original en el ranking | `OPEN` |
| Reversa de cierre | 24h post `CLOSED` | SUPER_ADMIN | Devuelve a `OPEN` (raro, error administrativo) | `CLOSED` → `OPEN` |
| **Recurso administrativo** | **30 días post `LOCKED`** | **Comisión externa + SUPER_ADMIN** | **Genera `OutcomeAmendment`** | `LOCKED` (sigue locked, se amenda) |

### Modelo de datos nuevo (en F6)

> **TODO Fase 2 antes de implementar (v6 fix R4):**
> Cuando F6 entre a sprint, refactorizar este modelo para alinearlo con la convención v6:
> - Reemplazar `candidato_id` con `enrollment_id` (FK a Enrollment, no Student) — coherente con el resto del refactor v6.
> - Agregar `original_outcome_id` (FK a `CandidateOutcome.id`) como anchor explícito hacia el outcome original que se amenda.
> - Declarar la relación inversa `amendments OutcomeAmendment[]` en `CandidateOutcome` (ya declarada) y `OutcomeAmendment[]` en `Enrollment`.
> - Agregar al `AuditLog` con `OUTCOME_AMENDMENT_REGISTER` (ya en enum).

```prisma
// FUTURO — Fase 2 (F6). NO incluir en V1 schema.
// Antes de implementar, aplicar los TODOs del bloque arriba.
model OutcomeAmendment {
  id                String   @id @default(cuid())
  convocatoria_id   String
  candidato_id      String        // TODO F6: → enrollment_id (FK a Enrollment)
  original_decision Decision      // APTO o NO_APTO original al cierre
  amended_decision  Decision      // nuevo veredicto post-recurso
  reason            String        // texto formal del recurso resuelto
  acta_recurso_url  String        // PDF del acta de comisión
  acta_sha256       String
  amended_by        String        // SUPER_ADMIN id
  amended_at        DateTime @default(now())
  organization_id   String

  @@index([convocatoria_id])
  @@index([candidato_id])         // TODO F6: → @@index([enrollment_id])
}
```

**Reglas:**
- Una convocatoria `LOCKED` **NO se desbloquea** por un recurso. Sigue `LOCKED`.
- El recurso resuelto produce un `OutcomeAmendment` que **complementa** el `CandidateOutcome` original. Ambos quedan en histórico.
- El acta de la comisión es **obligatoria** y se persiste con SHA256 igual que el acta del cierre.
- El portal del alumno y los exports muestran AMBAS decisiones: original (con su acta de cierre) y amendment (con su acta de recurso).
- Las plazas de la convocatoria **no se modifican**. Si un recurso aprueba a un candidato adicional, técnicamente se adjudica una plaza adicional fuera del cupo original — esto es práctica habitual en oposiciones públicas españolas y debe acordarse legalmente con CMadrid.

### Endpoints

```
GET    /convocatorias/:id/recursos              listado de OutcomeAmendments
POST   /convocatorias/:id/recursos              SUPER_ADMIN registra resolución
                                                body: {candidato_id, amended_decision,
                                                       reason, acta_pdf}
GET    /students/:id/full-evidence-pack         export ZIP firmado para defensa legal
                                                (todos los attempts, samples, audit, scores)
                                                Auth: candidato (sí mismo) o SUPER_ADMIN
```

### Estados ampliados de Convocatoria

```
   OPEN → CLOSING → CLOSED → LOCKED
                              │
                              └→ (LOCKED queda LOCKED, pero acepta OutcomeAmendments)
```

**Por qué bloquea producción:** sin esto, un recurso legal mal procesado puede invalidar la convocatoria entera y exponer al cliente a contencioso administrativo.

## 17.8 Reunión de planificación Fase 2

```
   Día 16 (martes 12/05/2026, post-demo):
     - Reunión de 2h, equipo completo.
     - Confirmar fechas de F1-F6 según prioridad.
     - Asignar responsables día a día.
     - Coordinar con CMadrid: DPO, asesor legal, formato del acta.
     - Salir con un sprint plan de 6-8 semanas escrito.

   (Día 15 = lunes 11/05 = REUNIÓN CMADRID demo; ver §5.4 calendario)
```

## 17.9 Lo que NO entra en Fase 2 (Fase 3+)

Para evitar scope creep:

```
   ✗ Pesos por ruta editables (peso != 1.0) — Fase 3
   ✗ Confidence model continuo (0..1) — Fase 3
   ✗ PWA del kiosko — Fase 3
   ✗ Reproductor de telemetría dinámico — Fase 3
   ✗ Analítica de cohorte y mapas de calor — Fase 3
   ✗ Atajos de teclado en matriz — Fase 3
```

Estos items mejoran la UX pero no son requisitos legales ni de producción inicial.

---

# 18. Deuda detectada en review adversarial v6 — pendiente de evaluar

Tras la segunda ronda adversarial (judgment-day), los jueces detectaron findings que **un solo juez vio**. Las 4 críticas + 5 warnings reales confirmados (los que ambos vieron) ya están resueltos en este documento. Esta sección lista los **suspects** —vistos por solo un juez— para revisión en la próxima reunión de planificación. **No bloquean la demo del 11/05** pero **deben evaluarse antes del cutover real**.

## 18.1 Suspects WARNING (real) — revisar y decidir

| # | Item | Origen | Acción propuesta | Cuándo |
|---|---|---|---|---|
| **18.1** | `computeRanking` no especifica cómo deduplica reevaluaciones (parent + child del mismo route_id del mismo enrollment) | Judge A | Documentar regla: si un attempt tiene `children` (reevaluaciones), el ranking usa solo el más reciente CLOSED. Filtro SQL en input al ranking. | Sprint 1 Fase 2 |
| **18.2** | `plazas` mutable mientras OPEN — exec doc dice "público desde día 1" pero schema no enforza | Judge A | Agregar `plazas_locked_at` que se popula al crear el primer ranking_snapshot; PATCH a plazas tras lock → 409 | Sprint 1 Fase 2 |
| **18.3** | Recategorización a ABORTED_TECHNICAL por admin sin doble validación | Judge A | Endpoint `/attempts/:id/recategorize` con justificación ≥ 50 chars + AuditLog; tras snapshot publicado requiere SUPER_ADMIN | Sprint 1 Fase 2 |
| **18.4** | Sin validación que `attempt.started_at ∈ [convocatoria.starts_at, closes_at]` | Judge A | Validación en `POST /attempts`. Reject si fuera de rango. | Sprint 1 Fase 2 |
| **18.5** | `GET /students/:id/standing` permite enumerar IDs y reconstruir el ranking | Judge A | Cambiar a `GET /students/me/standing`; o backend valida `params.id == auth.user.student_id` | **Sprint demo (es vulnerabilidad de privacidad)** |
| **18.6** | §8.7 endpoint legacy `/close` aún descrito en el doc — contradice §8.4 (3 pasos) | Judge A | Borrar §8.7 del paper o reescribir como referencia a §8.4 | Antes del kickoff (limpieza doc) |
| **18.7** | Doc ejecutivo §10.3 promete "exportación de evidencia" como capacidad presente cuando es F6 | Judge A (parcialmente fixeado en este round) | **Ya corregido** en este round con tiempo verbal futuro; verificar | ✓ |
| **18.8** | Joel seed plan dice "8 attempts con override" — terminología deprecada | Judge A | Reword a "8 attempts con reevaluación post-auditoría" | Antes del kickoff |
| **18.9** | Reevaluación creada a las 14:00 → ranking se actualiza el cron 6 AM día siguiente. 16h de desfase con UI del alumno | Judge B | Trigger ranking refresh on-demand al confirmar reevaluación; invalidar cache standing del candidato afectado | Sprint 1 Fase 2 |
| **18.10** | Dos kioskos pareados al mismo `vehicle_id` → dos attempts OPEN simultáneos en mismo camión | Judge B | Constraint DB: `UNIQUE WHERE status IN ('OPEN','PROCESSING','AWAITING_DOBACK_DATA')` por `vehicle_id` | **Sprint demo (corruption risk)** |
| **18.11** | "Acta firmada digitalmente" en exec doc induce a error legal (SHA256 ≠ firma cualificada) | Judge B (parcialmente fixeado en este round) | **Ya corregido** en exec §9.2 con lenguaje preciso; verificar | ✓ |
| **18.12** | `GdprDataExport.expires_at` no tiene cron de cleanup físico del ZIP | Judge B | Cron diario que borra ZIPs expirados del storage. Audit log de cleanup. | Sprint 1 Fase 2 |
| **18.13** | Privacy consent no tiene schema field — `User.privacy_consent_accepted_at` (ya añadido en este round). Verificar gate en auth middleware | Judge A (parcialmente fixeado) | Implementar el gate de auth: si rol ALUMNO y `privacy_consent_accepted_at IS NULL` → forzar pantalla aceptación antes de cualquier ruta protegida | **Sprint demo** |
| **18.14** | Audit log no registra DOWNLOAD del data export (solo registra que se solicitó) | Judge A | Agregar AuditAction `STUDENT_DATA_EXPORT_DOWNLOAD` con IP y timestamp | Sprint 1 Fase 2 |
| **18.15** | `tiebreak_key` con sorteo determinista — algoritmo predecible si alguien conoce la fórmula | Judge B (theoretical, low prob) | Documentar algoritmo exacto (SHA256 + encoding); incluir `closes_at_iso` en seed (fixeado en cascada de desempate) | ✓ (parcialmente) |
| **18.16** | Email burst de 200 candidatos al cierre — sin bounce handling | Judge A | Worker `notifications` con tracking de bounce, retry, fallback a notificación postal | F1 Fase 2 (ya está en plan) |
| **18.17** | Forget request bloqueado durante OPEN viola GDPR art. 12 (1 mes respuesta obligatoria) | Judge A | Sistema responde DENIED_LEGAL_BASIS antes de los 30 días con base legal LPACAP. Ya documentado en D23 fix. | ✓ |
| **18.18** | Multi-turno race entre cierre A (samples streaming Doback) y apertura B | Judge A | Definir buffer de gracia 10s antes de open B; samples con timestamp anterior al boundary van a A, posteriores a B. Documentar en D-MT-001 fixed | Sprint 1 Fase 2 |

## 18.2 Suspects SUGGESTION — anotar, no bloquear

| # | Item |
|---|---|
| 18.S1 | Joel 14 días con onboarding asume 100% productividad — recalibrar scope si necesario |
| 18.S2 | Sandbox Webfleet de CMadrid no confirmada — Antonio verifica antes del kickoff |
| 18.S3 | Endpoints GDPR sin rate limit — agregar 1 export/24h/usuario en F1 |
| 18.S4 | Acta PDF lenguaje mezclado español/inglés — template formal en F3 |
| 18.S5 | "<1% auditorías" sin base empírica — recalibrar tras primera convocatoria real |
| 18.S6 | Datos seed 10 plazas/50 candidatos no realista — alinear con ratio CMadrid (~25%) |
| 18.S7 | `RankingSnapshot` retention indefinida — política: dailies 30d, weeklies después, final indefinido |
| 18.S8 | Renumeración del ranking post-recategorización ABORTED_TECHNICAL post-cierre — ya cubierto por inmutabilidad LOCKED |

## 18.3 Cómo se procesan estos items

```
   1. Antes del kickoff (lunes 9:00 AM):
      - Antonio revisa esta sección durante 15 min
      - Items marcados "Antes del kickoff" → fixear ahora
      - Items "Sprint demo" → asignar a quien corresponda en kickoff
      - Items "Sprint 1 Fase 2" → entran al backlog Fase 2

   2. Durante el sprint (semana 1-2):
      Se mantiene foco en demo. NO se reabre esta lista.

   3. Reunión Fase 2 (día 15, post-demo):
      Esta sección se revisa entera. Cada item con dueño y fecha.
```

---

# Anexo A — Memoria histórica del proyecto

| Quiero saber sobre... | Voy a... |
|---|---|
| Decisiones de negocio con CMadrid | `training-module_documento-fundacional-v1` |
| Plan de migración previo | `training-module_plan-migracion-v2` |
| Decisiones mayo 2026 | `training-module_decisiones-mayo-2026` |
| Spec de scoring v1 | `training-module_scoring-spec-v1` |
| Webfleet integración v1 | `training-module_webfleet-integracion-v1` |
| Taxonomía 4 eventos | `project_stability_final_taxonomy` |
| VPS de despliegue | `project_vps_infrastructure` |
| Layout de carpeta de datos en VPS | `project_vps_data_folder_layout` |
| BD connection gotcha | `project_bd_connection_gotcha` |
| Prisma JSON null gotcha | `project_prisma_json_null_gotcha` |

---

# Anexo B — Documentos archivados

**No son fuente de verdad operativa.**

- Plan Maestro CMadrid v3.0 — `~/Desktop/dobacksoft-plan-maestro-cmadrid.pdf`
- Plan.md (Jesús) — Migración a Flask. Rechazado.
- Roadmap.md (Jesús) — Rechazado junto con el plan Flask.
- Documento Arquitectural Frontend (Alejandro) — Stack Vue rechazado, contenido de producto absorbido en §9.
- Paper Maestro v1 / v2 / v3 / v4 — Iteraciones previas, superadas por v5.
- Documento ejecutivo v1 / v2 — Iteraciones del documento de negocio, superadas por v3 ejecutivo (modelo oposición).

---

# Anexo C — CHECKLIST DE MODOS DE FALLO EN PRODUCCIÓN

> **Joel es el dueño de este checklist.** Lo ejecuta:
> - **Día 12** (verificación pre-demo, items aplicables)
> - **Antes del cutover real** (todos los items)
> - **Mensualmente post-cutover** como rutina

## C.1 INGEST / DATOS DEL SENSOR

| # | Modo de fallo | Defensa |
|---|---|---|
| 1.1 | Archivo malformado entra al parser | Validación Zod en boundary, error `INVALID_FILE_FORMAT` |
| 1.2 | Mismo archivo subido 2 veces | Hash SHA256 + UNIQUE(attempt_id, source, source_hash) |
| 1.3 | Archivo enorme (>500 MB) | Streaming parsing, límite 256 MB, async en worker |
| 1.4 | Encoding raro (BOM UTF-16, Latin-1) | Detección al inicio, rechazar si no UTF-8/ASCII |
| 1.5 | Timestamp en futuro | Validación: `t > now() + 5min` → reject |
| 1.6 | Filas duplicadas dentro del archivo | Dedup en parser por hash de fila |
| 1.7 | Archivo vacío o de 1 línea | Mínimo 100 filas, sino `INSUFFICIENT_DATA` |

## C.2 WEBFLEET

| # | Modo de fallo | Defensa |
|---|---|---|
| 2.1 | API Webfleet caída | Timeout 30s + circuit breaker + estado visible |
| 2.2 | Cuota 14.400/día agotada | Contador Redis + alerta a 80% + cola si 100% |
| 2.3 | Username con tilde mal codificado | URL encoding UTF-8 OBLIGATORIO |
| 2.4 | Webfleet retorna lista vacía | Distinguir 200 con [] vs error, loggear ambos |
| 2.5 | Latencia alta | Sync siempre async, nunca síncrono desde request |
| 2.6 | Datos viejos por rate limit | Flag `webfleet_data_freshness` + notificar |
| 2.7 | Cambio de schema en Webfleet | Contract tests semanales contra sandbox |

## C.3 NORMALIZATION

| # | Modo de fallo | Defensa |
|---|---|---|
| 3.1 | Timestamps no monótonos | Rechazar con `TIMESTAMP_DISORDERED` |
| 3.2 | Gap de 5+ minutos | Flag `data_gap` explícito + data_quality baja |
| 3.3 | Aceleraciones imposibles | Flag `outlier`, no eliminar, marcar |
| 3.4 | Bias del sensor | Calibración estadística automática |
| 3.5 | Mismo evento detectado por sensor Y Webfleet | Dedup en detection con tolerancia ±2s |
| 3.6 | data_quality calculado mal | Tests determinísticos, threshold configurable |

## C.4 DETECTION

| # | Modo de fallo | Defensa |
|---|---|---|
| 4.1 | NaN en sample llega a detect | normalization rejecta, NUNCA llega a detect |
| 4.2 | Eventos compound (acel+gyro) | "primary event" + "secondary evidence" |
| 4.3 | Detect produce eventos diferentes en runs | Tests determinísticos. CI bloquea si reproduce !== anterior |
| 4.4 | Detector con bug en versión nueva | `detector_version` pinned + canary deploy |

## C.5 SCORING

| # | Modo de fallo | Defensa |
|---|---|---|
| 5.1 | criteria_version no existe | FK en DB + chequeo en servicio |
| 5.2 | División por cero | Tests determinísticos cubren edge cases |
| 5.3 | Score negativo o >10 | Clamp [0, 10] explícito + assertion |
| 5.4 | Reglas que se contradicen | Motor declarativo, no permite contradicción |
| 5.5 | Cambio de criteria mid-attempt | Pinned al ABRIR el attempt, no al cerrar |
| 5.6 | score_audit no se popula | Transacción atómica con score |
| 5.7 | Simulator con criteria inválida | Validar overrides antes de simular |

## C.6 ATTEMPT LIFECYCLE

| # | Modo de fallo | Defensa |
|---|---|---|
| 6.1 | Attempt sin candidato (FK roto) | FK NOT NULL + constraint |
| 6.2 | Attempt cerrado y reabierto por bug | DB constraint: si frozen_at != null, ningún UPDATE |
| 6.3 | Attempt sin samples | Endpoint /close valida samples. Si no, error |
| 6.4 | Concurrent close (2 workers) | Lock optimista: WHERE frozen_at IS NULL |
| 6.5 | Reevaluación crea loop | Profundidad max = 5 |
| 6.6 | Attempt abandonado >24h sin cerrar | Cron diario marca abandoned |
| 6.7 | ABORTED_TECHNICAL mal asignado | Criterios automáticos + admin puede recategorizar |

## C.7 RANKING (NUEVO v5)

| # | Modo de fallo | Defensa |
|---|---|---|
| 7.1 | Cron nocturno no corre | Healthcheck del worker + alerta si snapshot >36h |
| 7.2 | Ranking calculado con datos parciales | Validar que todos los attempts CLOSED estén procesados antes |
| 7.3 | Empate sin desempate aplicado | Tests determinísticos cubren empates exactos |
| 7.4 | Snapshot is_final=true se sobreescribe | Trigger DB rechaza UPDATE excepto campos voided_*. Ver §8.7.3. |
| 7.5 | Ranking inconsistente entre snapshots consecutivos | Cada snapshot tiene UUID propio. Comparación visible al admin |
| 7.6 | Cierre de convocatoria sin esperar al cron | Recálculo final inmediato al cierre |
| 7.7 | Reapertura de convocatoria LOCKED | Bloqueado por DB constraint absoluto. CLOSED → OPEN solo via /close/reverse <24h. |
| 7.8 | CandidateOutcome duplicado | `enrollment_id @unique` (v6 fix R3): un outcome por inscripción |
| 7.9 | RankingEntry duplicada en mismo snapshot | UNIQUE(snapshot_id, enrollment_id) en schema |

## C.8 AUDITORÍAS (NUEVO v5)

| # | Modo de fallo | Defensa |
|---|---|---|
| 8.1 | Alumno solicita auditoría sin razón | Validación frontend Y backend (>30 caracteres) |
| 8.2 | Manager resuelve audit sin justificación | Validación: resolución obligatoria |
| 8.3 | Reevaluación crea attempt en convocatoria CLOSED | Bloqueado por constraint |
| 8.4 | Audit request abandonada (sin respuesta) | Alerta al manager si pendiente >7 días |

## C.9 KIOSKO

| # | Modo de fallo | Defensa |
|---|---|---|
| 9.1 | Doble lectura RFID milisegundos | Debounce 2s misma tarjeta, 500ms tarjetas distintas |
| 9.2 | Pérdida wifi en mitad attempt | IndexedDB queue + reintentos infinitos backoff |
| 9.3 | Browser colgado, alumno cambia tarjeta | Modo recovery al reabrir |
| 9.4 | IndexedDB lleno (>50 eventos) | Alerta visible "consultar técnico" |
| 9.5 | Reinicio dispositivo mid-attempt | Persistir IndexedDB tras CADA acción crítica |
| 9.6 | Pantalla se apaga (wake-lock falló) | wake-lock con verificación + indicador si no |
| 9.7 | Tarjeta no leída pero kiosko cree que sí | Cada apertura requiere RFID válido en BACKEND |
| 9.8 | Apertura concurrente mismo attempt en 2 kioskos | Lock backend |
| 9.9 | Batería del dispositivo agotándose | Indicador <20%. Sync proactivo |

## C.10 FRONTEND

| # | Modo de fallo | Defensa |
|---|---|---|
| 10.1 | Convocatoria 500 alumnos en matriz/ranking | Virtualización react-window obligatoria |
| 10.2 | React Query cache stale | Invalidación post-mutaciones |
| 10.3 | Push reload pierde estado del audit form | Persistir borrador en localStorage |
| 10.4 | Audit request sin justificación pasa | Validación frontend Y backend |
| 10.5 | data_quality LOW no avisa al manager | Banner amarillo en M6 |
| 10.6 | Manager intenta modificar nota directamente | UI sin botón. Backend rechaza si llega |

## C.11 INFRA

| # | Modo de fallo | Defensa |
|---|---|---|
| 11.1 | Postgres lleno | Alerta a 80%. Archivado raw_samples >12 meses |
| 11.2 | Redis caído | Alerta + worker healthcheck que falla |
| 11.3 | Worker caído pero API acepta uploads | Healthcheck cruzado |
| 11.4 | Backup falla silenciosamente | Verificación post-backup, alerta si falla 2 veces |
| 11.5 | Migración Prisma falla a la mitad | `migrate deploy` en CI, backup pre-migración |
| 11.6 | Logs llenan disco | Logrotate + alerta a 80% |

## C.12 OPERATIVOS / CLIENTE

| # | Modo de fallo | Defensa |
|---|---|---|
| 12.1 | CMadrid pide cambiar threshold "para ayer" | Versionado: cambio = nueva versión, attempts viejos no afectados |
| 12.2 | Bug en scoring detectado 1 mes después | Reevaluación masiva opt-in, NO sobreescribe |
| 12.3 | Auditoría legal pide datos pero raw_samples expirados | Política de retención clara contractualmente |
| 12.4 | CMadrid pide reabrir convocatoria cerrada (LOCKED) | Bloqueado por sistema. Conversación documentada |
| 12.5 | CMadrid cambia número de plazas mid-convocatoria | Bloqueado por sistema una vez publicado. Conversación documentada |

## C.13 CIERRE DE CONVOCATORIA REFORZADO (NUEVO v6)

| # | Modo de fallo | Defensa |
|---|---|---|
| 13.1 | Admin único intenta cerrar | Endpoint `/close/confirm` valida `confirming_admin_id != closing_admin_id` |
| 13.2 | Admin escribe nombre incorrecto en confirmación | Validación strict-equal del nombre. Error claro. |
| 13.3 | Acta PDF no se genera (Puppeteer falla) | Cierre no se ejecuta. Status queda en CLOSING. Admin debe reintentar. |
| 13.4 | Hash SHA256 del acta no coincide al verificar | Alarma. Acta queda en cuarentena. Investigar. |
| 13.5 | Reversa intentada después de 24h | Endpoint rechaza con 403 + mensaje "ventana expirada" |
| 13.6 | Reversa sin justificación o <50 chars | Validación frontend Y backend |
| 13.7 | Convocatoria con `status = LOCKED` recibe UPDATE | Constraint DB lo bloquea |
| 13.8 | Dos admins inician cierre concurrente | Lock DB-enforced: `UPDATE convocatoria SET status='CLOSING', closing_admin_id=$me, closing_initiated_at=NOW() WHERE id=$id AND status='OPEN' RETURNING *`. Si filas afectadas = 0, otro admin ganó el race; respuesta 409 con `closing_admin_id` actual. El segundo admin debe ir a `/close/confirm`, no a `/close/initiate`. La transición OPEN→CLOSING es atómica. |
| 13.9 | Solo hay un admin en la organización (V1 demo con admin único) | Validación previa al primer `/close/preview`: contar admins activos. Si `count(admin) < 2 OR count(super_admin) = 0`, error con instrucción de crear cuentas faltantes. Cierre imposible hasta tener 2 ADMIN + 1 SUPER_ADMIN distintos. |
| 13.10 | Confirmación por nombre escrito es bypaseable si un atacante tiene 2 sesiones de admins distintos | El paso `/close/confirm` exige re-autenticación (re-introducir contraseña) además del nombre escrito. Sin re-auth, el endpoint rechaza 401. |

## C.14 GDPR / PRIVACIDAD (NUEVO v6)

| # | Modo de fallo | Defensa |
|---|---|---|
| 14.1 | Alumno solicita data export, datos enormes (>1GB) | Generación async + paginación. Email con link al estar ready. |
| 14.2 | URL de export se filtra | URL firmada con expiración 7d. Single-use idealmente. |
| 14.3 | Alumno solicita borrado durante convocatoria abierta | Procesamiento bloqueado hasta cierre + plazo legal. |
| 14.4 | Borrado borra evidencia legal | Soft delete + retención de attempts cerrados como evidencia. |
| 14.5 | DPO contact no configurado | Error visible en config check del deploy. |
| 14.6 | Aviso de privacidad no aceptado por candidato | Login bloqueado hasta aceptación. |
| 14.7 | Audit log se llena (millones de filas) | Particionado por mes + archivado tras 24 meses. |

## C.15 SYNC DOBACK ELITE (NUEVO v6)

| # | Modo de fallo | Defensa |
|---|---|---|
| 15.1 | Doback Elite no notifica al kiosko al final del attempt | Kiosko marca `awaiting_doback_data = true` y entra a status AWAITING_DOBACK_DATA |
| 15.2 | Pairing token comprometido | Revocación por admin. Audit log de pairings. |
| 15.3 | Doback Elite POST con firma inválida | Backend rechaza 401. Log de incidente. |
| 15.4 | Cron de reintento no corre | Healthcheck del worker + alerta si attempt en AWAITING >2h |
| 15.5 | Doback Elite jamás hace POST (>24h) | Cron marca attempt.status = ABORTED_TECHNICAL. Notifica admin. Candidato debe repetir. |
| 15.6 | Datos de Doback Elite llegan corruptos | Validación de schema. Si corrupto: ABORTED_TECHNICAL + investigación. |

## C.16 CRITERIA VERSION PINNING AL ABRIR (NUEVO v6)

| # | Modo de fallo | Defensa |
|---|---|---|
| 16.1 | Attempt creado sin criteria_version active disponible | Error: no hay versión activa. Admin debe activar una. POST falla. |
| 16.2 | Activación de nueva criteria afecta attempt en curso | Imposible: criteria_version está pinned al CREAR. UPDATE bloqueado. |
| 16.3 | Test de reproducibilidad falla por mismatch de versión | El attempt guarda versión pinned. Replay siempre usa esa. |
| 16.4 | criteria_version pinned no existe en DB | FK NOT NULL. Si la versión se borra (no debería), constraint protege. |

## C.17 Cómo usar este checklist

```
   ▶ DÍA 12 (pre-demo)
     Items aplicables a la demo: 1.1, 1.2, 2.3, 5.3, 6.3,
     7.1, 7.6, 8.1, 9.1, 9.3, 10.1, 10.6,
     13.1, 13.2, 13.3, 16.1, 16.2
     ~17 items, 3 horas en equipo. Joel coordina.

   ▶ ANTES DE CUTOVER REAL
     TODOS los items. 3-4 días de testing dedicado.
     Especial atención a C.13 (cierre), C.14 (GDPR), C.15 (Doback).

   ▶ MENSUAL POST-CUTOVER
     Pasada de items operativos (C.11, C.12, C.14).
```

---

# Anexo D — Glosario

| Término | Significado |
|---|---|
| **Attempt** | Un intento de evaluación. Unidad central. Un alumno + una ruta + una sesión = un attempt. |
| **Convocatoria** | Proceso de oposición concreto. Tiene plazas, fecha de cierre, ruta principal de desempate, candidatos. |
| **Ranking** | Ordenamiento competitivo dentro de una convocatoria. Se actualiza diariamente. Final al cierre. |
| **Plazas** | Número de candidatos que entrarán al final. Definido por convocatoria, público desde el día 1. |
| **Corte** | Línea entre los candidatos que entran (top N = plazas) y los que no. Provisional hasta el cierre. |
| **Cierre de convocatoria** | Acción administrativa irrevocable que congela el ranking y emite las decisiones APTO/NO_APTO. |
| **Auditoría** | Solicitud formal del alumno para revisar un intento. Derecho del candidato. Frecuencia esperada <1%. |
| **Reevaluación** | Attempt nuevo con `parent_attempt_id`. Se genera tras una auditoría confirmada. El original NO se modifica. |
| **CMadrid** | Cuerpo de bomberos de la Comunidad de Madrid. Cliente. |
| **DobackSoft** | Sistema actual de telemetría del que extraemos Training. |
| **Doback Elite** | Dispositivo propio instalado en cada camión. Sensor inercial + GPS propio. |
| **Webfleet** | Plataforma de gestión de flotas de Bridgestone (antes TomTom Telematics). Aporta GPS + KPIs de comportamiento + eventos. |
| **Kiosko** | El dispositivo (tablet/PC) instalado en la cabina del camión. Pantalla simple, RFID. |
| **RFID** | Tarjeta sin contacto. Cada alumno tiene la suya. El lector emite el UID como teclas USB-HID. |
| **Manager** | El profesor / instructor que supervisa. Solo lectura. Resuelve auditorías. |
| **Score / Nota** | Valor 0-10 que el sistema calcula automáticamente para un attempt. |
| **Decision** | El veredicto APTO/NO_APTO. SOLO existe a nivel de candidato + convocatoria al cierre. |
| **Override** | Intervención manual sobre un veredicto. **En v5: NO existe como flujo normal.** Solo via auditoría. |
| **frozen_at** | Timestamp que marca cuándo un attempt se cerró. Si está poblado, el attempt es inmutable. |
| **parent_attempt_id** | FK al attempt original cuando este es una reevaluación. |
| **raw_samples** | Datos crudos sin procesar (sensor o Webfleet). |
| **normalized_samples** | Samples saneados por package `normalization`. |
| **Event** | Algo detectable: frenada brusca, exceso, etc. Tiene `source` y `confidence`. |
| **Source** | De dónde viene un event: `sensor` o `webfleet`. |
| **Confidence** | Qué tan confiable es un event: `high` o `low`. Ortogonal a source. |
| **data_quality** | Calidad global de un attempt: `HIGH | MEDIUM | LOW`. |
| **score_audit** | Tabla con desglose granular del score: regla a regla, evidencia. |
| **criteria_version** | Versión inmutable de las reglas de scoring. |
| **CandidateOutcome** | Decisión final APTO/NO_APTO de un candidato en una convocatoria. Generada al cierre. |
| **AuditRequest** | Solicitud formal de auditoría hecha por un alumno. |
| **Simulator** | Endpoint y pantalla admin: simula cambios de reglas, muestra reordenamiento del ranking. |
| **Pairing** | Proceso one-time para vincular un kiosko al sistema con un token. |
| **Wake-lock** | API del navegador que evita que la pantalla se apague. Crítica en kiosko. |
| **IndexedDB** | Almacenamiento local persistente del browser. Usado en kiosko para cola offline. |
| **BullMQ** | Librería de colas async sobre Redis. |
| **Prisma** | ORM TypeScript. |
| **Zustand** | Store de estado React. |
| **React Query** | Librería de fetch + cache + sync de datos del servidor. |
| **Leaflet** | Librería de mapas open source. Envuelta en `<MapViewer>`. |
| **Puppeteer** | Chrome headless para generar PDFs server-side. |
| **Cutover** | Momento de pasar del sistema viejo al nuevo. Por convocatorias, no Big Bang. |
| **Modo sombra** | Procesar mismos inputs en ambos sistemas y comparar outputs sin servir el nuevo a usuarios. |
| **Idempotencia** | Misma operación N veces = mismo resultado que una. |
| **Reproducibilidad** | Dado un attempt cerrado, regenerar exactamente el mismo score. |
| **Inmutabilidad** | Atributo de un attempt cerrado o de una convocatoria cerrada: nada lo modifica. |
| **ABANDONED** | Estado de attempt: candidato no completó. Cuenta como 0. |
| **ABORTED_TECHNICAL** | Estado de attempt: fallo del sistema. NO cuenta. |

---

**Fin del Paper Maestro v5. Documento autocontenido. Punto de partida obligatorio del equipo.**

