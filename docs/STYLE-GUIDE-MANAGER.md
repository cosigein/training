# Guía de Estilos — Portal Manager CMadrid Training

> Stack: **Flask + Jinja2 + CSS puro**  
> Convocatoria: Bomberos CMadrid · Oposición pública 2026  
> Última revisión: 2026-04-28

---

## 1. Archivos CSS y orden de carga

```
app/static/css/
├── tokens.css        ← Variables globales (PRIMER archivo en cargar)
├── reset.css         ← Normalización de estilos
├── base.css          ← Tipografía base, body, links
├── layout.css        ← Utilidades de layout (grid, flex, shells)
├── manager.css       ← Estilos específicos del portal Manager
└── components/
    ├── alert.css
    ├── badge.css
    ├── button.css
    ├── card.css
    ├── form.css
    ├── nav.css
    └── table.css
```

**Regla de oro**: `tokens.css` siempre primero. Todo lo demás referencia sus variables.

---

## 2. Tokens de diseño (`tokens.css`)

### Fuentes

| Variable | Valor | Uso |
|----------|-------|-----|
| `--font-body` | Inter, sans-serif | Texto corriente |
| `--font-heading` | Inter, sans-serif (700) | Títulos, KPIs, números |

### Espaciado

| Variable | Valor | Equivalente |
|----------|-------|-------------|
| `--space-xs` | 4px | Gaps mínimos |
| `--space-sm` | 8px | Padding interno pequeño |
| `--space-md` | 16px | Gap estándar entre bloques |
| `--space-lg` | 24px | Padding de contenedores |
| `--space-xl` | 32px | Separación entre secciones |

### Radios

| Variable | Valor | Uso |
|----------|-------|-----|
| `--radius-sm` | 4px | Badges, pills pequeñas |
| `--radius-md` | 6px | Inputs, botones |
| `--radius-lg` | 8px | Cards, tablas, contenedores |

### Sombras

| Variable | Valor | Uso |
|----------|-------|-----|
| `--shadow-sm` | 0 1px 3px rgba(0,0,0,.06) | Contenedores, cards |
| `--shadow-md` | 0 4px 12px rgba(0,0,0,.1) | Modales, dropdowns |

### Transiciones

| Variable | Valor |
|----------|-------|
| `--transition-fast` | 100ms ease |
| `--transition-base` | 200ms ease |

### Colores del sistema

| Variable | Hex | Rol |
|----------|-----|-----|
| `--color-border` | `#e2e8f0` | Bordes de todos los contenedores |
| `--color-bg` | `#f0f4f8` | Fondo de la página |
| `--color-surface` | `#ffffff` | Cards, tablas, modales |
| `--color-text` | `#1e293b` | Texto principal |
| `--color-muted` | `#64748b` | Texto secundario |
| `--color-subtle` | `#94a3b8` | Labels, placeholders |

---

## 3. Paleta de colores semánticos

### Acción principal — Azul institucional

```
#0d47a1   ← brand primary (botones, logos, nav activo)
#1e3a8a   ← cabeceras de tabla
#1d4ed8   ← badges de categoría Cat. C / C+E
#eff6ff   ← fondo de badges de categoría
```

### Estados de circuito

| Estado | Color de fondo | Color de texto | Clase CSS |
|--------|---------------|----------------|-----------|
| Apto | `#16a34a` (verde) | `#fff` | `.mgr-rbox--apto` |
| Suspenso | `#dc2626` (rojo) | `#fff` | `.mgr-rbox--suspenso` |
| Pendiente | `#cbd5e1` (gris claro) | `#64748b` | `.mgr-rbox--pendiente` |

### KPI cards — borde izquierdo de 4px

| Variante | Color | Clase |
|----------|-------|-------|
| Azul | `#0d47a1` | `.mgr-kpi--blue` |
| Gris | `#64748b` | `.mgr-kpi--gray` |
| Verde | `#16a34a` | `.mgr-kpi--green` |
| Rojo | `#dc2626` | `.mgr-kpi--red` |

### Stat badges — borde izquierdo de 3px

| Variante | Color | Clase |
|----------|-------|-------|
| Azul (sesiones) | `#0d47a1` | `.mgr-stat__item--blue` |
| Verde (aptos) | `#16a34a` | `.mgr-stat__item--green` |
| Ámbar (nota media) | `#d97706` | `.mgr-stat__item--amber` |
| Gris (última sesión) | `#64748b` | `.mgr-stat__item--gray` |

### Ranking — posiciones

| Posición | Fondo | Texto | Clase |
|----------|-------|-------|-------|
| 1.º (oro) | `#fef3c7` | `#d97706` | `.mgr-pos--gold` |
| 2.º (plata) | `#f1f5f9` | `#475569` | `.mgr-pos--silver` |
| 3.º (bronce) | `#fff7ed` | `#c2410c` | `.mgr-pos--bronze` |

---

