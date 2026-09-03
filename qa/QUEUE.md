# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-03T10:55+05:30 (terminal state FINDINGS: 6 open, 18 verified,
1 fixed-by-this-sweep). North star unchanged since 458304a, `.regrill-due` absent, no reopen
escalation. `qa/.last-sweep` staleness confirmed: prior queue rows AT-009/AT-010 were resolved
(both closed `verified` at T-005 cycle-1) and are dropped below — this refresh replaces them with
genuinely current work.

| # | Status | Unit | Issues | Why now |
|---|--------|------|--------|---------|
| 1 | TODO | T-040 `stages/execute.py`: script-first runner producing RawResult | — | Next scheduled unit per `.goal/goal.json` (`current: T-040`); T-030 deps satisfied, unblocked |
| 2 | TODO | Author `.goal/rubrics/T-050.md`, `T-110.md`, `T-120.md` before those units are attempted | AT-014 | Their `done_check.type=rubric_ref` cannot resolve without the rubric files — author at each contract's START, not at close time |
| 3 | TODO | Author `qa/loop.md` (re-run `/maker init` step 3b) | AT-011 | Loop-Doctor-lite has had nothing to check since the first sweep; low effort, closes a standing liveness gap |

Also open (lower): AT-012 `.last-tick` timezone mix (historical lines only; current writes already
use `+0530`, cosmetic) · AT-015 `lab-session-start.ps1` injects an empty ARCHITECTURE block (still
unaddressed, flagged to whichever unit next touches the hook) · AT-023 t020 manifest test-count
off-by-one (low, cosmetic) · AT-024 `ProjectStore` O(n) re-read on every add (low, perf, revisit at
T-070 scale).

Sweep note: AT-021 (doctor crash on malformed ledger) independently re-probed this sweep with three
fresh cases (duplicate id, broken JSON, short-title validation error) against current `doctor.py` —
all three now report a clean single-line `ledger-invalid: ...` with no traceback, exit 1. Confirmed
fixed and flipped to `verified`. Also flipped 17 other `fixed`-but-unconfirmed rows to `verified`
where the ledger's own evidence already showed a checker re-check "reproduced closed" (ledger
hygiene — claims were not outrunning checks, the status field was just stale).
