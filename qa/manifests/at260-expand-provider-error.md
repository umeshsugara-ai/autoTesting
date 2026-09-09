# Manifest — at260-expand-provider-error

**Unit:** AT-260 — `autotester expand` lets a `ProviderError` escape uncaught
**Commit:** `945cf56`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/expand.md` (X1, X4 — no-fire on refusal)
**Goal task:** none — issue-driven
**Issues addressed:** AT-260 (medium)

## What was wrong

> `autotester expand <project> --provider gemini` lets a `ProviderError` escape uncaught: full
> Rich traceback, exit non-zero, zero cases persisted. Run by the checker against a real approved
> FlowSpec with live credentials: `ProviderError: gemini: the answer hit max_output_tokens and was
> truncated (role=agent)` printed as a raw traceback panel out of `cli.py::expand_cases`,
> `cases.jsonl` absent. `cli.py:221-225` catches only `review_stage.FlowSpecNotReviewed`.

The same class as AT-264 (fixed earlier this session in the UI's `generate_cases` route), on the
CLI side of the same feature.

## What changed

- `src/autotester/cli.py` — `expand_cases` now catches `ProviderError` alongside the existing
  `FlowSpecNotReviewed`, printing the same one-line `secho` style the no-credentials and
  no-flowspec refusals already use.
- **The manifest's own remedy asked a second question — "partial results persisted or explicitly
  discarded, stated either way"** — answered explicitly rather than left implicit:
  `stages/expand.py::expand` builds every flow's `Case`s in memory and only returns once *all*
  flows succeed, so a failure partway through discards whatever had already been generated, by
  construction, not by an extra step this fix adds. The new test asserts
  `store.list_cases() == []` after the failure rather than assuming it.
- `tests/test_expand_cli.py` — one new test: a `MockProvider` subclass whose `.act()` raises
  `ProviderError`, confirming exit 1, no traceback, the clean message, and no cases on disk.

## How to verify (commands + expected)

- `uv run pytest tests/test_expand_cli.py -v` → expected: exit 0, 9 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_expand_cli.py -v
[... 9 tests, all PASSED]

$ uv run pytest
929 passed, 2 skipped, 1 warning in 98.58s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), one mutation, restored immediately after:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted unit layered
onto the extract by hand, since it postdates HEAD — `cli.__file__` verified inside the extract,
not the live tree). Removed the new `except ProviderError` block entirely. Result: **exactly 1
failure**, `test_a_provider_failure_mid_expand_is_a_clean_refusal_not_a_traceback`:

```
AssertionError: assert 'no cases persisted' in ''
where '' = <Result ProviderError('the answer hit max_output_tokens and was truncated (role=agent)')>.output
```

Note the exact shape differs slightly from the finding's own description — Typer's `CliRunner`
swallows the unhandled exception rather than rendering the literal string `"Traceback"` into
`result.output` (that string only appears with a real terminal, not the test harness) — but the
test's actual assertion (the clean message must be present) still catches the regression
precisely: an empty `result.output` is exactly "no clean signal why", the finding's own complaint.

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree confirmed
untouched (`grep -c "no cases persisted"` → 1, unchanged).

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/cli.py`,
`tests/test_expand_cli.py`. CLI-only.

## What this unit does not claim

- Does not change `stages/expand.py::expand`'s all-or-nothing behaviour — only documents and
  tests it explicitly. A design that persists cases per-flow as they succeed would be a genuinely
  different, larger change, and isn't what AT-260 asked for.
- Does not touch the UI's `generate_cases` route — that's AT-264, already fixed separately this
  session, on the same underlying class of bug.

## Status: ready-for-check
