# Roadmap Training — Lo que falta

> **Fuente:** `Training - Documentacion Completa.pdf` (254 p.).
> **Alcance:** SOLO el dominio Training (alumnos haciendo pruebas de conducción para oposición CMadrid). Todo lo de fleet genérico (KPIs, geofences, telemetría libre) se ignora o se descarta.
> **Última actualización:** 2026-04-28.

---

## 0. Resumen (3 frases)

El PDF describe un sistema de evaluación competitiva: el alumno se identifica por RFID, conduce una ruta, el sistema captura datos de Doback Elite + Webfleet, calcula nota, mantiene ranking diario, y al cierre formal de 3 pasos genera acta PDF firmada con decisiones APTO / NO_APTO. El Flask actual tiene piezas reutilizables (Session, GpsMeasurement, Event, User+roles, audit, uploads) pero **falta el dominio Training entero**: Convocatoria, Enrollment, Attempt como entidad de Training, ranking, cierre 3 pasos, RBAC con rol STUDENT/ALUMNO. El próximo sprint debe entregar el flujo end-to-end mínimo: identificar alumno → ingestar datos → score automático → ranking nocturno → cierre formal con acta.

---

## 1. Modelo de datos

### Convocatoria (PDF §2, §3.1) — ❌ falta
- [ ] **Convocatoria**
  - Estado actual: no existe.
  - Campos clave:
    - `id`, `organizationId` (FK), `name`
    - `routePrincipal` (string, ruta del desempate)
    - `plazas` (int, cupo fijo y público)
    - `umbralMin` (float 0-10), `pesosPorFamilia` (JSONB)
    - `criteriaVersion`, `normalizerVersion`, `detectorVersion` (string, pinned)
    - `openedAt`, `closedAt` (NULL hasta cierre)
    - `closureStatus` (enum: OPEN, PREVIEW, CLOSING, CLOSED, LOCKED)
    - `closureInitiatedBy` (FK User), `closureConfirmedBy` (FK User)
    - `finalRankingSnapshot` (JSONB), `acta` (bytea), `actaSignatureHash` (SHA256)
    - `reverseWindowUntil` (datetime, +24h tras cierre)
  - Relaciones: `has_many :enrollments`, `has_many :attempts` (vía enrollment).

### Enrollment (PDF §2) — ❌ falta
- [ ] **Enrollment**
  - Estado actual: no existe.
  - Campos: `id`, `convocatoriaId`, `studentId`, `routeId`, `status` (ACTIVE / COMPLETED / INVALIDATED), `attempts_count`.
  - Constraint: `unique(convocatoriaId, studentId)` — un alumno una sola vez por convocatoria.

### Attempt (= Session reconvertida) (PDF §2, §6) — ⚠️ parcial
- [ ] **Attempt**
  - Estado actual: existe `Session` en `app/models/session.py` con `trainingStatus` y `trainingMetadata`. Reusar y extender.
  - Campos a añadir:
    - `enrollmentId` (FK, requerido)
    - `convocatoriaId`, `studentId` (desnormalizados para queries de ranking)
    - `kioskCode`, `attemptNumber`
    - `scoreRaw`, `score` (float 0-10), `scoreBreakdown` (JSONB)
    - `scoreExplanation` (text, audit trail granular)
    - `dataQuality` (JSONB: gaps, missing events, confidenceScore)
    - `criteriaVersion_pinned`, `normalizerVersion_pinned`, `detectorVersion_pinned` (INMUTABLES post-creación)
    - `closedAt` (timestamp del freeze)
    - `invalidatedAt`, `invalidatedReason`
    - `auditLog` (JSONB array)
  - **INVARIANTE:** una vez `closedAt` se setea, `score` no cambia (DB trigger + service-layer guard).

### Event (PDF §6.2) — ⚠️ parcial
- [ ] **Event**
  - Estado actual: existe `app/models/event.py`.
  - Campos a añadir:
    - `attemptId` (FK)
    - `type` (enum: HARSH_BRAKING, SPEEDING, DEVIATION, ACCELERATION_LATERAL, HARSH_ACCELERATION)
    - `severity` (enum: LOW / MEDIUM / HIGH / CRITICAL)
    - `confidence` (float 0-1)
    - `source` (DOBACK_ELITE / WEBFLEET)
    - `penaltyPoints` (float)

