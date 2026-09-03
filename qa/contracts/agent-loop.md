# Contract — Agent fallback loop (T-080)

**Covers:** goal task T-080. **Owner:** /checker. **Criticality:** MEDIUM — a cost-control and
resilience feature (a case survives a UI change without a human rewriting it), not itself on the
critical path to the north star's first scorecard.
**Depends on:** `core-invariants.md` (all), `execute.md` (E1-E5, dependency — `run_case` is
reused unchanged), `browser-and-secrets.md` (B1-B9, dependency).

## Purpose

When `execute.py::run_case` returns `ERRORED` (a script-first run broke partway through, e.g. a
selector changed), ask an agent provider to propose a fix for the one step that failed, retry, and
— on success — persist the corrected case so the next run needs no agent call at all. This is the
plan's "agent only pays tokens on new or broken cases" line, made literal.

## Design decision this contract locks in (read with skepticism — same cycle as the code)

The plan's `Script` model (a literal `.py` file per case, path under
`projects/<slug>/scripts/`) is **not implemented by this unit**. There is no script-execution
engine in this codebase yet (nothing runs a `Script.path` file), and building one is a separate,
larger concern (arbitrary-code-execution surface) than fixing one broken step. Instead,
"durable" is delivered by persisting the **corrected `Case`** (content-addressed, via
`ProjectStore.add_case`) — the next call to `stages/execute.py::run_case` against that corrected
case replays it deterministically, with zero agent involvement, which satisfies T-080's own
acceptance note ("re-run is script-only, ~zero tokens") without literal source generation. If
this interpretation is judged to fall short of the task's intent, the fix direction is scoping a
follow-on unit for literal script generation — not re-litigating this one under a different name.

## Criteria

### AL1 — The agent is never consulted on a clean run
`run_with_fallback` calls `run_case` first; if the outcome is not `ERRORED`, it returns
immediately with `iterations=0`, `fixed=False`, and the agent provider's `act` is never called.

### AL2 — The agent sees only the failing step, not the case's full history
`build_fix_prompt` renders only: the case's title/rationale (context, not history), the one
step that failed (action + target), the executor's error message, and the last screenshot's
filename. It never renders the full `case.steps` list, any prior fix's reasoning, or a script.

### AL3 — A working fix is folded back and is idempotent
On a step fix that resolves the error, `Case.with_fixed_step` produces a new `Case` with the
failing step's `action`/`target`/`value` replaced and a `note` recording the agent's reasoning,
and a **recomputed content-addressed id** (different steps → different id, per `Case`'s existing
`compute_id` contract) — so persisting the same fix twice via `ProjectStore.add_case` never
creates a duplicate row.

### AL4 — A bounded number of attempts, never an infinite loop
`run_with_fallback` retries at most `MAX_ITERATIONS` (5) times. If every attempt still ends
`ERRORED`, it returns the last result with `fixed=False` and `iterations=MAX_ITERATIONS` — it
never raises, never loops unbounded, and never silently claims success.

### AL5 — Prompt is a file, not an inline string
The fix prompt lives at `prompts/agent_fix_v1.md`; `build_fix_prompt` only fills placeholders.

## No-fire list

- Literal `Script` (`.py` file) generation and a script-execution engine — explicitly deferred,
  see the design-decision note above.
- Multi-step fixes (the agent proposes exactly one corrected step per call; a case broken in two
  places takes two fix iterations, each seeing only the step currently failing).
- Vision-based screenshot analysis by this stage itself — the screenshot's *filename* is passed
  to the prompt as a reference; whether/how the provider actually looks at image content is a
  provider-level concern (`AnthropicProvider` today sends text-only prompts; multimodal image
  attachment is a future enhancement, not required for this contract).
- Real network calls to Anthropic in the default test suite — `tests/test_agent_loop.py` uses
  `MockProvider` exclusively; `AnthropicProvider` itself is exercised only for `available()` and
  its structured-output plumbing shape, never a live API call, in this unit's own tests.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-080 — no contract existed before this cycle.
