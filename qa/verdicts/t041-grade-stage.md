# Verdict — t041-grade-stage

**Date:** 2026-09-03
**Cycle checked:** 1
**Contract:** qa/contracts/grade.md (G1-G5) + qa/contracts/core-invariants.md (C7) + qa/contracts/execute.md
**Manifest:** qa/manifests/t041-grade-stage.md

## What I re-ran myself (fresh, not trusted from the manifest)

- `uv run pytest tests/test_grade.py -v` → `collected 10 items` / `10 passed in 0.32s`.
- `uv run pytest -q` (full suite, verbose confirm) → `113 passed in 1.54s`. Dot-count in `-q`
  output is 72 (77%) + 41 (100%) = 113, consistent.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `wc -l docs/ARCHITECTURE.md` → `140` (<=150, contract limit).

All match the manifest's claimed outputs exactly.

## Criteria judged on evidence

**[G1] Stateless, evidence-only judge — MET.** Read `stages/grade.py::build_grade_prompt` in
full (lines 40-46). It reads only `rubric` (via `_render_rubric`) and `result.evidence`/
`result.outcome` (via `_render_evidence`), plus the template file and `rubric.feedback_format`.
No import of `Case` or `Script` anywhere in `grade.py` (grepped: only imports are `RepoDocs`,
`Provider`, `Outcome`/`Result`, `RawResult`, `Failure`/`Judgment`/`Rubric`/`Verdict`). `case_id`
is passed to `grade()` only to populate the `Verdict` envelope after judging
(`_verdict(..., result=result, ...)` reads `result.case_id`), never rendered into the prompt
string. Confirmed by `test_prompt_carries_only_rubric_and_evidence_no_case_metadata`, which I
re-ran (passing) and which asserts `"case_abc" not in prompt` — verified this assertion is real
by reading the test body, not just its name.

**[G2] Deterministic outcomes never reach the judge — MET.** `grade()` lines 83-90: both
`BLOCKED_HITL` and `ERRORED` branches `return _verdict(...)` before `build_grade_prompt`/
`judge.judge` are ever called. `test_blocked_hitl_is_blocked_without_calling_the_judge` and
`test_errored_is_inconclusive_without_calling_the_judge` both assert `judge.prompts == []` — the
mock provider's own call log, not an inference — and both pass.

**[G3] Unevidenced/inconsistent judgment rejected — MET, mechanism verified directly.** Read
`_inconsistency()` (grade.py:49-64) end to end: it checks (a) every `failure.criterion_id` is in
`known_ids` else names the unknown id, (b) any failure on an `evidence_required` criterion with
empty `evidence_refs`, (c) `criteria_total != len(rubric.criteria)`, (d) `PASS` with non-empty
`failures`, (e) `FAIL` with empty `failures` — exactly the five checks the contract names.
`grade()` line 94-98 calls it after `judge.judge(...)` and downgrades to `Result.INCONCLUSIVE`
with a `note` naming the specific check, before any of those five conditions could reach the
caller as PASS/FAIL. Three of the five branches have dedicated tests I re-ran and confirmed pass:
unknown criterion, missing evidence_refs, PASS-with-failures. The other two branches
(`criteria_total` mismatch, FAIL-with-no-failures) have no dedicated test, but I read their code
directly (grade.py:58-59, :62-63) — same simple equality/emptiness checks as the tested branches,
correctly wired into the same downgrade path — so the mechanism is verified by direct reading,
not by assuming untested code works. Noting this as a minor test-coverage gap, not a criterion
failure: the contract asks for the mechanism to exist and work, which it does.

**[G4] Verdict complete and persisted — MET.** Every return path in `grade()` constructs via the
shared `_verdict()` helper (lines 67-77), which always sets `run_id`, `case_id=result.case_id`,
`result=verdict_result`, `grader_provider` (`"rule"` for the two deterministic paths, `judge.id`
for a judged one), and `rubric_hash=rubric.fingerprint` — no path skips any of these. Read
`store/project_store.py`: `save_verdict` writes to `<case_id>.verdict.json`; `load_results`
(line 79) explicitly excludes `*.verdict.json` from its `*.json` glob so it never cross-reads a
verdict as a result. `test_verdict_round_trips_through_project_store_without_colliding_with_results`
re-run and passes, exercising both `load_results` and `load_verdicts` against the same run dir.

**[G5] Prompt is a file — MET.** `src/autotester/prompts/grade_v1.md` exists, contains
`{{RUBRIC}}`, `{{EVIDENCE}}`, `{{FORMAT}}` placeholders. `build_grade_prompt` only does
`.read_text()` + `.replace()` calls — no inline prompt text constructed in `grade.py`.
`test_prompt_is_read_from_a_file_not_built_inline` re-run and passes.

**No-fire list respected.** `grade()` takes an already-constructed `judge: Provider` — no
provider-selection logic in the stage. No multi-case aggregation. No retry-on-malformed-judge-
output. No `EvidenceKind.DB` requirement — `_render_evidence` renders whatever `result.evidence`
contains generically.

**Dependency check — core-invariants C7 ("the executor never grades itself").** Satisfied
structurally: `grade.py` has zero imports from `stages/execute.py`, `schema/case.py`, or
`schema/script.py` (grepped the import block, lines 12-18) — it only consumes `RawResult`, the
already-recorded evidence artifact, never anything execute.py used internally.

## Manifest bookkeeping

- `Issues addressed: none` — correct, this is a new unit; nothing in `qa/issues.jsonl` claims to
  be fixed by it, so nothing to cross-check there.
- No secrets touched: grepped `grade.py`, `test_grade.py`, `grade_v1.md`, `verdict.py` for
  `.env`-shaped tokens — none found; this unit is pure code/schema/prompt/tests, consistent with
  the manifest's own claim.
- No new issues found; `qa/issues.jsonl` unchanged by this check.

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 1/1 invariant holds (C7)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All five grade.md criteria (G1-G5) are evidenced by direct code reading plus a
fresh re-run of tests/test_grade.py (10/10) and the full suite (113/113, was 103), ruff clean,
doctor clean, ARCHITECTURE.md at 140/150 lines. G3's self-consistency mechanism was read in full
and confirmed to implement all five named checks; three of five have dedicated passing tests, the
other two (criteria_total mismatch, FAIL-with-no-failures) are covered by direct code reading
only — a minor test-coverage gap worth the maker adding, not a contract violation. No case
metadata leaks into the judge's prompt (grep + dedicated test). No-fire list and C7 dependency
both respected.
```
