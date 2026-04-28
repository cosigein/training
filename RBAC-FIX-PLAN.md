# Plan de fix: separación de roles ADMIN vs MANAGER

> **Objetivo:** que `manager@cmadrid.com` vea y pueda hacer lo MISMO que en `dobackv2-main`, ni más ni menos.
> **Estimado total:** 2–3 horas de curro real.
> **Estado HOY:** roto. Manager y admin ven lo mismo. Manager puede borrar sesiones del admin (eso ya está LIVE).

---

## 0. TL;DR de lo que está mal

1. **`base.html`** muestra el MISMO sidebar para todo usuario logueado. No hay un solo `{% if %}` por rol.
2. **Solo 2 endpoints** tienen `@require_role(["ADMIN"])` (`/admin/users`, `/admin/organizations`). Todo lo demás solo pide JWT + org → cualquier MANAGER pasa.
3. **Regresión crítica:** `DELETE /sessions/<id>` (lo que arreglamos ayer) NO tiene rol → manager borra recorridos.

---

## 1. Matriz de roles (lo que decidimos hoy)

> Basado 1:1 en lo que MANAGER veía en `dobackv2-main` (`frontend/src/components/Navigation.tsx` + `routes.tsx`). Si Antonio define algo distinto, ajustar esta tabla y propagar.

### UI — sidebar (`base.html`)

| Ítem del menú | MANAGER | ADMIN | Notas |
|---|:---:|:---:|---|
| Dashboard (`kpis`) | ✅ | ✅ | — |
| Gestión Flota (`vehicles`) | ✅ (read) | ✅ (CRUD) | manager VE; no crea ni edita |
| Rutas / Recorridos (`sessions`) | ✅ (read) | ✅ (read + DELETE) | manager NO borra |
| Gestor de Eventos (`events`) | ✅ | ✅ | ack permitido a ambos |
| Reportes (`reports`) | ❌ | ✅ | admin-only en el viejo |
| KPIs Avanzados | ✅ | ✅ | placeholder |
| Ingesta (`uploads`) | ❌ | ✅ | admin-only en el viejo |
| Administración (`admin`) | ❌ | ✅ | obvio |
| Configuración (`system`) | ✅ | ✅ | cada uno la propia |
| Salir | ✅ | ✅ | — |

### Backend — endpoints (decoradores Flask)

| Endpoint | Decorador objetivo |
|---|---|
| `GET /sessions/`, `GET /sessions/<id>`, `GET /sessions/<id>/gps` | `@require_role(["ADMIN", "MANAGER"])` |
| **`DELETE /sessions/<id>`** | `@require_role(["ADMIN"])` |
| `GET /vehicles/`, `GET /vehicles/<id>` | `@require_role(["ADMIN", "MANAGER"])` |
| `POST /vehicles/`, `PATCH /vehicles/<id>`, `DELETE /vehicles/<id>` | `@require_role(["ADMIN"])` |
| `GET /events/` | `@require_role(["ADMIN", "MANAGER"])` |
| `POST /events/<id>/acknowledge` | `@require_role(["ADMIN", "MANAGER"])` |
| `GET /kpis/dashboard` | `@require_role(["ADMIN", "MANAGER"])` |
| `GET /reports/*`, `POST /reports/*` | `@require_role(["ADMIN"])` |
| `GET /uploads/*`, `POST /uploads/upload` | `@require_role(["ADMIN"])` |
| `GET /geofences/*`, mutaciones | `@require_role(["ADMIN"])` |
| `GET /telemetry/live` | `@require_role(["ADMIN"])` |
| `GET /system/settings` | `@require_role(["ADMIN", "MANAGER"])` (cada uno ve la propia) |
| `GET /admin/users`, `GET /admin/organizations` | `@require_role(["ADMIN"])` (ya está) |

---

## 2. Cambios concretos

### 2.1 Sidebar — `app/templates/base.html`

Reemplazar el bloque `<nav class="sidebar__nav">` por esto:

