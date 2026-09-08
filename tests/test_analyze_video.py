"""The ensemble driver — VL2/VL3.

This is the only stage in Track A that spends money, so the tests that matter
are about not spending it twice. Every provider here is a spy: the assertions
are on the number of calls made, because "the cache works" is a claim about
calls, not about output.

Contract: qa/contracts/video-learning.md VL2/VL3.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.core.paths import RepoDocs
from autotester.providers.base import Provider, ProviderError
from autotester.schema.enums import IssueCategory, SourceKind
from autotester.schema.media import MediaChunk, MediaPrep, Transcript, TranscriptSegment
from autotester.schema.observation import ObservedIssue, ObservedScreen, VideoObservation
from autotester.schema.project import Project, Source
from autotester.stages.analyze_video import (
    PROMPT_NAMES,
    NoObservations,
    analyze,
    build_chunk_prompt,
)
from autotester.store.project_store import ProjectStore


class SpyProvider(Provider):
    """Counts calls and records the prompts it was handed."""

    def __init__(self, label: str, *, fail: bool = False) -> None:
        super().__init__(model=label)
        self.id = "spy"
        self._label = label
        self.calls: list[tuple[str, str]] = []   # (video path, prompt)
        self.fail = fail

    @property
    def label(self) -> str:
        return self._label

    def available(self) -> bool:
        return True

    def see_video(self, path, prompt, schema, options=None):
        self.calls.append((str(path), prompt))
        if self.fail:
            raise ProviderError("no credentials")
        return VideoObservation(
            screens=[ObservedScreen(name="Trainers", t_start=1.0, t_end=9.0)],
            issues=[ObservedIssue(t_start=5.0, screen="Trainers",
                                  category=IssueCategory.FEATURE_GAP,
                                  title="t", what_is_wrong="w")],
            summary="a trainer tool",
        )


@pytest.fixture
def prepared(tmp_path: Path) -> tuple[ProjectStore, Source]:
    store = ProjectStore("erp", tmp_path)
    store.save_project(Project(slug="erp", name="ERP", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake")
    source = store.add_source(Source(project="erp", kind=SourceKind.VIDEO,
                                     path=str(video), sha256="d", label="erp1.mp4"))
    store.save_media_prep(MediaPrep(source_id=source.id, duration_s=400.0, chunks=[
        MediaChunk(index=0, path=str(video), offset_s=0.0, length_s=180.0),
        MediaChunk(index=1, path=str(video), offset_s=165.0, length_s=180.0),
    ]))
    return store, source


# -- the rule that costs money if it is wrong ------------------------------

def test_every_model_sees_every_prompt_on_every_chunk(prepared) -> None:
    store, source = prepared
    pro, flash = SpyProvider("spy:pro"), SpyProvider("spy:flash")

    analyze(store, source, [pro, flash], docs=RepoDocs())

    assert len(pro.calls) == len(PROMPT_NAMES) * 2   # 2 prompts x 2 chunks
    assert len(flash.calls) == len(PROMPT_NAMES) * 2


def test_a_second_analyze_makes_zero_provider_calls(prepared) -> None:
    """The rule this whole stage is shaped by. A re-run after a crash, after a
    code change, or just to look again must cost nothing."""
    store, source = prepared
    pro = SpyProvider("spy:pro")

    analyze(store, source, [pro], docs=RepoDocs())
    first = len(pro.calls)
    pro.calls.clear()

    analyze(store, source, [pro], docs=RepoDocs())

    assert first > 0
    assert pro.calls == [], "a cached observation was re-requested"


def test_force_is_the_only_way_past_the_cache(prepared) -> None:
    store, source = prepared
    pro = SpyProvider("spy:pro")
    analyze(store, source, [pro], docs=RepoDocs())
    pro.calls.clear()

    analyze(store, source, [pro], docs=RepoDocs(), force=True)

    assert len(pro.calls) == len(PROMPT_NAMES) * 2


def test_adding_a_second_model_only_calls_the_new_one(prepared) -> None:
    """The cache is keyed per model, so widening the ensemble costs only the
    widening — otherwise nobody would ever add the second model."""
    store, source = prepared
    pro, flash = SpyProvider("spy:pro"), SpyProvider("spy:flash")
    analyze(store, source, [pro], docs=RepoDocs())
    pro.calls.clear()

    analyze(store, source, [pro, flash], docs=RepoDocs())

    assert pro.calls == []
    assert len(flash.calls) == len(PROMPT_NAMES) * 2


# -- failure is partial, never total ---------------------------------------

def test_one_failing_model_does_not_lose_the_other(prepared) -> None:
    """A single failed provider must not throw away the answers that arrived."""
    store, source = prepared
    working, broken = SpyProvider("spy:pro"), SpyProvider("spy:broken", fail=True)

    analysis = analyze(store, source, [working, broken], docs=RepoDocs())

    assert analysis.provider_labels == ["spy:pro"]
    assert analysis.screens


def test_every_model_failing_refuses_instead_of_writing_an_empty_analysis(
    prepared,
) -> None:
    """An empty analysis persisted after a total failure would read as "we
    watched it and found nothing" — the opposite of what happened."""
    store, source = prepared

    with pytest.raises(NoObservations, match="nothing to adjudicate"):
        analyze(store, source, [SpyProvider("spy:broken", fail=True)], docs=RepoDocs())

    assert store.load_analysis(source.id) is None


