"""AT-480/AT-489: a fired crawl bound must not silence itself under X18, and the fill-target
fallback must not misclassify a screen it never actually confirmed as the login screen.

Split out of `test_explore_login_wall.py` (at its 300-line cap) so both stay under it.

AT-480: when a bound (`max_actions`, `wall_clock_s`, `max_screens`) fires WHILE the crawl is
also stuck at a login wall or a failed login (X18), `terminal_status` used to replace
`stop_reason` with the wall/login-failed sentence outright, so X4's "the bound that fired is
named" silently stopped holding, and the wall sentence's "no link led anywhere else" claim was
asserted about links the bound left untried. The fix keeps the wall/login-failed STATUS (the
crawl is stuck either way) but appends the fired bound to the reason, and swaps in a
bound-honest wall sentence that drops the untried-links claim.

AT-489: the fill-target fallback (`_still_login`) used to fire on selector overlap alone. A
genuinely different post-login screen that happens to reuse every one of the login case's FILL
selectors (e.g. a dashboard with its own `#email` field) was misclassified LOGIN_FAILED. The fix
also requires the login case's own submit control -- the selector of its last CLICK step -- to
be present; a case with no CLICK step never fires the fallback at all.
"""

from __future__ import annotations

from pathlib import Path

import crawl_fake
import pytest
from crawl_fake import crawl_it, grant_crawl_approval, make_session

from autotester.schema.case import Case
from autotester.schema.crawl import CrawlBounds
from autotester.schema.enums import Action, CaseClass, CaseKind, CrawlStatus
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.schema.screen_graph import ElementRef, ScreenNode
from autotester.stages.explore import run_crawl
from autotester.stages.explore_status import terminal_status
from autotester.store.project_store import ProjectStore

SIGNIN = "https://app.test/signin"
_DENIED_SUBMIT = {"role": "button", "name": "Sign in", "selector": "#go", "is_form_submit": True}


def _self_link(name: str, selector: str, href: str = crawl_fake.BASE) -> dict:
    """A same-page link: following it revisits the SAME node, never discovering a new
    one -- lets a test spend real `actions_used` without the frontier ever growing."""
    return {"role": "link", "name": name, "selector": selector, "href": href}


# -- AT-480(b): no declared login case, a bound fires while still walled --------------------

