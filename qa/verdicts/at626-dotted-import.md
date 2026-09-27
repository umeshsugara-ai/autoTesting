# Verdict — at626-dotted-import

**Date:** 2026-09-27
**Cycle checked:** 1 (matches manifest's `Fix cycle: 1 of max 3`)
**Unit:** AT-626. Code commit `e37c07f0` (single commit, worktree `.worktrees/at626-dotted-import`,
branch `wave/at626-dotted-import`). Base: `git merge-base master wave/at626-dotted-import` =
`08bf6a66` (parent of e37c07f0 — this is a one-commit branch).
**Contract:** `qa/contracts/core-invariants.md` — scoped to C2 (line cap), C3, C11 (soft-import class).
**Checker:** fresh Claude subagent (claude-sonnet-5), Mode A. `self != executor`
(manifest's `Executor: claude-opus-5, the maker orchestrator, inline`) — independence holds.

## What I re-ran myself (real output, not pasted)

```
$ uv run pytest tests/test_doctor.py
40 passed in 6.48s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ wc -l src/autotester/ledger/render.py tests/test_doctor.py
  300 src/autotester/ledger/render.py
  300 tests/test_doctor.py
```

All four verify commands reproduce the manifest's claimed outputs exactly.

## [C11] The classifier's widening — independently probed beyond the unit's own test

Wrote a standalone probe (`.work/at626-probe/probe.py` in the bound worktree, deleted after use;
not part of the commit) driving `doctor.run` against synthetic repos, covering every shape the
dispatch named plus extra adversarial ones the unit's own test suite does not cover:

| shape | result | expected |
|---|---|---|
| `import os` + `os._exit(1)` | HARD | HARD |
| `import os.path` + `os._exit(1)` (the new behaviour) | HARD | HARD |
| `import sys as s` + `s.exit()` | HARD | HARD |
| `from sys import exit as bye` + `bye(1)` | HARD | HARD |
| genuine `try/except ImportError: pytest = None` (graceful degrade) | SOFT | SOFT |
| `import os.path` with NO exit call in the handler | SOFT | SOFT |
| `import os.path` + unrelated `os.path.exists(...)` in handler | SOFT | SOFT |
| `import os.path` + unrelated `os.environ.get(...)` in handler | SOFT | SOFT |
| `import os.path as osp` + `osp.exists(...)` (the deliberately-excluded shape) | SOFT | SOFT |
| `import xml.etree.ElementTree` + unrelated call (dotted, non-sys/os) | SOFT | SOFT |

No newly-false HARD found. The widening is correctly scoped to the `_SYS_OS` set and does not
leak into other dotted-import shapes.

**On the deliberate exclusion (`import os.path as osp`):** re-derived independently —
`python -c "import os.path; print(hasattr(os.path,'_exit'), hasattr(os.path,'exit'))"` → `False
False`. `os.path` genuinely has neither attribute, so binding an aliased dotted import's alias to
`os` would be wrong, not merely incomplete, exactly as the manifest and AT-626's own `expected`
field argue. This is not the next AT-626 — it's a correct scope boundary. No new issue filed for it.

## [C2] Line cap and comment tightening

Both changed files verified at exactly 300/300 (`wc -l` above, `doctor: clean`). Read the diff
(`git show e37c07f0`) comment-by-comment: the AT-590/AT-619/AT-621 docstring in
`tests/test_doctor.py` was tightened but gained the `os_path` case name, so it reads as an
improvement. The `render.py` comment lost one clause — "the same lazy-import pattern this module
already serves" — which cross-referenced other lazy-import code elsewhere in the module; it does
not explain this fix and its removal costs nothing a later reader needs to understand `soft_import_ids`
itself. Noted, not a finding: this doesn't rise to "a fix that survives only by deleting the
explanation of itself."

## Capability coverage — reproduced independently in a throwaway copy

**Copy:** built with `tar --exclude=.git --exclude=.venv --exclude=.pytest_cache
--exclude=.ruff_cache --exclude=.work` from the bound worktree (post-change state, the same state
verified above) to `<scratchpad>/at626-falsify`, **outside** the bound root. `.venv` was junctioned
in from the worktree (`New-Item -ItemType Junction`) to avoid a ~20 min `uv sync` — the copy's
*source* is a real, independent copy; only the interpreter/site-packages are shared, which does
not affect this row (no dependency changed).

**Copy resolves its own source (proven before any edit):**
```
$ uv run --active python -c "import autotester.ledger.render as r; print(r.__file__)"
...\scratchpad\at626-falsify\src\autotester\ledger\render.py
```

**Row 1 — the manifest's only claimed capability** (An unaliased dotted `import os.path` binds
`os`, so an `os._exit(1)` ImportError handler in such a file is classified HARD, not SOFT):

- GREEN before, in the copy:
  ```
  $ uv run --active pytest "tests/test_doctor.py::test_shapes_that_look_like_a_guard_but_are_not_stay_hard[os_path]"
  1 passed in 3.97s
  ```
- Falsifying edit applied **only in the copy** — single-hunk, single-file, exactly the hunk named
  in the manifest's capability row (`src/autotester/ledger/render.py`'s `modules` comprehension,
  the module named in "What changed"): reverted to
  `{a.asname or a.name for n in ... if a.name in _SYS_OS}` (drops the dotted-import branch).
