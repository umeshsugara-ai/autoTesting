# at125-at132-declared-but-unapplied

**Unit:** AT-125 + AT-128 + AT-129 (checker-found on T-131) + **AT-132** (found by my own test)
**Commit:** c4c878a (cycle 1) → **d9396d4** (cycle 2)
**Fix cycle:** 2
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

## Cycle 2 — the FAIL, and why it is the most interesting finding of this unit

The checker FAILed cycle 1 on **AT-133**, and the finding is **this unit's own thesis reappearing
inside the fix for it.** `load_sidecar`'s docstring promised *"a malformed sidecar must not stop an
ingest"*; the code caught only `(OSError, ValueError)`, while `from_sidecar` raises `AttributeError`
on a non-object top level and `TypeError` on non-mapping segments. Declared, plumbed, not applied —
written by me, in the commit whose entire argument was against exactly that.

Reproduced by the checker end to end: sidecar `[1,2,3]` → `ingest run` exit **1**.

### AT-134 — the half that took a real judgement, and the checker drew the line correctly

Returning `None` for an unreadable sidecar made the prompt assert **"no speech detected"** about a
recording that demonstrably has speech — a false statement inside the block the prompt itself
labels ground truth. Worse than saying nothing.

The dispatch asked whether swallowing here contradicts my own AT-108/AT-114 sweep, which argued
that swallowing a cause **is** the defect. It does not, and the checker's formulation is the one
that resolves it:

> swallowing is fine when the fallback is **neutral**, and a defect when it is an **assertion the
> reader will believe**.

That sweep's rule was never "always re-raise" — it was *never let a failure become a
confident-looking silence*. Same rule, applied one layer up. `narration_block` now carries three
states that are never conflated: speech → the transcript; genuinely absent → assert silence;
present-but-unreadable → say exactly that, and tell the model not to assume silence.

### AT-135 — typed refusals in both paths I added

`path.exists()` is true for a **directory**, so `file_sha256` raised a raw `PermissionError` out of
the CLI instead of the `SourceChanged` that function exists to produce; and a missing file escaped
`upload_and_wait` as a bare `FileNotFoundError`.

### Cycle 2 evidence

```
$ SABOTAGE H: AT-133/134 -- load_sidecar back to the narrow catch returning None
failures: 4
FAILED ...::test_a_malformed_sidecar_never_stops_an_ingest[[1, 2, 3]]
FAILED ...::test_a_malformed_sidecar_never_stops_an_ingest[{"segments": ["hi"]}]
FAILED ...::test_an_unreadable_sidecar_is_never_reported_as_silence[[1, 2, 3]]

$ SABOTAGE I: AT-134 only -- an unreadable sidecar reported as silence again
failures: 2
FAILED ...::test_an_unreadable_sidecar_is_never_reported_as_silence[[1, 2, 3]]
FAILED ...::test_an_unreadable_sidecar_is_never_reported_as_silence[{"segments": [{...confidence...}]}]

$ SABOTAGE J: AT-135 -- exists() instead of is_file(), so a directory falls through
FAILED ...::test_a_source_pointing_at_a_directory_gets_a_typed_refusal

$ RESTORE
16 passed
```

**The separation is the point.** H fails four tests, I fails exactly the two silence cases, J fails
one. That proves the two halves of AT-133/AT-134 are defended independently rather than by a single
over-broad test that would pass on either fix alone.

### A tooling correction I am carrying forward, from the checker

`addopts = "-q"` in `pyproject.toml` plus a command-line `-q` is `-qq` under pytest 9, which
**suppresses the count line entirely** — so `uv run pytest -q`, the command my earlier manifests
document, cannot produce the number those manifests quote. I had hit this and worked around it with
`grep` without understanding why. Bare `uv run pytest` prints it; every count in this manifest came
from that.

### Cycle 2 verification

```
uv run pytest                          623 passed, 2 skipped   (614 at cycle 1 + 9 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

### Left open deliberately

**AT-136** (`Source.duration_s`, `Source.notes`, `FlowSpec.app_overview` are still
declared-and-unapplied) and **AT-137** (`RepoDocs()` ≠ `RepoDocs(repo_root())` — the hidden
`_root_given` flag is a smell even though the checker ruled the behaviour correct and not a
split-brain). Both are the checker's own follow-ups, both non-blocking, and both belong to a unit
that is about them rather than tacked onto a re-check.

## Status: checked-PASS
