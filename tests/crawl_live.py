"""One real Chromium crawl of one local fixture site — the shared setup.

Not a test module (pytest does not collect it). T-165 needs several real-browser
crawls across three test files (`test_explore_traversal.py`,
`test_explore_completeness.py`), and each one is ~30 lines of project + paths +
secrets + approval + session boilerplate. One copy here rather than three, so
the files stay under the 300-line cap and there is one place that knows how a
live crawl is set up (C3).

Modelled on `test_explore_live.py`'s own module fixture, which stays as it is.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from autotester.browser.observe import PageObserver
from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.schema.approval import RunApproval
from autotester.schema.crawl import Crawl, CrawlBounds, SafetyPolicy
from autotester.schema.enums import ApprovalKind
from autotester.schema.project import Project
from autotester.stages.explore import run_crawl
from autotester.store.project_store import ProjectStore

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def make_live_project(slug: str, base_url: str, **overrides: Any) -> Project:
    return Project(slug=slug, name=slug, base_url=base_url + "/",
                   allowed_domains=["127.0.0.1"], headed=False, **overrides)


def grant(store: ProjectStore, project: Project, bounds: CrawlBounds) -> None:
    """A real signed approval — the D-018 gate is exercised, never bypassed.
    `production=False` is what lets an X10-b synthetic-typing run start at all
    (explore_consent, AT-535)."""
    store.add_approval(RunApproval(
        project=project.slug, run_kind=ApprovalKind.CRAWL, target=project.base_url,
        scope="local fixture crawl in the T-165 live tests", max_actions=bounds.max_actions,
        wall_clock_s=bounds.wall_clock_s, production=False, granted_by="test",
        granted_at="2026-09-27", expires_at="2099-01-01",
    ).sign())


def live_crawl(tmp_path: Path, base_url: str, *, slug: str, bounds: CrawlBounds,
               policy: SafetyPolicy | None = None, strategy: Any = None,
               incremental: bool = False,
               store: ProjectStore | None = None) -> tuple[Crawl, ProjectStore]:
    """Run ONE real crawl against `base_url` and return it with its store.

    `store` is accepted so a caller can crawl the same project twice into the
    same filestore — CR3's incremental skip and CR4's change tracking both need
    a second crawl that can read the first one's persona.
    """
    pytest.importorskip("playwright")
    project = make_live_project(slug, base_url)
    paths = ProjectPaths(slug, tmp_path)
    paths.ensure()
    env = tmp_path / ".env"
    if not env.exists():
        env.write_text("", encoding="utf-8")
    secrets = SecretStore.load(project, env, strict=False)
    store = store or ProjectStore(slug, tmp_path)
    grant(store, project, bounds)
    observer = PageObserver()
    session = BrowserSession(project, secrets, tmp_path / "shots", paths, observer=observer)
    try:
        session.start()
    except Exception as exc:  # browser binary missing on this machine
        pytest.skip(f"chromium unavailable: {type(exc).__name__}")
    kwargs: dict[str, Any] = {"observer": observer, "bounds": bounds, "policy": policy,
                              "incremental": incremental}
    if strategy is not None:
        kwargs["strategy"] = strategy
    try:
        crawl = run_crawl(project, session, store, **kwargs)
    finally:
        session.close()
    return crawl, store
