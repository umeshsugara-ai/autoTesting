# Manifest — at465-466-unreadable-narration-keeps-its-cause

**Unit:** AT-465 + AT-466 — an unreadable transcript sidecar loses its cause, a `{}` sidecar reads as silence, and `ingest prep` prints unreadable narration as "0 narration segment(s)"
**Contract:** `qa/contracts/video-learning.md` (VL1, VL1b) · `qa/contracts/core-invariants.md` (C1, C3, C7)
**Goal task:** none (issue-driven batch: one concept, the unreadable-narration state, across its three consumers)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-465 (low, open → fixed) · AT-466 (low, open → fixed)

## Why

Both issues were filed by the at216 cycle-1 checker while grepping every consumer of `Transcript`.

- **AT-466a, the cause is discarded.** `media/transcribe.py:63-66` and `stages/ingest.py:187-188` each
  wrapped `Transcript.from_sidecar` in their own `except Exception:` and returned a bare
  `engine="unreadable"`. That is two copies of one concept (C3), and neither kept the exception. Bad
  JSON, non-UTF-8 bytes and a wrong shape were indistinguishable.
- **AT-466b, `{}` is silence.** `from_sidecar` read `raw.get("segments", [])`, so a sidecar asserting
  nothing loaded as `engine="sidecar"` with no segments. Downstream that renders "no speech detected",
  which is VL1's forbidden claim of silence.
- **AT-465, the operator is told the same thing for both.** `cli_video.py:104-110` printed
  `{segments} narration segment(s)` and never read `engine`. So an unreadable sidecar printed
  "0 narration segment(s)", exactly like a recording with no narration.

## What changed

- `src/autotester/schema/media.py:36-37` — `Transcript.unreadable_reason: str | None` (default `None`,
  so every persisted `transcript.json` still loads; C1 `extra="forbid"` is unaffected).
- `src/autotester/schema/media.py:48-49` — `from_sidecar` raises `ValueError("sidecar has no segments
  list")` unless the top level is an object with a `segments` LIST.
- `src/autotester/schema/media.py:58-67` — new `Transcript.read_sidecar`, the ONE best-effort reader:
  `from_sidecar`, or `engine="unreadable"` with `unreadable_reason = "<ExceptionType>: <message>"`
  (truncated to 300 chars).
- `src/autotester/media/transcribe.py:60-63` and `src/autotester/stages/ingest.py:185` — both call
  `Transcript.read_sidecar` instead of their own try/except copies.
- `src/autotester/cli_video.py:104-110` — `ingest prep` prints
  `narration unreadable (<reason>)` for an unreadable transcript. The segment count line is unchanged for
  every other case.
- Tests:
  - `tests/test_schema_video.py` — `test_an_unreadable_sidecar_keeps_why_it_could_not_be_read`
    (`bad-json`→`JSONDecodeError`, `not-utf8`→`UnicodeDecodeError`, `empty-object` and
    `segments-not-a-list`→"segments") and `test_a_readable_sidecar_carries_no_unreadable_reason` (the
    real erp1 fixture: 6 segments, no reason).
  - `tests/test_media_prep.py` — `test_prep_tells_the_operator_the_narration_is_unreadable_and_why`
    drives the real `ingest prep` CLI.
  - `tests/test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep` and
    `tests/test_analyze_video.py::test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript`
    each gain one assertion that the cause survives.
  - `tests/test_ingest_real_cli.py` — the existing `test_a_malformed_sidecar_never_stops_an_ingest`
    parametrize gains `ids=[...]`, with no change to its cases (reason under "Known limits").

## How to verify (commands + expected)

