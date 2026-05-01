# Análisis — Integración Doback / Webfleet en Training

> **Fecha**: 2026-05-01
> **Branch**: `claude/training-doback-integration-analysis-RroDJ`
> **Estado**: análisis técnico — no se modificó código.
> **Objetivo**: definir cómo construir el motor de evaluación de Training desde cero, con Webfleet como input principal y Doback Elite como sensor IMU complementario.

---

## 1. Reality check verificado

### 1.1 Lo que existe en código (no quiere decir que funcione)

- **Pipeline determinista en `app/services/pipeline/`** — está cableado a 3 endpoints (`manager/routes.py:605,618` y `sessions/services.py:81`) pero **nunca se ha ejecutado contra un TXT real del Doback Elite**. Las 6 fixtures `tests/fixtures/sensor/*.txt` están a **0 bytes**. Las 3 fixtures de simulación y las 2 de Webfleet también están a **0 bytes**.
- **Modelos administrativos sólidos**: `Convocatoria`, `Enrollment`, `Attempt`, `AttemptEvent`, `Ranking`, `TrainingAuditLog`, `RfidCard`, `User+RBAC`, `Vehicle+VehicleConfiguration`. Esto sí está consistente y se puede mantener.
- **Kiosko/tap RFID**: `kiosko/services.py:32` `process_tap` crea Attempt en BD de verdad.
- **`VehicleConfiguration`** ya tiene `cgHeight=1.6, mass=12000, trackWidth=2.1, wheelbase=4.5` — sirven como input para el StabilityProcessor cuando exista.

### 1.2 Lo que no existe (verificado por `ls`, `grep`, `find`)

| Lo que `roadmap.md` y `memory/decision-webfleet-entra.md` dicen que debería estar | Estado real |
|---|---|
| `app/services/webfleet/` (cliente, normalizer, sync, mapper) | **No existe** |
| `app/workers/webfleet_worker.py` | **No existe** |
| `app/services/ingestion/webfleet_client.py` | **No existe** (`ingestion/` no existe) |
| Modelo `RawSample` con `source ∈ {SENSOR, WEBFLEET}` | **No existe** — `GpsMeasurement` no tiene campo `source` |
| Modelo `NormalizedSample` (fusión sensor+webfleet) | **No existe** |
| Modelo `CriteriaVersion` (versionado de baremos) | **No existe** — solo string `criteriaVersionPinned` |
| Modelo `ScoreAudit` (auditoría granular por regla) | **No existe** — solo JSONB `Attempt.scoreBreakdown` |
| Variables `WEBFLEET_*` en `.env.example` | `.env.example` solo tiene `SENTRY_DSN=` y `APP_VERSION=` |
| Cliente Webfleet en `requirements.txt` | No (solo `httpx` genérico) |
| Circuit breaker / rate limiter Redis | No |
| `Vehicle.webfleet_object_no` | No |
| Migrations Alembic activas | `migrations/versions/` vacío — schema se crea con `db.create_all()` |
| Tests del pipeline | Cero |

**Conclusión**: el 80% del input del sistema (Webfleet) **no está empezado**. Lo que llamamos "pipeline determinista" es código sin pruebas contra datos reales.

### 1.3 Bombas para la demo

- **UI del kiosko usa mock data**: `kiosko/routes.py:11` importa listas Python `CANDIDATOS, CONVOCATORIAS, AUDITORIAS` desde `manager/routes.py:54,98,303`. Las pantallas `/kiosko/rutas` y `/kiosko/intento/<id>` no leen BD.
- **Score breakdown del kiosko es ficticio**: `kiosko/routes.py:86-91` reparte la nota linealmente con pesos default; no lee `Attempt.scoreBreakdown` real.
- **Inmutabilidad de Attempt cerrado**: solo chequeada en código (`pipeline.py:34`, `scorer.py:54`). Sin trigger PG, cualquier UPDATE directo modifica score post-cierre.
- **Speed limit hardcodeado a 90 km/h** (`event_detector.py:27`) sin filtro de glitches GPS — un alumno puede ser penalizado por un pico espurio.
- **Servicios de soporte con 0 bytes**: `app/services/{stability_processor,kpi_calculator,alert_service,map_matching}.py`.

