"""The crawl pages (Track B5). Contract: qa/contracts/ui.md + explore.md X11."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.schema.crawl import Crawl, CrawlIssue
from autotester.schema.enums import Action, CrawlStatus, EdgeOutcome, IssueKind, ReviewStatus
from autotester.schema.flowspec import FlowSpec, Review, Screen
from autotester.schema.project import Project, SecretRef
from autotester.schema.screen_graph import ScreenEdge, ScreenNode
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def make_project(root: Path) -> ProjectStore:
    store = ProjectStore("demo", root)
    secret = SecretRef(key="DEMO_PASSWORD", domains=["demo.test"])
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"], secrets=[secret]))
    return store


def seed_crawl(store: ProjectStore) -> Crawl:
    crawl = Crawl(project="demo", id="crawl_demo", status=CrawlStatus.STOPPED_BOUND,
                  stop_reason="max_actions", screens=2, actions=9, edges=2, denied=1, issues=1)
    store.save_crawl(crawl)
    home = ScreenNode(crawl_id=crawl.id, project="demo", url_template="demo.test/",
                      url_example="https://demo.test/", signature="s_home", name="Home")
    settings = ScreenNode(crawl_id=crawl.id, project="demo", url_template="demo.test/settings",
                          url_example="https://demo.test/settings", signature="s_set", depth=1,
                          name="Settings")
    store.add_node(home)
    store.add_node(settings)
    store.add_edge(ScreenEdge(crawl_id=crawl.id, from_node=settings.id, action=Action.CLICK,
                              target="#del", name="Delete account",
                              outcome=EdgeOutcome.DENIED_POLICY,
                              reason="destructive-name deny-list"))
    store.add_crawl_issue(CrawlIssue(crawl_id=crawl.id, project="demo", kind=IssueKind.CONSOLE,
                                     node_id=settings.id, detail="TypeError: x is undefined"))
    return crawl


def test_a_project_with_no_crawls_says_so_and_offers_to_explore(
    client: TestClient, scratch_root: Path
) -> None:
    make_project(scratch_root)
    response = client.get("/projects/demo/crawls")
    assert response.status_code == 200
    assert "No crawls yet" in response.text
    assert "/projects/demo/explore" in response.text
    for name in ("max_screens", "max_actions", "wall_clock_s", "max_depth"):
        assert f"name='{name}'" in response.text


def test_the_crawl_page_names_why_the_crawl_stopped(
    client: TestClient, scratch_root: Path
) -> None:
    seed_crawl(make_project(scratch_root))
    text = client.get("/projects/demo/crawls/crawl_demo").text
    assert "max_actions" in text
    assert "stopped" in text


def test_the_crawl_page_shows_what_was_refused_and_why(
    client: TestClient, scratch_root: Path
) -> None:
    seed_crawl(make_project(scratch_root))
    text = client.get("/projects/demo/crawls/crawl_demo").text
    assert "Delete account" in text
    assert "destructive-name deny-list" in text


def test_screens_and_issues_appear_with_names_not_ids(
    client: TestClient, scratch_root: Path
) -> None:
    seed_crawl(make_project(scratch_root))
    text = client.get("/projects/demo/crawls/crawl_demo").text
    assert "Settings" in text
    assert "TypeError: x is undefined" in text


def test_an_unknown_crawl_id_is_a_themed_404(
    client: TestClient, scratch_root: Path
) -> None:
    make_project(scratch_root)
    response = client.get("/projects/demo/crawls/crawl_nope")
    assert response.status_code == 404
    assert "AutoTester" in response.text
    assert "No crawl" in response.text


def test_a_path_traversal_crawl_id_is_refused(
    client: TestClient, scratch_root: Path
) -> None:
    make_project(scratch_root)
    response = client.get("/projects/demo/crawls/..%2F..%2Fetc/report.xlsx")
    assert response.status_code in (400, 404)


def test_crawl_page_escapes_injected_text(client: TestClient, scratch_root: Path) -> None:
    store = make_project(scratch_root)
    crawl = Crawl(project="demo", id="crawl_x", stop_reason="frontier empty")
    store.save_crawl(crawl)
    store.add_node(ScreenNode(crawl_id=crawl.id, project="demo", url_template="demo.test/x",
                              url_example="https://demo.test/x", signature="s",
                              name="<script>alert(1)</script>"))
    text = client.get("/projects/demo/crawls/crawl_x").text
    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;" in text


@pytest.mark.parametrize("escape", ["absolute", "traversal", "symlink"])
def test_crawl_page_never_embeds_a_screenshot_outside_its_shots_directory(
    client: TestClient, scratch_root: Path, escape: str,
) -> None:
    store = make_project(scratch_root)
    crawl = Crawl(project="demo", id="crawl_x")
    store.save_crawl(crawl)
    outside = store.paths.dir / "outside.png"
    outside.write_bytes(b"not-a-crawl-screenshot")
    ref = str(outside) if escape == "absolute" else "../../../outside.png"
    if escape == "symlink":
        store.paths.crawl_shots_dir(crawl.id).symlink_to(store.paths.dir, target_is_directory=True)
        ref = outside.name
    store.add_node(ScreenNode(crawl_id=crawl.id, project="demo", url_template="demo.test/x",
                              url_example="https://demo.test/x", signature="s", screenshot_ref=ref))
    text = client.get("/projects/demo/crawls/crawl_x").text
    assert "data:image/png;base64" not in text

def test_the_xlsx_download_is_a_workbook(client: TestClient, scratch_root: Path) -> None:
    seed_crawl(make_project(scratch_root))
    response = client.get("/projects/demo/crawls/crawl_demo/report.xlsx")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert response.content[:2] == b"PK"


def test_merge_writes_the_screens_into_the_flowspec_and_resets_review(
    client: TestClient, scratch_root: Path
) -> None:
    store = make_project(scratch_root)
    seed_crawl(store)
    store.save_flowspec(FlowSpec(project="demo",
                                 review=Review(status=ReviewStatus.APPROVED, by="umesh")))
    response = client.post("/projects/demo/crawls/crawl_demo/merge", follow_redirects=False)
    assert response.status_code == 303
    spec = ProjectStore("demo", scratch_root).load_flowspec()
    assert {s.name for s in spec.screens} == {"Home", "Settings"}
    assert spec.review.status is ReviewStatus.DRAFT


def test_coverage_card_reports_screens_the_flowspec_cannot_name(
    client: TestClient, scratch_root: Path
) -> None:
    store = make_project(scratch_root)
    seed_crawl(store)
    store.save_flowspec(FlowSpec(project="demo", screens=[
        Screen(id="s1", name="Home", url_pattern="/"),
        Screen(id="s2", name="Billing", url_pattern="/billing"),
    ]))
    text = client.get("/projects/demo/crawls/crawl_demo").text
    assert "/settings" in text   # crawled, unknown to the spec
    assert "/billing" in text    # known to the spec, never reached


def test_the_merge_button_tells_the_user_it_un_approved_the_flowspec(
    client: TestClient, scratch_root: Path
) -> None:
    store = make_project(scratch_root)
    seed_crawl(store)
    store.save_flowspec(FlowSpec(project="demo",
                                 review=Review(status=ReviewStatus.APPROVED, by="umesh")))
    client.post("/projects/demo/crawls/crawl_demo/merge", follow_redirects=False)
    text = client.get("/projects/demo/crawls/crawl_demo").text
    assert "draft" in text.lower()
    assert "not approved" in text.lower()


def test_an_approved_flowspec_is_not_falsely_warned_about(
    client: TestClient, scratch_root: Path
) -> None:
    store = make_project(scratch_root)
    seed_crawl(store)
    store.save_flowspec(FlowSpec(project="demo", screens=[
        Screen(id="s1", name="Home", url_pattern="/"),
    ], review=Review(status=ReviewStatus.APPROVED, by="umesh")))
    text = client.get("/projects/demo/crawls/crawl_demo").text
    assert "not approved" not in text.lower()
    assert "approved" in text.lower()


def test_explore_without_an_approval_is_refused_and_leaves_no_trace(
    client: TestClient, scratch_root: Path
) -> None:
    make_project(scratch_root)
    response = client.post("/projects/demo/explore", follow_redirects=False)
    assert response.status_code == 403
    assert "AutoTester" in response.text
    assert "/projects/demo/env#crawl-approval" in response.text
    assert "uv run autotester" not in response.text
    assert not (scratch_root / "projects" / "demo" / "crawl").exists()
    assert not (scratch_root / "profiles" / "demo").exists()


def test_credentials_page_grants_a_server_scoped_crawl_approval(
    client: TestClient, scratch_root: Path,
) -> None:
    store = make_project(scratch_root)
    page = client.get("/projects/demo/env")
    assert "id='crawl-approval'" in page.text
    assert "applies only to <code>https://demo.test</code>" in page.text
    assert "new Date(expiry.value)" in page.text
    assert "name='target'" not in page.text and "name='project'" not in page.text
    expiry = "2099-09-11T12:00"
    response = client.post("/projects/demo/crawl-approval", data={
        "granted_by": "Umesh", "scope": "read and click safe controls",
        "expires_at": expiry, "timezone_offset_minutes": "330",
        "max_actions": "17", "wall_clock_s": "45",
        "target": "https://evil.test", "project": "other",
    }, follow_redirects=False)
    assert response.status_code == 303
    approval = store.list_approvals()[0]
    assert (approval.project, approval.target, approval.max_actions) == (
        "demo", "https://demo.test", 17)
    assert approval.wall_clock_s == 45 and approval.granted_by == "Umesh"
    assert approval.expires_at == "2099-09-11T06:30:00+00:00"


def test_crawl_approval_refuses_a_secret_in_free_text(
    client: TestClient, scratch_root: Path,
) -> None:
    store = make_project(scratch_root)
    (scratch_root / ".env").write_text("DEMO_PASSWORD=hunter2\n", encoding="utf-8")
    response = client.post("/projects/demo/crawl-approval", data={
        "granted_by": "Umesh", "scope": "hunter2", "note": "safe",
        "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "max_actions": "10", "wall_clock_s": "20",
    })
    assert response.status_code == 400 and "hunter2" not in response.text
    assert all(text in response.text for text in (
        "Crawl approval not saved", "Return to crawl approval"))
    assert store.list_approvals() == []


def test_invalid_bounds_are_themed_and_never_launch(
    client: TestClient, scratch_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_project(scratch_root)
    monkeypatch.setattr("autotester.browser.session.BrowserSession",
                        lambda *_a, **_k: pytest.fail("browser launched"))
    response = client.post("/projects/demo/explore", data={"max_screens": "0"})
    assert response.status_code == 400
    assert "AutoTester" in response.text and "Invalid crawl bounds" in response.text
    assert not (scratch_root / "projects" / "demo" / "crawl").exists()


def test_one_bounds_object_reaches_preflight_and_run(
    client: TestClient, scratch_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_project(scratch_root)
    seen: list[object] = []

    class Session:
        def __init__(self, *_a: object, **_k: object) -> None: pass
        def __enter__(self) -> Session: return self
        def __exit__(self, *_a: object) -> None: pass

    def preflight(_project: object, _store: object, bounds: object) -> None:
        seen.append(bounds)

    def run(_project: object, _session: object, _store: object, **kwargs: object) -> Crawl:
        seen.append(kwargs["bounds"])
        return Crawl(project="demo", id=str(kwargs["crawl_id"]))

    monkeypatch.setattr("autotester.browser.session.BrowserSession", Session)
    monkeypatch.setattr("autotester.stages.explore.require_consent", preflight)
    monkeypatch.setattr("autotester.stages.explore.run_crawl", run)
    response = client.post("/projects/demo/explore", data={
        "max_screens": "7", "max_actions": "11", "wall_clock_s": "13", "max_depth": "3",
    }, follow_redirects=False)
    assert response.status_code == 303 and seen[0] is seen[1]
    bounds = seen[0]
    assert (bounds.max_screens, bounds.max_actions, bounds.wall_clock_s, bounds.max_depth) == (  # type: ignore[attr-defined]
        7, 11, 13, 3)