### RawSample (PDF §2) — ⚠️ parcial
- [ ] **RawSample** (canonicalizar)
  - Estado actual: existen `GpsMeasurement`, `StabilityMeasurement`, `RotativoMeasurement`, `CanMeasurement` en `app/models/session.py`.
  - Decisión: o (a) consolidar en una tabla `RawSample` con `payload JSONB`, o (b) dejar 4 tablas y mapear conceptualmente. **Recomendación: dejar las 4** (tipado fuerte, queries más rápidas).
  - Añadir: `attemptId` (renombre de `sessionId`), `source` (DOBACK_ELITE / WEBFLEET), `data_freshness` (FRESH / STALE / MISSING).

### Ranking (PDF §3.1, §3.2) — ❌ falta
- [ ] **Ranking** (insert-only log)
  - Estado actual: no existe.
  - Campos: `id`, `convocatoriaId`, `attemptId`, `studentId`, `score` (snapshot), `rank` (int), `status` (PROVISIONAL / DEFINITIVE), `snapshotAt` (datetime, 6:00 AM), `createdAt`.
  - **INVARIANTE:** insert-only, sin UPDATE ni DELETE. Snapshot diario.

### AuditEvent (PDF §8.5) — ⚠️ parcial
- [ ] **AuditEvent**
  - Estado actual: existe `app/models/audit.py`.
  - Validar / extender:
    - `actor` (FK User), `action` (enum amplio: ATTEMPT_CREATED, SCORE_CALCULATED, ATTEMPT_CLOSED, CONVOCATORIA_CLOSED, RANKING_PUBLISHED, ENROLLMENT_CREATED, CLOSURE_INITIATED, CLOSURE_CONFIRMED, CLOSURE_REVERSED, GDPR_EXPORT, GDPR_FORGET).
    - `resource_type`, `resource_id`, `delta` (JSONB), `timestamp`, `ip_address`.
  - **INVARIANTE:** sin UPDATE ni DELETE.

### User / Roles (PDF §4, §5) — ⚠️ parcial
- [ ] **User**
  - Estado actual: enum `UserRole` con `ADMIN / MANAGER / OPERATOR / VIEWER` en `app/models/auth.py:9`.
  - Cambios requeridos:
    - Agregar `STUDENT` (alias `ALUMNO`) y `SUPER_ADMIN` al enum.
    - Campo `student_profile_id` opcional (si role = STUDENT).
    - Campo `managed_convocatorias` (JSONB array de IDs) para MANAGER scope.
    - `OPERATOR` y `VIEWER` se pueden mantener pero no aplican al dominio Training.

---

## 2. Endpoints API

### Auth & Setup
- [ ] `POST /auth/login` — ✅ existe (`app/blueprints/auth/routes.py:12`). Validar que acepta STUDENT.
- [ ] `POST /auth/logout` — ✅ existe.

### Convocatorias (ADMIN)
- [ ] `POST /admin/convocatorias` — ❌ falta. Body: `{name, plazas, routePrincipal, umbralMin, pesosPorFamilia, criteriaVersion, ...}`.
- [ ] `GET /admin/convocatorias` — ❌ falta. Filtros: `status`. Response: lista + stats.
- [ ] `GET /admin/convocatorias/:id` — ❌ falta. Detalle + matriz alumno×ruta + ranking actual.
- [ ] `PATCH /admin/convocatorias/:id` — ❌ falta. Solo `pesosPorFamilia` y `criteriaVersion` mientras `OPEN`. **Crea versión nueva**, attempts viejos quedan pinned a la versión vieja.

### Enrollments (ADMIN / MANAGER)
- [ ] `POST /admin/convocatorias/:cid/enrollments` — ❌ falta. Body: `{studentId, routeId}`.
- [ ] `GET /admin/convocatorias/:cid/enrollments` — ❌ falta.
- [ ] `DELETE /admin/convocatorias/:cid/enrollments/:eid` — ❌ falta. Solo si convocatoria `OPEN`.