---

## 2. Webfleet — qué es y cómo se integra

**Webfleet** (ex TomTom Telematics, hoy Bridgestone) es la plataforma de gestión de flota que CMadrid ya tiene contratada para sus camiones de bomberos. La API pública es **WEBFLEET.connect**.

### 2.1 Características relevantes

- **Protocolo**: HTTPS REST. CSV por defecto; con `outputformat=json` devuelve JSON con los mismos nombres de columna.
- **Auth**:
  - Legacy: `account + username + password + apikey` por query string.
  - OAuth2 (recomendado): bearer-token (PDF Webfleet 2023).
- **Métodos relevantes para Training** (verificados en lib `webfleet-connect` PyPI):
  - `show_tracks` — **histórico de posiciones** (lat/lon/speed/timestamp/heading) por vehículo y rango. **Esto es lo principal.**
  - `show_object_report_extern` — estado actual del vehículo.
  - `show_vehicle_report_extern` — info estática.
  - `show_address_report_extern` — direcciones / paradas.
  - `show_nearest_vehicles` — geo-proximidad.
- **Retención**: 90 días en Webfleet. Después, dato perdido — hay que copiarlo a nuestra BD antes.
- **Cuota CMadrid**: 14.400 req/día (~10/min). Diseñar con rate-limit, batch, cache.
- **Gotcha**: el username de CMadrid lleva tilde — URL-encode UTF-8 obligatorio o devuelve 401 sin pista (`memory/decision-webfleet-entra.md:34`).
- **Acceso ya autorizado** por Bridgestone para el sprint vía Antonio.

### 2.2 División de responsabilidades de datos

| Dato | Fuente primaria | Fuente fallback |
|---|---|---|
| GPS (lat/lon) | Webfleet | Doback Elite |
| Velocidad | Webfleet | Doback Elite |
| Acelerómetro (ax/ay/az) | Doback Elite | — |
| Giróscopo (gx/gy/gz) | Doback Elite | — |
| Roll / Pitch / Yaw | Doback Elite | — |
| Células de carga (`usciclo1..4`) | Doback Elite | — |
| Índice de estabilidad (SI) | Doback Elite | — |

"20% Doback / 80% Webfleet" en volumen de datos GPS tiene sentido. Pero **la dinámica vehicular (la parte que define la nota de seguridad real) es 100% Doback** — Webfleet no entrega IMU. Importante distinguirlo en la conversación con el cliente.

---

## 3. Arquitectura propuesta — la joya de la corona

### 3.1 Principios firmes (no negociables)

1. **Sin lógica hardcoded** — todos los números en YAML versionado.
2. **Determinismo total** — mismo input + misma `criteria_version` = mismo output bit-a-bit.
3. **Idempotencia** — re-procesar 100 veces produce el mismo resultado.
4. **Inmutabilidad post-cierre** enforced en BD (trigger PG), no solo código.
5. **Webfleet = primaria GPS+velocidad. Doback = única IMU.**
6. **Safety-first** — gate físico que capa la nota antes del scoring, independiente de la fórmula.
7. **Cliente decide la fórmula vía YAML** — bumpás versión, no tocás código.
8. **Webfleet aislado con circuit breaker** — si cae, el sistema sigue degradado y marcado.

### 3.2 Estructura de módulos nueva

