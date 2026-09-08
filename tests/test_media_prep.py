"""MEDIA PREP degrades, never crashes — VL1.

The interesting behaviour of this stage is what it does on a host that is
missing something. Measured on this host 2026-09-08: ffmpeg 8.1.1 present,
`faster_whisper` absent from the project venv. So the no-whisper path is what
actually runs here, and the no-ffmpeg path is simulated rather than exotic.

Contract: qa/contracts/video-learning.md VL1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.schema.analysis import AnalysedScreen, VideoAnalysis
from autotester.schema.enums import SourceKind
from autotester.schema.project import Project, Source
from autotester.stages import media_prep
from autotester.store.project_store import ProjectStore


@pytest.fixture
def store(tmp_path: Path) -> ProjectStore:
    s = ProjectStore("demo", tmp_path)
    s.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                           allowed_domains=["demo.test"]))
    return s


def a_source(store: ProjectStore, tmp_path: Path, *, sidecar: str | None = None) -> Source:
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake-mp4")
    if sidecar is not None:
        video.with_suffix(".transcript.json").write_text(sidecar, encoding="utf-8")
    return store.add_source(Source(project="demo", kind=SourceKind.VIDEO,
                                   path=str(video), sha256="deadbeef"))


def no_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(media_prep.probe_mod, "ffmpeg_available", lambda: False)


# -- VL1: degrade, never crash ----------------------------------------------

def test_without_ffmpeg_prep_still_produces_one_usable_chunk(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deliberately not an empty chunk list. A caller iterating `prep.chunks`
    then does the right thing on a host without ffmpeg instead of silently
    doing nothing — one long video a model can still watch whole."""
    no_ffmpeg(monkeypatch)
    source = a_source(store, tmp_path)

    prep = media_prep.prepare(store, source, use_whisper=False)

    assert len(prep.chunks) == 1
    assert prep.chunks[0].path == str(tmp_path / "erp1.mp4")
    assert prep.ffmpeg_version is None, "the absent version is what records WHY there is one chunk"


def test_prep_persists_everything_it_learned(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T-131's whole lesson: a stage that returns without persisting leaves no
    trace on disk, and no caller remembers to save for it."""
    no_ffmpeg(monkeypatch)
    source = a_source(store, tmp_path)

    media_prep.prepare(store, source, use_whisper=False)

    assert store.load_media_prep(source.id) is not None
    assert store.load_transcript(source.id) is not None


def test_a_sidecar_is_reused_through_the_whole_stage(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End to end, not just in `transcribe`: the narration a tester actually
    spoke must survive prep byte-for-byte."""
    no_ffmpeg(monkeypatch)
    source = a_source(store, tmp_path, sidecar=(
        '{"segments": [{"start": 1.42, "end": 3.42, "text": "Move to next stage"}],'
        ' "speech_seconds": 2.0}'))

    media_prep.prepare(store, source, use_whisper=False)

    saved = store.load_transcript(source.id)
    assert saved is not None
    assert [s.text for s in saved.segments] == ["Move to next stage"]
    assert saved.speech_seconds == 2.0


def test_running_prep_twice_does_not_change_what_was_said(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Idempotent on the transcript. Narration is injected as ground truth, so
    a second run that produced different words would rewrite a real person's
    quote (I8)."""
    no_ffmpeg(monkeypatch)
    source = a_source(store, tmp_path, sidecar=(
        '{"segments": [{"start": 1.0, "end": 2.0, "text": "this should say Save"}],'
        ' "speech_seconds": 1.0}'))

    media_prep.prepare(store, source, use_whisper=False)
    first = store.load_transcript(source.id)
    media_prep.prepare(store, source, use_whisper=False)
    second = store.load_transcript(source.id)

    assert first is not None and second is not None
    assert [s.text for s in first.segments] == [s.text for s in second.segments]


# -- refusals that name what the operator must do ---------------------------

def test_a_source_whose_file_vanished_is_refused_by_name(
    store: ProjectStore, tmp_path: Path,
) -> None:
    source = store.add_source(Source(project="demo", kind=SourceKind.VIDEO,
                                     path=str(tmp_path / "gone.mp4"), sha256="x"))

    with pytest.raises(FileNotFoundError, match="not a readable file"):
        media_prep.prepare(store, source, use_whisper=False)


def test_a_stage_needing_prep_is_sent_to_the_host_not_told_to_retry(
    store: ProjectStore,
) -> None:
    """`analyze` runs in the CONTAINER, where prep cannot be performed at all,
    so "run it here" is advice it cannot follow. The refusal has to name the
    host command."""
    with pytest.raises(media_prep.SourceNotPrepared) as caught:
        media_prep.require_prepared(store, "src_missing")

    assert "media prep" in str(caught.value)
    assert "HOST" in str(caught.value)


# -- frames ------------------------------------------------------------------

def test_frames_are_extracted_only_for_the_seconds_the_model_named(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    asked: list[float] = []

    def fake_extract(video: Path, t_s: float, out_png: Path) -> bool:
        asked.append(t_s)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        out_png.write_bytes(b"png")
        return True

    monkeypatch.setattr(media_prep.frame_mod, "extract_frame", fake_extract)
    source = a_source(store, tmp_path)
    analysis = VideoAnalysis(source_id=source.id, screens=[
        AnalysedScreen(name="Home", t_start=1.0, screenshot_ts=[1.5, 9.0]),
        AnalysedScreen(name="Home", t_start=9.0, screenshot_ts=[9.0]),  # duplicate second
    ])

    written = media_prep.extract_frames(store, source, analysis)

    assert asked == [1.5, 9.0], "a second named twice must not be extracted twice"
    assert len(written) == 2


def test_a_frame_that_could_not_be_grabbed_is_omitted_not_faked(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing still is a gap in the evidence, not a failed analysis — and
    nothing downstream may reference a PNG that does not exist (A5)."""
    monkeypatch.setattr(media_prep.frame_mod, "extract_frame",
                        lambda video, t_s, out_png: False)
    source = a_source(store, tmp_path)
    analysis = VideoAnalysis(source_id=source.id, screens=[
        AnalysedScreen(name="Home", t_start=1.0, screenshot_ts=[1.5])])

    assert media_prep.extract_frames(store, source, analysis) == []
