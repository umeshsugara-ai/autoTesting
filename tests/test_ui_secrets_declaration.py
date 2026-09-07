"""Declaring a project's credentials from the UI. Contract: qa/contracts/ui.md.

Track 0 / AT-068: nothing anywhere wrote `project.json::secrets`, so every
project declared zero credentials — `/projects/<slug>/env` rendered "This
project declares no credentials" and 400d every save. Setting up a logged-in
test through the UI was therefore impossible. These tests hold that path open,
and hold the line that a SecretRef never carries a value.
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


def _onboard(client: TestClient) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    })


def _declare(client: TestClient, **overrides: str):
    data = {"key": "DEMO_PASSWORD", "domains": "demo.test",
            "description": "the test account password", "mask_in_screenshot": "on"}
    data.update(overrides)
    return client.post("/projects/demo/secrets", data=data, follow_redirects=False)


def test_declaring_a_credential_persists_a_real_secretref(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)

    response = _declare(client)

    assert response.status_code == 303
    project = ProjectStore("demo", scratch_root).load_project()
    assert [r.key for r in project.secrets] == ["DEMO_PASSWORD"]
    ref = project.secrets[0]
    assert ref.domains == ["demo.test"]
    assert ref.mask_in_screenshot is True
    assert ref.description == "the test account password"


def test_declaring_makes_the_credentials_page_usable(
    client: TestClient, scratch_root: Path
) -> None:
    """The whole point: before this, /env said "declares no credentials" and
    refused every key, so a value could not be stored at all."""
    _onboard(client)
    before = client.get("/projects/demo/env")
    assert "declares no credentials" in before.text

    _declare(client)

    after = client.get("/projects/demo/env")
    assert "DEMO_PASSWORD" in after.text
    assert "declares no credentials" not in after.text


def test_the_declaration_form_never_accepts_or_stores_a_value(
    client: TestClient, scratch_root: Path
) -> None:
    """A SecretRef holds a key and a scope, never a value. Posting an extra
    `value` field must be inert, not persisted anywhere."""
    _onboard(client)

    _declare(client, value="hunter2")  # type: ignore[arg-type]

    project = ProjectStore("demo", scratch_root).load_project()
    assert "hunter2" not in project.model_dump_json()


def test_a_key_that_looks_like_a_value_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """SecretRef's own _reject_value_like validator, surfaced as a readable 400
    instead of a 500."""
    _onboard(client)

    response = _declare(client, key="A" * 65)

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).load_project().secrets == []


def test_a_lowercase_key_is_refused(client: TestClient, scratch_root: Path) -> None:
    _onboard(client)

    response = _declare(client, key="demo_password")

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).load_project().secrets == []


def test_a_credential_with_no_scope_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """SecretRef itself allows an empty domains list, but such a key can never
    resolve anywhere — it would fail only at typing time. Refuse it up front."""
    _onboard(client)

    response = _declare(client, domains="  ,  ")

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).load_project().secrets == []


def test_declaring_the_same_key_twice_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)
    _declare(client)

    response = _declare(client, description="a second go")

    assert response.status_code == 400
    assert len(ProjectStore("demo", scratch_root).load_project().secrets) == 1


def test_the_form_defaults_the_scope_to_the_projects_allowed_domains(
    client: TestClient, scratch_root: Path
) -> None:
    """A credential typed into a host the browser may not even visit is a
    mistake waiting to happen, so the scope arrives prefilled."""
    _onboard(client)

    response = client.get("/projects/demo/edit")

    assert response.status_code == 200
    assert "value='demo.test'" in response.text


def test_removing_a_credential_leaves_the_others(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)
    _declare(client, key="DEMO_EMAIL")
    _declare(client, key="DEMO_PASSWORD")

    response = client.post("/projects/demo/secrets/DEMO_EMAIL/delete", follow_redirects=False)

    assert response.status_code == 303
    project = ProjectStore("demo", scratch_root).load_project()
    assert [r.key for r in project.secrets] == ["DEMO_PASSWORD"]


def test_removing_an_undeclared_credential_is_404(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)

    response = client.post("/projects/demo/secrets/NOPE/delete")

    assert response.status_code == 404


def test_declaring_on_an_unknown_project_is_404(
    client: TestClient, scratch_root: Path
) -> None:
    response = client.post("/projects/nope/secrets", data={
        "key": "X_KEY", "domains": "x.test",
    })

    assert response.status_code == 404
