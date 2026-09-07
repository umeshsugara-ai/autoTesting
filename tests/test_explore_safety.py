"""`stages/explore_safety.py` — the D-016 write_policy matrix, the never-click
list, the link/request classifiers, and the dialog circuit breaker. Pure
logic, no browser. Contract: qa/contracts/explore.md X5-X9 (T-143).
"""

from __future__ import annotations

import pytest

from autotester.schema.crawl import DialogEvent
from autotester.schema.enums import WritePolicy
from autotester.schema.project import Project
from autotester.schema.screen_graph import ElementRef
from autotester.stages.explore_safety import (
    DialogBreaker,
    classify_request,
    deny_reason,
    link_is_safe,
    policy_for,
)


def make_project(write_policy: WritePolicy = WritePolicy.READ_ONLY) -> Project:
    return Project(
        slug="erp", name="ERP", base_url="https://www.vidysea.com/erp",
        allowed_domains=["vidysea.com", "www.vidysea.com"], write_policy=write_policy,
    )


def el(name: str, *, role: str = "button", is_form_submit: bool = False) -> ElementRef:
    return ElementRef(role=role, name=name, selector=f"#{name}", is_form_submit=is_form_submit)


CONTROLS = {
    "delete": el("Delete account"),
    "save_submit": el("Save", is_form_submit=True),
    "log_out": el("Log out"),
    "unnamed_button": el(""),
    "unnamed_link": el("", role="link"),
    "deliverables": el("Deliverables"),
    "send": el("Send"),
}


# -- the write_policy matrix (D-016), table-driven ---------------------------

@pytest.mark.parametrize("policy_kind,control,expect_denied", [
    (WritePolicy.READ_ONLY, "delete", True),
    (WritePolicy.READ_ONLY, "save_submit", True),
    (WritePolicy.READ_ONLY, "log_out", True),
    (WritePolicy.READ_ONLY, "deliverables", False),
    (WritePolicy.READ_ONLY, "send", True),
    (WritePolicy.TEST_ACCOUNT, "delete", True),
    (WritePolicy.TEST_ACCOUNT, "save_submit", False),
    (WritePolicy.TEST_ACCOUNT, "log_out", True),
    (WritePolicy.ALLOW_WRITES, "delete", False),
    (WritePolicy.ALLOW_WRITES, "save_submit", False),
    (WritePolicy.ALLOW_WRITES, "log_out", True),  # never-click applies at EVERY policy
])
def test_deny_matrix(policy_kind: WritePolicy, control: str, expect_denied: bool) -> None:
    policy = policy_for(make_project(policy_kind))
    reason = deny_reason(CONTROLS[control], policy)
    assert (reason is not None) is expect_denied


def test_deliverables_does_not_match_the_deliver_style_pattern() -> None:
    """Word-boundary matching: "Deliverables" must not match a "deliver"-ish
    fragment of any deny pattern."""
    policy = policy_for(make_project(WritePolicy.READ_ONLY))
    assert deny_reason(CONTROLS["deliverables"], policy) is None


def test_unnamed_non_link_control_is_denied_by_default() -> None:
    policy = policy_for(make_project(WritePolicy.ALLOW_WRITES))
    assert deny_reason(CONTROLS["unnamed_button"], policy) == "unnamed control"


def test_unnamed_link_is_not_denied_for_being_unnamed() -> None:
    """A link with no accessible name is still a link — safety for it is
    `link_is_safe`'s job (domain check), not the unnamed-control rule."""
    policy = policy_for(make_project(WritePolicy.READ_ONLY))
    assert deny_reason(CONTROLS["unnamed_link"], policy) is None


def test_click_unnamed_override_allows_an_unnamed_control() -> None:
    policy = policy_for(make_project(WritePolicy.ALLOW_WRITES), click_unnamed=True)
    assert deny_reason(CONTROLS["unnamed_button"], policy) is None


# -- link safety --------------------------------------------------------------

def test_same_domain_relative_link_is_safe() -> None:
    project = make_project()
    link = el("Students", role="link")
    link.href = "/erp/students"
    assert link_is_safe(link, project) is True


def test_external_link_is_not_safe() -> None:
    project = make_project()
    link = el("External", role="link")
    link.href = "https://example.com/"
    assert link_is_safe(link, project) is False


def test_javascript_and_mailto_links_are_never_safe() -> None:
    project = make_project()
    for href in ("javascript:void(0)", "mailto:x@y.com", "tel:+1234567890"):
        link = el("x", role="link")
        link.href = href
        assert link_is_safe(link, project) is False


def test_link_with_no_href_is_not_safe() -> None:
    project = make_project()
    assert link_is_safe(el("x", role="link"), project) is False


def test_protocol_relative_link_is_not_safe() -> None:
    project = make_project()
    link = el("x", role="link")
    link.href = "//evil.test/phish"
    assert link_is_safe(link, project) is False


# -- request classification (X9) ----------------------------------------------

def test_first_party_request_is_classified_first_party() -> None:
    project = make_project()
    policy = policy_for(project)
    assert classify_request("https://www.vidysea.com/erp/api/x", project, policy) == "first_party"


def test_known_analytics_host_is_ignored() -> None:
    project = make_project()
    policy = policy_for(project)
    assert classify_request(
        "https://www.google-analytics.com/collect", project, policy
    ) == "ignored"


def test_unknown_third_party_host_is_noise() -> None:
    project = make_project()
    policy = policy_for(project)
    assert classify_request("https://cdn.unknown-third.test/x", project, policy) == "noise"


def test_userinfo_spoofed_host_is_never_first_party() -> None:
    """AT-007-style host confusion: a backslash-userinfo trick must not be
    classified as first-party."""
    project = make_project()
    policy = policy_for(project)
    spoofed = "https://evil.test" + chr(92) + "@www.vidysea.com/x"
    assert classify_request(spoofed, project, policy) != "first_party"


# -- dialog circuit breaker ----------------------------------------------------

def test_breaker_trips_after_the_limit() -> None:
    breaker = DialogBreaker(limit=3)
    event = DialogEvent(dialog_type="confirm", message="are you sure?")
    tripped = [breaker.record("node_a", event) for _ in range(5)]
    assert tripped == [False, False, False, True, True]


def test_breaker_counts_per_node() -> None:
    breaker = DialogBreaker(limit=1)
    event = DialogEvent(dialog_type="alert")
    assert breaker.record("node_a", event) is False
    assert breaker.record("node_b", event) is False  # different node, own count
    assert breaker.record("node_a", event) is True


def test_breaker_reset_clears_the_count() -> None:
    breaker = DialogBreaker(limit=1)
    event = DialogEvent(dialog_type="alert")
    breaker.record("node_a", event)
    breaker.record("node_a", event)  # tripped
    breaker.reset("node_a")
    assert breaker.record("node_a", event) is False
