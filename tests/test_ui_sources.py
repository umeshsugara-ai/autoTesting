"""Sources-page contract tests for Track A5.2 and AT-277."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.providers.mock import MockProvider
from autotester.schema.analysis import AnalysedIssue, VideoAnalysis
from autotester.schema.case import Case
from autotester.schema.enums import CaseClass, CaseKind, IssueCategory, ReviewStatus, SourceKind
from autotester.schema.flowspec import FlowSpec, Review, Screen
from autotester.schema.media import MediaChunk, MediaPrep
from autotester.schema.observation import ObservedIssue, ObservedScreen, VideoObservation
from autotester.schema.project import Project, Source
from autotester.stages.ingest import register_source
from autotester.stages.issues import derive_issues
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app
from autotester.ui.routes_sources import _save_analysis_outputs


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

    submitted_path = str(tmp_path / "missing.mp4")
    response = client.post(
        "/projects/demo/sources",
        data={"path": submitted_path, "label": "Missing"},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert "Recording not found" in response.text
    assert submitted_path not in response.text
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


def test_sources_page_uploads_into_a_content_addressed_project_directory(
    client: TestClient, scratch_root: Path,
) -> None:
    store = _project(scratch_root)

    response = client.post(
        "/projects/demo/sources/upload",
        files={"recording": ("walkthrough.mp4", b"uploaded recording", "video/mp4")},
        data={"label": "Uploaded walkthrough"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    source = store.list_sources()[0]
    assert source.label == "Uploaded walkthrough"
    assert Path(source.path or "").read_bytes() == b"uploaded recording"
    assert Path(source.path or "").parent.name == source.id


def test_uploaded_recordings_are_gitignored() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "projects/demo/sources/src_fake/recording.mp4"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0


def test_analyze_without_media_prep_refuses_with_real_host_command(
    client: TestClient, scratch_root: Path, tmp_path: Path,
) -> None:
    store = _project(scratch_root)
    recording = tmp_path / "unprepared.mp4"
    recording.write_bytes(b"video")
    source = register_source(store, recording, label="Unprepared")

    response = client.post(
        f"/projects/demo/sources/{source.id}/analyze", follow_redirects=False)

    assert response.status_code == 400
    assert "autotester ingest prep demo" in response.text
    assert "HOST" in response.text


def test_analyze_refreshes_outputs_without_mutating_an_approved_flowspec(
    client: TestClient, scratch_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _project(scratch_root)
    recording = tmp_path / "prepared.mp4"
    recording.write_bytes(b"video")
    source = register_source(store, recording, label="Prepared")
    store.save_media_prep(MediaPrep(
        source_id=source.id,
        chunks=[MediaChunk(index=0, path=str(recording), offset_s=0, length_s=3)],
    ))
    spec = FlowSpec(
        project="demo", screens=[Screen(id="screen_login", name="Login")],
        review=Review(status=ReviewStatus.APPROVED, by="Umesh"),
    )
    store.save_flowspec(spec)
    before = store.paths.flowspec.read_bytes()
    observation = VideoObservation(
        screens=[ObservedScreen(name="Login", t_start=0)],
        issues=[ObservedIssue(t_start=1, screen="Login", category=IssueCategory.LOGIC_ERROR,
                              title="Submit fails", what_is_wrong="Nothing happens")],
    )
    provider = MockProvider(responses={"vision": [observation, observation]})
    monkeypatch.setattr("autotester.ui.routes_sources.providers.get", lambda _name: provider)

    response = client.post(
        f"/projects/demo/sources/{source.id}/analyze", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/projects/demo/product-map"
    assert len(store.list_issues()) == 1
    assert len(store.load_screen_map().screens) == 1  # type: ignore[union-attr]
    assert store.paths.flowspec.read_bytes() == before


def test_partial_analysis_cannot_delete_the_last_complete_issue_set(
    scratch_root: Path, tmp_path: Path,
) -> None:
    store = _project(scratch_root)
    recording = tmp_path / "recording.mp4"
    recording.write_bytes(b"video")
    source = register_source(store, recording, label="Partial refresh")
    complete = VideoAnalysis(
        source_id=source.id,
        observations_used=2,
        observations_expected=2,
        issues=[AnalysedIssue(
            t_start=1,
            screen="Login",
            category=IssueCategory.LOGIC_ERROR,
            title="Submit fails",
            what_is_wrong="Nothing happens",
        )],
    )
    for issue in derive_issues(complete, source, "demo"):
        store.add_issue(issue)
    known_ids = {issue.id for issue in store.list_issues()}
    partial = VideoAnalysis(
        source_id=source.id,
        observations_used=1,
        observations_expected=2,
    )

    _save_analysis_outputs(store, source, partial)

    assert {issue.id for issue in store.list_issues()} == known_ids
