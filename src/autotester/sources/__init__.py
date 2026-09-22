"""The source-adapter seam: any teaching material -> the ONE `Source` model.

Adapters CONVERT material into a content-addressed `Source`; they never decide
what the product is (qa/contracts/source-adapters.md). This package is the
single place TEXT and DOC uploads enter the system, alongside the VIDEO path
that already lives in `stages/ingest.py::register_source`.
"""

from __future__ import annotations

from autotester.sources.adapters import (
    Registration,
    register_document,
    register_text,
)
from autotester.sources.extract import DOC_SUFFIXES, Extraction, extract_document_text

__all__ = [
    "DOC_SUFFIXES",
    "Extraction",
    "Registration",
    "extract_document_text",
    "register_document",
    "register_text",
]
