"""The BFS-style companion to `routes_report.py`'s DFS per-run step flow:
one merged branch-tree per flow, built from every case's own steps.
Contract: qa/contracts/ui-flow-diagram.md FD1-FD4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from autotester.schema.case import Case
from autotester.schema.flowspec import Step
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404

router = APIRouter()

_KIND_TONE = {"best": "positive", "worst": "danger", "edge": "warning", "anchor": "neutral"}


@dataclass
class _Node:
    children: dict[str, _Node] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)


def _step_key(step: Step) -> str:
    label = f"{step.action.value}: {step.target}"
    return f"{label} = {step.value}" if step.value else label


def _insert(root: _Node, case: Case) -> None:
    """Merge `case` into the tree on its genuine common prefix — the same
    action+target(+value) at the same position collapses into one chain
    node; the first differing step becomes a real branch (FD1)."""
    node = root
    for step in case.steps:
        key = _step_key(step)
        if key not in node.children:
            node.children[key] = _Node()
            node.order.append(key)
        node = node.children[key]
    node.cases.append(case)


def _build_forest(cases: list[Case]) -> dict[str, _Node]:
    forest: dict[str, _Node] = {}
    for case in cases:
        forest.setdefault(case.flow_id, _Node())
    for case in cases:
        _insert(forest[case.flow_id], case)
    return forest


def _leaf_html(case: Case) -> str:
    kind = escape(case.kind.value)
    tone = _KIND_TONE.get(case.kind.value, "neutral")
    return (
        f"<span class='tree-node tree-leaf'>{theme.pill(kind, tone)} {escape(case.title)}</span>"
    )


def _node_html(key: str, node: _Node) -> str:
    label = f"<span class='tree-node'><span class='step-label'>{escape(key)}</span></span>"
    items = "".join(f"<li>{_leaf_html(c)}</li>" for c in node.cases)
    items += "".join(f"<li>{_node_html(k, node.children[k])}</li>" for k in node.order)
    return f"{label}<ul>{items}</ul>" if items else label


def _tree_html(root: _Node) -> str:
    items = "".join(f"<li>{_leaf_html(c)}</li>" for c in root.cases)
    items += "".join(f"<li>{_node_html(k, root.children[k])}</li>" for k in root.order)
    return f"<ul class='flow-tree'>{items}</ul>"


@router.get("/projects/{slug}/flow-diagram", response_class=HTMLResponse)
def flow_diagram(slug: str) -> str:
    store, _project = _load_project_or_404(slug)
    safe_slug = escape(slug)
    breadcrumb = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Flow diagram</div>"
    )
    cases = store.list_cases()
    if not cases:
        body = breadcrumb + "<h1>Flow diagram</h1>" + theme.empty_state(
            "🌳", "no cases yet — generate or add cases to see their branch structure here.",
        )
        return theme.page("Flow diagram", body)
    forest = _build_forest(cases)
    sections = "".join(
        theme.card(_tree_html(forest[flow_id]), title=f"Flow: {escape(flow_id)}")
        for flow_id in sorted(forest)
    )
    body = (
        breadcrumb + "<h1>Flow diagram</h1>"
        "<p class='subtitle'>Every case's own steps, merged on their shared prefix — where "
        "the branches actually diverge (best/worst/edge), not just a list of cases.</p>"
        f"{sections}"
    )
    return theme.page("Flow diagram", body)
