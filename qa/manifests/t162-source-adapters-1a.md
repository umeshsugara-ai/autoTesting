# Manifest — T-162 phase-1a — source-adapter seam + TEXT + DOC

- **Contract:** `qa/contracts/source-adapters.md` (SA1–SA6). **This is a gate-A-approved DRAFT.**
  The checker should assume contract ownership and finalize it (D-entry) on this check.
- **Goal task:** T-162 (multi-source adapters — phase-1a: TEXT + DOC; AUDIO/DRIVE/EMAIL deferred).
- **Fix cycle:** 1 of 3.
- **Dual check: required** (T-162 is CRITICAL).
- **Issues addressed:** none — new feature.
- **Status:** checked-PASS. DUAL check PASS (primary a7187214 6/6 fb18d13 + contract D-035 f227f9b; blind secondary a13040b5 5/5 14b6830); both re-derived 4 capability rows + full suite 1549 passed. source-adapters.md DRAFT->ACTIVE.

## Scope delivered (phase-1a)

The unified adapter **seam** — a single package where any teaching material converts into the
existing `Source` model with provenance — plus the **TEXT** and **DOC** adapters. AUDIO/DRIVE/EMAIL
are explicitly out of this unit and were not built (the enum is left intact for them).

## What changed (file:line)

- **`src/autotester/sources/__init__.py`** (new) — the seam package. Exports `register_text`,
  `register_document`, `Registration`, `extract_document_text`, `DOC_SUFFIXES`, `Extraction`. Module
  docstring names it the single entry point for TEXT/DOC, alongside the VIDEO path in
  `stages/ingest.py::register_source`.
