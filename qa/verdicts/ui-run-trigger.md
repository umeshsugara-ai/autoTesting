# Verdict — ui-run-trigger

**Contract:** qa/contracts/ui-run.md RU1-RU4
**Manifest:** qa/manifests/ui-run-trigger.md
**Cycle checked:** 1
**Date:** 2026-09-04
**Checked by:** /checker (Mode A, fresh subagent, no builder context)

## VERDICT: PASS

SCOREBOARD: 4/4 criteria met, 0/0 additional invariants (contract has none beyond RU1-RU4)

## What I re-ran myself (not trusted from the manifest)

- `uv run ruff check src tests scripts` -> All checks passed!
- `uv run pytest -q` -> full suite green (no failures/errors), including
  `tests/test_providers.py` and `tests/test_langchain_fallback.py` (the exact tests the manifest
  says a module-level `load_dotenv` polluted) run together in the same process as `test_ui.py`/
  `test_ui_runs.py` — no leak observed.
- `uv run pytest tests/test_ui_runs.py -v` -> 4 passed.
- `uv run autotester doctor` -> clean (confirms `app.py` is back under the 300-line limit after
  the split).
- Read `src/autotester/ui/app.py` directly: `_lifespan` is an `@asynccontextmanager` function
  passed to `FastAPI(lifespan=_lifespan)`, `load_dotenv(repo_root() / ".env")` is called only
  inside it — not at module level. `TestClient(app)` in the test suite is never used as a `with`
  block, so this call never fires during pytest, matching the manifest's claim.
- `git show 20f4f95 -- src/autotester/ui/app.py`: confirmed the removed code
  (`_require_slug`/`_require_safe_id`/`_project_slugs`/`_load_project_or_404`, the `/env` routes,
  `run_view`, `report`) reappears byte-for-byte in `helpers.py`/`routes_credentials.py`/
  `routes_runs.py` — the diff is a real relocation, not a rewrite, except for the new lifespan
  hook and the `run_button` HTML added to `project_detail`. `env_editor.py` (pre-existing helper
  module, not part of this unit) is still correctly imported by the new `routes_credentials.py`.
- Read `src/autotester/ui/routes_runs.py::trigger_run`: loads cases, 400s if empty, then
  constructs `LangChainFallbackProvider()` and 400s if `.available()` is `False` — in that exact
  order (RU2). Calls `run_and_grade_case` from `stages/run_case_pipeline.py` per case via a real
  `BrowserSession`, saves each result/verdict through `ProjectStore`, saves a `Run` record, then
  `RedirectResponse(..., status_code=303)` to `/projects/{slug}/report` (RU1, RU3).

## Independent live-Docker verification (own reproduction, not the manifest's pasted output)

Container `autotesting-autotester-1` was already running (bind-mounted `.:/app`, so it already
held this commit's code — confirmed by grepping `_lifespan` inside the container).

1. Confirmed a real provider is configured from the container's own `.env` via lifespan-style
   load: `load_dotenv('.env'); LangChainFallbackProvider().available()` -> `True` (no secret
   values printed).
2. Seeded a throwaway project `checker-ru-verify` (zero cases) via `ProjectStore` inside the
   container. `POST /projects/checker-ru-verify/run` -> **`400 {"detail":"project
   'checker-ru-verify' has no cases to run"}`** — reproduces RU2's first branch live.
3. Added one real case (`navigate` to a fixture page served on a fixed local port). First
   `POST /run` attempt used a slug/domain mismatch on my part (`127.0.0.1` vs `allowed_domains:
   ['localhost']`) and correctly 400'd via the browser's own domain-allowlist guard (unrelated
   safety mechanism working as designed, not a contract failure) — result persisted as
   `outcome: errored`, `INCONCLUSIVE`, `grader_provider: rule` on disk.
4. Fixed the allowed_domains to match, re-triggered: **`POST /projects/checker-ru-verify/run` ->
   `303 See Other`, `location: /projects/checker-ru-verify/report`.** On-disk verdict JSON in the
   container:
   ```
   {"result": "PASS", "criteria_met": 1, "criteria_total": 1,
    "grader_provider": "gemini", "rubric_hash": "rub_59a268c166db"}
   ```
   A real Gemini judgment (`grader_provider: gemini`, not "rule"/mock) — proves RU4: the
   lifespan-loaded `.env` key was genuinely visible to `LangChainFallbackProvider()` inside the
   live uvicorn process, and RU1/RU3: a real `BrowserSession` ran the case and both the result and
   verdict were persisted via `ProjectStore`, plus a `Run` record (`run.json` on disk with the
   correct `case_ids`).
5. `GET /projects/checker-ru-verify/report` rendered the real stat (`1 PASS`) from the on-disk
   verdict, not a stub.
6. Cleaned up: killed the fixture `http.server`, `rm -rf projects/checker-ru-verify
   profiles/checker-ru-verify` inside the container (bind-mounted, so also gone on the host —
   confirmed via `git status`/`ls projects/` on the host afterward: no leftover, no host diff).

## Criteria

- **RU1** (real synchronous run, no second execution path) — MET. Code reads directly through
  `run_and_grade_case`/`BrowserSession`; live run took measurable wall-clock time (request blocked
  until the browser finished) and produced a genuinely provider-graded verdict, not a canned one.
- **RU2** (honest 400 before any browser starts, cases-then-provider order) — MET. Reproduced live:
  empty-cases 400 with the exact message in the manifest; code order matches (cases checked before
  `LangChainFallbackProvider()` is even constructed).
- **RU3** (every case run and persisted, `Run` record saved, 303 to report) — MET. Reproduced
  live: result + verdict JSON on disk, `run.json` with correct `case_ids`, `303` with the correct
  `Location` header, report page renders the real result.
- **RU4** (global provider keys visible to the running process via `.env`) — MET. Reproduced live
  end-to-end: a real Gemini grading happened from the running Docker/uvicorn process using a key
  only present in `.env`, and static-read confirms the load happens in a lifespan hook (never a
  module-level call), so `TestClient(app)` without `with` cannot leak it into the pytest process —
  consistent with the full pytest suite passing with no `test_providers.py`/
  `test_langchain_fallback.py` pollution.

## Issues

None found. No new `qa/issues.jsonl` entries. No issues were claimed as addressed by this
manifest ("Issues addressed: none") — nothing to cross-check there.

## Scope notes honored

Per the contract's no-fire list, I did not require a background job queue, report enrichment
(history list, screenshots, downloads), or a `/settings/providers` page — none of those are RU1-RU4
criteria.

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 0/0 invariants (none defined beyond RU1-RU4)
FAILURES: none
ISSUES-WRITTEN: none
EXPLANATION: All four criteria were independently reproduced against the live Docker container
(not just the manifest's pasted transcript) — RU2's honest 400 on zero cases, RU1/RU3's real
BrowserSession run with persisted result/verdict/Run record and 303 redirect, and RU4's lifespan-
only `.env` load proven by a real Gemini-graded verdict from the running process plus a clean full
pytest run with no cross-test env leakage. The module split is a genuine relocation confirmed via
`git show`, not a rewrite-in-disguise.
