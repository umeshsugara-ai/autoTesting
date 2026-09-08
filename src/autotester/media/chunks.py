"""Split a recording into overlapping chunks a vision model can actually read.

Pure planning here; the encode is `encode_chunks`, which shells out to ffmpeg.
Kept apart because the plan is the part with the interesting edge cases and it
must be testable without a video file or a binary on PATH.

Why overlap at all: a chunk boundary lands mid-action about as often as not, and
a model that sees only the second half of a click reports a screen appearing
from nowhere. The overlap gives the next chunk enough lead-in to recognise what
it walked in on; `stages/adjudicate.py` then drops what it sees twice (A4).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from autotester.schema.media import MediaChunk

DEFAULT_CHUNK_S = 180.0
DEFAULT_OVERLAP_S = 15.0
MIN_TAIL_S = 10.0
"""A tail shorter than this is folded into the previous chunk rather than sent
on its own: a 4-second clip costs a whole model call to say almost nothing.

**Reachable only when `overlap_s < MIN_TAIL_S`.** The loop breaks on the first
offset whose remainder fits in one chunk, and that remainder is always in
`(overlap_s, chunk_s]` — so at the DEFAULTS (overlap 15 > min tail 10) a runt
tail cannot arise at all. Recorded because a test written at the defaults
appears to exercise this branch and does not: the plan is identical with the
fold disabled, which is how it was found (an INCONCLUSIVE sabotage under C7).
The branch still earns its place — `encode_chunks` is called with a smaller
overlap for short recordings, where the case is real."""


def plan_chunks(duration_s: float, *, chunk_s: float = DEFAULT_CHUNK_S,
                overlap_s: float = DEFAULT_OVERLAP_S,
                min_tail_s: float = MIN_TAIL_S) -> list[tuple[float, float]]:
    """`(offset, length)` pairs covering `duration_s`, overlapping by `overlap_s`.

    Pure. Every downstream timestamp is shifted by its chunk's offset in code
    (`adjudicate.shift`), never by the model, so this function's output is the
    only thing that decides where a reported second actually lands."""
    if duration_s <= 0:
        return []
    if duration_s <= chunk_s:
        return [(0.0, duration_s)]
    if overlap_s >= chunk_s:
        raise ValueError(f"overlap {overlap_s}s must be shorter than chunk {chunk_s}s")

    step = chunk_s - overlap_s
    plan: list[tuple[float, float]] = []
    offset = 0.0
    while offset < duration_s:
        remaining = duration_s - offset
        if remaining <= chunk_s:
            if remaining < min_tail_s and plan:
                # Fold the runt into its predecessor rather than spend a call on it.
                prev_offset, _ = plan[-1]
                plan[-1] = (prev_offset, duration_s - prev_offset)
            else:
                plan.append((offset, remaining))
            break
        plan.append((offset, chunk_s))
        offset += step
    return plan


def chunk_name(index: int, offset_s: float) -> str:
    """Sortable and self-describing: the offset is in the filename because a
    chunk that loses its plan is otherwise an anonymous clip."""
    return f"chunk_{index:02d}_{int(offset_s)}s.mp4"


def encode_chunks(source: Path, out_dir: Path,
                  plan: list[tuple[float, float]]) -> list[MediaChunk]:
    """Cut `source` into `plan`'s pieces with ffmpeg. Accurate-seek re-encode.

    `-ss` AFTER `-i` is deliberate and costs real time: placed before, ffmpeg
    seeks to the nearest keyframe, so a chunk can start up to several seconds
    from where the plan says. Every timestamp this pipeline reports is relative
    to a chunk offset, so a keyframe-rounded cut silently moves every issue's
    reported second. Slower and correct beats fast and quietly wrong.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks: list[MediaChunk] = []
    for index, (offset_s, length_s) in enumerate(plan):
        path = out_dir / chunk_name(index, offset_s)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(source), "-ss", f"{offset_s}", "-t", f"{length_s}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
             "-c:a", "aac", str(path)],
            check=True, capture_output=True,
        )
        chunks.append(MediaChunk(index=index, offset_s=offset_s, length_s=length_s,
                                 path=str(path)))
    return chunks
