"""Track B1: the four new `BrowserSession` actions (go_back/hover/press_key/
scroll) and `current_url`. New file — `test_browser.py` is already near the
300-line cap. Same FakePage pattern as `test_browser.py`/`test_execute.py`.
"""

from __future__ import annotations

from pathlib import Path

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession, launch_options
from autotester.core.paths import ProjectPaths
from autotester.schema.enums import EvidenceKind
from autotester.schema.project import Project, SecretRef

LOGIN = "https://app.pathlynks.test/login"


class FakeLocator:
    def __init__(self, page: FakePage, selector: str) -> None:
        self.page, self.selector = page, selector

    def hover(self) -> None:
        self.page.hovers.append(self.selector)

    def press(self, key: str) -> None:
        self.page.presses.append((self.selector, key))


class FakeKeyboard:
    def __init__(self, page: FakePage) -> None:
        self.page = page

    def press(self, key: str) -> None:
        self.page.presses.append((None, key))


class FakeMouse:
    def __init__(self, page: FakePage) -> None:
        self.page = page

    def wheel(self, dx: int, dy: int) -> None:
        self.page.wheels.append((dx, dy))


class FakePage:
    def __init__(self, url: str) -> None:
        self.url = url
        self.hovers: list[str] = []
        self.presses: list[tuple[str | None, str]] = []
        self.wheels: list[tuple[int, int]] = []
        self.back_calls = 0
        self.keyboard = FakeKeyboard(self)
        self.mouse = FakeMouse(self)

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    def go_back(self, wait_until: str = "") -> None:
        self.back_calls += 1
        self.url = "https://app.pathlynks.test/"


def make_project() -> Project:
    return Project(
        slug="pathlynks", name="Pathlynks", base_url=LOGIN,
        allowed_domains=["pathlynks.test"],
        secrets=[SecretRef(key="PATHLYNKS_PASSWORD", domains=["pathlynks.test"])],
    )


def make_store(tmp_path: Path) -> SecretStore:
    env = tmp_path / ".env"
    env.write_text("PATHLYNKS_PASSWORD=hunter2\n", encoding="utf-8")
    return SecretStore.load(make_project(), env)


def session_with_fake_page(tmp_path: Path) -> BrowserSession:
    paths = ProjectPaths("pathlynks", tmp_path)
    s = BrowserSession(make_project(), make_store(tmp_path), tmp_path / "run", paths)
    s._page = FakePage(LOGIN)
    s.state.run_dir.mkdir(parents=True, exist_ok=True)
    return s


def test_launch_options_still_importable_from_session_after_the_move(tmp_path: Path) -> None:
    """`launch_options` moved to `browser/launch.py` (B1) — must remain
    importable from `session` (existing callers/tests) with identical output."""
    from autotester.browser.launch import launch_options as moved

    paths = ProjectPaths("pathlynks", tmp_path)
    assert launch_options(make_project(), paths) == moved(make_project(), paths)


def test_current_url_reads_the_page_without_a_direct_page_touch(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    assert s.current_url() == LOGIN


def test_go_back_calls_the_page_and_records_url_evidence(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    ev = s.go_back(step_order=3)
    assert s.page.back_calls == 1
    assert ev.kind is EvidenceKind.DOM or ev.kind is EvidenceKind.URL
    assert ev.label == "back"
    assert ev.step_order == 3


def test_hover_composes_the_locator(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    ev = s.hover("a.nav-link", step_order=1)
    assert s.page.hovers == ["a.nav-link"]
    assert "hovered" in (ev.label or ev.path)


def test_press_key_with_a_locator_targets_that_element(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    s.press_key("Enter", "input[name=email]", step_order=2)
    assert s.page.presses == [("input[name=email]", "Enter")]


def test_press_key_without_a_locator_uses_the_keyboard(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    s.press_key("Escape")
    assert s.page.presses == [(None, "Escape")]


def test_scroll_uses_the_mouse_wheel_with_a_default_delta(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    s.scroll()
    assert s.page.wheels == [(0, 800)]


def test_scroll_accepts_a_custom_delta(tmp_path: Path) -> None:
    s = session_with_fake_page(tmp_path)
    s.scroll(delta_y=200)
    assert s.page.wheels == [(0, 200)]
