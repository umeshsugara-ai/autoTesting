"""RUN_CASE_PIPELINE: the one function that runs a case and grades it.

Contract: qa/contracts/run-case-pipeline.md RP1-RP4. Before this stage,
grading always required a hand-written `Rubric` inline in a throwaway script
(`scripts/regression_proof.py`, `scripts/bench_trial.py`,
`scripts/run_pathlynks_first_cases.py`) — there was no generic "grade this
case" path a UI button could call for an arbitrary project's case. This
stage is that path: it lazily builds and persists a plain default rubric the
first time a case is run without one, so any case is gradeable, forever,
with no hand-written Python required.
"""

from __future__ import annotations

from autotester.browser.session import BrowserSession
from autotester.providers.base import Provider
from autotester.schema.case import Case
from autotester.schema.run import RawResult
from autotester.schema.verdict import Criterion, Rubric, Verdict
from autotester.stages.execute import run_case
from autotester.stages.grade import grade
from autotester.store.project_store import ProjectStore


def default_rubric(case: Case, rubric_id: str) -> Rubric:
    """A plain, honest default: pass if the evidence is consistent with the
    case's own stated rationale. Not a substitute for a hand-tuned rubric
    when one exists — only the fallback so every case is gradeable at all."""
    claim = case.rationale or f"the case '{case.title}' completes as its steps describe"
    return Rubric(
        id=rubric_id, case_id=case.id,
        criteria=[Criterion(id="c1", text=(
            f"The evidence is consistent with: {claim}. If you cite this as a failure, "
            "use criterion id 'c1' exactly — do not invent a different id."
        ))],
        no_fire=["exact wording of any error message shown by the product"],
    )


def run_and_grade_case(
    case: Case, session: BrowserSession, judge: Provider, run_id: str,
    store: ProjectStore | None = None,
) -> tuple[RawResult, Verdict]:
    """Run `case` on `session`, then grade it against its persisted rubric —
    building and saving a `default_rubric` the first time one doesn't exist
    for this `rubric_ref`. The single source of truth for "run one case,"
    so a UI button and a CLI script call exactly the same path."""
    store = store or ProjectStore(case.project)
    result = run_case(case, session)
    rubric_id = case.rubric_ref or f"rub_{case.id}"
    rubric = store.load_rubric(rubric_id)
    if rubric is None:
        rubric = default_rubric(case, rubric_id)
        store.save_rubric(rubric)
    verdict = grade(rubric, result, run_id, judge)
    return result, verdict
