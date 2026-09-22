"""SOURCE ADAPTERS -- TEXT + DOC (T-162 phase-1a). Contract:
qa/contracts/source-adapters.md. AUDIO lives in test_source_adapters_audio.py
(split by responsibility, doctor's file-length rule) but shares this file's
fixtures/helpers pattern.

Covers the adapter seam for TEXT and DOC: SA1 (one store, one enum), SA2
(content-addressed dedupe), the SA-table (TEXT verbatim, no model call; DOC
extracted host-side), SA4 (provenance is the Source id), and SA5 (honest
degradation — an unreadable doc keeps an `extraction_error` note, never
silent empty text).

No provider is constructed anywhere in this file: the adapters take no model,
which is the SA6/"a model may NAME, never DECIDE" boundary enforced by shape.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from autotester.schema.enums import SourceKind
from autotester.sources import register_document, register_text
from autotester.store.project_store import ProjectStore

FIXTURES = Path(__file__).resolve().parent / "fixtures"

_DOCX_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "<w:body>"
    "<w:p><w:r><w:t>Chapter one of the manual.</w:t></w:r></w:p>"
    "<w:p><w:r><w:t>The submit button lives on the review screen.</w:t></w:r></w:p>"
    "</w:body></w:document>"
)


def _make_docx(path: Path, body_xml: str = _DOCX_XML) -> Path:
    """A minimal valid .docx (a zip with one `word/document.xml`)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", body_xml)
    return path


def _store(tmp_path: Path) -> ProjectStore:
    return ProjectStore("pathlynks", tmp_path)


# -- TEXT: verbatim, no model call -------------------------------------------
def test_text_is_stored_verbatim(tmp_path: Path) -> None:
    store = _store(tmp_path)
    body = "The password reset email never arrives — this is the bug.\nSecond line."

    result = register_text(store, body, label="tester note")

    assert result.created is True
    assert result.source.kind is SourceKind.TEXT
    assert result.source.text == body  # byte-for-byte, not summarised (SA-table)
    assert store.list_sources()[0].text == body  # persisted verbatim too


# -- DOC: deterministic host-side extraction ---------------------------------
def test_doc_extracts_markdown_verbatim(tmp_path: Path) -> None:
    store = _store(tmp_path)

    result = register_document(store, FIXTURES / "sample_doc.md")

    assert result.source.kind is SourceKind.DOC
    assert result.source.text == (FIXTURES / "sample_doc.md").read_text(encoding="utf-8")
    assert result.source.notes is None  # a clean read carries no error note


def test_doc_extracts_plaintext(tmp_path: Path) -> None:
    store = _store(tmp_path)

    result = register_document(store, FIXTURES / "sample_doc.txt")

    assert "open the sign-in page" in (result.source.text or "")


def test_doc_extracts_docx_paragraph_text(tmp_path: Path) -> None:
    store = _store(tmp_path)
    docx = _make_docx(tmp_path / "manual.docx")

    result = register_document(store, docx)

    assert result.source.kind is SourceKind.DOC
    assert result.source.text == (
        "Chapter one of the manual.\nThe submit button lives on the review screen."
    )


# -- SA4: provenance cites the Source id -------------------------------------
def test_extracted_doc_is_addressable_by_its_source_id(tmp_path: Path) -> None:
    store = _store(tmp_path)

    result = register_document(store, FIXTURES / "sample_doc.md")

    assert result.source.id
    assert result.source.id == store.list_sources()[0].id  # what T-163 will cite (SA4)


# -- SA2: content-addressed dedupe -------------------------------------------
def test_same_bytes_register_once(tmp_path: Path) -> None:
    store = _store(tmp_path)
    docx = _make_docx(tmp_path / "manual.docx")

    first = register_document(store, docx)
    second = register_document(store, _make_docx(tmp_path / "manual_copy.docx"))

    assert first.created is True
    assert second.created is False  # "already registered", not a new row
    assert second.source.id == first.source.id
    assert len(store.list_sources()) == 1  # ONE Source, not two (SA2)


def test_same_pasted_text_registers_once(tmp_path: Path) -> None:
    store = _store(tmp_path)
    body = "identical paste"

    first = register_text(store, body)
    second = register_text(store, body)

    assert first.created is True
    assert second.created is False
    assert len(store.list_sources()) == 1


# -- SA5: honest degradation -------------------------------------------------
def test_corrupt_doc_registers_with_extraction_error_not_empty(tmp_path: Path) -> None:
    store = _store(tmp_path)
    corrupt = tmp_path / "broken.docx"
    corrupt.write_bytes(b"this is not a real zip archive")

    result = register_document(store, corrupt)

    assert result.created is True  # it IS registered — a source exists
    assert result.source.text is None  # NOT silently empty text
    assert result.source.notes is not None
    assert result.source.notes.startswith("extraction_error")


def test_doctype_bearing_docx_is_refused_as_extraction_error(tmp_path: Path) -> None:
    store = _store(tmp_path)
    hostile = _make_docx(
        tmp_path / "xxe.docx",
        body_xml='<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><w:document/>',
    )

    result = register_document(store, hostile)

    assert result.source.text is None
    assert result.source.notes is not None
    assert result.source.notes.startswith("extraction_error")


def test_pdf_degrades_honestly_without_a_dependency(tmp_path: Path) -> None:
    store = _store(tmp_path)
    fake_pdf = tmp_path / "scanned.pdf"
    fake_pdf.write_bytes(b"%PDF-1.7 not really parseable here")

    result = register_document(store, fake_pdf)

    assert result.source.text is None
    assert result.source.notes is not None
    assert result.source.notes.startswith("extraction_error")


# -- SA1: one evidence model, one enum ---------------------------------------
def test_text_and_doc_share_one_store_and_one_enum(tmp_path: Path) -> None:
    store = _store(tmp_path)

    register_text(store, "a note")
    register_document(store, FIXTURES / "sample_doc.md")

    sources = store.list_sources()
    assert len(sources) == 2  # both landed in the SAME sources.jsonl (SA1)
    assert {s.kind for s in sources} == {SourceKind.TEXT, SourceKind.DOC}
    # both kinds come from the single SourceKind enum, nowhere else:
    assert all(s.kind in set(SourceKind) for s in sources)
