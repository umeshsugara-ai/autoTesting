# at158-at160-program-position

**Unit:** AT-158 (medium) + AT-159 (low) + AT-160 (medium)
**Commit:** 62c3e65
**Fix cycle:** 1
**Contract:** `qa/contracts/core-invariants.md` C9 · C7

## AT-158 — one line of sloppiness, and the same shape a third time

I asked `"pytest" in parts` — **any token anywhere** — instead of asking what actually runs. So
`echo pytest tests/x.py` and `true # pytest tests/x.py` both read as pytest invocations, and the
suite's own must-reject case `true # tests/test_x.py` was defeated by *adding the word "pytest" to
it*.

That is the same mistake as AT-154 (the directory `tests/` satisfying a check meant for files) and
as AT-148 → AT-149 → AT-151: **I matched the instance in front of me rather than the thing itself.**

Also admitted: `--co`, pytest's documented alias for `--collect-only`, excluded one line away; and
`| true` / `|& true`, because my splitter handled `||` and not `|`.

Fixed at the root. `_program()` returns the first token that is not a runner wrapper, so a name only
counts in the program position; and any shell-neutering character (`| # \` $( > < &`) rejects the
segment outright. A `done_check` needs none of them, and a waiver is how to ask for one.

## AT-159 — rejected by bugs, not by policy

`python3 scripts/x.py` and a script outside `scripts/` were both refused — and both are exactly the
shape that branch was written for: an interpreter running a repo script. **Waiving them would have
waived a typo**, which is the failure mode a waiver system has to avoid.

## AT-160 — C7's own class, inside the test written to close it

My waiver test asserted the two helpers **separately** and never their composition. Deleting
`and not waiver_of(t)` from the offenders rule left the suite **green** — an unguarded exemption
clause.

The rule is now extracted as `offenders_in()` and asserted on rows chosen so a broken composition
cannot pass: one waived and one not, otherwise identical. `offenders_in([waived, unwaived])` must be
exactly `["T-u"]` — a deleted exemption returns both, a mis-scoped one returns neither.

## Evidence

```
SABOTAGE Z6  (delete the exemption clause)          -> 1   <- was GREEN before this commit
SABOTAGE Z7  (program matched by any token again)   -> 1
SABOTAGE Z8  (shell-neutering characters allowed)   -> 1
SABOTAGE Z9  (--co stops counting as --collect-only)-> 1
SABOTAGE Z10 (python3 / non-scripts path rejected)  -> 1
RESTORED: 8 passed
```

Each printed `anchor matched once, file changed` before its result was believed. **Z6 is the one
that matters** — it was green at the parent commit, so that guard was decorative until now.

## A wrong number in my own commit message

The commit says **661 passed**. The real count is **658** — I added cases to existing tests and
extracted a helper; I added no new test *functions*. I wrote the number before running the suite
and did not re-read it against the output pasted directly above it.

I am not rewriting a pushed commit to hide it (this repo is public and the history is shared).
It is corrected here, and this manifest is the record. It is a small instance of exactly the thing
this whole afternoon has been about: **stating a number I expected instead of the one I measured.**

## Verification (host; Docker down, `uv` native; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          658 passed, 2 skipped   (unchanged: no new test functions)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## Put to the checker

The allowlist now rejects any segment containing `&`, which also rejects a legitimate background
form and — more plausibly — `VAR=1 cmd &&` style chains are still fine but a single `&` anywhere is
not. I believe that is correct for a `done_check` (nothing about "is this done" needs a background
job), but it is broader than AT-158 strictly required, and you ruled on the fail-closed trade last
time, so it is yours to confirm or narrow.

## THIS CLOSES THE GOVERNANCE CHAIN

Three units now — `at141-at115` → `at154-at157` → this — each finding smaller holes in the same
predicate. The guard now fails closed, the waiver is a written decision, and every shape either
verdict measured is pinned.

**Next unit is T-132 (Track A3, host media prep) regardless of what this verdict returns, unless it
returns something `high`.** Stating it on disk as a commitment, exactly as with the consent chain,
because the failure mode is identical: polishing a guard while the product work waits. Track A has
not moved since T-131, and the plan gives it tick priority.

Corpus facts already measured for it (`.work/track-a-corpus-facts.md`): the recordings are on `C:`,
not `D:` as the plan says; `faster_whisper` is **not** in the project venv, so the sidecar path is
the one that works here; `ffmpeg 8.1.1` is present.

## What this does NOT claim

- **AT-156** (C9's third field `approved`) stays queued — the checker ruled that scoping correct.
- **AT-153** stays queued; the consent chain is closed.
- No crawl has run against a real product. That is the ERP credential gate.

## Status: checked-PASS
