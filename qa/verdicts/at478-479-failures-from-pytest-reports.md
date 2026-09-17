# Verdict — at478-479-failures-from-pytest-reports

**Date:** 2026-09-17
**Checker:** /checker Mode A (fresh subagent, bound to `d:/autoTesting`)
**Manifest:** `qa/manifests/at478-479-failures-from-pytest-reports.md` (Fix cycle: 1, Status: ready-for-check)
**Cycle checked: 1**
**Unit commit:** 07428a7 (HEAD ad68453 only stamps `qa/.last-tick`; `git diff --quiet 07428a7 -- scripts/mutation_check.py tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py` is clean)

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C7 attribution clause + mutation duty), invariants hold (doctor clean)
FAILURES (if any):
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: not-applicable (scripts/mutation_check.py, tests/test_mutation_check.py, qa/evidence/at478-479-failures-from-pytest-reports/, qa/manifests/at478-479-* — a verification CLI and its tests; confirmed from `git show 07428a7 --stat`)
ISSUES-WRITTEN: AT-481 (low, fail-closed, not charged); AT-478 and AT-479 open -> fixed
EXPLANATION: The report plugin removes both false-KILLED shapes: across the at469 19-probe set HEAD answers 19/19 correctly while the parent instrument false-KILLs P4, P5, P5b and loses the P1/P2 real kills, and 14 further probes (teardown, xfail-strict, skip, native and unittest subtests, nested classes, a hook-defining conftest, no-ini rootdir, chdir, PYTHONPATH, xdist -n 2/-n 3, two concurrent runs) found no false KILLED and no newly lost kill except where a test tampers with the harness's own MUTATION_REPORT variable (silent SURVIVED) or os._exit (disclosed, and equally lost by the parent). Existing specs at438/at465-466/at355/at216/at461 re-run with identical KILLED rows; the only failure-list deltas are stale recordings, confirmed by running the parent instrument on the same code. Question for the maker, not a finding: the plugin trusts whatever JSON sits at MUTATION_REPORT at session end, so a test that deliberately writes that file could forge a kill — adversarial, not accidental, unlike the printed-line shape this unit closes.
```

## What I re-ran (my own runs)

| command | result |
|---|---|
| `uv run pytest tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py -p no:cacheprovider` | `35 passed in 214.89s`, exit 0 — matches |
| `uv run ruff check src tests scripts` | `All checks passed!` — matches |
| `uv run autotester doctor` | `doctor: clean` — matches |
| `uv run python scripts/mutation_check.py qa/evidence/at478-479-failures-from-pytest-reports/mutations.json` | `4/4 mutations killed`, exit 0; every row's claims/actually-failed lines identical to the manifest |
| older specs at465-466 / at216 / at461 (manifest) + at438 / at355 (dispatch) | 5/5, 2/2, 5/5, 9/9, 5/5 KILLED — identical KILLED rows (detail below) |
| `uv run pytest -p no:cacheprovider -rfE` (full) | `1415 passed, 2 skipped, 32 xfailed, 1 warning in 786.85s`, exit 0 |

## Capability coverage (4b) — throwaway copies

A fresh copy per row of `scripts/ tests/ src/ pyproject.toml` in the session scratchpad (outside the bound root); named check(s) run from the copy's cwd with the root venv's python, `-o addopts= -p no:cacheprovider`. `import mutation_check` from each copy printed `...scratchpad\rowN\scripts\mutation_check.py` (the copy's), and the test file inserts its own `parents[1]/scripts`. Every cell is a single-hunk edit to `scripts/mutation_check.py`, a file named in "What changed" -> admissible, none executed as a command. Anchor asserted to match exactly once; file asserted changed.

| row | before (copy) | after edit | assertion that fired |
|---|---|---|---|
| 1 `if report.when == "call" and report.failed:` -> `if False:` (plugin source) | 1 passed | exit 1 | `assert result["killed"] is True` — `assert False is True` in `test_a_real_mutation_is_killed_and_attributed` |
| 2 `failures = failed_tests(work)` -> `... \| {ln.split()[1] ... startswith("FAILED ")}` | 2 passed | exit 1, 2 failed | both new e2e tests: `assert result["killed"] is False` — `'killed': True, 'expected': ['tests/test_p.py::test_ns[x]']` (AT-478) and `'expected': ['tests/test_gen.py::test_gen[c]']` (AT-479) |
| 3 `report.when == "call" and report.failed` -> `report.failed` | 1 passed | exit 1 | `assert result["killed"] is False` — `'killed': True, 'expected': ['tests/test_setup.py::test_uses_fixture']` |
| 4 `return set()` -> `raise` | 1 passed | exit 1 | `test_mutation_check.py:118` `assert failed_tests(work) == set()` -> `FileNotFoundError ... mutation-report.json` |

All four die for the assertion they are named for; none is an import or collection failure. State-trap check: the AT-478/479 checks assert `killed is False` on runs where the named test passed / never ran, a state the text reader demonstrably does not produce (row 2).

## Adversarial probes — real pytest 9.1.1, `check()` on scratch repos, two instruments

Instruments: `07428a7:scripts/mutation_check.py` (head) and `07428a7^` (parent), each extracted to the scratchpad and loaded by path (`__file__` asserted). Scratch repo: `scripts/mod.py` with `FAIL = {}` / `GEN = ["c"]`, mutated per probe. Truth is about the NAMED test.

### at469 cycle-2 probe set (19 shapes)

| probe | truth | head | parent |
|---|---|---|---|
| P1 `[a]` fails `boom] - z`; kills sibling / kills `[a]` | not / KILLED | not / KILLED | not / **lost** |
| P2 sibling fails `z`; kills `[a]` / kills sibling | not / KILLED | not / KILLED | not / **lost** |
| P3a `[b]` fails; kills middle / last | not / not | not / not | not / not |
| P3b middle fails; kills `[b]` / last | not / not | not / not | not / not |
| P3c last fails; kills `[b]` / middle | not / not | not / not | not / not |
| P3d `[b]` fails `X]`; kills middle | not | not | not |
| P3e `[b]` fails `q`; kills `[b]` | KILLED | KILLED | KILLED |
| P3f middle fails `q`; kills `[b]` | not | not | not |
| P4 id renamed to `c] - Failed: q` (AT-479) | not | not | **KILLED** |
| P4b id renamed to `c d` | not | not | not |
| P5 printer fakes `test_sp[x y]` (AT-478) | not | not | **KILLED** |
| P5b printer fakes `test_ns[x]` (AT-478) | not | not | **KILLED** |
| P6 `test_dup[m n]` fails, prints own line twice | KILLED | KILLED | KILLED |
| P6b printer prints amb line twice, `[a]` fails; kills sibling | not | not | not |

Parent column reproduces the at469 cycle-2 ee98728 column exactly. Head: 19/19 correct, including the two fail-closed losses the parent disclosed.

### New shapes (each run with and without a root `conftest.py` defining its own `pytest_runtest_logreport` + `pytest_sessionfinish`; identical results)

| probe | truth | head | parent |
|---|---|---|---|
| N1 named test fails in call AND errors in teardown | KILLED | KILLED | KILLED |
| N1b teardown-only error | not | not | not |
| N2 xfail(strict) XPASS | KILLED (pytest FAILED) | KILLED | KILLED |
| N3 test skipped by the mutation | not | not (exit 0) | not |
| N4 pytest-9 native `subtests` failure | KILLED | KILLED | KILLED |
| N4b `unittest.TestCase.subTest` failure (`TestUni::test_u`) | KILLED | KILLED | **lost** |
| N5 nested class `tests/sub/test_cls.py::TestOuter::TestInner::test_n[p q]` fails; kills it | KILLED | KILLED | KILLED |
| N5b same run; kills passing `[r]` | not | not | not |
| no `pyproject.toml` (rootdir from args): P3e, N5, N5b | K / K / not | K / K / not | K / K / not |
| E1 an earlier test `os.chdir`s away without restoring | KILLED | KILLED | KILLED |
| E4 an earlier test sets `PYTHONPATH` | KILLED | KILLED | KILLED |
| **E2 an earlier test reassigns `os.environ["MUTATION_REPORT"]`** | KILLED | **not (silent)** | KILLED |
| **E3 an earlier test pops `MUTATION_REPORT`** | KILLED | run refused: `baseline is NOT green (pytest exit 1)` (KeyError in sessionfinish) | KILLED |
| E5 named test fails, then a later test `os._exit(1)` | KILLED | not | not |

- **xdist** (`uv run --no-project --with pytest==9.1.1 --with pytest-xdist`, xdist 3.8.0, confirmed `created: 2/2 workers`): with xdist merely installed, and with `PYTEST_ADDOPTS="-n 2"`, head answers P1x2, P3e, P4, P5, N1, N1b correctly (parent: lost P1, false-KILLED P4/P5). `-p _mutation_report` does not conflict. Six failures spread over `-n 3`, three runs: the report held all six every time (controller aggregates worker reports).
- **Concurrency:** two head `check()` runs in parallel processes, each on its own repo: identical correct results; report paths are per `mkdtemp` root, no collision.
- **Repo containment / cleanup:** no `_mutation_report*` or `mutation-report.json` anywhere in the bound tree after all runs. After every run finished, the only `mutation-check-*` dirs in `%TEMP%` were two predating this check (07:14, 11:00); none from ~40 of my `check()` calls, so `_discard` removes plugin, `__pycache__` and report with the sandbox.

## Existing specs re-run (parametrized kills)

| spec | recorded | re-run now (head) |
|---|---|---|
| at438-display-contents | 9/9 KILLED | 9/9 KILLED, identical KILLED rows |
| at465-466-unreadable-narration-keeps-its-cause | 5/5 | 5/5, identical KILLED rows |
| at355-refuse-bidi-overrides | 5/5 | 5/5, claims/actually-failed lines byte-identical |
| at216-unreadable-transcript-is-not-silence | 2/2 | 2/2 |
| at461-line-cap-walk-stays-in-tree | 5/5 | 5/5 |

Full claims/actually-failed diffs against the recorded `mutations.out` (at438, at465-466, at355):
- at465-466 row 3: head lists `test_an_unreadable_sidecar_is_never_reported_as_silence[[1, 2, 3]]` and `[{"segments": [...]}]` whole; the recording (pre-AT-469) had them truncated at the first space. Same tests, better names.
- at438 row 1: the recording also lists `test_the_detector_sees_what_the_dom_hides`; head does not. **Not a lost failure:** the parent instrument run on the same code today gives output identical to head's for all 9 rows, and that test run directly in a copy with the mutation applied passes 3/3. The recording predates ba30b71/9fc937d.

Nothing newly KILLED, nothing lost.

## Known limits — judgement

- "A run that dies before `pytest_sessionfinish` writes no report ... reads SURVIVED" — reproduced (E5), honest; the parent also loses that kill, so no regression.
- "Only CALL failures; xfail(strict) XPASS still counts; teardown error does not" — reproduced (N1, N1b, N2), honest.
- "`_mutation_report` module name could shadow" — honest.
- "`collected_tests` still reads `--collect-only` text" — honest; no probe (spaced, bracketed, nested-class, no-ini) made it disagree with `report.nodeid`.
- **Incomplete (minor):** the plugin reads `MUTATION_REPORT` from `os.environ` at session END, so a test that reassigns it and does not restore silently turns every kill into SURVIVED (E2), and one that removes it makes the run refuse (E3). Both fail closed and need a test to touch the harness's own private variable, so not charged — filed AT-481 (low). Unmentioned improvement: `unittest` subTest failures are now attributed (N4b).

## Issues

- AT-478: open -> **fixed** (P5, P5b, row 2).
- AT-479: open -> **fixed** (P4, row 2).
- AT-481 (new, low): the report path is read from the environment at session end.
