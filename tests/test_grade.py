"""GRADE stage. Contract: qa/contracts/grade.md G1-G5."""

from __future__ import annotations

from pathlib import Path

from autotester.core.paths import RepoDocs
from autotester.providers.mock import MockProvider
from autotester.schema.enums import EvidenceKind, Outcome, Result
from autotester.schema.run import Evidence, RawResult
from autotester.schema.verdict import Criterion, Failure, Judgment, Rubric
from autotester.stages.grade import grade
from autotester.store.project_store import ProjectStore


def make_rubric() -> Rubric:
    return Rubric(
        id="rub_login",
        criteria=[
            Criterion(id="c1", text="Login form is visible before submit"),
            Criterion(id="c2", text="Dashboard greeting appears after submit"),
        ],
        no_fire=["cosmetic spacing"],
    )


def make_result(outcome: Outcome, **kw) -> RawResult:
    evidence = kw.pop("evidence", [
        Evidence(kind=EvidenceKind.SCREENSHOT, path="01-login.png", step_order=1),
        Evidence(kind=EvidenceKind.SCREENSHOT, path="02-dashboard.png", step_order=2),
    ])
    return RawResult(case_id="case_abc", outcome=outcome, evidence=evidence, **kw)


# -- G2 deterministic outcomes never reach the judge -------------------------

def test_blocked_hitl_is_blocked_without_calling_the_judge() -> None:
    judge = MockProvider()
    result = make_result(Outcome.BLOCKED_HITL, hitl_prompt="need OTP")
    verdict = grade(make_rubric(), result, "run_1", judge)

    assert verdict.result is Result.BLOCKED
    assert verdict.note == "need OTP"
    assert verdict.grader_provider == "rule"
    assert judge.prompts == []


def test_errored_is_inconclusive_without_calling_the_judge() -> None:
    judge = MockProvider()
    result = make_result(Outcome.ERRORED, error="TimeoutError: locator not found")
    verdict = grade(make_rubric(), result, "run_1", judge)

    assert verdict.result is Result.INCONCLUSIVE
    assert "TimeoutError" in verdict.note
    assert judge.prompts == []


# -- G1 stateless prompt contains only rubric + evidence ---------------------

def test_prompt_carries_only_rubric_and_evidence_no_case_metadata() -> None:
    rubric = make_rubric()
    judgment = Judgment(result=Result.PASS, scoreboard="2/2", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})
    result = make_result(Outcome.COMPLETED)

    grade(rubric, result, "run_1", judge)

    assert len(judge.prompts) == 1
    role, prompt = judge.prompts[0]
    assert role == "judge"
    assert "c1: Login form is visible" in prompt
    assert "01-login.png" in prompt and "02-dashboard.png" in prompt
    assert "case_abc" not in prompt  # no case id/metadata leaks into the judge's prompt


def test_completed_run_judged_pass(tmp_path: Path) -> None:
    rubric = make_rubric()
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})
    result = make_result(Outcome.COMPLETED)

    verdict = grade(rubric, result, "run_1", judge)

    assert verdict.result is Result.PASS
    assert verdict.grader_provider == "mock"
    assert verdict.rubric_hash == rubric.fingerprint
    assert verdict.run_id == "run_1" and verdict.case_id == "case_abc"


# -- AT-049 the judge actually sees the screenshots, not just their names ----

def test_judge_receives_the_real_screenshot_files_when_run_dir_is_given(
    tmp_path: Path,
) -> None:
    """The judge used to be told nothing but filenames in the prompt text --
    a plausible-sounding guess, never a real look at the evidence. When
    grade() is given the run's real directory, the judge must receive the
    actual image files that exist there."""
    run_dir = tmp_path / "run_1"
    run_dir.mkdir()
    (run_dir / "01-login.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (run_dir / "02-dashboard.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})

    grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge, run_dir=run_dir)

    assert judge.judge_images == [[run_dir / "01-login.png", run_dir / "02-dashboard.png"]]


def test_judge_receives_no_images_when_run_dir_is_not_given(tmp_path: Path) -> None:
    """A caller that hasn't been updated yet (an older script) still gets
    today's text-only behavior -- never a crash for a missing run_dir."""
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})

    grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge)

    assert judge.judge_images == [[]]


# -- G3 an unevidenced or inconsistent judgment is rejected ------------------

