# Alejandro — Tu trabajo en Training

## Sprint de 14 días · Demo CMadrid: lunes 11 de mayo de 2026

---

## ⚡ TLDR — esto es lo que tenés mañana en 5 líneas

1. **Sos frontend lead.** 4 portales (admin, manager, alumno, kiosko) · ~32 pantallas · empezás por las **14 pantallas P0** listadas más abajo en este doc (sección "Priorización P0/P1/P2"). Si llegamos justos, recortamos P2 primero, nunca P0.
2. **Llegá al kickoff con Node 20 LTS instalado y la invite del repo aceptada.** **NO clones el repo, NO instales nada del proyecto, NO crees `apps/web`.** Lo hacemos juntos mañana en el scaffolding compartido. Si te falta algo, se instala en los primeros 15 min.
3. **Martes 28/04 09:00:** kickoff de 1h (lectura silenciosa + Q&A). Después (10:00-13:00) scaffolding compartido entre los 4. Setup de Vite + Tailwind 4 + tokens del §0.3 en pantalla compartida.
4. **Coordinación clave (te ahorra dos semanas de drift):** los tipos TypeScript backend↔frontend van en un package compartido `packages/api-types/` (Jesús lo expone, vos los importás). Los `data-testid` los ponés vos con la convención de `CONTRIBUTING.md` para que Joel pueda usarlos en E2E.
5. **No sos bombero.** Si tenés dudas de dominio (qué es una "convocatoria", cómo es físicamente la cabina del camión), están en el "Glosario rápido del dominio" más abajo. Pedile a Antonio una foto/video del kiosko al llegar mañana.

---

| | |
|---|---|
| **Tu rol** | Frontend completo (4 portales · ~32 pantallas · Wrappers · Tests Vitest) |
| **Tu jefe técnico** | Antonio (director técnico) |
| **Tus pares** | Jesús (backend) · Joel (simulador + QA) |
| **Documento maestro** | `docs/PAPER-MAESTRO.md` (referencia completa cuando dudes) |
| **Convenciones del repo** | [`OWNERS.md`](../../OWNERS.md) y [`CONTRIBUTING.md`](../../CONTRIBUTING.md) |

---

## Glosario rápido del dominio (no sos bombero, leé esto primero)

| Término | Qué significa visualmente |
|---|---|
| **Oposición pública** | Proceso de selección por el que un cuerpo público (en este caso bomberos de Madrid) cubre plazas. Hay un nº fijo de plazas, los candidatos compiten entre sí. **Tu UI tiene que dejar claro que esto NO es un examen escolar — es una competición**. |
| **convocatoria** | Una "edición" del proceso de selección. Tiene fecha de inicio, fecha de cierre, número de plazas y un grupo cerrado de candidatos inscritos. CMadrid puede tener varias convocatorias activas a la vez (raro en V1, pero posible). |
| **Student / alumno** | El humano evaluado. Un mismo Student puede inscribirse en varias convocatorias a lo largo del tiempo → cada inscripción es un `Enrollment`. |
| **Enrollment** | Inscripción de un Student a UNA convocatoria. Es la unidad sobre la que computa el ranking. |
| **attempt / intento** | Un Student + una ruta + una sesión de conducción. Tiene una nota 0-10. Múltiples attempts dentro de un Enrollment. |
| **Doback Elite** | Dispositivo físico instalado en el camión (sensor inercial + GPS propio). Es producto NUESTRO. No lo dibujás en pantalla, pero el **kiosko** muestra estado de conexión con él. |
| **Webfleet** | Plataforma externa de Bridgestone que CMadrid tiene contratada. Provee datos GPS redundantes. No la dibujás. |
| **kiosko** | **Tablet fija dentro de la cabina del camión.** Es la pantalla que ve el conductor mientras hace su intento. Modo oscuro obligatorio (legibilidad nocturna y cabina ruidosa). El conductor **NO ve la nota** desde el kiosko — solo el manager la ve después en el portal manager. |
| **manager / responsable** | Bombero senior que supervisa la convocatoria. Lee la matriz, gestiona auditorías. **Read-only sobre las notas** (no las cambia). |
| **APTO / NO_APTO** | La decisión final por candidato al cierre de la convocatoria. **No se emite por intento** — solo al cierre, según ranking final + plazas. |
| **acta** | PDF generado al cierre con SHA256 de integridad. Documento legal. |
| **matriz** (M5/M6) | **Tabla 2D**: filas = candidatos enrolled en la convocatoria, columnas = rutas evaluadas. Cada celda = la nota del último attempt del candidato en esa ruta (o vacío si aún no la hizo). Es la pantalla más importante para el manager. Por eso virtualizada (`react-window`) — puede tener 265 filas × 4-8 columnas. |
| **ranking** | Tabla 1D: lista ordenada de candidatos dentro de UNA convocatoria por su `nota_media` o criterio agregado. Se publica diaria a las 06:00 Madrid. |

> Si te falta saber **cómo se ve físicamente un camión de bomberos por dentro**, pediselo a Antonio el día 1 — idealmente foto/video. Sin haber visto la cabina, vas a inventar UX del kiosko.

---

## Priorización de pantallas (P0 / P1 / P2)

> **Si llegamos justos al 11/05, recortamos en este orden:** primero P2, luego P1, nunca P0.

| Priori | Pantallas (objetivo de la demo) |
|---|---|
| **P0 — Bloquea la demo** | M1 (login manager) · M5 (matriz convocatoria) · M6 (detalle attempt + auditoría desde manager) · A1 (login alumno) · A2 (StandingCard del alumno: posición + nota media + dentro/fuera del corte) · D1 (login admin) · D5 (cierre convocatoria — flujo 3 pasos) · K1 (idle kiosko) · K2 (RFID) · K3 (sesión activa) · D12 (simulador) |
| **P1 — Importante para credibilidad** | A3-A6 (portal alumno completo: histórico, ruta, audit request) · M7 (reevaluación tras auditoría) · D2-D4 (admin: rutas, RFID, students) · D11 (matriz vista admin) · K4 (recovery modal) |
| **P2 — Nice-to-have demo / Fase 2** | D6-D10 (admin: convocatorias edit, exports, GDPR ops, audit log viewer) · K5-K6 (kiosko: cierre intento, abandono) — si no llegan, los simulamos en demo |

> **~14 pantallas P0** en 9 días laborables = ~1.5 pantallas/día. Es factible si el contrato API está estable desde el día 3 y los wrappers (MapViewer, Matrix, Ranking) se reusan. Sin contrato API estable, esta priorización no se cumple — escalá a Antonio.

---

## Resolución de la contradicción §0.2 ↔ §0.12

- **§0.2** dice "no crees apps/web por adelantado". Eso aplica a **antes del scaffolding compartido del kickoff**. Correcto.
- **§0.12** habla de tu primer hito serio (jueves 30/04). Para entonces YA hicimos el scaffolding juntos en el kickoff — la estructura existe.

Resumen: **antes del kickoff, NO toques nada del proyecto**. Martes 28/04 por la mañana, durante el scaffolding compartido, nace `apps/web/` con todo el equipo en pantalla. Desde ahí, vos lo manejás.

---

## Decisiones de producto que cerramos en el Q&A del kickoff (09:30)

Estas son preguntas que hace falta resolver antes de que tengas que pintar pantallas con datos reales (semana 1 tarde):

1. **Identificación en ranking público (M5, A2):** ¿se muestran nombres y apellidos completos, dorsales/IDs anónimos, o iniciales? Decisión legal de CMadrid; Antonio la trae cerrada al kickoff o la decide en Q&A si no llegó.
2. **Foto/video del kiosko físico (cabina del camión):** Antonio te enseña una foto al menos durante el café del kickoff. Sin verlo no se puede decidir orientación, anclaje ni jerarquía visual. Si no hay foto, asumís un fixture razonable y se ajusta cuando llegue.
3. **D5 cierre — botón "Confirmar":** ¿lo deshabilitás en frontend si `auth.user.id === closing_admin_id` o lo dejás y dejás que el backend devuelva 403? Decisión rápida en Q&A — recomendación: frontend defensivo + backend como red de seguridad.

---

# 0. Cómo arrancás el día 1 (design system + estados + setup)

> **Importante (estado real al 27/04/2026):** este repo (`cosigein/training`) está recién creado y solo contiene los documentos del proyecto. **No hay código todavía.** Las versiones, estructura de carpetas, tokens y componentes que aparecen en este §0 son **la propuesta de partida** — la materializamos juntos durante el kickoff del MARTES 28/04. No instales ni configures nada de forma unilateral antes del kickoff.
>
> **Lo que sí necesitás tener listo para el martes:**
>
> - Node 20 LTS instalado (`node --version` debe imprimir v20.x.x)
> - Git configurado con tu usuario de GitHub
> - Acceso al repo `cosigein/training` aceptado (Antonio te invita)
> - Haber leído este documento + el README del repo + escaneo del paper maestro
>
> Si te falta alguna, **no hay drama** — los instalamos en los primeros 15 min del kickoff.

## 0.1 Stack y versiones (propuesta a fijar el día 1)

