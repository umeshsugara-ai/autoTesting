# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-03 (full refresh, not incremental — prior queue was stale
since T-120's PASS/push at `d364036`). Re-verified from scratch this sweep: `.goal/goal.json`
now shows **20/20 tasks `done`** (confirmed via direct parse — every task's `status` field is
`"done"`, none pending/blocked). `git status --porcelain` is clean (nothing uncommitted); `git
log` top commit is `d364036` (T-120 PASS, pushed). Health checks all green: `uv run pytest -q` →
74 passed, 1 skipped; `uv run ruff check src tests scripts` → All checks passed; `uv run
autotester doctor` → clean.

**Issue ledger re-verified against current disk state, not trusted from old text.** Two items
the old queue still listed as TODO turned out to already be checker-PASSed and just stuck at
`fixed` in `qa/issues.jsonl` (ledger staleness, now corrected this sweep):
- **AT-011** (`qa/loop.md` absent) — file exists (5398 bytes), `qa/verdicts/at011-loop-md.md`
  says `VERDICT: PASS`. Flipped `fixed` → `verified`.
- **AT-015** (empty ARCHITECTURE.md injection) — re-extracted the live filter from
  `.claude/hooks/lab-session-start.ps1:111-131` and ran it against the real
  `docs/ARCHITECTURE.md`: 139 lines kept, all 10 headings through `## Status` present, no
  truncation. `docs/DECISIONS.md` D-008/D-010/D-011 all carry `Approved-by: Umesh`.
  `qa/verdicts/at015-at028-hook-adapter-fix.md` says `VERDICT: PASS (stall recovery confirmed)`.
  Flipped `fixed` → `verified`.
- **AT-014** (`.goal/rubrics/` absent) — `.goal/rubrics/T-050.md`, `T-110.md`, `T-120.md` all
  exist now with real criteria (not stubs), and the three goal tasks they gate are `done`.
  Flipped `open` → `verified`.

North star unchanged since `458304a`; `.regrill-due` absent; no reopen escalation — no `GRILL:`
row needed.

**Remaining open issues (5), none critical/high — re-checked this sweep, not restated:**

| # | Status | Unit | Issues | Why now |
|---|--------|------|--------|---------|
| 1 | TODO | Scope + build literal Script-artifact generation for the agent fallback loop (construct a `Script` under `projects/<slug>/scripts/`, set `Case.script_ref`) | AT-026 (medium) | Only medium-severity open issue. `schema/case.py`'s `Script`/`script_ref` surface (design-lock `a5ffcec`) was built for exactly this and still unused; `agent_loop.run_with_fallback` is now stable (T-080 long since PASSed, T-090/T-100/T-110/T-120 all shipped since), so the earlier blocker ("once the fix is stable") no longer applies. No HUMAN_GATE needed to scope it. |
| 2 | TODO | `ProjectStore.add_source`/`add_case` full-collection re-read before every append (`src/autotester/store/project_store.py:32-37`, `:50-55`) | AT-024 (low, perf) | Flagged to "revisit at T-070 scale" — T-070 (expand stage, taxonomy-driven case generation) has since shipped (`9bede99`), so collections can now legitimately grow past the small-project size this was deferred against. Worth a quick check whether real project sizes have hit the point where this matters; still non-blocking today. |
| 3 | TODO | `ObservedScreen` content-id hashes only `name`, not signals — two same-named screens with different content collide (`src/autotester/stages/ingest.py:37-42`, `core/ids.py:35-37`) | AT-034 (low, coverage gap) | Filed as a coverage gap, not a criterion violation — `qa/contracts/ingest.md` I1/I3 hold literally as worded. No urgency, but the only other open item besides AT-026/AT-024 with any product-facing surface. |

Also open (lower, cosmetic, unchanged this sweep): **AT-012** `.last-tick` timezone mix on 3
historical pre-`+0530` lines (current writes already correct, confirmed by direct read of
`qa/.last-tick`) · **AT-023** `t020-filestore` manifest test-count off-by-one (94 claimed vs. 93
actual per `pytest --collect-only`; all tests pass, purely a stale manifest number).

**Bottom line: the goal backlog is genuinely closed (20/20), the working tree is clean and
pushed, and nothing open is blocking.** The 3 rows above are optional housekeeping/hardening a
future `/maker` tick could pick up at its own judgement — none are gated on Umesh and none
require a DECISIONS entry to *start* (AT-026, AT-024, AT-034 are all ordinary code, not
enforcement-path files). If nothing further is dispatched, the project is idle by design, not by
neglect.
