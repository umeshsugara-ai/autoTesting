"""The mutation instrument's SANDBOX: where it runs, and what it deletes.

Split out of `test_mutation_check.py` (doctor's 300-line cap, by
responsibility): that file is about what counts as a KILL -- attribution,
anchors, red baselines, exit codes. This one is about the sandbox lifecycle,
which is the half with a destructive operation in it.

AT-325 was the leak (1824 abandoned trees). AT-329 was cleanup deleting a
sandbox-shaped path it did not own. AT-357 is the pair of assertions that were
written about the whole machine rather than about this run, so they went red
whenever a second maker loop ran a mutation check -- which, with C7 making these
runs mandatory, is the steady state.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from mutation_check import MutationError, check
from tests_mutation_fixtures import spec


@pytest.fixture
def private_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A temp root belonging to THIS test, so leak assertions are not global.

    **Requested explicitly, never autouse (AT-384).** It was autouse for one
    cycle and that silently removed an EXISTING mutation kill. `_discard`'s
    guard is `not under-temp OR wrong prefix`; moving the temp root means
    `tmp_path/"precious"` stops being under temp, the first clause
    short-circuits, and `test_cleanup_refuses_to_delete_anything_it_did_not_create`
    never reaches the PREFIX clause it is named for. Measured: the pre-change
    tree kills an edit deleting that clause, the autouse tree survives it with
    everything green. A fixture that makes a destructive operation's guard
    untestable is the exact vacuity C7 refuses — introduced by the unit that
    congratulated itself for catching vacuity elsewhere.

    Autouse was only ever load-bearing BEFORE the file split, when tests that
    did not need it shared a module with tests that did and their real-temp
    `check()` calls let a mutated glob-sweep escape. The split removed that, and
    nobody revisited the fixture. Every test in this file that calls `check()`
    requests it by name; the two cleanup-guard tests must NOT have it.

    AT-357. These tests used to diff `gettempdir().glob("mutation-check-*")`
    across the run, which is a statement about the whole machine: any OTHER
    mutation run in flight changed that set and the test failed. Two maker loops
    share this repo and C7 makes mutation runs mandatory, so concurrent runs are
    the steady state rather than a rarity — the instrument that enforces C7 went
    red precisely when C7 was being enforced somewhere else.

    Pointing `tempfile.tempdir` at a per-test directory scopes the assertion to
    this run's own sandbox. It is also STRICTER than what it replaces: the root
    starts empty, so the test asserts emptiness rather than equality with a
    `before` set that may already have held anything at all.
    """
    import tempfile

    root = tmp_path / "temp-root"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    return root


def test_the_sandbox_really_is_created_under_the_private_root(
    mutation_repo: Path, private_temp: Path
) -> None:
    """Without this, every assertion below is VACUOUS.

    `private_temp` earns its emptiness assertions only if the sandbox actually
    lands inside it. Drop the `tempfile.tempdir` redirection and the sandboxes
    go to the real temp dir instead — `private_temp` then holds nothing, the
    "is removed" tests pass because an empty directory is empty, and a genuine
    leak sails through. That is the shared-sentinel vacuity this repo has now
    been bitten by twice, so it is pinned rather than trusted.
    """
    from mutation_check import _discard, _sandbox

    _work, owned_root = _sandbox(mutation_repo)
    try:
        assert owned_root.is_relative_to(private_temp), owned_root
    finally:
        _discard(owned_root)


def test_the_sandbox_is_removed_when_the_run_finishes(
    mutation_repo: Path, private_temp: Path
) -> None:
    """AT-325. Every run copied scripts/ tests/ src/ and left them behind; 1824
    `mutation-check-*` trees had accumulated. C7 makes this instrument mandatory,
    so the leak grows with every unit."""
    check(spec(), mutation_repo)

    assert list(private_temp.iterdir()) == []


def test_the_sandbox_is_removed_even_when_the_run_is_refused(
    mutation_repo: Path, private_temp: Path
) -> None:
    """A refused run leaks just as much as a completed one — more often, since a
    bad spec is the common case while an author is writing it."""
    with pytest.raises(MutationError):
        check(spec(mutation={"kills": ["test_does_not_exist"]}), mutation_repo)

    assert list(private_temp.iterdir()) == []


def test_a_concurrent_runs_sandbox_is_left_alone(
    mutation_repo: Path, private_temp: Path
) -> None:
    """AT-357's other half, and the reason the fix is not merely "scope the test".

    Cleanup deletes only the root its own `_sandbox` call returned — it never
    sweeps by glob, because it cannot tell its own sandbox from a concurrent
    run's. Nothing pinned that. A future "tidy up the leftovers" sweep would
    look exactly like a fix for AT-325 and would delete another loop's LIVE
    sandbox mid-run: a destructive operation keyed on a path this process does
    not own, which is AT-314's shape wearing different clothes.
    """
    decoy = private_temp / "mutation-check-someone-elses-live-run"
    decoy.mkdir()
    (decoy / "repo").mkdir()

    check(spec(), mutation_repo)

    assert decoy.is_dir(), "cleanup deleted a sandbox it did not create"
    assert list(private_temp.iterdir()) == [decoy]


