# Verdict — t163-orchestrator (PRIMARY of a dual check)

**Date:** 2026-09-23
**Cycle checked:** 1
**Contract:** `qa/contracts/orchestrator.md` — DRAFT -> **ACTIVE** (flipped by this verdict per D-036's
own authorization; see the contract's amendment log entry added alongside this file).
**Manifest:** `qa/manifests/t163-orchestrator.md`
**Bound project:** `D:/autoTesting/.worktrees/t163-orchestrator`
**Executor:** manifest names none explicitly; no `ANTHROPIC_BASE_URL` override observed in the
worktree — `self != executor` holds (checker: claude-sonnet-subagent, fresh context).

## What I re-ran myself

- `PYTHONUTF8=1 uv run pytest` (bare, whole suite) at HEAD `7cb1d61`: **1578 passed, 5 skipped, 32
  xfailed, 1 warning in 692.67s. 0 failed.** Whole-log scanned for `FAILED|ERROR|^E ` — zero matches.
- `PYTHONUTF8=1 uv run pytest tests/test_orchestrate.py tests/test_orchestrate_runners.py` (T-163's
  registered `done_check`): **10 passed in 1.41s** — exactly the 10 tests the manifest claims.
- `PYTHONUTF8=1 uv run ruff check src tests scripts`: **All checks passed!**
- `PYTHONUTF8=1 uv run autotester doctor`: **1 violation** — `stale-generated: docs/SNAPSHOT.md —
  differs from regeneration; run autotester snapshot`. Investigated below (not counted against this
  unit).
- `git diff 2a0b31e...HEAD --stat` + full diff, and `git show --name-only 6cad8e0` (the unit's own
  commit) for C10 scoping.

## OR1–OR6 — capability coverage (6/6 rows reproduced in a throwaway copy)

Copied `src/`, `tests/`, `scripts/`, `pyproject.toml`, `uv.lock` into 6 isolated scratch dirs outside
the bound tree, junctioned each to the bound tree's own `.venv`. Every row: GREEN in the copy before
the edit (proves the copy is real), single-hunk edit exactly as the manifest describes, RED with the
**named** assertion/exception, discarded (throwaway, no revert needed since the copy is never reused).

| OR | Falsifying edit applied | Result |
|---|---|---|
| OR1 | `orchestrate.py::choose_mode`: `if teaching:` → `if False and teaching:` | GREEN → `AssertionError: assert 'explore' == 'learn'` (exact match) |
| OR2 | `orchestrate.py::run_or_resume`: drop the done/skipped guard → `if False and checkpoint.status in (...)` | GREEN → `AssertionError: a done stage was re-run\nassert 2 == 1` (exact match) |
| OR3 | `orchestrate_runners.py::make_model_runner`: `merged = merge_flowspec(...)` → `merged = incoming` | GREEN → `assert None is not None` on the `s_home` survivor lookup (exact match — reviewed screen discarded) |
| OR4 | `orchestrate.py::_run_stage` except branch: `"status": "failed"` → `"status": "done"` | GREEN → `AssertionError: assert 'done' == 'failed'` (exact match) |
| OR5 | `orchestrate.py::_state_path`: `run_dir(ctx.run_id)` → `run_dir("shared")` | GREEN → `AttributeError: 'NoneType' object has no attribute 'run_id'` (exact match — lineages collided) |
| OR6 | `orchestrate_runners.py::_read_proposal` None-branch: `raise MissingArtifact(...)` → `return FlowSpec(project="demo")` | GREEN → `Failed: DID NOT RAISE MissingArtifact` (exact match) |

All 6 assertions that fired are the ones each row is named for (no wrong-reason reds; no import/parse
breakage that would have reddened everything). CAPABILITY-COVERAGE: **6/6 reproduced.**

## OR3 — extra scrutiny (per dispatch)

Read `stages/merge_flowspec.py` and `stages/review.py` in full, not just the test.
- `merge_flowspec`: `_new_screens`/`_new_flows` only ever **add** rows the existing spec lacks by id;
  an existing `Screen`/`Flow` object is never replaced. `_learned_url_patterns` fills a `None`
  `url_pattern` only — never overwrites one already set. Any real change (`added_screens`,
  `added_flows`, `new_patterns`, `new_conflicts` non-empty) resets `review` to
  `Review(status=DRAFT, note=...)` — the gate is **re-armed**, not bypassed. `merge_flowspec` returns
  `existing` unchanged (no version bump, no review reset) on a genuine no-op merge.
- `review.py::require_reviewed` raises `FlowSpecNotReviewed` unless `spec.review.status is APPROVED`
  — called by `expand.py` before any case generation.
- `orchestrate_runners.py::make_model_runner` calls `merge_flowspec` and nothing else — no local
  approval logic, no direct `flowspec.json` write bypassing the merge seam.
- `test_orchestrated_run_never_overwrites_approved_truth` asserts all three legs at once:
  `survivor.model_dump() == approved.screens[0].model_dump()` (byte-identical reviewed screen),
  the new screen present, `review.status is DRAFT`, and `require_reviewed` raising — and I reproduced
  the falsifying edit (raw overwrite) going red on exactly the survivor assertion (row OR3 above).
- Conclusion: the contract's own "Interpretation note for the checker" is correct — `flowspec.json`
  being rewritten to the DRAFT merge is how the review gate re-arms, not an overwrite of APPROVED
  truth. No new approval path exists; the orchestrator reuses the existing seam exactly as claimed.
  **No FAIL here.**

## Diff scope (step 4c)

`git diff 2a0b31e...HEAD --stat`: 11 files, +765/-11. Every path is either in the manifest's "What
changed" (`schema/run_state.py`, `stages/orchestrate.py`, `stages/orchestrate_runners.py`,
`tests/test_orchestrate.py`, `tests/test_orchestrate_runners.py`, `docs/ARCHITECTURE.md`,
`docs/MAP.md`, `docs/SNAPSHOT.md`, the manifest itself) or is the disclosed merged-master material
(`.goal/goal.json`, `.goal/dashboard.html` — tick timestamps + T-163 registration from `daafba4`/
`b8c2297`/`7cb1d61`, not this unit's own work). No existing function, class, test, route, or config
key is deleted or renamed. `git show --name-only 6cad8e0` (the unit's own feature commit) touches
**only** the 9 paths above — C10 (a unit's commit carries only that unit's paths) holds. `pyproject.toml`
and `uv.lock` are byte-identical to base — no new dependency. `schema/base.py` untouched; the only new
file under `schema/` is `run_state.py` — no schema sprawl outside it. ARCHITECTURE.md is exactly 150
lines (doctor's cap, and doctor raised no size violation). No vendor SDK import in the two new stage
modules (C8 holds).

## Explicit no-fire list — honored

Grepped for `langgraph|sqlite|sqlalchemy` in the three new/changed modules: no hits. Grepped for
`approve|APPROVED` usage: only comments/docstrings referencing the existing gate, no new approval
logic. `run_id` is per-invocation and sequential; nothing here adds concurrent-run support, and none
was raised as a finding.

## Doctor's 1 violation — investigated, not counted against this unit

`stale-generated: docs/SNAPSHOT.md` traces to the branch's own **base** commit, not to T-163's diff:
`git show 2a0b31e:docs/DECISIONS.md` already contains `D-036` and `D-037`, but
`git show 2a0b31e:docs/SNAPSHOT.md` still lists "Last decisions" only through `D-035` — i.e. master
was already stale at the commit this branch forked from, before any T-163 work happened. T-163's own
feature commit (`6cad8e0`) *did* regenerate `docs/SNAPSHOT.md` correctly at the time it was made; the
subsequent `merge master` commit (`daafba4`, explicitly disclosed by the dispatch as not this unit's
change) reintroduced the staleness by pulling in `D-037` without a snapshot regen. This is the exact
recurring shape already on this project's ledger as **AT-557** (`stale-generated-doc`, found by a
Mode B sweep, fixed once, evidently regressed since) and the exact reasoning already applied by a
Mode A unit checker in **`ISS-t162-drive-2b-1`** ("Not a blocker on this unit's own PASS — the
staleness predates it ... and this unit did not touch [the stale file]"). Filed as **ISS-t163-1**
(severity low). No OR criterion depends on `docs/SNAPSHOT.md` content, and re-running `autotester
snapshot` is a one-command doc regen unrelated to the orchestrator's own logic — filing it as debt
rather than failing a CRITICAL unit's cycle-1 PASS over an inherited housekeeping gap is consistent
with this project's own precedent and with core-invariants' no-fire principle (don't judge a unit
harder than the pattern already established for equivalent gaps elsewhere in this repo).

## Goal wiring

T-163's registered `done_check` (`uv run pytest tests/test_orchestrate.py tests/test_orchestrate_runners.py`)
re-run directly: **10 passed**. Closed via
`python D:/ai_os/.claude/skills/goal/scripts/goal_cli.py done --root "D:/autoTesting/.worktrees/t163-orchestrator" --task-id "T-163"`
→ `{"ok": true, "task": "T-163", "percent": 67}`.

## Not touched (confirmed)

`merge_flowspec.py`, `review.py`, `ingest.py`, `explore_merge.py`, `schema/base.py`, the filestore —
all byte-identical to base. `qa/adapter.json` unchanged.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (OR1-OR6), 10/10 core invariants hold for this unit's own diff
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 6/6 rows reproduced (throwaway copy, green-before -> red-for-the-named-reason)
LIVE-BROWSER: not-applicable (orchestration/schema layer; changed paths: schema/run_state.py, stages/orchestrate.py, stages/orchestrate_runners.py, tests/test_orchestrate.py, tests/test_orchestrate_runners.py, docs/ARCHITECTURE.md, docs/MAP.md, docs/SNAPSHOT.md)
ISSUES-WRITTEN: ISS-t163-1 (low, stale-generated-doc, not a PASS blocker per AT-557/ISS-t162-drive-2b-1 precedent)
EXECUTOR: none named (checker: claude-sonnet-subagent)
EXPLANATION: All 6 OR criteria carry a re-derived falsifying edit that reddens for the exact named
reason in a throwaway copy; whole-suite pytest is green (1578 passed, 0 failed) and ruff is clean.
OR3 was read end-to-end through merge_flowspec.py/review.py and confirmed: reviewed screens survive
byte-for-byte, only new material lands, the gate re-arms to DRAFT rather than auto-approving, and
require_reviewed still raises. doctor's sole violation (stale docs/SNAPSHOT.md) predates this unit's
base commit and is filed as debt, not charged to T-163. Contract taken DRAFT->ACTIVE; T-163 closed via
goal_cli.
```
