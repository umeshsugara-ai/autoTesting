# Manifest — T-162 phase-1b — AUDIO source adapter (completes phase-1)

- **Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035). AUDIO row of the phase-1 table +
  criteria SA1–SA6.
- **Goal task:** T-162 (multi-source adapters — phase-1b: AUDIO; DRIVE/EMAIL remain phase-2).
- **Fix cycle:** 1 of 3.
- **Dual check: required** (T-162 is CRITICAL, and this unit touches the credential boundary SA3).
- **Issues addressed:** none — new feature (fast-follow of `t162-source-adapters-1a`).
- **Status:** ready-for-check.

## Scope delivered (phase-1b)

The **AUDIO** adapter: `.mp3`/`.wav`/`.m4a`/`.ogg`/`.opus` uploads become content-addressed AUDIO
`Source` rows in the SAME `sources.jsonl` phase-1a already built, transcribed **Gemini-first**
through the existing Provider seam (`providers/base.py::Provider.see_video` — no new vendor, no new
abstract method), with `media/transcribe.py`'s Whisper subprocess as the no-API fallback and
`media/probe.py` reused to tell a corrupt file from "no engine available". Phase-1 (TEXT + DOC +
AUDIO) is now complete; DRIVE/EMAIL stay phase-2.

**Design call made without escalating:** the brief said to STOP if the Provider seam genuinely
lacked an audio/transcription method and adding one was a real design decision. It doesn't need one:
`Provider.see_video(path, prompt, schema)` already uploads a media file and asks Gemini for
structured output shaped however the caller likes (`providers/gemini.py::_contents` just uploads
whatever `path` is — nothing in the mechanism is video-specific). AUDIO reuses that method unchanged,
asking for a transcript schema instead of a screen reading, so no change to `Provider`'s abstract
surface was needed and no other provider (`AnthropicProvider`, `MockProvider`,
`LangChainFallbackProvider`) had to grow a new method.

**Known, stated simplification:** `media/chunks.py` long-file chunking (also named in the AUDIO row)
is not wired — Gemini's file API takes a voice note or lecture-length recording whole, so phase-1b
sends the file once. Chunking a multi-hour recording is a real fast-follow, flagged here rather than
half-built and left untested. `media/probe.py` IS reused (corruption detection, see SA5 below).

## What changed (file:line)

- **`src/autotester/schema/enums.py:12`** — `SourceKind.AUDIO = "audio"` added. SA1: enum only,
  nowhere else. TEXT/DOC/AUDIO now three members; DRIVE/EMAIL still absent by design.
- **`src/autotester/sources/audio.py`** (new, 151 lines) — Gemini-first transcription:
  - `AUDIO_SUFFIXES` (`:40`) — the five accepted extensions.
  - `TRANSCRIBE_PROMPT` (`:42`) — the fixed prompt asked of Gemini (verbatim segments, no
    summarising/inventing).
  - `GeminiSegment`/`GeminiTranscription` (`:51`, `:65`) — the structured-output schema passed to
    `Provider.see_video`; `extra="forbid"`, transcription fields only (SA6).
  - `TranscriptionOutcome` (`:73`) — `(transcript, note)`, `extract.py::Extraction`'s shape widened
    for AUDIO's two degradation paths.
  - `transcribe_audio(path, source_id, *, provider, secrets)` (`:87`) — dispatches Gemini-first vs.
    straight-to-Whisper when no provider/unavailable.
  - `_via_gemini` (`:114`) — calls `assert_no_raw_secrets(TRANSCRIBE_PROMPT, secrets)` **before**
    `provider.see_video` (SA3), then builds a `Transcript` (`engine=f"gemini:{provider.label}"`) or
    an `extraction_error` note when Gemini returns zero segments.
  - `_via_whisper` (`:135`) — calls `media.transcribe.transcribe` unmodified; `engine != "none"`
    (a sidecar or a real whisper reading, even a silent one) → `Transcript` + a `"degraded: ..."`
    note (SA5); `engine == "none"` → `media.probe.probe` decides corrupt (`duration_s <= 0`,
    `extraction_error`) vs. no-engine-available (`extraction_error`, different reason), never a
    silent empty transcript.
