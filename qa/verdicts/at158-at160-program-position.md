# Verdict — at158-at160-program-position

**Date:** 2026-09-08
**Cycle checked:** 1
**Commit checked:** 62c3e65 (manifest 61bf5b3)
**Contract:** `qa/contracts/core-invariants.md` — C7, C9
**Verdict:** PASS

## What I re-ran myself (host, Docker down, `uv` native, bare `uv run pytest`)

```
uv run pytest                          658 passed, 2 skipped, 1 warning in 72.21s
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

**The count.** 658 confirmed, so the manifest's correction of its own commit message (which
says 661) is accurate. I also verified the manifest's *reason*: `git show 62c3e65 --
tests/test_goal_done_checks.py | grep '^[+-]def '` shows one test function renamed
(`test_a_waived_task_is_exempt_from_the_unfailable_check` →
`test_a_waived_task_is_exempt_and_an_unwaived_one_is_not`) and two non-test helpers added
(`_program`, `offenders_in`) — net zero new test functions, exactly as claimed, so the total
was always going to be unchanged from the parent.

**Ruling on how it was corrected: right call.** The commit is pushed to a public repo with
shared history; rewriting it to hide a wrong number would trade a durable, auditable record
for a cosmetic one and would break every reference to 62c3e65 (this verdict included). The
manifest is the record, the correction is greppable, and the miss is named for what it is.
Nothing in C7 requires the commit message to be the artifact of record — it requires the
*manifest* to paste real output, which it does. Rewriting history to fix a self-reported
error is also the one form of the correction that leaves no evidence the error happened.

## AT-158 families — re-driven against the new predicate

All five must-reject shapes from my previous pass are rejected (probe imports
`is_capable_of_failing` directly from `tests/test_goal_done_checks.py`):

```
ok reject  'uv run pytest --co tests/test_x.py'          program='pytest'
ok reject  'uv run pytest tests/test_x.py | true'        program='pytest'
ok reject  'uv run pytest tests/test_x.py |& true'       program='pytest'
ok reject  'echo pytest tests/test_x.py'                 program='echo'
ok reject  'true # pytest tests/test_x.py'               program='true'
```

Third-pass hunt (new shapes, none previously tried):

```
ok reject  './tools/pytest/run.py'         program='run.py'  -- a dir named pytest does not count
ok reject  'рytest tests/x.py'   (cyrillic r)       -- lookalike rejected, fail-closed
ok reject  'nohup pytest tests/x.py'       program='nohup'
ok reject  'xargs pytest tests/x.py'       program='xargs'
ok reject  'timeout 5 pytest tests/x.py'   program='timeout'
ok reject  "sh -c 'pytest tests/x.py'"     program='sh'
ok reject  'PYTEST=1 true'                 -- the '=' skip does not smuggle a name past
ok accept  'env FOO=1 pytest tests/x.py'   program='pytest'
ok accept  'uv  run  pytest tests/x.py'    (doubled spaces)
ok accept  ' uv run pytest tests/x.py '    (leading/trailing space)
ok accept  'pytest<TAB>tests/x.py'         (tab-separated)
ok accept  'python3.12 scripts/x.py' + 'python.exe scripts/x.py'
```

**Ruling on the `=` skip in `_program`.** It does the right thing in both directions:
`env FOO=1 pytest tests/x.py` resolves to `pytest` (correct — env assignments genuinely
precede the program), and `PYTEST=1 true` resolves to `true` and is rejected by
`ALWAYS_TRUE`. The skip cannot be used to smuggle a program name past the program position,
because it skips *to* the next token; it never matches on the token it skipped.

**Ruling on the two "runs nothing" forms I was asked about.**
`pytest tests/x.py --deselect tests/x.py::test_all` and `pytest tests/x.py -k <no-match>`
are both accepted, and that is correct: pytest exits **5** when nothing is collected or run,
so neither is unfailable — they fail, in the safe direction. Not a finding.

**Ruling on `python scripts/nonexistent.py` (accepted).** Correct, and deliberately so. A
`done_check` naming a script that does not exist fails at run time with a non-zero exit,
which is exactly the "distinguishes done from not-started" property the predicate protects.
Requiring the path to exist would also turn a guard whose stated design (module docstring,
lines 13–17) is to be STATIC into one that reads the current filesystem. No change wanted.

## AT-159 — re-verified accepted

```
ok accept  'python3 scripts/check_crawl_approval.py erp'
ok accept  'uv run python src/autotester/tools/verify.py'
```

## Sabotages — reproduced in my own harness (`git archive`, PYTHONPATH pinned; AT-101)

Each asserts anchor-matched-exactly-once + file-on-disk-changed before any result is
believed (C7). Restored baseline printed before and after every run.

```
RESTORED:  8 passed                                            FAILED-lines=0
Z6  (delete `and not waiver_of(r)` from offenders_in)  once=True changed=True  1 FAILED
     -> test_a_waived_task_is_exempt_and_an_unwaived_one_is_not
