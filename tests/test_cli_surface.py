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
  with a traceback. Cheap and broad, and **much narrower than it looks**: the
  checker measured that only **4 of 22** invocations reached application code
  at all; the other 18 stopped at click's `Usage:` banner, so the assertion was
  about click rather than about autotester (AT-180). Arity is now derived from
  click itself, which takes it to **20 of 22** — measured, not asserted.

  The remaining two, `ledger add` and `ledger weight`, stop at a **closed
  vocabulary** rejecting the placeholder, which is correct behaviour rather
  than a gap. They are deliberately not forced past it: valid arguments would
  make both commands **write**, and a write command running for real inside the
  verify step is exactly AT-181, which this same cycle exists to fix.
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


def invocation_for(command: str, root: Path | None = None) -> list[str]:
    """The command plus one placeholder per REQUIRED parameter, from click.

    AT-180: the first matrix passed `nonexistent-project nonexistent-id` to
    everything, so 18 of 22 commands got the wrong ARITY and stopped at click's
    `Usage:` banner — the assertion was about click's parser, not about
    autotester. Seeding a project did not help, because the problem was never
    state.

    Arity is a property click already knows, so it is asked rather than
    guessed. Placeholders are deliberately nonexistent: the property under test
    is still "answer a bad invocation cleanly", now from INSIDE the command."""
    root_cmd = get_command(app)
    ctx = click.Context(root_cmd)
    cmd: click.Command = root_cmd
    for part in command.split():
        cmd = cmd.get_command(ctx, part)  # type: ignore[union-attr]

    # AT-184: a placeholder is not always an INPUT. `report excel` takes an
    # output path, so a bare "nonexistent" made the matrix write a file called
    # `nonexistent` into the repo root -- AT-181's shape again, produced by
    # AT-181's own fix. Placeholders are absolute paths inside the temp root, so
    # a command that treats one as a destination cannot reach the repository.
    placeholder = str(root / "nonexistent") if root is not None else "nonexistent"

    argv = command.split()
    for param in cmd.params:
        if not param.required:
            continue
        # A positional's `opts[0]` is its NAME, not a flag. Testing
        # `isinstance(param, click.Argument)` silently failed for typer's
        # parameters, so every positional was passed as "<name> nonexistent"
        # -- doubling the arity and putting the command right back at the
        # `Usage:` banner this helper exists to get past.
        flag = param.opts[0]
        if flag.startswith("-"):
            argv += [flag, placeholder]
        else:
            argv.append(placeholder)
    return argv


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
    result = runner.invoke(app, invocation_for(command, root))

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

@pytest.mark.parametrize("command", [["doctor"], ["providers"], ["snapshot", "--print"]])
def test_the_repo_level_commands_run_without_a_project(
    root: Path, command: list[str],
) -> None:
    """These describe the REPO, not a project, so they must work in a fresh
    checkout — and `doctor` in particular is the adapter's own verify step, so
    a required argument appearing on it would break the project's own verify.

    AT-181, high, and entirely mine: the first version of this test took no
    `root` fixture, so it ran `map` and `snapshot` against the LIVE repo — and
    both WRITE. `uv run pytest`, the adapter's own verify command, was
    rewriting the git-tracked `docs/MAP.md` and `docs/SNAPSHOT.md` it verifies.
    The checker proved it by appending a marker to SNAPSHOT and watching this
    one test erase it. A verify step that mutates what it verifies is not a
    check anyone else can re-run, which is C7's whole sentence.

    So: `root` pins a temp AUTOTESTER_ROOT, `snapshot` runs with `--print`, and
    `map` is dropped — it has no read-only mode, and a test that needs one is
    not worth a rewritten repo.

    The oracle is the absence of click's `Usage:` banner, not the absence of a
    traceback: my first version asserted only "no traceback", and adding a
    required `project` argument to `doctor` came back INCONCLUSIVE under C7 —
    a missing argument is a USAGE error, which prints no traceback at all. The
    banner oracle was measured for AT-171 and covers exactly this."""
    result = runner.invoke(app, command)

    assert "Traceback" not in result.output
    assert "Usage:" not in result.output, (
        f"`autotester {' '.join(command)}` now needs an argument it did not "
        f"need before: {' '.join(result.output.split())[:140]!r}")


# -- the guarantees this file's own fixes rest on ---------------------------

def _repo_fingerprint() -> dict[str, str]:
    """Content hashes of everything a CLI command might rewrite in the repo."""
    import hashlib

    repo = Path(__file__).resolve().parents[1]
    watched = [*(repo / "docs").glob("*.md"), *(repo / "docs").glob("*.jsonl")]
    watched += [p for p in repo.iterdir() if p.is_file()]
    return {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(watched) if p.exists()}


