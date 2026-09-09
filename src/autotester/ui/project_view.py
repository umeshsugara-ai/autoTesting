"""The project page's action card — the operator's control panel for one product.

Split out of `app.py` when that file crossed its 300-line cap. It sits beside
`case_form.py`, `crawl_view.py` and `env_editor.py`, which are the same idea:
`app.py` owns routes, these own the markup a route renders.
"""

from __future__ import annotations

from autotester.ui import theme


def _actions_card(safe_slug: str, run_button: str, case_count: int) -> str:
    """The project's action row, plus — when it has no cases yet — a prompt
    saying what to do next. AT-057: a project with zero cases can run nothing,
    so a disabled Run button on its own was a dead end for a non-technical
    user, with no route anywhere to add the case that would fix it."""
    card = theme.card(
        "<p class='subtitle' style='margin-bottom:1rem'>Manage this project.</p>"
        "<div class='card-actions'>"
        f"{run_button}"
        f"<a class='btn' href='/projects/{safe_slug}/cases'>🧪 Cases</a>"
        f"<a class='btn' href='/projects/{safe_slug}/cases/new'>+ Add case</a>"
        f"<a class='btn' href='/projects/{safe_slug}/env'>🔑 Credentials</a>"
        f"<a class='btn' href='/projects/{safe_slug}/report'>📋 Latest report</a>"
        f"<a class='btn' href='/projects/{safe_slug}/flow-diagram'>🌳 Flow diagram</a>"
        f"<a class='btn' href='/projects/{safe_slug}/crawls'>🕸 Crawls</a>"
        f"<a class='btn' href='/projects/{safe_slug}/edit'>⚙ Project settings</a>"
        "<a class='btn' href='/live'>▶ Watch live</a>"
        "</div>",
        title="Actions",
    )
    if case_count:
        return card
    return theme.empty_state(
        "🧪",
        "No cases yet — nothing can run until this project has at least one. "
        "A case is one claim about the product, checked in a real browser.",
        f"<a class='btn btn-primary' href='/projects/{safe_slug}/cases/new'>"
        "+ Add the first case</a> "
        # AT-241: hand-writing cases was the ONLY remedy offered here, which made
        # the product's own generator invisible to the operator and T-100's
        # "onboard without touching the CLI" false. The learning route is the
        # other half of the way out of a cold start.
        f"<a class='btn' href='/projects/{safe_slug}/flowspec'>"
        "Teach it from a recording</a>",
    ) + card
