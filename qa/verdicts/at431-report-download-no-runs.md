# Verdict — at431-report-download-no-runs

**Date:** 2026-09-16
**Checker:** /checker Mode A + Mode D, fresh subagent, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at431-report-download-no-runs.md` (Fix cycle: 1)
**Cycle checked: 1**
**Contracts:** `qa/contracts/ui-report.md` (UR1-UR6), `qa/contracts/report-export.md` (RE1-RE5), `qa/contracts/core-invariants.md` (C2, C7)

```
VERDICT: PASS
SCOREBOARD: 11/11 criteria met, 2/2 invariants hold
FAILURES (if any):
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at431-report-download-no-runs-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-431 open -> fixed (row updated in qa/issues.jsonl, left uncommitted: file carries other sessions' hunks)
EXPLANATION: Both download routes now check valid_runs_newest_first (the same run definition the /report page and the exporter use) before exporting, and return a themed text/html 404 "No runs yet" page instead of the uncaught ValueError 500. In my own headed Chromium, the with-runs Download Excel/HTML buttons really download (valid xlsx zip / self-contained html, both carrying the seeded case), no-runs and crawl-only projects get the 404 page with a working back link and breadcrumb, and unknown or traversal-shaped slugs stay 404/400. All 5 falsifying edits reddened exactly the named tests on the intended assertion in a copy outside the tree.
```

## What I re-ran (bound tree, read-only)

| Command | Result |
|---|---|
| `uv run pytest tests/test_ui_report_no_runs.py -o addopts= -q` | `4 passed` |
| `uv run pytest tests/test_ui_report_no_runs.py tests/test_ui_report.py tests/test_report_export.py -o addopts= -q` | `27 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` (routes_report.py 258 lines, new test 67) |
| Full suite, once, sequential, redirected, run in the copy (`uv run pytest -p no:cacheprovider -o addopts= -q -rx`) | `1 failed, 1315 passed, 2 skipped, 32 xfailed` in 288.74s. The one failure is `test_ui_sources.py::test_uploaded_recordings_are_gitignored`: `git check-ignore` -> `fatal: not a git repository` because the git-archive copy has no `.git`. An artifact of the copy, unrelated to this unit; the same file passes in the bound tree (`9 passed`). 32 XFAILs are `test_browser_scroll_invariance.py` (AT-416/417, pre-existing). |

## Capability coverage (throwaway copy)

Copy: `git archive HEAD` extracted to the session scratchpad (`.../scratchpad/checker-at431/`), plus the 2 unit files and its own `uv sync`. `autotester.ui.routes_report.__file__` resolved inside the copy. Named checks were GREEN before the edits: `16 passed` (`test_ui_report_no_runs.py` + `test_ui_report.py`). Each anchor matched exactly once, one edit at a time, restored afterwards (`16 passed`).

| Row | Edit | Observed | Assertion that fired |
|---|---|---|---|
| 1 xlsx no-runs is a page | delete xlsx guard | 2 failed (both `[report.xlsx]` no-runs tests) | `assert 500 == 404` |
| 2 html no-runs is a page | delete html guard | 2 failed (both `[report.html]`) | `assert 500 == 404` |
| 3 it is a 404 | drop `status_code=404` on `_no_runs_page` | 4 failed (all no-runs tests) | `assert 200 == 404` |
| 4 same run definition as /report | html guard -> `if not store.paths.runs_dir.exists():` | 1 failed, only `test_run_artifacts_without_a_run_envelope_still_count_as_no_runs[report.html]` | `assert 500 == 404` |
| 5 with runs still downloads | xlsx guard -> `if True:` | 1 failed, only `test_report_offers_real_excel_and_html_downloads` | `assert 404 == 200` |

No cell was a shell command or touched a non-listed file. Trap check: the no-runs tests assert status + content-type + text, a state the bug (500) does not produce; row 5 covers the guard answering yes.

## Mode D — my own journey

Server: uvicorn from the copy on 127.0.0.1:8041. `AUTOTESTER_ROOT` was an isolated scratchpad root holding only synthetic projects, seeded through `ProjectStore`: `withruns` (run_1 PASS, run_2 FAIL, plus a `crawl_latest` dir), `noruns`, and `crawlonly` (runs/ holding only `crawl_latest`). The server log shows zero 500s. The server was stopped and the browser closed afterwards.

Instrument note: the Playwright MCP browser lost its connection on every download event (twice). The journey was re-driven with Playwright's Python API in headed Chromium, recorded per step with console errors.

- `withruns /report`: 200, two buttons "⬇ Download Excel" / "⬇ Download HTML", 0 console errors.
- Clicking Download Excel gave a real download `withruns-report.xlsx`: 5097 bytes, a valid zip with `xl/workbook.xml`, containing the seeded case title. 0 errors.
- Clicking Download HTML gave a real download `withruns-report.html`: 943 bytes, containing the seeded case title and not the no-runs page. 0 errors.
- `noruns /report`: 200 empty state, 0 buttons. Direct `report.html` / `report.xlsx`: **404 text/html "No runs yet"** with breadcrumb Projects / noruns / Report / No runs yet.
- Clicking "Back to the report" lands on `/projects/noruns/report`. Clicking the breadcrumb Report link lands on the same page.
- `crawlonly`: `report.html` / `report.xlsx` -> 404 "No runs yet". `/report` shows the empty state with 0 buttons, so the page and the download agree.
- Edges: `nosuchproj` -> 404 JSON `no project` (unchanged). `..%5C..%5Cwithruns` and `with%22runs%3Cx%3E` -> 400 `invalid project slug`. `..%2F..%2Fetc`, `withruns%2F..%2Fnoruns` and `%2E%2E` -> 404 route not found. None served another project's data.
- Console errors: every non-zero count is exactly one Chrome "Failed to load resource: 404/400" line for the non-2xx URL the step deliberately requested. There are no JS errors and 0 unexplained errors (per-step attribution in report.json).

## Criteria

- UR1, UR2, UR6: unchanged and untouched by the diff. /report renders history and the empty state live.
- UR3: with runs, the routes still stream `export_excel` / `export_html` (live downloads verified). Without runs, a page is returned instead of a crash. There is no second export path.
- UR4: reads go through `ProjectStore` via `_load_project_or_404` and `valid_runs_newest_first`.
- UR5: "no runs" uses the same valid-envelope definition (row 4 and the live crawl-only case).
- RE1-RE5: `report_export.py` is unchanged. The CLI still raises for a library caller, as the manifest states.
- C2: file and function sizes are within limits, doctor is clean, and the docstrings state the job.
- C7: independently re-run, with sabotage reproduced in a copy that was green before each edit.