```
app/
├── ingestion/                          # CAPA DE ENTRADA
│   ├── doback/
│   │   ├── parser.py                   # TXT → RawSample[] (puro, sin DB)
│   │   ├── format_v1.yaml              # contrato del formato (columnas, unidades)
│   │   └── tests/                      # fixtures REALES anonimizadas
│   └── webfleet/
│       ├── client.py                   # cliente HTTP (auth, retry, encoding tildes)
│       ├── circuit_breaker.py          # Redis CLOSED/OPEN/HALF-OPEN
│       ├── rate_limiter.py             # cuota 14.400/día con alertas 70/85/95%
│       ├── poller.py                   # APScheduler/Celery beat → show_tracks
│       ├── normalizer.py               # response → RawSample[] con source=WEBFLEET
│       └── mapper.py                   # Vehicle.webfleet_object_no ↔ Webfleet objectno
├── pipeline/                           # MOTOR DE DECISIÓN
│   ├── 01_axis_validator.py            # valida ejes IMU; falla → ABORTED_TECHNICAL
│   ├── 02_sanitizer.py                 # filtra spikes, NaN, fuera de rango
│   ├── 03_normalizer.py                # fusiona SENSOR+WEBFLEET por ventana ±500ms
│   ├── 04_physical_metrics.py          # LTR, SSF, DRS, RSC, roll filtrado
│   ├── 05_safety_gate.py               # reglas críticas → cap de nota
│   ├── 06_event_detector.py            # eventos por reglas YAML
│   ├── 07_scorer.py                    # pesos YAML → ScoreAudit + score_total
│   ├── orchestrator.py                 # secuencia 01→07 transaccional
│   └── replay.py                       # re-ejecuta sandbox sin mutar
├── criteria/                           # CONFIGURACIÓN VERSIONADA
│   ├── v1.0.0.yaml                     # axes, sanitizer, gate, events, weights
│   ├── v1.0.1.yaml                     # cambios = nueva versión, nunca se sobreescribe
│   └── loader.py                       # lee, valida, hashea SHA256, cachea
└── models/
    └── (nuevos)
        ├── RawSample
        ├── NormalizedSample
        ├── CriteriaVersion
        └── ScoreAudit
```

### 3.3 Flujo end-to-end

```
[Doback TXT] ──► ingestion/doback/parser ──► RawSample(source=DOBACK_ELITE)
[Webfleet poller] ──► ingestion/webfleet/poller ──► RawSample(source=WEBFLEET)
                                          │
                                          ▼
                              pipeline/orchestrator.py
                                          │
01_axis_validator → 02_sanitizer → 03_normalizer → 04_physical_metrics
                                                          │
                                                          ▼
                                                 05_safety_gate (verdict + max_allowed)
                                                          │
                                                          ▼
                                                 06_event_detector → AttemptEvent[]
                                                          │
                                                          ▼
                                                  07_scorer → ScoreAudit[] + score_total
                                                          │
                                                          ▼
                              final = min(scorer.total, gate.max_allowed)
                                                          │
                                                          ▼
                                            persist + close + audit log
```

Un solo punto de orquestación. Cada paso función pura. Persistencia solo en `orchestrator.py`.

---

## 4. Modelo de datos nuevo (4 tablas clave)

```
CriteriaVersion(
    id, version_tag, yaml_text, yaml_sha256,
    published_at, published_by, is_active
)
   - INSERT-only. Una vez publicada, NUNCA se modifica.
   - Constraint: solo una `is_active=true` a la vez.
   - Convocatoria.criteriaVersionId → FK aquí, pinned al crear convocatoria.

RawSample(
    id, attempt_id, source ENUM(DOBACK_ELITE, WEBFLEET),
    ts, payload_json, ingested_at
)
   - Insert-only por convención de servicio.
   - Índice (attempt_id, source, ts).
   - Idempotencia: UNIQUE(attempt_id, source, ts, content_hash).

NormalizedSample(
    id, attempt_id, ts,
    lat, lon, speed_kmh,
    ax, ay, az, gx, gy, gz, roll, pitch,
    source_used ENUM(DOBACK, WEBFLEET, INTERPOLATED, FUSION),
    quality_flag ENUM(HIGH, MEDIUM, LOW),
    gap_filled BOOL
)
   - Output del normalizer. Una fila por timestamp consolidado.
   - Borrable y regenerable mientras attempt OPEN.

ScoreAudit(
    id, attempt_id, criteria_version_id,
    rule_id, rule_name, max_points, earned_points,
    events_applied JSON, computed_at
)
   - 1 fila por regla del YAML aplicada al attempt.
   - Permite explicar al alumno: "perdiste 1.2 pts por la regla SP-01".
   - Insert-only. Recálculo = DELETE+INSERT en misma transacción.
```

