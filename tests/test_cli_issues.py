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
from autotester.schema.project import Project, SecretRef
from autotester.store.project_store import ProjectStore

runner = CliRunner()


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectStore:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    result = ProjectStore("demo", tmp_path)
    result.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                                allowed_domains=["demo.test"]))
    return result


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
        "--step", "navigate:https://demo.test/signup",
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
    step = ["--step", "navigate:https://demo.test/signup"]

    first = runner.invoke(app, ["pin", "demo", issue.id, *step])
    second = runner.invoke(app, ["pin", "demo", issue.id, *step])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert len(store.list_cases()) == 1


# -- AT-597 cycle 2: the CLI gets the same guards the UI route already has ---

def test_pin_preserves_a_url_scheme_in_the_navigate_target(store: ProjectStore) -> None:
    """A plain `split(":", 3)` used to cut the URL's own scheme colon as a
    field separator, turning 'https://demo.test/login' into target='https'."""
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, [
        "pin", "demo", issue.id, "--step", "navigate:https://demo.test/login",
    ])

    assert result.exit_code == 0, result.output
    assert store.list_cases()[0].steps[0].target == "https://demo.test/login"


def test_pin_refuses_an_out_of_scope_navigate_step(store: ProjectStore) -> None:
    """Same AT-058/AT-432 guard the UI pin route runs (`_require_reachable_
    navigate_steps`): a step that could never run at execution time is
    refused at pin time too, on the CLI as well as the UI."""
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, [
        "pin", "demo", issue.id, "--step", "navigate:https://not-allowed.test/x",
    ])

    assert result.exit_code != 0
    assert "could never run" in result.output
    assert store.list_cases() == []


def test_pin_refuses_a_raw_secret_value(store: ProjectStore) -> None:
    """C5: `cases.jsonl` is git-tracked in a public repo -- a raw declared
    credential typed into a step must be refused exactly like the UI's pin
    route refuses it (400 there, non-zero exit here), and nothing pinned."""
    store.save_project(Project(
        slug="demo", name="Demo", base_url="https://demo.test",
        allowed_domains=["demo.test"],
        secrets=[SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])],
    ))
    (store.paths.root / ".env").write_text("DEMO_PASSWORD=SuperSecretRaw123\n", encoding="utf-8")
    issue = _an_issue()
    store.add_issue(issue)

    result = runner.invoke(app, [
        "pin", "demo", issue.id,
        "--step", "navigate:https://demo.test/signup",
        "--step", "fill:#password:SuperSecretRaw123",
    ])

    assert result.exit_code != 0
    assert "looks like it contains a real credential" in result.output
    assert store.list_cases() == []
    cases_file = store.paths.cases
    assert not cases_file.exists() or "SuperSecretRaw123" not in cases_file.read_text(
        encoding="utf-8")


def test_pin_refuses_a_second_pin_of_the_same_issue_with_different_steps(
    store: ProjectStore,
) -> None:
    """AT-604: `Case.id` is content-addressed on its steps, so re-pinning the
    same issue with different steps would otherwise create a second pinned
    case for the same finding instead of colliding with the first."""
    issue = _an_issue()
    store.add_issue(issue)
    runner.invoke(app, ["pin", "demo", issue.id, "--step", "navigate:https://demo.test/signup"])

    result = runner.invoke(app, [
        "pin", "demo", issue.id, "--step", "navigate:https://demo.test/other",
    ])

    assert result.exit_code != 0
    assert "already pinned as case" in result.output
    assert len(store.list_cases()) == 1
