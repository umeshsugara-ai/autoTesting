# AutoTester — Target & Roadmap

**What this file is.** The human-readable roadmap: what is *shipped* vs what is *target*, as a
step-by-step checklist, so any session (human or agent) can open it and know exactly where we are
and what is next. The machine backlog with done-checks is `.goal/goal.json` (55 tasks); this is the
milestone view over it. Open me at session start alongside `docs/SNAPSHOT.md`.

**Legend.** `[x]` ✅ shipped & checker-verified · `[~]` 🟡 shipped, proven on fixtures only (not yet
on a real product) · `[!]` 🔒 blocked on a human input · `[ ]` 🎯 target, not built yet.

**Read the honesty rule first:** a box is ticked only when the code exists AND a checker/test proved
it. Coverage never counts an unexplored branch as tested. Goal statements say "AutoTester **will**";
status statements say "currently does".

---

## The two-layer goal

### North Star (the one line)
> **Give AutoTester a product, not a test script.** It will independently discover how the product
> works, systematically explore its meaningful states and branches, decide what is working or
> suspicious, preserve evidence of every failure, and re-verify the product after every release.

### Two sentences to remember
- **Vision:** explore the product like a *graph*, not a *journey*.
- **Proof:** find the same real defects as a strong human tester — with fewer false positives,
  transparent coverage, and reproducible evidence.

### Product goal (full, "AutoTester will…")
AutoTester will be an autonomous end-to-end software-testing platform that can learn, explore and
validate a web application with minimal prior knowledge. Given a URL, scoped test credentials and
optional evidence (business flows, requirements, videos, screenshots, docs, existing test cases), it
will progressively build a persistent model of the application's screens, states, actions and
workflows. Rather than following one likely journey, it will maintain the application's **unexplored
testing frontier**: every meaningful action from a state is either exercised or explicitly accounted
for as pending / blocked / unsafe / unsupported / intentionally skipped — never silently dropped.
The engine will combine bounded graph-exploration strategies (breadth-first discovery, deeper
workflow traversal, structural state deduplication, loop detection, reliable backtracking & state
restoration, risk-based prioritisation). For each workflow it will test the expected path plus
negative, boundary, edge, permission, recovery and adversarial scenarios. Where verified business
knowledge exists it is the explicit **oracle**; where it is absent, AutoTester runs in discovery
mode and clearly separates confirmed regressions from AI-inferred suspicion. Every action yields
traceable evidence (what was attempted, prior state, what changed, why it was classified as it was).
Coverage measures exercised-vs-discovered; untested branches stay visible. After releases it reuses
its product understanding to re-exercise workflows, find regressions, reproduce the exact failing
path, and report failures + remaining gaps. Later versions extend below the UI (API / backend /
infra signals) for authorization, security, reliability, integration and performance defects. First
acceptance targets: Vidysea ERP and Pathlynks. First proof of quality: a measured comparison against
human testers on defects found, false-positive rate, coverage and effort.

---

## The differentiator (BFS/DFS is a mechanism, not the moat)

State-graph crawling is not new (Crawljax ~2010s; QA.tech commercially today). AutoTester's edge is
the **product**, not any one algorithm:

> Exploration quality × Oracle quality × State restoration × Coverage honesty = AutoTester quality

If exploration is great but every oddity is called a bug → useless. If the oracle is brilliant but
only 8% is seen → insufficient. Both must hold together.

---

## Issue classification (the credibility layer) — 🎯 target taxonomy
Every finding must carry exactly one label, so AI inference is never dressed as fact:
`CONFIRMED REGRESSION` · `LIKELY DEFECT` · `SUSPICIOUS BEHAVIOUR` · `UX / CONSISTENCY ISSUE` ·
`PERFORMANCE ANOMALY` · `SECURITY CONCERN` · `UNABLE TO VERIFY` · `EXPECTED / PASSED`.
*(Today: execute/grade produce PASS/FAIL/INCONCLUSIVE verdicts; the richer taxonomy is target.)*

---

