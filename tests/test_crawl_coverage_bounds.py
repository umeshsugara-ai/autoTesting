"""The three findings of the cycle-1 checker on V7 coverage (AT-470, AT-471, AT-472).

Split from `test_crawl_coverage.py` (doctor's 300-line cap) along the verdict's own seam: that
file proves coverage is stated and balances; this one proves a bound is never hidden or misnamed
and that coverage can never cost a crawl its record. Verdict:
`qa/verdicts/at459-crawl-states-its-coverage.md` (cycle 1 FAIL).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import crawl_fake
import pytest
from crawl_fake import crawl_it
from test_crawl_coverage import _balanced, _compute, _edge, _node

from autotester.schema.crawl import CrawlBounds, CrawlCoverage
from autotester.schema.enums import CrawlStatus, EdgeOutcome, NodeStatus
from autotester.stages import crawl_coverage
from autotester.store.project_store import ProjectStore


def test_screens_a_depth_bound_kept_the_crawl_out_of_are_holes_and_cap_the_figure(
    tmp_path: Path,
) -> None:
    """AT-470, the checker's probe: max_depth=0 read "100% (1 of 1)", completed, 0 holes, while
    two screens a link led to were never entered and listed nowhere."""
    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_depth=0))
    cov = crawl.coverage

    assert cov is not None and cov.screens_not_entered, "the dropped screens must be listed"
    assert {h.reason for h in cov.screens_not_entered} == {"bound:max_depth"}


def test_a_depth_bound_alone_keeps_an_otherwise_full_crawl_below_100(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The checker's exact probe: ONE link, performed, whose screen is beyond max_depth=0. Every
    discovered control was exercised, so without the cap this reads "100% (1 of 1)" while a
    screen was never entered. Only the not-entered screen may pull it under 100 (V7d)."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        {"role": "link", "name": "Settings", "selector": "a.settings", "href": "/settings"},
    ])
    monkeypatch.setitem(crawl_fake.SITE, "https://app.test/settings", [
        {"role": "link", "name": "Profile", "selector": "a.profile", "href": "/profile"},
    ])

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_depth=0))
    cov = crawl.coverage

    assert cov is not None
    assert (cov.controls_exercised, cov.controls_discovered) == (1, 1), "the precondition"
    assert [h.reason for h in cov.screens_not_entered] == ["bound:max_depth"]
    assert cov.percent < 100, "a crawl a bound kept out of a screen can never read 100 (V7d)"


def test_a_screen_bound_names_the_controls_it_left_untried(tmp_path: Path) -> None:
    """max_screens is checked before EVERY action (`explore.stop_reason`), so once it is reached
    the crawl stops before following another link: the would-be screen is never navigated to,
    and the control that would have led there is an untried control named `bound:max_screens`.
    (Measured: `_enqueue`'s own max_screens drop is never reached by a real crawl.)"""
    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_screens=2))
    cov = crawl.coverage

    assert crawl.stop_reason == "max_screens"
    assert cov is not None and cov.by_reason().get("bound:max_screens", 0) >= 1
    assert cov.percent < 100
    assert _balanced(crawl)


def test_the_per_node_cap_on_an_earlier_screen_is_not_blamed_on_a_later_global_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-471, the checker's probe: per_node_action_cap=2, max_actions=3. The home screen spends
    its cap of 2 and leaves a third control untried; the global max_actions fires LATER, on the
    next screen. The home screen's untried control is the cap's, not max_actions'."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        {"role": "link", "name": f"Page {i}", "selector": f"a.p{i}", "href": f"/p{i}"}
        for i in (1, 2, 3)
    ])
    for i in (1, 2, 3):
        monkeypatch.setitem(crawl_fake.SITE, f"https://app.test/p{i}", [
            {"role": "link", "name": f"Leaf {i}{j}", "selector": f"a.l{i}{j}", "href": f"/l{i}{j}"}
            for j in (1, 2)
        ])

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(per_node_action_cap=2,
                                                                 max_actions=3))
    home = [h for h in crawl.coverage.holes if h.url_template == "/"]

    assert crawl.stop_reason == "max_actions"
    assert [h.reason for h in home] == ["bound:per_node_action_cap"], home


def test_a_login_wall_crawl_still_names_the_real_global_bound() -> None:
    """AT-471: `_terminal_status` rewrites stop_reason on a login wall; the bound that really
    fired is passed separately and must be the one named for a screen it cut short."""
    node = _node(NodeStatus.EXPLORED, "#a", "#b")
    edges = [_edge(node, "#a", EdgeOutcome.SAME_SCREEN)]

    cov = _compute(CrawlStatus.LOGIN_WALL, [node], edges, bound="max_actions",
                   bounds=CrawlBounds(per_node_action_cap=25))

    assert cov.by_reason() == {"bound:max_actions": 1}


