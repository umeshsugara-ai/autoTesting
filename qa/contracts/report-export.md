# Contract — Tester report export (new, 2026-09-04)

**Covers:** ad-hoc unit `report-export` (no `.goal` task). **Owner:** /checker.
**Criticality:** MEDIUM — a reporting/export feature, reads existing evidence only.
**Depends on:** `execute.md`/`grade.md` (the `RawResult`/`Verdict` shapes exported), `ui.md`
design principle 8 (never a second source of truth).

## Purpose

Umesh: "testing hone ke baad step by step, like an Excel sheet and an HTML report with
screenshots, screen by screen, proper reporting as a tester." `autotester report excel/html
<slug> [run_id]` turns an existing run's evidence into two portable, shareable artifacts — an
`.xlsx` summary and a self-contained `.html` walkthrough with embedded screenshots — without
ever inventing or recomputing anything not already in `RawResult`/`Verdict`.

## Criteria

### RE1 — Reads only existing evidence, never a new source of truth
Both exporters read exclusively through `ProjectStore` (`list_cases`, `load_results`,
`load_verdicts`) — no new data model, no recomputed verdict, no hand-typed number.

### RE2 — Excel: one row per case, real fields only
`export_excel` produces one row per `RawResult` in the run: case title, kind, class, outcome,
verdict result, criteria met/total, duration, grader, and either the verdict's scoreboard or the
raw error — verbatim from the stored artifacts, not summarized or reworded.

### RE3 — HTML: self-contained, portable, one section per case
`export_html` produces a single `.html` file with every screenshot embedded as a base64 data URI
— opening the file needs no other file on disk, no server, no network. One section per case, in
run order, showing the case title, its result badge, and every screenshot captured for it.

### RE4 — Defaults to the latest run when none is named
Both CLI commands accept an optional `run_id`; omitting it uses the most recent run for that
project (matches the existing `ui/app.py::report` route's own "latest run" convention).

### RE5 — No secret ever reaches an exported file
Screenshots are already masked before capture (B7, unchanged); scoreboards/errors are whatever
the grader already redacted. This contract adds no new secret-handling path — it inherits the
existing guarantee, and `scripts/check_no_secrets.py` must pass clean on both exported files
against a project touching real credentials.

## No-fire list

- Any new run-triggering, grading, or execution logic — this is read-only export over data that
  already exists.
- A PDF exporter, a scheduled/automatic export, or upload to any external service — out of
  scope; a human runs the CLI command and gets a local file.
- Styling parity with the live UI theme (`ui/theme.py`) — the exported HTML has its own minimal,
  self-contained stylesheet; sharing CSS with the live server would break the "one portable file"
  property (RE3) the moment `ui/theme.py` changes.

## Amendment log (append-only; git history is the version)

- 2026-09-04 · init · contract created for the report-export unit.