- **`src/autotester/sources/extract.py`** (new, 94 lines) — deterministic host-side text extraction,
  **no model call**. `extract_document_text(path)` (`:47`) dispatches by suffix:
  - `.txt`/`.md` → `_read_text` (`:70`), strict UTF-8.
  - `.docx` → `_read_docx` (`:75`), stdlib `zipfile` + `xml.etree` over `word/document.xml`
    (contract open-question #1 default: stdlib-first, no new dependency).
  - `.pdf` → honest `extraction_error` (`_PDF_DEFERRED`, `:36`) — pure-python PDF text extraction
    needs a dependency this repo does not declare; deferred to a later unit (see "Decision surfaced").
  - Any exception (corrupt zip, undecodable bytes, unsupported suffix) → `Extraction(None, error)`
    (`:63`), never silent empty text.
  - **Security:** `_read_docx` (`:87`) refuses a `document.xml` carrying a `<!DOCTYPE>` before
    parsing — closes XXE + billion-laughs against the stdlib expat parser without `defusedxml`
    (flagged by the PostToolUse security hook; fixed in-band, degrades to SA5).
- **`src/autotester/sources/adapters.py`** (new, 130 lines) — the seam proper.
  - `Registration` NamedTuple (`:29`) — `(source, created)`; `created=False` is SA2's "already
    registered" signal for the UI.
  - `register_text(store, text, *, label)` (`:41`) — verbatim TEXT `Source`, sha256 of UTF-8 bytes,
    **no provider parameter → structurally cannot call a model** (SA-table / SA6).
  - `register_document(store, path, *, label, recorded_on)` (`:64`) — content-addressed DOC `Source`
    via `file_sha256`; extracted text on `Source.text`; an error becomes an `extraction_error` note
    on `Source.notes` with `text=None` (SA5).
  - `_existing_by_digest` (`:115`) — SA2 dedupe by sha256, reads `list_sources()` fresh from disk
    (same discipline as `register_source` for VIDEO).
- **`tests/test_source_adapters.py`** (new) — 11 tests (this is T-162's `done_check` target).
- **`tests/fixtures/sample_doc.md`**, **`tests/fixtures/sample_doc.txt`** (new) — DOC-extract fixtures.
- **`docs/MAP.md`** — regenerated via `uv run autotester map` (new module; generated section, +2 lines).

**SA1 note — no enum change was needed.** `SourceKind.TEXT` and `SourceKind.DOC` already exist in
`src/autotester/schema/enums.py:9-16`. The seam converges on the existing enum and the existing
`sources.jsonl` (`store.add_source`); no second store, no second enum. AUDIO/DRIVE/EMAIL are absent
by design (this unit does not add them and does not break the enum for them).

## How to verify (commands + expected)

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py -v` → all pass.
2. `PYTHONUTF8=1 uv run pytest tests/test_schema.py tests/test_store.py tests/test_ingest.py` → pass
   (Source/ingest extended, not broken).
3. `uv run ruff check src tests scripts` → clean.
4. `uv run autotester doctor` → clean.

## Actual outputs (pasted)

```
$ PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py -v
collected 11 items
tests\test_source_adapters.py ...........                                [100%]
============================= 11 passed in 0.26s ==============================
```

```
$ PYTHONUTF8=1 uv run pytest tests/test_schema.py tests/test_store.py tests/test_ingest.py
....................................                                     [100%]
36 passed in 0.44s
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

## Capability coverage (C7 mutation duty — single-hunk falsifying edit per claim)

Green baseline for every row: the `11 passed` run above. Each mutation is a single hunk in one
`src/` file, applied, the named test re-run RED, then reverted (suite green again afterward).

| SA claim | Falsifying edit (single hunk) | Defending test | Result |
|---|---|---|---|
| **TEXT-verbatim** (SA-table) | `adapters.py` `text=text` → `text=text[:-1]` | `test_text_is_stored_verbatim` | GREEN→RED: `AssertionError` at `:54` — stored `Second line` != `Second line.` |
| **DOC-extract** (SA-table) | `extract.py` `"\n".join(paragraphs)` → `"".join(paragraphs)` | `test_doc_extracts_docx_paragraph_text` | GREEN→RED: `AssertionError` at `:84` — paragraphs concatenated with no separator |
| **SA2-dedupe** | `adapters.py` `if existing.sha256 == digest:` → `… and False:` | `test_same_bytes_register_once`, `test_same_pasted_text_registers_once` | GREEN→RED: `AssertionError` at `:121` — `second.created` True, two rows written |
| **SA5-honest-degradation** | `adapters.py` `note = (…extraction_error…)` → `note = None` | `test_corrupt_doc_registers_with_extraction_error_not_empty`, `test_pdf_degrades_honestly_without_a_dependency`, `test_doctype_bearing_docx_is_refused_as_extraction_error` | GREEN→RED: `AssertionError` at `:149` — `source.notes is None`, degradation silent |

Raw RED output for each mutation was captured during the run and matches the table (assertion lines
54, 84, 121, 149). All four hunks reverted; final `11 passed` + doctor clean confirmed post-revert.

## Live browser evidence

**Not UI-touching — source-adapter/schema layer; no UI surface changed.** This unit adds
`src/autotester/sources/` (seam + extraction) and tests only. No route, template, or `ui/` file was
touched; no intake UI was wired in phase-1a. Changed paths: `src/autotester/sources/*`,
`tests/test_source_adapters.py`, `tests/fixtures/sample_doc.{md,txt}`, `docs/MAP.md` (generated).

## Decision surfaced to the checker/Umesh (non-blocking)

`.pdf` text extraction needs a pure-python dependency (e.g. `pypdf`) that this repo does not declare;
adding one is a real decision. The contract's open-question #1 default is "stdlib-first, no new
heavyweight dependency" and its stdlib list (`.md/.txt/.docx via zip+xml`) **omits `.pdf`**, so
phase-1a delivers `.txt/.md/.docx` fully and degrades `.pdf` to an honest `extraction_error` (SA5),
matching that default. Wiring PDF (pure-text via a dep, scanned-image via Gemini) is a clean
follow-on unit. Flagged here rather than guessed.
