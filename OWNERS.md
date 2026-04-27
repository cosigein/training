# Owners

> **Cómo se lee este archivo:** "todos pueden proponer un cambio, pero **una sola persona aprueba el merge**". Si tu PR toca un recurso de la columna izquierda, necesita la review de la persona de la columna derecha. Sin excepciones.

---

## Recursos compartidos del repo

| Recurso | Dueño (review obligatoria) | Quién puede proponer cambios |
|---|---|---|
| `package.json` raíz · `pnpm-workspace.yaml` · `tsconfig.base.json` | **Jesús** | Cualquiera |
| `eslint.config.js` · `.prettierrc` · husky / lint-staged | **Jesús** | Cualquiera |
| `docker-compose.dev.yml` · `docker-compose.yml` | **Jesús** | Cualquiera |
| `.env.example` raíz (fuente única de verdad de variables) | **Jesús** | Quien necesita una variable nueva añade aquí + en el PR |
| `prisma/schema.prisma` · migraciones Prisma | **Jesús** | Solo Jesús edita; Alejandro/Joel proponen vía issue |
| `packages/api-types/` (tipos compartidos backend↔frontend) | **Jesús** | Jesús expone, Alejandro y Joel consumen |
| `packages/ingestion/webfleet/` | **Antonio** | Solo Antonio edita |
| `apps/web/` (todo el frontend) | **Alejandro** | Alejandro edita; Joel toca solo `data-testid` con su convención |
| `apps/web/src/styles/tokens.css` · design system | **Alejandro** | Alejandro decide |
| `apps/web/src/pages/admin/ScoringSimulator.tsx` | **Antonio** | Antonio edita; Alejandro le entrega componentes base; Joel escribe E2E test #7 contra esta pantalla |
| `apps/api/src/routes/scoring.simulate.ts` | **Antonio** | Antonio edita; consume `packages/scoring/simulate()` de Jesús |
| `docs/SIMULATOR-USER-GUIDE.md` | **Antonio** | Doc para admin CMadrid (español, 1-2 páginas) |
| `apps/api/` resto (salvo `routes/health`) | **Jesús** | Jesús edita |
| `apps/worker/src/jobs/webfleetSync.ts` | **Antonio** (define el contrato) + **Jesús** (orquesta BullMQ) | Antonio define qué llama, Jesús cómo se programa |
| `e2e/` (Playwright tests) | **Joel** | Joel edita |
| `seed/` · `scripts/seed.ts` | **Joel** | Joel edita; Jesús revisa coherencia con schema |
| `.github/workflows/*` (CI/CD) | **Joel** | Joel edita; cuando un cambio de Jesús/Alejandro rompa CI, lo arregla quien lo rompió |
| `docs/` (cualquier `.md`) | **Antonio** | Cualquiera edita; Antonio mergea |
| `README.md` · `CONTRIBUTING.md` · `OWNERS.md` | **Antonio** | Cualquiera propone, Antonio mergea |

---

## Antonio — review **obligatoria** en estos archivos

Independientemente del dueño técnico, Antonio (director técnico) tiene que aprobar cualquier PR que toque:

```
   ▶ prisma/schema.prisma            (cambios al modelo de datos)
   ▶ apps/api/src/middleware/        (auth, multi-tenant, CSRF)
   ▶ package.json raíz                (dependencias compartidas)
   ▶ .github/workflows/               (CI/CD pipeline)
   ▶ docker-compose*.yml              (infra)
   ▶ Cualquier endpoint que toque
     /close/*, /scoring/simulate, /gdpr/*, /admin/*
     (los flujos legalmente sensibles)
```

Esto significa: **2 reviews** en estos PRs (el dueño técnico + Antonio).

---

## Convenciones que afectan a varios dueños

### Convención de `data-testid` (Alejandro pone, Joel usa)

Formato: `data-testid="<portal>-<pantalla>-<elemento>"`

Ejemplos:
- `data-testid="manager-matrix-row-3"`
- `data-testid="kiosko-rfid-prompt"`
- `data-testid="admin-close-step1-button-confirm"`

Reglas:
- Alejandro pone los `data-testid` cuando crea o edita un componente.
- Joel los usa en E2E tests.
- Si Alejandro quiere renombrar uno → coordina con Joel ANTES de mergear (no después: rompe los tests).
- Sin `data-testid` no hay test E2E posible — Joel puede bloquear merge si una pantalla nueva no los tiene.

### Naming de migraciones Prisma (Jesús)

Formato: `YYYYMMDD_HHMM_<verbo>_<modelo>`

Ejemplos:
- `20260428_1100_init_base_models`
- `20260429_0930_add_convocatoria_status`
- `20260507_1530_modify_attempt_score_audit`

**Regla:** una migración por PR. Squashes solo en la migración inicial.

### Branch namespace por persona

Formato: `<tipo>/<area>-<descripcion>`

Áreas reservadas:
- `wf` → trabajo de Antonio (webfleet)
- `be` → trabajo de Jesús (backend)
- `fe` → trabajo de Alejandro (frontend)
- `qa` → trabajo de Joel (tests + CI + simulator)
- `cross` → cambios que cruzan áreas (revisar con Antonio antes)

Ejemplos:
- `feat/be-auth-jwt-cookies`
- `feat/fe-matrix-virtualized`
- `feat/qa-e2e-login-flow`
- `feat/wf-circuit-breaker`
- `chore/cross-pnpm-workspaces`

---

## Política de breaking changes durante el sprint

Si tu cambio rompe algo de otra persona (renombrar un endpoint, cambiar shape de respuesta, mover un componente):

1. **Avisás ANTES** — chat del equipo + comentario en el issue del afectado.
2. **Mergeás el cambio + el fix del consumidor en el mismo PR**, o coordinás dos PRs back-to-back en menos de 1 hora.
3. **Si no podés coordinar el back-to-back**, abrís un PR pequeño primero que mantiene compatibilidad temporal (ambos shapes funcionan), después tu cambio real, después el cleanup.

**Lo que NO está permitido:** mergear y "ya verá Alejandro mañana cuando le rompa". Eso bloquea al equipo y consume horas que no tenemos.

---

## Endpoint freeze diario

Cada noche, un job en CI commitea automáticamente `docs/api-snapshot.md` con el listado de endpoints estables (path, método, request/response shape).

- **Joel** monta y mantiene el cron desde el día 2: extrae los endpoints desde el código de `apps/api/` (anotaciones JSDoc o decorador) y los serializa a Markdown.
- Si el snapshot cambia respecto al día anterior, se mergea como commit `chore(qa): api-snapshot YYYY-MM-DD` y se postea el diff en el chat del equipo.
- Alejandro y Joel solo escriben código contra el snapshot vigente.
- Cambios deliberados durante el día = PR de Jesús + aviso explícito en chat con `@Alejandro @Joel`.

---

## Si dudás sobre quién es dueño de algo

Preguntá en el chat. Una respuesta de Antonio en chat queda como decisión documentada.

Si la duda se repite, abrí un PR que añade la fila correspondiente a este `OWNERS.md`.
