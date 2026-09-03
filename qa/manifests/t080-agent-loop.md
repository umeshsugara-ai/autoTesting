# Manifest — t080-agent-loop

**Contract:** qa/contracts/agent-loop.md (AL1–AL5, new this cycle) + qa/contracts/core-invariants.md
+ qa/contracts/execute.md (dependency) + qa/contracts/browser-and-secrets.md (dependency)
**Goal task:** T-080 (`user_value: normal`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none (new unit)

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-080 providers/anthropic.py + agent fallback loop that
emits a durable script"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for the agent fallback loop. Wrote `qa/contracts/agent-loop.md` (AL1–AL5)
before writing any code, following the `execute.md`/`grade.md`/`db-assert.md` pattern.

## Interpretive decision flagged for the checker (read the contract's own design-decision note)

The plan's `Script` model implies a literal `.py` file per case. This unit does **not** build
that or a script-execution engine (nothing in this codebase currently runs a `Script.path` file
— that would be a separate, larger arbitrary-code-execution concern). Instead, "durable" is
delivered by persisting the **corrected `Case`** via `ProjectStore.add_case` (content-addressed,
idempotent) — the next `run_case` call against it needs no agent. This satisfies T-080's own
note ("re-run is script-only, ~zero tokens") in spirit without literal source generation. Called
out explicitly in the contract itself so the checker judges this interpretation on purpose, not
by accident.

## What changed

- `pyproject.toml` — added `anthropic>=0.40.0`; `uv sync` installed it + its transitive deps
  (httpx, anyio, jiter, etc.).
- `qa/contracts/agent-loop.md` (new) — AL1 (agent never consulted on a clean run) · AL2 (agent
  sees only the failing step + error + last screenshot, never the case's full history) · AL3 (a
  fix is folded back with a recomputed content-addressed id — idempotent) · AL4 (bounded to
  `MAX_ITERATIONS=5`, never infinite, never a false success) · AL5 (prompt is a file).
- `src/autotester/providers/anthropic.py` (new, 68 lines) — `AnthropicProvider`: `available()`
  checks `ANTHROPIC_API_KEY` presence; `act`/`judge` both route through `_structured`, which
  forces a single named tool call shaped by the caller's Pydantic schema (`model_json_schema()`)
  and validates the tool's `input` back into that schema. The `anthropic` SDK import is lazy
  (inside `_structured`), so importing this module never requires a live key or a socket.
- `src/autotester/providers/__init__.py` — registered `"anthropic": AnthropicProvider` alongside
  the existing `"mock"` entry. No existing registration changed.
- `src/autotester/schema/case.py` — added `AgentFix` (the agent's proposed correction: action,
  target, value, reasoning) and `Case.with_fixed_step(order, fix)` (returns a new `Case` with
  that one step replaced; content-addressed id recomputes automatically via the existing
  `model_post_init`/`compute_id` mechanism — no change to that mechanism itself).
- `src/autotester/prompts/agent_fix_v1.md` (new) — the fix prompt, following the existing
  `relitigation_v1.md`/`grade_v1.md` placeholder pattern.
- `src/autotester/stages/agent_loop.py` (new, 76 lines) — `run_with_fallback(case, session,
  agent, docs=None) -> AgentLoopResult`. Runs `execute.py::run_case` unchanged; on `ERRORED`,
  locates the failing step (the first step past the last one with a screenshot — reusing E2's
  "screenshot after every step that doesn't raise" guarantee, no new bookkeeping needed), asks
  the agent for one fix, applies it via `Case.with_fixed_step`, re-runs. Loops up to
  `MAX_ITERATIONS` (5) times; returns `AgentLoopResult(result, case, iterations, fixed)`.
- `tests/test_agent_loop.py` (new, 4 tests) — a clean run never calls the agent; one fix resolves
  a broken selector (id changes, note records the reasoning, the corrected target is actually
  clicked); the loop exhausts `MAX_ITERATIONS` and reports `fixed=False` when the agent's fix
  never actually works; the prompt carries only the failing step/error/title, not the full case.
- `tests/test_providers.py` (new, 4 tests) — `anthropic` resolves via the registry;
  `available()` reflects key presence; `act()` without a key raises `ProviderError` without
  touching the network; `act()` without a schema raises (no live API call anywhere in this file).
- `docs/ARCHITECTURE.md` — two concept→file rows (`stages/agent_loop.py`,
  `providers/anthropic.py`); Status line updated. 143 lines (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_agent_loop.py -v` → 4 passed
- `uv run pytest tests/test_providers.py -v` → 4 passed
- `uv run pytest -q` → exit 0, 129 collected (was 121 before this unit: +8)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 143 (≤ 150)
- `grep -rn "ANTHROPIC_API_KEY" tests/` → only in `test_providers.py`, never a literal key value

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_agent_loop.py -v
....                                                                     [100%]
4 passed
$ uv run pytest tests/test_providers.py -v
....                                                                     [100%]
4 passed
$ uv run pytest -q
................................s....................................... [ 55%]
.........................................................                [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run autotester map
map: docs/MAP.md regenerated
$ uv run autotester snapshot
snapshot: 32 lines written
```

## Scope notes for the checker

- No live call to Anthropic anywhere in this unit's own tests — `ANTHROPIC_API_KEY` is not set
  in this environment, and `_structured`'s network call happens only after `available()` returns
  true, which every test either mocks around or deliberately sets `api_key=None`/a fake string to
  avoid.
- `EvidenceKind.DB` / `stages/agent_loop.py` do not interact — this unit is independent of T-045.
- Per the no-fire list: no literal `Script`/`.py` file is generated or executed; no multi-step
  fix in one agent call; no image/vision content sent to the provider (text-only prompt,
  screenshot referenced by filename only).
- T-080's `done_check` in `.goal/goal.json` is `uv run pytest tests/test_agent_loop.py -q`, which
  passes (4/4).

## Status: checked-PASS

Verdict: `qa/verdicts/t080-agent-loop.md` (Cycle checked: 1, PASS, 5/5 + 8/8; commit `29e55d1`,
pushed). The corrected-Case-not-literal-script scope call was judged defensible for its own
narrow claim but not a full delivery of T-080's stated goal given the pre-existing
`Script`/`Case.script_ref` schema surface — recorded as **AT-026** (medium, open) recommending a
follow-on unit for literal script generation, not re-opened against this PASS. **Correction:**
`.goal/goal.json` still showed T-080 `pending` after the checker's commit (its own return text
claimed "closed" but that never landed on disk — per the maker's own rule, disk state is
authoritative, not a chat summary). Closed it myself as the documented fallback (`goal_cli.py
done --task-id T-080`, idempotent, only run because the verdict is an unambiguous PASS) —
goal now 58%.
