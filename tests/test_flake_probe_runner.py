"""How the flake probe RUNS, and whether its own claims are honest.

Split from `test_flake_probe.py` (doctor's 300-line rule) along the seam the file
already had: that file is the arithmetic — what a bound means, what N clean runs
prove. This one is the runner — `run_once` and `probe`, the subprocess halves the
41-run AT-335 headline rests on (AT-386) — plus the guard on the prose that
justifies them (AT-396/405/406), which belongs here because it pins the reasons
recorded beside those same flags.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import flake_probe

# -- the subprocess halves: AT-386 ---------------------------------------------
# The 41-run headline rests entirely on run_once's returncode->failed mapping, and
# nothing tested it. If that mapping broke, 41 undetected failures would read as 41
# green runs and every statistic above would be computed from a lie. The debt was
# enumerated honestly but the stated reason was wrong: this needs no pytest inside
# pytest, only a monkeypatched `subprocess.run`.


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def test_a_nonzero_return_code_is_what_makes_a_run_count_as_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The single mapping the whole measurement stands on."""
    monkeypatch.setattr(flake_probe.subprocess, "run",
                        lambda *a, **k: _FakeCompleted(1, stdout="E   assert 1 == 2\n"))

    run = flake_probe.run_once("tests/test_x.py::test_y", 7)

    assert run.failed is True
    assert run.index == 7
    assert "assert 1 == 2" in run.tail, "the rare failure's output is the whole prize"


def test_a_clean_run_keeps_no_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """41 green runs would otherwise carry 41 copies of pytest's chatter into the
    report, burying the one failing tail somebody actually needs to read."""
    monkeypatch.setattr(flake_probe.subprocess, "run",
                        lambda *a, **k: _FakeCompleted(0, stdout="." * 5000))

    run = flake_probe.run_once("tests/test_x.py::test_y", 1)

    assert run.failed is False
    assert run.tail == ""


