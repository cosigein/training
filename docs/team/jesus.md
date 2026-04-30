# Jesús — Tu trabajo en Training

## Sprint de 14 días · Demo CMadrid: lunes 11 de mayo de 2026

---

## ⚡ TLDR — esto es lo que tenés mañana en 5 líneas

1. **Sos backend lead.** Construís api + worker + packages internos (domain, normalization, detection, scoring, ranking) + schema Prisma + auth.
2. **Llegá al kickoff con Node 20 LTS + Docker Desktop instalados** y la invite del repo aceptada. **NO clones el repo, NO corras `pnpm install` antes.** Si te falta algo, lo instalamos en los primeros 15 min del kickoff.
3. **Martes 28/04 09:00:** kickoff de 1h (lectura silenciosa + Q&A). Después (10:00-13:00) scaffolding compartido entre los 4. Tu primer PR: `chore/setup-jesus`.
4. **Tu primer hito serio (miércoles 29/04):** health endpoints + schema base + migración `20260428_HHMM_init_base_models` aplicada. Detalle en §0.10.
5. **Lectura silenciosa durante el kickoff** (la dirige Antonio, ~30 min): leé glosario del paper + §3 (9 invariantes) + §5 (modelo de datos). El resto del paper se consulta cuando dudes durante el sprint.

---

