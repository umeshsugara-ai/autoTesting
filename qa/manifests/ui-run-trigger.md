# Manifest — ui-run-trigger

**Contract:** qa/contracts/ui-run.md RU1-RU4 (new this cycle)
**Goal task:** none (`.goal/goal.json` is 20/20 done — ad-hoc plan work,
`C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md` §3b)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Umesh: "proper product ki tarah lo isko — rerun kar paaye, report dekh paaye ... sabhi kuch
chahiye" — a non-technical user must be able to click a button and get a real, graded run, no
terminal. Before this unit, `ui/app.py` could only view state a CLI script had already produced;
`qa/contracts/ui.md`'s own no-fire list explicitly deferred triggering a run.

## What changed

- `qa/contracts/ui-run.md` (new) — RU1 (real synchronous run, no second execution path) · RU2
  (honest 400s before any browser starts: no cases, then no AI provider) · RU3 (every case run
  and persisted, `Run` record saved, 303 redirect) · RU4 (global provider keys from `.env` are
  actually visible to the running process).
- `src/autotester/ui/routes_runs.py` (new) — `POST /projects/{slug}/run` (`trigger_run`),
  `GET /projects/{slug}/runs/{run_id}` (`run_view`), `GET /projects/{slug}/report` (`report`).
  Moved out of `app.py` (which was pushing past the 300-line file limit) rather than added
  alongside — a real module split by responsibility, not a workaround.
- `src/autotester/ui/routes_credentials.py` (new) — the .env editor routes, moved out of
  `app.py` for the same reason; zero logic change from the previous inline version.
- `src/autotester/ui/helpers.py` (new) — `_require_slug`/`_require_safe_id`/`_project_slugs`/
  `_load_project_or_404`, shared by `app.py` and both new route modules (one place for the
  slug-validation logic AT-035 was found in, not three copies of it).
- `src/autotester/ui/app.py` — trimmed to project-list/onboarding/live-view routes only;
  `app.include_router(routes_runs.router)` / `.include_router(routes_credentials.router)` wire
  the rest back in. `_require_slug` still importable from `app` (re-exported via `__all__`) so
  the existing `test_path_traversal_slug_is_rejected` test needs no change.
- `src/autotester/ui/app.py` — `POST /projects/{slug}/run`'s real logic (RU1-RU3) lives in
  `routes_runs.trigger_run`; `project_detail()` gets a real "▶ Run tests" primary button
  (disabled-looking span with a title when the project has zero cases).
- **RU4 fix, found by real Docker verification, not assumed:** a plain `uvicorn`/Docker process
  never sources `.env` on its own — every real-run script (`scripts/run_pathlynks_first_cases.py`
  etc.) calls `load_dotenv(repo_root / ".env")` itself, but `ui/app.py` never did, so a key set in
  `.env` was invisible to `LangChainFallbackProvider()` from the web UI even though every script
  could see it. Fixed via a FastAPI **lifespan** hook (`_lifespan` in `app.py`), not a module-level
  call — a module-level `load_dotenv()` was tried first and immediately caused real cross-test
  pollution (see below), which is exactly why lifespan (never run by `TestClient(app)` unless used
  as a context manager) is the correct fix, not a workaround.
- `tests/test_ui.py` — run-trigger tests moved to `tests/test_ui_runs.py` (mirrors the
  `routes_runs.py` split, keeps this file under 300 lines); U1-U5 tests unchanged.
- `tests/test_ui_runs.py` (new) — the 4 run-trigger tests, `monkeypatch.setattr` targets updated
  from `autotester.ui.app` to `autotester.ui.routes_runs` (the module that now actually owns
  `LangChainFallbackProvider`/`run_and_grade_case` references).
- `docs/MAP.md` regenerated (`autotester map`).

## A real bug found and fixed during this unit's own verification

The first attempt at RU4 was a bare `load_dotenv(repo_root() / ".env")` at module level in
`app.py`. Running the full suite (`uv run pytest -q`) immediately failed 4 unrelated tests
(`test_langchain_fallback.py::test_available_false_when_chain_is_empty`,
`::test_call_with_no_chain_raises_without_a_network_call`,
`test_providers.py::test_gemini_available_reflects_api_key_presence`,
`::test_gemini_see_video_without_a_key_raises_without_touching_the_network`) — because importing
`ui.app` (via `test_ui.py`) leaked the real `GEMINI_API_KEY` from the repo's own `.env` into
`os.environ` for the rest of the pytest process, so later tests asserting "no key configured"
behavior instead made a real (failing) network call. Root-caused to the difference between a
module-level side effect (runs once at import, for every consumer including tests) and a lifespan
hook (only runs when an ASGI server actually serves the app — `TestClient(app)` without a `with`
block never triggers it). Fixed by moving the call into `_lifespan`; confirmed no pollution by
re-running the full suite clean, and confirmed the real fix still works by restarting the live
Docker container and re-triggering a real run (see below).

