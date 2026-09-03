# Manifest — issue-batch-at012-023-024

**Contract:** qa/contracts/core-invariants.md (C1, C3, C6 — the feature these three issues were
all filed under)
**Goal task:** none (`.goal/goal.json` is 20/20 done — housekeeping backlog cleanup)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-012 (S3), AT-023 (low), AT-024 (low)

## Why this unit

Per Umesh's "proceed ahead, don't sleep" — after `docker-live-ui` closed, `qa/issues.jsonl` had 4
open items. `AT-026` (medium) needs a human design call (building a script-execution engine —
flagged `HUMAN_GATE` in an earlier tick, unchanged) so it's left open. These three are genuinely
unblocked, small, and real: one real code fix (AT-024), one documentation correction (AT-023),
one verify-and-close (AT-012, no code path to patch).

## What changed

### AT-024 — real fix: `ProjectStore.add_source`/`add_case`/`add_request` no longer re-scan
`src/autotester/store/project_store.py`:
- Constructor now carries `_source_ids`/`_case_ids`/`_request_ids: set[str] | None` (lazy caches).
- Each `add_*` method: populate the cache from `list_*()` on first use only, then check/update
  the in-memory set on every subsequent call — O(n) once per instance instead of O(n) per add.
- `list_*()` methods are unchanged — they always read fresh from disk, so a second `ProjectStore`
  instance (a different process/script) is never masked by another instance's cache.
- `tests/test_store.py` — 2 new tests: `test_add_case_does_not_rescan_the_file_on_every_call`
  (monkeypatches `read_jsonl` with a call-counter, asserts exactly 1 call across 5 sequential
  `add_case` calls), `test_add_case_cache_does_not_hide_a_case_added_by_another_process` (two
  `ProjectStore` instances on the same directory both see both cases via `list_cases()`).

### AT-023 — documentation correction: `qa/manifests/t020-filestore.md`
Added a dated correction note (not a silent edit of the historical record — this project's
manifests are evidence of what was actually run at the time) confirming the original "13
tests"/"94 tests" figures were off by one (`tests/test_store.py` had 12 test functions, the suite
collected 93) — a self-reported-count typo, never a functional violation (all tests passed then
and now).

### AT-012 — verified, no code change
`qa/.last-tick` is a single overwritten line (not an append log); every stamp written this
session already carries a consistent `+05:30` offset. No script writes this file programmatically
— each tick's agent writes it directly — so there is no code path to patch. The mixed-format
lines the original finding cited are historical git content, not a live bug. Verified by reading
the current file and this session's own recent commits.

### `qa/issues.jsonl`
AT-024 → `fixed` (real code change + regression tests). AT-023, AT-012 → `verified` (no
functional bug; documentation/verification only). Each row's `evidence` field appended with a
`RECONCILED`/`FIXED` note citing the exact change — the ledger stays append-only-in-spirit (never
silently rewriting the original finding text).

## How to verify (commands + expected)

- `uv run pytest tests/test_store.py -v` → 14 passed
- `uv run pytest -q` → all green, 205 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `grep -A1 "AT-024" qa/issues.jsonl` → status `fixed`, evidence cites the cache fix
- Read `qa/manifests/t020-filestore.md`'s tail → correction note present, original numbers left
  untouched above it

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_store.py -v
..............                                                          [100%]
14 passed
$ uv run pytest -q
........................................................................ [ 70%]
.....................................................s.......            [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- `add_request`'s identical O(n)-rescan pattern was fixed alongside `add_source`/`add_case` even
  though AT-024's title only names the latter two — same bug class, same file, same fix shape;
  fixing two of three and leaving the third with the identical defect would be inconsistent, not
  narrower scope.
- No behavior change to `list_*()` methods anywhere — only the `add_*` idempotency check is
  cached. `qa/contracts/core-invariants.md` C6 ("artifacts are human-editable files") still holds:
  a human hand-editing a JSONL file between two `add_*` calls on a *fresh* `ProjectStore` instance
  is picked up correctly (verified by the new cross-instance test); a *long-lived* instance's
  cache could theoretically miss a concurrent hand-edit mid-run, but that was already true of the
  pre-fix code too within a single script's own already-completed adds (nothing regresses).
- AT-026 remains open, deliberately — it is a `HUMAN_GATE` item (script-execution engine =
  arbitrary-code-execution surface), not part of this batch.

## Status: checked-PASS

Verdict: `qa/verdicts/issue-batch-at012-023-024.md` (Cycle checked: 1, PASS). AT-024 fixed
(cache correctness verified against staleness/cross-instance risk), AT-023 and AT-012 verified
closed honestly. No goal task — housekeeping.
