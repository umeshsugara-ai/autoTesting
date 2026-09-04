"""Agent fallback loop. Contract: qa/contracts/agent-loop.md AL1-AL5."""

from __future__ import annotations

from pathlib import Path

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.providers.mock import MockProvider
from autotester.schema.case import AgentFix, Case
from autotester.schema.enums import Action, CaseClass, CaseKind
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.stages.agent_loop import MAX_ITERATIONS, run_with_fallback

LOGIN = "https://app.pathlynks.test/login"


class FakeLocator:
    def __init__(self, page: FakePage, selector: str) -> None:
        self.page, self.selector = page, selector

    def click(self) -> None:
        if self.selector in self.page.broken_selectors:
            raise RuntimeError(f"element not found: {self.selector}")
        self.page.clicks.append(self.selector)

    def evaluate(self, script: str) -> None:
        pass

    def fill(self, value: str) -> None:
        self.page.filled[self.selector] = value


class FakePage:
    def __init__(self, broken_selectors: set[str]) -> None:
        self.url = LOGIN
        self.broken_selectors = broken_selectors
        self.clicks: list[str] = []
        self.filled: dict[str, str] = {}
        self.styles: list[str] = []
        self.shots: list[str] = []

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    def add_style_tag(self, content: str) -> None:
        self.styles.append(content)

    def screenshot(self, path: str, full_page: bool = False) -> None:
        self.shots.append(path)
        Path(path).write_bytes(b"png")

    def goto(self, url: str, wait_until: str = "") -> None:
        self.url = url

    def wait_for_load_state(self, state: str = "load", timeout: int = 0) -> None:
        pass

    def wait_for_timeout(self, timeout_ms: int) -> None:
        pass


def make_project() -> Project:
    return Project(slug="pathlynks", name="Pathlynks", base_url=LOGIN,
                    allowed_domains=["pathlynks.test"], secrets=[])


def session_with(tmp_path: Path, broken_selectors: set[str]) -> BrowserSession:
    paths = ProjectPaths("pathlynks", tmp_path)
    store = SecretStore.load(make_project(), tmp_path / ".env")
    s = BrowserSession(make_project(), store, tmp_path / "run", paths)
    s._page = FakePage(broken_selectors)
    s.state.run_dir.mkdir(parents=True, exist_ok=True)
    return s


def make_case(target: str = "button.old") -> Case:
    return Case(
        project="pathlynks", flow_id="flow_login", kind=CaseKind.BEST,
        case_class=CaseClass.HAPPY, title="log in", rationale="proves login works",
        steps=[
            Step(order=1, action=Action.NAVIGATE, target=LOGIN),
            Step(order=2, action=Action.CLICK, target=target),
        ],
    )


# -- AL1 a clean run never calls the agent ------------------------------------

def test_no_error_never_calls_the_agent(tmp_path: Path) -> None:
    session = session_with(tmp_path, broken_selectors=set())
    agent = MockProvider()
    loop = run_with_fallback(make_case(), session, agent)

    assert loop.result.outcome.value == "completed"
    assert loop.iterations == 0
    assert loop.fixed is False
    assert agent.prompts == []


# -- AL2 one fix resolves the case, corrected case is persisted correctly ----

def test_one_fix_resolves_a_broken_selector(tmp_path: Path) -> None:
    session = session_with(tmp_path, broken_selectors={"button.old"})
    fix = AgentFix(action=Action.CLICK, target="button.new",
                    reasoning="button.old is not in the DOM per the screenshot")
    agent = MockProvider(responses={"agent": [fix]})

    loop = run_with_fallback(make_case(), session, agent)

    assert loop.result.outcome.value == "completed"
    assert loop.iterations == 1
    assert loop.fixed is True
    assert session.page.clicks == ["button.new"]
    assert loop.case.id != make_case().id  # content-addressed id changed with the fix
    fixed_step = next(s for s in loop.case.steps if s.order == 2)
    assert fixed_step.target == "button.new"
    assert "agent fix" in (fixed_step.note or "")


# -- AL3 exhausts the iteration cap and gives up ------------------------------

def test_exhausts_max_iterations_when_the_fix_never_works(tmp_path: Path) -> None:
    session = session_with(tmp_path, broken_selectors={"button.old", "button.still-broken"})
    always_broken = AgentFix(action=Action.CLICK, target="button.still-broken",
                              reasoning="try a different selector")
    agent = MockProvider(responses={"agent": [always_broken] * MAX_ITERATIONS})

    loop = run_with_fallback(make_case(), session, agent)

    assert loop.result.outcome.value == "errored"
    assert loop.iterations == MAX_ITERATIONS
    assert loop.fixed is False
    assert len(agent.prompts) == MAX_ITERATIONS


# -- AL4 the agent sees only the failing step, not the whole case -------------

def test_prompt_carries_only_the_failing_step_and_error(tmp_path: Path) -> None:
    session = session_with(tmp_path, broken_selectors={"button.old"})
    fix = AgentFix(action=Action.CLICK, target="button.new", reasoning="fixed")
    agent = MockProvider(responses={"agent": [fix]})

    run_with_fallback(make_case(), session, agent)

    assert len(agent.prompts) == 1
    role, prompt = agent.prompts[0]
    assert role == "agent"
    assert "button.old" in prompt
    assert "element not found" in prompt
    assert "log in" in prompt  # case title for context, per the prompt template
