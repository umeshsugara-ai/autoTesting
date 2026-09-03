"""One real, visible browser session per project. Contract: browser-and-secrets.md B5-B9.

The session owns exactly one persistent Chromium context (so a human login
survives to later runs), refuses to leave the project's domains, types secrets
only through the `SecretStore` boundary, masks secret inputs before every
screenshot, and on teardown closes only what it opened — never another
process's Chrome.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from autotester.browser.secrets import SecretStore, host_of
from autotester.core.paths import ProjectPaths
from autotester.core.redact import PLACEHOLDER_RE
from autotester.schema.enums import EvidenceKind, Outcome
from autotester.schema.project import Project
from autotester.schema.run import Evidence

# CSS applied to secret inputs right before capture. Text becomes unreadable
# without changing layout, so the screenshot still shows *where* the field is.
MASK_CSS = (
    "[data-autotester-secret] { -webkit-text-security: disc !important; "
    "color: transparent !important; text-shadow: 0 0 8px rgba(0,0,0,.6) !important; }"
)
MASK_ATTR = "data-autotester-secret"


class NavigationRefused(RuntimeError):
    """The destination host is outside the project's allowed domains."""


@dataclass
class HitlRequest:
    """The run must pause for a human (OTP, captcha, consent). B8."""

    prompt: str
    outcome: Outcome = Outcome.BLOCKED_HITL


@dataclass
class SessionState:
    """What the session has done so far — the executor reads this, never the page."""

    run_dir: Path
    evidence: list[Evidence] = field(default_factory=list)
    secret_locators: list[str] = field(default_factory=list)
    hitl: HitlRequest | None = None
    screenshots: int = 0


def check_destination(project: Project, url: str) -> str:
    """Return the host if `url` is inside the project's domains, else raise (B6)."""
    host = host_of(url)
    if not host or not project.allows_domain(host):
        raise NavigationRefused(f"'{url}' is outside allowed domains {project.allowed_domains}")
    return host


def launch_options(project: Project, paths: ProjectPaths) -> dict[str, Any]:
    """Arguments for `launch_persistent_context` (B5): headed by default, own profile."""
    paths.profile_dir.mkdir(parents=True, exist_ok=True)
    return {
        "user_data_dir": str(paths.profile_dir),
        "headless": not project.headed,
        "viewport": {"width": 1366, "height": 850},
        "args": [
            "--disable-blink-features=AutomationControlled",
            # Found running this for real under Docker/Xvfb: screenshot capture crashed
            # intermittently ("Protocol error (Page.captureScreenshot): Unable to capture
            # screenshot") on the second persistent-context launch in a process, specifically
            # when Chromium runs as root (the container's default user) without --no-sandbox,
            # and again for the same reason --disable-dev-shm-usage helps in constrained
            # display environments. Both are no-ops on a normal host launch.
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    }


class BrowserSession:
    """Drive one project's browser. Construct, `start()`, act, `close()`.

    Every method that touches the page is small on purpose: the executor stage
    composes them per step and records the returned evidence.
    """

    def __init__(
        self,
        project: Project,
        secrets: SecretStore,
        run_dir: Path,
        paths: ProjectPaths | None = None,
    ) -> None:
        self.project = project
        self.secrets = secrets
        self.paths = paths or ProjectPaths(project.slug)
        self.state = SessionState(run_dir=run_dir)
        self._playwright: Any = None
        self._context: Any = None
        self._page: Any = None

    # -- lifecycle ------------------------------------------------------------
    def start(self) -> BrowserSession:
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            **launch_options(self.project, self.paths)
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.state.run_dir.mkdir(parents=True, exist_ok=True)
        return self

    def close(self) -> None:
        """Close only this session's context and driver (B9). Never a process kill."""
        try:
            if self._context is not None:
                self._context.close()
        finally:
            self._context = None
            self._page = None
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None

    def __enter__(self) -> BrowserSession:
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- actions --------------------------------------------------------------
    @property
    def page(self) -> Any:
        if self._page is None:
            raise RuntimeError("session not started")
        return self._page

    def goto(self, url: str) -> Evidence:
        check_destination(self.project, url)
        self.page.goto(url, wait_until="domcontentloaded")
        return self._record(EvidenceKind.URL, self.page.url)

    def fill(self, locator: str, value: str | None, *, step_order: int | None = None) -> None:
        """Type into `locator`. A `{{SECRET:KEY}}` value is resolved for the CURRENT page
        host only (B2/B3, AT-007: never the intended URL) and the input is tagged for masking."""
        is_secret = bool(value and PLACEHOLDER_RE.search(value))
        real = self.secrets.resolve(value, self.page.url) if is_secret else value
        target = self.page.locator(locator)
        if is_secret:
            target.evaluate(f"el => el.setAttribute('{MASK_ATTR}', '1')")
            self.state.secret_locators.append(locator)
        target.fill(real or "")
        self._record(EvidenceKind.DOM, f"filled {locator}" + (" [secret]" if is_secret else ""),
                     step_order=step_order)

    def click(self, locator: str, *, step_order: int | None = None) -> Evidence:
        self.page.locator(locator).click()
        return self._record(EvidenceKind.DOM, f"clicked {locator}", step_order=step_order)

    def select_option(
        self, locator: str, value: str | None, *, step_order: int | None = None
    ) -> Evidence:
        self.page.locator(locator).select_option(value)
        return self._record(EvidenceKind.DOM, f"selected {value!r} in {locator}",
                             step_order=step_order)

    def upload(self, locator: str, file_path: str, *, step_order: int | None = None) -> Evidence:
        self.page.locator(locator).set_input_files(file_path)
        return self._record(EvidenceKind.DOM, f"uploaded to {locator}", step_order=step_order)

    def wait_for(
        self, locator: str | None, *, timeout_ms: int = 5000, step_order: int | None = None
    ) -> Evidence:
        if locator:
            self.page.locator(locator).wait_for(timeout=timeout_ms)
            label = f"waited for {locator}"
        else:
            self.page.wait_for_timeout(timeout_ms)
            label = f"waited {timeout_ms}ms"
        return self._record(EvidenceKind.DOM, label, step_order=step_order)

    def screenshot(self, label: str, *, step_order: int | None = None) -> Evidence:
        """Capture with every secret input masked first (B7)."""
        self.page.add_style_tag(content=MASK_CSS)
        self.state.screenshots += 1
        name = f"{self.state.screenshots:02d}-{label}.png"
        self.page.screenshot(path=str(self.state.run_dir / name), full_page=False)
        return self._record(EvidenceKind.SCREENSHOT, name, step_order=step_order, label=label)

    def request_human(self, prompt: str) -> HitlRequest:
        """Pause for OTP/2FA (B8). The executor turns this into `blocked_hitl`."""
        self.state.hitl = HitlRequest(prompt=prompt)
        return self.state.hitl

    # -- evidence ---------------------------------------------------------------
    def _record(
        self,
        kind: EvidenceKind,
        path: str,
        *,
        step_order: int | None = None,
        label: str | None = None,
    ) -> Evidence:
        scrubbed = self.secrets.redactor().scrub(path)
        item = Evidence(kind=kind, path=scrubbed, step_order=step_order, label=label, masked=True)
        self.state.evidence.append(item)
        return item