`Attempt.score` y `Attempt.scoreBreakdown` pasan a ser **caché** de `ScoreAudit`. La fuente de verdad pasa a `ScoreAudit + CriteriaVersion`.

---

## 5. YAML v1.0.0 — esqueleto

```yaml
# app/criteria/v1.0.0.yaml
version: "1.0.0"
published_at: "2026-04-30"

axes:
  source: "DOBACK_ELITE_FW_2.3"
  ax: { meaning: "longitudinal", positive: "forward", unit: "m/s²" }
  ay: { meaning: "lateral",      positive: "right",   unit: "m/s²" }
  az: { meaning: "vertical",     positive: "up",      unit: "m/s²" }
  gx: { meaning: "roll_rate",    positive: "right",   unit: "deg/s" }
  gy: { meaning: "pitch_rate",   positive: "up",      unit: "deg/s" }
  gz: { meaning: "yaw_rate",     positive: "ccw",     unit: "deg/s" }
  validation:
    rest_accmag_min_g: 0.95
    rest_accmag_max_g: 1.05

sanitizer:
  vehicle_profile: "HEAVY_VEHICLE_FIRE_TRUCK"
  max_roll_deg: 25
  max_pitch_deg: 20
  max_lateral_accel_ms2: 10
  max_longitudinal_accel_ms2: 10
  max_vertical_accel_ms2: 20
  max_roll_rate_deg_per_sample: 5
  max_pitch_rate_deg_per_sample: 4

gps_quality:
  min_satellites: 4
  hdop_good: 2.0
  max_valid_speed_kmh: 150       # MAX_VALID_FIRE_TRUCK
  min_coverage_percent: 50
  critical_coverage_percent: 30

normalizer:
  fusion_window_ms: 500
  primary_source_for_speed: "WEBFLEET"
  primary_source_for_imu: "DOBACK_ELITE"
  interpolate_gap_max_s: 5

safety_gate:
  rules:
    - { id: "SG-ROLL-01", metric: "max_abs_roll_deg",   threshold: 25,  cap_score_to: 0.0 }
    - { id: "SG-LAT-01",  metric: "lateral_accel_g",    threshold: 1.0, cap_score_to: 4.0 }
    - { id: "SG-LTR-01",  metric: "ltr_sustained",      threshold: 0.85, window_samples: 10, cap_score_to: 4.0 }
    - { id: "SG-DRS-01",  metric: "drs_min",            threshold: 0.10, cap_score_to: 4.0 }
    - { id: "SG-SI-01",   metric: "si_min",             threshold: 0.20, cap_score_to: 5.0 }
    - { id: "SG-COH-01",  metric: "axes_coherence_pct", threshold: 0.95, action: "ABORTED_TECHNICAL" }
    - { id: "SG-DQ-01",   metric: "gps_coverage_pct",   threshold: 50,  cap_score_to: 5.0 }
    - { id: "SG-DQ-02",   metric: "gps_coverage_pct",   threshold: 30,  action: "ABORTED_TECHNICAL" }

events:
  HARSH_BRAKING:
    metric: "ax"
    threshold_ms2: -2.5            # ← CMadrid decide
    severity_bands: { LOW: 2.5, MEDIUM: 4.0, HIGH: 6.0, CRITICAL: 8.0 }
    debounce_s: 3
  HARSH_ACCELERATION:
    metric: "ax"
    threshold_ms2: 3.0             # ← CMadrid decide
    severity_bands: { LOW: 3.0, MEDIUM: 4.0, HIGH: 6.0, CRITICAL: 8.0 }
  ACCELERATION_LATERAL:
    metric: "abs_ay"
    threshold_ms2: 2.5             # ← CMadrid decide
    severity_bands: { LOW: 2.5, MEDIUM: 4.0, HIGH: 6.0, CRITICAL: 8.0 }
  SPEEDING:
    metric: "speed_kmh"
    speed_limits_per_route: { default: 90 }
    excess_severity_kmh: { LOW: 5, MEDIUM: 15, HIGH: 25, CRITICAL: 35 }

penalty_points:
  LOW: 0.3
  MEDIUM: 0.6
  HIGH: 1.2
  CRITICAL: 2.0

scoring:
  weights:
    estabilidad: 0.40
    velocidad:   0.30
    ruta:        0.15
    conduccion:  0.15
  event_to_family:
    ACCELERATION_LATERAL: estabilidad
    SPEEDING:             velocidad
    DEVIATION:            ruta
    HARSH_BRAKING:        conduccion
    HARSH_ACCELERATION:   conduccion
  formula: "weight_max - sum(penalty_points)"
  clamp: { min: 0.0, max: 10.0 }
```

