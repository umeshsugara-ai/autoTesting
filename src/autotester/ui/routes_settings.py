"""Global AI/API provider keys. Contract: qa/contracts/ui-settings.md US1-US4.
A different concept from a project's own `SecretRef`s (routes_credentials.py):
these are read straight from `os.environ` by `providers/langchain_fallback.py`
and `providers/gemini.py`, not scoped to any one project.
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.browser.secrets import parse_env
from autotester.core.paths import repo_root
from autotester.ui import theme
from autotester.ui.env_editor import InvalidEnvValue, set_env_value

router = APIRouter()

# The complete, closed set this page manages (US1) -- a new provider key is a
# code change here, not a dynamic field.
_PROVIDER_KEYS = (
    "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
    "OLLAMA_BASE_URL", "OLLAMA_MODEL", "OPENAI_API_KEY",
)


def _present_keys() -> dict[str, str]:
    env_path = repo_root() / ".env"
    return parse_env(env_path.read_text(encoding="utf-8")) if env_path.exists() else {}


@router.get("/settings/providers", response_class=HTMLResponse)
def provider_settings_view() -> str:
    present = _present_keys()

    def _status_cell(key: str) -> str:
        return (theme.pill("● Set", "positive") if present.get(key)
                else theme.pill("○ Not set", "neutral"))

    rows = "".join(
        f"<tr><td><code>{escape(key)}</code></td>"
        f"<td>{_status_cell(key)}</td>"
        f"<form method='post' action='/settings/providers'>"
        f"<input type='hidden' name='key' value='{escape(key)}'>"
        "<td><input type='password' name='value' placeholder='new value'></td>"
        "<td><button class='btn btn-sm' type='submit'>Save</button></td></form></tr>"
        for key in _PROVIDER_KEYS
    )
    table = f"<table><tr><th>Key</th><th>Status</th><th>New value</th><th></th></tr>{rows}</table>"
    body = (
        "<div class='breadcrumb'><a href='/'>Projects</a> / Settings</div>"
        "<h1>Provider settings</h1>"
        "<p class='subtitle'>Global AI/API keys every project's grading and agent steps fall "
        "back through. Values are never shown once saved — only whether one is set.</p>"
        f"{theme.card(table)}"
    )
    return theme.page("Settings", body)


@router.post("/settings/providers")
def provider_settings_submit(key: str = Form(...), value: str = Form(...)) -> RedirectResponse:
    if key not in _PROVIDER_KEYS:
        raise HTTPException(400, f"'{key}' is not a known provider setting")
    try:
        set_env_value(repo_root() / ".env", key, value)
    except InvalidEnvValue as exc:
        raise HTTPException(400, str(exc)) from exc
    return RedirectResponse("/settings/providers", status_code=303)
