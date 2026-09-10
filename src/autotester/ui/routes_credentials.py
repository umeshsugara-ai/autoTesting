"""The masked .env editor. Contract: qa/contracts/ui.md U3 — a real value is
never rendered once saved, only whether one is set.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from html import escape
from math import isfinite

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from autotester.browser.secrets import SecretStore, parse_env
from autotester.core.paths import ProjectPaths, repo_root
from autotester.schema.approval import RunApproval
from autotester.schema.enums import ApprovalKind
from autotester.ui import theme
from autotester.ui.env_editor import InvalidEnvValue, set_env_value
from autotester.ui.helpers import _load_project_or_404, _refuse_unsafe_submission

router = APIRouter()


def _crawl_approval_form(slug: str, target: str) -> str:
    """Human-readable counterpart to the CLI-only crawl approval command."""
    safe = escape(slug)
    form = (
        f"<p>This approval applies only to <code>{escape(target)}</code>.</p>"
        f"<form method='post' action='/projects/{safe}/crawl-approval'>"
        "<div class='field'><label>Signed by</label>"
        "<input name='granted_by' required placeholder='your name'></div>"
        "<div class='field'><label>Scope</label>"
        "<input name='scope' required placeholder='what this crawl may read and click'></div>"
        "<div class='field'><label>Expires at</label>"
        "<input type='datetime-local' name='expires_at' required></div>"
        "<div class='field'><label>UTC offset in minutes (auto-detected)</label>"
        "<input type='number' id='crawl-timezone-offset' name='timezone_offset_minutes' "
        "min='-840' max='840' value='0' required></div>"
        "<script>const expiry=document.querySelector(\"[name='expires_at']\");"
        "const offset=document.getElementById('crawl-timezone-offset');"
        "const syncOffset=()=>{const selected=new Date(expiry.value);"
        "if(!Number.isNaN(selected.valueOf()))offset.value="
        "String(-selected.getTimezoneOffset());};"
        "expiry.addEventListener('change',syncOffset);"
        "expiry.form.addEventListener('submit',syncOffset);</script>"
        "<div class='field'><label>Maximum actions</label>"
        "<input type='number' name='max_actions' min='1' value='200' required></div>"
        "<div class='field'><label>Wall clock (seconds)</label>"
        "<input type='number' name='wall_clock_s' min='1' step='any' value='600' required></div>"
        "<div class='field'><label>Note (optional)</label>"
        "<input name='note' placeholder='why this crawl is approved'></div>"
        "<button type='submit'>Save crawl approval</button></form>"
    )
    return f"<section id='crawl-approval'>{theme.card(form, title='Approve a crawl')}</section>"


def _approval_error(slug: str, detail: str) -> HTMLResponse:
    safe = escape(slug)
    body = theme.breadcrumb(
        ("Projects", "/"), (safe, f"/projects/{safe}"), ("Credentials", None),
    ) + "<h1>Crawl approval not saved</h1>" + theme.card(
        f"<p>{escape(detail)}</p><p><a class='btn' href='/projects/{safe}/env#crawl-approval'>"
        "Return to crawl approval</a></p>", title="Check the approval details",
    )
    return HTMLResponse(
        theme.page("Crawl approval not saved", body, active_slug=slug), status_code=400,
    )


def _future_iso(value: str, offset_minutes: int) -> str:
    text = value.strip()
    try:
        expiry = datetime.fromisoformat(text)
    except ValueError:
        raise HTTPException(400, "expiry must be an ISO date and time") from None
    if "T" not in text:
        raise HTTPException(400, "expiry must include an ISO date and time")
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone(timedelta(minutes=offset_minutes)))
    expiry = expiry.astimezone(UTC)
    if expiry <= datetime.now(UTC):
        raise HTTPException(400, "expiry must be in the future")
    return expiry.isoformat()


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
        theme.breadcrumb(
            ("Projects", "/"), (name, f"/projects/{safe_slug}"), ("Credentials", None),
        )
        + "<h1>Credentials</h1>"
        "<p class='subtitle'>Values are never shown once saved — only whether one is set.</p>"
        f"{theme.card(table)}"
        f"{_crawl_approval_form(slug, project.base_url)}"
    )
    return theme.page(f"{name} — credentials", body, active_slug=slug)


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


@router.post("/projects/{slug}/crawl-approval")
def crawl_approval_submit(
    slug: str, granted_by: str = Form(""), scope: str = Form(""),
    expires_at: str = Form(""), max_actions: str = Form(""),
    wall_clock_s: str = Form(""), timezone_offset_minutes: str = Form("0"),
    note: str = Form(""),
) -> Response:
    """Persist one bounded approval; project and target always come from disk."""
    store, project = _load_project_or_404(slug)
    signer, allowed_scope = granted_by.strip(), scope.strip()
    try:
        if not signer or not allowed_scope:
            raise HTTPException(400, "crawl approval requires a signer and scope")
        secrets = SecretStore.load(project, ProjectPaths(slug).env_file, strict=False)
        _refuse_unsafe_submission([
            ("signer", signer), ("scope", allowed_scope), ("expiry", expires_at),
            ("maximum actions", max_actions), ("wall clock", wall_clock_s),
            ("timezone offset", timezone_offset_minutes), ("note", note),
        ], project, secrets)
        actions, seconds = int(max_actions), float(wall_clock_s)
        offset = int(timezone_offset_minutes)
        if actions <= 0 or seconds <= 0 or not isfinite(seconds):
            raise HTTPException(400, "crawl approval bounds must be positive")
        if not -840 <= offset <= 840:
            raise HTTPException(400, "timezone offset must be between -840 and 840 minutes")
        expiry = _future_iso(expires_at, offset)
    except ValueError:
        return _approval_error(slug, "crawl bounds must be numbers")
    except HTTPException as exc:
        return _approval_error(slug, str(exc.detail))
    now = datetime.now(UTC).isoformat()
    store.add_approval(RunApproval(
        project=project.slug, run_kind=ApprovalKind.CRAWL, target=project.base_url,
        scope=allowed_scope, max_actions=actions, wall_clock_s=seconds,
        granted_by=signer, granted_at=now, expires_at=expiry,
        note=note.strip() or None,
    ))
    return RedirectResponse(f"/projects/{slug}/env#crawl-approval", status_code=303)
