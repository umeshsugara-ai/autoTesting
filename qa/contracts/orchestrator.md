# Contract — orchestrator (resumable learn-or-explore run)

**Status:** DRAFT (authorized by D-036; the checker takes it DRAFT->ACTIVE on T-163's first PASS).
**Feature:** the run orchestrator that drives the stage pipeline as a resumable run, choosing between
the teaching (INGEST/learn) and credential-bootstrapped exploration (DISCOVER) entry paths and merging
both into a reviewed FlowSpec without overwriting human-approved truth.
**Covers:** goal task T-163. **Deps:** T-135, T-162 (both done).
**Grounding:** `.work/t163-orchestrator-design.md`; brain persistence.md + hitl.md (trace 0ee72e8c9a36).

## What the orchestrator is

A driver stage `stages/orchestrate.py::run_or_resume(project, ctx) -> RunState` that runs the existing
pure `run(input, ctx) -> artifact` stages in order, recording a durable per-stage checkpoint after each.
The checkpoint substrate is the existing filestore (T-020): each stage already persists its typed
artifact under `projects/<slug>/`, so a stage's persisted artifact IS the proof it completed. A thin
`RunState` ledger (`projects/<slug>/runs/<run_id>/state.json`) records per-stage status and the
resume pointer. No LangGraph / external database dependency is added (D-036).

`schema/run_state.py` (Pydantic, `extra="forbid"`):
- `RunState`: `run_id`, `project_slug`, `mode: Literal["learn","explore"]`, `stages: list[StageCheckpoint]`,
  `created`, `updated`.
- `StageCheckpoint`: `stage: StageName`, `status: Literal["pending","running","done","failed","skipped"]`,
  `artifact_ref: str | None`, `error: str | None`, `started`, `finished`.
- Resume pointer = the first `StageCheckpoint` whose status is not `done`/`skipped`.

## Criteria (OR1-OR6) — each judged on re-runnable evidence

- **OR1 — Path selection is explicit and recorded.** `mode` is written to RunState with the reason
  (teaching Sources present vs absent); it is never silently defaulted. A run with teaching Sources
  takes `learn`; one with credentials and no teaching Sources takes `explore`.
- **OR2 — Resume never redoes a completed stage.** Given a RunState whose stage N is `done`, a
  re-invocation enters at the first non-done stage and does NOT re-run N or rewrite N's artifact.
  (Falsifiable: mark N done with an artifact, re-run, assert N's `run()` is not called / its artifact
  is byte-unchanged, and execution resumes at N+1.)
- **OR3 — Never overwrites APPROVED truth.** An orchestrated run against a project holding an APPROVED
  FlowSpec proposes its new work into a DRAFT and stops at the review gate; the APPROVED spec's bytes
  are intact until a human approves the new one. The orchestrator routes merges through `merge_flowspec`
  (which resets to DRAFT / refuses to discard APPROVED), never a raw overwrite. (Falsifiable: APPROVED
  spec + new run -> assert APPROVED bytes unchanged and the new material is DRAFT.)
- **OR4 — A crashed stage leaves an honest checkpoint.** A stage that raises records `status="failed"`
  with a non-empty `error`, never `done`; a subsequent resume re-enters that stage. No stage is silently
  skipped or marked done without its artifact. (Falsifiable: force a stage to raise, assert its
  checkpoint is `failed` + resume re-enters it.)
- **OR5 — One run_id keys one lineage.** Checkpoints are keyed by `run_id`; two runs (different projects
  or different invocations) never read or overwrite each other's `state.json`. (Falsifiable: two runs
  with distinct run_ids -> assert each reads only its own checkpoints.)
- **OR6 — DISCOVER and MODEL are stages, not side effects.** Each is a `run(input, ctx) -> artifact`
  reading only the previous stage's artifact (the existing stage discipline). DISCOVER wraps the existing
  bounded-BFS explore path; MODEL wraps FlowSpec assembly. Neither reaches into another stage's internals.

## Explicit no-fire list (do not raise these as findings)

- No LangGraph / SqliteSaver / external DB — the filestore artifacts are the checkpoints by design (D-036).
- No concurrent same-project runs in this unit — run_id is per invocation, sequential per project (D-036;
  a superseding entry widens it if needed). Raising "should support parallel runs" is out of scope here.
- The orchestrator does NOT add a new approval mechanism — it reuses the existing review gate and
  merge_flowspec; proposing anything that bypasses them is a violation, not an enhancement.

## How a unit is verified (adapter slot 1)

`uv run pytest <the orchestrator test module>` (bare, no CLI -q, AT-503) + `uv run ruff check src tests
scripts` + `uv run autotester doctor`, all exit 0; each OR criterion carries a capability-coverage row
with a single-hunk falsifying edit reproduced green->red-for-the-named-reason->revert->green.
