# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-03T08:40+05:30 (first sweep; terminal state FINDINGS: 10).
Gate lines (if any) sit above the table; the maker reads them before TODO rows. None this sweep —
north star unchanged since 458304a, `.regrill-due` absent, no reopen escalation.

| # | Status | Unit | Issues | Why now |
|---|--------|------|--------|---------|
| 1 | TODO | Record the out-of-pair `doctor.py` allowlist edit (commit 5f83bdb) in the T-005 manifest or a `session` DECISIONS entry | AT-009 | Only bypass found; close it before the pattern repeats |
| 2 | TODO | Append D-005 (FlowSpec/Case: 13 proposed amendments from T-004) via `scripts/append_decision.ps1`, ACTIVE or REJECTED per group | AT-010 | Must land before T-060 locks FlowSpec |
| 3 | TODO | Author `qa/loop.md` (re-run `/maker init` step 3b) and fix the tick-stamp timezone | AT-011, AT-012 | Liveness surfaces read these files |

Also open (lower): AT-013 living-ledger L7 numbering (checker applies at the T-005 check) · AT-014 rubrics for
T-050/T-110/T-120 · AT-015 lab-session-start injects an empty ARCHITECTURE block (flag to T-005) · AT-016 stale
STALLED notification · AT-017 proposed goal task T-065 FlowSpec review gate · AT-018 DB assertions onto T-040.

In flight at sweep time (not a finding): T-005 files under `src/autotester/ledger/`, `prompts/`,
`schema/ledger.py` being written (08:33–08:34), no manifest yet; `uv run ruff check` currently red on
`ledger/relitigation.py` (E501 x2) and `ledger/store.py` (E501, SIM102) — the maker's own gate will catch it.
