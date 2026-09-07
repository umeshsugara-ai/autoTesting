# Manifest — ui-back-nav-and-live-clarity
**Contract:** qa/contracts/ui.md
**Goal task:** none (feedback-driven unit)
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none filed (feedback-inbox entries, 2026-09-07)

## What changed
- `src/autotester/ui/theme.py` — new `breadcrumb(*crumbs)` helper. Each crumb is
  `(label, href)`, the current page passing `href=None`. Renders a real
  `← Back` button plus the trail; the back button targets the **last crumb that has an
  href** (the natural parent), so a nested page goes back one level rather than always
  jumping home. Labels must already be caller-escaped — same discipline as `page()`.
- `src/autotester/ui/theme_style.py` — new `.crumbs` flex row and `.btn-back` sizing (a
  smaller `.btn`); `.breadcrumb`'s own `margin-bottom` moved to the `.crumbs` wrapper so
  the two sit on one line. New `.live-tip-muted` for the secondary live-view note.
- `src/autotester/ui/app.py` — `onboard_form`, `project_detail` and `live_view` now call
  `theme.breadcrumb(...)` instead of each hand-writing the same `<div class='breadcrumb'>`
  markup.
- `src/autotester/ui/routes_report.py` (×2 — run view and report view),
  `routes_credentials.py`, `routes_flow_diagram.py`, `routes_settings.py` — same
  substitution. All 8 hand-written breadcrumb blocks across 5 files are now one helper
  (the project's "one concept, one place" rule; `doctor` does not catch duplicated inline
  markup, so this was silent drift).
- `src/autotester/ui/app.py::live_view` — replaced the stale tip (which told the user to
  start a run via `scripts/regression_proof.py`, predating the ▶ Run tests button) with
  two honest notes: (a) a black screen is **normal** — it is the container's real display
  and it is empty whenever no run is in progress, so open a project and press ▶ Run tests
  with this page open in a second tab; (b) runs finish in about a second at full speed, so
  set `AUTOTESTER_SLOW_MO_MS=1500` before `docker compose up -d` to make one watchable
  (the opt-in shipped as AT-054).
- `tests/test_ui_dashboard.py` — 3 new tests: every non-home page (7, parametrized:
  onboard, project detail, env, report, flow-diagram, settings, live) renders a real
  `<a class='btn btn-back'>`; a nested page's back button targets its parent
  (`/projects/demo/env` → `/projects/demo`), not home; and the home page renders no back
  anchor at all.

## How it was found
User feedback while using the UI, 2026-09-07: **"dekh maine abhi ERP project ki details
daali, there is no back button for easy navigation"** and, minutes later, **"and live
preview and all mai kuch bhi nhi ho rhaa"** (nothing at all is happening in the live
preview). Investigated both rather than assuming:
- The breadcrumb trail *did* exist on every page, but as a 0.78rem muted uppercase line —
  it reads as a location label, not a control, and scrolls out of view. Not a missing
  feature so much as a control that was never a control.
- The live view's noVNC iframe is genuinely **working** — confirmed via browser console on
  `/live`: `core/display.js` loads and performs canvas readback, i.e. the VNC session
  connects. The black rectangle is an empty X display, correct-but-idle, with nothing on
  the page saying so.

## Known gap NOT fixed by this unit (logged, not silently dropped)
While verifying, found the bigger cause of "nothing is happening": a freshly-onboarded
project has **zero cases**, so its ▶ Run tests button is permanently disabled and there is
**no UI path anywhere to add a case** — onboarding dead-ends for a non-technical user.
Evidence: `/projects/erp` renders "0 CASES" with a greyed-out Run button. Cases are today
creatable only via `ProjectStore.add_case` from Python, or `stages/expand.py` off a
reviewed FlowSpec that itself needs an ingested video. Logged verbatim to
`qa/feedback-inbox.md` (2026-09-07) as the single biggest remaining "this is not a real
product" gap. Deliberately out of scope for this unit, which is navigation + live-view
honesty only — it needs its own contract-scoped cycle.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → expected: exit 0, all tests pass
- `docker compose exec autotester uv run pytest -q tests/test_ui_dashboard.py` → expected: exit 0, 12 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: exit 0
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Real end-to-end: `docker compose restart autotester` (uvicorn has no `--reload`), then load
  `http://localhost:8010/projects/erp` → expected: a visible `← Back` button beside the
  trail; and `http://localhost:8010/live` → expected: the black-screen-is-normal
  explanation above the viewer.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q
........................................................................ [ 75%]
.......................................................................  [100%]
(all pass, no failures)

$ docker compose exec autotester uv run pytest -q tests/test_ui_dashboard.py
............                                                             [100%]

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end, after `docker compose restart autotester`, via a live Playwright browser:
- `/projects/erp` (screenshot `.work/erp-back-button.png`) — a real `← Back` button now
  renders as a button beside the `PROJECTS / ERP` trail.
- `/live` (screenshot `.work/live-view-fixed.png`) — the "A black screen below is normal"
  explanation and the slow-motion note both render above the viewer.

One test-authoring mistake worth recording: the first version of
`test_home_page_has_no_back_button` asserted `"btn-back" not in response.text`, which
failed — `.btn-back`'s CSS rule ships in the shared stylesheet on *every* page, so the bare
substring always matches. Fixed by asserting on the rendered anchor
(`<a class='btn btn-back'`) instead. The test was wrong, not the code.

## Status: ready-for-check
