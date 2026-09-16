# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-16T11:55:00+05:30**; bound strictly to `D:/autoTesting`.
Sweep window: `7ab22c9..d08da0f` (28 commits, 7 source-bearing). Supersedes the
2026-09-11T13:45 queue: **AT-227 and T-135 stay closed; AT-345/346 STALLED after three FAILs and
is diagnosed, not queued.**

## Reconciliation

- **Sweep was 4.9 days overdue, and so was the maker.** `qa/.last-tick` jumps
  `2026-09-11T09:22:41Z` straight to `2026-09-16T05:45Z` with no `qa/.paused` on disk and a
  non-empty backlog throughout. That is a dead loop, not a pause — filed **AT-368 (high)**. The
  overdue sweep is the same outage seen from the other side.
- **Bypass detection, 7 source-bearing commits, CLEAN.** `7ef68b1` (at126-127), `acfe782`
  (at137), `c1c8f63` (at355), `b91147a` (at161), `41fa5e6`+`8fc215c` (at358), `d08da0f` (at169) —
  every one maps to a manifest. No unmanifested source commit in the window.
- **Handshake: 122 manifests / 134 verdict files.** Exactly one manifest is not `checked-PASS`:
  `at358-visual-order-detector.md` at `ready-for-check`, FAIL cycle 1, **disclosed in-flight work
  belonging to a concurrent session** (uncommitted edits to `browser/visual_order.js`,
  `tests/test_browser_visual_order.py` and the bidi fixtures were present in the tree and were
  read, never touched) — not a dispatch gap and not a bypass. `at015-at028` and `at345-346` are
  STALLED with their `qa/debug/` diagnoses on disk, as required. No FAIL verdict with an
  unresponded manifest; no PASS verdict with a skipped close-out.
- **Cycle-stamp hygiene:** `at076-navigation-secret-escape-hatch.md` carries 3 verdicts and 1
  `Cycle checked:` stamp, `t100-ui.md` carries 2 and 1. The close-outs themselves are correct, so
  this is hygiene rather than a broken gate — filed **AT-369 (low)**.
- **Baseline, re-derived by this checker (not pasted):** `uv run pytest -q` → **exit 0**, 1185
  passed / 2 skipped / 0 failed; `uv run ruff check src tests scripts` → exit 0, "All checks
  passed!"; `uv run autotester doctor` → clean, exit 0. Green **including** the concurrent
  session's uncommitted at358 work. AT-357 (the known `test_mutation_check.py` flake) did not
  fire on this run.
- **Fixed-ledger backlog now 60 rows (was 55), against 204 verified.** Seventh consecutive sweep
  carrying it; not re-derived this sweep either. Disclosed as a persistence flag.
- **Inbox clean:** every entry carries a fold/resolution marker. Two 2026-09-04 entries (report
  regression; AT-046→AT-049) narrate their own resolution instead of using the `FOLDED:` form —
  cosmetic, not filed.
- **Contract staleness:** none new. `ui-flow-diagram.md` and `ui-sidebar.md` still lack an
  amendment log (AT-099, open low, carried).
- **Enforcement liveness, confirmed by execution:** `.claude/settings.json` carries the
  `SessionStart` / `PreToolUse` / `SessionEnd` hooks and all five hook scripts exist
  (`.claude/hooks/decisions-append-guard.ps1`, `lab-session-start.ps1`, `lab-session-end.ps1`,
  `qa/hooks/mc-sessionstart.ps1`, `mc-precommit.ps1`); repo at **690 commits**;
  `docs/DECISIONS.md` has **26** entries. **Lab Protocol branch: no finding** — the mc wiring is
  installed, so neither the `approval-required` nor the "install wiring per D-NNN" branch applies.
- **Loop spec (Loop-Doctor-lite):** `qa/loop.md` present; its `Stop` line lists all seven terminal
  states; its `Human gate` line is not contradicted by `qa/adapter.json` (no `improve` block, so
  no target/budget/plateau stop is owed). Of the three loop-design questions, **"can it spin"** is
  answered no in design but **yes in fact this window** — nine units closed and the goal moved
  **0 tasks (35/55 before and after)**; **"can it Goodhart the verifier"** remains the live risk
  (slot-1 is tests the maker writes; the C7 mutation duty is the mitigation and it is
  checker-enforced, which is the right side of the seam) — both already carried by AT-218, not
  re-filed; **"can it run a wrong answer to completion"** is answered no — T-145's `done_check`
  is now `scripts/check_crawl_approval.py`, which demands a finished crawl AND an intact
  unexpired approval, the strongest one in the file.
- **Data boundary (MC-003, first sweep to run it here): VIOLATION.** `qa/adapter.json` declares no
  `data_class`, so the gate cannot fire at all — the synthetic-only posture lives in a `_note` a
  human has to read. Filed **AT-365 (high)**.
- **Silent-failure hunt over the window's PASSed `src/` diff** (`gemini.py`, `paths.py`,
  `redact.py`, `ui/helpers.py`, `transcribe.py`): two hits, both the default-value-fallback class.
  **AT-366 (high)** — all three providers drop a missing screenshot path in silence, so the judge
  can grade on a subset with nothing recording how many images it saw. **AT-367 (medium)** —
  `_config`'s `elif` silently discards a caller-set `temperature` on the DEFAULT 3.x model, the
  same declared-option-never-applied class the unit fixed two lines above. `paths.py`, `redact.py`
  and `helpers.py` are clean — the new guard raises rather than folds, which is the point of
  AT-355.
