"""A navigate step the browser would refuse is refused when the case is saved. AT-432.

Found by live-browser validation, not by any test: a case with
`navigate https://evil.test/` was saved on a project allowed only `127.0.0.1`,
silently, and would have failed hours later at run time with `NavigationRefused`.
AT-058's dead-on-arrival class, one level below the project's own base URL.

The refusal is decided by `browser.session.check_destination` — the function that
refuses the step at run time — so creation and execution cannot disagree.

Split from `test_ui_cases.py` (doctor's 300-line rule) along a real seam: that file
proves a case CAN be added; this one proves a case that could never run CANNOT.
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


def _onboard(client: TestClient) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
    })

# -- AT-432: a navigate step the browser would refuse is refused up front -------

def _post_case(client: TestClient, *targets: str, actions: list[str] | None = None):
    acts = actions or [Action.NAVIGATE.value] * len(targets)
    return client.post("/projects/demo/cases", data={
        "title": "Probe", "case_class": CaseClass.HAPPY.value,
        "step_action": acts, "step_target": list(targets),
        "step_value": [""] * len(targets), "step_expected": [""] * len(targets),
    })


def test_an_off_domain_navigate_step_is_refused_and_nothing_is_saved(
    client: TestClient, scratch_root: Path
) -> None:
    """The defect, found in a live browser: a case that could never run was
    saved silently and failed hours later with NavigationRefused. The assertion
    that matters is that NO case was written, not merely that a 400 came back."""
    _onboard(client)

    response = _post_case(client, "https://evil.test/")

    assert response.status_code == 400
    assert "evil.test" in response.json()["detail"], "name the host so it can be fixed"
    assert ProjectStore("demo", scratch_root).list_cases() == [], "nothing may be saved"


def test_only_the_offending_step_is_named_when_a_later_step_leaves_the_domain(
    client: TestClient, scratch_root: Path
) -> None:
    """A case is usually several steps; the message has to point at the right one."""
    _onboard(client)

    response = _post_case(client, "https://demo.test/signin", "https://evil.test/x")

    assert response.status_code == 400
    assert "step 2" in response.json()["detail"]
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_a_relative_target_is_refused_because_the_browser_cannot_open_it(
    client: TestClient, scratch_root: Path
) -> None:
    """`check_destination` refuses a target with no parseable host at run time,
    so a relative `/login` never worked. Refusing it now is agreeing with run
    time, not a new restriction."""
    _onboard(client)

    response = _post_case(client, "/login")

    assert response.status_code == 400
    assert "full URL" in response.json()["detail"]


def test_an_in_domain_and_a_subdomain_target_are_still_accepted(
    client: TestClient, scratch_root: Path
) -> None:
    """The guard must be able to say yes, including to a subdomain the project's
    own `allows_domain` covers — or it would satisfy every refusal above."""
    _onboard(client)

    response = _post_case(client, "https://demo.test/signin", "https://app.demo.test/home")

    assert response.status_code in (200, 303)
    assert len(ProjectStore("demo", scratch_root).list_cases()) == 1


def test_a_secret_placeholder_target_is_not_judged_at_creation(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-076: the whole target may be a `{{SECRET:KEY}}` placeholder with no host
    to check here; it is gated at run time against the secret's own domains.
    Refusing it would break a supported feature to close this one.

    The credential MUST be declared first. My first version of this test used an
    undeclared key, and the 400 it got came from a different, pre-existing guard
    ("has not declared a credential called ..."), not from this unit — so as an
    acceptance test it failed for an unrelated reason, and written as a refusal
    test it would have passed for the wrong one."""
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test/signin",
        "allowed_domains": "demo.test",
        "credential_key": "DEMO_LOGIN_URL", "credential_value": "https://demo.test/secret-entry",
        "credential_domains": "demo.test", "credential_description": "login url",
    })

    response = _post_case(client, "{{SECRET:DEMO_LOGIN_URL}}")

    assert response.status_code in (200, 303)
    assert len(ProjectStore("demo", scratch_root).list_cases()) == 1


def test_a_non_navigate_step_with_an_off_domain_looking_target_is_not_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """A click's target is a locator, not a destination. Judging it as a URL would
    refuse perfectly good cases whose selector happens to contain a dot."""
    _onboard(client)

    response = _post_case(client, "https://demo.test/signin", "a[href='https://evil.test']",
                          actions=[Action.NAVIGATE.value, Action.CLICK.value])

    assert response.status_code in (200, 303)
    assert len(ProjectStore("demo", scratch_root).list_cases()) == 1


def test_a_pasted_credential_in_a_navigate_target_is_not_echoed_back(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-088: `host_of` returns a pseudo-host for garbage, and the run-time
    message names the host unconditionally. A password pasted into the target
    box must not come back in the response."""
    _onboard(client)
    canary = "Zq9-canary-hunter2-NOT-A-HOST"

    response = _post_case(client, canary)

    assert response.status_code == 400
    assert canary not in response.text
    assert canary.lower() not in response.text.lower()
