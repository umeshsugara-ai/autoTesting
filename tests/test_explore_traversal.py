"""CR1/CR6 — the ORDER the frontier is walked in, against real pages.

Contract: qa/contracts/crawl-traversal.md. `explore.md` X1-X18 are unamended and
untouched here; every criterion below is about which queued screen is visited
next (CR1) and about that choice being a pure, reproducible function of
frontier state (CR6).

CR2/CR7 — replaying an action the crawl already performed — lives in
`test_explore_replay.py`, split out at the 300-line C2 cap.

The CR1 proof is a REAL Chromium crawl of a local fixture site, not a fake:
traversal order is about what a browser actually does, and this repo has a
filed history (AT-243) of fixture-only "proof".
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from crawl_live import FIXTURES, live_crawl

from autotester.schema.crawl import Crawl, CrawlBounds
from autotester.schema.enums import Action, TraversalStrategy
from autotester.schema.screen_graph import ScreenEdge, ScreenNode
from autotester.stages import explore_traversal
from autotester.store.project_store import ProjectStore

DEEP_SITE = FIXTURES / "deep_site"

# The budget is the whole point of CR1: `/` costs 5 actions, each branch page
# costs 3, each workflow step costs 1. Breadth-first spends 5 + 1 + 3 + 3 = 12
# before it even pops the second workflow step; a bounded depth-first descent
# reaches the fourth step at action 8.
DEEP_BOUNDS = CrawlBounds(max_screens=20, max_actions=10, wall_clock_s=120.0,
                          dialog_repeat_limit=2)


def _templates(store: ProjectStore, crawl: Crawl) -> set[str]:
    return {n.url_template for n in store.list_nodes(crawl.id)}


@pytest.fixture(scope="module")
def deep_crawls(
    tmp_path_factory: pytest.TempPathFactory, serve_dir: Callable[[Path], str]
) -> dict[str, tuple[Crawl, ProjectStore]]:
    """ONE bfs crawl and ONE hybrid crawl of the same site under the SAME budget.
    Module-scoped: two real browser crawls, many assertions about them."""
    base = serve_dir(DEEP_SITE)
    out = {}
    for name, strategy in (("bfs", TraversalStrategy.BFS), ("hybrid", TraversalStrategy.HYBRID)):
        out[name] = live_crawl(tmp_path_factory.mktemp(f"deep-{name}"), base,
                               slug=f"deep-{name}", bounds=DEEP_BOUNDS, strategy=strategy)
    return out


# --- CR1: hybrid reaches depth a same-budget BFS does not -------------------


def test_hybrid_reaches_the_deep_workflow_that_bfs_under_the_same_budget_does_not(
    deep_crawls: dict[str, tuple[Crawl, ScreenNode]],
) -> None:
    """CR1's falsifiable, verbatim: on a fixture site with a workflow N screens
    deep behind a branch BFS would ordinarily defer, a `hybrid` crawl under a
    fixed action budget reaches a depth-N screen that a `bfs` crawl under the
    SAME budget does not."""
    bfs_crawl, bfs_store = deep_crawls["bfs"]
    hyb_crawl, hyb_store = deep_crawls["hybrid"]
    assert bfs_crawl.bounds.max_actions == hyb_crawl.bounds.max_actions
    assert "/deep4.html" in _templates(hyb_store, hyb_crawl)
    assert "/deep4.html" not in _templates(bfs_store, bfs_crawl)


def test_hybrid_still_maps_breadth_first_and_does_not_revive_d023(
    deep_crawls: dict[str, tuple[Crawl, ScreenNode]],
) -> None:
    """CR1: `hybrid` is NOT D-023's rejected single happy-path DFS. Every branch
    the seed screen links to is still DISCOVERED and enqueued breadth-first —
    what changes is only the order they come off the queue in. A single
    depth-first line through the portal would never have enqueued the branches."""
    crawl, store = deep_crawls["hybrid"]
    found = _templates(store, crawl)
    assert {f"/wide{n}.html" for n in (1, 2, 3, 4)} <= found


def test_hybrid_invents_no_new_bound(deep_crawls: dict[str, tuple[Crawl, ScreenNode]]) -> None:
    """CR1: `hybrid` is governed by the same X4 bounds, unchanged — so when it
    stops, it stops on one of THEM, named (X4), and never on a bound of its own."""
    crawl, _ = deep_crawls["hybrid"]
    assert crawl.stop_reason in {"max_screens", "max_actions", "wall_clock_s"} or \
        crawl.stop_reason.startswith("frontier empty")


# --- CR6: pure function of frontier state, no provider ----------------------


def _node(node_id: str, depth: int) -> ScreenNode:
    return ScreenNode(id=node_id, crawl_id="c", project="p", url_template=f"/{node_id}",
                      url_example=f"/{node_id}", signature=node_id, depth=depth)


def _edge(from_node: str, to_node: str) -> ScreenEdge:
    return ScreenEdge(crawl_id="c", from_node=from_node, to_node=to_node,
                      action=Action.CLICK, target=f"#{to_node}", outcome="navigated")


def _graph() -> tuple[dict[str, ScreenNode], dict[str, ScreenEdge]]:
    nodes = {"a": _node("a", 0), "b": _node("b", 1), "c": _node("c", 1), "d": _node("d", 2)}
    discovery = {"b": _edge("a", "b"), "c": _edge("a", "c"), "d": _edge("b", "d")}
    return nodes, discovery


def test_bfs_ordering_is_byte_identical_to_the_original_fifo_pop() -> None:
    """CR1: `bfs` is byte-identical to today's FIFO `.pop(0)` behaviour."""
    nodes, discovery = _graph()
    queue = ["b", "c", "d"]
    taken = [explore_traversal.next_node_id(queue=queue, nodes=nodes, discovery=discovery,
                                            strategy=TraversalStrategy.BFS, last_visited="a")
             for _ in range(3)]
    assert taken == ["b", "c", "d"]
    assert queue == []