```
   React            18.3
   Vite             6.x
   TypeScript       5.6 (strict)
   Tailwind         4.x (con tokens propios — ver §0.3)
   React Query      5.x
   Zustand          5.x
   Leaflet          1.9 (envuelto en wrapper propio)
   Chart.js         4.x (envuelto en wrapper)
   i18next          23.x + react-i18next
   Vitest           1.x (unit tests)
   Testing Library  React Testing Library + user-event
   react-window     1.x (virtualización matriz y ranking)
   react-hook-form  7.x (formularios)
   date-fns-tz      2.x (fechas en Europe/Madrid)
   idb              7.x (wrapper IndexedDB para kiosko offline)
```

## 0.2 Estructura de carpetas propuesta

> Esta es la estructura objetivo. La consolidamos contigo el día 1. No la crees por adelantado.

```
apps/web/src/
├── main.tsx                   ← entry point
├── App.tsx                    ← router root
├── pages/
│   ├── auth/
│   ├── manager/               ← M1 a M9
│   ├── alumno/                ← A1 a A6
│   ├── admin/                 ← D1 a D13
│   └── kiosko/                ← K1 a K6
├── components/
│   ├── ui/                    ← Button, Input, Card, Modal, Badge,
│   │                            componentes base atómicos
│   ├── feedback/              ← LoadingSpinner, EmptyState, ErrorBoundary,
│   │                            ErrorBanner, SuccessToast
│   ├── MapViewer/             ← wrapper Leaflet
│   ├── Timeline/              ← wrapper timeline
│   ├── Matrix/                ← virtualizado
│   ├── Ranking/               ← virtualizado
│   ├── ScoreBreakdown/
│   ├── ConfidenceBadge/
│   ├── DataQualityBadge/
│   ├── StandingCard/
│   └── modals/
│       ├── AuditRequestModal/
│       ├── OverrideModal/     ← OJO: en v6 NO hay override real,
│       │                         se usa para AuditRequest desde manager
│       └── ConfirmDialog/
├── stores/
│   ├── auth.store.ts
│   ├── ui.store.ts            ← sidebar, theme, idioma
│   └── kiosko.store.ts        ← persistido IndexedDB
├── api/                       ← React Query hooks (no fetch directo)
│   ├── auth.ts
│   ├── attempts.ts
│   ├── convocatorias.ts
│   ├── ranking.ts
│   ├── students.ts
│   ├── audit-requests.ts
│   └── ...
├── hooks/
│   ├── useAuth.ts
│   ├── useToast.ts
│   ├── useConfirm.ts
│   └── ...
├── config/
│   ├── api.ts                 ← TODAS las URLs aquí (regla firme)
│   └── env.ts                 ← getter tipado de import.meta.env
├── i18n/
│   ├── index.ts
│   ├── es-ES.json             ← idioma único en V1
│   └── keys.ts                ← export de todas las claves (type-safe)
├── styles/
│   ├── tokens.css             ← variables CSS de design system
│   └── globals.css
└── types/
    ├── api.ts                 ← types de las respuestas backend
    └── domain.ts              ← types del dominio (AttemptStatus, etc.)
```

## 0.3 Design system — tokens (V1, propuesto)

**Como no hay diseñador externo, propongo estos tokens.** Son punto de partida: Antonio los aprueba o los modifica en el kickoff. Si CMadrid tiene una guía de marca corporativa (logos, paletas oficiales del cuerpo de bomberos), la incorporamos en Fase 2 — para la demo del 11/05 alcanza con que sea sobrio y profesional.

### Paleta

```css
/* tokens.css — usados como CSS variables y por Tailwind */

:root {
  /* Brand */
  --color-primary-50:  #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #1e40af;  /* azul institucional, evoca seguridad */
  --color-primary-700: #1e3a8a;
  --color-primary-900: #172554;

  /* Neutrales */
  --color-neutral-0:   #ffffff;
  --color-neutral-50:  #f8fafc;
  --color-neutral-100: #f1f5f9;
  --color-neutral-200: #e2e8f0;
  --color-neutral-300: #cbd5e1;
  --color-neutral-500: #64748b;
  --color-neutral-700: #334155;
  --color-neutral-900: #0f172a;

  /* Semánticos */
  --color-success:     #15803d;   /* verde — apto, dentro del corte */
  --color-warning:     #b45309;   /* ámbar — calidad media, atención */
  --color-danger:      #b91c1c;   /* rojo — suspenso, fuera del corte */
  --color-info:        #0e7490;   /* cyan — informativo */

  /* Confidence (mapeo directo del dominio) */
  --color-confidence-high: var(--color-success);
  --color-confidence-low:  var(--color-warning);

  /* Data quality */
  --color-quality-high:   var(--color-success);
  --color-quality-medium: var(--color-warning);
  --color-quality-low:    var(--color-danger);

  /* KIOSKO — paleta dark obligatoria, optimizada para conducción nocturna */
  --kiosko-bg:        #000000;
  --kiosko-text:      #f8fafc;
  --kiosko-accent:    #1e40af;
  --kiosko-warning:   #f59e0b;   /* ámbar de cabina, NO blanco */
}
```

### Tipografía

```
   FUENTE PRINCIPAL
   System UI stack: -apple-system, BlinkMacSystemFont, "Segoe UI",
                    Roboto, "Helvetica Neue", Arial, sans-serif
   (No web fonts en V1 — performance + no FOUC)

   ESCALAS
   text-xs    11px   datos secundarios, metadatos
   text-sm    13px   texto general
   text-base  15px   párrafos
   text-lg    17px   subtítulos
   text-xl    20px   títulos secundarios
   text-2xl   24px   títulos principales
   text-3xl   30px   números grandes (puesto del ranking, nota)
   text-4xl   36px   solo en kiosko (legibilidad cabina)

   PESOS
   400  regular (texto)
   500  medium (énfasis suave)
   600  semibold (subtítulos)
   700  bold (títulos principales)
```

### Espaciado

```
   Sistema base 4px.
   spacing-1 (4px) · spacing-2 (8px) · spacing-3 (12px) · spacing-4 (16px)
   spacing-6 (24px) · spacing-8 (32px) · spacing-12 (48px) · spacing-16 (64px)

   En el KIOSKO, padding mínimo 16px en cualquier elemento clickable
   y target ≥ 64×64 px (uso con guantes).
```

### Bordes y sombras

```
   border-radius
     0     bordes rectos (tablas, kiosko)
     4px   default
     8px   cards
     12px  modales

   shadow
     none / sm / md / lg / xl  — escala estándar Tailwind
     KIOSKO: cero sombras (pantalla plana, alto contraste)
```

## 0.4 Estados globales — decisión firme

**Toda pantalla con datos del backend tiene cuatro estados. NO improvises.**

### Loading

```
   ▶ Carga inicial de pantalla:
     <SkeletonScreen> que imita la forma del contenido.
     - Matriz: skeleton de 10 filas × 4 columnas.
     - Ranking: skeleton de 20 filas.
     - Detalle attempt: skeleton del map + score breakdown.

   ▶ Acción del usuario (submit, click):
     <Button loading={true}> con spinner inline + texto deshabilitado.

   ▶ Refetch en background (React Query refetchOnWindowFocus):
     <SubtleRefreshIndicator> en la esquina, sin bloquear contenido.

   ▶ Pagina entera bloqueada (raro, p.ej. cierre de convocatoria):
     <BlockingOverlay> con mensaje explícito.
```

### Empty (datos vacíos pero sin error)

```
   <EmptyState> con:
     - Icono ilustrativo (lucide-react o similar)
     - Mensaje primario ("Aún no tienes intentos")
     - Mensaje secundario opcional ("Tu primer intento aparecerá aquí
       después de tu primera ruta")
     - CTA opcional (botón a otra pantalla)
```

### Error

```
   ▶ Error de red / 500:
     <ErrorState variant="server"> con:
       - Mensaje "Algo salió mal. Reintentá."
       - Botón "Reintentar"
       - Detail technical visible solo si debug=true (dev tools)

   ▶ Error 403:
     <ErrorState variant="forbidden"> con:
       - Mensaje "No tenés permiso para ver esto"
       - Link "Volver"

   ▶ Error 404:
     <ErrorState variant="notfound"> con:
       - Mensaje contextual ("Esta convocatoria ya no existe")
       - Link "Volver al listado"

   ▶ Error 422 (validación de form):
     Mostrar inline en el form con react-hook-form errors.
     NO usar <ErrorState> para validación.

   ▶ Error 429 (rate limit):
     <ErrorState variant="ratelimit"> con:
       - Mensaje "Esperá un momento antes de reintentar"
       - Auto-retry con countdown visible
```

### Success

```
   <Toast variant="success"> efímero (3s) tras acción exitosa.
   Para acciones críticas (cierre de convocatoria), usar <ConfirmDialog>
   antes Y <SuccessScreen> después.
```

## 0.5 Responsive — qué pantallas en qué dispositivos

```
   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   │   PORTAL ADMIN          desktop only (≥1280px)           │
   │   PORTAL MANAGER        desktop primario (≥1280px)       │
   │                         tablet supported (≥1024px) — la  │
   │                         matriz se simplifica             │
   │   PORTAL ALUMNO         mobile-first (≥360px)            │
   │                         tablet (≥768px)                  │
   │                         desktop (≥1024px)                │
   │   KIOSKO                pantalla fija dedicada en cabina │
   │                         (resolución a confirmar con      │
   │                         CMadrid; objetivo 1280×800       │
   │                         landscape, dark mode)            │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
```

**Decisión firme:**
- Admin y Manager NO se diseñan para móvil. Si CMadrid lo pide en Fase 2, se evalúa.
- Alumno SÍ es mobile-first (es el único que va a usar el sistema desde su teléfono).
- Kiosko es resolución única (objetivo 1280×800, a confirmar con el hardware real cuando se instale).

