"""The source-adapter seam: any teaching material -> the ONE `Source` model.

Adapters CONVERT material into a content-addressed `Source`; they never decide
what the product is (qa/contracts/source-adapters.md). This package is the
single place TEXT, DOC, AUDIO and EMAIL uploads enter the system, alongside
the VIDEO path that already lives in `stages/ingest.py::register_source`.
"""

from __future__ import annotations

from autotester.sources.adapters import (
    Registration,
    register_audio,
    register_document,
    register_text,
)
from autotester.sources.audio import AUDIO_SUFFIXES, TranscriptionOutcome, transcribe_audio
from autotester.sources.email import (
    EMAIL_SUFFIXES,
    Attachment,
    ParsedMessage,
    iter_mbox_messages,
    parse_eml_bytes,
)
from autotester.sources.email_register import register_email
from autotester.sources.extract import DOC_SUFFIXES, Extraction, extract_document_text

__all__ = [
    "AUDIO_SUFFIXES",
    "DOC_SUFFIXES",
    "EMAIL_SUFFIXES",
    "Attachment",
    "Extraction",
    "ParsedMessage",
    "Registration",
    "TranscriptionOutcome",
    "extract_document_text",
    "iter_mbox_messages",
    "parse_eml_bytes",
    "register_audio",
    "register_document",
    "register_email",
    "register_text",
    "transcribe_audio",
]
