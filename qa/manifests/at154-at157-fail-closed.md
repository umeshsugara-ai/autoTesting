# at154-at157-fail-closed

**Unit:** AT-154 (medium) + AT-155 (medium) + AT-157 (low)
**Commit:** 90e4219
**Fix cycle:** 1
**Contract:** `qa/contracts/core-invariants.md` C9 · C7

## Why this unit exists

On the last unit I told the checker my predicate **fails open**, that this is the wrong direction
for a guard, and that if it could design a fail-closed version *"that is a better unit than this
one."* It could. This is that unit.

## AT-154 — a hole inside my own stated logic

`pytest tests/` is the whole suite. The directory `tests/` satisfied the same `startswith("tests")`
my docstring said made a check **specific**. The comment and the code, one line apart, said
different things — and I wrote both.

## AT-155 — a denylist on shell commands cannot fail closed

Every shape I had not thought of was accepted. The checker measured **seven** false negatives:
`echo done`, `python -c "pass"`, `test -f README.md`, `--collect-only` (collects, never runs), and
anything with `|| true` appended — my splitter handled `&&` and `;` but not `||`, and a trailing
`|| true` neuters whatever precedes it.

**The predicate is now an allowlist.** A command is task-specific only if it is a shape known to
depend on a deliverable; anything unrecognised is rejected; `||` disqualifies outright.

The escape hatch is `done_check.waiver: "<why>"` — the checker's design, and the good part is what
it converts: *a silent hole becomes a sentence someone had to write and anyone can grep*. A waiver
under 20 characters is itself a failure. **Every pending task survives the stricter rule; no waivers
were needed today.**

## AT-157

`--contains` raised an unhandled traceback on a directory or binary. Never unsafe — still non-zero —
but a `done_check` that dies with a stack trace tells its reader nothing about what is missing,
which is its whole job.

## The C7 clause earned its place this tick

Sabotages **Z4** and **Z5** first came back:

```
SABOTAGE Z4 (a waiver no longer has to say anything)
  anchor matched once, file changed
  INCONCLUSIVE -- 0 failures; mutation not shown to change behaviour (C7)

SABOTAGE Z5 (--contains stops handling an unreadable path)
  anchor matched once, file changed
  INCONCLUSIVE -- 0 failures; mutation not shown to change behaviour (C7)
```

Under the clause as it stood two units ago, I would have read zero failures as *"these guards are
solid."* **It meant the opposite.** No task on disk carries a waiver, so that rule had no data to
bite on; and nothing exercised `--contains` on an unreadable path. Both were untested, and both
looked tested.

They are now asserted against rows and paths that would break them, and both bite on re-run:

```
SABOTAGE Z4 (re-run)  failures: 1  test_the_waiver_rule_actually_rejects_a_hollow_waiver
SABOTAGE Z5 (re-run)  failures: 1  test_check_deliverable_reports_an_unreadable_path_instead_of_crashing
```

**A clause the checker wrote one unit ago stopped me claiming coverage I did not have, in this
unit, today.** That is the strongest evidence for it I can offer.

## Full evidence

```
Z1 (a bare `tests/` path counts as specific again)                -> 1
Z2 (`||` stops disqualifying a command)                           -> 1
Z3 (the allowlist inverts back to a denylist)                     -> 1
Z4 (a waiver no longer has to say anything)                       -> 1   (was INCONCLUSIVE)
Z5 (--contains stops handling an unreadable path)                 -> 1   (was INCONCLUSIVE)
RESTORED: 8 passed
```

Each printed `anchor matched once, file changed` before its result was believed.

## Verification (host; Docker down, `uv` native; bare `pytest` — `-q` twice is `-qq`)

```
uv run pytest                          658 passed, 2 skipped   (654 before + 4 net new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

## Put to the checker

**The allowlist is now the thing that can be wrong in the other direction.** It rejects legitimate
checks it does not recognise, and the cost of that is a waiver nobody wanted to write — which is a
pressure toward waiving rather than fixing. I think that is the right trade (a waiver is visible;
a false negative is not), but it is a trade, and you designed the shape, so you should rule on
whether the allowlist is too narrow rather than me deciding my own homework.

## What this does NOT claim

- **AT-156** — C9's third field, `approved`, is still unpinned. The checker ruled deferring it
  correct scoping and it stays queued.
- **AT-153** (percent-encoded dot-segments, low) stays queued: the consent chain was closed on disk
  and a low advisory finding does not reopen it.
- No crawl has run against a real product; that is still the ERP credential gate.

## Status: ready-for-check
