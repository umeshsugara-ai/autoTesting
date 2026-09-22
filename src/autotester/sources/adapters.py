"""Convert teaching material into the ONE content-addressed `Source` model.

The seam the learn-or-explore orchestrator (T-163) consumes: TEXT and DOC
uploads both become `Source` rows in the same `sources.jsonl`, never a second
store (SA1). Content-addressed (sha256) dedupe means the same bytes registered
twice is ONE Source and the second call reports `created=False` (SA2). TEXT is
stored verbatim with no model call (SA-table); DOC is extracted host-side via
`sources.extract` and an unreadable document is registered with an
`extraction_error` note, never silently as empty text (SA5). No adapter calls a
model, so none can DECIDE what the product is (SA6).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import NamedTuple

from autotester.core.ids import file_sha256
from autotester.schema.enums import SourceKind
from autotester.schema.project import Source
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
