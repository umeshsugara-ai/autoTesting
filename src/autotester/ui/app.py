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


def _project_card(slug: str) -> str:
    store = ProjectStore(slug)
    project = store.load_project()
    name = escape(project.name) if project else escape(slug)
    case_count = len(store.list_cases())
    safe_slug = escape(slug)
    return (
        f"<a class='project-card' href='/projects/{safe_slug}'>"
        f"<span class='name'>{name}</span>"
        f"<span class='meta'>{case_count} case{'s' if case_count != 1 else ''}</span></a>"
    )


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    slugs = _project_slugs()
    header = (
        "<div class='page-header'><div><h1>Projects</h1>"
        "<p class='subtitle'>Onboard a product once, then let AutoTester keep watching it.</p>"
        "</div><a class='btn btn-primary' href='/onboard'>+ New project</a></div>"
    )
    if not slugs:
        body = header + theme.empty_state(
            "🧪", "No projects yet — onboard your first one to get started.",
            "<a class='btn btn-primary' href='/onboard'>+ New project</a>",
        )
    else:
        cards = "".join(_project_card(s) for s in slugs)
        body = header + f"<div class='project-grid'>{cards}</div>"
    return theme.page("Projects", body)


@app.get("/onboard", response_class=HTMLResponse)
def onboard_form() -> str:
    fields = (
        "<div class='field'><label for='slug'>Slug</label>"
        "<input id='slug' name='slug' placeholder='my-product' required>"
        "<span class='hint'>lowercase letters, digits and hyphens — "
        "becomes the folder name</span></div>"
        "<div class='field'><label for='name'>Name</label>"
        "<input id='name' name='name' placeholder='My Product' required></div>"
        "<div class='field'><label for='base_url'>Base URL</label>"
        "<input id='base_url' name='base_url' "
        "placeholder='https://app.example.com/signin' required></div>"
        "<div class='field'><label for='allowed_domains'>Allowed domains</label>"
        "<input id='allowed_domains' name='allowed_domains' "
        "placeholder='example.com, app.example.com' required>"
        "<span class='hint'>comma-separated — the browser will never navigate "
        "outside these</span></div>"
        "<button class='btn btn-primary' type='submit'>Create project</button>"
    )
    form = f"<form method='post' action='/onboard'>{fields}</form>"
    body = (
        "<div class='breadcrumb'><a href='/'>Projects</a> / Onboard</div>"
        "<h1>Onboard a project</h1>"
        "<p class='subtitle'>This creates a project record — "
        "nothing is tested until you add cases.</p>"
        f"{theme.card(form)}"
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
    review_tone = ("positive" if review == "approved"
                   else "warning" if spec is not None else "neutral")
    safe_slug = escape(slug)
    name = escape(project.name)
    stats = (
        "<div class='stat-row'>"
        + theme.stat(str(len(store.list_cases())), "Cases")
        + theme.stat(str(len(project.allowed_domains)), "Allowed domain(s)")
        + "</div>"
    )
    actions = theme.card(
        "<p class='subtitle' style='margin-bottom:1rem'>Manage this project.</p>"
        "<div class='card-actions'>"
        f"<a class='btn' href='/projects/{safe_slug}/env'>🔑 Credentials</a>"
        f"<a class='btn' href='/projects/{safe_slug}/report'>📋 Latest report</a>"
        "<a class='btn' href='/live'>▶ Watch live</a>"
        "</div>",
        title="Actions",
    )
    body = (
        "<div class='breadcrumb'><a href='/'>Projects</a> / " + name + "</div>"
        f"<h1>{name}</h1>"
        f"<p class='subtitle'>{escape(project.base_url)} &middot; review: "
        f"{theme.pill(escape(review), review_tone)}</p>"
        f"{stats}{actions}"
    )
    return theme.page(name, body)


@app.get("/projects/{slug}/env", response_class=HTMLResponse)
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
        f"<h1>Credentials</h1>"
        "<p class='subtitle'>Values are never shown once saved — only whether one is set.</p>"
        f"{theme.card(table)}"
    )
    return theme.page(f"{name} — credentials", body)


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
    safe_slug = escape(slug)
    safe_run_id = escape(run_id)
    verdicts = {v.case_id: v for v in store.load_verdicts(run_id)}
    def _result_cell(case_id: str) -> str:
        return theme.badge(escape(verdicts[case_id].result.value)) if case_id in verdicts else "-"

    results = store.load_results(run_id)
    rows = "".join(
        f"<tr><td><code>{escape(r.case_id)}</code></td><td>{escape(r.outcome.value)}</td>"
        f"<td>{_result_cell(r.case_id)}</td></tr>"
        for r in results
    )
    table = (theme.empty_state("📭", "No case results in this run yet.") if not results else
             f"<table><tr><th>Case</th><th>Outcome</th><th>Result</th></tr>{rows}</table>")
    body = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Run</div>"
        f"<h1>Run <code>{safe_run_id}</code></h1>"
        f"{theme.card(table)}"
    )
    return theme.page(f"Run {safe_run_id}", body)


@app.get("/projects/{slug}/report", response_class=HTMLResponse)
def report(slug: str) -> str:
    _store, _project = _load_project_or_404(slug)
    safe_slug = escape(slug)
    breadcrumb = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Report</div>"
    )
    paths = ProjectPaths(slug)
    run_ids = sorted(p.name for p in paths.runs_dir.iterdir() if p.is_dir()) \
        if paths.runs_dir.exists() else []
    if not run_ids:
        body = breadcrumb + "<h1>Report</h1>" + theme.empty_state(
            "📋", "no runs yet — run a case against this project to see a report here.",
        )
        return theme.page("Report", body)
    store = ProjectStore(slug)
    counts: dict[str, int] = {}
    for verdict in store.load_verdicts(run_ids[-1]):
        counts[verdict.result.value] = counts.get(verdict.result.value, 0) + 1
    stats = "<div class='stat-row'>" + "".join(
        theme.stat(str(v), theme.badge(escape(k))) for k, v in counts.items()
    ) + "</div>"
    safe_run_id = escape(run_ids[-1])
    body = (
        breadcrumb + f"<h1>Latest report</h1>"
        f"<p class='subtitle'>Run <code>{safe_run_id}</code> · "
        f"<a href='/projects/{safe_slug}/runs/{safe_run_id}'>view case-by-case</a></p>"
        f"{stats}"
    )
    return theme.page(f"Report — {safe_run_id}", body)


@app.get("/live", response_class=HTMLResponse)
def live_view() -> str:
    """Presentation-only: an embedded noVNC viewer onto the container's virtual
    display. Reads no project state, triggers no run (qa/contracts/docker.md D4)."""
    example = "docker compose exec autotester uv run python scripts/regression_proof.py"
    body = (
        "<div class='breadcrumb'><a href='/'>Projects</a> / Live view</div>"
        "<h1>Live view</h1>"
        "<p class='subtitle'>Watch the real browser as a run happens — nothing is running "
        "here yet unless you start one.</p>"
        f"<div class='live-tip'>▶ Start a run from a script, e.g. <code>{example}</code>, "
        "while this page is open.</div>"
        "<div class='live-shell'>"
        "<iframe src='http://localhost:6080/vnc.html?autoconnect=true&resize=scale'></iframe>"
        "</div>"
    )
    return theme.page("Live view", body)
