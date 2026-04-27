# Joel — Welcome & Day 1

## You're starting work on Training (Madrid). This is your day 1 guide.

> **Reality check (written 27 April 2026):** the repo `cosigein/training` was created today and only contains documents — no code, no scaffolding, no CI yet. The 14-day sprint **starts Tuesday 28 April** with a kickoff at 09:00 where the four of us set up the project together. Don't try to install or clone anything alone before then.

---

## ⚡ TLDR — what tomorrow looks like in 5 lines

1. **Your role:** QA + simulator + E2E tests + seed data + CI/CD. You don't write product features — you make sure they work and that we ship.
2. **Tonight (Monday):** install Node 20 LTS + Docker Desktop. Accept the GitHub invite. **DO NOT clone the repo, DO NOT install anything else.** That's it.
3. **Tomorrow 09:00 in the office:** 1h kickoff with the team. Then we set up the project scaffolding together (the 4 of us, screen-shared) until ~13:00.
4. **Your first task (afternoon):** bootstrap Playwright in the new `e2e/` workspace, write 1 smoke test, open a PR. Antonio will guide you. ~3 hours of work, very doable.
5. **You don't speak Spanish — that's expected and OK.** This doc + the README in English at the top + your full role doc (`joel-en.md`) are in English. Antonio translates anything else you need.

---

---

## Read this first — the people you'll meet on day 1

| Name | Role | Languages | How to talk to them |
|---|---|---|---|
| **Antonio Hermoso** | Tech lead. Owns the Webfleet code and the client (CMadrid) relationship. | Spanish (native) · English (good) | DM in English is fine. He'll switch for you. |
| **Jesús** | Senior backend. He'll write the core logic; you'll pair with him in week 2. | Spanish (native) · English (basic, slow but works) | Use simple English sentences. Be patient. Code reviews in Spanish — Antonio can translate if needed. |
| **Alejandro** | Frontend lead. He builds all the screens. | Spanish (native) · English (basic) | Day-to-day chat works. For tricky design conversations, ask Antonio to bridge. |
| **You (Joel)** | Simulator owner + QA + tests + seed data + CI/CD. | English. Spanish — learning. | Speak English. Write code comments in Spanish (one-line, simple — copy nearby comments as templates) once code exists. |

```
   Daily standup is at 09:30 sharp. It's in Spanish.
   Don't worry — Antonio will translate the relevant parts for you.
   You speak last, in English. Three sentences max:
     - What I did yesterday
     - What I'll do today
     - Anything blocking me
```

---

## Glossary — read this BEFORE anything else

The codebase will mix Spanish and English. The Spanish words are domain terms — treat them like proper nouns.

| Spanish (in code & chat) | English | What it means |
|---|---|---|
| **alumno** / `Student` | candidate | The person being evaluated. The model is `Student`, conversation says "alumno". |
| **convocatoria** | exam call / cohort | A specific public-examination process. ~265 candidates, fixed spots, fixed close date. |
| **plazas** | spots / vacancies | Number of fixed seats available at the end of the convocatoria. |
| **manager** | manager / examiner | Senior firefighter who supervises evaluation. **Read-only on scores.** |
| **admin** | administrator | Configures the system. Closes convocatorias. |
| **kiosko** | kiosk | The in-cabin tablet inside the truck. Where the alumno taps RFID. |
| **attempt** | (same) | One evaluation = one alumno + one route + one drive. Has a score 0–10. |
| **enrollment** | (same) | A Student's enrollment to ONE convocatoria. Same human, multiple convocatorias = multiple enrollments. |
| **ranking** | (same) | The competitive ordering inside a convocatoria. Updated daily at 06:00 Madrid time. |
| **APTO / NO_APTO** | PASS / FAIL | The final decision per candidate at convocatoria closure. **NOT issued per attempt.** |
| **acta** | closing minutes | The PDF generated at convocatoria closure with SHA256 integrity hash. Legal document. |
| **CMadrid** | Madrid Region Fire Department | The client. ~265 firefighter-driver candidates per call. |
| **Doback Elite** | (proper noun, internal product) | Physical device installed in each truck. Captures sensor + own GPS. |
| **Webfleet** | (proper noun, third-party) | Bridgestone's fleet platform. CMadrid has it contracted. |
| **oposición** | competitive public examination | Spanish public-sector hiring process. Ranking-based. Don't think "exam pass/fail" — think "Olympic qualifier with N spots". |

