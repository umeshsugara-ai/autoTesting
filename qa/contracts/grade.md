# Contract — GRADE stage (T-041)

**Covers:** goal task T-041. **Owner:** /checker. **Criticality:** HIGH — the stage that turns
observation into the verdict everything downstream (T-050, T-090, T-110, T-120, the north star's
bugs-found/false-positive scoring) depends on.
**Depends on:** `core-invariants.md` (all, esp. C7 "the executor never grades itself"),
`execute.md` (E1-E5, produces the `RawResult` this stage consumes).

## Purpose

Grade one case's `RawResult` against its `Rubric` in a fresh, stateless context — never re-run,
never given the case's own steps/script/reasoning, only the rubric and the evidence `execute.py`
recorded. Produces a `Verdict`. This is the plan's "the runner never grades itself" line, made
literal: `stages/grade.py` cannot see anything `stages/execute.py` did except what it wrote down.

## Criteria

### G1 — Stateless, evidence-only judge
`stages/grade.py::grade` receives only a `Rubric` and a `RawResult` (plus a `run_id` and a
`Provider`) — it never imports `Case`, never reads `case.steps`, never reads a `Script`. The
prompt built by `build_prompt` contains only the rubric's criteria/no-fire list and the
`RawResult`'s evidence list — no case metadata, no script source, no prior verdict.

### G2 — Deterministic outcomes never reach the judge
`Outcome.BLOCKED_HITL` → `Result.BLOCKED` and `Outcome.ERRORED` → `Result.INCONCLUSIVE`, both
without calling `judge.judge(...)` — there is nothing coherent to grade when the execution itself
didn't complete. Only `Outcome.COMPLETED` results are sent to the judge.

### G3 — PASS requires cited evidence; an unevidenced or inconsistent judgment is rejected
Before a judge's `Judgment` becomes the stage's `Verdict`, `_inconsistency` checks it against the
rubric it was actually given: every `Failure.criterion_id` must name a real criterion; a
criterion with `evidence_required=True` must have a non-empty `evidence_refs` when cited as a
failure; `criteria_total` must equal the rubric's criterion count; `PASS` requires an empty
`failures` list; `FAIL` requires a non-empty one. Any violation downgrades the result to
`Result.INCONCLUSIVE` with a `note` naming which check failed — the stage never lets a
self-contradictory or unevidenced judgment ship as PASS or FAIL. This is the mechanism behind the
plan's "seeded fake-pass rejected" eval row.

### G4 — Verdict is complete and persisted
Every path through `grade()` returns a `Verdict` with `run_id`, `case_id`, `result`,
`grader_provider` (the real provider id for a judged call, `"rule"` for a deterministic one),
and `rubric_hash` (`Rubric.fingerprint`) always set. `ProjectStore.save_verdict(run_id, verdict)`
writes it to `projects/<slug>/runs/<run_id>/<case_id>.verdict.json`, distinct from the
`RawResult` file at `<case_id>.json` so `load_results`/`load_verdicts` never cross-read each
other's files (C6 — no new file format, one glob pattern per artifact kind).

### G5 — Prompt is a file, not an inline string
The grading prompt lives at `prompts/grade_v1.md`, versioned by filename per the project's
"prompts are files" rule; `build_prompt` only fills placeholders, it never constructs prompt
text inline in `grade.py`.

## No-fire list

- Choosing which provider judges (that's the project's `providers{judge: ...}` config, not this
  stage's job — `grade()` takes an already-constructed `Provider`).
- Multi-case aggregate scoring / a run-level report (T-100's job).
- Retrying a judge call on a malformed response (the mock provider in tests never fails this
  way; a real provider's structured-output failure handling is a provider-layer concern).
- `EvidenceKind.DB` assertions (T-045) — grade.py grades whatever evidence exists; it does not
  require a particular evidence kind to be present.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-041 (grade stage), following the pattern set by
  `execute.md` for T-040 — no contract existed before this cycle.
