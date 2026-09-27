"""CR2/CR7 — form-input replay: re-entering a screen that only a typed value opens.

Contract: qa/contracts/crawl-traversal.md CR2 (replay) and CR7 (the replay
widens nothing — it passes the SAME X10-b gate a fresh keystroke passes).
`explore.md` X10/X10-b are unamended.

Split from `test_explore_traversal.py` at the 300-line C2 cap: that file owns
the ORDER the frontier is walked in, this one owns re-performing an action the
crawl already performed once. The live half is a REAL Chromium crawl of a
fixture whose target screen is a client-side STATE at the same URL (AT-227), so
`goto` can never restore it and only the replay can.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from crawl_live import FIXTURES, live_crawl

from autotester.schema.crawl import Crawl, CrawlBounds, SafetyPolicy
from autotester.schema.enums import Action, CrawlStatus, WritePolicy
from autotester.schema.screen_graph import ElementRef, ScreenEdge
from autotester.stages import explore_replay
from autotester.store.project_store import ProjectStore

FORM_SITE = FIXTURES / "form_site"


# --- CR2 / CR7: form-input replay, live -------------------------------------


TYPING_POLICY = SafetyPolicy(write_policy=WritePolicy.TEST_ACCOUNT, synthetic_typing=True)


@pytest.fixture(scope="module")
def form_crawl(
    tmp_path_factory: pytest.TempPathFactory, serve_dir: Callable[[Path], str]
) -> tuple[Crawl, ProjectStore]:
    """A real crawl of a site whose second screen is a client-side STATE that
    only appears once a field has really been filled — the exact shape CR2 names."""
    return live_crawl(tmp_path_factory.mktemp("form"), serve_dir(FORM_SITE), slug="form",
                      bounds=CrawlBounds(max_screens=10, max_actions=40, wall_clock_s=120.0),
                      policy=TYPING_POLICY)


def test_a_screen_behind_a_filled_form_is_re_entered_not_abandoned(
    form_crawl: tuple[Crawl, ProjectStore],
) -> None:
    """CR2's falsifiable: a screen reachable only after filling and submitting a
    form is re-entered by `return_to` replaying BOTH the fill and the click.

    Before CR2, `_replay_discovery` re-clicked the button against an empty
    field, the panel stayed shut, and the node was abandoned with a NAVIGATION
    issue naming "landed on a different screen"."""
    crawl, store = form_crawl
    nodes = store.list_nodes(crawl.id)
    panel = [n for n in nodes if any(el.selector.endswith("detail") for el in n.elements)]
    assert panel, "the crawl never reached the state behind the filled form"
    assert panel[0].status.value == "explored", (
        f"the form-gated screen was reached but abandoned: {panel[0].status}")
    lost = [i for i in store.list_crawl_issues(crawl.id)
            if "landed on a different screen" in i.detail]
    assert lost == [], f"replay still lost the form-gated screen: {[i.detail for i in lost]}"


def test_the_crawl_really_typed_and_really_replayed(
    form_crawl: tuple[Crawl, ProjectStore],
) -> None:
    """Guards the test above against passing for the wrong reason: if typing
    never happened, the panel screen would not exist and the assertion above
    would be vacuous on a site that simply has one screen."""
    crawl, store = form_crawl
    fills = [e for e in store.list_edges(crawl.id) if e.action is Action.FILL]
    assert fills, "no FILL edge — the X10-b pre-pass never ran, so CR2 was never exercised"
    assert crawl.status is not CrawlStatus.LOGIN_FAILED


# --- CR7: the replay passes the SAME gate a fresh type passes ---------------


class _RecordingSession:
    """Records what a replay asks the browser to do, and nothing else."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def fill(self, selector: str, value: str) -> None:
        self.calls.append(("fill", selector, value))

    def select_option(self, selector: str, value: str) -> None:
        self.calls.append(("select", selector, value))

    def click(self, selector: str) -> None:
        self.calls.append(("click", selector, ""))

    def settle(self, timeout_ms: int = 0) -> None:
        return None


class _FakeRuntime:
    """The two attributes `explore_replay` reads, and no more."""

    def __init__(self, policy: SafetyPolicy) -> None:
        self.session = _RecordingSession()
        self.policy = policy
        self.bounds = CrawlBounds()
        self.typed: dict[str, list[explore_replay.TypedAction]] = {}


def _seed_typed(rt: _FakeRuntime, node_id: str = "n1") -> None:
    element = ElementRef(role="textbox", name="Reference code", selector="#code")
    rt.typed[node_id] = [explore_replay.TypedAction(
        node_id=node_id, element=element, action=Action.FILL, value="AT-165")]


def test_a_recorded_value_is_reissued_before_the_submitting_click() -> None:
    """CR2: the fill comes back before the click, in that order."""
    rt = _FakeRuntime(TYPING_POLICY)
    _seed_typed(rt)
    edge = ScreenEdge(crawl_id="c", from_node="n1", to_node="n2", action=Action.CLICK,
                      target="#go", outcome="navigated")
    assert explore_replay.perform(rt, edge) is None  # type: ignore[arg-type]
    assert rt.session.calls == [("fill", "#code", "AT-165"), ("click", "#go", "")]


def test_a_node_discovered_by_a_typed_edge_is_replayed_as_that_typed_action() -> None:
    """CR2: a FILL-discovered edge was being "replayed" by CLICKING a text
    input, which does nothing. It is re-issued as the fill it was."""
    rt = _FakeRuntime(TYPING_POLICY)
    _seed_typed(rt)
    edge = ScreenEdge(crawl_id="c", from_node="n1", to_node="n2", action=Action.FILL,
                      target="#code", outcome="navigated")
    assert explore_replay.perform(rt, edge) is None  # type: ignore[arg-type]
    assert rt.session.calls == [("fill", "#code", "AT-165")]


def test_a_recorded_value_is_never_replayed_under_a_policy_that_refuses_typing() -> None:
    """CR7's falsifiable: the "read the recorded values" path passes through the
    same X5/X10-b gate a fresh type would — it is NOT a bypass that only checks
    "was this typed once before". Both refusing policies, both directions."""
    for policy in (SafetyPolicy(write_policy=WritePolicy.READ_ONLY),
                   SafetyPolicy(write_policy=WritePolicy.TEST_ACCOUNT, synthetic_typing=False)):
        rt = _FakeRuntime(policy)
        _seed_typed(rt)
        edge = ScreenEdge(crawl_id="c", from_node="n1", to_node="n2", action=Action.CLICK,
                          target="#go", outcome="navigated")
        refused = explore_replay.perform(rt, edge)  # type: ignore[arg-type]
        assert refused is not None and "policy" in refused
        assert rt.session.calls == [], f"{policy.write_policy} replayed a value anyway"


def test_a_password_field_is_never_replayed_even_though_it_was_recorded() -> None:
    """CR7: the per-target half of the gate (`typing_target_allowed`) is
    re-evaluated too, not only the run-level boolean."""
    rt = _FakeRuntime(TYPING_POLICY)
    rt.typed["n1"] = [explore_replay.TypedAction(
        node_id="n1", element=ElementRef(role="textbox", name="Password", selector="#pw"),
        action=Action.FILL, value="x")]
    edge = ScreenEdge(crawl_id="c", from_node="n1", to_node="n2", action=Action.CLICK,
                      target="#go", outcome="navigated")
    assert explore_replay.perform(rt, edge) is not None  # type: ignore[arg-type]
    assert rt.session.calls == []
