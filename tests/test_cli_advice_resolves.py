"""Every command this codebase tells an operator to run must actually exist.

AT-163 → AT-172 → AT-176. Three fix cycles of T-132 went on one message naming
`autotester media prep`, a command the CLI does not expose. Then the same dead
end appeared one command over (`ingest analyze`). Then — after this guard was
built to end the class — a checker pointed `PREP_COMMAND` back at the dead name
and **this test returned zero failures**, because the backtick and the command
name lived in different AST nodes.

So the collector no longer scans string literals. `tests/advice_scan.py` renders
each string the way Python will, substituting module constants, and reads
commands out of the result whether or not they are backticked. That took the
visible surface from 5 sites to 9 — including `ingest prep`, the message the
whole class exists for, which the literal scanner could not see.

Two oracles, because they answer different questions:

* **does it resolve** — registered, and takes the arity implied.
* **does it work** — the causal one: trigger the refusal, run the command it
  names, assert the refusal stops firing. That was designed by a checker after
  I argued no such oracle could exist without encoding the answer in the test
  (AT-174). I was wrong; my premise held only for *static* oracles.

Contract: qa/contracts/video-learning.md VL1d, generalised.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
from advice_scan import advice_in_source
from typer.testing import CliRunner

from autotester.cli import app
from autotester.schema.enums import SourceKind
from autotester.schema.project import Project, Source
from autotester.stages import media_prep
from autotester.store.project_store import ProjectStore

SRC = Path(__file__).resolve().parents[1] / "src" / "autotester"
runner = CliRunner()


def advice() -> list[tuple[Path, str]]:
    return advice_in_source(SRC)


def _unprepared_source(tmp_path: Path) -> tuple[ProjectStore, Source]:
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    video = tmp_path / "erp1.mp4"
    video.write_bytes(b"fake-mp4")
    source = store.add_source(Source(project="demo", kind=SourceKind.VIDEO,
                                     path=str(video), sha256="deadbeef"))
    return store, source


def test_the_collector_sees_the_site_the_class_exists_for() -> None:
    """AT-176 in one assertion. `ingest prep` is built from a module constant
    interpolated into an f-string, so the literal scanner missed it — and it is
    precisely the message three fix cycles were spent on."""
    commands = {c for _, c in advice()}

    assert "ingest prep" in commands
    assert len(commands) >= 6, commands


@pytest.mark.parametrize("where,command", advice(),
                         ids=lambda v: str(v).replace("/", "_").replace("\\", "_"))
def test_every_command_the_code_names_is_one_the_cli_exposes(
    where: Path, command: str,
) -> None:
    """click prints its `Usage:` banner for an unregistered command, an
    unregistered subcommand and the wrong arity alike, so its absence is one
    oracle covering all three. Measured, not assumed (AT-171)."""
    result = runner.invoke(app, [*shlex.split(command), "--help"])

    assert "Usage:" not in result.output or "--help" in result.output, (
        f"{where} tells an operator to run `autotester {command}`, "
        f"which the CLI does not expose: {' '.join(result.output.split())[:140]!r}")
    assert "No such command" not in result.output, (
        f"{where} names a command that does not exist: `autotester {command}`")


def test_the_refusal_names_a_command_that_actually_stops_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-174 — the causal oracle, and it is a checker's design, not mine.

    I argued no oracle could tell a correct command from a plausible sibling
    without encoding the answer in the test. True of *static* oracles only.
    This tests the message's PROMISE: it says "run X and this stops", so run X
    and check that it stops."""
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    store, source = _unprepared_source(tmp_path)
    monkeypatch.setattr(media_prep.probe_mod, "ffmpeg_available", lambda: False)

    with pytest.raises(media_prep.SourceNotPrepared) as caught:
        media_prep.require_prepared(store, source.id)
    message = str(caught.value)
    assert "`" in message, f"the refusal named no command: {message}"

    named = message.split("`")[1]
    argv = shlex.split(named)[1:]          # drop the leading "autotester"
    result = runner.invoke(app, argv)

    assert result.exit_code == 0, f"the command the refusal named failed: {result.output}"
    media_prep.require_prepared(store, source.id)   # must no longer raise


def test_a_sibling_command_would_not_satisfy_that_promise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The half that proves the oracle discriminates. `ingest frames` is
    registered and takes the same two arguments, so every static check passes
    it — and it leaves the refusal firing, which is the whole point."""
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    store, source = _unprepared_source(tmp_path)

    runner.invoke(app, ["ingest", "frames", "demo", source.id])

    with pytest.raises(media_prep.SourceNotPrepared):
        media_prep.require_prepared(store, source.id)
