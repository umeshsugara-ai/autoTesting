"""AT-076: a navigation target can itself be a `{{SECRET:KEY}}` placeholder.
Contract: qa/contracts/browser-and-secrets.md B2/B3.

Split from test_browser.py once that file passed doctor's 300-line cap —
`fill()`'s secret resolution stays there; `goto()`'s stays here.

Unlike `fill()` (always scoped to the CURRENT page host), a navigation
target can be the placeholder itself with no literal host around it — there
is nothing to scope by until AFTER substitution. `resolve_for_navigation`
flips the order: substitute, then check the resulting host against the
secret's own declared domains, then `session.goto` still runs
`check_destination` on the resolved value exactly as it would a plain URL.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_browser import LOGIN, FakePage

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession, NavigationRefused
from autotester.core.paths import ProjectPaths
from autotester.schema.project import Project, SecretRef

LOGIN_URL_VALUE = "https://app.pathlynks.test/login?token=xyz789"


def _session_with_secret_url(
    tmp_path: Path, *, key: str = "PATHLYNKS_LOGIN_URL", ref_domains: list[str] | None = None,
    project_domains: list[str] | None = None, value: str = LOGIN_URL_VALUE,
) -> BrowserSession:
    project = Project(
        slug="pathlynks", name="Pathlynks", base_url="https://app.pathlynks.test",
        allowed_domains=project_domains or ["pathlynks.test"],
        secrets=[SecretRef(key=key, domains=ref_domains or ["pathlynks.test"])],
    )
    env = tmp_path / ".env"
    env.write_text(f"{key}={value}\n", encoding="utf-8")
    store = SecretStore.load(project, env)
    paths = ProjectPaths("pathlynks", tmp_path)
    s = BrowserSession(project, store, tmp_path / "run", paths)
    s._page = FakePage(LOGIN)
    s.state.run_dir.mkdir(parents=True, exist_ok=True)
    return s


def test_goto_resolves_a_bare_secret_placeholder_navigation_target(tmp_path: Path) -> None:
    s = _session_with_secret_url(tmp_path)
    s.goto("{{SECRET:PATHLYNKS_LOGIN_URL}}")
    assert s.page.url == LOGIN_URL_VALUE
    assert "xyz789" not in " ".join(e.path for e in s.state.evidence)


def test_goto_resolves_a_secret_embedded_in_a_literal_url(tmp_path: Path) -> None:
    s = _session_with_secret_url(tmp_path)
    s.goto("https://app.pathlynks.test/sso?next={{SECRET:PATHLYNKS_LOGIN_URL}}")
    assert s.page.url == f"https://app.pathlynks.test/sso?next={LOGIN_URL_VALUE}"


def test_goto_still_refuses_a_resolved_destination_outside_project_domains(
    tmp_path: Path,
) -> None:
    """Per-secret domain scoping is not the only gate: `check_destination`
    still runs on the RESOLVED value exactly as it would a plain literal
    URL, so a secret whose own declared domains are wrong or stale cannot
    navigate the browser outside the project's allowed_domains."""
    s = _session_with_secret_url(
        tmp_path, key="ROGUE_URL", ref_domains=["evil.test"], value="https://evil.test/steal",
    )
    with pytest.raises(NavigationRefused):
        s.goto("{{SECRET:ROGUE_URL}}")
    assert s.page.url == LOGIN


def test_goto_refuses_a_secret_scoped_to_a_different_domain_than_it_resolves_to(
    tmp_path: Path,
) -> None:
    """The secret's OWN declared domains must cover the host its value
    actually resolves to — a stale or wrong domains list fails closed."""
    s = _session_with_secret_url(
        tmp_path, key="MISBOUND_URL", ref_domains=["not-the-login-host.test"],
    )
    with pytest.raises(Exception, match=re.escape("not-the-login-host.test")):
        s.goto("{{SECRET:MISBOUND_URL}}")
    assert s.page.url == LOGIN


def test_goto_passes_a_plain_url_through_unchanged(tmp_path: Path) -> None:
    s = _session_with_secret_url(tmp_path)
    s.goto("https://app.pathlynks.test/dashboard")
    assert s.page.url == "https://app.pathlynks.test/dashboard"
