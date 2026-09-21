# Manifest — at523-a-guard-so-the-q-doubling-cannot-come-back (AT-523 + AT-524)

**Unit:** AT-523 — the `-q` regression guard: a CLI `-q` must never stack on `pyproject.toml`'s
own `addopts` `-q` (`-qq` prints no summary line at all). AT-524 — the same guard extended to
`.goal/goal.json`'s `done_check.cmd` rows.
**Contract:** `qa/contracts/core-invariants.md` C7 (real, re-runnable verification output);
the AT-503 measured table (bare → summary line; `-qq` → none).
**Goal task:** none (process/governance, issue-driven).
**Date:** 2026-09-21 (built 2026-09-18, session interrupted before manifest)
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-523 (fixed here), AT-524 (fixed here). Ledger rows are the checker's
write surface (AT-499) — not flipped by this manifest.

## What was built

Two doctor checks in `src/autotester/ledger/checks.py` (+95 lines, file 222/300), registered in
`src/autotester/doctor.py::run` between `check_qa_issue_rows` and `check_generated_fresh`
(doctor.py 176/300):

- `check_adapter_pytest_q` — AT-523: scans `qa/adapter.json`'s `verify.commands[].cmd`.
- `check_goal_pytest_q` — AT-524: scans every `done_check.cmd` with `type == "cmd"` in
  `.goal/goal.json`, violation location names the task id (`.goal/goal.json:T-NNN`).
- Both share `_q_doubling_violations`; rule: a pytest invocation's **effective** `-q` weight
  must stay `< 2`.

The rule reasons, it does not grep (each proven by its own falsifying test):

- `_count_q_tokens` sums `action="count"` weight (`-q`=1, `-qq`=2).
- `_pyproject_addopts_q_count` reads the **live** `pyproject.toml` via `tomllib` — if addopts
  stops setting `-q` tomorrow, the guard tracks the config, never a baked-in constant.
- `_pytest_invocations` splits a chained command on `&&`/`||`/`|` and inspects only the
  sub-commands that actually invoke pytest — a trailing `-q` on `autotester doctor` is a
  different program's flag.
- `_effective_q_total` handles `-o addopts=...`: an explicit override REPLACES pyproject's
  addopts for that invocation (pytest's own precedence), so `pytest -q -o addopts= tests/…`
  is the deliberate, safe subset shape AT-506's runs use — not a doubling.

Tests: 9 new in `tests/test_ledger_checks.py` (28 total in file, 182/300 lines — the file
AT-513 split specifically to regain headroom for this).

## How to verify (commands + expected)

```
uv run pytest tests/test_ledger_checks.py    # expect: 28 passed
uv run ruff check src tests scripts          # expect: All checks passed!
uv run autotester doctor                     # expect: doctor: clean (new checks run on the live repo)
```

Full-suite evidence from this build session:
`qa/evidence/at523-a-guard-so-the-q-doubling-cannot-come-back/full_suite.log` — exit=0,
`1496 passed, 2 skipped, 32 xfailed` (run against this working tree by the earlier agent of the
interrupted session, ~40 min wall clock; whole-log scanned, not tailed).

## Actual outputs (from my own run, 2026-09-21)

```
$ uv run pytest tests/test_ledger_checks.py
28 passed in 2.55s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

The doctor-clean line is itself a live falsification point: both new checks execute against the
real repo (AT-503 already swept `qa/adapter.json`; AT-521/522 swept goal.json's 43 rows) and
find 0 violations on the post-sweep tree — while the fixture tests prove each check fires on
the defect shape.

## Mutations (5/5 killed, first run)

`qa/evidence/at523-a-guard-so-the-q-doubling-cannot-come-back/mutation_run.txt` /
`mutations.json`:

| # | Mutation | Kills |
|---|---|---|
| 1 | doubling threshold loosened (`>= 2` → `> 2`) so a real `-qq` is not caught | `test_adapter_command_stacking_cli_q_on_addopts_is_flagged` (+ goal-json twin) |
| 2 | addopts count hardcoded to 1 instead of read from pyproject.toml | `test_the_guard_reads_addopts_live_rather_than_assuming_it` |
| 3 | explicit `-o addopts=` override ignored → doubling on top of the real config | `test_an_explicit_addopts_override_is_not_a_doubling` |
| 4 | every chained sub-command treated as pytest, not only the real one | `test_only_the_pytest_sub_command_of_a_chained_cmd_is_checked` |
| 5 | goal.json violation location drops the task id | `test_goal_json_cmd_row_stacking_cli_q_is_flagged_with_its_task_id` |

## Capability coverage (each claim -> its isolating check)

| capability | check | falsifying condition | observed |
|---|---|---|---|
| bare pytest still prints a summary | `test_adapter_command_matching_addopts_is_not_flagged` + AT-503's measured table | guard flags the compliant bare command | not flagged |
| the actual AT-503 defect is caught | `test_adapter_command_stacking_cli_q_on_addopts_is_flagged` | stacking CLI `-q` on addopts's `-q` passes | `pytest-q-doubled` |
| override subset runs stay legal | `test_an_explicit_addopts_override_is_not_a_doubling` | `-o addopts=` misfires the guard | not flagged |
| guard tracks live config, not today's value | `test_the_guard_reads_addopts_live_rather_than_assuming_it` | addopts emptied → CLI `-q` still flagged | not flagged |
| chained non-pytest `-q` ignored | `test_only_the_pytest_sub_command_of_a_chained_cmd_is_checked` | `doctor -q` after `&&` flagged | not flagged |
| goal rows carry their task id in the location | `test_goal_json_cmd_row_stacking_cli_q_is_flagged_with_its_task_id` | location lacks `T-NNN` | `.goal/goal.json:T-160` |
| missing files are not violations | two tests | missing adapter/goal flagged | not flagged |
| the rule survives falsifying edits | 5/5 mutations killed | any survivor | 5/5 KILLED |

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/ledger/checks.py`,
`src/autotester/doctor.py`, `tests/test_ledger_checks.py`, plus this manifest and the
evidence dir. Nothing rendered by a page.

## Known limits (disclosed, not claimed)

- The full-suite log is from the earlier agent of the interrupted session (same working tree,
  before the deterministic tick churn to `.goal/`); I re-ran the unit's subset, ruff, and
  doctor fresh today. The checker re-runs the suite independently per the adapter anyway.
- The guard checks only `-q` stacking. Other addopts interactions (e.g. someone adding `-x`
  to addopts) are out of scope — that would be a different defect class, none observed.
- AT-524's sweep of the live goal.json happened in the at521 unit by hand; this unit builds
  the standing guard so it cannot come back — it does not re-sweep anything.

## Status: ready-for-check (cycle 1)