# Verdict — t162-audio-1b (INDEPENDENT DUAL CHECK, checker B)

**Date:** 2026-09-22
**Cycle checked:** 1
**Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035) — AUDIO row + SA1–SA6, plus
`core-invariants.md` (all) and `ingest.md` (read for the VIDEO-seam-reuse boundary; no
criterion there applies — this unit adds no ingest-stage code).
**Manifest:** `qa/manifests/t162-audio-1b.md`
**Project root (bound):** `D:/autoTesting/.worktrees/t162-audio-1b`
**Role:** second, independent checker of a CRITICAL unit (SA3 credential boundary). This
verdict was formed with no access to the primary checker's verdict or reasoning.

## What I re-ran myself

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_schema.py tests/test_providers.py tests/test_media.py tests/test_ingest.py -v`
   → `65 passed in 0.74s` (matches the manifest's pasted output).
2. `uv run ruff check src tests scripts` → `All checks passed!`
3. `uv run autotester doctor` → `doctor: clean`
4. Full project suite, `PYTHONUTF8=1 uv run pytest` (bare, no CLI `-q`, AT-503), in the bound
   tree → `1557 passed, 5 skipped, 32 xfailed, 1 warning in 643.45s`, exit 0. Nothing broken
   project-wide.
5. `git diff 9f1be4d...HEAD --stat` and the full diff, against the stated base commit
   (unit commit `efbb17e` on `wave/t162-audio-1b`).
6. Read the code directly: `sources/audio.py`, `sources/adapters.py`, `schema/enums.py`,
   `sources/__init__.py`, `core/redact.py::assert_no_raw_secrets`, `providers/base.py::Provider`,
   `media/transcribe.py`, `media/probe.py`, `store/project_store.py` (`save_transcript`/
   `load_transcript`), `schema/project.py::Source.model_post_init`.
7. Capability coverage: reproduced all 5 rows independently in a THROWAWAY COPY outside the
   bound tree (`…/scratchpad/t162-audio-1b-row`, a full `cp -r` of the worktree). Green-before
   confirmed in the copy itself (not reused from step 1), then each single-hunk falsifying edit
   applied one at a time, confirmed RED for the named assertion, reverted, and the local suite
   re-confirmed green. After the last revert, `diff -r` against the bound tree's `audio.py` and
   `adapters.py` came back empty — the copy matches the bound tree exactly; the bound tree itself
   was never touched.

## Criteria — SA1–SA6

- **SA1 — one evidence model, no second store.** `grep` + read of `schema/enums.py:12` confirms
  `AUDIO` is added ONLY there; TEXT/DOC/AUDIO now three members, DRIVE/EMAIL absent. All three
  kinds write to the same `sources.jsonl` via `ProjectStore.add_source` — confirmed by
  `test_audio_shares_the_one_store_and_enum_with_text_and_doc`, re-run green. **MET.**
- **SA2 — content-addressed dedupe.** `register_audio` keys on `file_sha256(path)`, checks
  `_existing_by_digest` (the same helper TEXT/DOC use), and does not call `transcribe_audio` on
  the dedupe path. Row 2 below falsifies this specifically. **MET.**
- **SA3 — credentials never reach a model.** `_via_gemini` (`audio.py:119`) calls
  `assert_no_raw_secrets(TRANSCRIBE_PROMPT, secrets)` **before** `provider.see_video` on the very
  next line. Re-read `core/redact.py::assert_no_raw_secrets` — it raises `ValueError` on any
  non-empty secret value found in the text, unconditionally (AT-002, no length floor).
  `test_audio_gemini_call_is_gated_by_assert_no_raw_secrets` re-run green, and it asserts
  `provider.prompts == []` afterward — the call never reached the mock at all, not just that an
  exception was raised somewhere. **MET.**
- **SA4 — provenance to the Source id (+ segments for audio).** `_add_audio_source` mints a
  `provisional_id` from a throwaway `Source(...).id` before transcribing, then persists the real
  `Source` afterward. I independently read `Source.model_post_init`
  (`schema/project.py:114-119`): the id is `content_id("src", {"k": kind, "v": sha256})` —
  deterministic on `(kind, sha256)` alone, with no dependency on when or how many times the
  constructor runs. So the throwaway instance and the real one necessarily produce the identical
  id; this is not a coincidence the tests happen to exercise, it is guaranteed by the id formula.
  Row 5 below falsifies the wiring. **MET.**
- **SA5 — honest degradation, never silent.** Three paths, all exercised: no-provider → Whisper
  fallback WITH a `"degraded: …"` note (row 3, and a second test covers the mid-call
  `ProviderError` variant, both re-run green); corrupt/unreadable (Whisper absent, `probe`
  returns zeroed duration) → `extraction_error` note, `transcript=None`, never a fake empty
  transcript (row 4, and `test_corrupt_audio_registers_with_extraction_error_not_empty` asserts
  `store.load_transcript(...) is None` directly). **MET.**
- **SA6 — a model may NAME, never DECIDE.** `GeminiSegment`/`GeminiTranscription`
  (`extra="forbid"`) carry only `start`/`end`/`text` — no field through which Gemini's answer
  could select a check, alter stored text, or change control flow beyond "how many segments came
  back". Enforced by shape, matching the manifest's claim. **MET.**

## Capability coverage — reproduced independently, 5/5

| Row | Edit applied | Result in my throwaway copy |
|---|---|---|
| AUDIO-transcribes-via-provider | `engine=f"gemini:{provider.label}"` → `engine=f"{provider.label}"` | RED: `'mock'.startswith('gemini:')` is False — exact match to manifest |
| SA2-dedupe | `if existing is not None:` → `if False and existing is not None:` in `register_audio` | RED: `second.created` came back `True`, notes shows a fresh `extraction_error` (re-transcribed, un-mocked provider on the "second" call) |
| SA5-whisper-fallback-with-note | `note = f"degraded: …"` → `note = f"info: …"` | RED: `.startswith("degraded:")` is False |
| SA5-corrupt-extraction_error | `"extraction_error: …"` → `"unreadable_audio: …"` | RED: `.startswith("extraction_error")` is False |
| SA4-segment-provenance | `transcribe_audio(path, provisional_id, …)` → `transcribe_audio(path, "wrong_id", …)` | RED: `store.load_transcript(result.source.id)` returns `None` — transcript filed under the wrong key |

Every row failed for the assertion the row names (not a parse/import cascade), and every revert
returned the copy to byte-identical with the bound tree. No row is `UNVERIFIED`.

## Diff scope (C10 / step 4c)

`git diff 9f1be4d...HEAD --stat`: `docs/MAP.md` (+1, generated), `qa/manifests/t162-audio-1b.md`
(new), `schema/enums.py` (+1), `sources/__init__.py` (exports only), `sources/adapters.py`
(+97/-… additive: new `register_audio`/`_require_audio_file`/`_add_audio_source`),
`sources/audio.py` (new file), `tests/test_source_adapters.py` (docstring-only reword, zero test
functions added/removed/changed — diffed line-by-line, confirmed), `tests/test_source_adapters_audio.py`
(new file). **No function, class, test, route, or config key was deleted or renamed.** Nothing
outside "What changed" was touched. Clean.

## The two disclosed simplifications

1. **Reusing `Provider.see_video` for audio instead of a new method.** I independently read
   `providers/base.py:55-62`: the signature and docstring (`path, prompt, schema, options`) are
   already medium-agnostic — "upload a file, ask for structured output" — nothing about it is
   video-specific in implementation, only in name. No `SA` criterion requires a new abstract
   method, and C8 (provider-agnostic, no vendor SDK outside `providers/`) is unaffected either
   way. **Acceptable engineering judgment, not a violation** — and it was surfaced rather than
   silently assumed, which is what the brief asked for.
2. **`media/chunks.py` not wired; only `probe.py` is.** The contract's phase-1 SCOPE TABLE
   mentions "Track A3's media/ probe+chunk reused" as descriptive text for the AUDIO row, but the
   *criteria* SA1–SA6 — the thing actually graded — say nothing about chunking, and
   `core-invariants.md`'s no-fire list explicitly excludes "missing features scheduled in a later
   phase and not claimed by this unit." Chunking is disclosed, not claimed, and no test asserts
   it. Gemini's file API accepts a whole recording per the manifest's stated reasoning (unverified
   independently — no live Gemini call was made in this check, matching the contract's
   `MockProvider`-only posture for this unit). **Judged as acceptable disclosed scope, not an SA
   violation** — same reasoning `ingest.md`'s no-fire list applies elsewhere in this repo to
   deferred phases.

## Mode D (live browser)

**Not applicable.** Changed paths are `schema/enums.py`, `sources/audio.py`,
`sources/adapters.py`, `sources/__init__.py`, `tests/test_source_adapters*.py`, `docs/MAP.md`
(generated) — no route, template, or `ui/` file, confirmed directly from the diff stat, not from
the manifest's claim.

## Issues addressed

None claimed ("new feature, fast-follow of t162-source-adapters-1a") — nothing to verify against
the ledger.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (SA1-SA6), 10/10 core-invariants criteria touched by this unit hold (C1 schema-first, C2 file-length, C3 one-place, C5 secrets, C7 verification/mutation duty, C8 provider-agnostic, C10 commit/diff scope; C4/C6/C9 untouched by this unit)
CAPABILITY-COVERAGE: 5/5 rows reproduced (independent throwaway copy, all green-before/red-after/reverted-green)
LIVE-BROWSER: not-applicable (schema/enums.py, sources/audio.py, sources/adapters.py, sources/__init__.py, tests/test_source_adapters*.py, docs/MAP.md — no UI/route/template path touched)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All SA1-SA6 criteria evidenced by independent re-derivation, not by trusting the manifest's prose — SA3's ordering, SA4's id-determinism, and SA2's dedupe were each traced through the actual code, not just the passing test. All 5 capability-coverage rows were independently reproduced in a throwaway copy with the bound tree untouched. Diff scope is purely additive (C10 clean) and the full 1557-test suite stays green. The two disclosed simplifications (see_video reuse, chunking deferral) are judged acceptable: neither is required by SA1-SA6, and the chunking gap is disclosed scope under core-invariants.md's no-fire list, not a silent omission.
```
