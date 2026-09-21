# Verdict — at523-a-guard-so-the-q-doubling-cannot-come-back

**Cycle checked:** 1
**Date:** 2026-09-21
**Checked by:** /checker (fresh context, bound to `D:/autoTesting`)
**Commit under check:** `5a88ed4` — `feat(doctor): pytest -q doubling guard for adapter + goal.json (AT-523/AT-524)` (`git show --name-only 5a88ed4` = the manifest, its `qa/evidence/at523-*` dir, `src/autotester/doctor.py`, `src/autotester/ledger/checks.py`, `tests/test_ledger_checks.py` — exactly the manifest's declared "What changed" set)
**Contract:** `qa/contracts/core-invariants.md` — C7 (real, re-runnable verification output; mutation duty on a unit that adds tests) is the governing criterion; C2 (line caps) and C10 (commit scope) also judged.

## VERDICT: PASS

SCOREBOARD: 6/6 capability-coverage rows reproduced; C7, C2, C10 hold; 0 criteria failed.
Verify instruments re-run by me: `uv run pytest tests/test_ledger_checks.py` → `28 passed in 15.03s`; `uv run ruff check src tests scripts` → `All checks passed!`; `uv run autotester doctor` → `doctor: clean`; my own `scripts/mutation_check.py` run → `5/5 mutations killed` with every named test in the actual failure list; AT-503's measured table re-derived with my own runs (`-o addopts=` → `28 passed` summary line; `-qq` added → dots only, no summary line).

## What I independently re-derived (not trusted from the manifest)

1. **Verify commands re-run by me (Mode A step 3).** All three reproduce the manifest's "Actual outputs" exactly: subset pytest 28 passed; ruff clean; doctor clean.

2. **The rule reasons, it does not grep — confirmed by reading the code.** `src/autotester/ledger/checks.py:185-275`: `_count_q_tokens` sums `action="count"` weight over purely-`-q...` tokens; `_pyproject_addopts_q_count` reads the live `pyproject.toml` via `tomllib` (no baked-in constant); `_pytest_invocations` splits on `&&`/`||`/`|` and keeps only sub-commands matching pytest; `_effective_q_total` treats an explicit `-o addopts=...` as REPLACING config addopts (pytest's own precedence — verified live: `pytest -q -o addopts=` prints the summary, so the override genuinely removes the config `-q`). Both checks registered in `doctor.py::run` (doctor.py:193-209), between `check_qa_issue_rows` and `check_generated_fresh` as the manifest claims.

3. **Doctor-clean is a true negative, not a silent miss.** I independently counted the live scan surface: `.goal/goal.json` has 50 `cmd` fields, 44 of them invoke pytest, and **0 contain any `-q` token** (grep for `-q` among pytest commands → empty). `qa/adapter.json`'s three verify commands are all bare (no `-q`). `pyproject.toml:62` still carries `addopts = "-q"`, so config_q = 1 and any CLI `-q` on a pytest invocation would now be flagged — the checks are wired, execute, and find nothing because AT-503/AT-521/AT-522 genuinely swept the tree. Fixture tests prove the same checks fire on the defect shape. Both halves of the falsification point hold.

4. **Mutations: 5/5 killed — re-run by me with the repo's own audited harness.** `uv run python scripts/mutation_check.py qa/evidence/at523-*/mutations.json` → identical output to `mutation_run.txt`, including mutation 1's honest extra kill (the goal-json twin fails under the same threshold loosening — the manifest's table lists only its primary kill; `mutation_run.txt` discloses both). The harness internally asserts every C7 clause: green baseline before any mutation, anchor matched exactly once + file actually changed, kill = exit 1 AND the named test present in pytest's structured failure report, sandbox outside the repo, restore verified. **Old-string fidelity independently confirmed against the commit under judgment:** each of the 5 `old` strings appears exactly once in `git show 5a88ed4:src/autotester/ledger/checks.py` and once in the working tree.

5. **Capability coverage table reproduced** (6 substantive rows — see table below). One row ("missing files are not violations") spans two tests, both of which I ran in the subset.

| capability | my reproduction | result |
|---|---|---|
| bare pytest not flagged / AT-503 defect caught | ran both fixture tests' scenarios against the reasoning in checks.py + re-derived AT-503's table with my own `-o addopts=` / `-qq` runs | reproduced: bare → summary line present; stacked `-qq` → no summary |
| override subset runs stay legal | `test_an_explicit_addopts_override_is_not_a_doubling` + mutation 3 killed by it | reproduced |
| guard tracks live config | `test_the_guard_reads_addopts_live_rather_than_assuming_it` + mutation 2 (hardcode 1) killed | reproduced |
| chained non-pytest `-q` ignored | `test_only_the_pytest_sub_command_of_a_chained_cmd_is_checked` + mutation 4 killed | reproduced |
| goal rows carry task id | `test_goal_json_cmd_row_stacking_cli_q_is_flagged_with_its_task_id` (asserts `.goal/goal.json:T-160` exactly) + mutation 5 killed | reproduced |
| rule survives falsifying edits | my own `mutation_check.py` run: 5/5 KILLED, attribution verified | reproduced |

6. **Diff scope (step 4c).** `git show 5a88ed4 --numstat`: checks.py +95, doctor.py +8/−2, tests +102, plus the manifest and its evidence dir — the manifest's declared set exactly, no other paths. The doctor.py diff is purely the import + two registrations in `run`. Nothing deleted or renamed. `git diff 5a88ed4 HEAD -- src tests` is **empty** — the code judged is intact at HEAD. `5a88ed4` is C10-clean: only the unit's own paths.

7. **C2 line caps hold.** Measured: checks.py 275 total (222 non-blank), doctor.py 210 (176 non-blank), tests 265 (182 non-blank). The manifest's "222/176/182" figures are **non-blank** counts — a cosmetic mismatch of convention, disclosed here, not a false claim (all files ≤ 300 on either convention, and doctor's own checker passes them).

8. **Full-suite log treated as supporting, per the dispatch.** `full_suite.log` is internally consistent: I counted 1496 `.` + 32 `x` + 2 `s` = 1530 outcome characters, matching its summary line (`1496 passed, 2 skipped, 32 xfailed`, `exit=0`). Today's tree collects 1529 — a one-test delta from environment-dependent collection (the scroll-invariance corpus enumerates scrollers at runtime; tests/ is unchanged since 5a88ed4). Not load-bearing for this PASS; my own subset + mutation + doctor runs are the verification, and C7's verify instrument (`uv run pytest`) is exercised below.

9. **Issues addressed.** AT-523 and AT-524 are the unit's subject; the manifest correctly did NOT touch the ledger (`git show --name-only 5a88ed4` confirms `qa/issues.jsonl` absent — the checker's write surface per AT-499/AT-526). **I flipped both: `open → fixed`, `fixed_by` naming this verdict** (rows 520, 521; single-line edits, every other byte preserved). No new defects found in the artifact itself; one low-severity robustness note filed as AT-527 (below, not charged to this unit).

## Residuals (disclosed, not charged)

- **AT-527 (low, filed by this check):** `check_adapter_pytest_q` calls `json.loads` on `qa/adapter.json` unguarded (checks.py:254) — a malformed adapter makes `doctor` traceback (`JSONDecodeError`) instead of reporting a violation. Reproduced by me in a scratch dir. AT-021's convention ("a doctor reports, it never tracebacks") wraps `check_ledger`'s load the same way; the new checks should too. Not charged here: the live adapter is valid and committed, the failure is loud (not silent), and the manifest's declared scope is the `-q` rule, which is fully evidenced.
- **Collect-count drift:** 1529 today vs 1530 in the log — environment-dependent parametrization, not a code change (tests/ identical). No action.

## Mode D / scope

No UI surface touched (changed paths are doctor-rule code, its tests, and qa/ artifacts) → `LIVE-BROWSER: not-applicable`. No external data collected → no scope claim to verify. No matching `.goal/` task (manifest: "none, issue-driven") → no goal close-out.

## Close-out

- Ledger: AT-523 and AT-524 flipped `open → fixed` with `fixed_by` naming this verdict (cycle 1, PASS); AT-527 filed (low, open). No other rows touched.
- The maker must still flip the manifest to `checked-PASS` (its own close-out step, per the handshake).

VERDICT: PASS