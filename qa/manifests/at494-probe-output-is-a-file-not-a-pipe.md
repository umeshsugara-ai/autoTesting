# Manifest — at494-probe-output-is-a-file-not-a-pipe

**Unit:** AT-494 — `flake_probe.run_once`'s timeout was not a real bound: `subprocess.run` kills
pytest and then drains the pipe, which waits for every holder of the write end, and this probe's own
subject is a browser crawl whose browser is such a holder
**Contract:** `qa/contracts/core-invariants.md` (C7: an instrument that can hang forever cannot be
the thing that measures)
**Goal task:** none (issue-driven; filed by the at401 checker from that manifest's disclosed gap)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-494 (medium, open → fixed)

## What changed

This is exactly the remedy AT-494's `expected` names: "move `run_once` onto the same
log-file-plus-process-tree-kill pattern `scripts/mutation_check.py` already uses".

- `scripts/mutation_check.py:151` — `_kill_tree` → **`kill_tree`** (public). One rename, no body
  change: it now has a second caller, and a private name borrowed across modules is worse than a
  public one. `tests/test_mutation_sandbox.py:209,233` follow the rename; no assertion changed. The
  AT-490/491 mutation spec's anchors do not name the function, so
  `qa/evidence/at490-491-tree-kill-is-bounded/mutations.json` still applies unchanged (re-run below).
- `scripts/flake_probe.py`
  - imports `os`, `tempfile`, and `kill_tree` from `mutation_check` (the script dir is put on
    `sys.path` first, as `tests/` already does). **Not a copy** — one bounded-kill implementation.
  - `run_once` now launches pytest with `subprocess.Popen`, `stdout` to a per-run log FILE in the
    temp dir (`stderr` merged), `PYTHONUTF8=1`, and `start_new_session` off Windows so the POSIX
    kill has a group to signal. On `TimeoutExpired` it calls `kill_tree(proc)` and records
    `TIMED_OUT`; if the tree outlives the kill, `kill_tree` raises and its message is appended to
    the run's tail rather than aborting the probe. The log file is removed in a `finally`.
- `tests/test_flake_probe_runner.py`
  - `_FakeCompleted` → `_FakePopen` (writes its output to the sink, `wait(timeout)` returns or
    raises `TimeoutExpired`, carries a `pid`). The four pre-existing tests that stubbed the launcher
    move to it: **every assertion, name, docstring and reason is unchanged** — only the stub they
    patch. The seam moved, so the stub had to.
  - `_hanging(monkeypatch, killed)` helper replaces `_timing_out`, and
    `test_a_run_that_outlives_its_bound...` now also asserts the recorded kill was `kill_tree` on
    the process (pid `424242`), not a bare `proc.kill()`.
  - The AT-386 comment's "only a monkeypatched `subprocess.run`" now says
    "a monkeypatched launcher (`subprocess.Popen` since AT-494)".

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe.py tests/test_mutation_sandbox.py` → `36 passed`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at494-probe-output-is-a-file-not-a-pipe/mutations.json` → `3/3 mutations killed`, exit 0
- The rename did not weaken the sibling unit: `uv run python scripts/mutation_check.py qa/evidence/at490-491-tree-kill-is-bounded/mutations.json` → `5/5 mutations killed`

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe.py tests/test_mutation_sandbox.py
....................................                                     [100%]
36 passed in 16.46s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run python scripts/mutation_check.py qa/evidence/at494-probe-output-is-a-file-not-a-pipe/mutations.json
3/3 mutations killed
```

## Capability coverage (each new claim -> its isolating falsification)

`qa/evidence/at494-probe-output-is-a-file-not-a-pipe/mutations.{json,out}`; each edit is one hunk in
`scripts/flake_probe.py`. Ids below are in `tests/test_flake_probe_runner.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a timed-out run kills the whole tree, not just pytest | `test_a_run_that_outlives_its_bound...` | `kill_tree(proc)` → `proc.kill()` | `KILLED` — that test failed (the recorded kill was not `kill_tree`) |
| output goes to a file, never a pipe | `test_a_failure_tail_is_bounded...`, `test_each_run_is_isolated...` (+`test_a_clean_run_keeps_no_output`) | `stdout=sink,` → `stdout=subprocess.PIPE,` | `KILLED` — all three failed |
| a hung run is still recorded as timed out through the new path | `test_a_run_that_outlives...`, `test_the_probe_keeps_going...` | `code = TIMED_OUT` → `code = 0` | `KILLED` — both failed |

`3/3 mutations killed`. The AT-401 rows (the `Run.timed_out` mapping, the description, the CLI
refusal) are unchanged and still covered by
`qa/evidence/at401-flake-probe-runs-are-bounded/mutations.json`, which this unit does not alter.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/flake_probe.py`,
`scripts/mutation_check.py` (one rename), `tests/test_flake_probe_runner.py`,
`tests/test_mutation_sandbox.py` (the same rename).

## Known limits (disclosed, not claimed)

- **Still no test drives a real hung OS process.** `_FakePopen` raises `TimeoutExpired` rather than
  hanging. What is pinned is that the file seam and the tree kill are used; that they work against a
  real browser grandchild is argued from `mutation_check`'s AT-487 evidence (which DID drive a real
  hung pytest with a real child), not measured here.
- **`kill_tree` raising is handled but untested**: if the tree outlives the kill, the message lands
  in the run's tail. No test covers that branch; the sibling behaviour is covered in
  `tests/test_mutation_sandbox.py::test_a_process_that_survives_the_tree_kill...`.
- **`flake_probe` now imports `mutation_check`.** Both live in `scripts/`; the import is at module
  level and costs nothing at runtime, but it does couple the probe to the mutation instrument's
  module-level constants. The alternative was a second copy of the kill, which C1 forbids.
- **The log file is `<temp>/flake-probe-<pid>-<index>.log`.** Two probes of the same nodeid from one
  process would collide only if they shared an index, which `probe` never does.

## Status: checked-PASS

Verdict: `qa/verdicts/at494-probe-output-is-a-file-not-a-pipe.md` (Cycle checked: 1, commit 1688da3, pushed). The first checker died on a session rate limit with no verdict (not a fix cycle); this is the re-dispatch. Checker re-verified the sibling AT-490/491 evidence (5/5) after the rename, filed AT-495 (low, the real-hung-process gap carried forward) and AT-496 (medium, the shared ledger working copy lost rows mid-write).