- **`src/autotester/sources/adapters.py`** — `register_audio` (`:115`, 8 lines) validates via
  `_require_audio_file` (`:143`), dedupes via the existing `_existing_by_digest` (SA2, unchanged),
  and delegates to `_add_audio_source` (`:156`, 20 lines) which mints the content-addressed id from
  a throwaway `Source` instance (so the `Transcript` can cite it before the real row exists — SA4),
  calls `transcribe_audio`, persists the `Source` with `notes=outcome.note`, and
  `store.save_transcript(outcome.transcript)` when there is one — the exact `ProjectStore` method
  VIDEO already uses (`store/project_store.py:209`), no second store.
- **`src/autotester/sources/__init__.py`** — exports `register_audio`, `AUDIO_SUFFIXES`,
  `TranscriptionOutcome`, `transcribe_audio` alongside the phase-1a exports.
- **`tests/test_source_adapters.py`** — trimmed back to TEXT/DOC only (unchanged tests, moved
  nothing else) after the split below; still 11 tests, still green.
- **`tests/test_source_adapters_audio.py`** (new, 218 lines) — 8 AUDIO tests. Split into its own
  file because `uv run autotester doctor`'s file-length rule (≤300 lines) flagged the combined file
  at 372 lines; TEXT/DOC stayed in the original file per the contract's "extend
  tests/test_source_adapters.py" instruction, AUDIO went to a sibling file in the same suite.
- **`docs/MAP.md`** — regenerated via `uv run autotester map` (new module; generated section only).

## How to verify (commands + expected)

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py -v` → 11 passed (phase-1a, unchanged).
2. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters_audio.py -v` → 8 passed (new, this unit).
3. `PYTHONUTF8=1 uv run pytest tests/test_schema.py tests/test_providers.py tests/test_media.py tests/test_ingest.py` → all pass (Source/enum/provider/media extended, not broken).
4. `uv run ruff check src tests scripts` → clean.
5. `uv run autotester doctor` → clean.

## Actual outputs (pasted)

