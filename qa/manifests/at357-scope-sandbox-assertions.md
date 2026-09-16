# Manifest — at357-scope-sandbox-assertions

**Unit:** AT-357 — the mutation harness's own leak tests assert on a machine-global temp glob
**Contract:** `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven, promoted to the top of `qa/QUEUE.md` by the 2026-09-16 sweep
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-357 (open → fixed) · AT-331 (the same flake, filed separately)

## Why this one, and why now

`scripts/mutation_check.py` is the instrument C7 makes mandatory: every unit that adds a test must
prove the test dies when the behaviour it names is reverted. Two of the harness's own tests asserted
that `tempfile.gettempdir().glob("mutation-check-*")` was unchanged across a run — **a statement
about the whole machine, not about this run.** Any other mutation check in flight changed that set
and the tests went red.

Two maker loops run in this repo, so concurrent mutation runs are the steady state. **The instrument
that enforces C7 went red precisely when C7 was being enforced somewhere else**, and it has been
mis-attributed as a flake in three separate manifests. The 2026-09-16 sweep promoted it for exactly
that reason: it had stopped being a nuisance and started costing runs — it cost that sweep its own.

The production code was already correct. `_discard` deletes only the root its own `_sandbox` call
returned and never sweeps by glob. **The defect was entirely in the tests**, which is why this unit
touches no behaviour.

## What changed

- `tests/test_mutation_check.py` — the two global-glob assertions replaced by an **autouse
  `private_temp` fixture** that points `tempfile.tempdir` at a per-test directory. The assertion
  becomes `list(private_temp.iterdir()) == []`, which is **stricter** than what it replaced: the
  root starts empty, so it asserts emptiness rather than equality with a `before` set that may
  already have held anything.
- `tests/test_mutation_sandbox.py` — **new**. The sandbox half, split out under doctor's 300-line
  cap (the edit pushed the file to 314). The seam is a real responsibility boundary, not an
  arbitrary cut: `test_mutation_check.py` is about what counts as a **kill** — attribution, anchors,
  red baselines, exit codes — and this file is about the **sandbox lifecycle**, the half with a
  destructive operation in it. No source module was duplicated and no behaviour moved.
- Two tests added (18 → 20 across the pair).

## Three things this unit found that were not in the issue

1. **The fix as first written was vacuous, and the mutation run is what showed it.** Scoping
   `private_temp` to the three leak tests left the assertions passing for the wrong reason: drop the
   `tempfile.tempdir` redirection and the sandboxes go to the real temp dir, `private_temp` holds
   nothing, `list(...) == []` is satisfied by an empty directory, and a genuine leak sails through.
   `test_the_sandbox_really_is_created_under_the_private_root` pins the redirection itself, and a
   mutation kills it. This is the third time a shared/implicit sentinel has made a test in this repo
   vacuous, and the third time only a mutation caught it.

2. **The glob mutation reached out of the sandbox and destroyed the instrument measuring it.** With
   the fixture scoped to three tests, the mutation that makes cleanup sweep by glob was executed by
   the *other* tests in the file — which still used the machine-wide temp dir — so the mutated code
   deleted **the outer mutation harness's own sandbox, mid-run**. The run died with

   ```
   FileNotFoundError: [Errno 2] No such file or directory:
     'C:\\Users\\Lenovo\\AppData\\Local\\Temp\\mutation-check-ydjjjwud\\repo\\scripts\\mutation_check.py'
   ```

   instead of reporting a kill. Making the fixture **autouse** is what fixed it, and that is why
   autouse is load-bearing here rather than tidiness: every test in the module is hermetic now,
   which is also the honest reading of what "sandbox" was supposed to mean.

3. **Nothing pinned "cleanup does not sweep by glob."** The docstring explains at length that
   `_discard` cannot tell its own sandbox from a concurrent run's, and no test held it to that. A
   future "tidy up the leftovers" change would look exactly like a fix for AT-325 and would delete
   another loop's **live** sandbox mid-run — a destructive operation keyed on a path the process
   does not own, which is AT-314's shape in different clothes.
   `test_a_concurrent_runs_sandbox_is_left_alone` plants a decoy and pins it.

## Capability coverage (each new claim → its isolating falsification)

All three rows are single-hunk edits to a single file named in "What changed". `observed` is the
pasted `mutation_check.py` output below; the runner refuses to start against a red baseline, so each
row's named test is green before the edit, and the runner prints `claims to kill` against
`actually failed` so the kill is **attributed**, not merely a non-zero exit.

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| the sandbox is removed when a run finishes or is refused (AT-325) | `test_the_sandbox_is_removed_when_the_run_finishes`, `…even_when_the_run_is_refused` | `_discard` returns without deleting | KILLED (row 1) |
| cleanup never sweeps the temp dir by glob, so a concurrent run's live sandbox survives (AT-357) | `test_a_concurrent_runs_sandbox_is_left_alone` | `_discard` deletes every `mutation-check-*` under temp | KILLED (row 2) |
| the leak assertions are scoped to this run and are not vacuous (AT-357) | `test_the_sandbox_really_is_created_under_the_private_root` | drop the `tempfile.tempdir` redirection | KILLED (row 3) |

## How to verify (commands + expected)

- `uv run pytest` → expected: `1209 passed, 2 skipped`
  *(`uv run pytest -q` resolves to `-qq` — `pyproject.toml` `addopts` already carries `-q` — and
  suppresses the summary line. Exit 0 is the signal.)*
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py` → expected: 20 passed
- `uv run python scripts/mutation_check.py qa/evidence/at357-scope-sandbox-assertions/mutations.json`
  → expected: `3/3 mutations killed` (C7)

**The verification that actually settles AT-357** is none of the above — it is running the tests
*while a mutation check is in flight*, which is the condition that used to redden them:

```
$ uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json &
$ sleep 20 && ls $TEMP/mutation-check-* -d | wc -l
live sandboxes during the run: 3
$ uv run pytest tests/test_mutation_check.py
19 passed in 29.44s
$ wait
concurrent run finished: 21/21 mutations killed
```

Three foreign sandboxes live in the temp dir, and the tests are green. Under the old assertions they
would have failed on the first one. (That run predates the file split, hence 19 rather than 20.)

## Actual outputs (from maker's own run)

```
$ uv run pytest
1209 passed, 2 skipped, 1 warning in 211.67s (0:03:31)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py -o addopts= -q
....................                                                     [100%]
20 passed in 32.28s

$ uv run python scripts/mutation_check.py qa/evidence/at357-scope-sandbox-assertions/mutations.json
KILLED  the sandbox is never removed - AT-325's leak returns  (pytest exit 1)
KILLED  AT-357: cleanup sweeps the temp dir by glob and eats a concurrent run's live sandbox  (pytest exit 1)
KILLED  AT-357: the temp-root redirection is dropped, so every leak assertion goes vacuous  (pytest exit 1)
3/3 mutations killed
```

Per-mutation attribution is in `qa/evidence/at357-scope-sandbox-assertions/mutations.out`.

The `1209` total includes tests belonging to the **other maker loop**, whose `cli_loop.py`,
`loop_status.py` and `test_loop_status.py` are untracked in this shared working tree. This unit
adds **two** tests; the rest of the delta is not mine and is not claimed.

## Live browser evidence

**Not UI-touching — no surface changed.** The changed paths are `tests/test_mutation_check.py` and
the new `tests/test_mutation_sandbox.py`; no `src/` file, no template, no route, and nothing a
page's data flows through. The unit's subject is a build-time instrument that never runs in a
browser.

## Status: ready-for-check
