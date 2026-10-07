# Checkpoint - t125-catalog - coordinator A - cycle 4

Attribution: coordinator A checker (this file + qa/verdicts/t125-catalog.md). Environment: Windows 11, Python 3.11.15 (`.venv` of the bound worktree), uv.lock sha256 prefix 188681b3a300c36f, tests/conftest.py blob e5ff4b8402fd.
Code identity: HEAD 778b5f86815f301c5a8baf212c95bf3d0cbf7026, tree 1b7b1c37ab979982fd03c703cac3d7e2f7dc6c28. Blobs: stages/catalog.py 41283e8e40a6, ui/routes_runs.py 8cfb5b00f27e, ui/run_execution.py 21ff612e4eb7, stages/run_budget.py 0bfee7a2a1d4, ui/routes_catalog.py 9ed4f8bcecb5.
Worktree also carried uncommitted other-unit bookkeeping (.goal/goal.json, docs/DECISIONS.md, docs/FEATURES.jsonl, docs/SNAPSHOT.md); not part of the identity of T-125 code.

| Check | Command / scope | Result |
|---|---|---|
| Full suite | `uv run pytest` (PID 39436), bound worktree, collected 2299 outcomes | 3 failed, 2276 passed, 6 skipped, 14 xfailed in 3667.39s; all 3 baseline/load |
| Baseline re-runs | pristine `git archive bd2fe8f4`: test_redact_wrap_perf (x2), test_goal_contract_registration | same failures as the bound tree |
| Lint | `ruff check src tests scripts` | All checks passed |
| Doctor | `autotester doctor` (bound worktree, with uncommitted bookkeeping) | clean |
| Falsification | 22 isolated single-hunk mutants m01-m22 (`git archive HEAD` copy each) | all green-before / red-after / restored-green |
| Browser (headless Playwright library, seeded scratch root, build = worktree HEAD) | project page link click, catalog page, run page, unknown project | pass; 1 console error = intentional 404 |

Browser build id: uvicorn from worktree src at HEAD 778b5f86 (source unchanged since 52bba0b7). Data snapshot: scratch root `scratchpad/ui-root`, seeded by `scratchpad/seed_ui.py`.
Reuse rule: every field above unchanged required before reuse; a source change under src/ or tests/ voids the suite and mutant rows.
