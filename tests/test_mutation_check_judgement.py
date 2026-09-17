"""How the mutation instrument JUDGES a run — the kill decision and its report.

Split from `test_mutation_check.py` at the 300-line cap (C2). That file owns
what the instrument REFUSES (an invalid run); this one owns what it CONCLUDES
from a valid one.

Both halves exist because the instrument shipped with the defects it was written
to catch: an unattributed kill (AT-313), a sandbox promise that was only a
docstring (AT-314), a vacuous test inside the vacuous-test detector (AT-315), a
bare test name mistaken for an identifier (AT-320), and a false "pytest ran
nothing" about a run that produced results (AT-322).
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from mutation_check import MutationError, check, is_kill, report
from tests_mutation_fixtures import spec

# -- AT-315: the kill DECISION, asserted head-on rather than inferred ---------
#
# A mutation cannot prove the exit-code clause: a collection error produces no
# FAILED lines, so `expected <= failures` fails too and a weakened
# `exit_code != 0` survives every mutation. That is how a vacuous test got into
# the instrument built to catch vacuous tests. So the decision is a pure
# function and these assert it directly.

def test_is_kill_requires_pytest_to_have_actually_run_tests() -> None:
    """Exit 1 means tests ran and some failed. Every OTHER non-zero code means
    no test result was produced at all — a collection error exits 4, an internal
    error 3 — and counting those as kills is AT-311."""
    named = {"test_thing"}

    assert is_kill(1, named, named) is True
    assert is_kill(4, named, named) is False, "a collection error is not a kill"
    assert is_kill(3, named, named) is False, "an internal error is not a kill"
    assert is_kill(2, named, named) is False
    assert is_kill(0, named, named) is False, "a green run cannot be a kill"


def test_is_kill_requires_every_named_test_to_have_failed() -> None:
    """A red suite is not evidence that THIS test noticed."""
    assert is_kill(1, {"a", "b"}, {"a"}) is False
    assert is_kill(1, {"a", "b"}, {"a", "b"}) is True
    assert is_kill(1, {"a"}, {"a", "unrelated"}) is True


def test_is_kill_refuses_a_claim_no_test_makes() -> None:
    """AT-313. An empty `kills` collapsed the verdict to "some test failed,
    attributed to nothing" — verbatim the defect this instrument refuses."""
    with pytest.raises(MutationError, match="claimed by no test"):
        is_kill(1, set(), {"whatever"})


def test_it_refuses_a_mutation_whose_kills_list_is_empty(mutation_repo: Path) -> None:
    """AT-313 through the front door: it refused a `kills` NAME that did not
    exist, while accepting no name at all."""
    with pytest.raises(MutationError, match="names no test"):
        check(spec(mutation={"kills": []}), mutation_repo)


# -- AT-314: the sandbox promise, enforced rather than documented -------------

def test_it_refuses_a_file_that_escapes_the_sandbox_by_climbing(mutation_repo: Path) -> None:
    with pytest.raises(MutationError, match="outside the sandbox"):
        check(spec(mutation={"file": "../../../etc/passwd"}), mutation_repo)


def test_it_refuses_an_absolute_file_path(mutation_repo: Path, tmp_path: Path) -> None:
    """`work / mutation["file"]` DISCARDS the sandbox for an absolute right
    operand, so the docstring's "can never touch the live tree" was a promise
    the code did not keep."""
    decoy = tmp_path / "decoy.py"
    decoy.write_text("if value > 10:\n", encoding="utf-8")

    with pytest.raises(MutationError, match="outside the sandbox"):
        check(spec(mutation={"file": str(decoy)}), mutation_repo)

    assert decoy.read_text(encoding="utf-8") == "if value > 10:\n", "the decoy was mutated"

# -- AT-321: the "unreachable clause" claim was FALSE -------------------------


def test_an_interrupted_run_with_real_failures_is_not_a_kill(mutation_repo: Path) -> None:
    """The mutation cycle 2 said could not exist.

    Cycle 2 argued that no mutation could reach `exit_code == 1`, because every
    non-1 non-zero exit is a collection error yielding no FAILED lines. That is
    false: **pytest exit 2 is INTERRUPTED**, and it prints the FAILED lines of
    tests that already failed. So this run separates the two clauses — a
    weakened `exit_code != 0` calls it killed, the correct `== 1` does not.

    Kept beside the direct `is_kill` table because the claim it refutes was
    mine, and it was the second unreachability claim I made that fell to one
    attempt. "I could not think of a mutation" is not "no mutation exists".
    """
    # The anchor `if value > 10:` leaves the existing 4-space indent in place, so
    # the first line must NOT be indented again. Getting this wrong produced a
    # SyntaxError, i.e. exit 2 for the WRONG reason — a collection error rather
    # than an interrupt. That is the very confusion AT-322 is about, and it is
    # why the assertions below pin the reason and not just the code.
    interrupting = (
        "if value == 999:" + chr(10)
        + "        raise KeyboardInterrupt" + chr(10)
        + "    if value > 0:")

    result = check(spec(mutation={
        "new": interrupting,
        "kills": ["test_small_values_are_small"]}), mutation_repo)[0]

    assert result["exit"] == 2, "precondition: the run was INTERRUPTED, not a collection error"
    assert result["failed"] == ["tests/test_mod.py::test_small_values_are_small"], (
        "an interrupted run still reports the tests that really failed")
    assert result["killed"] is False, "exit 2 is not 'pytest ran the tests and some failed'"
    assert result["no_test_results"] is False, (
        "AT-322: tests DID produce results here — reporting 'ran nothing' would be a lie")


