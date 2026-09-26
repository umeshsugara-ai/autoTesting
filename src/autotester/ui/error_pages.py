"""App-wide `HTTPException` -> HTML page, split out of `ui/app.py` to keep that
module under the 300-line design cap. Contract: qa/contracts/ui.md U5.

AT-596: `app.py` registered no exception handler, so every `HTTPException`
raised anywhere under it (400s, 404s, T-184's pinned-case 409) fell through
FastAPI's default handler as a raw `{"detail": ...}` JSON body -- Chrome
renders that as its own built-in JSON viewer: no styling, no nav, no link
back. A browser-driving request (`Accept: text/html`, what every real browser
sends) now gets a page in this app's own visual language instead; a
JSON/API caller -- every existing test that never sets `Accept` gets `*/*`
from httpx, and every fetch that asks for `application/json` -- keeps the
exact JSON body FastAPI already produced, via FastAPI's own default handler,
so no status code, header or JSON shape changes for that caller.
"""

from __future__ import annotations

from html import escape
from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler as _default_json_handler
from fastapi.responses import HTMLResponse, Response
from fastapi.utils import is_body_allowed_for_status_code

from autotester.browser.secrets import parse_env
from autotester.core.env import ENV_FILE
from autotester.core.paths import repo_root
from autotester.core.redact import Redactor
from autotester.ui import theme


def _repo_redactor() -> Redactor:
    """Every value currently in the repo-root `.env`, keyed by name -- the
    same file `ProjectPaths(<any slug>).env_file` resolves to (\"one
    credential file for the whole repo,\" core/paths.py) and the same
    shared-.env matching U9 already requires of the credential guard. Reused
    here rather than a project-scoped `SecretStore` because an app-wide error
    page has no single project in scope to load one from."""
    path = repo_root() / ENV_FILE
    if not path.exists():
        return Redactor({})
    return Redactor(parse_env(path.read_text(encoding="utf-8")))


def _wants_html(request: Request) -> bool:
    """Every real browser sends `Accept: text/html,...`; a JSON/API client
    that asks for `application/json`, or sends no `Accept` at all (httpx's
    `*/*` default -- every pre-existing test), does not."""
    return "text/html" in request.headers.get("accept", "")


def _status_title(status_code: int) -> str:
    try:
        return f"{status_code} {HTTPStatus(status_code).phrase}"
    except ValueError:
        return str(status_code)


def _error_page(status_code: int, detail: str) -> HTMLResponse:
    """The themed page. `detail` is redacted before it is escaped -- redact
    first, since scrubbing an already-escaped string would need to match
    against escaped secret values instead of the real ones."""
    title = _status_title(status_code)
    safe_detail = escape(_repo_redactor().scrub(detail))
    body = theme.card(
        f"<p>{safe_detail}</p>"
        "<p style='margin-top:14px'><a class='btn' href='/'>&larr; Back to projects</a></p>",
        title=title,
    )
    return HTMLResponse(theme.page(title, body), status_code=status_code)


async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Registered for every route in `app.py`'s routers (`FastAPI.
    add_exception_handler` applies globally, not per-router)."""
    if not _wants_html(request):
        return await _default_json_handler(request, exc)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=exc.headers)
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_page(exc.status_code, detail)


def register_exception_handler(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
