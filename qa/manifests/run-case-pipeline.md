# Manifest — run-case-pipeline

**Contract:** qa/contracts/run-case-pipeline.md (RP1–RP4, new this cycle)
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Plan §3a (`C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md`): Umesh wants
a real "▶ Run tests" button in the UI. Before that button can mean anything for a project's own
cases (not just Umesh's 3 hand-written Pathlynks ones), the system needs a generic way to grade
an arbitrary `Case` — today every real run hand-writes a `Rubric` inline in a throwaway script.

## Real gap confirmed by reading the code (not assumed)

`Case.rubric_ref` (`schema/case.py:30`) was never populated by `stages/expand.py`, and
`ProjectStore` had no `save_rubric`/`load_rubric` methods despite `ProjectPaths.rubrics_dir`
existing since design-lock — every real grading run this session
(`run_pathlynks_first_cases.py`, `regression_proof.py`, `bench_trial.py`) built its `Rubric`
inline, by hand, in the calling script.

## What changed

- `qa/contracts/run-case-pipeline.md` (new) — RP1 (every case gradeable, no hand-written Python)
  · RP2 (default rubric is honest, grounded in the case's own rationale) · RP3 (idempotent
  persistence via the previously-unused `rubrics_dir`) · RP4 (never touches `execute.py`/
  `grade.py`'s own logic).
- `src/autotester/store/project_store.py` — `save_rubric`/`load_rubric`, one JSON file per
  rubric id, same pattern as every other artifact kind in this file (C1/C3).
- `src/autotester/stages/run_case_pipeline.py` (new, 53 lines) — `default_rubric(case,
  rubric_id)` (one plain criterion grounded in `case.rationale`, falling back to `case.title`;
  pinned criterion id `"c1"` matching the project's own established anti-invented-id pattern) and
  `run_and_grade_case(case, session, judge, run_id, store=None)` — runs the case, loads a
  persisted rubric or lazily builds+saves the default one, grades, returns `(RawResult, Verdict)`.
- `tests/test_run_case_pipeline.py` (new, 4 tests) — default rubric is grounded in rationale;
  falls back to title when rationale is empty; a fresh case gets a default rubric built AND
  persisted; an EXISTING (hand-tuned) rubric is reused, never silently overwritten.
- `docs/ARCHITECTURE.md` — one new concept→file row (merged to stay in the 150-line budget).
- `docs/MAP.md` regenerated.

## Deliberate scope decision (per the contract's own no-fire list)

The 3 existing scripts (`regression_proof.py`, `bench_trial.py`,
`run_pathlynks_first_cases.py`) are **not** refactored to call this new function in this unit —
each is already checker-PASSed against a real product/fixture with its own hand-tuned rubric;
migrating them risks a regression for no immediate benefit. The UI run-trigger (plan §3b, a
separate upcoming unit) is this function's first real caller.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_run_case_pipeline.py -v
....                                                                      [100%]
4 passed
$ uv run pytest -q                        # all green, 228 collected
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

## How to verify

- `uv run pytest tests/test_run_case_pipeline.py -v` → 4 passed
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean
- Read `src/autotester/stages/run_case_pipeline.py` in full — confirm `run_and_grade_case` never
  raises for a rubric-less case and never overwrites an existing persisted rubric.

## Scope notes for the checker

- This unit adds no new route, no new CLI command, no UI change — it is purely the shared
  function the next unit (the UI run-trigger) will call. Judge it on whether the function itself
  is correct and well-tested, not on end-user visibility (there isn't any yet).
- `default_rubric`'s criterion wording deliberately mirrors `scripts/regression_proof.py`'s own
  `make_rubric` pattern (pinned `"c1"` id, explicit instruction not to invent a different one) —
  this is a real, previously-observed failure mode (`grade.md` G3's self-consistency downgrade),
  not decoration.

## Status: checked-PASS — see qa/verdicts/run-case-pipeline.md, cycle 1 PASS