```jinja
<nav class="sidebar__nav">
    <a href="{{ url_for('kpis.dashboard_executive') }}"
       class="sidebar__link {% if request.blueprint == 'kpis' %}active{% endif %}">
        <i class="ph ph-layout"></i> Dashboard
    </a>
    <a href="{{ url_for('vehicles.list_vehicles') }}"
       class="sidebar__link {% if request.blueprint == 'vehicles' %}active{% endif %}">
        <i class="ph ph-truck"></i> Gestión Flota
    </a>
    <a href="{{ url_for('sessions.list_sessions') }}"
       class="sidebar__link {% if request.blueprint == 'sessions' %}active{% endif %}">
        <i class="ph ph-map-pin-line"></i> Rutas / Recorridos
    </a>
    <a href="{{ url_for('events.list_events') }}"
       class="sidebar__link {% if request.blueprint == 'events' %}active{% endif %}">
        <i class="ph ph-warning-circle"></i> Gestor de Eventos
    </a>
    <a href="#" class="sidebar__link">
        <i class="ph ph-chart-bar"></i> KPIs Avanzados
    </a>

    {% if current_user.role.value == 'ADMIN' %}
    <a href="{{ url_for('reports.list_reports') }}"
       class="sidebar__link {% if request.blueprint == 'reports' %}active{% endif %}">
        <i class="ph ph-file-text"></i> Reportes
    </a>
    <a href="{{ url_for('uploads.unified_upload') }}"
       class="sidebar__link {{ 'active' if request.blueprint == 'uploads' }}">
        <i class="ph ph-cloud-arrow-up"></i> Ingesta
    </a>
    <a href="{{ url_for('admin.list_organizations') }}"
       class="sidebar__link {{ 'active' if request.blueprint == 'admin' }}">
        <i class="ph ph-shield-check"></i> Administración
    </a>
    {% endif %}
</nav>
```

> **Patrón:** `current_user.role` es un `Enum`, así que se compara contra `.value`. Si dudás, en una vista poné `{{ current_user.role.value }}` y mirá qué imprime.

> **Anti-patrón a evitar:** poner el `{% if %}` solo alrededor del enlace de "Administración" pensando que ya está. Hay 3 ítems que son admin-only: Reportes, Ingesta, Administración. Los 3 dentro del mismo `{% if %}`.

### 2.2 Decoradores en blueprints

> El decorador `require_role` ya existe en `app/utils/decorators.py:6`. NO reinventarlo.
> Importarlo en cada `routes.py` que lo use.

#### `app/blueprints/sessions/routes.py`

```python
from app.utils.decorators import jwt_required, get_jwt_identity, require_org, require_role

@sessions_bp.route("/", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def list_sessions():
    ...

@sessions_bp.route("/<string:id>", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def get_session_detail(id):
    ...

@sessions_bp.route("/<string:id>", methods=["DELETE"])
@require_role(["ADMIN"])     # ← era @require_org. CAMBIAR.
def delete_session(id):
    ...

@sessions_bp.route("/<string:id>/gps", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def get_session_gps(id):
    ...
```

> **Importante:** `require_role` YA llama a `jwt_required()` y `require_org` adentro. NO encadenar los tres decoradores — basta con uno. Ver `app/utils/decorators.py` líneas 11-14.

#### Resto de blueprints

Mismo patrón:
- `vehicles/routes.py` → GET con `["ADMIN", "MANAGER"]`, POST/PATCH/DELETE con `["ADMIN"]`
- `events/routes.py` → todo `["ADMIN", "MANAGER"]`
- `kpis/routes.py` → `["ADMIN", "MANAGER"]`
- `reports/routes.py` → `["ADMIN"]`
- `uploads/routes.py` → `["ADMIN"]`
- `geofences/routes.py` → `["ADMIN"]`
- `telemetry/routes.py` → `["ADMIN"]`
- `system/routes.py` → `["ADMIN", "MANAGER"]`
- `admin/routes.py` → ya está bien, `["ADMIN"]`

### 2.3 Mensaje de error consistente

`require_role` devuelve `403 {"message": "Permisos insuficientes"}` cuando rechaza. Eso aplica a peticiones JSON. Para peticiones del navegador (sin `Accept: application/json`), debería redirigir a una página de "no tenés permiso" o al dashboard.

**Fix opcional pero recomendado** — modificar `require_role` para distinguir HTML vs JSON, igual que ya hicimos con los handlers de JWT:

