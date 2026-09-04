"""Run history, per-case screenshots, and portable downloads. Contract:
qa/contracts/ui-report.md UR1-UR4.
"""

from __future__ import annotations

import os
import tempfile
from html import escape
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask

from autotester.core.paths import ProjectPaths
from autotester.schema.enums import EvidenceKind, Result
from autotester.stages.report_export import export_excel, export_html, png_base64
from autotester.store.project_store import ProjectStore
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404, _require_safe_id

router = APIRouter()


def _run_ids_newest_first(slug: str) -> list[str]:
    paths = ProjectPaths(slug)
    if not paths.runs_dir.exists():
        return []
    return sorted((p.name for p in paths.runs_dir.iterdir() if p.is_dir()), reverse=True)


def _run_counts(store: ProjectStore, run_id: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for verdict in store.load_verdicts(run_id):
        counts[verdict.result.value] = counts.get(verdict.result.value, 0) + 1
    return counts


def _counts_stats(counts: dict[str, int]) -> str:
    return "<div class='stat-row'>" + "".join(
        theme.stat(str(v), theme.badge(escape(k))) for k, v in counts.items()
    ) + "</div>"


def _counts_badges(counts: dict[str, int]) -> str:
    """Compact inline pills (a run-history row) rather than full-size stat
    tiles — a stat tile's ~2rem number is meant for one page-level headline,
    not repeated once per row (that's what made the run-history table read
    as a wall of oversized, meaningless numbers)."""
    if not counts:
        return "<span class='meta'>no verdicts</span>"
    return "<div class='run-results'>" + "".join(
        theme.badge(escape(k), count=v) for k, v in counts.items()
    ) + "</div>"


def _run_date(store: ProjectStore, run_id: str) -> str:
    run = store.load_run(run_id)
    return escape(run.created_at.strftime("%Y-%m-%d %H:%M")) if run else ""


def _step_flow(run_dir: Path, evidence: list, case_index: int) -> str:
    """The DFS-style trace Umesh asked for: the literal ordered sequence of
    screens THIS case actually walked through — never every hypothetical
    branch (that's the deferred, explicitly-descoped BFS/mindmap idea,
    qa/feedback-inbox.md). Each thumbnail links to a same-page CSS-only
    lightbox (`:target`) so the compact flow can still show full detail on
    click, no JS needed."""
    shots = sorted(
        (s for s in evidence if s.kind is EvidenceKind.SCREENSHOT),
        key=lambda s: s.step_order if s.step_order is not None else 10**9,
    )
    steps: list[str] = []
    lightboxes: list[str] = []
    for i, shot in enumerate(shots):
        data = png_base64(run_dir / shot.path)
        if data is None:
            continue
        lb_id = f"lb-{case_index}-{i}"
        caption = escape(shot.label or shot.path)
        steps.append(
            f"<a class='flow-step' href='#{lb_id}'>"
            f"<span class='thumb'><img src='data:image/png;base64,{data}' loading='lazy'></span>"
            f"<span class='step-label'>{caption}</span></a>"
        )
        lightboxes.append(
            f"<a href='#' class='lightbox' id='{lb_id}'>"
            f"<img src='data:image/png;base64,{data}'>"
            f"<span class='lightbox-caption'>{caption}</span></a>"
        )
    if not steps:
        return "<p class='meta'>no screenshots captured</p>"
    arrow = "<span class='flow-arrow'>→</span>"
    return f"<div class='flow'>{arrow.join(steps)}</div>{''.join(lightboxes)}"


def _failure_list(failures: list) -> str:
    if not failures:
        return ""
    items = "".join(
        f"<li><code>{escape(f.criterion_id)}</code> — {escape(f.reason)}"
        + (f" <em>{escape(f.fix_hint)}</em>" if f.fix_hint else "") + "</li>"
        for f in failures
    )
    return f"<ul class='failure-list'>{items}</ul>"


@router.get("/projects/{slug}/runs/{run_id}", response_class=HTMLResponse)
def run_view(slug: str, run_id: str) -> str:
    store, _project = _load_project_or_404(slug)
    _require_safe_id(run_id, "run_id")
    safe_slug = escape(slug)
    safe_run_id = escape(run_id)
    run_dir = store.paths.run_dir(run_id)
    cases = {c.id: c for c in store.list_cases()}
    verdicts = {v.case_id: v for v in store.load_verdicts(run_id)}
    results = store.load_results(run_id)
    counts = _run_counts(store, run_id)

    def _case_body(r, case_index: int) -> str:
        verdict = verdicts.get(r.case_id)
        meta = [f"<span class='meta'>{escape(r.outcome.value)}</span>"]
        if verdict:
            meta.append(theme.badge(escape(verdict.result.value)))
            if verdict.grader_provider:
                provider = escape(verdict.grader_provider)
                meta.append(f"<span class='meta'>judged by {provider}</span>")
        scoreboard = (
            f"<p class='scoreboard'>{escape(verdict.scoreboard)}</p>"
            if verdict and verdict.scoreboard else ""
        )
        failures = _failure_list(verdict.failures) if verdict else ""
        error = f"<p class='scoreboard'>{escape(r.error)}</p>" if r.error else ""
        return (
            f"<div class='case-meta'>{''.join(meta)}</div>{scoreboard}{failures}{error}"
            f"{_step_flow(run_dir, r.evidence, case_index)}"
        )

    sections = "".join(
        theme.card(_case_body(r, i), title=escape(cases[r.case_id].title if r.case_id in cases
                                                  else r.case_id))
        for i, r in enumerate(results)
    )
    body = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / "
        f"<a href='/projects/{safe_slug}/report'>Report</a> / Run</div>"
        f"<h1>Run <code>{safe_run_id}</code></h1>"
        + (_counts_stats(counts) if counts else "")
        + (sections or theme.empty_state("📭", "No case results in this run yet."))
    )
    return theme.page(f"Run {safe_run_id}", body, active_slug=slug)


