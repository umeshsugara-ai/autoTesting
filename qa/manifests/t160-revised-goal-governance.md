# Manifest — t160-revised-goal-governance

**Unit:** T-160 — Corrected AutoTester product-goal governance
**Commit:** `4add220`; post-close lifecycle fix `df60f4d`
**Fix cycle:** 2 of 3
**Dual check:** yes — fresh senior-software-engineer review before checker
**Contract:** D-023; `plan.md` section 9
**Goal task:** T-160

## User-visible claim

The repository now tracks the product Umesh actually requested: one UI accepts any project URL,
domain-scoped credential references and optional teaching/evaluation sources; AutoTester either
learns those sources or performs bounded breadth-first authenticated exploration, preserves a
durable Portal Persona, compiles traceable evals, reruns them after releases in a visible browser,
and produces unified HTML, Excel, text and screenshot evidence. The tracker no longer presents
the narrower prior backlog as 69% of that larger objective.

## What changed

- D-023 records the corrected north star, bounded-completeness rule, durable checkpointing,
  three-level evaluation matrix and the T-160..T-169 implementation sequence.
- `.goal/goal.json` registers T-160..T-169 with explicit dependencies and task-specific checks.
- `plan.md` section 9 maps intake, source adapters, orchestration, Portal Persona, frontier/API
  coverage, eval compilation, release regression, unified reporting and two-mode acceptance.
- `.goal/dashboard.html` and `docs/SNAPSHOT.md` were regenerated from the revised goal.
- `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered` pins all ten
  dependency lists and exact check commands, essential scope clauses, progress totals and
  generated-dashboard parity.

## Verification reproduced by maker

```text
uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider
  --basetemp=.work/pytest-t160-final
  tests/test_goal_done_checks.py tests/test_goal_criticality_vocabulary.py -q
11 passed

Full repository suite (fresh senior reviewer): 100% passed, 2 skipped
Repository Ruff (fresh senior reviewer): All checks passed!
Task graph: 55 unique tasks, 0 missing dependencies, 0 cycles
Post-close progress/dashboard: 32 done, 23 pending, 58%, exact parity
tests/test_goal_done_checks.py: 300 lines (cap met)
git diff --check: passed; Windows line-ending notices only
autotester doctor: only unrelated untracked root AGENTS.md reported
```

Fresh senior-software-engineer review of cycle 1: **APPROVE**, no findings.
Fresh cycle-2 review after the post-close check fix: **APPROVE**, no findings; full suite green.

## Cycle-2 lifecycle correction

Cycle 1 correctly verified the revised contract, but closing T-160 exposed that its regression test
had pinned the transient pre-close totals (31/24/56). That made the task's own `done_check` fail
after a legitimate PASS closeout. `df60f4d` replaces the transient constants with independent
status-count and percentage recomputation, then checks the generated dashboard against those live
values. The exact T-160..T-169 dependency and full command mappings remain literal and pinned.

## What this unit does not claim

- T-161..T-169 remain implementation work; this unit makes that remainder complete and visible.
- It does not claim unbounded exploration. Completion requires an exhausted actionable BFS
  frontier; safety/time/action/depth bounds must name all skipped, denied and unreached controls.
- It does not include or expose credential values, recordings or runtime project artifacts.
- The untracked root `AGENTS.md`, `.codex/`, `qa/.last-tick` and runtime `projects/*` artifacts are
  concurrent/out-of-scope and are excluded from this commit.
- This is pre-push evidence. The remote push and post-push live-browser validation remain pending
  the explicitly requested confirmation of the named GitHub remote and branch.

## Status: ready-for-check
