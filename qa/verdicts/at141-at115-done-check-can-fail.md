# Verdict — at141-at115-done-check-can-fail

**Date:** 2026-09-08
**Cycle checked:** 1
**Commit checked:** b86bf77 (tree at b0b3eb3, `git status` clean)
**Contract:** `qa/contracts/core-invariants.md` C9 (+ C7 on the sabotage evidence)

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 2/2 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: AT-154, AT-155, AT-156, AT-157 (all open, none blocking)
ISSUES-CLOSED: AT-115, AT-141 -> verified
EXPLANATION: I re-measured the prior state at b86bf77^ rather than believing it — all three
old done_checks really do exit 0 on a tree where none of their work exists, so the AT-100 shape
was present three times as the maker claims and not twice as AT-115 recorded. All three new
checks exit 1 today AND flip to exit 0 in a scratch copy once their deliverables are created,
so they are failable in both directions, which the manifest did not prove. Sabotages W, X and Y
all reproduce in my own harness with anchor-uniqueness and file-changed assertions armed. The
predicate's false negatives are real and I found more than the maker did — but they are declared
in the manifest as an open weakness rather than claimed closed, so they are new issues, not a
FAIL of the unit's own scope.
```

## What I re-ran

### 1. Verification (manifest's claims, counted myself)

```
uv run pytest                          654 passed, 2 skipped, 1 warning in 70.49s
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
git status --porcelain                 (empty)
```

All three claims reproduce exactly.

### 2. The prior state at `b86bf77^` — measured, not believed

`git show b86bf77^:.goal/goal.json` confirms the four commands the manifest quotes. Running them:

```
OLD T-126 / T-150  uv run autotester doctor                       -> exit 0
OLD T-135          uv run pytest -q && uv run autotester doctor    -> exit 0
    T-145          check_crawl_approval.py erp                     -> exit 1  (post-AT-100)
```

None of T-126/T-135/T-150's deliverables exist on this tree (confirmed below), so all three
would have reported "done" for work nobody has started. **The maker's measurement is correct,
including the correction from two occurrences to three.**

### 3. The new checks — failable in BOTH directions

Negative direction, live tree:

```
T-135  check_deliverable --exists merge_flowspec.py test_merge_flowspec.py && pytest ...  -> exit 1
       FAIL missing: src/autotester/stages/merge_flowspec.py
       FAIL missing: tests/test_merge_flowspec.py
T-126  check_deliverable --contains qa/adapter.json explore_proof && doctor               -> exit 1
       FAIL qa/adapter.json does not mention 'explore_proof'
T-150  check_deliverable --exists ai-target.md adversarial.md && doctor                   -> exit 1
       FAIL missing: qa/contracts/ai-target.md
       FAIL missing: qa/contracts/adversarial.md
```

Positive direction — **the manifest does not prove this and it matters as much**: a check that
can never pass is as broken as one that can never fail. In a `git archive HEAD` scratch copy
(AT-101 — the live tree was never touched):

```
T-150  before: exit 1 (both missing)
       touch qa/contracts/ai-target.md qa/contracts/adversarial.md
       after:  OK 2 deliverable(s) present    -> exit 0
T-126  before: 'explore_proof' in qa/adapter.json = False -> exit 1
       insert the key into the scratch copy
       after:  OK 1 deliverable(s) present    -> exit 0
```

Both flip. The property the manifest claims — "each will exit 0 exactly when its deliverables
exist" — is now evidenced, not asserted.

### 4. Sabotages W, X, Y — my own harness, C7-compliant

Independent harness in the scratchpad: `git archive HEAD` per run, `PYTHONPATH` pinned to the
scratch `src/`, and **every mutation asserts its anchor matched exactly once and that the file
on disk changed** before any result is believed; a zero-failure run would print
`INCONCLUSIVE — mutation not shown to change behaviour`. I did not read or re-run the maker's
harness.

```
BASELINE: 4 passed
SABOTAGE W (T-126 done_check reverted to `uv run autotester doctor`): failures=2
    test_no_pending_task_has_a_done_check_that_cannot_fail
    test_the_three_known_offenders_are_actually_fixed
