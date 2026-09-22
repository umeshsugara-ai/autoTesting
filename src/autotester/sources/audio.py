"""Gemini-first transcription for AUDIO sources, Whisper as the no-API fallback.

qa/contracts/source-adapters.md AUDIO row + SA3-SA6. `register_audio`
(`sources/adapters.py`) calls `transcribe_audio` here for every new AUDIO
Source. A Gemini reading goes straight through the Provider seam
(`providers/base.py::Provider.see_video` -- the same media-upload-plus-
structured-output mechanism VIDEO already uses, asked for a transcript
instead of a screen reading; no new vendor). No Gemini key, or the call
itself failing, degrades to `media/transcribe.py`'s Whisper subprocess WITH
a note on the Source (SA5); corrupt or genuinely unreadable audio -- neither
engine produces a transcript -- registers with an `extraction_error` note
instead of silent empty text, the same discipline `sources/extract.py`
applies to DOC. `media/probe.py` (Track A3) is reused to tell "corrupt" from
"no engine available at all": `probe` returns zeroed-out numbers when
ffprobe cannot read the file.

Long-file chunking (`media/chunks.py`, also Track A3) is deliberately NOT
wired here: Gemini's file API accepts a voice note or lecture-length
recording whole, so phase-1b sends the file once rather than splitting it.
Chunking a multi-hour recording is a real fast-follow, not claimed as done.

SA6: this module transcribes and NAMES what it heard; it never chooses which
checks run or edits stored text beyond the transcription itself.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from pydantic import BaseModel, ConfigDict, Field

from autotester.core.redact import assert_no_raw_secrets
from autotester.media.probe import probe
from autotester.media.transcribe import transcribe as whisper_transcribe
from autotester.providers.base import Provider, ProviderError
from autotester.schema.media import Transcript, TranscriptSegment

AUDIO_SUFFIXES = frozenset({".mp3", ".wav", ".m4a", ".ogg", ".opus"})

TRANSCRIBE_PROMPT = (
    "Transcribe the spoken audio verbatim, as JSON segments. Each segment is one "
    "distinct utterance: its start and end time in seconds from the start of this "
    "clip, and the exact words spoken -- do not summarise, translate, or invent "
    "words you did not hear. If there is no speech at all, return an empty "
    "segments list."
)


class GeminiSegment(BaseModel):
    """One utterance as Gemini's structured output names it.

    SA6: transcription fields only -- naming what was heard, never deciding
    anything about the product.
    """

    model_config = ConfigDict(extra="forbid")

    start: float
    end: float
    text: str


class GeminiTranscription(BaseModel):
    """The schema asked of `Provider.see_video` for one audio file."""

    model_config = ConfigDict(extra="forbid")

    segments: list[GeminiSegment] = Field(default_factory=list)


class TranscriptionOutcome(NamedTuple):
    """What `register_audio` persists: a `Transcript` (or None) plus the
    `Source.notes` value.

    `sources/extract.py::Extraction`'s shape, widened for AUDIO's two honest
    degradation paths (SA5): `note` is `"degraded: ..."` when Whisper stood
    in for Gemini and still produced a transcript, `"extraction_error: ..."`
    when nothing usable was produced, and None on a clean Gemini reading.
    """

    transcript: Transcript | None
    note: str | None


def transcribe_audio(
    path: Path,
    source_id: str,
    *,
    provider: Provider | None,
    secrets: Iterable[str] = (),
) -> TranscriptionOutcome:
    """Gemini first; Whisper next; an honest `extraction_error` last (SA5).

    `secrets` gates the model call (SA3): a raw secret value present in the
    prompt raises before anything is sent to Gemini -- the same discipline
    `browser/secrets.py::assert_no_raw_secrets` applies before typing into a
    page.
    """
    if provider is not None and provider.available():
        try:
            return _via_gemini(path, source_id, provider, secrets)
        except ProviderError as exc:
            return _via_whisper(path, source_id, f"the Gemini call failed ({exc})")
    reason = (
        "no Gemini provider was configured"
        if provider is None
        else "the Gemini provider is unavailable (no API key)"
    )
    return _via_whisper(path, source_id, reason)


def _via_gemini(
    path: Path, source_id: str, provider: Provider, secrets: Iterable[str]
) -> TranscriptionOutcome:
    """The clean path: one Gemini call over the whole file (no chunking, see
    the module docstring), validated against `assert_no_raw_secrets` first."""
    assert_no_raw_secrets(TRANSCRIBE_PROMPT, secrets)
    result = provider.see_video(path, TRANSCRIBE_PROMPT, GeminiTranscription)
    segments = [TranscriptSegment(start=s.start, end=s.end, text=s.text) for s in result.segments]
    if not segments:
        return TranscriptionOutcome(
            None, "extraction_error: gemini heard no speech and returned no segments"
        )
    transcript = Transcript(
        source_id=source_id,
        segments=segments,
        engine=f"gemini:{provider.label}",
        speech_seconds=round(sum(s.end - s.start for s in segments), 2),
    )
    return TranscriptionOutcome(transcript, None)


def _via_whisper(path: Path, source_id: str, degraded_reason: str) -> TranscriptionOutcome:
    """The fallback path: a sidecar or a real whisper reading -- even one with
    no speech in it -- is a genuine reading (SA5's degraded-with-note case).
    Only `engine="none"` (no sidecar, whisper absent or its subprocess
    failed) falls through to `probe` to tell corruption from "no engine"."""
    transcript = whisper_transcribe(path, source_id)
    if transcript.engine != "none":
        note = f"degraded: {degraded_reason} -- used the whisper fallback"
        return TranscriptionOutcome(transcript, note)
    duration_s, _, _ = probe(path)
    if duration_s <= 0:
        return TranscriptionOutcome(
            None, "extraction_error: the audio file could not be read (corrupt or invalid)"
        )
    return TranscriptionOutcome(
        None, f"extraction_error: {degraded_reason} and no transcript could be produced"
    )
