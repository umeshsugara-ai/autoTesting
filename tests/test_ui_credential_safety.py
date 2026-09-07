"""The credential path, end to end and safe. Contract: qa/contracts/ui.md U3.

Track 0, Unit 0.2. Before this, a user handed a password had no safe place to
put it in a test step: `cases.jsonl` is not gitignored, and a literal value
carries no `{{SECRET:KEY}}` placeholder, so `session.fill` never tags the field
and it appears in cleartext in every screenshot. A mistyped key surfaced only
mid-run as a stringified `UndeclaredSecret`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import Action, CaseClass
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app

REAL_PASSWORD = "hunter2-this-is-the-real-one"


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _project_with_credential(client: TestClient, scratch_root: Path, *, value: str = "") -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    })
    client.post("/projects/demo/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })
    if value:
        (scratch_root / ".env").write_text(f"DEMO_PASSWORD={value}\n", encoding="utf-8")


def _add_case(client: TestClient, value: str):
    return client.post("/projects/demo/cases", data={
        "title": "Log in", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.FILL.value], "step_target": ["input[type=password]"],
        "step_value": [value], "step_expected": [""],
    }, follow_redirects=False)


# -- the plaintext hole ------------------------------------------------------

def test_pasting_the_real_credential_into_a_step_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    response = _add_case(client, REAL_PASSWORD)

    assert response.status_code == 400
    assert "looks like a real credential" in response.text
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_the_refused_value_never_reaches_the_cases_file(
    client: TestClient, scratch_root: Path
) -> None:
    """`cases.jsonl` is not gitignored — a leak here is a leak into the repo."""
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    _add_case(client, REAL_PASSWORD)

    cases_file = scratch_root / "projects" / "demo" / "cases.jsonl"
    assert not cases_file.exists() or REAL_PASSWORD not in cases_file.read_text(encoding="utf-8")


def test_the_placeholder_is_accepted_and_stored(
    client: TestClient, scratch_root: Path
) -> None:
    """The safe form of the same intent must work."""
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    response = _add_case(client, "{{SECRET:DEMO_PASSWORD}}")

    assert response.status_code == 303
    case = ProjectStore("demo", scratch_root).list_cases()[0]
    assert case.steps[0].value == "{{SECRET:DEMO_PASSWORD}}"
    assert REAL_PASSWORD not in case.model_dump_json()


def test_an_undeclared_key_is_refused_up_front(
    client: TestClient, scratch_root: Path
) -> None:
    """Previously this resolved only at typing time, deep inside `_value_for`,
    arriving as a stringified UndeclaredSecret in a generic ERRORED outcome."""
    _project_with_credential(client, scratch_root)

    response = _add_case(client, "{{SECRET:NOT_DECLARED}}")

    assert response.status_code == 400
    assert "NOT_DECLARED" in response.text
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_an_ordinary_value_is_untouched(client: TestClient, scratch_root: Path) -> None:
    """The guard must not get in the way of normal typing."""
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    response = _add_case(client, "  Bengaluru  ")

    assert response.status_code == 303
    assert ProjectStore("demo", scratch_root).list_cases()[0].steps[0].value == "Bengaluru"


# -- the form makes the safe thing the easy thing ----------------------------

def test_the_form_offers_the_declared_credentials(
    client: TestClient, scratch_root: Path
) -> None:
    _project_with_credential(client, scratch_root)

    response = client.get("/projects/demo/cases/new")

    assert "{{SECRET:DEMO_PASSWORD}}" in response.text
    assert "list='declared-credentials'" in response.text


def test_a_project_with_no_credentials_gets_no_picker(
    client: TestClient, scratch_root: Path
) -> None:
    """The box behaves exactly as before for a project that declares nothing."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.get("/projects/demo/cases/new")

    assert "declared-credentials" not in response.text


# -- fail fast, not mid-run --------------------------------------------------

def test_a_run_is_refused_when_a_declared_credential_has_no_value(
    client: TestClient, scratch_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The UI loads secrets with strict=False, so a missing value used to
    surface only when a step tried to type it — as BLOCKED_HITL, after a
    browser had already been launched."""
    _project_with_credential(client, scratch_root)  # declared, no value
    _add_case(client, "{{SECRET:DEMO_PASSWORD}}")

    class _AvailableProvider:  # the provider gate is a different precondition
        def available(self) -> bool:
            return True

    import autotester.ui.routes_runs as routes_runs_module
    monkeypatch.setattr(routes_runs_module, "LangChainFallbackProvider", _AvailableProvider)

    response = client.post("/projects/demo/run")

    assert response.status_code == 400
    assert "DEMO_PASSWORD" in response.text
    assert "Credentials page" in response.text
