# Antonio — Tu trabajo en Training

## Sprint de 14 días · Demo CMadrid: lunes 11 de mayo de 2026

---

## ⚡ TLDR — esto es lo que tenés mañana en 5 líneas

1. **Sos director técnico.** Conducís el kickoff de 1h a las 09:00 (agenda en §12).
2. **Tu código:** Webfleet ingestion package (`packages/ingestion/webfleet/`). Nadie más lo toca.
3. **Tu otra responsabilidad:** comunicación CMadrid, decisiones cross-team, review obligatoria en archivos críticos (lista en `OWNERS.md`).
4. **Esta noche:** revisá la checklist "Pendientes para Antonio antes del kickoff" en el `README.md`. 7 puntos en ~90 minutos.
5. **Demo CMadrid:** lunes 11 de mayo. Plan día por día en §7.

---

| | |
|---|---|
| **Tu rol** | Director técnico · Cliente · Webfleet (dev) |
| **Equipo** | Vos · Jesús (backend) · Alejandro (frontend) · Joel (simulador + QA) |
| **Tu carga** | 3 frentes simultáneos: arquitectura, cliente, código de Webfleet |
| **Tu issue principal** | [#2 — Webfleet ingestion package](https://github.com/cosigein/training/issues/2) |
| **Issues compartidos** | [#1 — Scaffolding día 1](https://github.com/cosigein/training/issues/1) · [#6 — Convenciones del sprint](https://github.com/cosigein/training/issues/6) |
| **Documento maestro** | `docs/PAPER-MAESTRO.md` (referencia completa cuando dudes) |
| **Convenciones** | [`OWNERS.md`](../../OWNERS.md) y [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — léelas antes de mañana |
| **Memo Dirección** | [`docs/MEMO-DIRECCION-INTERNO.md`](../MEMO-DIRECCION-INTERNO.md) — caso de negocio para tu jefe |

---

## TOC

1. [Tu rol en una línea](#1-tu-rol-en-una-línea)
2. [Tu territorio de código](#2-tu-territorio-de-código)
3. [Tu agenda externa — calendario con cliente](#3-tu-agenda-externa--calendario-con-cliente-y-stakeholders)
4. [Tu rol con el cliente](#4-tu-rol-con-el-cliente--lo-que-sí-hacés-y-lo-que-no)
5. [Cuota Webfleet — circuit breaker](#5-cuota-webfleet--circuit-breaker-desde-día-1)
6. [Tu interfaz con Jesús](#6-tu-interfaz-con-jesús-la-api-pública-del-package)
7. [Tu calendario día por día](#7-tu-calendario-día-por-día)
8. [Decisiones que SOLO vos tomás](#8-decisiones-que-solo-vos-podés-tomar)
9. [Decisiones que delegás](#9-decisiones-que-delegás)
10. [Reglas no negociables — las 9 invariantes](#10-reglas-no-negociables--las-9-invariantes)
11. [Reglas de proceso](#11-reglas-de-proceso-10-reglas-operativas)
12. [Antes del kickoff — checklist tuya](#12-antes-del-kickoff--checklist-tuya-hoy-lunes-2704)
13. [Criterios de "tu trabajo está bien hecho"](#13-criterios-de-tu-trabajo-está-bien-hecho)
14. [Glosario mínimo](#14-glosario-mínimo)
15. [Si algo va mal](#15-si-algo-va-mal)

---

## Decisiones tomadas pre-kickoff (si algo te preguntan, esto está cerrado)

| Tema | Decisión |
|---|---|
| Gestor de paquetes | **pnpm** + workspaces |
| Estructura monorepo | `apps/{api,worker,web}` + `packages/*` |
| TypeScript | strict + `tsconfig.base.json` raíz |
| Lint/format | ESLint + Prettier + Husky pre-commit + lint-staged |
| Logger backend | **Winston** con transport JSON estructurado |
| Logger frontend | helper propio `utils/logger.ts` con flag `LOG_LEVEL` |
| Convención branches | `feat/<area>-<desc>` con áreas reservadas (wf/be/fe/qa/cross) — ver CONTRIBUTING |
| Convención commits | Conventional commits (`feat:`, `fix:`, `chore:`...) |
| Squash merge | Por defecto en todos los PRs |
| `data-testid` | `<portal>-<pantalla>-<elemento>` — ver CONTRIBUTING §5.quater |
| Tipos compartidos backend↔frontend | Package `packages/api-types/` (Jesús lo expone, Alejandro y Joel consumen) |
| VPS staging | **Hetzner CX22** (Ubuntu 22.04, 2 vCPU / 4GB / 40GB · ~6€/mes) — provisionado por Antonio el jueves 30/04 antes del despliegue automático |
| Plan B screencast demo | Vos lo grabás el sábado 09/05 por la tarde tras tortura kiosko (45 min, 3 takes) |

---

# 1. Tu rol en una línea

Sos **el director técnico**. Eso significa **3 cosas a la vez** durante estos 14 días:

```
   1. ARQUITECTO
      Tomás las decisiones de diseño que afectan a más de 1 persona.
      Aprobás (o rechazás) cambios estructurales.

   2. INTERFAZ CON EL CLIENTE
      Sos la única voz hacia CMadrid durante estos 14 días.
      Comunicás expectativas, fechas, scope.

   3. DEV CONTRIBUTOR — DUEÑO DE WEBFLEET
      Tu código vive en `packages/ingestion/webfleet/`.
      Es la única parte del backend que NO toca Jesús.
```

No sos coordinador puro. **Tenés código asignado y deadlines como cualquier dev.**

---

# 2. Tu territorio de código

```
training/
├── packages/
│   └── ingestion/
│       └── webfleet/        ← TU CÓDIGO
│           ├── client.ts            cliente HTTP de Webfleet
│           ├── normalizer.ts        convierte respuesta cruda
│           ├── syncService.ts       orquesta sync periódico + on-demand
│           ├── eventMapper.ts       convierte eventos Webfleet a Event interno
│           │                        con confidence assignment
│           ├── circuitBreaker.ts    cuotas, retries
│           └── tests/               fixtures + tests determinísticos
│
└── apps/worker/src/jobs/
    └── webfleetSync.ts              ← TU CÓDIGO (orquestación BullMQ)
```

**Jesús no toca esto. Vos no tocás el resto del backend.**

---

# 3. Tu agenda externa — calendario con cliente y stakeholders

Esto NO está en el paper maestro. Es tuyo.

## 3.1 Comunicación con CMadrid — cadencia propuesta

```
   ANTES del kickoff (HOY, lunes 27/04 — víspera)
   ▶ Mandar HOY mismo o mañana temprano:
     - Documento Ejecutivo (versión actual)
     - Propuesta Comercial (con secciones de SLA + términos)
   ▶ Llamada de 15-30 min cuando puedan (ideal antes del jueves):
     - Confirmar fecha demo del lunes 11/05
     - Confirmar disponibilidad de fixtures Webfleet
     - Confirmar quién es DPO en su lado

   DURANTE el sprint (martes 28/04 - viernes 08/05)
   ▶ Status update por email cada VIERNES a las 17:00.
     Una página: qué se construyó, qué queda, riesgos.
     Sin escalado de problemas — solo informativo.
   ▶ Recordá que el viernes 01/05 es festivo: el primer status
     update va el viernes 08/05.
   ▶ Si hay riesgo de no llegar al 11/05:
     llamada inmediata a CMadrid, no esperar al viernes.

   SEMANA DE LA DEMO
   ▶ Lunes 04/05: confirmar logística (lugar, hora, asistentes)
   ▶ Jueves 07/05: enviar resumen 1 página de lo que verán
   ▶ Lunes 11/05: demo

   POST-DEMO
   ▶ Email mismo día por la tarde: "qué validamos hoy + próximos pasos"
   ▶ Reunión Fase 2: proponé martes 12/05 a CMadrid
     (contigo + DPO + asesor legal por su lado)
```

## 3.2 A quién reportás vos

Aclará esto antes del kickoff con tu jefe (si tenés uno por encima):

```
   ▶ ¿Reportás horas? ¿A quién? ¿Con qué cadencia?
   ▶ ¿Hay un comité de dirección que quiera updates?
   ▶ ¿Las decisiones de alcance las tomás vos solo o pasa por alguien?
```

Si la respuesta es "soy yo y no tengo a quien reportar", **anotalo igual**. La transparencia interna evita conversaciones incómodas después.

## 3.3 Política de comunicación fuera de horario

```
   HORARIO LABORAL  L-V 09:00-18:30 (Europe/Madrid)
   ▶ Slack del equipo, email a CMadrid: respuesta misma jornada.

   FUERA DE HORARIO normal
   ▶ Slack del equipo: leer pero no esperás respuesta inmediata.
   ▶ CMadrid: NO te metés en email/llamadas en fin de semana.
     Excepción: incidente crítico durante un cierre de convocatoria
     real. En ese caso vos coordinás soporte.

   SEMANA DE DEMO + CIERRE DE CONVOCATORIA REAL
   ▶ Soporte extendido coordinado con anticipación.
     Esto debe estar en el SLA acordado con CMadrid.
     Si no está acordado, no asumas responsabilidad.

   ANTI-PATTERN A EVITAR
   ▶ NO hagas commits propios fuera de horario laboral durante el sprint.
     Riesgo: rompés algo a las 23:00, nadie lo ve hasta el día siguiente,
     bloqueás al equipo.
```

## 3.4 Tu backup operativo

Si te enfermás 3 días o tenés un imprevisto:

```
   ▶ Backup técnico:    Jesús
     Hablá con él el día 1: "si no estoy, vos sos el contacto técnico
     interno". Que tenga claros los gotchas críticos.

   ▶ Backup cliente:    NO HAY
     CMadrid solo escucha a vos. Si te ausentás, comunicás vos mismo
     que te ausentás (aunque sea con un email simple "estoy fuera 3 días,
     pinchame mañana").

   ▶ Acceso de emergencia (a configurar el DÍA 1):
     - Repo `cosigein/training` en GitHub: Jesús como admin.
     - VPS de staging: aún no provisionado. Vos decidís proveedor
       el día 1 (Hetzner / DigitalOcean / VPS propio existente).
     - Cuenta de email del proyecto: a crear.
```

## 3.5 Cosas que tenés que tener listas ANTES del 11/05

```
   PARA LA DEMO
   ☐ Datos seed creíbles (Joel los hace, vos los validás)
   ☐ Script de presentación rehearsed 3 veces
   ☐ Plan B operativo (ver §3.6 — NO es solo "screencast")
   ☐ Conexión a internet del lugar de demo, probada
   ☐ Hotspot 4G del móvil como red de respaldo
   ☐ Laptop principal cargada + cargador de respaldo
   ☐ Pendrive con backup de los PDFs ejecutivo + servicio CMadrid
   ☐ Tarjeta RFID o teclado para simular RFID

   PARA EL CLIENTE
   ☐ PDF Ejecutivo + PDF Descripción del Servicio entregados al menos el 04/05
   ☐ Resumen 1 página enviado el 07/05
   ☐ Email post-demo redactado a medias antes del 11/05
   ☐ Audit trail del acuerdo CMadrid documentado por escrito
        (acta de reunión, email firmado, lo que sea)
        antes del jueves 30/04 — sin esto el proyecto está en aire

   ADMINISTRATIVO
   ☐ NDA mutuo firmado o en proceso
   ☐ DPO de CMadrid identificado y contactado
```

## 3.6 Plan B real para la demo (no es "el screencast pregrabado")

El "screencast pregrabado" es Plan C. **El Plan B real es un demo offline en staging con datos sintéticos y red local.**

```
   ESCENARIO 1 — Falla la conexión a internet del lugar
   → Activás hotspot 4G del móvil (preparado el día antes con datos suficientes).
   → Si tampoco funciona: laptop solo, demo sobre `localhost` con docker compose
     levantado y datos seed v4.
   → Tiempo de pivot: <2 minutos.

   ESCENARIO 2 — Falla algo del backend en demo
   → No reiniciás. NO debugueás en vivo.
   → Pasás a la siguiente pantalla del script y avisás "este flujo lo
     mostramos en otro momento". Sigue la demo.
   → Si lo que falló es bloqueante (login, navegación), pivotás a screencast
     desde la sección que sigue, no desde el principio.

   ESCENARIO 3 — Falla algo del frontend / kiosko
   → Mostrás el flujo equivalente desde el portal manager (siempre tiene la
     misma información en formato distinto).
   → El kiosko en producción es una pantalla, en demo lo simulamos: si no
     funciona, lo describís y mostrás la captura del Paper Maestro.

   ESCENARIO 4 — Falla TODO (catastrófico)
   → Plan C: screencast pregrabado el sábado 09/05 después de la tortura
     del kiosko. Lo grabás vos en pantalla compartida + voiceover en vivo.
     Duración: 8 minutos. Dueño de grabación: vos. Dueño de revisión: Joel.

   QUÉ LLEVÁS ENCIMA EL DÍA DE LA DEMO (kit físico)
   ☐ Laptop con docker compose precorrido, base seed v4 cargada
   ☐ Hotspot 4G activo, password apuntada
   ☐ Pendrive con screencast .mp4 (Plan C)
   ☐ Pendrive con los 3 PDFs (Ejecutivo + Servicio CMadrid + Memo si lo pide)
   ☐ Tarjeta RFID o teclado USB-HID para simular
   ☐ Batería de respaldo del móvil
   ☐ Cable HDMI propio (NO confiás en el del lugar)
```

---

# 4. Tu rol con el cliente — lo que SÍ hacés y lo que NO

```
   ▶ Comunicás fecha de demo: 11/05/2026
   ▶ Mantenés expectativas alineadas:
     "estamos construyendo lo nuevo, lo verán funcionar"
   ▶ NO prometés features fuera del scope demo (§6.2 paper maestro)
   ▶ NO discutís stack ni arquitectura con el cliente
     (no le interesa, no le importa)
   ▶ Si CMadrid pide algo nuevo durante el sprint:
     respuesta default = "lo evaluamos para Fase 2"
   ▶ Coordinás backups y staging access para CMadrid
```

## El mensaje a CMadrid en 5 frases (memorízalas)

```
   1. "Construimos un sistema NUEVO, autónomo y orientado al
       modelo de OPOSICIÓN que pediste."

   2. "El sistema emite NOTAS por intento. La decisión APTO o
       NO APTO se emite al cierre de la convocatoria, según
       ranking final + plazas que vos publicaste."

   3. "Lo que están viendo HOY funciona end-to-end con datos
       reales. Es la base."

   4. "El SIMULADOR te permite probar cualquier cambio de regla
       y ver cómo se reordena el ranking ANTES de aplicarlo en
       producción."

   5. "En las 4-8 semanas siguientes endurecemos contra datos
       reales: kiosko offline robusto, cuotas Webfleet,
       cutover gradual, PDFs definitivos, recurso administrativo."
```

## Qué NO le decís

```
   ✗ "Tiramos todo y empezamos de cero"
   ✗ "El sistema anterior estaba mal"
   ✗ "Vamos a Python/Flask"
   ✗ "Vue / nuevo framework"
   ✗ Detalles arquitectónicos profundos
   ✗ "Esto ya está terminado"
```

## Qué le preguntamos / confirmamos

```
   ▶ "¿Confirmás los criterios de empate que propusimos?"
   ▶ "¿Cuál es la ruta principal para desempates?"
   ▶ "¿Cuántas plazas tiene la próxima convocatoria real?"
   ▶ "¿Cuándo es la próxima convocatoria de candidatos?"
   ▶ "¿Hay rutas o reglas que quieran cambiar?"
   ▶ "¿Necesitan integración con sistemas internos?"
   ▶ "¿Quién es vuestro DPO (Delegado de Protección de Datos)?"
   ▶ "¿Tenéis sandbox de Webfleet o solo producción?"
```

---

# 5. Cuota Webfleet — circuit breaker desde día 1

CMadrid tiene cuota de **14.400 requests/día**. Sin circuit breaker, podés agotarla en 30 minutos por un bug.

**Implementación obligatoria:**

```
   Redis key: webfleet:quota:YYYYMMDD
   - Incrementa en cada request
   - TTL = 24h auto-expira
   - Si > 11.520 (80%) → log warning + alerta
   - Si > 14.000 (97%) → rechazar nuevos syncs hasta el día siguiente
   - Si Webfleet responde 429 → backoff exponencial mínimo 60s
```

---

# 6. Tu interfaz con Jesús (la API pública del package)

Webfleet es un package. Jesús lo consume desde `apps/worker` y `apps/api`. La interfaz que vos exponés:

```typescript
// packages/ingestion/webfleet/index.ts

export interface WebfleetSyncResult {
  attempt_id: string;
  raw_samples_count: number;
  events_count: number;
  data_freshness: 'fresh' | 'stale' | 'missing';
  fetched_at: Date;
}

export async function syncAttempt(
  attempt_id: string,
  options: { force?: boolean }
): Promise<WebfleetSyncResult>;

export async function getQuotaStatus(): Promise<{
  used: number;
  limit: number;
  resets_at: Date;
}>;
```

**Si cambiás esta interfaz, le avisás a Jesús ANTES.**

---

# 7. Tu calendario día por día

```
SEMANA 1 — INFRAESTRUCTURA
─────────────────────────

MARTES (DÍA 1) 28/04 — KICKOFF
09:00  Reunión kickoff con todo el equipo. Lectura silenciosa
       del paper maestro. Q&A. Resolución de dudas.
10:00  Café + buffer + setup individual:
       - Quien no tenga Node 20 / Docker / GitHub access, los instala.
       - Antonio crea el chat del equipo si no estaba creado.
       - Confirmar permisos de cada uno en el repo.
11:00  Scaffolding mínimo del repo en vivo con todo el equipo
       (estructura de carpetas, package.json, docker-compose dev).
       NO se hace por separado: lo hacemos juntos para que
       todos compartan la base.
~13:00 Comida.
14:30  Cada uno arranca con su primer commit asignado:
       - Jesús: rama chore/setup-jesus + scaffolding apps/api
       - Alejandro: rama chore/setup-alejandro + apps/web base
       - Joel: rama feat/qa-e2e-bootstrap (PR1)
       - Antonio: rama chore/cross-... según necesidad

MIÉRCOLES (DÍA 2) 29/04
- Investigar fixtures Webfleet reales del cliente.
- Documentar formato exacto del payload, qué campos importan
  para Training y cuáles ignoramos.

JUEVES (DÍA 3) 30/04
- Empezar packages/ingestion/webfleet/:
  - client.ts (cliente HTTP con encodeURI obligatorio)
  - auth con tilde resuelto
- Tests iniciales contra fixtures.
- 17:30 — RETROSPECTIVA SEMANA 1 (30 min, todo el equipo)
    · ¿Qué funcionó? · ¿Qué nos bloqueó? · ¿Qué cambiamos para semana 2?
    · La conducís vos. Anotás 3-5 acciones concretas para semana 2.

VIERNES (DÍA 4) 01/05 — FESTIVO (Día del Trabajador, España)
- Sin trabajo planificado. Si querés adelantar algo, libre.
- Si CMadrid manda algo urgente: respondés vos.

[fin de semana — descanso]


SEMANA 2 — INTEGRACIÓN, CLIENTE, DEMO
────────────────────────────────────

LUNES (DÍA 7) 04/05
- Webfleet en staging real (sandbox CMadrid).
- Verificar que el username con tilde funciona.
- Validar quota tracking en Redis real.
- syncService.ts (orquestación periódica + on-demand) — adelantado
  desde la semana 1 al perderse el viernes festivo.
- eventMapper.ts con confidence assignment (high/low).

MARTES (DÍA 8) 05/05
- Coordinar con CMadrid: pedir un fixture grande para demo
  (ideal: una convocatoria histórica anonimizada).
- Ajustar EventMapper si los datos reales muestran patrones
  no contemplados en fixtures.
- Documentar la interfaz pública del package (§5 de este doc)
  y entregar a Jesús — demo interna informal.

MIÉRCOLES (DÍA 9) 06/05
- Pulir Webfleet edge cases mínimos:
  - Webfleet retorna 200 con [] vs error
  - Latencia >10s
  - Quota 80%/97%
- Soporte ad-hoc al equipo.

JUEVES (DÍA 10) 07/05
- Documentación cliente (PDF resumen de la demo, 1 página).
- Enviar resumen a CMadrid.
- Soporte ad-hoc.

VIERNES (DÍA 11) 08/05
- Backup completo de la DB de staging.
- Validación end-to-end con datos reales.
- Verificar que demo está al 90%.
- 17:30 — RETROSPECTIVA SEMANA 2 + PRE-DEMO (45 min, todo el equipo)
    · Estado real de los entregables vs DoD de cada issue.
    · ¿Qué cortamos del scope si llegamos justos?
    · Plan operativo del fin de semana (tortura + ensayo).

SÁBADO (DÍA 12) 09/05 — TORTURA DEL KIOSKO
- Liderado por Joel. Todo el equipo participa (voluntario, fuera del horario laboral acordado).
- Vos validás que Webfleet aguanta los escenarios.
- 18:00 — Grabación del screencast Plan C (vos solo, en pantalla compartida + voiceover).
    · 8 minutos. Joel revisa al cierre.

DOMINGO (DÍA 13) 10/05 — ENSAYO DEMO
- Conducís el ensayo (3 pasadas completas).
- Plan B operativo (§3.6) verificado en cada pasada (¿qué hago si falla X?).
- Script de presentación rehearsed.

LUNES (DÍA 14) 11/05 — REUNIÓN CMADRID
- Llegás 1h antes al lugar.
- Conexión a internet probada.
- Demo en staging.
- Documento ejecutivo en PDF para entregar.
```

> **Nota sobre el festivo del 1 de mayo:** España tiene festivo nacional el viernes 01/05 (Día del Trabajador). Eso reduce el sprint a **9 días laborables efectivos + 2 días de fin de semana de torture/ensayo + demo**. El plan de cada doc absorbe esto. Si vemos que vamos justos, hablamos al final de la semana 1.

---

# 8. Decisiones que SOLO vos podés tomar

```
   - Reabrir cualquier decisión firme (D1-D25 del paper maestro)
   - Aceptar o rechazar features fuera de scope
   - Comunicación con CMadrid (cualquier email/llamada)
   - Aprobar PRs estructurales (cambios arquitectónicos)
   - Decidir si cancelamos o postponemos la demo del 11/05
   - Onboarding/offboarding del equipo
   - Ejecutar /close/reverse en producción (rol SUPER_ADMIN)
   - Aprobar GDPR forget-requests
```

# 9. Decisiones que delegás

```
   - Implementación interna de cada package: a Jesús
   - Implementación interna de pantallas: a Alejandro
   - Cómo se testea: a Joel
   - Datos seed específicos: a Joel
   - Bugs y fixes tácticos: a quien corresponda
```

---

# 10. Reglas no negociables — las 9 invariantes

Cualquier PR (tuyo o del equipo) que rompa una de estas se rechaza:

```
   1. IDEMPOTENCIA DE INGEST — mismo archivo 2 veces ≠ duplicar samples
   2. REPRODUCIBILIDAD — replay <attempt_id> regenera score idéntico
   3. INMUTABILIDAD attempt cerrado (frozen_at != null = sin UPDATE)
   4. VERSIONADO PINNED al ABRIR (criteria/normalizer/detector)
   5. SOURCE + CONFIDENCE ortogonales en cada Event
   6. INMUTABILIDAD del ranking final (LOCKED es absoluto)
   7. DECISIÓN solo al cierre de convocatoria (no por intento)
   8. CIERRE con doble validación + acta + ventana 24h
   9. CRITERIA_VERSION pinned al CREAR el attempt, no al cerrar
```

---

# 11. Reglas de proceso (10 reglas operativas)

```
   ▶ Daily de 15 minutos a las 9:30 AM. Inflexible.
   ▶ Si bloqueado >2h, escalar al chat del equipo.
   ▶ Cada commit pusheado y desplegado a staging automático.
   ▶ El que rompe staging, lo arregla antes de irse.
   ▶ Trabajo en main con feature branches cortas (<1 día).
   ▶ PR de un dev requiere 1 review de OTRO dev (no auto-merge).
   ▶ Joel revisa la calidad de demo cada viernes.
   ▶ Lógica de dominio NO en handlers HTTP (va a packages).
   ▶ Webfleet encapsulado: solo packages/ingestion/webfleet/ importa el cliente.
   ▶ Logger Winston, NO console.log.
```

---

# 12. Antes del kickoff — checklist tuya (HOY, lunes 27/04)

```
   ☑ Repo `cosigein/training` creado (ya está)
   ☐ Invitar a Jesús/Alejandro/Joel al repo (necesitás sus usernames de GitHub)
   ☐ Bloquear backlog de DobackSoft Fleet (decir a tu jefe: "estoy en Training 14 días")
   ☐ Confirmar a CMadrid fecha de demo (lunes 11/05/2026)
   ☐ Conseguir fixtures Webfleet realistas (al menos 1 ejemplo de payload)
   ☐ Mandar HOY al equipo el link al repo + sus docs individuales
        (Jesús → docs/team/jesus.md, Alejandro → docs/team/alejandro.md,
         Joel → docs/team/joel-day1-en.md PRIMERO, después joel-en.md)
   ☐ Crear espacio Slack/Discord/Teams para el equipo (a tu elección)
        y pasarle el link a los 3
   ☐ Preparar la agenda del kickoff (1 hora) — borrador abajo
```

## Reunión kickoff (Día 1, MARTES 28/04, 09:00)

```
   AGENDA (60 minutos) — la conducís vos
   ─────────────────────────────────────
   00:00 - 00:05   Antonio: contexto y por qué este doc
   00:05 - 00:30   Lectura silenciosa del Paper Maestro
                   (cada uno lee su sección)
   00:30 - 00:50   Preguntas y discusión
                   NO REAPERTURA de decisiones, solo aclaraciones
   00:50 - 00:55   Cada uno dice qué va a hacer hoy
   00:55 - 01:00   "Empezamos. Daily mañana 9:30."

   DESPUÉS DEL KICKOFF (mañana del día 1)
   ─────────────────────────────────────
   ▶ Scaffolding inicial del repo en vivo entre los 4
     (decidir estructura de carpetas, package.json, docker-compose,
      tooling de lint/format). Lo hacemos juntos para que nadie tenga
      que reescribir su trabajo después por una decisión tomada por otro.
   ▶ Cada uno crea su rama `chore/setup-<nombre>` con su primer commit
     (un archivo en `docs/onboarding/<nombre>.md` con sus notas del día).
     Validamos así que el flujo PR/review funciona.
```

---

# 13. Criterios de "tu trabajo está bien hecho"

```
   ✓ Webfleet client maneja correctamente username con tilde
   ✓ Quota Redis funciona con thresholds 80%/97%
   ✓ Circuit breaker se activa con backoff exponencial 60s+
   ✓ Tests determinísticos del client + normalizer + eventMapper
   ✓ syncService funciona en staging con datos reales de CMadrid
   ✓ Interfaz pública documentada y consumida por Jesús sin fricción
   ✓ Demo CMadrid sale sin errores
   ✓ Cliente sale de la reunión confiando en la dirección
```

---

# 14. Glosario mínimo

| Término | Significado |
|---|---|
| **Attempt** | Intento de evaluación. Un alumno + una ruta + una sesión. |
| **Convocatoria** | Proceso de oposición concreto. Tiene plazas, fecha cierre, candidatos. |
| **Enrollment** | Inscripción de un Student a UNA convocatoria. Un humano puede tener varias. |
| **Doback Elite** | Nombre del dispositivo propio instalado en cada camión. |
| **Webfleet** | Plataforma externa de Bridgestone. Tu territorio. |
| **Ranking** | Ordenamiento competitivo dentro de una convocatoria. |
| **CLOSED / LOCKED** | Estados del cierre. CLOSED = revertible 24h. LOCKED = irrevocable. |
| **OutcomeAmendment** | Modificación post-LOCKED por recurso administrativo (Fase 2). |
| **SUPER_ADMIN** | Rol exclusivo para reverse + GDPR forget. Existe en V1. |

---

# 15. Si algo va mal

```
   ▶ Webfleet no responde después de horas:
     → activar fallback a Doback Elite GPS
     → notificar al equipo en chat
     → informar a CMadrid si la convocatoria demo se ve afectada

   ▶ La demo se cae el 11/05:
     → activar Plan B: screencast pregrabado
     → comunicar al cliente con honestidad
     → reagendar con nueva fecha

   ▶ CMadrid pide cambio de scope a mitad de sprint:
     → "lo evaluamos para Fase 2"
     → NO comprometerse en la sala
     → consultar al equipo antes de aceptar

   ▶ Un dev se traba >4h en algo:
     → escalar y desbloquear
     → si es de tu área (Webfleet), ayudar directamente
     → si es de otra área, conectar con el dueño del dominio
```

---

**Este es tu documento. Si necesitás detalle adicional, mirá el Paper Maestro completo.**

**Vamos.**
