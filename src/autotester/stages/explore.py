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

from autotester.browser.observe import PageObserver, observe
from autotester.browser.session import BrowserSession, NavigationRefused
from autotester.schema.case import Case
from autotester.schema.crawl import Crawl, CrawlBounds, NoiseCount, SafetyPolicy
from autotester.schema.enums import CrawlStatus, Outcome
from autotester.schema.project import Project
from autotester.schema.screen_graph import CrawlFrontier, ScreenNode
from autotester.stages import explore_node
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
    noise: dict[str, int] = field(default_factory=dict)
    edges: int = 0
    denied: int = 0
    issues: int = 0
    stop_reason: str | None = None
    seed_error: str | None = None

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
    the explorer types anything, and the only pre-crawl form submit (X10)."""
    result = run_case(case, rt.session)
    rt.store.save_result(rt.crawl.id, result)
    return result.outcome is Outcome.COMPLETED


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


def _finish(rt: ExploreRuntime, status: CrawlStatus) -> Crawl:
    crawl = rt.crawl.model_copy(update={
        "status": status,
        "stop_reason": rt.stop_reason,
        "finished_at": _now_iso(),
        "screens": len(rt.nodes),
        "edges": rt.edges,
        "actions": rt.frontier.actions_used,
        "denied": rt.denied,
        "issues": rt.issues,
        "noise_counts": [NoiseCount(host=h, count=c) for h, c in sorted(rt.noise.items())],
    })
    rt.crawl = crawl
    rt.store.save_crawl(crawl)
    rt.store.save_frontier(crawl.id, rt.frontier)
    return crawl


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
    """
    envelope = {
        "project": project.slug,
        "bounds": bounds or CrawlBounds(),
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
        rt.stop_reason = "login case did not complete"
        return _finish(rt, CrawlStatus.LOGIN_FAILED)
    if _seed(rt) is None:
        rt.stop_reason = f"could not open base_url -- {rt.seed_error or 'cause not recorded'}"
        return _finish(rt, CrawlStatus.ABORTED)
    _bfs(rt)
    completed = rt.stop_reason == "frontier empty"
    return _finish(rt, CrawlStatus.COMPLETED if completed else CrawlStatus.STOPPED_BOUND)
