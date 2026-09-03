# Verdict — t020-filestore

**Date:** 2026-09-03
**Cycle checked:** 1
**Checker mode:** A (unit check, fresh context, project root bound to `D:/autoTesting`)

## Commands re-run (by me, not pasted)

- `uv run pytest tests/test_store.py -q` → 12 passed, exit 0 (manifest claims 13 — see AT-023)
- `uv run pytest tests/test_ledger.py -q` → 20 passed, exit 0 (full suite, not spot checks; matches manifest)
- `uv run pytest -q` → 93 passed (dot-count of `77%`+`100%` lines and `--collect-only` per-file
  totals both agree at 93), exit 0 (manifest claims 94 — see AT-023)
- `uv run ruff check src tests` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 137 (≤ 150)
- `wc -l` on `filestore.py` (94), `project_store.py` (58), `store/__init__.py` (13),
  `test_store.py` (142) — all ≤ 300, matches manifest's stated line counts.

## Adversarial checks

- **Atomicity (C6):** read `_atomic_write` in `src/autotester/store/filestore.py:22-31` —
  genuinely `tempfile.mkstemp` in the target directory → write → `os.replace(tmp_name, path)`,
  with the temp file unlinked on any exception before the exception propagates. `write_json`/
  `upsert_jsonl` both route through it. `test_write_json_is_atomic_and_leaves_no_tmp_files`
  confirms no `.tmp-*` leftover. Genuine, not just claimed.
- **`upsert_jsonl` order (C6):** read `filestore.py:75-94` — it iterates existing rows in file
  order, replacing only the matching id in place, appending only if no match was found; never
  re-sorts. `test_upsert_replaces_matching_id_in_place_and_appends_new_ids` asserts
  `[r.id for r in rows] == [a.id, b.id]` after replacing `a` (not last) — order preserved.
  Confirmed by reading the code and re-running the test myself.
- **DRY refactor of `src/autotester/ledger/store.py` (C3):** read the current file —
  `load_events`/`append_event` call `filestore.read_jsonl`/`append_jsonl` (imported as
  `_read_jsonl`/`_append_jsonl`); no hand-rolled line-parsing loop remains in the ledger module.
  `ledger/store.py` is untracked (never previously committed), so there is no git diff to
  compare against a "before" state, but the current source has zero duplicated parsing logic
  and the full `tests/test_ledger.py` suite (20/20, re-run myself, not spot-checked) passes —
  behaviour-preserving by the only evidence available (tests + code reading).
- **C6 literal test:** re-ran `test_a_human_can_hand_edit_an_artifact_and_the_store_still_loads`
  (passes) AND ran my own independent hand-edit probe (fresh tmp project, hand-rewrote
  `"name": "MyProj"` → `"name": "Hand Edited By Checker"` directly on disk, reloaded via
  `ProjectStore.load_project()`) — loaded name matched the hand-edit. C6 holds.
- **`Case.add_case` idempotency scan:** confirmed `add_source`/`add_case`
  (`project_store.py:32-37`, `:50-55`) call `list_sources()`/`list_cases()` (a full
  `read_jsonl` scan) on every call — genuine O(n) per add, not a criterion violation today
  (small per-project collections) but a real footgun once T-070 regenerates cases repeatedly.
  Filed as AT-024 (low) per the dispatch instruction, not scored against this unit.
- **Scope (C1):** grepped `src/autotester/store/*.py` for grade/verdict/execute/stage/validate-
  business-rule content — none found. `ProjectStore` is a thin typed facade; `filestore.py` is
  generic (`TypeVar("ModelT", bound=BaseModel)`), no business validation beyond what Pydantic
  models already enforce. Store stays persistence-only.

## Criteria

- **C1** (schema-first, single source of truth) — met. No dict/dataclass shadow of a schema
  model in the store; generic primitives are model-agnostic via `TypeVar`.
- **C3** (one concept, one place) — met. `doctor` clean (duplicate-concept + drift-filename
  rules); ledger's line-parsing now genuinely delegates to `filestore`, no second implementation.
- **C6** (artifacts are human-editable files) — met. Atomic writes, order-preserving upsert,
  and both the shipped test and my independent probe confirm a hand-edited file still loads.

## Findings (new, filed to ledger, do not block this unit)

- **AT-023** (low): manifest self-reports 13 tests in `test_store.py` and 94 in the full suite;
  actual are 12 and 93. All tests pass either way — no functional impact, but the manifest's own
  numbers should be corrected in the future.
- **AT-024** (low): `add_source`/`add_case` idempotency check is O(n) per call (full collection
  scan) — noted for later, not a criterion violation for this unit's scope.

## Issues addressed

None claimed by this manifest; none applicable.

VERDICT: PASS
SCOREBOARD: 3/3 criteria met, 0/0 invariants (none named beyond C1/C3/C6 in scope)
FAILURES (if any): none
ISSUES-WRITTEN: AT-023, AT-024
EXPLANATION: Re-ran every verify command myself (pytest full suite + test_store.py +
test_ledger.py, ruff, doctor, ARCHITECTURE.md line count) — all green, matching the manifest's
claims apart from two off-by-one test-count typos (AT-023, filed, non-blocking). Read
filestore.py's atomic-write and upsert-order-preservation code directly and independently
reproduced the C6 hand-edit test with my own probe; both hold genuinely, not just by assertion.
The ledger DRY refactor has no prior committed version to diff against, but the current source
has zero duplicated parsing logic and the full 20-test ledger suite passes. No stage/execute/
grade logic found in store scope. PASS.
