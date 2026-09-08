"""INGEST: turn a video Source into a FlowSpec, provenance-tracked to the second.

Contract: qa/contracts/ingest.md I1-I5. Every `Step` this stage produces carries
a `SourceRef` back to the exact video timestamp it was read from, so a human
reviewing the resulting `FlowSpec` can jump straight to the second the system
learned a given action — the same discipline `stages/execute.py`/`grade.py`
apply to their own evidence.
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.ids import content_id, file_sha256
from autotester.core.paths import RepoDocs
from autotester.core.urls import url_template
from autotester.providers.base import Provider
from autotester.schema.enums import ReviewStatus, SourceKind
from autotester.schema.flowspec import Flow, FlowSpec, Screen, SourceRef, Step
from autotester.schema.media import Transcript
from autotester.schema.observation import (
    ObservedFlow,
    ObservedScreen,
    VideoObservation,
    VisionOptions,
)
from autotester.schema.project import Source
from autotester.store.project_store import ProjectStore

PROMPT_NAME = "ingest_video_v1.md"


class FlowSpecApproved(RuntimeError):
    """Raised rather than overwriting a FlowSpec a human already approved (I6)."""


def build_ingest_prompt(source: Source, docs: RepoDocs,
                        transcript: Transcript | None = None) -> str:
    """The prompt, with the human's own narration injected as GROUND TRUTH.

    A tester saying "this should be X" is the highest-value signal in a
    recording and the one a vision model is least able to recover from pixels.
    Injecting the existing transcript is also why the model is told to ALIGN to
    it rather than re-transcribe: asked to do both, it paraphrases speech into
    something plausible, and a paraphrased complaint is a fabricated one."""
    template = (docs.prompts_dir / PROMPT_NAME).read_text(encoding="utf-8")
    narration = "(no speech detected — do not invent dialogue)"
    if transcript is not None and transcript.segments:
        narration = transcript.slice(0.0, transcript.segments[-1].end)
    return (template
            .replace("{{SOURCE_LABEL}}", source.label or source.id)
            .replace("{{NARRATION}}", narration))


def register_source(store: ProjectStore, path: Path, *, label: str | None = None,
                    recorded_on: str | None = None) -> Source:
    """Record a video on disk as a `Source`. Idempotent on content: the same
    bytes registered twice return the existing row rather than a second id, so
    re-running a shell command never silently doubles the corpus."""
    if not path.exists():
        raise FileNotFoundError(f"no such recording: {path}")
    digest = file_sha256(path)
    for existing in store.list_sources():
        if existing.sha256 == digest:
            return existing
    return store.add_source(Source(
        project=store.paths.slug, kind=SourceKind.VIDEO, path=str(path.resolve()),
        sha256=digest, label=label, recorded_on=recorded_on,
    ))


def _to_screen(observed: ObservedScreen, source_id: str) -> Screen:
    """One observed screen as a FlowSpec `Screen`.

    `url_pattern` is templated through the SAME `url_template` the crawler uses
    (I7), so a screen learned from a video and the same screen found by a crawl
    produce one row and not two. It is set only when a url was actually visible
    in the recording -- inventing one would make coverage report a gap closed
    that nothing has seen."""
    return Screen(
        id=content_id("scr", {"name": observed.name, "signals": sorted(observed.signals)}),
        name=observed.name,
        signals=observed.signals,
        url_pattern=url_template(observed.url) if observed.url else None,
        fields=observed.fields,
        source_ref=SourceRef(source_id=source_id, t_start=observed.t_start,
                             t_end=observed.t_end),
    )


def _to_flow(observed: ObservedFlow, source_id: str, screen_ids: dict[str, str]) -> Flow:
    steps = [
        Step(
            order=s.order,
            action=s.action,
            target=s.target,
            value=s.value,
            source_ref=SourceRef(source_id=source_id, t_start=s.t_start, t_end=s.t_end),
        )
        for s in observed.steps
    ]
    entry_screen = screen_ids.get(observed.entry_screen, observed.entry_screen)
    return Flow(
        id=content_id("flow", {"name": observed.name}),
        name=observed.name,
        entry_screen=entry_screen,
        steps=steps,
    )


def persist_ingest(store: ProjectStore, spec: FlowSpec, *, replace: bool = False) -> FlowSpec:
    """Write the FlowSpec, refusing to discard an APPROVED one (I6).

    The old `ingest_video` returned a spec and persisted nothing, so learning
    from a recording left no trace unless a caller remembered to save it -- and
    no caller did. Persisting blindly would be the opposite bug: overwriting a
    spec a human reviewed and approved throws away the review, not just the
    data. `--replace` is how a human says they meant it."""
    existing = store.load_flowspec()
    if existing is not None and existing.review.status is ReviewStatus.APPROVED and not replace:
        raise FlowSpecApproved(
            f"{store.paths.slug}'s FlowSpec is APPROVED (v{existing.version}) — "
            f"ingesting would discard that review. Re-run with --replace to overwrite, "
            f"or merge instead once merge_flowspec exists.")
    store.save_flowspec(spec)
    return spec


def ingest_video(
    source: Source, project_slug: str, provider: Provider, docs: RepoDocs | None = None,
    *, transcript: Transcript | None = None, options: VisionOptions | None = None,
) -> FlowSpec:
    """Watch `source` (a video `Source`) and produce a fresh `FlowSpec` for
    `project_slug`. Does not merge with an existing `FlowSpec` — a human reviews
    and merges via the review gate (T-065), which is a separate, later stage."""
    if source.path is None:
        raise ValueError(f"source {source.id} has no path to watch")
    docs = docs or RepoDocs()
    prompt = build_ingest_prompt(source, docs, transcript)
    observation = provider.see_video(Path(source.path), prompt, VideoObservation, options)

    screen_ids: dict[str, str] = {}
    screens: list[Screen] = []
    for observed in observation.screens:
        screen = _to_screen(observed, source.id)
        screen_ids.setdefault(observed.name, screen.id)
        if screen.id not in {s.id for s in screens}:  # AT-034: same screen named twice -> one row
            screens.append(screen)
    flows = [_to_flow(f, source.id, screen_ids) for f in observation.flows]

    return FlowSpec(project=project_slug, screens=screens, flows=flows,
                    source_ids=[source.id], app_overview=observation.summary)
