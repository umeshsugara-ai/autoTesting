# Verdict — t055-langchain-fallback

**Date:** 2026-09-03
**Cycle checked:** 1
**Contract:** qa/contracts/langchain-fallback.md (LC1–LC5)
**Manifest:** qa/manifests/t055-langchain-fallback.md

## Re-run evidence (fresh, this check — nothing pasted trusted)

```
$ uv run pytest tests/test_langchain_fallback.py -v
tests\test_langchain_fallback.py ..........                              [100%]
10 passed in 0.08s

$ uv run pytest -q
................................s....................................... [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
exit 0 (all pass, 1 skip, no failures)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ wc -l docs/ARCHITECTURE.md
147 docs/ARCHITECTURE.md   (<=150)
```

## Criteria judged against the code directly

- **LC1** — `src/autotester/providers/langchain_fallback.py:77` `LangChainFallbackProvider(Provider)`
  implements `act(prompt, schema=None)` and `judge(prompt, schema)` matching
  `providers/base.py:48,53` signatures exactly. `abstractmethod available()` implemented
  (`langchain_fallback.py:93`). Confirmed `grade.py`/`stages/agent_loop.py` are untouched by this
  unit (not present in the manifest's "What changed", and `git diff` shows no changes to either
  file in the unit's own scope). MET.
- **LC2** — `_default_chain()` (`langchain_fallback.py:32-74`) builds Anthropic → Gemini → Ollama →
  ChatGPT strictly in that order, each `if os.environ.get(...)` gated on its own credential
  (`ANTHROPIC_API_KEY`; `GEMINI_API_KEY` or `GOOGLE_API_KEY`; `OLLAMA_BASE_URL`; `OPENAI_API_KEY`).
  SDK imports are deferred inside each `make_*` factory closure, so an unconfigured tier never
  imports its SDK. MET.
- **LC3** — `_call` (`langchain_fallback.py:102-117`) loops the chain, catching bare `Exception`
  per tier and continuing; `_try_tier` (`langchain_fallback.py:119-131`) sets `self.id = name`
  at line 127 **before** calling `self.record(...)` at line 129 — verified the order directly in
  the source, not by trusting the manifest's claim of a fixed bug. `record()` in
  `providers/base.py:62-78` stamps `ProviderUsage.provider = self.id`, so usage is attributed to
  the winning tier, not the generic `"langchain-fallback"` id. `test_first_tier_success_sets_id_and_records_usage`
  and `test_falls_through_to_second_tier_on_failure` pin this in the test file and both pass. MET.
- **LC4** — exhausted-chain path (`_call`, lines 108-117) collects `f"{name}: {type(exc).__name__}: {exc}"`
  per tier into `errors` and raises one `ProviderError` naming every tier + its failure — never a
  silent `None`/bare exception. `test_raises_when_every_tier_fails` exercises this and passes. MET.
- **LC5** — read `tests/test_langchain_fallback.py` in full (152 lines). Every chat model is
  `FakeChatModel`/`FakeStructured`/`FakeRawMessage` — no `langchain_anthropic`, `langchain_google_genai`,
  `langchain_ollama`, or `langchain_openai` import anywhere in the file; no real API key string;
  `chain=[]` or `chain=chain_of(...)` is passed explicitly to the constructor in every test,
  bypassing `_default_chain()` (and therefore the real env-based credential lookup) entirely.
  No network call possible. MET.

## Wiring checked beyond LC1-LC5

- `src/autotester/providers/__init__.py:9,15` imports `LangChainFallbackProvider` and registers it
  under `"langchain-fallback"` in `_REGISTRY`. Confirmed by direct read.
- `src/autotester/schema/project.py:48-49` — `ProviderConfig.agent` and `.judge` defaults are now
  `"langchain-fallback"` (was `"anthropic"`), confirmed by direct read + grep.
- `projects/pathlynks/project.json:48-52` — `providers.agent`/`providers.judge` both
  `"langchain-fallback"`, matching the schema default change. Confirmed by direct read.

## No-fire list / scope notes verified as claimed

- Ollama/ChatGPT tiers are not proven end-to-end here (no server/key configured) — this is
  explicitly out of scope per the contract's no-fire list; LC2 only requires the conditional
  mechanism, which is proven by code + the multi-tier fallback tests. Not counted against the unit.
- `see_video` unimplemented — inherits `Provider.see_video`'s `Unsupported`, unchanged; matches
  every other non-vision provider. Confirmed no override in `langchain_fallback.py`.

## Scoreboard

SCOREBOARD: 5/5 criteria met, all core-invariants.md invariants hold (no raw secrets touched by
this unit's own files; module reads env vars only, never logs/prints keys)

## Verdict

VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 0/0 invariant violations found
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All five LC criteria verified directly against the source (not the manifest's
narrative) — the id-before-record ordering fix at langchain_fallback.py:127-129 is real and
correctly ordered, the chain is genuinely conditional per credential with deferred SDK imports,
and the test file contains zero real network calls. All re-run commands (pytest unit + full
suite, ruff, doctor, ARCHITECTURE.md line count) reproduced the manifest's claimed results
exactly. Registry, schema default, and pathlynks project.json wiring all confirmed by direct
read.
