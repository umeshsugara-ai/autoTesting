"""The media primitives: chunk planning, frame naming, transcript sourcing.

Contract: qa/contracts/video-learning.md VL1. These are the pure parts — they
must be testable with no ffmpeg, no GPU and no video file, because the whole
point of VL1 is that this pipeline behaves predictably on a host that has none
of them. Measured on this host 2026-09-08: ffmpeg 8.1.1 IS present,
`faster_whisper` is NOT in the project venv, so the no-whisper path is the
default here rather than an exotic fallback.
"""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path

import pytest

from autotester.media import transcribe
from autotester.media.chunks import chunk_name, plan_chunks
from autotester.media.frames import frame_name

# -- plan_chunks: pure, and the only thing that decides where a second lands --

def test_a_short_recording_is_one_chunk() -> None:
    assert plan_chunks(30.0) == [(0.0, 30.0)]


def test_a_long_recording_is_cut_with_overlap() -> None:
    """The exact plan the design specifies. Overlap exists because a boundary
    lands mid-action about as often as not, and a model that sees only the
    second half of a click reports a screen appearing from nowhere."""
    assert plan_chunks(400.0) == [(0.0, 180.0), (165.0, 180.0), (330.0, 70.0)]


def test_a_runt_tail_is_folded_into_its_predecessor() -> None:
    """A 4-second tail costs a whole model call to say almost nothing, so it
    joins the chunk before it rather than becoming its own.

    The overlap MUST be below `MIN_TAIL_S` for this to be reachable at all —
    the loop breaks on the first remainder that fits in one chunk, and that
    remainder is always in `(overlap_s, chunk_s]`. My first version of this
    test used the defaults (overlap 15 > min tail 10), where a runt tail cannot
    occur, so it asserted on a plan the fold never touched: disabling the fold
    produced a byte-identical result. C7's INCONCLUSIVE rule is the only reason
    that surfaced — a green sabotage that meant "this test proves nothing"."""
    folded = plan_chunks(363.0, overlap_s=3.0)
    unfolded_tail = 363.0 - 354.0  # 9.0s, below MIN_TAIL_S

    assert unfolded_tail < 10.0, "precondition: this duration must produce a runt"
    assert folded == [(0.0, 180.0), (177.0, 186.0)], "the runt must join its predecessor"
    assert all(length >= 10.0 for _offset, length in folded)


def test_the_fold_is_what_produced_that_plan_not_the_loop_ending() -> None:
    """The distinction the first version missed: with the same inputs and no
    fold, the plan would carry a third 9-second chunk."""
    without_fold = [(0.0, 180.0), (177.0, 180.0), (354.0, 9.0)]

    assert plan_chunks(363.0, overlap_s=3.0) != without_fold
    assert len(plan_chunks(363.0, overlap_s=3.0)) == 2


def test_every_second_of_the_recording_is_covered() -> None:
    """A gap in the plan is a stretch of product no model ever watches, and
    nothing downstream would report its absence."""
    for duration in (45.0, 200.0, 400.0, 1000.0, 3600.0):
        plan = plan_chunks(duration)
        assert plan[0][0] == 0.0
        assert plan[-1][0] + plan[-1][1] == pytest.approx(duration)
        for (off_a, len_a), (off_b, _) in pairwise(plan):
            assert off_b <= off_a + len_a, f"gap at {off_b} for duration {duration}"


def test_a_zero_length_recording_plans_nothing() -> None:
    """`probe` returns 0.0 when it cannot read a file, so this is the shape an
    unreadable video takes — no chunks, rather than one bad one."""
    assert plan_chunks(0.0) == []
    assert plan_chunks(-5.0) == []


def test_an_overlap_at_least_as_long_as_the_chunk_is_refused() -> None:
    """It would never advance. Raising beats looping forever."""
    with pytest.raises(ValueError, match="must be shorter"):
        plan_chunks(600.0, chunk_s=60.0, overlap_s=60.0)


