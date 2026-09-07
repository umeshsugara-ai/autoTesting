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


@pytest.mark.parametrize("path", [
    "/onboard", "/projects/demo", "/projects/demo/env", "/projects/demo/report",
    "/projects/demo/flow-diagram", "/settings/providers", "/live",
])
def test_every_non_home_page_has_a_real_back_button(
    client: TestClient, scratch_root: Path, path: str
) -> None:
    """Umesh, 2026-09-07: "there is no back button for easy navigation" — the
    breadcrumb trail alone was a muted 0.78rem uppercase line that read as a
    location label, not a control. Every page a user can navigate INTO must
    offer a visible way back out."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get(path)

    assert response.status_code == 200
    assert "<a class='btn btn-back'" in response.text, f"{path} has no back button"
    assert "&larr; Back" in response.text


def test_back_button_targets_the_parent_not_always_home(
    client: TestClient, scratch_root: Path
) -> None:
    """A nested page goes back one level (to its project), not all the way
    home — otherwise "back" silently loses the user's place."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get("/projects/demo/env")

    assert "<a class='btn btn-back' href='/projects/demo'>" in response.text


def test_home_page_has_no_back_button(client: TestClient, scratch_root: Path) -> None:
    """Home is the root — a back button there would point at itself. Asserts on
    the rendered anchor, not the class name: `.btn-back`'s CSS rule ships in the
    shared stylesheet on every page, so a bare substring check always matches."""
    response = client.get("/")

    assert response.status_code == 200
    assert "<a class='btn btn-back'" not in response.text


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
