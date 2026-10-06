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