## 0.6 Accesibilidad — WCAG AA mínimo

Para una administración pública española, accesibilidad es **obligatorio legalmente**.

```
   ▶ Contraste de color
     - Texto normal: ratio ≥ 4.5:1 contra el fondo
     - Texto grande (≥18pt o ≥14pt bold): ratio ≥ 3:1
     - Verificar con: webaim.org/resources/contrastchecker

   ▶ Navegación por teclado
     - Todos los elementos interactivos accesibles con Tab
     - Focus visible (outline propio, no remover el de browser)
     - Atajos: Esc cierra modales, Enter confirma forms

   ▶ ARIA
     - aria-label en iconos sin texto
     - aria-describedby en inputs con ayuda
     - role="alert" en error banners
     - aria-live="polite" en notificaciones

   ▶ Imágenes
     - alt text descriptivo
     - decorativas: alt=""

   ▶ Forms
     - <label> asociado a <input> (htmlFor + id)
     - Mensaje de error vinculado vía aria-describedby
     - Estado de validación con aria-invalid

   ▶ Tests automáticos
     - axe-core integrado en Playwright — coordiná con Joel el día 1
       quién lo configura (setup del runner es de Joel, reglas y suite
       de smoke a11y las podés definir vos)
     - Vitest + jest-axe en componentes críticos
```

## 0.7 i18n — V1 es-ES, preparado para más

```
   IDIOMAS V1
     es-ES   (único)

   ESTRUCTURA
   src/i18n/
   ├── index.ts            ← inicialización i18next
   ├── es-ES.json          ← claves
   └── keys.ts             ← export const Keys = {...} type-safe

   NAMING DE CLAVES
     <portal>.<pantalla>.<elemento>
     ej:  manager.matrix.title
          alumno.dashboard.standing.dentro_del_corte
          kiosko.idle.tap_card_prompt

   USO EN COMPONENTES
     const { t } = useTranslation();
     return <h1>{t('manager.matrix.title')}</h1>;

   FECHAS
     Siempre Europe/Madrid. Usar date-fns-tz:
       formatInTimeZone(date, 'Europe/Madrid', 'dd/MM/yyyy HH:mm')

   PLURALES
     i18next maneja plurales nativos:
       "rutas_completadas": "{{count}} ruta completada",
       "rutas_completadas_plural": "{{count}} rutas completadas"
```

**Regla firme:** **NUNCA hardcodear strings** en componentes. Si te pillás haciéndolo, parar y crear la clave i18n.

## 0.8 Estados de la pantalla D5 (Cierre de Convocatoria) — TypeScript types

D5 es la pantalla más compleja. Tiene tres estados visuales según `convocatoria.status`. Acá el TypeScript explícito:

```typescript
// types/domain.ts
export type ConvocatoriaStatus = 'OPEN' | 'CLOSING' | 'CLOSED' | 'LOCKED';

export interface ConvocatoriaDetail {
  id: string;
  name: string;
  status: ConvocatoriaStatus;
  starts_at: string;        // ISO en Europe/Madrid
  closes_at: string;
  plazas: number;

  // Solo populados si status = CLOSING o más
  closing_initiated_at: string | null;
  closing_admin_id: string | null;
  closing_admin_name: string | null;

  // Solo populados si status = CLOSED o LOCKED
  closed_at: string | null;
  confirming_admin_id: string | null;
  confirming_admin_name: string | null;
  acta_pdf_url: string | null;
  reversal_window_until: string | null;  // null si LOCKED

  // Para preview/decisión
  total_candidatos: number;
  total_aptos: number | null;        // null si OPEN/CLOSING
  total_no_aptos: number | null;
}
```

```typescript
// pages/admin/CerrarConvocatoria.tsx
function CerrarConvocatoria({ id }: { id: string }) {
  const { data, isLoading, error } = useConvocatoria(id);
  const { user } = useAuth();

  if (isLoading) return <SkeletonScreen />;
  if (error)     return <ErrorState variant="server" onRetry={refetch} />;
  if (!data)     return <ErrorState variant="notfound" />;

  switch (data.status) {
    case 'OPEN':    return <D5_A_Preview convocatoria={data} />;
    case 'CLOSING': return <D5_B_Confirm convocatoria={data} currentUser={user} />;
    case 'CLOSED':  return <D5_C_Reverse convocatoria={data} currentUser={user} />;
    case 'LOCKED':  return <D5_D_Locked convocatoria={data} />;
  }
}
```

## 0.9 Convención modal vs pantalla

**Aclaración:** "modal" en la doc no siempre significa overlay. Voy a fijar la convención.

```
   MODAL = overlay con backdrop oscuro + cierre con Esc
     - M6 OverrideModal/AuditRequestModal: SÍ es modal (overlay)
     - M7 ReevaluateModal:                  SÍ es modal
     - K4 RecoveryModal:                    SÍ es modal (full-screen kiosko)

   PANTALLA = ruta propia con URL
     - M5 Ranking: pantalla, /manager/convocatoria/:id/ranking
     - M6 Vista Examinador: pantalla, /manager/attempts/:id
     - D5 Cierre de Convocatoria: pantalla, /admin/convocatorias/:id/close

   POPOVER / DROPDOWN = anchored al elemento
     - Filtros, menús contextuales
```

Si el wireframe te confunde, la regla es: si tiene URL única y back button, es pantalla. Si vive sobre otra pantalla, es modal.

## 0.10 Convención de datos React Query

```typescript
// api/convocatorias.ts
export function useConvocatoria(id: string) {
  return useQuery({
    queryKey: ['convocatoria', id],
    queryFn: () => api.get(CONVOCATORIA_ENDPOINTS.detail(id)),
    staleTime: 30_000,    // datos frescos por 30s
  });
}

export function useCloseInitiate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params) => api.post(CONVOCATORIA_ENDPOINTS.closeInitiate(params.id), params.body),
    onSuccess: (_, params) => {
      qc.invalidateQueries({ queryKey: ['convocatoria', params.id] });
    },
  });
}
```

**Reglas:**
- `queryKey` siempre array, primer elemento es el "namespace" del recurso.
- `staleTime` razonable según volatilidad del dato (ranking 30s, lista de rutas 5 min).
- `invalidateQueries` tras mutaciones — no refetch manual.

## 0.11 Mockups visuales

Para 14 días no vamos a tener Figma profesional. **Decisión firme:**

```
   V1 (este sprint)
     - Wireframes ASCII en este doc + tokens del §0.3 = guía visual
     - Vos diseñás "razonable y consistente" usando los tokens
     - Antonio aprueba/ajusta en daily
     - No buscamos UI premium, buscamos UI funcional, accesible y limpia

   Fase 2
     - Si CMadrid pide retoque visual o branding propio,
       contratamos diseñador y rehacemos
     - El sistema de tokens permite reskin sin tocar componentes
```

**Regla:** si en algún punto sentís que necesitás un diseñador para no improvisar, **decílo en daily YA**. No esperes al día 12.

## 0.12 Tu primer commit objetivo (día 2 de la mañana)

```
   1. Vite + React + Tailwind + TypeScript strict configurado
   2. tokens.css aplicado y Tailwind extendido con ellos
   3. Estructura de carpetas creada (vacías o stubbed)
   4. config/api.ts con AUTH_ENDPOINTS y CONVOCATORIA_ENDPOINTS
   5. Componentes ui/ atómicos: Button, Input, Card, Badge
   6. Componentes feedback/: SkeletonScreen, ErrorState, EmptyState
   7. Login Manager (M1) funcionando contra backend mock
   8. Test Vitest del componente Button
   9. PR mergeado, CI verde
```

Eso es tu hito 1. Si lo tenés el martes a mediodía, vamos bien.

---

# 1. Qué construimos (5 minutos)

**Training** es un sistema de evaluación competitiva (oposición pública española) para candidatos a conductor de camión de bomberos en CMadrid. ~265 candidatos compiten por un nº fijo de plazas. El sistema mide objetivamente la conducción, calcula una nota por cada intento, mantiene un ranking, y al cierre de la convocatoria emite la decisión APTO/NO_APTO según puesto + plazas.

```
   Modelo OPOSICIÓN (no escolar):
   · El sistema NO emite "apto/no apto" por intento.
   · El sistema emite una NOTA por intento.
   · El ranking se actualiza diariamente.
   · Al cierre se emite APTO/NO_APTO según ranking final + plazas.
   · Las notas son INMUTABLES.
   · El ranking es PROVISIONAL hasta el cierre.
   · Tras 24h post-cierre queda LOCKED de forma absoluta.
```

**Cuatro tipos de usuario** (= tus 4 portales):

```
   Alumno (candidato)        — consulta sus notas y puesto, pide auditorías
   Manager (instructor)      — supervisa convocatoria, RESUELVE auditorías. SOLO LECTURA del ranking.
   Admin                     — configura sistema. EJECUTA cierre con doble validación.
   Conductor en cabina       — pasa tarjeta RFID. Pantalla simple, modo oscuro, NO ve notas.
```

---

# 2. Tu territorio de código

