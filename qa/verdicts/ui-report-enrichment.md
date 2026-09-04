# Verdict — ui-report-enrichment

**Cycle checked:** 1
**Date:** 2026-09-04
**Checker:** fresh-context Mode A unit check (no builder reasoning consulted)
**Contract:** qa/contracts/ui-report.md (UR1-UR4)
**Manifest:** qa/manifests/ui-report-enrichment.md (Fix cycle 1 of max 3)

## VERDICT: PASS

## Scoreboard: 4/4 criteria met, 0/0 additional invariants declared

## What I re-ran myself (not trusted from the manifest)

- `uv run pytest tests/test_ui_report.py -v` → 5 passed (re-run fresh).
- `uv run pytest -q` → full suite green (243 passed, 2 skipped), no regressions.
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean.
- Rename audit: `grep -rn "_b64_png|png_base64" src` → zero remaining references to the old
  private `_b64_png` name; `png_base64` has exactly one internal call site
  (`report_export.py::_case_section` line 93) plus the new UI caller
  (`routes_report.py` line 62) — confirms the manifest's own scope note.

## Live Docker verification (independent, own throwaway project — not the manifest's)

`docker compose restart` (container had only been up 2 minutes; restarted anyway to force this
unit's code to load — uvicorn has no `--reload`), waited for `curl http://localhost:8010/` → 200
(first try after restart completed).

Seeded a throwaway project `checker-ui-report-demo` via `ProjectStore` (one NAVIGATE-only case
`homepage loads` against `http://localhost:8000/`, the container's own UI server), triggered
`POST /projects/checker-ui-report-demo/run` twice:

```
run1: 303
run2: 303
```

- **UR1 (real run history):** `GET /projects/checker-ui-report-demo/report` → both real run ids
  present (`run-01M1NBWFZ0HMJPF0A50M9NVV7X`, `run-01M1NBWR22HRKAMNG3THX8ZBJD`). Byte-offset check
  confirms newest-first: the second-triggered run (`...WR22...`) appears at offset 33, the
  first-triggered run (`...WFZ0...`) at offset 10762. Each row carries its own outcome counts
  and links to `/runs/{run_id}`. Confirms UR1.
- **UR2 (real inline screenshots):** `GET /projects/checker-ui-report-demo/runs/run-...WR22...`
  → contains exactly one `data:image/png;base64,` image, a real screenshot read from the actual
  run directory via `png_base64`. The "no screenshot evidence" honest-empty-state path is also
  covered by the manifest's own unit test (`test_run_view_says_so_honestly_when_a_case_has_no_screenshots`),
  which I re-ran above. Confirms UR2.
- **UR3 (real portable downloads, no reimplementation):**
  `GET /projects/checker-ui-report-demo/report.xlsx` → 200, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  5100 bytes, verified a genuine `Microsoft Excel 2007+` file via `file`.
  `GET /projects/checker-ui-report-demo/report.html` → 200, `text/html`, 49412 bytes, containing
  the real case title `homepage loads`. Both stream `report_export.export_excel`/`export_html`'s
  own output (code review: `routes_report.py` calls the exact same functions, writes to a
  reserved temp path, cleans up via `BackgroundTask`) — no second export implementation.
  Unknown-project 404 also re-verified live: both `/projects/nope-not-real/report.xlsx` and
  `.../report.html` → 404, before any export function runs. Confirms UR3.
- **UR4 (never a second source of truth):** code review of `routes_report.py` confirms every
  route reads only through `ProjectPaths`/`ProjectStore` and the shared `report_export` module —
  no duplicated logic. Confirms UR4.

Cleaned up afterward: `rm -rf projects/checker-ui-report-demo profiles/checker-ui-report-demo` —
`git status --short` shows no leftovers, `ls projects/` shows only the pre-existing `pathlynks`
and `regression-demo`.

## Issues addressed

Manifest claims none — correct, no ledger rows were claimed fixed by this unit.

## New finding (does not block PASS — cosmetic only)

**AT-040** (low, filed to `qa/issues.jsonl`): `src/autotester/ui/app.py`'s module docstring
(lines 1-7) still says "Run-trigger/report routes live in `ui/routes_runs.py`" — stale since
`report()`/`run_view()` moved to `ui/routes_report.py` this unit. No functional impact; both
routers are correctly wired (`app.py` lines 42-43). Not a contract criterion, so it does not
gate this PASS, but flagged for the next touch of `app.py`.

## Explanation

All four criteria (UR1-UR4) are evidenced by my own re-run of the test suite, static checks, and
an independent live-Docker round trip against a throwaway project I seeded and cleaned up myself
(distinct run ids from the manifest's own verification, so this is not a re-read of pasted
output). The `_b64_png` → `png_base64` rename is clean with no orphaned references. One cosmetic
doc-drift issue (AT-040) filed but does not affect PASS.
