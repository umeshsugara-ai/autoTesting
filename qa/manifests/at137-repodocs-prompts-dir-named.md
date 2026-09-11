# Manifest — at137-repodocs-prompts-dir-named

**Unit:** AT-137 — `RepoDocs.prompts_dir` selects on a hidden boolean, not a named parameter
**Contract:** `qa/contracts/ingest.md` (provider/prompt seam), core-invariants C2
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-137 (medium)

## What was wrong

`RepoDocs(root)` and `RepoDocs()` differed in `prompts_dir` because of a private `_root_given`
flag the constructor set from whether `root` was passed — a substituted prompt tree was a side
effect of the docs root, not something a caller could name. A prior checker ruling (recorded in
AT-137's own evidence) confirmed this was the RIGHT behavior in effect (the AT-132 fallback, and
`tests/test_ledger.py::make_docs`'s stub-prompt-tree injection, are both legitimate) — the only
thing wrong was the *shape*: one parameter carrying two meanings, selected by a flag a reader
cannot see at the call site.

## What changed

- `src/autotester/core/paths.py::RepoDocs.__init__` — new keyword-only `prompts_dir: Path | None`
  parameter, stored as `self._prompts_dir_override`.
- `RepoDocs.prompts_dir` (the property) — checks the override FIRST, before the existing
  `_root_given`/fallback logic, which is otherwise **byte-identical** to before: `RepoDocs(tmp_path)`
  alone still resolves `prompts_dir` exactly as it did (C2 — no behaviour change for any caller
  that doesn't adopt the explicit form).
- `tests/test_ledger.py::make_docs` — the one real call site the checker's own evidence named as
  relying on the implicit side effect — updated to pass `prompts_dir=` explicitly, demonstrating
  the named form at the point AT-137 was actually raised about.
- `tests/test_ledger.py` — two new direct tests: an explicit `prompts_dir` wins over `root`'s
  inferred one; `root` alone still behaves exactly as documented (the AT-132 fallback).

## What this unit does not claim

- Does not change any OTHER `RepoDocs(...)` call site — grepped every one (`cli.py`, `cli_video.py`,
  `doctor.py`, `ledger/relitigation.py`, `stages/*.py`, `ui/routes_*.py`, and every test file):
  all either call `RepoDocs()` with no root (unaffected) or `RepoDocs(root)` in `doctor.py`, which
  the original checker evidence already confirmed never touches `prompts_dir` (verified again by
  grep here). `test_ledger.py::make_docs` was the only real caller of the implicit form.
- Does not remove the `root`-alone fallback behavior — the prior checker ruling explicitly wanted
  it kept; this unit only adds a named way to opt out of inferring from it.

## How to verify (commands + expected)

- `uv run pytest tests/test_ledger.py -q` → expected: exit 0, 22 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ledger.py -q
......................                                                   [100%]  (22 passed)

$ uv run pytest -q
[all dots, exit 0]
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. Extracted clean `HEAD`, layered my diff on.
2. `uv sync`; confirmed `autotester.__file__` resolves inside the extract.
3. Baseline: `uv run pytest tests/test_ledger.py -q` → 22 passed, exit 0.
4. Mutated `prompts_dir` to remove the override check entirely (falling straight through to the
   pre-existing `_root_given` logic) — **exactly the predicted single test failed**
   (`test_an_explicit_prompts_dir_wins_over_root`, asserting the wrong resolved path), all 21
   others stayed green, including the `make_docs`-based tests (their explicit `prompts_dir=`
   value happens to equal the inferred fallback, so they can't distinguish the two paths — exactly
   why the dedicated unit test above exists).
5. Extract deleted; live tree confirmed to carry only the two real edits.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/core/paths.py`,
`tests/test_ledger.py`. Pure path-resolution logic + tests, no route/template touched.

## Status: checked-PASS (cycle 1, verdict qa/verdicts/at137-repodocs-prompts-dir-named.md, commit d639adb)
