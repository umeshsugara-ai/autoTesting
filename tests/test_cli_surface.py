"""Every shipped command, driven — AT-177.

The sweep measured what AT-140 actually left behind: **15 of 22 shipped
commands had no test driving them**, including `flowspec approve` — the human
review gate I6 exists to protect — and all three `report` commands, which are
the exact reader surfaces AT-120 through AT-123 were filed against.

AT-140 closed the gap for `explore` and `approve`. This closes the rest, and
the argument is the same one that unit made: a test that calls a function
proves the function works; only a test that runs the command proves the product
does. Nine of this session's findings were that distinction.

Two layers here:

* a **smoke matrix** over all 22 commands — none may answer a wrong invocation
  with a traceback. Cheap and broad, and **narrower than it looks**: see below.
* **focused tests** on the surfaces that carry a decision: the review gate, and
  the three reports.
"""

from __future__ import annotations

from pathlib import Path

import click
import pytest
from typer.main import get_command
from typer.testing import CliRunner

from autotester.cli import app
from autotester.schema.enums import ReviewStatus
from autotester.schema.flowspec import FlowSpec, Review, Screen
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore

runner = CliRunner()


def shipped_commands() -> list[str]:
    """Walk click's own tree — so a command added tomorrow is covered without
    anyone remembering to add it here. A hand-written list would drift out of
    date silently, which is the failure this file is about."""
    root = get_command(app)
    ctx = click.Context(root)

    def walk(cmd: click.Command, prefix: tuple[str, ...] = ()) -> list[str]:
        subs = getattr(cmd, "commands", None)
        if subs is None and hasattr(cmd, "list_commands"):
            subs = {n: cmd.get_command(ctx, n) for n in cmd.list_commands(ctx)}
        if subs:
            out: list[str] = []
            for name, sub in sorted(subs.items()):
                out += walk(sub, (*prefix, name))
            return out
        return [" ".join(prefix)]

    return walk(root)


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


def test_the_walker_finds_the_whole_surface() -> None:
    """A walker that silently found nothing would make the matrix below
    vacuously green — the exact shape this session kept producing."""
    commands = shipped_commands()

    assert len(commands) >= 20, commands
    for expected in ("flowspec approve", "report excel", "ledger add", "doctor"):
        assert expected in commands


@pytest.mark.parametrize("command", shipped_commands())
def test_no_command_answers_a_bad_invocation_with_a_traceback(
    root: Path, command: str,
) -> None:
    """No command may answer a bad invocation with a traceback. All 22 at once.

    `--help` is not enough (AT-171: it proves registration, not behaviour), so
    each command is invoked against an EMPTY root — every project, source and
    artifact it might name is absent. Any exit code is fine; a traceback is
    not. An unhandled exception reaching an operator is never the right answer
    to "that does not exist".

    **What this does NOT cover, measured rather than assumed.** I first wrote
    that this "is the layer that would have caught AT-166". It is not, and
    sabotaging AT-166 back in proved it: with nonexistent arguments every
    command short-circuits in ARGUMENT VALIDATION, long before the stage where
    that bug lived, so the sabotage came back INCONCLUSIVE under C7.

    So this matrix guards the shallow path across the whole surface, and the
    deep paths are guarded one at a time by the targeted tests
    (`test_media_prep.py::test_the_shipped_prep_command_answers_a_refusal_cleanly`
    is the one that actually catches AT-166). Writing the claim before checking
    it is the exact habit this session keeps finding; it is corrected here
    rather than left as a comfortable sentence."""
    result = runner.invoke(app, [*command.split(), "nonexistent-project", "nonexistent-id"])

    assert "Traceback" not in result.output, (
        f"`autotester {command}` answered a bad invocation with a traceback:\n"
        f"{result.output[-600:]}")


# -- the review gate: the one command that changes what may be trusted -------

def _project(root: Path, *, status: ReviewStatus = ReviewStatus.DRAFT) -> ProjectStore:
    store = ProjectStore("demo", root)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    store.save_flowspec(FlowSpec(project="demo", review=Review(status=status),
                                 screens=[Screen(id="scr_1", name="Home")]))
    return store


def test_flowspec_approve_records_who_approved_it(root: Path) -> None:
    """I6's gate. `expand` refuses an unreviewed spec, so this command is what
    decides whether generated cases may exist at all — and it had no test."""
    store = _project(root)

    result = runner.invoke(app, ["flowspec", "approve", "demo", "--by", "umesh"])

    assert result.exit_code == 0, result.output
    saved = store.load_flowspec()
    assert saved is not None
    assert saved.review.status is ReviewStatus.APPROVED
    assert saved.review.by == "umesh"


def test_flowspec_approve_needs_a_name(root: Path) -> None:
    """An approval nobody signed is not an approval. `--by` is the whole point
    of the record."""
    _project(root)

    result = runner.invoke(app, ["flowspec", "approve", "demo"])

    assert result.exit_code != 0
    assert "Traceback" not in result.output


def test_flowspec_request_edit_takes_approval_back(root: Path) -> None:
    """The gate has to swing both ways, or a spec approved by mistake is
    approved forever.

    `--by` is required here as well as on approve, which is right: taking an
    approval back is also a decision someone made. My first version of this
    test omitted it and failed — my bug, and the command's design was the
    thing that was correct."""
    store = _project(root, status=ReviewStatus.APPROVED)

    result = runner.invoke(app, ["flowspec", "request-edit", "demo",
                                 "--by", "umesh", "--note", "wrong screen"])

    assert result.exit_code == 0, result.output
    saved = store.load_flowspec()
    assert saved is not None
    assert saved.review.status is not ReviewStatus.APPROVED


def test_flowspec_status_on_an_unknown_project_is_clean(root: Path) -> None:
    result = runner.invoke(app, ["flowspec", "status", "nope"])

    assert "Traceback" not in result.output


# -- the reader surfaces AT-120..AT-123 were filed against -------------------

@pytest.mark.parametrize("report", ["excel", "html", "crawl"])
def test_a_report_for_something_that_does_not_exist_refuses_cleanly(
    root: Path, report: str,
) -> None:
    """All three `report` commands were untested, and every count-honesty
    finding this session (AT-120, AT-121, AT-122, AT-123) was about exactly
    what a report tells its reader."""
    result = runner.invoke(app, ["report", report, "demo", "run_nope"])

    assert result.exit_code != 0
    assert "Traceback" not in result.output


# -- the read-only commands, which must never need a project ----------------

@pytest.mark.parametrize("command", ["doctor", "providers", "map", "snapshot"])
def test_the_repo_level_commands_run_without_a_project(command: str) -> None:
    """These describe the REPO, not a project, so they must work in a fresh
    checkout — and `doctor` in particular is the adapter's own verify step, so
    a required argument appearing on it would break the project's own verify.

    The oracle is the absence of click's `Usage:` banner, not the absence of a
    traceback: my first version asserted only "no traceback", and adding a
    required `project` argument to `doctor` came back INCONCLUSIVE under C7 —
    a missing argument is a USAGE error, which prints no traceback at all. The
    banner oracle was measured for AT-171 and covers exactly this."""
    result = runner.invoke(app, [command])

    assert "Traceback" not in result.output
    assert "Usage:" not in result.output, (
        f"`autotester {command}` now needs an argument it did not need before: "
        f"{' '.join(result.output.split())[:140]!r}")
