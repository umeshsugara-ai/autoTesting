"""Onboarding validation + editing a project after the fact. Contract: qa/contracts/ui.md.

AT-058: Umesh typed "all" in Allowed domains meaning "allow everything". It was
stored verbatim as a literal domain named `all`, so the project was dead on
arrival — every run died at the first step with NavigationRefused, and there was
no route anywhere to fix it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _onboard(client: TestClient, **overrides: str):
    data = {
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    }
    data.update(overrides)
    return client.post("/onboard", data=data, follow_redirects=False)


# -- AT-058a: refuse an unrunnable project at onboarding, not mid-run ---------

def test_onboarding_refuses_domains_that_exclude_the_projects_own_base_url(
    client: TestClient, scratch_root: Path
) -> None:
    """The exact shape of the real incident: "all" is not a wildcard, it is a
    literal domain, so the project could never reach its own base URL."""
    response = _onboard(client, allowed_domains="all")

    assert response.status_code == 400
    assert "could never run" in response.text
    assert ProjectStore("demo", scratch_root).load_project() is None


def test_onboarding_error_names_the_host_the_user_must_add(
    client: TestClient, scratch_root: Path
) -> None:
    """A 400 the user cannot act on is barely better than the mid-run failure it
    replaces — the message must name the missing host."""
    response = _onboard(client, allowed_domains="all")

    assert "demo.test" in response.text


def test_onboarding_refuses_a_base_url_that_is_not_openable(
    client: TestClient, scratch_root: Path
) -> None:
    response = _onboard(client, base_url="not a url", allowed_domains="demo.test")

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).load_project() is None


def test_onboarding_still_accepts_a_subdomain_of_an_allowed_domain(
    client: TestClient, scratch_root: Path
) -> None:
    """The validator must not be stricter than the boundary it guards:
    Project.allows_domain already accepts subdomains, so app.demo.test under
    demo.test is legitimate and must still onboard."""
    response = _onboard(
        client, base_url="https://app.demo.test/signin", allowed_domains="demo.test"
    )

    assert response.status_code == 303
    assert ProjectStore("demo", scratch_root).load_project() is not None


# -- AT-058b: a project's own settings are editable afterwards ----------------

def test_edit_form_shows_the_projects_current_values(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)

    response = client.get("/projects/demo/edit")

    assert response.status_code == 200
    assert "https://demo.test/signin" in response.text
    assert "demo.test" in response.text


def test_editing_persists_new_domains_through_the_store(
    client: TestClient, scratch_root: Path
) -> None:
    """The recovery path the real incident had no route for."""
    _onboard(client)

    response = client.post("/projects/demo/edit", data={
        "name": "Demo Renamed", "base_url": "https://other.test/app",
        "allowed_domains": "other.test, www.other.test",
    }, follow_redirects=False)

    assert response.status_code == 303
    project = ProjectStore("demo", scratch_root).load_project()
    assert project is not None
    assert project.name == "Demo Renamed"
    assert project.base_url == "https://other.test/app"
    assert project.allowed_domains == ["other.test", "www.other.test"]
    assert project.slug == "demo"  # identity never changes


def test_editing_refuses_domains_that_would_strand_the_base_url(
    client: TestClient, scratch_root: Path
) -> None:
    """Editing must not be a back door around the onboarding check."""
    _onboard(client)

    response = client.post("/projects/demo/edit", data={
        "name": "Demo", "base_url": "https://demo.test/signin", "allowed_domains": "all",
    })

    assert response.status_code == 400
    project = ProjectStore("demo", scratch_root).load_project()
    assert project is not None
    assert project.allowed_domains == ["demo.test"]  # unchanged on disk


def test_editing_refuses_an_empty_domain_list(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)

    response = client.post("/projects/demo/edit", data={
        "name": "Demo", "base_url": "https://demo.test/signin", "allowed_domains": " , ",
    })

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).load_project().allowed_domains == ["demo.test"]


def test_editing_an_unknown_project_is_404(client: TestClient, scratch_root: Path) -> None:
    response = client.post("/projects/nope/edit", data={
        "name": "x", "base_url": "https://x.test", "allowed_domains": "x.test",
    })

    assert response.status_code == 404


def test_project_page_links_to_its_settings(client: TestClient, scratch_root: Path) -> None:
    _onboard(client)

    response = client.get("/projects/demo")

    assert "/projects/demo/edit" in response.text
