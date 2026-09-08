"""The explorer, on screen: crawl history, one crawl's screen graph, its
Excel export, and the two buttons that start a crawl or fold it into the
FlowSpec (Track B5).

Before this, `autotester explore` wrote a graph to disk that nothing rendered.
Contract: qa/contracts/explore.md (X11 artifacts are human-readable) +
qa/contracts/ui.md.
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette.background import BackgroundTask

from autotester.core.ids import run_id
from autotester.core.paths import ProjectPaths
from autotester.schema.crawl import CrawlBounds
from autotester.schema.enums import IssueKind
from autotester.stages.coverage import diff_crawl, unreached_screens
from autotester.stages.crawl_report import export_crawl_excel
from autotester.stages.explore_merge import merge_screens
from autotester.store.project_store import ProjectStore
from autotester.ui import crawl_view, theme
from autotester.ui.helpers import (
    _load_project_or_404,
    _require_safe_id,
    _reserved_temp_path,
)

router = APIRouter()

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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
            f"<form method='post' action='/projects/{safe}/explore'>"
            "<button type='submit'>Explore now</button></form>",
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
            f"<td>{crawl.tool_failures or '—'}</td>"
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
        + f"<form method='post' action='/projects/{safe}/explore'>"
        "<button type='submit'>Explore again</button></form>"
        + theme.card(table)
    )
    return theme.page("Crawls", body, active_slug=slug)


@router.get("/projects/{slug}/crawls/{crawl_id}", response_class=HTMLResponse)
def crawl_page(slug: str, crawl_id: str) -> str:
    store, _project = _load_project_or_404(slug)
    _require_safe_id(crawl_id, "crawl_id")
    crawl = store.load_crawl(crawl_id)
    safe = escape(slug)
    safe_id = escape(crawl_id)
    if crawl is None:
        body = _crumbs(slug, ("Crawl", None)) + theme.empty_state(
            "❓", f"No crawl '{safe_id}' in this project.")
        return theme.page("Crawl", body, active_slug=slug)

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
def start_crawl(slug: str) -> RedirectResponse:
    """Synchronous, like the Run button — the same trade-off `routes_runs.py`
    already makes (no background job queue), so the page returns when the crawl
    is genuinely finished rather than promising one that never ran."""
    from autotester.browser.observe import PageObserver
    from autotester.browser.secrets import SecretStore
    from autotester.browser.session import BrowserSession
    from autotester.core.consent import ApprovalRequired
    from autotester.stages import explore as explore_stage

    _store, project = _load_project_or_404(slug)
    store = ProjectStore(slug)
    try:
        explore_stage.require_consent(project, store, CrawlBounds())
    except ApprovalRequired as exc:
        # 403, not 500: refused on purpose, and the detail names the grant
        # command. Before `paths.ensure()` and the browser launch (AT-111).
        raise HTTPException(status_code=403, detail=str(exc)) from None
    paths = ProjectPaths(slug)
    paths.ensure()
    secrets = SecretStore.load(project, paths.env_file, strict=False)
    observer = PageObserver()
    crawl_id = run_id("crawl")
    try:
        with BrowserSession(project, secrets, paths.crawl_shots_dir(crawl_id),
                            paths, observer=observer) as session:
            crawl = explore_stage.run_crawl(project, session, store, observer=observer,
                                            crawl_id=crawl_id)
    except ApprovalRequired as exc:
        # 403, not 500: the run was refused on purpose, and the message names the
        # exact command that grants consent (D-018).
        raise HTTPException(status_code=403, detail=str(exc)) from None
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
    return RedirectResponse(f"/projects/{slug}/crawls/{crawl_id}", status_code=303)
