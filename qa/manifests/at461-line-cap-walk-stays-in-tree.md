# Manifest — at461-line-cap-walk-stays-in-tree

**Unit:** AT-461 — doctor's line-cap walk follows Windows junctions (a loop crashes it, a foreign folder gets capped) and measures tool caches
**Contract:** `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-461 (low, open → fixed)

## Why

AT-419 widened `check_file_sizes` to every file under `src/` and `tests/` with `base.rglob("*")`. The
at419 checker then showed, in a throwaway copy, that on Python 3.11 `rglob` treats a junction as a plain
directory:

- A self-referencing junction under `tests/` made doctor raise `OSError [WinError 1921]`, a traceback
  instead of a violation.
- A junction from `tests/` to a folder outside the repo got that folder's 400-line file reported as ours.
- A gitignored tool cache under `tests/` (for example `.pytest_cache`) would be capped.

None of these exist in the repo today, so this is robustness, not a live failure.

## What changed

- `src/autotester/doctor.py:11` — `import os`.
- `src/autotester/doctor.py:49-65` — `_capped_files` now walks with `os.walk` and prunes, before
  descending, any directory that:
  - **resolves somewhere other than where it sits** (`realpath(dir)` ≠ `realpath(parent)/name`, compared
    with `normcase`). That excludes junctions and directory symlinks whether they loop or leave the tree.
    The comparison is against the parent's resolved path, so a repo opened through a junction is still
    walked (pinned by a test; an 8.3 short-name path is the same mechanism but has no test);
  - **starts with a dot** (tool caches such as `.pytest_cache`, `.ruff_cache`, `.mypy_cache`);
  - **is `__pycache__`.**

  `check_file_sizes`, the threshold and the message are unchanged. `_python_files`, which feeds the
  other doctor checks, is untouched.
- `tests/test_doctor.py` — three tests:
  - `test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree` (Windows only, skipped where
    `_winapi.CreateJunction` is absent): a self-loop junction and a junction to a foreign folder holding
    a 400-line file. Doctor must neither raise nor report it.
  - `test_the_line_cap_still_walks_a_repo_opened_through_a_junction` (Windows only): a repo reached
    through a junction alias still has its nested 301-line fixture reported, and only that one.
  - `test_the_line_cap_skips_tool_cache_directories`: a 301-line file under `tests/.pytest_cache/` is
    not reported.

## How to verify (commands + expected)

- `uv run pytest tests/test_doctor.py` → `12 passed`
- `uv run autotester doctor` → `doctor: clean`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at461-line-cap-walk-stays-in-tree/mutations.json` → `5/5 mutations killed`
- `uv run pytest` → green (below)

## Actual outputs (from maker's own run)

Test-first, before the `doctor.py` change:

```
E       OSError: [WinError 1921] The name of the file cannot be resolved by the system: '...\repo\tests\loop\back\back\back\...'
tests\test_doctor.py:83: AssertionError
FAILED tests/test_doctor.py::test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree
FAILED tests/test_doctor.py::test_the_line_cap_skips_tool_cache_directories
2 failed, 9 passed in 0.96s
```

After:

```
$ uv run pytest tests/test_doctor.py
12 passed in 0.47s
$ uv run autotester doctor
doctor: clean
$ uv run ruff check src tests scripts
All checks passed!
```

Full suite (`uv run pytest`, bare):

```
1366 passed, 2 skipped, 32 xfailed, 1 warning in 318.83s (0:05:18)
```

The count includes tests from the other maker loop working in this tree.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| the walk never enters a junction, looping or leaving the tree (AT-461) | `test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree` | drop the `realpath` comparison from the prune | KILLED (row 1) |
| tool caches under `src/`/`tests/` are not capped (AT-461) | `test_the_line_cap_skips_tool_cache_directories` | drop `not d.startswith(".")` | KILLED (row 2) |
| nested files are still measured (AT-419, re-pinned on the new walk) | `test_the_line_cap_reads_every_file_c2_names_not_only_python` | prune every directory (`dirnames[:] = [] and [...]`) | KILLED (row 3) |
| non-Python files are still measured (AT-419, re-pinned on the new walk) | same test | keep only `*.py` filenames | KILLED (row 4) |
| a repo opened through a junction is still walked (the prune compares with the RESOLVED parent) | `test_the_line_cap_still_walks_a_repo_opened_through_a_junction` | `here = os.path.realpath(dirpath)` → `os.path.abspath(dirpath)` | KILLED (row 5) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at461-line-cap-walk-stays-in-tree/mutations.json
KILLED  AT-461 reopens: the walk enters junctions, so a loop crashes doctor and a foreign folder is capped  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree
    actually failed: tests/test_doctor.py::test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree
KILLED  tool caches under tests/ are capped again  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_skips_tool_cache_directories
    actually failed: tests/test_doctor.py::test_the_line_cap_skips_tool_cache_directories
KILLED  AT-419 reopens: the walk stops recursing, so nested files are never measured  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
    actually failed: tests/test_doctor.py::test_long_file_is_flagged, tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python, tests/test_doctor.py::test_the_line_cap_still_walks_a_repo_opened_through_a_junction
KILLED  AT-419 reopens: the walk keeps only Python files, so a long .js or fixture passes  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python
    actually failed: tests/test_doctor.py::test_the_line_cap_reads_every_file_c2_names_not_only_python, tests/test_doctor.py::test_the_line_cap_still_walks_a_repo_opened_through_a_junction
KILLED  the prune compares against the unresolved parent, so a repo opened through a junction loses every subdirectory  (pytest exit 1)
    claims to kill : tests/test_doctor.py::test_the_line_cap_still_walks_a_repo_opened_through_a_junction
    actually failed: tests/test_doctor.py::test_the_line_cap_still_walks_a_repo_opened_through_a_junction

5/5 mutations killed
```

Each row is a single-hunk edit to `src/autotester/doctor.py` and fails its named test. Row 3 also
breaks the older `test_long_file_is_flagged`, whose file sits one level down: the same defect twice.

**One row covers two symptoms.** Row 1's test holds both the loop and the out-of-tree junction. That is
deliberate, because both are closed by the single `realpath` comparison, so no edit can break one and
not the other. The test fails on the loop's `OSError` first.

**AT-419's own spec no longer applies, and says so.** Its rows 1–2 anchored on `base.rglob("*")`, which
this unit replaces. Re-running it now refuses rather than passing:

```
$ uv run python scripts/mutation_check.py qa/evidence/at419-line-cap-every-file/mutations.json
MUTATION RUN INVALID: mutation 'AT-419 reopens: the cap reads only Python again, so a long .js or fixture passes': anchor matched 0 times in src/autotester/doctor.py (need exactly 1)
```

Rows 3–4 above re-pin those two AT-419 claims on the new code. AT-419's binary-skip and exact-cap rows
still anchor on unchanged lines (`check_file_sizes`), and both of their tests pass.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/doctor.py` (the design-rule CLI)
and `tests/test_doctor.py`.

## Known limits (disclosed, not claimed)

- **Untracked but not dot-named files are still capped.** For example, a stray 400-line `tests/out.log`
  would fail doctor. I kept the working-tree walk rather than switching to `git ls-files`. Doctor runs
  in test repos without git, and a large untracked file under `src/` or `tests/` is itself clutter worth
  a red. If the contract means "tracked files only", that is a C2 wording question for /checker.
- **A file-level symlink is still read** (only directories are pruned). None exist; a symlinked file
  cannot loop.
- **The junction test is Windows-only.** On POSIX it is skipped; the same `realpath` comparison covers
  directory symlinks there, but no test pins that on this host.

## Status: ready-for-check
