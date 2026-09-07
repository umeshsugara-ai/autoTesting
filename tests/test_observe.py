"""`browser/observe.py`: PageObserver (console/network/dialog capture) and
`enumerate_elements`. Track B1 — no real browser needed, a fake page with
`.on(event, handler)` and `.evaluate(js)` exercises the whole seam.
"""

from __future__ import annotations

from typing import Any

from autotester.browser.observe import PageObserver, enumerate_elements, observe
from autotester.schema.screen_graph import ElementRef


class FakeDialog:
    def __init__(self, dialog_type: str, message: str = "") -> None:
        self.type = dialog_type
        self.message = message
        self.accepted = False
        self.dismissed = False

    def accept(self) -> None:
        self.accepted = True

    def dismiss(self) -> None:
        self.dismissed = True


class FakeConsoleMessage:
    def __init__(self, kind: str, text: str) -> None:
        self.type = kind
        self.text = text


class FakeRequest:
    def __init__(self, url: str, error_text: str = "net::ERR_FAILED") -> None:
        self.url = url
        self.failure = {"errorText": error_text}


class FakeResponse:
    def __init__(self, url: str, status: int) -> None:
        self.url = url
        self.status = status


class FakeContext:
    def __init__(self) -> None:
        self.handlers: dict[str, list[Any]] = {}

    def on(self, event: str, handler: Any) -> None:
        self.handlers.setdefault(event, []).append(handler)


class FakePage:
    def __init__(self, url: str = "https://app.test/", elements: list[dict] | None = None) -> None:
        self.url = url
        self.context = FakeContext()
        self.handlers: dict[str, list[Any]] = {}
        self._elements = elements or []

    def on(self, event: str, handler: Any) -> None:
        self.handlers.setdefault(event, []).append(handler)

    def evaluate(self, script: str) -> list[dict]:
        return self._elements

    def title(self) -> str:
        return "Test Page"


# -- PageObserver.attach installs exactly the five listeners, once ----------

def test_attach_installs_console_requestfailed_response_dialog_and_popup_once() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    observer.attach(page)  # second attach is a no-op

    assert list(page.handlers.keys()) == ["console", "requestfailed", "response", "dialog"]
    assert all(len(handlers) == 1 for handlers in page.handlers.values())
    assert list(page.context.handlers.keys()) == ["page"]
    assert len(page.context.handlers["page"]) == 1


# -- dialogs: beforeunload accepted, everything else dismissed --------------

def test_beforeunload_dialog_is_accepted() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    dialog_handler = page.handlers["dialog"][0]

    dialog = FakeDialog("beforeunload")
    dialog_handler(dialog)

    assert dialog.accepted is True
    assert dialog.dismissed is False
    assert observer.dialogs[0].accepted is True


def test_confirm_dialog_is_dismissed() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    dialog_handler = page.handlers["dialog"][0]

    dialog = FakeDialog("confirm", "Are you sure?")
    dialog_handler(dialog)

    assert dialog.dismissed is True
    assert dialog.accepted is False
    assert observer.dialogs[0].message == "Are you sure?"


def test_custom_dialog_action_is_honoured() -> None:
    page = FakePage()
    observer = PageObserver(dialog_action=lambda _t: "accept")
    observer.attach(page)
    dialog_handler = page.handlers["dialog"][0]

    dialog = FakeDialog("alert")
    dialog_handler(dialog)

    assert dialog.accepted is True


# -- console/network capture -------------------------------------------------

def test_console_errors_and_warnings_are_captured_info_is_not() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    console_handler = page.handlers["console"][0]

    console_handler(FakeConsoleMessage("error", "boom"))
    console_handler(FakeConsoleMessage("warning", "careful"))
    console_handler(FakeConsoleMessage("info", "fyi"))

    assert observer.console == ["error: boom", "warning: careful"]


def test_failed_requests_and_4xx_responses_are_captured() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    request_handler = page.handlers["requestfailed"][0]
    response_handler = page.handlers["response"][0]

    request_handler(FakeRequest("https://app.test/api/x"))
    response_handler(FakeResponse("https://app.test/api/y", 404))
    response_handler(FakeResponse("https://app.test/ok", 200))

    assert ("https://app.test/api/x", "net::ERR_FAILED") in observer.failed
    assert ("https://app.test/api/y", "404") in observer.failed
    assert len(observer.failed) == 2


def test_popup_pages_are_counted() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    popup_handler = page.context.handlers["page"][0]

    popup_handler(object())
    popup_handler(object())

    assert observer.popups == 2


def test_drain_returns_and_clears_everything() -> None:
    page = FakePage()
    observer = PageObserver()
    observer.attach(page)
    page.handlers["console"][0](FakeConsoleMessage("error", "x"))

    console, failed, dialogs, popups = observer.drain()

    assert console == ["error: x"]
    assert observer.console == []
    assert (failed, dialogs, popups) == ([], [], 0)


# -- enumerate_elements / observe --------------------------------------------

def test_enumerate_elements_validates_into_element_ref() -> None:
    page = FakePage(elements=[
        {"role": "button", "name": "Submit", "selector": "#submit", "enabled": True,
         "visible": True, "href": None, "is_form_submit": True, "in_row": False,
         "target_blank": False, "tag": "button"},
    ])
    elements = enumerate_elements(page)
    assert len(elements) == 1
    assert isinstance(elements[0], ElementRef)
    assert elements[0].name == "Submit"
    assert elements[0].is_form_submit is True


def test_observe_returns_url_title_and_elements() -> None:
    page = FakePage(url="https://app.test/dashboard", elements=[
        {"role": "link", "name": "Home", "selector": "a.home"},
    ])

    class FakeSession:
        def __init__(self, page: FakePage) -> None:
            self.page = page

    result = observe(FakeSession(page))
    assert result.url == "https://app.test/dashboard"
    assert result.title == "Test Page"
    assert result.elements[0].name == "Home"
