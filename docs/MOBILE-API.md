# Mobile API V1 — contrato

> API JSON read-only sobre HTTPS en `/api/v1/*`. Pensada para consumirse desde clientes nativos (Apple SwiftUI / Watch en planificación). El portal web Jinja sigue usando cookies y NO está en este contrato — solo `/api/v1/*` aplica.

**Versión:** v1 · **Estado:** estable (post-merge de los PRs de Fase 1) · **Owner contrato:** Antonio · **Owner backend:** Jesús.

---

## 1. Política de versionado

- **v1 es estable.** Una vez mergeada Fase 1, no se rompe sin bumpear `/api/v2/*`.
- **Cambios non-breaking** (agregar campos opcionales en una respuesta): permitidos en v1.
- **Cambios breaking** (remover/renombrar campos, cambiar shape, cambiar semántica): NO en v1 — se publica `/api/v2/*` y se anuncia.
- **Deprecation:** cuando se vaya a retirar un endpoint, se sirve con header `Deprecation: true` durante al menos 4 semanas antes de retirarlo.

---

## 2. Autenticación

Dos transportes coexisten en el mismo backend:

| Cliente | Transporte | CSRF | Notas |
|---|---|---|---|
| Portal web (Jinja) | JWT en cookie HttpOnly | Sí (`JWT_COOKIE_CSRF_PROTECT=True`) | Sin cambios respecto a hoy. |
| Cliente nativo (`/api/v1/*`) | JWT en `Authorization: Bearer <token>` | No aplica (los headers no son enviables cross-site sin JS explícito) | Habilitado vía `JWT_TOKEN_LOCATION = ["cookies", "headers"]`. |

**Regla del portal web:** el JS del portal **nunca** envía `Authorization: Bearer` — siempre cookie implícita. Si un día algún endpoint web hiciera `fetch` con header de Authorization, se saltea CSRF. No hacerlo.

### Login

- **`POST /api/v1/auth/login`** · público · 10 req/min por IP.
- Request:
  ```http
  POST /api/v1/auth/login HTTP/1.1
  Content-Type: application/json

  {"email": "alumno@cmadrid.com", "password": "..."}
  ```
- Response 200:
  ```json
  {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "ck...",
      "email": "alumno@cmadrid.com",
      "name": "Alumno Apellido",
      "role": "STUDENT",
      "organizationId": "ck...",
      "studentProfileId": "ck..."
    }
  }
  ```
- **Sin `Set-Cookie`** en la respuesta. Los clientes nativos no manejan cookies — la respuesta es predecible para SwiftUI/Watch.
- 401 si las credenciales no coinciden:
  ```json
  {"error": "unauthenticated", "message": "Credenciales inválidas"}
  ```

### Refresh

- **`POST /api/v1/auth/refresh`** · refresh JWT en `Authorization` · 30 req/min.
- Request:
  ```http
  POST /api/v1/auth/refresh HTTP/1.1
  Authorization: Bearer <refresh_token>
  ```
- Response 200:
  ```json
  {"access_token": "eyJ...", "expires_in": 3600}
  ```
- El refresh token **NO rota** en v1. Sigue válido hasta su expiración natural (30 días).

### Tokens

- **Access token:** 1 hora.
- **Refresh token:** 30 días.
- **Sin revocation list / sin denylist** en v1. Si un token se filtra, queda válido hasta su expiración. Deuda asumida; se mitiga en change separado post-v1 si CMadrid lo exige.

### Logout

No hay endpoint de logout en v1. El cliente borra los tokens de su almacenamiento local (Keychain en iOS) y listo.

### Inconsistencia conocida en errores 401/403

- Los error handlers del blueprint devuelven `{"error": "<codigo>", "message": "<texto>"}`.
- El decorador compartido `@require_role` (en `app/utils/decorators.py`) devuelve `{"message": "<texto>"}` sin la clave `error`. Es código existente del repo y refactorizarlo está fuera de scope de v1.
- **El cliente debe tolerar ambas shapes** en respuestas 4xx. En la práctica: leer `message` siempre; `error` puede no estar.

