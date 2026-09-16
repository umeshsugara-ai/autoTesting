# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-16T18:05+05:30**; bound strictly to `D:/autoTesting`.
This is the **second Mode B sweep of 2026-09-16** — it supersedes the 11:55 queue, keeps that
sweep's still-open findings verbatim, and adds the ledger-hygiene and gate work that pass did not
cover.

## Correction to this sweep's own dispatch brief (read this first)

- **The dispatch said the last sweep was ~4.9 days ago. It was not.** A full Mode B sweep ran and
  committed at `4714db0` (2026-09-16 11:35, `FINDINGS: 5`), stamping `qa/.last-sweep` and filing
  AT-365…AT-369. The 4.9-day figure was true when the maker queued the dispatch and stale by the
  time it ran. Checks 1–7 were therefore **not re-derived from scratch** here; they were read from
  that sweep, spot-checked, and extended. Stated so the next reader does not count this as two
  independent passes over the same window.
- **The dispatch asked for AT-288/AT-289/AT-290/AT-291 to be renumbered. This sweep did NOT do
  that, deliberately.** `AT-293` is a standing checker governance ruling that forbids it — two
  cycle-1 verdicts and a manifest cite those ids by number, and renumbering would destroy the
  audit trail the T-135 dual check exists to create. The ruling was ratified by the
  `at319-issue-id-collision-reconcile` cycle-1 **PASS**, and all eight rows already carry the
  promised `checker: checkerA|checkerB` + `id_collision` discriminators (re-read on disk this
  sweep, present on all eight). Re-proposing a ruled-and-rejected remedy without flagging it is
  the protocol violation; it is flagged here instead of performed. **If Umesh wants them
  renumbered anyway, that is a decision to overturn AT-293, not a sweep action.**

## What this sweep changed on disk

- **`AT-355` collision resolved.** The ledger carried two `AT-355` rows. The `ingest`/medium row
  (`VisionOptions.thinking_level` is an unvalidated bare str) was renumbered to **`AT-370`** with
  `supersedes_id_collision: AT-355` and a full `id_collision` note. The `ui`/high row (the U+202E
  bidi-override finding) **keeps** the id, because it is the one every other artifact means —
  `qa/contracts/ui.md` U13, `qa/gates/at355-guard-shape.md`, the `at355-refuse-bidi-overrides`
  manifest + verdict, `qa/QUEUE.md`, and the `at345-346` and `at358` verdicts. This deviates from
  AT-319's "renumber the SECOND occurrence" default on purpose: here the second occurrence is the
  cited one. The renumbered row's single old citation
  (`qa/verdicts/at126-127-gemini3-detection.md`, lines 80/105/112/118) is left byte-intact as
  history and named in the new row.
- **Duplicate-id state after this sweep:** `AT-288`, `AT-289`, `AT-290`, `AT-291` only — exactly
  the four AT-293 ruled on, each discriminated. No other id appears twice across 373 rows.
- **Two new findings filed:** AT-375, AT-376 (below).

## Findings — FINDINGS: 2 new, this pass

- **AT-375 (medium, governance)** — id allocation is *still* not collision-safe. `AT-355` is the
  **third** collision event (after `AT-282` and the `AT-288..291` quartet) and it was already
  sitting un-actioned in `qa/gates/at355-guard-shape.md:132`. `qa/adapter.json` declares
  `tools.reserve_id = kernel`, still unused; AT-296 (low, open) already says AT-293's remedy is
  written nowhere a checker reads. **This sweep hit the bug live while filing:** its first append
  took `AT-371`/`AT-372`, which the concurrent `at358` checker had allocated seconds earlier; the
  rows were withdrawn and re-filed as `AT-375`/`AT-376`. Remedy is (a) make the declared
  reservation real, or (b) write the `AT-NNNb` per-checker suffix convention where the next
  checker will read it.
