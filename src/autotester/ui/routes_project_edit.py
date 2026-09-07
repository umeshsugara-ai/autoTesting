"""Edit a project's own settings after onboarding. Contract: qa/contracts/ui.md.

AT-058: getting the allowed domains wrong once made a project permanently
unrunnable, and there was no route anywhere to change them — `routes_credentials`
edits `.env` values only, never `project.json`. So a user who mistyped at
onboarding had to either abandon the project or edit JSON by hand.

Only the three fields a human can get wrong at onboarding are editable here:
name, base_url, allowed_domains. The slug is the project's identity (it names
the directory every artifact already lives under) and is deliberately NOT
editable — renaming it would orphan runs, cases and the browser profile.
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404, _require_reachable_base_url

router = APIRouter()


@router.get("/projects/{slug}/edit", response_class=HTMLResponse)
def edit_project_form(slug: str) -> str:
    _store, project = _load_project_or_404(slug)
    safe_slug = escape(slug)
    name = escape(project.name)
    fields = (
        "<div class='field'><label for='name'>Name</label>"
        f"<input id='name' name='name' value='{name}' required></div>"
        "<div class='field'><label for='base_url'>Base URL</label>"
        f"<input id='base_url' name='base_url' value='{escape(project.base_url)}' required>"
        "<span class='hint'>where a run starts — its host must be covered below</span></div>"
        "<div class='field'><label for='allowed_domains'>Allowed domains</label>"
        "<input id='allowed_domains' name='allowed_domains' "
        f"value='{escape(', '.join(project.allowed_domains))}' required>"
        "<span class='hint'>comma-separated — the browser will never navigate outside "
        "these. There is no wildcard: name every host you mean.</span></div>"
        "<button class='btn btn-primary' type='submit'>Save changes</button>"
    )
    form = f"<form method='post' action='/projects/{safe_slug}/edit'>{fields}</form>"
    body = (
        theme.breadcrumb(("Projects", "/"), (name, f"/projects/{safe_slug}"),
                          ("Settings", None))
        + "<h1>Project settings</h1>"
        "<p class='subtitle'>The slug never changes — every run, case and browser profile "
        "is filed under it.</p>"
        f"{theme.card(form)}"
    )
    return theme.page("Project settings", body, active_slug=slug)


@router.post("/projects/{slug}/edit")
def edit_project_submit(
    slug: str,
    name: str = Form(...),
    base_url: str = Form(...),
    allowed_domains: str = Form(...),
) -> RedirectResponse:
    store, project = _load_project_or_404(slug)
    if not name.strip():
        raise HTTPException(400, "a project needs a name")
    domains = [d.strip() for d in allowed_domains.split(",") if d.strip()]
    if not domains:
        raise HTTPException(400, "a project needs at least one allowed domain")
    _require_reachable_base_url(base_url, domains)

    store.save_project(project.model_copy(update={
        "name": name.strip(), "base_url": base_url.strip(), "allowed_domains": domains,
    }))
    return RedirectResponse(f"/projects/{slug}", status_code=303)
