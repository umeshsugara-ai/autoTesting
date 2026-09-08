# at141-at115-done-check-can-fail

**Unit:** AT-141 (medium) + AT-115 (medium) — the sweep's outstanding queue row
**Commit:** b86bf77
**Fix cycle:** 1
**Contract:** `qa/contracts/core-invariants.md` **C9**

## The gap, stated as C9 states it

C9: *a declared control value is honoured or rejected, never silently ignored.* It names three
fields — `base_criticality`, `done_check`, `approved` — and its **Verify** clause tested only the
first. So the field C9 governs second was ungoverned by C9.

Three tasks proved it. **Measured before touching anything:**

```
T-126/T-150 done_check `uv run autotester doctor`             -> exit 0
T-135      done_check `uv run pytest -q && autotester doctor` -> exit 0
T-145      done_check `check_crawl_approval.py erp`           -> exit 1   (post-AT-100, correct)
```

All three exit **0 before any of their work exists**. That is the AT-100 shape **three** times, not
the twice AT-115 recorded — and it lives in the machinery that decides whether anything is finished.

## What changed

`scripts/check_deliverable.py` — so a task can name a deliverable instead of a repo-wide health
command. **Deliberately dumb:** it checks the artifact is *there*, not that it is good. A
`done_check` that tried to judge quality would be a second, worse checker, and the real one already
exists.

| Task | Now checks | Exit today |
|---|---|---|
| T-135 | `merge_flowspec.py` + its tests | 1 |
| T-150 | the two checker-authored Track C contracts | 1 |
| T-126 | the D-018 adapter-allowlist widening, then doctor | 1 |

Each will exit 0 exactly when its deliverables exist — which is the whole property.

## The guard, and why it is static

`tests/test_goal_done_checks.py`. Running every pending `done_check` for real would take minutes
**and would pass once the work landed** — so "it fails today" is the wrong property. What is worth
pinning is that a check is **capable of failing**: it names something specific to its task rather
than asserting the repo is healthy.

## The self-correction that justifies the guard having a self-test

**My first predicate did not catch `true`** — AT-100's original defect, verbatim, on the CRITICAL
live-ERP crawl. I had written it against the three offenders in front of me instead of against the
shape's own history, which is the same "I fixed the instance I was looking at" pattern AT-148 →
AT-149 → AT-150 → AT-151 has been about all afternoon.

`test_the_guard_recognises_the_shapes_it_exists_to_catch` failed and told me. **A guard whose
predicate is wrong protects nothing**, so the predicate is pinned against real commands from this
repo's history — including the two shapes it must catch and the three it must not.

## Evidence — C7-compliant, and reporting inconclusiveness where it applies

```
SABOTAGE W: anchor matched once, file changed
SABOTAGE W (T-126's done_check reverted to `autotester doctor`)
  failures: 2
    FAILED ...::test_no_pending_task_has_a_done_check_that_cannot_fail
    FAILED ...::test_the_three_known_offenders_are_actually_fixed

SABOTAGE X: anchor matched once, file changed
SABOTAGE X (AT-100's original `true` on the CRITICAL live-ERP crawl)
  failures: 1
    FAILED ...::test_no_pending_task_has_a_done_check_that_cannot_fail

SABOTAGE Y: anchor matched once, file changed
SABOTAGE Y (the guard's own predicate stops recognising repo-wide commands)
  failures: 1
    FAILED ...::test_the_guard_recognises_the_shapes_it_exists_to_catch

RESTORED
4 passed
```

The harness reports a zero-failure sabotage as **INCONCLUSIVE — mutation not shown to change
behaviour** rather than as a vacuous test, per the C7 clause the checker amended one unit ago. None
of the three hit that path; the branch exists because the next one might.

**Y is the one I would keep.** W and X prove the data is fixed; Y proves the *guard* is, and a guard
that cannot fail is precisely the defect this unit is about — one level up.

## Put to the checker

1. **Is a static predicate the right instrument here**, or does C9 want the checks actually
   executed? I argue static, because a dynamic check inverts the moment the work lands and so cannot
   be a standing regression test. If you disagree, the alternative is a periodic sweep check rather
   than a unit test, and that belongs in your sweep rather than in `tests/`.
2. **`is_capable_of_failing` is a heuristic and will have false negatives** — a task-specific
   command I have not thought of that is nonetheless unfailable. It fails *open* (permissive), which
   is the wrong direction for a guard. I could not find a way to make it fail closed without
   rejecting legitimate checks; if you can, that is a better unit than this one.

## Verification (host; Docker down, `uv` native; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          654 passed, 2 skipped   (650 before + 4 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT claim

- **C9's third field, `approved`, is still unpinned by any test.** This unit closes the second of
  three. Naming it so the gap is on record rather than implied closed.
- No crawl has run against a real product.
- **AT-153** (percent-encoded dot-segments, `low`) was filed against the consent path by the last
  verdict and is **deliberately queued, not fixed** — the consent-hardening chain was closed on disk
  before this unit began, and reopening it for a low advisory-only finding is exactly the drift that
  commitment exists to prevent.

## Status: checked-PASS
