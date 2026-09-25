"""Trigger a real run. Contract: qa/contracts/ui-run.md RU1-RU4. Run-history
and report views live in `ui/routes_report.py`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.ids import ulid
from autotester.core.paths import ProjectPaths
from autotester.providers.langchain_fallback import LangChainFallbackProvider
from autotester.schema.case import Case
from autotester.schema.enums import Action, Outcome
from autotester.schema.project import Project
from autotester.schema.run import RawResult, Run
from autotester.schema.run_state import StageCheckpoint, StageName
from autotester.schema.verdict import Verdict
from autotester.stages.coverage import diff_coverage, queue_requests
from autotester.stages.orchestrate import StageContext
from autotester.stages.parallel_run import (
    ParallelPlan,
    default_session_factory,
    plan_parallel_run,
    run_cases,
)
from autotester.stages.run_case_pipeline import (
    grade_errored_result,
    run_and_grade_case_resilient,
)
from autotester.store.project_store import ProjectStore
from autotester.ui.helpers import _load_project_or_404

router = APIRouter()


def _is_entry_case(case: Case, project: Project) -> bool:
    """True when this case's first step navigates to the project's own
    declared entry screen (`base_url`) -- e.g. a sign-in page. Such a case is
    testing the entry screen itself, which only means something from a
    genuinely logged-out state; the shared, persistently-authenticated
    profile every other case reuses would make the entry screen never
    appear (AT-044 -- exactly the staleness bug already fixed once for
    `scripts/run_pathlynks_first_cases.py`, but never generalized into this
    pipeline)."""
    return bool(case.steps) and case.steps[0].action is Action.NAVIGATE \
        and case.steps[0].target == project.base_url


def _run_and_grade_resilient(
    case: Case, session: BrowserSession, judge: LangChainFallbackProvider, run_id: str,
    store: ProjectStore,
) -> tuple[RawResult, Verdict]:
    """Never let one case take the whole run down (AT-574). `run_and_grade_
    case_resilient` already keeps a real COMPLETED result when only grading
    fails after execution (AT-573); this adds the outer guard for an
    exception in `run_case` itself, or anything else the resilient wrapper
    doesn't catch -- the same shape `stages/parallel_run.py::_run_one`
    already applies on the parallel path, expressed here for callers that
    run one case at a time (the serial loop and the shared dedicated-profile
    entry-case session) so every case still gets a saved result+verdict
    through the exact `grade_errored_result` path AT-568 built, and the
    caller never sees an exception to propagate into a 500."""
    try:
        return run_and_grade_case_resilient(case, session, judge, run_id, store)
    except Exception as exc:  # AT-574: reported as this case's own ERRORED result
        result = RawResult(case_id=case.id, outcome=Outcome.ERRORED,
                            error=f"{type(exc).__name__}: {exc}")
        verdict = grade_errored_result(case, result, judge, run_id, store)
        return result, verdict


def _run_entry_case(
    case: Case, project: Project, secrets: SecretStore, run_dir: Path, slug: str,
    judge: LangChainFallbackProvider, run_id: str, store: ProjectStore,
) -> tuple[RawResult, Verdict]:
    """A dedicated, wiped-before-every-run profile so an entry-screen case is
    always exercised from a genuinely logged-out state -- order-independent
    (no "run this kind last" ordering hack needed) and cross-run-independent
    (no stale login survives from a previous run)."""
    entry_paths = ProjectPaths(f"{slug}-entry-test")
    shutil.rmtree(entry_paths.profile_dir, ignore_errors=True)
    session = BrowserSession(project, secrets, run_dir, entry_paths)
    session.start()
    try:
        return _run_and_grade_resilient(case, session, judge, run_id, store)
    finally:
        session.close()


def _require_declared_values(project: Project, secrets: SecretStore, slug: str) -> None:
    """Refuse the run up front when a declared credential has no value yet.

    The UI path loads secrets with `strict=False`, so a missing value used to
    surface only when a step tried to type it — as `BLOCKED_HITL`, mid-run,
    after a browser had already been launched. Name the key instead, and say
    where to fix it."""
    missing = [ref.key for ref in project.secrets if not secrets.has_value(ref.key)]
    if missing:
        raise HTTPException(400, (
            f"{', '.join(missing)} has no value yet. Enter it on the project's "
            f"Credentials page (/projects/{slug}/env) before running."
            if len(missing) == 1 else
            f"these credentials have no value yet: {', '.join(missing)}. Enter them on the "
            f"project's Credentials page (/projects/{slug}/env) before running."
        ))


def _run_cases_serially(
    cases: list[Case], entry_flags: list[bool], project: Project, secrets: SecretStore,
    run_dir: Path, paths: ProjectPaths, slug: str, judge: LangChainFallbackProvider,
    run_id: str, store: ProjectStore,
) -> None:
    """`plan.n <= 1` (the default, AT-562/PR1): one shared session reused
    across every non-entry case (login continuity across the whole run), one
    dedicated wiped profile per entry case (AT-044). Not routed through
    `run_cases`: that module's contract starts and closes one session per
    case (PR2's isolation), which would tear down this shared session after
    the first case.

    AT-574: each case goes through `_run_and_grade_resilient` -- before this
    fix, a grader/provider exception, or a `run_case` crash, propagated
    straight out of this loop, 500ing `trigger_run` before the remaining
    cases ran or the `Run` record was saved. Now a crash is reported as that
    case's own result+verdict and the loop, and the run, continue.

    AT-576: every entry case runs to completion first -- its own dedicated
    session, started and closed by `_run_entry_case` -- BEFORE the shared
    session below ever starts (same order `_run_cases_in_parallel` uses).
    Starting the shared session first and only THEN hitting an entry case
    used to start a SECOND sync Playwright driver on this thread while the
    shared one was still live -- Playwright raises "Sync API inside the
    asyncio loop" the moment that happens, 500ing the whole run. Entry
    cases first, one shared session started once, never nests two."""
    for case, is_entry in zip(cases, entry_flags, strict=True):
        if not is_entry:
            continue
        result, verdict = _run_entry_case(case, project, secrets, run_dir, slug, judge, run_id,
                                          store)
        store.save_result(run_id, result)
        store.save_verdict(run_id, verdict)

    normal_cases = [c for c, is_entry in zip(cases, entry_flags, strict=True) if not is_entry]
    if not normal_cases:
        return
    session = BrowserSession(project, secrets, run_dir, paths)
    session.start()
    try:
        for case in normal_cases:
            result, verdict = _run_and_grade_resilient(case, session, judge, run_id, store)
            store.save_result(run_id, result)
            store.save_verdict(run_id, verdict)
    finally:
        session.close()


def _run_cases_in_parallel(
    cases: list[Case], entry_flags: list[bool], plan: ParallelPlan, project: Project,
    secrets: SecretStore, run_dir: Path, slug: str, judge: LangChainFallbackProvider,
    run_id: str, store: ProjectStore,
) -> None:
    """`plan.n > 1` (T-173/AT-562): fan the non-entry cases out through the
    real `stages.parallel_run.run_cases` at the planned width, each in its
    own isolated browser context (PR2). Entry cases keep their dedicated
    wiped profile (AT-044) and always run serially, before the fan-out — an
    entry-screen assertion is about one logged-out state, not something
    concurrency helps."""
    entry_cases = [c for c, is_entry in zip(cases, entry_flags, strict=True) if is_entry]
    normal_cases = [c for c, is_entry in zip(cases, entry_flags, strict=True) if not is_entry]

    for case in entry_cases:
        result, verdict = _run_entry_case(
            case, project, secrets, run_dir, slug, judge, run_id, store
        )
        store.save_result(run_id, result)
        store.save_verdict(run_id, verdict)

    if not normal_cases:
        return
    case_by_id = {c.id: c for c in normal_cases}
    verdicts: dict[str, Verdict] = {}

    def _run_and_grade(case: Case, session: object) -> RawResult:
        # AT-573: run_and_grade_case_resilient captures the real RawResult
        # BEFORE grading, so a grader/provider exception (caught inside it)
        # never discards a COMPLETED run's evidence -- it only downgrades
        # the verdict to INCONCLUSIVE, naming the grader failure.
        result, verdict = run_and_grade_case_resilient(case, session, judge, run_id, store)
        verdicts[case.id] = verdict
        return result

    session_factory = default_session_factory(project, secrets, run_dir)
    for result in run_cases(normal_cases, plan, session_factory, _run_and_grade):
        # AT-568/PR6: a session_factory crash, or any exception BEFORE
        # run_and_grade_case_resilient captures its own result, means
        # `_run_and_grade` above never ran to completion for this case, so
        # `verdicts` has no entry for it — `run_cases` still reports the
        # case as its own ERRORED RawResult (PR6), and that ERRORED outcome
        # is always safe to grade directly (grade_errored_result never
        # calls the judge for it).
        verdict = verdicts.get(result.case_id)
        if verdict is None:
            verdict = grade_errored_result(
                case_by_id[result.case_id], result, judge, run_id, store
            )
        store.save_result(run_id, result)
        store.save_verdict(run_id, verdict)


def _execute_with_trace(
    store: ProjectStore, run_id: str, secrets: SecretStore, project: Project,
    cases: list[Case], entry_flags: list[bool], run_dir: Path, paths: ProjectPaths,
    slug: str, judge: LangChainFallbackProvider,
) -> ParallelPlan:
    """AT-562/AT-564: build this run's `StageContext` with the project's real
    `SecretStore` (RT6 — a real, redacted `trace.jsonl`), attach it to the
    judge so its LLM calls join that trace (RT4/RT5), decide this run's width
    (PR1), execute the cases at that width, and record one EXECUTE stage span
    covering the whole batch."""
    ctx = StageContext(store=store, run_id=run_id, secrets=secrets)
    judge.trace = ctx.trace
    plan = plan_parallel_run(project)

    started = ctx.clock()
    if plan.n > 1:
        _run_cases_in_parallel(
            cases, entry_flags, plan, project, secrets, run_dir, slug, judge, run_id, store
        )
    else:
        _run_cases_serially(
            cases, entry_flags, project, secrets, run_dir, paths, slug, judge, run_id, store
        )
    assert ctx.trace is not None
    ctx.trace.record_stage(StageCheckpoint(
        stage=StageName.EXECUTE, status="done", started=started, finished=ctx.clock(),
    ))
    return plan


@router.post("/projects/{slug}/run")
def trigger_run(slug: str) -> RedirectResponse:
    """A real, synchronous run: the request waits for the browser to finish
    every case before redirecting to the report (RU1-RU4 — v1's honest
    boundary, no background job queue). Runs every case through the same
    resilient pipeline (stages/run_case_pipeline.py) whether serial or
    parallel (AT-574) -- a CLI script that wants the un-guarded, self-grading
    path still calls `run_and_grade_case` directly.

    AT-562/AT-564: this is the live entry point wired to the T-172/T-173
    machinery those goal-coverage gaps named -- see `_execute_with_trace`."""
    store, project = _load_project_or_404(slug)
    cases = store.list_cases()
    if not cases:
        raise HTTPException(400, f"project '{slug}' has no cases to run")
    judge = LangChainFallbackProvider()
    if not judge.available():
        raise HTTPException(
            400, "no AI provider is configured (set an API key in .env) -- cannot grade a run"
        )
    paths = ProjectPaths(slug)
    secrets = SecretStore.load(project, paths.env_file, strict=False)
    _require_declared_values(project, secrets, slug)
    run_id = f"run-{ulid()}"
    run_dir = paths.run_dir(run_id)
    entry_flags = [_is_entry_case(c, project) for c in cases]

    plan = _execute_with_trace(
        store, run_id, secrets, project, cases, entry_flags, run_dir, paths, slug, judge
    )

    store.save_run(Run(
        id=run_id, project=slug, case_ids=[c.id for c in cases],
        parallel_n=plan.n, parallel_bound_by=plan.bound_by,
    ))
    _ask_for_what_it_did_not_recognise(store, run_id)
    return RedirectResponse(f"/projects/{slug}/report", status_code=303)


def _ask_for_what_it_did_not_recognise(store: ProjectStore, run_id: str) -> None:
    """Turn this run's coverage gaps into video requests.

    AT-240: `diff_coverage`, `request_for` and `add_request` were each written,
    each tested, and each called from nothing -- so across four real projects
    not one `VideoRequest` had ever been created and the north star's "when it
    meets a screen it does not know, it asks the human for a video instead of
    guessing" had never once happened. A loop whose last link is missing is not
    a slow loop, it is an open one.

    Deliberately after `save_run`: a request is about a run that HAPPENED, and
    failing to ask must never lose the run itself."""
    spec = store.load_flowspec()
    if spec is None:
        return                      # nothing learned yet -> nothing is "unknown" (V2)
    results = store.load_results(run_id)
    queue_requests(store, diff_coverage(spec, results))
