"""T-191/AT-587 V3/V4, real browser: the masking CSS is active for the WHOLE
recording (not just at screenshot()'s point-in-time call), and the resulting
video cannot be used to recover the fake secret it was typed into -- the same
guarantee `EvidenceMixin.screenshot()` already gives screenshots (browser-and
-secrets.md B7), now proven for a *continuous* capture. Contract:
qa/contracts/run-video.md V3, V4.

Drives `BrowserSession` step-by-step (not through the full
`run_and_grade_case` pipeline, unlike test_video_evidence.py) so this test can
interleave `page.evaluate` probes while the recording is still open -- the
pipeline runs a case start-to-finish with no hook for that. FAKE credential
only, in a fixture `.env` this test writes itself -- never a live value
(CLAUDE.md's Credentials boundary). The secret goes into the USERNAME field
(plain text input), deliberately not the password field: `<input
type="password">` is already masked by the browser's own native rendering, so
proving OUR CSS mechanism needs a field that has no such built-in disguise.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from autotester.browser.evidence import MASK_ATTR
from autotester.browser.launch import DEFAULT_VIEWPORT, RECORD_VIDEO_SIZE
from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.paths import ProjectPaths
from autotester.media.frames import extract_frame
from autotester.schema.project import Project, SecretRef

SITE = Path(__file__).resolve().parent / "fixtures" / "login_site"
FAKE_SECRET = "fixture-user-9137"  # this test's own fixture value -- never a real credential
WAIT_S = 4.0


def _skip_if_no_chromium() -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    try:
        with sync_api.sync_playwright() as pw:
            pw.chromium.launch(headless=True).close()
    except Exception as exc:  # pragma: no cover - browser binary missing
        pytest.skip(f"chromium unavailable: {type(exc).__name__}")


def _skip_if_no_ffmpeg() -> None:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10, check=True)
    except (OSError, subprocess.SubprocessError):
        pytest.skip("ffmpeg not on PATH")


def _project(base_url: str) -> Project:
    return Project(slug="video-mask", name="Video Mask", base_url=base_url,
                   allowed_domains=["127.0.0.1"], headed=False,
                   secrets=[SecretRef(key="LOGIN_USER", domains=["127.0.0.1"])])


def _record_masked_video(tmp_path: Path, base: str) -> Path:
    """Drive one case's worth of steps by hand -- fill the FAKE secret into the
    username field, hold for `WAIT_S` so the recorder captures several whole
    seconds of the masked, steady-state field, probing the computed style
    three times across the hold (V3) -- and return the finished video file."""
    project = _project(f"{base}/login.html")
    (tmp_path / ".env").write_text(f"LOGIN_USER={FAKE_SECRET}\n", encoding="utf-8")
    secrets = SecretStore.load(project, tmp_path / ".env", strict=False)
    paths = ProjectPaths("video-mask", tmp_path)
    session = BrowserSession(project, secrets, tmp_path / "runs" / "run_1", paths,
                             record_video=True)
    session.start()
    try:
        session.begin_case_video("case-mask")
        session.goto(f"{base}/login.html")
        session.fill("#username", "{{SECRET:LOGIN_USER}}")
        assert session.page.get_attribute("#username", MASK_ATTR) == "1"  # V3 precondition

        probes = []
        for _ in range(3):
            probes.append(session.page.eval_on_selector(
                "#username", "el => getComputedStyle(el).webkitTextSecurity"))
            session.page.wait_for_timeout(int(WAIT_S * 1000 / 3))
        for when, style in zip(("before", "mid", "after"), probes, strict=True):
            assert style == "disc", f"masking CSS not applied {when} the hold: {style!r}"
    finally:
        video_rel = session.end_case_video()
        session.close()

    assert video_rel is not None, "no video was recorded -- session.record_video must be True"
    video_path = tmp_path / "runs" / "run_1" / video_rel
    assert video_path.exists() and video_path.stat().st_size > 0
    return video_path


def test_masking_css_is_active_for_the_whole_hold_not_just_at_screenshot_time(
    tmp_path: Path, serve_dir: Callable[[Path], str],
) -> None:
    """V3: the three `page.evaluate` probes inside `_record_masked_video` are
    the assertion -- a failure there raises before this test's own body runs."""
    _skip_if_no_chromium()
    base = serve_dir(SITE)
    _record_masked_video(tmp_path, base)


def test_the_recorded_video_does_not_contain_the_raw_fake_secret_in_its_bytes(
    tmp_path: Path, serve_dir: Callable[[Path], str],
) -> None:
    """V4(a): a byte-level grep -- necessary, not sufficient (a compressed
    video encoding a masked field correctly would also never contain the raw
    string), but a cheap first gate."""
    _skip_if_no_chromium()
    base = serve_dir(SITE)
    video_path = _record_masked_video(tmp_path, base)

    raw = video_path.read_bytes()
    assert FAKE_SECRET.encode() not in raw
    assert FAKE_SECRET.encode("utf-16-le") not in raw  # a plausible alternate text encoding


def test_a_frame_extracted_during_the_hold_visually_differs_from_the_field_unmasked(
    tmp_path: Path, serve_dir: Callable[[Path], str],
) -> None:
    """V4(b): reuses `media/frames.py::extract_frame` (C3 -- never a second
    frame-grabbing mechanism) to pull a still from inside the masked hold
    window, then diffs it against an unmasked render of the SAME page at the
    SAME viewport (scaled to the video's own `RECORD_VIDEO_SIZE` via ffmpeg,
    since Playwright records at that resolution while the page itself renders
    at `DEFAULT_VIEWPORT`) using ffmpeg's own `ssim` filter -- no new
    image-processing dependency; ffmpeg is already this repo's frame-handling
    seam (`media/frames.py`)."""
    _skip_if_no_chromium()
    _skip_if_no_ffmpeg()
    base = serve_dir(SITE)
    video_path = _record_masked_video(tmp_path, base)

    masked_frame = tmp_path / "masked.png"
    assert extract_frame(video_path, WAIT_S / 2, masked_frame)

    unmasked_full = tmp_path / "unmasked_full.png"
    _unmasked_reference(base, unmasked_full)
    unmasked_scaled = tmp_path / "unmasked_scaled.png"
    _scale_png(unmasked_full, unmasked_scaled, RECORD_VIDEO_SIZE)

    score = _ssim(masked_frame, unmasked_scaled)
    assert score < 0.995, (
        f"masked frame and unmasked reference scored SSIM={score} -- too similar to prove "
        "the masking CSS visibly changed the field's rendering"
    )


def _unmasked_reference(base: str, out_png: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport=dict(DEFAULT_VIEWPORT))
            page.goto(f"{base}/login.html")
            page.fill("#username", FAKE_SECRET)  # raw Playwright fill: none of our masking
            page.screenshot(path=str(out_png))
        finally:
            browser.close()


def _scale_png(src: Path, dst: Path, size: dict) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vf", f"scale={size['width']}:{size['height']}",
         str(dst)],
        check=True, capture_output=True, timeout=30,
    )


def _ssim(a: Path, b: Path) -> float:
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(a), "-i", str(b), "-lavfi", "ssim", "-f", "null", "-"],
        capture_output=True, text=True, timeout=30,
    )
    match = re.search(r"All:([0-9.]+)", proc.stderr)
    assert match, f"ffmpeg produced no SSIM score:\n{proc.stderr}"
    return float(match.group(1))
