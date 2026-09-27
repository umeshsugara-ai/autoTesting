# Manifest — at621-exit-call-aliases (AT-621)

**Unit:** AT-621 — `soft_import_ids`'s `_is_exit_call` (`ledger/render.py`) recognised only a bare
`exit`/`quit` name or the literal attribute `sys.exit`. An `ImportError` handler doing
`os._exit(1)`, an aliased module (`import sys as s; s.exit(1)`), or a name imported directly
(`from sys import exit as bye; bye(1)`) was still classified as a graceful degrade (SOFT), so an
undeclared hard dependency guarded that way escaped C11's undeclared-dependency check. Filed by
checker Mode A of at590-doctor-optional-imports cycle 2 (adversary lens).

**Contract:** `qa/contracts/core-invariants.md` C11 (every third-party import is a declared
dependency; the `TYPE_CHECKING`/`try-except-ImportError` carve-out is a known false-positive
class, not a licence to miss a real hard import) and C2 (300-line file cap / 50-line function cap).
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk: skip** (doctor internals, no UI)
**Issues addressed:** AT-621 (low, open → fixed here). Not flipped by me — `qa/issues.jsonl` is
the checker's write surface, untouched.
**Goal task:** T-195
**Executor:** claude-opus-subagent

## What changed

- **`src/autotester/ledger/render.py`** (300/300 lines, unchanged — same hard cap as AT-590/AT-613
  left it):
  - `_is_exit_call` now also matches `os._exit`, and resolves aliases: `func.attr in {"exit",
    "_exit"}` on any Name whose id is in a `modules` set (local names bound to the `sys`/`os`
    module via `import sys as s` / `import os`), plus bare-Name calls whose id is in a `names` set
    (local names bound directly to `sys.exit`/`os._exit` via `from sys import exit as bye`).
  - `modules`/`names` are resolved once per file by `soft_import_ids` (two set comprehensions over
    `ast.walk(tree)`, one for `ast.Import`, one for `ast.ImportFrom`) and threaded through
    `_handler_exits` into a newly nested `is_exit_call` closure — nesting it inside `_handler_exits`
    (rather than keeping the old standalone `_is_exit_call` top-level, which is how the first draft
    of this fix worked) was the piece that bought back the line budget: `soft_import_ids` stayed a
    single function that would otherwise have needed to hold `_is_exit_call` + `_handler_exits` +
    the alias resolution as nested closures and blew past 50 lines (measured: 71). Keeping
    `_handler_exits` top-level (as before) with the exit-check nested one level inside it keeps
    every function under the 50-line cap (`_handler_exits` is now ~28 lines) while removing one
    whole top-level function + its blank-line separator pair, which is what made the file fit
    exactly 300/300 again.
  - `_EXIT_CALL_NAMES` and the new `_EXIT_ATTRS` (`{"exit", "_exit"}`) are declared on one line
    (`_EXIT_CALL_NAMES, _EXIT_ATTRS = {...}, {...}`) and the multi-line "why this lives here"
    comment above them (a `#` comment, not a docstring) was tightened from 4 lines to 2 — both are
    pure line-budget moves, disclosed here per the anti-drift edit-in-place discipline. **No
    existing docstring's wording or wrapping was touched** — `soft_import_ids`'s 9-line docstring
    and `_handler_exits`'s 3-line docstring are byte-identical to before this unit (the process
    note from a prior unit's docstring re-wrap was the reason to hold this line, and the fix fit
    without needing to touch either).
  - Considered moving the exit-detection helpers to another module (the brief's fallback if there
    was no room). There wasn't a genuinely better-fitting existing module — `doctor.py` already
    imports `soft_import_ids` lazily from here specifically because it didn't have the budget
    either (AT-590's own comment) — so this stayed the "no new file" path via nesting instead.
- **`tests/test_doctor.py`** (294 → 300 lines, exactly at the cap): added to
  `_LOOKS_LIKE_A_GUARD_BUT_IS_HARD` three positive rows (`os_exit`, `sysalias`,
  `aliased_name_import_exit`) and to `_SOFT_IMPORT_SHAPES` one negative row
  (`unrelated_dot_exit_on_non_sys_object_stays_soft` — a handler calling `.exit()` on an object
  aliased from an unrelated module, e.g. `import json as app; app.exit()`, stays SOFT: only a name
  actually bound to `sys`/`os` counts, never an arbitrary object with an `exit` method). Two of the
  three positive rows (`os_exit`, `sysalias`) use Python's single-line `try: stmt` /
  `except X: stmt` form instead of the usual multi-line block purely to fit each `pytest.param` on
  one physical line under the 300-line cap; this is valid Python (a `try`/`except` header may be
  followed by a single simple statement on the same line) and the test bodies are never executed,
  only parsed by `doctor.run`, so runnability was never a concern. Extended the existing
  `test_shapes_that_look_like_a_guard_but_are_not_stay_hard` docstring to name AT-621 explicitly
  (tightened the existing AT-590/AT-619 wording to make room under the 300-line cap rather than
  leaving the file over budget — full before/after wording is in the diff, nothing about the
  original behavior claim was dropped, only re-worded more tersely).

No other file touched. `docs/SNAPSHOT.md`/`docs/MAP.md` were not stale — `uv run autotester
doctor` reports `doctor: clean` with no `check_generated_fresh` diff, so nothing to regenerate.

## Verify — actual outputs

```
$ uv run pytest tests/test_doctor.py -v
============================= test session starts =============================
collected 39 items
tests\test_doctor.py .......................................             [100%]
============================= 39 passed in 3.54s ==============================

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

Targeted tests only, per instruction — full suite (`uv run pytest` with no `-k`/no path filter)
not run for this unit.

## Live browser evidence

Not UI-touching — a doctor/AST-classifier fix. Changed paths: `src/autotester/ledger/render.py`,
`tests/test_doctor.py`, this manifest.

## Capability coverage (falsifying edit → named test goes red)

Falsified in a throwaway full copy of the worktree, **outside** it, at
`C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/dd410a44-7522-428c-9b91-fda96de822cd/scratchpad/at621-falsify/`
(a full `cp -r`, not a hand-built stub — the render/doctor import graph is small but real). Never
used `git stash`; the real worktree's files were never mutated for this exercise.

| claim | falsifying edit | check | before (fixed copy) | after (sabotaged copy) |
|---|---|---|---|---|
| AT-621: `os._exit(1)` in an `ImportError` handler is a hard exit, not a graceful degrade | reverted `src/autotester/ledger/render.py` in the copy to the pre-fix version (`git show master:...` over it) | `uv run pytest tests/test_doctor.py -k "os_exit or sysalias or aliased_name_import_exit or unrelated_dot_exit"` | 4 passed | **3 failed** (`os_exit`, `sysalias`, `aliased_name_import_exit` all `AssertionError: assert False` on `any("opt.py" in v.location for v in violations)`) — `unrelated_dot_exit_on_non_sys_object_stays_soft` still passed (1 passed), as expected: that shape was never supposed to change |

Confirmed GREEN in the real worktree first (with the fix intact, the run above), then reverted the
fix in the throwaway copy only and confirmed RED on exactly the three new named assertions, then
deleted the copy.

## Gaps

- Not re-run against the full test suite (`uv run pytest` with no filter) — targeted tests only,
  per instruction.
- `raise SystemExit` (as opposed to a call to `sys.exit`/`exit`/`quit`/`os._exit`) was checked
  against the existing behavior and is already covered by the pre-existing `ast.Raise` branch in
  `_handler_exits` (a `raise` of any kind, including `raise SystemExit(...)`, already makes the
  handler stay hard) — no change was needed there, and no new test row was added for it since
  AT-619's existing `reraise`/`raise_from` rows already exercise that branch generally; naming this
  explicitly per the brief's "check and keep existing behavior" instruction.
- AT-621's evidence also names `import sys as s` (module-level rename) as the aliasing shape; a
  deeper alias chain (e.g. re-exporting the alias through a second module) is out of scope — the
  resolver only looks at the file being checked, matching how `soft_import_ids` already only ever
  reasons about one file's own AST.

## Status: ready-for-check

Status: checked-PASS (qa/verdicts/at621-exit-call-aliases.md, Cycle checked: 1, verdict commit 14f13a22, merged c679ad89)
