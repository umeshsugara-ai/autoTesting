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


@app.command("prep")
def media_prep_cmd(
    project: str = typer.Argument(..., help="project slug"),
    source_id: str = typer.Argument(..., help="a source id from `ingest list`"),
    chunk_minutes: float = typer.Option(3.0, "--chunk-minutes"),
    no_whisper: bool = typer.Option(False, "--no-whisper",
                                    help="skip transcription even if it is available"),
) -> None:
    """Probe, chunk and transcribe a recording. RUN THIS ON THE HOST — the
    container has no ffmpeg and no GPU."""
    from autotester.stages import media_prep

    store = ProjectStore(project)
    source = _require_source(store, project, source_id)
    try:
        prep = media_prep.prepare(store, source, chunk_minutes=chunk_minutes,
                                  use_whisper=not no_whisper)
    except (FileNotFoundError, ValueError, media_prep.UnreadableRecording) as exc:
        # AT-166: `UnreadableRecording` is a RuntimeError, so this clause did
        # not catch it and the shipped command answered a deliberate refusal
        # with a raw traceback. I fixed the STAGE last cycle and not the path
        # an operator actually runs -- the same mistake as AT-163, one cycle on.
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(2) from None

    transcript = store.load_transcript(source_id)
    segments = len(transcript.segments) if transcript else 0
    tool = prep.ffmpeg_version or "no ffmpeg — one chunk on the original file"
    typer.secho(
        f"{source_id}: {prep.duration_s:.0f}s, {len(prep.chunks)} chunk(s), "
        f"{segments} narration segment(s) [{tool}]",
        fg=typer.colors.GREEN,
    )


@app.command("frames")
def media_frames_cmd(
    project: str = typer.Argument(..., help="project slug"),
    source_id: str = typer.Argument(..., help="a source id from `ingest list`"),
) -> None:
    """Extract the stills the vision pass named. Needs an analysis on disk."""
    from autotester.stages import media_prep

    store = ProjectStore(project)
    source = _require_source(store, project, source_id)
    analysis = store.load_analysis(source_id)
    if analysis is None:
        # AT-172: this named `autotester ingest analyze`, which does not exist
        # -- that stage is Track A4 and is not built. Pointing an operator at a
        # future command is the same dead end as AT-163, one command over, and
        # it survived three fix cycles spent on exactly that shape. When there
        # is nothing to run, say so instead of inventing something to run.
        typer.secho(
            f"{source_id} has no analysis.json — the analyze stage (Track A4) is not "
            f"built yet, so there are no frames to extract",
            fg=typer.colors.YELLOW)
        raise typer.Exit(2)

    try:
        written = media_prep.extract_frames(store, source, analysis)
    except (FileNotFoundError, ValueError, media_prep.UnreadableRecording) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(2) from None
    # AT-173: a vanished recording printed a GREEN `0 frame(s) written`, exit 0
    # -- success for work that could not even be attempted.
    colour = typer.colors.GREEN if written else typer.colors.YELLOW
    typer.secho(f"{source_id}: {len(written)} frame(s) written", fg=colour)


def _require_source(store: ProjectStore, project: str, source_id: str):
    source = next((s for s in store.list_sources() if s.id == source_id), None)
    if source is None:
        typer.secho(f"{project} has no source {source_id} — try `autotester ingest list`.",
                    fg=typer.colors.RED)
        raise typer.Exit(2)
    return source


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
    source = _require_source(store, project, source_id)

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
