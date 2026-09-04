# Manifest — report-export

**Contract:** qa/contracts/report-export.md (RE1–RE5, new this cycle)
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Umesh, after watching a real headed-browser run against Pathlynks: "testing hone ke baad step by
step, like an Excel sheet and an HTML report with screenshots, screen by screen, proper reporting
as a tester." The live UI's `/report` page only shows aggregate counts — this adds two portable
export formats over the exact same underlying evidence.

## What changed

- `qa/contracts/report-export.md` (new) — RE1 (reads only existing evidence) · RE2 (Excel: one
  row per case, real fields) · RE3 (HTML: self-contained, embedded screenshots) · RE4 (defaults
  to latest run) · RE5 (no secret ever reaches an exported file).
- `pyproject.toml`/`uv.lock` — added `openpyxl>=3.1.5` (real `.xlsx` generation).
- `src/autotester/stages/report_export.py` (new, 133 lines) — `export_excel(project_slug,
  run_id, out_path, root=None)`, `export_html(...)` — both read exclusively through
  `ProjectStore`; `export_html` base64-embeds every screenshot so the file needs no other file on
  disk.
- `src/autotester/cli.py` — new `report_app` Typer sub-group: `autotester report excel <slug>
  [run_id] --out <path>` and `autotester report html <slug> [run_id] --out <path>`; `run_id`
  omitted defaults to the project's latest run (RE4), matching `ui/app.py::report`'s convention.
- `tests/test_report_export.py` (new, 5 tests) — Excel has one row per case with real fields;
  defaults to the latest run; raises a clear error with zero runs; HTML embeds a screenshot as
  base64 (not a file reference) and shows the case title/result; an errored case's raw error
  text appears in the HTML.
- `docs/ARCHITECTURE.md` — one new concept→file row (merged into the existing db-assert/
  manual-login row to stay in budget); 150 lines (at cap).
- `docs/MAP.md` regenerated.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_report_export.py -v
.....                                                                     [100%]
5 passed
$ uv run pytest -q                        # all green
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

**Real export against a real run** — the actual Pathlynks run just performed this session
(`run-01M1N4HZ83AWWHYJ8QTENKTYBD`, 3 cases, real headed browser, real judge):
```
$ uv run autotester report excel pathlynks run-01M1N4HZ83AWWHYJ8QTENKTYBD --out .work/pathlynks-report.xlsx
wrote .work\pathlynks-report.xlsx
$ uv run autotester report html pathlynks run-01M1N4HZ83AWWHYJ8QTENKTYBD --out .work/pathlynks-report.html
wrote .work\pathlynks-report.html
```
Opened the `.xlsx` via `openpyxl.load_workbook` and confirmed real rows (case titles, outcomes,
`INCONCLUSIVE` results, durations, the actual raw error text). Rendered the `.html` via a real
headless Playwright screenshot and visually confirmed: three sections (one per case), each with
its result badge and its real embedded screenshots (the actual Pathlynks sign-in page and the
already-authenticated dashboard) — not placeholders, not broken image links.

Secrets scan on both real exported files (touching a real product's data):
```
$ uv run python scripts/check_no_secrets.py .work/pathlynks-report.xlsx .work/pathlynks-report.html
scanned 2 file(s); 0 leak(s)
```

## How to verify

- `uv run pytest tests/test_report_export.py -v` → 5 passed
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean
- `uv run autotester report excel <slug> --out <path>.xlsx` against any project with a real run →
  a real, openable Excel file with one row per case
- `uv run autotester report html <slug> --out <path>.html` → open in any browser, no server
  needed, screenshots render inline

## Scope notes for the checker

- `.work/pathlynks-report.xlsx`/`.html` are scratch verification artifacts under the gitignored
  `.work/` directory — not committed, per this project's "scratch/evidence goes to `.work/`" rule.
- No change to `ui/app.py`'s existing `/report` route or any other UI page — this is a CLI-only
  addition, per the no-fire list's exclusion of scheduled/automatic export or UI styling parity.
- The exported HTML deliberately does NOT reuse `ui/theme.py` — a shared stylesheet would break
  the "one portable file" property the moment the live theme changes; verify the exported HTML
  has its own inline `<style>` block, not an import/link to anything external.

## Status: checked-PASS — see qa/verdicts/report-export.md, cycle 1 PASS (checker-flagged missing charset meta tag fixed post-verdict)
