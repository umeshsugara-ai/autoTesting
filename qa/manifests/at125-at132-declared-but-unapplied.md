# at125-at132-declared-but-unapplied

**Unit:** AT-125 + AT-128 + AT-129 (checker-found on T-131) + **AT-132** (found by my own test)
**Commit:** c4c878a
**Fix cycle:** 1
**Contract:** `qa/contracts/ingest.md` I7–I10 (authored by the checker on the T-131 verdict).

## Why these are one unit

All four are bugs in code I shipped last tick, and all four are the same shape: **something
declared, plumbed through, and then never actually applied by the path that ships.** Splitting them
would be four manifests describing one mistake.

## AT-125 — and the reason this file exists

No shipped caller passed `VisionOptions`. The checker measured it through the real CLI:
`vision_options == [None]`. So HIGH media resolution never applied in production.

My T-131 test proved the options **reach the provider when passed**. That is a different claim from
*the product passes them*, and I wrote the first while believing I had established the second.

**This is my fourth consecutive unit with the same cause** — AT-116 (a criticality floor the
classifier never read), AT-120 (a count separated in the enum and nowhere a reader looks), AT-122
(a surface that then dropped it), and now this. Each time I verified the mechanism I changed rather
than what a production run does. So every test in `tests/test_ingest_real_cli.py` drives the real
CLI through `CliRunner`. That is the entire design of the file.

**Found while fixing it, filed by nobody:** `build_ingest_prompt` has taken a `transcript` since
T-131 and **no caller passed one either**, so `{{NARRATION}}` rendered *"no speech detected"* on
every real ingest. The ground-truth block was exactly as dead as the options — the same bug, one
file over, that neither I nor the checker had named. `load_sidecar` now finds
`<video>.transcript.json` beside the recording.

Verified against the real corpus (`C:/Users/Lenovo/Videos/Screen Recordings/erp1.transcript.json`):
6 segments, `speech_seconds` 22.0, and `slice()` emits exactly the shape the prompt injects —

```
[00:01-00:03] Move to next stage
[00:10-00:18] Remove not getting this error
[00:19-00:24] Say which center and job role if this nomination is for
```

## AT-128 — a cache key that collides on the thing it is caching

Keyed `resolve()::st_size`. A recording re-exported in place at the same byte size was a **hit**:
the model receives the OLD video and produces a confident reading of footage nobody asked about.
Keyed on content now. `core.ids.file_sha256` was two modules away the whole time.

## AT-129 — provenance that reads as precise and points at the wrong recording

`register_source` is immutable by design, so changed bytes mint a **new** source and leave the old
row pointing at the same path. Ingesting that stale row watches the new video while stamping every
`SourceRef` with the old id. That is worse than an error, because a human reviewing the provenance
has no reason to doubt it. `verify_source_bytes` refuses, and names the command that fixes it.

## AT-132 — my own test found this, not the checker

`RepoDocs.prompts_dir` resolved under `root`, which honours `AUTOTESTER_ROOT` — a switch for
relocating a project's **data**. So relocating data moved the **prompt** lookup, and
`autotester ingest run` under a relocated root died on
`FileNotFoundError: <data root>/src/autotester/prompts/...`. Every prompt-reading stage was one
environment variable away from the same failure.

An explicit `root` still wins: substituting a stub prompt tree is a legitimate thing for a test to
do. The defect was only the env var leaking into a path it does not own.

**This is the argument for the whole unit.** A test that drove the real CLI found a latent
production trap in fifteen minutes; four units of tests that drove functions directly never could.

## Evidence

```
$ SABOTAGE D: AT-125 -- the CLI stops passing options and transcript (the shipped state at 1c8c8e4)
FAILED tests/test_ingest_real_cli.py::test_the_shipped_cli_passes_vision_options
FAILED tests/test_ingest_real_cli.py::test_the_shipped_cli_injects_the_sidecar_narration

$ SABOTAGE E: AT-128 -- the cache key goes back to path::size
E       assert 1 == 2
FAILED tests/test_ingest_real_cli.py::test_a_same_size_re_export_is_not_served_from_cache

$ SABOTAGE F: AT-129 -- ingest stops re-validating the recording bytes
FAILED tests/test_ingest_real_cli.py::test_ingesting_a_recording_that_changed_is_refused
FAILED tests/test_ingest_real_cli.py::test_the_refusal_writes_no_flowspec

$ SABOTAGE G: AT-132 -- the env-var data root moves the prompt lookup again
failures: 3
FAILED tests/test_ingest_real_cli.py::test_the_shipped_cli_passes_vision_options
FAILED tests/test_ingest_real_cli.py::test_the_shipped_cli_injects_the_sidecar_narration
FAILED tests/test_ingest_real_cli.py::test_a_recording_with_no_sidecar_still_ingests

$ RESTORE
27 passed
```

## Two self-corrections

1. **My first cut of AT-132 was too blunt.** It resolved prompts from the package *always*, which
   broke **15 ledger tests** that legitimately inject a stub prompt tree via an explicit `root`. The
   full suite caught it, not me. The narrow fix distinguishes explicit injection from env leakage —
   the bug was never the injection.
2. **I restored a sabotage from a stale backup** and silently reverted the refined fix to the blunt
   one; the ledger tests failed again and I traced it back. Then a subsequent index-based splice
   mangled `paths.py` outright and I restored it from `HEAD` — safe *there* because that file had no
   other uncommitted work, which I checked first, having destroyed an uncommitted prompt rewrite the
   same way one unit ago (AT-131's manifest). The lesson is holding, but only just.

## Verification (host; Docker daemon down, `uv` runs natively)

```
uv run pytest -q                       614 passed, 2 skipped   (607 before + 7 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- Still `MockProvider` only; no live model call, and `upload_and_wait` is still exercised against a
  stub client rather than the real Files API.
- AT-126, AT-127, AT-130 (declare `google-genai`), AT-131 (extend AT-101 to uncommitted files),
  AT-123 and AT-124 remain **open** — this unit deliberately took only the four that are the same
  defect. AT-130 is scheduled for A3 by the checker's own ruling.
- The corpus facts I measured this tick (`.work/track-a-corpus-facts.md`) correct four plan
  assumptions — including `ERP_Issues_ALL.xlsx` having **32** rows, not the plan's 33. That is a
  recall denominator and belongs in T-136's manifest before any score is computed against it. Not
  acted on here.

## Status: ready-for-check
