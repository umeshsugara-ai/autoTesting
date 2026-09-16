# Manifest — at431-report-download-no-runs

**Unit:** AT-431 — report.html / report.xlsx answered 500 on a project with no runs
**Contract:** `qa/contracts/ui-report.md` (UR1-UR4), `qa/contracts/report-export.md`; core-invariants C2, C7
**Goal task:** none — issue-driven (found by the independent live-browser validation, `qa/verdicts/live-2026-09-16-ui.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-431 (low)
**Status:** checked-PASS (qa/verdicts/at431-report-download-no-runs.md, cycle 1, commit 2ea23b2)

## What was wrong

`GET /projects/<slug>/report.html` and `/report.xlsx` answered **500** on a project that had never
been run. `report_export._latest_run_id` raises `ValueError("no runs exist yet …")`, and neither
download route caught it. The /report page hides the buttons when there are no runs, so the URL is
reached only when bookmarked or shared. In that case nothing else tells the person what went wrong.

## What changed

- `src/autotester/ui/routes_report.py`:
  - Adds `_no_runs_page(slug)`, a themed **404** "No runs yet" page with a breadcrumb and a
    "Back to the report" link. It sits next to the existing `_unknown_run_page`, which has the same
    shape.
  - Both download routes now call `valid_runs_newest_first(store)` **before** reserving a temp path
    or exporting, and return the page when the list is empty. The return annotation widens from
    `FileResponse` to `Response`.
  - The routes use the **same** run definition as the /report page, so run-artifact directories
    with no run envelope (for example `crawl_latest`) count as "no runs" in both places. 258 lines.
- `tests/test_ui_report_no_runs.py` (new, 4 tests). It uses `TestClient(raise_server_exceptions=False)`
  so the test sees the 500 a browser saw rather than a re-raised exception. It is a separate file
  because `test_ui_report.py` is at 289 lines; that file covers downloads with runs, and this one
  covers downloads without them.

**Not changed:** `report_export._latest_run_id` still raises for a CLI or library caller. That is
correct there, since the exception is the refusal. Only the UI was crashing.

**Dropped before the manifest:** I wrote a fifth test claiming the refusal leaves no temp file
behind. It passed **before the fix**: `_reserved_temp_path` reserves a name and immediately
unlinks it, so the test could never fail. I deleted it rather than ship a guard that cannot fail
(AT-218).

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_ui_report_no_runs.py -o addopts= -q` | `4 passed` (at HEAD without the fix: `4 failed`, observed) |
| `uv run pytest tests/test_ui_report_no_runs.py tests/test_ui_report.py tests/test_report_export.py -o addopts= -q` | `27 passed` (maker: observed) |
| `uv run ruff check src tests scripts` | `All checks passed!` (maker: observed) |
| `uv run autotester doctor` | `doctor: clean` (maker: observed) |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract with `routes_report.py` and the
new test copied in and its own `uv sync`. `autotester.ui.routes_report.__file__` was confirmed
inside the extract. Each anchor matched exactly once. The baseline was `16 passed`
(`test_ui_report_no_runs.py` + `test_ui_report.py`), and it was `16 passed` again after restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `routes_report.py`) | Observed |
|---|---|---|---|
| report.xlsx with no runs is a page, not a 500 | `test_a_download_with_no_runs_is_a_themed_404_not_a_500[report.xlsx]` + artifact test `[xlsx]` | delete the guard in `download_report_excel` | **2 failed, 14 passed** — exactly the two xlsx rows |
| report.html with no runs is a page, not a 500 | same tests `[report.html]` | delete the guard in `download_report_html` | **2 failed, 14 passed** — exactly the two html rows |
| It is a 404, not a 200 | `…themed_404_not_a_500` + artifact tests | `_no_runs_page`: drop `status_code=404` | **4 failed, 12 passed** |
| "No runs" means no valid run envelope, same as the /report page | `test_run_artifacts_without_a_run_envelope_still_count_as_no_runs[report.html]` | html guard → `if not store.paths.runs_dir.exists():` | **1 failed, 15 passed** — exactly that row |
| A project WITH runs still downloads (the guard can say yes) | `test_ui_report.py::test_report_offers_real_excel_and_html_downloads` | xlsx guard → `if True:` | **1 failed, 15 passed** — exactly that test |

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at431-2026-09-16-maker-smoke/report.json`: server from the extract, synthetic-only root.
- /report → 200 page. /report.html → **404 "No runs yet"**. Clicking "Back to the report" → /report.
  /report.xlsx → **404 "No runs yet"**.
- 2 console errors, both Chrome's "Failed to load resource: 404" for the two deliberate URLs.
- Not smoked in the browser: the download path for a project that has runs, because the synthetic
  root has no runs. Test coverage for it is row 5.

## Full suite

One clean run, output redirected in full to a fresh file (60 lines). The command was
`uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its final line is
`1316 passed, 2 skipped, 32 xfailed, 1 warning in 301.30s (0:05:01)`, exit=0. That is 1312 + this
unit's 4. All 32 XFAIL lines are `tests/test_browser_scroll_invariance.py` cases whose reasons name
AT-416 / AT-417, which are pre-existing. The warning is starlette's anyio deprecation. The run began
after sabotage had finished.
