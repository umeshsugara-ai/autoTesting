# Manifest — t163-orchestrator

- **Contract ref:** `qa/contracts/orchestrator.md` (DRAFT; OR1-OR6 + Explicit no-fire list), authorized by D-036.
- **Goal task:** T-163 — resumable learn-or-explore orchestrator. CRITICAL.
- **Fix cycle:** 1 of 3
- **Dual check: required**
- **Issues addressed:** none (new unit)
- **Status: checked-PASS** (dual check, cycle 1). Primary `qa/verdicts/t163-orchestrator.md` (71badf2)
  + blind secondary `qa/verdicts/t163-orchestrator.b.md` (00036af) both PASS: 6/6 OR1-OR6 reproduced,
  OR3 (never overwrites APPROVED truth) verified end-to-end via merge_flowspec/require_reviewed on both
  sides, full suite 1578 passed / 0 failed, contract taken ACTIVE (D-036). ISS-t163-1 (stale SNAPSHOT.md,
  low, pre-existing) filed; regenerated at merge close-out.

## What changed

New driver stage that runs the existing pure `run(input, ctx) -> artifact` stages as a **resumable
run**, choosing the learn (INGEST) vs explore (DISCOVER) entry path once and merging both into a
DRAFT FlowSpec without ever overwriting APPROVED truth. No LangGraph / external DB — the existing
filestore artifacts are the checkpoints; a thin `RunState` ledger records per-stage status + the
resume pointer.

- `src/autotester/schema/run_state.py` — `RunState` + `StageCheckpoint` + `StageName` enum, Pydantic
  `extra="forbid"`. Resume pointer = `RunState.next_pending()` = first checkpoint whose status is not
  `done`/`skipped`. (finished/verified — no change needed from the prior draft.)
- `src/autotester/stages/orchestrate.py` — `run_or_resume(project, ctx) -> RunState`; `choose_mode`,
  `load_or_create`, `_run_stage` (records `running`→`done`+ref, or `failed`+error on raise), keyed by
  `run_id` at `projects/<slug>/runs/<run_id>/state.json`. (verified.)
- `src/autotester/stages/orchestrate_runners.py` — `make_ingest_runner` / `make_discover_runner` /
  `make_model_runner`: thin adapters over `ingest_video`, the injected bounded-BFS crawl +
  `merge_screens`, and `merge_flowspec`. MODEL reads ONLY `prev_ref` and folds through `merge_flowspec`
  (resets to DRAFT, refuses to discard APPROVED). Split kept both stage files ≤300 / functions ≤50.
- `tests/test_orchestrate.py` — OR1/OR2/OR4/OR5 (pre-existing draft, verified green).
- `tests/test_orchestrate_runners.py` — **NEW**: OR3 (APPROVED-truth protection) + OR6 (stages read
  only the previous artifact; DISCOVER parks its own DRAFT proposal, never `flowspec.json`).
- `docs/ARCHITECTURE.md` — under D-036: Pipeline reframed to `{INGEST | DISCOVER} → MODEL → EXPAND →
  EXECUTE → GRADE → REPORT+COVERAGE → BENCH`, named `stages/orchestrate.py::run_or_resume`, added a
  Concept→file row for the orchestrator/run_state. Kept at exactly 150 lines (doctor cap).
- `docs/MAP.md`, `docs/SNAPSHOT.md` — regenerated (`autotester map` / `snapshot`) for the new modules.

## How to verify (from the worktree, PYTHONUTF8=1)

- `uv run pytest` → expected: all pass (whole-suite; the two orchestrator modules = 10 tests).
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`.

## Capability coverage — OR1-OR6 (each falsifying edit is single-hunk, reverted after)

| OR | Test (falsifying edit) | RED (for the named reason) | GREEN |
|---|---|---|---|
| OR1 mode chosen once + reason recorded | `test_orchestrate.py::test_teaching_material_drives_a_learn_run` — `choose_mode`: `if False and teaching:` | `AssertionError: assert 'explore' == 'learn'` | reverted → pass |
| OR2 resume never re-runs a done stage | `test_orchestrate.py::test_resume_never_reruns_a_done_stage` — drop the `done`/`skipped` skip: `if False and checkpoint.status in (...)` | `AssertionError: a done stage was re-run; assert 2 == 1` | reverted → pass |
| OR3 never overwrites APPROVED truth | `test_orchestrate_runners.py::test_orchestrated_run_never_overwrites_approved_truth` — `make_model_runner`: `merged = incoming` (raw overwrite, bypass merge) | `AssertionError: assert None is not None` (approved screen `s_home` discarded) | reverted → pass |
| OR4 raising stage → failed+error, resume re-enters | `test_orchestrate.py::test_a_raising_stage_leaves_a_failed_checkpoint_then_resume_re_enters` — record `status="done"` in the except branch | `AssertionError: assert 'done' == 'failed'` | reverted → pass |
| OR5 checkpoints keyed by run_id | `test_orchestrate.py::test_two_run_ids_keep_separate_lineages` — `_state_path`: `run_dir("shared")` | `AttributeError: 'NoneType' object has no attribute 'run_id'` (both runs collide, per-run state.json absent) | reverted → pass |
| OR6 DISCOVER/MODEL read only prior artifact | `test_orchestrate_runners.py::test_model_stage_reads_only_the_previous_stage_artifact` — `_read_proposal` None-branch: `return FlowSpec(project="demo")` instead of raising | `Failed: DID NOT RAISE MissingArtifact` (MODEL reached past prev_ref) | reverted → pass |

Explicit no-fire list honored: no LangGraph/SqliteSaver/DB (filestore artifacts are the checkpoints);
run_id per invocation, sequential per project (no concurrent-run support attempted); NO new approval
mechanism — MODEL reuses `merge_flowspec` + the existing `stages/review.py::require_reviewed` gate.

## Not touched

`qa/contracts/` (contract is DRAFT, checker-owned), `qa/issues.jsonl`, `merge_flowspec.py`,
`review.py`, `ingest.py`, `explore_merge.py`, the filestore, and every other existing stage — the
orchestrator only sequences and threads refs; it reinvents no persistence and no approval path.

## Live browser evidence

Not UI-touching — orchestration/schema layer. Changed paths: `src/autotester/schema/run_state.py`,
`src/autotester/stages/orchestrate.py`, `src/autotester/stages/orchestrate_runners.py`,
`tests/test_orchestrate.py`, `tests/test_orchestrate_runners.py`, `docs/ARCHITECTURE.md`,
`docs/MAP.md`, `docs/SNAPSHOT.md`.

## Interpretation note for the checker (OR3)

The design (`.work/t163-orchestrator-design.md`) and the contract both route the merge through
`merge_flowspec`, which **resets the reviewed spec to DRAFT** and adds the new material while never
rewriting an existing (human-reviewed) screen. So "APPROVED truth intact" is tested at the
content/gate level: after a run against an APPROVED spec, every reviewed screen survives byte-for-byte
inside the merged spec, the new material is present, `review.status is DRAFT` (no auto-approval), and
`require_reviewed` raises. `flowspec.json` is intentionally rewritten to the DRAFT merge (that is how
the gate re-arms) rather than left byte-identical; flagging that as a raw overwrite would contradict
the design's "call the merge that protects APPROVED, never a raw overwrite."