def test_chunk_names_sort_chronologically_and_name_their_offset() -> None:
    names = [chunk_name(i, off) for i, (off, _) in enumerate(plan_chunks(400.0))]

    assert names == ["chunk_00_0s.mp4", "chunk_01_165s.mp4", "chunk_02_330s.mp4"]
    assert names == sorted(names), "a directory listing must read in time order"


# -- frame_name --------------------------------------------------------------

def test_frame_names_sort_chronologically_and_keep_milliseconds() -> None:
    """Milliseconds because two frames a third of a second apart are two
    different screens during a transition."""
    names = [frame_name(t) for t in (0.0, 1.5, 12.34, 100.0)]

    assert names == ["00000000.png", "00001500.png", "00012340.png", "00100000.png"]
    assert names == sorted(names)


# -- transcript sourcing: sidecar first, always ------------------------------

def _sidecar(tmp_path: Path, payload: dict) -> Path:
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake")
    video.with_suffix(".transcript.json").write_text(json.dumps(payload), encoding="utf-8")
    return video


def test_an_existing_sidecar_is_reused_and_whisper_is_never_called(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The corpus already carries known-good transcripts. Re-running whisper
    would spend GPU minutes to produce a DIFFERENT transcript — and narration
    is injected as ground truth, so a regenerated line is a changed quote from
    a real person (I8)."""
    called = {"n": 0}
    monkeypatch.setattr(transcribe, "transcribe_subprocess",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    video = _sidecar(tmp_path, {
        "segments": [{"start": 1.42, "end": 3.42, "text": "Move to next stage"}],
        "speech_seconds": 2.0})

    result = transcribe.transcribe(video, "src_1")

    assert [s.text for s in result.segments] == ["Move to next stage"]
    assert called["n"] == 0, "whisper ran despite a sidecar being present"


def test_a_recording_with_no_sidecar_and_no_whisper_is_silent_not_broken(
    tmp_path: Path,
) -> None:
    """`engine="none"` is a real outcome: a recording with no narration ON
    RECORD. It is NOT a claim the video is silent, which is the distinction
    AT-134 was about."""
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake")

    result = transcribe.transcribe(video, "src_1", use_whisper=False)

    assert result.engine == "none"
    assert result.segments == []


def test_a_malformed_sidecar_does_not_stop_media_prep(tmp_path: Path) -> None:
    """AT-133's lesson, one stage earlier: best-effort must mean best-effort,
    and `unreadable` must not read as silence downstream."""
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake")
    video.with_suffix(".transcript.json").write_text("[1, 2, 3]", encoding="utf-8")

    result = transcribe.transcribe(video, "src_1")

    assert result.engine == "unreadable"
    assert result.segments == []


def test_find_sidecar_only_reports_one_that_exists(tmp_path: Path) -> None:
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake")

    assert transcribe.find_sidecar(video) is None

    video.with_suffix(".transcript.json").write_text("{}", encoding="utf-8")
    assert transcribe.find_sidecar(video) is not None


def test_a_negative_overlap_is_refused_rather_than_silently_skipping_footage() -> None:
    """AT-167: a negative overlap makes the step LONGER than a chunk, so the
    plan skips stretches of the recording entirely — and a gap is the one
    failure nothing downstream reports, because a screen no model watched
    leaves no trace anywhere.

    Sabotaging this guard was INCONCLUSIVE before this test existed (C7)."""
    with pytest.raises(ValueError, match="cannot be negative"):
        plan_chunks(400.0, overlap_s=-5.0)


@pytest.mark.parametrize("kwargs", [
    {"chunk_s": 0.0},
    {"chunk_s": -10.0},
    {"chunk_s": float("inf")},
])
def test_an_impossible_chunk_size_is_refused(kwargs: dict) -> None:
    """Validated BEFORE the short-circuits. Checked after them, an absurd chunk
    size was accepted whenever the recording happened to be shorter than it —
    the guard fired only on inputs that were already fine."""
    with pytest.raises(ValueError, match="positive, finite"):
        plan_chunks(400.0, **kwargs)


def test_an_infinite_duration_is_refused_rather_than_looping() -> None:
    with pytest.raises(ValueError, match="finite"):
        plan_chunks(float("inf"))
