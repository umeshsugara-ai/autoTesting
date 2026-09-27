"""Serves a kept run video by its evidence-relative path (ISS-t191-run-video-2:
T-191's video was recorded and retained but no verified path reached it).
`ui/routes_video.py` is the route; `ui/routes_report.py::_video_section`
links to it from the live per-run page. `video_path` arrives verbatim from
the URL -- every traversal test here treats it as attacker-controlled.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

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
    store.save_result(RUN_ID, RawResult(case_id=case.id, outcome=Outcome.COMPLETED))
    store.save_verdict(RUN_ID, Verdict(run_id=RUN_ID, case_id=case.id, result=Result.PASS,
                                       criteria_met=1, criteria_total=1, grader_provider="mock"))

    response = client.get(f"/projects/demo/runs/{RUN_ID}")

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


def test_serve_run_video_refuses_percent_encoded_traversal_end_to_end(
    client: TestClient, scratch_root: Path
) -> None:
    """The mandatory falsification target: `video_path` is attacker-controlled
    over HTTP. A bare `../` never even reaches the guard -- httpx normalizes
    dot-segments in the URL client-side before the request is sent, so
    requesting a literal `../` 404s at ROUTING, proving nothing (confirmed
    empirically: it never matched the `{video_path:path}` route at all).
    Percent-encoding (`%2e%2e`) survives that normalization and arrives in
    the handler as a real `..` segment -- the shape a manual HTTP client
    (curl, Burp, a scripted attacker) would actually send. The outside file
    is a real `.webm` at the EXACT depth `run_dir` sits below `scratch_root`
    -- a wrong depth or a non-`.webm` outside file would make this pass even
    with the containment check deleted (caught by this unit's own
    falsification pass: an earlier draft used a `.txt` file and too many
    `..` segments, and disabling `is_relative_to` alone did not redden it --
    the suffix check and a missing-file 404 were silently doing the proving
    instead)."""
    store = _seed_with_video(scratch_root)
    depth = len(store.paths.run_dir(RUN_ID).relative_to(scratch_root).parts)
    (scratch_root / "secret.webm").write_bytes(b"must-not-leak")
    dots = "/".join(["%2e%2e"] * depth)

    response = client.get(f"/projects/demo/runs/{RUN_ID}/videos/{dots}/secret.webm")

    assert response.status_code == 404
    assert response.content != b"must-not-leak"


def test_serve_run_video_refuses_an_absolute_path(client: TestClient, scratch_root: Path) -> None:
    """Same depth/extension care as the traversal test above: the outside
    file must be a real `.webm` or the suffix check alone (not the
    containment check under test) would explain a 404."""
    _seed_with_video(scratch_root)
    outside = scratch_root / "secret.webm"
    outside.write_bytes(b"must-not-leak")

    response = client.get(
        f"/projects/demo/runs/{RUN_ID}/videos/{quote(str(outside), safe='')}"
    )

    assert response.status_code == 404


def test_serve_run_video_refuses_a_non_webm_file_even_inside_the_run_dir(
    client: TestClient, scratch_root: Path
) -> None:
    store = _seed_with_video(scratch_root)
    (store.paths.run_dir(RUN_ID) / "01-shot.png").write_bytes(b"not-a-video")

    response = client.get(f"/projects/demo/runs/{RUN_ID}/videos/01-shot.png")

    assert response.status_code == 404


def test_safe_video_path_refuses_a_dotdot_segment(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (tmp_path / "secret.webm").write_bytes(b"must-not-leak")

    assert _safe_video_path(run_dir, "../secret.webm") is None


def test_safe_video_path_refuses_a_symlinked_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.webm").write_bytes(b"must-not-leak")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "escape").symlink_to(outside, target_is_directory=True)

    assert _safe_video_path(run_dir, "escape/secret.webm") is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
def test_safe_video_path_refuses_a_windows_junction_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.webm").write_bytes(b"must-not-leak")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    junction = run_dir / "escape"
    made = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True,
    )
    assert made.returncode == 0, made.stderr.decode(errors="replace")

    assert _safe_video_path(run_dir, "escape/secret.webm") is None


def test_safe_video_path_refuses_a_unc_path_without_touching_the_network(tmp_path: Path) -> None:
    """senior-software-engineer review, this cycle: before the string-level
    guard existed, an attacker-controlled `\\\\host\\share\\...` reached
    `Path.resolve()`, which makes Windows attempt a real SMB connection to
    `host` -- measured ~21s against an unreachable host in review, a
    blocking DoS / forced-SMB-auth vector, not merely a wrong answer. The
    bounded wall-clock assertion proves the guard fires BEFORE `resolve()`
    is ever called; `result is None` alone would pass even at 21s."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    start = time.perf_counter()

    result = _safe_video_path(run_dir, r"\\198.51.100.1\share\x.webm")

    assert result is None
    assert time.perf_counter() - start < 2.0


def test_safe_video_path_refuses_a_drive_rooted_path(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    assert _safe_video_path(run_dir, r"C:\Windows\System32\drivers\etc\hosts") is None


def test_serve_run_video_refuses_a_unc_path_end_to_end(
    client: TestClient, scratch_root: Path
) -> None:
    _seed_with_video(scratch_root)
    unc = r"\\198.51.100.1\share\x.webm"

    response = client.get(f"/projects/demo/runs/{RUN_ID}/videos/{quote(unc, safe='')}")

    assert response.status_code == 404


def test_safe_video_path_accepts_a_real_nested_video(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    (run_dir / "prefix").mkdir(parents=True)
    (run_dir / "prefix" / "case.webm").write_bytes(b"real")

    result = _safe_video_path(run_dir, "prefix/case.webm")

    assert result == (run_dir / "prefix" / "case.webm").resolve()
