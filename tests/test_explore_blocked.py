"""`stages/explore.py`'s terminal-status distinction between a genuine
exhaustive crawl and a crawl that could act on nothing.

Contract: qa/contracts/explore.md X4/X16 (AT-242). Split out of
`test_explore.py` to keep that file under the 300-line cap — the fixture
(`crawl_fake.py`) is shared, not duplicated.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from crawl_fake import crawl_it, grant_crawl_approval, make_session

from autotester.browser.observe import PageObserver
from autotester.schema.crawl import SafetyPolicy
from autotester.schema.enums import CrawlStatus
from autotester.schema.project import Project
from autotester.stages.explore import run_crawl
from autotester.store.project_store import ProjectStore


def test_a_login_gate_with_every_action_denied_is_not_reported_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real repro: an entry screen with only an unnamed input and a
    read_only-refused submit button. The frontier genuinely empties (nothing
    is left to visit), but nothing was ever DONE -- reporting that as the same
    status word as an exhaustive crawl is indistinguishable from success."""
    import crawl_fake

    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        {"role": "textbox", "name": "", "selector": "#user"},
        {"role": "button", "name": "Login", "selector": "#login", "is_form_submit": True},
    ])
    crawl, _store, _page = crawl_it(tmp_path)

    assert crawl.actions == 0
    assert crawl.denied == 2  # skipped_unnamed + denied_policy
    assert crawl.status is CrawlStatus.BLOCKED_NO_ACTIONS
    assert crawl.stop_reason is not None and "denied" in crawl.stop_reason


def test_a_page_with_no_controls_at_all_still_reports_completed(tmp_path: Path) -> None:
    """The negative case this fix must not floor: a genuinely trivial page
    (nothing to click, nothing denied) is real, exhaustive coverage."""
    project = Project(slug="demo", name="Demo", base_url="https://app.test/deleted",
                      allowed_domains=["app.test"])
    session, _page = make_session(tmp_path, project)
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)
    crawl = run_crawl(project, session, store, observer=PageObserver(),
                      policy=SafetyPolicy(write_policy=project.write_policy))

    assert crawl.actions == 0
    assert crawl.denied == 0
    assert crawl.status is CrawlStatus.COMPLETED, (
        "a page with genuinely nothing to click must not be floored to blocked_no_actions"
    )
