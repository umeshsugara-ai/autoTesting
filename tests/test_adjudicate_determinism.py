"""Determinism — VL4. The property the observation cache rests on.

If loading order changed the output, a cached re-run would produce a different
analysis every time and re-running would mean nothing. Split out of
`test_adjudicate.py` at the 300-line cap: everything here answers one question
(is the merge a function of its inputs and nothing else?), and it is the
question AT-197 was hiding in.

Contract: qa/contracts/video-learning.md VL4.
"""

from __future__ import annotations

import random

from video_fakes import FLASH, PRO, issue, obs, screen

from autotester.schema.enums import Severity
from autotester.stages.adjudicate import adjudicate


def content(analysis) -> str:
    """The analysis WITHOUT its provenance envelope.

    `Artifact.created_at` is a wall-clock stamp, so two calls a microsecond
    apart differ there and nowhere else. Comparing whole JSON conflated
    "adjudication is deterministic" with "the clock did not tick" — my first
    version of the determinism test failed on exactly that, and my
    adjudicate-twice test PASSED only because both calls landed in the same
    microsecond. Determinism is a property of the CONTENT."""
    return analysis.model_dump_json(exclude={"created_at", "provenance"})


def test_the_result_does_not_depend_on_input_order() -> None:
    """VL4. If loading order changed the output, the cached observations would
    produce a different analysis every run and re-running would mean nothing."""
    observations = [
        obs(PRO, chunk=0, offset=0.0, screens=[screen("Home", 1.0, 9.0)],
            issues=[issue("Home", 5.0)], summary="a"),
        obs(FLASH, chunk=0, offset=0.0, screens=[screen("home", 2.0, 8.0)], summary="b"),
        obs(PRO, chunk=1, offset=165.0, screens=[screen("Trainers", 10.0, 20.0)]),
        obs(FLASH, chunk=1, offset=165.0, screens=[screen("Trainers", 11.0, 21.0)],
            issues=[issue("Trainers", 12.0)]),
    ]
    baseline = content(adjudicate(observations, "src_1"))

    for seed in range(8):
        shuffled = list(observations)
        random.Random(seed).shuffle(shuffled)
        assert content(adjudicate(shuffled, "src_1")) == baseline


def test_order_still_does_not_matter_with_TWO_prompts_per_chunk() -> None:
    """The shape that actually ships — `PROMPT_NAMES` has two entries, so every
    chunk is read twice by each model.

    AT-197: the sort key omitted `prompt_name`, these two observations tied,
    and Python's stable sort handed the merge straight back to caller order.
    Permuting them produced two different analyses — different screens,
    journey, issues and summary. Eight shuffles of a single-prompt fixture
    could not see it, because a single-prompt fixture has no tie in it."""
    pair = [
        obs(PRO, chunk=0, prompt="ingest_video_v1",
            screens=[screen("Home", 1.0, 9.0, purpose="landing")],
            issues=[issue("Home", 4.0, severity=Severity.S3)], summary="maps the product"),
        obs(PRO, chunk=0, prompt="video_issues_v1",
            screens=[screen("Home", 2.0, 8.0, purpose="sign in")],
            issues=[issue("Home", 6.0, severity=Severity.S1)], summary="finds the faults"),
    ]

    assert content(adjudicate(pair, "src_1")) == content(adjudicate(pair[::-1], "src_1"))


def test_adjudicating_twice_gives_byte_identical_output() -> None:
    observations = [obs(PRO, screens=[screen("Home", 1.0, 9.0)])]

    first = content(adjudicate(observations, "src_1"))
    second = content(adjudicate(observations, "src_1"))

    assert first == second


def test_omitting_expected_records_UNKNOWN_not_complete() -> None:
    """AT-208. `expected=None` used to default to the number of observations
    present, so every caller but `analyze` got an artifact declaring itself
    COMPLETE -- a default-value fallback inside the very field added to stop
    one. T-136's scorer re-adjudicates cached observations and is the caller
    this protects: a fragment must never read as a full run."""
    unknown = adjudicate([obs(PRO, screens=[screen("Home", 1.0)])], "src_1")

    assert unknown.observations_expected == 0
    assert not unknown.is_complete


def test_a_partial_reading_says_how_partial_it_is() -> None:
    """AT-198: one answer out of twenty-four produces the same shape as
    twenty-four out of twenty-four. The numbers are the only thing that tells
    a reader which one they are holding."""
    one_of_four = adjudicate([obs(PRO, screens=[screen("Home", 1.0)])], "src_1", expected=4)

    assert (one_of_four.observations_used, one_of_four.observations_expected) == (1, 4)
    assert not one_of_four.is_complete
    assert adjudicate([obs(PRO)], "src_1", expected=1).is_complete
