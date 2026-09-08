"""MEDIA PREP: make a recording readable — probe it, cut it, transcribe it.

Contract: qa/contracts/video-learning.md VL1. Runs on the HOST, never in the
container: the container has no ffmpeg and no GPU, and the 9GB corpus is never
mounted into it. The chunks land under `projects/<slug>/sources/<id>/` which the
container sees through the existing bind mount, so the two halves meet on disk
and nowhere else.

VL1's rule is that this stage DEGRADES, never crashes. Without ffmpeg it emits a
single chunk pointing at the original file — one long video a model can still
watch whole. Without whisper it emits an empty `Transcript`, which the ingest
prompt renders as "no speech detected" rather than as silence it has verified
(AT-134). Both are honest, smaller results; neither is an exception thrown at an
operator holding a 40-minute recording.
"""

from __future__ import annotations

from pathlib import Path

from autotester.media import chunks as chunk_mod
from autotester.media import frames as frame_mod
from autotester.media import probe as probe_mod
from autotester.media import transcribe as transcribe_mod
from autotester.schema.analysis import VideoAnalysis
from autotester.schema.media import MediaChunk, MediaPrep
from autotester.schema.project import Source
from autotester.store.project_store import ProjectStore


class SourceNotPrepared(RuntimeError):
    """Raised when a stage needs `media.json` and there is none."""


def prepare(store: ProjectStore, source: Source, *,
            chunk_minutes: float = 3.0, overlap_s: float = chunk_mod.DEFAULT_OVERLAP_S,
            use_whisper: bool = True) -> MediaPrep:
    """Probe, chunk and transcribe `source`, persisting all three.

    Idempotent on the transcript: `transcribe` reuses an existing sidecar
    byte-for-byte rather than regenerating it, so running prep twice cannot
    change what a tester is recorded as having said."""
    if source.path is None:
        raise ValueError(f"source {source.id} has no path to prepare")
    video = Path(source.path)
    if not video.is_file():
        raise FileNotFoundError(f"{source.id} points at {video}, which is not a readable file")

    transcript = transcribe_mod.transcribe(video, source.id, use_whisper=use_whisper)
    store.save_transcript(transcript)

    if not probe_mod.ffmpeg_available():
        prep = _unchunked(source, video, transcript.source_id)
    else:
        duration_s, width, height = probe_mod.probe(video)
        plan = chunk_mod.plan_chunks(duration_s, chunk_s=chunk_minutes * 60.0,
                                     overlap_s=overlap_s)
        out_dir = store.paths.source_chunks_dir(source.id)
        cut = chunk_mod.encode_chunks(video, out_dir, plan) if plan else []
        prep = MediaPrep(
            source_id=source.id, duration_s=duration_s,
            width=width, height=height, chunks=cut,
            transcript_ref=transcript.source_id,
            ffmpeg_version=probe_mod.ffmpeg_version(),
        )
    store.save_media_prep(prep)
    return prep


def _unchunked(source: Source, video: Path, transcript_ref: str) -> MediaPrep:
    """The no-ffmpeg shape: one chunk that IS the original file.

    Deliberately not an empty chunk list. A caller iterating `prep.chunks` then
    does the right thing on a host without ffmpeg instead of silently doing
    nothing, and the absent `ffmpeg_version` is what records why there is one
    chunk rather than twelve."""
    return MediaPrep(
        source_id=source.id,
        chunks=[MediaChunk(index=0, path=str(video), offset_s=0.0,
                           length_s=source.duration_s or 0.0)],
        transcript_ref=transcript_ref, ffmpeg_version=None,
    )


def extract_frames(store: ProjectStore, source: Source,
                   analysis: VideoAnalysis) -> list[Path]:
    """Pull the stills the vision pass named (`screenshot_ts`).

    Returns only the frames that actually landed. A missing still is a gap in
    the evidence, not a failed analysis — and `product_map` references a PNG
    only when it exists, so a half-extracted set degrades to fewer pictures
    rather than to broken links (A5)."""
    if source.path is None:
        raise ValueError(f"source {source.id} has no path")
    video = Path(source.path)
    out_dir = store.paths.source_frames_dir(source.id)

    wanted = sorted({t for screen in analysis.screens for t in screen.screenshot_ts})
    written: list[Path] = []
    for t_s in wanted:
        png = out_dir / frame_mod.frame_name(t_s)
        if png.exists() or frame_mod.extract_frame(video, t_s, png):
            written.append(png)
    return written


def require_prepared(store: ProjectStore, source_id: str) -> MediaPrep:
    """`media.json` or a refusal that names the host command that makes one.

    The analyze stage runs in the container, where prep cannot be performed at
    all, so "run it here" is not advice it can give — the message has to send
    the operator to the host (VL1)."""
    prep = store.load_media_prep(source_id)
    if prep is None:
        raise SourceNotPrepared(
            f"{source_id} has no media.json — run `autotester media prep "
            f"{store.paths.slug} {source_id}` on the HOST first (the container "
            f"has no ffmpeg)")
    return prep