```
training/apps/web/                       ← TU TERRITORIO COMPLETO
├── src/
│   ├── pages/
│   │   ├── auth/                        ← LoginAdmin, LoginManager, LoginAlumno
│   │   ├── manager/                     ← LO MÁS IMPORTANTE
│   │   ├── alumno/
│   │   ├── admin/
│   │   └── kiosko/                      ← SISTEMA CRÍTICO
│   ├── components/                      ← <MapViewer>, <Timeline>, <Matrix>, ...
│   ├── stores/                          ← Zustand (auth, ui, kiosko)
│   ├── api/                             ← React Query hooks
│   └── config/api.ts                    ← TODAS las URLs aquí
└── package.json
```

**Vos NO tocás:**
- backend (`apps/api`, `apps/worker`, `packages/`)
- `prisma/schema.prisma`
- código de Webfleet (Antonio)

---

# 3. Reglas no negociables — leelas, entendelas

```
   1. TODAS las URLs de API en `config/api.ts`. Nunca hardcodear "localhost:9998".
   2. React Query SIEMPRE para datos del servidor. Nunca fetch directo en componentes.
   3. Zustand SOLO para:
      - Estado UI global (sidebar abierto, tema, idioma)
      - Estado del kiosko (offline persistido en IndexedDB)
      NO uses Zustand para datos del servidor.
   4. Componentes <500 líneas. Si pasa, refactorizás.
   5. Wrappers para librerías externas. Nunca importás `from 'leaflet'`
      en una página. Importás `from '@/components/MapViewer'`.
   6. Dark mode kiosko es REQUISITO (no opcional).
   7. Eventos low confidence se MUESTRAN, no se esconden.
   8. Override sin justificación NO se permite (validación frontend Y backend).
   9. TypeScript strict. Cero `any` sin justificación.
   10. Notas son inmutables. Manager NO modifica notas (solo audit request).
   11. Alumno NO ve telemetría cruda (gráficas de aceleración, datos sensor).
   12. Kiosko NUNCA muestra notas. Nunca.
```

---

# 4. Stack obligatorio

```
   React 18 + Vite 6 + TypeScript strict
   Tailwind 4 (con tokens propios)
   React Query 5 (datos del servidor)
   Zustand 5 (estado UI global y kiosko offline)
   Leaflet (mapas, envuelto en wrapper)
   Chart.js 4 (charts, envuelto en wrapper)
   i18next (es-ES para V1)
   Vitest (unit tests)
   Playwright (E2E críticos — los hace Joel mayormente)
```

---

# 5. Tu calendario día por día

```
SEMANA 1
────────
DÍA 1 (mar 28/04)  Kickoff con todo el equipo a las 09:00.
                   Scaffolding del repo + Vite + Tailwind + tokens (en pantalla
                   compartida con Antonio + Jesús + Joel, no por separado).
                   Primer PR: rama chore/setup-alejandro.
DÍA 2 (mié 29/04)  Layouts base de los 3 portales + páginas login (M1, A1, D1).
DÍA 3 (jue 30/04)  Login funcionando contra backend. Routing protegido.
                   Empezar wrapper <MapViewer>.
DÍA 4 (vie 01/05)  FESTIVO — Día del Trabajador, España. Sin trabajo planificado.

SEMANA 2
────────
DÍA 7  (lun 04/05) Componente <Matrix> con datos mock. Virtualización react-window.
                   Estructura vista examinador (M5/M6). Layout sin datos.
DÍA 8  (mar 05/05) Conectar matriz con datos reales (React Query). Filtros.
                   Vista examinador completa con datos reales.
                   PANTALLA NUEVA: Ranking del manager (M5 — ver §9.4 paper maestro).
DÍA 9  (mié 06/05) Modal Override (M6) + Modal Reevaluación (M7) +
                   Portal alumno completo (A2 con StandingCard, A3, A4, A5, A6).
DÍA 10 (jue 07/05) KIOSKO completo (K1, K2, K3, K4, K5, K6) +
                   Pantalla cierre de convocatoria (D5 — flujo 3 pasos).
DÍA 11 (vie 08/05) Admin: D2, D3, D4, D5, D6, D7, D8, D9, D10, D11
                   (con Simulador D12 prioridad).
DÍA 12 (sáb 09/05) TORTURA del kiosko (Joel lidera, vos apoyás — voluntario).
DÍA 13 (dom 10/05) Pulido final + ensayo demo.

DÍA 14 (lun 11/05) — REUNIÓN CMADRID
```

> **Nota sobre el viernes 1 de mayo:** España tiene festivo nacional (Día del Trabajador). El plan absorbe la pérdida moviendo la matriz al lunes 04/05 y comprimiendo las semanas. Si vemos que vamos justos, hablamos con Antonio antes del fin de la semana 1.

---

# 6. Catálogo de pantallas — vista general

```
   PORTAL MANAGER (9 pantallas)
   ────────────────────────────
   M1  · Login Manager
   M2  · Dashboard Manager
   M3  · Lista de Convocatorias
   M4  · La Matriz (alumno × ruta)         ← CORE
   M5  · Ranking de la Convocatoria        ← NUEVO v5/v6
   M6  · Vista del Examinador (detalle attempt)
   M7  · Modal Override / Audit Request
   M8  · Perfil del Alumno (desde fila matriz)
   M9  · Análisis de Ruta (desde columna matriz)

   PORTAL ALUMNO (5 pantallas)
   ───────────────────────────
   A1  · Login Alumno
   A2  · Dashboard del Alumno (con StandingCard)
   A3  · Historial de Attempts
   A4  · Detalle Pedagógico
   A5  · Audit Request Form
   A6  · Módulo de Evolución

   PORTAL ADMIN (13 pantallas)
   ───────────────────────────
   D1  · Login Admin
   D2  · Dashboard Admin
   D3  · CRUD Convocatorias
   D4  · Editor de Convocatoria
   D5  · Cierre de Convocatoria (3 PASOS — crítico)
   D6  · CRUD Rutas
   D7  · Editor de Ruta (con mapa)
   D8  · CRUD RFID
   D9  · CRUD Kioskos
   D10 · Pairing Kiosko
   D11 · Listado Scoring Versiones (read-only V1)
   D12 · SIMULADOR DE SCORING                ← Joel implementa, vos lo enmarcás
   D13 · Gestión Usuarios

   KIOSKO (6 pantallas)
   ────────────────────
   K1  · Pairing Kiosko (one-time)
   K2  · Idle (esperando RFID)
   K3  · Active (attempt en curso)
   K4  · Recovery Modal
   K5  · Admin Panel (acceso técnico, long-press logo)
   K6  · Logs Export
```

---

# 7. PORTAL MANAGER — pantallas detalladas

## M1 — Login Manager

| Aspecto | Detalle |
|---|---|
| **Endpoint** | `POST /auth/login` con `role: MANAGER` |
| **Estados** | idle, submitting, error |
| **Validación** | email formato, password mínimo 8 |
| **Edge cases** | credenciales inválidas → error inline; cuenta bloqueada → mensaje específico |

## M2 — Dashboard Manager

| Endpoint | Componentes |
|---|---|
| `GET /convocatorias?manager_id=me` | Cards de convocatorias activas, badge de auditorías pendientes |

```
   ┌─────────────────────────────────────────────────────┐
   │ Hola, Carlos │  notif (3) │ logout                  │
   ├─────────────────────────────────────────────────────┤
   │  CONVOCATORIAS ACTIVAS                              │
   │  ┌──────────────────┐  ┌──────────────────┐         │
   │  │ Convocatoria 26-A│  │ Convocatoria 26-B│         │
   │  │ 200 candidatos   │  │ 150 candidatos   │         │
   │  │ Plazas: 50       │  │ Plazas: 30       │         │
   │  │ Cierre: 15/06/26 │  │ Cierre: 30/06/26 │         │
   │  │ ⚠ 3 auditorías   │  │                  │         │
   │  │ [VER MATRIZ]     │  │ [VER MATRIZ]     │         │
   │  │ [VER RANKING]    │  │ [VER RANKING]    │         │
   │  └──────────────────┘  └──────────────────┘         │
   │  AUDITORÍAS PENDIENTES                              │
   │  ┌─────────────────────────────────────────┐        │
   │  │ Juan P. · Ruta A · solicitud 14/05      │        │
   │  │ Maria G. · Ruta C · solicitud 13/05     │        │
   │  └─────────────────────────────────────────┘        │
   └─────────────────────────────────────────────────────┘
```

## M3 — Lista de Convocatorias

`GET /convocatorias`. Filtros: open/closing/closed. Click → M4 (Matrix).

## M4 — LA MATRIZ (alumno × ruta) — la pantalla más importante

| Endpoint | Componente | Performance |
|---|---|---|
| `GET /matrix?convocatoria=:id` | `<Matrix>` virtualizado con `react-window` | Soportar 265 alumnos × N rutas sin lag |

**Cada celda muestra solo NOTA, no APTO/NO_APTO** (eso es por convocatoria, no por intento).

```
   ┌───────────────────────────────────────────────────────────────┐
   │ Convocatoria 2026-A · 200 candidatos · Plazas: 50            │
   │ [Ver RANKING ▶]  Filtros: ...                                │
   ├───────────────────────────────────────────────────────────────┤
   │              RUTA-A    RUTA-B    RUTA-C    RUTA-D             │
   │            ┌────────┬────────┬────────┬────────┐              │
   │  Alumno1   │ 8.8 HQ │ 7.2    │ — pend │ — no   │              │
   │            ├────────┼────────┼────────┼────────┤              │
   │  Alumno2   │ 6.5 HQ │ 7.0 HQ │ 5.8 LQ⚠│ 7.2 HQ │              │
   │            ├────────┼────────┼────────┼────────┤              │
   │  Alumno3   │ —      │ — pend │ —      │ —      │              │
   │            └────────┴────────┴────────┴────────┘              │
   │                                                               │
   │  Click celda  → Vista del Examinador (M6)                     │
   │  Click fila   → Perfil del Alumno (M8)                        │
   │  Click columna→ Análisis de Ruta (M9)                         │
   └───────────────────────────────────────────────────────────────┘
```

