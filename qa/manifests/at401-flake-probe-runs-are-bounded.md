# Manifest — at401-flake-probe-runs-are-bounded

**Unit:** AT-401 — `scripts/flake_probe.py::run_once` launched pytest with no `timeout=`, so one hung
run stopped an unattended N-run probe forever, with nothing recorded
**Contract:** `qa/contracts/core-invariants.md` (C7: a probe that loses trials silently reports a rate
computed from fewer trials than it claims)
**Goal task:** none (issue-driven; sweep check 7, filed 2026-09-16)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-401 (medium, open → fixed)

## Why this shape

The issue's `expected` asks for exactly two things: "pass a timeout and map `TimeoutExpired` to a
distinct `Run` outcome — a hung run is evidence about flakiness, not an absence of it." Both are done.
AT-487 (the same defect in `scripts/mutation_check.py`, PASSed earlier today) went further — a log
FILE instead of a pipe, plus a process-tree kill — because a mutation can make pytest loop forever
while a child holds the pipe. Here that would have meant rewriting four existing tests that carry
the reasons for `run_once`'s flags (AT-386/396/405/406) onto a new seam. The residual is disclosed
below rather than silently inherited.

## What changed

- `scripts/flake_probe.py`
  - `TIMED_OUT = -1` and `RUN_TIMEOUT_S = 1800.0` module constants.
  - `run_once(nodeid, index, timeout=RUN_TIMEOUT_S)`: `subprocess.run(..., timeout=timeout)`; on
    `TimeoutExpired` returns a `Run` with `returncode=TIMED_OUT`, the elapsed seconds, and a tail
    saying the run did not finish plus whatever pytest had printed before the kill.
  - `_decode(output)`: `TimeoutExpired.stdout` is bytes on some platforms even under `text=True`.
    `_tail(output, lines=25)`: the existing 25-line bound, now shared by both paths.
  - `Run.timed_out` property; `failed` is unchanged, so a hung run counts as a failure in every
    statistic (`observed_rate`, `ceiling`) with no special case.
  - `probe(nodeid, runs, timeout=RUN_TIMEOUT_S)` passes it through and keeps running the remaining
    trials after a timeout.
  - `describe`: a timed-out run prints `run N TIMED OUT (Xs)` instead of `FAILED (rc=-1)`.
  - `write_report`: each detail row carries `timed_out`.
  - CLI `--timeout` (seconds); `<= 0` prints `--timeout must be a positive number of seconds` and
    returns 2.
- `tests/test_flake_probe_runner.py` (appended; imports `json`) — five tests: the timed-out run's
  shape, the probe continuing, the report/description naming it, and the CLI refusal (`0`, `-5`).
- `tests/test_flake_probe_runner.py:123` — the ONE pre-existing line changed: the local
  `fake_run_once` stub in `test_the_probe_runs_every_trial_even_after_one_fails` gained the new
  `timeout` parameter. No existing assertion, name or reason was touched.

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe.py` → `27 passed`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at401-flake-probe-runs-are-bounded/mutations.json` → `5/5 mutations killed`, exit 0 (~2 min; no row spawns a real process — every row is driven through a stubbed `subprocess.run`)

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe.py
...........................                                              [100%]
27 passed in 0.31s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

Red before the fix (the five tests written first, against the unchanged probe):

```
FAILED tests/test_flake_probe_runner.py::test_a_run_that_outlives_its_bound_is_a_failure_marked_timed_out
FAILED tests/test_flake_probe_runner.py::test_the_probe_keeps_going_after_a_timed_out_run
FAILED tests/test_flake_probe_runner.py::test_a_timed_out_run_says_so_in_the_report_and_the_description
FAILED tests/test_flake_probe_runner.py::test_the_cli_refuses_a_timeout_that_is_not_positive[0]
FAILED tests/test_flake_probe_runner.py::test_the_cli_refuses_a_timeout_that_is_not_positive[-5]
5 failed, 6 passed
```

## Capability coverage (each new claim -> its isolating falsification)

`qa/evidence/at401-flake-probe-runs-are-bounded/mutations.{json,out}`; every edit is one hunk in
`scripts/flake_probe.py`. Test ids below are in `tests/test_flake_probe_runner.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a probe run is bounded | `test_a_run_that_outlives_its_bound...`, `test_the_probe_keeps_going...` | `check=False, timeout=timeout,` → `check=False,` | `KILLED` — both named tests failed |
| a hung run is never a green run | same two | `return Run(index=index, returncode=TIMED_OUT,` → `returncode=0,` | `KILLED` — both named tests failed |
| a hang is distinguishable from an ordinary failure | `...outlives...`, `test_a_timed_out_run_says_so...` | `return self.returncode == TIMED_OUT` → `return False` | `KILLED` — both named tests failed |
| the description names a timeout as a timeout | `test_a_timed_out_run_says_so...` | the `verdict = "TIMED OUT" if ...` line → `verdict = f"FAILED (rc=...)"` | `KILLED` |
| the CLI refuses a non-positive timeout | `test_the_cli_refuses...[0]`, `[-5]` | `if args.timeout <= 0:` → `if False:` | `KILLED` — both ids failed |

`5/5 mutations killed`.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/flake_probe.py`,
`tests/test_flake_probe_runner.py`.

## Known limits (disclosed, not claimed)

- **`UNVERIFIED — the bound is not proof against a child that holds the pipe.** `subprocess.run`
  kills pytest on timeout and then calls `communicate()`, which waits for the write end of the pipe
  to close; a grandchild (a browser the crawl started) inherits that handle and can keep it open.
  The very subject AT-401 names — the modal crawl (AT-335) — is that case. `mutation_check.py`'s
  `_run_pytest`/`_kill_tree` (AT-487/AT-490) is the stronger pattern: a log file plus a tree kill.
  Moving `run_once` onto it is a separate unit, and this one carries the gap as stated debt. No issue
  id yet: filing is the checker's, and this manifest is the record it should file from.
- **No test drives a real hung pytest.** Every new test stubs `subprocess.run`, so what is pinned is
  the mapping and the plumbing, not the OS behaviour.
- **Two probes of the same nodeid still share `.work/flake-probe.json`** unless `--out` differs.
  Pre-existing, untouched here.

## Status: ready-for-check
