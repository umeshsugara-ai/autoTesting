# Manifest — at468-unreadable-reason-never-quotes-content

**Unit:** AT-468 — `Transcript.unreadable_reason` says "the parse error, never the file", but a pydantic
validation failure quoted the sidecar's narration (and whatever PII it held) into the persisted transcript
and the `ingest prep` line
**Contract:** `qa/contracts/video-learning.md` (VL1) · `qa/contracts/core-invariants.md` (C1, C7) · the
CLAUDE.md credential boundary ("logs pass `Redactor.scrub`": a cause line must not carry content)
**Goal task:** none (issue-driven)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-468 (low, open → fixed)

## Why

The issue's `expected` offers two options: make the description true, or correct the description. This
unit takes the first. The description is the contract a reader relies on, and the cause is still useful
without the input: *which field* and *what kind of error* is what a human needs to repair a sidecar.

## What changed

- `src/autotester/schema/media.py:17-28` — new module-private `_reason(exc)`. A `ValidationError` is
  rendered from `exc.errors()` as `<loc>: <type>` per error (e.g. `ValidationError: end: missing`). An
  `extra_forbidden` error is rendered as `unknown field`, because the key name is itself sidecar content.
  Every other exception keeps the AT-466 form `<Type>: <message>`.
- `src/autotester/schema/media.py:80` — `read_sidecar` uses `_reason(exc)[:300]` instead of the raw
  `f"{type(exc).__name__}: {exc}"`. `import ValidationError` added. The field description is unchanged,
  and is now true.
- `tests/test_schema_video.py` (appended) —
  `test_an_unreadable_reason_names_the_error_never_the_sidecar_content`, parametrised
  `missing-field` / `wrong-type` / `unknown-key`, each carrying `hunter2` and `alice@example.com` in the
  place pydantic would quote (narration text, a mistyped value, a key name).

## How to verify (commands + expected)

- `uv run pytest -q tests/test_schema_video.py tests/test_media_prep.py tests/test_media.py tests/test_ingest_real_cli.py tests/test_analyze_video.py` → all pass
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at468-unreadable-reason-never-quotes-content/mutations.json` → `3/3 mutations killed`, exit 0
- The issue's own probe: a sidecar `{"segments":[{"start":0,"text":"my password is hunter2 for alice@example.com"}]}` through `Transcript.read_sidecar` → reason `'ValidationError: end: missing'`
- Full suite `uv run pytest -q` → green (maker did not run it: 2.8 GB free RAM and a concurrent loop; checker's call)

## Actual outputs (from maker's own run)

```
$ uv run pytest -q tests/test_schema_video.py tests/test_media_prep.py tests/test_media.py tests/test_ingest_real_cli.py tests/test_analyze_video.py
........................................................................ [ 86%]
...........                                                              [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ issue probe
'ValidationError: end: missing'
```

Red before the fix (new test written first, run against the unchanged `media.py`): all three ids FAILED,
e.g. the `unknown-key` reason was
`'ValidationError: 1 validation error for TranscriptSegment\n`hunter2 alice@example.com`\n  Extra inputs are not permit...'`.

## Capability coverage (each new claim -> its isolating falsification)

Instrument: `scripts/mutation_check.py` (sandbox copy, green baseline required, kill = exit 1 and every
named id in pytest's own failure report). Spec and full output:
`qa/evidence/at468-unreadable-reason-never-quotes-content/mutations.{json,out}`.

| capability | check | falsifying edit (media.py, single hunk) | observed |
|---|---|---|---|
| a validation failure's reason carries location + kind, never the input | `test_an_unreadable_reason_names_the_error_never_the_sidecar_content[missing-field,wrong-type,unknown-key]` | `if not isinstance(exc, ValidationError):` → `if True:` | `KILLED ... actually failed: [missing-field], [unknown-key], [wrong-type]` |
| an unknown key is named by kind, not by its (sidecar-authored) name | `...[unknown-key]` | `"unknown field" if e["type"] == "extra_forbidden"` → `"unknown field" if False` | `KILLED ... actually failed: [unknown-key]` |
| AT-466 still holds through the helper: non-validation causes keep their type | `test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[bad-json,not-utf8]` | `return f"{type(exc).__name__}: {exc}"` → `return f"{exc}"` | `KILLED ... actually failed: [bad-json], [not-utf8]` |

`3/3 mutations killed`.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/schema/media.py`,
`tests/test_schema_video.py`. The only consumer of `unreadable_reason` outside the schema is the CLI
line `src/autotester/cli_video.py:107` (grep `unreadable_reason` over `src/`); no template renders it.

## Known limits (disclosed, not claimed)

- **Non-validation messages are passed through, on inspection, not by test.** `UnicodeDecodeError` names
  one undecodable byte and its offset; `JSONDecodeError` a line/column; `TypeError` (a non-mapping
  segment) a type name; `OSError` the file path (a path, not content). None quotes text, but a future
  exception type that does would pass through.
- **Transcripts already persisted** by `ProjectStore.save_transcript` before this change keep their old
  reason. Nothing rewrites them; re-running `ingest prep` does.
- **`loc` can contain a list index** (e.g. `segments.0.end` is not produced here because segments are
  validated one at a time, so `loc` is the field name only). Indices and schema field names are not
  sidecar content.

## Status: checked-PASS

Verdict: `qa/verdicts/at468-unreadable-reason-never-quotes-content.md` (Cycle checked: 1, commit 2e4d9b0, pushed). Checker probed 8 further sidecar shapes, no leak. Ledger: AT-468 → fixed.
