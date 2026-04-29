# Decisión D-API-001 — API móvil V1 read-only por fases

**Tipo**: decision
**Autor**: Antonio
**Fecha**: 2026-04-29

## Qué

Training se diseña como **plataforma con backend común y clientes múltiples**, no como "una web con app añadida". Sobre el backend Flask existente se publica una **API JSON `/api/v1/*` read-only** consumible por clientes nativos (Apple SwiftUI / Watch en planificación). El portal web Jinja sigue siendo el cliente principal y NO se reescribe.

La implementación se hace **por fases**, no en paralelo simultáneo:

- **Fase 0** (hoy → demo Madrid 11/05): cero Xcode. Doc del contrato + auth dual-mode (cookies+headers) + observabilidad mínima (Loguru/Sentry). Tres PRs pequeños, sin robar foco al sprint del demo.
- **Fase 1** (post-demo, ~12/05 → ~25/05): blueprint `app/blueprints/mobile_api/` con 11 endpoints read-only (auth, me, convocatorias, ranking, matrix, attempt detail), Marshmallow schemas, integration tests mínimos.
- **Fase 2** (post-Fase 1, ~26/05 →): proyecto Xcode SwiftUI en `/Users/antoniohermoso/IOS/Dobacksoft Training` consumiendo la API. iPhone primero (Login + Dashboard + Convocatorias), luego iPad/Mac.
- **Fase 3** (después): Apple Watch como resumen ligero (notificación + último score + convocatoria activa). NO una app completa.

## Por qué

Pensar "¿cómo le doy esto a un cliente nativo?" reveló deuda técnica del backend que duele igual aunque iOS no exista:

- No hay capa de servicios reutilizable (lógica vive en `routes.py` + `services.py` por blueprint, ad-hoc).
- No hay DTOs (Marshmallow está en `requirements.txt` pero CERO schemas activos).
- No hay API REST coherente (solo `/auth/login`, `/auth/me`, `/auth/refresh` y unos endpoints `admin/`).
- `JWT_TOKEN_LOCATION = ["cookies"]` solo soporta navegadores — un cliente nativo no puede consumirlo.
- Cero tests, cero CI.

La API móvil es la excusa correcta para limpiar esa deuda **sin** cargarla a la web actual: el blueprint `/api/v1/*` es aditivo, el portal web sigue funcionando con cookies sin tocar nada.

El **timing por fases** existe porque a 12 días del demo CMadrid no se puede repartir el foco del director técnico (Antonio) entre dos productos cuando el primero todavía no está cerrado. Fase 0 son 3 PRs pequeños y compatibles con el sprint; Fase 1 espera al post-demo.

## Dónde aplica

- **Backend**: nuevo `app/blueprints/mobile_api/{__init__.py, routes.py, schemas.py, services.py, errors.py}` (Fase 1). Tocan `app/config.py` (1 línea) y `app/__init__.py` + `app/extensions.py` (Loguru/Sentry) en Fase 0.
- **Reuso**: `app/blueprints/manager/ranking_service.py` se importa directo desde `mobile_api/services.py` (sin mover queries a `app/services/training/*` durante el sprint).
- **Doc canónica**: `docs/MOBILE-API.md` — contrato V1, política de versionado, errores estándar, GDPR note, anti-creep list.
- **Cliente nativo (futuro)**: `/Users/antoniohermoso/IOS/Dobacksoft Training` — proyecto Xcode SwiftUI (Fase 2+), fuera de este repo.

## Cómo aplicarlo

