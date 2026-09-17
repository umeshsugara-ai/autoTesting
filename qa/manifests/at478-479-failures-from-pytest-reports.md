# Manifest — at478-479-failures-from-pytest-reports

**Unit:** AT-478 + AT-479 — the C7 mutation gate can still report a false KILLED: captured stdout can fake a sibling's failure, and a test that never ran can be credited
**Contract:** `qa/contracts/core-invariants.md` (C7 and its mutation-instrument clauses)
**Goal task:** none (issue-driven batch: both are the same root cause, reading failures out of text)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-478 (low, open → fixed) · AT-479 (low, open → fixed)

## Why

The at469 cycle-2 checker ran 19 real-pytest probes and closed AT-473. Two false-KILLED shapes remained,
both older than AT-469, and both came from one design choice: **failures were read by scanning the text
pytest prints.**

- **AT-478.** `^FAILED` matched every line of output, including a failing test's captured stdout. A
  failing test that printed `FAILED tests/test_p.py::test_ns[x] - boom` made that PASSING test read
  KILLED. AT-469 widened this to spaced ids.
- **AT-479.** A mutation that renames a parametrize id removes `test_gen[c]` from the run. Its
  replacement `test_gen[c] - Failed: q]` fails, and that summary line fit the BASELINE nodeid, which
  was credited with a kill it never took part in.

AT-469 and AT-473 were spent recovering where a nodeid ends inside that same text. Every patch to the
text reading closed one shape and left others, so this unit **stops reading text**. The checker's issue
row names exactly this direction: *"a structured source (--junitxml / a -p plugin recording rep.nodeid on
rep.failed), not from every line of output"*.

## What changed

- `scripts/mutation_check.py:51-68` — `REPORT_PLUGIN` / `PLUGIN_SOURCE`: a 15-line pytest plugin that
  records `report.nodeid` for every `call` phase with `report.failed`. At `pytest_sessionfinish` it
  writes the sorted list as JSON to `$MUTATION_REPORT`. The `FAILED` regex and the `re` import are gone.
- `scripts/mutation_check.py:188` (`_sandbox`) — writes the plugin to the sandbox's OWNED ROOT, the
  parent of the copied tree, so it is never inside the tree under test or the repo.
- `scripts/mutation_check.py:111-126` — `_run_pytest` loads it with `-p _mutation_report` (module found
  via `PYTHONPATH` = the owned root, prepended), points `MUTATION_REPORT` at
  `<owned_root>/mutation-report.json`, and deletes any previous report before each run.
- `scripts/mutation_check.py:155-169` — `failed_tests(cwd)` reads that report, replacing
  `failed_tests(output, known)`. No readable report yields no failures, which can only read SURVIVED.
- `scripts/mutation_check.py:298` — the mutation loop uses it. `is_kill`, exit-code handling and every
  refusal are unchanged.
- `tests/test_mutation_check.py`:
  - **new** `test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill` (AT-478, real pytest)
  - **new** `test_a_named_test_that_did_not_run_under_the_mutation_is_never_killed` (AT-479, real pytest)
  - **new** `test_a_named_test_that_errors_in_setup_is_not_a_kill`. Only a failed CALL counts, as `ERROR`
    lines never did before.
  - **replaced** `test_failed_tests_reads_names_out_of_pytest_output` →
    `test_failed_tests_reads_pytests_own_report_and_nothing_else`. The AT-320 distinct-nodeids property
    and a spaced/bracketed nodeid are both kept; a missing report must be the empty set.
  - **removed** `test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces`, a unit test of
    the text parser that no longer exists. Its behaviour stays pinned END TO END by the kept tests
    `test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id` (AT-469) and
    `test_a_passing_sibling_is_never_credited_with_another_tests_failure` (AT-473).

## How to verify (commands + expected)

