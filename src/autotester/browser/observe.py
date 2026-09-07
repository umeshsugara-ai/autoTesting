"""Passive observation: enumerate a page's controls, capture console/network
failures and dialogs. The explorer (Track B3) reads through this — never
`.page` directly — so every browser touch stays inside `browser/` (the
actuator choke-point, `tests/test_actuator_chokepoint.py`).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from autotester.schema.crawl import DialogEvent
from autotester.schema.screen_graph import ElementRef, PageObservation

_ENUMERATE_JS = (Path(__file__).with_name("enumerate.js")).read_text(encoding="utf-8")

DialogAction = Callable[[str], str]  # dialog_type -> "accept" | "dismiss"


def _default_dialog_action(dialog_type: str) -> str:
    """`beforeunload` is accepted (leave the page); every other dialog is
    dismissed — the crawl never blocks on a confirm/alert/prompt (D-016)."""
    return "accept" if dialog_type == "beforeunload" else "dismiss"


class PageObserver:
    """Installed once per session (`BrowserSession(..., observer=...)`).
    Buffers console errors, failed/4xx+ requests, dialogs, and popup counts
    until `drain()` is called."""

    def __init__(self, dialog_action: DialogAction | None = None) -> None:
        self.dialog_action = dialog_action or _default_dialog_action
        self.console: list[str] = []
        self.failed: list[tuple[str, str]] = []
        self.dialogs: list[DialogEvent] = []
        self.popups = 0
        self._attached = False

    def attach(self, page: Any) -> None:
        """Install listeners exactly once. Safe to call more than once — a
        second `attach` on the same observer is a no-op."""
        if self._attached:
            return
        self._attached = True
        page.on("console", self._on_console)
        page.on("requestfailed", self._on_request_failed)
        page.on("response", self._on_response)
        page.on("dialog", self._on_dialog)
        if page.context is not None:
            page.context.on("page", self._on_popup)

    def _on_console(self, message: Any) -> None:
        if getattr(message, "type", "") in ("error", "warning"):
            self.console.append(f"{message.type}: {message.text}")

    def _on_request_failed(self, request: Any) -> None:
        failure = getattr(request, "failure", None)
        reason = failure.get("errorText", "failed") if isinstance(failure, dict) else "failed"
        self.failed.append((request.url, reason))

    def _on_response(self, response: Any) -> None:
        if response.status >= 400:
            self.failed.append((response.url, str(response.status)))

    def _on_dialog(self, dialog: Any) -> None:
        action = self.dialog_action(dialog.type)
        accepted = action == "accept"
        self.dialogs.append(
            DialogEvent(dialog_type=dialog.type, message=dialog.message or "", accepted=accepted)
        )
        if accepted:
            dialog.accept()
        else:
            dialog.dismiss()

    def _on_popup(self, _page: Any) -> None:
        self.popups += 1

    def drain(self) -> tuple[list[str], list[tuple[str, str]], list[DialogEvent], int]:
        """Return and clear everything buffered since the last drain."""
        console, failed, dialogs, popups = self.console, self.failed, self.dialogs, self.popups
        self.console, self.failed, self.dialogs, self.popups = [], [], [], 0
        return console, failed, dialogs, popups


def enumerate_elements(page: Any) -> list[ElementRef]:
    """Run `enumerate.js` and validate its output into `ElementRef`s."""
    raw = page.evaluate(_ENUMERATE_JS)
    return [ElementRef(**item) for item in raw]


def observe(session: Any) -> PageObservation:
    """One page-visit's observation: url, title, interactive elements."""
    page = session.page
    return PageObservation(
        url=str(page.url), title=str(page.title()), elements=enumerate_elements(page),
    )