- **Goal coverage: 35/55 done, 20 pending — unchanged since 2026-09-11.** Matches disk; the north
  star is byte-identical to the committed copy, so no goal-drift trigger fires on that arm.
- **No reopens.** AT-366/AT-367 are new defects in code a PASSed unit touched, not evidence that
  any unit's own criteria were unbacked.
- **Gates reconciled:** `next-unit-scope.md` answered (2026-09-11).
  `at355-guard-shape.md` answered (2026-09-11, C plus the narrow half of A).
  `t162-contract-approval.md` genuinely unanswered — **now 5 days open**, and unlike last sweep it
  is no longer being worked around, because the loop was dead. `at110-approval-forgery.md`,
  `erp-credentials.md`, `t135-url-pattern-data-migration.md` still have no `Answered:` line, and
  this sweep found no off-disk answer across the window's 28 commit messages.
  `at147-expiry-end-of-day.md` still an empty stub; `at218` and `t136-model-credentials.md`
  unchanged.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), 7th consecutive sweep.
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.

## HUMAN_GATE — do not build as ordinary units

- **T-162 contract approval** (`qa/gates/t162-contract-approval.md`): Option A (interview now) /
  B (CTO-brief HLD first) / C (different next unit) / D (pause). Blocks T-162 and therefore T-163.
  **Open 5 days; the single highest-leverage action available in this repo.**
- **AT-110:** consent-forgery posture. Still no `Answered:` line.
- **AT-147:** start-of-day vs end-of-day expiry. `Answered:` line is an empty stub.
- **AT-253:** wire model fallback, correct the ARCHITECTURE claim, or defer.
- **ERP credentials:** T-122/T-145 gated on a test account entered through the UI.
- **AT-130** is deliberately gated to the A3 unit that first calls the Files API for real — not a
  gap, not re-filed.

## TOP-3 BUILDABLE NEXT UNITS (non-gated)

1. **AT-365 (high) — declare `data_class` in `qa/adapter.json`.** One line, no gate, and it
   converts a boundary that currently only a human can see into one the sweep checks every run.
   Smallest unit on this list by an order of magnitude and it un-breaks a gate that will otherwise
   fail on every future sweep. Build it first.
2. **AT-366 (high) — a missing screenshot must not vanish silently.** `gemini.py:106-107`,
   `anthropic.py:72`, `langchain_fallback.py:86-88` each drop a non-existent image path with no
   error and no count; `langchain_fallback` falls all the way back to the text-only prompt that
   AT-049 was filed against. Surface an images-seen/images-requested count on the `Verdict` (or
   raise), so a judgement rendered on partial evidence is distinguishable from a full one. Real
   product-integrity work on the flagship grading path, no gate.
3. **AT-368 (high) — make a dead loop visible.** The continuation chain stopped for 4.85 days and
   nothing on disk said so until a human dispatched this sweep. The buildable half is a liveness
   signal whose own failure is detectable (and/or a rule that a deliberate stop must write
   `qa/.paused`), so "asleep" and "paused" stop looking identical. Governance work, no gate.

Runner-up, unchanged and still not cleared: **fixed-ledger reconciliation** — re-derive a batch of
the 60 `fixed` rows by sabotage, oldest untouched cohort first (AT-207/208/219-223/228). Flagged
by seven consecutive sweeps.

## Revised-goal coverage

- Intake: covered (T-161).
- Multi-source learning: partial — video only; T-162 gated on contract approval.
- Learn-or-explore orchestration: T-135 done; T-163 blocked on T-162.
- Portal Persona: missing, T-164 — no contract in `qa/contracts/` yet (needs `init-contract` at
  build time, not a separate gate).
- BFS/frontier/API completeness: partial; AT-335 (modal non-determinism) is the next
  crawl-completeness defect; AT-362/AT-363 (visual_text false negatives/positives) are in flight
  under at358; forward/back/network completeness still T-165.
- Traceable best/worst/edge compiler: partial, T-166.
- Release-triggered regression: missing, T-167.
- Unified damage-control report: partial, T-168.
- Two-mode real acceptance: missing, threshold-gated by AT-281, T-169.

Terminal state: **FINDINGS: 5** — AT-365 (high, data-boundary: no `data_class` declared),
AT-366 (high, silent-failure: providers drop missing screenshots, judge grades on a subset),
AT-368 (high, liveness: maker loop dead 4.85 days with no `qa/.paused`), AT-367 (medium,
silent-failure: `temperature` silently discarded on 3.x models), AT-369 (low, handshake hygiene:
appended verdicts with no cycle stamp). No reopens. Carried unchanged: AT-218, AT-281, AT-285,
AT-243, AT-099, the t162 gate, and the fixed-ledger backlog (now 60 rows, 7th sweep). Ledger after
this sweep: 204 verified / **99 open** (10 high, 30 medium, 59 low) / 60 fixed / 2 wontfix /
2 dismissed.
