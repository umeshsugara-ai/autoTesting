"""A crawl that never gets past the login wall never reads as COMPLETED (X18, AT-458).

Umesh, 2026-09-16: "abhi tho hmara testing flow login k baad hi ruk jata hi". Every crawl on
disk had stopped on or before the login page, and three of them said `completed`. AT-242's
BLOCKED_NO_ACTIONS only caught the case where NOTHING was done; a login page with one
followable link that leads back still came out COMPLETED while the product behind the wall
was never seen. A stuck crawl that calls itself complete is the most expensive lie this tool
can tell, because nobody re-runs a crawl that says it finished.

Uses the scripted fake site (`crawl_fake.py`) like the other explorer unit tests; the real
browser version of "logged in, got past the wall" lives in `test_ui_crawl_login.py`.
"""

from __future__ import annotations

from pathlib import Path

import crawl_fake
import pytest
from crawl_fake import crawl_it, grant_crawl_approval, make_session

from autotester.browser.observe import PageObserver
from autotester.schema.case import Case
from autotester.schema.crawl import Crawl
from autotester.schema.enums import Action, CaseClass, CaseKind, CrawlStatus
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.schema.screen_graph import ScreenNode
from autotester.stages.explore import run_crawl
from autotester.stages.explore_status import displayed_status, terminal_status
from autotester.store.project_store import ProjectStore

SIGNIN = "https://app.test/signin"
DASHBOARD = "https://app.test/dashboard"
_LOGIN_FORM = [
    {"role": "textbox", "name": "Email", "selector": "#email"},
    {"role": "button", "name": "Sign in", "selector": "#go", "is_form_submit": True},
]


# -- (b) no declared login case --------------------------------------------------

def test_a_login_page_with_a_followable_link_back_is_not_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """X18's named verify: one same-domain link is followed (actions >= 1) and leads to a
    screen with the SAME structure — a login page reached another way. Before X18 this
    returned COMPLETED."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        *_LOGIN_FORM,
        {"role": "link", "name": "Sign in instead", "selector": "a.again", "href": "/login"},
    ])
    monkeypatch.setitem(crawl_fake.SITE, "https://app.test/login", [
        *_LOGIN_FORM,
        {"role": "link", "name": "Sign in instead", "selector": "a.again", "href": "/login"},
    ])

    crawl, _store, _page = crawl_it(tmp_path)

    assert crawl.actions >= 1, "the precondition: something WAS done"
    assert crawl.status is CrawlStatus.LOGIN_WALL
    assert crawl.stop_reason is not None and "login" in crawl.stop_reason.lower()


def test_a_public_page_with_a_sign_in_form_and_real_content_is_still_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The negative the wall rule must not floor: a home page with a sign-in box AND a link
    to a genuinely different screen is a public product that was really explored."""
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        *_LOGIN_FORM,
        {"role": "link", "name": "Pricing", "selector": "a.pricing", "href": "/pricing"},
    ])
    monkeypatch.setitem(crawl_fake.SITE, "https://app.test/pricing", [
        {"role": "link", "name": "Home", "selector": "a.home", "href": "/"},
    ])

    crawl, _store, _page = crawl_it(tmp_path)

    assert crawl.status is CrawlStatus.COMPLETED


def test_a_public_site_with_a_form_on_every_page_is_still_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A newsletter box on every page means every screen carries a refused submit — the
    wall's first condition holds. What makes it NOT a wall is that a link led to a
    structurally different screen. Without this test that half of the rule is untested
    (the maker's M3 sabotage survived until it existed)."""
    newsletter = {"role": "button", "name": "Subscribe", "selector": "#sub", "is_form_submit": True}
    monkeypatch.setitem(crawl_fake.SITE, crawl_fake.BASE, [
        newsletter,
        {"role": "link", "name": "Pricing", "selector": "a.pricing", "href": "/pricing"},
    ])
    monkeypatch.setitem(crawl_fake.SITE, "https://app.test/pricing", [
        newsletter,
        {"role": "link", "name": "Home", "selector": "a.home", "href": "/"},
        {"role": "link", "name": "Annual plans", "selector": "a.annual", "href": "/pricing"},
    ])

    crawl, _store, _page = crawl_it(tmp_path)

    assert crawl.status is CrawlStatus.COMPLETED


# -- (a) a declared login case that never got past the login page -----------------

def _login_case() -> Case:
    return Case(project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
                title="log in", steps=[
                    Step(order=1, action=Action.NAVIGATE, target=SIGNIN),
                    Step(order=2, action=Action.FILL, target="#email", value="someone"),
                ])


def _crawl_with_login(tmp_path: Path, *, stays_on_signin: bool) -> Crawl:
    project = Project(slug="demo", name="Demo", base_url=DASHBOARD, allowed_domains=["app.test"])
    session, page = make_session(tmp_path, project)
    page.fillable[SIGNIN] = {"#email"}
    if stays_on_signin:  # the credentials were wrong: the product keeps sending you back
        page.redirects[DASHBOARD] = SIGNIN
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)
    return run_crawl(project, session, store, observer=PageObserver(), login_case=_login_case())


