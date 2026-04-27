# Joel — Your Work on Training

## 14-day Sprint · CMadrid Demo: Monday, May 11th, 2026

> ⚠️ **Read [`joel-day1-en.md`](joel-day1-en.md) FIRST.** It contains your glossary, day-1 plan, office logistics (we're in **Córdoba**, southern Spain — the client CMadrid is in Madrid, we travel only for the demo), and cultural notes. This document (`joel-en.md`) is for **days 2 onwards** — your full role reference. **Don't read this on day 1.** Open it Wednesday morning, when you're settled and the project has actual code in it.

> **Reality check (written 27/04/2026):** the repo `cosigein/training` was just created and only contains documents. **No code, no `apps/`, no `packages/`, no `e2e/` folders exist yet.** Folder structures and test layouts described below are **the target**, not the state. We materialize them during week 1, starting with the kickoff scaffolding session on Tuesday 28/04.

---

| | |
|---|---|
| **Your role** | Scoring Simulator (sole owner) + QA + E2E Tests + Seed Data + CI/CD |
| **Your tech lead** | Antonio (technical director) |
| **Your peers** | Jesús (backend) · Alejandro (frontend) |
| **Your main issue** | [#5 — Simulator + QA + E2E + Seed Data + CI/CD](https://github.com/cosigein/training/issues/5) |
| **Shared issues** | [#1 — Day-1 scaffolding](https://github.com/cosigein/training/issues/1) · [#6 — Sprint conventions](https://github.com/cosigein/training/issues/6) |
| **Master document** | `docs/PAPER-MAESTRO.md` (in Spanish — full reference when in doubt) |

---

# 1. Why this role — and why I assigned it to you

```
   You're NEW to the team. That's an ADVANTAGE, not a problem.
   Testing the system from outside forces you to understand
   how it's used, not just how it's built.

   Your role is high-leverage:

   1. SIMULATOR end-to-end (SOLE OWNER)
      It's the most marketable piece for the CMadrid client.
      It lets users test rule changes WITHOUT touching production.

   2. E2E TESTS (Playwright)
      The first thing teams sacrifice when no one owns it.
      You're that owner.

   3. REALISTIC SEED DATA
      Critical for the demo to feel credible.
      Not "Test User 01" — data that looks real.

   4. CI/CD
      Setup that automates everything. Every push to main → staging.

   5. DEMO READINESS
      Every Friday you tell me what works and what doesn't.

   6. DAY 13 — KIOSK TORTURE
      You lead the deliberate attack on the kiosk.

   What you do NOT do this sprint:
   - Domain logic (that's Jesús)
   - User-facing screens (that's Alejandro)
   - Webfleet (that's Antonio)
```

---

# 2. What we're building (5 minutes)

**Training** is a **competitive evaluation system** (Spanish public examination) for fire-truck driver candidates at CMadrid (Madrid Region Fire Department). ~265 candidates compete for a fixed number of spots.

```
   COMPETITIVE EXAM model:
   · The system does NOT issue "pass/fail" per attempt. It issues a SCORE.
   · The ranking is updated daily.
   · At convocation closure, PASS/FAIL is issued based on final ranking + spots.
   · Scores are IMMUTABLE.
   · The 3-step closing requires TWO different admins.
   · After closure: 24h reversal window (SUPER_ADMIN only).
   · After 24h → LOCKED (absolutely irrevocable).
```

**Four user types:** Candidate (consults), Manager (supervises, resolves audit requests), Admin (configures, closes), In-cabin driver (kiosk, no scores shown).

**Two data sources:** Doback Elite (in-vehicle sensor + own GPS) + Webfleet (Bridgestone's external platform).

---

# 3. Your territory — the simulator is your flagship

The simulator spans backend and frontend. Your job is to **integrate the pieces and own it end-to-end**:

```
training/
├── apps/api/src/routes/
│   └── scoring.simulate.ts       ← YOUR CODE (endpoint)
│                                    Jesús writes the core logic,
│                                    you integrate it.
│
├── packages/scoring/
│   └── simulate.ts               ← YOUR CODE (pure logic)
│                                    Day 11 you pair with Jesús.
│
├── apps/web/src/pages/admin/
│   └── ScoringSimulator.tsx      ← YOUR CODE (screen D12)
│                                    Alejandro helps with reusable
│                                    UI components.
│
├── seed/
│   ├── students.ts
│   ├── enrollments.ts
│   ├── routes.ts
│   ├── attempts.ts
│   ├── webfleet-fixtures.ts
│   ├── sensor-fixtures/
│   ├── simulation-fixtures.ts
│   └── run.ts
│
├── e2e/
│   ├── playwright.config.ts
│   ├── manager/
│   ├── alumno/  (= candidate)
│   ├── admin/
│   ├── kiosko/  (= kiosk, in-cabin device)
│   └── flujo-completo.spec.ts  (= full-flow integration test)
│
├── .github/workflows/
│   ├── ci.yml
│   └── deploy-staging.yml
│
└── docs/
    ├── DEMO-READINESS.md         ← YOUR DOC (weekly status)
    └── SIMULATOR-USER-GUIDE.md   ← YOUR DOC (for CMadrid)
```

---

# 4. The 9 architectural invariants — read them, understand them

You don't implement these (Jesús does), but **your E2E tests verify them**.

```
1. INGEST IDEMPOTENCY
   Test: uploading the same file twice → no duplicate samples.

2. REPRODUCIBILITY
   Test: replay <attempt_id> reproduces identical score.

3. CLOSED ATTEMPT IMMUTABILITY
   Test: close an attempt + try to mutate → fails with clear error.

4. PINNED VERSIONING at CREATE
   Test: activating new criteria_version → existing attempts
   keep their old version.

5. SOURCE + CONFIDENCE orthogonal
   Test: every Event has source ∈ {sensor, webfleet} and
   confidence ∈ {high, low}.

6. FINAL RANKING IMMUTABILITY
   Test: closed convocation → ranking_snapshot is_final cannot be rewritten.

7. DECISION ONLY AT CLOSURE
   Test: a CLOSED attempt has no `decision` field.
   The PASS/FAIL decision only appears in CandidateOutcome
   after /close/confirm.

8. CLOSING REQUIRES DUAL VALIDATION
   Test: /close/confirm with auth.user.id == closing_admin_id → 403.
   Test: the full flow requires all 3 steps.

9. CRITERIA_VERSION PINNED at OPEN
   Test: POST /attempts captures the criteria active AT THAT MOMENT.
```

---

# 5. Your day-by-day calendar

```
WEEK 1 — INFRASTRUCTURE AND INITIAL QA
──────────────────────────────────────

DAY 1 (Tue 28/04)  KICKOFF 09:00 with the whole team.
                   Whole-team scaffolding (10:00-13:00) — your part:
                     bootstrap Playwright, e2e/ workspace, first smoke test,
                     .github/workflows/ci.yml (lint + tsc + tests).
                   First PR merged: chore(e2e): bootstrap Playwright.

DAY 2 (Wed 29/04)  Harden CI. Configure auto staging deploy
                   (assuming staging VPS has been provisioned by Antonio).
                   Initial seed data: 1 convocation, 5 candidates, 2 routes.
                   E2E placeholder tests.

DAY 3 (Thu 30/04)  E2E Test #1: login for the 3 roles (once auth lands
                   from Jesús).

DAY 4 (Fri 01/05)  HOLIDAY — Spanish Labour Day. No work planned.

[weekend — rest]


WEEK 2 — INGESTION, SIMULATOR, FULL TESTS, KIOSK TORTURE
────────────────────────────────────────────────────────

DAY 7  (Mon 04/05) Seed data v2: 10 candidates, 4 routes, 5 empty attempts.
                   E2E Test #2: upload file → attempt created.
                   E2E Test #3: mocked Webfleet sync → events generated.

DAY 8  (Tue 05/05) E2E Test #4: close attempt → matrix reflects score.
                   Seed data v3: convocation with 30 closed attempts.

DAY 9  (Wed 06/05) E2E Test #5: ranking computes and renders in manager UI.
                   Seed data v4 enriched: variants for simulation.

DAY 10 (Thu 07/05) E2E Test #6: audit request + reevaluation flow.
                   Pair with Jesús: simulator logic
                   (packages/scoring/simulate.ts).
                   Start SIMULATOR screen (D12) with Alejandro.

DAY 11 (Fri 08/05) SIMULATOR end-to-end complete + user docs
                   (`docs/SIMULATOR-USER-GUIDE.md`, in Spanish).
                   E2E Test #7: simulator with threshold change,
                   ranking visually re-orders.
                   E2E Test #8: full kiosk flow (idle → RFID → active → close).
                   FULL pass of Annex C checklist from the master paper.
                   Document what does NOT work and why
                   (`docs/DEMO-READINESS.md`, weekly status doc you maintain).
                   Internal demo at 18:00.

DAY 12 (Sat 09/05) KIOSK TORTURE — voluntary. You lead. Whole team participates.
                   Cut wifi · power off device · double RFID · unregistered card
                   · frozen browser · simulated low battery.
                   Each failure → document, decide whether to fix or accept.

DAY 13 (Sun 10/05) DEMO REHEARSAL. 3 full passes on staging.
                   Plan B: pre-recorded screencast as fallback.

DAY 14 (Mon 11/05) CMADRID MEETING — the demo.
```

> **Reality check on day 1.** When you walk in Tuesday morning, the repo has only documents. There's no `apps/`, `packages/`, `e2e/` or `seed/` yet — those folders are created during the morning scaffolding session. Your "bootstrap Playwright" task means physically creating the `e2e/` workspace, not adding tests to one that already exists. The structure described in §3 of this doc is the **target** we're going to build.

---

# 6. THE SIMULATOR — your flagship piece

## 6.1 Why it matters

Changing rules has impact. And in this competitive examination model, the impact is DOUBLE: it changes individual scores **AND** reorders the entire ranking.

The simulator answers questions like:
- "What if I raise the speed-overrun threshold from 10 to 15 km/h?"
- "What if I lower the weight of the 'route' family?"
- "How many candidates would change spots?"

Without simulator → the client changes and prays. With simulator → they see impact first.

## 6.2 How it works

**Input:**
- `convocatoria_id` (which convocation to simulate)
- `criteria_overrides` (which thresholds/weights to change)

**Process:**

```
   1. Take all CLOSED attempts of that convocation.
   2. For each attempt:
      Recompute the score with modified rules.
      (Pure logic — does NOT touch anything in production.)
   3. Build a SIMULATED ranking with the new scores.
   4. Compare ORIGINAL vs SIMULATED ranking.
   5. Identify candidates who CROSS the cut-off (in/out).
```

**Output:**

```typescript
{
  attempts_simulated: [
    { attempt_id, original_score, simulated_score, diff }
  ],
  ranking_original: [
    { enrollment_id, puesto, nota_media, dentro_del_corte }
  ],
  ranking_simulado: [
    { enrollment_id, puesto, nota_media, dentro_del_corte }
  ],
  candidatos_que_cruzan_corte: [
    { enrollment_id, name, direction: 'enters'|'exits',
      original_position, simulated_position }
  ],
  summary: {
    affected_attempts: int,
    avg_score_diff: float,
    decisions_that_would_change: int
  }
}
```

> **Note about Spanish field names**: the schema and API field names are in Spanish (the project's working language) and will not be translated. They are domain-specific terms that match the Spanish public-examination vocabulary CMadrid uses. Treat them as proper nouns: `puesto` = position, `nota_media` = average score, `dentro_del_corte` = within the cut-off, `candidatos_que_cruzan_corte` = candidates who cross the cut-off line, `convocatoria` = convocation/exam call.

## 6.3 Endpoint

```
POST /scoring/simulate

Body: {
  convocatoria_id: string,
  criteria_overrides: {
    family: 'estabilidad' | 'velocidad' | 'ruta' | 'conduccion',
    rule_id: string,
    threshold?: number,
    weight?: number
  }[]
}

Auth: ADMIN

Response: the object described above.
```

**Who does what:**
- **Jesús** writes `packages/scoring/simulate.ts` (pure function `simulate(attempts, overrides) → newScores`).
- **You** write the endpoint `apps/api/src/routes/scoring.simulate.ts` that calls that function + builds the new ranking + compares with the original.

## 6.4 Screen D12 — Simulator

| Frontend ownership | Your role |
|---|---|
| You own this screen | Alejandro helps with base UI components (`<ScoreBreakdown>`, layouts) |

```
   ┌──────────────────────────────────────────────────────┐
   │ Scoring Simulator · Convocation 2026-A               │
   ├──────────────────────────────────────────────────────┤
   │                                                      │
   │ Base version: [v2.1 (active) ▾]                      │
   │ Apply to:     [Convocation 2026-A ▾]                 │
   │                                                      │
   │ Modify rules:                                        │
   │ ┌──────────────────────────────────────────────┐    │
   │ │ Family    Rule               Original  New  │    │
   │ │──────────────────────────────────────────────│    │
   │ │ Stability harsh-brake threshold  8.0    10.0│    │
   │ │ Stability harsh-brake weight     0.4     0.4│    │
   │ │ Speed     overrun threshold     10kh   10kh │    │
   │ │ Speed     overrun weight         0.3     0.3│    │
   │ │ Route     deviation max         100m   100m │    │
   │ └──────────────────────────────────────────────┘    │
   │                                                      │
   │ [SIMULATE]                                           │
   │                                                      │
   │ ──────────────────────────────────                   │
   │                                                      │
   │ RESULT (87 simulated attempts):                      │
   │                                                      │
   │ ┌─────────────────────────────────────────────┐     │
   │ │ SCORE IMPACT                                │     │
   │ │  Affected attempts: 87                      │     │
   │ │  Avg score difference: +0.45 pts            │     │
   │ │                                             │     │
   │ │ RANKING IMPACT                              │     │
   │ │  Candidates CROSSING the cut-off:           │     │
   │ │   → 5 enter (moved up in position)          │     │
   │ │   → 5 exit (moved down in position)         │     │
   │ │                                             │     │
   │ │  Top-50 movements:                          │     │
   │ │   - Biggest rise: Pedro M. (+12 positions)  │     │
   │ │   - Biggest fall: Laura B. (-8 positions)   │     │
   │ │                                             │     │
   │ │ [VIEW FULL LIST]   [EXPORT CSV]             │     │
   │ │                                             │     │
   │ │ ⚠ Activating the new version does NOT      │     │
   │ │   reprocess already-closed attempts.        │     │
   │ │   It only affects future ones.              │     │
   │ │                                             │     │
   │ │ [DISCARD]   [SAVE AS NEW VERSION]           │     │
   │ └─────────────────────────────────────────────┘     │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

**This is the most marketable piece for the CMadrid client.** Polish it.

## 6.5 SIMULATOR-USER-GUIDE.md

Short documentation (1-2 pages) **for the CMadrid admin** explaining how to use the simulator. Tone: clear, jargon-free, with examples. **Write it in Spanish** (the client's language).

```
   Structure:
   1. What the simulator is for (1 paragraph)
   2. How to open the simulator (step-by-step)
   3. How to modify a rule
   4. How to read the result (score impact + ranking impact)
   5. How to save a new version (and what happens next)
   6. What the simulator does NOT do (doesn't touch production,
      doesn't reprocess closed attempts, isn't a prediction)
```

---

# 7. E2E Tests (Playwright) you must have

## 7.1 Structure

```
e2e/
├── playwright.config.ts
├── manager/
│   ├── login.spec.ts
│   ├── matriz.spec.ts        (= matrix)
│   ├── ranking.spec.ts                ← v6
│   ├── examinador.spec.ts    (= examiner)
│   └── auditoria.spec.ts              ← v6 (resolve with Confirm/Reject/Reev)
├── alumno/                   (= candidate)
│   ├── dashboard-con-standing.spec.ts  ← v6
│   ├── historial.spec.ts     (= history)
│   ├── pedagogico.spec.ts    (= pedagogical detail)
│   └── solicitar-auditoria.spec.ts     ← v6 (request audit)
├── admin/
│   ├── convocatorias.spec.ts          ← v6
│   ├── cerrar-convocatoria.spec.ts    ← v6 (3 steps)
│   ├── simulador.spec.ts              ← v6 (you test your own work)
│   └── gdpr-export.spec.ts            ← v6
├── kiosko/
│   ├── pairing.spec.ts
│   ├── flujo-rfid.spec.ts    (= RFID flow)
│   ├── recovery.spec.ts                ← v6
│   └── logs-export.spec.ts
└── flujo-completo.spec.ts              ← final integration test
```

## 7.2 Critical tests, one by one

### Test #1 — 3-role login (day 3)

```
Scenario: Login works for all 3 roles
  Given an existing admin user
  When they navigate to /login and complete credentials
  Then they reach the Admin Dashboard

  (same for manager, same for candidate)
```

### Test #2 — Sensor file upload creates samples (day 4)

```
Scenario: File upload creates raw_samples
  Given an attempt created by admin
  When a manager uploads a sensor TXT file
  Then the attempt has >0 raw_samples
  And uploading the same file twice does NOT duplicate samples (idempotency)
```

### Test #3 — Webfleet sync brings events (day 5)

```
Scenario: Webfleet sync brings events
  Given an attempt created and a file uploaded
  When mocked Webfleet sync runs
  Then the attempt has >0 events of webfleet source
  And events have source and confidence assigned
```

### Test #4 — Closing attempt produces score (day 8)

```
Scenario: Closing attempt computes score
  Given an attempt with samples and events
  When manager clicks "close"
  Then the attempt has frozen_at != null
  And it has score 0..10
  And it does NOT have a `decision` (it's just a score, not a verdict)
  And it has >0 score_audit rows
  And it appears in the manager's matrix
```

### Test #5 — Ranking computes (day 9)

```
Scenario: Nightly ranking computes and shows
  Given N closed attempts in a convocation
  When the ranking cron is triggered manually
  Then a RankingSnapshot exists with N entries
  And the manager sees the ranking on screen M5
  And positions are correctly ordered
```

### Test #6 — Full audit flow (day 10)

```
Scenario: Candidate requests audit, manager resolves
  Given a closed attempt with a low score
  When the candidate requests audit from A5 with reason ≥30 chars
  Then it appears in the manager's dashboard (M2)
  When the manager resolves with "Create reevaluation"
  Then a new attempt with parent_attempt_id exists
  And the original attempt is NOT modified (frozen_at intact)
  When the manager resolves ANOTHER audit with "Reject"
  Then the AuditRequest has status REJECTED
```

### Test #7 — Simulator (day 11)

```
Scenario: Simulator returns decision diff
  Given N closed attempts with criteria v2.1 in a convocation
  When admin opens D12 and simulates with threshold X changed
  Then the response has N simulated attempts
  And shows ranking_original vs ranking_simulado
  And identifies candidates who cross the cut-off (in/out)
  And NOTHING in production has changed (attempts keep original score)
```

### Test #8 — Kiosk flow (day 11)

```
Scenario: Kiosk opens and closes attempt via RFID
  Given a paired kiosk and two assigned RFID cards (A and B)
  When tap RFID-A is simulated
  Then the kiosk shows K3 (Active) with candidate A
  And an attempt is created in backend
  When tap RFID-B is simulated (after >5s wait period)
  Then the first attempt closes (without penalty,
       INTERRUPTED_BY_OTHER_CARD or ABANDONED depending on context)
  And a new attempt opens for B
```

### Test #9 — Kiosk recovery (day 13)

```
Scenario: Kiosk reopens and detects in-progress attempt
  Given a kiosk with an attempt in progress
  When browser reload is simulated
  Then K4 (Recovery Modal) appears
  And lets the user continue or close the attempt
```

### Test #10 — Convocation closing 3-steps (day 11+)

```
Scenario: Closing with dual admin
  Given an OPEN convocation with N closed attempts
  When admin#1 calls POST /close/preview
  Then they see the simulated final ranking
  When admin#1 calls POST /close/initiate
  Then convocation moves to CLOSING
  When admin#1 tries /close/confirm with their own account
  Then 403 (dual-admin validation)
  When admin#2 (different) calls /close/confirm with re-auth
  Then convocation moves to CLOSED
  And ConvocatoriaCloseAct exists with SHA256
  And N CandidateOutcome rows exist with decision PASS or FAIL
  And reversal_window_until = closed_at + 24h
```

---

# 8. Seed data — make the demo credible

```
   FOR THE DEMO TO BE CREDIBLE, THE DATA MUST LOOK REAL.
   NOT "Test User 01". REALISTIC NAMES, PLAUSIBLE DISTRIBUTION.
```

## 8.1 Demo cohort

```
   1 convocation "2026-DEMO" with:
     - 50 candidates (demo scale, not 200)
     - 10 spots
     - 4 routes: Urban center · National highway ·
                 Mixed with roundabout · Industrial park
     - Closure date: ~30 days after the demo
     - 50 RFID cards assigned (1 per candidate)

   Required admin users for /health/deep to pass:
     - 1 SUPER_ADMIN: "supervisor@cmadrid.es"
     - 2 distinct ADMINs: "admin1@cmadrid.es", "admin2@cmadrid.es"
     - (you need them to demo the dual-admin closing flow)
```

## 8.2 Attempts distribution

```
   Total ~30 closed attempts with varied scores:

   - 18 attempts with varied scores (4-9)
   - 4 attempts with audits:
       2 CONFIRMED (manager confirmed without reevaluating)
       1 REEVALUATED (manager created reevaluation)
       1 REJECTED (no merit)
   - 3 attempts in pending_data_review
   - 2 ABORTED_TECHNICAL attempts (to be retaken)
   - 1 ABANDONED attempt
   - 1 INTERRUPTED_BY_OTHER_CARD attempt
   - 1 in-progress attempt (status OPEN)

   data_quality distribution:
     - 22 HIGH
     - 5 MEDIUM
     - 3 LOW

   Demo-visible cases:
     - 1 candidate with 3 consecutive failures (matrix alert ⚠)
     - 1 candidate with clear evolution (improving route by route)
     - 1 candidate with all routes passed (top 3 ranking)
     - 1 candidate with reevaluation that improves their score
     - 1 candidate without completing all routes (ranking penalty)
```

## 8.3 Webfleet + sensor fixtures

```
   - 10 sensor TXT files (realistic fixtures)
   - 10 JSON payloads simulating Webfleet responses
   - Cover cases:
     · Clean data → high score
     · Data with harsh brakes → mid score
     · Data with route deviation → fail
     · Data with gaps → data_quality MEDIUM
     · Data with many gaps → data_quality LOW
     · Webfleet down (full gap, Doback Elite covers with own GPS)
```

## 8.4 Simulator-specific data

```
   For the simulator demo to have impact:

   - Scores distributed so that changing 1 threshold moves
     ~5 candidates between in/out of the cut-off
   - Intentional ties (same points) to show tiebreak
   - A clearly-defined "principal route"
```

---

# 9. CI/CD setup

## 9.1 `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm run test:unit
      - run: npm run test:e2e:headless
      - run: npm run build
```

## 9.2 `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy Staging

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy-staging.sh   # SSH to dobacksoft-vps
      - run: npm run smoke-tests
      - name: Notify
        run: ...   # Slack / email / whatever
```

## 9.3 Post-deploy smoke tests

Minimum tests that run after deploy to verify staging is alive:
- `GET /health` → 200
- `GET /health/deep` → 200 (DB + Redis + Webfleet + admin-quorum)
- Admin login works

---

# 10. Demo Readiness — your weekly doc

Every **Friday at 17:00**, you update `docs/DEMO-READINESS.md` (write it in Spanish — Antonio reads it):

```markdown
# Demo Readiness — Week N

## What works end-to-end
- [x] Login 3 roles
- [x] Upload file + processing
- [ ] Reevaluation (in progress, day 10)

## What does NOT work yet
- Kiosk offline when wifi cuts (ETA: day 11)
- Scoring simulator (ETA: day 11)

## Risks detected this week
- Webfleet sandbox sometimes takes 6s to respond.
  Antonio investigating.
- Pedro López seed data does not show reevaluation
  correctly. Reported.

## Action items
- [ ] Antonio: investigate Webfleet slowness
- [ ] Alejandro: fix data_quality badge in matrix

## Demo confidence: 70% (week 1) / 85% (week 2)
```

---

# 11. Day 13 — Kiosk torture (you lead)

Saturday, **4-6 hour session with the whole team**. You direct.

```
   ATTACK 1: cut wifi
     - While an attempt is open, disconnect
     - Is the state visible? Does the sync queue grow?
     - Reconnect. Does sync recover? Are no events lost?

   ATTACK 2: double RFID
     - Same card 2 times in 100ms
     - 2 different cards in 200ms
     - Clear message? State doesn't break?

   ATTACK 3: browser reload
     - F5 with attempt in progress
     - Does Recovery Modal (K4) appear?
     - Is state persisted in IndexedDB?

   ATTACK 4: unregistered card
     - Tap UID that doesn't exist in DB
     - Visible error? Doesn't block kiosk?

   ATTACK 5: simulated low battery
     - Force screen off (simulate wake-lock fail)
     - How does the candidate find out?

   ATTACK 6: Webfleet quota exhausted
     - Artificially fill the quota
     - Sync delayed? Manager finds out?

   ATTACK 7: new card during active attempt
     - Verify the 5-second wait period
     - Verify INTERRUPTED_BY_OTHER_CARD applies
     - The first candidate must NOT be penalized

   Each failure:
   - Document exact case in DEMO-READINESS.md
   - Decide: fix or accept for Phase 2
   - If fixed, re-test
```

---

# 12. If you have additional DevOps strength

If you're also strong in DevOps, scope expands to:

```
   - Setup Sentry for frontend + backend errors
   - Setup basic Prometheus + Grafana (metrics)
   - Automated pre-cutover backups
   - systemd healthchecks
   - logrotate
   - Documented rollback plan
```

**We'll decide at kickoff if your profile allows it.**

---

# 13. Your interface with the rest of the team

## With Antonio

- Antonio is your tech lead. Direct reporting.
- Any demo risk you communicate to him first.
- Antonio speaks Spanish; the team operates in Spanish. **Team chat (`#training-equipo`) is bilingual — write in English when it helps clarity, especially in the first weeks.** DEMO-READINESS.md must be in Spanish (Antonio reads it as a status report).

## With Jesús

- **On day 11 you pair with Jesús** on `packages/scoring/simulate.ts`.
- If he breaks an endpoint, he warns you in advance (it affects your E2E tests).
- If you need a new endpoint, you ask him.

## With Alejandro

- Alejandro helps you with base UI components for D12 (`<ScoreBreakdown>`, layouts).
- If he breaks stable selectors (data-testid in screens), he warns you (breaks your E2E tests).
- If you need specific fixtures for a screen, ask Alejandro what the UI needs.

---

# 14. "Your work is well done" criteria

```
   ✓ Simulator returns ranking impact in <2s for 100 attempts
   ✓ Screen D12 shows top reordering with candidates crossing the cut-off
   ✓ User documentation for the client is clear and short (1-2 pages)
   ✓ 10 E2E tests passing in CI (those listed in §7.2)
   ✓ Credible seed data (no "Test User 01")
   ✓ Seed includes 1 SUPER_ADMIN + 2 distinct ADMINs
     (without this, /health/deep fails and the demo doesn't start)
   ✓ CI/CD working: every push runs tests
   ✓ Auto-deploy to staging on every merge to main
   ✓ Post-deploy smoke tests
   ✓ DEMO-READINESS.md updated every Friday
   ✓ Day 13 executed, failures documented
   ✓ Zero "tests passed locally but not in CI"
   ✓ Critical-flow E2E coverage ≥90%
```

---

# 15. Firm decisions you must accept

```
   D8: Binary confidence in V1 (high/low)
   D11: Global attempt data_quality (HIGH/MEDIUM/LOW)
   D14: COMPETITIVE EXAM model — your tests verify that NO
        per-attempt decision exists, only per-convocation at closure
   D17: ABANDONED / ABORTED_TECHNICAL / INTERRUPTED_BY_OTHER_CARD distinction
   D22: 3-step closing with dual admin — your E2E tests verify it
   D24: Doback Elite with device JWT — your tests mock the device
   D25: criteria_version pinned at OPEN — your test verifies that
        a mid-flow criteria change does NOT affect an
        already-created attempt
```

---

# 16. Mini glossary (Spanish ↔ English)

| Spanish (codebase term) | English | Meaning |
|---|---|---|
| **Attempt** | (same) | An evaluation attempt. Your test #4 closes one and verifies score. |
| **Convocatoria** | Convocation / exam call | A specific public-examination process. |
| **Enrollment** | (same) | A Student's enrollment in ONE convocation. Multiple possible per Student. |
| **Student** / **Alumno** | Candidate / Student | The human being evaluated. |
| **Manager** | Manager / Examiner | Read-only role that supervises and resolves audit requests. |
| **Plazas** | Spots / vacancies | Fixed number of approved candidates at closure. |
| **Ranking** | (same) | Competitive ordering. Your test #5 verifies it. |
| **Corte provisional** | Provisional cut-off | The line between top N (=spots) and the rest. |
| **Cierre** | Closing | Administrative 3-step process (D5-A, D5-B, D5-C). |
| **Acta PDF** | Closing minutes (PDF) | Document generated at closure with SHA256 integrity hash. |
| **Auditoría** | Audit (request) | Formal request from candidate (A5). Manager resolves (M7). |
| **Reevaluación** | Reevaluation | New attempt created by manager after a confirmed audit. |
| **Doback Elite** | (proper noun) | Internal-product physical device installed in each truck. |
| **Webfleet** | (proper noun) | Bridgestone's external fleet-management platform. |
| **Kiosko** | Kiosk | The in-cabin device of the truck. |
| **APTO / NO_APTO** | PASS / FAIL | The final decision at convocation closure. |
| **CLOSED / LOCKED** | (same) | Post-closure states. CLOSED = revertible 24h. LOCKED = absolute. |
| **/health/deep** | (same) | Healthcheck verifying DB + Redis + Webfleet + admin-quorum. |

> **Important:** the codebase and schemas use Spanish terms. The above table is for your internal reference, not for translation in code. If you write a comment in code, write it in Spanish to match the rest (one-line, simple — copy nearby comments). **Team chat is bilingual** — write in English when it helps clarity. **DEMO-READINESS.md is in Spanish** because it's a status report Antonio reads.

---

**For additional detail, see the master paper (in Spanish). Daily standup at 9:30. Let's go.**