## Target pipeline (DISCOVER + MODEL become first-class)
**Today (shipped):** `INGEST → EXPAND → EXECUTE → GRADE → REPORT/COVERAGE → BENCH`, with crawl/
explore a standalone **Track B** capability that hydrates the FlowSpec — *not* a canonical stage.
**Target:**
```
INPUT → { INGEST(evidence) | DISCOVER(app) } → MODEL(state/action graph) → EXPAND
      → EXPLORATION FRONTIER → EXPLORE+EXECUTE → OBSERVE → GRADE → EVIDENCE
      → COVERAGE → REPORT → LEARN → RE-RUN
```
DISCOVER and MODEL are primary stages, not side features. 🎯 (promotion tracked as T-163.)

---

## Milestones — what's built vs what's next

### M0 · Foundations & governance — ✅ done
- [x] T-000 P0 design lock: schema, core, provider seam, doctor, ARCHITECTURE
- [x] T-004 schema research scout → `docs/research/schema-2026-09.md`
- [x] T-005 living map + feature ledger + CLAUDE.md router + doctor freshness
- [x] T-020 filestore: every artifact JSON/JSONL under `projects/<slug>/`
- [x] T-121 governance: register plan.md, goal tasks, Track A/B backlog
- [x] T-160 revised-goal governance (D-023: the T-16x roadmap registered)

### M1 · Credential boundary & browser substrate — ✅ done
- [x] T-011 `.env` → `{{SECRET:KEY}}` fill-time injection, domain-scoped (security-critical)
- [x] T-010 headed Playwright + persistent profile + screenshot masking
- [x] T-045 read-only Mongo assertion helper (production Mongo never written)

### M2 · Core pipeline stages — ✅ built / 🟡 fixture-proven
- [x] T-060 ingest: video/docs → FlowSpec with SourceRefs
- [x] T-065 FlowSpec review gate (nothing drives off an unreviewed spec)
- [x] T-070 expand: FlowSpec → best/worst/edge cases per CaseClass
- [x] T-040 execute: script-first runner → RawResult + Evidence (observe only)
- [x] T-041 grade: independent stateless judge (rejects fake-pass, no evidence)
- [x] T-080 agent fallback loop → durable re-runnable script
- [x] T-055 multi-vendor provider fallback (Anthropic→Gemini→Ollama→ChatGPT)
- [x] T-090 coverage: route/screen diff → CoverageGap → VideoRequest
- [~] T-120 bench: human-vs-AI scorecard — *engine shipped; only real numbers come from T-136*

### M3 · First real proof on a product — ✅ done
- [x] T-030 onboard Pathlynks (project.json + knowledge file)
- [x] T-050 first real run: 3 hand-written Pathlynks cases verdicted in a headed browser
- [x] T-110 regression proof: break a staging feature, confirm exactly that case FAILs

### M4 · Exploration engine (Track B) — ✅ shipped, with named gaps
- [x] T-140 observation primitives + actuator choke-point
- [x] T-141 screen identity (url templating + structural signature) + crawl schema/store
- [x] T-142 explorer safety layer (deny-list, write-policy matrix, dialog breaker)
- [x] T-143 bounded **BFS** crawl stage + `qa/contracts/explore.md` (checker-PASS)
- [x] T-144 crawl → FlowSpec merge + exercised/discovered coverage + crawl report
- [x] T-124 consent gates as an artifact (RunApproval) — real done-check for T-145
  - Shipped ✅: screen-level FIFO frontier · state dedup · loop detection · 5-step restoration
    ladder · enumerate-all-controls-per-screen · honest coverage (45/677 = 6%).
  - 🎯 **edge-level `(state,action)` frontier** — today a bound (`per_node_action_cap=25`) turns
    remaining actions into coverage *holes*, not persisted future work. (folded into T-165)
  - 🎯 **DFS / adaptive / risk-first traversal** — today BFS only. (target)