- RED after, in the copy:
  ```
  FAILED tests/test_doctor.py::test_shapes_that_look_like_a_guard_but_are_not_stay_hard[os_path]
  assert False
   +  where False = any(<genexpr> ...)
  D:\autoTesting\.worktrees\at626-dotted-import\tests\test_doctor.py:277: AssertionError
  ```
  Fired on `assert any("opt.py" in v.location for v in violations)` at line 277 — the exact
  guard-stays-hard assertion the row is named for, not a collection/import error. **Row reproduced.**
- **Bound worktree stayed untouched throughout:** `git status --short src/autotester/ledger/render.py
  tests/test_doctor.py` → empty, both before and after the copy's edit; a fresh
  `uv run pytest tests/test_doctor.py` in the bound worktree after the falsification still shows
  `40 passed`.

**The stated oddity, independently resolved, not merely taken on the maker's word.** My own copy
reproduced it too: the failure traceback above prints the *worktree's* absolute path for
`test_doctor.py:277` even though the edit and the failure exist only in the copy. I found the
mechanism: `tar` carried over `tests/__pycache__/test_doctor.cpython-311-pytest-9.1.1.pyc` from
the original worktree (I had excluded `.pytest_cache`/`.ruff_cache` but not `__pycache__`) — a
stale compiled bytecode cache whose baked-in `co_filename` is the original absolute path, which is
what a traceback prints regardless of where the `.py` actually lives now. That the row's actual
outcome came from the copy, not the worktree, is proven independently of the traceback text: (a)
`r.__file__` resolved to the copy before any edit, (b) the bound worktree's two files show `git
status` clean across the whole sequence, and (c) the bound worktree's own `test_doctor.py::...[os_path]`
still passes after the copy was mutated. The maker's "rootdir/cache artifact, not a bound-tree
leak" claim is confirmed, not merely trusted.

**CAPABILITY-COVERAGE: 1/1 rows reproduced.**

## [C10] Diff scope

`git show --stat e37c07f0` (== the diff for this one-commit unit against its merge-base) touches
exactly `qa/manifests/at626-dotted-import.md`, `src/autotester/ledger/render.py`,
`tests/test_doctor.py` — matches the manifest's "What changed" exactly. No function, class, test,
route or config key was deleted or renamed; every hunk is a comment/logic tightening or an addition
(new `_SYS_OS` constant, new `os_path` parametrize case). No out-of-scope file touched.

## Ledger

AT-626 (`qa/issues.jsonl`, was `status: open`, `severity: low`) is fixed by this commit — the exact
`expected` field it specified (`a.name.split('.')[0]` bound when `a.asname is None`, plus the
`os_path` row in `_LOOKS_LIKE_A_GUARD_BUT_IS_HARD`) is what shipped, verified above. Flipped to
`status: fixed`, `fixed_date: 2026-09-27`, `regression_check:
tests/test_doctor.py::test_shapes_that_look_like_a_guard_but_are_not_stay_hard[os_path]` (appears
verbatim as a pytest node id under the adapter's `uv run pytest` slot-1 command), `fixed_by: at626-dotted-import
cycle 1 (e37c07f0, verdict qa/verdicts/at626-dotted-import.md, merge pending -- maker step)` —
same convention as AT-619/620/621/622 in this ledger. Left at `fixed`, not `verified`: this
project's own convention (AT-619/621/622, all reproduced by their checkers in the same sitting)
reserves `verified` for a later, separate re-check, so this checker follows precedent rather than
the SKILL.md's general default.

## Persona walk / Mode D

`Persona walk: skip` — justified: changed paths are `src/autotester/ledger/render.py` and
`tests/test_doctor.py` only, an AST classifier and its test, no `*.tsx/jsx/vue/svelte/html/css`,
no `ui/`, route, page, or component. **Mode D not applicable** — confirmed against the actual diff,
not just the manifest's assertion.

## Full suite (the maker's disclosed gap) — re-run by the checker

```
$ uv run pytest                                    (full suite, bound worktree, no -q)
1 failed, 2013 passed, 6 skipped, 32 xfailed, 15 warnings in 1615.32s (0:26:55)
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
```

Exactly one failure, and it is the disclosed, pre-existing **AT-627** environmental flake (the
AT-196/AT-505/AT-518 class — a real-subprocess timing test, unrelated to `render.py`/`test_doctor.py`).
No other failure surfaced. The pass count (2013) is consistent with at621's own full-suite run
(2012 passed) plus exactly the one new `os_path` test this unit adds — no other test count drift.

**No second failure found** (item 5 of the dispatch, answered directly: only one).

## Delegation

`qa/delegation-ledger.jsonl` had no dispatch-half row for this unit (Claude lane, not an external
executor — this is a low-severity process gap, not filed as an issue). Appended the outcome row
myself: `{"unit": "at626-dotted-import", ..., "executor": "claude-opus", "verdict": "PASS",
"reason_class": "claude-lane"}`.

## Final scoreboard

- C2 (line cap): MET — both files exactly 300/300, `doctor: clean`.
- C3 (one concept, one place): MET — `_SYS_OS` constant *reduces* duplication (replaces two inline
  literals); `doctor: clean` on duplicate-concept/drift-filename.
- C11 (soft-import class): MET — the new `os_path` HARD classification is correct, verified
  end-to-end via `doctor.run` against the unit's own test plus 5 additional adversarial shapes with
  no newly-false HARD; the `import os.path as osp` exclusion is independently confirmed correct
  (`os.path` genuinely lacks `_exit`/`exit`).
- C10 (diff scope): MET — commit touches only the manifest, `render.py`, `test_doctor.py`; nothing
  deleted or renamed.
- Capability coverage: 1/1 rows reproduced in an independent throwaway copy outside the bound root;
  the manifest's stated pytest-traceback oddity is independently resolved (stale `__pycache__`
  `.pyc` carried by the copy, not a bound-tree leak).
- Full suite: 1 failed (AT-627, disclosed, pre-existing, unrelated), 2013 passed — no new failures.
- Mode D: not applicable, confirmed against the diff (no UI-touching path).
- Ledger: AT-626 flipped open → fixed with `fixed_by` + `regression_check`.

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (C2, C3, C10, C11 in scope), 0/0 invariants (none named beyond the criteria)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 1/1 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: src/autotester/ledger/render.py, tests/test_doctor.py — no UI surface)
ISSUES-WRITTEN: none (AT-626 closed as fixed, not a new issue)
EXECUTOR: claude-opus-5 (the maker orchestrator, inline) (checker: claude-sonnet-subagent)
EXPLANATION: The dotted-import widening is correct and narrowly scoped — independently probed
against 10 synthetic shapes (5 beyond the unit's own tests) with no newly-false HARD, and the
deliberate `os.path as osp` exclusion is verified correct, not a gap. Both files hold exactly at
the C2 cap; one comment lost a cross-reference clause that isn't load-bearing for this fix. The
capability-coverage row was reproduced end-to-end in a copy outside the bound root, including
independently resolving the manifest's own disclosed pytest-traceback oddity. The full suite,
which the maker disclosed skipping, was re-run here: exactly one failure, the already-filed AT-627
flake, no regression.
```
