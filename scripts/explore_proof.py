"""Credential-free end-to-end proof of the explorer (Track B3).

Serves the local fixture site, crawls it in a REAL browser under READ_ONLY,
and asserts the safety invariants that matter — the ones a fake page cannot
prove. Exits 0 only if every one holds, so a checker can verify the crawler
without an ERP account or any credential at all.

    uv run python scripts/explore_proof.py [--headed]

Mirrors scripts/regression_proof.py, which does the same job for the
regression suite.
"""

from __future__ import annotations

import functools
import http.server
import shutil
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotester.browser.observe import PageObserver
from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.schema.crawl import CrawlBounds
from autotester.schema.enums import EdgeOutcome, IssueKind
from autotester.schema.project import Project
from autotester.stages.explore import run_crawl
from autotester.store.project_store import ProjectStore

SITE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "crawl_site"
SENTINELS = ("deleted.html", "saved.html", "logged-out.html")


class _NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        return None


def start_server() -> tuple[http.server.ThreadingHTTPServer, str]:
    handler = functools.partial(_NoCacheHandler, directory=str(SITE_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def crawl(base_url: str, root: Path, *, headed: bool) -> tuple[object, ProjectStore]:
    project = Project(slug="crawl-demo", name="Crawl demo", base_url=base_url,
                      allowed_domains=["127.0.0.1"], headed=headed)
    paths = ProjectPaths("crawl-demo", root)
    paths.ensure()
    (root / ".env").write_text("", encoding="utf-8")
    store = ProjectStore("crawl-demo", root)
    store.save_project(project)
    observer = PageObserver()
    session = BrowserSession(project, SecretStore.load(project, root / ".env", strict=False),
                             root / "shots", paths, observer=observer)
    with session:
        result = run_crawl(project, session, store, observer=observer,
                           bounds=CrawlBounds(max_screens=12, max_actions=60,
                                              wall_clock_s=180.0, dialog_repeat_limit=2))
    return result, store


def checks(crawl_obj: object, store: ProjectStore) -> list[tuple[str, bool, str]]:
    crawl_id = crawl_obj.id  # type: ignore[attr-defined]
    nodes = store.list_nodes(crawl_id)
    edges = store.list_edges(crawl_id)
    issues = store.list_crawl_issues(crawl_id)
    templates = [n.url_template for n in nodes]
    examples = " ".join(n.url_example for n in nodes)
    denied = {e.name for e in edges if e.outcome is EdgeOutcome.DENIED_POLICY}
    details = " ".join(i.detail for i in issues)
    reached = [s for s in SENTINELS if s in examples]
    return [
        ("finished, did not hang", crawl_obj.finished_at is not None,  # type: ignore[attr-defined]
         f"stop_reason={crawl_obj.stop_reason}"),  # type: ignore[attr-defined]
        ("found at least 4 screens", len(nodes) >= 4, f"{len(nodes)} screens"),
        ("/students/{id} collapsed to one screen",
         templates.count("/students/{id}") == 1,
         f"count={templates.count('/students/{id}')}"),
        ("no sentinel page ever reached", not reached, f"reached={reached}"),
        ("destructive controls all denied",
         {"Delete account", "Deactivate", "Remove user", "Save", "Log out"} <= denied,
         f"denied={sorted(denied)}"),
        ("external link refused",
         any(e.outcome is EdgeOutcome.OFF_DOMAIN_REFUSED for e in edges)
         and "example.com" not in examples, "off-domain edge present"),
        ("first-party 404 reported", "/api/missing" in details, details[:120]),
        ("console error reported",
         any(i.kind is IssueKind.CONSOLE for i in issues), f"{len(issues)} issues"),
        ("analytics never reported as an issue", "google-analytics" not in details, "clean"),
        ("unnamed control skipped, not clicked",
         any(e.outcome is EdgeOutcome.SKIPPED_UNNAMED for e in edges), "skipped edge present"),
    ]


def main() -> int:
    headed = "--headed" in sys.argv
    server, base_url = start_server()
    root = Path(tempfile.mkdtemp(prefix="explore-proof-"))
    try:
        crawl_obj, store = crawl(base_url, root, headed=headed)
        results = checks(crawl_obj, store)
    finally:
        server.shutdown()
        server.server_close()
    failed = 0
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})")
        failed += 0 if ok else 1
    shutil.rmtree(root, ignore_errors=True)
    print(f"\n{len(results) - failed}/{len(results)} invariants held")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
