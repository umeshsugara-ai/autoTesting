"""Run trigger. Contract: qa/contracts/ui-run.md RU1-RU4. Split out of
test_ui.py to match ui/routes_runs.py's own module split and stay under the
300-line design rule. A real browser is mocked out (BrowserSession.start/close,
run_and_grade_case) — the route's own control flow (case lookup, provider
availability, persistence, redirect) is exercised for real.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.enums import Outcome, Result
from autotester.schema.run import RawResult
from autotester.schema.verdict import Verdict
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _onboard_demo(client: TestClient) -> None:
    client.post("/onboard", data={
        "slug": "demo", "name": "Demo", "base_url": "https://demo.test",
        "allowed_domains": "demo.test",
    })


def test_run_refuses_a_project_with_no_cases(client: TestClient, scratch_root: Path) -> None:
    _onboard_demo(client)
    response = client.post("/projects/demo/run", follow_redirects=False)
    assert response.status_code == 400
    assert "no cases" in response.text


def test_run_refuses_when_no_ai_provider_is_configured(
    client: TestClient, scratch_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from autotester.schema.case import Case
    from autotester.schema.enums import Action, CaseClass, CaseKind
    from autotester.schema.flowspec import Step

    _onboard_demo(client)
    ProjectStore("demo", scratch_root).add_case(Case(
        project="demo", flow_id="flow-home", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Homepage loads",
        steps=[Step(order=1, action=Action.NAVIGATE, target="https://demo.test/")],
    ))

    class _UnavailableProvider:
        def available(self) -> bool:
            return False

    import autotester.ui.routes_runs as routes_runs_module

    monkeypatch.setattr(routes_runs_module, "LangChainFallbackProvider", _UnavailableProvider)

    response = client.post("/projects/demo/run", follow_redirects=False)

    assert response.status_code == 400
    assert "no AI provider" in response.text


def test_run_executes_every_case_and_redirects_to_the_report(
    client: TestClient, scratch_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from autotester.browser.session import BrowserSession
    from autotester.schema.case import Case
    from autotester.schema.enums import Action, CaseClass, CaseKind
    from autotester.schema.flowspec import Step

    _onboard_demo(client)
    store = ProjectStore("demo", scratch_root)
    case = store.add_case(Case(
        project="demo", flow_id="flow-home", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Homepage loads",
        steps=[Step(order=1, action=Action.NAVIGATE, target="https://demo.test/")],
    ))

    monkeypatch.setattr(BrowserSession, "start", lambda self: self)
    monkeypatch.setattr(BrowserSession, "close", lambda self: None)

    class _AvailableProvider:
        def available(self) -> bool:
            return True

    calls = []

    def fake_run_and_grade_case(case_, session, judge, run_id, store_):
        calls.append(case_.id)
        result = RawResult(case_id=case_.id, outcome=Outcome.COMPLETED)
        verdict = Verdict(run_id=run_id, case_id=case_.id, result=Result.PASS,
                           grader_provider="mock")
        return result, verdict

    import autotester.ui.routes_runs as routes_runs_module

    monkeypatch.setattr(routes_runs_module, "LangChainFallbackProvider", _AvailableProvider)
    monkeypatch.setattr(routes_runs_module, "run_and_grade_case", fake_run_and_grade_case)

    response = client.post("/projects/demo/run", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/projects/demo/report"
    assert calls == [case.id]
    verdicts = {v.case_id: v for v in store.load_verdicts(_only_run_id(store))}
    assert verdicts[case.id].result is Result.PASS


def _only_run_id(store: ProjectStore) -> str:
    run_ids = sorted(p.name for p in store.paths.runs_dir.iterdir() if p.is_dir())
    assert len(run_ids) == 1
    return run_ids[0]


def test_run_button_appears_only_when_the_project_has_cases(
    client: TestClient, scratch_root: Path
) -> None:
    _onboard_demo(client)
    without_cases = client.get("/projects/demo").text
    assert "no cases yet" in without_cases

    from autotester.schema.case import Case
    from autotester.schema.enums import Action, CaseClass, CaseKind
    from autotester.schema.flowspec import Step

    ProjectStore("demo", scratch_root).add_case(Case(
        project="demo", flow_id="flow-home", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Homepage loads",
        steps=[Step(order=1, action=Action.NAVIGATE, target="https://demo.test/")],
    ))
    with_cases = client.get("/projects/demo").text
    assert "action='/projects/demo/run'" in with_cases
