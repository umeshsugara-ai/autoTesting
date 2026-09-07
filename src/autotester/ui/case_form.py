"""Rendering the add-a-case form. Contract: qa/contracts/ui.md.

Split out of `routes_cases.py` when the credential picker pushed that module
past doctor's 300-line cap — the routes keep the request handling, this keeps
the HTML the form is built from.
"""

from __future__ import annotations

from html import escape

from autotester.schema.enums import Action
from autotester.schema.project import Project

# Enough rows for a real multi-step flow without a JS row-adder; blank rows are
# dropped, so this is a ceiling, never a requirement.
STEP_ROWS = 5


def _options(values: list[str], selected: str) -> str:
    return "".join(
        f"<option value='{escape(v)}'{' selected' if v == selected else ''}>{escape(v)}</option>"
        for v in values
    )


def _credential_datalist(project: Project) -> str:
    """The declared keys, offered as autocomplete on every value box, so the
    safe thing to type is the easy thing to type. Plain `<datalist>` — no JS,
    per ui.md's no-fire list. Empty when the project declares nothing, in which
    case the box behaves exactly as before."""
    if not project.secrets:
        return ""
    options = "".join(
        f"<option value='{{{{SECRET:{escape(ref.key)}}}}}'>"
        for ref in project.secrets
    )
    return f"<datalist id='declared-credentials'>{options}</datalist>"


def _step_row(index: int, action: str, target: str, has_secrets: bool) -> str:
    """One step's four inputs. `action`/`target` prefill row 0 with the project's
    own base_url, so the fastest useful case — "does the front door still load" —
    is one title away."""
    actions = _options([a.value for a in Action], action)
    picker = " list='declared-credentials'" if has_secrets else ""
    return (
        "<tr>"
        f"<td class='step-n'>{index + 1}</td>"
        f"<td><select name='step_action'>{actions}</select></td>"
        f"<td><input name='step_target' value='{escape(target)}' "
        "placeholder='https://… or a button&#39;s visible label'></td>"
        f"<td><input name='step_value'{picker} "
        "placeholder='text to type (optional)'></td>"
        "<td><input name='step_expected' placeholder='text that must appear (optional)'></td>"
        "</tr>"
    )
