# Frontend Analysis & Brainstorming — DobackV2 Training
> Fecha: 2026-05-05 | Analizador: Antigravity  
> Comparado contra: `PAPER-MAESTRO.md` (v6), `STYLE-GUIDE-MANAGER.md`, `LEAD-DASHBOARD.md`

---

## 1. Estado Real del Frontend — Inventario

### 1.1 Portales existentes

| Portal | Layout | Pantallas implementadas | Estado |
|--------|--------|------------------------|--------|
| **Manager** | `manager/layout.html` | dashboard, convocatorias, matriz, ranking, alumno, intento, auditorias, auditoria_detalle | ✅ Completo para demo |
| **Student (Alumno)** | `student/layout.html` | dashboard, historial, intento, evolucion, solicitar_auditoria, sin_inscripciones | ✅ Completo para demo |
| **Kiosko** | Sin layout propio | login, rutas, intento | ✅ Mínimo funcional |
| **Admin** | `admin/layout.html` | dashboard, convocatorias, cierre, simulador, matriz, gdpr, usuarios | ✅ Más completo de lo esperado |
| **Base (Legacy)** | `base.html` | sidebar DOBACKSOFT con rutas admin legacy | ⚠️ Layout viejo sin deprecar |

### 1.2 Assets CSS/JS

| Archivo | Rol | Estado |
|---------|-----|--------|
| `tokens.css` | Design tokens globales | ✅ Correcto pero **inconsistente con el style guide** |
| `reset.css` | Normalización | ✅ OK |
| `base.css` | Tipografía base | ✅ OK |
| `manager.css` | Estilos portal manager | ✅ 42KB — muy denso |
| `alumno.css` | Estilos portal alumno | ✅ 31KB |
| `kiosko.css` | Estilos kiosko | ✅ OK |
| `admin.css` | Estilos admin | ✅ 20KB |
| `layout.css` | Utilidades layout | ✅ OK |
| `components/` | Componentes atómicos | ✅ 7 archivos |
| `js/main.js` | JS global | ⚠️ 185 bytes — casi vacío |
| `js/manager.js` | JS del manager | ⚠️ 149 bytes — casi vacío |

---

## 2. Gaps: Spec vs Realidad

### 2.1 🔴 CRÍTICO — Pantallas completamente ausentes o incompletas

#### Portal Admin — D5 Cierre de Convocatoria (3 pasos)
**Spec PAPER-MAESTRO §9.6 — D5:**
> "El cierre es un proceso secuencial de 3 pasos: Preview → Initiate → Confirm. La misma URL muestra UNO de los tres estados."

**Realidad:** `admin/cierre.html` existe (29KB) y parece implementar los 3 estados. **Sin verificar si el flujo real de endpoints está conectado** (`/close/preview`, `/close/initiate`, `/close/confirm`, `/close/abort`, `/close/reverse`).

#### Portal Admin — D6 Simulador con dimensión de Ranking
**Spec §9.6 — D6:**
> "`ScoringSimulator.tsx` — v5 con ranking dimension"

**Realidad:** `admin/simulador.html` existe (16KB). Se desconoce si llama al endpoint `/scoring/simulate` con dimensión de ranking completa (reordenamiento visual + candidatos que cruzan el corte).

#### Manager — M4 Matriz: Data Quality (HQ/LQ) invisible
**Spec §9.4 — M4:**
> "Cada celda muestra la nota + calidad: `8.8 HQ ✓` / `5.8 LQ ⚠`"

**Realidad:** `manager/matriz.html` muestra la nota y el ícono de auditoría, pero **NO muestra el badge de data_quality** (HIGH/MEDIUM/LOW) en cada celda. La spec dice explícitamente que "HQ ✓" y "LQ ⚠" deben ser visibles.

#### Manager — Acciones de auditoría DESDE el Ranking
**Spec §9.4 — M5:**
> "Click ⚠ (auditoría) → modal con auditoría pendiente"

