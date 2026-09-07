"""Crawl artifact persistence — split from `project_store.py` at the
300-line cap (C2). `ProjectStore` inherits `CrawlStoreMixin`, so its public
API is unchanged; this file exists purely to keep one file under the cap,
not as a second store (C3).
"""

from __future__ import annotations

from autotester.core.paths import ProjectPaths
from autotester.schema.crawl import Crawl, CrawlIssue
from autotester.schema.screen_graph import CrawlFrontier, ScreenEdge, ScreenNode
from autotester.store.filestore import append_jsonl, read_json, read_jsonl, write_json


class CrawlStoreMixin:
    """Requires `self.paths: ProjectPaths` and `self._node_ids: dict[str, set[str]] | None`
    from `ProjectStore.__init__` — mixed in there, never instantiated alone."""

    paths: ProjectPaths
    _node_ids: dict[str, set[str]] | None

    def save_crawl(self, crawl: Crawl) -> None:
        write_json(self.paths.crawl_manifest(crawl.id), crawl)

    def load_crawl(self, crawl_id: str) -> Crawl | None:
        return read_json(self.paths.crawl_manifest(crawl_id), Crawl)

    def list_crawl_ids(self) -> list[str]:
        if not self.paths.crawls_dir.exists():
            return []
        return sorted(
            (p.name for p in self.paths.crawls_dir.iterdir() if p.is_dir()), reverse=True
        )

    def add_node(self, node: ScreenNode) -> ScreenNode:
        """Idempotent on id within one crawl, same lazy-cache pattern as `add_case`."""
        if self._node_ids is None:
            self._node_ids = {}
        seen = self._node_ids.setdefault(
            node.crawl_id, {n.id for n in self.list_nodes(node.crawl_id)}
        )
        if node.id in seen:
            return node
        append_jsonl(self.paths.crawl_nodes(node.crawl_id), node)
        seen.add(node.id)
        return node

    def list_nodes(self, crawl_id: str) -> list[ScreenNode]:
        return read_jsonl(self.paths.crawl_nodes(crawl_id), ScreenNode)

    def add_edge(self, edge: ScreenEdge) -> None:
        append_jsonl(self.paths.crawl_edges(edge.crawl_id), edge)

    def list_edges(self, crawl_id: str) -> list[ScreenEdge]:
        return read_jsonl(self.paths.crawl_edges(crawl_id), ScreenEdge)

    def add_crawl_issue(self, issue: CrawlIssue) -> None:
        append_jsonl(self.paths.crawl_issues(issue.crawl_id), issue)

    def list_crawl_issues(self, crawl_id: str) -> list[CrawlIssue]:
        return read_jsonl(self.paths.crawl_issues(crawl_id), CrawlIssue)

    def save_frontier(self, crawl_id: str, frontier: CrawlFrontier) -> None:
        write_json(self.paths.crawl_frontier(crawl_id), frontier)

    def load_frontier(self, crawl_id: str) -> CrawlFrontier | None:
        return read_json(self.paths.crawl_frontier(crawl_id), CrawlFrontier)