| | |
|---|---|
| **Tu rol** | Backend completo (api + worker + packages internos + schema Prisma) |
| **Tu jefe técnico** | Antonio (director técnico) |
| **Tus pares** | Alejandro (frontend) · Joel (simulador + QA) |
| **Tu issue principal** | [#3 — Backend completo](https://github.com/cosigein/training/issues/3) |
| **Issues compartidos** | [#1 — Scaffolding día 1](https://github.com/cosigein/training/issues/1) · [#6 — Convenciones del sprint](https://github.com/cosigein/training/issues/6) |
| **Documento maestro** | `docs/PAPER-MAESTRO.md` (referencia completa cuando dudes) |
| **Convenciones del repo** | [`OWNERS.md`](../../OWNERS.md) y [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |

---

## Tabla de contenidos

- [0. Cómo arrancás el día 1 (setup operativo)](#0-cómo-arrancás-el-día-1-setup-operativo)
- [1. Qué construimos (5 minutos)](#1-qué-construimos-5-minutos)
- [2. Tu territorio de código](#2-tu-territorio-de-código)
- [3. Las 9 invariantes (regla de oro)](#3-las-9-invariantes-regla-de-oro)
- [4. Tu calendario día por día](#4-tu-calendario-día-por-día)
- [5. Schema Prisma — modelos críticos](#5-schema-prisma--modelos-críticos)
- [6. Endpoints API — catálogo](#6-endpoints-api--catálogo)
- [7. Lógica del cierre (3 pasos)](#7-lógica-del-cierre-3-pasos)
- [8. Patrones de implementación de referencia](#8-patrones-de-implementación-de-referencia)
- [9. Coordinación con el equipo](#9-coordinación-con-el-equipo)
- [10. Glosario y siglas](#10-glosario-y-siglas)

---

## Glosario rápido (lectura previa de 1 minuto)

| Término | Significado |
|---|---|
| **Paper Maestro v6** | Sexta iteración del paper técnico de Training. La "v6" hace referencia a la versión del paper, no del producto. |
| **Doback Elite** | Dispositivo físico (sensor + GPS) instalado en cada camión. Producto propio. |
| **Webfleet** | Plataforma externa de Bridgestone que CMadrid tiene contratada. Antonio escribe el package que la consume (`packages/ingestion/webfleet/`). |
| **D1, D2, ..., D25** | Decisiones firmes del paper maestro. Las 25 están listadas en `docs/PAPER-MAESTRO.md` con su justificación. Buscá `### D` en el paper para encontrarlas. No se reabren durante el sprint. |
| **F1, F2, ..., F6** | Items de Fase 2 (post-demo). En el paper §17. No se construyen en el sprint. |
| **convocatoria** | Proceso de oposición concreto con plazas, fecha de cierre, candidatos inscritos. |
| **enrollment** | Inscripción de un Student a UNA convocatoria. Un humano puede tener varias enrollments (varias convocatorias). |
| **attempt** | Un intento de evaluación = un alumno + una ruta + una sesión. Tiene una nota 0-10. |

> **Lo que vas a leer del paper durante el silent reading del kickoff (martes 09:00, lo dirige Antonio):** el glosario del paper (§0) + las 9 invariantes (§3) + el §5 (modelo de datos). 30 minutos guiados. **No hace falta que leas nada antes.** El paper es referencia para consultar durante el sprint, no lectura previa obligatoria.

---

## Coordinación temporal con Antonio (cuándo recibís qué)

| Cuándo | Qué te entrega Antonio |
|---|---|
| **Día 3 (jueves 30/04)** | Versión 0 (mock estable) de `@training/ingestion-webfleet` con el shape congelado: `{ events_count, raw_samples_count, data_freshness, fetched_at }`. Te alcanza para empezar `apps/worker/src/jobs/webfleetSync.ts`. |
| **Día 7 (lunes 04/05)** | Versión real de `@training/ingestion-webfleet` operando contra el sandbox de CMadrid (con tilde resuelto, quota Redis en marcha, circuit breaker activo). |

**Si Antonio se retrasa con Webfleet:** el `apps/worker/src/jobs/webfleetSync.ts` y el `processAttempt` se desarrollan contra el mock del día 3. Tu cierre y ranking NO bloquean por Webfleet — el `data_freshness: 'missing'` está contemplado en la lógica de scoring.

---

# 0. Cómo arrancás el día 1 (setup operativo)

> **Importante (estado real al 27/04/2026):** este repo (`cosigein/training`) está recién creado y solo contiene los documentos del proyecto. **No hay código todavía.** El scaffolding inicial (package.json, docker-compose, estructura de carpetas, dependencias instaladas) lo levantamos **el martes 28/04 durante el kickoff con todo el equipo en pantalla compartida**. Las versiones, estructura de carpetas y `.env.example` que se describen en este §0 son la **propuesta técnica de partida** que vamos a materializar ese día — no comandos para correr la noche del lunes.
>
> **Lo que sí conviene traer al kickoff (martes 28/04 09:00):**
>
> - Node 20 LTS instalado en tu laptop (`node --version` debe imprimir v20.x.x)
> - Docker Desktop instalado y arrancando bien
> - Git configurado con tu usuario de GitHub
> - Acceso al repo `cosigein/training` aceptado (Antonio te invita)
>
> Si te falta alguna, **no hay drama** — los instalamos en los primeros 15 min del kickoff. El plan de la mañana absorbe esto sin problema.

## 0.1 Versiones exactas de dependencias (propuesta a confirmar el día 1)

```
   Node           20.x LTS
   PostgreSQL     17 (con extensiones: pg_trgm, citext)
                  No usamos PostGIS ni pgvector en V1.
   Redis          7
   Docker         última estable (para postgres + redis locales)

   npm packages clave:
     prisma          ^6.0
     @prisma/client  ^6.0
     express         ^4.19
     bullmq          ^5.0
     ioredis         ^5.0
     winston         ^3.11
     zod             ^4.0
     bcrypt          ^5.1
     csrf-csrf       ^3.0
     puppeteer       ^22.0    (para acta PDF)
     jest            ^29.0    (tests backend)
     ts-node-dev     ^2.0     (dev server)
     typescript      ^5.6
```

## 0.2 Estructura de carpetas propuesta para `apps/api/src/`

> Esta estructura es la **propuesta**, no el estado actual. La consolidamos contigo el día 1 (puede haber tweaks según veamos package.json y dependencias). No crees archivos por adelantado.

```
apps/api/src/
├── index.ts                   ← entrypoint Express
├── app.ts                     ← configuración Express (middlewares globales)
├── routes/                    ← un archivo por dominio
│   ├── auth.routes.ts
│   ├── attempts.routes.ts
│   ├── convocatorias.routes.ts
│   ├── doback.routes.ts
│   ├── matrix.routes.ts
│   ├── students.routes.ts
│   ├── routes.routes.ts       ← (sí, ese nombre — "rutas" en sentido de itinerarios)
│   ├── rfid.routes.ts
│   ├── kioskos.routes.ts
│   ├── scoring.routes.ts
│   ├── audit-requests.routes.ts
│   ├── gdpr.routes.ts
│   ├── admin.routes.ts
│   └── health.routes.ts
├── middleware/
│   ├── authenticate.ts        ← verifica JWT, popula req.user
│   ├── requireOrg.ts          ← popula req.orgId desde JWT
│   ├── requireRole.ts         ← rol mínimo (factory)
│   ├── requireSuperAdmin.ts
│   ├── csrf.ts
│   ├── audit.ts               ← agrega correlation_id
│   ├── errorHandler.ts        ← último middleware, captura errores
│   └── rateLimit.ts
├── services/                  ← orquestación (llaman a packages)
│   ├── attempt.service.ts
│   ├── convocatoria.service.ts
│   ├── ranking.service.ts     ← consume packages/ranking
│   ├── scoring.service.ts     ← consume packages/scoring
│   ├── close.service.ts       ← orquesta los 3 pasos del cierre
│   └── ...
├── errors/
│   ├── AppError.ts            ← clase base
│   ├── ValidationError.ts
│   ├── NotFoundError.ts
│   ├── ConflictError.ts       ← 409 (cierre concurrente, etc.)
│   ├── ForbiddenError.ts
│   └── index.ts
├── lib/
│   ├── logger.ts              ← winston configurado
│   ├── prisma.ts              ← cliente prisma
│   ├── redis.ts               ← cliente redis
│   ├── auditLog.ts            ← helper para escribir AuditLog
│   └── tz.ts                  ← helpers Europe/Madrid
└── types/
    └── express.d.ts           ← extensión de req.user, req.orgId
```

## 0.3 Variables de entorno — propuesta de `.env.example`

> Esta es la lista de variables que vamos a necesitar. Algunas las generamos el día 1 (JWT_SECRET, CSRF_SECRET), otras te las pasa Antonio (WEBFLEET_*). El archivo `.env.example` final lo commiteamos juntos durante el kickoff — no a ciegas la noche anterior.

```bash
# Database
DATABASE_URL="postgresql://training:training@localhost:5434/training"

# Redis
REDIS_URL="redis://localhost:6379"

# Auth — generamos con `openssl rand -base64 32` el día 1
JWT_SECRET=""                            # rellenar el día 1
JWT_ACCESS_TTL_SECONDS=900               # 15 min
JWT_REFRESH_TTL_SECONDS=2592000          # 30 días
CSRF_SECRET=""                           # rellenar el día 1
BCRYPT_ROUNDS=12

# Webfleet — Antonio te los pasa cuando estén disponibles
WEBFLEET_BASE_URL="https://csv.webfleet.com/extern"
WEBFLEET_ACCOUNT=""
WEBFLEET_USERNAME=""                     # cuidado encoding UTF-8 con tildes
WEBFLEET_PASSWORD=""
WEBFLEET_APIKEY=""

# Server
PORT=9998
NODE_ENV=development
LOG_LEVEL=debug

# Storage del acta PDF (V1: filesystem local; V2: S3/MinIO)
ACTA_STORAGE_PATH="./storage/actas"
ACTA_STORAGE_BACKEND="local"   # "local" | "s3"

# Ranking cron
RANKING_CRON_TZ="Europe/Madrid"
RANKING_CRON_PATTERN="0 6 * * *"

# GDPR
GDPR_EXPORT_TTL_DAYS=7
GDPR_RETENTION_RAW_SAMPLES_MONTHS=12

# Org defaults (V1: una sola org)
DEFAULT_ORG_ID="cmadrid"
```

## 0.4 Setup local — qué pasa el día 1

> **No corras estos pasos antes del martes.** El día 1, durante el kickoff con todo el equipo, levantamos el scaffolding inicial juntos. La secuencia abajo describe qué pasos haremos — para que llegues con contexto, no para que los ejecutes solo.

```bash
# Lo que vamos a hacer juntos el martes 28/04 por la mañana:

# 1. Clonar el repo (este, cosigein/training)
git clone https://github.com/cosigein/training.git
cd training

# 2. Decidir gestor de paquetes (npm vs pnpm) y workspaces
#    Probable decisión: pnpm + workspaces para monorepo apps/ + packages/

# 3. Crear package.json raíz, apps/api/package.json, apps/web/package.json,
#    y packages/* mínimos. Configurar TypeScript, ESLint, Prettier compartidos.

# 4. docker-compose.dev.yml con postgres:17 y redis:7 (puertos 5434 y 6379).

# 5. Inicializar Prisma con el schema base, primera migración "init".

# 6. Health-check endpoint /health/deep que verifique DB + Redis.

# 7. Verificar que `pnpm dev` levanta api + worker simultáneamente.

# 8. Cada uno crea rama `chore/setup-jesus` y mergea su primer PR
#    (puede ser solo añadir su archivo en docs/onboarding/jesus.md).
#    Esto valida el flujo de PR/review del equipo.
```

> **Por qué juntos:** si cada uno corre su propio `npm install` con versiones distintas o configuraciones distintas de TypeScript, el día 2 ya tenemos divergencia. Hacerlo en pantalla compartida lleva 2-3 horas y nos ahorra semanas de "en mi máquina funciona".

## 0.5 Convenciones de testing

```
   Tests UNITARIOS (jest):
     Ubicación:  packages/<package>/tests/*.test.ts
                 apps/api/src/services/*.test.ts (al lado del archivo)
     Tipo:       puros, sin DB ni red.
     Para:       packages/normalization, detection, scoring, ranking
                 services con mocks de prisma.

   Tests INTEGRACIÓN (jest + testcontainers):
     Ubicación:  apps/api/tests/integration/
     Tipo:       contra Postgres y Redis reales (testcontainers).
     Para:       endpoints HTTP con DB real, transacciones,
                 idempotencia, constraints.

   Tests E2E (Playwright):
     Joel los hace.
     Ubicación:  e2e/
```

**Regla:** los packages puros tienen 100% de tests determinísticos. Los servicios HTTP, integración. Joel cubre E2E.

## 0.6 Convenciones de error handling

Toda respuesta de error sigue este shape:

```typescript
// errors/AppError.ts
export class AppError extends Error {
  constructor(
    public statusCode: number,
    public code: string,           // ej: "VALIDATION_FAILED", "CLOSE_CONCURRENT_RACE"
    public message: string,
    public details?: unknown
  ) { super(message); }
}

// Response shape (errorHandler.ts):
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "<mensaje legible>",
    "details": { ... }            // opcional: lista de errores Zod, etc.
  },
  "correlation_id": "<uuid>"
}
```

**Códigos HTTP estandarizados:**

```
   400  bad request (Zod failed, malformed body)
   401  not authenticated
   403  authenticated but insufficient role
   404  resource not found
   409  conflict (race condition, ya existe, attempt frozen, etc.)
   422  semantic validation failed
   429  rate limited
   500  unexpected server error (loguea stack trace)
```

## 0.7 Logging

```typescript
// lib/logger.ts — winston con formato JSON estructurado
logger.info('attempt.closed', {
  attempt_id,
  enrollment_id,
  score,
  data_quality,
  correlation_id: req.correlationId,
});
```

**Niveles:**
```
   error  — errores no controlados, alarmar
   warn   — algo inesperado pero recuperable
   info   — eventos de negocio (attempt cerrado, ranking calculado, etc.)
   debug  — solo dev, detalles de flujo
```

**Regla firme:** `console.log` está prohibido en producción. CI lo bloquea.

## 0.8 Convenciones de naming en el código

```
   Archivos:           kebab-case  (audit-requests.routes.ts)
   Clases:             PascalCase  (AppError, AuditLogService)
   Funciones/vars:     camelCase   (computeRanking, attemptId)
   Constantes:         SCREAMING_SNAKE_CASE
   DB columns/tables:  snake_case  (enrollment_id, ranking_snapshot)
   Enums:              SCREAMING_SNAKE_CASE values, PascalCase nombre

   Spanish vs English en código:
     - Modelos de dominio: nombre en español si es término legal/contractual
       (Convocatoria, Enrollment). Attempt en inglés es decisión deliberada
       (más conciso, lo usás un millón de veces).
     - Tipos técnicos: en inglés (RankingInput, ValidationError)
     - Comentarios: español si aplica al dominio, inglés si es técnico
```

## 0.9 Linting y formatting

```
   ESLint config compartida en raíz: eslint.config.js
     - @typescript-eslint/recommended
     - prefer-const, no-unused-vars (level error)
     - no-console (level error en producción)
   Prettier compartido: .prettierrc
     - 2 espacios
     - single quotes
     - semicolons
     - trailing comma all
     - 100 chars max line
   Husky pre-commit: lint-staged ejecuta eslint + prettier en cambios.
```

## 0.10 Tu primer hito serio (miércoles 29/04 — DÍA 2)

Una vez que el setup del DÍA 1 deje `pnpm dev` (o `npm run dev`) levantando api+worker:

```
   1. Schema Prisma con los modelos básicos (User, Organization)
   2. Migración inicial aplicada localmente
   3. Endpoint GET /health funcionando (200 OK + version del package)
   4. Endpoint GET /health/deep que verifica DB + Redis
   5. Test de integración: GET /health → 200
   6. PR mergeado a main, CI verde
```

Si lo tenés el miércoles a mediodía, vamos bien.

---

# 1. Qué construimos (5 minutos)

**Training** es un sistema **automático de evaluación competitiva** de candidatos a conductor de camión de bombero para CMadrid. Es una **oposición pública**: 200+ candidatos compiten por un nº fijo de plazas. El sistema:

1. Captura datos del **dispositivo Doback Elite** (sensor del camión) y de **Webfleet** (plataforma externa).
2. Calcula una **nota 0-10** por cada intento ("attempt").
3. Mantiene un **ranking diario** (cron 6:00 AM Madrid).
4. Al cierre de la convocatoria emite la **decisión APTO / NO_APTO** según ranking final + plazas.

**El sistema NO emite "apto/no apto" por intento — solo nota.** La decisión final es competitiva, no por umbral absoluto.

```
   El alumno conduce → el sensor captura → el sistema mide y
   pone una NOTA → el ranking se actualiza diariamente → al
   cierre de la convocatoria se emiten APTO/NO_APTO según puesto.

   Las notas son INMUTABLES.
   El ranking es PROVISIONAL hasta el cierre.
   Tras el cierre + 24h queda LOCKED de forma absoluta.
```

---

# 2. Tu territorio de código

```
training/
├── apps/
│   ├── api/                    ← TU CÓDIGO — Express, ENDPOINTS REST
│   │   ├── src/
│   │   │   ├── routes/         ← un router por dominio
│   │   │   ├── middleware/     ← auth, requireOrg, requireRole, csrf, audit
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   └── worker/                 ← TU CÓDIGO — BullMQ jobs
│       ├── src/
│       │   ├── jobs/
│       │   │   ├── ingest.ts
│       │   │   ├── webfleetSync.ts        (orquesta el package de Antonio)
│       │   │   ├── pdfGenerate.ts
│       │   │   ├── rankingCron.ts         (6:00 AM Madrid)
│       │   │   └── lockClosedConvocatorias.ts (cron 15min CLOSED→LOCKED)
│       │   └── index.ts
│       └── package.json
│
├── packages/                   ← TODA LA LÓGICA AQUÍ
│   ├── domain/                 ← TU CÓDIGO — tipos puros (Attempt, Sample, Event, ...)
│   ├── ingestion/
│   │   ├── parser/             ← TU CÓDIGO — parser archivos del sensor
│   │   └── webfleet/           ← Antonio (NO TOCAR)
│   ├── normalization/          ← TU CÓDIGO — saneamiento (PURO, sin DB)
│   ├── detection/              ← TU CÓDIGO — detector eventos (PURO, sin DB)
│   ├── scoring/                ← TU CÓDIGO — motor scoring (PURO, sin DB)
│   ├── ranking/                ← TU CÓDIGO — motor ranking (PURO, sin DB)
│   ├── reporting/              ← TU CÓDIGO — PDFs, exports
│   └── shared/                 ← TU CÓDIGO — logger, config, prisma client
│
└── prisma/
    └── schema.prisma           ← TU CÓDIGO — schema y migraciones
```

**Antonio no toca el resto del backend. Vos no tocás `packages/ingestion/webfleet/` (es de Antonio).**

---

# 3. Las 9 invariantes arquitectónicas — leelas, entendelas

Si tu código rompe una de estas, **el PR se rechaza**. No hay excepciones.

```
1. IDEMPOTENCIA DE INGEST
   Mismo archivo entrando 2 veces ≠ samples duplicados.
   Hash SHA256 del contenido + UNIQUE(attempt_id, source, source_hash).
   El segundo upload retorna 200 con flag duplicate:true.

2. REPRODUCIBILIDAD
   Comando `replay <attempt_id>` rerun normalize+detect+score
   con las versiones pinned. Si difiere del score persistido = bug.

3. INMUTABILIDAD DEL ATTEMPT CERRADO
   Si frozen_at != null, ningún UPDATE pasa.
   Constraint en DB Y chequeo en servicio.
   Para corregir → attempt nuevo con parent_attempt_id.

4. VERSIONADO PINNEADO
   Cada attempt cierra con normalizer_version, detector_version,
   criteria_version. Cambios futuros NO afectan attempts cerrados.

5. FUENTE DECLARADA + CONFIANZA (ortogonales)
   Cada Event:
     - source ∈ {sensor, webfleet}
     - confidence ∈ {high, low}              ← visible
     - confidence_score ∈ [0, 1]              ← oculto, V2
     - confidence_reason: string?
   source = de dónde vino. confidence = qué tan confiable es.
   Son cosas distintas. NO las mezcles.

6. INMUTABILIDAD DEL RANKING FINAL
   Si convocatoria.status = CLOSED, ranking_snapshot is_final = true
   no se reescribe (excepción: voided_at/_by/_reason en /close/reverse).

7. DECISIÓN SOLO AL CIERRE
   Attempt NO tiene `decision`.
   La decisión APTO/NO_APTO vive en CandidateOutcome,
   generada por el cierre de convocatoria.

8. CIERRE CON DOBLE VALIDACIÓN + ACTA
   El cierre requiere closing_admin_id Y confirming_admin_id
   (dos personas DISTINTAS) + preview obligatorio + acta PDF.
   Sin las tres cosas: no hay cierre.

9. CRITERIA_VERSION PINNED AL ABRIR
   Cuando se crea un attempt (POST /attempts), el sistema
   captura criteria_version_active y la pinned. Activar nueva
   versión NO afecta attempts ya creados.
```

---

# 4. Tu calendario día por día

```
SEMANA 1 — INFRAESTRUCTURA Y BACKEND CORE
─────────────────────────────────────────

MARTES (DÍA 1) 28/04 — KICKOFF
09:00  Reunión kickoff de 1h con todo el equipo.
       Lectura del paper. Q&A.
11:00  Setup repo, monorepo, workspaces (con Antonio + Alejandro + Joel
       en pantalla compartida).
       Skeleton apps/api, apps/worker + packages internos
       (domain, ingestion/parser, normalization, detection,
       scoring, ranking, reporting, shared).
       Primer PR cada uno: rama chore/setup-<nombre>.

MIÉRCOLES (DÍA 2) 29/04
- Schema Prisma completo (ver §5 abajo).
- Migración inicial.
- Endpoint GET /health funcionando.

JUEVES (DÍA 3) 30/04
- Auth completo (3 roles: ADMIN, MANAGER, ALUMNO + SUPER_ADMIN).
- Middlewares: requireAuth, requireOrg, requireRole, csrf, audit.
- JWT httpOnly + CSRF (csrf-csrf).
- bcrypt para password_hash.
- CRUD básico de Convocatoria.

VIERNES (DÍA 4) 01/05 — FESTIVO (Día del Trabajador)
- Sin trabajo planificado.

[SÁBADO 02/05 + DOMINGO 03/05 — fin de semana, descanso]
[NO HAY DÍA 5 ni DÍA 6 — son festivo + fin de semana]


SEMANA 2 — NORMALIZATION, DETECTION, SCORING, CIERRE
────────────────────────────────────────────────────

LUNES (DÍA 7) 04/05
- Package normalization (saneamiento):
  - alineación timestamps
  - interpolación marcada
  - validación integridad
  - data_quality calculation
  - flag de gaps
- Tests determinísticos con fixtures.
- Empezar packages/detection (detector de eventos como paquete puro).

MARTES (DÍA 8) 05/05
- Terminar packages/detection — REFACTORIZAR a PURO (sin Prisma, sin red).
- Tests determinísticos con fixtures reales.
- Endpoint POST /attempts/:id/upload (idempotente).
- Motor scoring + score_audit poblado en cada cálculo.
- Endpoint POST /attempts/:id/close (normalize+detect+score+freeze).

MIÉRCOLES (DÍA 9) 06/05
- packages/ranking + lógica desempate (cascada 4 criterios).
- Cron job ranking nocturno (BullMQ repeatable, "0 6 * * *",
  TZ='Europe/Madrid').
- Endpoint GET /convocatorias/:id/ranking (último snapshot).
- Endpoints audit-request + reevaluate.

JUEVES (DÍA 10) 07/05
- Endpoints admin (rutas, RFID, scoring read-only).
- Endpoints cierre completos:
    /close/preview
    /close/initiate
    /close/confirm
    /close/abort
    /close/reverse
- Lógica de ConvocatoriaCloseAct + CandidateOutcome al cierre.
- Acta PDF con Puppeteer + SHA256.
- Función pura `packages/scoring/simulate(attempts, overrides) → newScores` lista al final del día. Antonio la consume el día 10 desde el endpoint que él escribe.

VIERNES (DÍA 11) 08/05
- Datos seed completos (con Joel).
- Verificación end-to-end.
- Pasada por checklist Anexo C del paper maestro.

SÁBADO (DÍA 12) 09/05 — TORTURA DEL KIOSKO
- Lidera Joel. Vos validás backend (voluntario, fuera del horario laboral acordado).

DOMINGO (DÍA 13) 10/05 — ENSAYO DEMO
- 3 pasadas completas en staging.

LUNES (DÍA 14) 11/05 — REUNIÓN CMADRID
```

> **Nota sobre el viernes 1 de mayo:** España tiene festivo nacional (Día del Trabajador). El plan absorbe la pérdida moviendo el trabajo de "Día 5 Viernes" a la semana 2. Si vemos que vamos justos, hablamos con Antonio antes del fin de la semana 1.

---

# 5. Schema Prisma — modelos críticos

> **Nota editorial**: los bloques `prisma` documentan el contrato. Las relaciones inversas escalares (`attempt Attempt @relation(fields: [attempt_id], references: [id])` en cada modelo hijo) **se omiten cuando son simétricas y triviales** — declarálas TODAS explícitamente al implementar `schema.prisma`. Donde un modelo hijo tenga `<modelo>_id String`, agregá el campo de relación. Si dudás, declará todo.

## 5.1 User & Auth (con SUPER_ADMIN)

```prisma
model User {
  id                          String   @id @default(cuid())
  email                       String   @unique
  password_hash               String
  role                        UserRole
  organization_id             String
  privacy_consent_accepted_at DateTime?     // GDPR — login bloqueado si null para rol ALUMNO
  privacy_notice_version      String?
  created_at                  DateTime @default(now())
}

enum UserRole {
  SUPER_ADMIN     // único rol que puede /close/reverse y aprobar GDPR forget
  ADMIN           // operaciones diarias + cierre (initiate / confirm)
  MANAGER         // solo lectura + resolución de auditorías
  ALUMNO          // candidato
}
```

**Reglas en V1:** seed bootstrap debe crear ≥1 SUPER_ADMIN + ≥2 ADMIN. `/health/deep` falla si la organización no tiene esos 3 actores.

## 5.2 Convocatoria — cierre reforzado v6

```prisma
model Convocatoria {
  id               String   @id @default(cuid())
  name             String
  description      String?
  starts_at        DateTime
  closes_at        DateTime              // fecha de cierre publicada
  plazas           Int                   // número de plazas (público)
  status           ConvocatoriaStatus    @default(OPEN)

  // CIERRE REFORZADO
  closing_initiated_at  DateTime?         // cuándo admin inició el cierre (entra a CLOSING)
  closing_admin_id      String?           // primer admin que inicia
  confirming_admin_id   String?           // segundo admin DISTINTO al primero
  closed_at             DateTime?         // ejecución definitiva
  acta_pdf_url          String?
  reversal_window_until DateTime?         // closed_at + 24h wallclock Madrid
  reversed_at           DateTime?
  reversed_by           String?
  reversal_reason       String?

  ruta_principal_id String?               // nullable hasta antes del primer ranking
  ruta_principal   Route?    @relation("RutaPrincipal", fields: [ruta_principal_id], references: [id])

  rutas             ConvocatoriaRuta[]
  enrollments       Enrollment[]                              // back-ref de Enrollment.convocatoria
  attempts          Attempt[]
  ranking_snapshots RankingSnapshot[]
  outcomes          CandidateOutcome[]
  close_acts        ConvocatoriaCloseAct[]                    // múltiples (VIGENTE + VOIDED)
  organization_id   String

  @@index([status])
  @@index([reversal_window_until])
}

enum ConvocatoriaStatus {
  OPEN       // En curso, ranking actualizable
  CLOSING    // Admin inició cierre, esperando confirmación de segundo admin
  CLOSED     // Cerrada (puede revertirse en ventana de 24h por SUPER_ADMIN)
  LOCKED     // Cerrada irrevocablemente (pasaron las 24h)
}

model ConvocatoriaRuta {
  convocatoria_id String
  ruta_id         String
  peso            Float   @default(1.0)  // V1 siempre 1.0, V2 configurable

  convocatoria Convocatoria @relation(fields: [convocatoria_id], references: [id])
  ruta         Route        @relation(fields: [ruta_id], references: [id])

  @@id([convocatoria_id, ruta_id])
}
```

## 5.3 Route, Vehicle, Kiosko

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

## 5.4 Student / Enrollment / RfidCard (refactor v6)

**Cambio crítico v6:** separamos al **humano** (`Student`) de su **inscripción** a una convocatoria (`Enrollment`). Un mismo candidato puede inscribirse en múltiples convocatorias sin duplicar User.

```prisma
// El humano. Hay UNA fila por candidato físico.
model Student {
  id              String   @id @default(cuid())
  user_id         String   @unique
  organization_id String

  enrollments     Enrollment[]
  rfid_cards      RfidCard[]
}

// La inscripción de un Student a UNA convocatoria.
// Es la unidad que entra al ranking.
model Enrollment {
  id               String   @id @default(cuid())
  student_id       String
  convocatoria_id  String
  enrolled_at      DateTime @default(now())
  withdrawn_at     DateTime?
  organization_id  String

  student          Student      @relation(fields: [student_id], references: [id])
  convocatoria     Convocatoria @relation(fields: [convocatoria_id], references: [id])
  attempts         Attempt[]
  outcome          CandidateOutcome?
  ranking_entries  RankingEntry[]

  @@unique([student_id, convocatoria_id])  // un mismo humano una sola vez por convocatoria
  @@index([convocatoria_id])
  @@index([student_id])
}

// RfidCard sin @unique de columna — partial unique en migration raw.
model RfidCard {
  id              String   @id @default(cuid())
  uid             String                   // ID físico del lector
  assigned_to     String?                  // student_id (nullable cuando libre)
  assigned_at     DateTime?
  revoked_at      DateTime?
  active          Boolean  @default(true)
  organization_id String

  student         Student? @relation(fields: [assigned_to], references: [id])

  @@index([assigned_to])
  @@index([uid])
  @@index([uid, active, revoked_at])
}
```

**Migration raw obligatoria:**

```sql
CREATE UNIQUE INDEX rfid_card_uid_active_unique
  ON "RfidCard" (uid)
  WHERE active = true AND revoked_at IS NULL;
```

## 5.5 Attempt — el cambio más importante

```prisma
model Attempt {
  id                    String   @id @default(cuid())
  enrollment_id         String                   // v6: FK a Enrollment, no a Student
  vehicle_id            String
  route_id              String
  convocatoria_id       String                   // denormalizado para queries de ranking
  kiosko_id             String?
  organization_id       String

  started_at            DateTime
  ended_at              DateTime?

  status                AttemptStatus @default(OPEN)

  // Versionado pinned AL CREAR (v6) — no al cerrar
  normalizer_version    String
  detector_version      String
  criteria_version      String

  // Resultado (al cerrar)
  score                 Float?         // nota 0-10
  stability_family_score Float?        // agregado de ScoreAudit family=estabilidad
  data_quality          DataQuality?
  data_quality_metrics  Json?

  // ✗ NO tiene `decision` — vive en CandidateOutcome al cierre

  // Sync Doback Elite (v6)
  awaiting_doback_data  Boolean @default(false)
  doback_sync_attempts  Int     @default(0)
  doback_synced_at      DateTime?

  // Auditoría — v6: AMBOS lados de las dos relaciones nombradas
  audit_request_id          String?
  audit_request             AuditRequest?  @relation("AttemptOriginatedByAudit", fields: [audit_request_id], references: [id])
  audit_requests_as_original AuditRequest[] @relation("OriginalAttemptOfAudit")

  // Reevaluación
  parent_attempt_id     String?
  parent                Attempt?  @relation("AttemptHistory", fields: [parent_attempt_id], references: [id])
  children              Attempt[] @relation("AttemptHistory")

  // Inmutabilidad
  frozen_at             DateTime?

  // Relaciones (back-refs)
  raw_samples           RawSample[]
  normalized_samples    NormalizedSample[]
  events                Event[]
  score_audit           ScoreAudit[]

  enrollment            Enrollment   @relation(fields: [enrollment_id], references: [id])
  convocatoria          Convocatoria @relation(fields: [convocatoria_id], references: [id])

  @@index([enrollment_id])
  @@index([convocatoria_id])
  @@index([frozen_at])
  @@index([awaiting_doback_data])
}

enum AttemptStatus {
  OPEN                       // En curso (kiosko activo)
  PROCESSING                 // Datos llegando
  AWAITING_DOBACK_DATA       // Cerrado en kiosko, esperando sync Doback Elite
  PENDING_DATA_REVIEW        // Normalization rechazó
  PENDING_TECHNICAL_REVIEW   // ABORTED técnico inminente al cierre — decisión admin
  PENDING_CRITERIA_REVIEW    // Kiosko offline con criteria_version stale
  CLOSED                     // Nota emitida, frozen
  ABANDONED                  // Candidato no completó (cuenta como 0)
  ABORTED_TECHNICAL          // Fallo del sistema (NO cuenta)
  INTERRUPTED_BY_OTHER_CARD  // Otra tarjeta cerró el attempt antes del 80% (NO cuenta)
}

enum DataQuality {
  HIGH
  MEDIUM
  LOW
}
```

## 5.6 Samples (raw + normalized)

```prisma
model RawSample {
  id              String   @id @default(cuid())
  attempt_id      String
  source          SampleSource
  source_hash     String
  timestamp       DateTime
  payload         Json
  organization_id String

  @@unique([attempt_id, source, source_hash])  // idempotencia
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

## 5.7 Event

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

## 5.8 Scoring versionado

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

## 5.9 Score Audit (granular)

```prisma
model ScoreAudit {
  id                 String   @id @default(cuid())
  attempt_id         String
  rule_id            String
  rule_version       String
  family             String  // estabilidad | velocidad | ruta | conduccion
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

## 5.10 Ranking

```prisma
model RankingSnapshot {
  id                String   @id @default(cuid())
  convocatoria_id   String
  calculated_at     DateTime @default(now())
  is_final          Boolean  @default(false)  // true solo al cierre
  total_candidates  Int
  total_plazas      Int

  // Invalidación tras reversa
  voided_at         DateTime?
  voided_by         String?
  voided_reason     String?

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
  enrollment_id       String                 // v6: ranking opera sobre Enrollment
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

## 5.11 CandidateOutcome (decisión final)

```prisma
model CandidateOutcome {
  id                  String   @id @default(cuid())
  enrollment_id       String   @unique           // v6: una decisión por inscripción
  convocatoria_id     String
  decision            Decision
  puesto_final        Int
  nota_media_final    Float
  rutas_completadas   Int
  decided_at          DateTime @default(now())

  // Invalidación tras reversa
  superseded_at       DateTime?
  superseded_by       String?
  superseded_reason   String?

  organization_id     String

  enrollment          Enrollment   @relation(fields: [enrollment_id], references: [id])
  convocatoria        Convocatoria @relation(fields: [convocatoria_id], references: [id])
  amendments          OutcomeAmendment[]         // F6 (Fase 2)

  @@index([convocatoria_id])
}

enum Decision {
  APTO
  NO_APTO
}
```

## 5.12 AuditRequest

```prisma
model AuditRequest {
  id                    String   @id @default(cuid())
  original_attempt_id   String                          // attempt sobre el que se solicita auditoría
  enrollment_id         String                          // quién solicita
  reason                String                          // ≥30 chars
  status                AuditStatus @default(PENDING)
  reviewed_by           String?
  reviewed_at           DateTime?
  resolution            String?
  filed_after_close     Boolean  @default(false)
  organization_id       String

  attempts              Attempt[] @relation("AttemptOriginatedByAudit")
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
  REJECTED        // solicitud sin mérito documentada
  POST_CLOSE      // solicitud presentada tras cierre (F5 Fase 2)
}
```

## 5.13 ConvocatoriaCloseAct (acta del cierre)

```prisma
model ConvocatoriaCloseAct {
  id                String   @id @default(cuid())
  convocatoria_id   String                    // SIN @unique (puede haber múltiples actas
                                              // VIGENTE + VOIDED tras reverse)
  generated_at      DateTime @default(now())
  closing_admin_id  String
  confirming_admin_id String
  ranking_snapshot_id String
  total_candidatos  Int
  total_aptos       Int
  total_no_aptos    Int
  pdf_url           String                    // path en object storage (S3/MinIO)
  pdf_sha256        String                    // hash para inmutabilidad
  status            CloseActStatus  @default(VIGENTE)
  organization_id   String

  convocatoria      Convocatoria @relation(fields: [convocatoria_id], references: [id])

  @@index([convocatoria_id])
}

enum CloseActStatus {
  VIGENTE
  VOIDED           // anulada por reverse en ventana 24h (queda como evidencia)
}
```

**Migration raw:**

```sql
CREATE UNIQUE INDEX close_act_one_vigente_per_convocatoria
  ON "ConvocatoriaCloseAct" (convocatoria_id)
  WHERE status = 'VIGENTE';
```

## 5.14 AuditLog (registro de acciones críticas)

```prisma
model AuditLog {
  id              String   @id @default(cuid())
  actor_id        String
  actor_role      UserRole
  action          AuditAction
  target_type     String                  // "Convocatoria", "Attempt", etc.
  target_id       String
  details         Json
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
  CONVOCATORIA_CLOSE_ABORT
  CONVOCATORIA_CLOSE_REVERSE
  ATTEMPT_OVERRIDE_VIA_AUDIT
  ATTEMPT_RECATEGORIZE_TECHNICAL
  CRITERIA_VERSION_ACTIVATE
  STUDENT_DATA_EXPORT
  STUDENT_DATA_EXPORT_DOWNLOAD
  STUDENT_DATA_DELETE
  STUDENT_DATA_FORGET_APPROVE
  STUDENT_DATA_ANONYMIZE
  OUTCOME_AMENDMENT_REGISTER
  RFID_ASSIGN
  RFID_REVOKE
  USER_ROLE_CHANGE
}
```

**Cada acción crítica del backend escribe en AuditLog ANTES de retornar al cliente. Si el INSERT AuditLog falla, la acción falla — no hay acción sin trazabilidad.**

## 5.15 GdprDataExport

```prisma
model GdprDataExport {
  id              String   @id @default(cuid())
  student_id      String
  requested_at    DateTime @default(now())
  status          GdprStatus @default(PENDING)
  generated_at    DateTime?
  export_url      String?
  expires_at      DateTime?          // 7 días
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

---

# 6. Endpoints — catálogo completo (que tenés que tener funcionando)

## 6.1 Auth

```
POST   /auth/login                          (3 roles + super_admin)
POST   /auth/logout
POST   /auth/refresh
GET    /auth/me
POST   /auth/csrf-token
```

## 6.2 Convocatorias (cierre 3-pasos completo)

```
GET    /convocatorias                       listado
GET    /convocatorias/:id                   detalle
POST   /convocatorias                       crear (admin)
PATCH  /convocatorias/:id                   editar (solo si OPEN)

POST   /convocatorias/:id/close/preview     PASO 1: simulación (idempotente)
POST   /convocatorias/:id/close/initiate    PASO 2: admin#1 inicia (OPEN→CLOSING)
POST   /convocatorias/:id/close/confirm     PASO 3: admin#2 confirma + acta
POST   /convocatorias/:id/close/abort       cancela CLOSING (initiator o SUPER_ADMIN)
POST   /convocatorias/:id/close/reverse     SUPER_ADMIN, ventana 24h
GET    /convocatorias/:id/acta              descargar acta PDF

GET    /convocatorias/:id/ranking           ranking actual
GET    /convocatorias/:id/ranking/history   listado snapshots
GET    /convocatorias/:id/outcomes          decisiones finales (CLOSED/LOCKED)
```

## 6.3 Attempts

```
POST   /attempts                            crear (pinea criteria/normalizer/detector versions)
POST   /attempts/:id/upload                 subir archivo sensor (idempotente)
POST   /attempts/:id/sync-webfleet          delega al package webfleet de Antonio
POST   /attempts/:id/close                  detect+score+freeze
GET    /attempts/:id                        detalle
GET    /attempts/:id/audit                  score_audit granular
POST   /attempts/:id/audit-request          ALUMNO solicita auditoría
POST   /attempts/:id/reevaluate             MANAGER crea reevaluación
GET    /attempts                            listado paginado
```

## 6.4 Doback Elite (sync)

```
POST   /doback/upload                       Doback Elite POST datos crudos
                                            Auth: device JWT (pairing token)
GET    /doback/attempts/awaiting-sync       Doback Elite GET attempts pendientes
```

## 6.5 Auditorías

```
GET    /audit-requests                      listado para manager
GET    /audit-requests/:id                  detalle
PATCH  /audit-requests/:id                  manager actualiza status (incluye REJECTED)
```

## 6.6 Matriz, Alumnos, Rutas

```
GET    /matrix?convocatoria=X               datos para matriz manager
GET    /students/me                         detalle propio (alumno)
GET    /students/me/history                 historial propio
GET    /students/me/attempts/:aid           detalle pedagógico propio
GET    /students/me/evolution               evolución propia
GET    /students/me/standings               PLURAL — multi-enrollment
GET    /students/:id                        detalle (rol ≥ MANAGER)
GET    /students/:id/history                historial (rol ≥ MANAGER)
GET    /routes                              CRUD
POST   /routes
PATCH  /routes/:id
DELETE /routes/:id
GET    /routes/:id/cohort-stats             análisis convocatoria
```

## 6.7 RFID

```
GET    /rfid                                listado tarjetas
POST   /rfid                                registrar
POST   /rfid/:id/assign                     asignar
DELETE /rfid/:id/assign                     desasignar
DELETE /rfid/:id                            desactivar
```

## 6.8 Scoring + Simulador (con dimensión RANKING)

```
GET    /scoring/versions                    listado
GET    /scoring/versions/:id                detalle
POST   /scoring/versions                    crear (admin)
POST   /scoring/versions/:id/activate       activar (transacción atómica)

POST   /scoring/simulate                    SIMULADOR (Joel implementa endpoint, vos lógica core puro)
                                            body: {criteria_overrides, convocatoria_id}
                                            → ranking_original + ranking_simulado +
                                              candidatos_que_cruzan_corte + summary
```

## 6.9 Kiosko

```
POST   /kiosko/pair                         pairing inicial
POST   /kiosko/rfid-tap                     tap RFID, abrir/cerrar attempt
GET    /kiosko/state                        estado actual
POST   /kiosko/sync                         sync de eventos pendientes (cola)
POST   /kiosko/heartbeat                    kiosko reporta vivo
```

## 6.10 Admin (kioskos, GDPR, scoring)

```
GET    /admin/kioskos                       listado con last_seen
DELETE /admin/kioskos/:id/pair              revoca pairing

POST   /students/me/data-export             ALUMNO solicita export
GET    /students/me/data-exports            listado de exports propios
GET    /gdpr/exports/:id/download           descarga ZIP (auth + ownership check)
POST   /students/me/forget-request          ALUMNO solicita borrado
GET    /admin/gdpr/forget-requests          admin lista pendientes
POST   /admin/gdpr/forget-requests/:id/approve  SUPER_ADMIN aprueba
```

## 6.11 Health

```
GET    /health                              200 OK
GET    /health/deep                         DB + Redis + Webfleet + admin-quorum
                                            (1 SUPER_ADMIN + ≥2 ADMIN per org)
```

---

# 7. Lógica clave del backend

## 7.1 packages/ranking — motor de ordenamiento

**Función pura.** No toca DB. Recibe input estructurado, devuelve output ordenado.

```typescript
interface RankingInput {
  convocatoria: {
    id: string;
    plazas: number;
    rutas: { id: string; peso: number }[];
    ruta_principal_id: string | null;
    closes_at_iso: string;
  };
  enrollments: {
    id: string;                   // enrollment_id
    student_id: string;
    attempts: Array<{
      route_id: string;
      score: number | null;
      status: AttemptStatus;
      data_quality: DataQuality | null;
      stability_family_score: number | null;
    }>;
  }[];
}

interface RankingOutput {
  entries: Array<{
    enrollment_id: string;
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

**Cascada de desempate (V1):**

```
   1° Mejor nota en ruta_principal_id
      Si ALGUNO empatado NO completó la principal, ese criterio
      se SALTA y se aplica el 2° entre todos.

   2° Menor TASA de attempts con data_quality = LOW
      = count(LOW) ÷ count(NOT NULL)
      Es PROPORCIÓN, no absoluto. Esto evita que abandonar
      muchas rutas gane el desempate.

   3° Mejor nota promedio en familia "estabilidad"

   4° Sorteo determinista
      Semilla = SHA256(convocatoria_id + enrollment_id + closes_at_iso)
```

## 7.2 Cron job ranking nocturno

```typescript
// apps/worker/src/jobs/rankingCron.ts
// BullMQ repeatable: cron pattern "0 6 * * *", TZ='Europe/Madrid'
// Para cada convocatoria con status = OPEN:
//   1. Recoger todos los attempts CLOSED
//   2. Llamar packages/ranking.computeRanking
//   3. Persistir RankingSnapshot + RankingEntry[]
//   4. is_final = false (será true solo al cierre)
```

## 7.3 Cierre de convocatoria — flujo de 3 pasos

### `/close/preview` (idempotente, solo lectura)

```typescript
// 1. SELECT convocatoria; validar status = OPEN
// 2. Calcular ranking final SIMULADO
// 3. Calcular advertencias (incompletos, audits pendientes, etc.)
// 4. RETURN { ranking_final_simulado, aptos_count, no_aptos_count, advertencias[] }
```

### `/close/initiate` (admin#1)

```typescript
// Body: { confirmation_text }
// 1. Validar confirmation_text === convocatoria.name
// 2. UPDATE atómico:
//      UPDATE convocatoria
//      SET status='CLOSING', closing_admin_id=$me, closing_initiated_at=NOW()
//      WHERE id=$id AND status='OPEN'
//      RETURNING *;
//    Si filas afectadas = 0 → 409
// 3. Insertar AuditLog: CONVOCATORIA_CLOSE_INITIATE
```

### `/close/confirm` (admin#2 distinto + re-auth)

```typescript
// Body: { confirmation_text, password }
// 1. Re-validar contraseña
// 2. SELECT convocatoria; validar status = CLOSING
// 3. VALIDAR auth.user.id !== convocatoria.closing_admin_id
// 4. Validar confirmation_text === convocatoria.name
// 5. Transacción:
//    a. Calcular ranking final
//    b. INSERT RankingSnapshot { is_final: true, ... }
//    c. Para cada Enrollment:
//         INSERT CandidateOutcome { enrollment_id, decision, puesto, ... }
//    d. Generar acta PDF con Puppeteer; calcular SHA256
//    e. Persistir el PDF en object storage
//    f. INSERT ConvocatoriaCloseAct { status: 'VIGENTE', ... }
//    g. UPDATE convocatoria
//         SET status='CLOSED', closed_at=NOW(),
//             confirming_admin_id=$me,
//             reversal_window_until=$now_plus_24h_wallclock_madrid
//    h. AuditLog: CONVOCATORIA_CLOSE_CONFIRM
// 6. RETURN { acta_url, candidate_outcomes_count }
```

### `/close/abort` (cancelar CLOSING)

```typescript
// Auth: ADMIN que sea closing_admin_id, O cualquier SUPER_ADMIN
// Body: { reason } // ≥30 chars
// UPDATE convocatoria
//   SET status='OPEN', closing_admin_id=NULL, closing_initiated_at=NULL
//   WHERE id=$id AND status='CLOSING'
// AuditLog: CONVOCATORIA_CLOSE_ABORT
```

### `/close/reverse` (SUPER_ADMIN, 24h)

```typescript
// Auth: SUPER_ADMIN
// Body: { reason } // ≥50 chars
// 1. SELECT convocatoria; validar status = CLOSED y NOW < reversal_window_until
// 2. Transacción:
//    a. UPDATE RankingSnapshot SET voided_at, voided_by, voided_reason
//       WHERE convocatoria_id=$id AND is_final=true AND voided_at IS NULL
//    b. UPDATE CandidateOutcome SET superseded_at, superseded_by, superseded_reason
//       WHERE convocatoria_id=$id AND superseded_at IS NULL
//    c. UPDATE ConvocatoriaCloseAct SET status='VOIDED'
//       WHERE convocatoria_id=$id AND status='VIGENTE'
//    d. UPDATE convocatoria
//         SET status='OPEN', reversed_at=NOW(), reversed_by=$me, reversal_reason=$reason,
//             closing_admin_id=NULL, closing_initiated_at=NULL,
//             confirming_admin_id=NULL, closed_at=NULL, reversal_window_until=NULL
//    e. AuditLog: CONVOCATORIA_CLOSE_REVERSE
```

### Cron CLOSED → LOCKED (cada 15 min)

```typescript
UPDATE convocatoria SET status = 'LOCKED'
WHERE status = 'CLOSED' AND reversal_window_until < NOW();
```

## 7.4 Triggers DB para inmutabilidad

```sql
-- ranking_snapshot_immutability:
-- Rechaza UPDATE de cualquier campo de RankingSnapshot DONDE is_final=true,
-- EXCEPTO voided_at, voided_by, voided_reason.

-- convocatoria_closed_immutability:
-- Rechaza UPDATE DONDE status='LOCKED' (sin excepciones).
-- Para status='CLOSED', rechaza UPDATE de campos value-bearing
-- (closes_at, plazas, ruta_principal_id, name) PERO permite
-- los campos del flujo de cierre/reversa.

-- candidate_outcome_immutability:
-- Rechaza UPDATE de campos value-bearing (decision, puesto_final, nota_media_final).
-- PERMITE UPDATE de superseded_at/_by/_reason.
```

## 7.5 ABANDONED vs ABORTED_TECHNICAL

**Función pura** `classifyIncomplete(attempt, samples_metrics, second_tap_metadata)`:

```
ABORTED_TECHNICAL si CUALQUIERA:
  1. DOBACK_ELITE_NO_DATA — awaiting_doback_data && now > started_at + 24h
  2. DOBACK_SAMPLE_LOSS — Doback envió pero <60% de la ventana tiene samples válidos
  3. WEBFLEET_NO_DATA_AND_NO_GPS_BACKUP — Webfleet vacío + Doback sin GPS
  4. RFID_KIOSKO_DISCREPANCY — kiosko reporta tap pero backend no encuentra RfidCard activa
  5. KIOSKO_LOST_AT_CRITICAL_PHASE — kiosko offline >30min con gap >5min al recuperar

ABANDONED si NINGUNO de los técnicos Y:
  - candidato no completó la ruta (ended_at sin alcanzar trayectoria mínima)
  - Y la ruta NO se cerró por tap de otra tarjeta

INTERRUPTED_BY_OTHER_CARD si:
  - la ruta se cerró porque OTRA tarjeta entró antes del 80%
  - este estado NO cuenta en el ranking (no penaliza al inocente)

PENDING_TECHNICAL_REVIEW si:
  - ABORTED_TECHNICAL Y la convocatoria cierra en <72h
  - admin debe decidir manualmente
```

---

# 8. Patrones de implementación de referencia

Algunos patrones técnicos que usás vienen del estado del arte de la empresa. Antonio te orienta el día 1 sobre **qué patrones aplicar** y **cómo se ven en producción**:

| Patrón | Dónde aplicarlo en Training |
|---|---|
| Schema Prisma con `Convocatoria`, `Enrollment`, `Attempt`, `Event` y relaciones inversas explícitas | `prisma/schema.prisma` (ver §5 de este doc) |
| Detección de eventos a partir de muestras (algoritmo puro, sin Prisma ni red) | `packages/detection/` |
| Normalización y saneamiento de datos antes de procesar | `packages/normalization/` |
| `requireOrg` middleware multi-tenant | `apps/api/src/middleware/` |
| JWT httpOnly + CSRF (csrf-csrf) + bcrypt | `apps/api/src/middleware/` |
| Parser de archivos del sensor (formato del cliente) | `packages/ingestion/parser/` |

**Regla del sprint:** Training es un sistema **nuevo y autónomo**. Cada archivo se escribe pensando en este proyecto, no en heredar deuda de otros sitios. Si te encontrás copiando algo a ciegas, parás y lo discutimos.

---

# 9. Tu interfaz con el resto del equipo

## Con Antonio (Webfleet)

Vos consumís el package que él escribe:

```typescript
// En apps/worker/src/jobs/processAttempt.ts:
import { syncAttempt, getQuotaStatus } from '@training/ingestion-webfleet';

const result = await syncAttempt(attempt_id, { force: false });
// result tiene events_count, raw_samples_count, data_freshness
```

Si Antonio cambia la interfaz, te avisa antes. Si vos necesitás algo nuevo de Webfleet, le pedís.

## Con Alejandro (frontend)

Alejandro consume tus endpoints. **Reglas de comunicación:**

- **Si cambiás un endpoint** (path, response shape, error codes), avisale ANTES de pushear.
- **Si Alejandro pide algo nuevo**, evaluás scope. Si entra en el sprint, lo agregás. Si no, va a Fase 2.
- Errores HTTP consistentes: 400 (request mal formado), 401 (no autenticado), 403 (sin permisos), 404 (no existe), 409 (conflict), 422 (validación), 500 (server error).

## Con Joel (simulador + tests + seed data + CI)

- **Simulador:** vos exponés `packages/scoring/simulate()` como función pura el día 9 al cierre. Joel escribe el endpoint `POST /scoring/simulate` el día 10 consumiendo tu función. Si tu función cambia firma a partir del día 10, le avisás a Joel en chat antes de mergear.
- Joel hace los tests E2E que llaman a TUS endpoints. Si rompés un endpoint, avisale.
- Joel hace los datos seed. Vos le decís qué datos necesita el sistema (cuántos enrollments, cuántos attempts cerrados, etc.).
- El `docs/api-snapshot.md` se genera automático cada noche desde tu código vía un cron de CI que monta Joel. Confirmá con él el día 1 qué anotaciones JSDoc/decorador necesita en tu plan.

---

# 10. Criterios de "tu trabajo está bien hecho"

```
   ✓ Tests determinísticos en normalization, detection, scoring, ranking
   ✓ El comando `replay <attempt_id>` reproduce score idéntico
   ✓ Subir mismo archivo 2 veces no duplica samples
   ✓ Cerrar attempt e intentar mutarlo falla (constraint + servicio)
   ✓ Cambiar criteria_version no afecta attempts ya creados
   ✓ Reevaluación crea attempt nuevo con parent, no muta el viejo
   ✓ score_audit tiene una fila por cada regla evaluada
   ✓ Cada Event tiene source Y confidence Y data_quality
   ✓ Ranking nocturno corre y persiste snapshot
   ✓ Cierre 3-pasos funciona: doble admin obligatorio
   ✓ Acta PDF generada con SHA256 visible al admin
   ✓ Ventana 24h de reversa funcional
   ✓ Cron CLOSED → LOCKED funciona
   ✓ Convocatoria LOCKED no acepta UPDATE
   ✓ Simulator devuelve impacto en ranking, no solo notas
   ✓ AttemptStatus distingue ABANDONED vs ABORTED_TECHNICAL vs INTERRUPTED_BY_OTHER_CARD
   ✓ AuditLog escribe en cada acción crítica
   ✓ /health/deep falla si no hay 1 SUPER_ADMIN + 2 ADMIN
   ✓ Cero console.log en producción (Winston siempre)
   ✓ Cero `: any` nuevos sin justificación
   ✓ requireOrg en TODOS los endpoints excepto los públicos
```

---

# 11. Reglas firmes que tenés que aceptar

**No se reabren durante el sprint. Si querés discutirlas, hacelo ANTES del kickoff.**

```
   D1: DB nueva y separada para Training (no se reutiliza ningún esquema previo)
   D2: 12 meses retención de samples
   D4: RFID = USB-HID emulando teclado
   D5: Formato actual del sensor (no inventar)
   D7: Routing cutover por header de cohorte
   D8: Confidence binario V1, score continuo en schema (oculto)
   D9: Normalization desde día 4
   D10: parent_attempt_id desde día 1
   D11: data_quality global del attempt
   D14: Modelo OPOSICIÓN (no escolar)
   D15: Media simple para agregación
   D16: Pesos por ruta = 1.0 en V1
   D17: ABANDONED vs ABORTED_TECHNICAL con criterios automáticos
   D18: Plazas configurable por convocatoria
   D19: Empates cascada de 4 criterios
   D21: Ranking diario 6 AM Madrid + cierre manual con confirmación
   D22: Cierre 3-pasos + doble admin + acta + ventana 24h
   D23: GDPR como decisión arquitectónica V1
   D24: Sync Doback Elite ↔ backend con device JWT
   D25: criteria_version pinned al ABRIR
```

---

# 12. Glosario mínimo

| Término | Significado |
|---|---|
| **Attempt** | Intento de evaluación. Un enrollment + una ruta + una sesión. |
| **Enrollment** | Inscripción de un Student a UNA convocatoria. Un humano puede tener varias. |
| **Student** | El humano. Una fila por candidato físico, vive durante años. |
| **Convocatoria** | Proceso de oposición concreto. |
| **Ranking** | Ordenamiento competitivo dentro de una convocatoria. Se actualiza diariamente. |
| **Plazas** | Número entero fijo de plazas. Público desde día 1. |
| **CandidateOutcome** | Decisión final APTO/NO_APTO. Generada al cierre. |
| **AuditRequest** | Solicitud formal de auditoría hecha por un alumno. |
| **ConvocatoriaCloseAct** | Acta PDF del cierre, con SHA256. |
| **OutcomeAmendment** | Modificación post-LOCKED por recurso administrativo (Fase 2). |
| **Doback Elite** | Dispositivo físico instalado en cada camión. Antonio escribe el package. |
| **Webfleet** | Plataforma externa de Bridgestone. Lo gestiona Antonio. |
| **frozen_at** | Timestamp del cierre del attempt. Si está poblado → inmutable. |
| **CLOSED / LOCKED** | Estados post-cierre. CLOSED = revertible 24h. LOCKED = irrevocable. |
| **SUPER_ADMIN** | Único rol que puede /close/reverse y aprobar GDPR forget. |

---

**Si necesitás detalle adicional, mirá el Paper Maestro completo. Daily a las 9:30. Vamos.**
