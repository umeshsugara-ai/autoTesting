"""Track A video-learning schema (D-014). Roundtrip, strictness, id stability.

Contract: qa/contracts/video-learning.md (VL1, VL5). No provider, no browser —
pure Pydantic model behaviour.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from autotester.schema.analysis import AnalysedIssue, AnalysedScreen, JourneyStop, VideoAnalysis
from autotester.schema.enums import Action, Confidence, IssueCategory, IssueOrigin
from autotester.schema.issue import Issue
from autotester.schema.media import MediaChunk, MediaPrep, Transcript, TranscriptSegment
from autotester.schema.observation import (
    ModelObservation,
    ObservedIssue,
    ObservedScreen,
    ObservedStep,
    VideoObservation,
    VisionOptions,
)
from autotester.schema.screenmap import Journey, MappedScreen, ScreenMap, ScreenVisit

FIXTURE = Path(__file__).parent / "fixtures" / "erp1.transcript.json"


# -- Transcript.from_sidecar (VL1: existing sidecars load byte-for-byte) -----

def test_from_sidecar_loads_the_real_erp1_shape() -> None:
    transcript = Transcript.from_sidecar(FIXTURE, source_id="src_erp1")

    assert transcript.source_id == "src_erp1"
    assert transcript.engine == "sidecar"
    assert len(transcript.segments) == 6
    assert transcript.speech_seconds == 22.0
    assert transcript.segments[0].start == 1.42
    assert transcript.segments[0].text == "Move to next stage"


def test_transcript_slice_is_clip_relative_and_windowed() -> None:
    transcript = Transcript.from_sidecar(FIXTURE, source_id="src_erp1")

    window = transcript.slice(offset_s=0.0, length_s=8.0)

    assert "[00:01-00:03] Move to next stage" in window
    assert "[00:05-00:07] Documents completed" in window
    assert "Today's state" not in window  # starts at 8.42, outside [0, 8)


def test_transcript_slice_with_no_overlap_is_empty() -> None:
    transcript = Transcript.from_sidecar(FIXTURE, source_id="src_erp1")
    assert transcript.slice(offset_s=100.0, length_s=5.0) == ""


# -- extra="forbid" everywhere (C1) -------------------------------------------

def test_transcript_segment_rejects_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        TranscriptSegment(start=0.0, end=1.0, text="x", extra_field="nope")


def test_observed_issue_rejects_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        ObservedIssue(
            t_start=1.0, screen="Dashboard", category=IssueCategory.FEATURE_GAP,
            title="x", what_is_wrong="y", bogus="z",
        )


def test_issue_rejects_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Issue(
            project="erp", source_id="src_1", recording_label="erp1.mp4",
            at_s=1.0, screen="Dashboard", title="x", what_is_wrong="y",
            not_a_real_field=True,
        )


# -- Issue.id is content-addressed and stable ---------------------------------

def make_issue(**overrides: object) -> Issue:
    defaults = dict(
        project="erp", source_id="src_1", recording_label="erp1.mp4",
        at_s=12.3, screen="Trainer pipeline", title="Wrong status shown",
        what_is_wrong="Status reads Assessment Done instead of Closure",
        category=IssueCategory.DATA_INCONSISTENCY,
    )
    defaults.update(overrides)
    return Issue(**defaults)  # type: ignore[arg-type]


def test_issue_id_is_stable_across_created_at_and_severity() -> None:
    a = make_issue()
    b = make_issue()
    assert a.id == b.id
    assert a.id.startswith("iss_")


def test_issue_id_differs_when_title_differs() -> None:
    a = make_issue(title="Wrong status shown")
    b = make_issue(title="Completely different problem")
    assert a.id != b.id


def test_issue_id_buckets_nearby_timestamps_together() -> None:
    """Same 5s bucket (round(at_s/5)) -> same id when everything else matches."""
    a = make_issue(at_s=12.0)   # round(12/5) = 2
    b = make_issue(at_s=13.4)   # round(13.4/5) = 3 -- different bucket
    c = make_issue(at_s=12.4)   # round(12.4/5) = 2 -- same bucket as a
    assert a.id == c.id
    assert a.id != b.id


def test_add_issue_is_idempotent(tmp_path: Path) -> None:
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("erp", tmp_path)
    issue = make_issue()
    store.add_issue(issue)
    store.add_issue(issue)
    assert len(store.list_issues()) == 1


# -- ModelObservation / VideoAnalysis roundtrip through write_json/read_json --

def test_model_observation_roundtrips(tmp_path: Path) -> None:
    from autotester.store.filestore import read_json, write_json

    obs = ModelObservation(
        source_id="src_1", provider_label="gemini:gemini-3.1-pro-preview",
        prompt_name="ingest_video_v1.md", chunk_index=0, offset_s=0.0, length_s=180.0,
        observation=VideoObservation(
            screens=[ObservedScreen(name="Dashboard", t_start=0.0)],
            flows=[], issues=[], summary="a demo",
        ),
        input_tokens=100, output_tokens=50,
    )
    path = tmp_path / "obs.json"
    write_json(path, obs)
    loaded = read_json(path, ModelObservation)

    assert loaded is not None
    assert loaded.source_id == "src_1"
    assert loaded.observation.screens[0].name == "Dashboard"


def test_video_analysis_roundtrips_through_project_store(tmp_path: Path) -> None:
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("erp", tmp_path)
    analysis = VideoAnalysis(
        source_id="src_1",
        provider_labels=["gemini:gemini-3.1-pro-preview", "gemini:gemini-3.8-flash"],
        screens=[AnalysedScreen(name="Dashboard", t_start=0.0, models_agreeing=2)],
        issues=[
            AnalysedIssue(
                t_start=5.0, screen="Dashboard", category=IssueCategory.FEATURE_GAP,
                title="x", what_is_wrong="y", models_agreeing=2,
                origin=IssueOrigin.SPOKEN,
            )
        ],
        journey=[JourneyStop(name="Dashboard", t_start=0.0, what_user_does="looks around")],
    )
    store.save_analysis(analysis)
    loaded = store.load_analysis("src_1")

    assert loaded is not None
    assert loaded.screens[0].models_agreeing == 2
    assert loaded.issues[0].confidence == Confidence.MEDIUM  # default preserved


def test_media_prep_and_transcript_roundtrip_through_project_store(tmp_path: Path) -> None:
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("erp", tmp_path)
    prep = MediaPrep(
        source_id="src_1", duration_s=180.0, width=1920, height=1080,
        chunks=[MediaChunk(index=0, path="chunks/chunk_00_0s.mp4", offset_s=0.0, length_s=180.0)],
    )
    store.save_media_prep(prep)
    loaded_prep = store.load_media_prep("src_1")
    assert loaded_prep is not None
    assert loaded_prep.chunks[0].length_s == 180.0

    transcript = Transcript.from_sidecar(FIXTURE, source_id="src_1")
    store.save_transcript(transcript)
    loaded_transcript = store.load_transcript("src_1")
    assert loaded_transcript is not None
    assert len(loaded_transcript.segments) == 6


def test_vision_options_defaults_match_the_proven_pipeline_settings() -> None:
    options = VisionOptions()
    assert options.fps == 2.0
    assert options.seed == 7
    assert options.max_output_tokens == 65536
    assert options.media_resolution == "high"


def test_screen_map_roundtrips_through_project_store(tmp_path: Path) -> None:
    from autotester.store.project_store import ProjectStore

    store = ProjectStore("erp", tmp_path)
    screen_map = ScreenMap(
        project="erp",
        screens=[
            MappedScreen(
                id="scr_abc", name="Dashboard",
                visits=[ScreenVisit(source_id="src_1", t_start=0.0)],
            )
        ],
        journeys=[Journey(source_id="src_1", label="erp1.mp4", stops=[])],
        source_ids=["src_1"],
    )
    store.save_screen_map(screen_map)
    loaded = store.load_screen_map()
    assert loaded is not None
    assert loaded.screens[0].visits[0].source_id == "src_1"


# -- Action enum additions (D-014 discharges D-005) ---------------------------

def test_action_gained_back_hover_press_key_scroll() -> None:
    assert Action.BACK == "back"
    assert Action.HOVER == "hover"
    assert Action.PRESS_KEY == "press_key"
    assert Action.SCROLL == "scroll"


def test_observed_step_carries_optional_on_screen_text_and_narration() -> None:
    step = ObservedStep(
        order=1, action=Action.CLICK, target="Submit button", t_start=1.0,
        on_screen_text="Submit", narration="now I click submit",
    )
    assert step.on_screen_text == "Submit"
    assert step.narration == "now I click submit"
