"""BFS-style merged branch tree. Contract: qa/contracts/ui-flow-diagram.md FD1-FD4."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.case import Case
from autotester.schema.enums import Action, CaseClass, CaseKind
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _login_cases() -> list[Case]:
    navigate = Step(order=1, action=Action.NAVIGATE, target="/signin")
    fill_email = Step(order=2, action=Action.FILL, target="email", value="user@test.com")
    return [
        Case(project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
             title="Login with correct credentials",
             steps=[navigate, fill_email,
                    Step(order=3, action=Action.FILL, target="password", value="correct"),
                    Step(order=4, action=Action.CLICK, target="submit")]),
        Case(project="demo", flow_id="login", kind=CaseKind.WORST,
             case_class=CaseClass.AUTH_WRONG_CREDS,
             title="Login with wrong password",
             steps=[navigate, fill_email,
                    Step(order=3, action=Action.FILL, target="password", value="wrong"),
                    Step(order=4, action=Action.CLICK, target="submit")]),
        Case(project="demo", flow_id="login", kind=CaseKind.EDGE, case_class=CaseClass.INPUT_EMPTY,
             title="Submit the login form empty",
             steps=[navigate, Step(order=2, action=Action.CLICK, target="submit")]),
    ]


def test_empty_project_shows_an_honest_empty_state(
    client: TestClient, scratch_root: Path
) -> None:
    ProjectStore("demo", scratch_root).save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                 allowed_domains=["demo.test"])
    )

    response = client.get("/projects/demo/flow-diagram")

    assert response.status_code == 200
    assert "no cases yet" in response.text


def test_every_case_appears_exactly_once(client: TestClient, scratch_root: Path) -> None:
    store = ProjectStore("demo", scratch_root)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                 allowed_domains=["demo.test"])
    )
    for case in _login_cases():
        store.add_case(case)

    response = client.get("/projects/demo/flow-diagram")
    text = response.text

    assert response.status_code == 200
    assert text.count("Login with correct credentials") == 1
    assert text.count("Login with wrong password") == 1
    assert text.count("Submit the login form empty") == 1


def test_shared_prefix_steps_render_only_once(client: TestClient, scratch_root: Path) -> None:
    """FD1: navigate + fill(email) is common to all 3 cases -- must collapse
    into one chain, not be repeated per case."""
    store = ProjectStore("demo", scratch_root)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                 allowed_domains=["demo.test"])
    )
    for case in _login_cases():
        store.add_case(case)

    response = client.get("/projects/demo/flow-diagram")
    text = response.text

    assert text.count("navigate: /signin") == 1
    assert text.count("fill: email = user@test.com") == 1
    # the divergence: two DIFFERENT password fill steps must both appear
    assert "fill: password = correct" in text
    assert "fill: password = wrong" in text


def test_cases_are_grouped_by_flow_id_into_separate_trees(
    client: TestClient, scratch_root: Path
) -> None:
    store = ProjectStore("demo", scratch_root)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                 allowed_domains=["demo.test"])
    )
    store.add_case(Case(
        project="demo", flow_id="login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Login happy path",
        steps=[Step(order=1, action=Action.NAVIGATE, target="/signin")],
    ))
    store.add_case(Case(
        project="demo", flow_id="checkout", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Checkout happy path",
        steps=[Step(order=1, action=Action.NAVIGATE, target="/checkout")],
    ))

    response = client.get("/projects/demo/flow-diagram")
    text = response.text

    assert "Flow: login" in text
    assert "Flow: checkout" in text
    assert text.count("class='card'") >= 2


def test_flow_diagram_link_reachable_from_project_detail(
    client: TestClient, scratch_root: Path
) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get("/projects/demo")

    assert "/projects/demo/flow-diagram" in response.text
