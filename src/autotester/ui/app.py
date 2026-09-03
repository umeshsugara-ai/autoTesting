"""Thin FastAPI viewer/editor over project files. Design principle 8: never a
second source of truth — every route reads/writes through `ProjectStore`/
`SecretStore` exactly like the CLI does. Contract: qa/contracts/ui.md U1-U5.
"""

from __future__ import annotations

import re
from html import escape

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.browser.secrets import parse_env
from autotester.core.paths import ProjectPaths, repo_root
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore
from autotester.ui import theme
from autotester.ui.env_editor import InvalidEnvValue, set_env_value

app = FastAPI(title="AutoTester")

# Same shape as schema.project.Project.slug's own field pattern -- a slug is a
# single safe path segment, never `..`, `/`, `\`, or a null byte, before it is
# ever handed to ProjectPaths/ProjectStore as a directory name.
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# run/case ids are ulid- or content_id-shaped: alnum plus `_`/`-` only.
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _require_slug(slug: str) -> str:
    if not _SLUG_RE.fullmatch(slug):
        raise HTTPException(400, "invalid project slug")
    return slug


def _require_safe_id(value: str, label: str) -> str:
    if not _SAFE_ID_RE.fullmatch(value):
        raise HTTPException(400, f"invalid {label}")
    return value


def _project_slugs() -> list[str]:
    projects_dir = repo_root() / "projects"
    if not projects_dir.exists():
        return []
    return sorted(p.name for p in projects_dir.iterdir() if (p / "project.json").exists())


def _load_project_or_404(slug: str) -> tuple[ProjectStore, Project]:
    _require_slug(slug)
    store = ProjectStore(slug)
    project = store.load_project()
    if project is None:
        raise HTTPException(404, f"no project '{slug}'")
    return store, project


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    items = "".join(
        f'<li><a href="/projects/{escape(s)}">{escape(s)}</a></li>' for s in _project_slugs()
    )
    body = f"<h1>AutoTester</h1><ul>{items}</ul><a href='/onboard'>+ onboard a project</a>"
    return theme.page("Home", body)


@app.get("/onboard", response_class=HTMLResponse)
def onboard_form() -> str:
    body = (
        "<h1>Onboard a project</h1>"
        "<form method='post' action='/onboard'>"
        "slug: <input name='slug'><br>"
        "name: <input name='name'><br>"
        "base_url: <input name='base_url'><br>"
        "allowed_domains (comma-separated): <input name='allowed_domains'><br>"
        "<button type='submit'>Create</button></form>"
    )
    return theme.page("Onboard", body)


@app.post("/onboard")
def onboard_submit(
    slug: str = Form(...),
    name: str = Form(...),
    base_url: str = Form(...),
    allowed_domains: str = Form(...),
) -> RedirectResponse:
    _require_slug(slug)
    domains = [d.strip() for d in allowed_domains.split(",") if d.strip()]
    project = Project(slug=slug, name=name, base_url=base_url, allowed_domains=domains)
    ProjectStore(slug).save_project(project)
    return RedirectResponse(f"/projects/{slug}", status_code=303)


@app.get("/projects/{slug}", response_class=HTMLResponse)
def project_detail(slug: str) -> str:
    store, project = _load_project_or_404(slug)
    spec = store.load_flowspec()
    review = spec.review.status.value if spec is not None else "no flowspec yet"
    safe_slug = escape(slug)
    body = (
        f"<h1>{escape(project.name)}</h1>"
        f"<p>review: {escape(review)}</p>"
        f"<p>cases: {len(store.list_cases())}</p>"
        f"<a href='/projects/{safe_slug}/env'>credentials</a> | "
        f"<a href='/projects/{safe_slug}/report'>report</a>"
    )
    return theme.page(escape(project.name), body)


@app.get("/projects/{slug}/env", response_class=HTMLResponse)
def env_editor_view(slug: str) -> str:
    _store, project = _load_project_or_404(slug)
    paths = ProjectPaths(slug)
    present = (
        parse_env(paths.env_file.read_text(encoding="utf-8")) if paths.env_file.exists() else {}
    )
    rows = "".join(
        f"<tr><td>{escape(ref.key)}</td><td>{'set' if present.get(ref.key) else 'not set'}</td>"
        "<form method='post' action='env'>"
        f"<input type='hidden' name='key' value='{escape(ref.key)}'>"
        "<td><input type='password' name='value'></td>"
        "<td><button type='submit'>save</button></td></form></tr>"
        for ref in project.secrets
    )
    body = f"<h1>{escape(project.name)} — credentials</h1><table>{rows}</table>"
    return theme.page(f"{escape(project.name)} — credentials", body)


@app.post("/projects/{slug}/env")
def env_editor_submit(slug: str, key: str = Form(...), value: str = Form(...)) -> RedirectResponse:
    _store, project = _load_project_or_404(slug)
    if project.secret(key) is None:
        raise HTTPException(400, f"'{key}' is not a declared secret for '{slug}'")
    try:
        set_env_value(repo_root() / ".env", key, value)
    except InvalidEnvValue as exc:
        raise HTTPException(400, str(exc)) from exc
    return RedirectResponse(f"/projects/{slug}/env", status_code=303)


@app.get("/projects/{slug}/runs/{run_id}", response_class=HTMLResponse)
def run_view(slug: str, run_id: str) -> str:
    store, _project = _load_project_or_404(slug)
    _require_safe_id(run_id, "run_id")
    verdicts = {v.case_id: v for v in store.load_verdicts(run_id)}
    def _result_cell(case_id: str) -> str:
        return theme.badge(escape(verdicts[case_id].result.value)) if case_id in verdicts else "-"

    rows = "".join(
        f"<tr><td>{escape(r.case_id)}</td><td>{escape(r.outcome.value)}</td>"
        f"<td>{_result_cell(r.case_id)}</td></tr>"
        for r in store.load_results(run_id)
    )
    body = f"<h1>Run {escape(run_id)}</h1><table>{rows}</table>"
    return theme.page(f"Run {escape(run_id)}", body)


@app.get("/projects/{slug}/report", response_class=HTMLResponse)
def report(slug: str) -> str:
    _store, _project = _load_project_or_404(slug)
    paths = ProjectPaths(slug)
    run_ids = sorted(p.name for p in paths.runs_dir.iterdir() if p.is_dir()) \
        if paths.runs_dir.exists() else []
    if not run_ids:
        return theme.page("Report", "<h1>Report</h1><p>no runs yet</p>")
    store = ProjectStore(slug)
    counts: dict[str, int] = {}
    for verdict in store.load_verdicts(run_ids[-1]):
        counts[verdict.result.value] = counts.get(verdict.result.value, 0) + 1
    rows = "".join(f"<li>{theme.badge(escape(k))}: {v}</li>" for k, v in counts.items())
    body = f"<h1>Report — {escape(run_ids[-1])}</h1><ul>{rows}</ul>"
    return theme.page(f"Report — {escape(run_ids[-1])}", body)


@app.get("/live", response_class=HTMLResponse)
def live_view() -> str:
    """Presentation-only: an embedded noVNC viewer onto the container's virtual
    display. Reads no project state, triggers no run (qa/contracts/docker.md D4)."""
    example = "docker compose exec autotester uv run python scripts/regression_proof.py"
    body = (
        "<h1>Live view</h1>"
        "<p>Watch a run happen in real time — start one from a script "
        f"(e.g. <code>{example}</code>) while this page is open.</p>"
        "<iframe class='live-view' "
        "src='http://localhost:6080/vnc.html?autoconnect=true&resize=scale'></iframe>"
    )
    return theme.page("Live view", body)
