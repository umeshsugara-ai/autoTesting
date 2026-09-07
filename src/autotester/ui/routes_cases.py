"""Create a test case from the UI. Contract: qa/contracts/ui.md (U1-U5).

AT-057: onboarding used to dead-end — a new project had zero cases, its Run
button was permanently disabled, and cases were creatable only from Python
(`ProjectStore.add_case`) or from `stages/expand.py` off a reviewed FlowSpec
that itself needs an ingested video. Neither is reachable by a non-technical
user, which made "onboard a product and test it without touching the CLI"
(T-100's own goal-task note) false in practice.

Plain server-rendered HTML with a fixed number of step rows — no JS framework
and no HTMX, per ui.md's no-fire list. Blank rows are ignored, so a one-step
smoke test costs one field.
"""

from __future__ import annotations

from html import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester.schema.case import Case
from autotester.schema.enums import KIND_BY_CLASS, Action, CaseClass
from autotester.schema.flowspec import ExpectedState, Step
from autotester.ui import theme
from autotester.ui.helpers import _load_project_or_404

router = APIRouter()

# Enough rows for a real multi-step flow without a JS row-adder; blank rows are
# dropped, so this is a ceiling, never a requirement.
STEP_ROWS = 5


def _options(values: list[str], selected: str) -> str:
    return "".join(
        f"<option value='{escape(v)}'{' selected' if v == selected else ''}>{escape(v)}</option>"
        for v in values
    )


def _step_row(index: int, action: str, target: str) -> str:
    """One step's four inputs. `action`/`target` prefill row 0 with the project's
    own base_url, so the fastest useful case — "does the front door still load" —
    is one title away."""
    actions = _options([a.value for a in Action], action)
    return (
        "<tr>"
        f"<td class='step-n'>{index + 1}</td>"
        f"<td><select name='step_action'>{actions}</select></td>"
        f"<td><input name='step_target' value='{escape(target)}' "
        "placeholder='https://… or a button&#39;s visible label'></td>"
        "<td><input name='step_value' placeholder='text to type (optional)'></td>"
        "<td><input name='step_expected' placeholder='text that must appear (optional)'></td>"
        "</tr>"
    )


@router.get("/projects/{slug}/cases/new", response_class=HTMLResponse)
def new_case_form(slug: str) -> str:
    _store, project = _load_project_or_404(slug)
    safe_slug = escape(slug)
    name = escape(project.name)

    rows = "".join(
        _step_row(i, Action.NAVIGATE.value if i == 0 else Action.CLICK.value,
                  project.base_url if i == 0 else "")
        for i in range(STEP_ROWS)
    )
    table = (
        "<table class='step-table'><tr><th>#</th><th>Action</th><th>Target</th>"
        "<th>Value</th><th>Expect to see</th></tr>"
        f"{rows}</table>"
        "<p class='hint'>Leave a row blank to skip it. A row counts if it has a target "
        "or a value.</p>"
    )
    fields = (
        "<div class='field'><label for='title'>What are you checking?</label>"
        "<input id='title' name='title' required "
        "placeholder='Sign-in page loads and shows the login form'></div>"
        "<div class='field'><label for='case_class'>Kind of check</label>"
        f"<select id='case_class' name='case_class'>"
        f"{_options([c.value for c in CaseClass], CaseClass.HAPPY.value)}</select>"
        "<span class='hint'>happy = the normal path; the others are the worst/edge "
        "cases AutoTester grades against.</span></div>"
        f"{table}"
        "<button class='btn btn-primary' type='submit'>Add case</button>"
    )
    form = (
        f"<form method='post' action='/projects/{safe_slug}/cases'>{fields}</form>"
    )
    body = (
        theme.breadcrumb(("Projects", "/"), (name, f"/projects/{safe_slug}"),
                          ("New case", None))
        + "<h1>Add a case</h1>"
        "<p class='subtitle'>One falsifiable claim about the product — AutoTester runs "
        "these steps in a real browser and grades what it sees.</p>"
        f"{theme.card(form)}"
    )
    return theme.page("New case", body, active_slug=slug)


def _build_steps(
    actions: list[str], targets: list[str], values: list[str], expects: list[str]
) -> list[Step]:
    """Keep only rows a human actually filled in, renumbering from 1 so a skipped
    middle row never leaves a hole in `Step.order`."""
    steps: list[Step] = []
    for action, target, value, expect in zip(actions, targets, values, expects, strict=False):
        if not target.strip() and not value.strip():
            continue
        try:
            parsed = Action(action)
        except ValueError as exc:
            raise HTTPException(400, f"unknown action '{action}'") from exc
        expected = (
            ExpectedState(visible_text=[expect.strip()]) if expect.strip()
            else ExpectedState()
        )
        steps.append(Step(
            order=len(steps) + 1, action=parsed, target=target.strip(),
            value=value.strip() or None, expected=expected,
        ))
    return steps


@router.post("/projects/{slug}/cases")
async def create_case(slug: str, request: Request) -> RedirectResponse:
    """Reads the raw form rather than declaring `list[str] = Form(...)` params:
    the step inputs are repeated fields, and `getlist` is the direct way to read
    them without a mutable default in the signature (ruff B008)."""
    store, _project = _load_project_or_404(slug)
    form = await request.form()
    title = str(form.get("title", ""))
    case_class = str(form.get("case_class", ""))
    if not title.strip():
        raise HTTPException(400, "a case needs a title")
    try:
        parsed_class = CaseClass(case_class)
    except ValueError as exc:
        raise HTTPException(400, f"unknown case class '{case_class}'") from exc

    steps = _build_steps(
        [str(v) for v in form.getlist("step_action")],
        [str(v) for v in form.getlist("step_target")],
        [str(v) for v in form.getlist("step_value")],
        [str(v) for v in form.getlist("step_expected")],
    )
    if not steps:
        raise HTTPException(400, "a case needs at least one step")

    store.add_case(Case(
        project=slug,
        flow_id="manual",
        kind=KIND_BY_CLASS[parsed_class],
        case_class=parsed_class,
        title=title.strip(),
        # rationale is NOT provenance: `stages/run_case_pipeline.default_rubric`
        # feeds it to the grader verbatim as the claim to judge the evidence
        # against. An earlier version set "added by hand from the UI" here, and
        # the grader duly went looking for a UI-addition step and FAILed a case
        # whose screenshot plainly showed the very thing it asked for. Left
        # None so the rubric falls back to the user's own title; provenance
        # lives in flow_id="manual".
        rationale=None,
        steps=steps,
    ))
    return RedirectResponse(f"/projects/{slug}", status_code=303)
