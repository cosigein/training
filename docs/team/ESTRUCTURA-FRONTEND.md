# Estructura Completa del Frontend - DobackV2

Acá tenés el mapa total, loco. No falta ni un solo archivo. Esta es la arquitectura completa del frontend para que no andes adivinando qué hay en cada rincón.

## Árbol Completo de Archivos

```text
app/
├── static/
│   ├── css/
│   │   ├── components/
│   │   │   ├── alert.css
│   │   │   ├── badge.css
│   │   │   ├── button.css
│   │   │   ├── card.css
│   │   │   ├── form.css
│   │   │   ├── nav.css
│   │   │   └── table.css
│   │   ├── alumno.css
│   │   ├── base.css
│   │   ├── kiosko.css
│   │   ├── layout.css
│   │   ├── manager.css
│   │   ├── reset.css
│   │   └── tokens.css
│   └── js/
│       ├── main.js
│       └── manager.js
└── templates/
    ├── auth/
    │   └── login.html
    ├── errors/
    │   ├── 403.html
    │   ├── 404.html
    │   └── 500.html
    ├── kiosko/
    │   ├── intento.html
    │   ├── login.html
    │   └── rutas.html
    ├── kpis/
    │   └── executive.html
    ├── macros/
    │   ├── alerts.html
    │   ├── charts.html
    │   ├── forms.html
    │   ├── modals.html
    │   └── tables.html
    ├── manager/
    │   ├── alumno.html
    │   ├── auditoria.html
    │   ├── auditoria_detalle.html
    │   ├── auditorias.html
    │   ├── convocatorias.html
    │   ├── dashboard.html
    │   ├── intento.html
    │   ├── layout.html
    │   ├── matriz.html
    │   └── ranking.html
    ├── student/
    │   ├── dashboard.html
    │   ├── evolucion.html
    │   ├── historial.html
    │   ├── intento.html
    │   ├── layout.html
    │   ├── sin_inscripciones.html
    │   └── solicitar_auditoria.html
    ├── base.html
    └── settings.html
```

## Guía Rápida de Responsabilidades

### CSS & Estilos
- **static/css/components/**: Estilos atómicos. Si querés cambiar cómo se ve UN botón en toda la app, es acá.
- **tokens.css**: Definición de variables (colores, sombras, tipografía). Es el corazón del diseño.
- **base.css**: Estilos globales que aplican a todos los niveles de la app.

### Lógica de Cliente
- **static/js/main.js**: Funcionalidades transversales (menús, dropdowns, etc.).
- **static/js/manager.js**: Scripts pesados para el manejo de datos en el portal administrativo.

### Templates & Vistas
- **templates/macros/**: Fragmentos de HTML reutilizables (inputs, tablas, alertas). Se importan en otros templates para mantener el código DRY.
- **templates/manager/** & **templates/student/**: Las tripas de cada portal. Cada uno tiene su `layout.html` que define la estructura lateral y de navegación.
- **base.html**: El esqueleto de hierro. Todo lo que ves en la pantalla pasa por acá.

---
**Consejo de Senior:** Si vas a tocar algo en `manager.css`, asegurate de no romper `alumno.css`. Aunque están separados, comparten muchos conceptos en `layout.css`. ¡Ojo al piojo!
