# Manifest — at335-flake-probe-harness

**Unit:** AT-335 — a reproduction harness for the non-deterministic modal crawl, **not a fix**
**Contract:** `qa/contracts/explore.md`; core-invariants C2/C3/**C7**
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-335 (high) — **partially**; see "What this does not claim"

## What was wrong, and what this unit actually attacks

The modal crawl lost the dismissed-dashboard screen once, inside a red mutation baseline. The maker
who filed AT-335 tried 13 times to reproduce it, got 13 greens, and **correctly refused to ship a
fix**, writing: *"any fix I wrote would be unverifiable — and 'this cannot happen any more' with no
failing case to show is exactly the unfalsifiable claim C7 forbids."*

That was the right call. The arithmetic behind it was wrong, and the error runs the other way from
the usual one:

> **Thirteen clean runs bound the true failure rate at ~20.6%, not at zero.** The suspected rate is
> 7.1% (1 in 14), which sits comfortably *inside* that bound. Those 13 runs did not weakly support
> "it probably can't happen" — they said essentially **nothing** about the bug. To have a 95% chance
> of seeing a 1-in-14 flake you need **41** runs.

So the gap AT-335 leaves is not a missing fix, it is a **missing instrument**: no way to turn
"I tried and it didn't happen" into a number with a bound on it. Without that, any future
"AT-335 is fixed" is unfalsifiable in exactly the way C7 forbids — and so, equally, is
"AT-335 never happens".

## What changed

- `scripts/flake_probe.py` (new) — runs a pytest node id N times without stopping at the first
  failure, captures the failing output when the rare run lands, and reports **the bound a clean
  probe actually earns**. `ceiling_given_no_failures(n)` and `runs_for_confidence(rate)` are exact
  inverses of each other. Default `--runs` is `runs_for_confidence(1/14)` = 41, so the tool's
  default is the sample size AT-335 needed rather than a round number.
- `tests/test_flake_probe.py` (new) — 16 tests, driven entirely by fabricated `Run` rows. **No test
  here drives a browser:** a test whose own outcome depends on a 1-in-14 flake cannot be the thing
  that certifies the flake measurement.

No production code is touched. `stages/explore*.py`, the return ladder, `settle` — all unchanged.

### A bug in this unit, found by this unit's own consistency test

My first version used the familiar **rule of three** (`3/n`) for the bound. It is an approximation,
not the exact inverse of `runs_for_confidence`, and here that is not a rounding detail:

- `runs_for_confidence(7.1%)` → **41 runs**
- rule-of-three bound after 41 clean runs → **7.3%**, which is still *above* 7.1%

The tool would have told you to run 41 times and then told you 41 was not enough — two halves
contradicting each other about the same question. `test_the_named_sample_size_actually_achieves_what_it_claims`
exists to pin their agreement and is what caught it. Fixed to the exact form
`1 - (1-confidence)**(1/n)`, under which 41 clean runs bound the rate at **7.0%**.

## The probe's result on the real test — and it is not what I expected

```
$ uv run python scripts/flake_probe.py \
    "tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal" --runs 41
tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal: 0 failure(s) in 41 run(s)
  zero failures bounds the true rate at 7.0% (95% confidence) — NOT at zero
  the suspected 7.1% rate is outside that bound, so this probe excludes it
```

41 real crawls, 23.1 minutes of browser time, zero failures. **This bounds the rate below AT-335's
own 1-in-14 estimate** — the first evidence in this repo that actually constrains it.

**Three honest qualifications, because the margin is thin:**

1. **7.0% vs 7.1% is a 0.1-point margin.** "Excludes" is literally true at 95% and is what the tool
   prints, but nobody should read it as a robust refutation. One more run either way moves it.
2. **It excludes 7.1%, not the bug.** Any true rate below ~7% — 3%, 1%, 1-in-200 — remains fully
   consistent with this probe. The originally observed failure was real and is not explained away.
3. **The statistics line above was recomputed from the saved run data, not taken from the probe's
   own stdout.** The 41 runs launched before I fixed the rule-of-three bug, so the live output said
   "7.3% … does NOT exclude it" — the contradiction itself. The 41 outcomes are the measurement and
   are unaffected; the bound is a pure function of them, so I re-derived it with the shipped code
   rather than re-driving the browser for another 23 minutes. Both numbers are stated here so the
   checker can see exactly what was recomputed and why.

## What this does not claim

- **AT-335 is not fixed and must not be closed by this unit.** The return ladder is untouched, the
  suspected bfcache mechanism is unconfirmed, and a rate below 7% is still a rate.
- It does not diagnose the cause. It does not add retries, tolerance, or a settle change — doing
  that on this evidence would be the unfalsifiable fix AT-335's author refused to write, and I am
  refusing it for the same reason with better numbers.
- The 41 runs were sequential on a machine **shared with a concurrent maker session**. CPU
  contention was not controlled for, and the original failure was suspected to be timing-related, so
  a quiet machine is arguably the *least* likely condition to reproduce it. A future probe under
  deliberate load would be a stronger test; this one is not that.
- `run_once` / `probe` (the subprocess halves) have **no isolating test** — testing them would mean
  shelling out to pytest from inside pytest. They are thin wrappers, and the 41-run evidence above is
  the only thing that exercises them. Stated as enumerated debt, not covered.

## Capability coverage

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, single file) | Observed |
|---|---|---|---|
| The bound a clean probe earns is exact, and agrees with the sample size the tool recommends | `tests/test_flake_probe.py::test_the_named_sample_size_actually_achieves_what_it_claims` | `flake_probe.py`: `return 1.0 - (1.0 - confidence) ** (1.0 / runs)` → `return -math.log(1.0 - confidence) / runs` (the rule-of-three bug) | GREEN before (`16 passed`); after **FAILED** that test + 2 others, at `test_flake_probe.py:98` |
| An empty probe has no rate, rather than a rate of zero | `::test_an_empty_probe_has_no_rate_rather_than_a_rate_of_zero` | `flake_probe.py`: `... if self.runs else None` → `... if self.runs else 0.0` | GREEN before; after **FAILED exactly 1**, `where 0.0 = Summary(nodeid='t', runs=[]).observed_rate` |
| A clean probe says out loud that it bounds the rate, not that it proves absence | `::test_a_probe_that_saw_nothing_reports_a_bound_and_not_a_zero` | `flake_probe.py`: delete `— NOT at zero` from the `describe` f-string | GREEN before; after **FAILED exactly 1**, `assert 'NOT at zero' in 'tests/test_x.py::test_y: 0 failure(s) in 13 run(s)…'` |
| Once a failure is seen, the zero-failure bound is withheld rather than reported alongside it | `::test_a_reproduced_failure_reports_the_observed_rate_and_keeps_its_evidence` | `flake_probe.py`: `if not self.runs or self.failures:` → `if not self.runs:` | GREEN before; after **FAILED exactly 2**, at `test_flake_probe.py:150` |

Every edit is a single hunk in a single file named in "What changed"; each anchor was asserted to
match **exactly once** and to produce a real change; none broke import or collection (16 tests
collected every run).

**One mutation initially failed to apply and was NOT reported as a result.** My harness asserts
`count(anchor) == 1` before writing, and for row 4 my first anchor used `summary.` where the source
says `self.` — zero matches, so it refused. Without that assertion the run would have re-reported
the *previous* mutation's failures as row 4's evidence, which is precisely the wrong-reason red C7
forbids. Re-run with the correct anchor; that second run is what the table reports.

## How to verify (commands + expected)

- `uv run pytest tests/test_flake_probe.py -q` → expected: exit 0, 16 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run python scripts/flake_probe.py "tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal" --runs 3`
  → expected: exit 0, a 3-run report whose bound is ~63% and which says `does NOT exclude`
  (**a cheap re-run** — the full 41 takes ~23 minutes of real browser time)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_flake_probe.py -q
................                                                         [100%]   (16 passed)

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

AT-357's `tests/test_mutation_check.py` flake did not fire. Note that this suite run includes
`tests/test_explore_modal.py`, i.e. a 42nd clean crawl — not folded into the 41-run bound above,
because it ran under different conditions (inside the full suite) and mixing sample populations to
nudge a 0.1-point margin is exactly the kind of number-improving I should not be doing to my own
evidence.

`uv run pytest -q` emits no `N passed` line — `pyproject.toml` sets `addopts = "-q"`, making the
adapter's command effectively `-qq`. The exit code is the evidence.

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. `git archive HEAD | tar -x` into a scratchpad extract; layered this unit's two files on.
2. `uv sync`; `flake_probe.__file__` confirmed resolving **inside the extract**.
3. Baseline in the extract: `uv run pytest tests/test_flake_probe.py -q` → **16 passed**.
4. Four mutations, each applied from a pristine backup and reverted before the next, each guarded
   by the exactly-once anchor assertion described above. Results in the table.
5. Extract deleted; live tree confirmed to carry only this unit's two paths.

## Live browser evidence

**The unit's changed paths are not UI-touching** — `scripts/flake_probe.py` and
`tests/test_flake_probe.py`. No route, template, component or page is reachable from either, and no
production code changed.

A real browser **was** driven 41 times during this unit, by the probe, against the existing
`test_the_crawl_gets_past_the_modal` — but that is this unit's *subject*, not validation of a
surface this unit changed. Recording it here so the distinction is explicit rather than implied.
Raw per-run data: `.work/at335-flake-probe.json` (gitignored scratch, per this project's CLAUDE.md).

## Data-boundary gate (MC-003)

Exits 1 on `adapter.json has no "data_class"` — AT-365, open, at HUMAN_GATE. Not introduced here;
the changed paths hold no data.

## Checker ruling (2026-09-16, verdict 10e56ee) — PASS, 16/16 criteria, 9/9 invariants

All four capability rows reproduced outside the bound root, every statistic re-derived from
scratch, and all six dispatch questions ruled on. The sections above are left byte-intact; the
corrections it charged are recorded here.

- **AT-388 (low) — "exact inverses" over-states the implementation.** True of the maths, not of the
  code: `runs_for_confidence(ceiling_given_no_failures(n))` returns `n+1` for 236 of the first 499
  `n`, from float `ceil` epsilon. The direction the tool actually depends on,
  `ceiling(runs_for_confidence(r)) <= r`, holds at all 1799 rates the checker tested — so the code
  is right in every use it is put to and the *phrase* is what over-claims. Left for its own unit;
  I am not slipping a docstring edit in after a PASS.
- **AT-387 (low) — presentation.** The recomputed statistics sit inside a `$ command` block that
  reads as stdout, and the block elides a trailing clause. The recomputation itself was ruled
  **legitimate**: the checker opened `.work/at335-flake-probe.json`, found 41 contiguous `rc=0`
  entries totalling 23.1 min, and confirmed its stored ceiling `0.073067` is exactly `-ln(0.05)/41`
  — independently corroborating that the buggy form was live when those runs happened.
- **AT-386 (medium) — the debt matters more than where I put it.** The 41-run headline rests
  entirely on `run_once`'s returncode→`failed` mapping, which no test touches. **My stated reason
  was also wrong:** I said testing it would mean pytest-in-pytest, but monkeypatching
  `subprocess.run` tests `run_once` and monkeypatching `run_once` tests `probe`. The checker
  exercised both branches itself (3 clean runs → 63.2% bound; 3 injected failures → rate 100%,
  ceiling correctly withheld, tail captured). It also noted my enumeration carried no ledger id —
  prose, not an `UNVERIFIED` row — and assigned one rather than burning a fix cycle on a reformat.
- **AT-389 (low) — the anchor I excluded is itself a guess.** The 7.1% figure is a one-observation
  estimate whose own interval spans <1% to >30%, so "excluding 7.1%" excludes a guess, not a
  measured rate. The next unit must not cite it as settled.
- **AT-390 (low)** — `Run` and `probe` collide by name with `src/autotester` symbols.
- **AT-391 (low) — environmental, and the caller's to act on.** Two maker sessions share one
  working tree, so `qa/adapter.json` slot-1 is currently unreproducible for either: the checker hit
  `doctor` exit 1 and `pytest` exit 2 from the *other* session's in-flight files, and had to rebuild
  this unit's tree outside the root to get a clean read. Per-maker worktrees is the suggested fix.

The checker also ran `test_explore_modal` ~47 more clean times. **AT-335 stays open**, consistent
with a rate below 7%.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at335-flake-probe-harness.md`, commit 10e56ee; AT-335 stays open by design; AT-386..391 filed)
