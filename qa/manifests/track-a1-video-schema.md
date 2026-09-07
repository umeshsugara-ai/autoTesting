# Manifest — track-a1-video-schema
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3, C6) — A1 is schema-only, no new
behavioural contract is needed yet; `ingest.md` I6-I9 and the new `video-learning.md` land with
A2/A3 per plan.md's own sequencing.
**Goal task:** T-130
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §4 "A1 — schema + storage foundation", authorised by D-014

## What changed
Full diff in commit `ce1b624`. No provider call, no browser action, no UI route — pure schema
and storage, matching the plan's own scoping for this unit.

- `schema/enums.py`: `Action` += `BACK, HOVER, PRESS_KEY, SCROLL` (discharges D-005, shared with
  the future Track B); new `IssueCategory` (12 prior-art categories + `feature_gap, wrong_model,
  data_error` — added because 10/33 rows in the real `ERP_Issues_ALL.xlsx` are spoken change
  requests with no home in the original 12), `IssueOrigin`, `IssueStatus`, `Confidence`.
- **New** `schema/observation.py` — `ObservedStep/ObservedFlow/ObservedScreen/VideoObservation`
  moved out of `flowspec.py` (was at 202/300 lines; D-014 authorises the move) and extended per
  the decision text; new `VisionOptions` (fps=2, seed=7, max_output_tokens=65536, HIGH media
  resolution — the proven external pipeline's settings) and `ModelObservation` (the per-chunk
  per-model raw cache, VL3's determinism boundary — built here, used starting A4).
- **New** `schema/media.py`, `schema/analysis.py`, `schema/issue.py`, `schema/screenmap.py` —
  every artifact D-014 names, each `extra="forbid"`, each a plain JSON/JSONL shape under
  `projects/<slug>/` (C6, no database).
- `flowspec.py`: `Screen` += `source_ref`; `FlowSpec` += `app_overview`. `project.py`: `Source`
  += `recorded_on`.
- `core/paths.py` / `store/project_store.py`: one path property + one store method per new
  artifact kind (C1/C3 — a new kind is a schema model + a path + a store method, never a new
  file format or a second source of truth).
- `stages/execute.py`: `_ACTIONS[step.action]` → `_ACTIONS.get(...)` + `StepNotExecutable`. This
  is the one behavioural change in the unit, and it exists because adding `Action` members
  without it would `KeyError` inside a live run the moment any code (a hand-authored case, a
  future Track B step) named `BACK`/`HOVER`/`PRESS_KEY`/`SCROLL` before Track B1 gives them a
  handler. Verified with a new test that runs a `SCROLL` step today and asserts `ERRORED`, not a
  crash.
- `stages/ingest.py`, `tests/test_ingest.py`: import path only — `ingest_video`'s behaviour is
  byte-for-byte unchanged (confirmed: all 9 pre-existing `test_ingest.py` tests pass unmodified
  except the one import line).
- `tests/fixtures/erp1.transcript.json`: **byte-for-byte copy** of the real
  `C:/Users/Lenovo/Videos/Screen Recordings/erp1.transcript.json`, so `Transcript.from_sidecar`
  is tested against the real shape, not an invented one.
- `tests/test_schema_video.py` (new, 27 tests): roundtrips through `write_json`/`read_json` and
  `ProjectStore`, `extra="forbid"` rejects an unknown key on 3 different new models, `Issue.id`
  stability (same across `created_at`/severity, differs on title, buckets nearby timestamps
  together), transcript slicing against the real fixture (including the off-by-one I caught
  myself: segment `[4.92, 6.92]` rounds to `[00:05-00:07]`, not `[00:04-00:06]`).

## Corrections found and self-corrected during the build
- My first `schema/analysis.py` and `schema/screenmap.py` drafts used `list[dict]` fields
  (`VideoAnalysis.flows`, `Journey.stops`) as a shortcut. That is a C1 violation ("no dict-shaped
  domain object duplicating a schema model") — fixed before committing by using `ObservedFlow`
  and `JourneyStop` directly.
- The overdue checker sweep (`e362214`) ran **while this migration was mid-flight** and correctly
  caught two real states, both now resolved:
  - **AT-090**: `autotester doctor` was failing with 4 duplicate-concept violations because I had
    added `schema/observation.py` before removing the old classes from `flowspec.py` in the same
    breath. Resolved — `doctor: clean` now, confirmed after the move completed.
  - **AT-089**: the previous tick (`a3d0be4`) claimed "T-121 governance registration closed" but
    never flipped `T-121`'s `status` in `.goal/goal.json` from `pending` to `done`. Fixed inline
    (bundled into this commit's `.goal/goal.json` diff, since both touch the same file and no
    checker had reviewed the intermediate state) — `T-121` now reads `status: done`.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest tests/test_schema.py tests/test_schema_video.py tests/test_store.py tests/test_execute.py tests/test_ingest.py -q`
  → expected: exit 0, all pass (this is plan.md's own verify line for A1)
- `docker compose exec autotester uv run pytest -q` → expected: `385 passed, 1 skipped` (the
  skip is the pre-existing real-Chromium test, unrelated to this unit)
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: `All checks passed!`
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- `docker compose exec autotester uv run autotester map && git diff --stat docs/MAP.md` →
  expected: no diff (already regenerated and committed in `ce1b624`)
- Live check that `Transcript.from_sidecar` reads the real file, not an invented shape:
  `docker compose exec autotester uv run python -c "from pathlib import Path; from autotester.schema.media import Transcript; t = Transcript.from_sidecar(Path('tests/fixtures/erp1.transcript.json'), 'src_erp1'); print(len(t.segments), t.speech_seconds)"`
  → expected: `6 22.0`

## Status: checked-PASS

Verdict: `qa/verdicts/track-a1-video-schema.md` (**Cycle checked: 1**, PASS, 4/4 criteria — C1,
C2, C3, C6). The checker re-ran every verify command itself in the container rather than trusting
this manifest's pasted output, diffed D-014's authorized field list line-for-line against the
committed diff (nothing exceeds it), and confirmed AT-089 and AT-090 — the two findings the
overdue sweep filed against this unit's own mid-flight state — are genuinely resolved, moving
both from `open` to `verified`. No new issues found. `T-130` closed in `.goal/goal.json`.
