# Roadmap — DobackSoft V3 (Training CMadrid)

Basado en: *Paper Maestro v4 — Antonio Hermoso*
Fecha: 2026-04-28
Principio rector: **mínimos cambios a templates y static**. Todo lo nuevo va en blueprints/services/models. Las plantillas existentes se reutilizan o se extienden con bloques parciales (`hx-swap`).

---

## Estado actual vs requisitos

| Área | Estado actual | Gap |
|------|--------------|-----|
| Autenticación JWT | ✅ completo | — |
| RBAC ADMIN/MANAGER | ✅ corregido | — |
| Vehículos CRUD | ✅ básico | falta `type`, `brand`, sensor serial |
| Rutas (Routes) | ✅ CRUD básico | falta GeoJSON geometry, km, parcelas |
| Sesiones | ✅ básico | debe renombrarse a **Cohort** + Attempt |
| Eventos | ✅ básico | falta confidence, criterio vinculado |
| KPIs / Dashboard | ✅ esqueleto | falta datos reales de scoring |
| Reportes | ✅ estructura | falta generación real desde ScoreAudit |
| Ingesta / Uploads | ✅ UI | falta pipeline normalize→detect→score |
| Alumnos (Student) | ❌ no existe | modelo + CRUD completo |
| RFID | ❌ no existe | modelo + endpoint tap + debounce |
| Attempt | ❌ no existe | entidad central de todo el sistema |
| RawSample / NormalizedSample | ❌ no existe | pipeline de telemetría |
| CriteriaVersion | ❌ no existe | versionado pinneado de baremos |
| ScoreAudit | ❌ no existe | auditoría granular por regla |
| Kiosko | ❌ no existe | portal offline-first, sin puntuaciones |
| Webfleet integration | ❌ no existe | GPS/velocidad principal, circuit breaker |
| Scoring engine | ❌ no existe | motor de puntuación + simulador |
| Portal Alumno | ❌ no existe | 5 pantallas, sin telemetría raw |

---

## Invariantes técnicas (no negociables)

Toda decisión de implementación debe respetar estas cinco propiedades:

1. **Idempotencia**: reprocesar el mismo TXT siempre produce el mismo resultado.
2. **Reproducibilidad**: dado `attempt_id`, el score es siempre recalculable.
3. **Inmutabilidad**: un attempt `frozen_at != null` nunca se modifica; reevaluación crea nuevo attempt con `parent_attempt_id`.
4. **Versionado pinneado**: `attempt.criteria_version_id` no cambia post-freeze, aunque se publique una nueva versión de criterios.
5. **Fuente de confianza**: Webfleet es la fuente primaria de GPS y velocidad; el sensor TXT es secundario (fallback).

---

## Fase 0 — Fundamentos de datos (BLOCKER para todo lo demás)

### 0.1 Modelos nuevos (Prisma / SQLAlchemy)

#### `Student`
```
id, name, dni, email, organizationId, rfid_uid (nullable), status, created_at
```

#### `RfidCard`
```
id, uid (unique), student_id (FK, nullable — puede no estar asignada), issued_at, revoked_at
```

#### `CriteriaVersion`
```
id, version_tag (semver), published_at, published_by, rules_json (inmutable post-publish), is_active
```

#### `Attempt`
```
id, cohort_id (FK Session renombrada), student_id, vehicle_id, route_id,
criteria_version_id (pinneado al publicar), scheduled_start, scheduled_end,
actual_start, actual_end, status (PENDING|ACTIVE|SCORING|FROZEN|OVERRIDE),
frozen_at, parent_attempt_id (FK self, nullable — reevaluación),
score_total (nullable hasta freeze), data_quality (HIGH|MEDIUM|LOW),
created_by, override_reason (nullable), override_by (nullable)
```

#### `RawSample`
```
id, attempt_id, source (SENSOR|WEBFLEET), ts, lat, lon, speed_kmh, heading,
altitude_m, raw_json, ingested_at
```

#### `NormalizedSample`
```
id, attempt_id, ts, lat, lon, speed_kmh, source_used (SENSOR|WEBFLEET|INTERPOLATED),
quality_flag (HIGH|MEDIUM|LOW), gap_filled (bool)
```

#### `Event` (extender el modelo existente)
Agregar campos: `attempt_id (FK)`, `confidence (HIGH|LOW)`, `criteria_rule_id`, `auto_detected (bool)`.

#### `ScoreAudit`
```
id, attempt_id, criteria_version_id, rule_id, rule_name, max_points,
earned_points, events_applied (json array of event ids), calculated_at
```

#### `KioskoPairing`
```
id, device_uuid, cohort_id (FK), paired_at, last_heartbeat_at, is_active
```

