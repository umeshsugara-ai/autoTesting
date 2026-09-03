"""Benchmark scoring — the north star metric must be computed, never asserted."""

from __future__ import annotations

from autotester.schema import BenchCorpus, BenchTrial, Finding, SeededBug
from autotester.schema.enums import Participant, Severity


def corpus() -> BenchCorpus:
    return BenchCorpus(
        id="corpus_1",
        app="pathlynks-staging",
        build_ref="abc123",
        seeded_bugs=[
            SeededBug(id="b1", description="login rejects valid user", severity=Severity.S1,
                      location="/login", detect_hint="valid creds rejected"),
            SeededBug(id="b2", description="report section missing", severity=Severity.S2,
                      location="/report", detect_hint="section absent"),
            SeededBug(id="b3", description="footer year wrong", severity=Severity.S3,
                      location="/", detect_hint="wrong year"),
        ],
    )


def test_scoring_counts_hits_misses_and_false_positives() -> None:
    trial = BenchTrial(
        id="t1",
        corpus_id="corpus_1",
        participant=Participant.AUTOTESTER,
        findings=[
            Finding(text="valid creds rejected", matched_bug_id="b1"),
            Finding(text="section absent", matched_bug_id="b2"),
            Finding(text="button colour is off", matched_bug_id=None),
        ],
        duration_s=610.0,
    )
    score = trial.score(corpus())
    assert score["detected"] == 2
    assert score["seeded"] == 3
    assert score["false_positives"] == 1
    assert score["false_positive_rate"] == 1 / 3
    # S1 (3) + S2 (2) found out of 3+2+1 total weight
    assert score["severity_weighted_recall"] == 5 / 6


def test_perfect_trial_scores_one_with_no_false_positives() -> None:
    trial = BenchTrial(
        id="t2",
        corpus_id="corpus_1",
        participant=Participant.HUMAN,
        findings=[Finding(text=f"found {b}", matched_bug_id=b) for b in ("b1", "b2", "b3")],
    )
    score = trial.score(corpus())
    assert score["detection_rate"] == 1.0
    assert score["false_positive_rate"] == 0.0
    assert score["severity_weighted_recall"] == 1.0


def test_empty_trial_does_not_divide_by_zero() -> None:
    trial = BenchTrial(id="t3", corpus_id="corpus_1", participant=Participant.HUMAN)
    score = trial.score(corpus())
    assert score["detection_rate"] == 0.0
    assert score["false_positive_rate"] == 0.0