**Realidad:** `manager/ranking.html` solo filtra por "Con auditoría" pero no tiene modal. Redirige a `alumno_detalle`. No hay interacción inline en el ranking.

#### Portal Alumno — A3 Historial: columna Calidad y Auditoría
**Spec §9.5 — A3:**
> "FECHA · RUTA · NOTA · CALIDAD · AUDITORÍA"

**Realidad:** `student/historial.html` no fue revisado en detalle — comprobar si muestra la columna de calidad de datos.

### 2.2 🟡 INCOMPLETO — Implementado pero parcial

#### Kiosko `intento.html` — Estilos inline masivos
**Style Guide §5:**
> "No escribas estilos inline en las templates Jinja. Toda variación visual debe tener su propia clase modificadora."

**Realidad:** `kiosko/intento.html` tiene **docenas de estilos inline** hardcodeados: `style="font-size:42px;"`, `style="display:flex; align-items:center; gap:20px;"`, `style="background:#0d1527; border:..."` etc. **Violación directa y sistemática de la guía de estilos.**

#### Dashboard Manager — Convocatorias sin botones [VER MATRIZ] [VER RANKING]
**Spec §9.4 — M2:**
> "Convocatorias: `[VER MATRIZ]` + `[VER RANKING]`"

**Realidad:** `manager/dashboard.html` — las tarjetas de convocatoria son clickables al completo pero **no tienen los dos botones separados** para Matriz y Ranking. Un solo click lleva a la Matriz. El Ranking no tiene acceso directo desde aquí.

#### base.html — Layout legacy con sidebar DOBACKSOFT activo
**LEAD-DASHBOARD §3 — Riesgo #2:**
> "Frontend con branding 'DOBACKSOFT' en sidebar viejo. CMadrid bajo NDA NO debería ver eso."

**Realidad:** `base.html` sigue teniendo el sidebar con `CMadridTraining` pero aún referencia blueprints legacy (`sessions`, `vehicles`, `events`, `uploads`, `admin.list_organizations`) con rutas que pueden no existir o mostrar UI vieja. **El D-FE-001 no está completamente resuelto** — `base.html` sigue siendo el layout activo para los blueprints admin legacy.

#### manager/intento.html — MapViewer es placeholder
**Spec §9.4 — M6:**
> "`<MapViewer>` ruta + eventos"

**Realidad:** El mapa muestra un placeholder con ícono y texto *"MapViewer disponible en integración con datos reales"*. Correcto para la fase actual, pero debe estar en el radar.

#### solicitar_auditoria.html — form con `method="get"` 
**Realidad:** El formulario usa `method="get"` en lugar de `method="post"`. Esto expone la razón de la auditoría en la URL. **Bug de seguridad / UX.**

### 2.3 🟢 BIEN IMPLEMENTADO — Coincide con spec

| Item | Spec | Realidad |
|------|------|----------|
| Ranking provisional con corte visual | §9.4 — M5 | ✅ `ranking.html` con `mgr-cut-row` |
| StandingCard (dentro/fuera del corte) | §9.5 — A2 | ✅ `student/dashboard.html` con `.alu-estado--pass/fail` |
| Score breakdown con barras animadas | §9.4 — M6 | ✅ `manager/intento.html` |
| Timeline de eventos con confidence | §9.4 — M6 | ✅ Implementado con `ev.confidence` |
| Auditoría detalle con resolución M7 | §9.4 — M7 | ✅ `auditoria_detalle.html` |
| Formulario solicitud auditoría A5 | §9.5 — A5 | ✅ `solicitar_auditoria.html` (excepto method=get) |
| Filtros por categoría en Matriz | §9.4 — M4 | ✅ Pills Todos/Aprobados/Suspensos |
| Kiosko dark mode | §9.2 regla 6 | ✅ `ksk-root` dark theme |
| Ranking con posiciones oro/plata/bronce | Style Guide §4.7 | ✅ `.mgr-pos--gold/silver/bronze` |
| Nota media con 2 decimales | — | ✅ `"%.2f"` en ranking |

