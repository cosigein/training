# Resumen y hoja de ruta — Dirección

**Para:** Dirección
**De:** Antonio Hermoso · Director técnico
**Fecha:** 27 de abril de 2026 (lunes — víspera del kickoff)
**Asunto:** Sprint Training (CMadrid) · 14 días · demo 11/05

> ⚠️ **Documento estrictamente interno.** No se comparte con CMadrid. La propuesta hacia el cliente es `PROPUESTA-COMERCIAL.md`. La visión funcional es `DOCUMENTO-EJECUTIVO.md`. Este memo es tu panel de control mientras estás de viaje.

---

## TLDR — 30 segundos (leíble en el móvil)

```
   ✅ Hecho hoy:    Repo cosigein/training creado · 9 documentos · 6 issues con DoD ·
                    8 PDFs · Equipo informado · Convenciones cerradas · CI listo.

   ▶ Mañana:        Kickoff 09:00 con todo el equipo en Córdoba.
                    Yo lo conduzco. No necesito tu presencia.

   📅 Demo:         Lunes 11 de mayo · CMadrid en Madrid (yo viajo).

   ⚠️ Necesito de vos (5 puntos · ver §10):
     1. OK al arranque (asumiendo coste de §4)                  → default: arranco
     2. Rango económico (§5) — confirmar/corregir mis rangos    → SIN default, te necesito
     3. Confirmar póliza RC profesional                          → SIN default, te necesito
     4. Confirmar/negociar acuerdo Bridgestone (Webfleet)        → SIN default, te necesito
     5. Política Fase 2 si CMadrid no firma antes del 04/05      → default: pausa

   📞 Cómo respondés (estás de viaje):
     · Puntos 1 y 5     → WhatsApp basta. Si no respondés, aplican defaults.
     · Puntos 2, 3, 4   → llamada 15 min ideal antes del jueves 30/04.
                          Si no respondés, propuesta a CMadrid sale sin cifras
                          y los riesgos quedan abiertos en el status update.

   ⚡ El elefante en la habitación (§11.1):
     Mientras estoy en Training (74 días), DobackSoft V3 queda sin director
     técnico en pleno cutover Phase 2. No está cifrado en §4. Hay que
     decidir vos: ¿reparto al 60/40? ¿suplente interino? ¿pausa cutover V3?
```

---

## 1. Qué se construyó HOY (lunes 27/04)

- **Repo privado** `cosigein/training` con `main` protegida y 6 issues con Definition of Done.
- **3 documentos clave** entregables: Paper Maestro técnico (3500 líneas), Documento Ejecutivo (no técnico, cliente + gestión) y Propuesta Comercial (SLA, GDPR art. 22, hitos de pago, escrow).
- **5 docs individuales** del equipo + convenciones (`OWNERS.md`, `CONTRIBUTING.md`) + 8 PDFs.
- **Decisiones técnicas firmes** cerradas (no se reabren): pnpm workspaces, monorepo, Winston, React 18 + Vite + Tailwind 4, Playwright.
- **Pendientes mías** que se cierran esta noche / mañana temprano (no te bloquean): invitar al equipo al repo, crear chat, mandar PDFs a CMadrid, conseguir fixture Webfleet.

---

## 2. Hoja de ruta a la demo (11 de mayo de 2026)

```
SEMANA 1 — INFRAESTRUCTURA Y CORE
─────────────────────────────────
Mar 28/04  KICKOFF + scaffolding compartido (pnpm workspaces, Prisma, Docker)
Mié 29/04  Schema base + auth JWT + endpoints /health  (Jesús)
Jue 30/04  Webfleet client v0 (mock) + auth refinado + UI base       (yo + Jesús + Ale)
Vie 01/05  FESTIVO (Día del Trabajador)


SEMANA 2 — INTEGRACIÓN Y CIERRE
───────────────────────────────
Lun 04/05  Webfleet real contra sandbox CMadrid                       (yo)
           Normalization + detection + scoring                        (Jesús)
           Componente Matrix con datos mock                           (Ale)
Mar 05/05  Ranking + ConvocatoriaCloseAct                             (Jesús)
           Vista examinador con datos reales                          (Ale)
Mié 06/05  Endpoints /close/* (3 pasos) + cron ranking nocturno       (Jesús)
           Modal Override + Reevaluación                              (Ale)
Jue 07/05  Acta PDF (Puppeteer + SHA256)                              (Jesús)
           Kiosko completo + cierre 3-pasos UI                        (Ale)
           Pair Jesús + Joel: simulator core                          (cruzado)
Vie 08/05  Datos seed completos · validación E2E · status update CMadrid

Sáb 09/05  TORTURA del kiosko (voluntario)
Dom 10/05  Ensayo demo (3 pasadas)

Lun 11/05  REUNIÓN CMADRID — DEMO
```

