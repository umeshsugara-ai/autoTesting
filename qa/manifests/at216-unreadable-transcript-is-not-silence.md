# Manifest — at216-unreadable-transcript-is-not-silence

**Unit:** AT-216 — `analyze_video` treats an unreadable transcript as "no speech", so the model is told a recording with narration is silent
**Contract:** `qa/contracts/video-learning.md` (VL1, VL1b, VL5) · `qa/contracts/ingest.md` (I8) · `qa/contracts/core-invariants.md` (C3, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-216 (medium, open → fixed)

## Why

VL1: *"an unreadable sidecar is a third state (`engine="unreadable"`), never folded into either of the
other two."* Ingest already honours this (`stages/ingest.py::load_sidecar` + `narration_block`, AT-134).
The ensemble path did not, twice:

1. **`analyze_video.load_transcript`** (the AT-216 finding) caught any sidecar parse error and returned
   `None`, the value for a recording nobody transcribed. The cause was discarded.
2. **`analyze_video.build_chunk_prompt`** (found while fixing 1, same defect one function down) rendered
   `"(no speech detected — do not invent dialogue)"` for EVERY transcript without segments. That
   includes the `Transcript(engine="unreadable")` that `media_prep` itself persists for a bad sidecar.
   Production takes that path, so fixing only 1 would have changed nothing a model sees.

**Why this matters now.** In today's Pathlynks depth study (two real tester recordings, analysed per
10-minute chunk, outside this repo's pipeline), a model given a recording with a silent audio track
confidently produced a full invented narration. How the narration state is described to a model
decides what it will make up, so a false "no speech detected" in a block labelled ground truth is not a
cosmetic string.

## What changed

- `src/autotester/stages/analyze_video.py:31` — imports `load_sidecar, narration_block` from
  `stages/ingest.py`, and drops the now-unused `SIDECAR_SUFFIX` import.
- `src/autotester/stages/analyze_video.py:56-67` — `load_transcript` falls back to `ingest.load_sidecar`
  instead of its own copy of the sidecar loader. A malformed sidecar now yields
  `Transcript(engine="unreadable")`. That removes a second implementation of one concept (C3).
- `src/autotester/stages/analyze_video.py:78` — `build_chunk_prompt` starts from
  `narration_block(transcript)`: silence for absent/none, "could not be read" for unreadable. The
  per-chunk slice still overrides it when there are segments, so VL5 behaviour is unchanged.
- `tests/test_analyze_video.py` — three tests:
  - `test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript`
  - `test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent` (end to end through `analyze`
    with a spy provider: every chunk prompt)
  - `test_an_unreadable_transcript_saved_by_media_prep_is_not_rendered_as_silence` (the persisted path)

## How to verify (commands + expected)

- `uv run pytest tests/test_analyze_video.py` → `13 passed`
- `uv run pytest tests/test_analyze_video.py tests/test_analyze_cache.py tests/test_ingest*.py tests/test_media_prep.py` → `67 passed`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at216-unreadable-transcript-is-not-silence/mutations.json` → `2/2 mutations killed`
- `uv run pytest` → green (below)

## Actual outputs (from maker's own run)

Test-first. With `analyze_video.py` at HEAD and the three new tests present, all three fail on their own
assertions:

```
E       assert (None is not None)
E           AssertionError: assert 'could not be read' in '# ingest_video_v1 ... (prompt text) ...'
FAILED tests/test_analyze_video.py::test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript
FAILED tests/test_analyze_video.py::test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent
FAILED tests/test_analyze_video.py::test_an_unreadable_transcript_saved_by_media_prep_is_not_rendered_as_silence
3 failed, 10 passed in 0.74s
```

After:

```
$ uv run pytest tests/test_analyze_video.py
13 passed in 0.51s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

Full suite (`uv run pytest`, bare):

```
1371 passed, 2 skipped, 32 xfailed, 1 warning in 351.12s (0:05:51)
```

The count includes tests from the other maker loop working in this tree.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| a malformed sidecar is loaded as `unreadable`, not `None` (AT-216) | `test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript` | `return load_sidecar(source)` → `return None` | KILLED (row 1) |
| an unreadable transcript is never rendered to a model as silence | `test_an_unreadable_transcript_saved_by_media_prep_is_not_rendered_as_silence` | `narration = narration_block(transcript)` → the old hardcoded "no speech detected" line | KILLED (row 2) |

The end-to-end test fails under both edits, and each edit also fails its own isolating test:

```
$ uv run python scripts/mutation_check.py qa/evidence/at216-unreadable-transcript-is-not-silence/mutations.json
KILLED  AT-216 reopens: a malformed sidecar is swallowed into None, the same as no transcript  (pytest exit 1)
    claims to kill : tests/test_analyze_video.py::test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript, tests/test_analyze_video.py::test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent
    actually failed: tests/test_analyze_video.py::test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript, tests/test_analyze_video.py::test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent
KILLED  the chunk prompt asserts silence for an unreadable transcript (the AT-134 defect on the analyze path)  (pytest exit 1)
    claims to kill : tests/test_analyze_video.py::test_an_unreadable_transcript_saved_by_media_prep_is_not_rendered_as_silence, tests/test_analyze_video.py::test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent
    actually failed: tests/test_analyze_video.py::test_an_unreadable_transcript_saved_by_media_prep_is_not_rendered_as_silence, tests/test_analyze_video.py::test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent

2/2 mutations killed
```

**Unchanged behaviour, pinned by existing tests that still pass:** a chunk gets only its own narration
(`test_a_chunk_gets_only_its_own_narration`), and a chunk with no speech says "no speech in this
section" (`test_a_silent_section_says_so_rather_than_leaving_a_gap`). A valid sidecar is still reused
verbatim, because `ingest.load_sidecar` calls the same `Transcript.from_sidecar` (VL1b).

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/stages/analyze_video.py` (the text
of the prompt sent to a vision model) and `tests/test_analyze_video.py`. No template, route or rendered
field changes. The analysis a Sources page later shows depends on a model's reading, which this unit
cannot make deterministic and does not claim to.

## Known limits (disclosed, not claimed)

- **No live model run.** The claim is about the prompt text, pinned with a spy provider. Whether a real
  model then stops inventing narration is not measured here.
- **The cause is still not named.** "Unreadable" says a sidecar failed to parse, not why (bad JSON vs
  wrong shape). AT-216 asked that the loss be visible, and it now is, in the prompt and in
  `Transcript.engine`. No log line or `VideoAnalysis` field records the exception text.
- **A hand-inserted scratch step.** To prove the persisted-path test failed without the fix, I briefly
  ran `git stash push -- src/autotester/stages/analyze_video.py` on the shared tree and popped it
  straight back. It touched only this unit's file; the diff above is intact.

## Status: ready-for-check