**Estados de cada celda:**

```
   no_intentado    →  "—"
   en_curso        →  "⏱ pend."
   completado_HQ   →  "<nota> HQ" (data quality alta)
   completado_MQ   →  "<nota> MQ" (data quality media)
   completado_LQ   →  "<nota> LQ ⚠" (data quality baja, alerta)
   pending_review  →  "⏱ data review"
   abandonado      →  "✗ abandonado"
   interrupted     →  "⚠ interrumpido" (otra tarjeta cerró)
```

**Indicadores de atención (badges visibles):**
- 3+ suspensos consecutivos en una ruta → ⚠ riesgo de bloqueo
- Reevaluaciones existentes → ↻
- Auditorías pendientes → 🔍

## M5 — Ranking de la Convocatoria (NUEVO v5/v6)

**La pieza visual clave para el cliente CMadrid.**

| Endpoint | Componente |
|---|---|
| `GET /convocatorias/:id/ranking` | `<Ranking>` con scroll virtualizado |

```
   ┌──────────────────────────────────────────────────────────────────┐
   │ Ranking · Convocatoria 2026-A                                    │
   │ Plazas: 50 · Total candidatos: 200                               │
   │ Última actualización: 14/05/26 06:00 (Madrid)                    │
   │ Estado: PROVISIONAL                                              │
   │                                                                  │
   │ Filtros: [solo dentro del corte ▾] [solo con auditoría ▾] ...    │
   ├──────────────────────────────────────────────────────────────────┤
   │ PUESTO  CANDIDATO          NOTA   RUTAS    AUDITORÍAS  CORTE     │
   │   1     Juan Pérez         8.86   4 / 4    —           ✓ DENTRO  │
   │   2     Pedro López        8.45   4 / 4    —           ✓ DENTRO  │
   │   3     María García       8.21   4 / 4    1 ⚠         ✓ DENTRO  │
   │   ...                                                            │
   │  49     Ana Romero         6.63   4 / 4    —           ✓ DENTRO  │
   │  50     Diego Fernández    6.50   3 / 4    —           ✓ DENTRO  │
   │ ─────────────────────────  CORTE PROVISIONAL  ─────────────────  │
   │  51     Luis Castro        6.45   4 / 4    —           ✗ FUERA   │
   │  52     Carla Soto         6.40   3 / 4    —           ✗ FUERA   │
   │   ...                                                            │
   │ 200     Marta Bello        2.10   1 / 4    —           ✗ FUERA   │
   │                                                                  │
   │ Click fila → perfil del alumno (M8)                              │
   │ Click ⚠ (auditoría) → modal con auditoría pendiente              │
   └──────────────────────────────────────────────────────────────────┘
```

**Interactividad:**
- Click fila → M8 (perfil del alumno)
- Click ⚠ → M7 modal de auditoría pendiente
- Auto-refresh cada 60s (pero el dato real solo cambia 1x al día)
- Indicador prominente "Estado: PROVISIONAL" hasta el cierre. Tras LOCKED: "Estado: FINAL".

## M6 — Vista del Examinador (detalle de attempt) — sin override

**Cambio crítico v5: NO hay botón "SOBREESCRIBIR VEREDICTO".** El manager ve la información, NO modifica notas. Solo puede:
- Resolver auditoría si el alumno la solicitó (M7)
- Crear reevaluación si la auditoría procede

| Endpoints | Componentes |
|---|---|
| `GET /attempts/:id`, `GET /attempts/:id/audit` | `<MapViewer>`, `<Timeline>`, `<ScoreBreakdown>`, `<ConfidenceBadge>`, `<DataQualityBadge>` |

```
   ┌──────────────────────────────────────────────────────────────┐
   │ ← volver  │  Juan Pérez · Ruta A · 14/05 09:32 · 8.8        │
   │           │  data_quality: HIGH ✓   detector: v1.3           │
   │           │  criteria: v2.1   ↻ tiene 1 reevaluación         │
   ├──────────────────────────────────────────────────────────────┤
   │  ┌──────────────────────┐  ┌──────────────────────────────┐  │
   │  │     <MapViewer>      │  │  <ScoreBreakdown>            │  │
   │  │   ruta del alumno    │  │  (lee /attempts/:id/audit)   │  │
   │  │   con eventos        │  │  Estabilidad   3.4/4.0       │  │
   │  │   marcados:          │  │  └─ Detalle:                 │  │
   │  │     ●  evento HQ     │  │     · frenada brusca         │  │
   │  │     ◯  evento LQ     │  │       threshold: 8.0         │  │
   │  │                      │  │       observed: 11.0         │  │
   │  │                      │  │       contribution: -0.3     │  │
   │  └──────────────────────┘  │  Velocidad     2.7/3.0       │  │
   │                            │  Ruta          1.4/1.5       │  │
   │                            │  Conducción    1.2/1.5       │  │
   │                            │  ──────────────────          │  │
   │                            │  TOTAL         8.8/10        │  │
   │                            └──────────────────────────────┘  │
   │  ┌─────────────────────────────────────────────────────────┐ │
   │  │  <Timeline> unificado (sensor + Webfleet)               │ │
   │  │  09:32  ●─sensor─frenada─[HQ]                           │ │
   │  │  09:35  ◯─webfleet─exceso vel.─[LQ ⚠]                   │ │
   │  │  09:41  ●─sensor─acel.lateral─[HQ]                      │ │
   │  │  ...                                                    │ │
   │  └─────────────────────────────────────────────────────────┘ │
   │                                                              │
   │  Si el alumno solicitó AUDITORÍA:                            │
   │  ┌─────────────────────────────────────────────────────┐    │
   │  │ Solicitud de auditoría - 14/05 17:32                │    │
   │  │ Razón del alumno: "Hubo un atasco en la rotonda..." │    │
   │  │ [REVISAR Y RESPONDER]                               │    │
   │  └─────────────────────────────────────────────────────┘    │
   │                                                              │
   │  [VOLVER A MATRIZ]                                           │
   │  (sin botones de override — nada de modificar la nota)       │
   └──────────────────────────────────────────────────────────────┘
```

**Estados especiales:**
- `data_quality = LOW` → banner amarillo: *"datos con baja calidad, validá antes de confiar"*
- `status = pending_data_review` → banner rojo: *"este attempt no se cerró automáticamente; razón: [...]"*
- Si tiene reevaluaciones → link "ver historial de reevaluaciones"

## M7 — Modal Audit Request

| Endpoint | Validación |
|---|---|
| `PATCH /audit-requests/:id` | Resolución obligatoria con justificación ≥30 chars |

```
   ┌─────────────────────────────────────────────┐
   │ Auditoría — solicitada por Juan Pérez       │
   ├─────────────────────────────────────────────┤
   │ Intento: Ruta A · 14/05 09:32 · nota 6.8    │
   │ Razón del alumno:                           │
   │ ┌──────────────────────────────────────┐   │
   │ │ Hubo un atasco en la rotonda no       │   │
   │ │ previsible que me forzó a frenar      │   │
   │ │ varias veces.                          │   │
   │ └──────────────────────────────────────┘   │
   │ Tu resolución:                              │
   │ ( ) Confirmar la nota original              │
   │ ( ) Crear reevaluación                      │
   │ ( ) Rechazar la solicitud (sin mérito)      │
   │ Justificación de tu decisión (≥30 chars):   │
   │ ┌──────────────────────────────────────┐   │
   │ │ Texto libre...                        │   │
   │ └──────────────────────────────────────┘   │
   │ [CANCELAR]              [CONFIRMAR]         │
   └─────────────────────────────────────────────┘
```

**Status mapping:**
- "Confirmar la nota original" → `AuditStatus.CONFIRMED`
- "Crear reevaluación" → `AuditStatus.REEVALUATED` + llama `POST /attempts/:id/reevaluate`
- "Rechazar la solicitud" → `AuditStatus.REJECTED`

## M8 — Perfil del Alumno

`GET /students/:id` (rol ≥ MANAGER). Muestra historial de todos los intentos del alumno + evolución cualitativa.

## M9 — Análisis de Ruta (de toda la cohorte)

`GET /routes/:id/cohort-stats?convocatoria=X`. Útil para detectar si una ruta está mal calibrada (todos suspenden).

```
   Resumen:
   25 alumnos · 28 attempts (3 reevaluaciones)
   Tasa aprobación: 76% (19/25)
   Score medio: 78.4 / 100
   data_quality: 22 HQ · 4 MQ · 2 LQ

   Eventos más frecuentes:
   1. Frenada brusca (74% alumnos)
   2. Exceso velocidad (32%)
   3. Acel. lateral (28%)
```

---

# 8. PORTAL ALUMNO — pantallas detalladas

## A1 — Login Alumno

`POST /auth/login` con `role: ALUMNO`.

> Si `User.privacy_consent_accepted_at IS NULL`, el sistema bloquea el login y muestra pantalla de aceptación del aviso de privacidad GDPR antes de continuar.

