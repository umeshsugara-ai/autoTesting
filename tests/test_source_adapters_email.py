"""SOURCE ADAPTERS -- EMAIL (T-162 phase-2a). Contract:
qa/contracts/source-adapters.md EMAIL phase-2 row + SA1-SA6. Split into its
own file (doctor's file-length rule), the same split TEXT/DOC/AUDIO already
use.

`.eml`/`.mbox` are LOCAL FILES ONLY -- no IMAP/SMTP fetch, no mailbox
credentials anywhere in this suite (SA3). Covers: an email body becomes a
Source's text verbatim (SA-table's TEXT precedent, no model call to register
the body), an attachment becomes a CHILD Source via the EXISTING DOC adapter
linked to its parent via `Source.provenance` (SA4), a `.mbox` with N messages
becomes N EMAIL Sources (never one aggregated blob), SA2 (content-addressed
dedupe -- the same message registered twice is ONE Source), and SA5 (a
corrupt `.eml` registers with an `extraction_error` note, never silent empty
text).

No provider is exercised for these five capability rows: none of the
fixtures here carry an audio attachment, so `register_audio`'s Gemini/Whisper
path is untouched -- proven separately in test_source_adapters_audio.py.
"""

from __future__ import annotations

import mailbox
from email.message import EmailMessage
from pathlib import Path

from autotester.schema.enums import SourceKind
from autotester.sources import register_email
from autotester.store.project_store import ProjectStore


def _store(tmp_path: Path) -> ProjectStore:
    return ProjectStore("pathlynks", tmp_path)


def _build_eml_bytes(
    *, subject: str = "test", body: str = "hello", attachments: tuple = ()
) -> bytes:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content(body)
    for filename, content, maintype, subtype in attachments:
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
    return msg.as_bytes()


def _write_eml(tmp_path: Path, name: str, raw: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(raw)
    return path


# -- email body -> Source, verbatim, no model call ---------------------------
def test_email_body_becomes_a_source(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = _build_eml_bytes(subject="the bug", body="The submit button is broken.\n")
    eml = _write_eml(tmp_path, "one.eml", raw)

    results = register_email(store, eml)

    assert len(results) == 1
    result = results[0]
    assert result.created is True
    assert result.source.kind is SourceKind.EMAIL
    assert result.source.text == "The submit button is broken.\n"
    assert result.source.notes is None  # a clean parse carries no note


# -- attachment -> child DOC Source, linked via provenance --------------------
def test_email_attachment_becomes_child_doc_source(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = _build_eml_bytes(
        subject="with attachment",
        body="See the attached notes.\n",
        attachments=[("notes.txt", b"attachment body text\n", "text", "plain")],
    )
    eml = _write_eml(tmp_path, "two.eml", raw)

    results = register_email(store, eml)

    assert len(results) == 1
    parent = results[0].source
    sources = store.list_sources()
    assert len(sources) == 2  # the EMAIL Source + its DOC child, same store (SA1)
    child = next(s for s in sources if s.id != parent.id)
    assert child.kind is SourceKind.DOC
    assert child.text == "attachment body text\n"  # reused register_document's own extraction
    assert child.provenance is not None
    assert child.provenance.produced_by == "sources.email"
    assert child.provenance.inputs == [parent.id]  # SA4: linked to its parent message


# -- mbox with multiple messages -> one Source per message --------------------
def test_mbox_with_two_messages_becomes_two_email_sources(tmp_path: Path) -> None:
    store = _store(tmp_path)
    box_path = tmp_path / "inbox.mbox"
    box = mailbox.mbox(str(box_path))
    box.lock()
    box.add(_build_eml_bytes(subject="first", body="first message body\n"))
    box.add(_build_eml_bytes(subject="second", body="second message body\n"))
    box.flush()
    box.unlock()
    box.close()

    results = register_email(store, box_path)

    assert len(results) == 2
    assert all(r.created for r in results)
    assert all(r.source.kind is SourceKind.EMAIL for r in results)
    bodies = {r.source.text for r in results}
    assert bodies == {"first message body\n", "second message body\n"}
    assert len(store.list_sources()) == 2  # never aggregated into one blob


# -- SA2: content-addressed dedupe --------------------------------------------
def test_email_dedupes_same_bytes_registered_twice(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = _build_eml_bytes(subject="dup", body="identical message body\n")
    first_path = _write_eml(tmp_path, "first.eml", raw)
    second_path = _write_eml(tmp_path, "second.eml", raw)  # identical bytes, different filename

    first = register_email(store, first_path)
    second = register_email(store, second_path)

    assert first[0].created is True
    assert second[0].created is False  # "already registered", not a new row
    assert second[0].source.id == first[0].source.id
    assert len(store.list_sources()) == 1  # ONE Source, not two (SA2)


# -- SA5: honest degradation ----------------------------------------------------
def test_corrupt_eml_registers_with_extraction_error_not_empty(tmp_path: Path) -> None:
    store = _store(tmp_path)
    # a malformed multipart: declares a boundary it never closes, which
    # `raise_on_defect=True` turns into a genuine parse error (verified
    # against the real `email` stdlib module, not simulated).
    raw = (
        b'Content-Type: multipart/mixed; boundary="B"\r\n'
        b"Subject: broken\r\n\r\n"
        b"--B\r\n"
        b"Content-Type: text/plain\r\n\r\n"
        b"hello\r\n"
        b"--B--NEVER-CLOSED-PROPERLY"
    )
    eml = _write_eml(tmp_path, "broken.eml", raw)

    results = register_email(store, eml)

    assert len(results) == 1
    result = results[0]
    assert result.created is True  # it IS registered — a source exists
    assert result.source.text is None  # never a fake empty-string reading
    assert result.source.notes is not None
    assert result.source.notes.startswith("extraction_error")
    assert store.list_sources() == [result.source]  # no child sources fabricated either
