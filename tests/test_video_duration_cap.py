"""T-191/AT-587 V6(b): a case that runs longer than `MAX_VIDEO_DURATION_S`
(20 minutes, the gate's own "15-20 minute walkthrough" language) has its
video dropped as a disk safety net, regardless of verdict -- the plan's named
alternative to actively truncating a live Playwright recording mid-flight.
Contract: qa/contracts/run-video.md V6. Fixture-only: calls
`_finalize_video` directly with a `RawResult.duration_s` on each side of the
cap; no real browser or recording needed to prove this arithmetic.
"""

from __future__ import annotations

from pathlib import Path

from autotester.browser.video import MAX_VIDEO_DURATION_S
from autotester.schema.enums import EvidenceKind, Outcome, Result
from autotester.schema.run import RawResult
from autotester.schema.verdict import Verdict
from autotester.stages.run_case_pipeline import _finalize_video


def _fail_verdict() -> Verdict:
    return Verdict(run_id="run_1", case_id="case_1", result=Result.FAIL, grader_provider="mock")


def test_a_case_under_the_duration_cap_keeps_its_video_on_a_fail(tmp_path: Path) -> None:
    video = tmp_path / "case_1.webm"
    video.write_bytes(b"x")
    result = RawResult(case_id="case_1", outcome=Outcome.COMPLETED,
                       duration_s=MAX_VIDEO_DURATION_S - 1.0)

    _finalize_video(result, _fail_verdict(), "case_1.webm", tmp_path)

    assert video.exists()
    assert any(e.kind is EvidenceKind.VIDEO for e in result.evidence)


def test_a_case_over_the_duration_cap_drops_its_video_even_on_a_fail(tmp_path: Path) -> None:
    """The disk safety net beats the keep-on-FAIL rule -- a runaway case never
    parks an unbounded recording on disk just because it also failed."""
    video = tmp_path / "case_1.webm"
    video.write_bytes(b"x")
    result = RawResult(case_id="case_1", outcome=Outcome.COMPLETED,
                       duration_s=MAX_VIDEO_DURATION_S + 1.0)

    _finalize_video(result, _fail_verdict(), "case_1.webm", tmp_path)

    assert not video.exists()
    assert not any(e.kind is EvidenceKind.VIDEO for e in result.evidence)


def test_no_video_recorded_is_always_a_no_op_regardless_of_duration(tmp_path: Path) -> None:
    result = RawResult(case_id="case_1", outcome=Outcome.COMPLETED,
                       duration_s=MAX_VIDEO_DURATION_S + 100.0)

    _finalize_video(result, _fail_verdict(), None, tmp_path)  # video_rel=None: nothing to do

    assert result.evidence == []
