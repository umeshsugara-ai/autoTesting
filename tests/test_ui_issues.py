"""Video-issues page and workbook download tests."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from autotester.schema.enums import IssueCategory
from autotester.schema.issue import Issue
from autotester.schema.project import Project
from autotester.stages.issues import ISSUE_COLUMNS
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectStore:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    result = ProjectStore("demo", tmp_path)
    result.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                                allowed_domains=["demo.test"]))
    return result


def _hostile_issue() -> Issue:
    return Issue(project="demo", source_id="src_one", recording_label="Demo clip", at_s=4,
                 screen="Login", title="<script>alert(1)</script>",
                 what_is_wrong="Submit does nothing", category=IssueCategory.LOGIC_ERROR)


def test_issues_page_escapes_persisted_issue(store: ProjectStore) -> None:
    store.add_issue(_hostile_issue())
    response = TestClient(app).get("/projects/demo/issues")
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


def test_issues_workbook_has_the_human_thirteen_column_header(store: ProjectStore) -> None:
    store.add_issue(_hostile_issue())
    response = TestClient(app).get("/projects/demo/issues.xlsx")
    assert response.status_code == 200
    sheet = load_workbook(BytesIO(response.content)).active
    assert [cell.value for cell in sheet[1]] == ISSUE_COLUMNS
