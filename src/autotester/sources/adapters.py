"""Convert teaching material into the ONE content-addressed `Source` model.

The seam the learn-or-explore orchestrator (T-163) consumes: TEXT, DOC and
AUDIO uploads all become `Source` rows in the same `sources.jsonl`, never a
second store (SA1). Content-addressed (sha256) dedupe means the same bytes
registered twice is ONE Source and the second call reports `created=False`
(SA2). TEXT is stored verbatim with no model call (SA-table); DOC is
extracted host-side via `sources.extract`; AUDIO is transcribed Gemini-first
via `sources.audio` (the Provider seam), Whisper as the no-API fallback. An
unreadable document or untranscribable recording is registered with an
`extraction_error` note, never silently as empty text (SA5). Only AUDIO calls
a model, and only to transcribe -- SA6's "a model may NAME, never DECIDE"
boundary is enforced by shape (`sources.audio` never returns anything but a
transcript).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from autotester.core.ids import file_sha256
from autotester.providers.base import Provider
from autotester.schema.enums import SourceKind
from autotester.schema.project import Source
from autotester.sources.audio import AUDIO_SUFFIXES, transcribe_audio
from autotester.sources.extract import DOC_SUFFIXES, extract_document_text
from autotester.store.project_store import ProjectStore

_EXTRACTION_ERROR_PREFIX = "extraction_error"


class Registration(NamedTuple):
    """A register call's outcome.

    `created` is False when SA2 dedupe returned a Source already registered from
    identical bytes — the UI says "already registered" instead of showing a new
    row, and the document is not re-extracted.
    """

    source: Source
    created: bool


def register_text(store: ProjectStore, text: str, *, label: str | None = None) -> Registration:
    """Inline/pasted text -> a verbatim TEXT `Source`. No model call (SA-table).

    The text is content-addressed by the sha256 of its UTF-8 bytes so the same
    paste twice is ONE Source (SA2). Provenance is the whole Source (SA4): TEXT
    has no sub-sections.
    """
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing = _existing_by_digest(store, digest)
    if existing is not None:
        return Registration(existing, created=False)
    source = store.add_source(
        Source(
            project=store.paths.slug,
            kind=SourceKind.TEXT,
            text=text,
            sha256=digest,
            label=label,
        )
    )
    return Registration(source, created=True)


def register_document(
    store: ProjectStore,
    path: Path,
    *,
    label: str | None = None,
    recorded_on: str | None = None,
) -> Registration:
    """A `.txt`/`.md`/`.docx`/`.pdf` upload -> a content-addressed DOC `Source`.

    Text is extracted host-side and deterministically (`sources.extract`); a
    document that cannot be read is still registered, with an `extraction_error`
    note and `text=None`, never silently as empty text (SA5). The same file
    registered twice is ONE Source and is not re-extracted (SA2).
    """
    if not path.exists():
        raise FileNotFoundError(f"no such document: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"that is a folder, not a document file: {path}")
    if path.suffix.lower() not in DOC_SUFFIXES:
        raise ValueError(
            "that is not a document — add a file ending in " + ", ".join(sorted(DOC_SUFFIXES))
        )
    digest = file_sha256(path)
    existing = _existing_by_digest(store, digest)
    if existing is not None:
        return Registration(existing, created=False)
    extraction = extract_document_text(path)
    note = (
        f"{_EXTRACTION_ERROR_PREFIX}: {extraction.error}" if extraction.error is not None else None
    )
    source = store.add_source(
        Source(
            project=store.paths.slug,
            kind=SourceKind.DOC,
            path=str(path.resolve()),
            sha256=digest,
            text=extraction.text,
            label=label,
            recorded_on=recorded_on,
            notes=note,
        )
    )
    return Registration(source, created=True)


def register_audio(
    store: ProjectStore,
    path: Path,
    *,
    provider: Provider | None = None,
    secrets: Iterable[str] = (),
    label: str | None = None,
    recorded_on: str | None = None,
) -> Registration:
    """A `.mp3`/`.wav`/`.m4a`/`.ogg`/`.opus` upload -> a content-addressed
    AUDIO `Source`, transcribed via `sources.audio.transcribe_audio`
    (Gemini-first, Whisper fallback -- SA-table). The same bytes registered
    twice is ONE Source and is not re-transcribed (SA2), exactly
    `register_document`'s dedupe. A degraded (Whisper) or failed
    (extraction_error) reading is recorded as a note on the Source, never
    silently as a clean one (SA5); a clean transcript is persisted alongside
    it via `ProjectStore.save_transcript`, addressable by the Source id
    (SA4) the same way VIDEO's transcript already is.
    """
    _require_audio_file(path)
    digest = file_sha256(path)
    existing = _existing_by_digest(store, digest)
    if existing is not None:
        return Registration(existing, created=False)
    source = _add_audio_source(store, path, digest, provider, secrets, label, recorded_on)
    return Registration(source, created=True)


def _require_audio_file(path: Path) -> None:
    """Raise unless `path` is a real file with a recognised audio suffix."""
    if not path.exists():
        raise FileNotFoundError(f"no such audio file: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"that is a folder, not an audio file: {path}")
    if path.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError(
            "that is not an audio file — add a file ending in "
            + ", ".join(sorted(AUDIO_SUFFIXES))
        )


def _add_audio_source(
    store: ProjectStore,
    path: Path,
    digest: str,
    provider: Provider | None,
    secrets: Iterable[str],
    label: str | None,
    recorded_on: str | None,
) -> Source:
    """Transcribe and persist a new AUDIO `Source` + its `Transcript` sidecar.

    The id is content-addressed on sha256 alone (`Source.model_post_init`); a
    throwaway instance gives the real id without duplicating that formula
    here, so the `Transcript` can cite it before the real Source exists (SA4).
    """
    provisional_id = Source(project=store.paths.slug, kind=SourceKind.AUDIO, sha256=digest).id
    outcome = transcribe_audio(path, provisional_id, provider=provider, secrets=secrets)
    source = store.add_source(
        Source(
            project=store.paths.slug,
            kind=SourceKind.AUDIO,
            path=str(path.resolve()),
            sha256=digest,
            label=label,
            recorded_on=recorded_on,
            notes=outcome.note,
        )
    )
    if outcome.transcript is not None:
        store.save_transcript(outcome.transcript)
    return source


def _existing_by_digest(store: ProjectStore, digest: str) -> Source | None:
    """SA2: the Source already registered from these exact bytes, if any.

    Reads fresh from disk (`list_sources`) so a row written by another process
    in the same session is still seen — the same discipline
    `stages/ingest.py::register_source` applies to VIDEO.
    """
    for existing in store.list_sources():
        if existing.sha256 == digest:
            return existing
    return None
