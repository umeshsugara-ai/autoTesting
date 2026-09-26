# Verdict — at359-done-check-chain

**Date:** 2026-09-26 · **Head checked:** 25dcb56 (fix d0a333a) · **Cycle checked: 1** · **Issues addressed (claimed):** AT-359

```
VERDICT: FAIL
SCOREBOARD: AT-359's target is met (`pytest …; echo done` and `pytest …; ls` are now rejected; `&&` chains with a task-specific segment are accepted, as its expected clause prescribes); `||` stays rejected; but the rewrite REOPENS a hole AT-161 had closed
FAILURES:
- [C9 / AT-161 regression] sev: high · is_capable_of_failing (tests/test_goal_done_checks.py:103-131) now ACCEPTS `exit 0 && <task-specific>` and `exit 0; <task-specific>` as capable of failing. `exit` terminates the shell, so the task-specific segment never runs and the check always exits 0: the AT-100 "done_check that cannot fail" shape. The pre-unit master rule rejected both (verified). The rewrite dropped the blanket always-true reject and never modelled `exit` as a terminator. · fix: scan all segments left to right (across `;` and `&&`); once a bare `exit …` segment is reached, nothing after it is reachable, so score only the reachable prefix; add both strings to the `rejected` list in test_goal_done_check_shapes.py · issue: AT-359 (stays open)
CAPABILITY-COVERAGE: 2/2 manifest rows reproduced in an own-venv copy (the AT-161 flatten-any shape reverted -> red on 'accepted an unfailable check: …; echo done'; &&-group -> last-segment-only -> red, including T-126's real shape)
LIVE-BROWSER: not-applicable (changed paths: tests/test_goal_done_checks.py, tests/test_goal_done_check_shapes.py)
ISSUES-WRITTEN: none (AT-359 stays open with this evidence)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet subagent; reproduction: claude-opus-session)
EXPLANATION: The `;` fix is right, and moving `&& true` / `&& exit 0` to accepted is authorized by AT-359's own expected clause ("for a &&-joined chain, ANY segment being task-specific is enough"). But that clause never carved out `exit`, and the new position-scoped scoring now lets a leading `exit 0` hide the check entirely, a case master rejected.
```

## Evidence

- Shell ground truth: `bash -c 'exit 0 && echo RAN'` prints nothing, rc=0.
- Branch code (copy c359-1, identical test file):
  - `exit 0 && uv run pytest tests/x.py` -> True
  - `exit 0; uv run pytest tests/x.py` -> True
  - `pytest … && exit 0` -> True (correct)
  - `pytest …; true` -> False (correct)
  - `pytest … || true` -> False (correct)
- Master code (origin/master tests/test_goal_done_checks.py): both `exit 0 …` strings -> False.
- Worktree verify: the two test files -> 9 passed · ruff clean · doctor clean.
- Diff scope: only the two test files plus the manifest; the removed `rejected` entries are authorized by AT-359's expected clause (see explanation).

## The maker's questions

1. The `&& true` / `&& exit 0` move is authorized, as above; the regression is the separate leading-`exit` case.
2. `||` is still rejected (`pytest … || true` -> False).

Also noted (low, not scored): no code runs a `done_check.cmd`; an agent runs it by hand in whichever shell tool it picks. The PowerShell 5.1 tool parses `&&` and `||` as errors (fails loud, not a silent pass). State the POSIX-shell assumption in the goal skill's "typed done_check" section.

## Status: FAIL (cycle 1)