---

## 3. Violaciones a la Style Guide

### 3.1 Tokens inconsistentes (crítico)

**Style Guide §2** declara:
```css
--color-bg: #f0f4f8       /* fondo de página */
--color-surface: #ffffff  /* cards */
--color-border: #e2e8f0
--font-body: Inter, sans-serif
--font-heading: Inter, sans-serif (700)
```

**Realidad en `tokens.css`:**
```css
--color-bg-body: #f5f7fa   /* diferente nombre Y valor */
--font-body: 'Source Sans 3'  /* ≠ Inter */
--font-heading: 'Plus Jakarta Sans'  /* ≠ Inter */
```

**Las fuentes son distintas al style guide.** El guide dice Inter, el código usa Plus Jakarta Sans + Source Sans 3. Esto no es necesariamente malo (es una decisión válida), pero hay una **discordancia documental**.

### 3.2 Estilos inline en Kiosko

Conteo aproximado de bloques `style=""` en `kiosko/intento.html`: **~20 instancias**.  
Todos deberían ser clases en `kiosko.css`.

### 3.3 Estilos inline en Manager (menores)

En `manager/dashboard.html`:
- `<th style="width:100px">Nota</th>` — debería ser `.mgr-col-nota`
- `<span style="font-size:12px; color:#64748b">` — debería ser `.mgr-score-meta` o similar

En `manager/ranking.html`:
- `<p style="font-size:11px; color:#94a3b8...">` — caption fuera de sistema

### 3.4 Iconografía inconsistente en Auditorías

**Style Guide §6:**
> "Iconos de Phosphor, no emojis ni texto"

Revisión: Se usa `ph ph-magnifying-glass` para Auditorías en el nav (`layout.html`). El ícono correcto debería ser `ph ph-scales` (iconografía de justicia/auditoría). Actualmente la lupa se usa tanto para búsqueda como para auditorías.

### 3.5 Phosphor Icons cargado sin `defer`

En `manager/layout.html`:
```html
<script src="https://unpkg.com/@phosphor-icons/web"></script>
```
Sin `defer`. Esto bloquea el parsing del HTML. HTMX sí tiene defer.

### 3.6 Colors hardcodeados fuera de tokens

En `manager/matriz.html`:
```html
style="color:#0d47a1"
style="color:#16a34a"
style="color:#dc2626"
```
Deberían referenciar variables del sistema, no hexadecimales raw.

---

## 4. Deuda Técnica Crítica

### 4.1 JavaScript casi vacío

`main.js` (185 bytes) y `manager.js` (149 bytes) son prácticamente archivos vacíos. Toda la lógica JS está embebida en `{% block extra_js %}` dentro de cada template:
- `manager/dashboard.html` → 40 líneas de JS
- `manager/matriz.html` → 40 líneas de JS
- `manager/ranking.html` → 20 líneas de JS
- `manager/auditoria_detalle.html` → 90 líneas de JS

**Esta JS duplicada y dispersa** dificulta el mantenimiento y la reutilización. El filtrado de pills, el click en filas, las animaciones de contadores — todo está repetido.

### 4.2 Falta de CSRF en el form de auditoría del alumno

`solicitar_auditoria.html` usa `method="get"`. Necesita:
1. Cambiar a `method="post"`
2. Incluir `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`

### 4.3 El `base.html` legacy no está deprecado

Existe un `base.html` con sidebar DOBACKSOFT y todos sus blueprints legacy. Los portales nuevos (manager, student, kiosko, admin) tienen sus propios layouts, **pero `base.html` sigue accesible** y podría aparecer en cualquier ruta sin layout propio.

### 4.4 Sin favicon ni meta OG

`base.html`, `manager/layout.html`, `student/layout.html`, `kiosko/intento.html` — ninguno tiene:
- `<link rel="icon" ...>`
- `<meta name="description">`
- `<meta property="og:*">`

