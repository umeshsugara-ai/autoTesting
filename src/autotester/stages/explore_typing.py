"""The X10-b typing pre-pass (D-029): what the crawler types, and where it
stops.

Split from `explore_node.py` for the 300-line cap. One job: fill every
eligible post-login form field with a deterministic synthetic value BEFORE the
click loop, so a submit the click phase performs sees a filled form. The gate
is `explore_safety.typing_allowed`; the values come from
`synthetic_values.py`; nothing here invents a rule those two do not already
state. Contract: qa/contracts/explore.md X10 (amended).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from autotester.browser.observe import observe
from autotester.schema.enums import Action, EdgeOutcome, IssueKind
from autotester.schema.screen_graph import ScreenEdge, ScreenNode
from autotester.stages import crawl_coverage
from autotester.stages.explore_node import _enqueue, add_issue, record_edge, return_to, why_lost
from autotester.stages.explore_safety import typing_allowed, typing_target_allowed
from autotester.stages.screen_identity import node_from
from autotester.stages.synthetic_values import synthetic_value

if TYPE_CHECKING:
    from autotester.stages.explore import ExploreRuntime


def _type_one(rt: ExploreRuntime, node: ScreenNode, el: object) -> ScreenEdge:
    """Type one synthetic value (X10-b). Returns the edge recorded."""
    action = Action.SELECT if el.role == "combobox" else Action.FILL  # type: ignore[attr-defined]
    if action is Action.SELECT:
        value = rt.session.first_option(el.selector)  # type: ignore[attr-defined]
        if not value:
            return record_edge(rt, node, el, action, EdgeOutcome.ERRORED,
                               "no selectable option found")
        rt.session.select_option(el.selector, value)  # type: ignore[attr-defined]
    else:
        value = synthetic_value(el.name, el.selector, el.role)  # type: ignore[attr-defined]
        rt.session.fill(el.selector, value)  # type: ignore[attr-defined]
    rt.session.settle(timeout_ms=rt.bounds.settle_ms)
    landed = rt.session.current_url()
    if urlparse(landed).path != urlparse(node.url_example).path:
        new = node_from(observe(rt.session), rt.crawl.id, rt.project.slug, node.depth + 1)
        if new.id != node.id and new.id not in rt.nodes:
            edge = record_edge(rt, node, el, action, EdgeOutcome.NAVIGATED, None, new.id)
            _enqueue(rt, new, edge)  # type: ignore[arg-type]
            return edge
        if new.id != node.id:
            return record_edge(rt, node, el, action, EdgeOutcome.NAVIGATED, None, new.id)
    return record_edge(rt, node, el, action, EdgeOutcome.SAME_SCREEN, None, node.id)


def type_form(rt: ExploreRuntime, node: ScreenNode) -> int:
    """X10-b's typing pre-pass (D-029): fill every eligible post-login form
    field with a deterministic synthetic value BEFORE the click loop, so a
    submit the click phase performs sees a filled form — the behaviour the
    human asked to observe ("usse hota kya hai").

    Gated by `typing_allowed` (the one boolean); each target re-checked by
    `typing_target_allowed` (never a password field, never an upload). Every
    typed action counts toward the per-node cap and `max_actions` (X4 bounds
    bind typing exactly as they bind clicks). Returns how many were typed.
    """
    if not typing_allowed(rt.policy):
        return 0
    typed = 0
    for el in node.elements:
        if rt.frontier.actions_used >= rt.bounds.max_actions:
            return typed
        if not crawl_coverage.is_candidate(el) or not typing_target_allowed(el):
            continue
        if not typing_allowed(rt.policy):  # re-check: the gate cannot be outlived
            return typed
        typed += 1
        rt.frontier.actions_used += 1
        try:
            _type_one(rt, node, el)
        except Exception as exc:
            record_edge(rt, node, el,
                        Action.SELECT if el.role == "combobox" else Action.FILL,
                        EdgeOutcome.ERRORED, f"{type(exc).__name__}: {exc}")
        if not return_to(rt, node):
            add_issue(rt, node.id, IssueKind.NAVIGATION,
                      "could not return to this screen after typing — remaining "
                      f"fields not typed: {why_lost(rt)}")
            return typed
    return typed