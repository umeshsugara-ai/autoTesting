# Manifest — ui-run-view-flow-and-lightbox

**Contract:** qa/contracts/ui-report.md UR2 (screenshot rendering, unchanged meaning — richer
presentation of the same evidence)
**Goal task:** none (`.goal/goal.json` is 20/20 done — direct user feedback, not a plan section)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none (fresh user feedback, not a filed ledger issue)

## Why this unit

Two pieces of direct feedback, both logged verbatim in `qa/feedback-inbox.md`:

1. After seeing the just-shipped report/run-view fix (F-027) live, Umesh said the thumbnails
   were readable but too small to read detail — asked via `AskUserQuestion` whether to add a
   click-to-enlarge lightbox, make thumbnails bigger directly, or leave as-is. Chose
   **click-to-enlarge lightbox**.
2. Mid-build, Umesh sent "/workflow-diagram type kuch add kro" — wants a workflow/flow-diagram
   view. This is exactly the deferred idea from earlier in the session
   (`qa/feedback-inbox.md`'s mindmap/flow-diagram entry), already **re-scoped** by Umesh's own
   prior instruction to a **DFS-style trace** (the literal sequence of screens one case actually
   walked through) rather than a full BFS branch tree — so this unit builds that re-scoped
   version, not a new/bigger feature.

Both land on the same page (`run_view`) and the same underlying data (`RawResult.evidence`), so
built as one unit rather than two.

## What changed

- `src/autotester/ui/routes_report.py`:
  - `_shots()` renamed to `_step_flow(run_dir, evidence, case_index)` — screenshots are now
    **sorted by `Evidence.step_order`** (falling back to arrival order when absent) and rendered
    as a connected sequence (`.flow-step` thumbnails joined by `.flow-arrow` "→" separators) —
    the actual DFS path this case took, not a grid.
  - Each thumbnail is now an `<a href='#lb-{case_index}-{i}'>` linking to a same-page, CSS-only
    lightbox overlay (`<a class='lightbox' id='lb-...'>`, shown via the `:target` pseudo-class)
    — clicking anywhere on the overlay (including the image) navigates back to `#`, closing it.
    No JavaScript, matching this project's server-rendered-HTML-only UI constraint.
  - `run_view()` passes each case's index into `_step_flow` so lightbox ids are unique across
    every case on the page, not just within one case.
- `src/autotester/ui/theme.py`:
  - Replaced the `.shots`/`figure` grid CSS with `.flow`/`.flow-step`/`.flow-arrow` (a wrapping
    horizontal sequence, hover state on the thumbnail border) and new `.lightbox`/
    `.lightbox-caption` CSS (fixed full-screen dark overlay, `max-width: 94vw; max-height: 88vh`
    on the enlarged image, a caption pill reusing the step's own label).
- `tests/test_ui_report.py` (+2 tests) — a screenshot's thumbnail links to a matching
  `id='lb-...'` lightbox target; step flow order follows `step_order` even when the underlying
  evidence list arrives out of order (the actual DFS-correctness guarantee, not just presence).
- `qa/feedback-inbox.md` — both source entries marked resolved, cross-referencing this manifest
  and explaining the DFS-scope match to the earlier mindmap-idea refinement.

## Deliberate scope decisions

- This is **not** the full BFS/mindmap branch tree from the original, since-superseded idea
  (every worst/edge/best path merged into one diagram) — Umesh's own 2026-09-04 refinement
  explicitly re-scoped that to "the one path a given run actually took, DFS-style," and this
  unit builds exactly that, per-case, on the page that already has the data. A cross-case merged
  tree remains a separate, bigger, still-not-requested idea.
- No JavaScript — the lightbox is pure CSS (`:target`), consistent with every other page in this
  UI (server-rendered HTML/CSS only, no build step, no JS framework).

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui_report.py -v   # 11 passed (9 existing + 2 new)
$ uv run pytest -q                            # full suite green, no regressions
$ uv run ruff check src tests scripts         # All checks passed!
$ uv run autotester doctor                    # doctor: clean
```

**Real live Docker + real browser click (Playwright), against the exact `pathlynks` run from
Umesh's own earlier screenshot:**

- `docker compose restart` → `curl http://localhost:8010/` → 200.
- Navigated to `/projects/pathlynks/runs/run-01M1N7EE6GRBZ4RK4Q0QYK0ZF5` — screenshotted: three
  cases each show a connected step sequence (`step01-navigate → step02-fill → step03-fill →
  step04-click → best-final`, arrows between each) instead of a bare grid.
- **Clicked the first thumbnail with a real Playwright click** (not simulated) — URL correctly
  gained `#lb-0-0`, and the resulting screenshot shows a genuine full-size, real Pathlynks
  sign-in screenshot in a dark-backdrop overlay with a "step01-navigate" caption pill — the
  lightbox actually opens and shows real evidence, not a placeholder.

## How to verify

- `uv run pytest tests/test_ui_report.py -v` → 11 passed.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- Open any real run's detail page, click a screenshot thumbnail — confirm a full-size lightbox
  opens with the real image and a caption, and that the surrounding steps render as a connected
  left-to-right sequence, not a plain grid.

## Scope notes for the checker

- Please read both feedback-inbox entries this unit resolves (the lightbox follow-up and the
  DFS-scoped flow-diagram refinement) and judge whether this genuinely satisfies both, at the
  scope Umesh actually asked for — not a smaller nor a bigger feature than requested.
- Please do your own real click on a live thumbnail (Playwright or otherwise) rather than just
  grepping for the `:target` CSS — "does it actually open" is the real claim here.

## Status: ready-for-check
