# Manifest — at469-mutation-ids-with-spaces

**Unit:** AT-469 — `scripts/mutation_check.py` cuts a failing test's nodeid at its first space, so a genuinely killed mutation on a parametrized test with a spaced id is reported SURVIVED
**Contract:** `qa/contracts/core-invariants.md` (C7, the mutation instrument clauses)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-469 (low, open → fixed) · **AT-473** (medium, cycle-1 FAIL: "longest match wins" credited a PASSING sibling, a false KILLED)

## Cycle 2: my fix made the one error this gate must never make

The cycle-1 verdict confirmed the spaced-id defect is fixed and all four rows die for the right reason.
It then failed the unit under C7:

> **AT-473 (medium).** The fix picks the longest collected nodeid that matches a FAILED line. If B's
> nodeid is A's nodeid + " - " + more text, and A fails with a message that starts with that text, the
> failure is credited to B, which passed. A real pytest run with ids `['a', 'a] - Failed: boom']`, where
> only `[a]` failed, reported the sibling KILLED. The pre-fix instrument got it right.

The checker is right, and my own test was the proof: it asserted "longest wins" for exactly that shape
(`test_z[q]` vs `test_z[q] - r]`), and Known limits said the change could only err toward SURVIVED.

**The two lines really are the same bytes.** `test_z[q]` failing with message `r] - AssertionError` and
`test_z[q] - r]` failing with `AssertionError` both print `FAILED tests/t.py::test_z[q] - r] -
AssertionError`. No rule over the summary text can tell them apart. So the only safe answer is **credit
neither**: a line that more than one collected nodeid fits adds nothing to the failures. Its named test
can then only read SURVIVED, the direction C7 tolerates, and never KILLED.

### What changed in cycle 2

- `scripts/mutation_check.py::failed_tests` — `max(whole, key=len)` is gone. Exactly one match →
  credited; no match → the regex reading (unchanged); two or more → credited to none. The docstring
  records AT-473 and why.
- `tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces`
  — the "longest wins" assertion is REPLACED. The ambiguous line now yields the empty set, and a new case
  checks that the shorter sibling failing with a plain message is still attributed to it.
- `tests/test_mutation_check.py::test_a_passing_sibling_is_never_credited_with_another_tests_failure` —
  new, end to end through `check()` and real pytest. Ids are `["a", "a] - AssertionError: r"]`, only
  `[a]` fails with message `r]`, and a `kills` naming the passing sibling must NOT be KILLED.
- `qa/evidence/at469-mutation-ids-with-spaces/mutations.json` — row 3 now restores the cycle-1 rule
  (`if whole: failures.add(max(whole, key=len))`), and must fail both tests above.

## Why

C7 makes `scripts/mutation_check.py` the gate every unit's tests pass through. Its failure parser was
`FAILED = re.compile(r"^FAILED\s+(?P<nodeid>\S+)")`. Pytest's parametrize ids routinely contain spaces
(the default id for a string parameter is the string itself), so
`FAILED tests/t.py::test_x[not json at all] - AssertionError` parsed as `tests/t.py::test_x[not`.
`collected_tests` keeps the full id, so `expected <= failures` was False and a real kill printed
`>>> SURVIVED`.

It bit the at465-466 unit live. Rows 1 and 4 printed no KILLED although the tests failed, and the maker
had to rename the parametrize ids to work around it. The error direction is fail-closed (a false
SURVIVED, never a false KILLED), which is why it is low. But an instrument that cries wolf trains its
users to rename tests rather than trust it.

## What changed

- `scripts/mutation_check.py:129-142` — `failed_tests(output, known=None)`. For each `FAILED` line it
  takes the rest of that line and, if collected nodeids are supplied, attributes the line to the LONGEST
  (cycle 1; replaced in cycle 2 by "exactly one, else none", see above) known nodeid that is either the whole line or followed by `" - "`. That is pytest's separator before
  the short message. A line matching no known nodeid keeps the old `\S+` reading. Called with no
  `known`, it behaves exactly as before.
- `scripts/mutation_check.py:270` (in `_check_in`) — the mutation loop passes every collected nodeid:
  `failed_tests(out, set().union(*collected.values()))`.
- `tests/test_mutation_check.py` — two tests:
  - `test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces` (unit). Covers a spaced id; a
    known nodeid that is a prefix-plus-`" - "` of a longer known nodeid (the longest must win); and a
    known `test_y` that is only a string prefix of an UNcollected failing `test_yz`, which must not steal
    it, since that would be a false KILLED.
  - `test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id` (end to end through
    `check()` on the synthetic `mutation_repo`, a test file with `ids=["one small value", "two"]`).

## How to verify (commands + expected)