- **AT-376 (medium, tooling, UPSTREAM — outside this root)** — the MC-003 `data_boundary.py` gate
  scans **gitignored** paths. Re-run independently against the uncommitted `data_class: synthetic`
  declaration: **344 violations, of which 335 are under `.work/` and 2 under `profiles/` (both
  gitignored) and exactly 7 are tracked** — `pyproject.toml` (the repo author's own address),
  `qa/gates/at365-data-class-declaration.md`, `qa/issues.jsonl`, and four `qa/verdicts/*.md` whose
  addresses are all synthetic fixtures (`demo.test@evil.com`, `pathlynks.test@evil.test`,
  `pw@pathlynks.test`, `evil.test@sub.example.com`, `pass@vidysea.com`). **Zero real-person data
  in the repo.** Signal-to-noise 2%. The script lives in `D:/ai_os/.claude/skills/`, outside this
  bound root — filed UPSTREAM on the AT-118 precedent, not as a buildable unit here.

## Gates — re-derived from disk, every file in `qa/gates/` read

**OPEN (7)** — no `Answered:` line, or an empty/pending stub:

| Gate | Blocks | State |
|---|---|---|
| `t162-contract-approval.md` | **T-162 and therefore T-163** | unanswered, **5 days** — highest-leverage open decision in the repo |
| `at110-approval-forgery.md` | AT-110 (high) — consent forgery | no `Answered:` line at all |
| `at147-expiry-end-of-day.md` | AT-147 — start-of-day vs end-of-day expiry | `**Answered:**` present but **empty stub** |
| `at218-vacuous-guard-class.md` | AT-218 (high) — vacuous-guard policy | `_(not yet — gate remains open)_`, 8th sweep |
| `at253-agent-fallback-wiring.md` | AT-253 (high) — agent fallback / ARCHITECTURE claim | `_(pending)_` |
| `erp-credentials.md` | T-122 / T-145 — needs a test account via the UI | no `Answered:` line |
| `t135-url-pattern-data-migration.md` | **nothing** (stored-data cleanup only) | unanswered, harmless |
| `at365-data-class-declaration.md` | AT-365 (high) — **new, opened 2026-09-16 11:41** | unanswered; AT-376 above is its evidence |

That is **8 open gates**, not the 7 the dispatch brief listed — `at365-data-class-declaration.md`
was opened by the maker at 11:41 today and is not in the brief.

**ANSWERED (4), correctly closed on disk:** `at052-bfs-video-corpus-grill` (2026-09-07),
`at106-hook-architecture-path` (2026-09-08), `t136-model-credentials` (2026-09-09, "the gate was
wrong"; note the stale `_(pending)_` line four lines above the answer is AT-285, open low),
`at355-guard-shape` (2026-09-11, "C plus the narrow half of A"), `next-unit-scope` (2026-09-11).

**Gate-answered-off-disk hunt: none found.** Searched commit messages since 2026-09-08 and every
manifest/verdict for each open gate's slug; every hit describes the gate, none answers it.

## Handshake — 125 manifests reconciled against 136 verdicts

- **Dangling check: 1 — `at358-visual-order-detector`** (`ready-for-check`, `Fix cycle: 2`, verdict
  stamped `Cycle checked: 1`). **Not a finding:** a unit checker is running against it right now,
  dispatched in parallel with this sweep. Excluded by the dispatch and confirmed live (that
  checker filed AT-371…AT-374 into the ledger while this sweep was running).
- **STALLED with diagnosis on disk: 2, both correct.** `at345-346-fold-coverage` (3 FAILs,
  `qa/debug/at345-346-fold-coverage-cycle3.md` present; its gate is answered and explicitly rules
  "stays STALLED and is not reopened") and `at015-at028-hook-adapter-fix` (STALLED with a
  `Cycle checked: RECOVERY (post-STALL)` verdict carrying `VERDICT: PASS (stall recovery
  confirmed)`).
- **PASS not closed out: 0. FAIL with an unresponded manifest: 0. Bypassed unit: 0.**
- `qa/.last-tick` is **live** — last entry 2026-09-16T11:41:27+05:30. AT-368 (the 4.85-day dead
  loop) stays open as history, not as a current liveness finding.

## Baseline re-run by this sweep

- `uv run ruff check src tests scripts` → **exit 0**, "All checks passed!".
- `uv run autotester doctor` → **1 violation**: `function-too-long: src/autotester/stages/grade.py:98 — grade is 55 lines > 50`.
  **Not charged.** `git status` shows `M src/autotester/stages/grade.py` uncommitted, and the
  function is 44 lines at HEAD, `208f1b1`, `4714db0` and `d08da0f` — this is the concurrent loop's
  in-flight **AT-366** work, disclosed, appearing mid-sweep. It must go green before that unit is
  submitted.
- `uv run pytest -q` **deliberately not re-run**, and `scripts/mutation_check.py` **deliberately
  not run** — a unit checker is mid-run in this shared tree and AT-357/AT-331 make the mutation
  harness fail under concurrency. Last green: 1185 passed / 2 skipped, this morning's sweep.
  Disclosed as a gap, not reported as a pass.

## Filed-but-unfixed residue — judged one by one

| Issue | Verdict |
|---|---|
| **AT-335** (high, modal-crawl non-determinism) | **Still correctly deferred as a *fix*, but it has become the next *unit* in a different shape.** The maker could not reproduce it in 13 attempts, and C7 forbids shipping "this cannot happen any more" with no failing case — that reasoning holds. What is buildable *today* is the **reproduction harness**, not the fix: repeat the crawl N times and assert the screen set is stable. Queued at #3. |
| **AT-349** (low, curated confusables vs UTS #39) | **Correctly filed-and-deferred.** The `at355-guard-shape` answer (C + the narrow half of A) explicitly de-scopes Unicode exotica, and the docstring already declares the list partial. No change. |
| **AT-352** (medium, base64/hex/entities) | **Correctly deferred by an answered gate.** Recommendation, not an action: it is inflating the open count while being out of scope by decision — the maker should close it `wontfix` citing `at355-guard-shape` rather than leave it `open` indefinitely. Left `open` here because the close belongs with the evidence. |
| **AT-357** (medium, global `%TEMP%` glob in the mutation-harness tests) | **No longer merely filed — it is now costing verification.** This sweep's own dispatch had to *forbid* running `scripts/mutation_check.py` because of it. The mutation harness is this repo's primary anti-vacuous-guard instrument (C7), so a harness that goes red whenever two loops overlap disables the main defence exactly when two loops are the normal operating mode. **Promoted to #1.** AT-331 (low) is the same defect seen from the other side. |
| **AT-362 residue** (high, shadow DOM / iframes / generated content) | **Not dangling and not stale.** `208f1b1` part-fixed and part-disclosed it, and the `at358` cycle-2 verdict deciding whether that disclosure is acceptable is being written right now. Leave it to that checker. |

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), **8th consecutive sweep**.
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.

## HUMAN_GATE — do not build as ordinary units

- **T-162 contract approval** — A (interview now) / B (CTO-brief HLD first) / C (different next
  unit) / D (pause). Blocks T-162 and T-163. **Open 5 days.** Still the single highest-leverage
  action available in this repo.
- **AT-365 data_class declaration** — new today. AT-376 above is the measurement the gate was
  waiting for: the declaration is right, the 344-violation red is 98% gitignored scratch, and the
  7 tracked hits are all fixtures or the repo author's own address.
- **AT-110** consent-forgery posture · **AT-147** expiry semantics · **AT-253** agent fallback ·
  **ERP credentials** (test account via the UI) · **AT-130** deliberately gated to the first real
  Files-API unit.
- **AT-288..291 renumbering** — only Umesh can overturn AT-293. Not a build row.

## TOP-3 BUILDABLE NEXT UNITS (non-gated)

1. **AT-357 (medium, but blocking verification) — scope the mutation-harness cleanup assertions to
   the run's own sandbox.** `test_the_sandbox_is_removed_*` assert on a glob of the shared system
   temp dir, so any concurrent mutation run reds them, and `scripts/mutation_check.py` refuses to
   run against a red baseline. Two loops are now the steady state in this repo; this sweep is the
   second consecutive run that had to skip the harness. Small, self-contained, no gate, and it
   restores C7's enforcement instrument. **Build it first.** Closes AT-331 with it.
2. **AT-368 (high) — make a dead loop visible.** Carried from 11:55 and still the right #2: the
   continuation chain stopped for 4.85 days and nothing on disk said so until a human dispatched a
   sweep. Buildable half is a liveness signal whose own failure is detectable, plus a rule that a
   deliberate stop writes `qa/.paused`, so "asleep" and "paused" stop looking identical.
3. **AT-335 (high) — build the crawl-determinism harness, not the fix.** Repeat the modal crawl N
   times against a fixture and assert the screen set is stable; ~1 run in 14 currently loses the
   dismissed-dashboard screen. This converts an unfalsifiable "cannot reproduce" into a failing
   case a fix can be judged against, which is what C7 demands before anyone may claim it fixed.

**In flight, do not double-assign:** AT-366 (concurrent loop, `grade.py` dirty right now) and
AT-362/363/364 (at358 cycle 2, under check).

Runner-up, unchanged and still not cleared: **fixed-ledger reconciliation** — re-derive a batch of
the now-**63** `fixed` rows by sabotage, oldest untouched cohort first (AT-207/208/219-223/228).
Flagged by **eight** consecutive sweeps.

## Revised-goal coverage (unchanged from 11:55 — 35/55 done, 20 pending)

- Intake: covered (T-161). · Multi-source learning: partial, video only; T-162 gated.
- Learn-or-explore orchestration: T-135 done; T-163 blocked on T-162.
- Portal Persona: missing, T-164. · BFS/frontier/API completeness: partial (AT-335 is the next
  crawl-completeness defect; AT-362/363 in flight; forward/back/network still T-165).
- Traceable best/worst/edge compiler: partial, T-166. · Release-triggered regression: missing, T-167.
- Unified damage-control report: partial, T-168. · Two-mode real acceptance: missing, gated by AT-281 (T-169).

Terminal state: **FINDINGS: 2** — AT-375 (medium, governance: id allocation still not
collision-safe, third event, hit live by this sweep), AT-376 (medium, UPSTREAM: the data-boundary
gate scans gitignored paths, 2% signal). Plus one ledger repair (AT-355 → AT-370) and one
ruled-and-refused dispatch instruction (AT-288..291). **No reopens.** Ledger after this sweep:
**373 rows — 204 verified / 102 open (10 high, 33 medium, 59 low) / 63 fixed / 2 wontfix /
2 dismissed**; duplicate ids down from 5 to the 4 AT-293 ruled on.