Para un producto que se va a presentar a CMadrid, la falta de favicon es un detalle visual notable.

### 4.5 `htmx.org` v1.9.10 — sin uso real

HTMX está cargado en manager/layout.html pero **no se usa en ningún template revisado**. Es 14KB de JS extra sin beneficio actual.

### 4.6 CDNs sin integridad (SRI)

```html
<script src="https://unpkg.com/@phosphor-icons/web"></script>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```
Sin `integrity=""` ni `crossorigin=""`. Para una aplicación de oposición pública con datos sensibles, esto es un riesgo de supply-chain.

---

## 5. Pantallas del PAPER-MAESTRO No Cubiertas

| Pantalla | Spec | Realidad | Gap |
|----------|------|----------|-----|
| M8 — Perfil del Alumno (desde Manager) | §9.4 | `manager/alumno.html` existe | ✅ Cubierto |
| M9 — Análisis de Ruta | §9.4 | ❌ No existe | **FALTA COMPLETA** |
| A6 — Módulo de Evolución | §9.5 | `student/evolucion.html` existe | ✅ Cubierto |
| D2 — Admin Dashboard con estado sistema | §9.6 | `admin/dashboard.html` parcial | ⚠️ Sin estado Webfleet/Redis |
| D3 — CRUD Convocatorias | §9.6 | `admin/convocatorias.html` | ✅ Cubierto |
| D4 — Editor Convocatoria (v5) | §9.6 | ❌ No se encontró template específico | **FALTA** |
| D5 — Cierre 3 pasos | §9.6 | `admin/cierre.html` (29KB) | ✅ Cubierto |
| D6 — CRUD Rutas | §9.6 | ❌ No encontrado | **FALTA** |
| D7 — RFID Cards | §9.6 | ❌ No encontrado | **FALTA** |
| D8 — Kioskos pairing | §9.6 | ❌ No encontrado | **FALTA** |
| D9 — Scoring Versions (read-only) | §9.6 | ❌ No encontrado | **FALTA** |
| D10 — Simulador (con ranking dim.) | §9.6 | `admin/simulador.html` | ✅ Cubierto (verificar) |
| K1 — Kiosko: Idle state | §9.7 | `kiosko/rutas.html` | ⚠️ Parcial |
| K2 — Kiosko: Active (en curso) | §9.7 | `kiosko/intento.html` | ✅ Cubierto |
| K3 — Kiosko: Recovery | §9.7 | ❌ No existe | **FALTA** |
| GDPR Export | §17 | `admin/gdpr.html` existe | ✅ Cubierto |
| Admin Usuarios | §9.6 | `admin/usuarios.html` existe | ✅ Cubierto |

---

## 6. 🧠 BRAINSTORMING — Mejoras del Frontend

### 6.1 UX / Producto

#### 🔥 Alta prioridad

**1. Data Quality visible en Matriz**
La spec lo pide explícitamente y tiene impacto legal (oposición pública). Un badge `HQ`/`LQ`/`MQ` en cada celda de la matriz daría transparencia. El manager necesita saber si una nota baja es por conducción real o por datos de baja calidad.

**2. Acciones rápidas en Ranking (sin salir)**
El ranking tiene 200 filas. Hoy para ver detalles de auditoría hay que salir de la página. Una slide-over panel o un mini-modal con el resumen del intento auditado sin perder el contexto del ranking mejoraría drásticamente el flujo del manager.

**3. Indicador de "última actualización" en tiempo real**
El ranking se actualiza a las 6:00 AM. Mostrar un contador regresivo o timestamp claro "Próxima actualización en X horas" reduce la ansiedad del manager que llega a primera hora.

**4. Estado de convocatoria en el header del Manager**
El header actual muestra Logo + Nav + UserChip. Si la convocatoria activa está a 3 días de cerrar, no hay ninguna alerta visual. Un badge contextual `"Cierre en 3 días"` en el header sería valioso.

