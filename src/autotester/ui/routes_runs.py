"""Trigger a real run. Contract: qa/contracts/ui-run.md RU1-RU4. Run-history
and report views live in `ui/routes_report.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.ids import ulid
from autotester.core.paths import ProjectPaths
from autotester.providers.langchain_fallback import LangChainFallbackProvider
from autotester.schema.run import Run
from autotester.stages.run_case_pipeline import run_and_grade_case
from autotester.ui.helpers import _load_project_or_404

router = APIRouter()


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
    session = BrowserSession(project, secrets, paths.run_dir(run_id), paths)
    session.start()
    try:
        for case in cases:
            result, verdict = run_and_grade_case(case, session, judge, run_id, store)
            store.save_result(run_id, result)
            store.save_verdict(run_id, verdict)
    finally:
        session.close()
    store.save_run(Run(id=run_id, project=slug, case_ids=[c.id for c in cases]))
    return RedirectResponse(f"/projects/{slug}/report", status_code=303)