### Attempts (STUDENT vía RFID + MANAGER)
- [ ] `POST /attempts` — ❌ falta. Identificación RFID. Body: `{kioskCode, rfidTag}`. Respuesta: `Attempt` con `status: ACTIVE`. Crea attempt si Enrollment existe y convocatoria OPEN.
- [ ] `POST /attempts/:id/close` — ❌ falta. Trigger automático: otro alumno pasa tarjeta o timeout 30 min sin movimiento. Freeze de score.
- [ ] `POST /attempts/:id/ingest` — ⚠️ parcial (existe `uploads/`). Body: `{source, samples, events_count, data_freshness}`. **Idempotencia obligatoria** por `(attemptId, source, timestamp)`.
- [ ] `GET /attempts/:id` — ⚠️ parcial (existe `GET /sessions/<id>`). STUDENT ve nota + eventos + explicación pedagógica, sin datos crudos. MANAGER ve todo.

### Student dashboard (STUDENT)
- [ ] `GET /student/dashboard` — ❌ falta. Response: `{attempts, meanScore, provisionalRank, isWithinCutoff}`.
- [ ] `POST /student/audit-request` — ❌ falta. Body: `{attemptId, reason}`. Crea solicitud de auditoría.
- [ ] `POST /student/gdpr-export` — ❌ falta. Genera ZIP, link expira en 7 días.

### Manager (MANAGER)
- [ ] `GET /manager/convocatorias/:id/matrix` — ❌ falta. Matriz alumno × ruta con notas.
- [ ] `GET /manager/audit-requests` — ❌ falta. Pendientes asignadas a este manager.
- [ ] `POST /manager/audit-requests/:id/resolve` — ❌ falta. Body: `{resolution, notes}`. **No modifica el score original** — solo genera registro de revisión.

### Ranking (cron + query pública dentro de la app)
- [ ] `POST /cron/daily-ranking` (interno) — ❌ falta. Cron 6:00 AM Madrid. Recalcula y persiste snapshot.
- [ ] `GET /convocatorias/:id/ranking` — ❌ falta. Snapshot más reciente.

### Cierre de Convocatoria — flujo de 3 pasos (PDF §9)
- [ ] `POST /admin/convocatorias/:id/close/preview` — ❌ falta. ADMIN. Calcula ranking simulado. Solo lectura, estado sigue OPEN.
- [ ] `POST /admin/convocatorias/:id/close/initiate` — ❌ falta. ADMIN #1. Body: `{confirmationText: nombreConvocatoria}`. Estado → CLOSING. Genera acta borrador.
- [ ] `POST /admin/convocatorias/:id/close/confirm` — ❌ falta. ADMIN #2 distinto + re-auth. Estado → CLOSED. Firma SHA256 + publica resultado.
  - **INVARIANTE:** `closureInitiatedBy != closureConfirmedBy` (DB constraint + app guard).
- [ ] `POST /admin/convocatorias/:id/close/abort` — ❌ falta. Cancela CLOSING (initiator o SUPER_ADMIN).
- [ ] `POST /admin/convocatorias/:id/close/reverse` — ❌ falta. SUPER_ADMIN, ventana 24h. Body: `{reason}` ≥50 chars. Genera amendment, no overwrite.
- [ ] **Cron CLOSED → LOCKED** cada 15 min — ❌ falta. Sin endpoint público.

### GDPR (SUPER_ADMIN)
- [ ] `POST /admin/gdpr/forget-request/:studentId` — ❌ falta. Anonimiza datos personales tras plazo legal.

---

## 3. Lógica de negocio (servicios + reglas firmes)

