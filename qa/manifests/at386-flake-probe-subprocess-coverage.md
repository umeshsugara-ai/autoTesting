# Manifest — at386-flake-probe-subprocess-coverage

**Unit:** AT-386 — the flake probe's subprocess halves had no test, and the whole 41-run
headline rested on them
**Contract:** `qa/contracts/explore.md`; core-invariants **C7**
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-386 (medium)

## What was wrong

`at335-flake-probe-harness` shipped 16 tests driven entirely by fabricated `Run` rows. Neither
`run_once` nor `probe` was exercised by any of them — so the **one mapping the entire measurement
stands on**, `returncode != 0 → failed`, was untested. If it broke, 41 undetected failures would
have read as 41 green runs and every statistic in that manifest would have been computed from a
lie, with nothing in the suite noticing.

I enumerated this as debt, which is admissible. **But the reason I gave was wrong**, and the
checker said so: I wrote that testing it "would mean shelling out to pytest from inside pytest".
It does not. Monkeypatching `subprocess.run` tests `run_once`; monkeypatching `run_once` tests
`probe`. The debt was real; my excuse for it was not, and an inaccurate reason is how enumerated
debt quietly becomes permanent.

## What changed

- `tests/test_flake_probe.py` — five new tests, no production code touched:
  - `test_a_nonzero_return_code_is_what_makes_a_run_count_as_failed` — the load-bearing mapping.
  - `test_a_clean_run_keeps_no_output` — 41 green runs must not carry 41 copies of pytest chatter
    into the report and bury the one tail somebody needs.
  - `test_a_failure_tail_is_bounded_rather_than_the_whole_log` — and it keeps the **end** of the
    log, where the failure is.
  - `test_each_run_is_isolated_from_the_ones_before_it` — `-p no:cacheprovider` and `-o addopts=`
    are load-bearing, not cosmetic: without the first, pytest's cache lets one run inform the next,
    and **a probe whose trials are not independent cannot support a binomial bound at all.** Every
    number `flake_probe` prints would be wrong in a way no other assertion catches.
  - `test_the_probe_runs_every_trial_even_after_one_fails` — now driven through the real `probe`
    with `run_once` monkeypatched, rather than asserted on a hand-built `Summary`.

## A rule this unit has to bend, stated rather than hidden

The capability-coverage contract says a falsifying edit must be **a single-hunk edit to a single
file named in "What changed"**. This unit changes only a test file, so obeying that literally is
impossible: the capability claimed is *"this behaviour is now covered"*, and the only way to
falsify it is to break the behaviour — which lives in `scripts/flake_probe.py`, shipped in
`4be4503` and **byte-unchanged here**.

So all four falsifying edits below target `scripts/flake_probe.py`. I am naming it explicitly as
this unit's **subject** so the checker's single-file rule is satisfied by declaration rather than
violated silently. If the checker judges that inadmissible, the honest remedy is to amend the rule
for test-only units, not to let me quietly widen it.

## Capability coverage

**Subject under test:** `scripts/flake_probe.py` (unchanged by this unit; the file the new tests cover).

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `scripts/flake_probe.py`) | Observed |
|---|---|---|---|
| A failing run is counted as failed | `::test_a_nonzero_return_code_is_what_makes_a_run_count_as_failed` | `return self.returncode != 0` → `return False` | GREEN before (`21 passed`); after **FAILED 5 tests** including the named one. **Broad on purpose and reported as broad:** `Run.failed` is read by every statistic, so breaking it reddens the pre-existing rows too. The named test is in the list and fails on its own assertion. |
| The rare failure's output survives, bounded, end-first | `::test_a_failure_tail_is_bounded_rather_than_the_whole_log` | `tail = "" if proc.returncode == 0 else "\n".join(…[-25:])` → `tail = ""` | GREEN before; after **FAILED exactly 2**, at `test_flake_probe.py:203` |
| Trials are independent — the precondition for any bound at all | `::test_each_run_is_isolated_from_the_ones_before_it` | drop `"-p", "no:cacheprovider"` from the argv list | GREEN before; after **FAILED exactly 1**, `assert 'no:cacheprovider' in [...'-m', 'pytest', 'tests/test_x.py::test_y', '-q', '-o', ...]` |
| The probe measures a rate rather than confirming an existence | `::test_the_probe_runs_every_trial_even_after_one_fails` | `probe` rewritten to `break` on the first `failed` run | GREEN before; after **FAILED exactly 1**, at `test_flake_probe.py:245` |

Every anchor was asserted to match **exactly once** and to produce a real change; none broke import
or collection (21 tests collected on every run).

## What this does not claim

- It does not test that `run_once` actually launches a real pytest — `subprocess.run` is
  monkeypatched in all five. The end-to-end path was exercised for real by the checker last cycle
  (3 clean runs, 3 injected failures) and by the 41-run probe itself; these tests cover the logic
  around the call, not the call.
- It does not change any statistic, bound, or the AT-335 result. **AT-335 stays open.**
- It does not address AT-387/388/389/390 — the presentation, the `exact inverses` over-claim, the
  one-observation anchor, or the name collisions. Those are separate rows and separate units.

## How to verify (commands + expected)

