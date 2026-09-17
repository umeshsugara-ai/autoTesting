# Manifest — at419-line-cap-every-file

**Unit:** AT-419 — `autotester doctor` measures only `*.py`, so C2's 300-line cap was never enforced on the other files in `src/` and `tests/`
**Contract:** `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-419 (medium, open → fixed)

## Why

C2 says "No file in `src/` or `tests/` exceeds 300 lines". `doctor.check_file_sizes` read only
`src/**/*.py` plus top-level `tests/*.py`. The at379 cycle-3 manifest records `visual_order.js` at 316
lines while `uv run autotester doctor` printed `doctor: clean`. The rule and its enforcer disagreed, and
the file the loop most often grows (`visual_order.js`) sat outside the enforcer.

I chose the resolution that makes the enforcer match the written rule, rather than weakening C2 to
"no Python file". Maker never edits contracts, and the cap exists for exactly the files an agent has
to hold in context.

## What changed

- `src/autotester/doctor.py:48-56` — new `_capped_files(root)`: every regular file under `src/` and
  `tests/`, recursively, excluding `.venv` and `__pycache__`.
- `src/autotester/doctor.py:59-69` — `check_file_sizes` iterates `_capped_files` and skips a file that
  is not UTF-8 text (`UnicodeDecodeError` → no lines to count). The threshold and message are unchanged.
  `_python_files` is untouched and still feeds the function-size, drift-name and duplicate-concept checks.
- `tests/test_doctor.py` — two tests:
  - `test_the_line_cap_reads_every_file_c2_names_not_only_python`: a 301-line `src/autotester/browser.js`
    and a 301-line `tests/fixtures/site/page.html` are both flagged, and nothing else is.
  - `test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files`: a 300-line `.js` passes, and a
    non-UTF-8 binary in `tests/` is neither flagged nor a crash.

## How to verify (commands + expected)

- `uv run pytest tests/test_doctor.py` → `9 passed`
- `uv run autotester doctor` → `doctor: clean` (the repo's largest non-Python file is `visual_order.js`
  at exactly 300 lines, which the cap allows)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at419-line-cap-every-file/mutations.json` → `4/4 mutations killed`
- `uv run pytest` → green (suite output below)

## Actual outputs (from maker's own run)

Test-first: before the `doctor.py` change, the new test failed on its own assertion:

```
E         'src/autotester/browser.js'
E         'tests/fixtures/site/page.html'
tests\test_doctor.py:41: AssertionError
FAILED tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
1 failed, 8 passed in 0.42s
```

After:

```
$ uv run pytest tests/test_doctor.py
9 passed in 0.20s
$ uv run autotester doctor
doctor: clean
$ uv run ruff check src tests scripts
All checks passed!
```

Measured before building, so the widened rule does not turn the repo red:

```
$ find src tests -type f ! -name "*.py" ! -path "*__pycache__*" | sed 's/.*\.//' | sort | uniq -c
     37 html
      3 js
      1 json
      6 md
largest: 300 src/autotester/browser/visual_order.js · 150 src/autotester/browser/enumerate.js · 68 src/autotester/prompts/video_issues_v1.md
```

Full suite (`uv run pytest`, bare):

```
1346 passed, 2 skipped, 32 xfailed, 1 warning in 325.26s (0:05:25)
```

The count includes tests from the other maker loop working in this tree.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| a non-Python file over the cap is flagged (AT-419) | `test_the_line_cap_reads_every_file_c2_names_not_only_python` | `base.rglob("*")` → `base.rglob("*.py")` | KILLED (row 1) |
| files below the top level of `src/` and `tests/` are measured | same test (`tests/fixtures/site/page.html`) | `base.rglob("*")` → `base.glob("*")` | KILLED (row 2) |
| a binary file is skipped, not a crash | `test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files` | `continue` → `raise` | KILLED (row 3) |
| exactly 300 lines is allowed | same test (`at_cap.js`) | `lines > MAX_FILE_LINES` → `lines >= MAX_FILE_LINES` | KILLED (row 4) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at419-line-cap-every-file/mutations.json
KILLED  AT-419 reopens: the cap reads only Python again, so a long .js or fixture passes  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
    actually failed: tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
KILLED  the cap stops recursing, so files below src/ or tests/ top level are never measured  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
    actually failed: tests/test_doctor.py::test_long_file_is_flagged, tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
KILLED  a binary file crashes doctor instead of being skipped  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files
    actually failed: tests/test_doctor.py::test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files
KILLED  off by one: a file of exactly 300 lines is flagged  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files
    actually failed: tests/test_doctor.py::test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files

4/4 mutations killed
```

Every row is a single-hunk edit to `src/autotester/doctor.py`, and each fails its named test. Row 2 also breaks the older `test_long_file_is_flagged` (its file sits one level down), which is the same defect seen twice, not a different one.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/doctor.py` (the CLI design-rule
checker) and `tests/test_doctor.py`. Nothing either file touches is rendered by a page.

## Known limits (disclosed, not claimed)

- **The cap now counts test fixtures.** A future fixture over 300 lines (for example a recorded HTML
  page) will fail doctor. That is what C2's text says; if fixtures should be exempt, that is a contract
  amendment for /checker, not a doctor change.
- **"Text" means "decodes as UTF-8".** A text file in another encoding is skipped rather than measured.
  None exist in the repo today.
- **AT-403** (six `*.py` modules at 290–300 lines) is unchanged by this unit.

## Status: ready-for-check
