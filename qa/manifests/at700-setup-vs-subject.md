# AT-700 — the test could not tell its own setup from its subject

**Unit:** AT-700 (high) + AT-701 (filed by this unit, see below)
**Fix cycle:** 2 of max 3
**Contract:** `qa/contracts/core-invariants.md` C12 ("every health signal must fail closed";
the clause "before reporting a check as evidence, name the arrangement of the data in which
it would have failed")
**Files:** `tests/test_flake_probe_real_process.py`, `scripts/flake_probe.py`
**Schema:** no · **Runtime:** none · **After:** nothing

## What was wrong

`test_run_once_kills_a_real_hung_process_and_its_real_grandchild` timed the nested run out at
10s. The grandchild it asserts on is spawned only if the nested pytest finishes starting first.
When it does not, `child.pid` is never written and the test dies on `FileNotFoundError` reading
it — **the identical red a build with `run_once`'s tree kill removed entirely would produce**,
because in that build the grandchild never starts either. Setup failure and subject failure were
indistinguishable, so the test could not catch the mutation its own docstring says it exists for.

## The mechanism, corrected twice on measurement

The checker first read this as load-sensitivity; the maker then read the isolated failure as new
nondeterminism. Both were wrong axes. The checker measured the floor (9.57–11.59s against a 10.00s
bound) and attributed the cost to "this repo's own conftest and collection". **That attribution
does not survive its control being run the other way round:**

| scenario file location | cwd | full run | pytest `--collect-only` |
|---|---|---|---|
| INSIDE the repo (conftest in scope, `configfile: pyproject.toml`) | repo root | 1.31–2.55s | **0.64s** |
| OUTSIDE, under system temp (as `tmp_path` is) | repo root | 7.26–9.28s | **19.68s** |

The conftest is loaded in the *fast* case. The cost is pytest building a `Dir` node for every
directory from the filesystem root down to the argument: reaching `tmp_path` walks the system temp
directory, which holds **14,645 entries** on this machine. That is why the peer measured ~10s and
this machine ~8s and the `--collect-only` probe 19.68s — **the floor is a function of how cluttered
the machine's temp directory is, so it grows over time.** A fixed larger bound alone would have
rotted.

## What changed

1. `tests/test_flake_probe_real_process.py` — new `scenario_dir` fixture puts the nested run's test
   file INSIDE the repo (`.work/at700-scenario-<pid>/hang_case.py`, removed after; not named
   `test_*.py`, so the outer session never collects it). Floor drops to ~0.64s collect / 1.31–2.55s
   run. `BOUND_S = 20` is then ~8x margin rather than a coin flip.
2. Same file — the **setup branch is split from the subject**: a missing `child.pid` is now its own
   `pytest.fail` naming the measured floor and saying in words that it reports nothing about the
   tree kill. Never folded into the kill assertion; never a skip, because a skip here is the silence
   that was the bug.
3. `scripts/flake_probe.py::run_once` (**AT-701**, found by the falsification, not predicted) — log
   deletion is now best-effort. A process that survives the tree kill still holds the inherited
   handle, so on Windows `log.unlink` raised `PermissionError` **from the `finally`, discarding the
   `Run` already computed** — converting a correctly recorded timeout into an exception, in exactly
   this probe's documented subject (a browser holds such a handle). The failure is recorded in
   `notes` and the run is still returned.

Both halves of (1)+(2) are required. A bigger bound alone leaves the conflation for a slower or
more cluttered machine; splitting the branch alone converts the red into a permanent
"scenario never started", which is silencing by another name.

## Capability rows, each independently falsified

| # | Claim | Falsifying edit | Observed |
|---|---|---|---|
| 1 | The test detects the mutation it exists for | replace `kill_tree(proc)` with `proc.kill()` in `run_once` | **CYCLE 2, re-run on the committed tree** — RED at the kill assertion: `AssertionError: run_once killed pytest but left its real grandchild running`, `assert not True`, `_alive(3616)`, at `test_flake_probe_real_process.py:125`. Restored; `git status` 0 modified; both orphaned grandchildren killed. |
| 2 | Before the fix, that same mutation was indistinguishable from setup failure | (measured on the pre-fix file) | the pre-fix mutant died on `PermissionError [WinError 32]` unlinking the log, never reaching the assertion — which is what surfaced AT-701 |
| 3 | The floor claim is the fixture's shape, not the machine's mood | run the identical no-op inside vs outside the repo | 0.64s vs 19.68s collect, table above |

## Verification (re-run, not recalled)

- `uv run pytest tests/test_flake_probe_real_process.py tests/test_flake_probe_runner.py` →
  `13 passed in 23.97s`, exit 0 (direct, unpiped — AT-692).
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`, exit 0.
- Full-suite re-run NOT yet done for this unit — the last full suite took 26 minutes and its only
  failure was this test. Stated as not-done rather than implied.

## Cycle 1 FAIL — what it was, and it was not a design problem

Verdict `qa/verdicts/at700-setup-vs-subject.md` (c2e430aa). **The production half of this unit was
never on disk.** After the falsification I ran `git checkout -- scripts/flake_probe.py` to undo the
MUTATION; it reverted the AT-701 fix in the same stroke, because that fix was still uncommitted.
`6fd9dcaa` touched no path under `scripts/`, while this manifest described the change in the past
tense and the ledger carried AT-701 as `fixed`. The checker reproduced the row both ways in a
throwaway copy of `git archive 6fd9dcaa` and showed it holds if and only if the missing half is
restored. **The observation was real; it was real of a tree that was never shipped.** On the
committed tree the conflation had simply moved from setup to cleanup — the unit's own subject
arriving one layer over, which is why FAIL was the right call rather than a note.

## Cycle 2 — what changed

Only the missing commit. `2782083e` carries the `run_once` change, and it was committed **before**
the row was re-run so the row and the artifact are the same object. Nothing else in the unit moved.

Evidence the tree and the result are the same object — `git show 2782083e:scripts/flake_probe.py`:

```python
    finally:
        try:
            log.unlink(missing_ok=True)
        except OSError as held:  # AT-701: a survivor of the kill still holds the handle
            notes = f"{notes}{chr(10)}log file still held after the kill: {held}"
```

Re-run on that tree: baseline `2 passed in 22.55s` exit 0; mutation → `AssertionError: run_once
killed pytest but left its real grandchild running`, `_alive(28028)`, line 125 — the line that
never executed in cycle 1. `ruff` clean, `doctor: clean`.

## Status: checked-PASS (cycle 2, verdict qa/verdicts/at700-setup-vs-subject.md, 726074d5, pushed)

Checker note folded for the next unit of this kind: it falsified the half NO capability row claimed
— that the setup branch is separated from the subject — by keeping the tree kill INTACT and setting
`BOUND_S = 1` so the grandchild cannot start. Red at :119 with "scenario never started ... says
NOTHING about run_once's tree kill" in 2.69s, against the mutation's `AssertionError` at :125:
different line, different exception type, and a message that disclaims the subject. That was the
most informative run of the cycle and nothing in this manifest pointed at it. **A claim of
separation needs its own row, or asserting the split takes the original defect's shape.**