- `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py` → `23 passed` (22 in cycle 1, plus the AT-473 end-to-end test)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at469-mutation-ids-with-spaces/mutations.json` → `4/4 mutations killed`
- `uv run pytest` → green (below)

## Actual outputs (from maker's own run)

Test-first. With `mutation_check.py` at HEAD and the two new tests present:

```
tests\test_mutation_check.py:181: TypeError
E       AssertionError: {'name': 'threshold broken', 'killed': False, 'exit': 1, 'expected': ['tests/test_spaced.py::test_small[one small value]'], ...}
tests\test_mutation_check.py:200: AssertionError
FAILED tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
FAILED tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id
2 failed, 14 passed, 1 warning in 46.26s
```

The end-to-end failure is the defect itself: `killed: False` with exit 1. The unit test failed on the
new `known` parameter not existing yet (TypeError), which is expected for a signature change.

After:

```
$ uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py
22 passed in 52.65s
$ uv run ruff check src tests scripts
All checks passed!
```

Full suite, cycle 2 (`uv run pytest`, bare):

```
FAILED tests/test_explore_live.py::test_the_dialog_page_does_not_trap_the_crawl
1 failed, 1403 passed, 2 skipped, 32 xfailed, 1 warning in 377.02s (0:06:17)
```

The one failure is not this unit's. It is `AssertionError: assert 'aborted_error' in ('aborted_dialog', 'explored')`,
the known AT-196 flake in a live-crawl test, while the other maker loop has uncommitted explore changes in
this tree. Run alone twice right after:

```
$ uv run pytest tests/test_explore_live.py
8 passed in 84.89s (0:01:24)
8 passed in 81.95s (0:01:21)
```

The cycle-1 run of this unit was `1395 passed, 2 skipped, 32 xfailed`. The count includes the other loop's tests.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| a mutation run attributes a kill to a spaced parametrize id (AT-469) | `test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id` | `failed_tests(out, set().union(*collected.values()))` → `failed_tests(out)` | KILLED (row 1) |
| the parser reads a spaced nodeid whole | `test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces` | `whole = [...]` → `whole = []` | KILLED (row 2) |
| a line two known nodeids fit is credited to NEITHER, so a passing sibling is never KILLED (AT-473) | `test_a_passing_sibling_is_never_credited_with_another_tests_failure` + the unit test's ambiguous case | restore the cycle-1 rule: `if whole: failures.add(max(whole, key=len))` | KILLED (row 3) |
| a known nodeid that is only a string prefix of an uncollected failing test does not claim it (no false KILLED) | same test (`test_y` vs `test_yz`) | `line.startswith(n + " - ")` → `line.startswith(n)` | KILLED (row 4) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at469-mutation-ids-with-spaces/mutations.json
KILLED  AT-469 reopens: the run ignores the collected nodeids, so a spaced id is cut and a kill reads SURVIVED  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id
    actually failed: tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id
KILLED  the parser stops consulting known nodeids at all  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
    actually failed: tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id, tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
KILLED  AT-473 reopens: an ambiguous line is credited to the longest match, so a PASSING sibling reads KILLED  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_passing_sibling_is_never_credited_with_another_tests_failure, tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
    actually failed: tests/test_mutation_check.py::test_a_passing_sibling_is_never_credited_with_another_tests_failure, tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
KILLED  a known nodeid that is only a PREFIX of an uncollected failing test claims its failure (a false KILLED)  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
    actually failed: tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces

4/4 mutations killed
```

**The first spec run caught a gap in my own test.** Row 4 SURVIVED on the first run. That output file was
overwritten by the re-run, so here are its lines, copied from the first run:

```
>>> SURVIVED  a nodeid followed by anything but ' - ' is accepted, so test_x[a] claims test_x[a b]  (pytest exit 0)
    SURVIVING      : tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces  <- INCONCLUSIVE: this mutation did not make them fail
3/4 mutations killed
```

My test's only prefix pair was
`test_x[a]` vs `test_x[a b]`, and `[a]` is not a string prefix of `[a b]`. So nothing pinned the `" - "`
boundary. The case that boundary actually defends is a known nodeid that is a bare prefix of an
UNcollected failing test, which would be a false KILLED. I added that case (`test_y` vs `test_yz`) and
the row now dies. I also renamed the row, whose first name described the wrong case, and re-ran the
spec rather than editing its output.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/mutation_check.py` (a verification CLI)
and `tests/test_mutation_check.py`.

## Known limits (disclosed, not claimed)

- **A failing test absent from the collected set still uses the old `\S+` reading.** If it has a spaced
  id, it is still truncated. That only matters for a test outside the spec's `tests` files, which cannot
  be a `kills` target anyway, because unknown names are refused before any mutation runs.
- **The `" - "` separator is pytest's `-q`/short-summary format.** A pytest version that changed it
  would fall back to the old `\S+` reading. That reading is the pre-AT-469 instrument, with the same
  properties it always had.
- **An ambiguous line reads SURVIVED even when the named test really failed.** That is deliberate
  (AT-473). It needs ids that embed `"] - <message text>"`, so it is contrived.
- **Cycle 1's claim was wrong, and is corrected here.** Cycle 1 said this change "can only err toward
  SURVIVED". Its longest-match rule could err toward KILLED. After cycle 2, the new branches add a
  failure only for an exact single match, or when nothing matched (the old regex reading, unchanged).
- **Pre-existing, unchanged:** the `^FAILED` regex scans all pytest output, including captured stdout
  shown in tracebacks (the cycle-1 checker's open question). This unit does not touch that.
- **`scripts/mutation_check.py` is 330 lines.** C2's cap names `src/` and `tests/`, and doctor enforces
  exactly that, so `scripts/` is not capped. It was already 319 before this unit.
- **The at465-466 renamed ids stay renamed.** Readable space-free ids are fine on their own; nothing
  needs reverting.

## Status: checked-PASS — `qa/verdicts/at469-mutation-ids-with-spaces.md` (Cycle checked: 2, commit 29976d7, pushed). AT-469 and AT-473 fixed. The checker filed AT-478 (`^FAILED` matches captured stdout, so a failing test can fake another test's kill) and AT-479 (a mutation that renames a parametrize id credits a test that never ran). Both are pre-existing false-KILLED shapes; AT-469 widened AT-478 to spaced ids.