---

## 3. Errores

Shape JSON estándar para todos los errores de `/api/v1/*` (excepto los del decorador compartido — ver arriba):

```json
{"error": "<codigo>", "message": "<texto humano>", "details": {...opcional}}
```

| Status | `error` | Cuándo |
|---|---|---|
| 400 | `bad_request` | Payload mal formado (JSON inválido, content-type incorrecto). |
| 401 | `unauthenticated` | Token ausente, expirado o inválido. |
| 403 | `forbidden` | Rol/scope insuficiente para esa ruta. |
| 404 | `not_found` | Recurso ausente o el solicitante no es dueño legítimo (no leakeamos existencia). |
| 422 | `validation_error` | Payload válido como JSON pero rechazado por el schema. `details` lleva los campos en falla. |
| 429 | `rate_limited` | Excedió rate limit. Header `Retry-After` con segundos. |
| 500 | `internal_error` | Excepción no controlada. **No se devuelve stack trace.** Sentry registra el detalle. |

**Política de 404 vs 403:** cuando un STUDENT pide datos de otro alumno (ej: `/api/v1/attempts/<id>` ajeno), devolvemos **404**, no 403. Razón: 403 leakea que el recurso existe. 404 es más seguro y consistente con prácticas de defense in depth.

---

## 4. GDPR y restricciones legales

- La API **nunca** devuelve campos `apto`, `noApto`, `passed`, `failed`, ni cualquier shape que codifique automáticamente una decisión final. Por **GDPR art. 22**, esa decisión pertenece al cierre de la convocatoria, que es manual y con doble validación administrativa por CMadrid.
- La API **no** devuelve `withinCutoff` ni booleanos derivados que sugieran corte. El cliente puede calcular `position <= plazas` localmente si lo necesita — esa cuenta es responsabilidad del cliente, no del backend.
- Todas las respuestas respetan el scope organizacional: un usuario de la organización A no puede leer datos de la organización B (404, no 403).
- Datos de CMadrid bajo **NDA**. No pegar fixtures ni datos reales en PR descriptions, screenshots, chat público, ni servicios externos (pastebins, gists, prompts a herramientas LLM externas).

---

## 5. Endpoints

### Resumen (11 endpoints)

| Método | Path | Rol(es) | Rate |
|---|---|---|---|
| GET | `/api/v1/health` | público | 120/min |
| POST | `/api/v1/auth/login` | público | 10/min |
| POST | `/api/v1/auth/refresh` | refresh JWT | 30/min |
| GET | `/api/v1/me` | cualquier rol auth | 60/min |
| GET | `/api/v1/me/convocatorias` | cualquier rol auth | 60/min |
| GET | `/api/v1/me/convocatorias/<id>/standing` | STUDENT | 60/min |
| GET | `/api/v1/convocatorias` | MANAGER, ADMIN, SUPER_ADMIN | 60/min |
| GET | `/api/v1/convocatorias/<id>` | MANAGER, ADMIN, SUPER_ADMIN | 60/min |
| GET | `/api/v1/convocatorias/<id>/ranking` | MANAGER, ADMIN, SUPER_ADMIN | 30/min |
| GET | `/api/v1/convocatorias/<id>/matrix` | MANAGER, ADMIN, SUPER_ADMIN | 30/min |
| GET | `/api/v1/attempts/<id>` | MANAGER, ADMIN, SUPER_ADMIN — o STUDENT propio | 60/min |

### `GET /api/v1/health`

- **Auth:** público.
- **Uso:** sanity check para clientes y monitoring.
- Response 200:
  ```json
  {"status": "ok", "version": "v1", "time": "2026-04-29T12:00:00Z"}
  ```

### `GET /api/v1/me`

