"""Only a recording can become a video source — on every path that makes one. AT-433.

Found by live-browser validation, not by any test. Registering a source by path
checked only that the file existed, and an upload with an unknown suffix was
silently renamed `.video`. The checker registered `C:\\Windows\\win.ini` and the
repo's own `.env` credential file as VIDEO sources, each shown with its full path
and an Analyze button, and uploaded `evil.txt` as `recording.video`.

The rule now lives once, in `stages.ingest.require_recording_suffix`, and is read
by all three paths: `register_source` (the UI path form and the CLI) and the
upload route.

**Every refused file below genuinely EXISTS.** Before this fix, a missing file was
already refused as "not found" — so a test using a nonexistent `x.ini` would pass
with the new rule deleted, proving nothing about it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from autotester.cli import app as cli_app
from autotester.schema.project import Project
from autotester.stages.ingest import NotARecording, register_source
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app

_NOT_RECORDINGS = ["system.ini", ".env", "notes.txt", "payload.exe", "clip.mp4.txt", "noext"]


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def store(scratch_root: Path) -> ProjectStore:
    s = ProjectStore("demo", scratch_root)
    s.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                           allowed_domains=["demo.test"]))
    return s


def _real_file(folder: Path, name: str, body: bytes = b"not a video") -> Path:
    path = folder / name
    path.write_bytes(body)
    assert path.exists(), "precondition: the refusal must not be 'file not found'"
    return path


# -- the stage function: the one rule -----------------------------------------

@pytest.mark.parametrize("name", _NOT_RECORDINGS)
def test_a_real_non_recording_file_is_refused_and_nothing_is_saved(
    store: ProjectStore, tmp_path: Path, name: str,
) -> None:
    """Includes `.env`: for a dotfile `Path('.env').suffix` is `''`, so the
    credential file is refused by the same rule, not by a special case."""
    path = _real_file(tmp_path, name)

    with pytest.raises(NotARecording):
        register_source(store, path)

    assert store.list_sources() == [], "nothing may be registered"


@pytest.mark.parametrize("name", ["demo.mp4", "demo.WEBM", "demo.Mov", "demo.mkv", "demo.avi"])
def test_a_recording_is_still_registered_whatever_the_suffix_case(
    store: ProjectStore, tmp_path: Path, name: str,
) -> None:
    """The guard must be able to say yes — including to an upper-case suffix a
    phone or screen recorder may well produce."""
    body = b"fake video bytes " + name.encode()
    source = register_source(store, _real_file(tmp_path, name, body))

    assert len(store.list_sources()) == 1
    assert source.path.endswith(name)


def test_the_refusal_never_repeats_the_submitted_name(store: ProjectStore, tmp_path: Path) -> None:
    """AT-088: a credential pasted into the path box must not come back."""
    canary = "Zq9-hunter2-canary.txt"
    with pytest.raises(NotARecording) as info:
        register_source(store, _real_file(tmp_path, canary))

    assert canary not in str(info.value)
    assert "hunter2" not in str(info.value)


# -- the UI: path form and upload ----------------------------------------------

def test_the_path_form_refuses_the_real_credential_file(
    store: ProjectStore, scratch_root: Path,
) -> None:
    """The exact live reproduction: the repo's own `.env`, which exists."""
    env = _real_file(scratch_root, ".env", b"SECRET_KEY=do-not-register\n")

    response = TestClient(app).post(
        "/projects/demo/sources", data={"path": str(env), "label": "creds"},
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html"), "a themed page"
    assert not response.text.lstrip().startswith("{"), "not the raw-JSON refusal of AT-439"
    assert "Try another path" in response.text, "a way back to the form"
    assert "not a recording" in response.text
    assert "do-not-register" not in response.text
    assert store.list_sources() == []


def test_an_upload_with_an_unknown_suffix_is_refused_and_nothing_is_written(
    store: ProjectStore, scratch_root: Path,
) -> None:
    """It used to be renamed `recording.video` and stored. Refused before any
    byte is written — the source directory must not even be created."""
    response = TestClient(app).post(
        "/projects/demo/sources/upload",
        files={"recording": ("evil.txt", b"not a video", "text/plain")}, data={"label": "x"},
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert "not a recording" in response.text
    assert store.list_sources() == []
    assert not list(scratch_root.rglob("recording.video")), "the old rename must not happen"


def test_an_upload_of_a_real_recording_suffix_is_still_stored(
    store: ProjectStore, scratch_root: Path,
) -> None:
    response = TestClient(app).post(
        "/projects/demo/sources/upload",
        files={"recording": ("walkthrough.mp4", b"fake mp4 bytes", "video/mp4")},
        data={"label": "ok"},
    )

    assert response.status_code in (200, 303)
    assert len(store.list_sources()) == 1
    assert store.list_sources()[0].path.endswith("recording.mp4")


def test_a_folder_named_like_a_recording_is_refused_as_not_a_recording(
    store: ProjectStore, tmp_path: Path,
) -> None:
    """AT-446: `dir.mp4` passes the suffix rule and `exists()`, then `file_sha256`
    raised PermissionError on Windows (IsADirectoryError elsewhere). A folder is
    not a recording; say so before touching its bytes."""
    folder = tmp_path / "dir.mp4"
    folder.mkdir()

    with pytest.raises(NotARecording) as info:
        register_source(store, folder)

    assert "dir.mp4" not in str(info.value), "AT-088: never echo the submitted name"
    assert store.list_sources() == []


def test_the_path_form_names_a_folder_as_not_a_recording(
    store: ProjectStore, scratch_root: Path,
) -> None:
    """Before AT-446 the UI said "Recording not found" about a folder that exists —
    true of nothing. It now says what the thing actually is."""
    folder = scratch_root / "dir.mp4"
    folder.mkdir()

    response = TestClient(app).post("/projects/demo/sources", data={"path": str(folder)})

    assert response.status_code == 400
    assert "folder, not a recording file" in response.text
    assert store.list_sources() == []


# -- the CLI: a refusal, not a traceback ---------------------------------------

def test_the_cli_refuses_a_folder_named_like_a_recording_with_exit_2(
    store: ProjectStore, tmp_path: Path,
) -> None:
    folder = tmp_path / "dir.mp4"
    folder.mkdir()

    result = CliRunner().invoke(cli_app, ["ingest", "register", "demo", str(folder)])

    assert result.exit_code == 2, result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert store.list_sources() == []


def test_the_cli_refuses_an_unreadable_recording_with_exit_2(
    store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The issue's second half: a recording that exists but cannot be read (locked,
    no permission) is an OSError out of `file_sha256`, and was a traceback too."""
    path = _real_file(tmp_path, "locked.mp4", b"bytes")

    def _denied(_path: Path) -> str:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("autotester.stages.ingest.file_sha256", _denied)
    result = CliRunner().invoke(cli_app, ["ingest", "register", "demo", str(path)])

    assert result.exit_code == 2, result.output
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "could not be read" in result.output
    assert store.list_sources() == []

def test_the_cli_refuses_a_non_recording_with_exit_2_not_a_traceback(
    store: ProjectStore, tmp_path: Path,
) -> None:
    """`register_source` used to raise only FileNotFoundError, which is all the
    CLI caught. The new refusal must not escape as an unhandled exception."""
    path = _real_file(tmp_path, "config.ini")

    result = CliRunner().invoke(cli_app, ["ingest", "register", "demo", str(path)])

    assert result.exit_code == 2
    assert "not a recording" in result.output
    assert not isinstance(result.exception, NotARecording), "escaped as a traceback"
    assert store.list_sources() == []
