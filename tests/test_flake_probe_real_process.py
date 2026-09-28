"""Whether `run_once`'s kill is real, not argued.

Split from `test_flake_probe_runner.py` at the 300-line cap (C2), along the seam
AT-495 names: every test in that file stubs `subprocess.Popen`, so `run_once`'s
real `kill_tree` call (`scripts/flake_probe.py:179`) has never run against an
actual hung OS process, still less one with a real grandchild holding the log
file's inherited handle open — the exact shape `run_once`'s own docstring argues
against, by analogy to `mutation_check`'s AT-487 evidence, without ever measuring
it here. Both tests below use the real subprocess machinery; nothing here is a
fake. `test_mutation_check_judgement.py::test_a_hung_baseline_is_refused_even_
when_a_child_holds_the_output_open` is the direct precedent for the first test,
including its two helpers, imported rather than redefined (one concept, one
place — C3), and `test_flake_probe_runner.py`'s own `_FakePopen` is imported for
the second, which is a control-flow test and needs no real process at all.
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import flake_probe
from test_flake_probe_runner import _FakePopen
from test_mutation_check_judgement import _alive, _within

REPO = Path(__file__).resolve().parents[1]

# AT-700: the bound must exceed the MEASURED cost of the nested pytest reaching the
# grandchild's `Popen`, or this test cannot reach its own subject. Keeping the scenario
# file inside the repo (see `scenario_dir`) puts that cost at 0.64s to collect and
# 1.31-2.55s to run, so 20s is roughly an 8x margin. The first test's docstring has the
# measurements and why BOTH halves of the fix are needed.
BOUND_S = 20


@pytest.fixture
def scenario_dir() -> Iterator[Path]:
    """A scratch dir for the nested run's test file that is INSIDE the repo tree.

    AT-700: `tmp_path` cannot be used for that file, and the reason is the whole
    defect. pytest builds a `Dir` node for every directory from the filesystem root
    down to each argument, so an argument under the system temp dir makes the nested
    run walk the whole chain down to AppData/Local/Temp -- 14,645 entries on this
    machine -- before it collects anything. Measured `--collect-only` on ONE no-op
    test: 19.68s from temp against 0.64s from inside the repo. Nothing here is
    gitignore-visible to the outer run: the file is named `hang_case.py`, not
    `test_*.py`, so the outer session never collects it, and it is removed after.
    """
    path = REPO / ".work" / f"at700-scenario-{os.getpid()}"
    path.mkdir(parents=True, exist_ok=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_run_once_kills_a_real_hung_process_and_its_real_grandchild(
    tmp_path: Path, scenario_dir: Path,
) -> None:
    """The kill AT-494 added has never been proven against reality: every stub above
    raises `TimeoutExpired` synchronously and never spawns anything of its own. This
    spawns a REAL `python -m pytest` process whose one test starts its own child
    holding the log file's inherited handle open — the grandchild `run_once`'s
    docstring worries about — times it out at a real bound, and asserts that
    child is DEAD afterward, not merely that `run_once` returned. An earlier version
    of the sibling test in `mutation_check` asserted only the latter, and a mutation
    removing the tree kill survived it; that is the shape being guarded against
    here too.

    AT-700: the bound used to be 10s, which sat BELOW this scenario's floor cost, so
    the test was a coin flip that could not catch the mutation it exists for. The
    grandchild is spawned only if the nested pytest finishes starting before the
    bound fires; if it does not, `child.pid` is never written and the run dies on a
    `FileNotFoundError` reading it -- the SAME red a build with the tree kill removed
    entirely would produce, because in that build the grandchild never starts either.
    Setup failure and subject failure were indistinguishable, which is exactly what
    the paragraph above claims this test prevents.

    Measured on two machines, not assumed. Nested `python -m pytest` on ONE no-op
    test, same argv `run_once` builds: 9.28 / 7.26 / 7.95 / 8.47s here and 11.59 /
    9.76 / 10.32 / 9.57s on the peer session's box -- against the old 10s bound. The
    cost is not the 600s sleep and not machine load; it is startup, and it appears
    only when the test file lives OUTSIDE the repo as `tmp_path` does. The identical
    no-op INSIDE the repo runs in 1.31-2.55s, and pytest's own clock reports 7.70s
    against 0.36s for the two cases, so the floor is a property of this fixture's
    shape rather than of the machine.

    Two changes below, and BOTH are needed. A bigger bound alone leaves the
    conflation in place for a slower machine; separating the missing-file branch
    alone would turn the red into a permanent skip -- silencing with extra steps."""
    pid_file = tmp_path / "child.pid"
    child = (f"import os, pathlib, time; pathlib.Path({str(pid_file)!r})"
             ".write_text(str(os.getpid())); time.sleep(600)")
    test_file = scenario_dir / "hang_case.py"
    test_file.write_text(
        chr(10).join(["import subprocess, sys, time", "", "",
                      "def test_hang():",
                      f"    subprocess.Popen([sys.executable, '-c', {child!r}])",
                      "    time.sleep(600)", ""]),
        encoding="utf-8")

    run, elapsed = _within(
        120, lambda: flake_probe.run_once(f"{test_file}::test_hang", 1, timeout=BOUND_S))

    assert run.timed_out is True
    assert run.returncode == flake_probe.TIMED_OUT
    assert elapsed < 120, f"the {BOUND_S}s bound must bound the call, not just the child"
    # The SETUP branch, kept separate from the subject below on purpose (AT-700): a
    # missing pid file means the grandchild never STARTED, so this run measured
    # nothing about the kill. It is reported as its own failure naming the floor --
    # never folded into the kill assertion, and never skipped, because a skip here is
    # the silence that was the bug.
    if not pid_file.exists():
        pytest.fail(
            f"scenario never started: the nested pytest did not spawn its grandchild "
            f"within the {BOUND_S}s bound, so `child.pid` was never written. This says "
            f"NOTHING about run_once's tree kill, passing or broken. The measured "
            f"startup floor for this fixture shape was 7.3-11.6s across two machines; "
            f"if it has grown past {BOUND_S}s, raise BOUND_S -- do not skip or delete.")
    assert not _alive(int(pid_file.read_text())), (
        "run_once killed pytest but left its real grandchild running")


def test_a_tree_that_outlives_its_kill_is_recorded_timed_out_with_the_error_in_the_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The second half of AT-495: `run_once` catches `RuntimeError` from `kill_tree`
    (the tree outlived the kill) instead of letting it escape, but nothing asserted
    what happens to the run it was supervising. Undisclosed here would mean a
    genuinely un-killable browser reads as an ordinary red run rather than the
    operational emergency it actually is. A control-flow test, not a real-process
    one — `kill_tree`'s own raising behaviour is `mutation_check`'s to prove
    (`test_mutation_sandbox.py::test_a_process_that_survives_the_tree_kill_is_
    refused_not_awaited_forever`); this only proves `run_once` reacts to it
    correctly."""
    monkeypatch.setattr(flake_probe.subprocess, "Popen", _FakePopen(hangs=True, output="x"))

    def _unkillable(proc: object, *a: object, **k: object) -> None:
        raise RuntimeError(
            f"pytest (pid {proc.pid}) survived a kill of its process tree for 30s")

    monkeypatch.setattr(flake_probe, "kill_tree", _unkillable)

    run = flake_probe.run_once("tests/test_x.py::test_y", 4, timeout=9)

    assert run.timed_out is True, "an unkillable tree is still a timeout, not a lost run"
    assert run.returncode == flake_probe.TIMED_OUT
    assert "survived a kill of its process tree" in run.tail