### 0.2 Migración de Session → Cohort

La tabla `sessions` pasa a llamarse `cohorts` o se agrega un alias. Los blueprints de `sessions` se mantienen por ahora con redirección para no romper URLs existentes.

Campos a agregar al modelo `Session`/`Cohort`:
```
max_concurrent (int, default 10), webfleet_group_id (nullable), status (DRAFT|ACTIVE|CLOSED)
```

### 0.3 Actualizar `Vehicle`
Agregar: `type (CAMION_BRL|OTRO)`, `brand`, `sensor_serial (unique, nullable)`.

### 0.4 Actualizar `Route`
Agregar: `geometry_geojson (text)`, `total_km (float)`, `parcelas_json (array)`.

---

## Fase 1 — Pipeline de ingesta y scoring

### 1.1 Ingesta TXT del sensor

**Endpoint**: `POST /api/v1/attempts/<id>/ingest/sensor`
**Servicio**: `app/services/ingestion/sensor_parser.py`

- Parsea formato TXT propietario → lista de `RawSample` con `source=SENSOR`
- Idempotente: misma inserción con mismo `ts` → upsert por `(attempt_id, source, ts)`
- Calcula `data_quality` del attempt según cobertura y gaps

### 1.2 Ingesta Webfleet

**Servicio**: `app/services/ingestion/webfleet_client.py`

- Integración REST Webfleet API
- Circuit breaker en Redis: si >3 errores consecutivos → modo fallback sensor
- Quota: 14.400 req/día → rate limiter en Redis (`webfleet:quota:{date}`)
- Guarda como `RawSample` con `source=WEBFLEET`

```python
# Estructura del circuit breaker
WEBFLEET_CB_KEY = "webfleet:circuit:{date}"
# Estados: CLOSED (normal) | OPEN (fallback) | HALF-OPEN (probando)
```

### 1.3 Normalización

**Servicio**: `app/services/pipeline/normalizer.py`

- Fusiona SENSOR + WEBFLEET por ventana temporal (±500ms)
- Regla de fuente: Webfleet prioritario para GPS/speed; sensor como fallback
- Interpola gaps < 5s; marca como LOW_QUALITY si gap > 5s
- Produce `NormalizedSample[]` por attempt
- **Endpoint trigger**: `POST /api/v1/attempts/<id>/normalize`

### 1.4 Detección de eventos

**Servicio**: `app/services/pipeline/event_detector.py`

- Lee `NormalizedSample[]` + `CriteriaVersion.rules_json`
- Produce `Event[]` con `confidence=HIGH|LOW`
  - HIGH: señal limpia, fuente Webfleet, sin interpolación
  - LOW: interpolado o gap cercano
- Idempotente: re-detección limpia eventos anteriores del mismo attempt
- **Endpoint**: `POST /api/v1/attempts/<id>/detect`

### 1.5 Scoring

**Servicio**: `app/services/pipeline/scorer.py`

- Lee `Event[]` + `CriteriaVersion.rules_json` pinneada al attempt
- Produce `ScoreAudit[]` granular + `score_total`
- **Nunca** recalcula si `attempt.frozen_at != null`
- **Endpoint**: `POST /api/v1/attempts/<id>/score`

### 1.6 Freeze

**Endpoint**: `POST /api/v1/attempts/<id>/freeze`
**Rol requerido**: ADMIN

- Setea `frozen_at = now()`
- Setea `status = FROZEN`
- A partir de aquí: solo lectura. Override abre un nuevo attempt.

### 1.7 Simulador de scoring

**Endpoint**: `POST /api/v1/scoring/simulate`
**Rol**: ADMIN
**Body**: `{ attempt_id, criteria_version_id (puede ser distinto al pinneado) }`

- Corre el scorer sobre el attempt con la versión de criterios indicada
- **Nunca** persiste resultado ni modifica el attempt
- Devuelve `ScoreAudit[]` temporal para comparación
- Útil para evaluar impacto de nuevo baremo antes de publicar

---

## Fase 2 — Portal Manager (ampliar lo existente)

Pantallas a construir/completar. Principio: reutilizar `base.html` + tablas existentes con HTMX parciales.

### 2.1 Gestión de Cohorts (renombrar Sessions)

Ruta: `/cohorts/`
- Listado con estado (DRAFT/ACTIVE/CLOSED), fechas, nº alumnos
- Crear/editar/cerrar cohort
- Asignar vehículo + ruta + rango horario
- **Cambio mínimo**: extender blueprint `sessions` existente, añadir campos en template

### 2.2 Gestión de Alumnos

Blueprint nuevo: `app/blueprints/students/`
Ruta: `/students/`

