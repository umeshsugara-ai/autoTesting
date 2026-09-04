"""The masked .env editor. Contract: qa/contracts/ui.md U3 — a real value is
never rendered once saved, only whether one is set.
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.browser.secrets import parse_env
from autotester.core.paths import ProjectPaths, repo_root
from autotester.ui import theme
from autotester.ui.env_editor import InvalidEnvValue, set_env_value
from autotester.ui.helpers import _load_project_or_404

router = APIRouter()


@router.get("/projects/{slug}/env", response_class=HTMLResponse)
def env_editor_view(slug: str) -> str:
    _store, project = _load_project_or_404(slug)
    paths = ProjectPaths(slug)
    present = (
        parse_env(paths.env_file.read_text(encoding="utf-8")) if paths.env_file.exists() else {}
    )
    name = escape(project.name)
    safe_slug = escape(slug)
    if not project.secrets:
        table = theme.empty_state("🔑", "This project declares no credentials.")
    else:
        def _status_cell(key: str) -> str:
            return (theme.pill("● Set", "positive") if present.get(key)
                    else theme.pill("○ Not set", "neutral"))

        rows = "".join(
            f"<tr><td>{escape(ref.key)}</td>"
            f"<td>{_status_cell(ref.key)}</td>"
            f"<form method='post' action='env'>"
            f"<input type='hidden' name='key' value='{escape(ref.key)}'>"
            "<td><input type='password' name='value' placeholder='new value'></td>"
            "<td><button class='btn btn-sm' type='submit'>Save</button></td></form></tr>"
            for ref in project.secrets
        )
        header = "<tr><th>Key</th><th>Status</th><th>New value</th><th></th></tr>"
        table = f"<table>{header}{rows}</table>"
    body = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{name}</a> / Credentials</div>"
        "<h1>Credentials</h1>"
        "<p class='subtitle'>Values are never shown once saved — only whether one is set.</p>"
        f"{theme.card(table)}"
    )
    return theme.page(f"{name} — credentials", body)


@router.post("/projects/{slug}/env")
def env_editor_submit(slug: str, key: str = Form(...), value: str = Form(...)) -> RedirectResponse:
    _store, project = _load_project_or_404(slug)
    if project.secret(key) is None:
        raise HTTPException(400, f"'{key}' is not a declared secret for '{slug}'")
    try:
        set_env_value(repo_root() / ".env", key, value)
    except InvalidEnvValue as exc:
        raise HTTPException(400, str(exc)) from exc
    return RedirectResponse(f"/projects/{slug}/env", status_code=303)
