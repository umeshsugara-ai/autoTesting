"""The deterministic assertion layer (D-032/AT-540).

Split from `test_execute.py` at the 300-line cap. What it pins:
- a step whose declared expectation (url/visible_text/absent_text/dom_asserts)
  never holds makes `run_case` return `Outcome.ASSERTION_FAILED` — an
  observation, never a silent COMPLETED, and never a grade (C7: the grader
  still owns the verdict);
- each evaluated field records an explicit `assert <field>: met|unmet` DOM
  evidence item, so the grader has deterministic facts to weigh;
- a bare `Action.ASSERT` with nothing declared is harmless;
- an ERRORED mid-step exception still outranks an earlier unmet assertion.

Contract: qa/contracts/execute.md (E1 as amended by D-032, checker pending).
"""

from __future__ import annotations

from pathlib import Path

from test_execute import LOGIN, make_case, session_with_fake_page

from autotester.schema.enums import Action, EvidenceKind, Outcome
from autotester.schema.flowspec import Step
from autotester.stages.execute import run_case


def test_an_unmet_declared_expectation_is_assertion_failed_with_evidence(
    tmp_path: Path,
) -> None:
    """D-032/AT-540: a step whose expected.visible_text never appears is an
    ASSERTION_FAILED observation with the unmet assert recorded as DOM
    evidence — never a silent COMPLETED (the old `settle`-returns-either-way
    behaviour), and never a grade (the grader still owns the verdict)."""
    steps = [
        Step(order=1, action=Action.NAVIGATE, target=LOGIN),
        Step(order=2, action=Action.CLICK, target="button[type=submit]",
             expected={"visible_text": ["Dashboard"]}),
    ]
    session = session_with_fake_page(tmp_path)
    session.page.body_text = "Invalid credentials"  # the declared text never arrives

    result = run_case(make_case(steps), session)

    assert result.outcome is Outcome.ASSERTION_FAILED
    unmet = [e for e in result.evidence
             if e.kind is EvidenceKind.DOM and e.path.startswith("assert ")
             and "unmet" in e.path]
    assert unmet, "the unmet expectation was never recorded as evidence"
    assert "Dashboard" in unmet[0].path


def test_absent_text_and_dom_asserts_are_evaluated(tmp_path: Path) -> None:
    """`absent_text` must be met only when the text is truly absent;
    `dom_asserts` must be met only when the selector exists."""
    steps = [
        Step(order=1, action=Action.NAVIGATE, target=LOGIN),
        Step(order=2, action=Action.CLICK, target="button[type=submit]",
             expected={"absent_text": ["Invalid credentials"],
                       "dom_asserts": ["div.error-banner"]}),
    ]
    session = session_with_fake_page(tmp_path)
    session.page.body_text = "Invalid credentials"  # the absent_text IS present

    result = run_case(make_case(steps), session)
    assert result.outcome is Outcome.ASSERTION_FAILED
    assert any("absent_text: unmet" in e.path for e in result.evidence
               if e.kind is EvidenceKind.DOM)


def test_a_met_expectation_keeps_the_run_completed(tmp_path: Path) -> None:
    steps = [
        Step(order=1, action=Action.NAVIGATE, target=LOGIN + "/success",
             expected={"url": "/success", "visible_text": ["Welcome"]}),
    ]
    session = session_with_fake_page(tmp_path)
    session.page.body_text = "Welcome"

    result = run_case(make_case(steps), session)

    assert result.outcome is Outcome.COMPLETED
    met_asserts = [e for e in result.evidence
                   if e.kind is EvidenceKind.DOM and e.path.startswith("assert ")
                   and ": met" in e.path]
    assert len(met_asserts) == 2  # url + visible_text


def test_an_assert_step_with_no_expectation_is_harmless(tmp_path: Path) -> None:
    """A bare ASSERT (nothing declared) records no unmet evidence and does
    not fail the run — D-032's no-expected case."""
    steps = [Step(order=1, action=Action.ASSERT, target="")]
    session = session_with_fake_page(tmp_path)

    result = run_case(make_case(steps), session)

    assert result.outcome is Outcome.COMPLETED
    assert not [e for e in result.evidence if e.kind is EvidenceKind.DOM
                and "assert " in e.path]


def test_errored_still_beats_assertion_failed(tmp_path: Path) -> None:
    """A mid-step exception is still ERRORED even when an earlier step's
    assertion was unmet — the exception's own outcome wins (it explains why
    the rest of the case never ran)."""
    steps = [
        Step(order=1, action=Action.CLICK, target="button.broken",
             expected={"visible_text": ["Never checked"]}),
        Step(order=2, action=Action.CLICK, target="button.never-reached"),
    ]
    session = session_with_fake_page(tmp_path)

    result = run_case(make_case(steps), session)

    assert result.outcome is Outcome.ERRORED