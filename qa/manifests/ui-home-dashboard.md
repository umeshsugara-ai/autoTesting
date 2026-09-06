# Manifest — ui-home-dashboard
**Contract:** qa/contracts/ui.md
**Goal task:** none (feedback-driven unit)
**Date:** 2026-09-06
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none filed (feedback-inbox entry, not a ledger issue)

## What changed
- `src/autotester/ui/app.py`:
  - Imports `_run_counts`/`_run_ids_newest_first` from `routes_report.py` (reuse, not a
    second way to compute "how did the last run go" — ui.md U2/U4).
  - New `_latest_run_status(slug)` — the latest run id (or `None`) and its verdict counts
    for one project.
  - `_project_card(slug)` now renders a latest-run status badge row (or "never run") under
    the existing name/case-count, using the same `theme.badge()` component the report page
    already uses.
  - New `_portfolio_stats(slugs)` — aggregate stat tiles across every onboarded project:
    project count, total case count, "latest run clean" count, and (only when non-zero)
    "latest run failing" / "never run" counts. Reuses `theme.stat()` unchanged.
  - `index()` renders `_portfolio_stats(slugs)` between the page header and the project
    grid, only when at least one project exists (the empty state is unchanged).
- `src/autotester/ui/theme_style.py` — added `.card-status` (2 lines) so the new badge row
  on a project card sits cleanly under the existing meta line; no other style changed.
- `tests/test_ui.py` — no net line-count growth (the two dashboard tests originally added
  here were moved out, see below) — only the `test_unknown_project_is_404` trailing
  whitespace is unchanged code, verifying the split left it intact.
- `tests/test_ui_dashboard.py` (new file) — 3 tests: portfolio stats show real aggregate
  counts including a FAIL badge when a project's latest run failed, a project that never
  ran shows "never run" (not a false healthy/failing count), and a project whose latest run
  is all-PASS counts as "latest run clean" (not double-counted as failing). Split out of
  `test_ui.py` because adding the dashboard tests there pushed it to 330 lines, over
  `autotester doctor`'s 300-line file cap — matches the project's existing convention of
  one UI-surface-per-test-file (`test_ui_runs.py`, `test_ui_flow_diagram.py`, etc.).

## How it was found
User feedback, twice in one session (2026-09-06): "bhai ye kessa ui bnaya hai na dashboard
na kuch user kese testing krr payegaa" (what kind of UI is this, no dashboard, nothing — how
will a user test with this) and later "ye abhi wala tho essa lgg nhi rhaa ki koi sach mai
proper tool with dashboard and all hai" (this doesn't look like there's really a proper tool
with a dashboard). Logged verbatim in `qa/feedback-inbox.md` (2026-09-06 entry) with the
specific gap: `ui/app.py::index()` (lines 69-85 at the time) rendered only a bare grid of
project-name cards with a case count — no aggregate health view, no way to tell what's
passing or failing across the portfolio without clicking into every project one by one.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → expected: exit 0, all tests pass
- `docker compose exec autotester uv run pytest -q tests/test_ui.py tests/test_ui_dashboard.py` → expected: exit 0
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: exit 0
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Real end-to-end: `docker compose restart autotester` (uvicorn has no `--reload`), then load
  `http://localhost:8010/` in a real browser → expected: stat tiles for projects/cases/clean
  runs above the project grid, and each project card shows a real PASS/FAIL badge from its
  actual latest run (or "never run"), not just a case count.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q
........................................................s............... [ 25%]
........................................................................ [ 51%]
........................................................................ [ 77%]
..............................................................           [100%]
(all pass, 1 skip, no failures)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end, after `docker compose restart autotester` and loading `/` in a live
Playwright browser session (screenshot: `.work/dashboard-home.png`): the home page shows
three real stat tiles — "3 PROJECTS", "48 CASES", "3 LATEST RUN CLEAN" — and three project
cards (Pathlynks, Regression Proof Demo, Vidysea Centre Management ERP), each with its own
real latest-run PASS badge pulled from actual persisted verdict files, not invented or
cached data.

## Status: ready-for-check
