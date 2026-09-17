"""EXPLORE: a bounded, safety-gated BFS crawl of a (usually logged-in) app.

Contract: qa/contracts/explore.md. **This is the one stage permitted to
invent a click or a navigation** — `execute.md` E5 ("`run_case` performs
exactly the actions in `case.steps`") stays intact and untouched; the
explorer never routes through `run_case` except for the human-authored
login bootstrap case.

Every bound here can actually end the crawl and name itself in
`Crawl.stop_reason`, and no stop condition depends on provider output — a
crawl completes with `provider=mock` (X4). Per-node work lives in
`explore_node.py`; the safety decisions in `explore_safety.py`.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlparse

from autotester.browser.observe import PageObserver, observe
from autotester.browser.session import BrowserSession, NavigationRefused
from autotester.core.consent import require_approval
from autotester.schema.case import Case
from autotester.schema.crawl import Crawl, CrawlBounds, NoiseCount, SafetyPolicy
from autotester.schema.enums import Action, ApprovalKind, CrawlStatus, Outcome
from autotester.schema.project import Project
from autotester.schema.screen_graph import CrawlFrontier, ScreenEdge, ScreenNode
from autotester.stages import crawl_coverage, explore_node, explore_status
from autotester.stages.execute import run_case
from autotester.stages.explore_safety import DialogBreaker
from autotester.stages.screen_identity import node_from
from autotester.store.project_store import ProjectStore


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ExploreRuntime:
    """Live objects for one crawl — a session, a store, a clock, and the
    in-memory node index. Deliberately NOT a schema model: it duplicates no
    persisted shape (C1), and nothing here is serialisable."""

    project: Project
    session: BrowserSession
    store: ProjectStore
    crawl: Crawl
    observer: PageObserver
    breaker: DialogBreaker
    clock: Callable[[], float]
    started: float
    frontier: CrawlFrontier
    nodes: dict[str, ScreenNode] = field(default_factory=dict)
    discovery: dict[str, ScreenEdge] = field(default_factory=dict)
    """node id -> the edge that first reached it. AT-227: a screen that is only
    a client-side STATE of another (a dismissed modal) has no URL, so replaying
    this edge is the only way back."""
    noise: dict[str, int] = field(default_factory=dict)
    edges: int = 0
    denied: int = 0
    issues: int = 0
    tool_failures: int = 0
    stop_reason: str | None = None
    seed_error: str | None = None
    login_precheck_error: str | None = None
    """AT-273: why `_already_past_login` fell through to `False` on an exception,
    distinct from a genuine "not yet authenticated" `False` (diagnostic only)."""
    login_signature: str | None = None
    """X18(a)/AT-462: the login screen's structure, observed before the case typed."""
    login_observe_error: str | None = None  # AT-474: observed_signature()'s error, if any
    return_error: str | None = None
    """Why the most recent `return_to` failed. Scratch, not persisted — it is
    read straight into the issue text at the failure site (AT-108)."""

    @property
    def bounds(self) -> CrawlBounds:
        return self.crawl.bounds

    @property
    def policy(self) -> SafetyPolicy:
        return self.crawl.policy


def stop_reason(rt: ExploreRuntime) -> str | None:
    """Which bound (if any) has been reached. Checked before every node and
    before every action, so a bound cannot be overshot by a whole node."""
    if rt.frontier.screens_found >= rt.bounds.max_screens:
        return "max_screens"
    if rt.frontier.actions_used >= rt.bounds.max_actions:
        return "max_actions"
    if rt.clock() - rt.started >= rt.bounds.wall_clock_s:
        return "wall_clock_s"
    return None


