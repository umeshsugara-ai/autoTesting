"""Every swallowed cause in `stages/explore*.py` (AT-108 + AT-114 sweep).

These are not tests that the crawl survives a failure -- `test_explore_node_
recovery.py` already covers that. They test that when it survives, it can still
SAY WHAT HAPPENED. "The cause was swallowed" is a shape, not a location: the
same `except Exception:` with an empty body appeared at three sites, and a
crawl that loses a screen, cannot screenshot one, or cannot even get back to
the base URL used to report all three identically -- as nothing at all.

Contract: qa/contracts/explore.md X11/X16.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from crawl_fake import grant_crawl_approval, make_project, make_session

from autotester.browser.observe import PageObserver
from autotester.stages import explore_node
from autotester.stages.explore import run_crawl
from autotester.store.project_store import ProjectStore

# -- AT-114: a screenshot the crawler could not take ------------------------

def test_a_screenshot_failure_is_recorded_with_its_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`session.screenshot` retries the one transient CDP race AT-036
    documents and deliberately re-raises everything else because everything
    else is real. `capture`'s bare `except Exception: return None` threw that
    distinction away: a node with no screenshot looked the same whether the
    compositor hiccuped or the browser had died."""
    project = make_project()
    session, page = make_session(tmp_path, project)

    def dead_browser(path: str, full_page: bool = False) -> None:
        raise RuntimeError("Target page, context or browser has been closed")

    monkeypatch.setattr(page, "screenshot", dead_browser)
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)

    crawl = run_crawl(project, session, store, observer=PageObserver())

    issues = store.list_crawl_issues(crawl.id)
    shot_issues = [i for i in issues if i.kind.value == "evidence"]
    assert shot_issues, "a screenshot that never happened must leave a trace"
    assert any("browser has been closed" in i.detail for i in shot_issues)


def test_a_screenshot_failure_is_not_reported_as_a_product_bug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reason EVIDENCE is its own kind. Filing a failure of the TOOL as a
    navigation/console/network issue would inflate the product's issue count
    with the crawler's own problems -- the same dishonesty X9 forbids when it
    refuses to call third-party noise a product issue."""
    project = make_project()
    session, page = make_session(tmp_path, project)
    monkeypatch.setattr(
        page, "screenshot",
        lambda path, full_page=False: (_ for _ in ()).throw(RuntimeError("boom")))
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)

    crawl = run_crawl(project, session, store, observer=PageObserver())

    product_kinds = {"navigation", "console", "network", "dialog"}
    leaked = [i for i in store.list_crawl_issues(crawl.id)
              if i.kind.value in product_kinds and "screenshot" in i.detail]
    assert leaked == []


# -- AT-108: a screen the crawler could not get back to ---------------------

def test_a_lost_screen_reports_why_it_was_lost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`return_to` discarded its exception, so the issue it produced said only
    THAT the crawl lost a screen. On a live production crawl that is the
    difference between 'the app logged us out' and 'our own browser died'."""
    project = make_project()
    session, page = make_session(tmp_path, project)

    def broken_back(wait_until: str = "") -> None:
        raise RuntimeError("Navigation failed because page crashed")

    monkeypatch.setattr(page, "go_back", broken_back)
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)

    crawl = run_crawl(project, session, store, observer=PageObserver())

    issues = store.list_crawl_issues(crawl.id)
    assert any("page crashed" in i.detail for i in issues), (
        "the cause reached no artifact a human reads")


def test_a_failed_recovery_says_so_instead_of_passing_silently() -> None:
    """`_recover` is the last resort -- if it fails, every screen visited after
    it is suspect. It was the most serious failure in the file and the only one
    handled with a bare `pass`."""
    def dead(url: str, wait_until: str = "") -> None:
        raise RuntimeError("browser gone")

    rt = SimpleNamespace(
        session=SimpleNamespace(goto=dead, settle=lambda timeout_ms=0: None),
        project=SimpleNamespace(base_url="https://app.test/"),
        bounds=SimpleNamespace(settle_ms=10),
        return_error="back failed",
    )
    explore_node._recover(rt)  # type: ignore[arg-type]

    assert "browser gone" in (rt.return_error or "")
    assert "back failed" in (rt.return_error or ""), "the original cause was overwritten"
