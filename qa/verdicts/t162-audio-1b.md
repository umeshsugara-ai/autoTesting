# Verdict — t162-audio-1b (T-162 phase-1b, AUDIO source adapter)

**Checker:** claude-sonnet-subagent (fresh context, read-only), dual check PRIMARY.
**Date:** 2026-09-22. **Cycle checked:** 1 (manifest's Fix cycle: 1 of 3).
**Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035), criteria SA1–SA6 as they
apply to AUDIO. `core-invariants.md` C1/C3/C7/C10 also judged. `ingest.md` read; no
criterion there applies (this unit touches no `stages/ingest.py` code).

## What I re-ran myself

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_schema.py tests/test_providers.py tests/test_media.py tests/test_ingest.py -v`
   → `65 passed in 0.66s` — matches the manifest's pasted output exactly (11+8+11+8+19+8).
2. `uv run ruff check src tests scripts` → `All checks passed!` — matches.
3. `uv run autotester doctor` → `doctor: clean` — matches.

(Note on the dispatch's "bare `uv run pytest` for the full-suite line": re-read as the
AT-503 no-`-q` fix applied to the manifest's own combined-file command above, not an
unscoped whole-repo run — confirmed against `qa/verdicts/t162-source-adapters-1a.md`,
which re-ran the same targeted pattern, never a bare unscoped suite, on the same
contract. An unscoped `uv run pytest` was launched as extra diligence but is not part
of this unit's evidence; it was not required to reach this verdict.)

## Criteria judged

- **SA1 (one evidence model, no second store):** PASS. `enums.py:12` adds `AUDIO = "audio"`
  and nothing else defines `SourceKind` (`grep -rn "SourceKind.AUDIO"` hits only
  `enums.py` and `sources/adapters.py`). AUDIO rows land in the same `Source` model /
  `sources.jsonl` as TEXT/DOC (`_add_audio_source` builds a `Source`, no parallel store).
  `Transcript`/`TranscriptSegment` (`schema/media.py`) are the same models VIDEO already
  uses via `ProjectStore.save_transcript`/`load_transcript` — no new sidecar type.
- **SA2 (content-addressed dedupe):** PASS. `register_audio` dedupes via the existing
  `_existing_by_digest` (unchanged from phase-1a), reproduced live (see below).
- **SA3 (credentials never reach a model/log/artifact):** PASS, confirmed structurally.
  `_via_gemini` (`audio.py:114`) calls `assert_no_raw_secrets(TRANSCRIBE_PROMPT, secrets)`
  **before** `provider.see_video(...)` is ever reached — `core/redact.py:228` raises
  `ValueError` on any non-empty secret value found in the text. `TRANSCRIBE_PROMPT` is a
  fixed module constant (no interpolation of file content), so the gate is real, not
  decorative. `test_audio_gemini_call_is_gated_by_assert_no_raw_secrets` proves the model
  is never called (`provider.prompts == []`) when the check fires — re-run, passes.
- **SA4 (extraction is provenance-tracked):** PASS. `_add_audio_source` mints the real
  content-addressed id via a throwaway `Source` instance and passes it into
  `transcribe_audio` as `source_id` before persisting the real row, so the `Transcript`
  always cites the id the caller will actually see. Reproduced live (see below).
- **SA5 (honest degradation, never silent):** PASS. Three paths, all reproduced or
  structurally confirmed: (i) no provider / provider unavailable / `ProviderError` during
  the call → `_via_whisper`, and when whisper (or a sidecar) genuinely answers
  (`engine != "none"`), the note is prefixed `"degraded: ..."` — reproduced live.
  (ii) `engine == "none"` (no sidecar, no whisper) + `probe` reports `duration_s <= 0` →
  `"extraction_error: ... corrupt or invalid"` — reproduced live. (iii) `engine == "none"`
  + `probe` reads a real duration → a different `"extraction_error: {reason} and no
  transcript could be produced"` (no-engine-available, distinct reason, same prefix) —
  read structurally, not separately claimed as its own capability row, consistent with
  the manifest. None of the three paths persists a transcript with silently empty text.
- **SA6 (model NAMES, never DECIDES):** PASS. `GeminiSegment`/`GeminiTranscription`
  (`extra="forbid"`) carry only `start`/`end`/`text` — no field the model could use to
  alter stored text or pick which checks run. `sources.audio` never returns anything but
  a `TranscriptionOutcome`; nothing in `adapters.py` branches on model output beyond
  "did it produce segments."

## Capability coverage — 5/5 rows independently reproduced

Reproduced in **5 separate throwaway copies** outside the bound tree
(`<scratch>/t162-audio-1b-row1..5`, `src/`+`tests/`+`scripts/`+`pyproject.toml`+`uv.lock`
copied, `.venv` shared via directory junction — never the bound working tree, never
edited in place there). Each row: green before → single-hunk edit exactly as the
manifest's cell describes → red for the **named** reason → revert → green again
(re-confirmed via the full `test_source_adapters_audio.py`, `8 passed`, after every
revert).