- CRUD: crear, editar, desactivar alumno
- Asignar RFID (buscar tarjeta libre → vincular)
- Historial de attempts por alumno (tabla simple, sin telemetría)
- Template: `students/list.html`, `students/detail.html` — extends `base.html`

### 2.3 Gestión de Attempts

Blueprint nuevo: `app/blueprints/attempts/`
Ruta: `/attempts/`

- Crear attempt (cohort + alumno + vehículo + ruta + ventana horaria)
- Ver estado del pipeline (PENDING→ACTIVE→SCORING→FROZEN)
- Trigger manual de ingest/normalize/detect/score (botones HTMX)
- Override con campo `reason` obligatorio (textarea, mínimo 20 chars)
- Reevaluar: crea nuevo attempt con `parent_attempt_id`
- Template: reutilizar card + tabla existentes

### 2.4 Matriz de resultados

Ruta: `/cohorts/<id>/matrix`
- Tabla: filas=alumnos, columnas=reglas del baremo, celdas=puntos ganados/máximos
- Fila final: totales
- Color-coded: verde ≥ umbral, rojo < umbral
- Export CSV (endpoint `GET /api/v1/cohorts/<id>/matrix.csv`)
- Template: tabla HTML con CSS badge existente

### 2.5 Estadísticas de cohort

Ruta: `/cohorts/<id>/stats`
- Distribución de scores (histograma sencillo con CSS, sin chart library)
- Top 3 reglas más falladas
- Alumnos sin attempt completado
- Template: cards + tabla, reutiliza componentes existentes

### 2.6 RFID Management

Ruta: `/rfid/`
Blueprint: extender `admin` o nuevo `rfid`

- Listado de tarjetas (uid, alumno asignado, estado)
- Asignar / desasignar tarjeta
- Historial de taps por tarjeta (últimas 50 entradas)

---

## Fase 3 — Portal Alumno (nuevo, minimalista)

Blueprint: `app/blueprints/alumno/`
Autenticación: JWT con rol `ALUMNO` (agregar al enum de roles).

**Reglas no negociables**:
- Sin puntuaciones visibles
- Sin telemetría raw
- Sin acceso a datos de otros alumnos

### Pantallas

1. **Login** — reutilizar `auth/login.html`
2. **Mi perfil** — nombre, DNI, foto (opcional), RFID asignado, próximo attempt
3. **Mis attempts** — listado: fecha, cohort, vehículo, ruta, estado (sin score si no frozen)
4. **Detalle attempt** — estado del pipeline, eventos detectados (sin coordenadas exactas), resultado final si `frozen_at != null`
5. **Resultados** — solo attempts frozen: score total + desglose por área (no por regla individual)

Templates: `alumno/dashboard.html`, `alumno/attempts.html`, `alumno/attempt_detail.html` — extends `base.html` con sidebar reducido.

---

## Fase 4 — Kiosko (offline-first)

El kiosko es un dispositivo en la cabina del camión. **No forma parte de la app Flask principal** — es una SPA separada que se sincroniza con la API.

### 4.1 API endpoints para kiosko (en Flask)

```
POST /api/v1/kiosko/pair          # Registrar dispositivo en cohort
GET  /api/v1/kiosko/<uuid>/status # Estado actual (qué attempt está activo)
POST /api/v1/kiosko/rfid/tap      # Registrar tap RFID
POST /api/v1/kiosko/<uuid>/sync   # Subir datos offline acumulados
POST /api/v1/kiosko/<uuid>/heartbeat  # Keep-alive cada 30s
```

**Reglas**:
- `/rfid/tap` requiere `cohort_id`, `rfid_uid`, `ts` (timestamp del dispositivo)
- Debounce server-side: mismo uid dentro de 2s → ignorar (idempotente)
- El tap inicia o termina el attempt activo según estado
- `sync` acepta array de `RawSample` acumulados offline (JSON batch)
- Kiosko **nunca** recibe score ni nombre de alumnos previos

### 4.2 RFID debounce

```python
RFID_DEBOUNCE_KEY = "rfid:debounce:{cohort_id}:{uid}"
RFID_DEBOUNCE_TTL = 2  # segundos
```

Redis SETNX: si clave existe → rechazar tap (HTTP 409). Si no existe → procesar + setear TTL 2s.

### 4.3 Pantallas del kiosko (SPA — fuera de Flask templates)

Documentadas aquí como referencia para el equipo frontend:
1. Splash / pairing QR
2. Standby (esperando tap RFID)
3. Attempt activo (cronómetro, ruta en mapa offline)
4. Tap de salida (confirmar fin de recorrido)
5. Error / offline indicator
6. Configuración (código de acceso físico)

---

## Fase 5 — Portal Admin (ampliar)