**5. Página vacía mejorada para el Kiosko**
El kiosko en estado "nadie conectado" podría mostrar quién fue el último conductor, hace cuánto, y el estado general del día. Actualmente es solo un login form.

**6. Navegación con teclado en Kiosko**
El kiosko se usa en cabina (pantalla táctil). Los elementos interactivos necesitan áreas de toque mínimas de 48×48px. Revisar todos los botones del kiosko.

#### 🟡 Media prioridad

**7. Animación de entrada en el Ranking (corte)**
La línea de corte (`mgr-cut-row`) ya existe pero es estática. Una animación sutil al cargar (línea que se revela de izquierda a derecha) haría más memorable la demo con CMadrid.

**8. Tooltip rico en los circuitos de la Matriz Manager**
Los `mgr-rbox` ya tienen tooltip vía `::after + data-label`. Expandir este tooltip para mostrar: nombre completo de la ruta, nota, fecha del intento, y data_quality — todo sin salir de la matriz.

**9. Historial del alumno con timeline visual**
Actualmente es una tabla. Un timeline visual (tipo feed vertical) donde cada intento es una card con nota, fecha, y estado de auditoría sería más pedagógico y más "app".

**10. Badge de progreso en el nav del Student**
El nav del alumno tiene "Mis resultados" e "Historial". Añadir un badge con `rutas_completadas/rutas_total` en el ítem de nav haría el progreso siempre visible.

**11. Comparador de intentos en el Portal Alumno**
Si un alumno tiene múltiples intentos de una misma ruta (reevaluaciones), mostrar un comparador side-by-side de las notas por familia de criterios sería muy pedagógico.

**12. Modo de alto contraste para Kiosko**
Para condiciones de luz solar directa en cabina, ofrecer un tema de alto contraste (fondo negro, texto blanco puro, sin grays) mejora la accesibilidad.

#### 🟢 Baja prioridad / Fase 2

**13. Export CSV del Ranking**
Un botón "Exportar CSV" en la vista de Ranking del Manager. Los datos son públicamente accesibles para el manager — el export aceleraría su trabajo con el cliente final (CMadrid).

**14. Gráfico de distribución de notas**
Un histograma de la distribución de notas de la convocatoria (eje X: rangos de nota 0-10, eje Y: número de candidatos) daría al manager una visión estadística instantánea. Chart.js ya está contemplado en el stack.

**15. Atajos de teclado para el Manager**
`/` para foco en búsqueda, `M` para Matriz, `R` para Ranking, `←` para volver — para managers power-user que navegan rápido.

**16. Modo "presentación" para la demo**
Un `?demo=true` en la URL que oculte nombres reales (reemplazados por "Candidato #001") para demos ante el cliente sin exponer datos personales. Crítico para GDPR en demos.

---

### 6.2 Técnico / Arquitectura CSS-JS

**17. Extraer JS inline a módulos**
Todo el JavaScript en `{% block extra_js %}` debería migrarse a archivos propios por vista o por funcionalidad:
- `manager-filters.js` — lógica de pills y filtros
- `manager-clickable-rows.js` — filas clickables
- `manager-counters.js` — animación de KPI counters
- `manager-progress-bars.js` — barras animadas

**18. Centralizar la lógica de pills/filtros**
Tres páginas (`matriz.html`, `ranking.html`, `dashboard.html`) repiten la misma lógica de filtrado por pills. Una función utilitaria `setupPillFilter(selector, filterFn)` en `main.js` eliminaría esta duplicación.

**19. Refactorizar estilos inline del Kiosko**
Crear clases semánticas en `kiosko.css` para todo lo que actualmente es `style=""`:
```css
.ksk-score-display { font-size: 42px; text-align: center; }
.ksk-breakdown-card { background: #0d1527; border: 1px solid rgba(255,255,255,.07); border-radius: 14px; padding: 24px; }
```

