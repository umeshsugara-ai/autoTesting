# Manifest — at097-session-start-hook-regression
**Contract:** `qa/contracts/core-invariants.md` (C7 independent verification) + the Lab Protocol in
`CLAUDE.md` (enforcement paths change only under an authorizing DECISIONS entry). No feature
contract governs the hook itself; **that is part of the finding.**
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** **AT-097** (high), **AT-029** (medium) — the same defect's two halves
**Authorized by:** **D-019** (appended before any file was touched)

## The finding, verified independently before fixing
`.claude/hooks/lab-session-start.ps1` injects this project's ground truth into every session.
I executed its on-disk filter against the real `docs/ARCHITECTURE.md` (150 lines, 11 named
headings):

```
CURRENT FILTER kept lines: 1
  |# AutoTester - architecture
```

**One line. The title.** Every session started since 2026-09-05 has been injected an empty
ground-truth block. `D-008` and `D-010` are both ACTIVE, both `Approved-by: Umesh`, and both
authorize the opposite; `D-010`'s Result names the exact line and value. The disk disagreed with
both because commit `051303e` (D-013) — a *"byte-identical to the AIOS template"* sync whose own
text says *"Behaviour otherwise unchanged"* — reverted them as a side effect, with no `Supersedes:`
line. History: `5f83bdb` cap=100/numbered → `f9e3456` cap=150/named (the authorized fix) →
`051303e` cap=100/numbered (the silent revert).

This is the hook whose job is to make the protocol survive forgetting, and it had been quietly
forgetting for three days.

## What changed
- `.claude/hooks/lab-session-start.ps1` — filter restored to D-008's rule (keep every `## ` section
  except the generated `## Directory map and schema summary`), cap restored to D-010's 150, label
  text corrected, and a comment recording that this file is **deliberately not** byte-identical to
  the AIOS template so a future sync re-applies both deltas.
- **New** `tests/test_session_start_hook.py` (6 tests) — reads the **real** `.ps1`, not a copy.
- `docs/DECISIONS.md` — **D-019** (written first, per the Lab Protocol).

After the fix, the same probe keeps **140 lines and all 10 named headings** — Design rules,
Commands and Status now reach the session, which is AT-029's half.

## Why there was no test, and why that is the actual bug
Nothing tested this hook, so the same defect shipped twice and was caught both times only by a
sweep that happened to look. The tests are therefore **driven by the file itself**: the excluded
heading pattern and the cap are parsed out of the live `.ps1` and used to run the filter. If the
filter is reverted, the parse fails and every behavioural test fails with it, rather than quietly
simulating a filter the hook no longer contains.

## Sabotage — I re-applied `051303e`'s exact revert
```
=== SABOTAGE APPLIED (051303e's exact revert) ===
FAILED tests/test_session_start_hook.py::test_the_numbered_heading_filter_is_not_back
FAILED tests/test_session_start_hook.py::test_the_excerpt_cap_is_the_authorized_one
FAILED tests/test_session_start_hook.py::test_every_named_section_survives_the_filter
FAILED tests/test_session_start_hook.py::test_the_generated_directory_map_is_the_only_thing_dropped
FAILED tests/test_session_start_hook.py::test_the_excerpt_is_not_effectively_empty
=== RESTORED === 6 passed
```
**First attempt was weaker and I am recording it rather than only the good result:** my initial
tests mirrored the filter with a hardcoded constant, so the same sabotage failed only the 2
string-checking tests while the 3 behavioural ones passed against a fiction. Driving them from the
parsed file is what took it from 2/6 to 5/6 (the 6th is "the hook exists", correctly unaffected).

## The approval question — read this, it is the one judgement call
This is an **enforcement path**, which the Lab Protocol says needs `Approved-by:` from Umesh, and
**Umesh has not been asked this session.** D-019 records the reasoning explicitly: D-008 and D-010
are standing, ACTIVE, Umesh-approved authorizations for exactly these two values, so this restores
their effect and creates **no new authority**. I did not express it as `Supersedes: D-013`, because
D-013's real purpose (ASCII-escaping hook JSON, which fixed a genuine harness rejection) is
correct and load-bearing; marking it SUPERSEDED would tell every future reader to discard it.
**The checker should judge whether that reasoning holds.** If it does not, the correct outcome is
FAIL and a HUMAN_GATE, not a softened criterion — and it is one commit to reverse.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → **555 passed, 1 skipped** (549 before)
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- Re-run the sabotage above yourself; 5 of 6 must fail.
- Independently execute the repaired filter against `docs/ARCHITECTURE.md` and confirm ≥100 lines
  and all 10 named headings — **do not** take my probe's word for it.
- Confirm `D-013`'s ASCII-escaping is untouched (`git diff 051303e -- .claude/hooks/`).

## Status: ready-for-check
