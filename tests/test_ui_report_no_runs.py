"""A report download on a project with no runs is a page, not a crash. AT-431.

Found by live-browser validation: `GET /projects/<slug>/report.html` and
`/report.xlsx` answered **500** on a project that had never been run, because
`report_export._latest_run_id` raises `ValueError("no runs exist yet ...")` and
neither download route caught it. The /report page hides the buttons when there
are no runs, so this is reached by a bookmarked or shared URL — exactly the case
where a person has no other hint about what went wrong.

Split from `test_ui_report.py` (doctor's 300-line rule) along a real seam: that
file proves a report with runs downloads; this one proves one without runs says so.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app

_DOWNLOADS = ["/projects/demo/report.xlsx", "/projects/demo/report.html"]


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectStore:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    s = ProjectStore("demo", tmp_path)
    s.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                           allowed_domains=["demo.test"]))
    return s


@pytest.fixture
def client() -> TestClient:
    # raise_server_exceptions=False: the defect WAS an unhandled exception, and
    # the default client would re-raise it instead of showing the 500 a browser saw.
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("url", _DOWNLOADS)
def test_a_download_with_no_runs_is_a_themed_404_not_a_500(
    client: TestClient, store: ProjectStore, url: str,
) -> None:
    response = client.get(url)

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html"), "a page, not a file"
    assert "No runs yet" in response.text
    assert "/projects/demo/report" in response.text, "a way back to the report"


@pytest.mark.parametrize("url", _DOWNLOADS)
def test_run_artifacts_without_a_run_envelope_still_count_as_no_runs(
    client: TestClient, store: ProjectStore, url: str,
) -> None:
    """A crawl leaves directories under runs/ that are not runs. The report page
    already ignores them; the download must agree with it rather than 500."""
    (store.paths.runs_dir / "crawl_latest").mkdir(parents=True)

    response = client.get(url)

    assert response.status_code == 404
    assert "No runs yet" in response.text
