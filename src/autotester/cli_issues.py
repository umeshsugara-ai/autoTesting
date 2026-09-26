"""`autotester issues` — turn an analysis into the sheet a human tester reads.

AT-220. `stages/issues.py::derive_issues` and `stages/analyze_video.py::analyze`
were both built, checker-PASSed, and had **no caller anywhere under `src/`**. Two
units shipped with no way to run them, and the scorer's refusal message pointed
at `autotester issues derive`, a command that did not exist — so the one message
telling a human how to proceed named a dead end.

Separate from `cli_video.py` because that file is near its line budget and these
commands drive a different stage, which is the same reason `cli_video.py` is
separate from `cli.py`.
"""

from __future__ import annotations

from pathlib import Path

import typer

from autotester.schema.enums import Action
from autotester.schema.flowspec import ExpectedState, Step
from autotester.stages.issues import derive_issues, export_issues_excel, pin_issue_as_case
from autotester.store.project_store import ProjectStore

app = typer.Typer(help="Issues derived from a recording — the tester's sheet.")


def _sources_with_analysis(store: ProjectStore) -> list:
    return [s for s in store.list_sources() if store.load_analysis(s.id) is not None]


@app.command("derive")
def derive_cmd(
    project: str = typer.Argument(..., help="project slug"),
    source_id: str = typer.Option(None, "--source",
                                  help="one source; default is every analysed one"),
) -> None:
    """Turn each analysed recording into Issue rows. Idempotent on content."""
    store = ProjectStore(project)
    sources = ([s for s in store.list_sources() if s.id == source_id] if source_id
               else _sources_with_analysis(store))
    if not sources:
        typer.secho(
            f"{project}: no analysed source to derive from. Run `autotester ingest analyze "
            f"{project} <source-id>` first — `autotester ingest list` shows the sources.",
            fg=typer.colors.RED)
        raise typer.Exit(2)

    added = 0
    for source in sources:
        analysis = store.load_analysis(source.id)
        if analysis is None:
            typer.secho(f"  {source.id}: no analysis — skipped", fg=typer.colors.YELLOW)
            continue
        for issue in derive_issues(analysis, source, project):
            before = len(store.list_issues())
            store.add_issue(issue)
            added += len(store.list_issues()) - before

    typer.secho(f"{project}: {added} new issue(s); {len(store.list_issues())} total",
                fg=typer.colors.GREEN)


@app.command("list")
def list_issues_cmd(project: str = typer.Argument(..., help="project slug")) -> None:
    """Every issue derived for this project."""
    issues = ProjectStore(project).list_issues()
    if not issues:
        typer.secho(f"{project}: no issues yet — try `autotester issues derive {project}`.",
                    fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    for issue in sorted(issues, key=lambda i: (i.recording_label, i.at_s)):
        minutes, seconds = divmod(round(issue.at_s), 60)
        typer.echo(f"  {issue.severity.value}  {minutes:02d}:{seconds:02d}  "
                   f"{issue.recording_label[:28]:28s}  {issue.title[:70]}")


def _parse_step(order: int, raw: str) -> Step:
    """`action:target[:value[:expect]]` — the CLI's compact form of one confirmed
    repro step. Never a guess: the caller types exactly what they just verified
    reproduces the bug, same discipline `pin_issue_as_case` documents for its
    `steps` argument."""
    parts = raw.split(":", 3)
    if len(parts) < 2:
        raise ValueError(
            f"--step '{raw}' must look like 'action:target[:value[:expect]]'"
        )
    action_raw, target, *rest = parts
    try:
        action = Action(action_raw)
    except ValueError as exc:
        known = ", ".join(a.value for a in Action)
        raise ValueError(f"--step '{raw}': '{action_raw}' is not one of {known}") from exc
    value = rest[0].strip() or None if rest else None
    expect = rest[1].strip() if len(rest) > 1 else ""
    expected = ExpectedState(visible_text=[expect]) if expect else ExpectedState()
    return Step(order=order, action=action, target=target.strip(), value=value, expected=expected)


@app.command("pin")
def pin_cmd(
    project: str = typer.Argument(..., help="project slug"),
    issue_id: str = typer.Argument(..., help="issue id (see `issues list`)"),
    step: list[str] = typer.Option(
        None, "--step",
        help="one confirmed repro step, 'action:target[:value[:expect]]'. Repeat "
             "in order -- e.g. --step navigate:/signup --step click:#submit",
    ),
) -> None:
    """AT-597: pin a confirmed issue as a regression case (T-184/AT-585) — the
    CLI's entry point to `stages/issues.py::pin_issue_as_case`, alongside the
    issues page's 'Pin as regression case' action. Steps are never guessed:
    pass exactly the reproduction steps you confirmed yourself."""
    store = ProjectStore(project)
    issue = next((i for i in store.list_issues() if i.id == issue_id), None)
    if issue is None:
        typer.secho(f"{project}: no issue '{issue_id}' -- try `autotester issues list {project}`.",
                    fg=typer.colors.RED)
        raise typer.Exit(2)
    if not step:
        typer.secho(
            f"{project}: pinning needs at least one confirmed --step "
            "('action:target[:value[:expect]]') -- steps are never guessed.",
            fg=typer.colors.RED)
        raise typer.Exit(2)
    try:
        steps = [_parse_step(i + 1, raw) for i, raw in enumerate(step)]
    except ValueError as exc:
        typer.secho(f"{project}: {exc}", fg=typer.colors.RED)
        raise typer.Exit(2) from exc

    case = pin_issue_as_case(issue, flow_id="manual", steps=steps, project=project)
    if store.has_case(case.id):
        typer.secho(f"{project}: already pinned as case {case.id} -- nothing to do.",
                    fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    store.add_case(case)
    typer.secho(f"{project}: pinned '{issue.title}' as regression case {case.id}",
                fg=typer.colors.GREEN)


@app.command("export")
def export_cmd(
    project: str = typer.Argument(..., help="project slug"),
    out: Path = typer.Option(None, "--out", help="where to write the workbook"),
) -> None:
    """Write the issues as the 13-column workbook a tester can open beside theirs."""
    store = ProjectStore(project)
    issues = store.list_issues()
    if not issues:
        typer.secho(f"{project}: nothing to export — try `autotester issues derive {project}`.",
                    fg=typer.colors.RED)
        raise typer.Exit(2)
    target = out or (store.paths.dir / "issues.xlsx")
    export_issues_excel(issues, target)
    typer.secho(f"{project}: {len(issues)} issue(s) -> {target}", fg=typer.colors.GREEN)