```
   Why Spanish in code? Because the team works in Spanish, the
   contract documents are in Spanish, and the legal terminology
   has no clean English equivalent. Treat it as foreign vocabulary,
   not as a language barrier.

   Cheat: when you don't recognize a word, look it up in the
   table above. If it's not there, ask Antonio.
```

---

## Why this project exists — in 5 sentences

```
   Spain hires firefighters through public competitive exams (oposición).
   To become a fire-truck DRIVER specifically, candidates must demonstrate
   safe driving on real test routes.
   Today, evaluation is done by a human instructor watching from the
   passenger seat — slow, subjective, hard to defend in court.
   Training replaces that with sensors + automated scoring + a ranking.
   Our client is the Madrid Region Fire Department; ~265 candidates
   compete each year for a fixed number of spots.
```

That's it. Everything else builds on this.

---

## What's actually ready before day 1

This is the **honest** list. Don't assume more.

```
   ✓ The repo cosigein/training exists, with this document and the others
     under docs/.
   ✓ The project plan, schema, and decisions are written down (paper maestro).
   ✓ The team (4 people, including you) is committed to start Tuesday 28/04.

   ✗ NO source code yet. No package.json, no Docker setup, no migrations.
   ✗ NO Slack/Discord/Teams workspace yet — Antonio sets up the team channel
     on day 1 and invites you.
   ✗ NO staging server yet. We provision it during week 1.
   ✗ NO CI/CD yet. You'll set most of it up — that's part of your role.
```

If something here surprises you, ping Antonio before Tuesday morning.

---

## What to do BEFORE Tuesday morning

Three small things. None of them require the project to exist.

```
   ☐ Install Node 20 LTS on your laptop
        node --version  → must print v20.x.x
        (use nvm if you juggle Node versions)

   ☐ Install Docker Desktop (you'll need it for Postgres + Redis later)
        docker --version
        docker compose version

   ☐ Make sure your GitHub account is added to cosigein/training
        Antonio sends the invite — accept it.
        Confirm you can see https://github.com/cosigein/training

   That's it. Don't clone, don't install dependencies, don't write code.
   The four of us set up the scaffolding TOGETHER on Tuesday morning so
   nobody ends up with a slightly different version of anything.
```

## Logistics — confirm with Antonio Monday evening

The day-1 doc can't put these on paper because they vary by office and contract setup. **Ask Antonio in DM tonight** so you don't arrive lost tomorrow:

```
   ☐ Office address (or remote-work confirmation)
   ☐ How to enter the building at 09:00 (reception, code, doorbell?)
   ☐ Wifi network name + password
   ☐ NDA / employment paperwork — does Antonio bring it Tuesday morning,
     or is it already signed?
   ☐ Working hours expectation (Spanish 09:00-18:30 with long lunch is
     the assumption — confirm)
   ☐ Tax / payroll setup if relevant in your contract
   ☐ Lunch — does the team eat together day 1? Where?
```

> If Antonio doesn't reply by midnight, default plan: arrive at 08:45 to whatever address he gave you, ring the bell, ask reception, and have his phone number ready.

---

## Tuesday 28/04 — your actual first day

### Hour by hour

