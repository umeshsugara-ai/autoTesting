"""Contract: qa/contracts/run-case-pipeline.md RP1-RP4."""

from __future__ import annotations

from pathlib import Path

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.providers.mock import MockProvider
from autotester.schema.case import Case
from autotester.schema.enums import Action, CaseClass, CaseKind, Outcome, Result
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.schema.verdict import Judgment
from autotester.stages.run_case_pipeline import default_rubric, run_and_grade_case
from autotester.store.project_store import ProjectStore


class _FakePage:
    """Just enough of a Playwright page for execute.py::run_case's NAVIGATE step."""

    def __init__(self, url: str) -> None:
        self.url = url

    def add_style_tag(self, content: str) -> None:
        pass

    def screenshot(self, path: str, full_page: bool = False) -> None:
        Path(path).write_bytes(b"png")

    def goto(self, url: str, wait_until: str = "") -> None:
        self.url = url


def _project() -> Project:
    return Project(slug="demo", name="Demo", base_url="https://demo.test",
                    allowed_domains=["demo.test"])


def _case(rationale: str | None = "the page shows a welcome message") -> Case:
    return Case(project="demo", flow_id="flow-home", kind=CaseKind.BEST,
                case_class=CaseClass.HAPPY, title="Homepage loads", rationale=rationale,
                steps=[Step(order=1, action=Action.NAVIGATE, target="https://demo.test/")])


def _session(tmp_path: Path) -> BrowserSession:
    paths = ProjectPaths("demo", tmp_path)
    secrets = SecretStore.load(_project(), paths.env_file, strict=False)
    s = BrowserSession(_project(), secrets, tmp_path / "run", paths)
    s._page = _FakePage("https://demo.test/")
    s.state.run_dir.mkdir(parents=True, exist_ok=True)
    return s


def test_default_rubric_is_grounded_in_the_cases_own_rationale() -> None:
    rubric = default_rubric(_case(), "rub_x")
    assert "welcome message" in rubric.criteria[0].text
    assert rubric.criteria[0].id == "c1"


def test_default_rubric_falls_back_to_title_when_no_rationale() -> None:
    rubric = default_rubric(_case(rationale=None), "rub_x")
    assert "Homepage loads" in rubric.criteria[0].text


def test_run_and_grade_case_builds_and_persists_a_default_rubric_when_none_exists(
    tmp_path: Path,
) -> None:
    store = ProjectStore("demo", tmp_path)
    store.save_project(_project())
    case = _case()
    judge = MockProvider(responses={"judge": [
        Judgment(result=Result.PASS, criteria_met=1, criteria_total=1, scoreboard="1/1 met")
    ]})

    result, verdict = run_and_grade_case(case, _session(tmp_path), judge, "run_1", store)

    assert result.outcome is Outcome.COMPLETED
    assert verdict.result is Result.PASS
    persisted = store.load_rubric(f"rub_{case.id}")
    assert persisted is not None
    assert persisted.criteria[0].id == "c1"


def test_run_and_grade_case_reuses_an_existing_rubric_instead_of_overwriting_it(
    tmp_path: Path,
) -> None:
    store = ProjectStore("demo", tmp_path)
    store.save_project(_project())
    case = _case()
    hand_written = default_rubric(case, f"rub_{case.id}")
    hand_written.criteria[0].text = "a hand-tuned criterion, not the default"
    store.save_rubric(hand_written)
    judge = MockProvider(responses={"judge": [
        Judgment(result=Result.PASS, criteria_met=1, criteria_total=1, scoreboard="1/1 met")
    ]})

    run_and_grade_case(case, _session(tmp_path), judge, "run_1", store)

    reloaded = store.load_rubric(f"rub_{case.id}")
    assert reloaded is not None
    assert reloaded.criteria[0].text == "a hand-tuned criterion, not the default"
