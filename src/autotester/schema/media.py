"""Host-side media preparation artifacts: transcripts and chunk manifests.

`stages/media_prep.py` (host CLI, needs ffmpeg/faster-whisper) writes these;
the container only ever reads them back through `ProjectStore`, never runs
ffmpeg itself (A3 — the container has neither ffmpeg nor a GPU).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from autotester.schema.base import Artifact


class TranscriptSegment(BaseModel):
    """One spoken utterance, absolute seconds into the source video."""

    model_config = ConfigDict(extra="forbid")

    start: float
    end: float
    text: str


class Transcript(Artifact):
    """A video's narration. `from_sidecar` loads the exact shape the existing
    `erp*.transcript.json` files already use — those are reused byte-for-byte,
    never re-transcribed."""

    source_id: str
    segments: list[TranscriptSegment] = Field(default_factory=list)
    speech_seconds: float = 0.0
    engine: str = "none"

    @classmethod
    def from_sidecar(cls, path: Path, source_id: str) -> Transcript:
        """Load `{"segments": [{start,end,text}], "speech_seconds": N}` — the
        shape every existing `*.transcript.json` sidecar already has."""
        import json

        raw = json.loads(path.read_text(encoding="utf-8"))
        segments = [TranscriptSegment(**seg) for seg in raw.get("segments", [])]
        return cls(
            source_id=source_id,
            segments=segments,
            speech_seconds=raw.get("speech_seconds", 0.0),
            engine="sidecar",
        )

    def slice(self, offset_s: float, length_s: float) -> str:
        """Clip-relative narration lines for the window `[offset_s, offset_s+length_s)`,
        as `[MM:SS-MM:SS] text` — injected into the ingest prompt as ground truth
        so the model aligns speech to screen instead of re-transcribing (I8)."""
        end = offset_s + length_s
        lines = []
        for seg in self.segments:
            if seg.end <= offset_s or seg.start >= end:
                continue
            rel_start = max(seg.start, offset_s) - offset_s
            rel_end = min(seg.end, end) - offset_s
            lines.append(f"[{_fmt(rel_start)}-{_fmt(rel_end)}] {seg.text}")
        return "\n".join(lines)


def _fmt(seconds: float) -> str:
    m, s = divmod(round(seconds), 60)
    return f"{m:02d}:{s:02d}"


class MediaChunk(BaseModel):
    """One re-encoded chunk of a longer video."""

    model_config = ConfigDict(extra="forbid")

    index: int
    path: str = Field(description="project-relative path under sources/<id>/chunks/")
    offset_s: float
    length_s: float


class MediaPrep(Artifact):
    """Probe + chunk manifest for one `Source`. Degrades gracefully (VL1):
    without ffmpeg, a single chunk pointing at the original path;
    `transcript_ref` names the sibling `Transcript` when one exists."""

    source_id: str
    duration_s: float = 0.0
    width: int = 0
    height: int = 0
    chunks: list[MediaChunk] = Field(default_factory=list)
    transcript_ref: str | None = None
    ffmpeg_version: str | None = None
