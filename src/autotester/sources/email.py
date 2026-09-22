"""Parsing for EMAIL sources: `.eml`/`.mbox` LOCAL files only.

qa/contracts/source-adapters.md EMAIL phase-2 row + SA3/SA5. This module ONLY
parses -- turning raw message bytes into a body text + a list of attachment
bytes, or an honest reason it could not. `sources/email_register.py` does the
registering (dedupe, `Source` construction, delegating each attachment to the
EXISTING `register_document`/`register_audio` adapters) -- split out the same
way `sources/audio.py` (transcribe) stays separate from `sources/adapters.py`
(register), and to keep each file under the doctor's 300-line rule.

No IMAP/SMTP fetch and no mailbox credentials are read anywhere in this
module (SA3) -- `email.message_from_bytes`/`mailbox.mbox` operate on bytes
already on local disk. `raise_on_defect=True` promotes a malformed message
structure (an unterminated multipart boundary, a missing header/body
separator) to a caught, reported error instead of a silently truncated
reading (SA5) -- the same "an unreadable input is registered with an
`extraction_error` note, never silent empty text" discipline
`sources/extract.py` applies to DOC.
"""

from __future__ import annotations

import email
import email.policy
import mailbox
from pathlib import Path
from typing import NamedTuple

EMAIL_SUFFIXES = frozenset({".eml", ".mbox"})

_STRICT_POLICY = email.policy.default.clone(raise_on_defect=True)


class Attachment(NamedTuple):
    """One attachment part, as bytes -- never decoded/interpreted here.

    What kind of Source it becomes (DOC/AUDIO/honest-default) is
    `register_email`'s call, not this module's (SA6: naming, not deciding).
    """

    filename: str
    content: bytes
    content_type: str


class ParsedMessage(NamedTuple):
    """One email message, parsed -- or an honest reason it could not be.

    `error` set means `body_text`/`attachments` are meaningless; the caller
    registers a Source carrying the error note, never silently as empty
    text (SA5), the same shape `sources/extract.py::Extraction` uses.
    """

    body_text: str | None
    attachments: list[Attachment]
    error: str | None


def parse_eml_bytes(raw: bytes) -> ParsedMessage:
    """Parse one message's raw `.eml` bytes (also used per-message for
    `.mbox`, since a message extracted from a mbox is itself valid `.eml`
    bytes). A structurally malformed message raises under the strict
    policy and is turned into an honest `error` here rather than
    propagating a half-parsed reading (SA5)."""
    try:
        msg = email.message_from_bytes(raw, policy=_STRICT_POLICY)
    except Exception as exc:  # honest degradation (SA5): never a silent partial parse
        return ParsedMessage(None, [], f"{type(exc).__name__}: {exc}")
    return ParsedMessage(_extract_body(msg), _extract_attachments(msg), None)


def _extract_body(msg: email.message.Message) -> str | None:
    """The message's text body -- `text/plain` preferred, `text/html` as the
    fallback (SA-table's TEXT precedent: stored as given, not summarised).
    `None` only when no body part exists at all; an empty-but-present body
    (an attachment-only email) stays the empty string it really is."""
    body_part = msg.get_body(preferencelist=("plain", "html"))
    if body_part is None:
        return None
    try:
        content = body_part.get_content()
    except Exception:
        return None
    return content if isinstance(content, str) else None


def _extract_attachments(msg: email.message.Message) -> list[Attachment]:
    """Every part the message itself marks as an attachment (`Content-
    Disposition: attachment`, or a named part `email.policy` classifies as
    one) -- never the body part. A part whose payload cannot be decoded is
    skipped, not fabricated as empty bytes."""
    found: list[Attachment] = []
    for part in msg.walk():
        if not part.is_attachment():
            continue
        try:
            content = part.get_content()
        except Exception:
            continue
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif not isinstance(content, bytes):
            continue
        filename = part.get_filename() or "attachment"
        found.append(Attachment(filename, content, part.get_content_type()))
    return found


def iter_mbox_messages(path: Path) -> list[bytes]:
    """Every message's own raw bytes in a `.mbox`, in file order.

    `create=False` refuses to conjure an empty mbox for a path that turns
    out not to open as one -- the caller already checked the file exists.
    An empty list means "no messages found" (empty file, or content that is
    not mbox-shaped at all); `register_email` turns that into one honest
    `extraction_error` Source rather than silently registering nothing
    (SA5) -- it never means "corruption was silently swallowed".
    """
    box = mailbox.mbox(str(path), create=False)
    try:
        # `box` is a `mailbox.mbox`, not a dict -- `for key in box` yields
        # Message VALUES (its `__iter__` is `itervalues`), not keys, so
        # `.keys()` is required here despite ruff's dict-shaped heuristic.
        return [box.get_bytes(key) for key in box.keys()]  # noqa: SIM118
    finally:
        box.close()
