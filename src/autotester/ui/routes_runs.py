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
from autotester.schema.enums import Action
from autotester.schema.project import Project
from autotester.schema.run import RawResult, Run
from autotester.schema.verdict import Verdict
from autotester.stages.run_case_pipeline import run_and_grade_case
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
        return run_and_grade_case(case, session, judge, run_id, store)
    finally:
        session.close()


@router.post("/projects/{slug}/run")
def trigger_run(slug: str) -> RedirectResponse:
    """A real, synchronous run: the request waits for the browser to finish
    every case before redirecting to the report (RU1-RU4 — v1's honest
    boundary, no background job queue). Calls the exact same
    `run_and_grade_case` (stages/run_case_pipeline.py) a CLI script would."""
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
    run_id = f"run-{ulid()}"
    run_dir = paths.run_dir(run_id)
    entry_flags = [_is_entry_case(c, project) for c in cases]

    session: BrowserSession | None = None
    if not all(entry_flags):
        session = BrowserSession(project, secrets, run_dir, paths)
        session.start()
    try:
        for case, is_entry in zip(cases, entry_flags, strict=True):
            if is_entry:
                result, verdict = _run_entry_case(
                    case, project, secrets, run_dir, slug, judge, run_id, store
                )
            else:
                assert session is not None
                result, verdict = run_and_grade_case(case, session, judge, run_id, store)
            store.save_result(run_id, result)
            store.save_verdict(run_id, verdict)
    finally:
        if session is not None:
            session.close()
    store.save_run(Run(id=run_id, project=slug, case_ids=[c.id for c in cases]))
    return RedirectResponse(f"/projects/{slug}/report", status_code=303)
