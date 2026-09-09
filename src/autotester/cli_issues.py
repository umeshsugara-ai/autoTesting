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

from autotester.stages.issues import derive_issues, export_issues_excel
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
