"""GRADE: an independent, stateless judge reads a Rubric + a RawResult's evidence.

The executor never grades itself (core-invariants C7) — this stage never sees the
case's steps or script, only the rubric and the evidence execute.py recorded.
`BLOCKED_HITL`/`ERRORED` outcomes are judged deterministically (there is nothing
coherent to grade); only `COMPLETED` runs reach the judge. The judge's raw answer
is then self-consistency-checked before it becomes a `Verdict` — an unevidenced
failure, or a PASS that doesn't add up, is downgraded to INCONCLUSIVE rather than
trusted. Contract: qa/contracts/grade.md.
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.paths import RepoDocs
from autotester.providers.base import Provider
from autotester.schema.enums import EvidenceKind, Outcome, Result
from autotester.schema.run import RawResult
from autotester.schema.verdict import Failure, Judgment, Rubric, Verdict

PROMPT_NAME = "grade_v1.md"


def _render_evidence(result: RawResult) -> str:
    lines = [f"outcome: {result.outcome.value}"]
    for ev in result.evidence:
        loc = f" (step {ev.step_order})" if ev.step_order is not None else ""
        lines.append(f"- [{ev.kind.value}] {ev.path}{loc}")
    return "\n".join(lines)


def _render_rubric(rubric: Rubric) -> str:
    criteria = "\n".join(
        f"- {c.id}: {c.text}" + (" (evidence required)" if c.evidence_required else "")
        for c in rubric.criteria
    )
    no_fire = "\n".join(f"- {n}" for n in rubric.no_fire) or "(none)"
    return f"criteria:\n{criteria}\n\nno-fire (do not flag these):\n{no_fire}"


def build_grade_prompt(rubric: Rubric, result: RawResult, docs: RepoDocs) -> str:
    template = (docs.prompts_dir / PROMPT_NAME).read_text(encoding="utf-8")
    return (
        template.replace("{{RUBRIC}}", _render_rubric(rubric))
        .replace("{{EVIDENCE}}", _render_evidence(result))
        .replace("{{FORMAT}}", rubric.feedback_format)
    )


def _inconsistency(rubric: Rubric, judgment: Judgment) -> str | None:
    """Why `judgment` cannot be trusted as-is, or None if it's self-consistent."""
    known_ids = {c.id for c in rubric.criteria}
    evidence_required = {c.id for c in rubric.criteria if c.evidence_required}
    for failure in judgment.failures:
        if failure.criterion_id not in known_ids:
            return f"failure cites unknown criterion '{failure.criterion_id}'"
        if failure.criterion_id in evidence_required and not failure.evidence_refs:
            return f"failure on '{failure.criterion_id}' has no evidence_refs"
    if judgment.criteria_total != len(rubric.criteria):
        return f"criteria_total {judgment.criteria_total} != rubric has {len(rubric.criteria)}"
    if judgment.result is Result.PASS and judgment.failures:
        return "PASS but failures is non-empty"
    if judgment.result is Result.FAIL and not judgment.failures:
        return "FAIL but no failures cited"
    return None


def _verdict(
    run_id: str, result: RawResult, rubric: Rubric, *, verdict_result: Result,
    provider_id: str, scoreboard: str, note: str | None = None,
    criteria_met: int = 0, failures: list[Failure] | None = None,
) -> Verdict:
    return Verdict(
        run_id=run_id, case_id=result.case_id, result=verdict_result, scoreboard=scoreboard,
        criteria_met=criteria_met, criteria_total=len(rubric.criteria),
        failures=failures or [], grader_provider=provider_id,
        rubric_hash=rubric.fingerprint, note=note,
    )


def _screenshot_paths(result: RawResult, run_dir: Path | None) -> list[Path]:
    """Real image files the judge should actually see — AT-049: `_render_evidence`
    only ever put a screenshot's *filename* in the prompt, so a text-only judge
    was grading blind, guessing plausibility from a label it could not verify.
    `run_dir` is optional so a caller without one yet (an older script) still
    gets today's text-only behavior, never a crash."""
    if run_dir is None:
        return []
    return [
        run_dir / ev.path for ev in result.evidence if ev.kind is EvidenceKind.SCREENSHOT
    ]


def grade(rubric: Rubric, result: RawResult, run_id: str, judge: Provider,
          docs: RepoDocs | None = None, run_dir: Path | None = None) -> Verdict:
    """Judge one case's execution against `rubric`. Never sees the case's own steps."""
    if result.outcome is Outcome.BLOCKED_HITL:
        return _verdict(run_id, result, rubric, verdict_result=Result.BLOCKED,
                         provider_id="rule", scoreboard="not judged: execution was blocked",
                         note=result.hitl_prompt)
    if result.outcome is Outcome.ERRORED:
        return _verdict(run_id, result, rubric, verdict_result=Result.INCONCLUSIVE,
                         provider_id="rule", scoreboard="not judged: execution errored",
                         note=result.error)

    prompt = build_grade_prompt(rubric, result, docs or RepoDocs())
    judgment = judge.judge(prompt, Judgment, images=_screenshot_paths(result, run_dir))
    problem = _inconsistency(rubric, judgment)
    if problem is not None:
        return _verdict(run_id, result, rubric, verdict_result=Result.INCONCLUSIVE,
                         provider_id=judge.id, scoreboard="judge output rejected",
                         note=f"self-consistency check failed: {problem}")
    return _verdict(run_id, result, rubric, verdict_result=judgment.result,
                     provider_id=judge.id, scoreboard=judgment.scoreboard,
                     criteria_met=judgment.criteria_met, failures=judgment.failures,
                     note=judgment.note)
