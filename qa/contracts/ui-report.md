# Contract — ui-report (run history, inline screenshots, portable downloads)

**Status:** ACTIVE. Extends `qa/contracts/ui.md` U4 and `qa/contracts/ui-run.md`'s own
no-fire list, which deferred this ("report enrichment ... is plan §3c, a separate unit").

## Why this exists

Umesh: a non-technical user must be able to see and download the report without a terminal.
Before this, `/projects/{slug}/report` only showed the latest run's counts, and per-case
evidence (screenshots) was only visible by opening a run directory on disk.

## Criteria

- **UR1 — real run history.** `GET /projects/{slug}/report` lists every run under
  `paths.runs_dir`, newest first, each with its own outcome counts and a link to
  `/projects/{slug}/runs/{run_id}`. A project with zero runs still shows the existing honest
  empty state, unchanged.
- **UR2 — real inline screenshots.** `GET /projects/{slug}/runs/{run_id}` embeds every
  `SCREENSHOT`-kind evidence entry for each case as a real `<img>` (base64, read from the
  actual run directory on disk via the shared `report_export.png_base64` helper) — never a
  broken link, never a placeholder. A case with no screenshot evidence says so honestly.
- **UR3 — real portable downloads, no second export path.** `GET /projects/{slug}/report.xlsx`
  and `GET /projects/{slug}/report.html` stream the exact same file
  `report_export.export_excel`/`export_html` would produce for a run (default: the latest),
  via a real temp file that is deleted after the response is sent — never a second,
  UI-only reimplementation of the export logic.
- **UR4 — never a second source of truth.** Every route in this contract reads only through
  `ProjectStore`/`ProjectPaths`, exactly like every other UI route (design principle 8).
- **UR5 — run history contains only real Run envelopes, in truthful order.** A directory under
  `runs/` is listed and counted only when its persisted `Run` loads successfully, its id matches
  the directory name, and its project matches the current project. Runs are ordered newest-first by
  timezone-normalized `Run.created_at`, not by directory name. An unknown run id returns a themed
  HTTP 404 rather than a fabricated empty run page.
- **UR6 — the headline describes the newest run and names its denominator.** The displayed pass
  rate is computed only over the selected newest run's real `case_ids`, and is labelled as a
  latest-run metric alongside `N` cases and `M` distinct persisted flows. Historical reruns,
  onboarding directories, crawl directories, stray files, duplicate verdict rows, and verdicts for
  cases outside that run cannot inflate either numerator or denominator. A Mode-D browser check must
  interact with the report and unknown-run routes and record zero unexplained console errors.

## No-fire list (out of scope for this contract)

- `/settings/providers` (plan §3d) — a separate unit/contract.
- Any change to what `report_export.export_excel`/`export_html` actually produce — this
  contract only covers streaming the existing, already-checker-PASSed export functions from a
  live route.
- Pagination of run history for a project with a very large number of runs — a real project
  today has single-digit run counts; revisit if that changes.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for the run history/inline screenshots/portable downloads
  unit (plan §3c, UR1-UR4), checker-PASSed cycle 1 (`qa/verdicts/ui-report-enrichment.md`,
  ledger F-025).
- 2026-09-04 · routine · presentation-only fix (`ui-report-informativeness-fix`, ledger F-027,
  amends F-025) — overview stat tiles, compact per-run badges, richer per-case scoreboard/
  grader/failure info, and responsive screenshot CSS. UR1-UR4 wording unchanged; checker
  confirmed no criterion was reinterpreted or weakened (`qa/verdicts/ui-report-informativeness-fix.md`).
- 2026-09-10 · routine · **UR5–UR6 added** — folds the T-100 real-browser re-close feedback.
  Run history now has an explicit validity and chronological-order bar, missing runs must be true
  404s, and the headline must be a latest-run pass rate with its case and distinct-flow denominator.
  Tightening only; UR1–UR4 are unchanged.
