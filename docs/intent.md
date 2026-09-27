# Intent — AutoTester

<!-- PLAN phase step 1, written as a BACKFILL (maker SKILL.md init step 2b backfill clause):
     this project shipped M0–M6 before the PLAN rule existed. Drafted from target.md, .goal/goal.json,
     docs/ARCHITECTURE.md and qa/contracts/, not from a fresh interview. -->

**Originator:** Umesh · **Date:** 2026-09-27 · **Status:** draft (backfill — awaiting one approval)

## Problem

Regression testing of Vidysea's web products is done by hand. A tester is given a product, learns
it by using it, writes cases, and re-runs them after every dev cycle. That does not scale, it is
not reproducible, and a feature can silently break an old one between releases with nobody
noticing until a student hits it.

Existing tools need a test script written first. Umesh's framing, kept in his words:
**"give AutoTester a product, not a test script."** And when it meets a screen it does not
understand, it must **ask for a video instead of guessing** — a confident wrong test is worse
than an honest gap.

## Proposed outcome

- **O1** — Given only a URL and scoped test credentials, AutoTester builds and keeps a model of
  the product's screens, states and actions, and can say what it has and has not exercised.
- **O2** — It generates best / worst / edge cases per flow and runs them in a **real visible
  browser** after every dev cycle, so a regression is caught by a run, not by a user.
- **O3** — Every finding carries evidence (what was attempted, prior state, what changed, why it
  was classified that way) and an honest label — AI suspicion is never dressed as confirmed fact.
- **O4** — Coverage is honest: an unexplored branch is reported as unexplored, never as passed.
  Any bound (time, depth, safety) names what it left unreached.
- **O5** — When the model is insufficient for a screen, AutoTester raises a VideoRequest rather
  than inventing behaviour.
- **O6** — On a real product, AutoTester is measured against an expert human tester on bugs found,
  false-positive rate, coverage and time — and wins on those numbers.
- **O7** — Credentials never leak: a secret exists only as a `SecretRef` plus a value in a
  gitignored `.env`, substituted at `page.fill()` time inside the project's allowed domains, and
  masked in every screenshot, log, video and model prompt.

## Affected users and systems

### Audience
**`internal-tool`** — today AutoTester is operated by the Vidysea team against Vidysea products
(Pathlynks first, a second product after). It has a web UI, so UI units still get a live browser
run; persona walks stay limited to 1–2 of the user types below per unit (cost gate).
*Open question Q1 below asks whether this becomes `external-ui`.*

### User types (drafted from how the system is actually used — NOT yet founder-confirmed)
| id | who | goal | blocks on | patience | mental model | confirmed |
|---|---|---|---|---|---|---|
| `dev` | Vidysea developer who just pushed a commit | know within minutes whether the push broke an existing flow | a report that says FAIL without the failing step, the judge's reason or a repro | 2 | CI output, stack traces | — |
| `tester` | the human tester AutoTester is measured against | onboard a product, review the learned FlowSpec, prune bad cases before they cost tokens | cases generated with no way to tell which are actually runnable | 4 | manual test plans, Excel case sheets | — |
| `lead` | Umesh / product lead | see the trust number and the damage-control report; decide ship / no-ship | coverage that looks green because the unexplored part is invisible | 2 | dashboards, one-screen summaries | — |
| `trainer` | domain expert supplying recordings | teach a flow by recording it once; confirm a reported bug is real | being asked for a video with no indication of which screen is missing | 3 | screen recordings, WhatsApp, Excel issue sheets | — |
| `release-manager` | whoever runs the release | trigger the approved suite against a release and get a pass/fail with consent respected | a run that writes to production, or one that cannot be resumed after a crash | 1 | release checklists, approval gates | — |

### Systems
`src/autotester/` (stages · schema · browser · providers · ui) · Playwright/Chromium · the
provider seam (Anthropic → Gemini → Ollama → ChatGPT) · the filestore under `projects/<slug>/` ·
Pathlynks and the Vidysea ERP as acceptance targets · production Mongo, **read-only by
construction**.

## Constraints

- **Credential boundary** (`CLAUDE.md`, hard): values only in gitignored `projects/<slug>/.env`;
  `SecretRef` carries the key and its domain scope, never a value; `assert_no_raw_secrets` gates
  every model call; screenshots mask secret inputs before capture.
- **`write_policy` defaults to `read_only`.** Testing a real product needs a **test account** and
  explicit per-run approval — never a live user's credentials.
- **Production Mongo is never written.** Backend assertions are read-only.
- **Lab Protocol:** `docs/DECISIONS.md` is append-only via `scripts/append_decision.ps1`;
  `docs/ARCHITECTURE.md` prose changes need an authorizing entry first.
- **Design rules** (`uv run autotester doctor`): file ≤ 300 lines, function ≤ 50, one concept one
  place, every domain shape a Pydantic model in `schema/` with `extra="forbid"`, no `*_v2.py`.
- **Vendor independence:** all model calls go through `providers.base.Provider`; prompts are files.
- **Honesty rule:** a capability counts as shipped only when the code exists AND a checker proved
  it. Fixture-proven is stated as fixture-proven.

## Open questions

- [ ] **Q1** — Does AutoTester stay `internal-tool` (Vidysea team only) or become `external-ui`
      (other teams onboard their own products)? This sets how expensive every persona walk is.
- [ ] **Q2** — Are the five user types above right, and which are confirmed? (`dev`, `tester`,
      `lead`, `trainer`, `release-manager`.)
- [ ] **Q3 (carried, AT-281)** — The real two-mode acceptance thresholds for O6/T-169: what recall,
      false-positive rate and time actually count as beating the human? Open since 2026-09-11.
- [ ] **Q4 (carried, AT-218)** — The policy on vacuous guards: what makes a test admissible as
      proof, given the recurring class of guards that cannot fail.
- [ ] PARKED: which second product supplies the trust number — until Pathlynks is proven
      (Umesh 2026-09-24: "not only erp").