```python
# app/utils/decorators.py
from flask import request, redirect, url_for, flash, jsonify

def _wants_json():
    if request.is_json: return True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest': return True
    accept = request.headers.get('Accept', '')
    if 'text/html' in accept: return False
    if 'application/json' in accept: return True
    return False

def require_role(roles):
    if isinstance(roles, str):
        roles = [roles]
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                if _wants_json():
                    return jsonify({"message": "Usuario no encontrado"}), 404
                return redirect(url_for('auth.login'))
            user_role = user.role.value if hasattr(user.role, 'value') else user.role
            if user_role not in roles:
                if _wants_json():
                    return jsonify({"message": "Permisos insuficientes"}), 403
                flash("No tenés permisos para acceder a esa sección.", "warning")
                return redirect(url_for('kpis.dashboard_executive'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

## 3. Orden de ejecución (cómo trabajar las próximas 3 horas)

> Hacer EN ESTE ORDEN. Saltearse pasos = bugs en cascada.

1. **Backup mental:** `git status` limpio antes de empezar. Crear rama `feat/rbac-roles`.
2. **Decoradores en `sessions` primero** (es el blueprint más crítico — DELETE va a admin). Probar con manager y admin.
3. **`vehicles`, `events`, `kpis`** — los que MANAGER necesita ver.
4. **`reports`, `uploads`, `geofences`, `telemetry`** — los admin-only. Probar que MANAGER recibe 403/redirect.
5. **`base.html`** — gating del sidebar. Esto VISUALIZA todo lo anterior.
6. **`require_role` con redirect HTML** (sección 2.3) — opcional pero limpia mucho la UX.
7. **Manual smoke test** (sección 4 abajo).
8. **PR.** Antonio review obligatorio porque toca middleware (regla del repo, ver `CONTRIBUTING.md`).

---

## 4. Smoke test manual (5 minutos)

> Hacelo siempre con DOS pestañas privadas distintas, una con manager, otra con admin. Si tenés una sola, el JWT cookie te confunde.

### Como MANAGER (`manager@cmadrid.com` / `manager123`)
- [ ] Login OK, redirige al dashboard.
- [ ] Sidebar **NO muestra** "Reportes", "Ingesta", "Administración".
- [ ] Sidebar **SÍ muestra** Dashboard, Flota, Rutas, Eventos, KPIs, Configuración.
- [ ] Click en "Rutas / Recorridos" → ve el listado.
- [ ] El botón de basurero (DELETE) → debe responder 403 `{"message": "Permisos insuficientes"}`. La fila NO se borra.
- [ ] Tipear en URL `/admin/users` → 403 / redirect.
- [ ] Tipear en URL `/uploads` → 403 / redirect.

### Como ADMIN (`admin@cmadrid.com` / `admin123`)
- [ ] Sidebar muestra los 9 ítems.
- [ ] Borrar sesión → la fila desaparece (204).
- [ ] Acceder a `/admin/users` → 200 con la lista.
- [ ] Acceder a `/uploads` → 200.

---

## 5. Cosas que NO entran en este fix (Phase 2 / fuera de scope)

- **Features faltantes** que el viejo tenía y MANAGER usaba en su escena: stability analysis, AI/FleetMind, training admin, observability, knowledge base. **No se reconstruyen acá.** Si se decide migrarlos, abrir issues separados.
- **Permisos granulares por organización config** (`formacionHabilitada`, `viewMode`). El viejo tenía permisos finos basados en flags de la org. Por ahora se posterga — siempre se pueden agregar arriba del decorador de rol.
- **Audit log** de denegaciones. El viejo loggeaba intentos de acceso fallidos. Útil pero no urgente para el sprint.

---

## 6. Reglas firmes que aplican a partir de este fix

1. **Cada endpoint nuevo lleva un decorador de rol explícito.** No "se asume que MANAGER puede" — se escribe.
2. **Sidebar y backend siempre alineados.** Si agregás un ítem visible para MANAGER, el endpoint también tiene que estar en la lista de roles permitidos. Y al revés.
3. **`require_role` es el ÚNICO punto de chequeo.** No mezclar con `if user.role == ...` adentro de la view — duplica lógica y se desincroniza.
4. **Tests E2E con dos roles** cuando exista la suite (Joel). Hasta entonces, el smoke test manual de §4 es obligatorio antes de mergear cualquier cambio en `routes.py` o `base.html`.

---

**Cuando termines el fix, actualizá esta línea con la fecha:** `[ ] Aplicado y verificado: ___ / ___ / 2026 por ___`.
