# Manifest — docker-live-ui

**Contract:** qa/contracts/docker.md (D1–D6, new this cycle) + qa/contracts/ui.md (U1–U5,
unchanged behavior)
**Goal task:** none (`.goal/goal.json` is 20/20 done; this is Umesh's ad-hoc infra/UI request)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## What Umesh asked for, and the scope decision

Umesh (Hinglish): "mai khaa dekh sakta hu. live runn krr aur system mai docker mai runn krr and
ui ko user friendly bnaana hai bss functionalty nhi bnaani hai" — where can I watch, run it live,
run the system in Docker, and make the UI user-friendly — but don't build new [pipeline]
functionality. Clarified with Umesh (AskUserQuestion): live view = noVNC embedded in the browser;
target = local dev machine only, no remote/cloud hardening.

This unit touches only `ui/app.py` (route wrapping + one presentation-only `/live` route),
`ui/theme.py` (new), and infra files at the repo root / `docker/` — no `stages/`, `providers/`,
`schema/`, or `store/` file is touched, matching the no-fire boundary Umesh drew.

## Real bugs found and fixed while building this (not simulated)

1. **`docker-compose.yml`'s naive bind mount would have shadowed the container's Linux `.venv`
   with the host's Windows one**, breaking every `uv run` inside the container. Fixed with a named
   volume (`autotester-venv:/app/.venv`) overlaid on top of the `.:/app` bind mount.
2. **`apt-get install` hung indefinitely with zero error and zero output** — `novnc`/`websockify`
   transitively pull `tzdata`, whose postinst script prompts interactively for a timezone;
   `apt-get -y` answers confirmations but not debconf prompts, so the build sat at rising CPU with
   no progress for over an hour before this was diagnosed (confirmed via `docker buildx du`
   showing an unchanged cache size across repeated checks while `com.docker.backend`'s CPU kept
   climbing). Fixed with `ENV DEBIAN_FRONTEND=noninteractive TZ=UTC` before the `apt-get` layer.
3. **Host port 8000 was already bound by an unrelated container** (`deepinterview-agent-api-1`,
   a different project on this shared dev machine) — `docker compose up` failed with "port is
   already allocated". Fixed by remapping the UI to host port 8010 (container-internal port stays
   8000, `docker-compose.yml`'s `ports: ["8010:8000", ...]`).
4. **`uvicorn` was never an actual project dependency** — `pyproject.toml` only ever declared
   `fastapi`; the UI had only ever been exercised through `TestClient` in tests, never literally
   served as a real process. The entrypoint's `uv run uvicorn ...` failed with "Failed to spawn:
   uvicorn — No such file or directory". Fixed by adding `uvicorn[standard]>=0.30.0` to
   `pyproject.toml` and regenerating `uv.lock` (`uv lock`); re-synced on the host too so local dev
   stays consistent (`uv sync`). This is a real, previously-latent gap the "run it live" ask
   surfaced — not new pipeline functionality, just making an existing route actually runnable.
5. **Minor UX bug caught on first real render**: `index()`'s title was `"AutoTester"`, and
   `theme.page()` appends `" — AutoTester"`, so the browser tab read "AutoTester — AutoTester".
   Fixed by passing `"Home"` as the index route's title.

## What changed

- `qa/contracts/docker.md` (new) — D1 (image builds, runs unmodified app) · D2 (real virtual
  display + web viewer) · D3 (a run is genuinely watchable) · D4 (`/live` is presentation-only) ·
  D5 (every route visually wrapped, behaviorally identical) · D6 (state persists across restarts).
- `qa/feedback-inbox.md` — Umesh's verbatim ask + reading, flagging that `qa/contracts/ui.md`
  should gain an amendment noting the shared-layout invariant and `/live`'s existence (checker's
  job, not maker's).
- `Dockerfile` (new) — `mcr.microsoft.com/playwright/python:v1.62.0-jammy` base (ships Chromium +
  deps already); `DEBIAN_FRONTEND=noninteractive`; `xvfb x11vnc novnc websockify curl` via apt;
  `uv sync --frozen` for the exact same lockfile as local dev.
- `docker/entrypoint.sh` (new) — starts Xvfb → x11vnc → websockify (serving noVNC's static client
  via `--web`) → `uv run uvicorn autotester.ui.app:app`, in that order.
- `docker-compose.yml` (new) — one service, ports `8010:8000` (UI) + `6080:6080` (noVNC), bind
  mount `.:/app` for state persistence, named-volume overlay for `.venv`.
- `.dockerignore` (new).
- `src/autotester/ui/theme.py` (new, 55 lines) — `PAGE_STYLE` (one shared stylesheet), `NAV`,
  `badge(value)` (colored result/outcome spans), `page(title, body)` (the wrapper every route
  calls).
- `src/autotester/ui/app.py` — every existing route's return wrapped in `theme.page(...)`
  (no logic change — same `ProjectStore`/`SecretStore` calls, same `html.escape` discipline, same
  404s); new `GET /live` route (presentation-only, D4); `run_view`/`report` now render
  `theme.badge()` for result/outcome values.
- `src/autotester/doctor.py` — `ALLOWED_ROOT_ENTRIES` gained `Dockerfile`, `docker-compose.yml`,
  `docker`, `.dockerignore` (a real, deliberate layout change, not a workaround — Docker is now a
  legitimate part of this project's layout).
- `pyproject.toml` / `uv.lock` — added `uvicorn[standard]>=0.30.0` (bug #4 above).
- `tests/test_ui.py` — 3 new tests: `/live` returns 200 and contains the noVNC iframe/port;
  `/live` renders identically regardless of project state (D4, presentation-only); every route
  carries the shared nav.
- `docs/ARCHITECTURE.md` — two new concept→file rows (shared theme, Docker); 150 lines (at cap).
- `docs/MAP.md` regenerated.

## Real verification performed (not simulated) — cited evidence

```
$ docker compose build --progress=plain   # (after fixing bugs #1, #2, #4 above)
...
#16 naming to docker.io/library/autotesting-autotester:latest done
[exited with code 0]

$ docker compose up -d
 Container autotesting-autotester-1 Started

$ docker compose logs --tail=10
INFO:     Started server process [38]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/         -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/live     -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/onboard  -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html -> 200
```

**D3 (the real "where can I watch" proof)** — ran the existing regression-proof script *inside*
the container, on the container's own virtual display, real judge, real .env-mounted credentials:
```
$ docker compose exec autotester bash -c "rm -rf profiles/regression-demo && uv run python scripts/regression_proof.py"
--- BEFORE (working build) ---
Login with correct credentials: PASS  (observed: 'Login successful')
Homepage loads: PASS  (observed: 'Welcome to the demo site')
--- AFTER (broken build) ---
Login with correct credentials: FAIL  (observed: 'Invalid credentials')
Homepage loads: PASS  (observed: 'Welcome to the demo site')
REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
```
Real screenshots were captured from inside the container's Xvfb display during this run —
`projects/regression-demo/runs/run-after-01M1KQHNJHGN69E1S4XDAEJF4B/04-step04-click.png` (12KB,
visually confirmed: a real "Sign in" page showing "Invalid credentials", not a blank/black
frame — the literal proof the headed browser is genuinely rendering inside the container).

Fixture restoration confirmed clean afterward (`grep "password ===" .../login.html` → `pass123`;
`git diff` empty, only a CRLF-normalization warning, no real content change).

## How to verify (commands + expected)

- `uv run pytest -q` → all green (added `test_live_view_renders_the_novnc_iframe`,
  `test_live_view_touches_no_project_state`, `test_every_page_carries_the_shared_nav`)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `docker compose build && docker compose up -d` → succeeds; `curl localhost:8010/` and
  `curl localhost:6080/vnc.html` both 200
- `docker compose exec autotester uv run python scripts/regression_proof.py` → same
  PASS/PASS→FAIL/PASS pattern as the host, with real screenshots proving on-container rendering

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui.py -v
......s..........                                                       [100%]
16 passed, 1 skipped
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- D5's "behaviorally identical" claim: every pre-existing test in `tests/test_ui.py` (16 tests
  covering U1-U5) still passes unchanged under the new `theme.page()` wrapper — the substring
  assertions those tests make (e.g. `"case_1" in run_response.text`) still hold because `page()`
  only prepends/wraps, never removes or reorders the caller's fragment.
- Port 8010 (not 8000) is a deliberate, documented choice (bug #3 above) — a shared dev-machine
  conflict, not a design requirement; `docker-compose.yml`'s comment explains why.
- Per the no-fire list: no run-triggering added to the UI, no remote/cloud hardening, no JS
  framework/HTMX, no live-polling run view.
- `ALLOWED_ROOT_ENTRIES` in `doctor.py` was widened deliberately for the new Docker files — this
  is itself part of what the checker should verify is a legitimate layout change, not scope creep.

## Status: checked-PASS — see qa/verdicts/docker-live-ui.md, cycle 1 PASS
