"""The explorer, on screen: crawl history, one crawl's screen graph, its
Excel export, and the two buttons that start a crawl or fold it into the
FlowSpec (Track B5).

Before this, `autotester explore` wrote a graph to disk that nothing rendered.
Contract: qa/contracts/explore.md (X11 artifacts are human-readable) +
qa/contracts/ui.md.
"""

from __future__ import annotations

from html import escape
from math import isfinite

from fastapi import APIRouter, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from starlette.background import BackgroundTask

from autotester.core.ids import run_id
from autotester.core.paths import ProjectPaths
from autotester.schema.crawl import CrawlBounds
from autotester.schema.enums import IssueKind
from autotester.stages.coverage import diff_crawl, queue_requests, unreached_screens
from autotester.stages.crawl_report import export_crawl_excel
from autotester.stages.explore_merge import merge_screens
from autotester.stages.merge_flowspec import resolve_requests
from autotester.ui import crawl_view, theme
from autotester.ui.helpers import (
    _load_project_or_404,
    _require_safe_id,
    _reserved_temp_path,
)

router = APIRouter()

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _bounds_form(slug: str, label: str) -> str:
    """The exact four operator-controlled bounds used by crawl preflight/run."""
    safe = escape(slug)
    fields = (
        ("max_screens", "Maximum screens", "30", "1"),
        ("max_actions", "Maximum actions", "200", "1"),
        ("wall_clock_s", "Wall clock (seconds)", "600", "any"),
        ("max_depth", "Maximum depth", "6", "1"),
    )
    inputs = "".join(
        f"<div class='field'><label>{title}</label><input type='number' name='{name}' "
        f"min='1' step='{step}' value='{value}' required></div>"
        for name, title, value, step in fields
    )
    return (
        f"<form method='post' action='/projects/{safe}/explore'>"
        f"{inputs}<button type='submit'>{label}</button></form>"
    )


def _crawl_error(slug: str, status: int, title: str, detail: str) -> HTMLResponse:
    safe = escape(slug)
    detail = detail.split("Grant one with:", 1)[0].strip()
    action = (
        f"<p><a class='btn' href='/projects/{safe}/env#crawl-approval'>"
        "Review credentials and approve crawl</a></p>"
    )
    body = _crumbs(slug) + f"<h1>{escape(title)}</h1>" + theme.card(
        f"<p>{escape(detail)}</p>{action}", title="Crawl not started",
    )
    return HTMLResponse(theme.page(escape(title), body, active_slug=slug), status_code=status)


def _parse_bounds(values: tuple[str, str, str, str]) -> CrawlBounds:
    try:
        screens, actions, seconds, depth = (
            int(values[0]), int(values[1]), float(values[2]), int(values[3])
        )
    except ValueError:
        raise ValueError("all crawl bounds must be numbers") from None
    if screens <= 0 or actions <= 0 or seconds <= 0 or depth <= 0 or not isfinite(seconds):
        raise ValueError("all crawl bounds must be positive")
    return CrawlBounds(max_screens=screens, max_actions=actions,
                       wall_clock_s=seconds, max_depth=depth)


def _crumbs(slug: str, *tail: tuple[str, str | None]) -> str:
    return theme.breadcrumb(
        ("Projects", "/"), (escape(slug), f"/projects/{escape(slug)}"),
        ("Crawls", f"/projects/{escape(slug)}/crawls" if tail else None), *tail,
    )


