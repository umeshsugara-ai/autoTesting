# Manifest — at126-127-gemini3-detection

**Unit:** AT-126/AT-127 — model-version detection loses config fields silently
**Contract:** `qa/contracts/ingest.md` (provider seam), C8
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-126 (medium), AT-127 (medium)

## What was wrong

- **AT-127**: `GeminiProvider._config`'s 3.x-model detection was a bare
  `self._model.startswith("gemini-3")`. The Gemini SDK's own fully-qualified model form
  (`models/gemini-3.6-flash` — what `client.models.list()` returns, and a form a user could
  reasonably pass via `cli_video.py`'s `--model` flag) fails that check, so the provider silently
  fell into the `elif opts.temperature` branch and never applied `media_resolution` — a wrong
  answer with nothing failing.
- **AT-126**: `_config`'s own docstring says "3.x models take `media_resolution` and a thinking
  level," but `thinking_level` (a real, already-declared `VisionOptions` field, default `"high"`)
  was never read or turned into a `thinking_config` — documented behaviour that did not exist.

## What changed

- `src/autotester/providers/gemini.py` — new module-level `_is_gemini_3(model) -> bool`:
  `model.removeprefix("models/").startswith("gemini-3")`, tolerating the SDK's fully-qualified
  form. `_config` now calls this instead of the bare `startswith`, and its 3.x branch now also
  builds `kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=opts.thinking_level.upper())`
  — matching the `media_resolution` line right above it, same style.
- `tests/test_gemini_config.py` (**new file**, split from `test_gemini_schema.py` — that file is
  scoped to the response-schema sanitiser, AT-230; this is model-version detection, a different
  seam) — 8 tests: `_is_gemini_3` on bare/fully-qualified/older-model forms, `_config` applying
  `media_resolution` for the fully-qualified form, falling back to `temperature` for an older
  model, applying `thinking_config` for a 3.x model (two option values), and NOT setting
  `thinking_config` for an older model.

## How to verify (commands + expected)

- `uv run pytest tests/test_gemini_config.py -q` → expected: exit 0, 8 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_gemini_config.py -q
........                                                                 [100%]  (8 passed)

$ uv run pytest -q
[all dots, exit 0]
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. Extracted clean `HEAD`, layered my diff on (the new untracked test file copied in manually).
2. `uv sync`; confirmed `autotester.__file__` resolves inside the extract.
3. Baseline: `uv run pytest tests/test_gemini_config.py -q` → 8 passed, exit 0.
4. **Mutation A — revert `_is_gemini_3` to the bare `startswith`**: **exactly the 2 predicted
   tests failed** (`test_is_gemini_3_recognises_the_fully_qualified_sdk_form`,
   `test_config_applies_media_resolution_for_the_fully_qualified_form`), the other 6 stayed green.
5. **Restored, then mutation B — remove the `thinking_config` block entirely**: **exactly the 2
   predicted tests failed** (`test_config_applies_thinking_level_for_a_3x_model`,
   `test_config_thinking_level_follows_the_declared_option`, both `AttributeError: 'NoneType'
   object has no attribute 'thinking_level'`), the other 6 stayed green.
6. Extract deleted; live tree confirmed to carry only the two real edits throughout.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/providers/gemini.py`,
`tests/test_gemini_config.py`. Pure provider-config logic, no route/template touched — no
network call reachable without a real API key either, so this is exercised through the SDK's own
`GenerateContentConfig` object construction (the same instrument `test_gemini_schema.py` already
uses for `response_schema`), not a live Gemini call.

## What this unit does not claim

- Does not claim `_is_gemini_3` is a complete model-name parser — only that it now tolerates the
  one real ambiguity measured (an optional `models/` prefix). A third naming shape would be its
  own finding.
- Does not verify against a real Gemini API call (no key configured in this environment) — the
  config OBJECT the SDK would receive is asserted directly, which is what a real call would also
  build from the same code path.

## Status: ready-for-check
