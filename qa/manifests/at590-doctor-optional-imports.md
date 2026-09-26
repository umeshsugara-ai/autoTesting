# Manifest — at590-doctor-optional-imports

**Unit:** doctor's `check_dependencies_declared` (AT-130) stops treating an import
guarded by `if TYPE_CHECKING:` / `if typing.TYPE_CHECKING:` or by
`try/except ImportError`/`ModuleNotFoundError` exactly like a hard, undeclared
dependency. `except Exception` and a bare `except:` are NOT treated as soft — neither
proves the failure was specifically a missing package.
**Contract:** `qa/contracts/core-invariants.md` C11 names AT-590 directly: "Known
false-positive class: `TYPE_CHECKING`-only and `try/except ImportError` optional
imports. That is a check defect to fix, not a licence to skip declaring a real
import." This unit is exactly that fix. C2 (300-line file cap, `uv run autotester
doctor`) governs the implementation's placement.
**Date:** 2026-09-26
**Fix cycle:** 1
**Dual check:** no
**Persona walk:** skip (dev tooling, no UI)
**Issues addressed:** AT-590

## Chosen behaviour (as the issue asked me to pick one)

The issue offered two options for the try/except shape: "either require an
optional-dependencies declaration or skip them." I chose **skip** — `pyproject.toml`
has no `[project.optional-dependencies]` table at all today (confirmed by grep;
AT-169 recorded the same absence for `faster_whisper` specifically), so "require a
declaration" would mean inventing a packaging group as part of a doctor-check fix,
which is out of scope for this unit and would immediately re-flag the exact
real-world case (`media/transcribe.py`) the issue is about. TYPE_CHECKING-only
imports are skipped unconditionally in both design options — they are never runtime
imports at all, so there is nothing to declare.

## What changed

- `src/autotester/doctor.py`
  - `check_dependencies_declared`'s docstring gains one sentence pointing at the new
    exemption and where it lives (AT-590).
  - Inside its file loop: `soft = soft_import_ids(tree)` (lazy-imported from
    `autotester.ledger.render`, matching the pattern this function's neighbours
    already use for `check_generated_fresh`/`check_architecture_budget`/
    `check_docs_routed`), then `if id(node) in soft: continue` before the
    module-declaration check runs. Nothing else in the function changed — the
    `_dep_name`, `dist_map`, `stdlib`, and the undeclared-dependency `Violation`
    message are byte-identical to before.
  - Net: **277 lines** (cap 300; was 269 before this unit, then briefly 341 with the
    helper written in place, before the move below).
- `src/autotester/ledger/render.py`
  - New public `soft_import_ids(tree: ast.AST) -> set[int]` plus a private
    `_SOFT_EXCEPT_NAMES = {"ImportError", "ModuleNotFoundError"}` constant, added
    under a new `# -- optional-import detection --` section with a comment
    explaining why it lives here (C2's cap, not thematic fit — see "Placement"
    below).
  - `soft_import_ids` walks the tree once (`ast.walk`); for every `ast.If` whose
    test is `TYPE_CHECKING`/`typing.TYPE_CHECKING`, or every `ast.Try` whose
    handlers *all* name only `ImportError`/`ModuleNotFoundError` (bare or as a
    tuple), it walks that node's own `body` list in isolation via a second
    `ast.walk` per statement and records `id()` of every `Import`/`ImportFrom`
    found. Because each guard's body is walked independently of its parent, an
    `if`'s `else`, a handler's own body, and any statement after the `try` are
    never visited by this pass and default to hard; anything nested inside the
    guarded body (an `if`, `for`, `with`, or nested `try` inside it) is still
    caught, because the inner `ast.walk` recurses through it.
  - Net: **260 lines** (cap 300; was 216 before).
- `tests/test_doctor.py` — 12 new tests (some parametrized), replacing 11
  originally-separate ones after a parametrize pass to stay under C2's cap (see
  "File-size iteration" below):
  - `test_soft_import_guard_shapes_are_not_flagged` × 7 params: bare
    `TYPE_CHECKING`, dotted `typing.TYPE_CHECKING`, an import nested inside a
    further `if` inside `TYPE_CHECKING`, `try/except ImportError`,
    `try/except ModuleNotFoundError`, `try/except (ImportError,
    ModuleNotFoundError)` (tuple form), and an import nested inside a further `if`
    inside `try/except ImportError`.
  - `test_shapes_that_look_like_a_guard_but_are_not_stay_hard` × 4 params: the
    `else` branch of `if TYPE_CHECKING:`, a plain import placed after the `try`
    block (not inside any guard), `try/except Exception`, and a bare `except:`.
  - `test_a_hard_import_alongside_a_soft_one_in_the_same_file_is_still_flagged` —
    one file with both a `TYPE_CHECKING`-guarded `import pytest` and a plain,
    unguarded `import pytest`; asserts exactly 1 violation, pinning that the new
    exemption did not make the check blind to a real hard import living in the
    same file (the "Required behaviour" bullet in the issue).
  - Net: **285 lines** (cap 300; was 213 before).

