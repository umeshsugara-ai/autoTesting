"""One question: which FORMS of a credential does the UI guard recognise?

`Redactor.is_clean` is a plain substring test, so every form a pasted
credential can arrive in that a reader could trivially reverse has had to be
taught to the guard one incident at a time — percent-encoding and a stray space
or newline (AT-074, AT-071), then case and separators (AT-339, where a checker
put `zebra-quilt-apikey-31` past the guard for the live value
`ZEBRA_QUILT_APIKEY_31` and it became the on-disk directory name, every page
URL, and text on the home index).

The last test here guards the other direction: folding is a heuristic widening,
so it is floored, and ordinary text must not start being refused because some
short `.env` value folds into it.

Contract: qa/contracts/ui.md U8/U9. Split from
`test_ui_credential_safety_project.py` at doctor's 300-line cap (C2), which
keeps the question of which FIELDS are guarded and how values round-trip.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import Action, CaseClass
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app

REAL_PASSWORD = "hunter2-this-is-the-real-one"

UPPER_CREDENTIAL = "ZEBRA_QUILT_APIKEY_31"
"""A real `.env` value in the shape API keys actually take: upper snake case.
`REAL_PASSWORD` is already lowercase-with-hyphens, so every test written
against it exercised the one casing where a plain substring test happens to
work -- which is why the case class survived AT-073, AT-074 and AT-079."""


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
        env_line = "DEMO_PASSWORD=" + value + chr(10)
        (scratch_root / ".env").write_text(env_line, encoding="utf-8")


def _add_case(client: TestClient, value: str):
    return client.post("/projects/demo/cases", data={
        "title": "Log in", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.FILL.value], "step_target": ["input[type=password]"],
        "step_value": [value], "step_expected": [""],
    }, follow_redirects=False)


# -- AT-074: trivially-recoverable encodings ---------------------------------

def test_a_url_encoded_credential_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-074: `is_clean` is a plain substring test, so a percent-encoded value
    passed straight through and was written to a tracked file."""
    from urllib.parse import quote_plus
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    response = _add_case(client, quote_plus(REAL_PASSWORD))

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_a_credential_broken_by_a_space_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    half = len(REAL_PASSWORD) // 2
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    response = _add_case(client, f"{REAL_PASSWORD[:half]} {REAL_PASSWORD[half:]}")

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_a_case_and_separator_transform_of_a_credential_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-339, reproduced live by a checker: slug `zebra-quilt-apikey-31` for
    the value `ZEBRA_QUILT_APIKEY_31` was ACCEPTED, became the on-disk
    directory name and every page URL, and rendered on the home index.

    `Redactor.is_clean` is a plain substring test and `_credential_variants`
    normalised encoding and whitespace but never CASE, so a transform anyone
    can reverse in their head walked through the guard AT-079 had just
    tightened."""
    (scratch_root / ".env").write_text(
        f"DEMO_PASSWORD={UPPER_CREDENTIAL}\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": "seed3", "name": "Seed3", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    client.post("/projects/seed3/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })

    transformed = UPPER_CREDENTIAL.lower().replace("_", "-")
    response = client.post("/onboard", data={
        "slug": transformed, "name": "Leaky", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    }, follow_redirects=False)

    assert response.status_code == 400, transformed
    assert not (scratch_root / "projects" / transformed).exists()


def test_a_credential_with_its_separators_stripped_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """The same recoverability argument as AT-074's whitespace case: deleting
    the hyphens from a credential is not a different secret."""
    _project_with_credential(client, scratch_root, value=REAL_PASSWORD)

    response = _add_case(client, REAL_PASSWORD.replace("-", ""))

    assert response.status_code == 400
    assert ProjectStore("demo", scratch_root).list_cases() == []


def test_a_short_env_value_does_not_start_refusing_ordinary_text(
    client: TestClient, scratch_root: Path
) -> None:
    """The other half of the fix, and the reason it is bounded.

    Folding case and separators is a HEURISTIC widening: it makes the guard
    match strings that are not byte-equal to any secret. Applied without a
    floor, a short `.env` value would start refusing ordinary input that merely
    contains its letters -- `A-B` would fold to `ab` and refuse every title
    containing "ab". So folded matching requires a minimum folded length, while
    the exact and AT-074 variants keep matching at ANY length, so AT-002's
    "deliberately no minimum length" still holds for a real value.
    """
    (scratch_root / ".env").write_text("DEMO_PASSWORD=A-B\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": "shorty", "name": "Shorty", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    client.post("/projects/shorty/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })

    ok = client.post("/projects/shorty/cases", data={
        "title": "Grab the tab", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.FILL.value], "step_target": ["#q"],
        "step_value": ["nothing secret here"], "step_expected": [""],
    }, follow_redirects=False)
    assert ok.status_code in (200, 303), ok.text[:300]

    # the real value itself is still refused at that length -- AT-002 intact
    leak = client.post("/projects/shorty/cases", data={
        "title": "Leak", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.FILL.value], "step_target": ["#q"],
        "step_value": ["A-B"], "step_expected": [""],
    }, follow_redirects=False)
    assert leak.status_code == 400


def test_a_folded_credential_in_one_field_is_blamed_on_that_field(
    client: TestClient, scratch_root: Path
) -> None:
    """Not about detection -- both folded checks would catch this -- but about
    which one answers. The joined guard's message says a credential is "split
    across" the named fields, which is false and unactionable when the value
    sits whole in one box. The per-field check exists to say "the slug looks
    like it contains a real credential", and only the message proves it ran."""
    (scratch_root / ".env").write_text(
        f"DEMO_PASSWORD={UPPER_CREDENTIAL}\n", encoding="utf-8")
    client.post("/onboard", data={
        "slug": "seed4", "name": "Seed4", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })
    client.post("/projects/seed4/secrets", data={
        "key": "DEMO_PASSWORD", "domains": "demo.test", "mask_in_screenshot": "on",
    })

    response = client.post("/onboard", data={
        "slug": UPPER_CREDENTIAL.lower().replace("_", "-"), "name": "Leaky",
        "base_url": "https://demo.test", "allowed_domains": "demo.test",
    }, follow_redirects=False)

    assert response.status_code == 400
    assert "the slug looks like it contains a real credential" in response.text
    assert "split across" not in response.text


def test_a_folded_credential_split_across_two_fields_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    """AT-071's argument, one fold further on: neither half is a credential in
    any casing, and the concatenation is one `casefold` away from the real
    value. Only the joined check can see this."""
    _project_with_credential(client, scratch_root, value=UPPER_CREDENTIAL)
    half = len(UPPER_CREDENTIAL) // 2
    upper = UPPER_CREDENTIAL.lower().replace("_", "-")

    # Two Value boxes, because the join is ordered title -> targets -> values
    # -> expects: only fields ADJACENT in that order reassemble contiguously on
    # disk, which is the whole premise of the joined check. Splitting across
    # title and value would put a Target box between the halves, and then the
    # value genuinely does not reassemble -- a refusal there would be a false
    # positive, not a catch.
    response = client.post("/projects/demo/cases", data={
        "title": "Log in", "case_class": CaseClass.HAPPY.value,
        "step_action": [Action.FILL.value, Action.FILL.value],
        "step_target": ["#a", "#b"],
        "step_value": [upper[:half], upper[half:]], "step_expected": ["", ""],
    }, follow_redirects=False)

    assert response.status_code == 400
    assert "split across" in response.text
    assert ProjectStore("demo", scratch_root).list_cases() == []