### M5 · Video-learning (Track A) — ✅ done (real ERP recordings)
- [x] T-130 video-learning schema + storage · [x] T-131 hardened Gemini vision provider
- [x] T-132 host media prep (probe/chunks/transcript/frames)
- [x] T-133 two-model ensemble + deterministic adjudication + Issue derivation + Excel + scorer
- [x] T-134 product map / journeys / issues / sources pages · [x] T-135 coverage/merge/expand reconnected

### M6 · Unified intake & no-CLI UI — ✅ done
- [x] T-100 FastAPI onboarding, masked `.env` editor, live run view, report
- [x] T-161 unified project intake (URL, credential refs, evals, conditions, use cases, sources)

---

## THE PROOF (must clear before AutoTester counts as "working on a real product")

### M7 · ERP trust number — 🔒 human-gated, then 🎯
- [!] T-122 ERP login case + first logged-in run — **needs ERP_EMAIL/ERP_PASSWORD from Umesh** (401 today)
- [!] T-145 live bounded READ_ONLY crawl of vidysea.com/erp — needs T-122 + consent (CRITICAL, dual-check)
- [!] T-136 score erp1/2/3 vs `ERP_Issues_Trainers.xlsx` → real recall/FP/time — **needs the truth sheet**
- [ ] T-123 medium credential-safety batch · [ ] T-125 test catalog (runnable/blocked + cheap→expensive)
- [ ] T-126 governance debt sweep (adapter allowlist, QUEUE/SNAPSHOT drift, ledger backfill)

*Status truth: the plumbing is real, but everything downstream of a **learned** FlowSpec is
fixture-proven only. The ERP trust number is the first time AutoTester is measured against a human.*

---

## THE PRODUCT VISION (reusable platform) — 🎯 target, mostly unbuilt

### M8 · Systematic exploration upgrades
- [ ] T-163 resumable learn-or-explore orchestrator + durable per-stage checkpoints (promotes DISCOVER/MODEL)
- [ ] T-165 BFS frontier completeness + forward/back recovery + first-party API/network assertions

### M9 · Durable product model
- [ ] T-164 durable **Portal Persona** JSON + knowledge page (cross-run graph; today per-crawl scoped)
- [ ] T-162 multi-source adapters (Drive, video, audio, doc, email, text → one evidence model)

### M10 · Compile, re-run, report
- [ ] T-166 traceable eval compiler (rules + taught flows + persona + discoveries → best/worst/edge)
- [ ] T-167 commit/release-triggered visible-browser regression (consent, history, resumable retries)
- [ ] T-168 unified damage-control report (regression diff, API failures, workflows, screenshots, Excel)

### M11 · Adversarial / below-the-UI (Track C)
- [ ] T-150 Track C governance (file ai-target.md + adversarial.md criteria for the checker)
- [ ] T-151 read-only AI-target discovery + deterministic signals + classification
- [ ] T-152 AI check registry + catalog matching · [ ] T-153 behavioural checks graded by the judge
- [ ] T-154 bounded adversarial pass behind consent gate 2 (HIGHEST-RISK unit) · [ ] T-155 unified tiered AI report

### M12 · The finish line
- [ ] T-169 generic two-mode acceptance (rich-teaching mode AND url+credentials-only mode), no CLI,
      measured vs a human on bugs / false positives / coverage / time — **this is "done".**

---

## Definition of done (product-level)
1. ERP trust number exists (T-136): real recall / false-positive / time vs the trainer truth sheet.
2. Both intake modes work on a real target and beat-or-match a human tester (T-169).
3. Every finding is evidence-backed and correctly classified; coverage shows untested branches.

## Progress (from `.goal/goal.json`, 2026-09-22): 35 / 55 done (64%). Next current task: T-122.
_Machine backlog + done-checks: `.goal/goal.json`. Whole-project screen: `docs/SNAPSHOT.md`._
_Note: rewriting `.goal/goal.json`'s north star or adding DISCOVER/MODEL to `docs/ARCHITECTURE.md`
is a state change that needs an authorizing `docs/DECISIONS.md` entry first (Lab Protocol) — this
roadmap doc does not require one._
