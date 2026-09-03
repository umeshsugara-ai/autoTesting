# Contract — Multi-vendor provider fallback (T-055)

**Covers:** goal task T-055. **Owner:** /checker. **Criticality:** HIGH — removes the
single-vendor dependency that blocked T-050's grading and every high-value task after it.
**Depends on:** `core-invariants.md` (all).

## Purpose

No stage should ever be unable to get a judge/agent answer just because one vendor's key is
missing, rate-limited, or down. `LangChainFallbackProvider` implements the existing
`providers.base.Provider` seam (so `grade.py`/`agent_loop.py` need zero changes) by trying an
ordered list of LangChain chat models — Anthropic → Gemini → Ollama → ChatGPT — falling through
on any failure, and reporting which vendor actually answered. Umesh, 2026-09-03: "no dependency
on any one model... there should be a fallback system and use LangChain."

## Criteria

### LC1 — Drop-in `Provider` implementation, zero caller changes
`LangChainFallbackProvider` subclasses `providers.base.Provider` and implements `act`/`judge`
with the same signatures as every other provider. `grade.py` and `stages/agent_loop.py` are not
modified by this unit — the seam already accepted any `Provider` instance.

### LC2 — Ordered fallback, each tier conditional on its own credential
The chain order is Anthropic → Gemini → Ollama → ChatGPT (Umesh's stated priority). A tier is
only added to the chain when its credential/service is actually configured
(`ANTHROPIC_API_KEY`/`GEMINI_API_KEY` or `GOOGLE_API_KEY`/`OLLAMA_BASE_URL`/`OPENAI_API_KEY`) — an
unconfigured tier costs nothing and does not require its SDK to be importable.

### LC3 — Falls through on ANY tier failure, reports the real winner
If a tier raises (auth error, network error, structured-output parse failure, or a `None`
parsed result), the provider tries the next configured tier without raising to the caller,
until one succeeds or the chain is exhausted. On success, `provider.id` becomes the winning
tier's name (e.g. `"gemini"`), read by the caller AFTER the call returns — so
`Verdict.grader_provider` and `ProviderUsage.provider` both name the vendor that actually
answered, never a generic `"langchain-fallback"` label.

### LC4 — Exhausted chain fails loudly, with every tier's error
If every configured tier fails, `_call` raises `ProviderError` naming each tier and its error —
never a silent `None` or an unexplained exception from deep inside a vendor SDK.

### LC5 — No live network call in the default test suite
`tests/test_langchain_fallback.py` exercises the fallback loop entirely against fake chat-model
objects mimicking LangChain's `with_structured_output(..., include_raw=True).invoke(prompt)`
shape — no test in the default suite calls a real vendor API.

## No-fire list

- `see_video` / vision role — not implemented by this provider (Gemini's own dedicated provider,
  when it exists for T-060, owns that role); `Provider.see_video`'s base-class `Unsupported`
  applies unchanged.
- Retry/backoff within a single tier (a tier either answers or it doesn't; retry policy is a
  future enhancement, not required here).
- Streaming responses, tool-call chains beyond the single structured-output call, or caching a
  constructed chat-model client across calls (each `_call` rebuilds tiers lazily — a deliberate
  v1 simplicity tradeoff, not a defect).
- Ollama/ChatGPT tiers actually working end-to-end in THIS environment (no Ollama server or
  OpenAI key is configured here) — LC2 only requires that the mechanism is genuinely
  vendor-agnostic and conditionally includes a tier when its credential exists; proving Ollama or
  ChatGPT specifically work is out of scope until someone configures one.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-055 — no contract existed before this cycle.
