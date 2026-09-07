# Manifest — track-b5-crawl-merge-report
**Contract:** `qa/contracts/explore.md` (X1–X12 must stay intact) + `qa/contracts/coverage.md`
(V1) + `qa/contracts/ui.md`. **This unit requests four new criteria (X13–X16) and a V1 amendment**
— filed verbatim in `qa/feedback-inbox.md` (2026-09-08 entry) for the checker to author, tighten
or reject. Contracts are checker-owned; the maker never writes one.
**Goal task:** T-144
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §5 "B5 — crawl → FlowSpec, coverage, report, UI", authorised by D-015
**Issues addressed:** none directly (AT-096 remains open and is unrelated)

## What this closes
Track B's last unit. Before it, `autotester explore` wrote a screen graph to disk that **nothing
read** — no page rendered it, no export produced it, and it could not reach the FlowSpec. The
crawl was real and invisible.

## What changed
- **New** `stages/explore_merge.py` (127) — `screen_from(node)` and `merge_screens(spec, nodes,
  project, *, crawl_id)`. Never rewrites an existing screen; a real change resets `Review` to
  DRAFT and bumps `version`; re-merging the same crawl is a no-op.
- `stages/coverage.py` (63 → 100) — `diff_crawl`, `unreached_screens`, and `_path_of` now
  normalises through `core.urls.url_template(..., keep_host=False)` **on both sides**.
- **New** `stages/crawl_report.py` (138) — `crawl_summary` + `export_crawl_excel` (Summary /
  Screens / Edges / Denied & Skipped / Issues / Noise).
- **New** `core/excel.py` (21) — `autosize_columns` **extracted from** `report_export.py` rather
  than copied into the second exporter (C3). `report_export.py` now calls it.
- **New** `ui/routes_crawls.py` (174) + `ui/crawl_view.py` (149) — crawl list, crawl page (screen
  tree by `discovered_by`, thumbnails, refusals, issues, both-direction coverage), `report.xlsx`,
  `POST …/explore`, `POST …/crawls/{id}/merge`. Split in two to stay under the 300-line cap.
- `ui/app.py` — router registered, "🕸 Crawls" added to the project action row.
- `ui/helpers.py` — `_reserved_temp_path` **moved here** from `routes_report.py`; three download
  routes now need it (C3).
- `ui/theme_style.py` — `.data-table`, `.crawl-tree`, `.crawl-node`, generic `.meta`.
- **New** `cli_crawl.py` (99) — `explore` **moved verbatim** out of `cli.py` (272 → 227, which was
  4 lines from its cap) and extended with `--merge`; new `report crawl`. Both mounted onto the
  same typer apps in `cli.py`, so the CLI surface a user sees is unchanged.
- `.gitignore` — `projects/*/crawl/*/shots/` (D-015 authorised this and it was missing).
- Tests: **new** `test_explore_merge.py` (11), `test_crawl_report.py` (6), `test_ui_crawls.py`
  (10); `test_coverage.py` +6.

## Found by running it, not by reasoning about it
A real crawl of the fixture site produced **7 screens across 6 url patterns** — the index page's
filter toggle is two structurally distinct screens at one URL, exactly as X3 requires. My first
conflict rule would have filed a **false `Conflict` on every SPA**. Corrected so a conflict is
only raised against a *pre-existing* screen claim, and pinned by
`test_two_spa_states_at_one_url_are_two_screens_not_a_conflict`. This is flagged to the checker in
the inbox as the one judgement call in this unit (X14).

## Live end-to-end (REAL browser, no credentials) — pasted, not summarised
```
$ docker compose exec -T autotester uv run python .work/b5_e2e.py
crawl: 7 screens, stop=frontier empty, denied=8
merge 1: 7 screens, v2, review=draft
merge 2 (idempotent?): 7 screens, v2, fingerprint same=True
coverage after merge: gaps=0 unreached=0
excel: ['Summary', 'Screens', 'Edges', 'Denied & Skipped', 'Issues', 'Noise'] — refusals=8 screens=7
patterns: ['/', '/dialog.html', '/reports.html', '/settings.html', '/students', '/students/{id}']
```
`/students/1` and `/students/2` collapsing to `/students/{id}` is the templating working end to
end. The scratch script is not committed (`.work/` is scratch by C4); it is reproducible from the
steps above and the checker should write its own rather than reuse mine.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → **549 passed, 1 skipped** (516 before)
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- `docker compose exec -T autotester uv run python scripts/explore_proof.py` → `10/10 invariants
  held`, exit 0 — **B3 must not regress**; re-run because `coverage.py` and `cli.py` both changed.
- `docker compose exec -T autotester uv run pytest tests/test_explore_merge.py
  tests/test_crawl_report.py tests/test_ui_crawls.py tests/test_coverage.py -q` → 33 passed

## Adversarial checks worth making
1. **Prove the merge cannot launder an approval.** Set a FlowSpec to `APPROVED`, merge a crawl
   with one new screen, and confirm the spec is DRAFT again. Then sabotage the `Review(...)` reset
   in `merge_screens` and confirm a test fails — if none does, the human gate is decorative.
2. **Prove the idempotence claim is not vacuous.** Merge the same crawl twice and diff
   `flowspec.json` byte-for-byte, not just the version number.
3. **Prove the coverage fix is real.** On the pre-T-144 code, `/students/1` vs `/students/{id}`
   produced a gap. Confirm the new test fails if `_path_of` is reverted to `urlsplit(url).path`.
4. **X10 still holds:** grep the new modules for `fill`/`select_option` — the merge and report
   paths must not have introduced any typing.

## What this unit does NOT do (deliberately)
Model-named screens (`prompts/explore_name_screen_v1.md` designed for, not built — the crawl stays
provider-free per X12); background/async crawling; merging crawl-discovered *flows*; auto-expanding
cases from crawled screens (that is `expand.py`, after human review).

## Status: ready-for-check