## A2 — Dashboard del Alumno (con StandingCard NUEVO v5/v6)

| Endpoint | Componente |
|---|---|
| `GET /students/me/cohort-routes`, `GET /students/me/standings` | `<StandingCard>` |

```
   ┌─────────────────────────────────────────────────────┐
   │ Hola Juan,                                          │
   ├─────────────────────────────────────────────────────┤
   │  ┌─────────────────────────────────────────────┐   │
   │  │  TU PROGRESO EN LA CONVOCATORIA 2026-A      │   │ ← <StandingCard>
   │  │                                             │   │
   │  │  Rutas completadas: 3 de 4                  │   │
   │  │  Tu nota media:     7.4 / 10                │   │
   │  │                                             │   │
   │  │  Tu puesto provisional: 74 de 200           │   │
   │  │  Plazas: 50                                 │   │
   │  │                                             │   │
   │  │  ▼ Estás FUERA del corte provisional        │   │
   │  │    (provisional — el ranking final solo     │   │
   │  │     se conoce al cierre 15/06/26)           │   │
   │  └─────────────────────────────────────────────┘   │
   │                                                     │
   │  TUS RUTAS                                          │
   │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │
   │  │ Ruta A     │ │ Ruta B     │ │ Ruta C     │       │
   │  │ 8.8 / 10   │ │ 7.2 / 10   │ │ 5.8 / 10   │       │
   │  │ HQ ✓       │ │ HQ ✓       │ │ MQ         │       │
   │  │ último 25/4│ │ último 23/4│ │ último 23/4│       │
   │  │ [VER]      │ │ [VER]      │ │ [VER]      │       │
   │  └────────────┘ └────────────┘ └────────────┘       │
   │  ┌────────────┐                                     │
   │  │ Ruta D     │                                     │
   │  │ — pendiente│                                     │
   │  └────────────┘                                     │
   └─────────────────────────────────────────────────────┘
```

**REGLA FIRME: NO se muestra "APTO" ni "NO_APTO" en ninguna ruta. Solo nota.**

> El endpoint `/standings` es **plural** y devuelve un array, porque un alumno puede estar en múltiples convocatorias activas. Default: mostrar la convocatoria con cierre más próximo.

## A3 — Historial de Attempts

`GET /students/me/history`. Tabla cronológica.

```
   ┌────────────────────────────────────────────────────────┐
   │ FECHA       RUTA   NOTA   CALIDAD    AUDITORÍA         │
   │ ──────────────────────────────────────────────────     │
   │ 25/04 09:32 Ruta A 8.8    ✓ alta     —                 │
   │ 23/04 11:15 Ruta C 7.1    ✓ alta     ↻ reev de 5.8     │
   │ 23/04 10:00 Ruta C 5.8    ◐ media    Confirmada        │
   │ 20/04 09:00 Ruta B 7.6    ✓ alta     —                 │
   └────────────────────────────────────────────────────────┘
```

## A4 — Detalle Pedagógico

**REGLA CRÍTICA: NO se muestra telemetría cruda.** Solo infracciones contextualizadas en lenguaje pedagógico.

```
   ¿POR QUÉ?

   En esta ruta el sistema detectó:

   ▸ 5 frenadas bruscas
     (la mayoría en el tramo del semáforo de la plaza Mayor)
     → Esto resta 12 puntos de Estabilidad

   ▸ 2 excesos de velocidad (en la avenida principal)
     → Esto resta 8 puntos de Velocidad

   ▸ 1 desviación de ruta (te saliste 200m del recorrido)
     → Esto resta 5 puntos de Ruta

   ¿QUÉ PUEDES HACER?

   Tu próximo intento de esta ruta puede mejorar si:
   - Anticipás los semáforos para frenar suave
   - Mantenés velocidad legal en avenidas
   - Seguís el GPS sin desvíos
```

**Reglas firmes:**
- ✗ NO charts de aceleración
- ✗ NO timelines técnicos
- ✗ NO mapas con puntos crudos
- ✓ SÍ texto explicativo + lista de infracciones
- ✓ SÍ sugerencias de mejora

Botón al final: **"Solicitar auditoría de este intento"** → A5.

## A5 — Audit Request Form

| Endpoint | Validación |
|---|---|
| `POST /attempts/:id/audit-request` | Razón obligatoria, mínimo 30 caracteres |

```
   ┌─────────────────────────────────────────────┐
   │ Solicitar auditoría                         │
   ├─────────────────────────────────────────────┤
   │ Intento: Ruta C · 23/04 10:00 · nota 5.8    │
   │ Razón (obligatoria, mínimo 30 caracteres):  │
   │ ┌──────────────────────────────────────┐   │
   │ │ Hubo un atasco en la rotonda no       │   │
   │ │ previsible que me forzó a frenar.     │   │
   │ └──────────────────────────────────────┘   │
   │ Tu solicitud será revisada por un manager.  │
   │ Te notificaremos cuando haya resolución.    │
   │ [CANCELAR]              [ENVIAR]            │
   └─────────────────────────────────────────────┘
```

> En V1 la notificación al alumno sobre la resolución se ve **al iniciar sesión** (banner en dashboard). El email automático llega en Fase 2 (F1).

## A6 — Módulo de Evolución

`GET /students/me/evolution`. Indicadores cualitativos: mejora / estanca / empeora ruta a ruta.

---

# 9. PORTAL ADMIN — pantallas detalladas

## D1 — Login Admin

Idéntico a M1 con `role: ADMIN`.

## D2 — Dashboard Admin

```
   ┌─────────────────────────────────────────────────────┐
   │ Admin Dashboard                                     │
   ├─────────────────────────────────────────────────────┤
   │  CONVOCATORIAS                  ESTADO SISTEMA      │
   │  ┌──────────────────┐          ┌─────────────────┐  │
   │  │ 2026-A · OPEN    │          │ API: ✓          │  │
   │  │   Cierre 15/06   │          │ DB: ✓           │  │
   │  │   195/200 tienen │          │ Webfleet: 22%   │  │
   │  │   3+ rutas       │          │ uso cuota       │  │
   │  ├──────────────────┤          └─────────────────┘  │
   │  │ 2026-B · OPEN    │                                │
   │  └──────────────────┘          KIOSKOS               │
   │                                [4 listados]         │
   │  AUDITORÍAS PENDIENTES                              │
   │  ⚠ 3 solicitudes sin resolver                       │
   │                                                     │
   │  [Convocatorias] [Rutas] [RFID] [Kioskos]           │
   │  [Scoring] [Simulador] [Usuarios]                   │
   └─────────────────────────────────────────────────────┘
```

## D3 — CRUD Convocatorias

`GET /convocatorias`. Tabla con: nombre, status, plazas, candidatos, cierre.

## D4 — Editor de Convocatoria

```
   Nombre [_2026-A_______________________]
   Inicio [01/04/2026]
   Cierre [15/06/2026]   ← público para los candidatos

   Plazas (entero) [_50_]   ← público desde día 1

   Rutas obligatorias:
     ☑ Ruta A · Urbana centro
     ☑ Ruta B · Carretera nacional
     ☑ Ruta C · Mixta con rotonda
     ☑ Ruta D · Polígono industrial

   Ruta principal (criterio 1 de desempate):
     (•) Ruta A    ( ) Ruta B    ( ) Ruta C    ( ) Ruta D

   Status: OPEN   [BOTÓN DE CIERRE — solo si fecha ya llegó]

   [CANCELAR]                  [GUARDAR]
```

## D5 — Cierre de Convocatoria (REESCRITO v6: 3 PASOS)

**Esto es CRÍTICO. La pantalla muestra UNO de los tres estados según `convocatoria.status` y rol del admin.**

### D5-A — Estado "OPEN" — paso 1: Preview

| Endpoint | Auth |
|---|---|
| `POST /convocatorias/:id/close/preview` | ADMIN cualquiera |

```
   ┌──────────────────────────────────────────────────────┐
   │ Cerrar Convocatoria 2026-A — Paso 1 de 3 (PREVIEW)   │
   ├──────────────────────────────────────────────────────┤
   │  Fecha de cierre publicada: 15/06/2026 23:59 (Madrid)│
   │  Estado: OPEN                                        │
   │                                                      │
   │  RESUMEN DEL CIERRE PROVISIONAL                      │
   │  · 198 / 200 candidatos completaron las 4 rutas      │
   │  · 2 candidatos no completaron — sus rutas faltantes │
   │    contarán como 0                                   │
   │  · 0 auditorías pendientes                           │
   │                                                      │
   │  IMPACTO                                             │
   │  · 50 candidatos pasarían a APTO                     │
   │  · 150 candidatos pasarían a NO_APTO                 │
   │                                                      │
   │  [VER ranking final simulado ▾]                      │
   │                                                      │
   │  Si querés iniciar el cierre formal, vas a necesitar │
   │  que un SEGUNDO admin distinto a vos lo confirme.    │
   │                                                      │
   │  [CANCELAR]                  [INICIAR CIERRE — paso 2]│
   └──────────────────────────────────────────────────────┘
```

### D5-B — Estado "CLOSING" — paso 2: confirmación del segundo admin

