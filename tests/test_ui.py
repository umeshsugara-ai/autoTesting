"""UI. Contract: qa/contracts/ui.md U1-U5. Real FastAPI TestClient requests
against a scratch AUTOTESTER_ROOT -- "full onboarding -> report without
touching the CLI" (T-100's own goal-task note), proven literally: every test
here drives only HTTP routes, never ProjectStore/CLI directly except to seed
fixtures that a real run would have produced.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import EvidenceKind, Outcome, Result
from autotester.schema.run import RawResult
from autotester.schema.verdict import Verdict
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app
from autotester.ui.env_editor import set_env_value


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# -- U1 onboarding creates a real project.json, no CLI involved --------------

def test_onboard_creates_a_real_project(client: TestClient, scratch_root: Path) -> None:
    response = client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test, sub.demo.test",
    })

    assert response.status_code in (200, 303)
    project = ProjectStore("demo", scratch_root).load_project()
    assert project is not None
    assert project.name == "Demo"
    assert project.allowed_domains == ["demo.test", "sub.demo.test"]


def test_index_lists_onboarded_projects(client: TestClient, scratch_root: Path) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get("/")

    assert response.status_code == 200
    assert "demo" in response.text


def test_unknown_project_is_404(client: TestClient, scratch_root: Path) -> None:
    response = client.get("/projects/nope")
    assert response.status_code == 404


# -- U2 project detail shows review status without a second store ------------

def test_project_detail_shows_review_status(client: TestClient, scratch_root: Path) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get("/projects/demo")

    assert response.status_code == 200
    assert "no flowspec yet" in response.text


def test_a_malicious_slug_is_rejected_outright(client: TestClient, scratch_root: Path) -> None:
    """AT-035: app.py used to render the raw slug into two href attributes
    unescaped -- reproduced originally with a quote-breaking slug. The real
    fix is stronger than escaping alone: any slug not matching the project
    schema's own [a-z][a-z0-9-]* pattern is now refused with 400 before it
    ever reaches ProjectPaths/ProjectStore or gets rendered into HTML at all
    -- the same payload that used to leak an unescaped quote now never gets
    past the route's own input validation."""
    response = client.get("/projects/demo%27%20onmouseover%3D%27alert(1)")
    assert response.status_code == 400


def test_path_traversal_slug_is_rejected() -> None:
    """A literal '..' path segment gets normalized away by any standard HTTP
    client before it ever reaches the server (confirmed: GET /projects/..
    resolves client-side to GET /) -- so the real defense is server-side
    input validation, tested directly against the function that enforces it,
    not through a client that would silently normalize the attack away."""
    from fastapi import HTTPException

    from autotester.ui.app import _require_slug

    for bad in ("..", "../../etc", "a/b", "a\\b", "", "UPPER", "-leading-hyphen"):
        try:
            _require_slug(bad)
            raise AssertionError(f"expected rejection for {bad!r}")
        except HTTPException as exc:
            assert exc.status_code == 400


def test_onboard_refuses_an_invalid_slug(client: TestClient, scratch_root: Path) -> None:
    response = client.post("/onboard", data={
        "slug": "../../etc", "name": "Evil", "base_url": "https://evil.test",
        "allowed_domains": "evil.test",
    })
    assert response.status_code in (400, 422)


# -- U3 the env editor never renders a real value -----------------------------

def test_env_editor_never_renders_the_real_value(client: TestClient, scratch_root: Path) -> None:
    from autotester.schema.project import Project as ProjectModel
    from autotester.schema.project import SecretRef

    project = ProjectModel(
        slug="demo", name="Demo", base_url="https://demo.test", allowed_domains=["demo.test"],
        secrets=[SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])],
    )
    ProjectStore("demo", scratch_root).save_project(project)
    set_env_value(scratch_root / ".env", "DEMO_PASSWORD", "s3cr3t-real-value")

    response = client.get("/projects/demo/env")

    assert response.status_code == 200
    assert "s3cr3t-real-value" not in response.text
    assert "set" in response.text  # presence shown, value never shown


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
    written = (scratch_root / ".env").read_text(encoding="utf-8")
    assert "DEMO_PASSWORD=new-real-value" in written
    assert "new-real-value" not in response.text  # never echoed back either


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


# -- U4 report and run views read real persisted evidence --------------------

def test_report_and_run_view_reflect_real_persisted_data(
    client: TestClient, scratch_root: Path
) -> None:
    from autotester.schema.project import Project as ProjectModel

    ProjectStore("demo", scratch_root).save_project(
        ProjectModel(slug="demo", name="Demo", base_url="https://demo.test",
                     allowed_domains=["demo.test"])
    )
    store = ProjectStore("demo", scratch_root)
    result = RawResult(case_id="case_1", outcome=Outcome.COMPLETED,
                        evidence=[{"kind": EvidenceKind.URL, "path": "https://demo.test/ok"}])
    verdict = Verdict(run_id="run_1", case_id="case_1", result=Result.PASS,
                       grader_provider="mock", rubric_hash="rub_x")
    store.save_result("run_1", result)
    store.save_verdict("run_1", verdict)

    run_response = client.get("/projects/demo/runs/run_1")
    report_response = client.get("/projects/demo/report")

    assert "case_1" in run_response.text and "completed" in run_response.text
    assert "PASS" in report_response.text


def test_report_with_no_runs_says_so_instead_of_erroring(
    client: TestClient, scratch_root: Path
) -> None:
    from autotester.schema.project import Project as ProjectModel

    ProjectStore("demo", scratch_root).save_project(
        ProjectModel(slug="demo", name="Demo", base_url="https://demo.test",
                     allowed_domains=["demo.test"])
    )

    response = client.get("/projects/demo/report")

    assert response.status_code == 200
    assert "no runs yet" in response.text
