"""Which case a crawl logs in with — declared once on the project, shown before a crawl (X17).

Found by Umesh, 2026-09-16: "abhi tho hmara testing flow login k baad hi ruk jata hi".
Every crawl on disk had stopped at or before the login page, because the UI Explore route
never handed `run_crawl` a login case and `Project` had nowhere to name one. The explorer
already knew how to log in (`stages.explore._bootstrap_login`, X10); this module is the
single declaration it reads, and the notice that says so before anyone presses Explore.
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from autotester.schema.case import Case
from autotester.schema.project import Project
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404

router = APIRouter()


def login_card(slug: str, project: Project, cases: list[Case]) -> str:
    """What the next crawl will log in with, and the form that changes it.

    With nothing declared the card says, before the crawl starts, that the crawl will see
    only what a signed-out visitor sees — the stuck-at-login run was silent before."""
    safe = escape(slug)
    declared = next((c for c in cases if c.id == project.login_case_id), None)
    if declared is not None:
        status = (f"<p>{theme.pill('✓ Logs in first', 'positive')} Crawls log in with "
                  f"<strong>{escape(declared.title)}</strong> before exploring.</p>")
    elif project.login_case_id:
        status = ("<p>The declared login case no longer exists — a crawl will be refused "
                  "until another one is declared.</p>")
    else:
        status = ("<p><strong>No login case declared.</strong> A crawl will only see pages "
                  "a signed-out visitor can open — for a product behind a login, that is "
                  "the login page alone.</p>")
    options = "".join(
        f"<option value='{escape(c.id)}'"
        f"{' selected' if c.id == project.login_case_id else ''}>{escape(c.title)}</option>"
        for c in cases
    )
    form = (
        f"<form method='post' action='/projects/{safe}/login-case'>"
        "<div class='field'><label>Log in first with</label><select name='case_id'>"
        f"<option value=''>No login — the product is public</option>{options}</select></div>"
        "<button type='submit'>Save login for crawls</button></form>"
    )
    card = theme.card(status + form, title="Login for crawls")
    return f"<section id='crawl-login'>{card}</section>"


def _refusal(slug: str, detail: str) -> HTMLResponse:
    safe = escape(slug)
    body = theme.breadcrumb(
        ("Projects", "/"), (safe, f"/projects/{safe}"), ("Crawls", f"/projects/{safe}/crawls"),
        ("Login for crawls", None),
    ) + "<h1>Login case not saved</h1>" + theme.card(
        f"<p>{escape(detail)}</p><p><a class='btn' href='/projects/{safe}/crawls#crawl-login'>"
        "Back to crawls</a></p>",
    )
    return HTMLResponse(theme.page("Login case not saved", body, active_slug=slug), status_code=400)


@router.post("/projects/{slug}/login-case")
def declare_login_case(slug: str, case_id: str = Form("")) -> Response:
    """Declare (or clear, with an empty value) the project's login case. The submitted id is
    never echoed: it came from the request, and a stale or tampered one says nothing useful."""
    store, project = _load_project_or_404(slug)
    chosen = case_id.strip() or None
    if chosen is not None and store.get_case(chosen) is None:
        return _refusal(slug, "that is not one of this project's cases")
    store.save_project(project.model_copy(update={"login_case_id": chosen}))
    return RedirectResponse(f"/projects/{slug}/crawls#crawl-login", status_code=303)
