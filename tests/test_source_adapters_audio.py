"""SOURCE ADAPTERS -- AUDIO (T-162 phase-1b). Contract:
qa/contracts/source-adapters.md AUDIO row + SA3-SA6. Split out of
test_source_adapters.py (doctor's file-length rule); TEXT/DOC stay there.

AUDIO is the one adapter that calls a model, and only to transcribe --
`sources.audio` never returns anything but a transcript, which is the
SA6/"a model may NAME, never DECIDE" boundary enforced by shape. Covers:
SA1 (AUDIO shares the one store + enum with TEXT/DOC), SA2 (content-addressed
dedupe, no re-transcription), SA3 (a raw secret never reaches the model
call), SA4 (the transcript cites the Source id + segments), and SA5 (honest
degradation -- no Gemini falls back to Whisper WITH a note; corrupt/untran-
scribable audio gets an `extraction_error` note, never silent empty text).

Every model call here is mocked (`MockProvider`, seeded per
`qa/contracts/source-adapters.md`'s AUDIO row) or monkeypatched
(`whisper_transcribe`/`probe`) -- no network, no real transcription.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.providers.base import ProviderError
from autotester.providers.mock import MockProvider
from autotester.schema.enums import SourceKind
from autotester.schema.media import Transcript, TranscriptSegment
from autotester.sources import register_audio, register_document, register_text
from autotester.sources.audio import GeminiSegment, GeminiTranscription
from autotester.store.project_store import ProjectStore

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _store(tmp_path: Path) -> ProjectStore:
    return ProjectStore("pathlynks", tmp_path)


def _write_audio(tmp_path: Path, name: str = "note.mp3", body: bytes = b"fake mp3 bytes") -> Path:
    path = tmp_path / name
    path.write_bytes(body)
    return path


def _seeded_provider(*segments: GeminiSegment) -> MockProvider:
    return MockProvider(responses={"vision": [GeminiTranscription(segments=list(segments))]})


def test_audio_transcribes_via_gemini_provider(tmp_path: Path) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path)
    provider = _seeded_provider(
        GeminiSegment(start=0.0, end=2.5, text="the submit button is broken")
    )

    result = register_audio(store, audio, provider=provider)

    assert result.created is True
    assert result.source.kind is SourceKind.AUDIO
    assert result.source.notes is None  # a clean Gemini reading carries no note
    transcript = store.load_transcript(result.source.id)
    assert transcript is not None
    assert transcript.segments[0].text == "the submit button is broken"
    assert transcript.engine.startswith("gemini:")
    assert len(provider.prompts) == 1  # exactly one model call for one file


# -- SA2: content-addressed dedupe -------------------------------------------
def test_audio_dedupes_same_bytes_without_re_transcribing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    body = b"identical audio bytes"
    first_path = _write_audio(tmp_path, "one.mp3", body)
    second_path = _write_audio(tmp_path, "two.mp3", body)
    provider = _seeded_provider(GeminiSegment(start=0.0, end=1.0, text="hi"))

    first = register_audio(store, first_path, provider=provider)
    second = register_audio(store, second_path, provider=provider)

    assert first.created is True
    assert second.created is False  # "already registered", not a new row
    assert second.source.id == first.source.id
    assert len(store.list_sources()) == 1  # ONE Source, not two (SA2)
    assert len(provider.prompts) == 1  # the second call never reaches the provider


# -- SA5: honest degradation --------------------------------------------------
def test_audio_falls_back_to_whisper_with_a_degradation_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path)

    def _fake_whisper(path: Path, source_id: str, **_: object) -> Transcript:
        return Transcript(
            source_id=source_id,
            segments=[TranscriptSegment(start=0.0, end=1.2, text="whisper heard this")],
            engine="large-v3-turbo",
        )

    monkeypatch.setattr("autotester.sources.audio.whisper_transcribe", _fake_whisper)

    result = register_audio(store, audio, provider=None)  # no Gemini configured

    assert result.source.notes is not None
    assert result.source.notes.startswith("degraded:")
    assert "whisper fallback" in result.source.notes
    transcript = store.load_transcript(result.source.id)
    assert transcript is not None
    assert transcript.segments[0].text == "whisper heard this"


def test_audio_falls_back_to_whisper_when_the_gemini_call_itself_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path)

    class _FailingProvider(MockProvider):
        def see_video(self, path, prompt, schema, options=None):
            raise ProviderError("quota exceeded")

    def _fake_whisper(path: Path, source_id: str, **_: object) -> Transcript:
        return Transcript(
            source_id=source_id,
            segments=[TranscriptSegment(start=0.0, end=1.0, text="fallback narration")],
            engine="large-v3-turbo",
        )

    monkeypatch.setattr("autotester.sources.audio.whisper_transcribe", _fake_whisper)

    result = register_audio(store, audio, provider=_FailingProvider())

    assert result.source.notes is not None
    assert result.source.notes.startswith("degraded:")
    assert "Gemini call failed" in result.source.notes


def test_corrupt_audio_registers_with_extraction_error_not_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path, "broken.mp3", b"not really audio")

    def _no_whisper(path: Path, source_id: str, **_: object) -> Transcript:
        return Transcript(source_id=source_id, engine="none")  # no sidecar, no faster_whisper

    monkeypatch.setattr("autotester.sources.audio.whisper_transcribe", _no_whisper)
    monkeypatch.setattr("autotester.sources.audio.probe", lambda path: (0.0, 0, 0))  # unreadable

    result = register_audio(store, audio, provider=None)

    assert result.created is True  # it IS registered — a source exists
    assert result.source.notes is not None
    assert result.source.notes.startswith("extraction_error")
    assert store.load_transcript(result.source.id) is None  # never a fake empty transcript


# -- SA4: provenance cites the Source id + segments ---------------------------
def test_audio_transcript_cites_source_id_and_segments(tmp_path: Path) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path)
    provider = _seeded_provider(
        GeminiSegment(start=0.0, end=3.0, text="segment one"),
        GeminiSegment(start=3.0, end=5.0, text="segment two"),
    )

    result = register_audio(store, audio, provider=provider)

    transcript = store.load_transcript(result.source.id)
    assert transcript is not None
    assert transcript.source_id == result.source.id  # SA4: provenance is the Source id
    assert len(transcript.segments) >= 1
    assert transcript.segments[0].start == 0.0
    assert transcript.segments[0].end == 3.0


# -- SA3: a raw secret never reaches the model call ---------------------------
def test_audio_gemini_call_is_gated_by_assert_no_raw_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path)
    provider = _seeded_provider(GeminiSegment(start=0.0, end=1.0, text="hi"))
    monkeypatch.setattr(
        "autotester.sources.audio.TRANSCRIBE_PROMPT", "transcribe this SUPERSECRET123 clip"
    )

    with pytest.raises(ValueError, match="raw secret value"):
        register_audio(store, audio, provider=provider, secrets=["SUPERSECRET123"])

    assert provider.prompts == []  # refused before the model was ever called


# -- SA1: one evidence model, one enum (AUDIO included) -----------------------
def test_audio_shares_the_one_store_and_enum_with_text_and_doc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    audio = _write_audio(tmp_path)

    def _fake_whisper(path: Path, source_id: str, **_: object) -> Transcript:
        return Transcript(
            source_id=source_id,
            segments=[TranscriptSegment(start=0.0, end=1.0, text="x")],
            engine="large-v3-turbo",
        )

    monkeypatch.setattr("autotester.sources.audio.whisper_transcribe", _fake_whisper)

    register_text(store, "a note")
    register_document(store, FIXTURES / "sample_doc.md")
    register_audio(store, audio, provider=None)

    sources = store.list_sources()
    assert len(sources) == 3  # all landed in the SAME sources.jsonl (SA1)
    assert {s.kind for s in sources} == {SourceKind.TEXT, SourceKind.DOC, SourceKind.AUDIO}
    assert SourceKind.AUDIO in set(SourceKind)  # added to the ONE enum, nowhere else