- `uv run pytest tests/test_flake_probe.py -q` → expected: exit 0, 21 passed (was 16)
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_flake_probe.py -q
.....................                                                    [100%]   (21 passed)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest -q
[... all dots ...]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:53
  DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use
  anyio.from_thread.BlockingPortal instead.
EXIT: 0
```

AT-357's flake did not fire, and the shared-tree breakage AT-391 describes did not bite this run.

`uv run pytest -q` emits no `N passed` line (`pyproject.toml` sets `addopts = "-q"`, so the
adapter's command is effectively `-qq`). The exit code is the evidence.

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. `git archive HEAD | tar -x` into a scratchpad extract; layered this unit's one changed file on.
   `scripts/flake_probe.py` came from HEAD untouched — the subject is the shipped code, not a copy
   I could have quietly adjusted to suit the tests.
2. `uv sync`; `flake_probe.__file__` confirmed resolving **inside the extract**.
3. Baseline in the extract: `uv run pytest tests/test_flake_probe.py -q` → **21 passed**.
4. Four mutations, each applied from a pristine backup and reverted before the next, each guarded
   by the exactly-once anchor assertion. Results in the table.
5. Extract deleted; live tree confirmed to carry only this unit's one path.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed path: `tests/test_flake_probe.py`. No production
code, no route, template, component or page.

## Data-boundary gate (MC-003)

Exits 1 on `adapter.json has no "data_class"` — AT-365, open, at HUMAN_GATE. Not introduced here.

## Note on the shared tree (AT-391)

The checker filed AT-391 last cycle: two maker sessions share this working tree, so slot-1 verify is
intermittently unreproducible — it hit `doctor` exit 1 and `pytest` exit 2 from the *other*
session's in-flight files. My runs above were clean, but a checker re-running them may not be, and
that would be AT-391 rather than this unit. The sabotage extract is immune, being outside the root.

## Checker ruling (2026-09-16, verdict 6e8681a) — PASS, 4/4 criteria, 9/9 invariants

Sections above left byte-intact; corrections recorded here.

- **The "bend" was not a bend — and I should have known.** `core-invariants.md`'s amendment log
  already carries a 2026-09-16 entry (the at357 cycle-2 ruling) permitting a falsifying edit
  against the module under test for a test-only unit, precisely because a test cannot falsify
  itself and the literal reading would make C7's mutation duty unsatisfiable for that whole class.
  All four of its conditions were met. **Next time: cite that entry instead of asking for a
  bend.** I read the contract for its criteria and not for its amendment log, which is the half
  that says what the criteria have already become.
- **AT-396 (low) — my stated reason for `-p no:cacheprovider` over-claims, and the checker measured
  it rather than arguing.** With cacheprovider active and `-o addopts=` as `run_once` passes it,
  pytest writes `lastfailed` but the next identical invocation still collects **both** tests:
  selection is only informed by that cache under `--lf`/`--ff`/`--sw`, none of which is passed. So
  the flag is **defensive hygiene** — no shared `.pytest_cache` writes between trials, non-trivial
  in a repo with AT-357 — **not** the precondition for the binomial bound, as my test docstring
  claims. The test and the code are both correct; the prose is what is wrong. The checker noted
  this is *the same shape as the defect AT-386 existed to remove* — a confident justification
  nobody had measured.
- **AT-395 (medium) — a capability row I omitted.** "What changed" claims five behaviours; my table
  enumerates four. `test_a_clean_run_keeps_no_output` has no row, and row 2's edit (`tail = ""`)
  **cannot** redden it — the two tests pin the two arms of one ternary. The checker supplied the
  missing row itself (mutating the if-arm reddens exactly that test at `:191` on
  `assert run.tail == ""`), so the capability is covered and falsifiable and only the enumeration
  was missing. It recorded rather than charged, on the grounds that a FAIL would spend fix cycle
  2 of 3 producing a table row for a property already proved — and noted that a row whose edit had
  *survived* would have failed the unit outright.
### The row AT-395 says was missing, supplied (added 2026-09-16, after the PASS)

The table above is left byte-intact. This is the fifth row it should have carried, reproduced by
the checker in its own copy rather than by me:

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `scripts/flake_probe.py`) | Observed |
|---|---|---|---|
| A clean run keeps no output, so 41 greens do not bury the one failing tail | `tests/test_flake_probe.py::test_a_clean_run_keeps_no_output` | in `run_once`, mutate the **if-arm** of the tail ternary (the `""` branch) so a passing run also stores its stdout | reddens **exactly that one test**, at `test_flake_probe.py:191` on `assert run.tail == ""` |

Row 2's edit (`tail = ""` wholesale) **cannot** redden this test — the two tests pin opposite arms
of one ternary, which is exactly why one edit could not stand in for both and why the omission
mattered.

- **AT-397 (low)** — the all-monkeypatched limit was accurately stated and is **not** waived: once
  AT-386 closes, nothing standing covers a real subprocess launch. Filed so the residual is tracked.
- **Subject byte-identity verified, not believed:** `git hash-object` on the bound tree, on
  `4be4503:scripts/flake_probe.py`, and on the extracted copy all give blob `cddc387`; the diff is
  96 insertions, 0 deletions. The tests were not fitted to an adjusted subject.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at386-flake-probe-subprocess-coverage.md`, commit 6e8681a; ledger AT-386 open → fixed; AT-395/396/397 filed)
