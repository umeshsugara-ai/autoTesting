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
from autotester.schema.base import Provenance
from autotester.schema.case import Case
from autotester.schema.run import RawResult
from autotester.schema.verdict import Criterion, Rubric, Verdict
from autotester.stages.execute import run_case
from autotester.stages.grade import grade
from autotester.store.project_store import ProjectStore

GENERATOR = "stages.run_case_pipeline.default_rubric"


def claim_of(case: Case) -> str:
    """The single sentence a default rubric grades evidence against."""
    return case.rationale or f"the case '{case.title}' completes as its steps describe"


def _rubric_for_claim(claim: str, case_id: str, rubric_id: str) -> Rubric:
    return Rubric(
        id=rubric_id, case_id=case_id,
        criteria=[Criterion(id="c1", text=(
            f"The evidence is consistent with: {claim}. If you cite this as a failure, "
            "use criterion id 'c1' exactly — do not invent a different id."
        ))],
        no_fire=["exact wording of any error message shown by the product"],
        provenance=Provenance(produced_by=GENERATOR, inputs=[case_id], note=claim),
    )


def default_rubric(case: Case, rubric_id: str) -> Rubric:
    """A plain, honest default: pass if the evidence is consistent with the
    case's own stated rationale. Not a substitute for a hand-tuned rubric
    when one exists — only the fallback so every case is gradeable at all.

    Stamps `provenance.note` with the exact claim it was built from, which is
    what makes `is_stale_default` below possible (AT-059)."""
    return _rubric_for_claim(claim_of(case), case.id, rubric_id)


def is_stale_default(rubric: Rubric, case: Case) -> bool:
    """True when `rubric` is an auto-generated rubric, still untouched since it
    was generated, whose claim no longer matches the case's current one.

    AT-059: a rubric is persisted at `rub_<case_id>`, but its claim comes from
    `case.rationale`/`title`, which `Case.compute_id()` deliberately excludes —
    so correcting a case's rationale left the OLD claim grading forever, with no
    invalidation. Observed live: a case whose rationale was fixed still FAILed
    against the stale claim, on a screenshot that plainly showed what it asked
    for, and deleting the file by hand was the only recovery.

    Deliberately conservative on both edges, because a grading contract is not
    something to overwrite on a guess:
    - No provenance, or provenance from anything but this generator → treated as
      hand-authored and never touched. That includes rubrics written before this
      stamping existed: they are indistinguishable from hand-written, so they
      keep their claim.
    - Provenance from this generator but the criteria no longer match what it
      would have produced for its own recorded claim → a human edited it since,
      so it is hand-tuned now and is never touched.
    """
    provenance = rubric.provenance
    if provenance is None or provenance.produced_by != GENERATOR:
        return False
    recorded = provenance.note or ""
    if recorded == claim_of(case):
        return False
    untouched = _rubric_for_claim(recorded, rubric.case_id or case.id, rubric.id)
    return rubric.criteria == untouched.criteria and rubric.no_fire == untouched.no_fire


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
    if rubric is None or is_stale_default(rubric, case):
        rubric = default_rubric(case, rubric_id)
        store.save_rubric(rubric)
    verdict = grade(rubric, result, run_id, judge, run_dir=store.paths.run_dir(run_id),
                    secrets=session.secrets)
    return result, verdict
