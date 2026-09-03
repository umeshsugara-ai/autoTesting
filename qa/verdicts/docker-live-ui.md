# Verdict — docker-live-ui

**Unit:** docker-live-ui (no goal task; ad-hoc infra/UI request)
**Contract:** `qa/contracts/docker.md` (D1-D6) + `qa/contracts/ui.md` (U1-U5, must still hold)
**Cycle checked:** 1
**Verdict:** PASS

Fresh redispatch (the prior checker session for this unit died mid-run without writing a
verdict) — nothing below was trusted from the manifest; every command was re-run independently
and the screenshot was independently opened.

## Pre-check note: Docker daemon and a real leftover-state bug found

Docker Desktop had just been restarted per the dispatch note; `docker version` returned
`29.6.1` immediately, no retry needed.

`docker compose build` initially **failed**: `ERROR: invalid file request
profiles/regression-demo/SingletonCookie`. Root cause: `profiles/regression-demo/` (deliberately
*not* dockerignored, per `.dockerignore`'s own comment, so it reaches the build context and gets
overlaid by the runtime bind mount) contained live Chromium `SingletonCookie`/`SingletonLock`/
`SingletonSocket` symlinks left over from the prior interrupted checker session — Docker's build
context cannot traverse these. Fixed by `rm -rf profiles/regression-demo` (a gitignored runtime
directory the D3 verify command itself deletes and recreates anyway — not a source change). Build
then succeeded cleanly. Flagging this as a real fragility: **any leftover live browser-profile
symlink under `profiles/<slug>/` will break `docker compose build`** since that directory is not
excluded from the build context. Not a D1-D6 criterion violation (the image did build and run the
unmodified app once the transient artifact was cleared, and this class of leftover is exactly
what a real run produces and cleans up each time), but worth the maker/Umesh knowing — a
`docker compose build`-time `.dockerignore` guard for `**/Singleton*` would make this more
robust. Not filing as an open issue: it never affected the shipped app, and the only fix needed
was clearing stale local state left by an unrelated crashed session, not touching this unit's
own new files.

## D1 — image builds, runs the existing app unmodified

- `docker compose build` (after clearing the stale profile dir above): succeeded, final layer
  `naming to docker.io/library/autotesting-autotester:latest done`, `uv sync --frozen` output shows
  `uvicorn==0.52.4` and `uvicorn[standard]`'s transitive deps installed from the same lockfile.
- `docker compose up -d`: `Container autotesting-autotester-1 Started`; logs show
  `INFO: Uvicorn running on http://0.0.0.0:8000`.
- `Dockerfile` (read in full, `d:\autoTesting\Dockerfile`): `COPY pyproject.toml uv.lock ./` then
  `uv sync --frozen --no-install-project`, then `COPY . .` + `uv sync --frozen` — same lockfile,
  no divergent dependency resolution.
