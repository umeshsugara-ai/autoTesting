"""AT-335's arithmetic. `scripts/flake_probe.py` is the tool that says how little
a run of green runs proves.

The statistics are tested with fabricated `Run` rows and never by driving a real
browser: a test whose own outcome depends on a 1-in-14 flake cannot be the thing
that certifies the flake measurement.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from flake_probe import (
    SUSPECTED_RATE,
    Run,
    Summary,
    ceiling_given_no_failures,
    describe,
    runs_for_confidence,
    write_report,
)


def _clean(count: int) -> Summary:
    return Summary(nodeid="tests/test_x.py::test_y",
                   runs=[Run(index=i, returncode=0, seconds=1.0) for i in range(1, count + 1)])


# -- the number AT-335 was missing --------------------------------------------

def test_thirteen_green_runs_do_not_exclude_a_one_in_fourteen_defect() -> None:
    """The whole reason this tool exists. AT-335 tried 13 times, saw nothing, and
    honestly filed the fix as unproven — but the arithmetic is stronger than the
    note was: 13 clean runs bound the rate at ~21%, and the suspected 7.1% sits
    well inside that. The sample said nothing about the bug."""
    ceiling = ceiling_given_no_failures(13)

    assert 0.20 < ceiling < 0.21, "1 - 0.05**(1/13), not the rule-of-three 3/13"
    assert ceiling > SUSPECTED_RATE, "so 13 green runs cannot rule it out"


def test_the_tool_names_the_sample_size_that_would_have_settled_it() -> None:
    """41, not 13. Without this number 'I could not reproduce it' has no remedy."""
    assert runs_for_confidence(SUSPECTED_RATE) == 41


def test_the_named_sample_size_actually_achieves_what_it_claims() -> None:
    """The two functions must agree, or the tool tells you to run 41 and then says
    41 was not enough. This is the pair's internal consistency, not a restatement:
    41 clean runs must bound the rate BELOW the suspected one."""
    needed = runs_for_confidence(SUSPECTED_RATE)

    assert ceiling_given_no_failures(needed) < SUSPECTED_RATE


def test_more_runs_never_loosen_the_bound() -> None:
    bounds = [ceiling_given_no_failures(n) for n in (5, 13, 41, 100)]

    assert bounds == sorted(bounds, reverse=True)


@pytest.mark.parametrize("runs", [0, -1])
def test_a_bound_cannot_be_computed_from_no_runs(runs: int) -> None:
    """Zero runs is not zero failures. Returning a bound here would let a probe
    that never ran read as the strongest evidence of all."""
    with pytest.raises(ValueError, match="at least one run"):
        ceiling_given_no_failures(runs)


@pytest.mark.parametrize("rate", [0.0, 1.0, -0.1, 2.0])
def test_an_impossible_rate_is_refused(rate: float) -> None:
    with pytest.raises(ValueError, match="strictly between"):
        runs_for_confidence(rate)


# -- the summary reports what happened, not what we hoped ----------------------

def test_a_probe_that_saw_nothing_reports_a_bound_and_not_a_zero() -> None:
    lines = "\n".join(describe(_clean(13)))

    assert "0 failure(s) in 13 run(s)" in lines
    assert "NOT at zero" in lines, "the sentence that stops a clean probe reading as proof"
    assert "does NOT exclude" in lines
    assert "41 runs are needed" in lines


def test_a_probe_long_enough_to_settle_it_says_so() -> None:
    """At 41 clean runs the bound finally drops below the suspected rate, and the
    wording has to flip — a tool that says 'inconclusive' at every sample size is
    not measuring anything."""
    lines = "\n".join(describe(_clean(41)))

    assert "excludes" in lines and "does NOT exclude" not in lines
    assert "outside" in lines


def test_a_reproduced_failure_reports_the_observed_rate_and_keeps_its_evidence() -> None:
    """The rare run is the whole prize. Its output must survive the summary, or the
    probe that finally caught it has thrown away the only copy."""
    summary = Summary(nodeid="tests/test_x.py::test_y", runs=[
        Run(index=1, returncode=0, seconds=1.0),
        Run(index=2, returncode=1, seconds=2.0, tail="assert '/settings.html' in {'/'}"),
    ])
    lines = "\n".join(describe(summary))

    assert summary.observed_rate == 0.5
    assert summary.ceiling is None, "a bound on zero failures is meaningless once one is seen"
    assert "run 2 FAILED" in lines
    assert "reproduced, evidence captured" in lines
    assert summary.failures[0].tail.startswith("assert")


def test_the_probe_does_not_stop_at_the_first_failure() -> None:
    """A probe that halts on the first red can prove existence but never measure a
    rate — and AT-335 needs the rate, because the fix has to be shown to move it."""
    summary = Summary(nodeid="t", runs=[
        Run(index=1, returncode=1, seconds=1.0),
        Run(index=2, returncode=0, seconds=1.0),
        Run(index=3, returncode=1, seconds=1.0),
    ])

    assert len(summary.runs) == 3, "runs after the first failure are still recorded"
    assert summary.observed_rate == pytest.approx(2 / 3)


def test_an_empty_probe_has_no_rate_rather_than_a_rate_of_zero() -> None:
    empty = Summary(nodeid="t", runs=[])

    assert empty.observed_rate is None
    assert empty.ceiling is None
    assert describe(empty) == ["t: no runs"]


# -- the report on disk --------------------------------------------------------

def test_the_report_carries_the_bound_and_the_failing_output(tmp_path: Path) -> None:
    """The JSON is what a later session reads when nobody remembers the run."""
    import json

    summary = Summary(nodeid="t", runs=[Run(index=1, returncode=1, seconds=3.0, tail="boom")])
    written = json.loads(write_report(summary, tmp_path / "r.json").read_text(encoding="utf-8"))

    assert written["failures"] == 1
    assert written["observed_rate"] == 1.0
    assert written["ceiling_at_confidence"] is None
    assert written["detail"][0]["tail"] == "boom"

