# Manifest — at283-agents-md-root-clutter

**Unit:** AT-283 — `autotester doctor` rejects the active `AGENTS.md` as root clutter
**Contract:** `qa/contracts/core-invariants.md` (C4 — declared top-level layout)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-283 (medium), AT-336 (dismissed as duplicate of AT-283, no separate fix needed)

## What was wrong

`uv run autotester doctor` reported `root-clutter: AGENTS.md` — a permanent red governance
baseline. `AGENTS.md` is a real project-instruction file (the Codex-CLI equivalent of `CLAUDE.md`,
supplied for `D:/autoTesting` and explicitly not to be edited or removed by the checker), not
scratch or evidence — the thing `check_root_clean` actually exists to catch.

## What changed

- `src/autotester/doctor.py:19-26` — `ALLOWED_ROOT_ENTRIES` now includes `"AGENTS.md"`, alongside
  the pre-existing `"CLAUDE.md"`. One-line addition plus a docstring explaining why it sits beside
  `CLAUDE.md` rather than being treated as scratch.
- `tests/test_doctor.py` — new test
  `test_a_second_ai_tools_instruction_file_is_not_root_clutter`: writes an `AGENTS.md` into a
  synthetic repo and asserts `check_root_clean`/`doctor.run` does NOT flag it, symmetric to the
  existing `test_root_clutter_is_flagged` (which still asserts a stray log file DOES trip it).

## How to verify (commands + expected)

- `uv run pytest tests/test_doctor.py -q` → expected: exit 0, 7 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean` (was: 1 violation, root-clutter AGENTS.md)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_doctor.py -q
.......                                                                  [100%]  (7 passed)

$ uv run pytest -q
[all dots, no F, exit 0 — this repo's pytest summary line does not print in this shell
 environment (a pre-existing quirk, not new), exit code is the ground truth]
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. Extracted clean `HEAD`, layered my uncommitted diff on top via `git apply` (my fix postdates
   `HEAD`).
2. `uv sync` inside the extract; confirmed `uv run python -c "import autotester; print(autotester.__file__)"`
   resolves **inside the extract**, not the live tree.
3. Baseline: `uv run pytest tests/test_doctor.py -q` → 7 passed, exit 0.
4. Mutated `ALLOWED_ROOT_ENTRIES` back to remove `"AGENTS.md"` (the exact revert of this fix).
5. Re-ran: **exactly the predicted single test failed**
   (`test_a_second_ai_tools_instruction_file_is_not_root_clutter`, `AssertionError: assert not True`),
   the other 6 stayed green.
6. Extract deleted; live tree confirmed to carry only my two real edits
   (`git status --porcelain -- src/autotester/doctor.py tests/test_doctor.py`).

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/doctor.py`,
`tests/test_doctor.py`. Pure design-rule check + test, no UI/route/template touched.

## What this unit does not claim

- Does not claim every future foreign-tool config file dropped at the repo root should be
  auto-allowed — only `AGENTS.md`, because it's a named, deliberate, disclosed instruction
  surface (the same status `CLAUDE.md` already has), not a general carve-out for untracked files.
- Does not touch `.codex/` — it already passes `check_root_clean` because it starts with `.`
  (the existing dotfile exemption), unaffected by this change.
- AT-336 (a re-filing of this same finding by a later checker run) is dismissed as a duplicate,
  not independently fixed — this unit's fix closes both.

## Status: checked-PASS (cycle 1, verdict qa/verdicts/at283-agents-md-root-clutter.md, commit e6bd4df)
