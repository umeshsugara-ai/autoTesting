"""Operator-facing video issue ledger and its human-compatible workbook."""

from __future__ import annotations

from html import escape

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask

from autotester.stages.issues import ISSUE_COLUMNS, export_issues_excel, issue_row
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404, _reserved_temp_path

router = APIRouter()


@router.get("/projects/{slug}/issues", response_class=HTMLResponse)
def issues_page(slug: str) -> str:
    store, project = _load_project_or_404(slug)
    issues = store.list_issues()
    name = escape(project.name)
    header = "".join(f"<th>{escape(column)}</th>" for column in ISSUE_COLUMNS)
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in issue_row(issue)) + "</tr>"
        for issue in sorted(issues, key=lambda item: (item.recording_label, item.at_s))
    ) or f"<tr><td colspan='{len(ISSUE_COLUMNS)}'>No video issues derived yet.</td></tr>"
    body = (
        theme.breadcrumb(("Projects", "/"), (name, f"/projects/{slug}"), ("Issues", None))
        + "<h1>Video issues</h1>"
        + f"<p class='subtitle'>{len(issues)} finding(s) · "
          f"<a class='btn' href='/projects/{escape(slug)}/issues.xlsx'>⬇ Download Excel</a></p>"
        + theme.card(
            f"<div style='overflow:auto'><table><thead><tr>{header}</tr></thead>"
            f"<tbody>{rows}</tbody></table></div>", title=f"{name} issues")
    )
    return theme.page(f"{name} · Issues", body, active_slug=slug)


@router.get("/projects/{slug}/issues.xlsx")
def download_issues(slug: str) -> FileResponse:
    store, _project = _load_project_or_404(slug)
    out = export_issues_excel(store.list_issues(), _reserved_temp_path(".xlsx"))
    return FileResponse(
        out, filename=f"{slug}-issues.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(out.unlink, missing_ok=True),
    )
