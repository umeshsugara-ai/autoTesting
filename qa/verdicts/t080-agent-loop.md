# Verdict — t080-agent-loop

**Date:** 2026-09-03
**Cycle checked:** 1
**Checker mode:** A (unit check), fresh context, bound to `d:/autoTesting`

## What I re-ran myself

- `uv run pytest tests/test_agent_loop.py -v` → 4 passed (0.29s)
- `uv run pytest tests/test_providers.py -v` → 4 passed (0.18s)
- `uv run pytest -q` → exit 0, 129 collected (74 dots @55% + 59 dots(incl. 1 skip) @100% seen in
  output; `--collect-only -q` file-by-file sum = 4+3+11+9+6+6+6+12+20+4+4+8+24+12 = 129, matching
  the manifest's claimed +8 over 121)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 143 (≤150)
- `grep -rn "ANTHROPIC_API_KEY" tests/` → only `tests/test_providers.py:27`, no literal key value
- `grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/` → no matches (C8,
  provider-agnostic — `stages/agent_loop.py` never imports the vendor SDK)
- Read in full: `src/autotester/providers/anthropic.py`, `src/autotester/stages/agent_loop.py`,
  `src/autotester/schema/case.py`, `tests/test_agent_loop.py`, `tests/test_providers.py`,
  `src/autotester/prompts/agent_fix_v1.md`, `src/autotester/providers/__init__.py`,
  `src/autotester/providers/base.py`
- Environment check: `ANTHROPIC_API_KEY` unset in the shell environment; repo-root `.env` has
  `ANTHROPIC_API_KEY=` (declared, empty) — genuinely no live key present in this environment.

## Criteria (qa/contracts/agent-loop.md)

- **AL1** (agent never consulted on a clean run) — MET. `run_with_fallback` calls `run_case`
  first (agent_loop.py:75); `test_no_error_never_calls_the_agent` asserts `iterations==0`,
  `fixed is False`, `agent.prompts == []`.
- **AL2** (agent sees only the failing step, not history) — MET. `build_fix_prompt`
  (agent_loop.py:54-64) renders only title/rationale/failing step/error/last-screenshot filename;
  never `case.steps` in full. `test_prompt_carries_only_the_failing_step_and_error` confirms the
  rendered prompt contains the broken selector + error text + title, and by construction of
  `build_fix_prompt` cannot contain the full step list.
- **AL3** (working fix folds back, idempotent) — MET. `Case.with_fixed_step` (case.py:47-61)
  replaces the failing step and returns a new `Case`; the content-addressed id recomputes via the
  unchanged `model_post_init`/`compute_id` mechanism because `steps` is part of the id payload
  (case.py:38-45). `test_one_fix_resolves_a_broken_selector` confirms `loop.case.id !=
  make_case().id` and the fixed step's target/note. `ProjectStore.add_case`'s existing
  content-addressed idempotency is unchanged by this unit (no modification to project_store.py).
- **AL4** (bounded attempts) — MET. `run_with_fallback`'s while-loop condition is `fixes_applied
  < MAX_ITERATIONS` (=5); `test_exhausts_max_iterations_when_the_fix_never_works` confirms
  `iterations==MAX_ITERATIONS`, `fixed is False`, no exception, 5 agent calls — never unbounded,
  never a false success.
- **AL5** (prompt is a file) — MET. `src/autotester/prompts/agent_fix_v1.md` exists (34 lines);
  `build_fix_prompt` only does `.replace()` on its text; no inline prompt string in
  `agent_loop.py`.

## Dependency contracts

- **core-invariants.md**: C1 (schema-first: `AgentFix` is a proper Pydantic model with
  `extra="forbid"`) MET; C2 (file/function size, ARCHITECTURE ≤150) MET via `doctor: clean` +
  `wc -l`; C3 (no dup concept, no `_v2`/`_new` filenames, edit-in-place) MET — `agent_loop.py` and
  `providers/anthropic.py` are new modules but the manifest states the reason (new stage / new
  vendor), consistent with prior units' pattern; C5 (secrets) — `AnthropicProvider` receives only
  rendered prompts, never a `SecretRef`/raw value, and this unit adds no new secret-touching
  surface; C7 (independent verification) MET — this very check is the independent re-run; C8
  (provider-agnostic) MET, confirmed by the grep above.
- **execute.md**: `run_case` is reused unchanged (agent_loop.py imports and calls it directly,
  no override/monkeypatch); E2's "screenshot after every step that doesn't raise" is the exact
  mechanism `_failing_step_order` relies on (agent_loop.py:39-46) — consistent, not duplicated.
- **browser-and-secrets.md**: not touched by this unit; no new secret-resolution path introduced.

## Live-API-call scrutiny (requested specifically)

Confirmed clean. `AnthropicProvider._structured` (anthropic.py:44-72) raises `ProviderError`
before any import or network activity when `available()` is false (`not self.available()` check
at line 45, before the lazy `from anthropic import Anthropic` at line 49). Every test in
`test_providers.py` either passes `api_key=None` (raises before the SDK import) or a fake
`"sk-test-key"` string but never calls `.act()`/`.judge()` far enough to reach `client.messages.create`
except through a path that already raises first (`test_act_without_a_schema_raises` fails the
schema check at line 47-48, before the SDK import at line 49). `tests/test_agent_loop.py` uses
only `MockProvider`, never `AnthropicProvider`. `ANTHROPIC_API_KEY` is unset in this session's
environment and declared-but-empty in the repo `.env`, so even an accidental code path reaching
the SDK import would fail on `available()` first. No live call occurred during any command I ran.

## Scope-interpretation scrutiny (requested specifically) — independent judgment

The contract's design-decision (persist a corrected `Case`, not a literal `.py` `Script` file) is
**functionally sound and fully evidenced for the narrow claim it makes** (re-running the corrected
case needs no agent — true, because `run_case` is the same deterministic executor for any case).
However, independent evidence in this codebase weighs against treating this as the *complete*
delivery of T-080's stated goal ("agent fallback loop that **emits a durable script**"):

1. `schema/case.py`'s `Script` class — added in the original design-lock commit (`a5ffcec`, before
   this unit existed) — is documented almost verbatim with this unit's own durability claim
   ("after the first successful agent run, a case costs zero tokens to re-run") but attached to a
   literal `path`/`generated_by`/`iterations`/`stable_runs` artifact, not a `Case`. `Case.script_ref`
   (also pre-existing) is the dedicated link field for exactly this purpose. Neither is touched by
   this unit.
2. `qa/contracts/execute.md`'s no-fire list — written in an earlier cycle, for T-040, not
   authored by this unit's maker — independently describes T-080 as "the agent fallback path
   (write→run→read→edit a generated script)," i.e. the literal-script expectation predates this
   unit's own contract and was not this unit narrowing its own scope after the fact.

Given the contract's own design-decision section explicitly pre-empts this exact scrutiny and
states the remedy is a follow-on unit ("not re-litigating this one under a different name") if the
interpretation is judged to fall short, I am treating that written escape valve as controlling: I
do **not** FAIL this unit over the gap, but I am recording it as a ledger finding (`AT-026`,
severity: medium) recommending a follow-on unit to build the `Script` artifact and wire
`Case.script_ref`, or a CRITICAL (human-gated) amendment to formally retire the unused
`Script`/`script_ref` schema surface if literal script generation is permanently out of scope.
This is exactly the "machinery runs but goal not fully achieved" case Mode B's gap analysis exists
to catch — surfaced here on the unit check rather than waiting for the next sweep.

## Issues

- Written: `AT-026` (medium, open) — see above.
- None of the manifest's `Issues addressed` claims apply (declared "none — new unit"), consistent
  with what I found.

## No-fire list respected

Did not raise: literal `Script`/execution-engine absence as a blocking defect (per the contract's
own no-fire list and design-decision escape valve — filed as a recommendation instead, not a
criterion failure); multi-step-fix-per-call absence; vision/image content absence in the prompt.

---

VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 8/8 invariants hold (C1,C2,C3,C5,C7,C8 core-invariants + E2/B-dependency reuse checked; C4/C6 unaffected by this unit)
FAILURES (if any):
- none
ISSUES-WRITTEN: AT-026
EXPLANATION: All five AL criteria are fully evidenced by tests I re-ran myself (8/8 new tests pass, 129/129 suite, ruff/doctor clean), no live Anthropic call is possible in this environment or reachable in any test path, and the prompt/id/bound-loop mechanics match the contract exactly. The corrected-Case-not-literal-script scope decision is defensible for its narrow claim but does not fully deliver T-080's stated goal given the pre-existing Script/script_ref schema surface — recorded as AT-026 (medium) recommending a follow-on unit rather than blocking this one, per the contract's own written escape valve.