@router.get("/projects/{slug}/report", response_class=HTMLResponse)
def report(slug: str) -> str:
    _store, _project = _load_project_or_404(slug)
    safe_slug = escape(slug)
    breadcrumb = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Report</div>"
    )
    run_ids = _run_ids_newest_first(slug)
    if not run_ids:
        body = breadcrumb + "<h1>Report</h1>" + theme.empty_state(
            "📋", "no runs yet — run a case against this project to see a report here.",
        )
        return theme.page("Report", body, active_slug=slug)
    store = ProjectStore(slug)
    latest_id = run_ids[0]
    safe_run_id = escape(latest_id)

    all_counts = [_run_counts(store, rid) for rid in run_ids]
    total_verdicts = sum(sum(c.values()) for c in all_counts)
    total_pass = sum(c.get(Result.PASS.value, 0) for c in all_counts)
    pass_rate = f"{round(100 * total_pass / total_verdicts)}%" if total_verdicts else "—"
    overview = "<div class='stat-row'>" + "".join((
        theme.stat(str(len(run_ids)), "Total runs"),
        theme.stat(pass_rate, "Overall pass rate"),
        theme.stat(str(sum(all_counts[0].values())), "Cases in latest run"),
    )) + "</div>"

    downloads = (
        f"<a class='btn' href='/projects/{safe_slug}/report.xlsx'>⬇ Download Excel</a> "
        f"<a class='btn' href='/projects/{safe_slug}/report.html'>⬇ Download HTML</a>"
    )
    history_rows = "".join(
        f"<tr><td><a href='/projects/{safe_slug}/runs/{escape(rid)}'><code>{escape(rid)}</code>"
        f"</a><br><span class='run-date'>{_run_date(store, rid)}</span></td>"
        f"<td>{_counts_badges(_run_counts(store, rid))}</td></tr>"
        for rid in run_ids
    )
    history = theme.card(
        f"<table><tr><th>Run</th><th>Results</th></tr>{history_rows}</table>", title="Run history"
    )
    body = (
        breadcrumb + "<h1>Report</h1>"
        f"<p class='subtitle'>Latest run <code>{safe_run_id}</code> · "
        f"<a href='/projects/{safe_slug}/runs/{safe_run_id}'>view case-by-case</a> · "
        f"{downloads}</p>"
        f"{overview}"
        f"{history}"
    )
    return theme.page(f"Report — {safe_slug}", body, active_slug=slug)


def _reserved_temp_path(suffix: str) -> Path:
    """Reserve a unique filename via mkstemp, then hand it to the exporter to
    create fresh — export_excel/export_html both write a brand-new file, so
    the mkstemp-opened fd is closed and the placeholder removed immediately."""
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    path = Path(tmp)
    path.unlink()
    return path


@router.get("/projects/{slug}/report.xlsx")
def download_report_excel(slug: str) -> FileResponse:
    _load_project_or_404(slug)
    out = export_excel(slug, None, _reserved_temp_path(".xlsx"))
    return FileResponse(
        out, filename=f"{slug}-report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(out.unlink, missing_ok=True),
    )


@router.get("/projects/{slug}/report.html")
def download_report_html(slug: str) -> FileResponse:
    _load_project_or_404(slug)
    out = export_html(slug, None, _reserved_temp_path(".html"))
    return FileResponse(
        out, filename=f"{slug}-report.html", media_type="text/html",
        background=BackgroundTask(out.unlink, missing_ok=True),
    )