def test_running_every_command_leaves_the_repository_untouched(root: Path) -> None:
    """AT-181 and AT-184, and both were mine.

    AT-181: the repo-level test took no `root` fixture, so it ran `map` and
    `snapshot` against the LIVE repo — and both write. `uv run pytest`, the
    adapter's own verify command, was rewriting the git-tracked `docs/MAP.md`
    and `docs/SNAPSHOT.md` it verifies. A verify step that mutates what it
    verifies is not a check anyone else can re-run, which is C7's sentence.

    AT-184 then arrived from AT-181's own fix: a placeholder is not always an
    INPUT. `report excel` takes an output PATH, so a bare "nonexistent" made
    the matrix create a file called `nonexistent` in the repo root.

    Sabotaging either came back INCONCLUSIVE until this existed — I had fixed
    both and pinned neither."""
    before = _repo_fingerprint()

    for command in shipped_commands():
        runner.invoke(app, invocation_for(command, root))
    for command in (["doctor"], ["providers"], ["snapshot", "--print"]):
        runner.invoke(app, command)

    after = _repo_fingerprint()
    changed = sorted(k for k in before if before[k] != after.get(k))
    created = sorted(set(after) - set(before))

    assert changed == [], f"running the CLI surface rewrote {changed}"
    assert created == [], f"running the CLI surface created {created} in the repo"


def test_listing_sources_for_a_project_that_does_not_exist_refuses(root: Path) -> None:
    """AT-179, a real shipped defect the matrix could not see: this printed
    "no sources yet" and exited 0 for a project that does not exist —
    indistinguishable from a real project with none. Every sibling (`explore`,
    `login`, `flowspec status`) refuses on exit 1, and a script branching on
    this one's exit code was told everything was fine.

    The matrix cannot catch it: it asserts no exit code, only the absence of a
    traceback. Some properties need a named test."""
    result = runner.invoke(app, ["ingest", "list", "nonexistent-project"])

    assert result.exit_code == 1, result.output
    assert "no project" in result.output


def test_listing_sources_for_a_real_but_empty_project_succeeds(root: Path) -> None:
    """The distinction AT-179 is about: an empty project is not an error, and a
    fix that refused both would have replaced one wrong answer with another."""
    ProjectStore("demo", root).save_project(Project(
        slug="demo", name="Demo", base_url="https://demo.test",
        allowed_domains=["demo.test"]))

    result = runner.invoke(app, ["ingest", "list", "demo"])

    assert result.exit_code == 0, result.output


def test_snapshot_print_is_what_makes_the_repo_level_test_safe() -> None:
    """AT-181's fix rests on `--print`, so that is what gets pinned.

    The fingerprint test above cannot catch this: it sets a temp root, and the
    original bug was the ABSENCE of one — so reproducing it there is impossible
    by construction, and sabotaging it came back INCONCLUSIVE.

    This runs `snapshot --print` with NO temp root, deliberately, against the
    live repo — which is safe precisely because `--print` writes nothing. If
    that ever stops being true, the verify step starts rewriting the repository
    again and this fails."""
    before = _repo_fingerprint()

    result = runner.invoke(app, ["snapshot", "--print"])

    after = _repo_fingerprint()
    assert result.exit_code == 0, result.output
    assert len(result.output) > 200, "--print must actually print the snapshot"
    assert before == after, "snapshot --print wrote to the repository"


def test_map_has_no_read_only_mode_which_is_why_it_is_excluded() -> None:
    """The other half of AT-181's fix is an EXCLUSION, and an exclusion nobody
    justifies is one somebody quietly reverses. `map` is left out of the
    repo-level test because it can only write — if it ever gains a read-only
    flag, this fails and the exclusion should be revisited rather than
    inherited."""
    result = runner.invoke(app, ["map", "--help"])

    assert "--print" not in result.output and "--dry-run" not in result.output


def test_every_placeholder_stays_inside_the_temp_root(tmp_path: Path) -> None:
    """AT-184: a placeholder is not always an input. `report excel` takes an
    output PATH, so a bare "nonexistent" made the matrix create a file called
    `nonexistent` in the repo root — AT-181's shape, produced by AT-181's own
    fix.

    Asserted on the argv rather than on the filesystem, because the filesystem
    version needs the damage to happen first."""
    for command in shipped_commands():
        argv = invocation_for(command, tmp_path)
        parts = command.split()
        for token in argv[len(parts):]:
            if token.startswith("-"):
                continue
            assert token.startswith(str(tmp_path)), (
                f"`autotester {command}` gets placeholder {token!r}, which is "
                f"outside the temp root — a command treating it as a "
                f"destination would write into the repo")