- **Auth:** cualquier rol con token válido.
- Response 200:
  ```json
  {
    "id": "ck...",
    "email": "manager@cmadrid.com",
    "name": "Nombre Apellido",
    "role": "MANAGER",
    "organizationId": "ck...",
    "studentProfileId": null
  }
  ```

### `GET /api/v1/me/convocatorias`

- **Auth:** cualquier rol.
- **Filtrado por rol:**
  - `STUDENT`: solo convocatorias donde tiene `Enrollment` activo.
  - `MANAGER`: convocatorias asignadas al manager.
  - `ADMIN` / `SUPER_ADMIN`: todas las de su `organizationId`.
- Response 200:
  ```json
  {
    "items": [
      {
        "id": "ck...",
        "name": "Convocatoria 2026-A",
        "description": "...",
        "status": "ACTIVE",
        "plazas": 30,
        "totalCandidates": 87,
        "closedAt": null,
        "updatedAt": "2026-04-29T10:15:00Z"
      }
    ]
  }
  ```

### `GET /api/v1/me/convocatorias/<id>/standing`

- **Auth:** `STUDENT` exclusivamente. Otros roles → 403.
- **Validación de pertenencia:** si el STUDENT no está enrolled en `<id>` → **404**.
- Response 200:
  ```json
  {
    "convocatoriaId": "ck...",
    "position": 12,
    "totalCandidates": 87,
    "plazas": 30,
    "score": 87.5,
    "attemptsCompleted": 3,
    "attemptsTotal": 3,
    "status": "COMPLETED"
  }
  ```
- **Nota legal (GDPR):** la respuesta NO incluye `withinCutoff` ni similar. El cliente puede mostrar al alumno su `position` y `plazas` por separado; cualquier cálculo de "estoy dentro" / "estoy fuera" se hace en cliente y se etiqueta visualmente como información operacional, NUNCA como decisión APTO/NO APTO.

### `GET /api/v1/convocatorias`

- **Auth:** `MANAGER`, `ADMIN`, `SUPER_ADMIN`.
- Response 200: igual shape que `/me/convocatorias`.

### `GET /api/v1/convocatorias/<id>`

- **Auth:** `MANAGER`, `ADMIN`, `SUPER_ADMIN`.
- Response 200: un solo `ConvocatoriaSummary`.

### `GET /api/v1/convocatorias/<id>/ranking`

- **Auth:** `MANAGER`, `ADMIN`, `SUPER_ADMIN`. STUDENT → 403.
- Response 200:
  ```json
  {
    "convocatoria": { "id": "ck...", "name": "...", "...": "..." },
    "entries": [
      {
        "position": 1,
        "candidate": {"id": "ck...", "name": "Apellido, Nombre", "plaza": null},
        "score": 95.3,
        "attemptsCompleted": 3,
        "attemptsTotal": 3
      }
    ]
  }
  ```
- **Nota:** `RankingEntry` NO incluye `withinCutoff`.

### `GET /api/v1/convocatorias/<id>/matrix`

- **Auth:** `MANAGER`, `ADMIN`, `SUPER_ADMIN`.
- Response 200:
  ```json
  {
    "convocatoria": { "id": "ck...", "name": "...", "...": "..." },
    "circuits": [{"id": "R01", "label": "Salida cochera"}],
    "rows": [
      {
        "candidate": {"id": "ck...", "name": "..."},
        "scores": [{"circuitId": "R01", "score": 8.4}, {"circuitId": "R02", "score": null}]
      }
    ]
  }
  ```

### `GET /api/v1/attempts/<id>`