### 5.1 Gestión de CriteriaVersion

Ruta: `/admin/criteria/`

- Listado de versiones con estado (DRAFT/PUBLISHED/DEPRECATED)
- Editor JSON de reglas (textarea con validación básica)
- Publicar versión (activa la versión → futuros attempts la usan; attempts existentes no se tocan)
- No se puede editar una versión PUBLISHED — clonar y editar el clon
- Ver diffs entre versiones (tabla side-by-side)

### 5.2 Gestión de Kioscos

Ruta: `/admin/kioscos/`

- Listado de dispositivos: uuid, cohort asignada, último heartbeat, estado
- Forzar desvinculación
- Ver log de taps recientes

### 5.3 Scoring Simulator UI

Ruta: `/admin/scoring/simulator`

- Seleccionar attempt + versión de criterios alternativa
- Botón "Simular" → llama `POST /api/v1/scoring/simulate`
- Muestra tabla comparativa: score actual vs score simulado, regla a regla
- **No guarda nada**

### 5.4 Audit Log

Ruta: `/admin/audit/`

- Tabla de eventos de sistema: overrides, freeze, publicación de criterios, pairing kiosko
- Filtros: fecha, tipo, usuario
- Export CSV

---

## Fase 6 — Webfleet Integration (servicio de fondo)

### 6.1 Polling scheduler

`app/services/webfleet/poller.py` — corre como Celery beat o APScheduler:
- Cada 6 segundos durante cohorts activas (10 req/min por vehículo)
- Respeta quota diaria (14.400 req/día): si se acerca al límite → reducir frecuencia
- Circuit breaker: 3 errores consecutivos → abrir circuito por 5 min

### 6.2 Autenticación Webfleet

- Credenciales en `.env`: `WEBFLEET_ACCOUNT`, `WEBFLEET_USERNAME`, `WEBFLEET_PASSWORD`, `WEBFLEET_API_KEY`
- Tokens renovados automáticamente

### 6.3 Mapeo vehículo → Webfleet object

Agregar a `Vehicle`: `webfleet_object_no (nullable)` — el identificador en Webfleet del camión.

---

## Deuda técnica y refactors necesarios

| Item | Prioridad | Motivo |
|------|-----------|--------|
| Renombrar `Session` → `Cohort` en modelos + blueprints | ALTA | Semántica correcta según paper |
| Migrar `Event` para incluir `attempt_id` y `confidence` | ALTA | Sin esto no hay scoring real |
| Añadir rol `ALUMNO` al enum de roles | ALTA | Portal alumno lo requiere |
| Agregar `webfleet_object_no` a `Vehicle` | MEDIA | Webfleet integration |
| Agregar `sensor_serial` a `Vehicle` | MEDIA | Matching automático de TXT |
| Agregar `geometry_geojson` a `Route` | MEDIA | Kiosko + detección de eventos |
| Setup Redis (si no está) | ALTA | Circuit breaker + RFID debounce |
| Setup Celery o APScheduler | MEDIA | Webfleet polling |

---

## Orden de implementación recomendado

```
Fase 0 (modelos)          ← BLOQUEANTE para todo
  ↓
Fase 1.1-1.3 (pipeline básico: ingest + normalize)
  ↓
Fase 2.1-2.3 (cohorts + alumnos + attempts básico)
  ↓
Fase 1.4-1.6 (detect + score + freeze)
  ↓
Fase 2.4-2.6 (matriz + stats + RFID)
  ↓
Fase 3 (portal alumno)
  ↓
Fase 4.1-4.2 (API kiosko + RFID debounce)
  ↓
Fase 5 (admin avanzado: criteria, simulator)
  ↓
Fase 6 (Webfleet real)
  ↓
Fase 4.3 (SPA kiosko — equipo frontend)
```

---

## Restricciones no negociables (cliente CMadrid)

- Kiosko **nunca** muestra puntuaciones ni nombres de compañeros
- RFID debe soportar multi-vuelta en un mismo cohort (mismo uid puede tapar múltiples veces)
- Webfleet es la fuente primaria de GPS/velocidad — el sensor TXT es fallback
- Un criterio publicado **no** reprocessa attempts existentes automáticamente
- Override de score requiere justificación textual (mínimo 20 caracteres) — solo MANAGER
- Reevaluación crea nuevo attempt; el original queda inmutable
- Un alumno no ve telemetría raw ni coordenadas exactas de su recorrido

---

## Variables de entorno a agregar a `.env`

```
# Webfleet
WEBFLEET_ACCOUNT=
WEBFLEET_USERNAME=
WEBFLEET_PASSWORD=
WEBFLEET_API_KEY=
WEBFLEET_BASE_URL=https://csv.webfleet.com

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```
