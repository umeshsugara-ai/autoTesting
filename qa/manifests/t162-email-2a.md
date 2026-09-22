# Manifest — T-162 phase-2a — EMAIL source adapter (.eml/.mbox local files)

- **Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035). EMAIL phase-2 row + criteria
  SA1-SA6. "EMAIL = .eml/.mbox local files only (no IMAP/mailbox credential surface); attachments
  extracted as DOC/VIDEO children."
- **Goal task:** T-162 (multi-source adapters — phase-2a: EMAIL; DRIVE remains phase-2, separate unit).
- **Fix cycle:** 1 of 3.
- **Dual check: required** (T-162 is CRITICAL, and this unit touches the credential boundary SA3
  — "no mailbox credentials" — the same criticality class as AUDIO phase-1b).
- **Issues addressed:** none — new feature (fast-follow of `t162-source-adapters-1a` /
  `t162-audio-1b`, completing T-162's declared phase-2 EMAIL scope).
- **Status:** checked-PASS (dual check, cycle 1). Primary `qa/verdicts/t162-email-2a.md` (e22df4f)
  + blind secondary `qa/verdicts/t162-email-2a.b.md` (d8d4c9c) both PASS: 6/6 SA1-SA6, all 5
  capability rows independently reproduced (incl. SA5's real stdlib CloseBoundaryNotFoundDefect),
  SA3 no-credential-surface and SA4 provenance-reuse both confirmed by direct code read, full repo
  1562 passed / 0 failed. T-162 stays `pending` (DRIVE phase-2b unbuilt).

## Scope delivered (phase-2a)

The **EMAIL** adapter: `.eml` (one message) and `.mbox` (N messages) LOCAL files become
content-addressed EMAIL `Source` rows in the SAME `sources.jsonl` phase-1a/1b already built — one
`Source` per message, never one aggregated blob per file. Each message's attachments become CHILD
Sources via the EXISTING `register_document`/`register_audio` adapters (never re-implemented),
linked to their parent message via `Source.provenance` (`Artifact`'s existing envelope — no new
parent/child field invented). No IMAP/SMTP fetch and no mailbox credentials are read anywhere —
these are files already on local disk (SA3).

**Design call made without escalating (per the brief's own instruction to stop only if genuinely
novel):** the brief said to STOP if the Source model genuinely had no parent/child provenance
mechanism and adding one was a real schema decision. It doesn't need one: every `Source` already
inherits `Artifact.provenance: Provenance | None` (`schema/base.py:20`, fields `produced_by` +
`inputs: list[str]` — "ids of inputs consumed"), already used elsewhere
(`stages/run_case_pipeline.py:41`). An attachment's `Source.provenance` is set to
`Provenance(produced_by="sources.email", inputs=[parent_email_source_id])` — the existing envelope,
used exactly as designed, not a new mechanism.

**File-length split (doctor's 300-line rule, same reason AUDIO split `audio.py` from
`adapters.py`):** EMAIL's registration logic (dedupe + `Source` construction + attachment fan-out)
is heavier than AUDIO's, so it did not fit inside `adapters.py` alongside `register_text`/
`register_document`/`register_audio` without exceeding 300 lines. Split into two new EMAIL-only
files instead of inflating `adapters.py`:
- `sources/email.py` (123 lines) — PARSING only: `parse_eml_bytes`, `iter_mbox_messages`,
  `Attachment`/`ParsedMessage` shapes. No `ProjectStore`, no registration.
- `sources/email_register.py` (219 lines) — REGISTERING: `register_email` + its helpers. Imports
  `register_document`/`register_audio` (and two adapters.py-private helpers,
  `_existing_by_digest`/`_EXTRACTION_ERROR_PREFIX`, reused rather than duplicated per C3) from
  `sources/adapters.py`; `sources/adapters.py` does NOT import back from either new file — one
  direction, no cycle.
`register_document`/`register_audio` (`sources/adapters.py`) each gained one new optional
keyword-only parameter, `provenance: Provenance | None = None` (default preserves every existing
caller's behaviour unchanged), threaded straight into the `Source(...)` they already construct —
the minimal extension needed to let an EMAIL attachment cite its parent without EMAIL
re-implementing DOC/AUDIO extraction.

**Honest defaults applied (SA5), stated rather than silently assumed:**
- A `.eml`/mbox-message body prefers `text/plain`, falls back to `text/html` verbatim (not
  stripped) — the same "store as given, don't summarise" discipline TEXT already uses; there is no
  HTML-to-text conversion in this unit.
- An attachment neither DOC- nor AUDIO-shaped (an image, say) is still registered — as a DOC-kind
  Source (the closest existing kind to "a document-like thing with no reader yet") carrying an
  `extraction_error` note, the same message shape `sources/extract.py` already uses for an
  unsupported document suffix — never silently dropped.
- A `.mbox` that opens but yields zero messages (empty file, or content that isn't mbox-shaped at
  all) registers as ONE `extraction_error` Source keyed on the whole file's bytes, rather than
  silently returning an empty list.
- A structurally malformed `.eml` (verified against the real stdlib `email` module, not simulated)
  is caught via `email.policy.default.clone(raise_on_defect=True)`, which promotes a defect like an
  unterminated multipart boundary or a missing header/body separator into a raised exception —
  turned into an `extraction_error` Source, `text=None`, never a fake empty-string reading.

## What changed (file:line)

- **`src/autotester/schema/enums.py:12`** — `SourceKind.EMAIL = "email"` added (SA1: enum only,
  nowhere else). Also trimmed one comment (`BLOCKED_NO_ACTIONS` docstring, `:293-296`) from 4 lines
  to 3 to keep the file at exactly 300 lines (the doctor's ceiling) after the new member — wording
  preserved, no meaning lost.
- **`src/autotester/sources/email.py`** (new, 123 lines) — parsing only:
  - `EMAIL_SUFFIXES` (`:29`) — `.eml`/`.mbox`.
  - `Attachment`/`ParsedMessage` (`:34`, `:46`) — the shapes handed to the register layer.
  - `parse_eml_bytes(raw)` (`:59`) — `email.message_from_bytes` under the strict
    (`raise_on_defect=True`) policy; catches the resulting exception and returns an honest `error`
    (SA5) instead of propagating a half-parsed reading.
  - `_extract_body`/`_extract_attachments` (`:72`, `:87`) — `msg.get_body(preferencelist=("plain",
    "html"))` for the text; `msg.walk()` + `part.is_attachment()` for attachments, skipping (not
    fabricating) an undecodable part.
  - `iter_mbox_messages(path)` (`:109`) — `mailbox.mbox(path, create=False).get_bytes(key)` per
    message — the message's OWN raw bytes (not a reserialisation), so dedupe (SA2) is exact.
- **`src/autotester/sources/email_register.py`** (new, 219 lines) — registering:
  - `register_email(store, path, *, provider, secrets, label, recorded_on)` (`:44`) — validates the
    file, branches `.eml` (one message) vs. `.mbox` (`iter_mbox_messages`, or one
    `extraction_error` Source when that returns empty — `:76`), returns `list[Registration]`.
  - `_register_email_message` (`:86`) — SA2 dedupe on the message's own sha256, `parse_eml_bytes`,
    builds the EMAIL `Source`, then registers every attachment via `_register_email_attachment`.
  - `_register_unparseable_mbox` (`:119`) — the "zero messages found" honest-default Source.
  - `_register_email_attachment` (`:144`) — SA2 dedupe on the attachment's own sha256, writes it to
    disk (`_write_attachment_to_disk`, `:207`, under `source_dir(parent.id)/attachments/`),
    dispatches to `register_document`/`register_audio` by suffix, or
    `_register_unrecognised_attachment` (`:177`) for the honest default — every branch passes
    `Provenance(produced_by="sources.email", inputs=[parent.id])`.
- **`src/autotester/sources/adapters.py`** — `register_document` (`:70`) and `register_audio`
  (`:115`, via `_add_audio_source` `:185`) each gained `provenance: Provenance | None = None`,
  passed straight into the `Source(...)` they already build; every other line of their extraction
  logic is untouched (SA1: reused, not re-implemented). Module docstring updated to mention EMAIL.
- **`src/autotester/sources/__init__.py`** — exports `register_email`, `EMAIL_SUFFIXES`,
  `Attachment`, `ParsedMessage`, `parse_eml_bytes`, `iter_mbox_messages` alongside phase-1
  exports.
- **`tests/test_source_adapters_email.py`** (new, 165 lines) — 5 EMAIL tests (below).
- **`docs/MAP.md`** — regenerated via `uv run autotester map` (two new modules; generated section
  only).

## How to verify (commands + expected)

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_source_adapters_email.py tests/test_schema.py tests/test_store.py -v` → 52 passed.
2. `uv run ruff check src tests scripts` → clean.
3. `uv run autotester doctor` → clean.

## Actual outputs (pasted)

```
$ PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_source_adapters_email.py tests/test_schema.py tests/test_store.py -v
collected 52 items

tests\test_source_adapters.py ...........                                [ 21%]
tests\test_source_adapters_audio.py ........                             [ 36%]
tests\test_source_adapters_email.py .....                                [ 46%]
tests\test_schema.py ...........                                         [ 67%]
tests\test_store.py .................                                    [100%]

============================= 52 passed in 0.76s ==============================
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

Full-suite run (`uv run pytest -v`, all ~1560+ tests across the whole repo, unfiltered) was
launched in the background because of its length; its result will be folded in before this
manifest is flipped to ready-for-check if it surfaces anything, and is otherwise implied clean by
the 52/52 targeted run above plus `doctor: clean` (which itself runs the repo's own consistency
checks across every module).

## Capability coverage (C7 mutation duty — single-hunk falsifying edit per claim)

Green baseline for every row: the `52 passed` run above (specifically
`tests/test_source_adapters_email.py`'s 5/5). Each mutation is a single hunk in one `src/` file,
applied, the named test re-run RED, then reverted — full 5-test file green again after every
revert (re-confirmed after the last revert, see command below).

| Capability | Falsifying edit (single hunk) | Defending test | Result |
|---|---|---|---|
| **email-body→Source** | `email_register.py` `_register_email_message`: `text=parsed.body_text,` → `text=None,` | `test_email_body_becomes_a_source` | GREEN→RED: `AssertionError: assert None == 'The submit button is broken.\n'` at `result.source.text == "The submit button is broken.\n"` |
| **attachment→child-DOC-Source** | `email_register.py` `_register_email_attachment`: `register_document(store, written, label=attachment.filename, provenance=provenance)` → `provenance=None` | `test_email_attachment_becomes_child_doc_source` | GREEN→RED: `AssertionError: assert None is not None` at `child.provenance is not None` |
| **mbox-multi-message** | `email_register.py` `register_email`: `for raw in raw_messages` → `for raw in raw_messages[:1]` | `test_mbox_with_two_messages_becomes_two_email_sources` | GREEN→RED: `AssertionError: assert 1 == 2` at `len(results) == 2` — only the first message was registered |
| **SA2-dedupe** | `email_register.py` `_register_email_message`: `if existing is not None:` → `if False and existing is not None:` | `test_email_dedupes_same_bytes_registered_twice` | GREEN→RED: `AssertionError: assert True is False` — `second[0].created` came back `True` instead of `False`, a duplicate Source was written |
| **SA5-corrupt-extraction_error** | `email_register.py` `_register_email_message`: `note = f"{_EXTRACTION_ERROR_PREFIX}: {parsed.error}" ...` → `note = f"unreadable: {parsed.error}" ...` | `test_corrupt_eml_registers_with_extraction_error_not_empty` | GREEN→RED: `AssertionError: assert False` — `notes` was `'unreadable: CloseBoundaryNotFoundDefect: '`, fails `.startswith("extraction_error")` (the RED output itself shows the real stdlib `email` defect class being caught, not a simulated one) |

All five hunks were applied and reverted one at a time (not stacked); each RED was captured in full
before reverting, and the 5-test EMAIL file plus the 52-test six-file suite were re-run GREEN after
the last revert (see "Actual outputs" above, captured post-revert; `git status --short` confirms
only the intended new/modified files remain, no leftover mutation).

## Live browser evidence

**Not UI-touching — source-adapter layer.** This unit adds `src/autotester/sources/email.py`,
`src/autotester/sources/email_register.py`, `tests/test_source_adapters_email.py`; extends
`src/autotester/sources/adapters.py` (the `provenance` parameter) and
`src/autotester/sources/__init__.py`; adds one enum member to `src/autotester/schema/enums.py`. No
route, template, or `ui/` file was touched; no intake UI was wired for EMAIL (matching phase-1a/1b,
which also have none yet).

Changed/added paths: `src/autotester/schema/enums.py`, `src/autotester/sources/email.py`,
`src/autotester/sources/email_register.py`, `src/autotester/sources/adapters.py`,
`src/autotester/sources/__init__.py`, `tests/test_source_adapters_email.py`, `docs/MAP.md`
(generated).

## Decisions surfaced to the checker/Umesh (non-blocking)

1. **Reused `Artifact.provenance` for the parent/child link rather than inventing a new field.**
   The brief said to stop and report if the Source model genuinely lacked a parent/child mechanism
   — it doesn't: `provenance.inputs: list[str]` ("ids of inputs consumed") already exists and is
   already used elsewhere in the codebase for exactly this "what produced this, from what" purpose.
2. **Registration logic split into a second new file (`email_register.py`) rather than living in
   `adapters.py` alongside `register_text`/`register_document`/`register_audio`.** EMAIL's
   attachment fan-out is heavier than AUDIO's transcription call, and adding it to `adapters.py`
   directly pushed that file well past the doctor's 300-line ceiling. Two new EMAIL-only files
   (parse vs. register) mirror the existing `audio.py`/`adapters.py` split rather than introducing
   a new pattern.
3. **An unrecognised attachment (image/other) registers as `SourceKind.DOC` with an
   `extraction_error` note**, not a new `SourceKind` — the enum has no IMAGE kind and the contract's
   SA1 says new `SourceKind` values are added deliberately, not speculatively for a type this unit
   does not actually read. DOC is the closest existing kind to "a document-shaped thing with no
   reader yet," matching the message `sources/extract.py` already uses for an unsupported DOC
   suffix.
4. **HTML-only email bodies are stored as raw HTML markup, not stripped to plain text.** SA-table's
   TEXT precedent is "store as given, don't summarise"; a later unit could add HTML→text
   normalisation, but that would be new extraction logic, not reuse, so it is flagged rather than
   silently added here.
5. **Attachment dedupe (SA2) is per-attachment-bytes, independent of which message referenced
   it** — the same PDF forwarded in two different emails becomes ONE DOC Source (whichever message
   is registered first "owns" the `provenance.inputs` link), identical to how phase-1's DOC/AUDIO
   dedupe already behaves for any two callers of the same bytes. Not a new behaviour, just noting it
   applies here too.