**20. Unificar paleta de tokens**
Resolver la discordancia entre `tokens.css` (Plus Jakarta Sans + Source Sans 3) y el Style Guide (Inter). Elegir UNO y documentarlo. La consistencia importa más que qué fuente específica.

**21. Agregar SRI a los CDN externos**
```html
<script src="https://unpkg.com/@phosphor-icons/web@2.x.x"
        integrity="sha384-..."
        crossorigin="anonymous"></script>
```

**22. Favicon + meta básicos**
Crear un favicon institucional (iniciales "CM" en azul `#0d47a1`) y añadir las meta descriptions básicas a todos los layouts.

**23. Corregir el form de auditoría del alumno**
Cambiar `method="get"` a `method="post"` y añadir CSRF token.

**24. Deprecar o aislar `base.html`**
Añadir un banner de warning en desarrollo cuando se usa `base.html` legacy. Documentar cuáles blueprints aún lo usan y planificar su migración.

**25. Añadir `defer` a Phosphor Icons**
```html
<script src="..." defer></script>
```
Los iconos se pueden cargar asíncronamente sin impacto visual.

**26. Eliminar HTMX si no se usa**
Si HTMX no tiene uso real, eliminar la carga. Son 14KB menos de bloqueo. Si hay planes de uso, documentarlos.

---

### 6.3 Accesibilidad

**27. ARIA roles en la Matriz**
La matriz es una tabla compleja. Añadir `role="grid"`, `aria-label`, y `aria-sort` en los headers mejora la accesibilidad.

**28. Focus management en modales**
Si se implementan modales (ej: M7 auditoría modal desde ranking), el foco debe moverse al modal al abrirse y volver al trigger al cerrarse.

**29. Atributos `title` en los botones de nav**
El nav del manager tiene botones solo con ícono (`<i class="ph ph-..."></i>`). En viewports estrechos o con screen readers, los `title` o `aria-label` son críticos.

**30. Color no como único indicador**
Los `mgr-rbox--apto/suspenso/pendiente` usan solo color. Añadir un símbolo (✓/✗/—) como indicador secundario mejora accesibilidad para daltónicos.

---

### 6.4 Performance

**31. Preload de fuentes críticas**
```html
<link rel="preload" href="..." as="font" crossorigin>
```
Para Plus Jakarta Sans y Source Sans 3 desde Google Fonts.

**32. Lazy load de tablas largas**
La Matriz con 200+ candidatos y 4+ circuitos es una tabla grande. Implementar virtualización (mostrar solo las filas visibles + un buffer) mejoraría el rendimiento en convocatorias grandes.

**33. Cache de rendering del Ranking**
El ranking se calcula al vuelo en cada request. Hasta que el cron nocturno esté implementado (tarea 9), añadir un caché de 5 minutos en Flask para el endpoint del ranking reduciría la carga de DB.

---

## 7. Resumen Ejecutivo de Gaps Críticos

| Prioridad | Gap | Impacto demo 11/05 |
|-----------|-----|--------------------|
| 🔴 | Form auditoría alumno usa `method="get"` | Bug de seguridad |
| 🔴 | Data quality no visible en matriz | Funcionalidad especificada |
| 🔴 | `base.html` DOBACKSOFT aún activo | Riesgo NDA CMadrid |
| 🟡 | JS inline duplicado en 5+ templates | Deuda técnica |
| 🟡 | ~20 estilos inline en kiosko/intento.html | Violación style guide |
| 🟡 | Phosphor Icons sin `defer` | Performance |
| 🟡 | HTMX cargado sin uso real | Peso innecesario |
| 🟡 | Sin favicon ni meta descriptions | Profesionalidad visual |
| 🟢 | M9 Análisis de Ruta no implementado | Fuera de scope demo |
| 🟢 | D6-D9 (Rutas, RFID, Kioskos admin) | Fuera de scope demo |
| 🟢 | CDNs sin SRI | Seguridad no crítica ahora |

---

*Generado por Antigravity · DobackV2 Training Portal · 2026-05-05*
