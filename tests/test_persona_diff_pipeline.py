"""CR4 end to end — the diff the real pipeline writes onto the persona.

Contract: qa/contracts/crawl-traversal.md CR4/CR5. `test_persona_changes.py`
owns `classify()` as a pure function; this file owns what
`stages/portal_persona.build_portal_persona` really records after a real crawl,
including the live incremental pair. Split from it at the 300-line C2 cap.

The decisive test here is `test_a_real_incremental_recrawl_of_an_unchanged_site
_reports_no_deletion`: the join between a REAL incremental crawl's own graph
and `classify()` that no test made, which is exactly where
`ISS-t165-crawl-traversal-3` lived — 8 fabricated deletions on a byte-identical
site, with every synthetic-fixture test in the suite green.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from autotester.schema.enums import NodeStatus
from autotester.schema.portal_persona import PersonaRevision, PersonaScreen, PortalPersona
from autotester.schema.screen_graph import ScreenNode


def _node(template: str, signature: str, *, status: NodeStatus = NodeStatus.EXPLORED,
          name: str = "") -> ScreenNode:
    return ScreenNode(crawl_id="c", project="p", url_template=template, url_example=template,
                      signature=signature, name=name or template, status=status)


def _persona(*screens: tuple[str, str], history: list[PersonaRevision] | None = None
             ) -> PortalPersona:
    return PortalPersona(
        project="p",
        screens=[PersonaScreen(id=f"s{i}", name=t, url_template=t, signature=sig)
                 for i, (t, sig) in enumerate(screens)],
        history=history or [],
    )


def test_a_removed_screen_lands_on_the_persona_history_even_though_merge_adds_only(
    tmp_path: Path,
) -> None:
    """The point of putting the diff on the revision: PP2's add-only `_merge` has,
    by construction, nothing to add for a screen that DISAPPEARED — so before CR4
    a deletion produced no revision at all and left no trace anywhere."""
    from autotester.schema.crawl import Crawl
    from autotester.schema.enums import CrawlStatus
    from autotester.schema.project import Project
    from autotester.stages.portal_persona import build_portal_persona
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("p", tmp_path)
    store.save_project(Project(slug="p", name="p", base_url="https://app.test/"))
    store.save_portal_persona(_persona(("/a", "sig-a"), ("/gone", "sig-gone")))
    crawl = Crawl(project="p", status=CrawlStatus.COMPLETED)
    store.save_crawl(crawl)
    store.add_node(_node("/a", "sig-a").model_copy(update={"crawl_id": crawl.id}))

    persona = build_portal_persona(store, crawl_id=crawl.id)

    assert persona.history, "a deletion produced no revision"
    assert persona.history[-1].missing_screens == ["/gone"]
    assert [s.key() for s in persona.screens] == ["/a", "/gone"], "PP2 add-only was broken"


def test_a_real_incremental_recrawl_of_an_unchanged_site_reports_no_deletion(
    tmp_path_factory: pytest.TempPathFactory, serve_dir: Callable[[Path], str]
) -> None:
    """D-040 acceptance test (c), second half, on the MAINLINE incremental path:
    *the same two crawls with nothing removed produce zero `missing` entries.*

    `ISS-t165-crawl-traversal-3`, and the one test the fix was required to add.
    Every other test in this file feeds `classify()` synthetic nodes; the
    `incremental_pair` fixture in `test_explore_completeness.py` runs the real
    crawls but never joins crawl 2's own graph to `classify()`. The bug lived in
    exactly that join: `explore_incremental.skip_unchanged` short-circuits before
    `visit_node`, and `_enqueue` only runs inside `visit_node`, so a skipped
    entry screen's children are never discovered — crawl 2 ends with a ONE-node
    graph, `frontier_exhausted=True`, and the other 8 screens of a byte-identical
    site reported as deletions. Live headed-Chromium reproduction, checker A.

    So this test runs both real crawls and asserts on the revision the real
    pipeline writes — not on a hand-built node list.
    """
    from crawl_live import FIXTURES, live_crawl

    from autotester.schema.crawl import CrawlBounds
    from autotester.schema.project import Project
    from autotester.stages.portal_persona import build_portal_persona

    tmp_path = tmp_path_factory.mktemp("incr-diff")
    site = tmp_path / "site"
    shutil.copytree(FIXTURES / "deep_site", site)
    base = serve_dir(site)
    bounds = CrawlBounds(max_screens=20, max_actions=80, wall_clock_s=180.0)
    first, store = live_crawl(tmp_path, base, slug="incr", bounds=bounds)
    store.save_project(Project(slug="incr", name="incr", base_url=base + "/",
                               allowed_domains=["127.0.0.1"]))
    seeded = build_portal_persona(store, crawl_id=first.id)
    known = {s.key() for s in seeded.screens if s.signature}
    assert len(known) > 1, "crawl 1 learned one screen — the deletion claim would be vacuous"

    second, _ = live_crawl(tmp_path, base, slug="incr", bounds=bounds,
                           incremental=True, store=store)
    assert second.skipped_unchanged > 0, "nothing was skipped — this is not the incremental path"
    persona = build_portal_persona(store, crawl_id=second.id)
    revision = persona.history[-1]

    assert revision.missing_screens == [], (
        f"an unchanged site was reported as having lost {len(revision.missing_screens)} "
        f"screen(s): {revision.missing_screens}")
    assert set(revision.missing_unjudged) <= known
    assert [s.key() for s in persona.screens] == [s.key() for s in seeded.screens], (
        "PP2: the re-crawl dropped or duplicated a stored screen")
    assert "frontier empty" in (second.stop_reason or ""), second.stop_reason
    assert "frontier was not exhausted" not in revision.summary, (
        "the human-facing summary contradicts the crawl's own stop_reason: the frontier "
        f"WAS exhausted here, a skip is what blocked the claim -- {revision.summary!r}")


def test_a_bound_stopped_crawl_writes_unjudged_not_missing(tmp_path: Path) -> None:
    """The same path, with a crawl that did NOT exhaust its frontier."""
    from autotester.schema.crawl import Crawl
    from autotester.schema.enums import CrawlStatus
    from autotester.schema.project import Project
    from autotester.stages.portal_persona import build_portal_persona
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("p", tmp_path)
    store.save_project(Project(slug="p", name="p", base_url="https://app.test/"))
    store.save_portal_persona(_persona(("/a", "sig-a"), ("/unreached", "sig-u")))
    crawl = Crawl(project="p", status=CrawlStatus.STOPPED_BOUND, stop_reason="max_actions")
    store.save_crawl(crawl)
    store.add_node(_node("/a", "sig-a").model_copy(update={"crawl_id": crawl.id}))

    persona = build_portal_persona(store, crawl_id=crawl.id)

    assert persona.history[-1].missing_screens == []
    assert persona.history[-1].missing_unjudged == ["/unreached"]
    assert "not judged" in persona.history[-1].summary


def test_two_distinct_screens_sharing_a_url_are_both_stored(tmp_path: Path) -> None:
    """ISS-t165-crawl-traversal-2, the STORAGE half. `_incoming_screens` deduped
    on `PersonaScreen.key()` (url_template only), so the second of two
    structurally distinct states at one URL — an SPA toggle, the shape X3/X14
    document as real — never reached the persona at all. Deduping on `ident()`
    (key AND signature) keeps both; `_merge` stays add-only either way (PP2)."""
    from autotester.schema.crawl import Crawl
    from autotester.schema.enums import CrawlStatus
    from autotester.schema.project import Project
    from autotester.stages.portal_persona import build_portal_persona
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("p", tmp_path)
    store.save_project(Project(slug="p", name="p", base_url="https://app.test/"))
    crawl = Crawl(project="p", status=CrawlStatus.COMPLETED)
    store.save_crawl(crawl)
    for signature in ("sig-base", "sig-panel-open"):
        store.add_node(_node("/", signature, name="Home").model_copy(
            update={"crawl_id": crawl.id}))

    persona = build_portal_persona(store, crawl_id=crawl.id)

    assert sorted(s.signature for s in persona.screens) == ["sig-base", "sig-panel-open"], (
        "one of two structurally distinct screens at the same URL was dropped")


def test_a_second_state_at_a_known_url_survives_the_add_only_merge(tmp_path: Path) -> None:
    """The same, across two updates: the second state appears on a LATER crawl,
    so `_merge` — not `_incoming_screens` — is the thing that must not drop it.
    Add-only: the first state is still there afterwards."""
    from autotester.schema.crawl import Crawl
    from autotester.schema.enums import CrawlStatus
    from autotester.schema.project import Project
    from autotester.stages.portal_persona import build_portal_persona
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("p", tmp_path)
    store.save_project(Project(slug="p", name="p", base_url="https://app.test/"))
    store.save_portal_persona(_persona(("/", "sig-base")))
    crawl = Crawl(project="p", status=CrawlStatus.COMPLETED)
    store.save_crawl(crawl)
    store.add_node(_node("/", "sig-panel-open", name="Home").model_copy(
        update={"crawl_id": crawl.id}))

    persona = build_portal_persona(store, crawl_id=crawl.id)

    assert sorted(s.signature for s in persona.screens) == ["sig-base", "sig-panel-open"]
    assert persona.history[-1].changed_screens == ["/"], (
        "the new state at a known URL was stored but never classified")