---

## 3. Estado contractual con CMadrid (HOY)

> Sección que hace falta que confirmes vos. Marcá lo que aplica:

| Pregunta | Estado actual | Tu respuesta |
|---|---|---|
| ¿Hay carta de intenciones firmada? | __PENDIENTE — Antonio confirma__ | __ |
| ¿Hay propuesta económica entregada? | NO. Se entrega esta semana. | — |
| ¿Hay acuerdo verbal de adjudicación condicional al éxito de la demo? | __PENDIENTE — Antonio confirma__ | __ |
| ¿Hay contrato marco DobackSoft–CMadrid sobre el que apoyarse? | __PENDIENTE — Antonio confirma__ | __ |
| ¿Riesgo de que CMadrid no firme tras la demo? | Medio. Plan B en §6. | — |

---

## 4. Coste interno del compromiso

> Estimaciones mías de partida con tarifa loaded interna asumida ~300 €/día. **Corregí los números** que tengas más afinados.

| Concepto | Cálculo | Coste estimado |
|---|---|---|
| Sprint (14 días naturales · 9 días laborables efectivos · 4 personas) | 36 días-hombre × ~300 €/día | **~10.800 €** [tarifa interna a corregir] |
| Fase 2 (mayo–julio · ~8 semanas, dedicación 60%) | 19 semanas-hombre × 5 × 300 €/día | **~28.500 €** [estimación — corregir] |
| Hardware Doback Elite (5 dispositivos demo + 2 repuestos + instalación) | 7 × ~250 € + ~500 € | **~2.250 €** [confirmar con stock real] |
| Infraestructura (VPS staging + producción · 12 meses) | Hetzner CX22 staging 72 €/año + producción ~1.200 €/año | **~1.300 €/año** |
| **Coste de oportunidad — DobackSoft V3 sin director técnico durante 74 días** | Ver §11 — el agujero más grande del cuadro | **A cuantificar urgente — solo vos lo sabés** |
| **TOTAL pre-firma estimado (sin coste de oportunidad)** | | **~42.850 € en 11 semanas** |

> El **coste de oportunidad de DobackSoft V3** durante el sprint + Fase 2 es probablemente el mayor número aquí, y solo vos podés cifrarlo. Lo trato explícito en §11.

---

## 5. Modelo de ingresos propuesto a CMadrid

> Rangos de partida míos. **Corregilos vos** según margen objetivo y benchmarking de mercado público español. Detalle completo en `PROPUESTA-COMERCIAL.md` §8.bis.1.

```
   1. SETUP INICIAL (pago único, 4 hitos contra entregable)
      Total estimado: 60.000-90.000 €
        Hito 1 (~30%):  18.000-27.000 € — firma del contrato.
        Hito 2 (~30%):  18.000-27.000 € — demo aceptada (lunes 11/05).
        Hito 3 (~25%):  15.000-22.500 € — cutover validado primera convocatoria.
        Hito 4 (~15%):  9.000-13.500 € — primera convocatoria cerrada con acta.

   2. SUSCRIPCIÓN MENSUAL
      3.500-5.500 €/mes (mantenimiento + soporte L-V 09:00-18:30 +
                          backups + cron ranking + sync Webfleet).

   3. POR CONVOCATORIA REAL CERRADA
      2.000-4.000 €/convocatoria (cuota Webfleet + storage 12m +
                                   acta firmada cualificada).

   4. SOPORTE EXTENDIDO PARA DÍA DE CIERRE FORMAL (opcional)
      800-1.500 € por convocatoria con presencia on-site/stand-by.
```

**Para que cuadre** (a las cifras de §4): break-even del Sprint+Fase 2 con ~80.000 € de setup. Margen primer año depende de cuántas convocatorias reales se cierren (estimo 1-2 en 2026 con CMadrid solo).

> CMadrid (en su lado) ya avisó: **sin cifras concretas no entra en Intervención**. Tenemos que llegar al 11/05 con un rango propuesto. Si me das tu corrección por llamada o WhatsApp esta semana, ajusto la propuesta antes de mandarla.

---

## 6. Plan B si CMadrid no firma

**Lo que NO se pierde:**

- Código en `cosigein/training` queda como base reutilizable para otros cuerpos de bomberos públicos españoles (Barcelona, Valencia, Sevilla, parques provinciales, Andalucía, etc.).
- Conocimiento de dominio (modelo de oposición, GDPR, recurso administrativo) → IP de la empresa.
- Webfleet integration → reutilizable en el resto del producto DobackSoft.

