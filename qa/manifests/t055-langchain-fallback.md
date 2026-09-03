# Manifest — t055-langchain-fallback

**Contract:** qa/contracts/langchain-fallback.md (LC1–LC5, new this cycle) + qa/contracts/core-invariants.md
**Goal task:** T-055 (`user_value: high`, added this cycle)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** resolves the architecture gap logged in `qa/feedback-inbox.md`
(2026-09-03, "on provider architecture") — unblocks AT-033 (T-050 grading deferred)

## Why this unit, and why now

Umesh's direct feedback (recorded in `qa/feedback-inbox.md`): no single-provider dependency —
LangChain-based fallback chain, Anthropic → Gemini → Ollama → ChatGPT. Earlier this session he
asked to WAIT on this rather than take a throwaway shortcut; when explicitly told to stop asking
and drive to the goal ("you are /maker so do the needful... don't stop until you achieve the
/goal"), this became the highest-leverage unblock available — it's what T-050 (and everything
downstream of it: T-090, T-100, T-110, T-120) was actually waiting on.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-055 providers/langchain_fallback.py: multi-vendor
fallback"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for provider fallback. Wrote `qa/contracts/langchain-fallback.md` (LC1–LC5)
before writing any code.

## What changed

- `pyproject.toml` — added `langchain-core`, `langchain-anthropic`, `langchain-google-genai`
  (`uv add`, resolved cleanly, 31 packages installed).
- `qa/contracts/langchain-fallback.md` (new) — LC1 (drop-in `Provider`, zero caller changes) ·
  LC2 (ordered, conditional chain) · LC3 (falls through, reports the real winner via `self.id`) ·
  LC4 (exhausted chain fails loudly, names every tier's error) · LC5 (no live call in tests).
- `src/autotester/providers/langchain_fallback.py` (new, 130 lines) — `LangChainFallbackProvider`.
  `_default_chain()` builds the ordered (id, factory) list from whichever env credentials exist
  (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY`).
  `_call` tries each tier via `.with_structured_output(schema, include_raw=True).invoke(prompt)`,
  catching any exception and falling through; on success sets `self.id = <winning tier>` BEFORE
  calling `self.record(...)` (found a real bug during testing: recording before setting `id`
  attributed usage to the generic `"langchain-fallback"` label instead of the real vendor — fixed,
  test `test_first_tier_success_sets_id_and_records_usage` pins the correct order).
- `src/autotester/providers/__init__.py` — registered `"langchain-fallback"`.
- `src/autotester/schema/project.py` — `ProviderConfig` defaults for `agent`/`judge` changed from
  `"anthropic"` to `"langchain-fallback"` (the new recommended default; `"anthropic"` stays
  registered and usable standalone for anyone who wants to pin one vendor).
- `projects/pathlynks/project.json` — `providers.agent`/`providers.judge` updated to
  `"langchain-fallback"` to match (a project-config data edit, not a contract/enforcement path).
- `tests/test_langchain_fallback.py` (new, 10 tests) — registry resolution; first-tier success
  sets `id`/records usage under the right provider name; falls through one tier, and three tiers
  deep; every-tier-failure raises `ProviderError` naming each failure; a `None` parsed result
  counts as a failure and falls through; empty chain → `available()` False and a clean
  `ProviderError`, no network call; missing schema raises; missing `usage_metadata` defaults to
  zero rather than raising.
- `docs/ARCHITECTURE.md` — concept→file row. 147 lines (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## Real validation performed (not simulated) before committing to this design

Before writing the module, validated the actual mechanism live against the two real credentials
in `.env` (Anthropic invalid/empty, Gemini real):
```
$ uv run python -c "... ChatAnthropic(api_key='sk-invalid-test-key').with_structured_output(...).with_fallbacks([ChatGoogleGenerativeAI(...).with_structured_output(...)]).invoke(...)"
<class '__main__.Answer'> result='ok' reason='fallback worked'
```
Confirmed the real Gemini model id is `gemini-3.6-flash` (the `.env`'s working key rejected
`gemini-2.5-flash` as retired: "no longer available to new users... use models/gemini-3.6-flash").

## How to verify (commands + expected)

- `uv run pytest tests/test_langchain_fallback.py -v` → 10 passed
- `uv run pytest -q` → exit 0, 145 collected (was 135 before this unit: +10)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 147 (≤ 150)
- Real end-to-end proof: see `qa/manifests/t050-pathlynks-first-run.md`'s cycle-2 entry — this
  provider genuinely graded all 3 T-050 cases for real, falling through to Gemini since
  `ANTHROPIC_API_KEY` is empty, producing evidence-cited `PASS` verdicts.

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_langchain_fallback.py -v
..........                                                               [100%]
10 passed
$ uv run pytest -q
................................s....................................... [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- Per the no-fire list, Ollama/ChatGPT tiers are NOT proven to work end-to-end in this
  environment (no Ollama server or OpenAI key here) — only that the mechanism conditionally
  includes a tier when configured, which is what LC2 actually requires.
- `see_video`/vision role is not implemented by this provider — inherits the base class's
  `Unsupported` behavior, matching every other non-vision provider in this codebase.
- The `id`-before-`record` ordering bug (found and fixed during this cycle's own test-writing,
  before any checker involvement) is called out explicitly in "What changed" for the checker's
  own independent judgment, not smoothed over.
- No secrets touched by this unit's own files — `.env`'s real keys were read only via
  `os.environ`/`load_dotenv` inside code paths, never printed or logged; the module's docstring
  and tests use fake keys/values only.

## Status: checked-PASS

Reconciliation note (2026-09-03): this manifest was never flipped from ready-for-check at the time, even though qa/verdicts/t055-langchain-fallback.md recorded PASS and the unit shipped (see docs/FEATURES.jsonl / .goal/goal.json). Corrected during a disk-state reconciliation pass -- no re-check performed, no new claim made; the verdict file is the actual evidence, this is only the manifest catching up to it.
