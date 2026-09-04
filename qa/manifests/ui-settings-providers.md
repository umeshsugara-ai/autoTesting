# Manifest — ui-settings-providers

**Contract:** qa/contracts/ui-settings.md US1-US4 (new this cycle)
**Goal task:** none (`.goal/goal.json` is 20/20 done — ad-hoc plan work,
`C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md` §3d)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Plan §3d, the last of the four §3 units: Umesh's original ask included "ai, api set kar paaye" —
a non-technical user must be able to configure the global model provider keys without opening
`.env` in a text editor.

## What changed

- `qa/contracts/ui-settings.md` (new) — US1 (exactly the six known provider keys, no more) · US2
  (a real value is never rendered, matching U3's credential-editor discipline) · US3 (writes go
  through the existing, unchanged `env_editor.set_env_value` — no second write path) · US4
  (reachable from the shared nav).
- `src/autotester/ui/routes_settings.py` (new) — `GET`/`POST /settings/providers`. `_PROVIDER_KEYS`
  is the closed tuple of six keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`,
  `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OPENAI_API_KEY`) named in the plan; the view renders a
  masked status pill per key (same `theme.pill`/table pattern as `routes_credentials.py`'s
  per-project editor); the submit route 400s on any key outside that tuple before ever touching
  disk, then delegates the actual write to `env_editor.set_env_value` unchanged.
- `src/autotester/ui/app.py` — `app.include_router(routes_settings.router)` wired in.
- `src/autotester/ui/theme.py` — `NAV` gets a `⚙ Settings` link to `/settings/providers`.
- `tests/test_ui_settings.py` (new, 6 tests) — all six keys shown and nothing else; a real value
  is never rendered even after being set; a POST writes via the real `.env` file and never echoes
  the new value back; an unknown key is refused with 400 before any write; a newline-smuggling
  value is refused (mirrors U3's existing injection test); the settings link is present on the
  homepage nav.
- `docs/MAP.md` regenerated.

## Deliberate scope decision (per the contract's own no-fire list)

This page only records presence/absence, exactly like the per-project credential editor (U3) — it
never makes a real call to a provider to validate a key works. That is a genuinely different,
separate concern (and would cost real API usage on every page load), explicitly out of scope per
US1-US4 and the contract's no-fire list.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui_settings.py -v   # 6 passed
$ uv run pytest -q                              # full suite green, no regressions
$ uv run ruff check src tests scripts           # All checks passed!
$ uv run autotester doctor                      # doctor: clean
$ uv run autotester map                         # docs/MAP.md regenerated
```

**Real live Docker verification (GET only — see the safety note below):**

```
$ docker compose restart && curl http://localhost:8010/  # 200, container picked up the new route
$ curl http://localhost:8010/settings/providers           # 200
```

- All six keys present in the rendered page (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`,
  `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OPENAI_API_KEY`), confirming US1.
- Status pills genuinely reflect the real `.env` on disk (`GEMINI_API_KEY` and two others show
  "Set", the rest "Not set") — no real value string appears anywhere in the response body,
  confirming US2.
- `curl http://localhost:8010/` shows `/settings/providers` in the nav markup, confirming US4.

**Safety note — no live POST against the shared `.env`:** unlike the throwaway per-project demos
used to verify §3b/§3c, this page's six keys are the *actual* global credentials real projects
(Pathlynks etc.) depend on right now. A live `POST /settings/providers` against the running
container would overwrite a real, in-use key with a test value. POST/US3 is instead verified via
`tests/test_ui_settings.py`'s isolated `scratch_root` fixture (a fresh temp `.env`, never the real
one) — the same isolation every other `.env`-writing test in this project already relies on
(`test_ui.py`'s U3 credential-editor tests use the identical pattern). This is a deliberate,
documented scope boundary, not a gap: the write path itself (`env_editor.set_env_value`) is
unchanged, already-hardened code, re-verified by these new tests in isolation rather than risking
production credentials for one more layer of live proof.

## How to verify

- `uv run pytest tests/test_ui_settings.py -v` → 6 passed.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- `curl http://localhost:8010/settings/providers` → 200, all six keys shown, no real value in
  the body, status pills matching the real `.env`. Do **not** POST against the live container's
  `.env` — use the isolated pytest tests to verify the write path.

## Scope notes for the checker

- Please do NOT POST to the live Docker container's `/settings/providers` with a real key name —
  it would overwrite this repo's actual, in-use provider credentials. Verify US3 via the pytest
  suite's isolated `scratch_root` fixture, exactly as this manifest did.
- Confirm `_PROVIDER_KEYS` is exactly the six keys named in the plan, no more, no fewer, and that
  `provider_settings_submit` 400s before calling `set_env_value` for anything outside that tuple.

## Status: ready-for-check