**Cuando CMadrid decida en la reunión** "frenazo brusco resta X" → se mete en `events.HARSH_BRAKING`. "Si hay riesgo crítico de vuelco capamos a 4" → `safety_gate.rules`. Bumpás `version`, generás `v1.0.1.yaml`, los nuevos Attempts pinean a la nueva version, los viejos siguen pineados a la 1.0.0.

---

## 6. Plan de PRs (orden recomendado)

| PR | Rama | Dueño | Objetivo |
|---|---|---|---|
| PR-A | `chore/cross-reset-pipeline` | Antonio | Aislar `app/services/pipeline/` actual en `_legacy_pipeline/`. |
| PR-B | `feat/be-criteria-version-table` | Jesús | Modelo `CriteriaVersion` + activar Alembic real. FK desde `Convocatoria`. |
| PR-C | `feat/be-rawsample-normalizedsample` | Jesús | Modelos `RawSample`, `NormalizedSample`, `ScoreAudit`. Migración. |
| PR-D | `feat/be-criteria-loader-v100` | Jesús | `app/criteria/loader.py` + `v1.0.0.yaml`. Tests carga + hash. |
| PR-E | `feat/wf-webfleet-client` | **Antonio** | `ingestion/webfleet/client.py` con auth (encoding tilde), `show_tracks`. |
| PR-F | `feat/wf-circuit-breaker-rate-limiter` | Antonio | Redis CB + RL, alertas 70/85/95%. |
| PR-G | `feat/wf-poller` | Antonio + Jesús | Celery beat — `show_tracks` por vehículo+ventana → `RawSample`. |
| PR-H | `feat/be-doback-parser-v2` | Jesús | Parser nuevo, función pura, sin DB. Fixtures **reales** anonimizadas. |
| PR-I | `feat/be-pipeline-01-axis-validator` | Jesús | Módulo + tests (incl. ejes invertidos). |
| PR-J | `feat/be-pipeline-02-sanitizer` | Jesús | Port limpio de `dobackv2/MeasurementSanitizer.ts`. |
| PR-K | `feat/be-pipeline-03-normalizer` | Jesús | Fusión sensor+webfleet por ventana, gaps, quality. |
| PR-L | `feat/be-pipeline-04-physical-metrics` | Jesús | LTR/SSF/DRS/RSC con fórmulas correctas (no copiar bug DRS dobackv2). |
| PR-M | `feat/be-pipeline-05-safety-gate` | Jesús + review Antonio | Reglas YAML → veredicto. |
| PR-N | `feat/be-pipeline-06-event-detector` | Jesús | Reglas YAML → AttemptEvent[]. Determinismo. |
| PR-O | `feat/be-pipeline-07-scorer` | Jesús + review Antonio | Pesos YAML → ScoreAudit[]. `min(score, gate.cap)`. |
| PR-P | `feat/be-pipeline-orchestrator` | Jesús | Secuencia 01→07, transacción, idempotencia. |
| PR-Q | `feat/be-immutability-trigger` | Jesús + review Antonio | Trigger PG `attempt_immutable_after_close`. |
| PR-R | `feat/fe-score-audit-ui` | Alejandro | "Por qué tu nota" con `ScoreAudit` por regla. |
| PR-S | `feat/fe-criteria-simulator-ui` | Alejandro + Jesús | Simulador: cambia thresholds y muestra score nuevo. |
| PR-T | `qa/sim-fixtures-real-doback` | Joel + Antonio | 1 TXT real anonimizado → 5 variantes (clean, frenazos, glitch GPS, gaps, vuelco simulado). |
| PR-U | `qa/be-pipeline-integration-tests` | Joel | Tests integración con fixtures reales. |

