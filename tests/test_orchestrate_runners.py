"""T-163 stage adapters: DISCOVER/MODEL as stages that protect reviewed truth.

Covers OR3 (an orchestrated run against an APPROVED FlowSpec proposes into a
DRAFT via `merge_flowspec` and never auto-approves or discards the reviewed
screens) and OR6 (DISCOVER/MODEL are `run(input, ctx) -> artifact` stages that
read ONLY the previous stage's artifact — MODEL raises rather than silently
reading the reviewed flowspec, DISCOVER parks its own DRAFT proposal and never
touches `flowspec.json`).

Fully offline: no browser, network, or model. DISCOVER's crawl is an injected
`crawl_fn` returning a fixture `Crawl` + `ScreenNode`; MODEL reads a proposal
parked on disk. Each OR row in the manifest carries a single-hunk falsifying
edit reproduced red->green.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.schema.crawl import Crawl
from autotester.schema.enums import ReviewStatus
from autotester.schema.flowspec import FlowSpec, Review, Screen
from autotester.schema.project import Project
from autotester.schema.run_state import StageName
from autotester.schema.screen_graph import ScreenNode
from autotester.stages.orchestrate import StageContext
from autotester.stages.orchestrate_runners import (
    MissingArtifact,
    _persist_proposal,
    make_discover_runner,
    make_model_runner,
)
from autotester.stages.review import FlowSpecNotReviewed, require_reviewed
from autotester.store.filestore import read_json
from autotester.store.project_store import ProjectStore

_PROJECT = Project(slug="demo", name="Demo", base_url="https://demo.test",
                   allowed_domains=["demo.test"])


def _store(tmp_path: Path) -> ProjectStore:
    store = ProjectStore("demo", tmp_path)
    store.save_project(_PROJECT)
    return store


def _node(name: str = "Home") -> ScreenNode:
    return ScreenNode(
        crawl_id="crawl1", project="demo",
        url_template="https://demo.test/home", url_example="https://demo.test/home",
        signature=f"sig-{name}", name=name, title=name,
    )


# -- OR3 -------------------------------------------------------------------

def test_orchestrated_run_never_overwrites_approved_truth(tmp_path: Path) -> None:
    """OR3: MODEL folds a proposal into an APPROVED spec through `merge_flowspec`,
    which keeps every reviewed screen intact and re-arms the review gate (DRAFT)
    instead of auto-approving — so the human-approved truth is never discarded
    and the new material cannot drive anything until a human re-approves."""
    store = _store(tmp_path)
    approved = FlowSpec(
        project="demo",
        screens=[Screen(id="s_home", name="Home", url_pattern="/home")],
        review=Review(status=ReviewStatus.APPROVED, by="umesh"),
    )
    store.save_flowspec(approved)

    ctx = StageContext(store=store, run_id="run1")
    proposal = FlowSpec(
        project="demo",
        screens=[Screen(id="s_settings", name="Settings", url_pattern="/settings")],
    )
    prev_ref = _persist_proposal(ctx, StageName.DISCOVER, proposal)

    make_model_runner()(ctx, prev_ref)

    merged = store.load_flowspec()
    assert merged is not None
    # the reviewed screen survives, byte-for-byte (never rewritten/discarded)
    survivor = next((s for s in merged.screens if s.id == "s_home"), None)
    assert survivor is not None
    assert survivor.model_dump() == approved.screens[0].model_dump()
    # the new material landed...
    assert any(s.id == "s_settings" for s in merged.screens)
    # ...but as DRAFT: no auto-approval, the gate is re-armed
    assert merged.review.status is ReviewStatus.DRAFT
    with pytest.raises(FlowSpecNotReviewed):
        require_reviewed(merged)


# -- OR6 -------------------------------------------------------------------

def test_model_stage_reads_only_the_previous_stage_artifact(tmp_path: Path) -> None:
    """OR6: MODEL is `run(input, ctx) -> artifact` that reads ONLY `prev_ref`.
    Handed no reference (or a dangling one) it raises `MissingArtifact` rather
    than reaching into the reviewed `flowspec.json` sitting right next to it."""
    store = _store(tmp_path)
    # a reviewed spec is on disk: MODEL must NOT silently consume it as its input
    store.save_flowspec(FlowSpec(project="demo",
                                 screens=[Screen(id="s", name="S")]))
    ctx = StageContext(store=store, run_id="run1")

    with pytest.raises(MissingArtifact):
        make_model_runner()(ctx, None)
    with pytest.raises(MissingArtifact):
        make_model_runner()(ctx, str(tmp_path / "nope.json"))


def test_discover_stage_parks_its_own_draft_proposal(tmp_path: Path) -> None:
    """OR6: DISCOVER produces its OWN artifact (a DRAFT FlowSpec proposal under
    the run dir) from only its injected crawl output — it never writes the
    reviewed `flowspec.json`."""
    store = _store(tmp_path)
    crawl = Crawl(project="demo")
    runner = make_discover_runner(_PROJECT, lambda: (crawl, [_node()]))
    ctx = StageContext(store=store, run_id="run1")

    ref = runner(ctx, None)

    parked = Path(ref)
    assert parked != store.paths.flowspec
    assert store.paths.run_dir("run1") in parked.parents
    proposal = read_json(parked, FlowSpec)
    assert proposal is not None
    assert proposal.review.status is ReviewStatus.DRAFT
    assert proposal.screens  # the crawled screen became a proposed Screen
    # reviewed truth is untouched — DISCOVER wrote no flowspec.json
    assert store.load_flowspec() is None
