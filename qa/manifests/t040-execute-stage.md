# Manifest — t040-execute-stage

**Contract:** qa/contracts/execute.md (E1–E5, new this cycle) + qa/contracts/core-invariants.md
+ qa/contracts/browser-and-secrets.md (dependency, already PASSed)
**Goal task:** T-040 (`user_value: normal`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none (new unit)

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-040 stages/execute.py: script-first runner producing
RawResult + Evidence"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for the execute stage. `browser-and-secrets.md`'s amendment log already
flagged this ("belongs to a future execute contract, not B1-B9"). Wrote
`qa/contracts/execute.md` (E1–E5) before writing any code, per the maker's read-only-on-contracts
rule (this is the one legitimate maker write: creating a contract that does not yet exist).

## What changed

- `qa/contracts/execute.md` (new) — E1 (no judgement) · E2 (composes session primitives) · E3
  (missing-secret → BLOCKED_HITL, not ERRORED) · E4 (RawResult persisted via ProjectStore) · E5
  (write_policy respected by construction — the stage only runs the steps the case already has).
- `src/autotester/browser/session.py` — four new `BrowserSession` methods, same pattern as the
  existing ones (one action, evidence via `_record`, secrets never logged raw):
  `select_option`, `upload`, `wait_for`. No existing method changed.
- `src/autotester/stages/__init__.py` (new) — package docstring only.
- `src/autotester/stages/execute.py` (new, 75 lines) — `run_case(case, session) -> RawResult`.
  Dispatches each `Step.action` to a session method via a `dict[Action, StepHandler]` table
  (`ASSERT` is a no-op handler — evidence-only, see E1). Catches `MissingSecret` →
  `Outcome.BLOCKED_HITL` with `hitl_prompt`; any other exception → `Outcome.ERRORED` with
  `error` naming the exception type/message; otherwise `Outcome.COMPLETED`. A screenshot is taken
  after every step that doesn't raise, labeled `step<NN>-<action>`.
- `src/autotester/store/project_store.py` — `save_run`/`load_run`/`save_result`/`load_results`,
  same thin-wrapper-over-`filestore` pattern as the existing methods (no new file format; C6/C1).
  `runs/<run_id>/run.json` for the `Run` envelope, `runs/<run_id>/<case_id>.json` per result.
- `tests/test_execute.py` (new, 6 tests) — completed run (composes all four dispatch-table
  actions used + screenshots every step including the judgement-free ASSERT); select/upload/wait
  actions; a mid-step exception is `ERRORED` (not a crash, later steps never run); a missing
  declared secret is `BLOCKED_HITL` not `ERRORED`; `Run`/`RawResult` round-trip through
  `ProjectStore`; an unknown run's results load as `[]`, not an error.
- `docs/ARCHITECTURE.md` — concept→file row for `stages/execute.py::run_case`; Status line moved
  execute from Next to Built, Next now names `grade.py`. 139 lines (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated (`autotester map` / `autotester snapshot`).

## How to verify (commands + expected)

- `uv run pytest tests/test_execute.py -q` → exit 0, 6 passed
- `uv run pytest -q` → exit 0, 103 tests (was 97 before this unit: +6)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 139 (≤ 150)
- `grep -n "taskkill\|pkill\|killall" src/autotester/browser/session.py` → no output (B9 still
  holds; the new methods don't touch process control)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_execute.py -q
......                                                                   [100%]
$ uv run pytest -q
........................................................................ [ 69%]
...............................                                          [100%]
(103 collected: test_bench 3, test_browser 11, test_core 9, test_doctor 6,
 test_execute 6, test_ledger 20, test_onboard_pathlynks 4, test_schema 8,
 test_secrets 24, test_store 12)
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run autotester map
map: docs/MAP.md regenerated
$ uv run autotester snapshot
snapshot: 31 lines written
```

## Scope notes for the checker

- Per the contract's no-fire list, this unit does not implement: vision/LLM judgement of
  `visual_signal` (grade.py, T-041), the agent-fallback code-gen path (T-080), `EvidenceKind.DB`
  / Mongo assertions (T-045's own follow-on — `EvidenceKind` was not touched this cycle), retry
  logic, or CI/schedule triggers.
- `Action.ASSERT` deliberately performs no comparison against `Step.expected` — it only takes a
  screenshot (E1). This was a design choice made during the build (see contract E1's wording)
  rather than an oversight: comparing evidence against `ExpectedState` is `grade.py`'s job so
  that PASS/FAIL always comes from one place, judged fresh, per the plan's grading model.
- No secrets touched by this unit's own files — `check_no_secrets.py` was not re-run here since
  no `.env` value or credential-adjacent content appears in anything this unit wrote (pure code +
  tests using a fixture password `hunter2` local to the test fixture, never a real `.env` value).
- T-040's `done_check` in `.goal/goal.json` is `uv run pytest tests/test_execute.py -q`, which
  passes (6/6).

## Status: checked-PASS

Verdict: `qa/verdicts/t040-execute-stage.md` (Cycle checked: 1, PASS, 5/5 + 8/8; commit `dfb6c51`,
pushed). Goal task T-040 closed by the checker.