- [ ] **Cálculo de score por attempt** (PDF §6) — ⚠️ parcial. Existe lógica en `app/services/stability_processor.py` (revisar). Faltan: pesos por familia, score breakdown granular, audit trail explicativo.
- [ ] **Detector de eventos puro** (PDF §6.2) — ❌ falta. Función pura sin DB ni red, recibe samples normalizadas, devuelve eventos con `type`, `severity`, `confidence`. Versionable.
- [ ] **Normalizer de samples** (PDF §2) — ❌ falta. Alinear timestamps Doback/Webfleet, marcar gaps.
- [ ] **Ranking diario con cron** (PDF §3.2) — ❌ falta. Celery beat 6:00 AM TZ Europe/Madrid. Insert-only en `Ranking`.
- [ ] **Cierre 3 pasos + acta + reversa 24h** (PDF §9) — ❌ falta. PDF generation con WeasyPrint (ya en deps). Firma SHA256.
- [ ] **Idempotencia de ingest** (PDF §2) — ❌ falta. Dedup por `(attemptId, source, timestamp)`. Subir mismo archivo 2 veces ≠ samples duplicados.
- [ ] **Inmutabilidad de attempt cerrado** (PDF §5.2, §12.3) — ❌ falta. Si `closedAt != NULL`, ningún UPDATE de `score` pasa. Trigger DB + guard en service.
- [ ] **Versionado pinned** (PDF §12.4) — ❌ falta. Cada attempt captura `criteriaVersion / normalizerVersion / detectorVersion` activos al crearse, y NO los actualiza nunca. Cambios futuros no afectan attempts viejos.
- [ ] **Redundancia Doback ↔ Webfleet** (PDF §12.1) — ⚠️ parcial. Si Webfleet cae, Doback Elite sigue. Marcar `data_freshness: STALE` y seguir computando.
- [ ] **Double admin validation en cierre** (PDF §9.1) — ❌ falta. DB constraint + app guard.
- [ ] **Audit trail inmutable** (PDF §8.5) — ⚠️ parcial. Insert-only. Cubrir todas las acciones críticas listadas en §1 AuditEvent.
- [ ] **Clasificación de attempts incompletos** (PDF §6.3) — ❌ falta. Función pura `classifyIncomplete(attempt, metrics)` que devuelve `ABORTED_TECHNICAL / ABANDONED / INTERRUPTED_BY_OTHER_CARD`.
- [ ] **Cascada de desempate del ranking** (PDF §3.1) — ❌ falta. Implementar 4 criterios: nota en ruta principal → menor tasa de data_quality LOW → mejor nota familia "estabilidad" → sorteo determinístico (SHA256 con semilla).

---

## 4. UI / Templates

### Login y autenticación
- [ ] Login — ✅ existe (`app/blueprints/auth/templates/auth/login.html`).

### Dashboard ALUMNO (STUDENT)
- [ ] `/student/dashboard` — ❌ falta. Historial de intentos, nota media, puesto provisional, indicador "dentro/fuera del corte", botones de auditoría y export GDPR.

### Dashboard MANAGER
- [ ] `/manager/convocatorias/:id/matrix` — ❌ falta. Tabla alumno × ruta con nota y estado por celda.
- [ ] `/manager/audit-requests` — ❌ falta. Lista de auditorías pendientes y resueltas.
- [ ] `/manager/audit-requests/:id` — ❌ falta. Detalle + form de resolución.

### Detalle de Attempt
- [ ] `/attempts/:id/detail` — ⚠️ parcial. Existe vista de session detail. Extender con:
  - Vista STUDENT: nota, eventos con explicación, sin datos crudos.
  - Vista MANAGER: además mapa, eventos raw, gaps, score audit granular.

### Cierre de convocatoria (ADMIN)
- [ ] `/admin/convocatorias/:id/close/preview` — ❌ falta. Tabla del ranking simulado, advertencias.
- [ ] `/admin/convocatorias/:id/close/initiate` — ❌ falta. Form con `confirmationText` = nombre convocatoria.
- [ ] `/admin/convocatorias/:id/close/confirm` — ❌ falta. Form con re-auth + confirmación.
- [ ] `/admin/convocatorias/:id/acta` — ❌ falta. Descarga acta PDF.

### Ranking público (dentro de la app)
- [ ] `/convocatorias/:id/ranking` — ❌ falta. Tabla ordenada con etiqueta `PROVISIONAL` o `DEFINITIVO`.

### Admin de convocatorias
- [ ] `/admin/convocatorias` (lista) — ❌ falta.
- [ ] `/admin/convocatorias/new` (crear) — ❌ falta.
- [ ] `/admin/convocatorias/:id/edit` — ❌ falta. Editar pesos / criteria solo si OPEN.
- [ ] `/admin/convocatorias/:id/enrollments` — ❌ falta. Lista de alumnos inscritos + alta.

