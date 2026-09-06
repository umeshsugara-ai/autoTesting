"""The home-page dashboard. Contract: qa/contracts/ui.md U2 (real persisted
state, never recomputed/cached). Split out of test_ui.py (AT doctor's 300-line
file cap) once the home page grew from a bare project grid into a portfolio
health view.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import Result
from autotester.schema.run import Run
from autotester.schema.verdict import Verdict
from autotester.store.project_store import ProjectStore
from autotester.ui import theme
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_index_shows_portfolio_stats_across_projects(
    client: TestClient, scratch_root: Path
) -> None:
    """Feedback 2026-09-06: the home page showed project names and case
    counts only, nothing about what's actually passing or failing across the
    portfolio -- a non-technical user had to click into every project one by
    one. The dashboard must surface aggregate health without doing so."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    store = ProjectStore("demo", scratch_root)
    run = Run(project="demo", case_ids=["case-1"])
    store.save_run(run)
    store.save_verdict(run.id, Verdict(run_id=run.id, case_id="case-1",
                                        result=Result.FAIL, grader_provider="mock"))

    response = client.get("/")

    assert response.status_code == 200
    assert "projects" in response.text
    assert "latest run failing" in response.text
    assert theme.badge("FAIL", count=1) in response.text


def test_index_project_never_run_shows_that_state(
    client: TestClient, scratch_root: Path
) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get("/")

    assert response.status_code == 200
    assert "never run" in response.text


def test_index_project_with_clean_latest_run_counts_as_healthy(
    client: TestClient, scratch_root: Path
) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    store = ProjectStore("demo", scratch_root)
    run = Run(project="demo", case_ids=["case-1"])
    store.save_run(run)
    store.save_verdict(run.id, Verdict(run_id=run.id, case_id="case-1",
                                        result=Result.PASS, grader_provider="mock"))

    response = client.get("/")

    assert response.status_code == 200
    assert "latest run clean" in response.text
    assert "latest run failing" not in response.text
