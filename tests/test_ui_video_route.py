"""Serves a kept run video by its evidence-relative path (ISS-t191-run-video-2:
T-191's video was recorded and retained but no verified path reached it).
`ui/routes_video.py` is the route; `ui/routes_report.py::_video_section`
links to it from the live per-run page. Covers serving, linking, and run
validity; every traversal/attacker-controlled-input test lives in
`test_ui_video_route_traversal.py` (split by responsibility, doctor's
300-line file cap).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.case import Case
from autotester.schema.enums import Action, CaseClass, CaseKind, EvidenceKind, Outcome, Result
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.schema.run import Evidence, RawResult, Run
from autotester.schema.verdict import Verdict
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app
from autotester.ui.routes_video import _safe_video_path

RUN_ID = "run-video-route-test"


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _seed_with_video(scratch_root: Path, *, video_bytes: bytes = b"FAKE-WEBM") -> ProjectStore:
    store = ProjectStore("demo", scratch_root)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )
    case = Case(
        project="demo", flow_id="flow-login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Login attempt", steps=[Step(order=1, action=Action.NAVIGATE, target="/login")],
    )
    store.add_case(case)
    store.save_run(Run(id=RUN_ID, project="demo", case_ids=[case.id]))
    run_dir = store.paths.run_dir(RUN_ID)
    video_rel = "video.webm"  # fixed name: this fixture's `case.id` is a
    # content hash, irrelevant to what's under test here
    (run_dir / video_rel).write_bytes(video_bytes)
    store.save_result(RUN_ID, RawResult(
        case_id=case.id, outcome=Outcome.COMPLETED,
        evidence=[Evidence(kind=EvidenceKind.VIDEO, path=video_rel, masked=True)],
    ))
    store.save_verdict(RUN_ID, Verdict(
        run_id=RUN_ID, case_id=case.id, result=Result.FAIL, criteria_met=0, criteria_total=1,
        grader_provider="mock",
    ))
    return store


def test_serve_run_video_streams_the_real_file(client: TestClient, scratch_root: Path) -> None:
    _seed_with_video(scratch_root, video_bytes=b"REAL-ENOUGH-WEBM-BYTES")

    response = client.get(f"/projects/demo/runs/{RUN_ID}/videos/video.webm")

    assert response.status_code == 200
    assert response.content == b"REAL-ENOUGH-WEBM-BYTES"
    assert response.headers["content-type"] == "video/webm"


def test_run_view_links_to_the_video_route(client: TestClient, scratch_root: Path) -> None:
    _seed_with_video(scratch_root)

    response = client.get(f"/projects/demo/runs/{RUN_ID}")

    assert response.status_code == 200
    assert f"/projects/demo/runs/{RUN_ID}/videos/video.webm" in response.text


def test_run_view_shows_no_video_link_when_there_is_no_video_evidence(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-654 (checker, cycle 1): this test was VACUOUS. It seeded a `RawResult`
    with no `evidence=` at all, which `schema/run.py` defaults to `[]`, so the
    run had zero evidence of ANY kind — the assertion held whether
    `_video_section`'s `EvidenceKind.VIDEO` filter existed, was inverted, or was
    deleted. It now seeds a SCREENSHOT row, so the filter is the only thing that
    keeps `.webm` out of the page and removing it reddens this test.
    """
    store = ProjectStore("demo", scratch_root)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )
    case = Case(project="demo", flow_id="flow-home", kind=CaseKind.BEST,
                case_class=CaseClass.HAPPY, title="Homepage loads",
                steps=[Step(order=1, action=Action.NAVIGATE, target="/")])
    store.add_case(case)
    store.save_run(Run(id=RUN_ID, project="demo", case_ids=[case.id]))
    store.save_result(RUN_ID, RawResult(
        case_id=case.id, outcome=Outcome.COMPLETED,
        evidence=[Evidence(kind=EvidenceKind.SCREENSHOT, path="step-1.png", step_order=1)],
    ))
    store.save_verdict(RUN_ID, Verdict(run_id=RUN_ID, case_id=case.id, result=Result.PASS,
                                       criteria_met=1, criteria_total=1, grader_provider="mock"))

    response = client.get(f"/projects/demo/runs/{RUN_ID}")

    # The run HAS evidence, so the VIDEO filter is the only thing that can keep a
    # video link out -- and the prefix reddens for ANY row the filter lets past.
    assert f"/runs/{RUN_ID}/videos/" not in response.text
    assert ".webm" not in response.text


def test_serve_run_video_404s_for_an_unknown_run(client: TestClient, scratch_root: Path) -> None:
    ProjectStore("demo", scratch_root).save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )

    response = client.get("/projects/demo/runs/no-such-run/videos/x.webm")

    assert response.status_code == 404


def test_serve_run_video_404s_for_a_stray_directory_with_no_real_run_envelope(
    client: TestClient, scratch_root: Path
) -> None:
    """Isolates the run-validity check (mirrors UR5) from `_safe_video_path`'s
    own `is_dir()` guard: the directory and a real `.webm` file both exist on
    disk, exactly like a crawl-artifact directory dropped under `runs/`
    (`test_ui_report.py::test_run_view_returns_404_for_a_directory_without_a_run`)
    -- there is simply no persisted `Run` whose id is this directory's name.
    `test_serve_run_video_404s_for_an_unknown_run` above 404s for a
    completely absent directory too, but that alone could pass even if this
    route never checked run validity at all, since `_safe_video_path`'s own
    `trusted_root.is_dir()` check would 404 it independently -- this test
    is the one that actually isolates the run-existence check."""
    store = ProjectStore("demo", scratch_root)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )
    stray = store.paths.runs_dir / "zzz-crawl-artifacts"
    stray.mkdir(parents=True)
    (stray / "x.webm").write_bytes(b"must-not-serve")

    response = client.get("/projects/demo/runs/zzz-crawl-artifacts/videos/x.webm")

    assert response.status_code == 404


def test_safe_video_path_accepts_a_real_nested_video(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    (run_dir / "prefix").mkdir(parents=True)
    (run_dir / "prefix" / "case.webm").write_bytes(b"real")

    result = _safe_video_path(run_dir, "prefix/case.webm")

    assert result == (run_dir / "prefix" / "case.webm").resolve()
