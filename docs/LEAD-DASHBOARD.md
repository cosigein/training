# Lead Dashboard — Antonio (Training, sprint CMadrid)

> Documento personal de Antonio. Foto **honesta** del proyecto: lo real, lo mock, lo que falta.
> NO romantizar. Si algo es stub, lo dice. Si algo "anda" pero con datos sembrados, lo dice.
>
> **Última actualización:** 2026-04-29 (cierre día 2 / 14)
> **Demo Madrid:** 2026-05-11 (lunes) · viaja Antonio
> **Equipo:** 4 personas en Córdoba (Antonio lead/Webfleet · Jesús be · Alejandro fe · Joel qa/CI)

---

## 🎯 TL;DR — 30 segundos

- **Hecho de verdad:** RBAC, modelos (User extendido, Convocatoria, Enrollment, Attempt, Ranking, AttemptEvent, TrainingAuditLog, RfidCard), CRUD básico de convocatoria/enrollment, login/logout, kiosko/tap RFID, infra VPS (systemd + nginx + production).
- **Hecho pero MOCK/seeded:** dashboard manager (PR #11 conectado a BD real, pero los datos vienen de `seed_demo.py`, no de telemetría real). Frontend con 2 layouts conviviendo (DOBACKSOFT viejo vs CMadrid Training nuevo).
- **NO hecho (lo grande):** scoring real desde telemetría (tarea 8, 14h), cron daily-ranking (9), cierre 3 pasos + acta PDF (10), dashboard STUDENT (11), GDPR + auditoría (12), tests E2E, CI, Webfleet integration.
- **Riesgo #1:** sin tarea 8 (scoring real) la "demo" muestra ranking de **datos sembrados a mano por `seed_demo.py`**, no de evaluaciones reales. Si Jesús no termina tarea 8 antes del 09/05, hay que decidir Plan B (demoear con seed estático o pedir extensión).
- **Riesgo #2:** frontend con branding "DOBACKSOFT" en sidebar viejo. CMadrid bajo NDA NO debería ver eso. **Decisión D-FE-001 pendiente, vos + Alejandro, antes 09/05**.
- **Plazo crítico real:** todo cerrado para el viernes 08/05 (3 días de buffer). Lo que no esté el 08 no entra.

---

## 📊 Status maestro de tareas (1–12)

Leyenda: ✅ hecho real · 🟡 hecho con mocks/stubs · 🔄 en curso · ⏳ pendiente · ❌ no empezado

| # | Tarea | Status | Nota brutal |
|---|---|---|---|
| 1 | User + RBAC (STUDENT, SUPER_ADMIN) | ✅ | Real. Enum tiene `OPERATOR`/`VIEWER` legacy que sobran (cosmético). |
| 2 | Limpiar Flask (geofences/telemetry/kpis/reports) | ✅ | Real. Blueprints y modelos borrados. |
| 3 | Modelos Convocatoria + Enrollment | ✅ | Real. `app/models/training.py`. |
| 4 | Refactor Session → Attempt | ✅ | Real. `app/models/session.py:Attempt`. Conserva campos legacy `matched*`, `weatherConditions` que ya no se usan en Training puro. |
| 5 | Event extendido + Ranking + AuditEvent | ✅ | Real. Modelos `AttemptEvent`, `Ranking` (insert-only), `TrainingAuditLog`. |
| 6 | CRUD Convocatoria + Enrollment (admin) | ✅ | Real. Endpoints + templates en `app/blueprints/admin/`. **Layout viejo "DOBACKSOFT"**. |
| 7 | RfidCard + POST /kiosko/tap + cierre manual | ✅ | Real según commits. **No verificado E2E** todavía. |
| **7-bis** | **Manager dashboard → BD real + seed_demo** | 🟡 PR #11 | Code listo. Datos del seed (no de telemetría real). Esperando review Jesús + merge. |
| 8 | **Ingest + detector + scoring** (THE BIG ONE) | ❌ | 14h. `app/services/pipeline/` está VACÍO. Bloquea 9, 10, 11. |
| 9 | Cron daily-ranking + lock CLOSED→LOCKED | ❌ | 4h. `app/workers/` VACÍO. Necesita Celery beat funcional + redis dedicado. |
| 10 | Cierre 3 pasos + acta PDF + reversa 24h | ❌ | 10h. Endpoints + templates + WeasyPrint + SHA256. |
| 11 | Dashboard STUDENT + Matriz MANAGER (resto) | 🟡 parcial | Manager matriz/ranking ya están en PR #11. Falta portal STUDENT entero (`/student/*`). |
| 12 | Auditoría + GDPR export | ❌ | 6h. Modelo `AuditRequest` no existe. Hoy `/manager/auditoria/*` devuelve 404. |

**Estimación restante**: ~42h netas para 4 personas en 8 días laborables (29/04→08/05). Factible si no hay sorpresas, pero **sin colchón**.

---

## ✅ Lo que está REALMENTE funcionando hoy

| Componente | Dónde corre | Verificación |
|---|---|---|
| Auth con JWT en cookies + CSRF | local + VPS | login `manager@cmadrid.com / manager123` funciona |
| RBAC con `@require_role([...])` | local + VPS | `/manager/` da 302 sin sesión, redirect a login |
| Modelos SQLAlchemy todos | local + VPS | `db.create_all()` desde `setup_db.py` los crea OK |
| Postgres 17 + PostGIS | local Docker `:5435` / VPS host `:5432` | conexiones OK |
| Redis para limiter/cache | local Docker `:6380` / VPS compartido `:6379` | **VPS degradado a memoria** (sin password) |
| nginx SSL `:4000` → app `:5000` | VPS | https://srv844849.hstgr.cloud:4000/ → 302 |
| systemd `training-web.service` | VPS | `active`, `enabled`, autoarranca en boot |
| Manager dashboard (PR #11, no mergeado todavía) | local en branch `feat/be-manager-real-data` | 6 endpoints responden 200/302 con datos del seed |
| `setup_db.py` idempotente | local + VPS | seed: 1 org + 5 users + 2 RFID demo |
| `seed_demo.py` idempotente | local + VPS | 1 vehículo + 11 students + 2 convocatorias + 49 attempts |

---

## 🟡 Lo que parece hecho pero es MOCK/STUB/SEEDED

> Esto es importante para la demo: si CMadrid pregunta "¿de dónde sale esa nota?", la respuesta hoy es "del seed", no "del scoring real".

### `Attempt.score` y `Attempt.scoreBreakdown`
- **Hoy**: `seed_demo.py` los inserta a mano (3.0 a 9.6).
- **Realidad**: ningún proceso calcula scores desde telemetría. El detector y el scorer (tarea 8) están sin escribir.
- **Demo-ready?**: SÍ visualmente (el ranking se ve bien, las notas son consistentes). NO técnicamente (si CMadrid pregunta cómo se calcula, no hay respuesta más allá de "se va a implementar").

### `AttemptEvent` (eventos detectados)
- **Hoy**: cero filas en BD. El detector no existe.
- **Manager intento detalle** (`/manager/intento/<id>`) muestra eventos **placeholders inventados** ("FRENADA_BRUSCA", "ACELERACION_LATERAL") generados condicionalmente cuando `score < 6` o `dataQuality == LOW`. Está marcado `# TODO tarea 8` en el código.

### `Ranking` (snapshots)
- **Hoy**: cero filas en BD. El cron daily-ranking (tarea 9) no existe.
- **Manager ranking** (`/manager/ranking`) calcula el ranking **al vuelo en cada request** desde los Attempts. No persiste snapshot. Si tarea 9 no se hace, no hay historial.

### `AuditRequest` / auditorías pendientes
- **Hoy**: el modelo NO EXISTE. `/manager/auditoria/<id>` devuelve 404.
- **Dashboard manager** muestra "Auditorías pendientes: 0" — es honesto: realmente hay 0 (porque el modelo no existe).

### Webfleet integration
- **Hoy**: cero líneas. `app/services/webfleet/` no existe.
- **Realidad**: la fuente "primaria" de GPS/velocidad según el paper. Sin esto, scoring real no es completo. Antonio iba a entregar package día 7 según docs.

### Detector de eventos (`event_detector.py`)
- **Hoy**: archivo no existe. `app/services/pipeline/` está vacío.

### Scorer (`scorer.py`)
- **Hoy**: archivo no existe.

### Workers Celery
- **Hoy**: `app/workers/` vacío. `celery_worker.py` solo tiene el bootstrap básico.
- **Realidad**: ningún worker corriendo en VPS. Cron daily-ranking, generación de PDF acta, etc. — todo pendiente.

### Sockets (tiempo real)
- **Hoy**: `app/sockets/` vacío. Flask-SocketIO está instalado pero no se usa.
- **Demo**: si la demo no muestra "live updates", no afecta. Si los muestra, no van a funcionar.

### Tests
- **Hoy**: `tests/conftest.py` vacío. Cero tests. Cero E2E.
- **CI**: no hay workflow en `.github/workflows/`.

### Acta PDF
- **Hoy**: WeasyPrint instalado, sin código que lo use. `app/services/pdf_engine/` vacío.

---

## ❌ Lo que NO está hecho (claro)

| Item | Cuándo lo necesito | Bloquea demo? |
|---|---|---|
| Scoring engine completo (normalizer + detector + scorer) | tarea 8 | 🔴 SÍ — sin esto el ranking es seed |
| Cron daily-ranking 06:00 | tarea 9 | 🟡 NO si demoamos con ranking calculado al vuelo |
| Cierre 3 pasos + acta PDF | tarea 10 | 🟡 NO si la demo no incluye el flujo de cierre |
| Portal STUDENT | tarea 11 | 🟡 NO si la demo es solo del lado MANAGER/ADMIN |
| AuditRequest model + endpoints | tarea 12 | 🟡 NO si la demo no muestra auditorías |
| Webfleet client + circuit breaker | Antonio | 🟡 NO para demo, SÍ para producción |
| Tests E2E | Joel | 🟡 NO bloqueante para demo, SÍ para confianza |
| CI básico | Joel | 🟡 NO bloqueante |
| Migración Alembic real | post-tarea 8 | NO |
| Redis dedicado para Training | con tarea 9 | NO para demo |
| `pg_dump` cron diario en VPS | esta semana | NO para demo, SÍ para no perder data |
| Frontend dual-layout resuelto (D-FE-001) | antes 09/05 | 🔴 SÍ — riesgo NDA |
| Branding `DobackSoft` en `<title>` HTML | con D-FE-001 | 🟡 cosmético pero feo |

---

## 📅 Cronograma día por día (mi recomendación honesta)

```
 día | fecha       | qué pasa                                    | quién
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  3  | mié 29/04   | Hoy. Cierro sesión. PRs #11 #12 esperando.  | vos
     |             | Decidir D-FE-001 (combo D+C: 3-5h Alejandro)|
     |             | Jesús: leer STATE-2026-04-29.md y arrancar  |
     |             | tarea 8 (scoring).                          |
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  4  | jue 30/04   | Mergear PR #11 + deploy VPS.                | vos
     |             | Jesús: tarea 8 (normalizer + detector).     | Jesús
     |             | Joel: setup CI básico (lint + pytest).      | Joel
     |             | Alejandro: arreglo branding DOBACKSOFT.     | Alejandro
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  5  | vie 01/05   | FESTIVO España (Día del Trabajo). Suaves.   | —
     |             | Si alguien avanza, bonus.                   |
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  6  | sáb 02/05   | Buffer / catch-up.                          |
     |             | Vos: prep notas para demo.                  | vos
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  7  | dom 03/05   | Buffer.                                     | —
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  8  | lun 04/05   | Tarea 8 cerrada idealmente.                 | Jesús
     |             | Jesús arranca 9 y 10 en paralelo.           |
     |             | Alejandro: tarea 11 (STUDENT dashboard).    | Alejandro
     |             | Joel: primeros tests E2E.                   | Joel
─────┼─────────────┼─────────────────────────────────────────────┼──────────
  9  | mar 05/05   | Tareas 9 y 10 avanzando.                    | Jesús
     |             | Antonio termina Webfleet client (si aplica) | vos
─────┼─────────────┼─────────────────────────────────────────────┼──────────
 10  | mié 06/05   | Tarea 12 (Jesús) + seguir 11 (Alejandro).   |
     |             | Joel: E2E del flujo crítico.                | Joel
─────┼─────────────┼─────────────────────────────────────────────┼──────────
 11  | jue 07/05   | INTEGRACIÓN. Smoke E2E completo.            | todos
     |             | Última oportunidad de meter features.       |
─────┼─────────────┼─────────────────────────────────────────────┼──────────
 12  | vie 08/05   | 🔴 FEATURE FREEZE. Solo bug fixes.          | todos
     |             | Smoke test full path en VPS.                |
     |             | Vos: rehearsal de la talk de Madrid.        | vos
─────┼─────────────┼─────────────────────────────────────────────┼──────────
 13  | sáb 09/05   | 🤖 09:00 corre el ROUTINE pre-demo.         | agente
     |             | Vos: corres el checklist SSH del routine.   | vos
     |             | Rehearsal final.                            |
─────┼─────────────┼─────────────────────────────────────────────┼──────────
 14  | dom 10/05   | Vos viajás a Madrid.                        | vos
     |             | Solo bugfix CRÍTICO de aquí en adelante.    |
─────┼─────────────┼─────────────────────────────────────────────┼──────────
 15  | lun 11/05   | 🚀 DEMO MADRID                              | vos
```

**Buffer real disponible**: 02/05 + 03/05 + 09/05 = 3 días si todo se atrasa. Es **poco** si tarea 8 se complica.

---

## 🎭 Decisiones que TENÉS que tomar (vos, no delegables)

### 1. D-FE-001 — Frontend dual-layout
- Documento: `memory/decision-frontend-dual-layout.md`
- Opciones evaluadas (A/B/C/D).
- **Mi recomendación**: combo D+C (rebrand "DOBACKSOFT"→"CMadrid Training" en sidebar viejo + deprecar URLs duplicadas con `/manager/`).
- **Esfuerzo**: ~3-5h Alejandro.
- **Plazo**: decidir hoy/mañana (29-30/04).

### 2. ¿Demo con scoring real o demo con seed?
- **Si tarea 8 llega antes del 08/05**: demo con scoring real. Mejor cara. Pero si se complica, Plan B abajo.
- **Plan B (scoring seed)**: demoamos con `seed_demo.py` ejecutado en VPS y honestamente decimos "el motor de scoring está en development, hoy mostramos la UI con datos representativos". Funciona. CMadrid lo entiende.
- **Tu decisión**: cuándo declarar Plan B. Mi sugerencia: si lunes 04/05 tarea 8 NO está cerrada → activar Plan B y dedicar tiempo a UX, tests y rehearsal.

### 3. ¿Qué incluir / excluir de la demo del 11/05?
Lista realista para una demo de 30-45 min:
- ✅ Login (con LoadingState bien)
- ✅ Manager dashboard con KPIs, convocatorias, auditorías (placeholder OK)
- ✅ Manager → matriz alumnos × rutas
- ✅ Manager → ranking con corte
- ✅ Manager → detalle alumno
- ✅ Manager → detalle intento (con score breakdown del JSONB)
- ⚠️ Admin → CRUD convocatorias (layout viejo, depende de D-FE-001)
- ⚠️ Kiosko → POST /kiosko/tap (RFID, hay que probar E2E)
- ⏳ Cierre 3 pasos (si tarea 10 llega)
- ⏳ Portal STUDENT (si tarea 11 llega)
- ❌ Auditorías (tarea 12, si llega)

**Mi sugerencia**: corte fijo el 04/05. Lo que esté el 04/05 va a la demo. El resto se menciona como "fase 2".

### 4. ¿Levantar redis dedicado para Training?
- **Hoy**: `flask_limiter`/`flask_caching` caen a memoria silenciosamente.
- **Cuando hace falta**: tarea 9 (cron daily-ranking) si Celery se mete en serio.
- **Esfuerzo**: 30 min vos en VPS (`docker run`, exponer `:6381`, ajustar `.env`, restart).
- **Tu decisión**: hacerlo cuando arranque tarea 9 o ANTES por prevención.

### 5. ¿Mergear PR #12 (docs)?
- Es solo documentación. Riesgo cero.
- Mi sugerencia: mergear ya, así Jesús/Alejandro/Joel leen `STATE-2026-04-29.md` desde main.

---

## 🛠️ Comandos rápidos (chuleta)

### Local (resetear todo y arrancar)
```bash
# levantar BD + Redis
docker compose up -d

# venv + deps
source .venv/bin/activate

# reset BD limpio
PGPASSWORD=training psql -h localhost -p 5435 -U training -d postgres \
  -c "DROP DATABASE IF EXISTS training_dev; CREATE DATABASE training_dev OWNER training;"
python setup_db.py
python seed_demo.py    # opcional, datos demo

# correr app
python wsgi.py

# login
# manager@cmadrid.com / manager123
```

### VPS (deploy tras merge)
```bash
ssh dobacksoft-vps
sudo -u training git -C /home/training/treini pull --ff-only origin main
# si requirements cambió:
# sudo -u training /home/training/treini/.venv/bin/pip install -r /home/training/treini/requirements.txt
# si setup_db.py o modelos cambiaron:
# sudo -u training bash -c "cd /home/training/treini && set -a && . ./.env && set +a && /home/training/treini/.venv/bin/python setup_db.py"
sudo systemctl restart training-web
sudo systemctl status training-web
sudo tail -f /var/log/training-web.log    # verificar arranque limpio
curl -sk -o /dev/null -w "HTTP %{http_code}\n" https://srv844849.hstgr.cloud:4000/auth/login
```

### VPS (smoke check rápido)
```bash
ssh dobacksoft-vps
sudo systemctl is-active training-web    # active
sudo journalctl -u training-web -p err --since '24 hours ago' --no-pager | tail
df -h /
```

### VPS (backup BD antes de cambios riesgosos)
```bash
ssh dobacksoft-vps 'cd /home/training/treini && \
  PGPASS=$(grep ^DATABASE_URL= .env | sed -E "s|.*://training:([^@]*)@.*|\1|") && \
  PGPASSWORD="$PGPASS" pg_dump -h 127.0.0.1 -p 5432 -U training -d training | \
  gzip > /tmp/training_$(date +%s).sql.gz && ls -lh /tmp/training_*.sql.gz | tail'
scp dobacksoft-vps:/tmp/training_*.sql.gz /tmp/
```

### Local (re-correr seed_demo en VPS)
```bash
ssh dobacksoft-vps 'sudo -u training bash -c "cd /home/training/treini && \
  set -a && . ./.env && set +a && \
  /home/training/treini/.venv/bin/python seed_demo.py"'
```

### Git (limpiar branches mergeadas)
```bash
git branch -d docs/joel-onboarding-complete
git push origin --delete docs/joel-onboarding-complete
git branch -d claude/reassign-simulator-joel-tnvXW
```

---

## 🚨 Riesgos vivos (ordenados)

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | Tarea 8 (scoring) no cierra antes del 08/05 | 🟡 Media | 🔴 Alto | Plan B con seed_demo. Decidir el 04/05. |
| 2 | CMadrid ve "DOBACKSOFT" en demo (D-FE-001 no resuelto) | 🟡 Media | 🟡 Medio (NDA) | Decidir hoy/mañana, 3-5h Alejandro |
| 3 | VPS se cae el lunes de demo | 🟢 Baja | 🔴 Alto | systemd `Restart=always` + tener Plan offline (laptop con local) |
| 4 | BD VPS se corrompe sin backup diario | 🟢 Baja | 🔴 Alto | Setear cron `pg_dump` esta semana |
| 5 | Joel no llega a tener CI funcional | 🟡 Media | 🟢 Bajo | No es bloqueante para demo, postponer a Fase 2 |
| 6 | Webfleet integration no llega | 🟡 Media | 🟢 Bajo (demo) / 🔴 Alto (prod) | Mockear en demo, real en Fase 2 |
| 7 | Push directo a `main` rompe algo | 🟢 Baja | 🟡 Medio | Ya hay protección en GitHub. Recordar al equipo. |
| 8 | Cookie/JWT roto post-rotate de SECRET_KEY | 🟢 Baja | 🟡 Medio | NO rotar SECRET_KEY hasta post-demo |
| 9 | Redis del VPS dejara de aceptar conexiones (compartido con DobackSoft) | 🟢 Baja | 🟢 Bajo (degrada a memoria) | Levantar redis-training dedicado |
| 10 | Desincronización local↔VPS por commits diretos | 🟢 Baja | 🟡 Medio | Equipo SOLO mergea por PR. Recordar. |

---

## 🎬 Plan B para el 11/05 (si lo necesitás)

### Si tarea 8 NO está terminada
1. Demo con `seed_demo.py` ejecutado en VPS = lo que vimos hoy local.
2. Discurso: "El motor de scoring está en desarrollo activo. Hoy vamos a mostrar la UI con datos representativos. La integración Webfleet + sensor TXT está prevista para Fase 2."
3. Mostrar:
   - Ranking calculado al vuelo (no persistido) — funciona.
   - Score breakdown desde `scoreBreakdown` JSONB (los % vienen del seed pero la UI es real).
   - Eventos del intento como "ejemplo del tipo de información que tendremos cuando el detector esté integrado".

### Si frontend dual-layout NO se resolvió (D-FE-001 abierto)
1. Limitar la demo a `/auth/login` + `/manager/*` (todo el portal nuevo "CMadrid Training").
2. NO mostrar `/admin/*`, `/sessions/*`, `/vehicles/*`, `/events/*` (sidebar viejo "DOBACKSOFT").
3. Si CMadrid pregunta por gestión administrativa, decir "el panel de admin se está consolidando con el portal manager".

### Si VPS no responde el día de la demo
1. **Antes de subir al avión**: verificá `systemctl is-active training-web` + smoke `curl :4000/auth/login`.
2. **Backup absoluto**: tener tu laptop con local levantado (`docker compose up -d` + `python wsgi.py`). Demo desde laptop si hace falta.
3. URL del routine pre-demo (sábado 09/05) te avisa por Slack si algo está mal.

---

## 📁 Archivos clave (mapa mental)

```
training/
├── CLAUDE.md                    ← reglas del proyecto, leer antes que cualquier cosa
├── RBAC-FIX-PLAN.md             ← plan vivo RBAC, leer antes de tocar routes/decorators
├── TRAINING-ROADMAP.md          ← roadmap "oficial" tareas 1-12 con horas
├── MIGRATION-NOTES.md           ← Jesús, contexto del refactor reciente
├── roadmap.md                   ← roadmap técnico del paper (fases 0-6)
│
├── docs/
│   ├── LEAD-DASHBOARD.md        ← ESTE DOCUMENTO (vos)
│   ├── STATE-2026-04-29.md      ← snapshot público para el equipo
│   ├── SETUP-LOCAL.md           ← onboarding 10-15min para nuevos
│   ├── OPERATIONS-VPS.md        ← estado real VPS, deploy, troubleshoot
│   ├── PAPER-MAESTRO.md         ← spec funcional completa
│   ├── PROPUESTA-CMADRID.md     ← contrato/SLA/GDPR
│   ├── RESUMEN-EJECUTIVO.md     ← visión 10min
│   ├── DOCUMENTO-EJECUTIVO.md   ← versión larga del ejecutivo
│   ├── STYLE-GUIDE-MANAGER.md   ← guía estilo del top-nav nuevo (Alejandro)
│   └── team/
│       ├── antonio.md
│       ├── jesus.md
│       ├── alejandro.md
│       ├── joel-en.md           ← inglés
│       └── joel-onboarding-complete.md  ← inglés, scoring + simulator
│
├── memory/
│   ├── MEMORY.md                ← índice maestro
│   ├── decision-*.md            ← D-WF-001, D-SCR-001, D-MT-001, D-FE-001
│   ├── arquitectura-invariantes.md  ← las 9 reglas que no se rompen
│   ├── modelo-oposicion-publica.md
│   ├── contexto-cmadrid.md
│   ├── equipo.md
│   └── gotchas-sprint.md        ← G-001..G-013, trampas no obvias
│
├── app/
│   ├── __init__.py              ← create_app, registry de blueprints. SENSIBLE.
│   ├── config.py                ← Dev/Test/Prod configs. SENSIBLE.
│   ├── extensions.py            ← db/jwt/socketio/etc. SENSIBLE.
│   ├── middleware/              ← audit + jwt_handlers. SENSIBLE.
│   ├── utils/decorators.py      ← require_role/require_org. SENSIBLE.
│   ├── models/
│   │   ├── auth.py              ← User, Organization, UserRole
│   │   ├── session.py           ← Attempt + RawSamples
│   │   ├── training.py          ← Convocatoria, Enrollment, AttemptEvent, Ranking, AuditLog, RfidCard
│   │   ├── vehicle.py
│   │   └── event.py             ← legacy fleet, NO confundir con AttemptEvent
│   ├── blueprints/              ← 12 blueprints. Ver §Lo que está
│   ├── services/                ← VACÍOS hoy (tarea 8 los va a llenar)
│   ├── workers/                 ← VACÍOS hoy (tarea 9)
│   ├── sockets/                 ← VACÍOS hoy
│   ├── templates/manager/       ← layout nuevo "CMadrid Training" (Alejandro)
│   ├── templates/base.html      ← layout viejo "DOBACKSOFT" (heredado)
│   └── static/
│
├── setup_db.py                  ← schema + seed básico (5 users + 1 org)
├── seed_demo.py                 ← seed demo (11 students + 2 conv + 49 attempts)
├── wsgi.py                      ← entry point Flask + SocketIO
└── celery_worker.py             ← entry point Celery (vacío hoy)
```

---

## 🤖 Agentes / automatización en marcha

| Tipo | Cuándo | Qué hace | ID |
|---|---|---|---|
| Routine remoto Anthropic | sáb 09/05 09:00 Madrid | Pre-demo smoke check (endpoints, branding, PRs) + checklist SSH para vos | `trig_01Ww8AJT5DvVkEDvg3PhPuok` — gestión: https://claude.ai/code/routines/trig_01Ww8AJT5DvVkEDvg3PhPuok |

---

## ✏️ Próximas actualizaciones a este doc

Cuando algo cambie sustancialmente, **actualizá la fecha del header** y agregá una entrada en este log:

| Fecha | Cambio |
|---|---|
| 2026-04-29 | Creación inicial. Cierre día 2 del sprint. |