# -- AT-320: a bare name is not an identifier --------------------------------


def test_it_refuses_a_kills_name_that_collects_more_than_once(mutation_repo: Path) -> None:
    """A same-named test in another file satisfied attribution, so a mutation
    could be reported killed by a module it never touched — verbatim AT-311's
    second failure mode, inside the fix for AT-311."""
    other = mutation_repo / "tests" / "test_elsewhere.py"
    other.write_text(
        "def test_small_values_are_small():" + chr(10) + "    assert True" + chr(10),
        encoding="utf-8")

    with pytest.raises(MutationError, match="collect more than once"):
        check(spec(tests="tests/"), mutation_repo)


# -- AT-323: a survivor is INCONCLUSIVE, not proven vacuous ------------------


def test_a_survivor_is_reported_as_inconclusive_not_as_vacuous(capsys) -> None:
    """C7's zero-failure clause forbids the stronger word on this evidence: a
    mutation that changed no observable behaviour proves nothing about the test.
    The report used to print "vacuous for its property" for every survivor."""
    report([{"name": "m", "killed": False, "exit": 0,
             "expected": ["tests/t.py::test_a"], "failed": [], "survivors": ["tests/t.py::test_a"],
             "no_test_results": False}])

    out = capsys.readouterr().out
    assert "INCONCLUSIVE" in out
    assert "vacuous" not in out.lower()


def test_a_run_that_produced_no_results_says_so(capsys) -> None:
    report([{"name": "m", "killed": False, "exit": 4,
             "expected": ["tests/t.py::test_a"], "failed": [], "survivors": ["tests/t.py::test_a"],
             "no_test_results": True}])

    assert "produced no test results" in capsys.readouterr().out


# -- AT-487: a hung pytest is bounded, and a hang is never a kill --------------

def _within(seconds: float, fn):
    """Run `fn` on a daemon thread, so a regression that hangs fails THIS test in
    bounded time instead of wedging the whole suite."""
    box: dict = {}

    def run() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:  # re-raised on the test's own thread below
            box["error"] = exc

    worker = threading.Thread(target=run, daemon=True)
    started = time.monotonic()
    worker.start()
    worker.join(seconds)
    assert not worker.is_alive(), f"still running after {seconds}s: the pytest run is unbounded"
    if "error" in box:
        raise box["error"]
    return box["value"], time.monotonic() - started


def test_a_mutation_that_hangs_pytest_times_out_and_is_not_a_kill(mutation_repo: Path) -> None:
    """A mutation can introduce an infinite loop. It used to hang the run forever."""
    hang = {"old": "if value > 10:",
            "new": "while value > 0:" + chr(10) + "        pass" + chr(10) + "    if value > 10:"}

    results, _ = _within(120, lambda: check(spec(timeout_s=20, mutation=hang), mutation_repo))

    assert results[0]["killed"] is False, results
    assert results[0]["timed_out"] is True, results


def test_a_hung_baseline_is_refused_even_when_a_child_holds_the_output_open(
    mutation_repo: Path,
) -> None:
    """A test that starts a long-lived child keeps pytest's output handle open, so
    killing pytest alone still leaves a reader waiting for that handle to close, and
    leaves the child running after the sandbox it lives in is gone."""
    pid_file = mutation_repo.parent / "child.pid"
    child = (f"import os, pathlib, time; pathlib.Path({str(pid_file)!r})"
             ".write_text(str(os.getpid())); time.sleep(600)")
    (mutation_repo / "tests" / "test_hang.py").write_text(
        chr(10).join(["import subprocess, sys, time", "", "", "def test_hang():",
                      f"    subprocess.Popen([sys.executable, '-c', {child!r}])",
                      "    time.sleep(600)", ""]), encoding="utf-8")
    run = spec(tests=["tests/test_mod.py", "tests/test_hang.py"], timeout_s=15)

    with pytest.raises(MutationError, match="did not finish within 15s"):
        _within(120, lambda: check(run, mutation_repo))

    assert not _alive(int(pid_file.read_text())), "the timeout killed pytest but not its child"


def _alive(pid: int) -> bool:
    if sys.platform == "win32":
        listed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                capture_output=True, text=True, check=False).stdout
        return str(pid) in listed.split()
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@pytest.mark.parametrize("bad", [0, -5, "60", True, None])
def test_it_refuses_a_timeout_that_is_not_a_positive_number(mutation_repo: Path, bad) -> None:
    with pytest.raises(MutationError, match="'timeout_s' must be a positive number"):
        check(spec(timeout_s=bad), mutation_repo)
