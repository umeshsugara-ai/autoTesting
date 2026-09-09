"""The operator-facing recording registry.

This is the UI door to the same content-addressed ``Source`` ledger used by
``autotester ingest register``. It never creates a second upload registry or a
UI-only representation. Planned owner: Track A5.2 in ``plan.md``.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.browser.secrets import SecretStore
from autotester.core.paths import ProjectPaths
from autotester.stages.ingest import register_source
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404, _refuse_unsafe_submission

router = APIRouter()


def _link(href: str, text: str) -> str:
    return f"<a class='btn' href='{escape(href)}'>{escape(text)}</a>"


def _refusal(slug: str, message: str) -> HTMLResponse:
    body = theme.card(
        f"<p>{escape(message)}</p><p style='margin-top:14px'>"
        f"{_link(f'/projects/{slug}/sources', 'Try another path')}</p>",
        title="Recording not found",
    )
    return HTMLResponse(
        theme.page("Recording not found", body, active_slug=slug), status_code=400)


@router.get("/projects/{slug}/sources", response_class=HTMLResponse)
def sources_page(slug: str) -> str:
    """List registered sources and offer a server-local path registration form."""
    store, project = _load_project_or_404(slug)
    name = escape(project.name)
    crumbs = theme.breadcrumb(("Projects", "/"), (name, f"/projects/{slug}"),
                              ("Sources", None))
    rows = "".join(
        f"<tr><td><code>{escape(source.id)}</code></td>"
        f"<td>{escape(source.label or '—')}</td>"
        f"<td><code>{escape(source.path or '—')}</code></td></tr>"
        for source in store.list_sources()
    ) or "<tr><td colspan='3'>No recordings registered yet.</td></tr>"
    form = f"""
      <form method="post" action="/projects/{escape(slug)}/sources">
        <div class="field"><label for="path">Recording path on this machine</label>
          <input id="path" name="path" required placeholder="C:\\Videos\\product-flow.mp4">
          <span class="hint">The file stays where it is; AutoTester records its content hash.</span>
        </div>
        <div class="field"><label for="label">What this recording shows</label>
          <input id="label" name="label" placeholder="Trainer onboarding — happy path">
        </div>
        <button class="btn btn-primary" type="submit">Add recording</button>
      </form>"""
    body = crumbs + theme.card(form, title="Add a recording") + theme.card(
        "<table><thead><tr><th>Source</th><th>Label</th><th>Path</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>",
        title=f"{name} recordings",
    )
    return theme.page(f"{name} · Sources", body, active_slug=slug)


@router.post("/projects/{slug}/sources")
def add_source(slug: str, path: str = Form(""), label: str = Form("")):
    """Register a real local file through the canonical ingest-stage function."""
    store, project = _load_project_or_404(slug)
    secrets = SecretStore.load(project, ProjectPaths(slug).env_file, strict=False)
    _refuse_unsafe_submission([("recording path", path), ("label", label)], project, secrets)
    try:
        register_source(store, Path(path.strip()), label=label.strip() or None)
    except (FileNotFoundError, OSError) as exc:
        return _refusal(slug, str(exc))
    return RedirectResponse(f"/projects/{slug}/sources", status_code=303)
