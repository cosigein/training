# Memoria del proyecto — Training

Esta carpeta es la **memoria viva del equipo durante el sprint**. Aquí se anotan decisiones, gotchas, aprendizajes y contexto que el código por sí solo no explica.

---

## ¿Para qué sirve?

`docs/` contiene la documentación oficial — reglas del repo, especificaciones, convenciones. Esa es la **doctrina**.

`memory/` contiene **lo que aprendemos haciendo**:

- Decisiones tomadas durante el sprint que cambiaron el plan original
- Gotchas que costaron horas y queremos que nadie repita
- Contexto que viene de fuera del repo (CMadrid, Webfleet, etc.)
- Acuerdos verbales con cliente/equipo que necesitan estar por escrito

---

## ¿Quién escribe aquí?

**Cualquiera del equipo, en cualquier momento.** Si descubrís algo que el siguiente que toque ese código va a tener que descubrir solo, escribilo acá.

Reglas:
- **Una memoria por archivo** — un solo tema por `.md`.
- **Nombre del archivo en kebab-case**: `gotcha-prisma-json-null.md`, `decision-webfleet-circuit-breaker.md`.
- **Empezá con el índice**: añadí la entrada en `MEMORY.md` con un link y una línea de descripción.
- **En español.** Es la lengua de trabajo del equipo.

---

## Tipos de memoria

| Prefijo | Cuándo usarlo |
|---|---|
| `decision-` | Una decisión tomada en el sprint que cambia el plan original |
| `gotcha-` | Algo que falló de forma sorprendente y queremos evitar repetir |
| `convencion-` | Un patrón que el equipo adoptó (no documentado en `docs/`) |
| `aprendizaje-` | Algo que descubrimos sobre el dominio o la herramienta |
| `acuerdo-` | Un acuerdo con cliente o stakeholder externo |

---

## Formato de cada memoria

Cabecera mínima:

```markdown
# Título corto y claro

**Tipo**: decision | gotcha | convencion | aprendizaje | acuerdo
**Autor**: nombre
**Fecha**: YYYY-MM-DD

## Qué
Una frase: qué pasa o qué se decidió.

## Por qué
La motivación. Sin esto, la memoria envejece mal y nadie sabe si sigue siendo válida.

## Dónde aplica
Archivos, módulos, situaciones donde esto importa.

## Aprendido / Cómo aplicarlo
Para gotchas: cómo evitar el problema. Para decisiones: cuándo se invalidaría.
```

---

## ¿Cuándo se borra una memoria?

Cuando deja de ser cierta. Si una decisión se revierte, **NO se borra el archivo** — se añade una nota al final con la fecha y el motivo, y se quita del índice de `MEMORY.md`.

El historial queda en git.

---

## ¿Qué NO va aquí?

- Documentación de cómo funciona el código (eso son comentarios o `docs/`).
- Tutoriales (van a `docs/`).
- Listas de TODOs (eso son issues de GitHub).
- Información sensible (credenciales, datos personales, etc).
