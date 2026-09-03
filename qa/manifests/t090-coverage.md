# Manifest — t090-coverage

**Contract:** qa/contracts/coverage.md (V1–V4, new this cycle) + qa/contracts/execute.md
(E1-E5, dependency)
**Goal task:** T-090 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly (advances the pipeline; north star's self-extension half)

## Why this unit

Umesh: "don't stop until you achieve the /goal." T-090 was unblocked (deps=[T-050], done) and is
`user_value: high`, and matches the north star's own text: "when it meets a screen it does not
know, it asks the human for a video instead of guessing."

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-090 stages/coverage.py: route/screen diff -> CoverageGap
-> VideoRequest"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for coverage. Wrote `qa/contracts/coverage.md` (V1–V4) before writing any
code. `CoverageGap`/`VideoRequest` schema already existed (built during the T-000 design lock) —
this unit adds the diffing mechanism and persistence, not the shapes.

## What changed

- `qa/contracts/coverage.md` (new) — V1 (known route → no gap) · V2 (unseen route → exactly one
  gap, deduped across cases) · V3 (exactly one `VideoRequest` per gap, idempotent) · V4 (redacted
  evidence never mistaken for a route).
- `src/autotester/stages/coverage.py` (new, 60 lines) — `diff_coverage(spec, results) ->
  list[CoverageGap]` (path-only comparison via `urlsplit`, content-addressed dedup),
  `request_for(gap) -> VideoRequest`.
- `src/autotester/store/project_store.py` — `add_request`/`list_requests`, same idempotent
  thin-wrapper pattern as `add_case` (checks existing ids before appending). No existing method
  changed.
- `tests/test_coverage.py` (new, 6 tests) — a known route produces no gap; an unseen route
  produces exactly one gap; the same unseen route seen by two different cases still dedupes to
  one gap; a redacted evidence string is never treated as a route; `request_for` names the
  specific gap in its prompt; `ProjectStore.add_request` is idempotent (called twice for the same
  gap, still one row on disk).
- `docs/ARCHITECTURE.md` — concept→file row for `stages/coverage.py::diff_coverage`; merged the
  two Pathlynks-script rows into one to make room (net zero line change, same consolidation
  pattern as T-070's cycle); Status line updated (coverage.py built, Next = `ui/` only). 150
  lines (at the C2 cap, not over — `doctor`'s check is `> 150`).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_coverage.py -v` → 6 passed
- `uv run pytest -q` → exit 0, 177 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 150 (≤ 150)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_coverage.py -v
......                                                                   [100%]
6 passed
$ uv run pytest -q
......................................s................................. [ 40%]
........................................................................ [ 81%]
.................................                                        [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- Per the no-fire list, `stages/ingest.py::ingest_video` does NOT currently populate
  `Screen.url_pattern` (a vision model watching a video frequently cannot read a hidden address
  bar) — so this unit's tests build fixture `FlowSpec`s with `url_pattern` set directly, to prove
  the diff mechanism itself, rather than claiming an end-to-end real-Pathlynks demonstration.
  Flagged explicitly, not smoothed over — this is the same honesty pattern as T-060's
  golden-test-needs-a-real-video disclosure.
- Screen-level (name/signals) gap detection is out of scope (no-fire list) — only URL-path
  diffing, matching `CoverageGap.kind="route"`.
- No secrets touched — this unit has no credential surface; test fixtures use fake URLs only.

## Status: checked-PASS

Reconciliation note (2026-09-03): this manifest was never flipped from ready-for-check at the time, even though qa/verdicts/t090-coverage.md recorded PASS and the unit shipped (see docs/FEATURES.jsonl / .goal/goal.json). Corrected during a disk-state reconciliation pass -- no re-check performed, no new claim made; the verdict file is the actual evidence, this is only the manifest catching up to it.
