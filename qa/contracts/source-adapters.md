# Contract — SOURCE ADAPTERS (T-162) — DRAFT for Umesh's review

**Status:** DRAFT — authored 2026-09-21 by the maker from the T-162 gate interview
(`qa/gates/t162-contract-approval.md`, answered **(A)** by Umesh in chat 2026-09-21).
Nothing in `src/` implements this yet; this document is the review artifact. On approval
it becomes a D-0xx-authorized contract and the checker assumes ownership.
**Covers:** goal task T-162 (multi-source adapters: Google Drive, video, audio, document,
email and text into one evidence model) — **phase 1: TEXT, DOC, AUDIO** (VIDEO exists,
T-060/T-131); **phase 2 (declared, fast-follow unit): DRIVE (OAuth device flow), EMAIL
(.eml/.mbox local files only).**
**Owner:** /checker (on approval). **Criticality:** CRITICAL — T-163 (orchestrator),
T-164..T-169 all sit behind this stage.
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` B5-B9 (credentials
never reach a model/log/screenshot), `ingest.md` (the VIDEO half this extends, never
duplicates).

## Purpose

Any project's teaching material — typed text, an uploaded document, a voice note, a
screen recording, a Drive folder, an email thread — converges on ONE evidence model
(`Source`, already shipped in `schema/project.py`) with provenance, so the learn-or-
explore orchestrator (T-163) can consume every source kind through a single seam.
Adapters CONVERT; they never decide what the product is. Content-addressed (`sha256`)
dedupe: the same file uploaded twice is ONE Source.

## Phase-1 scope (build first)

| Kind | Input | Extraction path |
|---|---|---|
| `TEXT` | inline body / pasted text | stored verbatim on `Source.text`; no model call to register |
| `DOC` | .pdf/.docx/.md/.txt upload | text extraction (host-side, deterministic); Gemini only if pages are scanned images |
| `AUDIO` | .mp3/.wav/.m4a/.ogg/.opus | **Gemini-first** via the Provider seam (`providers/base.py`, Umesh's Gemini key; no new vendor); Track A3's `media/` probe+chunk reused; `media/transcribe.py` (Whisper) survives only as the no-API fallback |

## Criteria (checker to finalize wording at intake)

- **SA1 — One evidence model, no second store.** Every adapter converges on the existing
  `Source` model + `sources.jsonl` (C1/C3). New `SourceKind` values (`DRIVE`, `EMAIL`,
  plus `AUDIO` if absent at build time) are added to the enum in `schema/`, nowhere else.
- **SA2 — Content-addressed dedupe.** The same bytes registered twice is ONE Source
  (sha256); the UI says "already registered" instead of creating a duplicate row.
- **SA3 — Credentials never reach a model, log, or screenshot.** Drive OAuth refresh
  tokens are `SecretRef`s in the project `.env` (phase 2); email requires NO mailbox
  credentials in phase 1 (.eml/.mbox are local files). `assert_no_raw_secrets` gates any
  model call on extracted content.
- **SA4 — Extraction is provenance-tracked.** What the orchestrator later reads cites
  the Source id (and, for audio, the transcript segment) — same discipline as VIDEO's
  per-second SourceRefs.
- **SA5 — Degradation is honest, never silent.** No Gemini key -> audio falls back to
  Whisper with a note on the Source; an unreadable doc registers as a Source with an
  `extraction_error` note, never silently as empty text.
- **SA6 — A model may NAME, never DECIDE (D-017 boundary).** A model may summarise what
  a document says for the human; it may not choose which checks run or alter stored text.

## Phase-2 scope (declared now, built as a fast-follow unit)

- `DRIVE`: OAuth **device flow** (Umesh's answer #2) — interactive consent once, refresh
  token stored as a `SecretRef`; folder-scoped listing; every fetched file becomes a
  content-addressed DOC/VIDEO/AUDIO Source with its Drive id in `Source.url`.
- `EMAIL`: **.eml/.mbox local files only** (Umesh's answer #4); attachments extracted as
  DOC/VIDEO children; no IMAP/mailbox credential surface in this contract.

## Explicit no-fire list (do not raise these as findings)

- No IMAP/SMTP fetch, no mailbox credentials — phase 1 is local files only (gate answer #4).
- No service-account Drive auth — declined by Umesh (device flow chosen, answer #2).
- No Whisper replacement of Gemini for audio — Gemini-first is the recorded decision
  (answer #3); Whisper is the fallback, not a second competing path.
- The orchestrator (T-163) is NOT this contract — adapters produce Sources; what runs
  because of them is T-163's.

## Open questions for Umesh (blocking nothing else)

1. DOC text extraction library preference (pure-python vs a binary like pandoc) —
   default: stdlib-first (.md/.txt/.docx via zip+xml), no new heavyweight dependency.
2. Max upload size per Source (proposed: 200 MB; larger -> chunked like video already is).
3. Should TEXT sources be reviewable/editable in the UI before the orchestrator reads
   them (proposed: yes — the FlowSpec Review gate discipline, applied to Sources).