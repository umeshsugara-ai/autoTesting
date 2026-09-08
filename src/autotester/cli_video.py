"""`autotester ingest` — register a recording and learn a FlowSpec from it.

Separate from `cli.py` for the same reason `cli_crawl.py` is: that file is at
its line budget, and a stage's commands belong beside the stage they drive.
"""

from __future__ import annotations

from pathlib import Path

import typer

from autotester import providers
from autotester.core.paths import RepoDocs
from autotester.schema.observation import VisionOptions
from autotester.stages.ingest import (
    FlowSpecApproved,
    SourceChanged,
    ingest_video,
    load_sidecar,
    persist_ingest,
    register_source,
)
from autotester.store.project_store import ProjectStore

app = typer.Typer(help="Learn a product's screens and flows from a screen recording.")


@app.command("register")
def register_cmd(
    project: str = typer.Argument(..., help="project slug"),
    path: str = typer.Argument(..., help="path to the recording"),
    label: str = typer.Option(None, "--label", help="who recorded it and what it shows"),
    recorded_on: str = typer.Option(None, "--recorded-on", help="ISO date, e.g. 2026-08-18"),
) -> None:
    """Record a video as a Source. Idempotent on content — the same file twice
    is one source, not two."""
    store = ProjectStore(project)
    try:
        source = register_source(store, Path(path), label=label,
                                 recorded_on=recorded_on)
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(2) from None
    typer.secho(f"{source.id}  {source.label or '(no label)'}  sha256={source.sha256[:12]}",
                fg=typer.colors.GREEN)


@app.command("list")
def list_cmd(project: str = typer.Argument(..., help="project slug")) -> None:
    """Every source registered for this project."""
    sources = ProjectStore(project).list_sources()
    if not sources:
        typer.secho(f"{project} has no sources yet — `autotester ingest register` adds one.",
                    fg=typer.colors.YELLOW)
        return
    for source in sources:
        typer.echo(f"{source.id}  {source.kind.value:6}  {source.recorded_on or '—':10}  "
                   f"{source.label or Path(source.path or '').name}")


@app.command("run")
def run_cmd(
    project: str = typer.Argument(..., help="project slug"),
    source_id: str = typer.Argument(..., help="a source id from `ingest list`"),
    provider: str = typer.Option("gemini", "--provider", help="'mock' runs without a model"),
    model: str = typer.Option(None, "--model", help="override the provider's default model"),
    replace: bool = typer.Option(False, "--replace",
                                 help="overwrite an APPROVED FlowSpec, discarding its review"),
) -> None:
    """Watch one source and write the FlowSpec it produces."""
    store = ProjectStore(project)
    source = next((s for s in store.list_sources() if s.id == source_id), None)
    if source is None:
        typer.secho(f"{project} has no source {source_id} — try `autotester ingest list`.",
                    fg=typer.colors.RED)
        raise typer.Exit(2)

    prov = providers.get(provider, **({"model": model} if model else {}))
    try:
        spec = ingest_video(source, project, prov, RepoDocs(),
                            transcript=load_sidecar(source), options=VisionOptions())
    except SourceChanged as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(2) from None
    try:
        persist_ingest(store, spec, replace=replace)
    except FlowSpecApproved as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        raise typer.Exit(2) from None
    typer.secho(
        f"{project}: {len(spec.screens)} screens, {len(spec.flows)} flows from "
        f"{source.label or source.id} (review status {spec.review.status.value})",
        fg=typer.colors.GREEN,
    )
