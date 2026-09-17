# Manifest — at469-mutation-ids-with-spaces

**Unit:** AT-469 — `scripts/mutation_check.py` cuts a failing test's nodeid at its first space, so a genuinely killed mutation on a parametrized test with a spaced id is reported SURVIVED
**Contract:** `qa/contracts/core-invariants.md` (C7, the mutation instrument clauses)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-469 (low, open → fixed)

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
  known nodeid that is either the whole line or followed by `" - "`. That is pytest's separator before
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

- `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py` → `22 passed`
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

Full suite (`uv run pytest`, bare):

```
1395 passed, 2 skipped, 32 xfailed, 1 warning in 302.78s (0:05:02)
```

The count includes tests from the other maker loop working in this tree.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| a mutation run attributes a kill to a spaced parametrize id (AT-469) | `test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id` | `failed_tests(out, set().union(*collected.values()))` → `failed_tests(out)` | KILLED (row 1) |
| the parser reads a spaced nodeid whole | `test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces` | `whole = [...]` → `whole = []` | KILLED (row 2) |
| when two known nodeids match, the longest wins | same test (`test_z[q]` vs `test_z[q] - r]`) | `max(whole, key=len)` → `min(whole, key=len)` | KILLED (row 3) |
| a known nodeid that is only a string prefix of an uncollected failing test does not claim it (no false KILLED) | same test (`test_y` vs `test_yz`) | `line.startswith(n + " - ")` → `line.startswith(n)` | KILLED (row 4) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at469-mutation-ids-with-spaces/mutations.json
KILLED  AT-469 reopens: the run ignores the collected nodeids, so a spaced id is cut and a kill reads SURVIVED  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id
    actually failed: tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id
KILLED  the parser stops consulting known nodeids at all  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
    actually failed: tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id, tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
KILLED  the shortest matching nodeid wins, so a nodeid that prefixes another steals its failure  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
    actually failed: tests/test_mutation_check.py::test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces
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
  would fall back to the old reading, which errs toward SURVIVED, never KILLED.
- **`scripts/mutation_check.py` is 330 lines.** C2's cap names `src/` and `tests/`, and doctor enforces
  exactly that, so `scripts/` is not capped. It was already 319 before this unit.
- **The at465-466 renamed ids stay renamed.** Readable space-free ids are fine on their own; nothing
  needs reverting.

## Status: ready-for-check
