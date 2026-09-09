# HUMAN_GATE — wire the agent fallback in, or correct the doc that claims it

**Opened:** 2026-09-09 · **Blocks:** AT-253 (high)

## The question, in one line

Should `stages/agent_loop.py::run_with_fallback` be wired into the real execution path (every
broken case gets a real model call to repair it), or should `ARCHITECTURE.md` stop describing that
as the current execution model until it is?

## Why this is a gate and not a build task

`stages/agent_loop.py::run_with_fallback` is fully built and tested — `tests/test_agent_loop.py`
covers it — but has **zero production callers**. `docs/ARCHITECTURE.md:87-90` states as fact:
*"Per case: script-first... → agent fallback (provider act loop: write → run → read failure →
edit, capped iterations) → on success the agent emits a script. So a stable suite costs ~zero
tokens to re-run; the agent only pays for new or broken cases."* The second and third clauses
describe behaviour that cannot occur today — every broken case currently just fails, with no
repair attempt.

Unlike AT-239/240/242 (this session's earlier wiring fixes), closing this one for real changes
**runtime behaviour of the core execution loop**: every broken case in every run would start
making real model calls to attempt a repair, with real cost and real latency implications. That is
a product decision, not a mechanical connect-the-dots fix — the same reason AT-110 (the consent
tamper posture) was gated rather than picked unilaterally.

## Options

| | What it means |
|---|---|
| **A. Wire it in** | `stages/execute.py::run_case` (or `run_case_pipeline.py`) tries the durable script first; on failure, calls `run_with_fallback` to have an agent repair the step, capped at a bounded number of iterations, and persists the corrected script on success. Real model cost on every broken case, going forward. |
| **B. Correct the doc** | `ARCHITECTURE.md`'s Pipeline/Execution-model section stops describing agent fallback as the live path — states plainly it is built and tested but not yet wired, same honesty standard as the rest of this repo's own self-audits. Needs its own `docs/DECISIONS.md` entry (Lab Protocol: no `ARCHITECTURE.md` edit without one) authorizing the correction. |
| **C. Defer** | Leave both the code and the doc as they are; AT-253 stays open, tracked, not actioned this cycle. |

## How to answer

Say which option, or name a different scope for A (e.g. "wire it in behind a per-project cost cap"
or "wire it in for `regression-demo`/dev projects only, not live products yet"). If A, the next
unit becomes a real design-and-build cycle through `run_case_pipeline.py`; if B, the next unit is
a small, disclosed doc correction with its own D-entry.

## What is NOT blocked by this

Every other unit built this session — `AT-231/239/240/242/273/215/232` and their fixes — none of
them depend on this wiring existing.

**Answered:** _(pending)_