def test_cleanup_refuses_to_delete_anything_it_did_not_create(tmp_path: Path) -> None:
    """The first AT-325 fix deleted `work.parent`, which is only correct while
    `work` really is a sandbox. This module's own spec contains `work = repo`,
    which would have turned cleanup into "delete the real tree's parent" — a
    destructive operation keyed on an unverified path, which is AT-314 again.
    """
    from mutation_check import _discard

    victim = tmp_path / "precious"
    victim.mkdir()
    (victim / "data.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(MutationError, match="refusing to delete"):
        _discard(victim)

    assert (victim / "data.txt").read_text(encoding="utf-8") == "keep me"


def test_cleanup_refuses_a_sandbox_shaped_name_outside_the_temp_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AT-329: the guard is `not under temp OR wrong prefix`, and the sibling
    test above only exercises the PREFIX clause — it hands in a path already
    inside temp, so dropping the under-temp clause survived it.

    Reaching the other clause needs a path that is NOT under the temp dir, and
    `tmp_path` always is — which is very likely why this half went undefended.
    So the temp root is moved instead, leaving a directory whose name looks
    exactly like a sandbox sitting outside it.
    """
    import tempfile

    from mutation_check import _discard

    impostor = tmp_path / "mutation-check-not-really"
    impostor.mkdir()
    (impostor / "data.txt").write_text("keep me", encoding="utf-8")

    elsewhere = tmp_path / "a-different-temp-root"
    elsewhere.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(elsewhere))

    with pytest.raises(MutationError, match="refusing to delete"):
        _discard(impostor)

    assert (impostor / "data.txt").read_text(encoding="utf-8") == "keep me"


# -- AT-490/491: the tree kill is itself bounded, and its POSIX arm is pinned ---

class _FakeProc:
    """A process handle whose wait either returns or never does."""

    def __init__(self, exits: bool) -> None:
        self.pid, self.exits, self.waited_with = 4242, exits, []

    def wait(self, timeout=None):
        self.waited_with.append(timeout)
        if not self.exits:
            raise subprocess.TimeoutExpired("pytest", timeout)
        return -9


def test_a_process_that_survives_the_tree_kill_is_refused_not_awaited_forever(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-490: the wait after the kill had no bound, so a kill the OS did not carry out
    reproduced AT-487's hang one level down."""
    import mutation_check

    monkeypatch.setattr(mutation_check.subprocess, "run", lambda *a, **k: None)
    proc = _FakeProc(exits=False)

    with pytest.raises(MutationError, match="survived"):
        mutation_check._kill_tree(proc, posix=False)

    assert proc.waited_with and proc.waited_with[-1] is not None


def test_the_posix_arm_kills_the_whole_session_and_tolerates_a_group_already_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-491, and the review's race: the group can exit between the timeout and the
    kill, and `os.killpg` then raises ProcessLookupError."""
    import types

    import mutation_check

    calls = []

    def killpg(pid, sig):
        calls.append((pid, sig))
        raise ProcessLookupError

    monkeypatch.setattr(mutation_check.os, "killpg", killpg, raising=False)
    monkeypatch.setattr(mutation_check, "signal", types.SimpleNamespace(SIGKILL=9))
    proc = _FakeProc(exits=True)

    mutation_check._kill_tree(proc, posix=True)

    assert calls == [(4242, 9)]
    assert proc.waited_with and proc.waited_with[-1] is not None


def test_non_ascii_pytest_output_survives_the_log_round_trip(
    mutation_repo: Path, private_temp: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The log is a file, so the child's stdout encoding is the locale's unless forced;
    the refusal must quote what pytest printed, not replacement characters. The variable
    is cleared first: under a mutation run it is inherited from the outer instrument,
    which would pass this test with the fix removed."""
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    text = "caf" + chr(0xE9) + " " + chr(0x2713)
    (mutation_repo / "tests" / "test_uni.py").write_text(chr(10).join([
        "def test_uni():", "    print('caf' + chr(0xE9) + ' ' + chr(0x2713))", "    assert False",
        ""]), encoding="utf-8")

    with pytest.raises(MutationError) as refused:
        check(spec(tests=["tests/test_mod.py", "tests/test_uni.py"]), mutation_repo)

    assert text in str(refused.value)