## 4. Componentes del Manager

### 4.1 Layout raíz

```
.mgr-root          ← position:fixed, inset:0, flex column
  .mgr-header      ← 64px, fondo blanco, border-bottom, z-index:10
  .mgr-body        ← flex:1, overflow-y:auto, padding 24px, gap 18px
```

**Por qué `position:fixed`**: elimina el scroll del body entero; solo el `.mgr-body` hace scroll. Esto da sensación de app nativa.

### 4.2 Header

```html
<div class="mgr-root">
  <header class="mgr-header">
    <a href="..." class="mgr-logo">
      <div class="mgr-logo__icon">CM</div>
      <span class="mgr-logo__text">CMadrid <span>Training</span></span>
    </a>
    <nav class="mgr-nav">
      <a class="mgr-nav__btn active">...</a>   <!-- ← activo con clase .active -->
    </nav>
    <a class="mgr-btn-logout">Salir</a>
  </header>
  <main class="mgr-body">...</main>
</div>
```

- Logo: 32×32px, `#0d47a1`, radio 6px, texto "CM" en blanco.
- Nav: iconos Phosphor Icons 20px; `.active` → fondo `#0d47a1`, icono blanco.
- Logout: borde `#e2e8f0`; hover → borde + texto `#0d47a1`.

### 4.3 KPI Cards

```html
<div class="mgr-kpis">                    <!-- grid 4 columnas -->
  <div class="mgr-kpi mgr-kpi--blue">
    <span class="mgr-kpi__label">Conductores</span>
    <span class="mgr-kpi__value">8</span>
    <span class="mgr-kpi__sub">en formación activa</span>
  </div>
</div>
```

- Grid de 4 con gap 12px.
- Cada card: `min-height: 74px`, borde izquierdo 4px, sombra suave.
- Valor: 28px, 700, font-heading.
- Label: 11px, uppercase, letter-spacing 0.5px.

### 4.4 Toolbar (búsqueda + filtros)

```html
<div class="mgr-toolbar">
  <div class="mgr-search">
    <i class="ph ph-magnifying-glass mgr-search__icon"></i>
    <input type="text" class="mgr-search__input" placeholder="Buscar conductor…">
  </div>
  <span data-filter-cat="all" class="mgr-pill active">Todos</span>
  <span data-filter-cat="C"   class="mgr-pill">Cat. C</span>
  <span data-filter-cat="C+E" class="mgr-pill">Cat. C+E</span>
</div>
```

- Input: 280px fijo, 36px alto, focus `#0d47a1`.
- Pills: radio 20px, `active`/`hover` → fondo + borde `#0d47a1`, texto blanco.

### 4.5 Tabla de conductores

```html
<div class="mgr-table-wrap">           <!-- fondo blanco, radio 8, overflow auto -->
  <table class="mgr-table">           <!-- table-layout: fixed; min-width: 640px -->
    <thead>
      <tr>
        <th class="mgr-col-alumno sortable">Conductor</th>  <!-- 22% -->
        <th class="mgr-col-stats">Estadísticas</th>         <!-- 28% -->
        <th class="mgr-col-rutas">Circuitos</th>            <!-- 50% -->
      </tr>
    </thead>
    <tbody>
      <tr class="mgr-row" data-name="..." data-cat="...">
        <!-- celda conductor -->
        <td>
          <div class="mgr-alumno">
            <span class="mgr-alumno__name">Carlos Rodríguez</span>
            <div class="mgr-alumno__meta">
              <span class="mgr-alumno__plaza">#001</span>
              <span class="mgr-badge-cat">C+E</span>
            </div>
          </div>
        </td>
        <!-- celda estadísticas -->
        <td>
          <div class="mgr-stat">
            <div class="mgr-stat__item mgr-stat__item--blue">
              <span class="mgr-stat__val">5</span>
              <span class="mgr-stat__lbl">Sesiones</span>
            </div>
            <!-- más items... -->
          </div>
        </td>
        <!-- celda circuitos -->
        <td>
          <div class="mgr-rutas">
            <div class="mgr-rbox mgr-rbox--apto" data-label="Salida Cochera">01</div>
            <div class="mgr-rbox mgr-rbox--suspenso" data-label="Maniobra T">02</div>
            <div class="mgr-rbox mgr-rbox--pendiente" data-label="Paso Angosto">03</div>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

- Cabecera: `#1e3a8a`, texto blanco, sticky top.
- Filas: `border-bottom: 1px solid #f1f5f9`; hover `#f8fafc`.
- `mgr-rbox`: cuadros 20×20px con tooltip via `::after` + `data-label`.
- `mgr-stat`: grid 2 columnas; cada item es un mini-badge con borde izquierdo de color.

### 4.6 Matriz de progreso

