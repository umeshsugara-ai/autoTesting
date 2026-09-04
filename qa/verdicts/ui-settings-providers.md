# Verdict — ui-settings-providers

**Contract:** qa/contracts/ui-settings.md US1-US4
**Manifest:** qa/manifests/ui-settings-providers.md
**Cycle checked:** 1
**Date:** 2026-09-04
**Checker:** fresh subagent, Mode A unit check, bound to D:/autoTesting

## What I re-ran myself

- `uv run pytest tests/test_ui_settings.py -v` → 6 passed (re-executed, not trusted from the
  manifest).
- `uv run pytest -q` → full suite green (2 skipped, unrelated to this unit), no regressions.
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean.
- `docker compose restart` then `curl http://localhost:8010/` → 200.
- `curl http://localhost:8010/settings/providers` → 200. Extracted every `<code>KEY</code>` cell
  from the response body: exactly `ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY,
  OLLAMA_BASE_URL, OLLAMA_MODEL, OPENAI_API_KEY` — no other key rendered anywhere in the page.
- Cross-checked live status pills against the real repo `.env` (key names only, values never
  read into this transcript): `GEMINI_API_KEY` (len 39) → "● Set"; `ANTHROPIC_API_KEY` present
  in `.env` but with an **empty value** (len 0) → correctly rendered "○ Not set" — `_present_keys`
  uses `parse_env(...)` + `if present.get(key)`, so an empty string is falsy and correctly treated
  as not-set. (The manifest's live-verification note said "GEMINI_API_KEY and two others show
  Set" — that undercounts/overstates slightly; only GEMINI_API_KEY is genuinely non-empty among
  the six in the real `.env`. This is a narrative inaccuracy in the manifest, not a behavior bug —
  the page's own logic is correct and conservative. Not scored against any criterion.)
- `curl http://localhost:8010/` and grepped for `/settings/providers` → present in nav markup.
- Read `src/autotester/ui/routes_settings.py`, `src/autotester/ui/env_editor.py`,
  `src/autotester/ui/theme.py` (NAV block), `src/autotester/ui/app.py` (router wiring) directly —
  did not trust the manifest's description of the diff.
- Did **not** POST to the live container per the manifest's safety note (real global credentials)
  — US3 verified via `tests/test_ui_settings.py`'s isolated `scratch_root` fixture
  (`AUTOTESTER_ROOT` → `tmp_path`, never the real `.env`) plus direct code read of
  `provider_settings_submit` and `set_env_value`.

## Criteria

- **US1 — exactly the six known keys, nothing else.** MET. Live page renders exactly the six
  `<code>` cells named in the contract; `_PROVIDER_KEYS` in `routes_settings.py` is the literal
  closed tuple of those six, in that order; no dynamic key rendering.
- **US2 — a real value is never rendered.** MET. Live GET body contains no raw value strings (the
  masked-status-only pill markup was the only status signal present); `test_settings_page_never_renders_a_real_value`
  independently re-run and passing; `provider_settings_view` never interpolates `present[key]`'s
  value, only truthiness via `_status_cell`.
- **US3 — writes go through the one legitimate `.env` write path.** MET. `provider_settings_submit`
  400s on any key outside `_PROVIDER_KEYS` before ever calling `set_env_value` (code-read
  confirmed, `raise HTTPException(400, ...)` precedes the call); the only write call in the module
  is the unchanged `env_editor.set_env_value` import — no second write path exists in
  `routes_settings.py`. `test_settings_refuses_an_unknown_key` and
  `test_settings_refuses_a_value_with_a_newline` re-run and passing (newline rejection inherited
  unchanged from `env_editor.set_env_value`'s existing `_KEY_RE`/`\n`/`\r` guard).
- **US4 — reachable from the nav.** MET. `theme.py` `NAV` literally contains
  `<a href="/settings/providers">⚙ Settings</a>`; live `curl http://localhost:8010/` confirms it
  renders on the homepage.

## Manifest's claimed issues addressed

None claimed; ledger unaffected.

## Scope notes honored

Did not attempt a live POST against the shared `.env` — verified US3 through the isolated pytest
fixture and direct code inspection, per the manifest's explicit safety note and this dispatch's
own instruction.

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 0/0 invariants hold (contract states none as `[I*]`)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All four criteria (US1-US4) are evidenced by re-run tests, direct code reading, and
independent live-container GET checks. The six-key closed set, no-value-ever-rendered discipline,
single write path with pre-write validation, and nav reachability all hold. No live POST was made
against the real `.env`, per the manifest's safety note and this dispatch's explicit instruction;
US3 is instead evidenced by the isolated-fixture tests plus direct inspection of
`provider_settings_submit` and `env_editor.set_env_value`, which is sufficient since the write
path itself is unchanged, already-hardened code.
