"""Thin FastAPI viewer/editor over project files. Design principle 8: never a
second source of truth — every route reads/writes through `ProjectStore`/
`SecretStore` exactly like the CLI does. Contract: qa/contracts/ui.md U1-U5.
The run trigger lives in `ui/routes_runs.py`, run history/report/downloads in
`ui/routes_report.py`, the credentials editor in `ui/routes_credentials.py` —
this module keeps only the project-list, onboarding and live-view pages.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from html import escape

from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.core.paths import repo_root
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore
from autotester.ui import (
    routes_credentials,
    routes_flow_diagram,
    routes_report,
    routes_runs,
    routes_settings,
    theme,
)
from autotester.ui.helpers import _load_project_or_404, _project_slugs, _require_slug

__all__ = ["_require_slug", "app"]


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Same convention as every real-run script (e.g.
    scripts/run_pathlynks_first_cases.py) -- a plain `uvicorn`/docker process never
    sources .env on its own, so global provider keys (ANTHROPIC_API_KEY etc.) would
    otherwise be invisible to LangChainFallbackProvider() even though the file is
    present on disk. A startup hook, not a module-level call, so TestClient(app)
    (which never runs lifespan unless used as a context manager) never leaks real
    .env values into the test process."""
    load_dotenv(repo_root() / ".env")
    yield


app = FastAPI(title="AutoTester", lifespan=_lifespan)
app.include_router(routes_runs.router)
app.include_router(routes_report.router)
app.include_router(routes_flow_diagram.router)
app.include_router(routes_credentials.router)
app.include_router(routes_settings.router)


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
    case_count = len(store.list_cases())
    stats = (
        "<div class='stat-row'>"
        + theme.stat(str(case_count), "Cases")
        + theme.stat(str(len(project.allowed_domains)), "Allowed domain(s)")
        + "</div>"
    )
    run_button = (
        f"<form method='post' action='/projects/{safe_slug}/run' style='display:inline'>"
        "<button class='btn btn-primary' type='submit'>▶ Run tests</button></form>"
        if case_count else
        "<span class='btn' style='opacity:.5;cursor:default' title='no cases yet'>"
        "▶ Run tests</span>"
    )
    actions = theme.card(
        "<p class='subtitle' style='margin-bottom:1rem'>Manage this project.</p>"
        "<div class='card-actions'>"
        f"{run_button}"
        f"<a class='btn' href='/projects/{safe_slug}/env'>🔑 Credentials</a>"
        f"<a class='btn' href='/projects/{safe_slug}/report'>📋 Latest report</a>"
        f"<a class='btn' href='/projects/{safe_slug}/flow-diagram'>🌳 Flow diagram</a>"
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
