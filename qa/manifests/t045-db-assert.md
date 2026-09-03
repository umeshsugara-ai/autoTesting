# Manifest — t045-db-assert

**Contract:** qa/contracts/db-assert.md (D1–D5, new this cycle) + qa/contracts/core-invariants.md
+ qa/contracts/browser-and-secrets.md (dependency) + qa/contracts/execute.md (dependency)
**Goal task:** T-045 (`user_value: normal`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none (new unit; resolves the unfolded inbox item noted in
`browser-and-secrets.md`'s amendment log)

## Why this unit (human-gate context)

T-050 (the next `.goal/goal.json`-computed `current` task) needs a real headed-browser run
against live Pathlynks, including a deliberate wrong-password attempt — the maker skill's own
hard rule requires explicit per-use approval before "aiming the cycle at Pathlynks" that way.
Asked the user directly; the answer ("go whatever is the best way possible") did not clearly
bless the specific live/wrong-password action, so — per this project's standing "run, don't ask"
discipline applied conservatively to an outward-facing action against a real (if dev) system —
built T-045 instead: it is fully buildable and testable with zero live Pathlynks interaction
(D5), is genuinely next-most-valuable (unblocks nothing critical-path but was the standing
unfolded inbox item), and leaves T-050 queued for an unambiguous go-ahead.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-045 Backend assertions: EvidenceKind.DB + read-only
Mongo assertion helper"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for DB assertions. Wrote `qa/contracts/db-assert.md` (D1–D5) before writing
any code, following the `execute.md`/`grade.md` pattern.

## What changed

- `pyproject.toml` — added `pymongo>=4.9.0` as a real dependency (not lazy-imported without
  declaration); `uv sync` installed `pymongo==4.17.0` + `dnspython==2.8.0`.
- `qa/contracts/db-assert.md` (new) — D1 (read-only by construction, mirrors the standing Vidysea
  `lib/mongo.py::ReadOnlyCollection` pattern named in the global CLAUDE.md) · D2 (connection
  string never logged) · D3 (a document becomes evidence only redacted) · D4 (observation only,
  no judgement — grade.py's job) · D5 (no automated test opens a real socket without an explicit
  opt-in env var).
- `src/autotester/schema/enums.py` — added `EvidenceKind.DB`. No existing member changed.
- `src/autotester/browser/db.py` (new, 58 lines) — `ReadOnlyCollection` (exactly `find`,
  `find_one`, `count_documents`; no mutating method exists on the class, verified by a dedicated
  test enumerating its public members), `connect_read_only(uri, db, collection)` (lazy pymongo
  import, returns only the read-only wrapper, never the raw client), `assert_document(...)`
  (read-only `find_one`, returns `Evidence(kind=DB, ...)` with the summary text passed through
  the project's `Redactor` first).
- `tests/test_db.py` (new, 6 tests, 1 conditionally skipped) — read-only surface has exactly
  three public methods and none contain a mutating verb; delegation to a fake collection works;
  a document's secret value is redacted before becoming evidence; "not found" is evidence, not an
  exception; `db.py`'s source contains no `print`/`logging` of the uri; a real-connection test
  gated behind `AUTOTESTER_LIVE_MONGO_TEST=1` (skipped by default — D5, and consistent with this
  session's decision not to make a live Pathlynks/Mongo call without an unambiguous go-ahead).
- `docs/ARCHITECTURE.md` — concept→file row for `browser/db.py::ReadOnlyCollection`; Status line
  updated (T-045 built; T-050 next, noted as pending human sign-off for the live run). 141 lines
  (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_db.py -v` → 5 passed, 1 skipped (skip reason names the env var)
- `uv run pytest -q` → exit 0, 121 collected (120 passed + 1 skipped; was 115 before this unit)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 141 (≤ 150)
- `python -c "from autotester.browser.db import ReadOnlyCollection; print(sorted(m for m in
  dir(ReadOnlyCollection) if not m.startswith('_')))"` → `['count_documents', 'find', 'find_one']`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_db.py -v
...... [collected 6, 5 passed 1 skipped, see full run above]
$ uv run pytest -q
............................s........................................... [ 59%]
.................................................                        [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run autotester map
map: docs/MAP.md regenerated
$ uv run autotester snapshot
snapshot: 32 lines written
```

## Scope notes for the checker

- `PATHLYNKS_MONGO_URI` is already declared as a `SecretRef` on `projects/pathlynks/project.json`
  since T-030 — this unit adds no new secret declaration, only the mechanism to use it read-only.
- Per the no-fire list, `EvidenceKind.DB` is NOT wired into `stages/execute.py::run_case`'s
  action-dispatch table this cycle — `Step`/`Action` have no "assert a DB document" concept yet,
  and adding one is a FlowSpec/Case-authoring decision, not required for T-045 to close.
- No secrets touched by anything this unit's own files contain — the `.env`'s real
  `PATHLYNKS_MONGO_URI` value was never read, printed, or referenced by literal in any file this
  unit wrote; the skipped live test reads it via `os.environ` only if a human explicitly opts in.
- T-045's `done_check` in `.goal/goal.json` currently points at `tests/test_execute.py` (a stale
  placeholder from when the task was filed before this unit existed) — recommend the checker (or
  a future sweep) update it to `uv run pytest tests/test_db.py -q`, which is the actual verify
  command for this unit's own deliverable.

## Status: checked-PASS

Verdict: `qa/verdicts/t045-db-assert.md` (Cycle checked: 1, PASS, 5/5; commit `0af8ac0`, pushed).
Goal task T-045 closed by the checker, which also fixed the stale `done_check` this manifest
flagged (now `uv run pytest tests/test_db.py -q`).