def _bootstrap_login(rt: ExploreRuntime, case: Case) -> bool:
    """Run the human-authored login case through `run_case` — the ONLY place
    the explorer types anything, and the only pre-crawl form submit (X10).

    **AT-226.** A persistent browser profile can already hold a live session,
    in which case the login page itself redirects away before the case's own
    FILL step ever runs — the field it names (e.g. `input[name="identifier"]`)
    is not merely empty, it is not on the page at all, and `run_case` blocks
    for the full step timeout before reporting ERRORED. Checked once, before
    the case runs, against the case's own NAVIGATE step: if the browser lands
    somewhere other than the login page itself, the session is already
    authenticated and the case is skipped rather than run to a guaranteed
    timeout. This needs no app-specific "am I on the dashboard" marker — a
    login page that redirects away from itself has already done its job."""
    login_step = next(
        (s for s in sorted(case.steps, key=lambda s: s.order) if s.action is Action.NAVIGATE),
        None,
    )
    if login_step is not None and _already_past_login(rt, login_step.target):
        return True
    result = run_case(case, rt.session)
    rt.store.save_result(rt.crawl.id, result)
    return result.outcome is Outcome.COMPLETED


def _already_past_login(rt: ExploreRuntime, login_url: str) -> bool:
    """Navigate to the case's login page; report whether the app redirected away
    (AT-226). Still there -> record the login screen's signature for X18(a).
    AT-273: a nav failure must not read as a genuine "not yet authenticated"
    `False` -- it is still the safe fallback, but its CAUSE is kept."""
    try:
        rt.session.goto(login_url)
        rt.session.settle(timeout_ms=rt.bounds.settle_ms)
    except NavigationRefused as exc:
        rt.login_precheck_error = f"refused by the domain guard: {exc}"
        return False
    except Exception as exc:
        rt.login_precheck_error = f"{type(exc).__name__}: {exc}"
        return False
    if urlparse(rt.session.current_url()).path != urlparse(login_url).path:
        return True
    rt.login_signature, rt.login_observe_error = explore_status.observed_signature(rt.session)
    explore_node.record_login_observe_failure(rt, rt.login_observe_error)
    return False


def _seed(rt: ExploreRuntime) -> ScreenNode | None:
    """Open `base_url` and record it as the first node.

    AT-098: the cause is bound and kept. Detection was never lost -- the crawl
    did abort and did say so -- but every distinct failure collapsed to one
    string, so an operator watching a live ERP crawl could not tell whether the
    product was down or whether the crawl had been refused by its own domain
    guard. A `NavigationRefused` is the X7 SECURITY refusal and must never read
    like a DNS timeout.
    """
    try:
        rt.session.goto(rt.project.base_url)
        rt.session.settle(timeout_ms=rt.bounds.settle_ms)
        observation = observe(rt.session)
    except NavigationRefused as exc:
        rt.seed_error = f"refused by the domain guard: {exc}"
        return None
    except Exception as exc:
        rt.seed_error = f"{type(exc).__name__}: {exc}"
        return None
    node = node_from(observation, rt.crawl.id, rt.project.slug, depth=0)
    node = node.model_copy(update={"screenshot_ref": explore_node.capture(rt, node)})
    rt.nodes[node.id] = node
    rt.store.add_node(node)
    rt.frontier.queue.append(node.id)
    rt.frontier.screens_found += 1
    return node


def _bfs(rt: ExploreRuntime) -> None:
    while rt.frontier.queue:
        reached = stop_reason(rt)
        if reached:
            rt.stop_reason = reached
            return
        node = rt.nodes.get(rt.frontier.queue.pop(0))
        if node is None:
            continue
        explore_node.visit_node(rt, node)
        rt.frontier.visited.append(node.id)
        rt.store.save_frontier(rt.crawl.id, rt.frontier)
    rt.stop_reason = rt.stop_reason or "frontier empty"


def _login_failed_reason(rt: ExploreRuntime) -> str:
    """AT-273: name the login-precheck's own swallowed cause when the case
    then genuinely failed too, so an operator sees the precheck itself
    glitched rather than only that login did."""
    reason = "login case did not complete"
    if rt.login_precheck_error:
        reason += f" (precheck also failed: {rt.login_precheck_error})"
    return reason


def _terminal_status(rt: ExploreRuntime, completed: bool, login_case: Case | None) -> CrawlStatus:
    """Decided in `explore_status` (AT-242, X18); this feeds it the graph."""
    status, reason = explore_status.terminal_status(
        completed=completed, actions_used=rt.frontier.actions_used, denied=rt.denied,
        nodes=list(rt.nodes.values()), edges=rt.store.list_edges(rt.crawl.id),
        login_case=login_case, login_signature=rt.login_signature,
        login_observe_error=rt.login_observe_error, current_stop_reason=rt.stop_reason,
    )
    if reason is not None:
        rt.stop_reason = reason
    return status


