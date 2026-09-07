"""Adding a case from the UI. Contract: qa/contracts/ui.md.

AT-057: onboarding dead-ended — a new project had zero cases, a permanently
disabled Run button, and no route anywhere to add one, so "onboard a product and
test it without touching the CLI" was false in practice. These tests hold that
path open.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import Action, CaseClass, CaseKind
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _onboard(client: TestClient) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    })


def test_empty_project_offers_a_way_to_add_the_first_case(
    client: TestClient, scratch_root: Path
) -> None:
    """The dead end itself: a project with no cases must say what to do next,
    not just show a disabled Run button."""
    _onboard(client)

    response = client.get("/projects/demo")

    assert response.status_code == 200
    assert "No cases yet" in response.text
    assert "/projects/demo/cases/new" in response.text


def test_new_case_form_prefills_the_projects_own_base_url(
    client: TestClient, scratch_root: Path
) -> None:
    """The fastest useful case — "does the front door still load" — should cost
    one field, so step 1 arrives pointed at the project's own entry URL."""
    _onboard(client)

    response = client.get("/projects/demo/cases/new")

    assert response.status_code == 200
    assert "https://demo.test/signin" in response.text


def test_adding_a_case_persists_a_real_case_readable_by_the_store(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)

    response = client.post("/projects/demo/cases", data={
        "title": "Sign-in page loads",
        "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value, Action.CLICK.value],
        "step_target": ["https://demo.test/signin", ""],
        "step_value": ["", ""],
        "step_expected": ["Sign in to continue", ""],
    }, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/projects/demo"
    cases = ProjectStore("demo", scratch_root).list_cases()
    assert len(cases) == 1
    case = cases[0]
    assert case.title == "Sign-in page loads"
    assert case.case_class is CaseClass.HAPPY
    assert case.kind is CaseKind.BEST  # derived from the class, never asked for
    assert [s.action for s in case.steps] == [Action.NAVIGATE]  # blank row dropped
    assert case.steps[0].expected.visible_text == ["Sign in to continue"]


def test_rationale_is_not_provenance_because_it_feeds_the_grading_rubric(
    client: TestClient, scratch_root: Path
) -> None:
    """Found live: `run_case_pipeline.default_rubric` hands `case.rationale` to
    the grader verbatim as the claim to judge evidence against. An earlier
    version stored "added by hand from the UI" there, so the grader hunted for a
    UI-addition step and FAILed a case whose screenshot plainly showed the
    sign-in page it had asked for. Provenance belongs in flow_id, never here."""
    _onboard(client)

    client.post("/projects/demo/cases", data={
        "title": "Sign-in page loads",
        "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value],
        "step_target": ["https://demo.test/signin"],
        "step_value": [""],
        "step_expected": [""],
    })

    case = ProjectStore("demo", scratch_root).list_cases()[0]
    assert case.rationale is None
    assert case.flow_id == "manual"  # provenance lives here instead

    from autotester.stages.run_case_pipeline import default_rubric
    claim = default_rubric(case, "rub_test").criteria[0].text
    assert "Sign-in page loads" in claim  # the user's own title is the claim
    assert "from the UI" not in claim


def test_blank_rows_are_dropped_and_remaining_steps_renumber_from_one(
    client: TestClient, scratch_root: Path
) -> None:
    """A skipped middle row must not leave a hole in Step.order."""
    _onboard(client)

    client.post("/projects/demo/cases", data={
        "title": "Two real steps",
        "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value, Action.CLICK.value, Action.CLICK.value],
        "step_target": ["https://demo.test/", "", "Continue"],
        "step_value": ["", "", ""],
        "step_expected": ["", "", ""],
    })

    case = ProjectStore("demo", scratch_root).list_cases()[0]
    assert [s.order for s in case.steps] == [1, 2]
    assert [s.target for s in case.steps] == ["https://demo.test/", "Continue"]


def test_a_case_with_no_steps_is_refused(client: TestClient, scratch_root: Path) -> None:
    _onboard(client)

    response = client.post("/projects/demo/cases", data={
        "title": "Nothing to do",
        "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value],
        "step_target": [""],
        "step_value": [""],
        "step_expected": [""],
    })

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_an_unknown_case_class_is_refused_not_silently_written(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard(client)

    response = client.post("/projects/demo/cases", data={
        "title": "Bad class",
        "case_class": "not-a-real-class",
        "step_action": [Action.NAVIGATE.value],
        "step_target": ["https://demo.test/"],
        "step_value": [""],
        "step_expected": [""],
    })

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_adding_a_case_to_an_unknown_project_is_404(
    client: TestClient, scratch_root: Path
) -> None:
    response = client.post("/projects/nope/cases", data={
        "title": "x", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value], "step_target": ["https://demo.test/"],
        "step_value": [""], "step_expected": [""],
    })

    assert response.status_code == 404


def test_once_a_case_exists_the_run_button_is_live_and_the_prompt_is_gone(
    client: TestClient, scratch_root: Path
) -> None:
    """The whole point of AT-057: after adding a case the project is genuinely
    runnable, so the empty-state prompt must disappear and Run must be a real
    submit button rather than the disabled span."""
    _onboard(client)
    client.post("/projects/demo/cases", data={
        "title": "Front door loads",
        "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value],
        "step_target": ["https://demo.test/signin"],
        "step_value": [""],
        "step_expected": [""],
    })

    response = client.get("/projects/demo")

    assert "No cases yet" not in response.text
    assert "<button class='btn btn-primary' type='submit'>▶ Run tests</button>" in response.text
