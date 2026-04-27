# Resumen y hoja de ruta — Dirección

**Para:** Dirección
**De:** Antonio Hermoso · Director técnico
**Fecha:** 27 de abril de 2026 (lunes — víspera del kickoff)
**Asunto:** Sprint Training (CMadrid) · 14 días · demo 11/05

> ⚠️ **Documento estrictamente interno.** No se comparte con CMadrid. La descripción del servicio entregable está en `PROPUESTA-CMADRID.md`. La visión funcional está en `DOCUMENTO-EJECUTIVO.md`. Este memo es tu panel de control mientras estás de viaje.

---

## TLDR — 30 segundos (leíble en el móvil)

```
   ✅ Hecho hoy:    Repo cosigein/training creado · 9 documentos · 6 issues con DoD ·
                    8 PDFs · Equipo informado · Convenciones cerradas · CI listo.

   ▶ Mañana:        Kickoff 09:00 con todo el equipo en Córdoba.
                    Yo lo conduzco. No necesito tu presencia.

   📅 Demo:         Lunes 11 de mayo · CMadrid en Madrid (yo viajo).

   ⚠️ Necesito de vos (3 puntos · ver §6):
     1. Confirmar póliza RC profesional vigente y cobertura suficiente
     2. Confirmar / negociar acuerdo escrito con Bridgestone (Webfleet)
     3. Decidir cobertura de DobackSoft V3 mientras estoy en Training

   📞 Cómo respondés (estás de viaje):
     · Llamada de 15 min ideal antes del jueves 30/04, o audio cuando puedas.
     · Si no llegás a tiempo, los 3 quedan abiertos como riesgo en
       el primer status update del viernes.

   ⚡ El elefante en la habitación (§7.1):
     Mientras estoy en Training (74 días), DobackSoft V3 queda sin director
     técnico en pleno cutover Phase 2. Hay que decidir vos: ¿reparto al
     60/40? ¿suplente interino? ¿pausa cutover V3?
```

---

## 1. Qué se construyó HOY (lunes 27/04)

- **Repo privado** `cosigein/training` con `main` protegida y 6 issues con Definition of Done.
- **3 documentos clave**: Paper Maestro técnico (3500 líneas), Documento Ejecutivo (no técnico, cliente + gestión) y Propuesta CMadrid (alcance del servicio + SLA + GDPR + escrow).
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

## 3. Riesgos legales — exposición de la empresa

| Riesgo | Mitigación actual | Acción pendiente |
|---|---|---|
| Recurso administrativo de candidato impugnando un cierre | Versionado inmutable + acta SHA256 + audit log + revisión humana al cierre (GDPR art. 22 cubierto) | Validar con asesor legal de CMadrid antes del cutover |
| Responsabilidad civil si el sistema falla durante una convocatoria real | __PENDIENTE — confirmar póliza RC profesional vigente__ | Decisión §6 punto 1 |
| Acuerdo Bridgestone (Webfleet) — uso de su API en producto a terceros | __PENDIENTE — verificar contrato existente o negociar__ | Decisión §6 punto 2 |
| GDPR (somos Data Processor de datos sensibles: geolocalización + evaluación profesional) | DPA estándar + cláusulas en contrato con CMadrid | DPO de CMadrid debe firmar antes del cutover |
| Bus factor del equipo | 4 personas, plan documentado en §5, code escrow | Documentar reemplazo si Antonio o Jesús caen |

---

## 4. Plan de contingencia — bus factor

Equipo de 4 sin redundancia real. Si cae uno:

| Persona | Cae 3-5 días | Cae 1-2 semanas |
|---|---|---|
| **Antonio** | Equipo sigue, comunicación con cliente pausa | Detener proyecto, escalar a Dirección. CMadrid se notifica. |
| **Jesús** | Sprint tambalea pero sigue | Detener Fase 2, replanificar |
| **Alejandro** | Sprint sigue, Antonio cubre frontend mínimo | Contratar freelance React 1 mes |
| **Joel** | Tests se pausan, demo viable | QA externalizado para validar antes del cutover |

---

## 5. Replicabilidad técnica