```html
<div class="mgr-matrix-wrap">
  <table class="mgr-matrix">
    <thead>
      <tr>
        <th>Conductor</th>     <!-- sticky left -->
        <th>R01</th>           <!-- sticky top -->
        <!-- ... -->
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Carlos Rodríguez</td>    <!-- sticky left -->
        <td>
          <div class="mgr-cell-dot mgr-cell-dot--apto">✓</div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

- Primera columna: `position: sticky; left: 0` — se congela al hacer scroll horizontal.
- Cabecera: `position: sticky; top: 0` — se congela al hacer scroll vertical.
- `mgr-cell-dot`: círculo 28px.

### 4.7 Ranking

```html
<div class="mgr-ranking">
  <table class="mgr-rank-table">
    <tbody>
      <tr class="mgr-rank--pass">             <!-- fondo verde suave si aprueba -->
        <td><span class="mgr-pos mgr-pos--gold">1</span></td>
        <td>Elena Ruiz</td>
        <td class="align-right">
          <span class="mgr-score mgr-score--pass">9.6</span>
        </td>
      </tr>
      <tr class="mgr-cut-row">               <!-- línea de corte: dashed rojo -->
        ...
      </tr>
      <tr>
        <td colspan="...">
          <span class="mgr-cut-label mgr-cut-label--out">Fuera de nota de corte</span>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 5. Convenciones de nomenclatura CSS

| Patrón | Ejemplo | Cuándo usarlo |
|--------|---------|---------------|
| `mgr-` | `.mgr-header` | Todos los elementos propios del Manager |
| `mgr-{bloque}__elemento` | `.mgr-kpi__value` | Sub-elemento de un bloque |
| `mgr-{bloque}--modificador` | `.mgr-kpi--blue` | Variación de color/estado |
| `mgr-col-{nombre}` | `.mgr-col-alumno` | Columnas de tabla con ancho fijo |

**Regla**: no escribas estilos `inline` en las templates Jinja. Toda variación visual debe tener su propia clase modificadora.

---

## 6. Iconografía — Phosphor Icons

CDN en el `<head>` del layout:
```html
<script src="https://unpkg.com/@phosphor-icons/web"></script>
```

Uso:
```html
<i class="ph ph-magnifying-glass"></i>   <!-- búsqueda -->
<i class="ph ph-squares-four"></i>        <!-- dashboard -->
<i class="ph ph-grid-nine"></i>           <!-- matriz -->
<i class="ph ph-trophy"></i>              <!-- ranking -->
<i class="ph ph-sign-out"></i>            <!-- logout -->
<i class="ph ph-users"></i>               <!-- estado vacío -->
```

Tamaño por contexto:
- Nav: `font-size: 20px`
- Empty state: `font-size: 40px`
- Inline (input): `font-size: 15px`

---

## 7. Interactividad — HTMX + JS vanilla

```html
<!-- En el <head> del layout -->
<script src="https://unpkg.com/htmx.org@1.9.10" defer></script>

<!-- JS del manager -->
<script src="{{ url_for('static', filename='js/manager.js') }}"></script>
```

`manager.js` implementa:
- **Búsqueda en tiempo real**: filtra filas `[data-name]` comparando con el input.
- **Filtro por categoría**: activa/desactiva pills y filtra filas `[data-cat]`.
- **Columna sortable**: ordena la tabla alfabéticamente al clic en `<th class="sortable">`.

---

## 8. Añadir nuevas páginas

1. Crear `app/templates/manager/nueva_pagina.html` extendiendo `manager/layout.html`:
```jinja
{% extends "manager/layout.html" %}
{% block title %}Nueva Página — CMadrid Training{% endblock %}

{% block content %}
<div>
  <h1 class="mgr-page-title">Nueva Página</h1>
  <p class="mgr-page-subtitle">Subtítulo descriptivo</p>
</div>

<!-- contenido -->
{% endblock %}
```

2. Agregar la ruta en `app/blueprints/manager/routes.py`:
```python
@manager_bp.route('/nueva')
def nueva_pagina():
    return render_template('manager/nueva_pagina.html', active_page='nueva')
```

3. Agregar el botón en el `<nav>` del `layout.html`:
```html
<a href="{{ url_for('manager.nueva_pagina') }}"
   class="mgr-nav__btn {% if active_page == 'nueva' %}active{% endif %}"
   title="Nueva Página">
    <i class="ph ph-icon-name"></i>
</a>
```

---

## 9. Checklist de calidad

Antes de dar por terminada una pantalla del Manager:

- [ ] Extiende `manager/layout.html`
- [ ] `active_page` pasado desde la ruta y aplicado en el nav
- [ ] Sin estilos `inline` (solo clases del sistema)
- [ ] Vacíos cubiertos con `.mgr-empty`
- [ ] Tabla con `sticky` en cabecera si hay scroll
- [ ] Responsive: tablas con `overflow: auto` en su wrapper
- [ ] Iconos de Phosphor, no emojis ni texto

---

*Generado por Antigravity · DobackV2 Training Portal*
