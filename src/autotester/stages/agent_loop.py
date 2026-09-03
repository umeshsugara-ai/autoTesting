"""Agent fallback: when a case's steps break, ask the agent for a fix and retry.

Triggered only when `stages/execute.py::run_case` returns `ERRORED` — a script-
first run that fails partway through. The agent sees only the failing step,
the error, and the screenshot at that moment, never the rest of the case's
history (same evidence-only discipline as `grade.py`). A working fix is
folded back into the case as a corrected `Step` and persisted via
`ProjectStore.add_case` (content-addressed) — the next run replays the fixed
case through `run_case` alone, at zero agent cost, which is the "durable"
half of the fallback: durability comes from the corrected case being
deterministic to re-run, not from generating a literal script file (out of
scope here — see qa/contracts/agent-loop.md's no-fire list).
"""

from __future__ import annotations

from dataclasses import dataclass

from autotester.browser.session import BrowserSession
from autotester.core.paths import RepoDocs
from autotester.providers.base import Provider
from autotester.schema.case import AgentFix, Case
from autotester.schema.enums import EvidenceKind, Outcome
from autotester.schema.run import RawResult
from autotester.stages.execute import run_case

PROMPT_NAME = "agent_fix_v1.md"
MAX_ITERATIONS = 5


@dataclass
class AgentLoopResult:
    result: RawResult
    case: Case
    iterations: int
    fixed: bool


def _failing_step_order(case: Case, result: RawResult) -> int:
    """The first step that never got a post-step screenshot — see execute.py's
    "screenshot after every step that doesn't raise" contract (E2)."""
    completed = {e.step_order for e in result.evidence if e.kind is EvidenceKind.SCREENSHOT}
    remaining = sorted(s.order for s in case.steps if s.order not in completed)
    if not remaining:
        raise ValueError("run_case reported ERRORED but every step has a screenshot")
    return remaining[0]


def _last_screenshot(result: RawResult) -> str:
    shots = [e for e in result.evidence if e.kind is EvidenceKind.SCREENSHOT]
    return shots[-1].path if shots else "(none captured)"


def build_fix_prompt(case: Case, failing_order: int, error: str | None, result: RawResult,
                      docs: RepoDocs) -> str:
    template = (docs.prompts_dir / PROMPT_NAME).read_text(encoding="utf-8")
    failing_step = next(s for s in case.steps if s.order == failing_order)
    return (
        template.replace("{{TITLE}}", case.title)
        .replace("{{RATIONALE}}", case.rationale or "(none given)")
        .replace("{{FAILING_STEP}}", f"{failing_step.action.value} on '{failing_step.target}'")
        .replace("{{ERROR}}", error or "(no error message)")
        .replace("{{SCREENSHOT}}", _last_screenshot(result))
    )


def run_with_fallback(
    case: Case, session: BrowserSession, agent: Provider, docs: RepoDocs | None = None
) -> AgentLoopResult:
    """Run `case`; on ERRORED, ask `agent` to fix the failing step, up to `MAX_ITERATIONS`
    times. Returns the final result and the case as actually run (steps corrected in
    place on success) — the caller persists the corrected case via `ProjectStore.add_case`."""
    docs = docs or RepoDocs()
    working_case = case
    result = run_case(working_case, session)
    fixes_applied = 0
    while result.outcome is Outcome.ERRORED and fixes_applied < MAX_ITERATIONS:
        failing_order = _failing_step_order(working_case, result)
        prompt = build_fix_prompt(working_case, failing_order, result.error, result, docs)
        fix = agent.act(prompt, schema=AgentFix)
        working_case = working_case.with_fixed_step(failing_order, fix)
        fixes_applied += 1
        result = run_case(working_case, session)
    fixed = fixes_applied > 0 and result.outcome is not Outcome.ERRORED
    return AgentLoopResult(result, working_case, fixes_applied, fixed=fixed)
