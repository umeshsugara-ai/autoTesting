"""Contract: qa/contracts/bench.md K1-K5. Pure-logic pieces of stages/bench.py
-- the real end-to-end trial (a real browser + a real judge) is not a
network-independent unit test by nature; see
qa/manifests/t120-bench.md for that real run's cited evidence.
"""

from __future__ import annotations

from autotester.schema.bench import BenchCorpus
from autotester.schema.enums import Participant, Result, Severity
from autotester.schema.verdict import Failure, Verdict
from autotester.stages import bench


def _corpus() -> BenchCorpus:
    return BenchCorpus(
        id="corpus_test", app="demo", build_ref="broken",
        seeded_bugs=[
            bench.seeded_bug(
                "bug_login", "login rejects correct password", "/login.html",
                "shows an error on correct credentials", Severity.S1,
            )
        ],
    )


def _verdict(case_id: str, result: Result, criterion_id: str = "c1") -> Verdict:
    return Verdict(
        run_id="run_1", case_id=case_id, result=result,
        failures=(
            [Failure(criterion_id=criterion_id, reason="broke")] if result is Result.FAIL else []
        ),
    )


def test_findings_from_verdicts_maps_a_fail_to_its_seeded_bug() -> None:
    verdicts = [_verdict("case_login", Result.FAIL)]
    findings = bench.findings_from_verdicts(verdicts, {"case_login": "bug_login"})
    assert len(findings) == 1
    assert findings[0].matched_bug_id == "bug_login"


def test_findings_from_verdicts_unmapped_fail_is_a_false_positive() -> None:
    verdicts = [_verdict("case_home", Result.FAIL)]
    findings = bench.findings_from_verdicts(verdicts, {"case_login": "bug_login"})
    assert findings[0].matched_bug_id is None


def test_findings_from_verdicts_ignores_pass_and_inconclusive() -> None:
    verdicts = [_verdict("case_login", Result.PASS), _verdict("case_home", Result.INCONCLUSIVE)]
    findings = bench.findings_from_verdicts(verdicts, {})
    assert findings == []


def test_run_autotester_trial_detects_the_seeded_bug() -> None:
    corpus = _corpus()
    verdicts = [_verdict("case_login", Result.FAIL)]
    trial = bench.run_autotester_trial(
        "trial_ai", corpus, verdicts, {"case_login": "bug_login"}, duration_s=12.0,
    )
    assert trial.participant is Participant.AUTOTESTER
    score = trial.score(corpus)
    assert score["detected"] == 1
    assert score["false_positives"] == 0


def test_oracle_human_trial_is_labeled_a_baseline_not_a_live_run() -> None:
    corpus = _corpus()
    trial = bench.oracle_human_trial("trial_human", corpus, duration_s=300.0)
    assert trial.participant is Participant.HUMAN
    assert trial.participant_label == "human-oracle-baseline"
    score = trial.score(corpus)
    assert score["detection_rate"] == 1.0
    assert score["false_positive_rate"] == 0.0


def test_scorecard_calls_bench_trial_score_for_every_trial() -> None:
    corpus = _corpus()
    ai = bench.run_autotester_trial(
        "trial_ai", corpus, [_verdict("case_login", Result.FAIL)],
        {"case_login": "bug_login"}, duration_s=12.0,
    )
    human = bench.oracle_human_trial("trial_human", corpus, duration_s=300.0)
    card = bench.scorecard(corpus, [ai, human])
    assert card["autotester-real-run"] == ai.score(corpus)
    assert card["human-oracle-baseline"] == human.score(corpus)