def test_a_failure_tail_is_bounded_rather_than_the_whole_log(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    long_log = "\n".join(str(i) for i in range(500))
    monkeypatch.setattr(flake_probe.subprocess, "run",
                        lambda *a, **k: _FakeCompleted(1, stdout=long_log))

    run = flake_probe.run_once("t", 1)

    assert len(run.tail.splitlines()) == 25
    assert run.tail.splitlines()[-1] == "499", "the END of the log, where the failure is"


def test_each_run_is_isolated_from_the_ones_before_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both flags are pinned because both are deliberate, and for DIFFERENT reasons.

    `-o addopts=` neutralises `pyproject.toml:62`'s `addopts = "-q"`, which would
    otherwise combine with our own `-q` to make every invocation `-qq`. I nearly
    shipped "without it the failing output is suppressed" as the reason — while
    fixing an over-claim — and measured it instead: the traceback is captured
    either way, and the whole difference is ONE line (`1 failed in Xs`), 11 lines
    against 12. Worth pinning as a deliberate choice; not load-bearing.

    `-p no:cacheprovider` is **defensive hygiene, not a correctness precondition**
    — AT-396, and my earlier claim here was wrong. I wrote that pytest's cache
    "lets one run inform the next" so that trials would not be independent and no
    binomial bound could stand. A checker measured it rather than arguing: pytest
    writes `lastfailed`, but the next identical invocation still collects every
    test, because selection is only informed by that cache under `--lf`/`--ff`/
    `--sw`, none of which `run_once` passes. What the flag actually buys is that
    41 trials do not race each other writing a shared `.pytest_cache` — worth
    having in a repo that has already had a shared-temp-dir race (AT-357), but not
    the foundation of the statistics.

    Both are pinned anyway: a flag nobody asserts is a flag a future edit drops
    for free. What changed is the REASON recorded next to them, not the test."""
    seen: list[list[str]] = []

    def capture(cmd: list[str], **_kwargs: object) -> _FakeCompleted:
        seen.append(cmd)
        return _FakeCompleted(0)

    monkeypatch.setattr(flake_probe.subprocess, "run", capture)

    flake_probe.run_once("tests/test_x.py::test_y", 1)

    assert len(seen) == 1
    assert "no:cacheprovider" in seen[0], "41 trials must not share one .pytest_cache"
    assert "addopts=" in seen[0], "the project's -q must not silently double to -qq"
    assert "tests/test_x.py::test_y" in seen[0]


def test_the_probe_runs_every_trial_even_after_one_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A probe that halts on the first red proves existence but cannot measure a
    rate — and the rate is the only thing that can ever show a fix worked."""
    calls: list[int] = []

    def fake_run_once(nodeid: str, index: int, timeout: float = 0) -> flake_probe.Run:
        calls.append(index)
        return flake_probe.Run(index=index, returncode=1 if index == 2 else 0, seconds=0.0)

    monkeypatch.setattr(flake_probe, "run_once", fake_run_once)

    summary = flake_probe.probe("t", 5)

    assert calls == [1, 2, 3, 4, 5], "all five trials ran, in order, past the failure"
    assert len(summary.runs) == 5
    assert [r.index for r in summary.failures] == [2]


def test_the_isolation_flags_are_not_described_as_load_bearing() -> None:
    """AT-396. This file twice explained WHY those two flags are there, and twice
    the explanation was stronger than the facts — `no:cacheprovider` described as
    the precondition for the binomial bound (it is not: selection only reads that
    cache under --lf/--ff/--sw), and, in the first draft of this very fix,
    `-o addopts=` described as the thing that keeps failure output from being
    suppressed (it is not: the traceback survives either way; the difference is
    one summary line).

    A docstring is where a confident, unmeasured justification survives longest,
    because nothing executes it. So pin it: the two refuted claims must not come
    back, and the measured wording must stay.

    Two corrections to the first version of this guard, both from its checker:

    **AT-405 — it read `__doc__`, so it could not see the assertion messages.**
    Both refuted claims were still standing verbatim as the `assert ..., "..."`
    messages of the very function whose docstring had been corrected. I had fixed
    the prose a reader sees and left the prose a *failing test* prints, which is
    the copy someone meets at the worst moment. Reading `inspect.getsource` covers
    docstring, messages and comments in one, so the guard can no longer be
    satisfied by moving a claim a few lines down.

    My first version of this fix still only caught ONE of the two messages — it
    listed the refuted *consequence* ("must not suppress the failure output") and
    forgot the refuted *mechanism* ("runs must not inform each other"), so
    restoring the latter sailed straight through a guard whose whole stated point
    was catching both. My own sabotage caught it; both are listed now.

    **AT-406 — it was whitespace-sensitive.** The same sentence re-wrapped across
    this file's 78-column boundary — the wrap its own docstrings produce — would
    have sailed through. Normalising whitespace first means a line break cannot
    launder a refuted claim."""
    source = " ".join(
        inspect.getsource(test_each_run_is_isolated_from_the_ones_before_it).split()
    )

    assert "cannot support a binomial bound" not in source, "the refuted claim is back"
    assert "must not inform each other" not in source, "the refuted MECHANISM, as a message"
    assert "must not suppress the failure output" not in source, "the refuted CONSEQUENCE"
    assert "output this probe exists to capture is suppressed" not in source
    assert "defensive hygiene, not a correctness precondition" in source
    assert "not load-bearing" in source


# -- AT-401: a run that never ends is evidence, not an absence of evidence -----


def _timing_out(*_a: object, **kwargs: object) -> object:
    raise flake_probe.subprocess.TimeoutExpired("pytest", kwargs["timeout"])


def test_a_run_that_outlives_its_bound_is_a_failure_marked_timed_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-401: `run_once` had no timeout, so one hung run stopped an unattended
    41-run probe forever. The probe's subject is a browser crawl, the class that
    hangs rather than fails, and a hang is data about flakiness."""
    monkeypatch.setattr(flake_probe.subprocess, "run", _timing_out)

    run = flake_probe.run_once("tests/test_x.py::test_y", 3, timeout=12)

    assert run.timed_out is True
    assert run.failed is True, "a hung run is a failure, never a silent green"
    assert run.returncode == flake_probe.TIMED_OUT
    assert "12" in run.tail and "did not finish" in run.tail


def test_the_probe_keeps_going_after_a_timed_out_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same reason the probe does not stop at the first failure: a rate needs every
    trial. A timeout that aborted the probe would report the rate of a shorter run."""
    monkeypatch.setattr(flake_probe.subprocess, "run", _timing_out)

    summary = flake_probe.probe("tests/test_x.py::test_y", 3, timeout=1)

    assert len(summary.runs) == 3
    assert len(summary.failures) == 3


def test_a_timed_out_run_says_so_in_the_report_and_the_description(
    tmp_path: Path,
) -> None:
    """A reader must be able to tell "it failed" from "it never answered"."""
    hung = flake_probe.Run(index=2, returncode=flake_probe.TIMED_OUT, seconds=30.0,
                           tail="pytest did not finish within 30s")
    summary = flake_probe.Summary(nodeid="t::x", runs=[flake_probe.Run(1, 0, 1.0), hung])

    lines = flake_probe.describe(summary)
    report = json.loads(
        flake_probe.write_report(summary, tmp_path / "r.json").read_text(encoding="utf-8"))

    assert any("TIMED OUT" in line for line in lines), lines
    assert [d["timed_out"] for d in report["detail"]] == [False, True]


@pytest.mark.parametrize("bad", ["0", "-5"])
def test_the_cli_refuses_a_timeout_that_is_not_positive(bad: str, capsys) -> None:
    assert flake_probe.main(["t::x", "--timeout", bad]) == 2
    assert "positive" in capsys.readouterr().out