SABOTAGE X (AT-100's original `true`, on T-145 the CRITICAL live-ERP crawl): failures=1
    test_no_pending_task_has_a_done_check_that_cannot_fail
SABOTAGE Y (the REPO_WIDE branch deleted from the predicate): failures=1
    test_the_guard_recognises_the_shapes_it_exists_to_catch
RESTORED: 4 passed
```

All three reproduce, none hit the INCONCLUSIVE branch. **The maker's read of Y is right and I
endorse it:** W and X prove the data is fixed and would be satisfied by any correct predicate;
Y is the only one that pins the *guard itself*, and a guard that cannot fail is the very defect
this unit exists to remove, one level up. If only one of the three survives a future prune, keep Y.

### 5. Attacking `is_capable_of_failing` — the maker asked, so here is the list

17 candidates driven directly against the predicate. Accepted (false negatives):

| Command | Why it slips through | Actually |
|---|---|---|
| `uv run pytest tests/ -q` | `tests/` satisfies `startswith("tests")` | full suite, **exit 0 measured** |
| `uv run pytest tests` / `uv run pytest -q tests/` | same | full suite |
| `uv run pytest --collect-only tests/test_x.py` | path ends `.py` | collects, never runs; **exit 0 measured** |
| `echo done` | unrecognised shape | cannot fail |
| `uv run python -c "pass"` | unrecognised shape | cannot fail |
| `test -f README.md` | unrecognised shape | a repo fixture, not a deliverable |
| `ls <path> \|\| true` | splitter handles `&&` and `;`, **not `\|\|`** | cannot fail |
| `cat <path> > /dev/null \|\| exit 0` | same | cannot fail |
| `true # tests/test_x.py` | `shlex.split` keeps the comment as a part | cannot fail |

Correctly rejected: `autotester doctor || true`, `doctor; true`, `doctor && true` — but only
incidentally, because the segment still contains the `doctor` marker; the `|| true` itself is
invisible to the predicate.

One reassuring measurement: `uv run pytest tests/test_nonexistent.py -q` exits **4**, not 0 — a
typo'd path in a `done_check` fails loudly rather than passing silently. That failure mode is
not open.

The `pytest tests/` family is filed as **AT-154** — it is not an exotic, it is a hole inside the
predicate's own docstring, which claims a bare `pytest` is rejected and a named file accepted.
The rest is **AT-155**.

### 6. The two questions, ruled

**(a) Static predicate or executed checks?** — *The maker is right, and the reasoning is now in
the contract.* A standing regression test must pin an invariant, and "this check fails today" is
not one: it inverts the moment the work lands, so the dynamic form would go green exactly when
the task completes and assert nothing thereafter. What is invariant is that a `done_check` names
something specific to its own task. The dynamic direction is not discarded — it belongs to sweep
check 4's third loop-design question ("is every `done_check` at least as strong as the contract
criterion it closes"), which is mine to run, not `tests/`. Recorded as a routine amendment to
C9's Verify clause today.

**(b) Can it fail closed?** — **Yes, and the maker is right that it would be a better unit.**
Concretely (filed as AT-155): invert the denylist to an allowlist evaluated per segment. Accept a
segment only if it is (i) `check_deliverable.py` carrying at least one `--exists`/`--contains`,
(ii) `pytest` naming a part that ends `.py` or contains `::` and **not** carrying
`--collect-only`, or (iii) `python scripts/<name>.py` with at least one argument. Reject outright
any command containing `||`. Then give the escape hatch a name: `done_check.waiver: "<why a
repo-wide command is right for this task>"`, which the test asserts is non-empty. Unknown shape
is then *rejected*, and the legitimate exception becomes a greppable written decision instead of
a silent pass. That is what makes it fail closed without rejecting legitimate checks — the
legitimacy just has to be written down once.

### 7. `scripts/check_deliverable.py` itself

- `--contains` on a **missing** file → `FAIL missing: <path>`, exit 1. Correct.
- `--contains` on a **binary** file → unhandled `UnicodeDecodeError` traceback, exit 1.
- `--contains` on a **directory** → unhandled `PermissionError` traceback, exit 1.
  Both crash *in the safe direction* (non-zero), so no `done_check` passes on them — filed low
  as **AT-157**.
- **Exit 2 vs 1 is not meaningful to any consumer.** A `done_check` is
  `{"type":"cmd", ..., "expect_exit":0}` (`goal/SKILL.md`), so every non-zero is treated
  identically. The no-assertion guard nonetheless **earns its place**: without it, a bare
  `check_deliverable.py` would be an unfailable no-op — and the AT-154/AT-155 predicate accepts
  exactly that string. The guard converts it into an always-fail. Keep it; the exit-2 distinction
  is for the human reading the output, not for the machine.

### 8. C9's third field, `approved`

Confirmed unpinned: `grep -c '"approved"' .goal/goal.json` → **0**; no task carries the key at
all. Every `approved` hit under `tests/` is FlowSpec review state or a consent action budget,
none of them the goal control field. The reader is
`D:/ai_os/.claude/skills/goal/scripts/criticality.py:58-66`, outside this repo, where
`bool(task.get("approved"))` releases the human gate — so a mistyped key is falsy and fails
**safe**, which is why AT-156 is low.

**Scoping ruling: leaving it out was correct.** One control field per unit is the right
granularity, the field with no live instance is the right one to defer, and the manifest names
the gap explicitly rather than letting the C9 amendment read as closed. Deferring a gap you have
written down is not the AT-149 pattern; deferring one you have not is.

## Notes

- **No `.goal` task closes on this PASS.** The unit is issue-driven; no task in `.goal/goal.json`
  references AT-141 or AT-115. `goal_cli.py done` correctly not invoked.
- **AT-153** (percent-encoded dot-segments) remains deliberately queued. The maker's stop decision
  on the consent chain stands, as the previous verdict already endorsed.
- The three tasks whose `done_check`s were rewritten (T-126, T-135, T-150) are still `pending` and
  their checks correctly say so.
