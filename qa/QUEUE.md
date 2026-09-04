# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-04T16:45+05:30. Since the prior sweep (2026-09-04T13:13:31,
`278060a`, FINDINGS: 1 — AT-043) **three more units shipped**: `ui-run-view-flow-and-lightbox`
(F-028), `ui-flow-diagram` (F-029), and `at044-entry-case-profile-isolation` (F-030 — a real
regression Umesh hit live on Pathlynks, found and fixed the same session). This sweep independently
re-verified all three close-outs and ran the full six-check protocol fresh.

## What this sweep re-verified itself

- **Bypass detection** — walked every commit since `278060a`: `0f37759` (feat) → `51a7428`
  (checker PASS, cycle 1) → `287627d` (close-out, F-028); `480d492` (feat) → `8bad017` (checker
  PASS, cycle 1) → `d68a67c` (close-out, F-029); `939af44` (fix) → `5331261` (checker PASS,
  cycle 1) → `e08c08a` (close-out, F-030, files AT-047, ledgers). Each traces to one manifest at
  `Status: checked-PASS` and one verdict with a matching `Cycle checked: 1`, `VERDICT: PASS`. No
  bypassed unit found.
- **`qa/issues.jsonl`** — 48 rows (was 43 at last sweep; +4 from at044's cycle: AT-044, AT-045,
  AT-046, AT-047; +1 this sweep: AT-048). Exactly one `open` row: **AT-046** (medium — residual
  evidence-capture flakiness for pathlynks live reruns, explicitly scoped by the maker as a
  harder follow-up needing product-specific investigation, not chased further by this unit or
  this sweep). Confirmed genuinely the only open row — no other row anywhere in the ledger has
  `status: "open"`. Everything else is `verified` or `fixed` (fixed = this checker's own
  independent evidence at the unit that closed it; not yet re-verified by a *later* check, which
  is the correct resting state, not a gap).
- **`.goal/goal.json`** — still 20/20 tasks `status: "done"`; north-star text unchanged since
  last check. The at044/F-030 unit itself had `Goal task: none` (correctly — it was a live
  regression fix Umesh triggered by asking for a rerun, not a plan-driven backlog task). No
  goal-drift, no re-grill trigger.
- **`qa/manifests/*.md`** — `grep -l "Status: ready-for-check"` across all 37 manifests → zero
  hits. Nothing dangling; every manifest is `checked-PASS` (or the recovered `STALLED` unit,
  `at015-at028-hook-adapter-fix`, whose own recovery note already ends "Status: checked-PASS").
- **Verdict files git-tracked** — clean; all three new verdicts and their manifests/ledger rows
  are committed (`51a7428`/`287627d`, `8bad017`/`d68a67c`, `5331261`/`e08c08a`).

## Findings this sweep

- **AT-048 (low, fixed on the spot)** — contract staleness: `at044-entry-case-profile-isolation`
  (ledger F-030, checker-PASSed) shipped with **zero contract-side trace** in either
  `qa/contracts/ui-run.md` (the entry-case profile-isolation fix to `trigger_run`, RU1's
  mechanism) or `qa/contracts/execute.md` (the new `BrowserSession.settle()` call after CLICK
  steps, E2/E5) — same class of gap AT-043 found and fixed last sweep for three other contracts.
  Fixed: added 2026-09-04 amendment-log rows to both contracts, pointing at the real verdict and
  ledger row, explicitly noting neither criterion's *meaning* changed (routine — no
  reinterpretation, no weakening) and that AT-046 stays open/untouched by this record.
- **Feedback-inbox** — re-checked all `unfolded` status lines; still exactly the same two
  deliberately-unfolded entries as last sweep (the out-of-root `append_decision.ps1` template
  defect note; the flow-diagram/mindmap enhancement idea — which is now itself half-superseded:
  F-028 (DFS trace) and F-029 (BFS branch tree) both shipped and closed the underlying ask, but
  the inbox entry's own resolution notes already point at both). No new fold-in gap.
- **Contract staleness** — none found beyond AT-048 above.
- **Enforcement liveness** — `.claude/settings.json` present with real hook references; repo has
  **148 commits** (was 137). Live, not a dead-looking-alive gate.
- **Loop spec** — `qa/loop.md` Stop list matches the maker's seven terminal states; Human gate
  section not contradicted by `qa/adapter.json` (no `improve` block). Live and consistent.
- **Re-grill check** — no north-star edit, no uncoverable requirement, no escalated reopen
  disagreement, `qa/.regrill-due` absent. **No `GRILL:` row.**
- **Goal-coverage** — north star unchanged; all 20 goal tasks done; all three units shipped since
  the last sweep trace end-to-end (fix/feat commit → manifest → checker-dispatched verdict →
  ledger row → now, contract amendment). AT-046 is the one honest open gap against the north
  star's implicit promise of reliable evidence capture — correctly tracked as an open issue, not
  hidden or prematurely closed.

## Health checks (re-run by this sweep)

- `uv run pytest -q` → 275 passed, 2 skipped (pre-existing), 0 failed.
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"

## Backlog state — for Umesh's status report

- **AT-046 is the only open issue in the entire ledger** (48 rows checked; every other row is
  `fixed` or `verified`). Medium severity, `execute` feature, correctly scoped by the maker as a
  harder problem needing product-specific investigation (evidence-capture timing precision on
  Pathlynks specifically), not a quick fix — this sweep did not find grounds to reclassify it.
- **All six recent units (F-025 through F-030) close out cleanly**: each has a matching manifest
  at `checked-PASS`, a verdict with `Cycle checked: 1` / `VERDICT: PASS`, a `docs/FEATURES.jsonl`
  row with a real `verdict_ref`, and (as of this sweep, for the one gap found) contract-side
  amendment-log traceability.
- No bypassed units, no stale manifests, no unclosed PASS verdicts, no unfolded feedback that
  should have been folded, no dead enforcement, no goal-drift.

## Top-3 recommended next units

Backlog is legitimately empty of open issues beyond AT-046 and open goal tasks. If picking up
discretionary work, in priority order:

1. **AT-046 — evidence-capture timing flakiness on Pathlynks live reruns** (medium, `execute`).
   The only open issue. Needs product-specific investigation into a more deterministic
   post-submit signal than `networkidle` + fixed grace (client-side re-renders with no reliable
   network signal) — genuinely harder than AT-044/AT-045, correctly not rushed.
2. **Flow-diagram/mindmap report enhancement** — already fully delivered (F-028 DFS + F-029 BFS
   both shipped and PASSed); nothing further queued here unless Umesh asks for more.
3. (Not actionable here) Template-level `append_decision.ps1` encoding defect — lives outside
   this repo's root (`D:/ai_os/templates/lab-protocol/`); flagged for Umesh/AIOS session per the
   2026-09-03 inbox entry, not a task for this project's queue.

Nothing critical or high-severity is open. The system is in steady state; AT-046 is the one
genuine, honestly-scoped piece of unfinished work.
