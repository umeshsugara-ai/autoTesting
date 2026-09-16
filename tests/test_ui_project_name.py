"""A project must have a name — on every route that sets one. AT-430.

Found by live-browser validation, not by any test: `/onboard` accepted a blank or
whitespace-only name, and the project rendered with an empty heading, a
`— AutoTester` tab title and a text-less link in the sidebar on EVERY page. The
browser's `required` attribute was the only guard, and a direct POST ignores it.

The rule already existed — inline, in the edit route only. It also had no test
there, so the one place that got it right was unverified too. Both routes now
call `ui.helpers._require_project_name`, and this file pins both, because a rule
held on one route and not the other is exactly how this defect was born.

Separate from `test_ui.py` (at its line budget) along a real seam: this is the
one invariant "a project has a name", asserted across every route that writes it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.store.project_store import ProjectStore
from autotester.ui.app import app

_VALID = {"base_url": "https://demo.test/signin", "allowed_domains": "demo.test"}


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# -- onboard: the route that had no copy of the rule ---------------------------

@pytest.mark.parametrize("blank", ["", "   ", "\t", " \n "])
def test_onboard_refuses_a_blank_or_whitespace_name(
    client: TestClient, scratch_root: Path, blank: str,
) -> None:
    """The exact defect. A 400 alone is not enough — the assertion that matters is
    that NO project was written, because the harm was the saved project."""
    response = client.post("/onboard", data={"slug": "ghost", "name": blank, **_VALID})

    assert response.status_code == 400
    assert response.json()["detail"] == "a project needs a name"
    assert ProjectStore("ghost", scratch_root).load_project() is None, "nothing may be saved"


def test_a_refused_blank_name_leaves_no_ghost_link_in_the_sidebar(
    client: TestClient, scratch_root: Path,
) -> None:
    """The user-visible symptom, pinned directly: an empty `<a>` for the project
    rendered in the sidebar of every page. Asserting the status code would pass
    while this regressed, if a future change saved first and refused later."""
    client.post("/onboard", data={"slug": "ghost", "name": "  ", **_VALID})

    home = client.get("/")

    assert home.status_code == 200
    assert "/projects/ghost" not in home.text


def test_a_named_project_still_onboards(client: TestClient, scratch_root: Path) -> None:
    """The guard must be able to say yes. A check that refuses everything would
    satisfy every refusal test above."""
    response = client.post("/onboard", data={"slug": "real", "name": "Real", **_VALID})

    assert response.status_code in (200, 303)
    assert ProjectStore("real", scratch_root).load_project().name == "Real"


# -- edit: the route that had the rule, untested, and was just refactored ------

def test_edit_still_refuses_a_blank_name_after_moving_the_rule(
    client: TestClient, scratch_root: Path,
) -> None:
    """The inline check here was replaced by the shared helper. It had no test
    before, so without this one the refactor would have been unverified — and
    the stored name must be untouched, not merely the response a 400."""
    client.post("/onboard", data={"slug": "demo", "name": "Demo", **_VALID})

    response = client.post("/projects/demo/edit", data={"name": "   ", **_VALID})

    assert response.status_code == 400
    assert response.json()["detail"] == "a project needs a name"
    assert ProjectStore("demo", scratch_root).load_project().name == "Demo", "name unchanged"
