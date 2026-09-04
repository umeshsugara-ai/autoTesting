# Contract — ui-sidebar (persistent project navigation)

**Status:** ACTIVE. Umesh: "TOC features" — clarified into a persistent sidebar listing every
onboarded project, present on every page, for quick switching.

## Why this exists

Before this, switching projects meant clicking "Projects" in the top nav back to the homepage
first, then picking a different project card — every other page (report, run detail, flow
diagram, credentials) had no way to jump directly to a different project.

## Criteria

- **US1 — every page, one place.** `theme.page()` renders the sidebar on every route that calls
  it (project-scoped or not) — a single change to the shared wrapper, not a per-route addition.
- **US2 — real project data, no second source of truth.** The sidebar lists every project
  `ProjectStore` actually knows about (same `_project_slugs()`/`ProjectStore` lookup `index()`
  already uses), each showing its real declared name, not just its slug.
- **US3 — the active project is visible.** On a project-scoped page, the current project's own
  sidebar entry is visually distinguished from the rest (a real state, not just a link list).
- **US4 — honest empty state.** Zero onboarded projects still renders a real sidebar (not a
  broken/missing element) saying so, with a way to onboard the first one.
- **US5 — no behavior change to any existing page's own content.** This is a layout wrapper
  change only — every existing route's own body HTML, escaping, and data are untouched.

## No-fire list (out of scope for this contract)

- Collapsible/toggleable sidebar, search/filter within it — a real project list today is small;
  revisit if that changes.
- Per-project quick stats in the sidebar (case counts, latest result) — the sidebar is a
  navigation index, not a second dashboard; `index()`'s own project-card grid already covers
  that.