def _runtime(**overrides: object) -> SimpleNamespace:
    """The few ExploreRuntime fields `of_run` and `explore.stop_reason` read."""
    fields: dict[str, object] = dict(
        session=SimpleNamespace(secrets=SimpleNamespace(scrub_optional=lambda s: s)),
        store=SimpleNamespace(load_flowspec=lambda: None, list_edges=lambda _id: []),
        bounds=CrawlBounds(max_actions=3), nodes={}, crawl=SimpleNamespace(id="c"),
        frontier=SimpleNamespace(screens_found=1, actions_used=3), clock=lambda: 0.0, started=0.0,
        stop_reason="stopped at a login wall: every screen reached only offers a form submit",
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)


def test_the_bound_named_comes_from_the_crawls_counters_not_the_rewritten_stop_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-471: on a LOGIN_WALL crawl `_terminal_status` has already replaced stop_reason with the
    wall's sentence by the time `_finish` runs. The bound that fired must still reach coverage."""
    seen: dict[str, object] = {}

    def capture(**kwargs: object) -> CrawlCoverage:
        seen.update(kwargs)
        return CrawlCoverage()

    monkeypatch.setattr(crawl_coverage, "compute_coverage", capture)
    crawl_coverage.of_run(_runtime(), CrawlStatus.LOGIN_WALL)

    assert seen["bound"] == "max_actions"


def test_a_failure_inside_coverage_is_recorded_never_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-472: coverage must never cost a crawl its own record — `_finish` saves after this."""
    def boom(**_kwargs: object) -> CrawlCoverage:
        raise RuntimeError("graph was unreadable")

    monkeypatch.setattr(crawl_coverage, "compute_coverage", boom)
    cov = crawl_coverage.of_run(_runtime(), CrawlStatus.COMPLETED)

    assert cov.error is not None and "graph was unreadable" in cov.error


def test_an_unreadable_flowspec_never_costs_the_crawl_its_record(tmp_path: Path) -> None:
    """AT-472: coverage reads flowspec.json at _finish; a hand-broken spec used to raise before
    save_crawl and leave crawl.json `running`. The cause is recorded and the crawl finishes."""
    project = crawl_fake.make_project()
    store = ProjectStore("demo", tmp_path)
    store.paths.dir.mkdir(parents=True, exist_ok=True)
    store.paths.flowspec.write_text("{ this is not json", encoding="utf-8")

    crawl, store, _page = crawl_it(tmp_path, project=project)
    saved = store.load_crawl(crawl.id)

    assert saved is not None and saved.status is not CrawlStatus.RUNNING
    assert saved.finished_at is not None
    assert saved.coverage is not None and saved.coverage.spec_error
    assert saved.coverage.controls_discovered > 0, "the rest of coverage is still computed"


# -- cycle 3: qa/verdicts/at459-crawl-states-its-coverage.md "## Cycle 2" (AT-476) --------

def _home_with_a_refusal_first(monkeypatch: pytest.MonkeyPatch, refused: dict) -> None:
    """A refused control BEFORE three links, on a screen whose cap (3) is never used up: the
    refusal is recorded but not tried, so max_actions=2 is the bound that cuts off `a.p3`."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [refused, *[
        {"role": "link", "name": f"Page {i}", "selector": f"a.p{i}", "href": f"/p{i}"}
        for i in (1, 2, 3)
    ]])
    for i in (1, 2, 3):
        monkeypatch.setitem(crawl_fake.SITE, f"https://app.test/p{i}", [])


def _p3_reason(tmp_path: Path) -> str:
    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(per_node_action_cap=3,
                                                                 max_actions=2))
    assert crawl.stop_reason == "max_actions", "the precondition"
    return next(h.reason for h in crawl.coverage.holes if h.selector == "a.p3")


def test_a_policy_refusal_is_not_counted_as_a_try_against_the_per_node_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-476: counting the refused 'Delete everything' as a try would make the screen look like
    it spent its cap (3) and blame the cap for a.p3, when max_actions ended the crawl."""
    _home_with_a_refusal_first(monkeypatch, {"role": "button", "name": "Delete everything",
                                             "selector": "#del"})

    assert _p3_reason(tmp_path) == "bound:max_actions"


def test_an_off_domain_link_refused_before_trying_is_not_counted_against_the_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-476: the same, for a link `_candidate_denial` refuses as off-domain before trying it."""
    _home_with_a_refusal_first(monkeypatch, {"role": "link", "name": "Elsewhere",
                                             "selector": "a.ext", "href": "https://evil.test/"})

    assert _p3_reason(tmp_path) == "bound:max_actions"


def test_a_coverage_that_could_not_be_computed_shows_no_percentage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Checker's cycle-2 note: with `coverage.error` set the tile read "0%" — a number for a
    measurement that never happened."""
    from fastapi.testclient import TestClient

    from autotester.schema.crawl import Crawl
    from autotester.schema.project import Project
    from autotester.ui.app import app

    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://x.test/",
                               allowed_domains=["x.test"]))
    store.save_crawl(Crawl(id="crawl_err", project="demo", status=CrawlStatus.COMPLETED,
                           coverage=CrawlCoverage(error="RuntimeError: boom")))

    text = TestClient(app).get("/projects/demo/crawls/crawl_err").text

    assert "<div class='value'>0%</div><div class='label'>Coverage</div>" not in text
    assert "<div class='value'>—</div><div class='label'>Coverage</div>" in text
    assert "could not be computed" in text
