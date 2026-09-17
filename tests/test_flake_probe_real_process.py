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

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import flake_probe
from test_flake_probe_runner import _FakePopen
from test_mutation_check_judgement import _alive, _within


def test_run_once_kills_a_real_hung_process_and_its_real_grandchild(
    tmp_path: Path,
) -> None:
    """The kill AT-494 added has never been proven against reality: every stub above
    raises `TimeoutExpired` synchronously and never spawns anything of its own. This
    spawns a REAL `python -m pytest` process whose one test starts its own child
    holding the log file's inherited handle open — the grandchild `run_once`'s
    docstring worries about — times it out at a real 10s bound, and asserts that
    child is DEAD afterward, not merely that `run_once` returned. An earlier version
    of the sibling test in `mutation_check` asserted only the latter, and a mutation
    removing the tree kill survived it; that is the shape being guarded against
    here too."""
    pid_file = tmp_path / "child.pid"
    child = (f"import os, pathlib, time; pathlib.Path({str(pid_file)!r})"
             ".write_text(str(os.getpid())); time.sleep(600)")
    test_file = tmp_path / "test_hang.py"
    test_file.write_text(
        chr(10).join(["import subprocess, sys, time", "", "",
                      "def test_hang():",
                      f"    subprocess.Popen([sys.executable, '-c', {child!r}])",
                      "    time.sleep(600)", ""]),
        encoding="utf-8")

    run, elapsed = _within(
        60, lambda: flake_probe.run_once(f"{test_file}::test_hang", 1, timeout=10))

    assert run.timed_out is True
    assert run.returncode == flake_probe.TIMED_OUT
    assert elapsed < 60, "the 10s bound must actually bound the call, not just the child"
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