def test_hybrid_descends_into_the_workflow_just_entered_then_backtracks() -> None:
    """CR1: having just visited `b`, the descent takes `b`'s own child `d`
    before returning to breadth order for `c`."""
    nodes, discovery = _graph()
    queue = ["c", "d"]
    first = explore_traversal.next_node_id(queue=queue, nodes=nodes, discovery=discovery,
                                           strategy=TraversalStrategy.HYBRID, last_visited="b")
    second = explore_traversal.next_node_id(queue=queue, nodes=nodes, discovery=discovery,
                                            strategy=TraversalStrategy.HYBRID, last_visited="d")
    assert (first, second) == ("d", "c")


def test_every_strategy_removes_exactly_one_id_per_call_so_a_crawl_terminates() -> None:
    """X4 (`explore.md`, unamended): a crawl must ALWAYS terminate. `hybrid`
    inherits that only because it never re-adds to the queue — pinned here
    rather than argued in a docstring."""
    nodes, discovery = _graph()
    for strategy in TraversalStrategy:
        queue = ["b", "c", "d"]
        for expected in (2, 1, 0):
            explore_traversal.next_node_id(queue=queue, nodes=nodes, discovery=discovery,
                                           strategy=strategy, last_visited="b")
            assert len(queue) == expected
        assert explore_traversal.next_node_id(queue=queue, nodes=nodes, discovery=discovery,
                                              strategy=strategy, last_visited="b") is None


def test_hybrid_ordering_is_deterministic_across_repeated_runs() -> None:
    """CR6: the decision is a pure function of frontier state — no provider, no
    clock, no randomness. Two identical frontiers order identically."""
    runs = []
    for _ in range(5):
        nodes, discovery = _graph()
        queue = ["b", "c", "d"]
        runs.append([explore_traversal.next_node_id(
            queue=queue, nodes=nodes, discovery=discovery,
            strategy=TraversalStrategy.HYBRID, last_visited="a") for _ in range(3)])
    assert len({tuple(r) for r in runs}) == 1


def test_no_provider_or_vendor_sdk_reaches_the_traversal_modules() -> None:
    """CR6's falsifiable: `grep` for a Provider/vendor-SDK import in the modules
    this unit adds returns nothing (core-invariants C8)."""
    root = Path(__file__).resolve().parents[1] / "src" / "autotester" / "stages"
    banned = ("providers", "openai", "anthropic", "litellm", "Provider")
    for name in ("explore_traversal", "explore_incremental", "explore_replay",
                 "persona_changes"):
        text = (root / f"{name}.py").read_text(encoding="utf-8")
        imports = [ln for ln in text.splitlines()
                   if ln.startswith(("import ", "from ")) and any(b in ln for b in banned)]
        assert imports == [], f"{name}.py imports a provider: {imports}"
