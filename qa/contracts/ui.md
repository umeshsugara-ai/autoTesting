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
