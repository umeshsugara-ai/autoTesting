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

## Status: checked-PASS

Verdict: `qa/verdicts/track-b5-crawl-merge-report.md` (**Cycle checked: 1**, PASS, 20/20 criteria,
12/12 invariants). The checker authored **X13-X16** in `explore.md` and **amended `coverage.md` V1
+ added V5**, and it did not rubber-stamp what I proposed:

- **X14 upheld but restated.** My "two screens from the same crawl sharing a url_pattern is not a
  conflict" exception was accepted on its merits and rewritten as a principle -- *"sources
  disagree, not patterns collide"* -- rather than left as a carve-out. Two residuals were then
  recorded **inside** the criterion instead of letting it read clean: **AT-103** (my exemption is
  scoped to one *crawl*, not one *source*, so a re-crawl DOES file false conflicts -- proven live:
  0 conflicts when merged in one call, 1 when merged as c1 then c2) and **AT-102** (the clash test
  keys on the name string, so a same-name re-discovery is a silent duplicate).
- **X13 gained a mandatory sabotage clause** -- "a gate no test defends is decorative" is now
  contract text, not just something I asked for once.
- **My own count was wrong.** The manifest says 33 targeted tests; there are 39. Recorded by the
  checker rather than filed. Noted here so the next manifest counts before it claims.

**The adversarial check I asked for was decisive, and its failure mode is worth keeping.** Mutating
`merge_screens`'s `status=ReviewStatus.DRAFT` to `status=spec.review.status` **fails**
`test_new_screens_are_added_and_review_resets_to_draft` -- the human approval gate is defended by a
real test, and a crawl cannot silently keep a FlowSpec "approved" after adding screens nobody
reviewed. The checker also documented a trap it hit first: `PYTHONPATH` loses to `/app/src` under
this repo's pytest, so a sabotage applied in a *copied* tree is never loaded and everything passes
-- which reads exactly like "the gate is decorative". The mutation has to be on the real file.

Also verified independently: idempotent re-merge is byte-identical (same sha256, not just the same
version number); reverting `_path_of` fails 3 tests; no `fill`/`select_option`/`upload` anywhere in
the new modules (X10); `scripts/explore_proof.py` still 10/10 (B3 did not regress).

**Filed for me to act on:** **AT-104 (medium, before T-145)** -- the UI merge button sends the spec
back to DRAFT and redirects to a page that renders no review status anywhere. The CLI says it
explicitly; the UI does not. The gate is armed and the human is not told. Also AT-102, AT-103,
AT-105. `T-144` closed in `.goal/goal.json` (27/36, 75%); ledger row **F-035**.
