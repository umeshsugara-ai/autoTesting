"""EXPAND stage. Contract: qa/contracts/expand.md X1-X5."""

from __future__ import annotations

import pytest

from autotester.providers.mock import MockProvider
from autotester.schema.case import ExpandedSteps
from autotester.schema.enums import Action, CaseClass, CaseKind
from autotester.schema.flowspec import Flow, FlowSpec, Step
from autotester.stages.expand import applicable_classes, expand, expand_flow
from autotester.stages.review import FlowSpecNotReviewed, approve

LOGIN_FLOW = Flow(
    id="flow_login", name="Login",
    entry_screen="scr_signin",
    steps=[
        Step(order=1, action=Action.NAVIGATE, target="https://app.test/signin"),
        Step(order=2, action=Action.FILL, target="email field", value="{{SECRET:USER_EMAIL}}"),
        Step(order=3, action=Action.FILL, target="password field",
             value="{{SECRET:USER_PASSWORD}}"),
        Step(order=4, action=Action.CLICK, target="Login button"),
    ],
)

NO_FILL_FLOW = Flow(
    id="flow_browse", name="Browse catalog",
    entry_screen="scr_home",
    steps=[
        Step(order=1, action=Action.NAVIGATE, target="https://app.test/catalog"),
        Step(order=2, action=Action.CLICK, target="First item"),
    ],
)


def approved_spec(flows: list[Flow]) -> FlowSpec:
    spec = FlowSpec(project="pathlynks", flows=flows)
    return approve(spec, by="umesh")


def not_applicable() -> ExpandedSteps:
    return ExpandedSteps(steps=[], rationale="does not apply to this flow")


def make_steps(target: str, value: str | None = None) -> ExpandedSteps:
    return ExpandedSteps(
        steps=[Step(order=1, action=Action.FILL, target=target, value=value)],
        rationale="a real edge case",
    )


# -- applicable_classes: deterministic, D-004 -------------------------------

def test_login_flow_gets_input_and_auth_classes() -> None:
    classes = applicable_classes(LOGIN_FLOW)
    assert CaseClass.INPUT_EMPTY in classes
    assert CaseClass.AUTH_WRONG_CREDS in classes
    assert CaseClass.HAPPY in classes


def test_no_fill_flow_skips_input_and_auth_classes() -> None:
    classes = applicable_classes(NO_FILL_FLOW)
    assert CaseClass.INPUT_EMPTY not in classes
    assert CaseClass.AUTH_WRONG_CREDS not in classes
    assert CaseClass.HAPPY in classes
    assert CaseClass.DOUBLE_SUBMIT in classes  # universal class, always asked


# -- expand_flow: at least 12 cases for the login flow (goal task's own bar) --

def test_login_flow_produces_at_least_twelve_cases() -> None:
    non_happy = [c for c in applicable_classes(LOGIN_FLOW) if c is not CaseClass.HAPPY]
    responses = [make_steps(f"field for {c.value}") for c in non_happy]
    provider = MockProvider(responses={"agent": responses})

    cases = expand_flow(LOGIN_FLOW, "pathlynks", provider)

    assert len(cases) >= 12
    assert any(c.case_class is CaseClass.HAPPY and c.kind is CaseKind.BEST for c in cases)


def test_happy_case_uses_the_flows_own_steps_verbatim() -> None:
    provider = MockProvider(responses={"agent": [not_applicable()] * 20})
    cases = expand_flow(LOGIN_FLOW, "pathlynks", provider)

    happy = next(c for c in cases if c.case_class is CaseClass.HAPPY)
    assert [s.target for s in happy.steps] == [s.target for s in LOGIN_FLOW.steps]


def test_model_declining_a_class_produces_no_case_for_it() -> None:
    non_happy = applicable_classes(LOGIN_FLOW)[1:]  # skip HAPPY
    responses = [not_applicable() for _ in non_happy]
    provider = MockProvider(responses={"agent": responses})

    cases = expand_flow(LOGIN_FLOW, "pathlynks", provider)

    assert len(cases) == 1  # only HAPPY survives
    assert cases[0].case_class is CaseClass.HAPPY


# -- expand(): requires an approved FlowSpec ----------------------------------

def test_expand_refuses_an_unreviewed_flowspec() -> None:
    spec = FlowSpec(project="pathlynks", flows=[LOGIN_FLOW])  # still DRAFT
    provider = MockProvider(responses={"agent": [not_applicable()] * 20})

    with pytest.raises(FlowSpecNotReviewed):
        expand(spec, provider)


def test_expand_runs_all_flows_once_approved() -> None:
    spec = approved_spec([LOGIN_FLOW, NO_FILL_FLOW])
    login_calls = len(applicable_classes(LOGIN_FLOW)) - 1
    browse_calls = len(applicable_classes(NO_FILL_FLOW)) - 1
    provider = MockProvider(responses={"agent": [not_applicable()] * (login_calls + browse_calls)})

    cases = expand(spec, provider)

    flow_ids = {c.flow_id for c in cases}
    assert flow_ids == {"flow_login", "flow_browse"}


# -- prompt is a file, per T-070's own contract's I5-equivalent --------------

def test_prompt_is_read_from_a_file() -> None:
    from autotester.core.paths import RepoDocs
    from autotester.stages.expand import build_expand_prompt

    prompt = build_expand_prompt(LOGIN_FLOW, CaseClass.INPUT_EMPTY, RepoDocs())
    assert "input_empty" in prompt
    assert "{{CASE_CLASS}}" not in prompt
    assert "Login" in prompt
