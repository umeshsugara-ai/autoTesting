# Manifest — at161-goal-neutering-any-segment

**Unit:** AT-161 — `is_capable_of_failing` misses an ALWAYS_TRUE segment reached via `;`/`&&`
**Contract:** C9 (a declared control value is honoured or rejected, never silently ignored)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-161 (medium)

## What was wrong

`tests/test_goal_done_checks.py::is_capable_of_failing` normalises `&&` to `;`, splits into
segments, and returns `any(_is_task_specific(seg) for seg in segments)`. A trailing no-op segment
(`true`, `:`, `exit 0`) after a real one was invisible to this check: `any()` only asked "is at
least one segment task-specific", never noticing that ANOTHER segment always exits 0 and — for a
`;`-joined command — is the ONE that actually determines the overall exit code. Five concrete
`done_check.cmd` shapes were measured accepted (capable of failing) when they are not:
`"...; true"`, `"...&& true"`, `"...; :"`, `"...; exit 0"`, `"...&& exit 0"`.

The issue's own evidence explicitly rejected one candidate fix ("switch `any()` to `the last
segment must be task-specific`") because that would reject the legitimate on-disk shape
`"check_deliverable.py --exists X && uv run autotester doctor"` (T-126, T-150) — both segments
are real, neither is a no-op. The correct fix direction it names instead: **reject the whole
command when ANY segment is in `ALWAYS_TRUE`**, regardless of separator.

## What changed

- `tests/test_goal_done_checks.py::is_capable_of_failing` — added
  `if not segments or any(seg in ALWAYS_TRUE for seg in segments): return False` before the
  existing `any(_is_task_specific(...))` check. A no-op segment anywhere now disqualifies the
  whole command; a command with only real segments is unaffected.
- `tests/test_goal_done_check_shapes.py` (**new file**, split from `test_goal_done_checks.py`
  once this fix pushed it over the 300-line cap) — the two shape-recognition tests
  (`test_the_guard_recognises_the_shapes_it_exists_to_catch`,
  `test_the_three_known_offenders_are_actually_fixed`) moved here unchanged, importing
  `is_capable_of_failing`/`tasks` from the original module (the established
  `from test_X import Y` pattern this repo already uses — see `test_ui_requests.py`). The
  five AT-161 cases added to the existing `rejected` list in the moved test — the legitimate
  T-126/T-150 `&&`-of-two-real-segments shape is **already** in the `accepted` list, so no new
  test was needed to prove the rejected fix direction wasn't taken.
- `tests/test_goal_done_checks.py` itself is otherwise unchanged in content — only the two tests
  moved out, plus the one-line `is_capable_of_failing` fix.

## How to verify (commands + expected)

- `uv run pytest tests/test_goal_done_checks.py tests/test_goal_done_check_shapes.py -q`
  → expected: exit 0, 9 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_goal_done_checks.py tests/test_goal_done_check_shapes.py -q
.........                                                                [100%]  (9 passed)

$ uv run pytest -q
[all dots, exit 0] — one run hit tests/test_mutation_check.py::test_the_sandbox_is_removed_*
(2 failures), a PRE-EXISTING known race: another concurrent session was actively running
mutation_check.py at the time, and both sandbox-cleanup tests glob() the shared temp dir. Confirmed
unrelated by re-running `uv run pytest -q --ignore=tests/test_mutation_check.py` → exit 0, and the
two flaky tests touch neither file this unit changed.
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. Extracted clean `HEAD`, layered my diff on (the new untracked test file copied in manually).
2. `uv sync`; confirmed `autotester.__file__` resolves inside the extract.
3. Baseline: `uv run pytest tests/test_goal_done_checks.py tests/test_goal_done_check_shapes.py -q`
   → 9 passed, exit 0.
4. Reverted `is_capable_of_failing` to the original `bool(segments) and any(...)` (the exact
   pre-fix line) — **exactly the predicted single failure**
   (`test_the_guard_recognises_the_shapes_it_exists_to_catch`, `assert not True` on
   `'uv run pytest tests/test_x.py; true'` — reproducing the original AT-161 defect verbatim),
   the other 8 tests stayed green.
5. Extract deleted; live tree confirmed to carry only the two real edits.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `tests/test_goal_done_checks.py`,
`tests/test_goal_done_check_shapes.py` (new). Pure static-analysis test-helper logic, no
route/template touched.

## What this unit does not claim

- Does not claim `is_capable_of_failing` is a complete shell-semantics parser — it remains the
  same conservative allowlist heuristic it always was, now closed for this one measured gap.
- Does not touch any live `.goal/goal.json` `done_check.cmd` value — the issue's own evidence
  confirms no on-disk command currently has this shape (`;` appears in none, and all six `&&`
  commands pair two real segments), so this is a guard-correctness fix with no current-state
  behavior change.

## Status: ready-for-check