def test_analyzing_an_unprepared_recording_is_refused(tmp_path: Path) -> None:
    """Prep is where chunking and narration happen; skipping it changes the
    answer without saying so."""
    from autotester.stages.media_prep import SourceNotPrepared

    store = ProjectStore("erp", tmp_path)
    store.save_project(Project(slug="erp", name="ERP", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    source = store.add_source(Source(project="erp", kind=SourceKind.VIDEO,
                                     path=str(tmp_path / "x.mp4"), sha256="d"))

    with pytest.raises(SourceNotPrepared):
        analyze(store, source, [SpyProvider("spy:pro")], docs=RepoDocs())


# -- narration is sliced per chunk -----------------------------------------

def test_a_chunk_gets_only_its_own_narration(prepared) -> None:
    """Handing a model the whole recording's transcript while it watches three
    minutes of it invites alignment to speech it cannot see, and a quote
    attached to the wrong screen is worse than no quote."""
    store, source = prepared
    store.save_transcript(Transcript(source_id=source.id, engine="sidecar", segments=[
        TranscriptSegment(start=5.0, end=7.0, text="early words"),
        TranscriptSegment(start=200.0, end=202.0, text="later words"),
    ]))
    pro = SpyProvider("spy:pro")

    analyze(store, source, [pro], docs=RepoDocs())

    first_chunk = next(p for path, p in pro.calls if "erp1" in path)
    assert "early words" in first_chunk
    assert "later words" not in first_chunk, "chunk 0 was handed chunk 1's speech"


def test_a_silent_section_says_so_rather_than_leaving_a_gap(prepared) -> None:
    """An empty narration block invites the model to fill it."""
    store, source = prepared
    store.save_transcript(Transcript(source_id=source.id, engine="sidecar", segments=[
        TranscriptSegment(start=300.0, end=302.0, text="only late speech"),
    ]))

    prompt = build_chunk_prompt(PROMPT_NAMES[0], source, RepoDocs(),
                          MediaChunk(index=0, path="x", offset_s=0.0, length_s=180.0),
                          store.load_transcript(source.id))

    assert "no speech in this section" in prompt
    assert "{{NARRATION}}" not in prompt


@pytest.mark.parametrize("prompt_name", PROMPT_NAMES)
def test_both_prompts_exist_and_carry_the_placeholders(prompt_name: str) -> None:
    """A prompt named by the driver but absent from disk fails only when a
    real analyze runs, which is the most expensive place to find out. And a
    template missing `{{NARRATION}}` makes the injection a silent no-op —
    AT-133's lesson, one stage over."""
    text = (RepoDocs().prompts_dir / prompt_name).read_text(encoding="utf-8")

    assert "{{NARRATION}}" in text
    assert "{{SOURCE_LABEL}}" in text


def test_the_analysis_is_persisted_not_just_returned(prepared) -> None:
    """T-131's lesson: a stage that returns without persisting leaves no trace,
    and no caller remembers to save for it."""
    store, source = prepared

    analyze(store, source, [SpyProvider("spy:pro")], docs=RepoDocs())

    assert store.load_analysis(source.id) is not None


def test_timestamps_from_a_later_chunk_land_in_whole_video_time(prepared) -> None:
    """The spy reports t_start=1.0 for every chunk. Chunk 1 is offset 165s, so
    an unshifted merge would collapse both into one screen at 1.0 — the bug
    `shift` exists to prevent, seen from the driver's side."""
    store, source = prepared

    analysis = analyze(store, source, [SpyProvider("spy:pro")], docs=RepoDocs())

    assert {round(s.t_start) for s in analysis.screens} == {1, 166}