def test_failure_with_no_evidence_refs_is_downgraded_to_inconclusive() -> None:
    rubric = make_rubric()
    bad = Judgment(
        result=Result.FAIL, scoreboard="1/2", criteria_met=1, criteria_total=2,
        failures=[Failure(criterion_id="c2", reason="no greeting seen")],  # no evidence_refs
    )
    judge = MockProvider(responses={"judge": [bad]})
    verdict = grade(rubric, make_result(Outcome.COMPLETED), "run_1", judge)

    assert verdict.result is Result.INCONCLUSIVE
    assert "evidence_refs" in verdict.note


def test_pass_with_nonempty_failures_is_rejected() -> None:
    rubric = make_rubric()
    contradictory = Judgment(
        result=Result.PASS, scoreboard="1/2", criteria_met=1, criteria_total=2,
        failures=[Failure(criterion_id="c2", reason="x", evidence_refs=["02-dashboard.png"])],
    )
    judge = MockProvider(responses={"judge": [contradictory]})
    verdict = grade(rubric, make_result(Outcome.COMPLETED), "run_1", judge)

    assert verdict.result is Result.INCONCLUSIVE
    assert "PASS" in verdict.note


def test_failure_citing_unknown_criterion_is_rejected() -> None:
    rubric = make_rubric()
    bad = Judgment(
        result=Result.FAIL, scoreboard="1/2", criteria_met=1, criteria_total=2,
        failures=[Failure(criterion_id="c99", reason="x", evidence_refs=["01-login.png"])],
    )
    judge = MockProvider(responses={"judge": [bad]})
    verdict = grade(rubric, make_result(Outcome.COMPLETED), "run_1", judge)

    assert verdict.result is Result.INCONCLUSIVE
    assert "unknown criterion" in verdict.note


def test_criteria_total_mismatch_is_rejected() -> None:
    rubric = make_rubric()  # 2 criteria
    bad = Judgment(result=Result.PASS, scoreboard="1/1", criteria_met=1, criteria_total=1)
    judge = MockProvider(responses={"judge": [bad]})
    verdict = grade(rubric, make_result(Outcome.COMPLETED), "run_1", judge)

    assert verdict.result is Result.INCONCLUSIVE
    assert "criteria_total" in verdict.note


def test_fail_with_no_failures_cited_is_rejected() -> None:
    rubric = make_rubric()
    bad = Judgment(result=Result.FAIL, scoreboard="1/2", criteria_met=1, criteria_total=2)
    judge = MockProvider(responses={"judge": [bad]})
    verdict = grade(rubric, make_result(Outcome.COMPLETED), "run_1", judge)

    assert verdict.result is Result.INCONCLUSIVE
    assert "no failures cited" in verdict.note


def test_well_evidenced_fail_is_accepted() -> None:
    rubric = make_rubric()
    good = Judgment(
        result=Result.FAIL, scoreboard="1/2", criteria_met=1, criteria_total=2,
        failures=[Failure(criterion_id="c2", reason="dashboard never appeared",
                           evidence_refs=["02-dashboard.png"])],
    )
    judge = MockProvider(responses={"judge": [good]})
    verdict = grade(rubric, make_result(Outcome.COMPLETED), "run_1", judge)

    assert verdict.result is Result.FAIL
    assert verdict.failures[0].criterion_id == "c2"


# -- G4 persistence round-trips through ProjectStore -------------------------

def test_verdict_round_trips_through_project_store_without_colliding_with_results(
    tmp_path: Path,
) -> None:
    store = ProjectStore("pathlynks", tmp_path)
    result = make_result(Outcome.COMPLETED)
    store.save_result("run_1", result)
    judgment = Judgment(result=Result.PASS, scoreboard="2/2", criteria_met=2, criteria_total=2)
    verdict = grade(make_rubric(), result, "run_1", MockProvider(responses={"judge": [judgment]}))
    store.save_verdict("run_1", verdict)

    loaded_results = store.load_results("run_1")
    loaded_verdicts = store.load_verdicts("run_1")
    assert len(loaded_results) == 1 and loaded_results[0].case_id == "case_abc"
    assert len(loaded_verdicts) == 1 and loaded_verdicts[0].result is Result.PASS


# -- G5 prompt is a file --------------------------------------------------

def test_prompt_is_read_from_a_file_not_built_inline() -> None:
    docs = RepoDocs()
    template_path = docs.prompts_dir / "grade_v1.md"
    assert template_path.exists()
    assert "{{RUBRIC}}" in template_path.read_text(encoding="utf-8")
    assert "{{EVIDENCE}}" in template_path.read_text(encoding="utf-8")
