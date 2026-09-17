# Verdict — at461-line-cap-walk-stays-in-tree

**Checker:** /checker Mode A (fresh subagent, bound to `D:/autoTesting`)
**Date:** 2026-09-17
**Cycle checked: 1**
**Contract:** `qa/contracts/core-invariants.md` — C2, C7
**Artifact:** commit `8edaf17` (`src/autotester/doctor.py`, `tests/test_doctor.py`); both files byte-identical between HEAD and the working tree at check time.

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met, 0/0 invariants in scope hold
FAILURES: none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: src/autotester/doctor.py, tests/test_doctor.py, qa/manifests/…, qa/evidence/at461…/mutations.* — doctor CLI only, confirmed from `git show --stat 8edaf17`)
ISSUES-WRITTEN: AT-464 (low); AT-461 open -> fixed
EXPLANATION: The os.walk + resolved-parent realpath prune closes AT-461: a junction loop, an out-of-tree junction and a directory symlink are neither followed nor crash doctor, while a repo reached through a junction, a SUBST drive, a lower-case drive letter or a relative root is still walked. All five falsifying edits reproduce in a throwaway copy on their named tests, and AT-419's surviving capabilities (non-Python files, nesting, binary skip, exact 300/301 cap) hold. AT-464 records a manifest inaccuracy and two undisclosed limits, none present in the repo.
```

## Step 3 — verify commands re-run by the checker (bound tree)

| command | result |
|---|---|
| `uv run pytest tests/test_doctor.py` | `12 passed in 0.24s` |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run pytest -q -p no:cacheprovider` (full suite, shared tree incl. the other loop's uncommitted work) | exit code 0 (summary line was cut by my `tail`; exit 0 = no failures) |
| Python | 3.11.15 |

`mutation_check.py` was not used in the bound tree; the rows were reproduced by my own harness in a copy (below).

## Step 4 — criteria

- **C2 (doctor exits 0; cap every file in src/ and tests/)** — MET. Doctor clean on the real repo (3.96 s for `doctor.run`, 0.01 s for `_capped_files`, 293 files walked). `git ls-files src tests` contains no dot-named path, so the new dot prune excludes nothing real today.
- **C7 (independent verification, sabotage asserts it was applied)** — MET. Every mutation anchor asserted to match exactly once and the file asserted changed before the run; each named test observed green in the copy before the edit and red after, on its own assertion.

## Step 4b — capability coverage (throwaway copy)

Copy: working tree minus `.git/.venv/.work/projects/qa/evidence` at
`%TEMP%/claude/.../scratchpad/copy`; `src` diffed identical to the bound tree; import origin printed as
`...\scratchpad\copy\src\autotester\doctor.py` (PYTHONPATH=copy/src). All five cells are single-hunk edits
to `src/autotester/doctor.py`, which is named in "What changed" — admissible.

| row | before (copy) | anchor | after | assertion that fired |
|---|---|---|---|---|
| 1 drop realpath prune | 12 passed | 1 | FAILED `test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree` only | `assert not any(file-too-long)` — the out-of-tree file (see AT-464: NOT an OSError) |
| 2 drop dot prune | 12 passed | 1 | FAILED `test_the_line_cap_skips_tool_cache_directories` only | `assert not any(...)` — the cache file |
| 3 `dirnames[:] = [] and [` | 12 passed | 1 | FAILED `test_long_file_is_flagged`, `test_the_line_cap_reads_every_file_c2_names_not_only_python`, `..._through_a_junction` | named test: `assert set() == {'src/autotester/browser.js','tests/fixtures/site/page.html'}` |
| 4 keep only `.py` | 12 passed | 1 | FAILED named test + `..._through_a_junction` | named test: same set assertion, non-Python files missing |
| 5 `realpath`→`abspath` for `here` | 12 passed | 1 | FAILED `test_the_line_cap_still_walks_a_repo_opened_through_a_junction` only | `assert [] == ['tests/fixtures/big.html']` |

Restored copy: 12 passed.

## Attacks beyond the manifest (copy's doctor module, scratch fixtures)

| probe | result |
|---|---|
| directory symlinks (host permitted): link to foreign folder + link back to `tests` | only `tests/real/big.txt` reported — not followed |
| junction to a sibling INSIDE tests/ and one from src/ to tests/fixtures | target reported exactly once via its real location — no false negative |
| leading-dot FILE `tests/.eslintrc` (301 lines) | reported (files are not pruned) |
| dot-named content DIR `tests/fixtures/.well-known/big.txt` | **silently skipped** — undisclosed (AT-464) |
| `src/.venv/x.py`, `src/autotester/__pycache__/x.txt` | skipped (intended) |
| drive letter lower vs upper case, relative root `.` | both report the nested 301-line file |
| SUBST drive (`Q:` mapped to a scratch repo, removed afterwards), `Q:\` and `q:/` | nested file reported — walked |
| 8.3 short path | NOT TESTABLE: `GetShortPathNameW` returned no short name on D: and none on the scratch path (8.3 generation off); disclosed as untested in the manifest too |
| loop junction + exact cap + binary | `at300.txt` not reported, `at301.js` reported, binary skipped, loop not followed, 0.019 s |
| `tests/` itself a junction to a folder outside the repo | foreign file **reported** — os.walk follows the top; undisclosed (AT-464) |
| mutation row 1 applied, loop-only junction holding a 301-line file | no raise; **64 duplicate violations** for one file (AT-464: test loop half does not pin this) |

## Known limits — honesty

The three disclosed limits are accurate. Incomplete: the dot-directory false negative and the junctioned
base directory are not listed, and the prose "The test fails on the loop's OSError first" is false for the
os.walk mutation (it fails on the out-of-tree assertion). Recorded as AT-464 (low); not charged, as no such
path exists in the repo and the capability row is still isolated by its named test.

## Step 5 — issues

AT-461: the three symptoms it names (loop crash, foreign folder capped, tool cache capped) are closed —
status `open -> fixed` (fixed_date 2026-09-17). Goal task: none, no /goal close.
