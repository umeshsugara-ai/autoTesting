"""INGEST: turn a video Source into a FlowSpec, provenance-tracked to the second.

Contract: qa/contracts/ingest.md I1-I5. Every `Step` this stage produces carries
a `SourceRef` back to the exact video timestamp it was read from, so a human
reviewing the resulting `FlowSpec` can jump straight to the second the system
learned a given action — the same discipline `stages/execute.py`/`grade.py`
apply to their own evidence.
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.ids import content_id
from autotester.core.paths import RepoDocs
from autotester.providers.base import Provider
from autotester.schema.flowspec import (
    Flow,
    FlowSpec,
    ObservedFlow,
    ObservedScreen,
    Screen,
    SourceRef,
    Step,
    VideoObservation,
)
from autotester.schema.project import Source

PROMPT_NAME = "ingest_video_v1.md"


def build_ingest_prompt(source: Source, docs: RepoDocs) -> str:
    template = (docs.prompts_dir / PROMPT_NAME).read_text(encoding="utf-8")
    return template.replace("{{SOURCE_LABEL}}", source.label or source.id)


def _to_screen(observed: ObservedScreen) -> Screen:
    return Screen(
        id=content_id("scr", {"name": observed.name, "signals": sorted(observed.signals)}),
        name=observed.name,
        signals=observed.signals,
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


def ingest_video(
    source: Source, project_slug: str, provider: Provider, docs: RepoDocs | None = None
) -> FlowSpec:
    """Watch `source` (a video `Source`) and produce a fresh `FlowSpec` for
    `project_slug`. Does not merge with an existing `FlowSpec` — a human reviews
    and merges via the review gate (T-065), which is a separate, later stage."""
    if source.path is None:
        raise ValueError(f"source {source.id} has no path to watch")
    docs = docs or RepoDocs()
    prompt = build_ingest_prompt(source, docs)
    observation = provider.see_video(Path(source.path), prompt, VideoObservation)

    screen_ids: dict[str, str] = {}
    screens: list[Screen] = []
    for observed in observation.screens:
        screen = _to_screen(observed)
        screen_ids.setdefault(observed.name, screen.id)
        if screen.id not in {s.id for s in screens}:  # AT-034: same screen named twice -> one row
            screens.append(screen)
    flows = [_to_flow(f, source.id, screen_ids) for f in observation.flows]

    return FlowSpec(project=project_slug, screens=screens, flows=flows, source_ids=[source.id])
