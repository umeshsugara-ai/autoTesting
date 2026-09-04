# Manifest — ui-report-enrichment

**Contract:** qa/contracts/ui-report.md UR1-UR4 (new this cycle)
**Goal task:** none (`.goal/goal.json` is 20/20 done — ad-hoc plan work,
`C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md` §3c)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Plan §3c, following §3b's Run-trigger button: Umesh wants to see and download the report
without a terminal — run history, inline screenshots, and the same Excel/HTML exports the CLI
already produces (`stages/report_export.py`, checker-PASSed earlier this session).

## What changed

- `qa/contracts/ui-report.md` (new) — UR1 (real run history, newest first) · UR2 (real inline
  screenshots via the shared `png_base64` helper, never a placeholder) · UR3 (real portable
  downloads streaming the exact existing export functions, no reimplementation) · UR4 (never a
  second source of truth).
- `src/autotester/stages/report_export.py` — `_b64_png` renamed to public `png_base64` (now used
  by two callers: the portable HTML export and the live UI) — a real reuse, not a new function
  with the same logic duplicated.
- `src/autotester/ui/routes_report.py` (new) — `run_view` (moved from `routes_runs.py`, now
  embeds real inline screenshots per case via `png_base64`), `report` (moved, now lists every run
  newest-first with per-run outcome counts and download links), `download_report_excel` /
  `download_report_html` (new — `GET /projects/{slug}/report.xlsx` / `.html`, stream
  `report_export.export_excel`/`export_html`'s output from a real temp file, deleted via
  `BackgroundTask` after the response is sent).
- `src/autotester/ui/routes_runs.py` — trimmed to just `trigger_run`; `run_view`/`report` moved
  out to `routes_report.py` (this module was about to duplicate the report/run-history
  responsibility that now has its own file, matching the "one concept, one place" rule).
- `src/autotester/ui/app.py` — `app.include_router(routes_report.router)` wired in.
- `tests/test_ui_report.py` (new, 5 tests) — run history newest-first, a real screenshot embedded
  inline, a case with no screenshots says so honestly, both downloads return real non-empty
  content with the right media type, both downloads 404 for an unknown project before ever
  calling the export functions.
- `docs/MAP.md` regenerated.

## A real naming collision found by `autotester doctor`, not invented

The first pass named the two download routes `report_excel`/`report_html`, matching the CLI
command names in `cli.py` for symmetry. `autotester doctor`'s duplicate-concept check correctly
flagged this — the CLI commands and the new HTTP routes are genuinely different functions (one
writes to a user-given path and exits, the other streams a temp file and cleans it up), not the
same concept in two places, so renamed to `download_report_excel`/`download_report_html` rather
than suppressing the check.

## Deliberate scope decisions (per the contract's own no-fire list)

- `report_export.export_excel`/`export_html`'s own logic is untouched — this unit only streams
  their existing, already-checker-PASSed output from a new route.
- No pagination of run history — every real project today has single-digit run counts.
- `/settings/providers` (plan §3d) remains a separate unit.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui_report.py -v    # 5 passed
$ uv run pytest -q                             # full suite green, no regressions
$ uv run ruff check src tests scripts          # All checks passed!
$ uv run autotester doctor                     # doctor: clean (duplicate-concept fixed above)
$ uv run autotester map                        # docs/MAP.md regenerated
```

**Real live Docker verification (not just `TestClient`):** `docker compose restart`, seeded a
throwaway project (`ui-report-demo`, pointed at the container's own UI server, one NAVIGATE-only
case), triggered `POST /run` **twice** (to produce real run history, not just one run):

```
run1: 303
run2: 303
```

- `GET /projects/ui-report-demo/report` → both real run ids present
  (`run-01M1NBPKT5WZPCXBNQTPAG24TV`, `run-01M1NBPZ8CDNNGVGYP50SM89MT`), confirming UR1.
- `GET /projects/ui-report-demo/runs/<run-id>` → contains `data:image/png;base64,` — a real
  screenshot the run actually captured, embedded inline, confirming UR2.
- `GET /projects/ui-report-demo/report.xlsx` → `200`, 5106 bytes (a real, non-empty workbook).
- `GET /projects/ui-report-demo/report.html` → `200`, 48036 bytes, containing the real case
  title `homepage loads` (not a stub), confirming UR3.
- Cleaned up the throwaway project + profile afterward
  (`rm -rf projects/ui-report-demo profiles/ui-report-demo`) — no host-side leftovers.

## How to verify

- `uv run pytest tests/test_ui_report.py -v` → 5 passed.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- Seed a throwaway project + case, trigger 2 runs via `POST /projects/<slug>/run`, then confirm
  `/report` lists both newest-first, `/runs/<id>` embeds a real screenshot, and both
  `/report.xlsx` / `/report.html` return real non-empty content. Clean up afterward.

## Scope notes for the checker

- Please confirm the `report_export.py` rename (`_b64_png` → `png_base64`) has exactly one
  remaining internal call site updated (`_case_section`) and no other module still references the
  old private name.
- Do your own live-Docker verification if you can — two real runs producing real history + a real
  screenshot + real non-trivial downloads is the actual proof UR1-UR4 hold, not the pasted output
  above.

## Status: checked-PASS — see qa/verdicts/ui-report-enrichment.md, cycle 1 PASS (checker filed
AT-040, a low-severity cosmetic docstring-drift issue, fixed same-day post-verdict)