def test_max_actions_firing_on_a_walled_page_names_the_bound(tmp_path: Path,
                                                              monkeypatch: pytest.MonkeyPatch,
                                                              ) -> None:
    """Checker's probe (AT-480 evidence): a walled page with a followable self-link that
    exceeds `max_actions` must still read `login_wall`, and `stop_reason` must name the
    bound -- not silently read as if every link had been tried."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        _DENIED_SUBMIT, _self_link("Refresh 1", "a.r1"), _self_link("Refresh 2", "a.r2"),
        _self_link("Refresh 3", "a.r3"),
    ])

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_actions=2))

    assert crawl.actions == 2, "the precondition: the third self-link was cut off, not tried"
    assert crawl.status is CrawlStatus.LOGIN_WALL
    assert crawl.stop_reason is not None
    assert "max_actions" in crawl.stop_reason
    assert "no link led anywhere else" not in crawl.stop_reason


def test_wall_clock_firing_on_a_walled_page_names_the_bound(tmp_path: Path,
                                                             monkeypatch: pytest.MonkeyPatch,
                                                             ) -> None:
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        _DENIED_SUBMIT, _self_link("Refresh 1", "a.r1"), _self_link("Refresh 2", "a.r2"),
        _self_link("Refresh 3", "a.r3"),
    ])
    readings = iter([0.0] * 5 + [999.0] * 50)

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(wall_clock_s=10.0),
                                    clock=lambda: next(readings))

    assert crawl.actions < 3, "the precondition: the bound cut the page short"
    assert crawl.status is CrawlStatus.LOGIN_WALL
    assert crawl.stop_reason is not None
    assert "wall_clock_s" in crawl.stop_reason
    assert "no link led anywhere else" not in crawl.stop_reason


def test_a_completed_walled_crawl_keeps_todays_sentence_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Control: the existing (b) behaviour -- a wall crawl that finishes because its
    frontier genuinely emptied -- must not gain a bound suffix and must keep the
    original "no link led anywhere else" sentence byte-for-byte."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [_DENIED_SUBMIT])

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_actions=200))

    assert crawl.stop_reason == (
        "stopped at a login wall: every screen reached only offers a form submit denied by "
        "read_only, and no link led anywhere else -- declare a login case to crawl past it"
    )


def test_max_screens_on_a_would_be_wall_correctly_stays_a_plain_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`max_screens` is structurally unable to fire while X18(b) still reads LOGIN_WALL:
    `_enqueue` only ever declines a node once `screens_found` already reached the cap, so the
    node whose OWN discovery pushed the count to the cap is always left `queued`, never
    `explored` -- with zero edges of its own it can never be counted `walled`. Verified live
    (not sabotage): a two-branch walled site with `max_screens=2` reads `stopped_bound`, never
    `login_wall`. Pinned here as the honest boundary of AT-480's fix, not a regression."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        _DENIED_SUBMIT, {"role": "link", "name": "A", "selector": "a.a",
                        "href": "https://app.test/p2"},
        {"role": "link", "name": "B", "selector": "a.b", "href": "https://app.test/p3"},
    ])
    monkeypatch.setitem(crawl_fake.SITE, "https://app.test/p2", [_DENIED_SUBMIT])
    monkeypatch.setitem(crawl_fake.SITE, "https://app.test/p3", [_DENIED_SUBMIT])

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(max_screens=2))

    assert crawl.status is CrawlStatus.STOPPED_BOUND
    assert crawl.stop_reason == "max_screens"


# -- AT-480(a): a declared login case, a bound fires while never past the login screen -------

def _login_case_with_click() -> Case:
    return Case(project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
                title="log in", steps=[
                    Step(order=1, action=Action.NAVIGATE, target=SIGNIN),
                    Step(order=2, action=Action.FILL, target="#email", value="someone"),
                    Step(order=3, action=Action.CLICK, target="#go")])


def _root_case_with_click() -> Case:
    """Same shape as `_login_case_with_click`, but rooted at `/` to match the `_node("/", ...)`
    fixtures the pure `terminal_status` tests below use (they never touch a real browser)."""
    return _login_case_with_click().model_copy(update={"steps": [
        Step(order=1, action=Action.NAVIGATE, target="https://app.test/"),
        Step(order=2, action=Action.FILL, target="#email", value="someone"),
        Step(order=3, action=Action.CLICK, target="#go")]})


def test_login_failed_bound_names_the_bound(tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """AT-480(a): a login case that never leaves the login page, cut short by a bound
    instead of naturally emptying its frontier -- LOGIN_FAILED still names the bound."""
    monkeypatch.setitem(crawl_fake.SITE, SIGNIN, [
        _DENIED_SUBMIT, _self_link("Forgot password", "a.forgot", href=SIGNIN),
        _self_link("Forgot password 2", "a.forgot2", href=SIGNIN),
    ])
    project = Project(slug="demo", name="Demo", base_url=SIGNIN, allowed_domains=["app.test"])
    session, page = make_session(tmp_path, project)
    page.fillable[SIGNIN] = {"#email"}
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project, CrawlBounds(max_actions=1))

    crawl = run_crawl(project, session, store, observer=crawl_fake.PageObserver(),
                      login_case=_login_case_with_click(), bounds=CrawlBounds(max_actions=1))

    assert crawl.actions == 1, "the precondition: the second self-link was cut off"
    assert crawl.status is CrawlStatus.LOGIN_FAILED
    assert crawl.stop_reason is not None
    assert "still the login page" in crawl.stop_reason
    assert "max_actions" in crawl.stop_reason


# -- AT-489: the fallback needs the login case's own submit control, too --------------------

def _node(template: str, signature: str, elements: list[ElementRef] | None = None) -> ScreenNode:
    return ScreenNode(crawl_id="c", project="demo", url_template=template,
                      url_example=f"https://app.test{template}", signature=signature,
                      depth=0, elements=elements or [])


def test_a_dashboard_with_a_matching_field_but_no_sign_in_button_is_not_login_failed() -> None:
    """AT-489 / ISS-x18a-1: a genuinely different screen that coincidentally exposes the
    login case's `#email` selector, but NOT its submit control, must stay COMPLETED."""
    dashboard = [ElementRef(role="textbox", name="Email", selector="#email")]
    status, _reason = terminal_status(
        completed=True, actions_used=3, denied=0, nodes=[_node("/", "sig_dash", dashboard)],
        edges=[], login_case=_root_case_with_click(), login_signature="sig_login")

    assert status is CrawlStatus.COMPLETED


def test_a_login_case_with_no_click_step_never_fires_the_fallback() -> None:
    """AT-489: with no CLICK step, `login_submit_selector` is None, so the fallback must
    stay off even when every FILL target is present -- signature-only decides."""
    case = Case(project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
               title="log in", steps=[
                   Step(order=1, action=Action.NAVIGATE, target="https://app.test/"),
                   Step(order=2, action=Action.FILL, target="#email", value="someone")])
    reused_fields = [ElementRef(role="textbox", name="Email", selector="#email")]
    status, _reason = terminal_status(
        completed=True, actions_used=3, denied=0,
        nodes=[_node("/", "sig_dash", reused_fields)], edges=[], login_case=case,
        login_signature="sig_login")

    assert status is CrawlStatus.COMPLETED


def test_a_screen_with_the_submit_control_and_every_fill_target_is_still_login_failed() -> None:
    """Control: the coincidental-match gap ISS-x18a-1 named is now closed -- reproducing
    every FILL target AND the submit control still (correctly) reads LOGIN_FAILED, because
    at that point the fallback is no longer distinguishable from a real repeated login
    screen by selector alone; a real product would not build a second screen this way."""
    banner = [ElementRef(role="textbox", name="Email", selector="#email"),
             ElementRef(role="button", name="Sign in", selector="#go", is_form_submit=True),
             ElementRef(role="status", name="Wrong username or password", selector="#err")]
    status, _reason = terminal_status(
        completed=True, actions_used=3, denied=0, nodes=[_node("/", "sig_banner", banner)],
        edges=[], login_case=_root_case_with_click(), login_signature="sig_login")

    assert status is CrawlStatus.LOGIN_FAILED
