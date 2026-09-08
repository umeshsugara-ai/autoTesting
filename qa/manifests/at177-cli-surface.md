# at177-cli-surface

**Unit:** AT-177 (high) — the sweep's top queue row
**Commit:** 81efef9 (cycle 1) -> cycle 2, see `git log`
**Fix cycle:** 2
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

## Cycle 2 — FAIL on C7, and the failure was serious

**`uv run pytest` was rewriting the repository it verifies.**
`test_the_repo_level_commands_run_without_a_project` took no `root` fixture, so it ran `map` and
`snapshot` against the **live repo** — and both write. The checker proved it by appending a marker
to `docs/SNAPSHOT.md` and watching one test erase it.

The project's own verify command mutating the git-tracked files it checks is not "a check someone
else can re-run", which is C7's entire sentence. Fixed with a temp root, `snapshot --print`, and
`map` dropped — it has no read-only mode, and a test that needs one is not worth a rewritten repo.

**AT-184 then arrived from AT-181's own fix.** A placeholder is not always an *input*: `report excel`
takes an output **path**, so a bare `"nonexistent"` made the matrix create a file called
`nonexistent` in the repo root. Doctor caught that one.

### AT-180 — my headline overstated the coverage, measured

The checker measured that only **4 of 22** matrix invocations reached application code. The other 18
stopped at click's `Usage:` banner, so the assertion was about **click**, not about autotester.

Arity is now derived from click itself: **20 of 22**, measured and stated rather than claimed. The
remaining two stop at a **closed vocabulary** rejecting the placeholder — correct behaviour, and
deliberately not forced past, because valid arguments would make both commands **write**, which is
AT-181 again.

Two wrong turns on the way, kept because they are the interesting part:

- **seeding a real project changed nothing** — the problem was never state, it was arity;
- my first required-parameter loop used `isinstance(param, click.Argument)`, which **silently failed
  for typer's parameters** and passed every positional as `"<name> value"` — doubling the arity and
  putting each command right back at the banner the helper exists to get past.

### AT-179 — a real shipped defect the matrix cannot see

`ingest list <nonexistent-project>` printed *"no sources yet"* and exited **0** — indistinguishable
from a real project with none, while every sibling refuses on exit 1. A script branching on its exit
code was told everything was fine.

### All three fixes first came back INCONCLUSIVE

I fixed three things and pinned none of them, **in the unit whose whole subject is testing what
ships.** Two needed a different kind of test than I first reached for:

> The fingerprint test **cannot** catch AT-181 — it sets a temp root, and the original bug was the
> *absence* of one. Reproducing it there is impossible by construction.

So `snapshot --print` is pinned by running it against the live repo **deliberately** — safe
precisely because `--print` writes nothing — and `map`'s exclusion is pinned by asserting it has no
read-only flag, because **an exclusion nobody justifies is one somebody quietly reverses.**

### Cycle 2 evidence

```
AU (ingest list stops refusing an unknown project)      -> 1   (INCONCLUSIVE first)
AV (snapshot runs without --print on the live repo)     -> 1   (INCONCLUSIVE first)
AW (placeholders escape the temp root)                  -> 1   (INCONCLUSIVE first)
AR / AS / AT (cycle 1's three)                          -> 1 each
```

### And I pushed a commit with doctor RED

The `file-too-long` violation was in the **same output** I read to confirm 739 passed and ruff
clean. I took the green I was looking for and stopped reading. That is this session's habit in its
smallest form — verifying the part I had in mind rather than the whole result the command returned.
Fixed in the next commit (`test_cli_harness_safety.py` split out); the pushed commit stands, because
the record is worth more than a tidy history.

### Cycle 2 verification

```
uv run pytest                          739 passed, 2 skipped
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean      <- read in full this time
repo fingerprint across all 22 commands unchanged
```

## Status: checked-PASS
