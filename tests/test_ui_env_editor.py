"""U3, the credentials editor: display, write, and the empty-save wipe guard.

Split from `test_ui.py` for the 300-line cap (2026-09-21). Contract:
qa/contracts/ui.md U3 as amended 2026-09-21 by Umesh (Approver): the stored
value renders INTO the field (prefilled, editable); password-shaped keys are
masked with a show/hide toggle; an empty Save is refused and never wipes.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.store.project_store import ProjectStore
from autotester.ui.app import app
from autotester.ui.env_editor import set_env_value


@pytest.fixture()
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# -- U3 the env editor never renders a real value -----------------------------

def test_env_editor_shows_the_stored_value_to_the_operator(
    client: TestClient, scratch_root: Path
) -> None:
    """2026-09-21 UX amendment (Umesh, Approver): the write-only editor read as
    'everything wipes on Save'. The stored value is now rendered INTO the field
    (prefilled) so the operator sees what is saved and can edit it; password-
    shaped keys are masked inputs with a show/hide toggle. The value still
    never reaches a prompt, log, or screenshot — that boundary is unchanged."""
    from autotester.schema.project import Project as ProjectModel
    from autotester.schema.project import SecretRef

    project = ProjectModel(
        slug="demo", name="Demo", base_url="https://demo.test", allowed_domains=["demo.test"],
        secrets=[SecretRef(key="DEMO_EMAIL", domains=["demo.test"]),
                 SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])],
    )
    ProjectStore("demo", scratch_root).save_project(project)
    set_env_value(scratch_root / ".env", "DEMO_EMAIL", "ops@demo.test")
    set_env_value(scratch_root / ".env", "DEMO_PASSWORD", "s3cr3t-real-value")

    response = client.get("/projects/demo/env")

    assert response.status_code == 200
    # non-password key: the value is visible and editable
    assert "value='ops@demo.test'" in response.text
    # password key: masked input carrying the value, with a show/hide toggle
    assert "type='password' name='value' value='s3cr3t-real-value'" in response.text
    assert "i.type=i.type==='password'?'text':'password'" in response.text


def test_env_editor_writes_a_new_value_via_post(client: TestClient, scratch_root: Path) -> None:
    from autotester.schema.project import Project as ProjectModel
    from autotester.schema.project import SecretRef

    project = ProjectModel(
        slug="demo", name="Demo", base_url="https://demo.test", allowed_domains=["demo.test"],
        secrets=[SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])],
    )
    ProjectStore("demo", scratch_root).save_project(project)

    response = client.post(
        "/projects/demo/env", data={"key": "DEMO_PASSWORD", "value": "new-real-value"}
    )

    assert response.status_code in (200, 303)
    # Assert the ROUND-TRIP, not the on-disk spelling: AT-082 made the writer
    # quote values so one containing ` #`, edge whitespace or a quote survives
    # `parse_env`. What must hold is that the value reads back exactly.
    from autotester.browser.secrets import parse_env
    written = (scratch_root / ".env").read_text(encoding="utf-8")
    assert parse_env(written)["DEMO_PASSWORD"] == "new-real-value"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits don't apply on Windows")
def test_set_env_value_writes_owner_only_permissions(scratch_root: Path) -> None:
    import stat

    set_env_value(scratch_root / ".env", "DEMO_PASSWORD", "x")

    mode = stat.S_IMODE((scratch_root / ".env").stat().st_mode)
    assert mode == 0o600


def test_env_editor_refuses_an_undeclared_key(client: TestClient, scratch_root: Path) -> None:
    from autotester.schema.project import Project as ProjectModel

    project = ProjectModel(
        slug="demo", name="Demo", base_url="https://demo.test", allowed_domains=["demo.test"],
    )
    ProjectStore("demo", scratch_root).save_project(project)

    response = client.post(
        "/projects/demo/env", data={"key": "NOT_DECLARED", "value": "x"}
    )

    assert response.status_code == 400


def test_env_editor_refuses_a_value_with_a_newline(client: TestClient, scratch_root: Path) -> None:
    """A value containing a newline could inject a second .env line disguised
    as one value (e.g. a smuggled extra KEY=VALUE pair)."""
    from autotester.schema.project import Project as ProjectModel
    from autotester.schema.project import SecretRef

    project = ProjectModel(
        slug="demo", name="Demo", base_url="https://demo.test", allowed_domains=["demo.test"],
        secrets=[SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])],
    )
    ProjectStore("demo", scratch_root).save_project(project)

    response = client.post("/projects/demo/env", data={
        "key": "DEMO_PASSWORD", "value": "real-value\nINJECTED_KEY=evil",
    })

    assert response.status_code == 400
    env_path = scratch_root / ".env"
    written = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    assert "INJECTED_KEY" not in written


def test_an_empty_save_never_wipes_a_stored_value(
    client: TestClient, scratch_root: Path
) -> None:
    """2026-09-21 live wipe: pressing Save on an untouched (empty, masked)
    field overwrote the stored secret with '' — the password save was fine,
    but a stray Save on the email row blanked the stored email. An empty
    field means 'nothing typed', never 'erase': the submit must be refused
    and the stored value must survive byte-identically."""
    from autotester.browser.secrets import parse_env
    from autotester.schema.project import Project as ProjectModel
    from autotester.schema.project import SecretRef

    project = ProjectModel(
        slug="demo", name="Demo", base_url="https://demo.test", allowed_domains=["demo.test"],
        secrets=[SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])],
    )
    ProjectStore("demo", scratch_root).save_project(project)
    set_env_value(scratch_root / ".env", "DEMO_PASSWORD", "keep-me-real")

    response = client.post("/projects/demo/env", data={"key": "DEMO_PASSWORD", "value": ""})

    assert response.status_code == 400
    assert "keep-me-real" not in response.text  # never echoed, even on refusal
    written = (scratch_root / ".env").read_text(encoding="utf-8")
    assert parse_env(written)["DEMO_PASSWORD"] == "keep-me-real"

    whitespace = client.post("/projects/demo/env", data={"key": "DEMO_PASSWORD", "value": "   "})
    assert whitespace.status_code == 400
    written = (scratch_root / ".env").read_text(encoding="utf-8")
    assert parse_env(written)["DEMO_PASSWORD"] == "keep-me-real"


