"""The video-request queue on screen, and U5 on the new routes — AT-241.

Split from `test_ui_learn.py` at the 300-line cap, by responsibility: that file
asks whether the review gate and the Generate button work; this one asks whether
the product's "ask me for a video" promise is visible to the human it asks.

coverage.md's no-fire list makes surfacing a `VideoRequest` T-100's job. Until
this page existed the request was written to a file nothing rendered — which,
from the human's side, is not asking at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_ui_learn import _project, _spec, client, scratch_root

from autotester.schema.coverage import CoverageGap, VideoRequest
from autotester.schema.enums import ReviewStatus

__all__ = ["client", "scratch_root"]


# -- the video-request queue -------------------------------------------------

def test_the_requests_page_shows_what_the_system_is_asking_for(
    client: TestClient, scratch_root: Path
) -> None:
    """coverage.md's no-fire list says surfacing a `VideoRequest` is T-100's
    job. Until now T-100 had no such surface, so the request was written to a
    file nothing rendered — which is indistinguishable from not asking."""
    store = _project(scratch_root, spec=_spec(ReviewStatus.APPROVED))
    gap = CoverageGap(project="demo", kind="route", subject="/reports/new",
                      reason="observed '/reports/new' but no screen has this url_pattern")
    store.add_request(VideoRequest(project="demo", gap_id=gap.id,
                                   prompt="Record a short video showing '/reports/new'"))

    response = client.get("/projects/demo/requests")

    assert response.status_code == 200
    assert "/reports/new" in response.text


def test_the_requests_page_is_honest_when_nothing_is_being_asked_for(
    client: TestClient, scratch_root: Path
) -> None:
    _project(scratch_root, spec=_spec(ReviewStatus.APPROVED))

    response = client.get("/projects/demo/requests")

    assert response.status_code == 200
    assert "nothing" in response.text.lower() or "no video" in response.text.lower()


# -- U5, on every new route --------------------------------------------------

@pytest.mark.parametrize("route", ["/projects/demo/flowspec", "/projects/demo/requests"])
def test_the_new_pages_escape_project_data(
    client: TestClient, scratch_root: Path, route: str
) -> None:
    """ui.md U5. Two new GET routes render a project `name`, so both get the
    same hostile probe every existing route was given."""
    _project(scratch_root, spec=_spec(ReviewStatus.DRAFT), name="<script>alert(1)</script>")

    response = client.get(route)

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_the_project_page_offers_the_route_out_of_a_cold_start(
    client: TestClient, scratch_root: Path
) -> None:
    """The dead end AT-241 names: a project with zero cases offered exactly one
    remedy, "+ Add the first case". It must also offer the learning route, or
    the product's own generator stays invisible to the operator."""
    _project(scratch_root)

    response = client.get("/projects/demo")

    assert response.status_code == 200
    assert "/projects/demo/flowspec" in response.text
