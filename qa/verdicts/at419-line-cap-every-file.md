# Verdict — at419-line-cap-every-file

**Checker:** /checker Mode A (fresh subagent, bound to `D:/autoTesting`)
**Date:** 2026-09-17
**Manifest:** `qa/manifests/at419-line-cap-every-file.md` (Status: ready-for-check, Fix cycle: 1)
**Unit commit:** `6393776` fix(AT-419)
**Cycle checked: 1**

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (C2, C7; C10 also observed to hold), 0/0 invariants (contract declares none)
FAILURES: none
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: src/autotester/doctor.py, tests/test_doctor.py, qa/manifests/…, qa/evidence/at419-line-cap-every-file/* — CLI design-rule checker only, nothing rendered)
ISSUES-WRITTEN: AT-461 (low); AT-419 open -> fixed
EXPLANATION: doctor's file-size rule now walks every regular file under src/ and tests/ recursively, which matches C2's written text; the real repo stays `doctor: clean` (largest non-Python file visual_order.js = 300 lines, allowed) and the check runs in ~0.07 s. All four falsifying edits were reproduced in a throwaway copy, each green before and red on the assertion it is named for. Edge probing found only pathological junction/untracked-file behaviour, filed as low AT-461, not charged.
```

## What I re-ran (my own runs, not the maker's pasted output)

| command | result |
|---|---|
| `uv run pytest tests/test_doctor.py -q` (bound tree) | 9 passed |
| `uv run autotester doctor` (bound tree) | `doctor: clean`, exit 0 (8.1 s wall incl. `uv` start-up; `doctor.run` alone 0.63–0.78 s, `check_file_sizes` 0.06–0.09 s) |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `find src tests -type f ! -name '*.py' … wc -l` | max 300 `src/autotester/browser/visual_order.js`, 150 `enumerate.js`, 68 `video_issues_v1.md` — manifest's measurement confirmed |
| `scripts/mutation_check.py qa/evidence/at419-line-cap-every-file/mutations.json` (in the copy) | `4/4 mutations killed`, each with the claimed test in its FAILED list |
| full `pytest -q`, bound tree, run 1 | aborted mid-run (no summary) while the other maker loop was editing the shared tree |
| full `pytest -q`, bound tree, run 2 | exactly 1 failure: `test_cli_harness_safety::test_running_every_command_leaves_the_repository_untouched` — "rewrote `src/autotester/schema/enums.py`". That file is the other loop's uncommitted work (`git status`: ` M`, mtime 07:15 during my run); not a path of this unit |
| full `pytest -q` on `git archive 6393776` (isolated, imports confirmed from the archive) | exactly 1 failure: `test_ui_sources::test_uploaded_recordings_are_gitignored` — `git check-ignore` exit 128 "not a git repository" (the archive has no .git). That test passed in bound-tree run 2 |

Taken together: every test passes against the unit's commit; the two single failures are each an artefact of the environment they ran in (concurrent edit / no .git), and each passes in the other environment.

## Criteria

- **C2 — PASS.** "No file in `src/` or `tests/` exceeds 300 lines" is now what `check_file_sizes` measures (`doctor.py:48-69`: `rglob("*")` over both roots, regular files, `.venv`/`__pycache__` excluded, non-UTF-8 skipped). `uv run autotester doctor` exits 0 on the real repo. `_python_files` is unchanged and still feeds function-size, drift-filename and duplicate-concept checks (diff confirms). The old `tests/*.py` top-level glob is strictly subsumed. No documented exemption to the line cap exists anywhere in `qa/contracts/`, `docs/ARCHITECTURE.md`, `CLAUDE.md` (grep), so the widened rule contradicts nothing. New doctor.py is 1 file, functions < 50 lines.
- **C7 — PASS.** Tests re-runnable by anyone; the mutation harness asserts baseline, anchor-matched-once and attribution to the named test, and I reproduced all four rows independently (below). The TDD red pasted in the manifest is consistent with row 1's red.
- **C10 (observed)** — `git show --stat 6393776` carries only doctor.py, test_doctor.py, the manifest and its evidence.

## Capability coverage (step 4b)

Copy: working tree tarred (excluding `.git`, `.venv`, `projects`, `qa/evidence` except this unit's) to `scratchpad/copy` outside the bound root; `PYTHONPATH=<copy>/src` with the repo venv interpreter; `autotester.doctor.__file__` printed from the copy. Every falsifying-edit cell is a single-hunk edit to `src/autotester/doctor.py`, a file named in "What changed" — admissible. For each row my script asserted the anchor occurs exactly once and the file changed, ran the named test (+ `test_long_file_is_flagged`) green, applied, re-ran, restored (restore verified byte-identical).

| row | before (copy) | after | assertion that fired |
|---|---|---|---|
| 1 `rglob("*")`→`rglob("*.py")` | exit 0 | exit 1 | `assert flagged == {"src/autotester/browser.js", "tests/fixtures/site/page.html"}` — `set()` — the named AT-419 test |
| 2 `rglob("*")`→`glob("*")` | exit 0 | exit 1 | same assertion (`set()`), plus `test_long_file_is_flagged` — the recursion claim, isolated to the nested fixture/module |
| 3 `continue`→`raise` | exit 0 | exit 1 | `UnicodeDecodeError: … byte 0x89` inside `doctor.run` in `test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files` — the crash the row names |
| 4 `>`→`>=` | exit 0 | exit 1 | `assert not any(v.rule == "file-too-long" …)` → `not True` in the same test — the 300-line allowance |

Trap check: no check reads live state or asserts a state the bug also produces (row 1's set equality distinguishes "nothing flagged" from "both flagged").

## Attacks beyond the manifest (throwaway copy)

| probe | outcome |
|---|---|
| UTF-8 BOM + CRLF, 300 / 301 lines | 300 allowed, 301 flagged — correct |
| CR-only line endings, 301 | flagged — correct |
| Latin-1 file, 400 lines | skipped (disclosed limit); real repo has **zero** non-UTF-8 files under src/tests (verified by decoding every file) |
| UTF-16 file, 400 lines | skipped (same disclosed limit) |
| 200 MB binary under tests/ | skipped, 0.39 s, no crash |
| directory symlink to outside | not followed |
| **junction loop** under tests/ | `OSError [WinError 1921]` traceback out of doctor → AT-461 (low) |
| **junction to a dir outside the copy** | outside 400-line file reported as `tests\ext\big.txt` → AT-461 (low) |
| `.pytest_cache`/tool dirs under tests/ | none present in the real tree after many runs; `.gitignore` ignores them but doctor walks the working tree, so one would count → folded into AT-461 |
| build backend | `uv_build`, so no `*.egg-info` under src/ |

## Known limits — honesty

Accurate: fixtures are now capped (as C2's text says), "text = decodes as UTF-8" (none otherwise today — verified), AT-403 untouched. Not disclosed: junction following and working-tree (not git-tracked) scope — recorded as AT-461; neither exists in the repo, and the src/ half pre-dates this unit.
