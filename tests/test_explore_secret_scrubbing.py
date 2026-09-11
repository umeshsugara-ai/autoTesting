"""AT-341/AT-350: a resolved secret must never reach a persisted crawl
artifact through an exception's own message. Contract:
qa/contracts/browser-and-secrets.md B4, qa/contracts/core-invariants.md C5.

Split from test_explore_error_causes.py once that file passed doctor's
300-line cap — this is one coherent concern (the credential boundary,
post-AT-076), not a grab-bag of swallowed-cause tests.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from crawl_fake import grant_crawl_approval

from autotester.browser.observe import PageObserver
from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.schema.enums import Action, EdgeOutcome, IssueKind
from autotester.schema.project import Project, SecretRef
from autotester.stages import explore_node
from autotester.stages.explore import run_crawl
from autotester.store.project_store import ProjectStore

SECRET_VALUE = "zorro-battery-42"


def _rt_with_secret(tmp_path: Path) -> SimpleNamespace:
    project = Project(slug="demo", name="Demo", base_url="https://app.test",
                      allowed_domains=["app.test"],
                      secrets=[SecretRef(key="DEMO_TOKEN", domains=["app.test"])])
    env = tmp_path / ".env"
    env.write_text(f"DEMO_TOKEN={SECRET_VALUE}\n", encoding="utf-8")
    session = BrowserSession(project, SecretStore.load(project, env),
                             tmp_path / "shots", ProjectPaths("demo", tmp_path))
    saved: dict[str, list] = {"issues": [], "edges": []}
    store = SimpleNamespace(
        add_crawl_issue=lambda issue: saved["issues"].append(issue),
        add_edge=lambda edge: saved["edges"].append(edge),
    )
    rt = SimpleNamespace(
        session=session, project=project, store=store, saved=saved,
        crawl=SimpleNamespace(id="crawl_1"), tool_failures=0, issues=0, edges=0,
    )
    return rt


# -- AT-341: a secret leaking into a crawl issue / edge reason ---------------

def test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting(
    tmp_path: Path,
) -> None:
    rt = _rt_with_secret(tmp_path)

    explore_node.add_issue(rt, "node_1", IssueKind.NAVIGATION,
                           f"refused: destination contained {SECRET_VALUE}")

    saved = rt.saved["issues"][0]
    assert SECRET_VALUE not in saved.detail
    assert "REDACTED" in saved.detail


def test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting(
    tmp_path: Path,
) -> None:
    from autotester.schema.screen_graph import ElementRef

    rt = _rt_with_secret(tmp_path)
    el = ElementRef(role="link", name="Sneaky", selector="#sneaky")

    explore_node.record_edge(rt, SimpleNamespace(id="node_1"), el, Action.NAVIGATE,
                             EdgeOutcome.OFF_DOMAIN_REFUSED,
                             f"timeout near text '{SECRET_VALUE}'")

    saved = rt.saved["edges"][0]
    assert SECRET_VALUE not in (saved.reason or "")
    assert "REDACTED" in (saved.reason or "")


# -- AT-350: the same leak, at the seed/login-precheck call site ------------

def test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl(
    tmp_path: Path,
) -> None:
    """Unlike AT-341 (execute.py / explore_node.py), this is the
    seed/login-precheck call site in explore.py itself — a goto() failure
    that is NOT NavigationRefused (a real Playwright timeout/net:: error
    characteristically echoes the destination it was navigating to) must
    not leave the resolved secret in the persisted Crawl.stop_reason."""
    project = Project(slug="demo", name="Demo", base_url="https://app.test",
                      allowed_domains=["app.test"],
                      secrets=[SecretRef(key="DEMO_TOKEN", domains=["app.test"])])
    env = tmp_path / ".env"
    env.write_text(f"DEMO_TOKEN={SECRET_VALUE}\n", encoding="utf-8")
    session = BrowserSession(project, SecretStore.load(project, env),
                             tmp_path / "shots", ProjectPaths("demo", tmp_path))
    session._page = SimpleNamespace()
    session.state.run_dir.mkdir(parents=True, exist_ok=True)

    def boom(_url: str) -> None:
        raise RuntimeError(f"net::ERR_CONNECTION_RESET at https://app.test/?t={SECRET_VALUE}")

    session.goto = boom  # type: ignore[method-assign]
    store = ProjectStore("demo", tmp_path)
    grant_crawl_approval(store, project)

    crawl = run_crawl(project, session, store, observer=PageObserver())

    assert SECRET_VALUE not in (crawl.stop_reason or "")
    assert "REDACTED" in (crawl.stop_reason or "")
