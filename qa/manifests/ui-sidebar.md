# Manifest — ui-sidebar

**Contract:** qa/contracts/ui-sidebar.md US1-US5 (new this cycle)
**Goal task:** none (`.goal/goal.json` is 20/20 done — direct user feedback, not a plan section)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Umesh: "add these TOC features" — clarified via `AskUserQuestion` into a concrete scope: a
persistent sidebar listing every onboarded project on every page, so switching projects doesn't
require going back to the homepage first.

## What changed

- `qa/contracts/ui-sidebar.md` (new) — US1 (every page, one place — a single change to
  `theme.page()`) · US2 (real `ProjectStore` data, no second source of truth) · US3 (active
  project visibly distinguished) · US4 (honest empty state) · US5 (pure layout wrapper, no
  existing route's own content changes).
- `src/autotester/ui/theme.py` — new `_sidebar_html(active_slug)`: lists every project from
  `_project_slugs()`/`ProjectStore` (the same lookup `index()` already uses — no second source
  of truth), each showing its real declared name, marked `.active` when it matches. `page()`
  gains an optional `active_slug` param and now wraps `<aside class='sidebar'>` + `<main>` in a
  `<div class='layout'>` flex container.
- `src/autotester/ui/theme_style.py` — `.layout`/`.sidebar`/`.sidebar-link`/etc CSS: a sticky
  220px column (offset below the topbar), hover/active states reusing the existing accent
  token, collapses below 780px viewport width (mobile falls back to the top nav's own
  "Projects" link).
- `src/autotester/ui/app.py`, `routes_credentials.py`, `routes_flow_diagram.py`,
  `routes_report.py` — every project-scoped `theme.page(...)` call now passes
  `active_slug=slug`. Global pages (`index`, `onboard`, `live_view`, `settings`) are unchanged
  — no active project to highlight.
- `tests/test_ui_sidebar.py` (new, 6 tests) — honest empty state; every project listed by real
  name; present on every page type (home/onboard/live/project/settings); active project
  highlighted only on its own pages; a global page highlights nothing; existing page content
  (case list, headings) unaffected by the wrapper change.
- `tests/test_ui.py` — `test_live_view_touches_no_project_state` updated: the sidebar
  legitimately varies with project state now (the same "surrounding chrome" precedent
  `qa/contracts/docker.md` D5 already established for the original theme wrapper) — the test now
  checks `/live`'s own `<main>` content is unchanged, not full-page byte equality. `/live`'s own
  route function still calls zero `ProjectStore`/`SecretStore` methods (D4's actual, narrower
  claim), confirmed by reading the route — only the shared wrapper changed.

## Deliberate scope decisions (per the contract's own no-fire list)

- No collapse/search/filter UI for the sidebar itself — a real project list today is small
  (2 onboarded projects); revisit if that changes.
- No per-project stats in the sidebar (case counts, latest result) — it's a navigation index,
  not a second dashboard; `index()`'s own project-card grid already covers that.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui_sidebar.py -v   # 6 passed
$ uv run pytest -q                             # full suite green (one pre-existing test's
                                               #   assertion updated for the new legitimate
                                               #   sidebar variability, not a regression)
$ uv run ruff check src tests scripts          # All checks passed!
$ uv run autotester doctor                     # doctor: clean
$ uv run python -c "from autotester.ui.app import app"  # confirms no circular import
                                                          # (theme.py -> ui.helpers -> store)
```

**Real live Docker verification** — `docker compose restart`, real screenshot of
`/projects/pathlynks/report`: sidebar renders on the left, sticky below the topbar, "Pathlynks"
shown with the active amber highlight, "Regression Proof Demo" (the project's real declared
name) listed as the second real onboarded project, "+ New project" link at the bottom — matches
the design exactly, no layout overlap or clipping.

## How to verify

- `uv run pytest tests/test_ui_sidebar.py -v` → 6 passed.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- Open any page in a real browser — confirm the sidebar lists every real onboarded project, the
  current one is highlighted on its own pages, and every existing page's own content is
  otherwise unchanged.

## Scope notes for the checker

- Please confirm US5 specifically — that no existing route's own body HTML, escaping, or data
  changed, only the shared wrapper. The `test_live_view_touches_no_project_state` test update is
  itself worth double-checking: is the new assertion (unchanged `<main>` content) a faithful,
  non-weakened re-reading of D4's actual claim (the *route* touches no project state), or does it
  paper over something real? I believe it's the former — D4's own text says "reads no project
  state, calls no ProjectStore/SecretStore method," which is about the route function, not the
  full rendered page — but please judge this yourself rather than taking my word for it.
- `qa/contracts/docker.md` D4/D5 aren't edited by this manifest (maker never edits contracts) —
  please consider whether an amendment log entry belongs there now that a second, deliberately
  page-state-varying piece of shared chrome (the sidebar) exists alongside the original
  "byte-identical" wrapper (D5).

## Status: ready-for-check