```
$ PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_schema.py tests/test_providers.py tests/test_media.py tests/test_ingest.py -v
collected 65 items

tests\test_source_adapters.py ...........                                [ 16%]
tests\test_source_adapters_audio.py ........                             [ 29%]
tests\test_schema.py ...........                                         [ 46%]
tests\test_providers.py ........                                         [ 58%]
tests\test_media.py ...................                                  [ 87%]
tests\test_ingest.py ........                                            [100%]

============================= 65 passed in 0.54s ==============================
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

Green baseline for every row: the `65 passed` run above (specifically
`tests/test_source_adapters_audio.py`'s 8/8). Each mutation is a single hunk in one `src/` file,
applied, the named test re-run RED, then reverted — full suite green again after every revert
(re-confirmed: see "Actual outputs" above, captured post-revert).

| Capability | Falsifying edit (single hunk) | Defending test | Result |
|---|---|---|---|
| **AUDIO-transcribes-via-provider** | `audio.py` `_via_gemini`: `engine=f"gemini:{provider.label}"` → `engine=f"{provider.label}"` | `test_audio_transcribes_via_gemini_provider` | GREEN→RED: `AssertionError: assert False … 'mock'.startswith('gemini:')` at the `transcript.engine.startswith("gemini:")` line |
| **SA2-dedupe** | `adapters.py` `register_audio`: `if existing is not None:` → `if False and existing is not None:` | `test_audio_dedupes_same_bytes_without_re_transcribing` | GREEN→RED: `AssertionError: assert True is False` — `second.created` came back `True` and the audio was re-transcribed (`notes` shows a fresh `extraction_error` from the second, un-mocked call) instead of `False` |
| **SA5-whisper-fallback-with-note** | `audio.py` `_via_whisper`: `note = f"degraded: {degraded_reason} …"` → `note = f"info: {degraded_reason} …"` | `test_audio_falls_back_to_whisper_with_a_degradation_note` | GREEN→RED: `AssertionError: assert False` — `notes` was `'info: no Gemini provider was configured -- used the whisper fallback'`, fails `.startswith("degraded:")` |
| **SA5-corrupt-extraction_error** | `audio.py` `_via_whisper`: the corrupt-branch note `"extraction_error: the audio file could not be read …"` → `"unreadable_audio: …"` | `test_corrupt_audio_registers_with_extraction_error_not_empty` | GREEN→RED: `AssertionError: assert False` — `notes` was `'unreadable_audio: …'`, fails `.startswith("extraction_error")` |
| **SA4-segment-provenance** | `adapters.py` `_add_audio_source`: `transcribe_audio(path, provisional_id, …)` → `transcribe_audio(path, "wrong_id", …)` | `test_audio_transcript_cites_source_id_and_segments` | GREEN→RED: `AssertionError: assert None is not None` — the transcript was saved under `"wrong_id"`, so `store.load_transcript(result.source.id)` (the real id) returned `None` |

All five hunks were applied and reverted one at a time (not stacked); each RED was captured in full
before reverting, and the targeted test plus the full six-file suite were re-run GREEN after every
revert. Two more tests exist beyond this table and are not claimed as capability rows but strengthen
confidence: `test_audio_falls_back_to_whisper_when_the_gemini_call_itself_fails` (a `ProviderError`
mid-call, not just an unavailable provider, still degrades with a note) and
`test_audio_gemini_call_is_gated_by_assert_no_raw_secrets` (SA3 — a secret planted in the prompt via
monkeypatch raises `ValueError` before `provider.see_video` is ever called, proven by
`provider.prompts == []` afterward) and
`test_audio_shares_the_one_store_and_enum_with_text_and_doc` (SA1 — TEXT+DOC+AUDIO land in one
`sources.jsonl`, `SourceKind.AUDIO` is a member of the one enum).

## Live browser evidence

**Not UI-touching — source-adapter/provider layer.** This unit adds
`src/autotester/sources/audio.py`, extends `src/autotester/sources/adapters.py` and
`src/autotester/sources/__init__.py`, adds one enum member to `src/autotester/schema/enums.py`, and
adds `tests/test_source_adapters_audio.py`. No route, template, or `ui/` file was touched; no intake
UI was wired for AUDIO in phase-1b (matching phase-1a's TEXT/DOC, which also have none yet).
Changed/added paths:
`src/autotester/schema/enums.py`, `src/autotester/sources/audio.py`,
`src/autotester/sources/adapters.py`, `src/autotester/sources/__init__.py`,
`tests/test_source_adapters.py`, `tests/test_source_adapters_audio.py`, `docs/MAP.md` (generated).

## Decisions surfaced to the checker/Umesh (non-blocking)

1. **Reused `see_video` for audio rather than adding a new `Provider` method or role.** The brief
   said to stop and report if the seam genuinely lacked an audio/transcription method and adding one
   was a real design decision — it doesn't: `see_video`'s implementation (upload a file, ask for
   structured output) is not video-specific, so no `Provider` surface change was needed. Flagged here
   as a judgment call, not silently assumed.
2. **Long-file chunking deferred.** `media/chunks.py` is named in the contract's AUDIO row
   ("Track A3's media/probe+chunk reused") but only `probe` is exercised in phase-1b; chunking a
   multi-hour recording through Gemini (splitting via `plan_chunks`/`encode_chunks`, shifting
   segment timestamps by chunk offset, merging) is real, untested-here scope and would have added
   ffmpeg-dependent code with no test coverage in this cycle. Recommend a phase-1c follow-up if a
   recording longer than Gemini's own file-size ceiling shows up in practice.
