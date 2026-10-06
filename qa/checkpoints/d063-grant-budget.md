# Checkpoint A — d063-grant-budget (cycle 0): all mandatory checks complete

Environment: Windows, worktree in-tree .venv for suite/ruff/doctor; copies run via PYTHONPATH with D:/autoTesting/.venv python. Code head a4bd0a60. uv.lock sha256 188681b3a300c36f.. ; tests/conftest.py sha256 9bbb6a4bc2be7eb9.. ; no deploy or data snapshot.

| check | command / scope | result | attribution |
|---|---|---|---|
| full suite | uv --directory <root> run pytest (all) | 1 failed (already red at master e633bc69), 2314 passed, 5 skipped, 14 xfailed | coordinator A |
| lint | uv run ruff check src tests scripts | pass | coordinator A |
| doctor | uv run autotester doctor | 1 violation, stale docs/MAP.md | coordinator A |
| mix_live | tests/test_ui_runs_serial_entry_mix_live.py | 1 passed | coordinator A |
| capability table | 9 rows, one copy per row | 9/9 green-red-green | sub-checker af6b11a1a3a8b56a7 |
| exact-host | 5 test files in a copy (110 passed) + 4 mutants | killed on topic | sub-checker aaec53e9967d30fa3 |
| grant-path security review + probes | consent, ids, env_editor, routes_runs, cli_crawl | sound; P1 | sub-checker a6ca69731f059dccc |
| budget / receipt review | stages, ui, browser | sound; P2, P3 | sub-checker a3caa276e51f61a79 |

# Cycle 1 (repair) - coordinator A, head b90618c9; src/scripts/projects identical to a4bd0a60 (empty git diff); conftest 9bbb6a4bc2be7eb9.., uv.lock 188681b3a300c36f.. unchanged. All earlier rows remain valid by identity.

| check | command / scope | result | attribution |
|---|---|---|---|
| lint | uv run ruff check src tests scripts | pass | coordinator A |
| affected tests | test_approve_cli_bounds.py test_approve_cli.py test_consent.py (bound root) | 57 passed | coordinator A |
| row C3 CLI nan/inf | copy, cli_crawl.py:256 -> if False, node ..._writes_nothing | 9 passed / 2 failed [nan][inf] / 9 passed | coordinator A |
| row C3 CLI default production | copy, cli_crawl.py:246 False->True, node ..._not_production | 1 passed / failed :65 / 1 passed | coordinator A |
| row C1 grant production | copy, consent.py:85 production=False->True, node test_account_grant_is_new_exact_and_bounded | 13 passed / 2 failed [valid][unused] :258 / 13 passed | coordinator A |
| row C1 scope | copy, consent.py:45 clause->True, node ...[scope] | 1 passed / failed :250 / 1 passed | coordinator A |
| full suite, doctor, mix_live, exact-host, reviews | not re-run: src, conftest, lock identity unchanged from cycle 0 | reused | cycle-0 rows above |