@router.get("/projects/{slug}/crawls", response_class=HTMLResponse)
def crawls(slug: str) -> str:
    store, _project = _load_project_or_404(slug)
    safe = escape(slug)
    crawl_ids = store.list_crawl_ids()
    if not crawl_ids:
        body = _crumbs(slug) + "<h1>Crawls</h1>" + theme.empty_state(
            "🕸", "No crawls yet — explore this project to map its screens on its own.",
            _bounds_form(slug, "Explore now"),
        )
        return theme.page("Crawls", body, active_slug=slug)
    rows = []
    for crawl_id in crawl_ids:
        crawl = store.load_crawl(crawl_id)
        if crawl is None:
            continue
        rows.append(
            f"<tr><td><a href='/projects/{safe}/crawls/{escape(crawl_id)}'>"
            f"<code>{escape(crawl_id)}</code></a></td>"
            f"<td>{theme.pill(escape(crawl.status.value), 'neutral')}</td>"
            f"<td>{escape(crawl.stop_reason or '—')}</td><td>{crawl.screens}</td>"
            f"<td>{crawl.denied}</td><td>{crawl.issues}</td>"
            f"<td>{crawl.tool_failures}</td>"
            f"<td>{escape(crawl.started_at or '—')}</td></tr>"
        )
    table = (
        "<table class='data-table'><thead><tr><th>Crawl</th><th>Status</th>"
        "<th>Stopped because</th><th>Screens</th><th>Refused</th><th>Issues</th>"
        "<th>Tool failures</th>"
        f"<th>Started</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )
    body = (
        _crumbs(slug) + "<h1>Crawls</h1>"
        + theme.card(_bounds_form(slug, "Explore again"), title="New bounded crawl")
        + theme.card(table)
    )
    return theme.page("Crawls", body, active_slug=slug)


@router.get("/projects/{slug}/crawls/{crawl_id}", response_class=HTMLResponse)
def crawl_page(slug: str, crawl_id: str) -> str:
    store, _project = _load_project_or_404(slug)
    _require_safe_id(crawl_id, "crawl_id")
    crawl = store.load_crawl(crawl_id)
    safe, safe_id = escape(slug), escape(crawl_id)
    if crawl is None:
        body = _crumbs(slug, ("Crawl", None)) + theme.empty_state(
            "❓", f"No crawl '{safe_id}' in this project.")
        return HTMLResponse(theme.page("Crawl not found", body, active_slug=slug), status_code=404)

    nodes = store.list_nodes(crawl_id)
    edges = store.list_edges(crawl_id)
    issues = store.list_crawl_issues(crawl_id)
    names = {n.id: (n.name or n.title or n.url_template) for n in nodes}
    spec = store.load_flowspec()

    coverage = (
        theme.card(
            crawl_view.review_line(spec)
            + crawl_view.coverage_card(diff_crawl(spec, nodes), unreached_screens(spec, nodes))
            + f"<form method='post' action='/projects/{safe}/crawls/{safe_id}/merge'>"
            "<button type='submit'>Merge these screens into the FlowSpec</button></form>",
            title="Against the FlowSpec",
        )
        if spec is not None
        else theme.card(
            "<p class='meta'>This project has no FlowSpec yet.</p>"
            f"<form method='post' action='/projects/{safe}/crawls/{safe_id}/merge'>"
            "<button type='submit'>Create a FlowSpec from these screens</button></form>",
            title="Against the FlowSpec",
        )
    )
    body = (
        _crumbs(slug, ("Crawl", None))
        + f"<h1>Crawl <code>{safe_id}</code></h1>"
        + crawl_view.summary_stats(crawl)
        + f"<p><a href='/projects/{safe}/crawls/{safe_id}/report.xlsx'>"
          "Download Excel report</a></p>"
        + theme.card(crawl_view.screen_tree(slug, crawl, nodes, edges), title="Screens found")
        + theme.card(crawl_view.refused_table(edges, names), title="Refused & skipped")
        + theme.card(crawl_view.issues_table(
            [i for i in issues if i.kind is not IssueKind.EVIDENCE], names),
            title="Issues found in the product")
        + theme.card(crawl_view.tool_failures_table(
            [i for i in issues if i.kind is IssueKind.EVIDENCE], names),
            title="What the crawler itself could not do")
        + coverage
        + theme.card(crawl_view.summary_table(crawl), title="Run detail")
    )
    return theme.page(f"Crawl {safe_id}", body, active_slug=slug)


@router.get("/projects/{slug}/crawls/{crawl_id}/report.xlsx")
def download_crawl_excel(slug: str, crawl_id: str) -> FileResponse:
    _load_project_or_404(slug)
    _require_safe_id(crawl_id, "crawl_id")
    out = export_crawl_excel(slug, crawl_id, _reserved_temp_path(".xlsx"))
    return FileResponse(
        out, filename=f"{slug}-{crawl_id}.xlsx", media_type=_XLSX,
        background=BackgroundTask(out.unlink, missing_ok=True),
    )


@router.post("/projects/{slug}/explore")
def start_crawl(
    slug: str, max_screens: str = Form("30"), max_actions: str = Form("200"),
    wall_clock_s: str = Form("600"), max_depth: str = Form("6"),
) -> Response:
    """Synchronous, like the Run button — the same trade-off `routes_runs.py`
    already makes (no background job queue), so the page returns when the crawl
    is genuinely finished rather than promising one that never ran."""
    from autotester.browser.observe import PageObserver
    from autotester.browser.secrets import SecretStore
    from autotester.browser.session import BrowserSession
    from autotester.core.consent import ApprovalRequired
    from autotester.stages import explore as explore_stage

    store, project = _load_project_or_404(slug)
    try:
        bounds = _parse_bounds((max_screens, max_actions, wall_clock_s, max_depth))
    except ValueError as exc:
        return _crawl_error(slug, 400, "Invalid crawl bounds", str(exc))
    try:
        explore_stage.require_consent(project, store, bounds)
    except ApprovalRequired as exc:
        return _crawl_error(slug, 403, "Crawl approval required", str(exc))
    paths = ProjectPaths(slug)
    paths.ensure()
    secrets = SecretStore.load(project, paths.env_file, strict=False)
    observer = PageObserver()
    crawl_id = run_id("crawl")
    try:
        with BrowserSession(project, secrets, paths.crawl_shots_dir(crawl_id),
                            paths, observer=observer) as session:
            crawl = explore_stage.run_crawl(project, session, store, observer=observer,
                                            bounds=bounds, crawl_id=crawl_id)
    except ApprovalRequired as exc:
        return _crawl_error(slug, 403, "Crawl approval required", str(exc))
    # AT-240, the crawl half. `diff_crawl` was rendered on the crawl page and
    # never persisted as an ask, so a screen the crawler could not recognise
    # stayed a paragraph nobody was accountable for.
    spec = store.load_flowspec()
    if spec is not None:
        queue_requests(store, diff_crawl(spec, store.list_nodes(crawl.id)))
    return RedirectResponse(f"/projects/{slug}/crawls/{crawl.id}", status_code=303)


@router.post("/projects/{slug}/crawls/{crawl_id}/merge")
def merge_crawl(slug: str, crawl_id: str) -> RedirectResponse:
    """Fold the crawl's screens into the FlowSpec. Sends the spec back to DRAFT
    when anything changed — a crawl may propose screens, never approve them."""
    store, _project = _load_project_or_404(slug)
    _require_safe_id(crawl_id, "crawl_id")
    nodes = store.list_nodes(crawl_id)
    spec = merge_screens(store.load_flowspec(), nodes, slug, crawl_id=crawl_id)
    store.save_flowspec(spec)
    # AT-289: covering a gap and leaving its ask OPEN is the V6 two-seam drift on
    # the CLOSING side — `queue_requests` is called from both entry points, so
    # `resolve_requests` must be too, or the only door an operator has (T-100:
    # no CLI) closes the gap and never closes the request.
    resolve_requests(store, spec, source_id=crawl_id)
    return RedirectResponse(f"/projects/{slug}/crawls/{crawl_id}", status_code=303)
