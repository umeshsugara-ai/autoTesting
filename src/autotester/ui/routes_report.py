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
from autotester.schema.enums import EvidenceKind
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

    def _shots(evidence: list) -> str:
        images = "".join(
            f"<figure><img src='data:image/png;base64,{data}'>"
            f"<figcaption>{escape(shot.label or shot.path)}</figcaption></figure>"
            for shot in evidence if shot.kind is EvidenceKind.SCREENSHOT
            for data in [png_base64(run_dir / shot.path)] if data is not None
        )
        return images or "<p class='meta'>no screenshots captured</p>"

    def _result_cell(case_id: str) -> str:
        return theme.badge(escape(verdicts[case_id].result.value)) if case_id in verdicts else "-"

    sections = "".join(
        theme.card(
            f"<p class='subtitle'>{escape(r.outcome.value)} · {_result_cell(r.case_id)}</p>"
            f"<div class='shots'>{_shots(r.evidence)}</div>",
            title=escape(cases[r.case_id].title if r.case_id in cases else r.case_id),
        )
        for r in results
    )
    body = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Run</div>"
        f"<h1>Run <code>{safe_run_id}</code></h1>"
        + (sections or theme.empty_state("📭", "No case results in this run yet."))
    )
    return theme.page(f"Run {safe_run_id}", body)


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
        return theme.page("Report", body)
    store = ProjectStore(slug)
    latest_id = run_ids[0]
    safe_run_id = escape(latest_id)
    downloads = (
        f"<a class='btn' href='/projects/{safe_slug}/report.xlsx'>⬇ Download Excel</a> "
        f"<a class='btn' href='/projects/{safe_slug}/report.html'>⬇ Download HTML</a>"
    )
    history_rows = "".join(
        f"<tr><td><a href='/projects/{safe_slug}/runs/{escape(rid)}'><code>{escape(rid)}</code>"
        f"</a></td><td>{_counts_stats(_run_counts(store, rid))}</td></tr>"
        for rid in run_ids
    )
    history = theme.card(
        f"<table><tr><th>Run</th><th>Results</th></tr>{history_rows}</table>", title="Run history"
    )
    body = (
        breadcrumb + "<h1>Latest report</h1>"
        f"<p class='subtitle'>Run <code>{safe_run_id}</code> · "
        f"<a href='/projects/{safe_slug}/runs/{safe_run_id}'>view case-by-case</a> · "
        f"{downloads}</p>"
        f"{_counts_stats(_run_counts(store, latest_id))}"
        f"{history}"
    )
    return theme.page(f"Report — {safe_run_id}", body)


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
