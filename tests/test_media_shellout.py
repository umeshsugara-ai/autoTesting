"""What this stage hands to ffmpeg, and what it does when ffmpeg is not there.

AT-170: four behaviours the contract depends on had **no regression guard at
all**. A checker sabotaged each one and every sabotage produced **zero
failures** — reported INCONCLUSIVE per C7, which is exactly right and exactly
why they are still open: the behaviours are correct, and nothing would notice
if they stopped being.

They are grouped here rather than in `test_media.py` because they are one
responsibility: the boundary between this codebase and a program it does not
control. `subprocess.run` is intercepted, so nothing here needs ffmpeg — the
argv IS the artifact under test.

Contract: qa/contracts/video-learning.md VL1.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from autotester.media import chunks as chunks_mod
from autotester.media import frames as frames_mod
from autotester.media import probe as probe_mod


class Recorder:
    """Stands in for `subprocess.run`, keeping every argv it was given."""

    def __init__(self, *, fail: set[str] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.fail = fail or set()

    def __call__(self, argv, *args, **kwargs):
        self.calls.append(list(argv))
        if argv[0] in self.fail:
            raise FileNotFoundError(argv[0])
        return subprocess.CompletedProcess(argv, 0, stdout="{}", stderr="")

    def argv(self) -> list[str]:
        assert len(self.calls) == 1, f"expected one call, got {self.calls}"
        return self.calls[0]


def after(argv: list[str], flag: str) -> int:
    assert flag in argv, f"{flag} missing from {argv}"
    return argv.index(flag)


# -- -ss goes after -i, in both places that seek -----------------------------

def test_a_chunk_is_cut_with_the_seek_AFTER_the_input(monkeypatch, tmp_path: Path) -> None:
    """The ordering is the conservative one across ffmpeg builds, and the
    docstring in `encode_chunks` is careful to say the failure it once claimed
    for the other order does NOT happen on ffmpeg 8.1.1 (AT-168).

    It is still asserted, because every timestamp downstream is relative to a
    chunk offset: if a cut ever stopped landing where the plan says, every
    issue's reported second would move with it, and nothing else in the suite
    would say a word."""
    recorder = Recorder()
    monkeypatch.setattr(chunks_mod.subprocess, "run", recorder)

    chunks_mod.encode_chunks(tmp_path / "in.mp4", tmp_path / "out", [(30.0, 180.0)])

    argv = recorder.argv()
    assert after(argv, "-ss") > after(argv, "-i"), argv
    assert argv[after(argv, "-ss") + 1] == "30.0"
    assert argv[after(argv, "-t") + 1] == "180.0"


def test_a_frame_is_grabbed_with_the_seek_AFTER_the_input(monkeypatch, tmp_path: Path) -> None:
    """Same ordering, the other caller. A frame is shown to a human as
    evidence of a specific second, so a seek that lands elsewhere is a
    screenshot that quietly proves the wrong thing."""
    recorder = Recorder()
    monkeypatch.setattr(frames_mod.subprocess, "run", recorder)
    monkeypatch.setattr(frames_mod, "is_complete_png", lambda path: True)

    frames_mod.extract_frame(tmp_path / "in.mp4", 20.0, tmp_path / "f.png")

    argv = recorder.argv()
    assert after(argv, "-ss") > after(argv, "-i"), argv
    assert argv[after(argv, "-ss") + 1] == "20.0"


# -- both binaries, not either ----------------------------------------------

@pytest.mark.parametrize("missing", ["ffmpeg", "ffprobe"])
def test_one_binary_present_is_not_enough(monkeypatch, missing: str) -> None:
    """Chunking needs ffmpeg and probing needs ffprobe. A box with one and not
    the other would degrade **halfway through** rather than at the start, which
    is the worse place to find out — the whole reason `prepare` degrades rather
    than crashing."""
    monkeypatch.setattr(probe_mod.subprocess, "run", Recorder(fail={missing}))

    assert probe_mod.ffmpeg_available() is False


def test_both_present_is_enough(monkeypatch) -> None:
    """The other half: a guard that always says False guards nothing."""
    monkeypatch.setattr(probe_mod.subprocess, "run", Recorder())

    assert probe_mod.ffmpeg_available() is True


# -- an unreadable recording is a fact, not an exception ---------------------

def test_a_recording_that_cannot_be_probed_returns_zeros(monkeypatch, tmp_path: Path) -> None:
    """Zeros rather than an exception, because the caller's job is to record
    what is knowable about a source and "we could not read this" is knowable.

    `plan_chunks(0)` returns no chunks, so the zero propagates as "nothing to
    cut" rather than as a bad plan — the degrade path depends on this, and
    would turn into a traceback out of `prepare` if it ever raised."""
    monkeypatch.setattr(probe_mod.subprocess, "run", Recorder(fail={"ffprobe"}))

    assert probe_mod.probe(tmp_path / "gone.mp4") == (0.0, 0, 0)
    assert chunks_mod.plan_chunks(0.0) == []


def test_unreadable_json_from_ffprobe_is_the_same_fact(monkeypatch, tmp_path: Path) -> None:
    """A malformed answer and no answer are the same thing to a caller, and
    only one of the two was ever likely to be exercised by hand."""
    class Garbage(Recorder):
        def __call__(self, argv, *args, **kwargs):
            self.calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, stdout="not json", stderr="")

    monkeypatch.setattr(probe_mod.subprocess, "run", Garbage())

    assert probe_mod.probe(tmp_path / "x.mp4") == (0.0, 0, 0)
