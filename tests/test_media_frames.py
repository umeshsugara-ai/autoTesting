"""Frame extraction: what counts as evidence, and what a killed ffmpeg leaves.

Split from `test_media_prep.py` at doctor's 300-line cap, by responsibility:
that file is about PREPARING a recording (probe, chunk, transcribe, and the
refusals when it cannot), this one about pulling stills out of one afterwards.

They collected different bugs, which is the argument for the split: prep's were
about reporting success for work that did not happen (AT-164, AT-166); frames'
were about accepting a file as evidence when nobody finished writing it
(AT-165, twice).

Contract: qa/contracts/video-learning.md VL1 / I-VL4.
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


def a_source(store: ProjectStore, tmp_path: Path) -> Source:
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake-mp4")
    return store.add_source(Source(project="demo", kind=SourceKind.VIDEO,
                                   path=str(video), sha256="deadbeef"))


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


def test_a_zero_byte_leftover_png_is_not_returned_as_evidence(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-165: `png.exists()` alone reused ANY file at the expected name —
    including a truncated leftover from an interrupted run — and handed it back
    as evidence. A frame with no bytes shows a human nothing, so a report built
    on it is worse than one that admits the still is missing.

    Sabotaging the fix was INCONCLUSIVE before this test existed (C7): I had
    changed the code and pinned none of it."""
    frames_dir = store.paths.source_frames_dir("src_x")
    frames_dir.mkdir(parents=True, exist_ok=True)
    stale = frames_dir / media_prep.frame_mod.frame_name(1.5)
    stale.write_bytes(b"")  # an interrupted ffmpeg leaves exactly this

    monkeypatch.setattr(media_prep.frame_mod, "extract_frame",
                        lambda video, t_s, out_png: False)
    source = a_source(store, tmp_path)
    store.paths.source_frames_dir(source.id).mkdir(parents=True, exist_ok=True)
    empty = store.paths.source_frames_dir(source.id) / media_prep.frame_mod.frame_name(1.5)
    empty.write_bytes(b"")
    analysis = VideoAnalysis(source_id=source.id, screens=[
        AnalysedScreen(name="Home", t_start=1.0, screenshot_ts=[1.5])])

    assert media_prep.extract_frames(store, source, analysis) == []


def test_a_truncated_png_is_not_returned_as_evidence(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-165, cycle 3. `st_size > 0` closed only the EMPTY half. A checker
    truncated a real 277,206-byte frame to 92,402 and `extract_frames` returned
    it as evidence with zero re-extract calls — ffprobe rejects it outright.

    The path is reachable with no guard anywhere: the 60s timeout kills ffmpeg
    mid-write and the old failure path returned False WITHOUT unlinking, so the
    cache adopted the half-file permanently."""
    monkeypatch.setattr(media_prep.frame_mod, "extract_frame",
                        lambda video, t_s, out_png: False)
    source = a_source(store, tmp_path)
    frames_dir = store.paths.source_frames_dir(source.id)
    frames_dir.mkdir(parents=True, exist_ok=True)
    truncated = media_prep.frame_mod.PNG_MAGIC + b"x" * 200   # begins right, never ends
    (frames_dir / media_prep.frame_mod.frame_name(1.5)).write_bytes(truncated)
    analysis = VideoAnalysis(source_id=source.id, screens=[
        AnalysedScreen(name="Home", t_start=1.0, screenshot_ts=[1.5])])

    assert media_prep.extract_frames(store, source, analysis) == []


def test_a_killed_extract_leaves_no_half_file_behind(tmp_path: Path) -> None:
    """The other half of the same bug: the cache only adopts a partial frame
    because the failure path left one there."""
    import subprocess

    from autotester.media import frames

    out = tmp_path / "f.png"

    def die(*args, **kwargs):
        out.write_bytes(frames.PNG_MAGIC + b"half")   # ffmpeg mid-write
        raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=60)

    import unittest.mock as mock
    with mock.patch.object(subprocess, "run", die):
        assert frames.extract_frame(tmp_path / "v.mp4", 1.5, out) is False

    assert not out.exists(), "a killed extract must not leave a partial frame on disk"


def test_a_frame_already_on_disk_with_real_bytes_is_reused(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The other side of AT-165: caching a good frame is the point, and a fix
    that re-extracted everything would trade a wrong answer for a slow one."""
    calls: list[float] = []
    monkeypatch.setattr(media_prep.frame_mod, "extract_frame",
                        lambda video, t_s, out_png: calls.append(t_s) or False)
    source = a_source(store, tmp_path)
    good_dir = store.paths.source_frames_dir(source.id)
    good_dir.mkdir(parents=True, exist_ok=True)
    whole_png = (media_prep.frame_mod.PNG_MAGIC + b"x" * 200
                 + media_prep.frame_mod.PNG_END)
    (good_dir / media_prep.frame_mod.frame_name(1.5)).write_bytes(whole_png)
    analysis = VideoAnalysis(source_id=source.id, screens=[
        AnalysedScreen(name="Home", t_start=1.0, screenshot_ts=[1.5])])

    written = media_prep.extract_frames(store, source, analysis)

    assert len(written) == 1
    assert calls == [], "a good cached frame must not be re-extracted"
