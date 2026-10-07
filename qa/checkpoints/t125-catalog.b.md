# Checkpoint — t125-catalog, coordinator B, cycle 4 (evidence identities)

Checker: coordinator B (claude-opus-5-5). Verdict: qa/verdicts/t125-catalog.b.md. Result at cycle 4: PASS.
Code identity: commit 52bba0b7da45d807a0ffeb81156bf60810bb74e2, tree b6df6e52b0e0b94952f1a1e36a4844ef8e4ce852; src tree fa2be37734a6313244b3ca6446f239190834c6b3; tests tree bfc2c6e19a7d9bff3bb6e648934e89837c1675dd; tests/conftest.py blob e5ff4b8402fdf0b9f1dde251bd25c70401c39139.
Lock identity: uv.lock blob 9ecba7fb3b3ece6efd565db517b2110187b41b68; pyproject.toml blob 19a815ccf1402a4a6a09c31af5db7310a22a02d7.
Environment: Windows 11, CPython 3.11.15, venv `.worktrees/t125-b-check/.venv` (80 packages), machine under concurrent suite load.

| Check | Command + scope | Result |
|---|---|---|
| Full suite (once) | `uv run pytest` bare, 2299 collected, PIDs 57780/41116/60612 | 5 failed, 2274 passed, 6 skipped, 14 xfailed in 3481.34s; 0 T-125-owned (3 baseline-red at bd2fe8f4, 1 timing baseline+load, 1 load-only) |
| Affected copy baseline | pytest tests/test_ui_report.py test_ui_runs_serial_entry_order.py test_parallel_run_approval.py test_schema.py test_catalog.py test_catalog_packs.py test_ui_catalog.py in an isolated src+tests copy | 111 passed |
| ruff | `ruff check src tests scripts` | All checks passed |
| doctor | `autotester doctor` at the committed head | 10 violations: 7 baseline + 3 manifest D-061 prose citations |
| Mutants | 29 isolated copies, one per mutant | 25 RED, 4 explained survivors (C1b equivalent, C5 redundant, D3 inert with D3b RED, E6 label WARN) |
| Browser | own Playwright Chromium vs uvicorn PID 19560 on a scratch root; evidence `D:/autoTesting/.work/t125-b-browser-evidence/` | catalog, no-flowspec and run pages as asserted in the verdict; the one 404 console error is the intentional unknown-project navigation |