## Deliberate scope decisions (per the contract's own no-fire list)

- v1's Run trigger is synchronous — the HTTP request itself waits for the browser to finish. No
  background job queue in this unit; a documented, honest v1 boundary (RU1), not an oversight.
- Report enrichment (run history list, inline screenshots, download buttons) is plan §3c, a
  separate unit — this unit's `report()`/`run_view()` are the pre-existing latest-run-only views,
  unchanged in behavior, only relocated to `routes_runs.py`.
- `/settings/providers` (plan §3d) is a separate unit — RU4 only guarantees a key already in
  `.env` is visible to the running process; it does not add a UI to set one.

## Real verification performed (not simulated)

```
$ uv run ruff check src tests scripts    # All checks passed!
$ uv run pytest -q                        # 21 passed... + full suite all green, no pollution
$ uv run autotester doctor                 # doctor: clean (file-too-long on app.py/test_ui.py
                                            #   resolved by the module split above)
$ uv run autotester map                    # docs/MAP.md regenerated
```

**Real live Docker verification (not just `TestClient`) — three separate runs across the RU4
fix's two iterations, each seeding a throwaway project against the container's own UI server
(`http://localhost:8000/`, deliberately not Pathlynks — this unit is about the generic route,
not that project's specific login-flow-vs-shared-profile interaction) then deleting it:**

1. Before RU4 existed: `docker compose restart` (pick up the new `/run` route) →
   `POST /projects/run-button-demo/run` → `404 Not Found` — confirmed the route itself resolves
   only after a restart (uvicorn has no `--reload`), not a code bug.
2. After the first (buggy, module-level) RU4 attempt: `POST /projects/run-button-demo/run` →
   `400 {"detail":"no AI provider is configured..."}` even though `.env` genuinely has
   `GEMINI_API_KEY` — confirmed the process-env gap was real, not imagined.
3. After the lifespan fix + module split, fresh `docker compose restart`, fresh seed
   (`run-button-demo3`): `POST /projects/run-button-demo3/run` → `303 See Other`,
   `location: /projects/run-button-demo3/report`; `GET .../report` shows a real graded result
   (`FAIL`, from a real Gemini judgment on real evidence — not a mock, not `INCONCLUSIVE`
   from a broken pipeline). Verified case/verdict JSON on disk in the container: real screenshot
   path, `grader_provider: gemini`, an honest verdict note, `rubric_hash` pointing at a real
   lazily-created rubric (`stages/run_case_pipeline.py`, already checker-PASSed this session).
4. Cleaned up every throwaway project + its browser profile after each check
   (`rm -rf projects/run-button-demo* profiles/run-button-demo*`).

## How to verify

- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean, no cross-test pollution.
- `uv run pytest tests/test_ui_runs.py -v` → 4 passed.
- Seed a throwaway project + case pointed at `http://localhost:8000/` (the container's own UI,
  to avoid Pathlynks' known shared-profile interaction), `docker compose restart`, then
  `curl -X POST http://localhost:8010/projects/<slug>/run` → `303` to `/report`, with a real
  graded verdict on disk under `projects/<slug>/runs/<run-id>/`. Delete the throwaway project +
  profile after.
- Read `src/autotester/ui/app.py`'s `_lifespan` and confirm it is NOT a module-level call —
  `TestClient(app)` (no `with`) must never see the real `.env` values.

## Scope notes for the checker

- The module split (`helpers.py`/`routes_runs.py`/`routes_credentials.py`) is a real refactor,
  not decoration — `app.py` was pushing past `autotester doctor`'s 300-line limit once the run
  route was added. Please confirm no route's behavior changed by comparing `git diff` — it should
  show relocated code, not rewritten logic, for everything except the new lifespan hook and the
  new `trigger_run` function itself.
- Please independently confirm the lifespan-vs-module-level distinction actually holds — e.g. run
  the full suite yourself and confirm no `GEMINI_API_KEY`/`ANTHROPIC_API_KEY` leak into
  `test_providers.py`/`test_langchain_fallback.py`, the exact failure mode this unit's own first
  attempt hit.
- Do your own live-Docker verification if you can — a real `303` + real graded verdict on disk is
  the actual proof RU4 holds, not the pasted output above.

## Status: ready-for-check
