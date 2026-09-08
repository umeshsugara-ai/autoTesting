"""ANALYZE: run the ensemble over a prepared recording, then adjudicate.

Contract: qa/contracts/video-learning.md VL2/VL3. This is the only stage in
Track A that spends money, and the one rule that shapes it is:

    **a cached observation is never re-requested.**

Every (source, model, prompt, chunk) answer is written to disk the moment it
arrives. A second `analyze` over the same recording makes **zero** provider
calls and produces the same analysis — which is what makes it safe to re-run
after a crash, after a code change, or just to look again. `--force` is the
only way past it, and it says so.

Two models and two prompts per chunk is a deliberate cost: agreement between
independent readings is the strongest signal this pipeline can produce without
a human, and `adjudicate` can only count agreement it was given.
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.paths import RepoDocs
from autotester.media.transcribe import SIDECAR_SUFFIX
from autotester.providers.base import Provider, ProviderError
from autotester.schema.analysis import VideoAnalysis
from autotester.schema.media import MediaChunk, Transcript
from autotester.schema.observation import ModelObservation, VideoObservation, VisionOptions
from autotester.schema.project import Source
from autotester.stages.adjudicate import adjudicate
from autotester.stages.media_prep import require_prepared
from autotester.store.project_store import ProjectStore

PROMPT_NAMES = ("ingest_video_v1.md", "video_issues_v1.md")
"""Two passes with different questions. One asks what the product IS; the other
asks what is WRONG with it. Asking both in a single prompt produced answers that
were worse at each — a model told to map and criticise at once does neither
carefully."""


class NoObservations(RuntimeError):
    """Every provider call failed, so there is nothing to adjudicate."""


def load_transcript(store: ProjectStore, source: Source) -> Transcript | None:
    """The narration for this recording, preferring what media prep persisted.

    Falls back to the sidecar beside the video so `analyze` still has ground
    truth if prep ran elsewhere — the container sees the bind-mounted project
    directory but not necessarily the corpus."""
    saved = store.load_transcript(source.id)
    if saved is not None:
        return saved
    if source.path:
        sidecar = Path(source.path).with_suffix(SIDECAR_SUFFIX)
        if sidecar.exists():
            try:
                return Transcript.from_sidecar(sidecar, source.id)
            except Exception:
                return None
    return None


def build_chunk_prompt(prompt_name: str, source: Source, docs: RepoDocs,
                 chunk: MediaChunk, transcript: Transcript | None) -> str:
    """One chunk's prompt, with only THIS chunk's narration in it.

    Slicing matters: handing a model the whole recording's transcript while it
    watches three minutes of it invites alignment to speech it cannot see, and
    a quote attached to the wrong screen is worse than no quote."""
    template = (docs.prompts_dir / prompt_name).read_text(encoding="utf-8")
    narration = "(no speech detected — do not invent dialogue)"
    if transcript is not None and transcript.segments:
        sliced = transcript.slice(chunk.offset_s, chunk.length_s)
        narration = sliced or "(no speech in this section — do not invent dialogue)"
    return (template
            .replace("{{SOURCE_LABEL}}", source.label or source.id)
            .replace("{{NARRATION}}", narration))


def observe_chunk(store: ProjectStore, source: Source, provider: Provider,
                  prompt_name: str, chunk: MediaChunk, *,
                  docs: RepoDocs, transcript: Transcript | None,
                  options: VisionOptions, force: bool) -> ModelObservation | None:
    """One model's answer for one chunk under one prompt. Cached.

    Returns `None` when the call failed — a single failed chunk must not lose
    the eleven that succeeded, and `adjudicate` is happy with fewer inputs."""
    cached = _cached(store, source.id, provider.label, prompt_name, chunk.index)
    if cached is not None and not force:
        return cached

    prompt = build_chunk_prompt(prompt_name, source, docs, chunk, transcript)
    try:
        answer = provider.see_video(Path(chunk.path), prompt, VideoObservation, options)
    except ProviderError:
        return None

    observation = ModelObservation(
        source_id=source.id, provider_label=provider.label, prompt_name=prompt_name,
        chunk_index=chunk.index, offset_s=chunk.offset_s, length_s=chunk.length_s,
        observation=answer,
    )
    store.save_observation(observation)
    return observation


def _cached(store: ProjectStore, source_id: str, label: str,
            prompt_name: str, chunk_index: int) -> ModelObservation | None:
    for observation in store.list_observations(source_id):
        if (observation.provider_label == label
                and observation.prompt_name == prompt_name
                and observation.chunk_index == chunk_index):
            return observation
    return None


def analyze(store: ProjectStore, source: Source, providers: list[Provider], *,
            docs: RepoDocs | None = None, options: VisionOptions | None = None,
            force: bool = False) -> VideoAnalysis:
    """Every model, every prompt, every chunk -- adjudicated into one reading.

    Refuses without `media.json` rather than silently analysing an unprepared
    recording as a single blob — prep is where chunking and narration happen,
    and skipping it changes the answer without saying so."""
    prep = require_prepared(store, source.id)
    docs = docs or RepoDocs()
    options = options or VisionOptions()
    transcript = load_transcript(store, source)

    observations: list[ModelObservation] = []
    for provider in providers:
        for prompt_name in PROMPT_NAMES:
            for chunk in prep.chunks:
                observation = observe_chunk(
                    store, source, provider, prompt_name, chunk,
                    docs=docs, transcript=transcript, options=options, force=force)
                if observation is not None:
                    observations.append(observation)

    if not observations:
        raise NoObservations(
            f"{source.id}: every provider call failed — nothing to adjudicate. "
            f"Check `autotester providers` for credentials.")

    analysis = adjudicate(observations, source.id)
    store.save_analysis(analysis)
    return analysis