- `uv run pytest tests/test_schema_video.py tests/test_media_prep.py tests/test_media.py tests/test_analyze_video.py tests/test_ingest_real_cli.py tests/test_ingest_persist.py` → `94 passed`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at465-466-unreadable-narration-keeps-its-cause/mutations.json` → `5/5 mutations killed`
- `uv run python scripts/mutation_check.py qa/evidence/at216-unreadable-transcript-is-not-silence/mutations.json` → `2/2 mutations killed` (the previous unit's spec still anchors and still holds)
- `uv run pytest` → green (below)

## Actual outputs (from maker's own run)

Test-first. With the source at HEAD and the new tests and assertions present:

```
FAILED tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[{not json-JSONDecodeError]
FAILED tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[\xff\xfe\x00bad-UnicodeDecodeError]
FAILED tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[{}-segments]
FAILED tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[{"segments": "hello"}-segments]
FAILED tests/test_schema_video.py::test_a_readable_sidecar_carries_no_unreadable_reason
FAILED tests/test_media_prep.py::test_prep_tells_the_operator_the_narration_is_unreadable_and_why
FAILED tests/test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep
7 failed, 44 passed in 2.29s
```

(The ids were renamed to `bad-json` / `not-utf8` / `empty-object` / `segments-not-a-list` afterwards; see
"Known limits".)

After:

```
$ uv run pytest tests/test_schema_video.py tests/test_media_prep.py tests/test_media.py tests/test_analyze_video.py tests/test_ingest_real_cli.py tests/test_ingest_persist.py
94 passed in 2.13s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

Full suite (`uv run pytest`, bare):

```
1382 passed, 2 skipped, 32 xfailed, 1 warning in 344.77s (0:05:44)
```

The count includes tests from the other maker loop working in this tree.

## Capability coverage (each new claim -> its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| an unreadable sidecar keeps its cause (AT-466a) | `…keeps_why_it_could_not_be_read[bad-json]` | `unreadable_reason=f"{type(exc).__name__}: {exc}"[:300])` → `unreadable_reason=None)` | KILLED (row 1) |
| a sidecar with no segments list is unreadable, not silence (AT-466b) | `…keeps_why_it_could_not_be_read[empty-object]` | remove the `isinstance` guard, back to `raw.get("segments", [])` | KILLED (row 2) |
| media prep stays best-effort through the shared reader | `test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep` | `transcribe.py`: `read_sidecar` → `from_sidecar` | KILLED (row 3) |
| ingest stays best-effort through the shared reader | `test_ingest_real_cli.py::test_a_malformed_sidecar_never_stops_an_ingest[not-json]` | `ingest.py`: `read_sidecar` → `from_sidecar` | KILLED (row 4) |
| `ingest prep` names unreadable narration and its cause (AT-465) | `test_prep_tells_the_operator_the_narration_is_unreadable_and_why` | the unreadable branch's condition → `if False:` | KILLED (row 5) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at465-466-unreadable-narration-keeps-its-cause/mutations.json
KILLED  AT-466 reopens: an unreadable sidecar discards its cause again  (pytest exit 1)
    claims to kill : tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[bad-json]
    actually failed: tests/test_analyze_video.py::test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript, tests/test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep, tests/test_media_prep.py::test_prep_tells_the_operator_the_narration_is_unreadable_and_why, tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[bad-json], tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[empty-object], tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[not-utf8], tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[segments-not-a-list]
KILLED  AT-466 reopens: a sidecar with no segments list ({}) loads as silence  (pytest exit 1)
    claims to kill : tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[empty-object]
    actually failed: tests/test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep, tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[empty-object], tests/test_schema_video.py::test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[segments-not-a-list]
KILLED  media prep stops being best-effort: a malformed sidecar raises  (pytest exit 1)
    claims to kill : tests/test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep
    actually failed: tests/test_media.py::test_a_malformed_sidecar_does_not_stop_media_prep, tests/test_media_prep.py::test_prep_tells_the_operator_the_narration_is_unreadable_and_why
KILLED  ingest stops being best-effort: a malformed sidecar stops an ingest  (pytest exit 1)
    claims to kill : tests/test_ingest_real_cli.py::test_a_malformed_sidecar_never_stops_an_ingest[not-json]
    actually failed: tests/test_analyze_video.py::test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript, tests/test_analyze_video.py::test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent, tests/test_ingest_real_cli.py::test_a_malformed_sidecar_never_stops_an_ingest[not-json], tests/test_ingest_real_cli.py::test_a_malformed_sidecar_never_stops_an_ingest[segment-not-a-mapping], tests/test_ingest_real_cli.py::test_a_malformed_sidecar_never_stops_an_ingest[top-level-list], tests/test_ingest_real_cli.py::test_a_malformed_sidecar_never_stops_an_ingest[unknown-segment-field], tests/test_ingest_real_cli.py::test_an_unreadable_sidecar_is_never_reported_as_silence[[1,, tests/test_ingest_real_cli.py::test_an_unreadable_sidecar_is_never_reported_as_silence[{"segments":
KILLED  AT-465 reopens: prep prints an unreadable sidecar as 0 narration segments  (pytest exit 1)
    claims to kill : tests/test_media_prep.py::test_prep_tells_the_operator_the_narration_is_unreadable_and_why
    actually failed: tests/test_media_prep.py::test_prep_tells_the_operator_the_narration_is_unreadable_and_why

5/5 mutations killed
```

Each row is a single-hunk edit to a single file named above. Several rows also fail neighbouring tests
that exercise the same path; each row's named test is among the ones that failed.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/schema/media.py`,
`src/autotester/media/transcribe.py`, `src/autotester/stages/ingest.py`, `src/autotester/cli_video.py`
(a CLI line, not a web page), and five test files. No template, route or rendered web field reads
`unreadable_reason`.

## Known limits (disclosed, not claimed)

- **The reason can quote sidecar content.** A pydantic `ValidationError` message includes the offending
  input value, so `unreadable_reason` may hold up to 300 characters of the sidecar, which is narration
  text. It is persisted in the project's `transcript.json` and printed by `ingest prep`. It never enters
  a model prompt: `narration_block` renders the fixed "could not be read" sentence, not the reason.
- **A stricter `from_sidecar`.** A sidecar without a `segments` list is now unreadable rather than silent.
  Every sidecar this repo writes (`transcribe._main`) and every fixture carries `segments`, and the full
  suite passes. A third-party sidecar that stored narration under another key was already read as
  silence before, so nothing readable is lost.
- **The mutation harness cannot attribute a parametrized test whose id contains a space.** My first run
  printed no `KILLED` for rows 1 and 4, even though the tests failed. The failure lines were split at
  the space (`…[{not,` / `…[not,`). I gave both parametrize blocks space-free `ids=` rather than change
  the harness, which is outside this unit. This is a real `scripts/mutation_check.py` defect, left for
  the checker to file.
- **Proven red-before-fix without touching the shared tree.** No `git stash` this time: the failing run
  above is the new tests against unmodified source, before any source edit was made.

## Status: checked-PASS — `qa/verdicts/at465-466-unreadable-narration-keeps-its-cause.md` (Cycle checked: 1, commit 7252f47, pushed). Checker filed AT-468 (the `unreadable_reason` field description says "never the file", but a validation error quotes sidecar values) and AT-469 (confirmed: mutation_check.py:52 cuts a test id at its first space).