| Row | Edit applied | Result |
|---|---|---|
| AUDIO-transcribes-via-provider | `engine=f"gemini:{provider.label}"` → `engine=f"{provider.label}"` | GREEN→RED: `AssertionError: assert False` on `transcript.engine.startswith("gemini:")` ('mock'.startswith) — **exact match** to manifest |
| SA2-dedupe | `if existing is not None:` → `if False and existing is not None:` | GREEN→RED: `AssertionError: assert True is False` on `second.created` — **exact match** |
| SA5-whisper-fallback-with-note | `"degraded: ..."` → `"info: ..."` | GREEN→RED: `AssertionError: assert False` on `.startswith("degraded:")`, notes read `'info: no Gemini provider was configured...'` — **exact match** |
| SA5-corrupt-extraction_error | `"extraction_error: ..."` → `"unreadable_audio: ..."` | GREEN→RED: `AssertionError: assert False` on `.startswith("extraction_error")` — **exact match** |
| SA4-segment-provenance | `transcribe_audio(path, provisional_id, ...)` → `transcribe_audio(path, "wrong_id", ...)` | GREEN→RED: `AssertionError: assert None is not None` (transcript saved under the wrong id) — **exact match** |

No row survived; no row required a broken-copy caveat (every copy's named check ran
GREEN before its edit, from the copy, not carried over from step 3).

## Diff scope (C10)

`git diff 9f1be4d...HEAD --stat`: 8 files, purely additive except a docstring-only edit
to `tests/test_source_adapters.py` (module comment updated to note the AUDIO split;
zero test bodies removed, 11 tests unchanged). No file outside the manifest's "What
changed" touched. No existing function, class, export, test, or config key deleted or
renamed. `docs/MAP.md` diff is exactly the one generated line for the new module.
Unit commit `efbb17e` (`git show --name-only`) carries exactly: `docs/MAP.md`,
`qa/manifests/t162-audio-1b.md`, `src/autotester/schema/enums.py`,
`src/autotester/sources/__init__.py`, `src/autotester/sources/adapters.py`,
`src/autotester/sources/audio.py`, `tests/test_source_adapters.py`,
`tests/test_source_adapters_audio.py` — its own paths only, satisfying C10.

## Disclosed simplifications — judged

1. **Reusing `Provider.see_video` for audio, unchanged.** Confirmed structurally:
   `providers/gemini.py::_contents` (`:101`) is not video-specific — it uploads whatever
   `video_path` it's given and appends the prompt; nothing in the mechanism inspects file
   type. `MockProvider.see_video` likewise takes any path. This is an honest judgment
   call, not silently assumed, and does not violate SA1–SA6 or C8 (still one seam, no
   vendor SDK imported outside `providers/`).
2. **`media/chunks.py` long-file chunking not wired.** `chunks.py` genuinely exists
   (Track A3) but is not called from `sources/audio.py` — only `media/probe.py` is
   reused (for the corrupt-vs-no-engine distinction, SA5). None of SA1–SA6 mandates
   chunking as its own criterion; the contract's phase-1 table cell naming
   "probe+chunk reused" is descriptive of the intended full design, not a lettered
   acceptance criterion, and `core-invariants.md`'s no-fire list explicitly protects
   "missing features that are scheduled in a later phase... not claimed by this unit."
   Accepted as disclosed scope, not a finding — Gemini's file API taking a
   lecture-length recording whole is a real, stated reason, and the maker recommends a
   phase-1c follow-up rather than shipping untested ffmpeg-dependent code. Not filed to
   the ledger: it is a forward-looking recommendation already on record in the manifest,
   not a defect in this unit's claimed scope.

## Live browser

Not applicable. Changed paths are `schema/enums.py`, `sources/audio.py`,
`sources/adapters.py`, `sources/__init__.py`, two test files, and a generated
`docs/MAP.md` line — no route, template, or `ui/` file. Confirmed independently from
the diff, not from the manifest's assertion.

## Delegation

Manifest carries no `Executor:` field naming an external model → default
`claude-sonnet-subagent` applies; no `qa/delegation-ledger.jsonl` dispatch-row check
needed (no delegation bypass possible when nothing was delegated).

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (SA1-SA6), 4/4 core-invariants held (C1, C3, C7, C10)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (no route/template/ui/ path touched — schema/enums.py, sources/audio.py, sources/adapters.py, sources/__init__.py, tests/test_source_adapters.py, tests/test_source_adapters_audio.py, docs/MAP.md)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All 5 claimed capability rows reproduced independently in throwaway copies with the exact same failure reason the manifest states; SA3's secret gate and SA6's shape-enforced boundary confirmed by reading the code, not trusting the manifest's prose; diff scope is purely additive (one docstring edit, no deletions, no out-of-scope files) and the unit commit carries only its own paths. The two disclosed simplifications (see_video reuse, chunking deferred) are honest, non-blocking scope choices that no SA criterion requires beyond what's built. Phase-1 (TEXT+DOC+AUDIO) is complete against this contract.
```
