"""The credential guard's exemption, and the routes that echo input back.
Contract: qa/contracts/ui.md U8, U9.

AT-078 -> AT-083 -> AT-086/087: the guard must match every value in the shared
`.env`, declared or not, while still letting a project re-save its own stored
data. Getting one of those right at the expense of the other took three fix
cycles, so both directions are pinned here.

Split from test_ui_credential_safety_project.py at doctor's 300-line cap.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import Action, CaseClass
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# -- AT-078 + AT-083: the exemption must be narrow, not a hole ---------------

def test_a_project_can_resave_its_own_unmodified_data(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-078: `.env` holds plain configuration as well as credentials. When the
    guard matched every `.env` value, a project whose own base_url equalled a
    non-secret `.env` URL became uneditable — a no-op save returned 400 with no
    fix the user could express."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    })
    # The .env entry appears AFTER the project exists -- exactly how pathlynks
    # got here: PATHLYNKS_USER_LOGIN_URL was added to a shared .env long after
    # that project was onboarded. Onboarding a project whose base_url is
    # ALREADY in .env is still refused; filed as its own issue, not hidden.
    env = scratch_root / ".env"
    env.write_text("SOME_CONFIG_URL=https://demo.test/signin\n", encoding="utf-8")

    response = client.post("/projects/demo/edit", data={
        "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    }, follow_redirects=False)

    assert response.status_code == 303
    assert ProjectStore("demo", scratch_root).load_project().base_url == "https://demo.test/signin"


def test_an_undeclared_env_value_is_still_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-083: scoping the guard to DECLARED credentials to fix AT-078 opened a
    real hole — an undeclared provider API key sitting in the shared `.env` is
    still a credential, and this repo is public. Matching must stay broad; only
    already-stored data is exempt."""
    env = scratch_root / ".env"
    env.write_text("GEMINI_API_KEY=AIza-undeclared-but-very-real\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.post("/projects/demo/cases", data={
        "title": "AIza-undeclared-but-very-real", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.NAVIGATE.value], "step_target": ["https://demo.test/"],
        "step_value": [""], "step_expected": [""],
    })

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_the_exemption_does_not_let_a_credential_in_through_another_field(
    client: TestClient, scratch_root: Path
) -> None:
    """The exemption covers only data already stored for that same field. A
    credential pasted into a DIFFERENT field of the same form is still refused."""
    env = scratch_root / ".env"
    env.write_text("SECRET_TOKEN=tok-abcdefghijklmnop\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.post("/projects/demo/edit", data={
        "name": "tok-abcdefghijklmnop",          # a credential, not stored data
        "base_url": "https://demo.test",          # exempt (unchanged)
        "allowed_domains": "demo.test",           # exempt (unchanged)
    })

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).load_project().name == "Demo"


def test_a_credential_pasted_into_base_url_is_not_echoed_back(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-088: `_require_reachable_base_url` runs BEFORE the credential guard,
    so an unparseable value was handed straight back in the 400 body — a
    password pasted into Base URL would appear on screen and in the access log.
    Fourth occurrence of the AT-068/AT-075 echo pattern."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })

    response = client.post("/projects/demo/edit", data={
        "name": "Demo", "base_url": "hunter2-pasted-in-the-wrong-box",
        "allowed_domains": "demo.test",
    })

    assert response.status_code == 400
    assert "hunter2" not in response.text
