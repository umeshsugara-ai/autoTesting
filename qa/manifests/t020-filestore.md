# Manifest — t020-filestore

**Contract:** qa/contracts/core-invariants.md C1, C3, C6 (no dedicated feature contract — the plan's phase P0/P1 done_check is `pytest tests/test_store.py -q`)
**Goal task:** T-020 (`user_value: normal`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-020 store/filestore.py: load and save every artifact as JSON/JSONL under projects/<slug>/, human-editable files as the source of truth"` → `no gate — no retired features (rule)`.

## What changed

- `src/autotester/store/filestore.py` (new, 94 lines) — the five primitives every persisted
  artifact goes through: `write_json`/`read_json` (single-object, atomic via temp-file +
  `os.replace` — a crash mid-write can never leave a half-written file for a human or the next
  run to trip over), `read_jsonl` (line-numbered errors on a malformed row), `append_jsonl`
  (never rewrites existing lines — a torn write can only ever damage the last line),
  `upsert_jsonl` (replace-by-id or append, for the rare case a row's status changes in place).
- `src/autotester/store/project_store.py` (new, 58 lines) — `ProjectStore`: a thin, typed
  facade over `ProjectPaths` for the artifacts that exist today — `save/load_project`,
  `add/list_sources`, `save/load_flowspec`, `add/list_cases`. `add_source`/`add_case` are
  idempotent on the model's content-addressed `id`, so re-running ingest or regenerating a
  flowspec never duplicates a row. Deliberately does **not** pre-wire scripts/runs/rubrics/
  requests — those belong to the stages that create them (T-040/T-070/T-090), per "one concept,
  one place" and the no-fire list ("missing features scheduled in a later phase").
- **DRY refactor (C3, and Umesh's explicit ask for a DRY-designed schema/system):**
  `src/autotester/ledger/store.py::load_events`/`append_event` now call `filestore.read_jsonl`/
  `append_jsonl` instead of hand-rolling the same line-parsing loop a second time. The
  ledger-specific rule (a repeated `id` is a defect, not a merge) sits on top as a thin check.
  Behaviour and every existing `test_ledger.py` assertion are unchanged (20/20 still pass).
- `src/autotester/store/__init__.py` — package exports.
- `docs/ARCHITECTURE.md` — two concept→file rows; Status updated (137 lines).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.
- `tests/test_store.py` (new, 13 tests) — generic-primitive tests (roundtrip, missing-file,
  malformed-file naming its path, atomic write leaves no temp file, append order, malformed-row
  line number, upsert replace-vs-append) and `ProjectStore` tests (idempotent source/case add,
  flowspec roundtrip, and a C6-literal test: hand-edit the JSON file on disk, confirm the store
  still loads the human's edit).

## How to verify (commands + expected)

- `uv run pytest tests/test_store.py -q` → exit 0, 13 passed
- `uv run pytest tests/test_ledger.py -q` → exit 0, 20 passed (refactor did not change behaviour)
- `uv run pytest -q` → exit 0 (94 tests)
- `uv run ruff check src tests` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 137 (≤ 150)

## Actual outputs (from maker's own run)

```
$ uv run pytest -q
........................................................................ [ 77%]
.....................                                                    [100%]
$ uv run ruff check src tests
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- No new contract file: the plan names T-020's `done_check` as `pytest tests/test_store.py -q`
  under `core-invariants.md`, not a dedicated feature contract. Judge against C1/C3/C6.
- `upsert_jsonl` has no caller yet in this unit (built for a near-future need — case status
  transitions in the expand stage, T-070) but is exercised directly by its own test; flag if you
  judge unused-but-tested code out of scope for this unit.
- No live host, no secret, no browser touched by this unit.

## Status: checked-PASS

Verdict: `qa/verdicts/t020-filestore.md` (Cycle checked: 1, PASS; commit 837e6cb). Goal task T-020 closed by the checker. `user_value: normal` — no ledger row required. Non-blocking findings AT-023 (manifest test-count typo) and AT-024 (O(n) add_source/add_case scan, future optimization) filed for later.