```
   09:00 - 10:00   KICKOFF (whole team)
   ─────────────────────────────────────
   • Antonio explains context, project, the 14-day plan.
   • Silent reading of the master paper (each person reads their section).
   • Q&A. Glossary clarifications.
   • Daily-standup time confirmed (09:30 every weekday from tomorrow).

   10:00 - 13:00   SCAFFOLDING TOGETHER (whole team, screen-shared)
   ─────────────────────────────────────────────────────────────────
   • Decide package manager (npm vs pnpm) and monorepo layout.
   • Create package.json files, TypeScript config, ESLint+Prettier
     shared config.
   • Create docker-compose.dev.yml (postgres:17 + redis:7).
   • Initialize Prisma with the base schema. Run first migration locally.
   • Verify each person can `pnpm dev` (or equivalent) on their machine.
   • Each person creates their own branch chore/setup-<name> and
     opens their first PR (just adding docs/onboarding/<name>.md
     with their notes for the day). This validates the PR/review flow.

   ~13:00 - ~14:00 LUNCH (Spanish lunch is around 14:00, longer than you expect)

   14:30 - 16:00   YOUR FIRST CONCRETE TASK
   ─────────────────────────────────────────
   • Add Playwright to the repo as a top-level e2e/ workspace.
   • Write ONE smoke test: load the placeholder index page that
     Alejandro pushes during the morning scaffolding session.

     IMPORTANT: agree with Alejandro DURING the kickoff what URL
     and what test selector you'll use. Specifically:
       - URL: `http://localhost:5173/` (Vite default)
       - Selector: `data-testid="app-root"` on the root component.
     Without that contract, you write nothing this afternoon.

   • Open a PR: `chore(qa-e2e-bootstrap)` — Playwright + first smoke test.
   • Tag Antonio for review.

   16:00 - 17:00   GITHUB ACTIONS — first workflow
   ────────────────────────────────────────────────
   • Add .github/workflows/ci.yml that runs your test on every PR.
   • Push, verify it runs in CI, fix anything that breaks.
   • Goal: the moment somebody pushes anything to a branch, your
     test runs in CI within 2 minutes.

   17:00 - 17:30   WRAP UP
   ───────────────────────
   • Update docs/onboarding/joel.md with what you did today.
   • Push everything, even WIP.
   • Post in the team channel: "Day 1 done. Local works.
     First test passing. Tomorrow: more E2E tests."

   17:30 onwards   GO HOME
   ───────────────────────
   • Don't work late on day 1. Tomorrow is also a day.
```

### Your goal for day 1

**Not** to build the simulator. Day 1 success looks like:

```
   ✓ Local environment works (you can `pnpm dev` from the repo root)
   ✓ One PR merged (the e2e bootstrap one)
   ✓ CI runs your test on every PR
   ✓ You know who's who and how the team operates
```

If any of the above is blocked → ping Antonio. Don't sit in silence.

---

## Communication

### Team chat

Antonio sets up the team channel on day 1 (Slack, Discord, or Teams — he picks). He'll send you the invite Tuesday morning.

```
   Channel name (likely):   #training-equipo
   Language:                bilingual — Spanish baseline, you can
                            write English. The team will read it.

   Other channels Antonio may create as we grow:
   • #training-deploys      — automated deploy notifications
   • #training-bugs         — bugs and incidents
   • #cmadrid-cliente       — client comms (Antonio only)
```

### What if I'm blocked DURING the kickoff and there's no channel yet?

Until the team channel exists (Tuesday morning), the fallback is:

```
   1. Raise it out loud during the kickoff (everyone is in the same room).
   2. If it's after the kickoff and the channel still isn't ready,
      DM Antonio directly on whatever platform he uses with you.
   3. Don't sit silently for >20 minutes thinking. Ask.
```

### Rules of thumb

```
   ▶ If blocked > 30 min → ask in the team channel, in English, ping Antonio.
   ▶ If you find a bug → file an issue in GitHub with screenshot + steps.
   ▶ If you make a decision that affects the team → write it in the channel.
   ▶ Daily standup 09:30 sharp. Be there. You speak last, in English, 3 sentences.
   ▶ Don't private-message Jesús or Alejandro for non-urgent things —
     they don't always read DMs. Use the team channel.
   ▶ Antonio you can DM directly. He's your manager.
