"""MEDIA PREP degrades, never crashes — VL1.

The interesting behaviour of this stage is what it does on a host that is
missing something. Measured on this host 2026-09-08: ffmpeg 8.1.1 present,
`faster_whisper` absent from the project venv. So the no-whisper path is what
actually runs here, and the no-ffmpeg path is simulated rather than exotic.

Contract: qa/contracts/video-learning.md VL1.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

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


def test_a_stage_needing_prep_is_sent_to_a_command_that_exists(
    store: ProjectStore,
) -> None:
    """AT-163. `analyze` runs in the CONTAINER, where prep cannot be performed,
    so the refusal has to send the operator to the host — and to a command that
    is actually registered.

    It said `autotester media prep`. There is no `media` command; they live
    under `ingest`. And my first test asserted the substring "media prep", so a
    passing test PROTECTED the dead end. This one asks the CLI itself."""
    from typer.testing import CliRunner

    from autotester.cli import app

    with pytest.raises(media_prep.SourceNotPrepared) as caught:
        media_prep.require_prepared(store, "src_missing")
    message = str(caught.value)

    assert "HOST" in message
    quoted = re.search(r"`autotester ([^`]+)`", message)
    assert quoted, f"the refusal named no command: {message}"

    # AT-171: my first version captured only the COMMAND GROUP with a non-greedy
    # `([a-z ]+?)`, so `ingest frobnicate` and `ingest list` both passed --
    # `--help` on a group proves the GROUP is registered, not the subcommand.
    # Run the whole quoted invocation, arguments included, as an operator would.
    argv = shlex.split(quoted.group(1))
    result = CliRunner().invoke(app, argv)

    # The oracle, arrived at by measuring what each failure shape prints:
    # click emits its `Usage:` banner for an unregistered command, an
    # unregistered SUBcommand, and the wrong number of arguments alike, while a
    # correct invocation reaches the application's own message. So "no usage
    # banner" rejects all three at once.
    #
    # AT-171: my first oracle was `--help` on the captured command GROUP, under
    # which `ingest frobnicate` and `ingest list` both passed -- it proved the
    # group was registered, not that the invocation works. My second was a pair
    # of substring checks, and sabotaging the message to a REGISTERED-but-wrong
    # command (`ingest list`, which takes one argument, not two) came back
    # INCONCLUSIVE under C7. This is the third, and it bites on that case.
    assert "Usage:" not in result.output, (
        f"the refusal sends the operator to `autotester {quoted.group(1)}`, which the "
        f"CLI rejects as a usage error: {' '.join(result.output.split())[:160]!r}")


def test_the_unreadable_recording_refusal_is_not_a_green_success_line(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-164, and it is the sharper half. With ffmpeg PRESENT and a file it
    cannot read, prep used to persist `chunks=[]` and the CLI printed a green
    success line — a source nothing can ever watch, reported as prepared. That
    is the exact shape `_unchunked` exists to prevent, reached by the other
    branch."""
    monkeypatch.setattr(media_prep.probe_mod, "ffmpeg_available", lambda: True)
    monkeypatch.setattr(media_prep.probe_mod, "probe", lambda path: (0.0, 0, 0))
    source = a_source(store, tmp_path)

    with pytest.raises(media_prep.UnreadableRecording, match="read no duration"):
        media_prep.prepare(store, source, use_whisper=False)

    assert store.load_media_prep(source.id) is None, "a refused prep must persist nothing"


def test_a_failed_cut_writes_no_media_json(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-166: a partial chunk set is worse than none, because it reads as a
    complete plan and nothing downstream knows footage is missing."""
    monkeypatch.setattr(media_prep.probe_mod, "ffmpeg_available", lambda: True)
    monkeypatch.setattr(media_prep.probe_mod, "probe", lambda path: (400.0, 1920, 1080))

    def boom(video, out_dir, plan):
        raise RuntimeError("ffmpeg exited 1 on chunk 2 of 3")

    monkeypatch.setattr(media_prep.chunk_mod, "encode_chunks", boom)
    source = a_source(store, tmp_path)

    with pytest.raises(media_prep.UnreadableRecording, match="could not cut"):
        media_prep.prepare(store, source, use_whisper=False)

    assert store.load_media_prep(source.id) is None


def test_the_shipped_prep_command_answers_a_refusal_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-166, cycle 3, and it is my cycle-2 mistake repeating: I made
    `prepare` raise a typed `UnreadableRecording` and never widened the CLI's
    except clause, which caught only `(FileNotFoundError, ValueError)`. So the
    SHIPPED command answered a deliberate refusal with a raw Rich traceback —
    the stage was fixed and the path an operator runs was not, exactly as in
    AT-163 one cycle earlier.

    This drives the real CLI, because that is the only place the bug lived."""
    from typer.testing import CliRunner

    from autotester.cli import app

    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    video = tmp_path / "broken.mp4"
    video.write_bytes(b"")          # 0 bytes: ffmpeg reads no duration
    source = store.add_source(Source(project="demo", kind=SourceKind.VIDEO,
                                     path=str(video), sha256="deadbeef"))
    monkeypatch.setattr(media_prep.probe_mod, "ffmpeg_available", lambda: True)
    monkeypatch.setattr(media_prep.probe_mod, "probe", lambda path: (0.0, 0, 0))

    result = CliRunner().invoke(app, ["ingest", "prep", "demo", source.id])

    assert result.exit_code == 2, result.output
    assert "Traceback" not in result.output, "a refusal must not surface as a crash"
    assert "read no duration" in result.output
    assert store.load_media_prep(source.id) is None
