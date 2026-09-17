# Manifest — at487-pytest-runs-are-bounded

**Unit:** AT-487 — `scripts/mutation_check.py` ran pytest with no timeout, so one hung pytest (an
infinite loop introduced BY a mutation, or a wedged fixture) hung the whole mutation check forever
**Contract:** `qa/contracts/core-invariants.md` (C7: the mutation instrument is mandatory, so it must
terminate and must never report a hang as a kill)
**Goal task:** none (issue-driven, found by the 2026-09-17 sweep)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-487 (medium, open → fixed). Not AT-401 (`scripts/flake_probe.py`, same shape,
different file: left for its own unit).

## What changed

- `scripts/mutation_check.py`
  - `TIMED_OUT = -1` and `PYTEST_TIMEOUT_S = 1800.0` module constants.
  - `_run_pytest(..., timeout=PYTEST_TIMEOUT_S)`: `subprocess.Popen` writing to
    `<sandbox parent>/mutation-pytest.log` instead of a pipe, then `proc.wait(timeout=...)`. On
    `TimeoutExpired`, `_kill_tree` kills pytest AND its children (`taskkill /F /T` on Windows,
    `os.killpg` in a new session elsewhere) and the run returns `TIMED_OUT` with the sentence
    `pytest did not finish within <N>s; killed with its children` appended to the output.
    File, not pipe: a child a test starts inherits the handle, and a pipe reader then waits for that
    child too.
  - `collected_tests(cwd, tests, timeout=...)` passes it through; collection timing out is a refusal
    (existing `code != 0` path).
  - `_timeout(spec)`: optional spec key `timeout_s`, a positive number (bool refused), else
    `MutationError`.
  - `_check_in`: baseline timing out → existing "baseline is NOT green" refusal. A mutation that
    times out → `exit -1`, `killed False` (is_kill needs exit 1), new result key `timed_out: True`.
    The file is still restored, so the next mutation runs.
  - `report`: prints `NOTE: pytest timed out and was killed — a hang is not a kill`.
- `tests/test_mutation_check_judgement.py` (appended; imports `os`, `subprocess`, `threading`, `time`)
  - `_within(seconds, fn)`: runs the check on a daemon thread, so a regression fails the test in
    bounded time instead of wedging the suite.
  - `test_a_mutation_that_hangs_pytest_times_out_and_is_not_a_kill` (mutation `while value > 0: pass`,
    `timeout_s=20`).
  - `test_a_hung_baseline_is_refused_even_when_a_child_holds_the_output_open` (a test that starts a
    `sleep(600)` child which writes its pid, then sleeps; `timeout_s=15`; asserts the refusal AND that
    the child pid is no longer alive, via `tasklist` / `os.kill(pid, 0)`).
  - `test_it_refuses_a_timeout_that_is_not_a_positive_number[0,-5,60,True,None]`.

## How to verify (commands + expected)

- `uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py` → all pass (≈4 min; two tests wait out 15–20 s timeouts)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at487-pytest-runs-are-bounded/mutations.json` → `5/5 mutations killed`, exit 0 (≈10 min)
- **After any run that applies the mutations, clean up the orphans those mutations deliberately
  create** (rows 1 and 3 leave hung pytest / `sleep(600)` processes by design). Filter by THIS
  checkout's venv path and `child.pid`; a second maker loop runs pytest from
  `.work/wave-x18a-login/.venv` and must not be touched.

## Actual outputs (from maker's own run)

```
$ uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py
............................................                             [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

Red before the fix (tests written first, run against the unchanged instrument):

```
E       AssertionError: still running after 120s: the pytest run is unbounded
FAILED tests/test_mutation_check_judgement.py::test_a_mutation_that_hangs_pytest_times_out_and_is_not_a_kill
```

## Capability coverage (each new claim -> its isolating falsification)

Full spec and output: `qa/evidence/at487-pytest-runs-are-bounded/mutations.{json,out}` (run
16:24:32Z → exit 0). All edits single-hunk in `scripts/mutation_check.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| every pytest run is bounded | `test_a_mutation_that_hangs...`, `test_a_hung_baseline...` | `code = proc.wait(timeout=timeout)` → `code = proc.wait()` | `KILLED ... actually failed: test_a_hung_baseline..., test_a_mutation_that_hangs...` |
| a timed-out mutation is reported as timed out, never as a kill | `test_a_mutation_that_hangs...` | `"timed_out": code == TIMED_OUT,` → `"timed_out": False,` | `KILLED ... actually failed: test_a_mutation_that_hangs...` |
| the timeout kills pytest's children too | `test_a_hung_baseline...` (child pid assertion) | `["taskkill", "/F", "/T", "/PID", ...]` → `["taskkill", "/F", "/PID", ...]` | `KILLED ... actually failed: test_a_hung_baseline...` |
| a zero or negative `timeout_s` is refused | `test_it_refuses_a_timeout...[0,-5]` | `... or value <= 0:` removed | `KILLED ... actually failed: [-5], [0]` |
| a boolean `timeout_s` is refused | `...[True]` | `isinstance(value, bool) or ` removed | `KILLED ... actually failed: [True]` |

`5/5 mutations killed`.

**Honest history of row 3:** the first full run (16:08Z) reported `4/5` — row 3 SURVIVED, because the
test then asserted only that the run ended, which a file-based log achieves even when the child lives.
The test was strengthened (child writes its pid; assert it is dead), row 3 re-run alone → KILLED, then
the whole spec was re-run → 5/5. The `.out` in evidence is that second full run.

`UNVERIFIED -- the POSIX branch (start_new_session + os.killpg)` ships untested on this Windows host;
the tests take the same path on POSIX but no run here exercised it. Carried as disclosure, not as a
claim (no issue filed: CI is Windows-only today).

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/mutation_check.py`,
`tests/test_mutation_check_judgement.py`.

## Known limits (disclosed, not claimed)

- **Default 30 min per pytest run.** A legitimately slow suite over 30 min now refuses; a spec can raise
  `timeout_s`. No current spec comes near it.
- **The whole spec is not bounded**, only each pytest run: N mutations × timeout.
- **`scripts/mutation_check.py` grows to 401 lines** (AT-488, structural-erosion signal, was 361).
  `scripts/` is outside C2's cap; splitting is AT-488's decision, not this unit's.
- **Maker incident, self-reported:** while cleaning up orphans from the red-before-fix run, the maker's
  first process filter (`tests/test_mod.py` in the command line) also matched and killed one pytest
  process running in the other maker loop's worktree `.work/wave-x18a-login` (pid 51492, ~16:05Z). That
  loop may see one spurious failed or truncated run. All later cleanups filter by this checkout's venv
  path.

## Status: ready-for-check