**Lo que SÍ se pierde:**

- 36 días-hombre + hardware Doback Elite preparado para CMadrid.
- Tiempo del director técnico durante el sprint.

**Punto de no retorno propuesto:** si NO hay carta de intenciones firmada antes del **lunes 04/05** (semana de la demo), evaluamos pausar Fase 2 hasta tener compromiso por escrito. Tu llamada esta semana confirma o cambia esto.

---

## 7. Pipeline comercial — replicabilidad

Replicable a otros cuerpos públicos españoles que usen oposición (Bombers Generalitat, Valencia, País Vasco, Andalucía, Diputaciones provinciales). Una vez validado con CMadrid, el ciclo de venta de los siguientes se acorta. **Pero leé §11 sobre el supuesto frágil de recurrencia** antes de proyectar TAM.

---

## 8. Riesgos legales — exposición de la empresa

| Riesgo | Mitigación actual | Acción pendiente |
|---|---|---|
| Recurso administrativo de candidato impugnando un cierre | Versionado inmutable + acta SHA256 + audit log + revisión humana al cierre (GDPR art. 22 cubierto) | Validar con asesor legal de CMadrid + cláusula de responsabilidad en contrato |
| Responsabilidad civil si el sistema falla durante una convocatoria | __PENDIENTE — confirmar póliza RC profesional__ | Contratar / extender RC antes de Fase 3 (octubre 2026) |
| Acuerdo Bridgestone (Webfleet) | __PENDIENTE — verificar contrato existente o negociar__ | Cerrar acuerdo escrito antes del cutover |
| GDPR (somos Data Processor de datos sensibles) | DPA estándar + cláusulas en contrato | DPO de CMadrid debe firmar antes del 11/05 |
| Bus factor del equipo | 4 personas, plan documentado, code escrow | Documentar reemplazo si Antonio o Jesús caen |

---

## 9. Plan de contingencia — bus factor

Equipo de 4 sin redundancia real. Si cae uno:

| Persona | Cae 3-5 días | Cae 1-2 semanas |
|---|---|---|
| **Antonio** | Equipo sigue, comunicación con cliente pausa | Detener proyecto, escalar a Dirección. CMadrid se notifica. |
| **Jesús** | Sprint tambalea pero sigue | Detener Fase 2, replanificar |
| **Alejandro** | Sprint sigue, Antonio cubre frontend mínimo | Contratar freelance React 1 mes |
| **Joel** | Tests se pausan, demo viable | QA externalizado para validar antes del cutover |

---

## 10. Decisiones que necesito de Dirección

> 5 puntos. Los ordeno por **cómo querés responder**.

### Con default si no respondés (puedo arrancar sin tu OK)

1. ✅ / ❌ **Aprobar arranque del sprint** asumiendo el coste de §4. **Default: arranco.** Frenar ahora cuesta más que dejar correr.
5. **Política Fase 2 si CMadrid no firma carta de intenciones antes del 04/05:** ¿pausamos o seguimos? **Default: pausa** (postura prudente que protege los ~28.500 € de Fase 2 sin compromiso escrito).

### SIN default — necesitan tu respuesta explícita

> Estos 3 NO los resuelvo por mi cuenta. Si no respondés antes del 04/05, los marco como riesgo abierto en el primer status update y la propuesta a CMadrid sale sin cifras.

2. **Rangos económicos para los 3 componentes** (§5). Necesito que confirmes o corrijas los rangos que propuse — si confirmás, sale la propuesta tal cual; si corregís, ajusto antes del 30/04.
3. **Póliza RC profesional**: ¿está vigente? ¿cobertura suficiente para un sistema de evaluación que afecta a 265 candidatos por convocatoria?
4. **Acuerdo escrito Bridgestone (Webfleet)**: ¿existe? ¿lo negociamos vos o yo?

### Cómo respondés (estás de viaje)

- Puntos 1 y 5 → WhatsApp basta ("OK" / "no").
- Puntos 2, 3, 4 → idealmente llamada de 15 min antes del jueves 30/04. Si no podés, audio o WhatsApp con tu rango/respuesta.

---

## 11. Riesgos no obvios y supuestos frágiles (lectura post-brainstorming)

> Esta sección la añado tras un análisis divergente con consultor externo. Son riesgos que NO había escrito en versiones anteriores del memo y son los que más me preocupan **a mí** ahora.

### 11.1 — DobackSoft V3 sin director técnico durante 74 días

**El elefante en la habitación.** Mientras yo estoy en Training (sprint + Fase 2), DobackSoft V3 (nuestro producto madre, fuente de caja actual, en pleno cutover de Pipeline Audit Phase 2) **se queda sin director técnico** del 28/04 al ~12/07. Ese hueco es real y no aparece cifrado en §4.