- **Auth:** `MANAGER`, `ADMIN`, `SUPER_ADMIN` siempre. `STUDENT` solo si `attempt.studentId == current_user.id`. Si STUDENT y no es propio → **404**.
- Response 200:
  ```json
  {
    "id": "ck...",
    "candidate": {"id": "ck...", "name": "..."},
    "route": {"id": "R01", "label": "Salida cochera"},
    "score": 87.5,
    "dataQuality": "ok",
    "scoreBreakdown": [
      {"family": "estabilidad", "obtained": 24, "max": 30},
      {"family": "velocidad", "obtained": 20, "max": 25}
    ],
    "events": [
      {
        "type": "harsh_brake",
        "severity": "high",
        "confidence": 0.93,
        "description": "Frenada brusca en intersección",
        "timestamp": "2026-04-28T14:23:11Z"
      }
    ],
    "convocatoriaId": "ck..."
  }
  ```

---

## 6. Ejemplos curl

### Login + me

```bash
# Login
curl -sS -X POST https://training.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alumno@cmadrid.com", "password": "..."}'

# Tomá el access_token de la respuesta y úsalo
ACCESS=eyJ...

curl -sS https://training.example.com/api/v1/me \
  -H "Authorization: Bearer $ACCESS"
```

### Refresh

```bash
REFRESH=eyJ...

curl -sS -X POST https://training.example.com/api/v1/auth/refresh \
  -H "Authorization: Bearer $REFRESH"
```

### Standing del alumno

```bash
curl -sS https://training.example.com/api/v1/me/convocatorias/ck123/standing \
  -H "Authorization: Bearer $ACCESS"
```

---

## 7. Glosario

| Término | Significado |
|---|---|
| **convocatoria** | Cohorte de oposición pública bajo CMadrid. Tiene plazas, candidatos y status (ACTIVE / CLOSING / CLOSED). |
| **standing** | Posición individual de un STUDENT en una convocatoria. Self-referencial ("mi posición"), nunca lista. |
| **ranking** | Lista ordenada de TODOS los candidatos de una convocatoria. Solo MANAGER/ADMIN. |
| **matrix** | Vista 2D (candidatos × circuitos) con sus scores. Solo MANAGER/ADMIN. |
| **attempt** / **intento** | Una corrida individual de un STUDENT en un circuito de la convocatoria. |
| **plaza** | Cupo disponible en la convocatoria. CMadrid asigna al cierre formal. |
| **STUDENT propio** | En `/attempts/<id>`: el STUDENT cuyo `studentId` coincide con `attempt.studentId`. |

---

## 8. Anti-creep — explícitamente FUERA de scope de v1

- Apps nativas iOS / iPadOS / macOS / watchOS (clientes — su contrato es ESTE doc, pero el código de los clientes no vive acá).
- Cualquier endpoint de escritura de dominio (POST/PUT/PATCH/DELETE).
- Cierre de convocatoria desde móvil.
- Reproceso de scoring desde móvil.
- Cualquier campo que codifique `apto` / `no_apto` / `passed` / `failed` / `withinCutoff`.
- Refactor de `app/utils/decorators.py` o `app/middleware/`.
- Migración de queries de `manager` a `app/services/training/*`.
- OpenAPI auto-generado / Flask-Smorest / Flask-RESTful.
- factory_boy para tests.
- CI en GitHub Actions.
- CORS (clientes nativos no usan CORS).
- JTI denylist / refresh rotation / endpoint de logout móvil.
- Geometrías PostGIS expuestas en payloads.
- `GET /enrollments/<id>` (cubierto por `attempts` + `ranking`).
- Roles `OPERATOR` y `VIEWER` (legacy, ignorados).

---

## 9. Owners y contacto

- **Backend:** Jesús (`@Eldur4023`).
- **Contrato API / aprobador:** Antonio (`@hermoso92`).
- **Cliente iOS (planificado):** Antonio.
- **Tests integración:** Joel.

Para cualquier propuesta de cambio del contrato (campo nuevo, endpoint nuevo): abrir issue con label `mobile-api` y mencionar `@hermoso92`.

---

## 10. Historial de versiones

- **v1.0** (2026-04-29): contrato inicial. 11 endpoints read-only. Sin `withinCutoff`. JWT dual-mode cookies+headers.
