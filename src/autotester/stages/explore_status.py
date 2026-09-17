"""How a finished crawl is judged, and how a stored one is shown (X16, X18).

A crawl that never gets past the login wall must never read as COMPLETED. Umesh,
2026-09-16: "abhi tho hmara testing flow login k baad hi ruk jata hi" — every crawl on
disk had stopped at or before the login page, and three said `completed`. AT-242's
BLOCKED_NO_ACTIONS caught only the crawl that did NOTHING; a sign-in page with one
link that leads back still came out COMPLETED while the product behind it was never
seen. Nobody re-runs a crawl that says it finished, so this is the lie that costs most.

Split out of `stages/explore.py`, which sat at the 300-line cap (AT-460): the terminal
status is a judgement about a finished graph, not part of walking it.
"""

from __future__ import annotations

from collections.abc import Iterable

from autotester.browser.observe import observe
from autotester.core.redact import PLACEHOLDER_RE
from autotester.core.urls import absolute_url, url_template
from autotester.schema.case import Case
from autotester.schema.crawl import Crawl
from autotester.schema.enums import Action, CrawlStatus, EdgeOutcome
from autotester.schema.screen_graph import ScreenEdge, ScreenNode
from autotester.stages.explore_safety import FORM_SUBMIT_REFUSED
from autotester.stages.screen_identity import structural_signature

NEVER_LEFT_LOGIN = (
    "the login case ran, but every screen reached was still the login page ({template}) -- "
    "check the login case's steps and the credentials it uses"
)
LOGIN_WALL_REASON = (
    "stopped at a login wall: every screen reached only offers a form submit denied by "
    "read_only, and no link led anywhere else -- declare a login case to crawl past it"
)


def login_template(case: Case) -> str | None:
    """The url template of the login case's own start screen, templated exactly as a
    crawled node is (so the two can be compared), or None when it cannot be known here:
    no NAVIGATE step, or a `{{SECRET:KEY}}` target that only resolves at fill time
    (templating the raw placeholder gives "/", which matches the wrong screens — AT-462)."""
    step = next((s for s in sorted(case.steps, key=lambda s: s.order)
                 if s.action is Action.NAVIGATE), None)
    if step is None or PLACEHOLDER_RE.search(step.target):
        return None
    return url_template(absolute_url(step.target), keep_host=False)


def observed_signature(session: object) -> str | None:
    """The structural signature of the page the session shows now, computed exactly as a
    crawled node's is — or None if it cannot be observed, in which case X18(a) is simply
    not judged (never a crash, never a guessed failure)."""
    try:
        return structural_signature(observe(session).elements)
    except Exception:
        return None


def never_left_login(nodes: Iterable[ScreenNode], case: Case | None,
                     login_signature: str | None) -> str | None:
    """X18(a): with a declared login case, the reason every node IS the login screen.

    A screen is (url_template, signature) — X3 — and the login screen's signature is the one
    OBSERVED on the login page before the case typed anything (`login_signature`). Comparing
    the template alone called a working single-page-app login failed (AT-462, cycle 1); so did
    merely counting signatures, when the dashboard behind the login is a single state at the
    same url (AT-462, cycle 2). Unknown signature (the login page redirected away, or could
    not be observed) means this cannot be judged here, and it is not."""
    reached = list(nodes)
    template = login_template(case) if case is not None else None
    if template is None or not reached:
        return None
    # An unobserved (None) login signature never equals a node's, so it is never judged.
    if any(n.url_template != template or n.signature != login_signature for n in reached):
        return None
    return NEVER_LEFT_LOGIN.format(template=template)


def is_login_wall(nodes: list[ScreenNode], edges: list[ScreenEdge]) -> bool:
    """X18(b): every reached screen carries a refused form submit, and no NAVIGATED
    edge reaches a screen whose structure differs from the seed's — regardless of
    how many actions were spent going round in front of the wall."""
    if not nodes:
        return False
    seed = min(nodes, key=lambda n: n.depth)
    walled = {e.from_node for e in edges
              if e.outcome is EdgeOutcome.DENIED_POLICY and e.reason == FORM_SUBMIT_REFUSED}
    if any(n.id not in walled for n in nodes):
        return False
    signature = {n.id: n.signature for n in nodes}
    return not any(
        e.outcome is EdgeOutcome.NAVIGATED and e.to_node is not None
        and signature.get(e.to_node, seed.signature) != seed.signature
        for e in edges
    )


def terminal_status(*, completed: bool, actions_used: int, denied: int,
                    nodes: list[ScreenNode], edges: list[ScreenEdge],
                    login_case: Case | None,
                    login_signature: str | None = None) -> tuple[CrawlStatus, str | None]:
    """The status a finished crawl ends in, and a replacement stop reason when the
    status needs one. The wall checks come first: a crawl stuck at the login page is
    stuck whether its frontier emptied or a bound stopped it."""
    reason = never_left_login(nodes, login_case, login_signature)
    if reason is not None:
        return CrawlStatus.LOGIN_FAILED, reason
    if login_case is None and is_login_wall(nodes, edges):
        return CrawlStatus.LOGIN_WALL, LOGIN_WALL_REASON
    if not completed:
        return CrawlStatus.STOPPED_BOUND, None
    if actions_used == 0 and denied > 0:  # AT-242
        return CrawlStatus.BLOCKED_NO_ACTIONS, None
    return CrawlStatus.COMPLETED, None


def displayed_status(crawl: Crawl) -> CrawlStatus:
    """X18(d): what a human is SHOWN. A crawl.json written before AT-242 says `completed`
    with 0 actions and refusals — the file is history and stays as written, but it is
    not displayed as success."""
    if crawl.status is CrawlStatus.COMPLETED and crawl.actions == 0 and crawl.denied > 0:
        return CrawlStatus.BLOCKED_NO_ACTIONS
    return crawl.status


def is_success(crawl: Crawl) -> bool:
    """The one test every surface uses to decide whether to colour a crawl as success."""
    return displayed_status(crawl) is CrawlStatus.COMPLETED
