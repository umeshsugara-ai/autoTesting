"""EXECUTE: run one case's steps in a real browser, producing a RawResult.

No judgement here — PASS/FAIL belongs to GRADE (T-041). This stage only performs
the case's steps on an already-started `BrowserSession` and records what
happened: a screenshot after every step, and one of three outcomes —
COMPLETED, ERRORED (an exception mid-step), or BLOCKED_HITL (a secret the
project does not have yet, the OTP/2FA case). Contract: qa/contracts/execute.md.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from autotester.browser.secrets import MissingSecret
from autotester.browser.session import BrowserSession
from autotester.schema.case import Case
from autotester.schema.enums import Action, Outcome
from autotester.schema.flowspec import Step
from autotester.schema.run import RawResult

_DEFAULT_WAIT_MS = 5000

StepHandler = Callable[[BrowserSession, Step], None]

_ACTIONS: dict[Action, StepHandler] = {
    Action.NAVIGATE: lambda session, step: session.goto(step.target),
    Action.CLICK: lambda session, step: session.click(step.target, step_order=step.order),
    Action.FILL: lambda session, step: session.fill(
        step.target, step.value, step_order=step.order
    ),
    Action.SELECT: lambda session, step: session.select_option(
        step.target, step.value, step_order=step.order
    ),
    Action.UPLOAD: lambda session, step: session.upload(
        step.target, step.value or "", step_order=step.order
    ),
    Action.WAIT: lambda session, step: session.wait_for(
        step.target or None,
        timeout_ms=int(step.value) if step.value else _DEFAULT_WAIT_MS,
        step_order=step.order,
    ),
    Action.ASSERT: lambda session, step: None,  # evidence only — see run_case's screenshot
}


def run_case(case: Case, session: BrowserSession) -> RawResult:
    """Execute `case.steps` in order on `session`. E1/E2/E3: observe, never judge."""
    start = time.monotonic()
    for step in sorted(case.steps, key=lambda s: s.order):
        try:
            _ACTIONS[step.action](session, step)
            if step.action is Action.CLICK:
                # AT-045: a click often triggers an async transition (e.g. a
                # form-submit redirect) -- settle before the evidence
                # screenshot, or the grader only ever sees the click itself,
                # never what it caused.
                session.settle()
            session.screenshot(f"step{step.order:02d}-{step.action}", step_order=step.order)
        except MissingSecret as exc:
            return _result(case, session, start, Outcome.BLOCKED_HITL, hitl_prompt=str(exc))
        except Exception as exc:  # the executor reports, it never crashes the run
            return _result(
                case, session, start, Outcome.ERRORED, error=f"{type(exc).__name__}: {exc}"
            )
    return _result(case, session, start, Outcome.COMPLETED)


def _result(
    case: Case,
    session: BrowserSession,
    start: float,
    outcome: Outcome,
    *,
    error: str | None = None,
    hitl_prompt: str | None = None,
) -> RawResult:
    return RawResult(
        case_id=case.id,
        outcome=outcome,
        duration_s=round(time.monotonic() - start, 3),
        error=error,
        hitl_prompt=hitl_prompt,
        evidence=list(session.state.evidence),
    )
