# at172-at173-dead-command-shape

**Unit:** AT-172 (high) + AT-173 (medium)
**Commit:** 3b765a4
**Fix cycle:** 1
**Contract:** `qa/contracts/video-learning.md` VL1d, generalised · `core-invariants.md` C7

## Why this unit is about a shape and not two bugs

T-132 passed on cycle 3, and its checker immediately found **AT-172**: the other shipped command's
refusal names `autotester ingest analyze`, **which does not exist**.

That is AT-163's dead end **one command over, in the same file, after three fix cycles spent on
exactly that shape.** It escaped only because the contract criterion was scoped to the one message
that had already been caught.

Four occurrences is enough. Fixing instances was not working.

## The structural fix

`tests/test_cli_advice_resolves.py` finds **every** backtick-quoted `autotester …` string in `src/`
and asks the CLI to resolve it. Six exist today; all resolve; sabotaging either historical bug back
in makes it fail.

**Writing it was the instructive part**, and each round moved the line to where it belongs:

| Round | What it caught | What that meant |
|---|---|---|
| 1 | `ingest run` "unresolvable" | **my own slicing bug** — I dropped the first token, so the test failed on its own defect and reported it as the code's |
| 2 | my **comments** documenting the dead commands | a comment explains a bug; it does not advise running one |
| 3 | the **variable docstring** for `PREP_COMMAND` | which exists specifically to say `media prep` is dead |

The rule it settled on is precise rather than convenient: **a string that is an entire statement can
never be printed, so it is documentation by construction.** Comments and docstrings explain; only
runtime strings advise. That is an AST property, not a heuristic, and it is why round 3 was the last
round.

The AT-172 message now says the analyze stage **is not built yet**, rather than naming a command
that will exist in Track A4. When there is nothing to run, say so instead of inventing something to
run.

## AT-173 — success reported for work that could not be attempted

`ingest frames` printed a **green** `0 frame(s) written`, exit 0, for a recording that had vanished
— indistinguishable from a recording that genuinely had no stills to take.

Fixed at **both** levels: `extract_frames` refuses a missing file, the CLI maps that to a clean exit
2, and a zero-frame result prints yellow rather than green. Tested at both levels too, because the
lesson of AT-166 is that fixing the stage without the shipped path is fixing half of it — and that
lesson cost T-132 a whole cycle.

## Evidence

```
SABOTAGE AT-172 (a message names a command that does not exist)     -> 1
SABOTAGE AT-163 (the original dead group, reintroduced elsewhere)   -> 1
SABOTAGE AO     (a vanished recording is not refused)               -> 1
SABOTAGE AP     (the CLI swallows it back into a green line)        -> 1
RESTORED
```

Each printed `anchor matched once, file changed` before its result was believed.

## A practice changed, not an intention restated

Two commits this session lost backtick-quoted command names to shell command substitution inside a
heredoc. I said I would stop and did not. Commit messages now go through a file — verified on this
unit's own commit, where `autotester ingest analyze` survived intact.

## Verification (host; Docker down, `uv` native; bare `pytest`)

```
uv run pytest                          700 passed, 2 skipped   (691 before + 9 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## Put to the checker

**AT-174 is not closed and I do not think this unit closes it.** Your sabotage AN4 pointed the
refusal at `ingest frames` — a **registered, same-arity sibling** — and the `Usage:`-banner oracle
came back INCONCLUSIVE. The new test has the same blind spot: it proves a named command *resolves*,
not that it is the *right* one.

I could not find an oracle that distinguishes a correct command from a plausible sibling without
encoding the answer in the test, which would just move the assertion somewhere it cannot be wrong.
If you can, it is a better unit than this one — the same offer as AT-155, which you took and which
produced the fail-closed predicate.

## What this does NOT claim

- **AT-175** (the no-ffmpeg degrade prints `0s` and persists zeros as if measured) is untouched and
  queued.
- **AT-169** (`pyproject.toml` has no `[project.optional-dependencies]` block at all), **AT-170**,
  **AT-130** unchanged.
- No model call; no crawl against a real product.

## Status: checked-PASS