```
   ┌──────────────────────────────────────────────────────┐
   │ Cerrar Convocatoria 2026-A — Paso 2 de 3 (CONFIRMAR) │
   ├──────────────────────────────────────────────────────┤
   │  Estado: CLOSING                                     │
   │  Iniciado por: María García (admin) hace 12 minutos  │
   │  Iniciado a las: 15/06/2026 09:32 (Madrid)           │
   │                                                      │
   │  ⚠ Este cierre necesita un SEGUNDO admin para        │
   │    confirmarse. María García NO puede confirmar      │
   │    su propio cierre.                                 │
   │                                                      │
   │  Si vos sos María García:                            │
   │     [VOLVER]  (esperá a que otro admin confirme)     │
   │     [CANCELAR EL CIERRE]  → llama /close/abort       │
   │                                                      │
   │  Si vos sos otro admin:                              │
   │     RESUMEN (idéntico al paso 1)                     │
   │     [VER ranking final simulado ▾]                   │
   │                                                      │
   │     Para confirmar, re-introducí tu CONTRASEÑA       │
   │     y escribí el nombre exacto de la convocatoria:   │
   │                                                      │
   │     Contraseña: [________________]                   │
   │     Nombre:     [2026-A___________]                  │
   │                                                      │
   │     [CONFIRMAR CIERRE]                               │
   └──────────────────────────────────────────────────────┘
```

| Endpoint | Auth | Backend valida |
|---|---|---|
| `POST /convocatorias/:id/close/confirm` | ADMIN + re-auth | `auth.user.id !== convocatoria.closing_admin_id` |
| `POST /convocatorias/:id/close/abort` | initiator o SUPER_ADMIN | status = CLOSING |

### D5-C — Estado "CLOSED" — ventana de reversa de 24h

Solo `SUPER_ADMIN` ve botón "Solicitar reversa". `ADMIN` y `MANAGER` solo ven lectura del acta.

```
   ┌──────────────────────────────────────────────────────┐
   │ Convocatoria 2026-A — CERRADA                        │
   ├──────────────────────────────────────────────────────┤
   │  Estado: CLOSED                                      │
   │  Cerrada por: María García (initiate) +              │
   │              Carlos Soto (confirm)                   │
   │  Cerrada el: 15/06/2026 09:47 (Madrid)               │
   │  ACTA: [DESCARGAR PDF · SHA256: a1b2c3...]           │
   │                                                      │
   │  Resultado:                                          │
   │  · 50 APTO · 150 NO_APTO                             │
   │                                                      │
   │  ⚠ VENTANA DE REVERSA                                │
   │  Esta convocatoria pasa a LOCKED (irrevocable        │
   │  absoluto) en: 23h 13m                               │
   │                                                      │
   │  [Solo SUPER_ADMIN ve este botón:]                   │
   │     [SOLICITAR REVERSA]                              │
   └──────────────────────────────────────────────────────┘
```

Pasadas las 24h: el bloque "ventana" desaparece, estado pasa a `LOCKED`, sistema bloquea cualquier UPDATE.

## D6-D11 — CRUD básicos

- **D6**: CRUD Rutas (tabla, click → D7)
- **D7**: Editor de Ruta con `<MapViewer>` + leaflet-draw para dibujar polilínea
- **D8**: Asignación RFID (alumno ↔ tarjeta UID)
- **D9**: Listado Kioskos con last_seen, status
- **D10**: Pairing Kiosko (admin genera token de 16 chars; técnico lo introduce manualmente en el kiosko)
- **D11**: Listado Scoring Versiones (read-only en V1)

## D12 — SIMULADOR DE SCORING (Joel implementa, vos enmarcás)

**La pieza más vendible al cliente CMadrid.** Joel hace la pantalla; vos le ayudás con `<ScoreBreakdown>`, layout, integración con la matriz.

```
   Versión base: [v2.1 (activa) ▾]
   Aplicar a:    [Convocatoria 2026-A ▾]

   Modificar reglas:
   ┌──────────────────────────────────────────────┐
   │ Familia   Regla              Original  Nuevo │
   │──────────────────────────────────────────────│
   │ Estab.    frenada threshold  8.0       10.0  │
   │ Estab.    frenada peso       0.4       0.4   │
   │ ...                                          │
   └──────────────────────────────────────────────┘

   [SIMULAR]

   ──────────────────────────────────

   RESULTADO:

   IMPACTO EN NOTAS
     Attempts afectados: 87
     Diferencia media: +0.45 pts

   IMPACTO EN RANKING
     Candidatos que CAMBIAN de lado del corte:
      → 5 entran en plaza
      → 5 salen de plaza

     Movimientos del top 50:
      - Mayor subida: Pedro M. (+12 puestos)
      - Mayor caída: Laura B. (-8 puestos)

   [VER LISTADO COMPLETO]   [EXPORTAR CSV]
   [DESCARTAR]   [GUARDAR COMO NUEVA VERSIÓN]
```

## D13 — Gestión Usuarios

CRUD usuarios. Asignar roles. Resetear contraseñas. **NO incluye SUPER_ADMIN** (solo otro SUPER_ADMIN puede crear uno).

---

# 10. KIOSKO — sistema crítico (NUEVO v6)

```
   ┌──────────────────────────────────────────────────────┐
   │ ATENCIÓN                                             │
   │                                                      │
   │ El kiosko NO es una página web cualquiera.           │
   │ Es un dispositivo físico operando en cabina de       │
   │ camión, con conexión spotty, guantes, conducción     │
   │ nocturna y batería que se agota.                     │
   │                                                      │
   │ Tratarlo como página normal = pegarse una hostia.    │
   └──────────────────────────────────────────────────────┘
```

## 10.1 UI base

```
   ┌─────────────────────────────────────────────┐
   │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  ← Barra de
   │  ● online  ⏱ 14:23  ↻ 0 pendientes  ⚡ 87% │     estado
   │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │     SIEMPRE visible
   │                                             │
   │     EVALUANDO                               │
   │     JUAN PÉREZ                              │
   │     RUTA A                                  │
   │                                             │
   │     ⏱ 14:23                                  │  ← Solo duración,
   │                                             │     NO score
   │  Pase otra tarjeta para cambiar de alumno   │
   └─────────────────────────────────────────────┘
```

## 10.2 Las 6 pantallas

### K1 — Pairing (one-time)

| Endpoint | Storage |
|---|---|
| `POST /kiosko/pair` | Token guardado en IndexedDB (no localStorage) |

Admin emite un token de 16 caracteres en D10. Técnico lo introduce manualmente en el kiosko al instalarlo.

### K2 — Idle (esperando RFID)

Pantalla en espera. Muestra solo: "Pasá tu tarjeta por el lector". Barra de estado siempre visible arriba.

### K3 — Active (attempt en curso)

Muestra: nombre del alumno, ruta seleccionada, tiempo transcurrido. **NUNCA score.**

### K4 — Recovery Modal

```
   Al abrir el kiosko, si detecta attempt abierto sin sincronizar:

   ATENCIÓN
   Este kiosko tiene un attempt en curso que no se cerró:
        JUAN PÉREZ — Ruta A
        Iniciado: 14:23 (hace 18 min)

   ¿Continuar con este attempt o cerrarlo?
   [ CONTINUAR ]    [ CERRAR ATTEMPT ]

   Si elegís "cerrar", el attempt quedará marcado
   como ABANDONADO.
```

### K5 — Admin Panel (acceso técnico)

**Long-press de 5 segundos sobre el logo del header** → entra a este panel.

```
   Estado:
    Kiosko-03 · Camión 3
    Pairing OK desde 2026-04-15

   Conectividad:
    Online · última sync hace 30s

   Cola offline:
    5 eventos pendientes de sync
    [REINTENTAR SYNC]

   IndexedDB:
    Storage usado: 2.3 MB / 50 MB

   [DESCARGAR LOGS 24H]
   [LIMPIAR HISTORIAL LOCAL]
   [DESVINCULAR KIOSKO]
```

### K6 — Logs Export

Click en "DESCARGAR LOGS 24H" → genera JSON con últimas 24h de eventos del kiosko (RFID taps, sync attempts, errores) y descarga el archivo. Para mandar a Antonio cuando hay problema.

## 10.3 Los 5 mecanismos defensivos

```
1. MODO RECOVERY  (K4)
   Al abrir, si detecta attempt abierto sin sync → modal explícito.

2. ESTADO VISIBLE PERMANENTE  (barra superior en TODAS las pantallas)
   - ●/◯ Online / Offline
   - ⏱ Hora del attempt si hay uno
   - ↻ N eventos pendientes de sync
   - ⚡ Batería del dispositivo

3. LOGS LOCALES EXPORTABLES  (K6)
   Long-press en logo → Admin Panel → descarga 24h.

4. DEBOUNCE RFID  (K3)
   - Misma tarjeta 2x en <2s = ignorada.
   - Tarjeta diferente <500ms = error visible "lectura ambigua".
   - Tarjeta nueva durante attempt activo:
     · si <80% del recorrido completado → marcar ABANDONED del primero
     · pero ANTES, mostrar 5s de espera con botón "estoy en la ruta"
       que el primer alumno puede tocar para cancelar el cambio
     · si toca el botón → se ignora la nueva tarjeta
     · si NO toca → cierra el primero como INTERRUPTED_BY_OTHER_CARD
       (NO penaliza al inocente, no cuenta en ranking)

5. PÉRDIDA DE CONEXIÓN  (K2/K3)
   - Cola IndexedDB con backoff exponencial.
   - Reintentos infinitos.
   - Indicador de cola visible.
   - Si cola > 50 → alerta visible.
```

## 10.4 Reglas duras del kiosko

