# Manifest — at396-isolation-flag-claims

**Unit:** AT-396 — the recorded *reason* for the flake probe's isolation flags was stronger than
the facts; plus AT-395's missing capability row, supplied
**Contract:** `qa/contracts/core-invariants.md` (C2, **C7**)
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-396 (low), AT-395 (medium)

## What was wrong

`test_each_run_is_isolated_from_the_ones_before_it` pinned two flags and explained why. The
explanation was confident and unmeasured:

> *"Without the first, pytest's cache lets one run inform the next, and a probe whose trials are
> not independent cannot support a binomial bound at all — every number this tool prints would be
> wrong."*

A checker **measured** it instead of arguing: pytest writes `lastfailed`, but the next identical
invocation still collects every test, because selection is only informed by that cache under
`--lf`/`--ff`/`--sw` — none of which `run_once` passes. The flag is defensive hygiene (41 trials
not racing a shared `.pytest_cache`, non-trivial in a repo that has had exactly that race —
AT-357), **not** the precondition for the statistics.

The checker noted this is the same shape as the defect AT-386 existed to remove: a confident
justification nobody had measured. The test and the code were both correct; only the prose was
wrong — which is why nothing caught it, because nothing executes a docstring.

## The fix nearly shipped a second over-claim, inside the fix for the first

My replacement wording said `-o addopts=` is load-bearing because `pyproject.toml:62` sets
`addopts = "-q"`, so without it every run is `-qq` and "the failing output this probe exists to
capture is suppressed."

I measured it before writing it down. **It is false.** Running a deliberately failing test both
ways, inside the repo so `pyproject.toml` is the rootdir config:

```
WITHOUT -o addopts= -> lines: 11 | shows assert: True
WITH    -o addopts= -> lines: 12 | shows assert: True
```

The traceback survives either way. The entire difference is **one summary line** (`1 failed in
Xs`). So `-o addopts=` is also a deliberate choice rather than a correctness precondition, and the
docstring now says so.

Two over-claims about the same two flags, one of them written while fixing the other, is the
argument for pinning the wording rather than trusting the next author to be careful.

## What changed

- `tests/test_flake_probe.py` — the docstring of
  `test_each_run_is_isolated_from_the_ones_before_it` rewritten to state, separately for each flag,
  what was actually measured. **The test body is unchanged**; both flags are still pinned, because
  a flag nobody asserts is a flag a future edit drops for free. What changed is the reason recorded
  beside them.
- `tests/test_flake_probe.py` — one new test,
  `test_the_isolation_flags_are_not_described_as_load_bearing`, asserting neither refuted claim can
  return and the measured wording stays. A docstring is where an unmeasured justification survives
  longest, precisely because nothing runs it.
- `qa/manifests/at386-flake-probe-subprocess-coverage.md` — **AT-395**: the fifth capability row
  that manifest should have carried, added to its corrections block with the table above left
  byte-intact. The row is the checker's own reproduction, not mine: mutating the **if-arm** of the
  tail ternary reddens exactly `test_a_clean_run_keeps_no_output` at `:191`. Row 2's edit
  (`tail = ""` wholesale) cannot redden it — the two tests pin opposite arms of one ternary, which
  is why one edit could never have stood in for both.

No production code is touched. `scripts/flake_probe.py` is unchanged.

## Capability coverage

Unlike at386, every falsifying edit here lands in `tests/test_flake_probe.py` — the file named in
"What changed" — because the claim under test *is* the docstring. No rule accommodation needed.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `tests/test_flake_probe.py`) | Observed |
|---|---|---|---|
| The refuted binomial-bound claim cannot return | `::test_the_isolation_flags_are_not_described_as_load_bearing` | restore "a probe whose trials are not independent cannot support a binomial bound at all" to the docstring | GREEN before (`22 passed`); after **FAILED exactly 1**, at `test_flake_probe.py:283` |
| The refuted output-suppression claim cannot return | same test | rewrite the `-o addopts=` paragraph to assert the failing output "is suppressed without it" | GREEN before; after **FAILED exactly 1**, at `:283` |
| The measured verdict on `-o addopts=` stays stated | same test | soften "not load-bearing" to "it keeps the capture honest" | GREEN before; after **FAILED exactly 1**, `assert 'not load-bearing' in '…'` at `:285` |

### A mutation I ran that SURVIVED, reported rather than dropped

My first third mutation deleted the closing sentence *"Both are pinned anyway: a flag nobody
asserts is a flag a future edit drops for free. What changed is the REASON recorded next to them,
not the test."* — and **all 22 tests stayed green.**

That is not a coverage gap; it is a mis-aimed edit. That sentence carries no refuted claim and no
measured verdict, so it is not part of any capability this unit asserts, and nothing should have
reddened. I replaced it with the edit above, which targets wording the test genuinely asserts.

