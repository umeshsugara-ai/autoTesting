"""Ask ffmpeg what a recording actually is, and whether ffmpeg is here at all.

Every function degrades rather than raising: the pipeline's rule (VL1) is that
media prep without ffmpeg produces a smaller `MediaPrep`, never a crash. A
recording the system cannot chunk is still a recording it can watch whole.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

FFPROBE_TIMEOUT_S = 60.0


def ffmpeg_available() -> bool:
    """True when both ffmpeg and ffprobe can be run.

    Both, not either: chunking needs ffmpeg and probing needs ffprobe, and a
    box with one and not the other would degrade halfway through instead of
    at the start, which is the worse place to find out."""
    for binary in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([binary, "-version"], check=True, capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return False
    return True


def ffmpeg_version() -> str | None:
    try:
        out = subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return out.splitlines()[0].strip() if out else None


def probe(path: Path) -> tuple[float, int, int]:
    """`(duration_s, width, height)`, or zeros when it cannot be determined.

    Zeros rather than an exception because the caller's job is to record what
    is knowable about a source, and "we could not read this" is a fact worth
    persisting. `plan_chunks(0)` returns no chunks, so a zero duration
    propagates as "nothing to cut" rather than as a bad plan."""
    try:
        raw = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            check=True, capture_output=True, text=True, timeout=FFPROBE_TIMEOUT_S).stdout
        data = json.loads(raw)
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0.0, 0, 0

    duration = 0.0
    try:
        duration = float(data.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        duration = 0.0

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            try:
                return duration, int(stream.get("width", 0)), int(stream.get("height", 0))
            except (TypeError, ValueError):
                return duration, 0, 0
    return duration, 0, 0