**Paralelos día 1**: PR-A, PR-B, PR-T.
**Cuello de botella**: PR-T (TXT real) bloquea a PR-H y PR-U.

---

## 7. Tests mínimos obligatorios

| Test | Verifica |
|---|---|
| `test_no_high_score_with_rollover_risk` | Si SG-ROLL-01 dispara, score ≤ 0 aún con cero eventos. |
| `test_safety_gate_blocks_high_score_under_ml` | `Attempt.score ≤ gate.max_allowed_score` siempre. |
| `test_same_input_same_score_same_versions` | Replay produce el mismo `score` y `scoreBreakdown` byte-a-byte. |
| `test_closed_attempt_immutable_service` | Llamar pipeline sobre cerrado → ValueError. |
| `test_closed_attempt_db_immutable` | UPDATE directo sobre cerrado → trigger PG falla. |
| `test_axis_mapping_consistency_rest_state` | Vehículo en reposo: validate pasa. |
| `test_axis_mapping_inverted_detected` | Ejes invertidos → ABORTED_TECHNICAL. |
| `test_gps_glitch_filtered` | 200 km/h aislado → no genera SPEEDING. |
| `test_gps_data_quality_low_caps_score` | gpsValido < 30% → ABORTED_TECHNICAL. |
| `test_duplicate_ingest_idempotent` | Subir 2 veces el mismo TXT → no duplica. |
| `test_drs_dimensional_correctness` | DRS ∈ [0,1] y monotónico. |
| `test_replay_does_not_mutate_attempt` | Snapshot pre/post igual. |
| `test_criteria_version_pinning` | Re-replay usa la versión pineada, no la nueva. |
| `test_webfleet_circuit_breaker_opens` | 3 errores consecutivos → CB OPEN → fallback a sensor. |
| `test_webfleet_rate_limit_alerts_at_70_85_95_pct` | Logs/alertas a esos umbrales. |
| `test_webfleet_username_with_tilde_encoded` | Username "Comunidad de Madrid" se URL-encodea correctamente. |

---

## 8. Riesgos heredados de dobackv2 (no copiar a ciegas)

- **Fórmula DRS de `StabilityProcessor.ts`** divide dos veces por `g` — dimensionalmente inconsistente. Usar la estándar `1 - |ay|/(SSF·g)`.
- **`ACCEL_SCALE_FACTOR=100`** de `thresholds.ts` es de otra capa (raw → m/s²). Training ya hace mg→m/s² con `0.00981`. **No copiar la constante 100** sin entender contexto.
- **`usciclo1..4` (células de carga)**: Training las descarta hoy. Sin ellas no hay LTR físico. Validar con TXT real si vienen con valores fiables.
- **`confidence` field overloaded**: en Training mezcla k3 sensor con confianza de detección. Separar en `sensorK3` y `detectionConfidence`.
- **`isDRSHigh / isLTRCritical / isLateralGForceHigh`**: hardcoded `False` en parser; rama `event_detector.py:162` es código muerto. Borrar o conectar.

---

## 9. Lo que necesito de Antonio / equipo para arrancar

1. **Un TXT real anonimizado del Doback Elite** — 1 sesión completa con GPS+ESTABILIDAD+ROTATIVO (CAN si hay).
2. **Acceso al sandbox de Webfleet de CMadrid** — account, username, password, apikey (sub-account de pruebas).
3. **Confirmar el repo del simulador** — `cosigein/doback-2.0-simulation-improvements` da 404. Si está privado o en otro git, mandar nombre correcto.
4. **Decisión `usciclo1..4`** — ¿el TXT real trae las 4 células con valores fiables? Si no, descartar LTR formalmente y escribirlo en `memory/`.

---

## 10. Demo Madrid 11/05 — alcance defendible

