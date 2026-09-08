"""Pull a single still out of a recording, at a second the model named.

The vision pass reports `screenshot_ts` — seconds where a screen is stable and
fully rendered. Those become the images a human sees next to an issue, so the
frame has to land where the model said and not at the nearest keyframe.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FRAME_TIMEOUT_S = 60.0


def frame_name(t_s: float) -> str:
    """Zero-padded milliseconds: `12.34` -> `00012340.png`.

    Padded so a directory listing sorts chronologically, and in milliseconds
    because two frames a third of a second apart are two different screens
    during a transition."""
    return f"{round(t_s * 1000):08d}.png"


def extract_frame(video: Path, t_s: float, out_png: Path) -> bool:
    """One frame at `t_s`. True when the file exists afterwards.

    `-ss` goes after `-i`. **The reason I originally gave for that was wrong**
    (AT-168): I claimed `-ss` before `-i` seeks to the nearest keyframe and so
    lands on a different screen. A checker tested it on ffmpeg 8.1.1 — both
    orders produced a BYTE-IDENTICAL frame at t=20s with keyframes 4.27s apart,
    because modern ffmpeg decodes to the exact timestamp either way.

    The order is kept because it is the conservative one across ffmpeg builds
    and costs nothing at this scale, not because the failure I described is
    real here. What matters is the measured property the contract now states:
    the frame lands at the second that was asked for.

    Returns a bool rather than raising: a crawl or an analysis that could not
    grab one still is not a failed analysis, and `product_map.build_screen_map`
    only ever references a PNG that exists (A5)."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video), "-ss", f"{t_s}",
             "-frames:v", "1", "-q:v", "2", str(out_png)],
            check=True, capture_output=True, timeout=FRAME_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out_png.exists()