def test_a_login_case_that_never_leaves_the_login_page_is_login_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The login CASE completed (every step ran) but the product kept redirecting to the
    sign-in page: every screen reached is the login page. That is a failed login, not a crawl."""
    monkeypatch.setitem(crawl_fake.SITE, SIGNIN, [
        *_LOGIN_FORM,
        {"role": "link", "name": "Forgot password", "selector": "a.forgot", "href": "/signin"},
    ])

    crawl = _crawl_with_login(tmp_path, stays_on_signin=True)

    assert crawl.status is CrawlStatus.LOGIN_FAILED
    assert crawl.stop_reason is not None and "login page" in crawl.stop_reason


def test_a_login_case_that_gets_past_the_login_page_is_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(crawl_fake.SITE, SIGNIN, _LOGIN_FORM)
    monkeypatch.setitem(crawl_fake.SITE, DASHBOARD, [
        {"role": "link", "name": "Reports", "selector": "a.r", "href": "/dashboard"},
    ])

    crawl = _crawl_with_login(tmp_path, stays_on_signin=False)

    assert crawl.status is CrawlStatus.COMPLETED


def _node(template: str, signature: str, depth: int = 0) -> ScreenNode:
    return ScreenNode(crawl_id="c", project="demo", url_template=template,
                      url_example=f"https://app.test{template}", signature=signature, depth=depth)


def _root_login_case() -> Case:
    return _login_case().model_copy(update={"steps": [
        Step(order=1, action=Action.NAVIGATE, target="https://app.test/"),
        Step(order=2, action=Action.FILL, target="#email", value="someone"),
    ]})


def _judge(nodes: list[ScreenNode], case: Case, login_signature: str | None) -> CrawlStatus:
    status, _reason = terminal_status(completed=True, actions_used=3, denied=0, nodes=nodes,
                                      edges=[], login_case=case, login_signature=login_signature)
    return status


def test_a_single_page_app_whose_one_dashboard_state_shares_the_login_url_is_not_login_failed(
) -> None:
    """AT-462 cycle 2 (checker, reproduced LIVE): the login form and a dashboard that is ONE
    structural state share one url template. One node, one signature — counting signatures
    called it failed. It is a different screen from the login screen OBSERVED before typing."""
    assert _judge([_node("/", "sig_dashboard")], _root_login_case(),
                  login_signature="sig_login") is CrawlStatus.COMPLETED


def test_a_single_page_app_with_two_post_login_states_is_not_login_failed() -> None:
    """AT-462 cycle 1: two different signatures at the login url are two screens (X3)."""
    nodes = [_node("/", "sig_login"), _node("/", "sig_dashboard", depth=1)]
    assert _judge(nodes, _root_login_case(), login_signature="sig_login") is CrawlStatus.COMPLETED


def test_every_screen_being_the_observed_login_screen_is_login_failed() -> None:
    """The positive the comparison must still reach: every node is exactly the observed login
    screen (its template AND its signature)."""
    assert _judge([_node("/", "sig_login")], _root_login_case(),
                  login_signature="sig_login") is CrawlStatus.LOGIN_FAILED


def test_an_unobserved_login_screen_is_never_judged_failed() -> None:
    """No observed signature (the login page redirected away, or could not be observed): (a)
    cannot be judged, and a guess would be exactly the false failure AT-462 is about."""
    assert _judge([_node("/", "sig_login")], _root_login_case(),
                  login_signature=None) is CrawlStatus.COMPLETED


def test_a_placeholder_login_url_is_never_compared_as_the_root_page() -> None:
    """AT-462: a `{{SECRET:KEY}}` target resolves only at fill time; templated raw it is "/",
    so any product whose screens live at "/" would read as a failed login."""
    case = _login_case().model_copy(update={"steps": [
        Step(order=1, action=Action.NAVIGATE, target="{{SECRET:DEMO_LOGIN_URL}}"),
    ]})

    assert _judge([_node("/", "sig_home")], case, login_signature="sig_home") \
        is CrawlStatus.COMPLETED


# -- (d) legacy artifacts ---------------------------------------------------------

def test_a_legacy_completed_crawl_that_did_nothing_is_not_displayed_as_success() -> None:
    """The three on-disk crawls: persisted `completed`, 0 actions, 3 denied (they predate
    AT-242). The file is history and stays as written; what a human is SHOWN must not be
    success."""
    legacy = Crawl(project="demo", status=CrawlStatus.COMPLETED, actions=0, denied=3,
                   stop_reason="frontier empty")

    assert displayed_status(legacy) is not CrawlStatus.COMPLETED


def test_a_real_completed_crawl_is_displayed_as_completed() -> None:
    real = Crawl(project="demo", status=CrawlStatus.COMPLETED, actions=6, denied=1,
                 stop_reason="frontier empty")

    assert displayed_status(real) is CrawlStatus.COMPLETED
