"""`autotester issues pin` — the CLI half of AT-597's issue -> pinned Case path.

Sibling to the UI action in `ui/routes_issues.py`: same `pin_issue_as_case`
constructor (T-184, AT-585), a different human-facing entry point for anyone
scripting the tester workflow instead of clicking through the browser.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from autotester.cli_issues import app
from autotester.schema.enums import IssueCategory
from autotester.schema.issue import Issue
from autotester.store.project_store import ProjectStore

runner = CliRunner()


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectStore:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return ProjectStore("demo", tmp_path)


def _an_issue(**kw) -> Issue:
    return Issue(
        project="demo", source_id="src_one", recording_label="Demo clip", at_s=4,
        screen="Signup", title=kw.pop("title", "Google sign-in drops the data filled at signup"),
        what_is_wrong="fields filled before the Google redirect are gone on return",
        category=IssueCategory.LOGIC_ERROR, **kw,
    )


def test_pin_creates_a_protected_case_from_confirmed_steps(store: ProjectStore) -> None:
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, [
        "pin", "demo", issue.id,
        "--step", "navigate:/signup",
        "--step", "click:#google-sign-in::signup form still has my email",
    ])

    assert result.exit_code == 0, result.output
    cases = store.list_cases()
    assert len(cases) == 1
    assert cases[0].pinned is True
    assert cases[0].pinned_issue_id == issue.id
    assert cases[0].steps[0].order == 1
    assert cases[0].steps[1].value is None
    assert cases[0].steps[1].expected.visible_text == ["signup form still has my email"]


def test_pin_an_unknown_issue_fails_clearly(store: ProjectStore) -> None:
    result = runner.invoke(app, ["pin", "demo", "iss_nope", "--step", "navigate:/x"])

    assert result.exit_code != 0
    assert "no issue" in result.output.lower()
    assert store.list_cases() == []


def test_pin_requires_at_least_one_step(store: ProjectStore) -> None:
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, ["pin", "demo", issue.id])

    assert result.exit_code != 0
    assert "at least one confirmed --step" in result.output
    assert store.list_cases() == []


def test_pin_rejects_an_unparseable_step(store: ProjectStore) -> None:
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, ["pin", "demo", issue.id, "--step", "not-a-valid-step"])

    assert result.exit_code != 0
    assert "must look like" in result.output
    assert store.list_cases() == []


def test_pin_rejects_an_unknown_action(store: ProjectStore) -> None:
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, ["pin", "demo", issue.id, "--step", "flibber:/x"])

    assert result.exit_code != 0
    assert "is not one of" in result.output
    assert store.list_cases() == []


def test_pinning_the_same_issue_and_steps_twice_is_idempotent(store: ProjectStore) -> None:
    issue = _an_issue()
    store.add_issue(issue)
    step = ["--step", "navigate:/signup"]

    first = runner.invoke(app, ["pin", "demo", issue.id, *step])
    second = runner.invoke(app, ["pin", "demo", issue.id, *step])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert len(store.list_cases()) == 1