---

## 5. RBAC / roles

| Rol | Endpoints permitidos | Resumen |
|---|---|---|
| **STUDENT / ALUMNO** | `POST /attempts` (RFID), `GET /attempts/:id` (propio), `GET /student/dashboard`, `POST /student/audit-request`, `POST /student/gdpr-export` | Lee solo lo propio, solicita auditoría, exporta sus datos |
| **MANAGER** | Lecturas de convocatorias suyas, matriz, attempts (todos), ranking, audit-requests | Supervisa, resuelve auditorías, **NO cierra** convocatorias |
| **ADMIN** | Todo lo de MANAGER + crear/editar convocatoria, enrollments, los 3 pasos del cierre, abort | Gestión operativa completa |
| **SUPER_ADMIN** | Todo lo de ADMIN + `close/reverse` (24h), `gdpr/forget-request`, cambios de sistema | Reversa post-cierre y GDPR |
| ~~OPERATOR~~ ~~VIEWER~~ | — | Roles legacy de la app vieja, no aplican a Training |

### Cambios concretos
- [ ] Extender `UserRole` enum en `app/models/auth.py:9` con `STUDENT` y `SUPER_ADMIN`.
- [ ] Extender `require_role` en `app/utils/decorators.py` para soportar:
  - Filtrado por `managed_convocatorias` (MANAGER solo ve sus convocatorias).
  - STUDENT solo accede a recursos propios (chequeo de ownership).
- [ ] Aplicar decorador en TODOS los endpoints (ver el roadmap RBAC anterior, sigue siendo válido).

---

## 6. Infraestructura local

### Postgres
- [ ] Migraciones nuevas para: Convocatoria, Enrollment, Attempt extends Session, Event extends, Ranking, AuditEvent extends.
- [ ] Extensions: `uuid-ossp` (ya en uso vía `gen_random_uuid()`). `pg_trgm` opcional para búsqueda de alumnos.
- [ ] Índices clave:
  - `Attempt(enrollmentId)`, `Attempt(convocatoriaId, score)`, `Attempt(closedAt)` para freeze checks.
  - `Enrollment(convocatoriaId, studentId)` — unique.
  - `Ranking(convocatoriaId, snapshotAt)`.
  - `AuditEvent(resourceType, resourceId, timestamp)`.
- [ ] Triggers / constraints:
  - Trigger `attempt_immutable_after_close` — rechaza UPDATE de `score` si `closedAt IS NOT NULL`.
  - CHECK `closureInitiatedBy != closureConfirmedBy`.

### Redis
- [ ] Cache de ranking actual por `convocatoriaId` (invalidar al insert de snapshot).
- [ ] Cola para worker de ingesta (Celery).

### Celery / Cron
- [ ] Beat schedule:
  - `daily_ranking` @ 06:00 AM Europe/Madrid.
  - `lock_closed_convocatorias` cada 15 min (CLOSED → LOCKED tras ventana 24h).
  - `cleanup_expired_gdpr_exports` diario.
- [ ] Workers:
  - `ingest_worker` — procesa samples Doback/Webfleet, detecta eventos, computa score provisional.
  - `pdf_worker` — genera acta PDF al `close/initiate` y refirma al `close/confirm`.

### Storage
- [ ] Acta PDF — Postgres `bytea` (V1, simple) o S3 (V2). Retención: indefinida.
- [ ] GDPR exports — filesystem `./storage/gdpr/`, expira 7 días.
- [ ] Raw samples — Postgres, retención 12 meses.

---

## 7. Lo que SE QUEDA del Flask actual (mapeo)