I am recording the survived attempt because the alternative — quietly substituting the mutation
that worked — is precisely how a sabotage table starts describing a run that did not happen. C7's
INCONCLUSIVE rule is what makes a green sabotage informative rather than embarrassing.

## What this does not claim

- It does not change `run_once`'s behaviour, the flags it passes, or any statistic. The two flags
  are still passed and still pinned.
- It does not close AT-390 (the `Run`/`probe` name collisions) or AT-397 (nothing standing exercises
  a real subprocess launch). Separate rows, separate units.
- The pin is a **string** assertion on a docstring. It stops the two refuted sentences returning
  verbatim; it cannot stop a third, differently-worded over-claim. That is a real limit of this
  approach and I am not pretending otherwise — the general defence is measuring before writing, not
  a regex.

## How to verify (commands + expected)

- `uv run pytest tests/test_flake_probe.py -q` → expected: exit 0, 22 passed (was 21)
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- The measurement behind the corrected claim, re-runnable:
  write a failing test under `.work/`, then run it with and without `-o addopts=` — expected: the
  assert text appears both times; the line counts differ by exactly one.

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_flake_probe.py -q
......................                                                   [100%]   (22 passed)

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

No `N passed` line — `pyproject.toml:62`'s `addopts = "-q"` makes the adapter's command `-qq`,
which is the same mechanism this unit is about. The exit code is the evidence. AT-391's shared-tree
breakage did not bite this run.

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree:**

1. `git archive HEAD | tar -x` into a scratchpad extract; layered this unit's changed test file on.
   `scripts/flake_probe.py` came from HEAD untouched.
2. `uv sync`; `flake_probe.__file__` confirmed resolving **inside the extract**.
3. Baseline in the extract: **22 passed**.
4. Four mutations attempted, each from a pristine backup with an exactly-once anchor assertion:
   three killed their named test, one survived and is reported above as mis-aimed.
5. Extract deleted; live tree confirmed to carry only this unit's two paths.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `tests/test_flake_probe.py`,
`qa/manifests/at386-flake-probe-subprocess-coverage.md`. No production code, no route, template,
component or page.

## Data-boundary gate (MC-003)

Exits 1 on `adapter.json has no "data_class"` — AT-365, open, at HUMAN_GATE. Not introduced here.

## Checker ruling (2026-09-16, verdict 4891a77) — PASS, 9/9 criteria

Both measurements **re-derived independently rather than inherited**, which is what I asked for:

- `-o addopts=`: my replacement claim is **correct**, not a third over-claim. The checker's own
  failing-test run with `-c pyproject.toml` found the traceback, the `E AssertionError` and the
  short-summary `FAILED` line surviving both ways, with the entire delta being the one summary
  line. Its counts were 12/13 to my 11/12 (`wc -l` vs `splitlines()`); the delta — the
  load-bearing part — is identical. It added a point I had missed: `run_once` keeps only the last
  25 lines and both outputs fit inside 25, so the flag **cannot** change what the probe records
  even at the margin.
- `-p no:cacheprovider`: confirmed. Cacheprovider active, `lastfailed` written, and the next
  identical invocation still ran **both** tests; only `--lf` deselected. `run_once` passes none of
  `--lf/--ff/--sw` and passes an explicit nodeid, so selection is doubly moot.

**The pin is NOT the AT-218 vacuous-guard class** — it reddened under three separate mutations,
each on its own assertion, and it asserts the exact artifact that was wrong rather than a proxy.
The survived mutation was ruled correctly classified as mis-aimed: a red there would have meant
the guard pins prose the unit does not claim, which is C7's zero-failure clause working as
intended.

**AT-395's supplied row verified in both halves:** the if-arm mutation reddens *exactly*
`test_a_clean_run_keeps_no_output` at `:191`; the wholesale `tail = ""` edit reddens `:179` and
`:203` and leaves the clean-run test **green**. Genuinely cross-immune — one edit could never have
covered both arms.

### Three residuals, none a criterion violation

- **AT-406 (low) — my disclosure was one notch too generous.** I said the pin stops the two
  sentences returning verbatim. It stops them returning verbatim **on one line**: the same words
  wrapped across the 78-column boundary this file's own docstrings produce would survive. Cheap
  fix named: `' '.join(doc.split())` before matching.
- **AT-405 (low) — both refuted claims still stand verbatim as assertion messages** of the very
  function whose docstring I corrected: `:243` "runs must not inform each other" and `:244` "the
  project's -q must not suppress the failure output". The new guard reads `__doc__` only, so it
  structurally cannot see them. I corrected the prose a reader sees and left the prose a *failing
  test* prints.
- **AT-407 (medium) — the file was untracked.** Addressed immediately, outside this unit: see
  `5e9ae80`.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at396-isolation-flag-claims.md`, commit 4891a77; ledger AT-395 + AT-396 open → fixed; AT-405/406/407 filed)
