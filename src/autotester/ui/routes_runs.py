"""Trigger a real run and view its results. Contract: qa/contracts/ui-run.md
RU1-RU4 (run trigger) and qa/contracts/ui.md U4 (run/report views).
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.ids import ulid
from autotester.core.paths import ProjectPaths
from autotester.providers.langchain_fallback import LangChainFallbackProvider
from autotester.schema.run import Run
from autotester.stages.run_case_pipeline import run_and_grade_case
from autotester.store.project_store import ProjectStore
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404, _require_safe_id

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


@router.get("/projects/{slug}/runs/{run_id}", response_class=HTMLResponse)
def run_view(slug: str, run_id: str) -> str:
    store, _project = _load_project_or_404(slug)
    _require_safe_id(run_id, "run_id")
    safe_slug = escape(slug)
    safe_run_id = escape(run_id)
    verdicts = {v.case_id: v for v in store.load_verdicts(run_id)}

    def _result_cell(case_id: str) -> str:
        return theme.badge(escape(verdicts[case_id].result.value)) if case_id in verdicts else "-"

    results = store.load_results(run_id)
    rows = "".join(
        f"<tr><td><code>{escape(r.case_id)}</code></td><td>{escape(r.outcome.value)}</td>"
        f"<td>{_result_cell(r.case_id)}</td></tr>"
        for r in results
    )
    table = (theme.empty_state("📭", "No case results in this run yet.") if not results else
             f"<table><tr><th>Case</th><th>Outcome</th><th>Result</th></tr>{rows}</table>")
    body = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Run</div>"
        f"<h1>Run <code>{safe_run_id}</code></h1>"
        f"{theme.card(table)}"
    )
    return theme.page(f"Run {safe_run_id}", body)


@router.get("/projects/{slug}/report", response_class=HTMLResponse)
def report(slug: str) -> str:
    _store, _project = _load_project_or_404(slug)
    safe_slug = escape(slug)
    breadcrumb = (
        f"<div class='breadcrumb'><a href='/'>Projects</a> / "
        f"<a href='/projects/{safe_slug}'>{safe_slug}</a> / Report</div>"
    )
    paths = ProjectPaths(slug)
    run_ids = sorted(p.name for p in paths.runs_dir.iterdir() if p.is_dir()) \
        if paths.runs_dir.exists() else []
    if not run_ids:
        body = breadcrumb + "<h1>Report</h1>" + theme.empty_state(
            "📋", "no runs yet — run a case against this project to see a report here.",
        )
        return theme.page("Report", body)
    store = ProjectStore(slug)
    counts: dict[str, int] = {}
    for verdict in store.load_verdicts(run_ids[-1]):
        counts[verdict.result.value] = counts.get(verdict.result.value, 0) + 1
    stats = "<div class='stat-row'>" + "".join(
        theme.stat(str(v), theme.badge(escape(k))) for k, v in counts.items()
    ) + "</div>"
    safe_run_id = escape(run_ids[-1])
    body = (
        breadcrumb + "<h1>Latest report</h1>"
        f"<p class='subtitle'>Run <code>{safe_run_id}</code> · "
        f"<a href='/projects/{safe_slug}/runs/{safe_run_id}'>view case-by-case</a></p>"
        f"{stats}"
    )
    return theme.page(f"Report — {safe_run_id}", body)