**Llega a la demo (objetivo realista)**:

- Ingesta Doback funcional contra TXT real anonimizado.
- Ingesta Webfleet en sandbox con `show_tracks` real, **circuit breaker visible** (apagar Webfleet en vivo y ver al sistema seguir).
- Pipeline 01→07 corriendo end-to-end con `v1.0.0.yaml` con valores **placeholder declarados como tales**.
- **Pantalla de simulador**: cambiá threshold en YAML, mostrá score nuevo del mismo Attempt.
- **ScoreAudit en UI**: alumno ve por qué tiene la nota, regla por regla.
- Inmutabilidad: intento de modificar Attempt cerrado → trigger PG lo rechaza en pantalla.

**No llega y conviene avisar**:

- LTR físico real (depende de validar `usciclo` en TXT real).
- Machine learning / shadow mode.
- Acta PDF firmada con SHA256.
- App iOS.

---

## 11. Resumen de una línea

Lo que hay hoy es **andamiaje sin pruebas**, no software comprobado; Webfleet — el 80% del input — **no existe en código**; recomendación: archivar el pipeline actual, activar Alembic, levantar `CriteriaVersion + RawSample + NormalizedSample + ScoreAudit`, construir las dos ingestas (Doback parser nuevo + Webfleet con circuit breaker) y siete pasos de pipeline desde cero, todo gobernado por un YAML que CMadrid pueda llenar en la reunión sin que nadie toque código.

---

## Apéndice A — Referencias verificadas en código

- Pipeline actual cableado: `app/services/pipeline/{sensor_parser,event_detector,scorer,pipeline}.py`.
- Llamadas reales: `app/blueprints/manager/routes.py:573-629`, `app/blueprints/sessions/services.py:43-101`.
- Modelos administrativos: `app/models/training.py`, `app/models/session.py:33` (Attempt), `app/models/vehicle.py:85` (VehicleConfiguration con cgHeight/trackWidth).
- Mock data UI: `app/blueprints/manager/routes.py:54,98,303` (CONVOCATORIAS, CANDIDATOS, AUDITORIAS).
- Decisión Webfleet: `memory/decision-webfleet-entra.md`.
- Roadmap viejo (con plan Webfleet detallado, no implementado): `roadmap.md` §6.
- Archivos vacíos confirmados: `app/services/{stability_processor,kpi_calculator,alert_service,map_matching}.py` (0 bytes), todas las fixtures `tests/fixtures/**/*.{txt,json}` (0 bytes).

## Apéndice B — Referencias verificadas en `cosigein/dobackv2`

- `backend/src/services/StabilityProcessor.ts` — calcula LTR/SSF/DRS/RSC con ventana de 10 muestras y mediana. Bug DRS dimensional confirmado.
- `backend/src/services/stability/MeasurementSanitizer.ts` — sanitizer con audit trail, perfiles `URBAN_TRANSPORT_LIMITS`, `LIGHT_VEHICLE_LIMITS`, `HEAVY_VEHICLE_LIMITS`.
- `backend/src/config/thresholds.ts` — SIF, severidad SI, GPS quality, K1=1.15, K4=1.1, H=1.3, MAX_VALID_FIRE_TRUCK=150 km/h, ACCMAG_MIN/MAX=980/1030 mg.
- `backend/src/utils/imuAxesMapping.ts` — `validateAxesCoherence()`, ISM330DHCX.

## Apéndice C — Referencias Webfleet

- [WEBFLEET.connect API documentation](https://portals.webfleet.com/s/article/WEBFLEET-connect-API-documentation?language=en_GB)
- [WEBFLEET.connect 1.56.0 Reference Guide (PDF)](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.56.0)
- [Accessing Webfleet OAuth APIs Reference Guide 1.2 (2023)](https://media.webfleet.com/fl_attachment/media/doc/documentations/accessing-webfleet-oauth-apis-1.2)
- [webfleet-connect Python lib (PyPI)](https://pypi.org/project/webfleet-connect/)
- [Webfleet developer resources](https://www.webfleet.com/en_us/webfleet/partners/integration/developer-resources/)
