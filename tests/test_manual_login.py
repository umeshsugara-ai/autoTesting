"""Manual one-time login. Contract: qa/contracts/manual-login.md ML1-ML5.

No real browser is launched here -- `BrowserSession.start`/`goto`/`close` are
monkeypatched so this exercises manual_login()'s own logic (no secret read,
blocks on the human signal, always closes) without Playwright.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.schema.project import Project, SecretRef
from autotester.stages.manual_login import manual_login


def make_project(with_password_secret: bool = False) -> Project:
    secrets = [SecretRef(key="APP_PASSWORD", domains=["app.test"])] if with_password_secret else []
    return Project(
        slug="app", name="App", base_url="https://app.test/login",
        allowed_domains=["app.test"], secrets=secrets,
    )


def _patch_session(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    calls: dict[str, list] = {"start": [], "goto": [], "close": []}

    def fake_start(self: BrowserSession) -> BrowserSession:
        calls["start"].append(True)
        return self

    def fake_goto(self: BrowserSession, url: str) -> None:
        calls["goto"].append(url)

    def fake_close(self: BrowserSession) -> None:
        calls["close"].append(True)

    monkeypatch.setattr(BrowserSession, "start", fake_start)
    monkeypatch.setattr(BrowserSession, "goto", fake_goto)
    monkeypatch.setattr(BrowserSession, "close", fake_close)
    return calls


def test_manual_login_reads_no_secret_even_when_one_is_declared_but_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ML1: a declared-but-unfilled secret must never block manual login --
    SecretStore.load(strict=False) is the mechanism that makes this true."""
    calls = _patch_session(monkeypatch)
    project = make_project(with_password_secret=True)  # declared, but no .env value exists
    paths = ProjectPaths(project.slug, tmp_path)

    manual_login(project, paths, wait_for_human=lambda prompt: None)

    assert calls["start"] and calls["close"]


def test_manual_login_navigates_to_the_base_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _patch_session(monkeypatch)
    project = make_project()
    paths = ProjectPaths(project.slug, tmp_path)

    manual_login(project, paths, wait_for_human=lambda prompt: None)

    assert calls["goto"] == ["https://app.test/login"]


def test_manual_login_blocks_on_the_human_signal_before_continuing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ML2: no fixed sleep -- the wait_for_human callable is the only gate,
    and it runs strictly between goto and close."""
    order: list[str] = []
    monkeypatch.setattr(BrowserSession, "start", lambda self: (order.append("start"), self)[1])
    monkeypatch.setattr(BrowserSession, "goto", lambda self, url: order.append("goto"))
    monkeypatch.setattr(BrowserSession, "close", lambda self: order.append("close"))
    project = make_project()
    paths = ProjectPaths(project.slug, tmp_path)

    def waiting(prompt: str) -> None:
        order.append("wait")
        assert "Log in by hand" in prompt

    manual_login(project, paths, wait_for_human=waiting)

    assert order == ["start", "goto", "wait", "close"]


def test_manual_login_still_closes_if_the_human_wait_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The browser must never be left dangling even if something interrupts
    the wait (e.g. Ctrl-C) -- close() is in a finally."""
    calls = _patch_session(monkeypatch)
    project = make_project()
    paths = ProjectPaths(project.slug, tmp_path)

    def boom(prompt: str) -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        manual_login(project, paths, wait_for_human=boom)

    assert calls["close"]