Una vez validado con CMadrid, el sistema es replicable a otros cuerpos públicos españoles que usen oposición (Bombers Generalitat, Valencia, País Vasco, Andalucía, Diputaciones provinciales) — mismo modelo, mismo motor, distintos parámetros. Estrategia comercial fuera de scope de este memo.

---

## 6. Decisiones que necesito de Dirección

> 3 puntos operativos. Sin ninguno de ellos puedo seguir adelante con cobertura completa.

1. **Póliza RC profesional**: ¿está vigente? ¿cobertura suficiente para un sistema de evaluación que afecta a 265 candidatos por convocatoria? Esto bloquea Fase 3 (operación real, octubre 2026), no la demo.
2. **Acuerdo escrito Bridgestone (Webfleet)**: ¿existe? ¿lo negociamos vos o yo? Bloquea cutover real con datos productivos.
3. **Cobertura de DobackSoft V3 durante mi ausencia** (ver §7.1). El elefante en la habitación. Solo vos lo podés decidir.

### Cómo respondés (estás de viaje)

- Idealmente llamada de 15 min antes del jueves 30/04. Si no podés, audio o WhatsApp punto por punto.
- Si no respondés antes del miércoles 29/04, los 3 quedan marcados como riesgo abierto en el primer status update del viernes 02/05.

---

## 7. Riesgos no obvios y supuestos frágiles (lectura post-brainstorming)

> Sección añadida tras un análisis divergente con consultor externo. Son riesgos que NO había escrito antes y son los que más me preocupan a mí ahora.

### 7.1 — DobackSoft V3 sin director técnico durante 74 días

**El elefante en la habitación.** Mientras yo estoy en Training (sprint + Fase 2), DobackSoft V3 (nuestro producto madre, en pleno cutover de Pipeline Audit Phase 2) **se queda sin director técnico** del 28/04 al ~12/07. Eso es real y necesita decisión.

Opciones a evaluar contigo:
- (a) Yo divido tiempo (60% Training / 40% DobackSoft V3) durante Fase 2. Riesgo: ambos productos sufren.
- (b) Designamos un suplente interino para DobackSoft V3 durante el sprint. ¿Quién?
- (c) Pausamos el cutover de Pipeline Audit Phase 2 hasta julio.

### 7.2 — Webfleet sandbox de CMadrid: probablemente NO existe

**Riesgo endémico:** CMadrid usa Webfleet de Bridgestone, pero las flotas públicas españolas típicamente NO tienen sandbox separado, solo producción con datos reales. Si esto se confirma, **bloqueo legal de NDA + GDPR antes del 04/05** y el sprint pierde la integración real una semana entera.

Plan de mitigación: la primera reunión de esta semana con CMadrid pregunta explícita "¿hay sandbox o solo producción?". Si dicen "solo producción", negociamos export anonimizado de un período histórico para fixture.

---

## 8. Oportunidades técnicas a explorar **después** de la demo

Solo lectura — no son entregables del sprint.

- **Simulador como componente reutilizable** — el motor de scoring + simulación es aplicable a otros casos (flotas profesionales, formación CAP, ITV) más allá del modelo de oposición.
- **White paper "Evaluación algorítmica conforme a GDPR art. 22 + LPACAP"** — coste casi cero, autoridad técnica en un nicho donde nadie publica.
- **Dictamen jurídico AEPD/LPACAP previo a Fase 3** — convierte el moat de "tecnología" a "tecnología + defensa jurídica blindada".

---

## 9. Cómo revisar este memo (sugerencia, 5 minutos)

1. **TLDR** (30 seg).
2. **§1 Lo construido hoy** (30 seg).
3. **§7.1 DobackSoft V3 sin tech lead** (1 min — la decisión más importante).
4. **§3 Riesgos legales** + **§6 Decisiones** (2 min).
5. **§7.2 Webfleet sandbox** (30 seg).

§2, §4, §5, §8 es contexto que podés saltar si vas justo de tiempo.

---

**Antonio Hermoso · Director técnico**
27 de abril de 2026 · Córdoba

> *Si no recibo respuesta antes del miércoles 29/04 con los 3 puntos del §6, los marco como riesgo abierto en el primer status update del viernes 02/05. Status update por escrito al cierre de cada viernes vía WhatsApp.*
