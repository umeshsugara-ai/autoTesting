"""Does the judge actually SEE the evidence it grades on?

Contract: qa/contracts/grade.md G1/G3. Split out of `test_grade.py` (doctor's
file-length rule) because this is one responsibility, not a slice of the stage's
general behaviour: AT-049 found a judge reasoning from screenshot *filenames* it
could never verify, and AT-366 found the layer under it — a path that does not
exist is filtered out in silence by all three providers, so a verdict graded on
none of its images looked exactly like one graded on all of them.
"""

from __future__ import annotations

from pathlib import Path

from autotester.providers.mock import MockProvider
from autotester.schema.enums import EvidenceKind, Outcome, Result
from autotester.schema.run import Evidence, RawResult
from autotester.schema.verdict import Criterion, Judgment, Rubric
from autotester.stages.grade import grade


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


# -- AT-366 a screenshot that is missing is counted, never dropped in silence -

def _run_dir_missing_one(tmp_path: Path) -> Path:
    """The AT-036 retry class on disk: the run recorded two screenshots and only
    one of them was actually written."""
    run_dir = tmp_path / "run_1"
    run_dir.mkdir()
    (run_dir / "01-login.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    return run_dir


def test_a_screenshot_the_run_recorded_but_never_wrote_is_counted_not_dropped(
    tmp_path: Path,
) -> None:
    """All three providers filter a non-existent path out in silence, so before
    these counts a verdict graded on one of two screenshots looked exactly like
    one graded on both. The judge still only gets the real file -- sending a
    path that is not there would just move the failure into the provider -- but
    the Verdict now records what was asked for against what was seen."""
    run_dir = _run_dir_missing_one(tmp_path)
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})

    verdict = grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge,
                    run_dir=run_dir)

    assert judge.judge_images == [[run_dir / "01-login.png"]]
    assert verdict.images_requested == 2, "both SCREENSHOT evidence rows were offered"
    assert verdict.images_seen == 1, "only one file existed"
    assert verdict.graded_on_partial_evidence is True


def test_the_shortfall_reaches_the_field_the_report_actually_renders(
    tmp_path: Path,
) -> None:
    """A structured count nothing renders is the same silence one layer up.
    `report_export.py` puts `scoreboard` on the page — in the summary table and
    in `_case_section` — and renders `note` nowhere at all, so the sentence has
    to be on the scoreboard or a human never sees it. It goes on `note` too,
    because that is the durable record the artifact carries."""
    run_dir = _run_dir_missing_one(tmp_path)
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})

    verdict = grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge,
                    run_dir=run_dir)

    assert "graded on 1 of 2 screenshots" in verdict.scoreboard, "the rendered field"
    assert verdict.scoreboard.endswith("2/2 met"), "the judge's own scoreboard must survive"
    assert "graded on 1 of 2 screenshots" in (verdict.note or ""), "the durable record"


def test_a_complete_run_is_not_labelled_partial_and_keeps_its_own_note(
    tmp_path: Path,
) -> None:
    """The counts must be able to say 'nothing was lost', or they are an alarm
    that is always on. The judge's own note must survive untouched."""
    run_dir = _run_dir_missing_one(tmp_path)
    (run_dir / "02-dashboard.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2,
                        criteria_total=2, note="clean run")
    judge = MockProvider(responses={"judge": [judgment]})

    verdict = grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge,
                    run_dir=run_dir)

    assert (verdict.images_requested, verdict.images_seen) == (2, 2)
    assert verdict.graded_on_partial_evidence is False
    assert verdict.note == "clean run", "the judge's note must not be rewritten"
    assert verdict.scoreboard == "2/2 met", "nor its scoreboard"


def test_a_judgement_on_no_images_at_all_is_visible_as_such(tmp_path: Path) -> None:
    """The worst case and the one that motivated AT-366: every screenshot
    missing, the judge grading on prompt text alone -- the exact AT-049 state --
    and nothing anywhere saying so."""
    run_dir = tmp_path / "run_1"
    run_dir.mkdir()
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})

    verdict = grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge,
                    run_dir=run_dir)

    assert judge.judge_images == [[]]
    assert (verdict.images_requested, verdict.images_seen) == (2, 0)
    assert verdict.graded_on_partial_evidence is True
    assert "graded on 0 of 2 screenshots" in (verdict.note or "")


def test_a_caller_with_no_run_dir_is_not_falsely_flagged_as_partial() -> None:
    """`run_dir=None` is the documented text-only path, not a lost file. It must
    report 0 requested -- flagging it partial would make every older script
    caller look like it had dropped evidence."""
    judgment = Judgment(result=Result.PASS, scoreboard="2/2 met", criteria_met=2, criteria_total=2)
    judge = MockProvider(responses={"judge": [judgment]})

    verdict = grade(make_rubric(), make_result(Outcome.COMPLETED), "run_1", judge)

    assert (verdict.images_requested, verdict.images_seen) == (0, 0)
    assert verdict.graded_on_partial_evidence is False


