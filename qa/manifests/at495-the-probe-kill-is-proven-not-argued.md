# Manifest — at495-the-probe-kill-is-proven-not-argued

**Unit:** AT-495 — `flake_probe.run_once`'s tree-kill was argued sound by analogy to
`mutation_check`'s AT-487 evidence, never measured here
**Contract:** `qa/contracts/core-invariants.md` C7 (a capability is claimed only with an isolating
falsification — an unfalsifiable claim is the thing C7 forbids)
**Goal task:** none (issue-driven; filed by the at494 checker from that manifest's disclosed gap)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-495 (low, open → fixed)

## The measurement, first

Both gaps the issue names were real:

1. Every test in `tests/test_flake_probe_runner.py` stubs `subprocess.Popen` (`_FakePopen`), so
   `run_once`'s real `kill_tree(proc)` call at `scripts/flake_probe.py:179` had never executed
   against an actual OS process, let alone one with a real grandchild holding the log file's
   inherited handle open.
2. The branch at `scripts/flake_probe.py:180-181` — `kill_tree` raising `RuntimeError` because the
   tree outlived the kill — was reached by no test in this file. Nothing asserted the message
   lands in `run.tail` or that the run stays `TIMED_OUT` rather than lost.

I wrote a failing-first isolating test for each, modelled directly on
`tests/test_mutation_check_judgement.py::test_a_hung_baseline_is_refused_even_when_a_child_holds_
the_output_open` (real hung process + real grandchild, asserting the grandchild is **dead**
afterward, not merely that the call returned). **Both passed on the first run, against
unmodified code.** I then mutated each claim in turn (below) to confirm the tests are not
vacuous — a test I cannot make fail by breaking the thing it defends is not evidence, whichever
way its first run went. Per the brief: **this unit is pure test coverage.** No production line in
`scripts/flake_probe.py` or `scripts/mutation_check.py` changed. `run_once` already does what its
docstring claims; that claim had just never been checked.

## What changed

- **`tests/test_flake_probe_real_process.py` (new file).** `tests/test_flake_probe_runner.py` is
  already at 263 of the 300-line cap (C2) with no room for two process-spawning tests plus their
  docstrings, so this splits along the seam the brief names explicitly: "if your tests do not fit,
  split along a real seam and say why in the manifest." The seam matches the two existing splits in
  this file family (`test_flake_probe.py` → `test_flake_probe_runner.py`;
  `test_mutation_check.py` → `test_mutation_check_judgement.py` → `test_mutation_sandbox.py`):
  *runner-with-fakes* stays in `test_flake_probe_runner.py`; *runner-against-a-real-process* is new
  and named for exactly that. Two tests, imports only, no fixture/conftest changes.
  - `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` — spawns a real
    `python -m pytest` process via `run_once` itself, whose one test starts a real child that
    writes its own pid then sleeps, times out at a real 10s bound, and asserts the child is
    **dead** afterward (`_alive`, imported from `test_mutation_check_judgement`, not redefined —
    C3). Bounded by `_within(60, ...)` (same import), so a regression that hangs fails this test
    in bounded time rather than the suite.
  - `test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail` — a
    control-flow test, not a real-process one: it reuses `test_flake_probe_runner._FakePopen` to
    make `run_once` time out, monkeypatches `flake_probe.kill_tree` to raise `RuntimeError`
    (the real raising behaviour is `mutation_check`'s own to prove — already covered by
    `test_mutation_sandbox.py::test_a_process_that_survives_the_tree_kill_is_refused_not_awaited_
    forever` — this only proves `run_once` reacts to it correctly), and asserts the run is still
    `TIMED_OUT` with the message in its tail.
- Nothing else. `scripts/flake_probe.py`, `scripts/mutation_check.py`,
  `tests/test_flake_probe_runner.py` are unchanged (mutated only transiently, during the mutation
  run below, then restored — confirmed by `git status` showing no diff in them).

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe_real_process.py`
  → `13 passed`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at495-the-probe-kill-is-proven-not-argued/mutations.json`
  → `3/3 mutations killed`, exit 0

## Actual outputs (from my own run)

```
$ uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe_real_process.py
.............                                                            [100%]
13 passed in 12.68s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run python scripts/mutation_check.py qa/evidence/at495-the-probe-kill-is-proven-not-argued/mutations.json
KILLED  the real tree-kill call is dropped entirely on a real timeout  (pytest exit 1)
    claims to kill : tests/test_flake_probe_real_process.py::test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail, tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
    actually failed: tests/test_flake_probe_real_process.py::test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail, tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
KILLED  the unkillable-tree message is dropped from the run's tail  (pytest exit 1)
    claims to kill : tests/test_flake_probe_real_process.py::test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail
    actually failed: tests/test_flake_probe_real_process.py::test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail
KILLED  the Windows kill drops the tree flag and only kills pytest itself  (pytest exit 1)
    claims to kill : tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
    actually failed: tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild

3/3 mutations killed
```

## Capability coverage (each new claim → its isolating falsification)

`qa/evidence/at495-the-probe-kill-is-proven-not-argued/mutations.{json,out}`. Each mutation is one
hunk; the first two are in `scripts/flake_probe.py`, the third in `scripts/mutation_check.py`
(the module `run_once` imports `kill_tree` from — admissible under the 2026-09-16
core-invariants.md amendment: named here explicitly, single-hunk, single-file, and the file the
changed test directly exercises through the real, unmocked call path).

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a real timeout kills the whole real process tree, not just pytest | `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` | `kill_tree(proc)` → `pass` (`scripts/flake_probe.py`) | `KILLED` |
| the Windows kill actually reaches the tree (`/T`), not just the named pid | `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` | drop `"/T"` from the `taskkill` argv (`scripts/mutation_check.py`) | `KILLED` |
| an unkillable tree is still recorded `TIMED_OUT`, never lost | `test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail` | `kill_tree(proc)` → `pass` (`scripts/flake_probe.py`) | `KILLED` |
| the unkillable-tree message actually lands in the run's tail | `test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail` | `notes = f"{chr(10)}{unkilled}"` → `notes = ""` (`scripts/flake_probe.py`) | `KILLED` |

`3/3 mutations killed`. Baseline asserted green by the instrument itself before any mutation (C7);
each mutation's anchor matched exactly once in its file and the file was restored after
(`mutation_check.py`'s own `_check_in`/`_inside` guarantees, unchanged here).

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `tests/test_flake_probe_real_process.py`
(new), `qa/evidence/at495-the-probe-kill-is-proven-not-argued/{mutations.json,mutations.out}`,
this manifest.

## Known limits (disclosed, not claimed)

- **Both gaps AT-495 named are closed, not one.** Read the "Capability coverage" table against the
  issue text: gap 1 (real hung process, real grandchild) is the first two rows; gap 2 (`kill_tree`
  raising) is the last two.
- **The `RuntimeError`-raising test is a control-flow test, not a real-process one.** Making
  `kill_tree` genuinely fail to kill a real process on this machine, reliably and without leaving
  something un-killable for real, is not something I could construct safely under this unit's
  PROCESS-KILL SAFETY constraint (no killing anything this test did not itself spawn and record).
  I monkeypatch `flake_probe.kill_tree` to raise instead. That is a deliberate, disclosed choice,
  not an oversight: the real "can `kill_tree` itself fail to kill a real tree" question is
  `mutation_check`'s own to answer, and it already does —
  `test_mutation_sandbox.py::test_a_process_that_survives_the_tree_kill_is_refused_not_awaited_
  forever`. What was untested, and is now, is purely `run_once`'s reaction to that failure.
- **One transient flake observed and not reproduced.** On my first mutation run, the second
  mutation ("the unkillable-tree message is dropped") reported BOTH new tests failing instead of
  only the named one. I reproduced the mutation by hand outside the tool immediately after and got
  the clean, single-test failure shown above; two subsequent full tool runs (including the one
  pasted above) also showed only the named test failing. I could not pin a cause — my best guess is
  resource contention from the previous mutation's real orphaned grandchild (a `sleep(600)`
  process that mutation 1 deliberately leaves alive to prove it survived) still winding down on a
  machine also running a second maker/checker loop — but I am reporting a single unreproduced
  observation, not a diagnosed defect. `is_kill`'s `expected <= failures` clause means this would
  never produce a false PASS (an extra failure only ever adds a KILLED, never removes one); it
  could in principle produce a false SURVIVED if load caused a real test to pass when it should
  have failed, which is the opposite of what was observed. Flagging it rather than silently
  re-running until clean, per C7.
- **The real-process test leaves a real (bounded) orphan on purpose when a mutation is applied.**
  Mutation 1 and mutation 3 each cause the test-spawned grandchild to survive by design — that is
  the failure being detected. It self-terminates after its `sleep(600)` (10 minutes) regardless;
  nothing in this unit enumerates or kills processes by name, image, or command line, only pids the
  test itself spawned and recorded, per this unit's PROCESS-KILL SAFETY constraint.
- **`tests/test_flake_probe_real_process.py` adds ~13s to the suite** (two real subprocess-spawning
  tests, ~6s each). The full suite's ~9-minute baseline is not materially affected.

## Status: checked-PASS

Cycle 1, `qa/verdicts/at495-the-probe-kill-is-proven-not-argued.md` (commit `588cca7`, pushed per
D-007). PASS with no failures. The checker confirmed independently that the real-process test
asserts the grandchild **dead** by a pid the test recorded — the sound shape, not the weaker
"the call returned" shape that a missing `/T` would have satisfied — and that the file split
follows a seam this family has used twice before (`git log --diff-filter=A`: `1e95b1a`,
`baf56a1`/`de484fd`).

**The disclosed attribution anomaly is recorded as unmeasured, not absent.** The builder saw one
mutation misattribute on its first run and could not reproduce it. Three agents have now run the
set: builder 3 clean after the anomaly, maker 1 clean on master, checker 2 clean — six clean
against one anomalous, on a machine carrying ~19 concurrent `python.exe` processes and a second
maker loop. The checker also verified in code (`scripts/mutation_check.py:83-109`) that
`expected <= failures` cannot manufacture a false PASS: an extra failure only strengthens the
subset test. Six runs is a sample, not a rate — this repo ships `scripts/flake_probe.py` precisely
to say so — and the verdict says so rather than reading six greens as a clean bill.
