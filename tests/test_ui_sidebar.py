"""Persistent project sidebar. Contract: qa/contracts/ui-sidebar.md US1-US5."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _onboard(client: TestClient, slug: str, name: str) -> None:
    client.post("/onboard", data={
        "slug": slug, "name": name, "base_url": f"https://{slug}.test",
        "allowed_domains": f"{slug}.test",
    })


def test_sidebar_shows_an_honest_empty_state_with_no_projects(
    client: TestClient, scratch_root: Path
) -> None:
    response = client.get("/live")
    assert "No projects yet" in response.text
    assert "sidebar" in response.text


def test_sidebar_lists_every_onboarded_project_by_its_real_name(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client, "alpha", "Alpha Product")
    _onboard(client, "beta", "Beta Product")

    response = client.get("/live")

    assert "Alpha Product" in response.text
    assert "Beta Product" in response.text
    assert "href='/projects/alpha'" in response.text
    assert "href='/projects/beta'" in response.text


def test_sidebar_appears_on_every_page_not_just_the_homepage(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client, "alpha", "Alpha Product")

    for path in ("/", "/onboard", "/live", "/projects/alpha", "/settings/providers"):
        response = client.get(path)
        assert "class='sidebar'" in response.text, path
        assert "Alpha Product" in response.text, path


def test_active_project_is_highlighted_on_its_own_pages(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client, "alpha", "Alpha Product")
    _onboard(client, "beta", "Beta Product")

    on_alpha = client.get("/projects/alpha").text
    on_beta = client.get("/projects/beta").text

    assert "sidebar-link active' href='/projects/alpha'" in on_alpha
    assert "sidebar-link active' href='/projects/beta'" not in on_alpha
    assert "sidebar-link active' href='/projects/beta'" in on_beta


def test_a_global_page_highlights_no_project(client: TestClient, scratch_root: Path) -> None:
    _onboard(client, "alpha", "Alpha Product")

    response = client.get("/live")

    assert "sidebar-link active'" not in response.text


def test_existing_page_content_is_unchanged_by_the_sidebar(
    client: TestClient, scratch_root: Path
) -> None:
    """ui-sidebar.md US5: a pure wrapper change -- no existing route's own
    body content changes."""
    _onboard(client, "alpha", "Alpha Product")

    response = client.get("/projects/alpha")

    assert response.status_code == 200
    assert "no cases yet" in response.text
    assert "Alpha Product" in response.text  # both the heading AND the sidebar entry