Opciones a evaluar contigo:
- (a) Yo divido tiempo (60% Training / 40% DobackSoft V3) durante Fase 2. Riesgo: ambos productos sufren.
- (b) Designamos un suplente interino para DobackSoft V3 durante el sprint. ¿Quién?
- (c) Pausamos el cutover de Pipeline Audit Phase 2 hasta julio. Coste interno aceptable.

### 11.2 — Webfleet sandbox de CMadrid: probablemente NO existe

**Riesgo endémico:** CMadrid usa Webfleet de Bridgestone, pero las flotas públicas españolas típicamente NO tienen sandbox separado, solo producción con datos reales. Si esto se confirma, **bloqueo legal de NDA + GDPR antes del 04/05** y el sprint pierde la integración real una semana entera.

Plan de mitigación: la primera reunión de esta semana con CMadrid pregunta explícita "¿hay sandbox o solo producción?". Si dicen "solo producción", negociamos export anonimizado de un período histórico para fixture.

### 11.3 — Procedimiento negociado con 3 ofertas

**Riesgo legal contractual:** la administración pública española exige por defecto, para contratos > 40.000 €, un **procedimiento negociado con publicidad** que requiere al menos 3 ofertas comparables. Si el contrato Training estimado supera ese umbral (probable según §5), el comité de Intervención de CMadrid puede requerir que aparezcan 2 competidores formales.

Acción: en la reunión inicial con CMadrid, preguntar la modalidad contractual prevista. Si es procedimiento negociado, anticipar nombres de "competidores admitidos" y mantener relación con ellos para minimizar fricción.

### 11.4 — Recurrencia de las oposiciones (supuesto frágil del modelo)

**El supuesto que se rompe primero:** el modelo económico §5 asume cadencia de convocatorias razonable (1-2/año). En la realidad, las oposiciones de bomberos en España se convocan cada **4-7 años por cuerpo**. Para que el SaaS sea sostenible necesitamos ~8-10 cuerpos activos en paralelo, no los 6 del pipeline §7.

Implicación: el TAM real puede ser **un tercio del implícito**. Si solo CMadrid firma y nadie más en 2026, el LTV mensual no cubre el coste de mantenimiento entre convocatorias.

**Acción para mitigarlo:** explorar las oportunidades de §12 (motor de simulación desacoplado, white paper LPACAP) que dan ingresos sin depender de la cadencia de oposiciones.

---

## 12. Oportunidades a explorar **después** de la demo (no requieren acción ahora)

Solo lectura — no son entregables del sprint, pero no quiero perderlas.

- **Simulador como producto independiente** — el motor de scoring + simulación es un producto SaaS horizontal aplicable a flotas profesionales (mudanzas, ambulancias, basura, autoescuelas CAP). Mercado 100x el de oposiciones. Desacopla el riesgo CMadrid.
- **White paper "Evaluación algorítmica en oposición pública conforme a GDPR art. 22"** — coste casi cero, autoridad enorme en un nicho donde nadie publica. Blinda el ciclo de venta de los siguientes 5 cuerpos.
- **Canal B2B2C vía academias preparadoras** (CEP, MAD) — entrar por el lado del candidato, no del cuerpo. El opositor empuja al cuerpo a adoptar Training como "garantía de objetividad".
- **Dictamen jurídico AEPD/LPACAP previo a la demo** — convierte el moat de "tecnología" a "tecnología + defensa jurídica blindada". Coste ~5.000 € de consultoría legal especializada.

---

## 13. Cómo revisar este memo (sugerencia, 8 minutos)

1. **TLDR** (30 seg).
2. **§1 Lo construido hoy** (30 seg).
3. **§4 Coste interno** + **§11.1 DobackSoft V3** (3 min — la decisión más cara).
4. **§5 Modelo de ingresos** (1 min — confirmá o corregí los rangos).
5. **§10 Decisiones que necesito** (2 min).
6. **§11.2/11.3/11.4 riesgos no obvios** (1 min).

§2-3, §6-9, §12 es contexto que podés saltar si vas justo de tiempo.

---

**Antonio Hermoso · Director técnico**
27 de abril de 2026 · Córdoba

> *Si no recibo respuesta antes del miércoles 29/04, **aplico solo los defaults de los puntos 1 y 5** (arrancar sprint + pausar Fase 2 si no hay carta de intenciones al 04/05). Los puntos 2, 3, 4 quedan abiertos en el primer status update del viernes — la propuesta a CMadrid sale sin cifras y los riesgos legales sin resolver. Status update por escrito al cierre de cada viernes vía WhatsApp.*