- `uv run pytest tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py` → all pass (34 before the setup-error test, 35 with it)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at478-479-failures-from-pytest-reports/mutations.json` → `4/4 mutations killed`
- Older specs re-run under the new instrument, with results identical to their recorded runs:
  `at465-466-unreadable-narration-keeps-its-cause` (5/5), `at216-unreadable-transcript-is-not-silence`
  (2/2), `at461-line-cap-walk-stays-in-tree` (5/5)
- `uv run pytest` → green (below)

## Actual outputs (from maker's own run)

Test-first. With `mutation_check.py` at HEAD, both new end-to-end tests fail by reporting the false KILLED:

```
tests\test_mutation_check.py:267: AssertionError
E       AssertionError: {'name': 'threshold broken', 'killed': True, 'exit': 1, 'expected': ['tests/test_gen.py::test_gen[c]'], ...}
tests\test_mutation_check.py:285: AssertionError
FAILED tests/test_mutation_check.py::test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill
FAILED tests/test_mutation_check.py::test_a_named_test_that_did_not_run_under_the_mutation_is_never_killed
2 failed, 17 deselected, 1 warning in 28.43s
```

After, the whole harness suite, before the setup-error test was added:

```
34 passed in 139.69s (0:02:19)
```

and the setup-error test on its own: `1 passed`.

Older specs re-run under the NEW instrument, results identical to their recorded runs:

```
== at465-466-unreadable-narration-keeps-its-cause
KILLED  AT-466 reopens: an unreadable sidecar discards its cause again  (pytest exit 1)
KILLED  AT-466 reopens: a sidecar with no segments list ({}) loads as silence  (pytest exit 1)
KILLED  media prep stops being best-effort: a malformed sidecar raises  (pytest exit 1)
KILLED  ingest stops being best-effort: a malformed sidecar stops an ingest  (pytest exit 1)
KILLED  AT-465 reopens: prep prints an unreadable sidecar as 0 narration segments  (pytest exit 1)
5/5 mutations killed
== at216-unreadable-transcript-is-not-silence
KILLED  AT-216 reopens: a malformed sidecar is swallowed into None, the same as no transcript  (pytest exit 1)
KILLED  the chunk prompt asserts silence for an unreadable transcript (the AT-134 defect on the analyze path)  (pytest exit 1)
2/2 mutations killed
== at461-line-cap-walk-stays-in-tree
KILLED  AT-461 reopens: the walk enters junctions, so a loop crashes doctor and a foreign folder is capped  (pytest exit 1)
KILLED  tool caches under tests/ are capped again  (pytest exit 1)
KILLED  AT-419 reopens: the walk stops recursing, so nested files are never measured  (pytest exit 1)
KILLED  AT-419 reopens: the walk keeps only Python files, so a long .js or fixture passes  (pytest exit 1)
KILLED  the prune compares against the unresolved parent, so a repo opened through a junction loses every subdirectory  (pytest exit 1)
5/5 mutations killed
```

Full suite (`uv run pytest`, bare):

```
1413 passed, 2 skipped, 32 xfailed, 1 warning in 446.89s (0:07:26)
```

The count includes the other maker loop's tests. `ruff`: `All checks passed!`. `doctor`: `doctor: clean`.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| a real kill is still attributed, through the report | `test_a_real_mutation_is_killed_and_attributed` | the plugin records nothing (`if False:`) | KILLED (row 1) |
| printed output and a renamed test can never produce a kill (AT-478, AT-479) | `test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill`, `test_a_named_test_that_did_not_run_under_the_mutation_is_never_killed` | also trust `FAILED ` lines scraped from the text output | KILLED (row 2) |
| only a failed call phase counts, not a setup error | `test_a_named_test_that_errors_in_setup_is_not_a_kill` | `report.when == "call" and report.failed` → `report.failed` | KILLED (row 3) |
| no report means no failures, not a crash | `test_failed_tests_reads_pytests_own_report_and_nothing_else` | `return set()` → `raise` | KILLED (row 4) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at478-479-failures-from-pytest-reports/mutations.json
KILLED  the report plugin records no failure, so a real kill reads SURVIVED  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_real_mutation_is_killed_and_attributed
    actually failed: tests/test_mutation_check.py::test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill, tests/test_mutation_check.py::test_a_kills_entry_may_be_the_full_nodeid_the_guard_asks_for, tests/test_mutation_check.py::test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id, tests/test_mutation_check.py::test_a_real_mutation_is_killed_and_attributed, tests/test_mutation_check.py::test_a_suite_split_across_files_is_still_one_suite, tests/test_mutation_check.py::test_it_refuses_when_the_named_test_survives_but_another_fails, tests/test_mutation_check.py::test_the_spec_round_trips_through_json, tests/test_mutation_check_judgement.py::test_an_interrupted_run_with_real_failures_is_not_a_kill
KILLED  AT-478/479 reopen: summary lines scraped from the text output are trusted again  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill, tests/test_mutation_check.py::test_a_named_test_that_did_not_run_under_the_mutation_is_never_killed
    actually failed: tests/test_mutation_check.py::test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill, tests/test_mutation_check.py::test_a_named_test_that_did_not_run_under_the_mutation_is_never_killed
KILLED  a setup ERROR is counted as the named test noticing the mutation  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_named_test_that_errors_in_setup_is_not_a_kill
    actually failed: tests/test_mutation_check.py::test_a_named_test_that_errors_in_setup_is_not_a_kill
KILLED  a missing report raises instead of meaning no failures  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_failed_tests_reads_pytests_own_report_and_nothing_else
    actually failed: tests/test_mutation_check.py::test_failed_tests_reads_pytests_own_report_and_nothing_else

4/4 mutations killed
```

Each cell is a single-hunk edit to `scripts/mutation_check.py`. Rows 1 and 3 edit the plugin SOURCE
string. That works because the harness's own tests run `check()` from the mutated sandbox copy, which
writes its own (mutated) plugin for the nested run.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `scripts/mutation_check.py` (a verification CLI)
and `tests/test_mutation_check.py`.

## Known limits (disclosed, not claimed)

- **A run that dies before `pytest_sessionfinish` writes no report**, so it reads as no failures, i.e.
  SURVIVED. Examples are a hard crash of the interpreter, or `os._exit` inside a test. That is the
  fail-closed direction, but a genuine kill in such a run is lost. An ordinary interrupt (exit 2) still
  reaches session finish: `test_an_interrupted_run_with_real_failures_is_not_a_kill` passes and still
  sees the real failure.
- **The report names only CALL failures.** An xfail(strict) that unexpectedly passes is a failed call
  in pytest's report, so it still counts, as it did under the text reader (the at469 checker's probe).
  A teardown error does not count.
- **`-p _mutation_report` puts one module name on the nested run's path.** A project that ships its own
  `_mutation_report` module would shadow or be shadowed. None exists here.
- **`collected_tests` still reads `--collect-only` TEXT.** That is how `kills` labels are validated
  before anything is mutated. It is unchanged by this unit and not a kill decision.

## Status: ready-for-check
