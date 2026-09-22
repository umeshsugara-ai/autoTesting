# Manifest — at119-vocab

**Contract:** qa/contracts/goal-loop-design.md (AT-119 is filed under `feature: goal-loop-design`)
**Goal task:** none — checker-filed hardening follow-up
**Date:** 2026-09-22
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-119, AT-538 (cycle-1 FAIL)
**Executor:** ollama/deepseek-v4.1-flash
**Executor rationale:** first delegated unit; single test file, mechanical and fully specified by
the issue text, so the cheapest capable model was chosen over a Claude subagent.
**Delegation:** $0.00 (flat-rate Ollama subscription) · 136 s + 30 s (cycle 2)
**Status:** checked-PASS (cycle 2, verdict 2026-09-22)

## What changed
- `tests/test_goal_criticality_vocabulary.py`:18-26 — added `importlib.util` and `pytest` imports
  and a `CLASSIFIER_SOURCE` path constant.
- `tests/test_goal_criticality_vocabulary.py`:64-90 — added
  `test_the_deliberate_copy_has_not_drifted_from_its_source`, which loads the shared classifier by
  path, skips when it is absent or unloadable, and otherwise asserts
  `CLASSIFIER_VOCABULARY == set(criticality._ORDER)`.

Nothing else was touched. The deliberate duplication and its explanatory comment are unchanged —
AT-119 asked for a drift guard alongside the copy, not for the copy's removal.

## How to verify (commands + expected)
- `uv run pytest tests/test_goal_criticality_vocabulary.py -q` → expected: exit 0, 3 tests, and the
  new test **runs rather than skips** on a machine where `D:/ai_os` is present (a skip here would
  mean the guard is inert — check for `s` in the pytest output).
- `uv run ruff check src tests scripts` → expected: exit 0. **Cycle 1 FAILED here** (SIM300
  Yoda condition, AT-538); cycle 2 swapped the operands to `source_vocabulary ==
  CLASSIFIER_VOCABULARY`. I have re-run it since the fix: `All checks passed!`
- `uv run autotester doctor` → expected: exit 0 (the file is 90 lines, well under the 300 cap)
- Sabotage proof the checker should run itself: change `CLASSIFIER_VOCABULARY` to
  `{"low", "medium", "high"}` and re-run — the new test must FAIL, naming both sets. Restore after.

## Known weakness the checker should judge
`CLASSIFIER_SOURCE` is a hardcoded absolute Windows path (`D:/ai_os/...`). It came from the brief
and mirrors the path already named in the file's existing comment, but on any other machine the
guard silently degrades to a skip. Whether that is acceptable, or whether the path should be
env-overridable, is a contract question for the checker — not something the builder decided.

## Delegation record
Built by an external worker under `scripts/delegate_unit.py` (opencode runner, bash denied, writes
path-confined to the worktree, boundary check clean, 0 permission rejections). The commit on
`wave/at119-vocab` is `424568d`; base for diff scope is `ab404dd`. Full worker output:
`qa/delegation/at119-vocab-ollama-deepseek-v4.1-flash.log`.

## Cycle 2
`tests/test_goal_criticality_vocabulary.py`:86 — operand order swapped to satisfy ruff SIM300.
One line changed, nothing else; commit `162947f`. Re-run by me after the fix: ruff `All checks
passed!`, `pytest -q -rs` 3 passed with no skips.

**Correction owed on cycle 1:** this manifest originally listed `ruff ... → expected: exit 0`
without that command having been run. That was an unverified claim in an evidence manifest, which
is precisely what the checker exists to catch — and it did. Every expectation above has now been
executed rather than assumed.
