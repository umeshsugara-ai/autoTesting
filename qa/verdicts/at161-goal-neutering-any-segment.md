# Verdict — at161-goal-neutering-any-segment

**Cycle checked:** 1
**Date:** 2026-09-11
**Contract:** C9 (a declared control value is honoured or rejected, never silently ignored) —
`qa/contracts/core-invariants.md` §C9, judged directly (dedicated contract file, not an
issue-only criterion as the dispatch anticipated). C9's own Verify clause names
`tests/test_goal_criticality_vocabulary.py tests/test_goal_done_checks.py`.

## What I re-ran myself (live tree, commit b91147a)

- `uv run pytest tests/test_goal_done_checks.py tests/test_goal_done_check_shapes.py -q`
  → `.........` 9 passed, exit 0. Matches manifest claim.
- `uv run pytest -q --ignore=tests/test_mutation_check.py` → all green, exit 0 (ran the full
  suite twice; both green). Did not chase the excluded file — the manifest's own account of a
  concurrent-session temp-dir race there is independently corroborated by ledger row AT-357,
  filed the same day against the same two sandbox-cleanup tests, and neither file it names
  touches this unit's changed paths.
- `uv run ruff check src tests scripts` → `All checks passed!`, exit 0.
- `uv run autotester doctor` → `doctor: clean`, exit 0.

## Sabotage, re-run independently (not trusted from the manifest)

Fresh `git archive HEAD` extract to an isolated scratch dir, own `uv sync` venv. Confirmed
`autotester.__file__` resolved inside the extract (not the live tree). `tests/test_goal_done_check_shapes.py`
was present via the plain archive, as the dispatch predicted (tracked as of this commit).

1. Baseline on the extract: 9 passed, exit 0 — matches the live-tree run.
2. Reverted `is_capable_of_failing` to the pre-fix line
   (`return bool(segments) and any(_is_task_specific(seg) for seg in segments)`).
3. Re-ran: **exactly one failure** —
   `test_the_guard_recognises_the_shapes_it_exists_to_catch`, `assert not True` on
   `'uv run pytest tests/test_x.py; true'`. This is the AT-161 defect reproduced verbatim, and
   no other test in the two files moved from pass to fail.

Sabotage confirmed independently.

## Rejected-alternative claim, checked against the actual predicate (not taken on the manifest's word)

The manifest claims the obvious alternative fix ("the last segment must be task-specific") was
correctly rejected because it would break the legitimate on-disk T-126/T-150 shape
`"check_deliverable.py --exists X && uv run autotester doctor"`. I read `_is_task_specific`
directly (`tests/test_goal_done_checks.py:65-102`) and ran both candidates against that exact
string:

- Last segment is `uv run autotester doctor` → `_is_task_specific` returns `False` for it
  (`autotester` matches none of the `pytest`/`python`/`check_deliverable.py` branches, falls
  through to `return False`). So "last segment must be task-specific" **would** reject this
  legitimate command — the manifest's claim holds.
- The chosen fix (`any(seg in ALWAYS_TRUE for seg in segments)`) does not reject it, because
  `"uv run autotester doctor"` is not literally `"true"`/`":"`/`"exit 0"`; the command proceeds
  to `any(_is_task_specific(...))`, which is `True` on the first segment. Confirmed by direct
  call: `is_capable_of_failing("check_deliverable.py --exists qa/contracts/ai-target.md && uv run autotester doctor")`
  → `True`.

So on the specific comparison the manifest asks about, the chosen fix is correct where the
rejected one is not.

## A gap the manifest's own robustness claim does not survive — filed, not a FAIL

The dispatch asked me to confirm the chosen fix is "actually the more correct/robust one, not
just the one that passes the existing test suite," and to construct my own `;`-only case where
a first real segment is followed by something non-trivial but non-`ALWAYS_TRUE`. I did:

```
is_capable_of_failing("uv run pytest tests/test_x.py; echo done")  -> True   (measured)
is_capable_of_failing("uv run pytest tests/test_x.py; ls")         -> True   (measured)
```

Under real shell semantics a `;`-chain's exit code is the **last** segment's, independent of
earlier ones — both commands above always exit 0 (echo and a bare `ls` in an existing repo both
succeed) regardless of whether the guarded task is done. That is the exact AT-161 neutering
family, just not one of the three literal `ALWAYS_TRUE` tokens the fix's new clause checks for.
Interestingly, the *rejected* last-segment alternative **would** have caught both of these `;`
cases correctly (neither `echo` nor `ls` is task-specific) — it is only wrong for `&&` chains,
for exactly the reason the manifest gives. Neither candidate is fully correct on its own,
because the code (both before and after this fix) normalises `&&` and `;` into one split before
scoring, though the two separators have different exit-code semantics. Filed as **AT-359**
(medium; `qa/issues.jsonl`), with the fuller correct-direction note (treat `;` and `&&`
differently) in the issue body.

This is **not** charged as a FAIL of this unit: the manifest's own "What this unit does not
claim" section already discloses `is_capable_of_failing` "remains the same conservative
allowlist heuristic it always was, now closed for this one measured gap" — it does not claim
completeness against the whole neutering family, only against the five shapes AT-161's evidence
measured. AT-359 is the next measured gap in that same family, filed the way AT-161 itself was
filed against its parent unit (queued, not blocking).

## Criteria judged (C9, direct)

- [C9-a] A declared control value (`done_check`) is honoured or rejected, never silently
  ignored, for the five AT-161-named shapes — **met**: all five now rejected, verified by
  sabotage.
- [C9-b] Verify clause commands (`tests/test_goal_criticality_vocabulary.py
  tests/test_goal_done_checks.py`) exit 0 — **met**, re-run directly (the shape tests that used
  to live in `test_goal_done_checks.py` moved to the new file, which is imported by and
  collected alongside it; both pass).
- Rejected-alternative claim (T-126/T-150 would break under the discarded fix) — **verified
  independently**, holds.
- Not UI-touching, changed paths are `tests/` only — **confirmed** by `git show --stat`; Mode D
  correctly not invoked.

## Live browser

not-applicable (changed paths: `tests/test_goal_done_checks.py`,
`tests/test_goal_done_check_shapes.py` — pure test-helper logic, no route/template touched).

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 1/1 invariant holds
FAILURES (if any):
- none
LIVE-BROWSER: not-applicable (tests/test_goal_done_checks.py, tests/test_goal_done_check_shapes.py)
ISSUES-WRITTEN: AT-359
EXPLANATION: All four re-run verify commands passed on the live tree and the sabotage reproduced
the exact predicted single failure in an independently isolated git-archive extract. The
manifest's central correctness claim (the discarded "last segment must be task-specific" fix
would break the legitimate T-126/T-150 &&-of-two-real-segments shape) was independently checked
against _is_task_specific and holds. A further, narrower gap in the SAME neutering family (a
`;`-chain ending in a non-literal always-succeeding segment like `echo`/`ls`) is real and
measured but is outside what this unit's own manifest claims to close, so it is filed as AT-359
rather than failing this unit.
```
