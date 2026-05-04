# Guía de Implementación: Portal de Administración - Training CMadrid

Esta guía está diseñada para que una IA sea capaz de implementar el apartado de **Administración (Admin)** del sistema Training, asegurando una funcionalidad completa, un diseño premium y coherencia con las reglas de negocio de una oposición pública.

---

## 1. Visión y Contexto del Sistema

**Training** es un sistema de evaluación automática y competitiva para conductores de bomberos (CMadrid). 
- **No es un examen escolar**: Es una **oposición**. Hay plazas limitadas y los candidatos compiten por ellas.
- **El Admin es el "Dios" del sistema**: Configura las reglas (scoring), las rutas, las tarjetas RFID y, lo más importante, ejecuta el **Cierre de Convocatoria**.
- **Regla de Oro**: La objetividad y la trazabilidad legal son innegociables.

---

## 2. Arquitectura Funcional (Backend Flask/Jinja2)

> [!IMPORTANT]
> **Ignora las rutas mencionadas en documentos antiguos**. Las rutas válidas son las definidas en `app/blueprints/admin/routes.py`. El sistema usa Blueprints de Flask y plantillas Jinja2.

### Entidades Principales
- **Convocatoria**: Agrupa candidatos, rutas y plazas. Tiene estados: `OPEN`, `CLOSING`, `CLOSED`, `LOCKED`.
- **Enrollment**: Inscripción de un alumno a una convocatoria específica.
- **Attempt**: Intento de conducción con nota inmutable.
- **Ranking**: Snapshot diario (o final) de la posición de los candidatos.

---

## 3. Diseño y Estética Premium (Design System)

El Admin debe respirar autoridad y claridad. Usa el azul institucional como color primario.

### Tokens de Diseño
- **Primario**: `#0d47a1` (Azul CMadrid). Usar para botones `primary`, nav activo y cabeceras.
- **Superficie**: Fondo `#f0f4f8`, Cards `#ffffff`.
- **Tipografía**: `Inter, sans-serif`. Títulos en 700, cuerpo en 400.
- **Semántica**:
    - **Apto/Dentro del corte**: Verde `#16a34a`.
    - **No Apto/Fuera del corte**: Rojo `#dc2626`.
    - **Pendiente/Info**: Gris `#64748b`.

### Componentes Clave
- **KPI Cards**: Cards con borde izquierdo de 4px de color. Valores grandes (28px) y labels en uppercase (11px).
- **Toolbars**: Buscador a la izquierda (36px alto) y filtros (Pills) a la derecha.
- **Tablas de Convocatorias**: Sticky header, filas con hover sutil, badges de estado claros (`OPEN`, `CLOSED`).
- **Matriz de Progreso**: Tabla virtualizada (para cientos de alumnos) con primera columna (Nombres) y cabecera (Rutas) fijas (sticky).

---

## 4. Flujos Críticos de Implementación

### D5: Cierre de Convocatoria (El Proceso de 3 Pasos)
Este es el flujo más sensible legalmente. No debe ser un simple botón.

1.  **Paso 1: Preview**: El Admin ve un resumen: ¿Cuántos alumnos han terminado? ¿Cuántas auditorías hay pendientes? ¿Quiénes entrarían en plaza (Aptos) y quiénes no? Endpoints: `POST /admin/convocatorias/<id>/close/preview`.
2.  **Paso 2: Iniciación**: El Admin inicia el cierre. El estado pasa a `CLOSING`. Se bloquean nuevos intentos. Endpoints: `POST /admin/convocatorias/<id>/close/initiate`.
3.  **Paso 3: Confirmación**: Requiere un **segundo Administrador** distinto al primero (doble validación). Se solicita contraseña y texto de confirmación. 
    - Al confirmar, el sistema genera el **Acta PDF con firma SHA256**.
    - El ranking pasa a ser `FINAL` e irrevocable tras 24h.
    - Endpoints: `POST /admin/convocatorias/<id>/close/confirm`.

### D12: Simulador de Scoring
Permite al Admin cambiar una regla (ej: bajar la penalización por velocidad) y ver **qué pasaría** en el ranking antes de aplicar el cambio.
- Debe mostrar: "Candidatos que entran en plaza" vs "Candidatos que salen".

---

## 5. Instrucciones de Estilo (CSS/UX)

- **Layout Fijo**: Usa `.adm-root { position: fixed; inset: 0; flex-direction: column; }`. El scroll solo debe ocurrir en el contenedor de contenido principal, no en toda la página.
- **Prefix**: Usa el prefijo `adm-` para clases CSS (ej: `.adm-card`, `.adm-btn`).
- **Iconografía**: Usa **Phosphor Icons**. 
    - Dashboard: `ph-squares-four`.
    - Convocatorias: `ph-clipboard-text`.
    - Cierre: `ph-lock`.
    - Simulador: `ph-test-tube`.
- **Micro-interacciones**: 
    - Hover en filas de tabla con transición de 200ms.
    - Buttons con efecto de "presionado" activo.
    - Skeletons de carga mientras se obtienen datos pesados (como el ranking).

---

## 6. Checklist para la IA Ejecutora

- [ ] Implementar `admin/layout.html` heredando de `base.html` pero con el sidebar y header específicos de Admin.
- [ ] La vista de detalle de convocatoria debe permitir gestionar `Enrollments` (añadir/quitar alumnos).
- [ ] El flujo de cierre debe ser un asistente (stepper) o una serie de estados claros en la misma página, llamando a los endpoints correspondientes.
- [ ] Asegurar que el **Acta PDF** sea descargable una vez cerrada la convocatoria (`GET /admin/convocatorias/<id>/acta`).
- [ ] Cumplimiento de **GDPR**: Pantalla para gestionar solicitudes de "Olvido" (Forget requests).

---

**Nota Final**: Estás construyendo una herramienta para funcionarios públicos en un entorno de alta presión legal. La UI debe ser **impecable, seria y robusta**. Evita florituras innecesarias; prioriza la densidad de información y la claridad de los estados.
