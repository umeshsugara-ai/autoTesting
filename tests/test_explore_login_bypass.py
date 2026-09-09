"""AT-226: an already-authenticated session must not abort the crawl.

A persistent Chromium profile can hold a live session from a prior run, in
which case the login page itself redirects away before the login case's own
form-fill step ever finds a field to fill. `_bootstrap_login` must notice the
redirect and skip the case rather than let `run_case` block on a field that
will never appear. Contract: qa/contracts/explore.md (login bootstrap, X10).
"""

from __future__ import annotations

from pathlib import Path

from crawl_fake import BASE, grant_crawl_approval, make_project, make_session

from autotester.browser.observe import PageObserver
from autotester.schema.case import Case
from autotester.schema.enums import Action, CaseClass, CaseKind, CrawlStatus
from autotester.schema.flowspec import Step
from autotester.stages.explore import run_crawl
from autotester.store.project_store import ProjectStore

SIGNIN = "https://app.test/signin"
IDENTIFIER = "input[name='identifier']"


def _login_case(target: str = SIGNIN) -> Case:
    """A NAVIGATE then a FILL, exactly the shape that timed out in AT-226's
    real crawl (`Locator.evaluate: Timeout ... input[name="identifier"]`)."""
    return Case(
        project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="log in", steps=[
            Step(order=1, action=Action.NAVIGATE, target=target),
            Step(order=2, action=Action.FILL, target=IDENTIFIER, value="someone"),
        ],
    )


def test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated(
    tmp_path: Path,
) -> None:
    project = make_project()
    session, page = make_session(tmp_path, project)
    page.redirects[SIGNIN] = BASE
    # The field only "exists" at /signin -- the page it redirects to (BASE)
    # never renders it, exactly like the real Pathlynks dashboard did not.
    page.fillable[SIGNIN] = {IDENTIFIER}
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)
    crawl = run_crawl(project, session, store, observer=PageObserver(), login_case=_login_case())
    assert crawl.status is CrawlStatus.COMPLETED
    assert crawl.stop_reason == "frontier empty"


def test_a_login_page_that_does_not_redirect_still_runs_the_case(tmp_path: Path) -> None:
    project = make_project()
    session, page = make_session(tmp_path, project)
    page.fillable[SIGNIN] = {IDENTIFIER}
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)
    crawl = run_crawl(project, session, store, observer=PageObserver(), login_case=_login_case())
    # No redirect was staged, so the login page genuinely held and the FILL
    # step succeeds there -- the case runs to completion as normal.
    assert crawl.status is CrawlStatus.COMPLETED
    assert crawl.stop_reason == "frontier empty"
    # AT-274: crawl.status/stop_reason alone cannot tell "the case genuinely
    # ran" apart from "the case was skipped by an always-skip regression" --
    # a checker sabotage (_already_past_login -> unconditional True) left
    # this test green with the login case never touched. Assert the FILL
    # step's own side effect happened, on the exact selector/value the case
    # names, so an always-skip mutation fails here.
    assert (IDENTIFIER, "someone") in page.fills


def test_a_login_case_with_no_navigate_step_falls_back_to_running_it(
    tmp_path: Path,
) -> None:
    project = make_project()
    session, _page = make_session(tmp_path, project)
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)
    case = Case(
        project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="log in", steps=[],
    )
    crawl = run_crawl(project, session, store, observer=PageObserver(), login_case=case)
    assert crawl.status is CrawlStatus.COMPLETED