```
   ▶ Sin inputs de texto (botones grandes ≥64×64 px)
   ▶ Sin scores visibles
   ▶ Wake-lock activado durante attempt (pantalla NO se apaga)
   ▶ Offline-first (IndexedDB + queue)
   ▶ RFID = teclado USB-HID (los lectores baratos emiten keystrokes)
   ▶ Estado siempre visible
   ▶ Dark mode permanente (seguridad nocturna en cabina)
   ▶ ANTES DE CUTOVER: 1 día completo torturando el kiosko a propósito
     (cortar wifi, apagar, doble RFID, batería baja...) — Joel lidera
```

---

# 11. Wrappers reutilizables

```
training/apps/web/src/components/
├── MapViewer/                ← wrapper Leaflet
├── Timeline/                 ← timeline unificado sensor+webfleet
├── Matrix/                   ← virtualizado react-window
├── Ranking/                  ← virtualizado, lee /convocatorias/:id/ranking
├── StandingCard/             ← lee /students/me/standings (alumno)
├── ScoreBreakdown/           ← lee /attempts/:id/audit (granular)
├── ConfidenceBadge/          ← high/low visible
├── DataQualityBadge/         ← high/medium/low
├── AuditRequestModal/
└── ui/                       ← buttons, cards, inputs base
```

**Regla:** las páginas importan `from '@/components/...'`, nunca `from 'leaflet'` directamente.

---

# 12. Estado del frontend

```
   React Query     →  TODOS los datos del servidor (queries + mutations)
   Zustand         →  estado UI global (sidebar, tema, idioma)
                      + estado kiosko offline (persistido IndexedDB con middleware)
   Context         →  un AuthContext por flow:
                        - AuthAdminContext
                        - AuthManagerContext
                        - AuthAlumnoContext
                        - AuthKioskoContext (token de dispositivo)
   localStorage    →  borradores de formularios (override modal, audit form)
                      + theme preference
```

**No Redux. No useReducer global. No useEffect para fetch.**

---

# 13. URLs API — siempre en config/api.ts

```typescript
// apps/web/src/config/api.ts

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:9998';

export const AUTH_ENDPOINTS = {
  login: `${API_BASE}/auth/login`,
  logout: `${API_BASE}/auth/logout`,
  refresh: `${API_BASE}/auth/refresh`,
  me: `${API_BASE}/auth/me`,
  csrf: `${API_BASE}/auth/csrf-token`,
};

export const CONVOCATORIA_ENDPOINTS = {
  list: `${API_BASE}/convocatorias`,
  detail: (id: string) => `${API_BASE}/convocatorias/${id}`,
  ranking: (id: string) => `${API_BASE}/convocatorias/${id}/ranking`,
  closePreview: (id: string) => `${API_BASE}/convocatorias/${id}/close/preview`,
  closeInitiate: (id: string) => `${API_BASE}/convocatorias/${id}/close/initiate`,
  closeConfirm: (id: string) => `${API_BASE}/convocatorias/${id}/close/confirm`,
  closeAbort: (id: string) => `${API_BASE}/convocatorias/${id}/close/abort`,
  closeReverse: (id: string) => `${API_BASE}/convocatorias/${id}/close/reverse`,
  acta: (id: string) => `${API_BASE}/convocatorias/${id}/acta`,
};

// ...etc para ATTEMPTS, STUDENTS, ROUTES, RFID, KIOSKO, etc.
```

**NUNCA hardcodear URLs en componentes. Si te pillás haciéndolo, parar y mover a `config/api.ts`.**

---

# 14. Tu interfaz con el resto del equipo

## Con Antonio

- Antonio escribe el package Webfleet del backend, pero vos NO lo consumís directamente. Lo consume Jesús.
- Antonio es tu jefe técnico: cualquier decisión arquitectónica de frontend (estructura de carpetas, librería nueva) → consultar.

## Con Jesús

- Jesús escribe los endpoints. Vos los consumís.
- **Si Jesús cambia un endpoint** (path, response shape, error codes), te avisa antes.
- **Si vos necesitás algo nuevo del backend**, le pedís. Si entra en sprint, lo agrega; si no, va a Fase 2.
- Errores HTTP estandarizados: 400, 401, 403, 404, 409, 422, 500.

## Con Joel

- Joel implementa el simulador (D12) backend + frontend. Vos le ayudás con UI components reutilizables (`<ScoreBreakdown>`, layouts).
- Joel hace los tests E2E que cruzan tu frontend. Si rompés un selector estable, avisale.
- Joel hace los datos seed. Si necesitás un escenario específico para una pantalla, le pedís.

---

# 15. Tests Vitest críticos (los que tenés que tener)

```
   ✓ Matrix: virtualización funciona con 1000 filas
   ✓ Matrix: indicadores de atención (3+ suspensos, calidad LOW, auditorías)
   ✓ Ranking: corte provisional bien calculado en UI
   ✓ ScoreBreakdown: lee score_audit y muestra granular
   ✓ AuditRequestModal: validación frontend (≥30 chars)
   ✓ AuditRequestModal: 3 opciones (Confirm / Reevaluate / Reject)
   ✓ OverrideModal: NO existe (en v6, manager no modifica notas)
   ✓ Kiosko store: IndexedDB persiste estado tras reload
   ✓ Kiosko: debounce RFID (2s misma, 500ms distinta)
   ✓ Kiosko: dark mode aplica todo el tiempo
   ✓ StandingCard: maneja multi-enrollment (array)
   ✓ Cierre D5: cada estado (OPEN/CLOSING/CLOSED) renderiza la pantalla correcta
   ✓ Cierre D5: validación que el segundo admin sea distinto
```

---

# 16. Criterios de "tu trabajo está bien hecho"

```
   ✓ TODAS las URLs en config/api.ts (cero hardcoded)
   ✓ React Query para datos del servidor
   ✓ Zustand para estado UI / kiosko offline
   ✓ Tailwind classes (sin inline styles)
   ✓ Componentes <500 líneas
   ✓ TypeScript strict, cero `any` sin justificar
   ✓ Wrappers para Leaflet, Chart.js
   ✓ Tests Vitest críticos (matriz, score breakdown, audit modal, kiosko store)
   ✓ Dark mode kiosko REQUISITO
   ✓ Eventos low confidence visibles, no escondidos
   ✓ data_quality del attempt visible en M4 y M6
   ✓ StandingCard usa /students/me/standings (plural multi-enrollment)
   ✓ Sin telemetría cruda en portal alumno (A4)
   ✓ Manager NO modifica notas (solo audit request)
   ✓ Cierre de convocatoria con flujo 3 pasos correctamente implementado
   ✓ Simulador (D12) muestra impacto en ranking, no solo en notas
   ✓ Kiosko con los 5 mecanismos defensivos
```

---

# 17. Decisiones firmes que tenés que aceptar

**No se reabren durante el sprint:**

```
   D6: Repo "training" en GitHub org actual
   D8: Confidence binario en V1 (high/low visible al manager)
   D11: data_quality global del attempt (HIGH/MEDIUM/LOW visible)
   D14: Modelo OPOSICIÓN — no mostrar APTO/NO_APTO por intento
   D17: Distinción ABANDONED / ABORTED_TECHNICAL / INTERRUPTED_BY_OTHER_CARD
   D18: Plazas público desde día 1
   D20: Visibilidad alumno: puesto + media + dentro/fuera
   D21: Ranking con indicador "PROVISIONAL" hasta cierre
   D22: Cierre con 3 pasos + doble admin + acta + ventana 24h
   D23: GDPR — banner de aviso de privacidad obligatorio
   D24: Doback Elite no es algo de frontend (es device, no UI)
   D25: criteria_version pinned al ABRIR (no es UI, pero afecta cálculos)
```

---

# 18. Glosario mínimo

| Término | Significado |
|---|---|
| **Attempt** | Intento de evaluación. Una unidad mostrable en M4, M5, M6. |
| **Convocatoria** | Proceso de oposición. Vos no la creás, es del admin. |
| **Enrollment** | Inscripción del alumno a UNA convocatoria. Multi-enrollment posible. |
| **Ranking** | Ordenamiento competitivo. Lo muestra M5. |
| **Plazas** | Número fijo de aprobados al cierre. Visible siempre. |
| **Corte provisional** | Línea entre top N (=plazas) y resto. Estado mientras OPEN. |
| **Cierre** | Proceso administrativo de 3 pasos (D5-A, D5-B, D5-C). |
| **Acta PDF** | Documento generado al cierre con SHA256 de integridad. |
| **Auditoría** | Solicitud formal del alumno (A5). Manager resuelve (M7). |
| **Reevaluación** | Attempt nuevo creado por manager tras auditoría confirmada. |
| **data_quality** | Calidad de datos del attempt: HIGH / MEDIUM / LOW. |
| **confidence** | Confiabilidad de un evento: HIGH / LOW. Visible en timeline. |
| **Doback Elite** | Dispositivo físico del camión. No tiene UI propia. |
| **Webfleet** | Sistema externo. No tiene UI propia (lo gestiona Antonio). |
| **SUPER_ADMIN** | Rol con poder de revertir cierres. Solo se ven sus opciones a quienes lo son. |
| **CLOSED / LOCKED** | Estados del cierre. CLOSED = revertible 24h. LOCKED = absoluto. |

---

**Si necesitás detalle adicional, mirá el Paper Maestro completo. Daily a las 9:30. Vamos.**
