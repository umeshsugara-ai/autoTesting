"""MERGE_FLOWSPEC stage (Track A6, T-135).

Contract: qa/contracts/ingest.md I6 (the merge seam it defers to A6) and
qa/contracts/coverage.md V3 (one request per gap, content-addressed).

The loop these tests defend: coverage notices an unknown route -> a VideoRequest
is queued -> a human records it -> ingest produces a fresh FlowSpec -> this stage
folds it in without discarding the review -> the request closes and the gap stops
being re-asked. `test_the_full_loop_closes_a_gap_end_to_end` is that loop; the
rest pin the individual rules it depends on.
"""

from __future__ import annotations

from autotester.schema.enums import ReviewStatus
from autotester.schema.flowspec import Flow, FlowSpec, Review, Screen
from autotester.stages.merge_flowspec import merge_flowspec

PROJECT = "pathlynks"


def screen(sid: str, name: str, url_pattern: str | None = None) -> Screen:
    return Screen(id=sid, name=name, url_pattern=url_pattern)


def approved(*screens: Screen, flows: list[Flow] | None = None, version: int = 3) -> FlowSpec:
    """A spec a human has already reviewed — the truth a merge must not damage."""
    return FlowSpec(
        project=PROJECT,
        version=version,
        screens=list(screens),
        flows=flows or [],
        source_ids=["src_video_1"],
        review=Review(status=ReviewStatus.APPROVED, by="umesh", at="2026-09-10T00:00:00Z"),
    )


def ingested(*screens: Screen, flows: list[Flow] | None = None,
             source_id: str = "src_video_2") -> FlowSpec:
    """What `ingest_video` returns: a fresh spec, always DRAFT, never merged."""
    return FlowSpec(project=PROJECT, screens=list(screens), flows=flows or [],
                    source_ids=[source_id])


# -- reviewed truth survives --------------------------------------------------

def test_an_existing_screen_is_never_rewritten_by_a_later_recording() -> None:
    human_corrected = screen("scr_1", "Sign in (corrected by hand)", "https://app.test/signin")
    incoming = ingested(screen("scr_1", "whatever the model called it",
                               "https://app.test/signin"))

    merged = merge_flowspec(approved(human_corrected), incoming, source_id="src_video_2")

    assert [s.name for s in merged.screens] == ["Sign in (corrected by hand)"]


def test_a_new_screen_and_flow_are_added() -> None:
    existing = approved(screen("scr_1", "Sign in", "https://app.test/signin"))
    flow = Flow(id="flow_1", name="create report", entry_screen="scr_2")
    incoming = ingested(screen("scr_2", "New report", "https://app.test/reports/new"),
                        flows=[flow])

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert {s.id for s in merged.screens} == {"scr_1", "scr_2"}
    assert [f.id for f in merged.flows] == ["flow_1"]
    assert merged.source_ids == ["src_video_1", "src_video_2"]


def test_a_real_change_sends_the_spec_back_to_draft_and_bumps_the_version() -> None:
    existing = approved(screen("scr_1", "Sign in", "https://app.test/signin"))
    incoming = ingested(screen("scr_2", "New report", "https://app.test/reports/new"))

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert merged.review.status is ReviewStatus.DRAFT
    assert merged.version == existing.version + 1


def test_merging_the_same_recording_twice_changes_nothing_the_second_time() -> None:
    existing = approved(screen("scr_1", "Sign in", "https://app.test/signin"))
    incoming = ingested(screen("scr_2", "New report", "https://app.test/reports/new"))

    once = merge_flowspec(existing, incoming, source_id="src_video_2")
    twice = merge_flowspec(once, incoming, source_id="src_video_2")

    # A second reset would re-arm the review gate forever and EXPAND could never run.
    assert twice.version == once.version
    assert twice.review.note == once.review.note
    assert len(twice.screens) == 2


def test_with_no_existing_spec_the_recording_is_the_spec() -> None:
    incoming = ingested(screen("scr_1", "Sign in", "https://app.test/signin"))

    assert merge_flowspec(None, incoming, source_id="src_video_2") is incoming


