# Manifest — at626-dotted-import

**Contract:** qa/contracts/core-invariants.md (C2 line cap, C3, C11 soft-import class)
**Goal task:** none (ledger-driven unit; AT-626 was filed by the at621 cycle-1 check)
**Date:** 2026-09-27
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk:** skip (backend AST classifier inside `autotester doctor`; no UI surface, no screen, no navigation — the diff touches only `src/autotester/ledger/render.py` and `tests/test_doctor.py`)
**Issues addressed:** AT-626
**Executor:** claude-opus-5 (the maker orchestrator, inline)
**Executor rationale:** the diff was already derived and saved as a patch by an earlier build subagent that correctly refused to commit it onto a cycle that had just been PASSed. Re-dispatching a subagent to re-derive a known two-file, ~6-line change would have spent a build slot for nothing; the orchestrator applied the patch to a fresh worktree off master and verified it. No Ollama lane: this is a design-rule guard inside the repo's own enforcement tooling.

## Why this is its own unit, not at621 cycle 2

AT-626 was filed against `wave/at621-exit-call-aliases` while that unit was unchecked, so the
original intent was to fold it into cycle 1. By the time the build ran, the checker had already
written `qa/verdicts/at621-exit-call-aliases.md` — **PASS, Cycle checked: 1**, bound to code commit
`5c7a9e47` — and had *independently re-probed the AT-626 shape*, confirmed `import os.path` +
`os._exit` is still classified SOFT, and explicitly scoped it out of that unit's PASS. Amending a
judged cycle would put a second, different tree behind a cycle number that already has a binding
verdict. at621 was therefore merged as it stood (`c679ad89`, close-out `08bf6a66`) and this is a
separate unit off master.

## What changed
- `src/autotester/ledger/render.py`:156-158 — `soft_import_ids`'s `modules` comprehension now binds
  `a.name.split(".")[0]` when `a.asname is None`, so a dotted `import os.path` (which really does
  bind the name `os`) is recognised as an `os` binding. The membership test accepts either an exact
  `sys`/`os` import or an unaliased dotted import whose first component is one of them.
- `src/autotester/ledger/render.py`:112 — new module-level constant `_SYS_OS = {"sys", "os"}`
  replacing two inline `{"sys", "os"}` literals, plus two comment lines tightened. This buys back
  the line budget: the file is at the C2 cap and stays **exactly 300/300**. No behaviour rides on
  the comment edits.
- `tests/test_doctor.py`:258-259 — new `os_path` row in `_LOOKS_LIKE_A_GUARD_BUT_IS_HARD`:
  `import os.path` + `try: import pytest / except ImportError: os._exit(1)` must stay HARD.
  Two comment blocks tightened for the same reason; this file also stays exactly **300/300**.

**Deliberately out of scope:** `import os.path as osp` stays unresolved. That is AT-626's own
`expected` field — `osp` names the submodule `os.path`, which has no `_exit`/`exit` attribute, so
binding it to `os` would be wrong, not merely incomplete. Flagged for the checker to judge whether
that exclusion is still right or is the next AT-626.

## How to verify (commands + expected)
- `uv run pytest tests/test_doctor.py` → expected: exit 0, 40 passed (39 before this unit; the new
  row is the 40th)
- `uv run ruff check src tests scripts` → expected: exit 0, `All checks passed!`
- `uv run autotester doctor` → expected: exit 0, `doctor: clean` (proves both files are still
  within the 300-line C2 cap)
- `wc -l src/autotester/ledger/render.py tests/test_doctor.py` → expected: 300 and 300

## Actual outputs (from maker's own run, in the bound worktree)

```
$ uv run autotester doctor
doctor: clean

$ uv run ruff check src tests scripts
All checks passed!

$ uv run pytest tests/test_doctor.py
........................................                                 [100%]
40 passed in 6.26s

$ wc -l < src/autotester/ledger/render.py
300
$ wc -l < tests/test_doctor.py
300
```

Full-suite `uv run pytest` was NOT run by the maker for this unit — see the gap note below.

## Capability coverage (each new claim → its isolating falsification)

| capability (one line) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| An unaliased dotted `import os.path` binds `os`, so an `os._exit(1)` ImportError handler in such a file is classified HARD, not SOFT | `tests/test_doctor.py::test_shapes_that_look_like_a_guard_but_are_not_stay_hard[os_path]` (row at `tests/test_doctor.py`:258) | revert only the `modules` comprehension hunk in `src/autotester/ledger/render.py`:156-158 back to `{a.asname or a.name … if a.name in _SYS_OS}` — single file, single hunk, inside this manifest's "What changed" | GREEN before: `1 passed, 39 deselected in 0.76s` · RED after: `FAILED tests/test_doctor.py::test_shapes_that_look_like_a_guard_but_are_not_stay_hard[os_path]` / `1 failed, 39 deselected in 0.73s`, failing on the guard-stays-hard assertion (`assert not any(...)` at line 277), not on an import or collection error |

**Where the perturbation ran, and one honest oddity.** The copy lives at
`…/scratchpad/at626-falsify`, built with `tar --exclude=.git` from the worktree, i.e. the tree
**as this manifest describes it** (post-change), outside the bound root. The copy was proven to
resolve its own source before anything was edited:
`uv run python -c "import autotester.ledger.render as r; print(r.__file__)"` →
`…\scratchpad\at626-falsify\src\autotester\ledger\render.py`. The oddity: pytest's traceback
header in the copy prints the *worktree's* path for `test_doctor.py` (a rootdir/cache artifact),
which looks like the bound tree ran. It did not — the edit existed only in the copy, and the bound
worktree stayed green (`1 passed`) and `git status` clean of any revert throughout. Checker should
re-derive this independently rather than take the claim.

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths are `src/autotester/ledger/render.py` and
`tests/test_doctor.py` only: an AST classifier consumed by `doctor.check_dependencies_declared`
and its test. No `*.tsx|jsx|vue|svelte|html|css`, no `ui/`, no route, page or component, and
nothing a rendered page's data flows through.

## Gaps stated, not hidden

- **Full suite not run by the maker for this unit.** Two sibling builds were holding the machine
  (free RAM measured 2.0 GB of 23.7 at dispatch time) and a full `uv run pytest` on this repo takes
  ~1300 s. The targeted file is the one this change can affect, and `doctor`+`ruff` both ran green
  on the whole tree. The checker re-runs the suite itself; if it surfaces
  `tests/test_flake_probe_real_process.py`, that is **AT-627**, already filed as an environmental
  flake of the AT-196/AT-505/AT-518 class and explicitly not chargeable to this unit.
- **AT-627 is not addressed here** and is not claimed to be.

## Status: ready-for-check
