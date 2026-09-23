"""Render a `PortalPersona` as `knowledge.md` — a human-readable VIEW of the
JSON, regenerated on every update (PP4). Never a second source of truth: every
line here is projected from the persona, and nothing is authored that the JSON
does not hold.
"""

from __future__ import annotations

from autotester.schema.portal_persona import PortalPersona


def _profile_section(persona: PortalPersona) -> list[str]:
    p = persona.profile
    lines = [f"# {p.name or persona.project} — portal persona", ""]
    if p.base_url:
        lines.append(f"- **Base URL:** {p.base_url}")
    if p.overview:
        lines.append(f"- **What it is:** {p.overview}")
    lines.append("")
    return lines


def _auth_section(persona: PortalPersona) -> list[str]:
    auth = persona.auth
    lines = ["## Auth", ""]
    if not auth.required and not auth.fields:
        lines += ["No authentication learned yet.", ""]
        return lines
    lines.append(f"- **Required:** {'yes' if auth.required else 'no'}")
    if auth.login_screen:
        lines.append(f"- **Login screen:** {auth.login_screen}")
    if auth.domains:
        lines.append(f"- **Scoped to:** {', '.join(auth.domains)}")
    for field in auth.fields:
        key = f" → `{{{{SECRET:{field.secret_key}}}}}`" if field.secret_key else ""
        lines.append(f"- field `{field.name}` ({field.type}){key}")
    lines.append("")
    return lines


def _screens_section(persona: PortalPersona) -> list[str]:
    lines = [f"## Screens ({len(persona.screens)})", ""]
    for screen in persona.screens:
        url = f" — `{screen.url_template}`" if screen.url_template else ""
        lines.append(f"### {screen.name}{url}")
        if screen.purpose:
            lines.append(f"{screen.purpose}")
        if screen.controls:
            lines.append(f"- Controls: {', '.join(screen.controls)}")
        if screen.screenshot_ref:
            lines.append(f"- Screenshot: `{screen.screenshot_ref}`")
        lines.append("")
    return lines


def _transitions_section(persona: PortalPersona) -> list[str]:
    if not persona.transitions:
        return []
    lines = [f"## Transitions ({len(persona.transitions)})", ""]
    for t in persona.transitions:
        control = f" via {t.control}" if t.control else ""
        lines.append(f"- {t.from_screen} —[{t.action}{control}]→ {t.to_screen or '?'}")
    lines.append("")
    return lines


def _flows_section(persona: PortalPersona) -> list[str]:
    if not persona.taught_flows:
        return []
    lines = [f"## Taught flows ({len(persona.taught_flows)})", ""]
    for flow in persona.taught_flows:
        auth = " (needs auth)" if flow.requires_auth else ""
        lines.append(f"- **{flow.name}**{auth} — enters at `{flow.entry_screen}`")
        lines.append(
            f"  - Quick Re-Run: `{flow.run_ref.project}/{flow.run_ref.flow_id}`"
            f" @ `{flow.run_ref.entry_screen}`"
        )
    lines.append("")
    return lines


def _gotchas_section(persona: PortalPersona) -> list[str]:
    if not persona.gotchas:
        return []
    lines = ["## Gotchas", ""]
    for g in persona.gotchas:
        where = f"[{g.screen}] " if g.screen else ""
        lines.append(f"- {where}{g.note}")
    lines.append("")
    return lines


def _history_section(persona: PortalPersona) -> list[str]:
    if not persona.history:
        return []
    lines = ["## History", ""]
    for rev in persona.history:
        lines.append(f"- **{rev.at}** — {rev.summary}")
    lines.append("")
    return lines


def render_knowledge(persona: PortalPersona) -> str:
    """The whole `knowledge.md`, projected from the persona (PP4)."""
    lines: list[str] = []
    lines += _profile_section(persona)
    lines += _auth_section(persona)
    lines += _screens_section(persona)
    lines += _transitions_section(persona)
    lines += _flows_section(persona)
    lines += _gotchas_section(persona)
    lines += _history_section(persona)
    return "\n".join(lines).rstrip() + "\n"
