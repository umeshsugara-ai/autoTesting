# Manifest — at481-report-path-fixed-at-plugin-load

**Unit:** AT-481 — mutation_check's report plugin read `MUTATION_REPORT` at `pytest_sessionfinish`, so a
test that reassigned the variable turned every kill into SURVIVED, and one that removed it made the run
refuse
**Contract:** `qa/contracts/core-invariants.md` (C7: the mutation instrument's verdict must be the tests',
not something a test under measurement can redirect)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-481 (low, open → fixed)

## What changed

- `scripts/mutation_check.py` `PLUGIN_SOURCE` — the plugin reads `os.environ["MUTATION_REPORT"]` once
  into module-level `_REPORT` when pytest imports it (`-p _mutation_report`, before collection), and
  `pytest_sessionfinish` opens `_REPORT`. This is the issue's `expected` option "capture the report path
  once when the plugin loads". Nothing else in the instrument changed.
- `tests/test_mutation_check.py` (appended, file now 298 lines, under the C2 cap) —
  `test_a_test_that_touches_the_report_variable_cannot_hide_a_kill`, parametrised `reassigned` /
  `removed`. A `tests/test_env.py` that runs before `tests/test_mod.py` reassigns or pops the variable;
  the default mutation must still be KILLED.

## How to verify (commands + expected)

- `uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py` → all pass
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at481-report-path-fixed-at-plugin-load/mutations.json` → `1/1 mutations killed`, exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py
...............................                                          [100%]
$ uv run pytest -q tests/test_mutation_sandbox.py
......                                                                   [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

Red before the fix (test written first, against the unchanged plugin):

```
FAILED tests/test_mutation_check.py::test_a_test_that_touches_the_report_variable_cannot_hide_a_kill[reassigned]
FAILED tests/test_mutation_check.py::test_a_test_that_touches_the_report_variable_cannot_hide_a_kill[removed]
```

`[reassigned]` failed on `assert result["killed"] is True` (no failures recorded); `[removed]` failed with
`MutationError` at `scripts/mutation_check.py:279` (baseline not green: KeyError in sessionfinish), both
exactly the issue's two measured shapes.

## Capability coverage (each new claim -> its isolating falsification)

| capability | check | falsifying edit (scripts/mutation_check.py, single hunk) | observed |
|---|---|---|---|
| a test that reassigns or removes `MUTATION_REPORT` cannot redirect or break the report | `test_a_test_that_touches_the_report_variable_cannot_hide_a_kill[reassigned,removed]` | `with open(_REPORT, ...)` → `with open(os.environ["MUTATION_REPORT"], ...)` | `KILLED ... actually failed: [reassigned], [removed]` · `1/1 mutations killed` (`qa/evidence/at481-report-path-fixed-at-plugin-load/mutations.out`) |

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/mutation_check.py`,
`tests/test_mutation_check.py`.

## Known limits (disclosed, not claimed)

- **A conftest or test that runs before the plugin imports** could still change the variable first. `-p`
  plugins load before conftest and collection, so no test in the tree under measurement can do so; a
  `PYTHONSTARTUP`/sitecustomize in the sandbox could, which is outside this issue.
- **A test can still write the report file itself** (the path is not secret: it is `cwd.parent`). That is
  the same trust boundary as any test deleting files; not addressed here.
- Sweep shard 3 (this tick) proposed a separate finding for the same file: `_run_pytest` has no
  `timeout=`. Out of scope here; it goes to the ledger through the sweep consolidation.

## Status: checked-PASS

Verdict: `qa/verdicts/at481-report-path-fixed-at-plugin-load.md` (Cycle checked: 1, commit 86d4bff, pushed). Ledger: AT-481 → fixed.
