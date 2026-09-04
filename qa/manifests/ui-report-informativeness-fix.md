# Manifest — ui-report-informativeness-fix

**Contract:** qa/contracts/ui-report.md UR1-UR4 (unchanged behavior, presentation fix)
**Goal task:** none (`.goal/goal.json` is 20/20 done — direct user feedback, not a plan section)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none (fresh user feedback, not a filed ledger issue)

## Why this unit

Umesh, on a real screenshot of `/projects/pathlynks/report`: "still very bad ui and very non
professional ... no summary, no overview" — the run-history table rendered a full-size `.stat`
tile (the ~2rem serif number meant for one page-level headline) once per row, producing a wall
of oversized, disconnected numbers with no aggregate view of the project's health.

On a real screenshot of `/projects/pathlynks/runs/<run-id>`: "non informational too, big images
and all" — `ui/theme.py` had **zero CSS for `.shots`/`figure`/`img`**, so every screenshot
rendered at its native capture resolution (full desktop-sized PNGs), and the only per-case text
was a one-line outcome + badge — no scoreboard, no grader, no failure reasons.

Logged verbatim to `qa/feedback-inbox.md` before building (per the feedback-inbox hard rule).

## What changed

- `src/autotester/ui/theme.py`:
  - `badge(value, count=None)` — new optional `count` param renders a compact "N RESULT" pill
    (e.g. "✓ 3 PASS") reusing the existing color/icon lookup, for a run-history row's summary.
    Backward compatible — every existing `badge(x)` call is unaffected.
  - New CSS: `.run-results`/`.run-date` (compact history-row styling), `.case-meta`/
    `.scoreboard`/`.failure-list` (richer per-case info), and — the actual bug fix —
    `.shots`/`figure`/`img`/`figcaption` (a responsive `auto-fill` thumbnail grid, `width: 100%;
    height: auto` on the image itself, so a screenshot can never again render at native pixel
    size and dominate the page).
- `src/autotester/ui/routes_report.py`:
  - `report()` — added a real overview: **Total runs**, **Overall pass rate** (aggregated across
    every run's verdicts, not just the latest), **Cases in latest run** — three `theme.stat`
    tiles, the appropriate place for that component (one page-level headline each, not one per
    table row). The run-history table now uses `_counts_badges` (compact pills via the new
    `count=` param) instead of `_counts_stats` (the old giant-tile misuse), plus a real date per
    run (`store.load_run(run_id).created_at`, via the pre-existing but previously-unused
    `load_run`).
  - `run_view()` — each case's card now shows outcome + result badge + grader provider on one
    line (`.case-meta`), the verdict's own `scoreboard` text ("Criteria 2/2 met."), and — for a
    FAIL — the actual cited failures (`criterion_id`, `reason`, `fix_hint`) as a real list, not
    silently dropped. Screenshots render through the new `.shots` grid.
- `tests/test_ui_report.py` (+4 tests) — overview shows the three headline stats with a correct
  aggregate pass rate; history rows use `.run-results` badges, never a `.stat` tile, inside the
  "Run history" section; a PASS case's scoreboard + "judged by <provider>" line render; a FAIL
  case's failure reason + fix hint render.
- `.gitignore` — added `projects/*/rubrics/` (lazily-generated derived state, same category as
  the already-ignored `projects/*/runs/`; noticed as untracked cruft from earlier live
  verification while checking `git status` for this commit, unrelated to this fix's own code).

## Deliberate scope decisions

- No lightbox/click-to-enlarge on screenshots — the fix is that they no longer render at native
  size by default; a thumbnail grid is the honest v1, a future enhancement if still wanted.
- `run_view`'s own top-of-page stat row (`_counts_stats`, kept as-is) is a legitimate use of
  full-size `.stat` tiles — it is a genuine page-level headline (this run's own outcome mix),
  not a per-row repetition, so it was NOT changed.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui_report.py -v   # 9 passed (5 existing + 4 new)
$ uv run pytest -q                            # full suite green, no regressions
$ uv run ruff check src tests scripts         # All checks passed!
$ uv run autotester doctor                    # doctor: clean
```

**Real live Docker verification against the exact project from Umesh's screenshot
(`pathlynks`, not a throwaway demo — read-only GET requests only, no run triggered):**

```
$ docker compose restart && curl http://localhost:8010/   # 200
$ curl http://localhost:8010/projects/pathlynks/report
```
- `Total runs`, `Overall pass rate`, `Cases in latest run` all present — a real overview, not
  just a bare table.
- 17 occurrences of `class='run-results'` in the body (one per history row's compact badge
  group across pathlynks' 16 real recorded runs) — zero `.stat` tiles inside the "Run history"
  section (confirmed by grepping only the text after the "Run history" heading).

```
$ curl http://localhost:8010/projects/pathlynks/runs/run-01M1N7EE6GRBZ4RK4Q0QYK0ZF5
```
- All 3 cases show `completed` outcome, `judged by gemini`, and `Criteria 1/1 met` — real
  scoreboard/grader info that was previously invisible.
- 13 real screenshots render inside 3 `.shots` grid containers (one per case) with the new
  `width: 100%; height: auto` CSS actually present in the served page — confirmed the fix (no
  more native-resolution images) reaches the real browser, not just the template string.
- Also checked an `errored` run (`run-01M1K3DDACZ1AJ7BJPMX7A5KYF`, pre-dating the login-test
  redirect-race fix) — correctly shows `errored` outcome and "no screenshots captured" for the
  case with none, confirming the richer rendering degrades honestly for old/broken runs too.

## How to verify

- `uv run pytest tests/test_ui_report.py -v` → 9 passed.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- `docker compose restart`, then open `/projects/pathlynks/report` and
  `/projects/pathlynks/runs/<any-real-run-id>` in a real browser — confirm an overview with
  three headline stats, compact per-run badges (not giant numbers) in the history table, and
  screenshots that render as a reasonable thumbnail grid, not full native size.

## Scope notes for the checker

- This is a direct response to Umesh's own screenshots/words in `qa/feedback-inbox.md`
  ("2026-09-04 — Umesh, on report/run-view UI quality") — please read that entry and judge
  whether the fix actually addresses what he pointed at (no summary/overview; big, non-
  informative images) rather than just the contract's pre-existing UR1-UR4 text, which this
  unit does not change the meaning of.
- Please take your own screenshot (or at least inspect the served CSS) of a real run's page —
  "images no longer huge" is a visual claim as much as a functional one.

## Status: ready-for-check
