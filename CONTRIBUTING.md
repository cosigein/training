# Cómo contribuimos

Equipo de 4 personas, sprint corto. Estas reglas existen para que **nadie pierda tiempo** y para que **nada se rompa por sorpresa**.

---

## 1. Branch strategy

- **`main`** es la rama principal. Está protegida — todo entra por Pull Request.
- Trabajo en **feature branches cortas** (objetivo: < 1 día de vida).
- Convenciones de nombre:
  - `feat/<area>-<descripcion-corta>` — feature nueva.
  - `fix/<area>-<descripcion-corta>` — bug fix.
  - `chore/<descripcion>` — config, CI, dependencias.
  - `docs/<descripcion>` — solo documentación.
- Ejemplos:
  - `feat/scoring-tiebreak`
  - `fix/webfleet-tilde-encoding`
  - `chore/setup-eslint`

> Si una rama lleva >2 días abierta, partila en algo más chico.

---

## 2. Pull Requests

- **1 review obligatoria** de otro dev antes de hacer merge. Self-merge prohibido.
- El reviewer no es solo un sello — si veés algo raro, comentalo.
- PRs pequeños (< 300 líneas) se revisan en minutos. PRs grandes se revisan tarde y mal: si tu cambio crece, partilo.
- **Squash merge** por defecto. El historial de `main` debe ser legible.
- **CI verde** antes de merge. Si CI falla, el PR no entra (se arregla, no se ignora).

### Plantilla de descripción del PR

```
## Qué cambia
<una frase>

## Por qué
<motivación / issue que resuelve>

## Cómo se prueba
<pasos manuales o tests automáticos>

## Riesgos
<qué puede romperse, qué no se cubre>
```

---

## 3. Conventional commits

Cada commit en `main` (después del squash) debe seguir [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: …` — nueva funcionalidad
- `fix: …` — corrección de bug
- `docs: …` — solo documentación
- `chore: …` — config, build, dependencias
- `refactor: …` — refactor sin cambio funcional
- `test: …` — solo tests

> No firmar commits con co-autores de IA. Sin "Co-Authored-By".

---

## 4. Code review — qué pedimos

Cuando revisás el PR de otro:

- ¿Hace lo que dice que hace?
- ¿Tiene tests donde corresponde?
- ¿Rompe alguna invariante (ver `docs/PAPER-MAESTRO.md` §9)?
- ¿El nombre del commit/PR refleja el cambio?
- ¿Hay deuda escondida (TODO, console.log, código muerto)?
- ¿El cambio respeta los límites entre packages/apps?

No es necesario que el código sea perfecto — necesario que sea **honesto** (hace lo que dice, sin sorpresas).

---

## 5. Estructura del repo (durante el sprint)

Empezamos vacío. La estructura definitiva la consolidamos el día 1 del sprint con todo el equipo presente. La propuesta de partida (sujeta a validación) está en `docs/PAPER-MAESTRO.md`.

**No crees carpetas `apps/`, `packages/` ni añadas dependencias de forma unilateral antes del kickoff.** Eso lo hacemos juntos para evitar reescribir la base 3 veces.

---

## 6. Daily

- **09:30 (Europe/Madrid). 15 minutos.** Inflexible.
- Formato: cada uno responde 3 preguntas — qué hice ayer, qué hago hoy, qué me bloquea.
- Si te bloquea algo > 2 horas durante el día, no esperes al daily de mañana — escalá en el chat.

---

## 7. Issues

- Cada persona tiene un issue principal con su scope (etiqueta `role:antonio`, `role:jesus`, `role:alejandro`, `role:joel`).
- Los entregables se trackean como sub-tareas (checkbox list dentro del issue) o como issues hijos enlazados.
- Si descubrís trabajo nuevo durante el sprint que NO está en tu issue, abrís un issue nuevo y lo etiquetás. **No hacés trabajo invisible.**
- Cierre de issue solo al merge del PR que lo resuelve.

---

## 8. Calidad — no negociables

- **Sin `console.log` en código de producto.** Usar logger central (lo definimos día 1).
- **Sin `: any` en TypeScript** salvo casos justificados con comentario `// any: <razón>`.
- **Sin secrets en el repo.** Variables sensibles van por `.env` (ignorado) o secret manager.
- **Sin commits a `main`.** Siempre PR.

---

## 9. Si algo se rompe

- **Staging roto:** quien lo rompió, lo arregla antes de irse.
- **CI rojo:** no merges hasta que esté verde. Si te urge, hablá con Antonio.
- **Producción rota** (durante demo o cierre real): chat del equipo + ping directo a Antonio.

---

## 10. Comunicación

- Decisiones técnicas se documentan en el PR o en `docs/`.
- Acuerdos verbales que afectan a más de uno se anotan por escrito (chat o issue) — si no está escrito, no existió.
- Cualquier comunicación con CMadrid pasa **únicamente** por Antonio.

---

**Si tenés una duda sobre estas reglas, preguntá. Si una regla te parece tonta para tu caso, también preguntá — vale más cambiar la regla que ignorarla.**
