"""Sources-page contract tests for Track A5.2 and AT-277."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.case import Case
from autotester.schema.enums import CaseClass, CaseKind, SourceKind
from autotester.schema.project import Project, Source
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _project(root: Path) -> ProjectStore:
    store = ProjectStore("demo", root)
    store.save_project(Project(
        slug="demo", name="Demo", base_url="https://demo.test",
        allowed_domains=["demo.test"],
    ))
    return store


def test_normal_project_actions_expose_flowspec_and_sources_with_existing_cases(
    client: TestClient, scratch_root: Path
) -> None:
    store = _project(scratch_root)
    store.add_case(Case(
        project="demo", title="Existing case", flow_id="flow-login",
        kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
    ))

    response = client.get("/projects/demo")

    assert response.status_code == 200
    assert "href='/projects/demo/flowspec'" in response.text
    assert "href='/projects/demo/sources'" in response.text


def test_sources_page_registers_and_lists_a_real_recording(
    client: TestClient, scratch_root: Path, tmp_path: Path
) -> None:
    store = _project(scratch_root)
    video = tmp_path / "trainer-flow.mp4"
    video.write_bytes(b"real recording bytes")

    response = client.post(
        "/projects/demo/sources",
        data={"path": str(video), "label": "Trainer happy path"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Trainer happy path" in response.text
    assert "trainer-flow.mp4" in response.text
    sources = store.list_sources()
    assert len(sources) == 1
    assert sources[0].sha256


def test_sources_page_missing_recording_is_a_themed_no_write_refusal(
    client: TestClient, scratch_root: Path, tmp_path: Path
) -> None:
    store = _project(scratch_root)

    response = client.post(
        "/projects/demo/sources",
        data={"path": str(tmp_path / "missing.mp4"), "label": "Missing"},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert "Recording not found" in response.text
    assert store.list_sources() == []


def test_sources_page_escapes_persisted_label_and_path(
    client: TestClient, scratch_root: Path
) -> None:
    store = _project(scratch_root)
    store.add_source(Source(
        project="demo", kind=SourceKind.VIDEO,
        path="C:/videos/<script>alert(1)</script>.mp4",
        label="<img src=x onerror=alert(2)>",
    ))

    response = client.get("/projects/demo/sources")

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "<img src=x onerror=alert(2)>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "&lt;img src=x onerror=alert(2)&gt;" in response.text