- **Versionado desde día 1**: URLs con prefix `/api/v1/...`. Cambios non-breaking OK; cambios breaking → `/api/v2/...`. Sin `-beta`.
- **Auth dual-mode**: `JWT_TOKEN_LOCATION = ["cookies", "headers"]` global. Web sigue cookie + CSRF; nativo usa `Authorization: Bearer`. **Regla nueva no-negociable**: el JS del portal web NUNCA envía `Authorization: Bearer` — si lo hiciera, saltearía CSRF.
- **Serialización**: Marshmallow puro (sin `marshmallow-sqlalchemy`, sin Pydantic, sin `to_dict()`). Schemas con escalares y listas planas — nunca `fields.Nested` con relaciones lazy de SQLAlchemy.
- **Estructura**: blueprint Flask plano. NO Flask-Smorest, NO Flask-RESTful. Consistente con los otros 12 blueprints del repo.
- **Tests**: `app.test_client()` + SQLAlchemy directo en conftest. Sin factory_boy. 6 integration tests mínimos cubriendo auth, me, standing, ranking, attempt-owner check, health.
- **GDPR (no negociable)**: la API NUNCA devuelve `apto`/`no_apto`/`passed`/`failed`/`withinCutoff` ni shape que sugiera decisión final. El cliente puede calcular `position <= plazas` localmente — el backend no lo expone. Cumple GDPR art. 22 (revisión humana significativa, ver `arquitectura-invariantes.md`).
- **Roles**:
  - `STUDENT` ve solo su PROPIA posición (`/api/v1/me/convocatorias/<id>/standing`), nunca lista de otros.
  - `MANAGER` / `ADMIN` / `SUPER_ADMIN` (incluye SUPER_ADMIN equiparado a ADMIN) ven ranking completo, matrix, lista de convocatorias.
  - 404 (no 403) cuando un STUDENT pide datos ajenos — defense in depth, no leakeamos existencia.
- **Refresh tokens**: 1h access / 30d refresh. **Sin rotation, sin revocation list**. Deuda asumida y documentada en `docs/MOBILE-API.md`. Si CMadrid lo exige, change separado post-V1.
- **Sin escritura en V1**: cero endpoints `POST/PUT/PATCH/DELETE` de dominio. Únicas excepciones son `POST /auth/login` y `POST /auth/refresh`. Cierre de convocatoria, scoring reprocess y exports legales **NUNCA** desde móvil.

## Aprendido

- El "no quiero WebView" + "no quiero scraping" + "Jinja SSR" descarta automáticamente PWA encima del web actual. La opción honesta para "iPhone en demo" es **Safari abriendo el VPS** con CSS responsivo (cero código nuevo) — eso es lo que se proyecta el 11/05 si se hace falta.
- El SDD orchestrator hizo visible la deuda técnica antes de que el equipo la sintiera en producción. La fase de exploración encontró 5 gaps entre proposal y código (servicios sin filtro por rol, naming español/camelCase, etc.) que se resuelven en Fase 1 sin sorpresas.
- Lanzar sub-agentes en background con operaciones de git en paralelo al orquestador en el mismo working tree **causa colisión de HEAD**. Lección quemada el 2026-04-29 con `feat/be-loguru-sentry-init`. Patrón seguro: o sub-agente sin git, o git en serie, o `git worktree add` para procesos separados.
- `withinCutoff` (bool "estoy dentro de plazas") era candidato a campo, se descartó por riesgo GDPR. Cualquier campo cuya semántica pueda leerse como "APTO/NO APTO" es candidato a auditoría legal antes de exponerlo.

## Cuándo se invalidaría

- Si CMadrid pide explícitamente que el sistema decida APTO/NO APTO automáticamente desde móvil → invalidaría toda la decisión legal. Improbable (D-MT-001 + GDPR art. 22 son invariantes confirmados con cliente).
- Si Apple Developer Program no estuviera disponible para distribuir el cliente nativo a CMadrid → Fase 2 quedaría bloqueada y se cancelaría iOS. La API V1 sigue valiendo (la consume cualquier cliente, incluso un dashboard interno de Joel).
- Si post-demo el equipo creciera con un dev frontend dedicado a React/Next y se priorizara reescritura del web → la API V1 igualmente sirve, no se invalida.

## Referencias

- Contrato técnico: [`docs/MOBILE-API.md`](../docs/MOBILE-API.md)
- Invariantes que la API respeta: [`arquitectura-invariantes.md`](arquitectura-invariantes.md)
- Modelo de oposición pública (no-auto APTO/NO APTO): [`modelo-oposicion-publica.md`](modelo-oposicion-publica.md)
- Artefactos SDD vivos en engram (project `training`): topic_keys `sdd/mobile-api-v1-foundation/{explore, proposal, spec, design, tasks, apply-progress, scope-constraints, micro-decisions}`