| Flask actual | Mapeo a Training | Acción |
|---|---|---|
| `app/blueprints/auth/` | Auth (login/logout) | Reusar. Validar STUDENT login. |
| `app/blueprints/sessions/` | Lista y detalle de Attempt | Reusar. Renombrar conceptualmente, NO el path inicialmente. |
| `app/blueprints/uploads/` | Ingesta de archivos sensor | Reusar. Refactor con dedup + `attemptId` + idempotencia. |
| `app/models/session.Session` | Attempt | Extender campos (ver §1). |
| `app/models/session.GpsMeasurement` | RawSample (GPS) | Reusar. Renombrar `sessionId` → `attemptId`. Añadir `source`, `data_freshness`. |
| `app/models/session.StabilityMeasurement` | RawSample (estabilidad) | Igual. |
| `app/models/session.RotativoMeasurement` | RawSample (rotativo) | Igual. |
| `app/models/event.py` | Event | Extender (ver §1). |
| `app/models/auth.User, Organization` | User, Org | Extender User con STUDENT, SUPER_ADMIN. |
| `app/models/audit.py` | AuditEvent | Extender enum de actions. |
| `app/services/stability_processor.py` (si existe) | Scoring | Reusar como base. Sacarle estado, hacerla función pura. |
| `app/utils/decorators.py` (`require_role`, `require_org`) | RBAC | Extender (ver §5). |
| `app/middleware/jwt_handlers.py` | JWT loaders con redirect HTML | ✅ ya hecho. |
| `app/middleware/audit.py` | Audit context | Reusar. |
| `import_data.py` | Útil para seed dev (datos reales del Doback) | Mantener como herramienta de desarrollo. |

---

## 8. Lo que SE TIRA del Flask actual (out of Training)

| Flask actual | Razón | Acción |
|---|---|---|
| `app/blueprints/geofences/` | Generic fleet, no Training. | Borrar blueprint + modelo `app/models/geofence.py` + templates + `seed_geofences.py`. |
| `app/blueprints/telemetry/` | Vista live de fleet genérico. | Borrar. La ingesta de Training va por `uploads/` o un endpoint dedicado nuevo. |
| `app/blueprints/kpis/` | Fleet KPIs (combustible, idle, etc). | Borrar el endpoint `dashboard_executive` y el modelo `app/models/kpi.py`. El "dashboard" del MANAGER en Training es la matriz, no esto. |
| `app/blueprints/reports/` | Reportes genéricos (no acta). | Borrar. La única salida tipo "reporte" en Training es el acta PDF. |
| `app/blueprints/vehicles/` | Gestión de flota genérica. | **Mantener parcialmente** si Training necesita asociar `Doback Elite ID` a un Vehicle (caso del PDF §2). Recortar a lo mínimo. |
| `app/models/geofence.py` | Geofences. | Drop. |
| `app/models/kpi.py` | KPIs flota. | Drop. |
| `app/models/report.py` | Reports flota. | Drop. |
| `app/models/notifications.py` | Notificaciones genéricas. | Mantener si va a usarse para auditorías; sino drop. |
| `app/models/upload.py` | Upload logs (ingesta). | **Mantener** — sirve para idempotencia. Renombrar campos si hace falta. |
| `app/blueprints/admin/` | Admin actual (orgs, users). | Mantener pero recortar a lo mínimo. El admin de Training va a ser nuevo. |
| `app/blueprints/system/` | Settings generales. | Mantener para `Configuración` del usuario. |

---

## 9. Orden sugerido de ataque (top 12 tareas)

> Dependencias claras. Hacer en orden, no saltearse pasos. Estimaciones honestas (junior) — ajustar al equipo real.

