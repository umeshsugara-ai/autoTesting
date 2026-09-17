# Manifest — at490-491-tree-kill-is-bounded

**Unit:** AT-490 + AT-491, plus the two points the AT-487 code review raised
(`senior-software-engineer`, verdict Warning): the tree kill that bounds a hung pytest was itself
unbounded, its POSIX arm was unverified and crashed on a session that had already exited, and the
log decoded non-ASCII pytest output with the locale
**Contract:** `qa/contracts/core-invariants.md` (C7: the mutation instrument must terminate, and its
refusals must quote what pytest printed)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-490 (low, open → fixed) · AT-491 (low, open → fixed at the level its
`expected` names: "an explicit code-level test mocks os.name to prove the killpg call shape")

## What changed

- `scripts/mutation_check.py`
  - `KILL_GRACE_S = 30.0` and `import contextlib`.
  - `_kill_tree(proc, posix=os.name != "nt")`: the platform choice is a parameter so both arms are
    testable on one host.
    - POSIX: `os.killpg(proc.pid, signal.SIGKILL)` inside `contextlib.suppress(ProcessLookupError)`:
      the session can exit between the timeout and the kill (the review's race).
    - Windows: `taskkill /F /T` gets `timeout=KILL_GRACE_S`, and a taskkill that times out falls
      through. Its exit code stays unchecked on purpose: it is non-zero whenever some child had
      already exited (measured this session: 128). What decides is the next step.
    - `proc.wait(timeout=KILL_GRACE_S)`. A process still alive afterwards raises
      `MutationError("pytest (pid N) survived a kill of its process tree for 30s")` instead of
      waiting forever (AT-490's `expected`: "a short timeout and raise distinctly").
  - `_run_pytest`: the child env gets `PYTHONUTF8="1"`, so the log file is written in UTF-8 and read
    back as UTF-8.
- `tests/test_mutation_sandbox.py` (appended; `import subprocess`)
  - `_FakeProc`: a handle whose `wait` returns or raises `TimeoutExpired`.
  - `test_a_process_that_survives_the_tree_kill_is_refused_not_awaited_forever` (Windows arm,
    `subprocess.run` stubbed): raises `survived`, and the wait was given a timeout.
  - `test_the_posix_arm_kills_the_whole_session_and_tolerates_a_group_already_gone`: `os.killpg`
    stubbed (it does not exist on Windows) to record and raise `ProcessLookupError`, `signal`
    stubbed with `SIGKILL=9`. Asserts one call `(pid, 9)`, no exception, and a bounded wait.
  - `test_non_ascii_pytest_output_survives_the_log_round_trip`: a sandbox test prints `café ✓` and
    fails. The baseline refusal must quote it. `PYTHONUTF8` is deleted from the test's environment
    first (see row 5 below for why).

## How to verify (commands + expected)

- `uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py` → all pass (~3 min)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at490-491-tree-kill-is-bounded/mutations.json` → `5/5 mutations killed`, exit 0 (~2 min). No row here spawns a real hung process; the fake handle and stubs keep every kill off the machine.

## Actual outputs (from maker's own run)

```
$ uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py
...............................................                          [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

Red before the fix (tests written first, run against f29c41a's instrument):

```
E           TypeError: _kill_tree() got an unexpected keyword argument 'posix'   (x2)
E       assert 'caf\xe9 \u2713' in 'baseline is NOT green (pytest exit 1) ... FAILED tests/test_uni.py::test_uni - assert False ...'
3 failed, 6 deselected
```

The two kill tests go red on the signature, which is not the reason they are named for. The mutation
rows below are the evidence that each assertion discriminates on its own.

## Capability coverage (each new claim -> its isolating falsification)

`qa/evidence/at490-491-tree-kill-is-bounded/mutations.{json,out}`; every edit is one hunk in
`scripts/mutation_check.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| the post-kill wait is bounded | `test_a_process_that_survives...` | `proc.wait(timeout=KILL_GRACE_S)` → `proc.wait()` | `KILLED` (fails `survives` and `posix_arm`, both assert a bounded wait) |
| a survivor of the kill is refused, not ignored | `test_a_process_that_survives...` | the two-line `raise MutationError(... survived ...) from exc` → `return` | `KILLED` |
| a POSIX session already gone does not crash the run | `test_the_posix_arm...` | `contextlib.suppress(ProcessLookupError)` → `contextlib.suppress(OSError if False else ())` | `KILLED` |
| the POSIX arm SIGKILLs the session group | `test_the_posix_arm...` | `os.killpg(proc.pid, signal.SIGKILL)` → `os.killpg(proc.pid, 15)` | `KILLED` |
| non-ASCII pytest output reaches the refusal intact | `test_non_ascii...` | `PYTHONUTF8="1",` removed from the env | `KILLED` |

`5/5 mutations killed`.

**History of this spec (two rows fixed before the final run):**
- **Row 2's first edit** (`raise MutationError(` → `return print(`) left `from exc` behind. The
  sandbox suite failed to collect (exit 2), which SURVIVED correctly and proved nothing. The edit now
  replaces the whole statement.
- **Row 5 first SURVIVED** because the outer instrument now sets `PYTHONUTF8=1` for the pytest it
  runs, and the nested `check()` inherited it, so the test passed with the fix removed. The test now
  deletes the variable before running. That is a vacuity found by this instrument in its own test,
  and fixed in the test rather than explained away.

**What is still not covered (AT-491's other option):** no POSIX host has run the real hang tests
(`tests/test_mutation_check_judgement.py`), so `start_new_session=True` + a real `killpg` is still
unexercised end to end. The call shape and the race are pinned. The runtime behaviour on Linux is not.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/mutation_check.py`,
`tests/test_mutation_sandbox.py`.

## Known limits (disclosed, not claimed)

- **`scripts/mutation_check.py` is 416 lines** (AT-488, structural-erosion signal). Not split here.
- **`PYTHONUTF8=1` changes the child's default encoding for everything**, including files a test
  opens without `encoding=`. A project test that relied on the locale default could behave
  differently under mutation than under the normal suite. None in this repo does (ruff's `PLW1514`
  is not enabled, so this is not machine-checked).
- **A 30 s grace** is a judgement. A tree taking longer than that to die is refused as a survivor.

## Status: checked-PASS

Verdict: `qa/verdicts/at490-491-tree-kill-is-bounded.md` (Cycle checked: 1, commit 992f03f, pushed). Ledger: AT-490, AT-491 → fixed. The checker also re-ran the at468 and at481 specs against the changed harness (3/3 and 1/1, unchanged), so `PYTHONUTF8=1` regresses neither. This close-out also resolves AT-492 (the dispatch gap a sweep filed while the check was still running).
