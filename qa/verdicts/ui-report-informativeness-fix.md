# Verdict — ui-report-informativeness-fix

**Date:** 2026-09-04
**Cycle checked:** 1
**Contract:** qa/contracts/ui-report.md (UR1-UR4, unchanged; presentation-only fix)
**Manifest:** qa/manifests/ui-report-informativeness-fix.md

## What I re-ran myself

Shell (fresh, not trusted from the manifest):
```
uv run pytest tests/test_ui_report.py -v   → 9 passed
uv run pytest -q                            → full suite green (2 pre-existing skips, unrelated)
uv run ruff check src tests scripts         → All checks passed!
uv run autotester doctor                    → doctor: clean
```

Live Docker, read-only GETs against the real `pathlynks` project on the container already
restarted with this fix's code (no POST /run issued, per instructions):

- `GET /` → 200. `GET /projects/pathlynks/report` → 200, saved to disk and inspected byte-for-byte:
  - `Total runs`, `Overall pass rate`, `Cases in latest run` text present.
  - Exactly 3 `class='stat'` tiles in the whole page (byte offsets 11242/11328/11422), all
    located **before** the `Run history` heading (offset 11539) — i.e. the overview owns every
    stat tile and the history table has zero. This is the concrete fix for "no summary, no
    overview" / giant-tile-per-row.
  - 16 `class='run-results'` compact-badge groups (one per history row across pathlynks' 16
    real runs) inside the table.
- `GET /projects/pathlynks/runs/run-01M1N7EE6GRBZ4RK4Q0QYK0ZF5` → 200, 3 `.shots` grids, 13
  inline base64 `<img>` tags, the served `<style>` block contains
  `.shots img { width: 100%; height: auto }` (the actual CSS fix reaching the real page, not
  just the template string), 3 `class='case-meta'` + 3 `class='scoreboard'` blocks showing
  "Criteria 1/1 met." and "judged by gemini".
- `GET /projects/pathlynks/runs/run-01M1K3DDACZ1AJ7BJPMX7A5KYF` (an `errored` run) → 200,
  shows `errored` outcome honestly and "no screenshots captured" for the case with none —
  richer rendering degrades honestly on old/broken runs.
- `GET /projects/pathlynks/report.xlsx` → 200, 5277 bytes. `GET /projects/pathlynks/report.html`
  → 200, 2367788 bytes. UR3 downloads unaffected by this fix (regression check, contract's
  no-fire list confirms this unit doesn't touch export logic).

Code inspection (`src/autotester/ui/theme.py`, `src/autotester/ui/routes_report.py`,
`tests/test_ui_report.py`) confirms the manifest's description of the diff is accurate:
`badge(value, count=None)` is backward compatible, `.shots`/`figure`/`img` CSS is new and sets
`width:100%; height:auto`, `_counts_badges` replaces `_counts_stats` in the history table while
`run_view`'s own top stat row is deliberately untouched (a genuine page-level headline, matches
the contract's `stat` tile intent), and the 4 new tests
(`test_report_shows_an_overview_summary_not_just_a_bare_history_table`,
`test_run_history_rows_use_compact_badges_not_full_size_stat_tiles`,
`test_run_view_shows_scoreboard_and_grader_not_just_a_bare_badge`,
`test_run_view_shows_failure_reasons_for_a_fail`) assert real, specific text/markup, not
superficial presence checks.

## Feedback-inbox judgment (the actual bar for this unit)

Read `qa/feedback-inbox.md` § "2026-09-04 — Umesh, on report/run-view UI quality" verbatim:

1. "no summary, no overview" on `/projects/pathlynks/report` → **addressed.** The live page now
   leads with three real headline stats (Total runs / Overall pass rate — aggregated across all
   16 runs, not just the latest / Cases in latest run) before the run-history table, and the
   table itself no longer misuses full-size stat tiles per row.
2. "non informational too, big images and all" on `/projects/pathlynks/runs/<run-id>` →
   **addressed.** Screenshots now render in a responsive `auto-fill` thumbnail grid with
   `width:100%; height:auto` (confirmed in the served CSS, not just the source), and each case
   card gained a scoreboard line, grader-provider attribution, and cited failure reasons/fix
   hints for FAILs — replacing the previous single outcome+badge line.

Both Hindi/Hinglish complaints are concretely fixed by what's live on the container, not just by
text that happens to still satisfy UR1-UR4's pre-existing wording.

## Criteria (UR1-UR4, contract meaning unchanged by this unit)

- [C-UR1] real run history — MET (16 real runs listed newest-first, each linking to its run
  page; the informativeness fix only changed presentation of the summary column).
- [C-UR2] real inline screenshots — MET (13 real base64 images rendered via `png_base64`, honest
  "no screenshots captured" for a case with none, now additionally displayed responsively).
- [C-UR3] real portable downloads, no second export path — MET (both endpoints 200, unchanged
  code path, this unit's no-fire list explicitly excludes export logic).
- [C-UR4] never a second source of truth — MET (`ProjectStore`/`ProjectPaths`/`report_export`
  are the only data sources in the diff; no new parallel read path introduced).

No invariants in `qa/contracts/core-invariants.md` are implicated by a presentation-only CSS/HTML
change (no secrets, no new writes, no new provider calls).

## Issues addressed

None claimed by the manifest (fresh feedback, not a ledger issue) — none checked.

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 0/0 invariants hold (none implicated)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: Both feedback-inbox complaints (no overview/summary; oversized non-informative
screenshots) are verifiably fixed on the live pathlynks container, not just still-compliant with
UR1-UR4's pre-existing text. All shell verifications reproduced cleanly, and live GETs against
real project data confirm the overview stat tiles sit outside the history table, per-run badges
replaced the giant tiles, screenshot CSS reaches the served page, and case cards now show
scoreboard/grader/failure info.
