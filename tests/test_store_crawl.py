"""Crawl artifact persistence through `ProjectStore` (Track B2). Every kind
round-trips as a plain JSON/JSONL file under `projects/<slug>/crawl/<id>/`
(C6) — no database.
"""

from __future__ import annotations

from pathlib import Path

from autotester.schema.crawl import Crawl, CrawlIssue
from autotester.schema.enums import Action, EdgeOutcome, IssueKind
from autotester.schema.screen_graph import CrawlFrontier, ScreenEdge, ScreenNode
from autotester.store.project_store import ProjectStore


def make_node(crawl_id: str = "crawl_1", url: str = "https://app.test/dashboard") -> ScreenNode:
    return ScreenNode(
        crawl_id=crawl_id, project="erp", url_template="/dashboard", url_example=url,
        signature="sig_abc",
    )


def test_save_and_load_crawl_roundtrips(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    crawl = Crawl(project="erp", screens=3, actions=10)

    store.save_crawl(crawl)
    loaded = store.load_crawl(crawl.id)

    assert loaded is not None
    assert loaded.screens == 3
    assert loaded.actions == 10


def test_list_crawl_ids_sorted_newest_first(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    c1 = Crawl(project="erp", id="crawl_01AAA")
    c2 = Crawl(project="erp", id="crawl_02BBB")
    store.save_crawl(c1)
    store.save_crawl(c2)

    assert store.list_crawl_ids() == ["crawl_02BBB", "crawl_01AAA"]


def test_list_crawl_ids_empty_when_no_crawls(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    assert store.list_crawl_ids() == []


def test_add_node_is_idempotent(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    node = make_node()

    store.add_node(node)
    store.add_node(node)

    assert len(store.list_nodes("crawl_1")) == 1


def test_add_node_scopes_idempotency_per_crawl(tmp_path: Path) -> None:
    """The same node id in two different crawls is not deduped across them."""
    store = ProjectStore("erp", tmp_path)
    node_a = make_node(crawl_id="crawl_a")
    node_b = make_node(crawl_id="crawl_b")

    store.add_node(node_a)
    store.add_node(node_b)

    assert len(store.list_nodes("crawl_a")) == 1
    assert len(store.list_nodes("crawl_b")) == 1


def test_add_edge_and_list_edges(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    edge = ScreenEdge(
        crawl_id="crawl_1", from_node="node_a", to_node="node_b",
        action=Action.CLICK, target="#save", outcome=EdgeOutcome.NAVIGATED,
    )
    store.add_edge(edge)

    edges = store.list_edges("crawl_1")
    assert len(edges) == 1
    assert edges[0].outcome is EdgeOutcome.NAVIGATED


def test_add_crawl_issue_and_list(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    issue = CrawlIssue(
        crawl_id="crawl_1", project="erp", kind=IssueKind.NETWORK,
        node_id="node_a", detail="404 on /api/missing",
    )
    store.add_crawl_issue(issue)

    issues = store.list_crawl_issues("crawl_1")
    assert len(issues) == 1
    assert issues[0].kind is IssueKind.NETWORK


def test_save_and_load_frontier(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    frontier = CrawlFrontier(queue=["node_b"], visited=["node_a"], actions_used=5, screens_found=2)

    store.save_frontier("crawl_1", frontier)
    loaded = store.load_frontier("crawl_1")

    assert loaded is not None
    assert loaded.queue == ["node_b"]
    assert loaded.actions_used == 5


def test_load_frontier_for_unknown_crawl_is_none(tmp_path: Path) -> None:
    store = ProjectStore("erp", tmp_path)
    assert store.load_frontier("crawl_missing") is None
