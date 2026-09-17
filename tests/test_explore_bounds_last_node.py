"""A bound that fires mid-screen on the LAST queued screen still names itself (X4, AT-463).

`_bfs` checks the bounds before each node, and `visit_node` checks them before each action. The
inner check only stopped acting: it never recorded which bound fired. On any screen but the last
the next loop-top check named it, so the gap hid. On the last queued screen the queue was empty,
`_bfs` wrote "frontier empty", and a crawl that ran out of actions read COMPLETED — the checker's
probe: one login-shaped page, max_actions=1, status completed, the submit never even evaluated.

The existing X4 tests all crawl the default fake site, where screens are still queued when a
bound fires, so they pass either way. These pin the single-screen case.
"""

from __future__ import annotations

from pathlib import Path

import crawl_fake
import pytest
from crawl_fake import crawl_it

from autotester.schema.crawl import CrawlBounds
from autotester.schema.enums import CrawlStatus

_THREE_BUTTONS = [
    {"role": "button", "name": f"Show panel {i}", "selector": f"#b{i}"} for i in (1, 2, 3)
]


@pytest.fixture
def one_screen(monkeypatch: pytest.MonkeyPatch) -> None:
    """One screen, three safe controls that do not navigate: nothing is ever queued after it."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, _THREE_BUTTONS)


def test_max_actions_firing_on_the_last_screen_names_itself(
    tmp_path: Path, one_screen: None,
) -> None:
    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_actions=2))

    assert crawl.actions == 2, "the precondition: the third control was cut off, not tried"
    assert crawl.stop_reason == "max_actions"
    assert crawl.status is CrawlStatus.STOPPED_BOUND


def test_wall_clock_firing_on_the_last_screen_names_itself(
    tmp_path: Path, one_screen: None,
) -> None:
    """The clock passes the limit after the first action, with the queue already empty."""
    readings = iter([0.0, 0.0, 0.0, 0.0] + [999.0] * 50)

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(wall_clock_s=10.0),
                                    clock=lambda: next(readings))

    assert crawl.actions < 3, "the precondition: the bound cut the screen short"
    assert crawl.stop_reason == "wall_clock_s"
    assert crawl.status is CrawlStatus.STOPPED_BOUND


def test_a_last_screen_that_finishes_inside_its_bounds_is_still_completed(
    tmp_path: Path, one_screen: None,
) -> None:
    """The guard must be able to say yes: all three controls tried, no bound reached."""
    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_actions=10))

    assert crawl.actions == 3
    assert crawl.stop_reason == "frontier empty"
    assert crawl.status is CrawlStatus.COMPLETED


def test_the_per_node_cap_is_not_a_crawl_bound(tmp_path: Path, one_screen: None) -> None:
    """The cap ends one SCREEN, not the crawl: a last screen cut short by its own cap is still a
    finished crawl (its untried control is named by V7 coverage as bound:per_node_action_cap)."""
    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(per_node_action_cap=2))

    assert crawl.actions == 2
    assert crawl.stop_reason == "frontier empty"
    assert crawl.status is CrawlStatus.COMPLETED
