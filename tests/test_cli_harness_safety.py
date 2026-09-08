"""The test harness must not damage the repository it tests — AT-181 / AT-184.

Split from `test_cli_surface.py` at doctor's 300-line cap, by responsibility:
that file is about what the COMMANDS do, this one about what running them all
must never do.

The split earns itself. AT-181 was `uv run pytest` — this project's own verify
command — rewriting the git-tracked `docs/MAP.md` and `docs/SNAPSHOT.md` it
verifies, because the repo-level test took no temp root and `map`/`snapshot`
both write. AT-184 then arrived *from that fix*: a placeholder is not always an
input, so `report excel` created a file called `nonexistent` in the repo root.

Both were mine, and both are about the harness rather than the product.
Contract: `core-invariants.md` C4 (scratch belongs in `.work/`) and C7 (a check
someone else can re-run).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from test_cli_surface import invocation_for, shipped_commands
from typer.testing import CliRunner

from autotester.cli import app

runner = CliRunner()


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


def _repo_fingerprint() -> dict[str, str]:
    """Content hashes of everything a CLI command might rewrite in the repo."""

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
