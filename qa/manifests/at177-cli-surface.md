# at177-cli-surface

**Unit:** AT-177 (high) — the sweep's top queue row
**Commit:** 81efef9
**Fix cycle:** 1
**Contract:** `qa/contracts/ui.md` · `core-invariants.md` C7

## What the sweep measured

AT-140 was built to close *"no test drives the shipped CLI"*. The sweep then measured what it
actually left behind: **15 of 22 shipped commands still had no test driving them** — including
`flowspec approve`, the human review gate I6 exists to protect, and all three `report` commands,
which are the exact reader surfaces AT-120 through AT-123 were filed against.

## What shipped

**A smoke matrix over all 22 commands**, walked out of click's own tree so a command added tomorrow
is covered without anyone remembering to add it here. A hand-written list would drift silently,
which is the failure this file is about.

**Focused tests on the surfaces that carry a decision** — the review gate (approve, request-edit,
status) and the three reports.

## Two claims of mine that C7 caught

**1. "The matrix is the layer that would have caught AT-166."** It is not. Sabotaging AT-166 back
in came back **INCONCLUSIVE**: with nonexistent arguments every command short-circuits in *argument
validation*, long before the stage where that bug lived.

So the matrix guards the **shallow** path across the whole surface, and the deep paths are guarded
one at a time. I verified which test actually catches AT-166 — the targeted one in
`test_media_prep.py` — by running the same sabotage against it (1 failure). The docstring now says
exactly that instead of the comfortable sentence.

**2. The repo-level test asserted only "no traceback."** Adding a required argument to `doctor` —
which would break the project's own verify step — came back **INCONCLUSIVE** too, because a missing
argument is a *usage* error and prints no traceback at all. It now uses the banner oracle measured
for AT-171, and the sabotage bites.

Both were written before being checked. That is the session's own habit, caught twice inside one
unit by the clause written for it.

## One failure that was mine, where the code was right

`flowspec request-edit` requires `--by` as well as `--note`. My test omitted it. The design is
correct — **taking an approval back is also a decision someone made** — and I recorded that in the
test rather than treating the requirement as an obstacle.

## Evidence

```
SABOTAGE AR (the review gate stops recording WHO approved)        -> 1
SABOTAGE AS (request-edit no longer takes the approval back)      -> 1
SABOTAGE AT (a repo-level command starts needing a project)       -> 1   (INCONCLUSIVE before the oracle fix)
SABOTAGE AQ (a shipped command stops catching its refusal)        -> INCONCLUSIVE, and reported as such
```

Each printed `anchor matched once, file changed` first. **AQ is left in the record deliberately** —
it is the evidence for correction 1, not a gap being glossed.

## Verification (host; Docker down, `uv` native; bare `pytest`)

```
uv run pytest                          734 passed, 2 skipped   (700 before + 34 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## What this does NOT close, and it is the important part

**AT-176 is now `high` and is the next unit.** While this was being built, the `at172-at173` checker
ran the sabotage I had not: pointing `PREP_COMMAND` back at the dead `autotester media prep` — the
canonical AT-163 site — and **my structural guard yields 0 failures.** Only the pre-existing
*instance* test catches it.

Measured cause: at `media_prep.py:157` the command name lives in the `PREP_COMMAND` constant and its
backticks in a separate f-string, so they are **different AST nodes** and the collector cannot see
the pair. My claim that it "finds every backtick-quoted `autotester` string in `src/`" is
**overstated**, and the checker amended the contract to state that the instance test is not made
redundant and may not be retired.

That is the session's class **inside the guard built to stop the session's class**, exactly as the
sweep predicted one tick earlier. It does not belong in this unit's scope, and it is not being
deferred quietly: it is the next thing I build.

**AT-178** (un-backticked advice at `core/consent.py:35`) and **AT-174** — for which the checker
*designed* the oracle I said I could not find, a causal one that triggers the refusal, runs the
quoted command as rendered, and asserts it stops firing — are queued with it.

## Status: ready-for-check