1. [ ] **Extender User model + RBAC** — Agregar `STUDENT`, `SUPER_ADMIN` al enum. Extender `require_role` con ownership y `managed_convocatorias`. Re-seed admins/manager + crear un STUDENT en `setup_db.py`. **~4h.**
2. [ ] **Limpiar el Flask actual** — Borrar blueprints/modelos del §8. Migración Alembic con `drop_table`. Liberar mental load del proyecto. **~3h.**
3. [ ] **Modelos Convocatoria + Enrollment** — Crear, generar migración, agregar al `setup_db.py`. **~4h.**
4. [ ] **Refactor Session → Attempt** — Renombrar `sessionId → attemptId` en GPS/Stability/Rotativo/CAN. Agregar `enrollmentId`, `convocatoriaId`, `studentId`, `closedAt`, versiones pinned, scoreBreakdown. Migración + actualizar `import_data.py`. **~6h.**
5. [ ] **Modelo Event extendido + Ranking + AuditEvent extendido** — Crear/extender, migrar. **~4h.**
6. [ ] **CRUD básico de Convocatoria + Enrollment (admin)** — Endpoints + templates + RBAC. **~8h.**
7. [ ] **POST /attempts (RFID identify) + POST /attempts/:id/close** — Lookup por kioskCode + rfidTag, crear Attempt, freeze. **~6h.**
8. [ ] **Ingesta + detector + scoring** — `POST /attempts/:id/ingest` con dedup, función pura `detectEvents(samples)`, función pura `computeScore(events, criteria)`. **~14h.** El más gordo.
9. [ ] **Cron daily-ranking + lockClosedConvocatorias** — Celery beat + insert-only en `Ranking`. **~4h.**
10. [ ] **Cierre 3 pasos + acta PDF + reversa 24h** — Endpoints + templates + WeasyPrint + SHA256. **~10h.**
11. [ ] **Dashboard STUDENT + Matriz MANAGER** — Templates + queries. **~8h.**
12. [ ] **Auditoría + GDPR export** — Endpoints + flujo. **~6h.**

**Subtotal: ~77 horas.** Para 4 personas en 9 días laborables = factible si se paraleliza bien y no hay sorpresas. Reservar 20% buffer (~92h reales).

---

## 10. Lo que NO entra en este roadmap (Fase 2)

- [ ] **Notificaciones email/SMS** (PDF §11) — Templates + SendGrid + Twilio. Útil pero no demostrable en kickoff.
- [ ] **Recurso administrativo formal post-LOCKED** (PDF §10.3) — `OutcomeAmendment` con flujo legal completo. Demo no lo necesita.
- [ ] **Hardware Doback Elite (instalación, pairing avanzado)** — Responsabilidad de CMadrid + Bridgestone. No nuestro código.
- [ ] **Webfleet sandbox real (tilde encoding, quota Redis, circuit breaker)** — Antonio lo entrega como package; nosotros consumimos mock hasta el día 7.
- [ ] **Telemetría live para MANAGER** — Vista en vivo del camión circulando. Útil pero fuera del MVP.
- [ ] **Knowledge base, Observability, AI/FleetMind** — No aplican a Training.
- [ ] **GDPR forget-request implementation completa** — Anonimización post-plazo legal (5 años). Hasta confirmación con DPO.
- [ ] **Multi-org real** — V1 asume una sola organización (CMadrid). Multi-tenancy completo se valida en V2.

---

## Apéndice A — Patrones invariantes a respetar (resumen del PDF)

> Si tu código rompe alguno, el PR no entra. No hay excepciones.

1. **Idempotencia de ingest** — Mismo archivo 2 veces ≠ duplicados. Hash SHA256 + UNIQUE.
2. **Reproducibilidad** — Comando `replay <attemptId>` rerun normalize+detect+score con versiones pinned. Si difiere = bug.
3. **Inmutabilidad del Attempt cerrado** — `frozen_at != null` ⇒ ningún UPDATE pasa.
4. **Versionado pinned** — Cada attempt cierra con normalizer, detector, criteria versions. Cambios futuros NO afectan.
5. **Source declarado + confianza ortogonal** — Cada Event con `source ∈ {DOBACK_ELITE, WEBFLEET}` y `confidence` independiente.
6. **Inmutabilidad del ranking final** — Si convocatoria CLOSED y snapshot `is_final`, no se reescribe (excepto reversa).
7. **Decisión solo al cierre** — Attempt NO tiene `decision`. APTO/NO_APTO solo en `CandidateOutcome` post-cierre.
8. **Cierre con doble validación + acta** — `closing_admin_id != confirming_admin_id`, preview obligatorio, acta PDF con SHA256.
9. **Criteria_version pinned al ABRIR** — Al crear el Attempt, captura version activa. Activar nueva version NO afecta attempts ya creados.

---

**Cuando termines un bloque, marcá el checkbox correspondiente.** Si descubrís que un requisito del PDF no encaja con el modelo dato actual, abrí un sub-issue y notálo en este archivo, **no improvises**.
