"""VL1c's measured-placement half, closed by measurement — not by argument
order. `test_media_shellout.py` proves the `-ss`-after-`-i` argv shape is
what's called; this file proves the property the contract actually cares
about: **the frame that lands IS the second that was named**, verified by
reading the pixel content back, on a real ffmpeg, with no argv assertion at
all. If a future ffmpeg build (or a future maintainer) changes the seek form,
this file still passes as long as the placement stays correct — exactly
VL1c's own words: "judged against the measured property, not against the
comment."

Contract: qa/contracts/video-learning.md VL1c (HIGH-criticality). Kept apart
from `test_media.py` (deliberately ffmpeg-free, VL1's own no-ffmpeg-no-GPU
promise) and `test_media_shellout.py` (the argv half) — one file, one job.

Skipped whole when ffmpeg/ffprobe are not on PATH (`ffmpeg_available()`) so a
host without them still runs the rest of the suite; this repo's own host has
ffmpeg 8.1.1, so it is exercised here, not merely gestured at.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from autotester.media.chunks import encode_chunks, plan_chunks
from autotester.media.frames import extract_frame
from autotester.media.probe import ffmpeg_available

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not on PATH — VL1's own no-ffmpeg promise "
                                   "means the rest of the suite must still pass without them"
)

SIZE = "64x64"
# second -> (R, G, B). Chosen maximally distinguishable so compression noise
# on a solid field can never be mistaken for the wrong second's colour.
COLOURS: dict[int, tuple[int, int, int]] = {0: (255, 0, 0), 1: (0, 255, 0), 2: (0, 0, 255)}
TOLERANCE = 40  # generous against libx264 crf-18 noise on a flat field


@pytest.fixture(scope="module")
def three_second_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A real 3-second, 3-frame (1fps) video: second N is a pure, known colour.
    Built with ffmpeg's own `color` source + concat demuxer — no dependency
    beyond ffmpeg itself, and no hand-rolled container/codec logic to trust."""
    root = tmp_path_factory.mktemp("vl1c")
    segments = []
    for sec, (r, g, b) in COLOURS.items():
        seg = root / f"seg{sec}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", f"color=c=0x{r:02x}{g:02x}{b:02x}:s={SIZE}:r=1:d=1",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(seg)],
            check=True, capture_output=True, timeout=30,
        )
        segments.append(seg)
    listfile = root / "list.txt"
    listfile.write_text("".join(f"file '{s.name}'\n" for s in segments), encoding="utf-8")
    out = root / "source.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c", "copy", str(out)],
        check=True, capture_output=True, timeout=30, cwd=root,
    )
    return out


def _measured_colour(png: Path) -> tuple[int, int, int]:
    """Read a PNG's centre-pixel colour via a fresh, independent ffmpeg call --
    never the code under test, and no image library dependency for one test."""
    raw = subprocess.run(
        ["ffmpeg", "-y", "-i", str(png), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True, timeout=15,
    ).stdout
    w, h = 64, 64
    cx, cy = w // 2, h // 2
    i = (cy * w + cx) * 3
    return raw[i], raw[i + 1], raw[i + 2]


def _assert_matches_second(png: Path, second: int) -> None:
    expected = COLOURS[second]
    measured = _measured_colour(png)
    for channel, (exp, got) in enumerate(zip(expected, measured, strict=True)):
        assert abs(exp - got) <= TOLERANCE, (
            f"second {second}: channel {channel} expected {exp}, measured {got} "
            f"(full expected={expected}, measured={measured})"
        )


def test_a_chunks_first_frame_is_the_second_the_plan_named(
    three_second_video: Path, tmp_path: Path,
) -> None:
    """encode_chunks, for real. No argv inspection anywhere in this test --
    only the produced chunk's actual first-frame content."""
    plan = plan_chunks(3.0, chunk_s=1.0, overlap_s=0.0, min_tail_s=0.0)
    assert plan == [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)]
    chunks = encode_chunks(three_second_video, tmp_path / "chunks", plan)
    assert len(chunks) == 3

    for chunk, second in zip(chunks, (0, 1, 2), strict=True):
        first_frame = tmp_path / f"chunk{second}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-i", chunk.path, "-frames:v", "1", str(first_frame)],
            check=True, capture_output=True, timeout=15,
        )
        _assert_matches_second(first_frame, second)


def test_extract_frame_lands_on_the_second_it_was_asked_for(
    three_second_video: Path, tmp_path: Path,
) -> None:
    """extract_frame, for real, at each of the three named seconds directly
    on the source (not a chunk) -- the other call site VL1c governs."""
    for second in (0, 1, 2):
        out_png = tmp_path / f"frame{second}.png"
        ok = extract_frame(three_second_video, float(second), out_png)
        assert ok is True
        _assert_matches_second(out_png, second)