## Placement of `soft_import_ids` in `ledger/render.py`, not `doctor.py`

doctor.py was already at 269/300 lines before this unit. The full implementation
(module constant + helper + docstring update + two call-site lines) first landed
directly in `doctor.py` and measured **341 lines** — 41 over the cap. I trimmed the
implementation twice (removing a redundant module-level `_try_is_soft` wrapper in
favour of nested closures, and switching from a stateful recursive walker to two
independent `ast.walk` passes) and got `doctor.py` down to **312**, still 12 over. At
that point I moved the whole self-contained `soft_import_ids` (it depends on nothing
from `doctor.py` except the stdlib `ast` module) into `ledger/render.py`, which
already:
- imports `ast` for its own AST-based work (`_first_docstring_line`,
  `_class_summaries` — deriving structured info from parsed source), and
- is already the lazy-import target for three other doctor checks
  (`check_generated_fresh`, `check_architecture_budget`, `check_docs_routed`).

`ledger/checks.py` — the OTHER existing doctor-overflow module (split out under
AT-506 for the same 300-line reason) — was considered and rejected: it was already
at 288/300 lines (not enough headroom for a ~35-line addition), and its own module
docstring draws an explicit line I would have crossed: "the rules in `doctor.py`
read `src/` and `tests/`... the rules here read `docs/FEATURES.jsonl` and `qa/`."
`soft_import_ids` reads `src/` source ASTs, which is doctor.py's side of that split,
not checks.py's. `render.py`'s docstring ("Derive the living docs from code and the
ledger") is a closer fit — it is already in the business of parsing source ASTs to
derive structured facts, just for a different consumer (the generated map) than this
new one (the dependency checker). I added a 4-line section comment in `render.py`
documenting the real reason (line budget, not thematic fit) rather than silently
placing it there, since the placement.

## How to verify (commands + actual outputs)

```
$ uv run pytest tests/test_doctor.py
................................                                         [100%]
32 passed in 14.07s

$ uv run pytest tests/ -k doctor
........................................                                 [100%]
40 passed, 1919 deselected, 1 warning in 16.40s

$ uv run pytest tests/test_cli_advice_resolves.py
............................                                             [100%]
28 passed in 12.77s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

`uv run autotester map` was not run: no module was added (the new function landed
in an existing file), so `docs/MAP.md`'s per-module docstring table is unaffected
(confirmed by `doctor: clean`, which includes `check_generated_fresh`'s
freshness check over MAP.md).

The full unfiltered suite (`uv run pytest`, no target) was **not** run this cycle,
per the standing RAM-low instruction — only the doctor-scoped subset, the CLI-advice
file, ruff, and doctor.

## Capability coverage (each claim -> its isolating falsification)

Falsified in a throwaway plain-file copy OUTSIDE the tracked worktree
(`cp -r <worktree>/. <scratchpad>/at590-falsify/`, its own `uv run`-managed `.venv`
built and confirmed green before any mutation: `32 passed`). Each mutation is a
single hunk, applied via a Python script that asserts the anchor matched **exactly
once** before writing, then reverted with the same assert-and-replace approach
before the next one. The tracked worktree was diffed byte-for-byte against the
scratchpad copy after all four rounds and found identical (see "Diff scope" below).

| # | claim | falsifying edit (single hunk, in the throwaway copy) | before | after |
|---|---|---|---|---|
| A | `if TYPE_CHECKING:` / `if typing.TYPE_CHECKING:` detection is what makes those shapes soft | `render.py`: `is_type_checking` body -> `return False` | 32 passed | **4 failed**: `type_checking_bare`, `type_checking_dotted`, `nested_in_type_checking`, `test_a_hard_import_alongside_a_soft_one...` (the mixed-file pin, whose soft half is TYPE_CHECKING) |
| B | `try/except ImportError`/`ModuleNotFoundError` detection is what makes that shape soft | `render.py`: `try_is_soft` body -> `return False` | 32 passed | **4 failed**: `try_except_import_error`, `try_except_module_not_found_error`, `try_except_tuple_of_both`, `nested_in_try_except` |
| C | `except Exception`/bare `except:` are excluded from "soft" ON PURPOSE, not by accident | `render.py`: `try_is_soft` body -> `return bool(node.handlers)` (any handler type counts) | 32 passed | **2 failed**: `except_exception_too_broad`, `bare_except_too_broad` — the two rows this exact clause exists to pin |
| D | doctor.py's own `if id(node) in soft: continue` is what applies the exemption (not a no-op) | `doctor.py`: `if id(node) in soft:` -> `if False:  # ...` | 32 passed | **8 failed**: all 7 soft-shape params + the mixed-file pin |

Each mutation reproduced exactly, was reverted, and re-verified green
(`32 passed` each time) before the next one ran. Full transcripts (abridged to the
failing-test summary line) are in the tool-call history of this cycle; the pattern
for each was:

```
$ uv run pytest tests/test_doctor.py -v
...
FAILED tests/test_doctor.py::test_soft_import_guard_shapes_are_not_flagged[type_checking_bare]
...
N failed, (32-N) passed in ~6s
```

Final revert confirmed byte-identical to the tracked worktree:
```
$ diff <(cat src/autotester/doctor.py) <(cat <worktree>/src/autotester/doctor.py) && echo "doctor.py identical"
doctor.py identical
$ diff <(cat src/autotester/ledger/render.py) <(cat <worktree>/src/autotester/ledger/render.py) && echo "render.py identical"
render.py identical
$ git -C <worktree> status --short
 M src/autotester/doctor.py
 M src/autotester/ledger/render.py
 M tests/test_doctor.py
```
(exactly the 3 files this unit intends to change — the falsification copy never
touched the tracked worktree.)

**Not separately falsified:** the "hard imports elsewhere in the file must still be
checked" claim is the SAME test as mutation D's row (the mixed-file pin) — it is one
assertion (`len(violations) == 1`) that is falsified by either half going wrong
(soft half stops being soft, or hard half stops being hard), and mutation D already
demonstrates the hard half is load-bearing (removing the skip makes BOTH imports
flag, taking the count to 2, which the assertion catches either way). No dedicated
fifth mutation was run for this because it would not isolate anything mutation D
does not already show.

## Live browser evidence

Not applicable — dev-tooling fix, no UI surface. Changed paths: `src/autotester/
doctor.py`, `src/autotester/ledger/render.py`, `tests/test_doctor.py`.

## File-size iteration (disclosed, since it shaped the diff)

The straight-line implementation (helper written directly in `doctor.py`, one test
per shape, no parametrize) blew two separate 300-line caps before landing: `doctor.py`
at 341/300, then 312/300 after two rounds of compacting the AST-walking logic, and
`tests/test_doctor.py` at 364/300 with one test function per shape. Final state:
`doctor.py` 277, `render.py` 260, `tests/test_doctor.py` 285 — all under cap, `uv run
autotester doctor` confirms clean. Recorded so a future reader of the diff
understands why the helper lives in `render.py` and why the tests are parametrized
rather than one-function-per-case (the file's existing style, e.g.
`test_undeclared_third_party_import_is_flagged` and its siblings, is one function
per case — I deviated from that local convention specifically to fit the cap, not
out of a general preference).

## Known limits / gaps (disclosed, not claimed)

- The chosen "skip" behaviour (vs. "require an optional-dependencies declaration")
  means a soft import that is genuinely never available anywhere and never
  documented in any way still passes doctor silently — the check trades a false
  positive (AT-590's bug) for a smaller true-negative surface (a soft import with
  zero declaration of any kind). This is the same trade the issue's own wording
  offered as acceptable ("either require... or skip them"); flagged for the checker
  to confirm the choice, per C11's amendment-log convention of recording new
  criteria at merge time.
- `media/transcribe.py:47` (`try: import faster_whisper except Exception:`) is
  UNCHANGED by this unit and stays hard under the new rule, because its handler
  catches `Exception`, not `ImportError`/`ModuleNotFoundError` — this is the
  required behaviour, not a miss, but it means the real file the issue cites is not
  itself made doctor-clean by this fix in the scenario where faster_whisper becomes
  installed-but-undeclared (it currently is not installed in this venv at all, so
  `check_dependencies_declared` skips it today regardless, via the pre-existing
  "not resolvable in this env" branch — confirmed unaffected: `git diff` touches no
  file under `src/autotester/media/`). Narrowing that file's `except Exception` to
  `except ImportError` is a separate, real-code change outside a doctor-only unit's
  scope and is not proposed here.
- Full unfiltered `uv run pytest` (no target) not run this cycle — RAM-low standing
  instruction; only the doctor-scoped subset, `test_cli_advice_resolves.py`, ruff,
  and doctor.
- `qa/contracts/core-invariants.md` C11 already names AT-590 by number as the
  expected fix; maker does not edit contracts, so no amendment is proposed here —
  flagged for the checker to close the loop C11's own text describes.

## Status: ready-for-check