```

---

## The 14-day sprint — overview

```
   WEEK 1
   ──────
   Day 1  (Tue 28/04)  Today. Kickoff + scaffolding + your first PR.
   Day 2  (Wed 29/04)  CI/CD hardened. More E2E placeholders.
   Day 3  (Thu 30/04)  Test #1 (3-role login) once auth lands.
   Day 4  (Fri 01/05)  HOLIDAY — Labour Day. Spain. No work planned.

   WEEK 2
   ──────
   Day 7  (Mon 04/05)  Seed data v2. Test #2 (file upload flow).
   Day 8  (Tue 05/05)  Test #3 + ranking tests + seed v3.
   Day 9  (Wed 06/05)  Audit flow tests.
   Day 10 (Thu 07/05)  Pair with Jesús on simulator core. Start D12 screen
                       with Alejandro.
   Day 11 (Fri 08/05)  Simulator end-to-end + user docs. Internal demo 18:00.
   Day 12 (Sat 09/05)  KIOSK TORTURE day — voluntary. You lead. Whole team helps.
   Day 13 (Sun 10/05)  Demo rehearsal — 3 full passes (with Antonio).

   Day 14 (Mon 11/05)  CMADRID DEMO. The big one.
```

> The Friday holiday on 01/05 is real (Spanish national holiday — Labour Day). The plan absorbs it. Don't worry about catch-up: if we're tight by end of week 1, we'll talk it through together, not in panic.

Don't try to memorize week 2 yet. **Focus on getting day 1 right.**

---

## Cultural notes — small things that help

```
   ▶ FOOD TIMES
     - Breakfast: light, around 09:00
     - Lunch: around 14:00, often 1–1.5 hours, the office often empties
     - Coffee/snack: around 17:00
     - Dinner: 21:00 or later
     If you're hungry at 12:30, you'll be alone.

   ▶ WORK HOURS
     Spanish offices typically work 09:00–18:30 with a long lunch.
     Some teams work intensive jornada in summer (08:00–15:00).
     Ask Antonio what schedule applies here.

   ▶ SIESTA
     It's a tourist myth. Nobody actually sleeps. Don't expect office to
     close in the afternoon. (Some shops do. Offices generally don't.)

   ▶ GREETINGS
     Two cheek kisses (right then left) is normal between people who know
     each other. Handshakes for first meetings or formal contexts. Take
     your cue from the other person.

   ▶ DIRECTNESS
     Spanish team communication can sound blunt to non-Spanish speakers.
     "No me gusta" is not rude — it's information. Don't take it personally.

   ▶ "MAÑANA"
     Doesn't always mean "tomorrow". Sometimes means "soon-ish". Ask for
     concrete dates if you need them.
```

---

## Your full role — when to read the deeper doc

After today, when you're settled (probably day 2 morning), open:

```
   docs/team/joel-en.md         (or its PDF version)
```

That's the long version with everything: simulator architecture, all the tests, seed data plan, CI/CD detailed, the kiosk torture protocol. **Don't try to absorb it all on day 1.**

---

## Document map — which document when

| Doc | When to use |
|---|---|
| **This document** (Day 1) | Today only. After today, you don't need it. |
| **`docs/team/joel-en.md`** | Days 2–14. Your detailed role. Reference. |
| **`docs/PAPER-MAESTRO.md`** (Spanish) | Reference for the whole team. Don't try to read it. Antonio will translate any specific section if you need it. |
| **`README.md`** (root of repo) | Quick navigation. Always available. |
| **`CONTRIBUTING.md`** | Branch rules, PR conventions. Read once. |

---

## If you only remember three things from today

```
   1. Don't try to understand everything on day 1.
      Setup works → first PR merged → you met the team. That's success.

   2. The team operates in Spanish but they'll switch for you.
      Be polite, ask Antonio to translate when you need to, learn
      the glossary words above as you go.

   3. The team channel is your safety net.
      If you're blocked > 30 min, ask there. Antonio reads it constantly.
```

---

**Welcome to the team. Glad you're here.**

**— Antonio**
