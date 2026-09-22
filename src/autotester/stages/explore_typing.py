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
from autotester.browser.session import NavigationRefused, check_destination
from autotester.schema.enums import Action, EdgeOutcome, IssueKind
from autotester.schema.screen_graph import ScreenEdge, ScreenNode
from autotester.stages import crawl_coverage
from autotester.stages.explore_node import _enqueue, add_issue, record_edge
from autotester.stages.explore_return import return_to, why_lost
from autotester.stages.explore_safety import TYPING_DISABLED, typing_allowed, typing_target_allowed
from autotester.stages.screen_identity import node_from
from autotester.stages.synthetic_values import synthetic_value

if TYPE_CHECKING:
    from autotester.stages.explore import ExploreRuntime


def _type_one(rt: ExploreRuntime, node: ScreenNode, el: object) -> ScreenEdge:
    """Type one synthetic value (X10-b). Returns the edge recorded.

    AT-532 (X7): a typed action is a first-class crawl action, so the host is
    re-checked after it exactly as `try_action` re-checks after every click —
    a fill whose `onchange` auto-submits to another domain must never become an
    explored off-domain node."""
    action = Action.SELECT if el.role == "combobox" else Action.FILL  # type: ignore[attr-defined]
    try:
        if action is Action.SELECT:
            value = rt.session.first_option(el.selector)  # type: ignore[attr-defined]
            if not value:
                return record_edge(rt, node, el, action, EdgeOutcome.ERRORED,
                                   "no selectable option found")
            rt.session.select_option(el.selector, value)  # type: ignore[attr-defined]
        else:
            value = synthetic_value(el.name, el.selector, el.role)  # type: ignore[attr-defined]
            rt.session.fill(el.selector, value)  # type: ignore[attr-defined]
    except NavigationRefused as exc:
        return record_edge(rt, node, el, action, EdgeOutcome.OFF_DOMAIN_REFUSED, str(exc))
    except Exception as exc:
        return record_edge(rt, node, el, action, EdgeOutcome.ERRORED,
                           f"{type(exc).__name__}: {exc}")
    rt.session.settle(timeout_ms=rt.bounds.settle_ms)
    landed = rt.session.current_url()
    try:  # X7: the host is re-checked after EVERY action, typing included
        check_destination(rt.project, landed)
    except NavigationRefused as exc:
        add_issue(rt, node.id, IssueKind.NAVIGATION, str(exc))
        return record_edge(rt, node, el, action, EdgeOutcome.OFF_DOMAIN_REFUSED, str(exc))
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
    bind typing exactly as they bind clicks; AT-533: one shared budget with
    `visit_node`'s click loop, so the two passes together perform at most
    `per_node_action_cap` actions on this node).

    AT-534: when the gate refuses, each candidate typing target is recorded as
    `DENIED_POLICY` / `TYPING_DISABLED` (NOT silently clicked by the click
    loop — coverage then reads it as `policy:typing disabled`).

    Returns how many were typed."""
    if not typing_allowed(rt.policy):
        return _record_typing_denials(rt, node)
    typed = 0
    for el in node.elements:
        if rt.frontier.actions_used >= rt.bounds.max_actions:
            return typed
        # AT-533: the pre-pass itself consumes the per-node budget — typing
        # stops when THIS node's shared cap is reached, before the click loop.
        if typed >= rt.bounds.per_node_action_cap:
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


def _record_denial(rt: ExploreRuntime, node: ScreenNode, el: object) -> None:
    """AT-534: one skip the gate refused, as a first-class policy refusal."""
    action = Action.SELECT if el.role == "combobox" else Action.FILL  # type: ignore[attr-defined]
    record_edge(rt, node, el, action, EdgeOutcome.DENIED_POLICY, TYPING_DISABLED)
    rt.denied += 1


def _record_typing_denials(rt: ExploreRuntime, node: ScreenNode) -> int:
    """AT-534: typing refused by the gate — every eligible field is recorded as
    skipped (never silently CLICKED by the click loop and counted exercised)."""
    skipped = 0
    for el in node.elements:
        if (crawl_coverage.is_candidate(el) and typing_target_allowed(el)
                and el.role != "search"):  # search stays click-only (gate option (c))
            _record_denial(rt, node, el)
            skipped += 1
    return skipped