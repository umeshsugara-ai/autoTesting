# Contract — Docker + live-watch view (new, 2026-09-03)

**Covers:** ad-hoc unit `docker-live-ui` (no `.goal` task — this is infra/presentation work
outside the shipped P0–P5 backlog, per Umesh's explicit request). **Owner:** /checker.
**Criticality:** MEDIUM — makes the system runnable and watchable in a standard environment; does
not touch the ingest/expand/execute/grade pipeline.
**Depends on:** `ui.md` (U1–U5, unchanged by this unit's route-logic — only presentation wraps).

## Purpose

Three things, deliberately scoped to infra + presentation, never pipeline logic (Umesh: "bss
functionalty nhi bnaani hai" — don't build new functionality):

1. **Dockerize** the system so it runs the same way in a container as on the host.
2. **A live-watch view**: since the browser runs headed by default and Docker has no host
   display, give the container a virtual display (Xvfb) and a web-reachable viewer onto it
   (noVNC) so a run can be watched from any browser — no VNC client, no host display needed.
3. **UI polish**: a shared CSS layout wrapping every existing route — visual only, no new data
   flow, no new store access, no behavior change to any existing route's logic.

## Criteria

### D1 — The image builds and runs the existing app unmodified
`docker compose build` succeeds; `docker compose up -d` starts one container that serves the
FastAPI UI on port 8000 using the exact same `src/autotester/` code as the host (bind-mounted,
not copied+diverged) — `uv sync --frozen` inside the container uses the same lockfile as local
dev, so no dependency drift.

### D2 — A real virtual display + web viewer, not a stub
Inside the container: `Xvfb` provides `DISPLAY=:99`, `x11vnc` shares that display, `websockify`
(serving noVNC's static client via `--web`) proxies it to port 6080. `curl localhost:6080/vnc.html`
returns 200 from outside the container.

### D3 — A run is genuinely watchable end-to-end
Running an existing script inside the container (`docker compose exec ... uv run python
scripts/regression_proof.py`) while the noVNC page is open shows the real Chromium window
actually rendering navigation/fill/click actions — not a black screen, not a static screenshot.
This is the literal answer to "where can I watch".

### D4 — `/live` is presentation-only
`GET /live` (new route in `ui/app.py`) renders an iframe pointing at the noVNC client. It reads
no project state, calls no `ProjectStore`/`SecretStore` method, and triggers no run — consistent
with `qa/contracts/ui.md`'s existing no-fire item ("triggering a run from the UI is a future
enhancement," still true after this unit).

### D5 — Every existing route is visually wrapped, behaviorally identical
`ui/theme.py::page(title, body)` wraps every route's HTML in a shared nav + stylesheet. For each
of the 6 pre-existing routes, the exact same escaped data that was present in the response before
this unit is still present after it (verified by diffing rendered output for the same fixture
inputs) — only the surrounding chrome changed. `qa/contracts/ui.md` U1–U5 all still hold.

### D6 — State persists across container restarts
`.env`, `projects/`, `profiles/`, and `docs/` are bind-mounted from the host (not baked into the
image or container-local), so `docker compose down && docker compose up` retains prior project
data and browser login state exactly like restarting the app on the host does today.

## No-fire list

- Any change to `stages/`, `providers/`, `schema/`, or `store/` — this unit touches only
  `ui/app.py` (route wrapping + one new route), `ui/theme.py` (new), and infra files at the repo
  root / `docker/`.
- Triggering a run, uploading a video, or any new business action from the UI — still out of
  scope per `ui.md`'s existing no-fire list.
- Remote/cloud deployment hardening (TLS, auth in front of the UI or noVNC, network policies) —
  explicitly out of scope; Umesh confirmed this is for local dev machine use only.
- A JS framework, HTMX, or live-polling run views — `ui.md`'s no-fire list already rules these
  out; this unit's CSS-only wrapper needs none of them.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for the Docker + live-watch + UI-polish unit.
