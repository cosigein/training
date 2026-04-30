# D-FE-001 — Frontend con dos layouts conviviendo

**Fecha:** 2026-04-29
**Status:** PENDIENTE DE RESOLVER (decisión de Alejandro + Antonio antes del 09/05)
**Detectado por:** Antonio durante inspección browser del día 2 del sprint

---

## Hecho observado

Hoy el portal tiene **dos sistemas de layout/branding** distintos según la ruta:

### Layout NUEVO — top-nav blanco, branding "CMadrid Training"
Activo en `/manager/*`. Templates en `app/templates/manager/`.

### Layout VIEJO — sidebar oscuro, branding "DOBACKSOFT"
Activo en `/sessions/`, `/admin/*`, `/vehicles/`, `/events/`. Heredado del proyecto previo `dobackv2-main` (TS/Node, ya descartado).

## Síntomas concretos

1. Tras login con MANAGER, el redirect default va a `/sessions/` (sidebar viejo "DOBACKSOFT") en vez de a `/manager/` (top-nav nuevo).
2. CMadrid (cliente bajo NDA) vería el branding **DOBACKSOFT** durante la demo del 11/05 si navega esas rutas.
3. `/admin/convocatorias` (CRUD completo, layout viejo) y `/manager/convocatorias` (read-only, layout nuevo) son la misma información en dos UIs distintas.
4. El botón "Salir" del top-nav nuevo apunta a `/auth/login` (no hace logout); el sidebar viejo va a `/auth/logout`.
5. `<title>` de la página: páginas viejas dicen `- DobackSoft`, nuevas dicen `— CMadrid Training`.

## Por qué pasó

El proyecto Training es la **reescritura en Flask/Python** del producto previo `dobackv2-main` (TS/Node/React).
- El layout viejo (sidebar) viene de templates portados desde Doback al Flask sin rebrand.
- El layout nuevo (top-nav) lo armó Alejandro recientemente para el portal manager.
- No se decidió formalmente si migrar lo viejo o deprecarlo.

## Opciones a evaluar

| Opción | Esfuerzo | Resultado |
|---|---|---|
| **A. Migrar lo viejo al layout nuevo** | Alto (8-16h Alejandro) | UX uniforme, mejor para demo. CMadrid no ve "DOBACKSOFT" |
| **B. Migrar lo nuevo al layout viejo** | Medio (4-8h) | Pero el viejo dice "DOBACKSOFT" → no aceptable bajo NDA |
| **C. Deprecar rutas viejas duplicadas con `/manager/`** | Bajo (2-4h) | `/admin/*` se mantiene para CRUD que NO está en manager; resto se redirige a `/manager/` |
| **D. Solo cambiar branding "DOBACKSOFT" → "CMadrid Training" en sidebar viejo** | Trivial (1h) | Mitiga el riesgo NDA pero no resuelve la inconsistencia visual |

## Recomendación (Antonio, no oficial)

Combo **D + C**:
1. Cambiar el string "DOBACKSOFT" del sidebar viejo a "CMadrid Training" inmediatamente (1h, riesgo bajo, mitiga lo crítico para demo).
2. Deprecar `/admin/convocatorias` viejo (queda solo `/manager/convocatorias` + el CRUD que falte se agrega ahí).
3. Migración completa del layout viejo al nuevo se difiere a Fase 2 post-demo.

Esto NO compromete el sprint ni la demo del 11/05.

## Referencias

- Screenshots del estado actual: `/tmp/playwright-output/0[1-7]-*.png` (efímeros, regenerar con browser MCP si hace falta).
- `docs/STATE-2026-04-29.md` §4 — "Frontend findings".
- `docs/STYLE-GUIDE-MANAGER.md` — guía de estilo del layout NUEVO (Alejandro).
- Templates afectados:
  - Nuevos: `app/templates/manager/{layout,dashboard,convocatorias,matriz,ranking,alumno,intento,auditoria}.html`
  - Viejos: `app/templates/base.html`, `app/blueprints/*/templates/*` (sessions, vehicles, events, admin)

## Action items

- [ ] **Antonio + Alejandro** — decidir opción antes del 02/05.
- [ ] **Alejandro** — implementar la opción elegida antes del 09/05.
- [ ] **Joel** — agregar tests E2E que validen branding consistente en todas las rutas.
