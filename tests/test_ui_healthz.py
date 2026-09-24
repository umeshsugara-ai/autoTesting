"""AT-085: the container's uvicorn runs without `--reload`, so a source edit
made after process start is silently NOT served -- a "verified live" claim can
describe the previous build with nothing on the surface to say so. `/healthz`
gives one HTTP call the two mechanical signals a checker previously had to
gather by hand (`ps` for process start, `find -newermt` for source mtimes) so
a live-evidence probe can cite a single authoritative number instead of
archaeology. Contract: qa/contracts/docker.md (presentation-only, like D4's
`/live` -- reads no project state, touches no store).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.ui import routes_live
from autotester.ui.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_healthz_reports_the_three_fields(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert "started_at" in body
    assert "newest_source_mtime" in body
    assert "serving_stale_code" in body


def test_healthz_is_fresh_when_no_source_is_newer_than_start(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(routes_live, "_SRC_ROOT", tmp_path)
    monkeypatch.setattr(
        routes_live, "_PROCESS_STARTED_AT", datetime.now(UTC) + timedelta(seconds=5),
    )
    resp = client.get("/healthz")
    assert resp.json()["serving_stale_code"] is False


def test_healthz_detects_a_source_edit_after_process_start(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact AT-085 scenario: a `.py` file edited AFTER the process started."""
    (tmp_path / "helpers.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(routes_live, "_SRC_ROOT", tmp_path)
    monkeypatch.setattr(
        routes_live, "_PROCESS_STARTED_AT", datetime.now(UTC) - timedelta(seconds=5),
    )
    resp = client.get("/healthz")
    assert resp.json()["serving_stale_code"] is True


def test_healthz_with_no_source_files_is_never_stale(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routes_live, "_SRC_ROOT", tmp_path)
    resp = client.get("/healthz")
    assert resp.json()["serving_stale_code"] is False


def test_healthz_touches_no_project_state(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D4's own invariant, extended to this route: no `ProjectStore`/`SecretStore`
    call, no project param -- a pure process-freshness probe."""
    import inspect

    source = inspect.getsource(routes_live.healthz)
    assert "ProjectStore" not in source
    assert "SecretStore" not in source