def test_the_existing_app_overview_is_not_replaced_by_a_later_one() -> None:
    existing = approved(screen("scr_1", "Sign in", "https://app.test/signin"))
    existing = existing.model_copy(update={"app_overview": "reviewed description"})
    incoming = ingested(screen("scr_2", "New report", "https://app.test/reports/new"))
    incoming = incoming.model_copy(update={"app_overview": "model's fresh guess"})

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert merged.app_overview == "reviewed description"


# -- disagreement is recorded, never silently resolved ------------------------

def test_two_sources_claiming_one_url_under_different_names_conflict() -> None:
    existing = approved(screen("scr_1", "Sign in", "https://app.test/signin"))
    incoming = ingested(screen("scr_9", "Login page", "https://app.test/signin"))

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert len(merged.conflicts) == 1
    assert merged.conflicts[0].subject == "https://app.test/signin"
    # Both claims are kept — a merge never picks a winner.
    assert {s.id for s in merged.screens} == {"scr_1", "scr_9"}


def test_a_structurally_identified_screen_is_not_contradicted_by_a_recording() -> None:
    """A crawl identified this screen structurally; a video only claims a URL.
    Two states at one URL is an SPA, which is not a disagreement (AT-103)."""
    crawled = screen("node_abc123", "Dashboard", "https://app.test/app")
    incoming = ingested(screen("scr_9", "Home", "https://app.test/app"))

    merged = merge_flowspec(approved(crawled), incoming, source_id="src_video_2")

    assert merged.conflicts == []


def test_the_same_conflict_is_not_recorded_twice() -> None:
    existing = approved(screen("scr_1", "Sign in", "https://app.test/signin"))
    incoming = ingested(screen("scr_9", "Login page", "https://app.test/signin"))

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")
    again = merge_flowspec(merged, incoming, source_id="src_video_2")

    assert len(again.conflicts) == 1


# -- AT-290: a known screen must be able to LEARN the url it never showed -----

def test_a_re_recording_teaches_a_url_pattern_the_spec_lacked() -> None:
    """`Screen.id` is content-addressed on (name, signals) only, and ingest.md I7
    makes `url_pattern=None` the NORMAL outcome for a video with no visible
    address bar. So the common case was: ask for a video of an unknown route, get
    one, drop it whole because the screen name is already known, and leave the
    ask open forever."""
    existing = approved(screen("scr_1", "Login", None))
    incoming = ingested(screen("scr_1", "Login", "https://app.test/login"))

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert merged.screen("scr_1").url_pattern == "https://app.test/login"
    assert merged.review.status is ReviewStatus.DRAFT, "learning must re-arm the gate"


def test_an_existing_url_pattern_is_never_overwritten_by_a_later_one() -> None:
    """Filling a None is teaching; replacing a value is rewriting reviewed truth."""
    existing = approved(screen("scr_1", "Login", "https://app.test/signin"))
    incoming = ingested(screen("scr_1", "Login", "https://app.test/login"))

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert merged.screen("scr_1").url_pattern == "https://app.test/signin"
    assert merged is existing, "nothing was learned, so this is a no-op"


# -- AT-295: a LEARNED pattern is a claim too, and must face the conflict rule --

def test_learning_a_pattern_another_screen_claims_records_a_conflict() -> None:
    """`_conflicts_for` iterated `added` only, so filling an empty url_pattern
    with one another screen already claims produced two screens at one pattern
    and NO Conflict — silently picking a winner, which is the one thing this
    seam exists not to do."""
    existing = approved(
        screen("scr_1", "Trainers", "https://app.test/erp/trainers"),
        screen("scr_2", "Trainer list", None),
    )
    incoming = ingested(screen("scr_2", "Trainer list", "https://app.test/erp/trainers"))

    merged = merge_flowspec(existing, incoming, source_id="src_video_2")

    assert merged.screen("scr_2").url_pattern == "https://app.test/erp/trainers"
    assert len(merged.conflicts) == 1, "two screens now claim one url and nobody was told"
    assert merged.conflicts[0].subject == "https://app.test/erp/trainers"
