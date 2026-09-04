# Verdict — ui-sidebar

**Date:** 2026-09-04
**Cycle checked:** 1
**Contract:** qa/contracts/ui-sidebar.md (US1-US5)
**Manifest:** qa/manifests/ui-sidebar.md

## What I re-ran myself

- `uv run pytest tests/test_ui_sidebar.py -v` → 6 passed (re-ran, not trusted from the manifest).
- `uv run pytest -q` → full suite green (219 passed, 2 skipped — Windows perm-bit skips,
  pre-existing).
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean.
- Real live Docker check via Playwright against the running container at
  `http://localhost:8010` (restarted with this unit's code): screenshotted
  `/projects/pathlynks/report` and `/live`.
  - `/projects/pathlynks/report`: sidebar renders left of `<main>`, sticky below the topbar,
    "Pathlynks" shown with the amber `.active` highlight, "Regression Proof Demo" listed as the
    second real onboarded project (its real declared name, not the slug), "+ New project" link
    at bottom. No overlap/clipping.
  - `/live` (a global, non-project-scoped page): sidebar still renders with both real projects
    listed, **no** entry highlighted — correct per US3 (only a project-scoped page shows an
    active entry) and confirms `app.py::live_view()` passes no `active_slug`.
- Read the code directly (not just tests) to confirm each criterion's actual mechanism:
  `src/autotester/ui/theme.py::_sidebar_html`/`page`, `theme_style.py` sidebar CSS,
  `app.py`/`routes_report.py`/`routes_credentials.py`/`routes_flow_diagram.py` `active_slug=`
  call sites, and `app.py::index()` to confirm it uses the same `_project_slugs()` lookup the
  sidebar uses (no second source of truth).

## Criteria judged

- **US1 (every page, one place)** — MET. Single change to `theme.py::page()`; every route calls
  `theme.page(...)`, none builds its own sidebar. Verified in code and live (5 distinct page
  types checked across the test file + my own two live screenshots).
- **US2 (real project data, no second source of truth)** — MET. `_sidebar_html()` calls the same
  `_project_slugs()` / `ProjectStore(...).load_project()` lookup `index()` already uses; each
  entry shows the real declared `project.name`, confirmed live ("Regression Proof Demo", not
  "regression-demo").
- **US3 (active project visible)** — MET. `.sidebar-link.active` class applied only when
  `slug == active_slug`; confirmed live on `/projects/pathlynks/report` (Pathlynks highlighted,
  Regression Proof Demo not) and via `test_active_project_is_highlighted_on_its_own_pages`.
  Global pages (`index`, `onboard`, `live`, `settings`) correctly pass no `active_slug` —
  confirmed live on `/live` (nothing highlighted) and in code.
- **US4 (honest empty state)** — MET. `_sidebar_html([])` renders `<p class='sidebar-empty'>No
  projects yet.</p>` inside the same `<aside class='sidebar'>`, not a missing/broken element;
  covered by `test_sidebar_shows_an_honest_empty_state_with_no_projects`.
- **US5 (no behavior change to existing content)** — MET. All non-theme.py route files changed
  only add `active_slug=slug` to an existing `theme.page(...)` call — no body-HTML/data changes.
  `test_existing_page_content_is_unchanged_by_the_sidebar` and the full green `tests/test_ui.py`
  suite (unchanged escaping/data assertions) back this.

## The flagged question: the `test_live_view_touches_no_project_state` change

Read `qa/contracts/docker.md` D4 and D5 directly (not from the manifest's summary) before
judging. D4's actual text: "/live... reads no project state, calls no ProjectStore/SecretStore
method, and triggers no run" — this is a claim about **the route function**
(`app.py::live_view()`), confirmed by reading it: it calls `theme.page("Live view", body)` with
no `active_slug` and touches no store. D5's claim is that each of the 6 pre-existing routes'
**own escaped body data** is unchanged by the wrapper — not that the wrapper itself is
state-invariant.

The old full-page-byte-equality test was strictly *stronger* than what D4 actually asserts: it
also incidentally asserted the wrapper never varies with project state, which was never D4's
claim and is not a real invariant anywhere in either contract. Since `theme.page()` is shared
chrome (D5's own precedent — "only the surrounding chrome changed" already established that the
wrapper is allowed to differ from a route's raw content), and the sidebar is exactly that kind of
chrome, narrowing the test to diff `/live`'s own `<main>` content is a faithful re-reading of
D4's actual text, not a softened test. I verified independently that the narrowed test still
does real work: it still fails if `/live`'s own body content changed (confirmed by reading the
assertion logic: `before_main == after_main` on the exact same slice used for both the
onboarded and pre-onboard fetch). **Judged legitimate — not a quiet weakening.**

Added a routine amendment log entry to `qa/contracts/docker.md` (checker-owned surface, criticality
gate: routine — clarifies wording, changes no actual criterion) recording that the sidebar is a
second, deliberately-state-varying piece of shared chrome alongside the original wrapper, and why
neither D4 nor D5 is weakened by it.

## Issues

None found. No new `qa/issues.jsonl` row needed — no gap between the contract and the delivered
artifact.

## Goal wiring

`.goal/goal.json` has no matching task for this unit (manifest states "Goal task: none" —
confirmed: this was direct user feedback via `qa/feedback-inbox.md`, not a `.goal` backlog item);
no `goal_cli.py done` call applies.

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 0/0 invariants (contract has no separate [I*] section; US1-US5
covered above)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All five US criteria are evidenced in code and confirmed live via Playwright
screenshots against the running Docker container on two distinct page types (project-scoped and
global). Full test suite, ruff, and doctor are all clean, re-run directly rather than trusted
from the manifest. The flagged test-narrowing on test_live_view_touches_no_project_state is a
faithful, non-weakening re-reading of D4's actual text about the route function, not the full
page; a routine amendment was added to docker.md's log to record the sidebar as new state-varying
chrome and why it doesn't erode D4/D5.
```
