# Contract — Web UI (T-100)

**Covers:** goal task T-100. **Owner:** /checker. **Criticality:** HIGH — T-100's own note:
"full onboarding → report without touching the CLI."
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B1-B9 — the credential
boundary this UI's `.env` editor must respect), `execute.md`/`grade.md` (the `RawResult`/`Verdict`
shapes the report/run views read).

## Purpose

A thin FastAPI viewer/editor over the same project files the CLI reads and writes — design
principle 8: "the UI is a viewer/editor over those files, not a second source of truth." Every
route goes through `ProjectStore`/`SecretStore`, never a parallel store.

## Criteria

### U1 — Onboarding creates a real, CLI-compatible project
`POST /onboard` builds a `schema.project.Project` from form fields and persists it via
`ProjectStore.save_project` — the same file (`projects/<slug>/project.json`) and format the CLI
and every stage already read. No UI-only project representation exists.

### U2 — Project detail reflects real state, no caching/duplication
`GET /projects/{slug}` reads the project's actual `FlowSpec` (`review.status`) and case count
live via `ProjectStore` on every request — never a cached or UI-maintained copy. An unknown slug
is a 404, not a silently empty page.

### U3 — The env editor never renders a real secret value
`GET /projects/{slug}/env` shows, per declared `SecretRef`, only whether `.env` currently has a
non-empty value for that key (`"set"`/`"not set"`) — the actual value is never present anywhere
in the rendered HTML. `POST /projects/{slug}/env` writes a new value via
`ui/env_editor.py::set_env_value` (the one legitimate write path to the repo-root `.env`) and
never echoes the submitted value back in its response. Posting a key the project does not declare
is refused (400), never silently written.

### U4 — Run/report views read real persisted evidence, never invent it
`GET /projects/{slug}/runs/{run_id}` and `GET /projects/{slug}/report` read actual
`RawResult`/`Verdict` files via `ProjectStore.load_results`/`load_verdicts` — the outcome/result
values shown are exactly what was persisted by `execute.py`/`grade.py`, not recomputed or
guessed. A project with no runs yet reports that plainly (200 with a "no runs yet" message), not
an error.

### U5 — User-supplied values are HTML-escaped
Every string derived from user input or project data (`name`, `base_url`, slugs, case ids,
outcome/result values) is passed through `html.escape` before being placed in a response —
verified by reading `ui/app.py` in full, not merely tested against one payload.

## No-fire list

- Authentication/authorization — this is a local, single-operator tool for now (matches the
  plan's "Out of scope v1: multi-tenant SaaS").
- A JS framework or HTMX wiring — plain server-rendered HTML strings for this cycle; the plan
  names HTMX as a future refinement, not required to satisfy this contract.
- Live-updating run views (polling/websockets) — `GET /projects/{slug}/runs/{run_id}` is a
  point-in-time snapshot; "live" in T-100's title is satisfied by reading current persisted state
  on every request, not by push updates.
- Triggering a run or an onboarding video from the UI — this contract covers viewing/editing
  existing project state and creating a bare project record; kicking off `execute.py`/
  `ingest.py` from a UI button is a future enhancement.
- CSRF protection on the POST forms — acceptable for a local single-operator tool; flagged as a
  known gap if this UI is ever exposed beyond localhost.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-100 — no contract existed before this cycle.
- 2026-09-03 · /checker (docker-live-ui unit) · shared-layout invariant: every route in
  `ui/app.py` now returns its HTML fragment wrapped by `ui/theme.py::page(title, body)` — a
  shared nav + stylesheet, visual only. U1-U5 are unaffected: `page()` prepends/wraps the
  caller's already-escaped fragment and never removes, reorders, or unescapes it (verified —
  see `qa/verdicts/docker-live-ui.md` D5). A new presentation-only route, `GET /live` (renders
  an iframe onto the container's noVNC client; no `ProjectStore`/`SecretStore` call, triggers no
  run), now exists alongside U1-U5's routes — covered by `qa/contracts/docker.md` D4, not a U-item
  itself since it reads no project state. Routine, non-weakening; folds the flagged
  `qa/feedback-inbox.md` 2026-09-03 "Docker + live-watch + UI polish" entry.
- 2026-09-07 · /checker (ui-back-nav-and-live-clarity unit) · shared back-navigation invariant:
  every route that is not the home page now builds its trail with
  `ui/theme.py::breadcrumb(*crumbs)` — one helper replacing 8 hand-written
  `<div class='breadcrumb'>` blocks across 5 modules — which renders a real `← Back` anchor
  targeting the **last crumb carrying an href** (the natural parent), plus the same trail as
  before. U5 is unaffected and re-verified: `breadcrumb()` adds no escaping of its own (same
  caller-escaping discipline as `page()`), all 8 call sites pass `escape()`d labels, and every
  href is a literal or `/projects/{escape(slug)}` where the slug is already `_require_slug`
  regex-validated — so no user-controlled string reaches an `href=`. Verified live against a
  project named `<script>alert(1)</script>&'"` on 5 routes (see
  `qa/verdicts/ui-back-nav-and-live-clarity.md` U5). Also in this unit: `GET /live`'s tip text
  replaced — the stale `scripts/regression_proof.py` instruction (which predated the ▶ Run tests
  button) is gone, replaced by the honest "a black screen is normal, it is the container's real
  and idle display" note plus the AT-054 `AUTOTESTER_SLOW_MO_MS` opt-in; presentation-only, no
  `ProjectStore`/`SecretStore` call added. Routine, non-weakening. Known gap deliberately NOT
  covered by any criterion here and now tracked as ledger issue **AT-057**: an onboarded project
  with zero cases has no UI path to add one, so its ▶ Run tests button is permanently disabled —
  it needs its own contract-scoped cycle and a scoping decision (add-a-case flow vs explicit
  next-step prompt) before a criterion can be written for it.