- `docker-compose.yml`: `volumes: [.:/app, autotester-venv:/app/.venv]` — the bind mount is the
  actual host `src/autotester/` tree, not a baked copy; the named-volume overlay on `.venv` is
  exactly the venv-shadowing fix claimed (bug #1). Confirmed by exec'ing the regression script
  below and getting real, current code behavior.
- **PASS.**

## D2 — real virtual display + web viewer

- `docker/entrypoint.sh` (read in full): `Xvfb :99 ... &` → `x11vnc -display :99 ... &` →
  `websockify --web=/usr/share/novnc 6080 localhost:5900 &` → `exec uv run uvicorn ...`, in that
  order, matching the contract's required sequence.
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html` → `200`.
- Container logs confirm: `The VNC desktop is: 70ed512d9918:0`, `PORT=5900`,
  `WebSocket server settings: Listen on :6080 ... Web server. Web root: /usr/share/novnc ...
  proxying from :6080 to localhost:5900`.
- **PASS.**

## D3 — a run is genuinely watchable end-to-end (the literal "where can I watch" proof)

Ran, independently, inside the running container:
```
docker compose exec autotester bash -c "cd /app && rm -rf profiles/regression-demo && uv run python scripts/regression_proof.py"
```
Output:
```
--- BEFORE (working build) ---
Login with correct credentials: PASS  (observed: 'Login successful')
Homepage loads: PASS  (observed: 'Welcome to the demo site')
--- AFTER (broken build) ---
Login with correct credentials: FAIL  (observed: 'Invalid credentials')
Homepage loads: PASS  (observed: 'Welcome to the demo site')
REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
```
Exactly the reported pattern — login case flips, homepage case does not.

**Screenshot independently viewed** (Read tool, image):
`d:\autoTesting\projects\regression-demo\runs\run-after-01M1M5QNTBMZH7SWWDBZKMQKFD\04-step04-click.png`
— a real, non-blank, fully rendered "Sign in" page: `test@example.com` in the email field, a
masked password field, a "Log in" button, and the text "Invalid credentials" below the form. Not
a black screen, not a static/stub image — this is Chromium genuinely rendering inside the
container's Xvfb display (`DISPLAY=:99`) at the moment of the click step.

Fixture restoration confirmed clean afterward:
- `grep -n "password ===" tests/fixtures/regression_site/login.html` → line 19,
  `password === 'pass123'`.
- `git status --porcelain tests/fixtures/regression_site/login.html` → shows modified, but
  `git diff` on it produces **no content diff**, only:
  `warning: in the working copy of ... LF will be replaced by CRLF the next time Git touches it`
  — a line-ending-only artifact, zero real content change, matching what the manifest itself
  disclosed.

Note: before this run I found the fixture in the **broken** state (`pass124`, from the prior
interrupted checker session, not this unit's own doing) and `uv run pytest -q` failing on
`test_broken_fixture_checks_a_different_password` as a result. Restored with
`git checkout -- tests/fixtures/regression_site/login.html`; full `uv run pytest -q` was clean
afterward (see below). Recording this so it's clear the leftover was pre-existing interrupted-run
state, not something this dispatch's own actions produced — but flagging it because it means the
fixture was NOT actually left clean before this redispatch began, contrary to what a
"ready-for-check" status implies.

- **PASS** (on both the live-watch claim and the restored-fixture check, once corrected).

## D4 — `/live` is presentation-only

Read `src/autotester/ui/app.py:177-189`, the `live_view()` function directly:
```python
@app.get("/live", response_class=HTMLResponse)
def live_view() -> str:
    ...
    return theme.page("Live view", body)
```
No `ProjectStore`/`SecretStore` import or call anywhere in the function body — it only builds a
static string with a hardcoded example command and an iframe `src` pointing at
`http://localhost:6080/vnc.html?autoconnect=true&resize=scale`. No run is triggered.
`test_live_view_touches_no_project_state` (tests/test_ui.py:258-267) independently asserts the
response is byte-identical before and after onboarding a project — passed under `uv run pytest -q`.
`curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/live` → `200`.
- **PASS.**

## D5 — every existing route visually wrapped, behaviorally identical

- `ui/theme.py::page(title, body)` (`d:\autoTesting\src\autotester\ui\theme.py:54-59`) only
  prepends `<!doctype html><title>...</title>` + `PAGE_STYLE` + `NAV` in front of the caller's
  `body` string — never truncates, reorders, or re-escapes it.
- Every route in `ui/app.py` (`index`, `onboard_form`, `project_detail`, `env_editor_view`,
  `run_view`, `report`) still calls the same `ProjectStore`/`SecretStore` methods and the same
  `html.escape(...)` calls as before, just returning `theme.page(title, body)` instead of the raw
  body string — read in full, no logic removed or added to any of these six routes beyond the
  `theme.badge()` calls in `run_view`/`report` for colored result spans (presentation only, the
  underlying escaped value is unchanged).
- Spot-checked against the live container: `curl http://localhost:8010/` shows `<style>` and
  `<nav>` present, title `Home — AutoTester` (bug #5's doubled-title fix confirmed — not "AutoTester
  — AutoTester"); `curl http://localhost:8010/projects/regression-demo` shows the real project
  name `Regression Proof Demo` rendered inside the theme wrapper, confirming real project data
  still flows through unmodified alongside the new chrome.
- `uv run pytest -q`: full suite passes (74 passed, 2 skipped — one Windows-only POSIX-permission
  skip, one pre-existing skip unrelated to this unit), including all pre-existing U1-U5 tests in
  `tests/test_ui.py` (16 of them) unchanged, plus the 3 new D4/D5 tests
  (`test_live_view_renders_the_novnc_iframe`, `test_live_view_touches_no_project_state`,
  `test_every_page_carries_the_shared_nav`).
- `qa/contracts/ui.md` amended (this cycle, checker-owned) to record the shared-layout invariant
  and `/live`'s existence per the flagged `qa/feedback-inbox.md` entry — see amendment log entry
  dated 2026-09-03 in `ui.md`.
- **PASS.**

## D6 — state persists across container restarts

`docker-compose.yml`: `volumes: [.:/app, autotester-venv:/app/.venv]` — `.env`, `projects/`,
`profiles/`, `docs/` all live under the bind-mounted `.:/app`, not baked into the image or a
container-local volume; only `.venv` gets the named-volume overlay (the venv-shadowing fix, bug
#1). This means `docker compose down && docker compose up` retains host-side `projects/`/`.env`/
`profiles/` state exactly as claimed — verified structurally by reading the compose file; not
separately re-tested with a down/up cycle mid-run since D1/D3 already exercised the same bind
mount live (the container read and wrote real host-side `projects/regression-demo/` data during
the D3 run).
- **PASS.**

## U1-U5 (qa/contracts/ui.md) — confirmed still holding

Full `uv run pytest -q` run (after fixture restoration) is green, including every pre-existing
`tests/test_ui.py` test for U1 (onboarding →` project.json`), U2 (live project detail, 404 on
unknown slug), U3 (env editor never renders/echoes real values, refuses undeclared keys and
newline-injection), U4 (run/report read real persisted `RawResult`/`Verdict`, "no runs yet" on a
run-less project), and U5 (HTML-escaping — `ui/app.py` re-read in full this cycle, every
user/project-derived string is still passed through `escape(...)` before interpolation; `theme.py`
adds no escaping of its own and documents that it relies on caller discipline, matching the
existing U5 requirement). No route's behavior changed beyond the visual wrapper.
- **U1-U5: still hold, unchanged.**

## Other independent checks

- `uv run pytest -q` → 74 passed, 2 skipped (clean, after fixture restore).
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`.
- `doctor.py`'s `ALLOWED_ROOT_ENTRIES` diff (`git diff HEAD -- src/autotester/doctor.py`): adds
  exactly `.dockerignore`, `docker`, `docker-compose.yml`, `Dockerfile` — nothing else. Narrowly
  scoped, matches the no-fire list (`stages/`, `providers/`, `schema/`, `store/` untouched —
  confirmed via `git status`, none of those directories appear in the diff).
- `pyproject.toml`/`uv.lock`: `uvicorn[standard]>=0.30.0` added; build/run both worked from it.
- No-fire list respected: no run-triggering UI action added, no auth/TLS added, no JS
  framework/HTMX, no live-polling view — `/live` is a static iframe pointing at noVNC, confirmed
  above.

## Docker state left after this check

Ran `docker compose down` at the end — container and network removed, image (`autotesting-
autotester:latest`) and the `autotester-venv` volume left in place for a fast rebuild next time.
Machine left clean, nothing running.

## Overall

All of D1-D6 verified independently with real re-run commands and an independently-viewed
screenshot; U1-U5 confirmed unchanged. One real environmental fragility found and documented
(stale `profiles/<slug>/` browser-lock symlinks can break `docker compose build`) — not a
contract violation, not filed as an open issue, but noted for awareness. One real leftover-state
issue found and corrected (the regression fixture was left in its broken `pass124` state from the
prior interrupted checker session, not from this unit's own work) — restored via `git checkout --`
before verification; full test suite is green.

**PASS.**