def _finish(rt: ExploreRuntime, status: CrawlStatus) -> Crawl:
    crawl = rt.crawl.model_copy(update={
        "status": status,
        "stop_reason": rt.session.secrets.scrub_optional(rt.stop_reason),  # AT-350
        "finished_at": _now_iso(),
        "screens": len(rt.nodes),
        "edges": rt.edges,
        "actions": rt.frontier.actions_used,
        "denied": rt.denied,
        "issues": rt.issues,
        "tool_failures": rt.tool_failures,
        "noise_counts": [NoiseCount(host=h, count=c) for h, c in sorted(rt.noise.items())],
        "coverage": crawl_coverage.of_run(rt, status),  # V7
    })
    rt.crawl = crawl
    rt.store.save_crawl(crawl)
    rt.store.save_frontier(crawl.id, rt.frontier)
    return crawl


def require_consent(project: Project, store: ProjectStore, bounds: CrawlBounds) -> None:
    """D-018 gate 2. Public so a caller can ALSO check it before opening a
    browser — `run_crawl` still checks unconditionally, so the seam holds even
    if a new caller forgets the pre-flight.

    AT-111 (checker-found): checking only here was not enough. Both shipped
    entry points wrap `run_crawl` in `with BrowserSession(...)`, and
    `BrowserSession.start()` creates `crawl/<id>/shots/` and launches Chromium
    before `run_crawl` is ever entered — so the "a refused run leaves no trace"
    property this unit sells was true of the direct call and false of every path
    an operator actually uses.
    """
    require_approval(
        store.list_approvals(), project=project.slug, kind=ApprovalKind.CRAWL,
        target=project.base_url, actions=bounds.max_actions,
        wall_clock_s=bounds.wall_clock_s,
    )


def run_crawl(
    project: Project,
    session: BrowserSession,
    store: ProjectStore,
    *,
    observer: PageObserver,
    bounds: CrawlBounds | None = None,
    policy: SafetyPolicy | None = None,
    login_case: Case | None = None,
    crawl_id: str | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Crawl:
    """Crawl `project` breadth-first within `bounds`, refusing anything
    `policy` denies. Returns the finished `Crawl` envelope; the graph itself
    is on disk (nodes/edges/issues JSONL) and is loadable even if this
    raises partway (X11).

    `crawl_id` is accepted so a caller can mint it first and point the
    session's screenshot directory at `crawl/<id>/shots/` — the id has to
    exist before the session does.

    **Raises `ApprovalRequired` before anything is created or opened** — see
    `require_consent`.
    """
    bounds = bounds or CrawlBounds()
    require_consent(project, store, bounds)
    envelope = {
        "project": project.slug,
        "bounds": bounds,
        "policy": policy or SafetyPolicy(write_policy=project.write_policy),
        "login_case_id": login_case.id if login_case else None,
        "started_at": _now_iso(),
    }
    crawl = Crawl(id=crawl_id, **envelope) if crawl_id else Crawl(**envelope)  # type: ignore[arg-type]
    store.save_crawl(crawl)
    rt = ExploreRuntime(
        project=project, session=session, store=store, crawl=crawl, observer=observer,
        breaker=DialogBreaker(crawl.bounds.dialog_repeat_limit), clock=clock,
        started=clock(), frontier=CrawlFrontier(),
    )
    if login_case is not None and not _bootstrap_login(rt, login_case):
        rt.stop_reason = _login_failed_reason(rt)
        return _finish(rt, CrawlStatus.LOGIN_FAILED)
    if _seed(rt) is None:
        rt.stop_reason = f"could not open base_url -- {rt.seed_error or 'cause not recorded'}"
        return _finish(rt, CrawlStatus.ABORTED)
    _bfs(rt)
    completed = rt.stop_reason == "frontier empty"
    return _finish(rt, _terminal_status(rt, completed, login_case))