Z7  (program matched by any token again)              once=True changed=True  1 FAILED
Z8  (shell-neutering characters allowed)              once=True changed=True  1 FAILED
Z9  (--co stops counting as --collect-only)           once=True changed=True  1 FAILED
Z10 (python3 rejected again)                          once=True changed=True  1 FAILED
RESTORED after: 8 passed                                       FAILED-lines=0
```

**Z6 at the parent commit — the manifest's central AT-160 claim, verified.** In a separate
`git archive 62c3e65^` tree, deleting the parent's own exemption clause
(anchor `        and not waiver_of(t)` + newline, matched exactly once, file changed)
produced **8 passed, 0 failures — GREEN**. The same mutation at HEAD produces 1 failure.
The guard was decorative before this commit and is load-bearing after it. That is the
strongest evidence available for an "uncovered guard now covered" claim, and it holds.

## Ruling: rejecting any segment containing `&` (the maker's open question)

**Keep it as written. No narrowing.**

The breadth is smaller than the manifest fears, and I measured it: `is_capable_of_failing`
replaces `&&` with `;` *before* segmentation, so `_is_task_specific` never sees a `&&` —
confirmed by `uv run python scripts/check_deliverable.py --exists ... && uv run autotester
doctor` still being accepted. The `&` rule therefore bites exactly three things: a
background job (`cmd &`), `&>` redirection, and `|&`. None of the three has any business in
a check whose only question is "is this task done", and all three change what the exit code
means. Narrowing to `&&`-aware handling would buy nothing that is not already bought, and
would re-open a shell-shaped surface — which is what AT-155 was, and what I ruled against
last time when I refused `test -f` and `grep -q`. Fail-closed with a written waiver as the
escape hatch stays the right trade. Recorded here so it is not re-litigated a fourth time.

## New findings

### AT-161 (medium) — the `|| true` family escaping through `;` and `&&`

`is_capable_of_failing` disqualifies `||` outright and `_is_task_specific` rejects `|`, but
the segment rule is `any(_is_task_specific(seg))` — so a task-specific segment followed by a
no-op segment is accepted, and in a shell the exit code is the *last* command's:

```
ACCEPTED!!  'uv run pytest tests/x.py; true'
ACCEPTED!!  'uv run pytest tests/x.py && true'
ACCEPTED!!  'uv run pytest tests/x.py; :'
ACCEPTED!!  'uv run pytest tests/x.py; exit 0'
ACCEPTED!!  'uv run pytest tests/x.py && exit 0'
```

Every one of those exits 0 unconditionally. It is the same neutering family as AT-158's
`| true` and AT-155's `|| true`, reached through the two separators the code deliberately
splits on. `ALWAYS_TRUE` is already defined and already consulted — but only for the segment
being scored, never for its siblings.

Fix direction (do **not** change `any()` to "the last segment must be task-specific" — that
would break the legitimate on-disk shape `check_deliverable.py --exists X && uv run
autotester doctor`): reject the whole command if **any** segment is in `ALWAYS_TRUE`. A
no-op segment has no legitimate place in a `done_check`; a task that needs one asks with a
waiver. Verified no task on disk carries this shape — `;` appears in no `done_check.cmd`,
and all six `&&` commands pair two real segments.

### AT-162 (low) — `offenders_in` edge behaviour on malformed rows

Adversarial rows driven against the extracted rule:

```
{"id":"T-1","done_check":{"cmd":"true"}}                          -> KeyError 'status'
{"id":"T-2","status":"pending","done_check":{"cmd":""}}           -> []   (not an offender)
{"id":"T-5","status":"pending","done_check":{"cmd":null}}         -> []   (not an offender)
{"id":"T-3","status":"pending","done_check":{"cmd":"true","waiver":"   "}} -> ['T-3']  correct
{"id":"T-4","status":"DONE","done_check":{"cmd":"true"}}          -> ['T-4'] correct (case-strict)
```

Rulings. **Missing `status` raising KeyError is acceptable**, and I am not asking for
`.get`. C9's whole subject is that an unreadable control value must fail loudly rather than
be replaced by a weaker default; a row with no status silently treated as `done` would be
that exact defect. Loud is right. **A whitespace-only waiver does not exempt** (`waiver_of`
strips) and is independently caught by `_waiver_offenders`' 20-character floor — no hole.
**Empty-string / null `cmd` slips past `offenders_in`** but is caught on disk by
`test_every_pending_task_actually_has_a_done_check`, which applies the same falsy test. The
residual is only that the extracted, publicly-named rule is silently permissive there while
its docstring calls itself "the exact rule" — a comprehension a future caller could reuse
without the sibling test beside it. Low: no live instance, safe direction on disk. Fix
direction when picked up: one line in the docstring naming the sibling test that owns the
empty-cmd case.

## Criteria

| Criterion | Judgement |
|---|---|
| C7 — verification is independent | **met.** All five sabotages reproduced in my own harness with anchor-once + file-changed assertions; the one zero-failure result (Z6 at the parent) is reported as the GREEN baseline it is, which is the claim under test, not as "the test is vacuous". The manifest pastes real output that I reproduced. |
| C9 — declared control value honoured or rejected | **met.** `done_check` stays pinned; the predicate now resolves the program position rather than any token; the waiver exemption is asserted as a composition and deleting it fails. |
| C1–C6, C8 | **met** — `doctor: clean`, `ruff` clean, no schema, layout, or provider surface touched. |

Issues claimed addressed: AT-158 fixed (all four families rejected), AT-159 fixed (both
shapes accepted), AT-160 fixed (Z6 fails at HEAD, was green at the parent). Ledger updated
`open → fixed`.

## The stop decision

**Agreed — go to T-132.** Both new findings are medium and low; nothing is `high`, so the
manifest's stated condition is met on its own terms and I am not inventing a reason to hold
it. **AT-161 and AT-162 should be QUEUED, not fixed now.** Stated explicitly because AT-161
is a real unfailable-command family and the reflex on this chain has been to fix such a thing
the same afternoon: neither has a live instance on disk, both sit behind a fail-closed
default plus a written waiver, and a fourth consecutive unit spent on this one predicate is
precisely the failure mode the commitment device exists to stop. Track A has not moved since
T-131. The governance chain is closed; these two ride the next sweep's queue.

```
VERDICT: PASS
SCOREBOARD: 9/9 criteria met, 0/0 invariants violated
FAILURES: none
ISSUES-WRITTEN: AT-161 (medium), AT-162 (low); AT-158/AT-159/AT-160 -> fixed
EXPLANATION: Re-ran the suite (658 passed, 2 skipped — the manifest's correction of its own
commit message is accurate, and recording it rather than rewriting a pushed public commit was
the right call), ruff and doctor clean. All five AT-158 families are rejected against the new
program-position predicate and both AT-159 shapes are accepted; a third hunting pass found one
new medium (AT-161: `pytest x.py; true` / `&& true` — the `|| true` family reaching through the
two separators the splitter itself creates) and one low. All five sabotages reproduced at 1
failure each with anchor-once + file-changed asserted, and Z6 was verified GREEN at 62c3e65^
and failing at HEAD, which is the manifest's central AT-160 claim. Ruled: the blanket `&`
rejection stays (it only reaches background jobs, `&>` and `|&`, since `&&` is normalised
before segmentation); missing `status` raising KeyError is correct under C9. Agreed with the
stop — both findings are queued, not fixed now.
```
