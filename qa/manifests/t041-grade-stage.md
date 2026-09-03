# Manifest — t041-grade-stage

**Contract:** qa/contracts/grade.md (G1–G5, new this cycle) + qa/contracts/core-invariants.md
(esp. C7) + qa/contracts/execute.md (dependency, already PASSed)
**Goal task:** T-041 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none (new unit)

## Why this unit, not the top QUEUE.md row

`qa/QUEUE.md`'s refreshed #1 row was T-040 (now PASSed and closed). Rows #2/#3 (AT-014 author
`.goal/rubrics/T-050,T-110,T-120.md`, AT-011 author `qa/loop.md`) are real but lower-value right
now: T-050/T-110/T-120 haven't started their own contracts yet (AT-014's own fix direction says
"author each rubric when its contract is initialised... not at close time" — none of those three
have started), and `qa/loop.md` is a standing liveness gap, not a blocker for anything currently
in flight. `.goal/goal.json`'s own computed `progress.current` is `T-041`, and it is the single
task blocking the rest of the critical path (T-050 → T-090/T-100 → T-110 → T-120). Built T-041
this cycle; AT-014/AT-011 remain queued for a tick with nothing higher-value unblocked.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-041 stages/grade.py: independent stateless grader,
rubric in / Verdict out"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for the grade stage. Wrote `qa/contracts/grade.md` (G1–G5) before writing any
code, following the same pattern as `execute.md` (T-040) — the maker's one legitimate write to
`qa/contracts/` is creating a contract that does not yet exist.

## What changed

- `qa/contracts/grade.md` (new) — G1 (stateless, evidence-only) · G2 (BLOCKED_HITL/ERRORED never
  reach the judge) · G3 (an unevidenced or self-contradictory judgment is rejected, downgraded to
  INCONCLUSIVE — the mechanism behind the plan's "seeded fake-pass rejected" eval) · G4 (Verdict
  persisted, distinct file from RawResult) · G5 (prompt is a file).
- `src/autotester/schema/verdict.py` — added `Judgment` (the judge's raw structured output;
  `run_id`/`case_id`/`grader_provider`/`rubric_hash` are filled in by the stage afterward, never
  asked of the model). No existing class changed.
- `src/autotester/prompts/grade_v1.md` (new) — the grading prompt template, following the
  existing `relitigation_v1.md` pattern (placeholders, no inline prompt text in code).
- `src/autotester/stages/grade.py` (new, 102 lines) — `grade(rubric, result, run_id, judge,
  docs=None) -> Verdict`. `Outcome.BLOCKED_HITL`→`Result.BLOCKED` and `Outcome.ERRORED`→
  `Result.INCONCLUSIVE` short-circuit before any model call (G2). Otherwise builds the prompt
  (`build_grade_prompt` — named to avoid a doctor `duplicate-concept` collision with
  `ledger/relitigation.py::build_prompt`, caught by the maker's own `doctor` run), calls
  `judge.judge(prompt, Judgment)`, then `_inconsistency()` checks the answer against the rubric
  it was actually given (unknown criterion ids, missing evidence_refs on an evidence-required
  criterion, `criteria_total` mismatch, PASS-with-failures, FAIL-with-no-failures) before trusting
  it — any violation becomes `Result.INCONCLUSIVE` with the specific check named in `note`.
- `src/autotester/store/project_store.py` — `save_verdict`/`load_verdicts`, same thin-wrapper
  pattern; verdict files are `<case_id>.verdict.json` (distinct suffix from `<case_id>.json`
  RawResult files) so `load_results`'s glob was also updated to exclude `*.verdict.json`.
- `tests/test_grade.py` (new, 10 tests) — deterministic BLOCKED/INCONCLUSIVE never call the
  judge; the prompt carries only rubric+evidence, never the case id/metadata; a normal PASS;
  three distinct G3 rejections (no evidence_refs, PASS-with-failures, unknown criterion id); a
  well-evidenced FAIL is accepted as-is; Verdict/RawResult round-trip without file collision;
  the prompt file exists with its placeholders.
- `docs/ARCHITECTURE.md` — concept→file row for `stages/grade.py::grade`; Status line moved
  grade from Next to Built, Next now names T-050 (first real run). 140 lines (≤150).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_grade.py -q` → exit 0, 10 passed
- `uv run pytest -q` → exit 0, 113 tests (was 103 before this unit: +10)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean" (this run originally caught a
  `duplicate-concept` on `build_prompt` — fixed by renaming this stage's to
  `build_grade_prompt`, see What changed)
- `wc -l docs/ARCHITECTURE.md` → 140 (≤ 150)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_grade.py -q
..........                                                               [100%]
$ uv run pytest -q
........................................................................ [ 63%]
.........................................                                [100%]
(113 collected)
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

- G1's "never sees the case's own steps/script" is verified in
  `test_prompt_carries_only_rubric_and_evidence_no_case_metadata`, which asserts the literal
  string `"case_abc"` (the case id) never appears in the rendered prompt — the id is passed to
  `grade()` separately for the `Verdict` envelope, never rendered into the judge's context.
- Per the contract's no-fire list, this unit does not implement: provider selection/config
  (project-level, not this stage's job), multi-case aggregate reporting (T-100), judge
  retry-on-malformed-output, or any dependency on `EvidenceKind.DB` (T-045).
- No secrets touched — pure code, tests, and a mock-provider fixture password never a real
  `.env` value.
- T-041's `done_check` in `.goal/goal.json` is `uv run pytest tests/test_grade.py -q`, which
  passes (10/10).

## Status: checked-PASS

Verdict: `qa/verdicts/t041-grade-stage.md` (Cycle checked: 1, PASS, 5/5 criteria + C7; commit
`5b2b3f0`, pushed). Goal task T-041 closed by the checker. The checker's one non-blocking note —
two of `_inconsistency`'s five branches (`criteria_total` mismatch, FAIL-with-no-failures) were
verified correct by code reading but had no dedicated test — closed post-PASS by adding
`test_criteria_total_mismatch_is_rejected` and `test_fail_with_no_failures_cited_is_rejected`
(115 tests total now). `docs/FEATURES.jsonl` F-005 appended (`user_value: high`, per L2/L3 —
the checker's PASS didn't itself add the ledger row, so the maker did at close-out per CLAUDE.md
"Ledger on PASS"), `docs/SNAPSHOT.md` regenerated; `autotester doctor` confirms clean
(`ledger-row-missing` fired and was resolved before this close-out).
