# Manifest — at513-the-block-tests-leave-the-row-tests

**Unit:** AT-513 — `tests/test_ledger_checks.py` reached 295 of C2's 300 lines after four consecutive
units added to it (AT-508, AT-509, AT-511). Split it along the seam its tests already had, before a
fifth unit hits the cap mid-fix-cycle.
**Contract:** `qa/contracts/core-invariants.md` (C2 — file ≤ 300 lines; C7 — new/moved tests owe a
mutation run)
**Goal task:** none (issue-driven; filed by the at511 cycle-1 checker off my own disclosure)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-513 (medium, open -> fixed). Not closed here: AT-514 (low, the fence stop
holds by ordering not design) and AT-512 (low, the single-line parenthetical limit) — both are
behaviour changes, and this unit changes no behaviour.

## This unit is a move, so its only real claim is "nothing changed"

Every other unit in this chain changed what the checks conclude. **This one must change nothing**,
and that is the claim the evidence has to carry. Three independent measurements, none of them a
re-reading:

**1. The collected test-name set is identical.** Captured before the split, re-derived after, and
diffed as sets rather than eyeballed:

```
$ diff -u names_before.txt names_after.txt
TEST NAME SET IDENTICAL          # 34 tests before, 34 after, same names, same parametrisations
```

That is the measurement that matters: a test silently dropped in a move is invisible to a green
suite, because a test that no longer exists cannot fail. The AT-311 lesson one level up.

**2. The move was made by AST span, not by line numbers.** `scratchpad/at513_split.py` parses the
module, takes each target function's `lineno`..`end_lineno` **including its decorator_list** (three
of the ten are `@pytest.mark.parametrize`, whose decorator sits above `lineno` and would have been
left behind by a naive span), asserts every named function was found, and removes exactly those
lines. A hand-moved block is where a parametrisation gets orphaned.

**3. The moved tests still kill the mutants they were written for** — see the mutation table below.
A moved test that is no longer wired to anything still passes.

## The seam

`tests/test_ledger_checks.py` asks **what the check CONCLUDES about a row** — lost, stale, or fine
(AT-496), what counts as an id (AT-500), what counts as a fix claim (AT-508).

`tests/test_marker_blocks.py` asks **what the check READS before it concludes anything** — whether a
line carries a claim at all (AT-504), and where the block carrying it stops (AT-509, AT-511).

That seam is not invented for the split; it is the seam the four crowding units already fell along.
All four wrote into the *reading* half, which is why one half grew and the other did not.

## What changed

- `tests/test_marker_blocks.py` — **new file**, 154 lines. The 10 block-reading tests, moved
  verbatim (docstrings and all), plus a header stating the seam.
- `tests/test_ledger_checks.py` — 295 → **163 lines**. Keeps `_qa` and `ROW`, which the new file
  **imports rather than copies**: `from test_ledger_checks import ROW, _qa`. One concept, one place.
  The bare (non-`tests.`-prefixed) import matches the existing precedent at
  `tests/test_flake_probe_real_process.py:15` (`from test_flake_probe_runner import _FakePopen`);
  there is no `tests/__init__.py`, and rootdir insertion is what makes both work.
- No `src/` file changed. No behaviour changed.

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_marker_blocks.py` → `34 passed`
- **Re-derive the identity yourself**, don't take the number: check out the pre-split file
  (`git show HEAD:tests/test_ledger_checks.py`), collect its test names, collect the two post-split
  files' names, and diff the sets. They must be equal. This is the claim; everything else is support.
- `uv run autotester doctor` → `doctor: clean` (both files now under C2's 300)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at513-the-block-tests-leave-the-row-tests/mutations.json`
  → `4/4 mutations killed`, exit 0
- Whole suite `uv run pytest` exits 0 — redirect to a **file** and scan it whole (AT-503; `-q`
  resolves to `-qq` here and prints no summary line, so a `tail` proves nothing).

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ wc -l tests/test_ledger_checks.py tests/test_marker_blocks.py
  163 tests/test_ledger_checks.py
  154 tests/test_marker_blocks.py
$ uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_marker_blocks.py
34 passed in 0.61s
$ diff names_before names_after
TEST NAME SET IDENTICAL
$ uv run python scripts/mutation_check.py qa/evidence/at513-.../mutations.json
4/4 mutations killed        # exit 0
```

## Capability coverage (each claim -> its isolating falsification)

| capability | check | falsifying edit | observed |
|---|---|---|---|
| AT-504's marker recognition survived the move | 3 tests, now in `test_marker_blocks.py` | `_is_marker_line` back to `marker in line` | `KILLED` |
| AT-511's field-label stop survived the move | `..._carrying_a_parenthetical_still_ends_the_block` | `_NEW_FIELD` back to the AT-509 form | `KILLED` |
| AT-508's claim grammar stayed behind and still fires | 3 tests, still in `test_ledger_checks.py` | drop the `_NOT_FIXED` negation | `KILLED` |
| **the shared helper is really shared** | `test_a_fix_claim_on_a_continuation_line_is_read` (new file) | change `ROW` **in the old file** | `KILLED` |

The fourth row is the split's own risk and the only one worth arguing about. If the new file had
quietly carried its own copy of `ROW`/`_qa`, mutating the original would not touch it. It does touch
it — a test in `test_marker_blocks.py` fails when a constant in `test_ledger_checks.py` changes,
which is only possible across a live import.

## Live browser evidence

Not UI-touching — no surface changed, no `src/` file changed. Changed paths:
`tests/test_ledger_checks.py`, `tests/test_marker_blocks.py` (new),
`qa/evidence/at513-the-block-tests-leave-the-row-tests/*`.

## Known limits (disclosed, not claimed)

- **I have to correct my own prose in three earlier manifests, and the checker should not have to
  find it.** `at508:97`, `at509:95` and `at511:96` each say the mutation run showed "every row's
  actual failure set **==** its claim exactly". The harness does not enforce equality. The predicate
  at `scripts/mutation_check.py:110` is `exit_code == 1 and expected <= failures` — a **subset**:
  the named tests must fail, collateral failures are permitted. Those three sentences were true as
  *observations of those particular runs* (the sets did coincide) but they describe the instrument
  as stricter than it is, and a reader would take them as a guarantee. **This unit's row 4 is a live
  counter-example**: it claims one test and 16 actually fail, and the harness passes it. I have not
  edited the closed manifests — they are checked artifacts — so this is the record.
- **This split makes 3 of 33 evidence specs unrunnable**, measured, not estimated: `at506`,
  `at509` and `at511`'s `mutations.json` each name nodeids as `tests/test_ledger_checks.py::…` for
  tests that now live in `tests/test_marker_blocks.py`. They fail closed (`a 'kills' label is a
  claim, not a comment`, `mutation_check.py:319-323`) rather than silently mis-reporting, and I left
  them alone on the AT-504 precedent — a unit's evidence is the record of what *that* unit ran.
  **But this is the second time a split has done it** (AT-506 did it to `at504`), so it is a pattern,
  not an accident, and there is no rule saying which way to resolve it. That belongs in the ledger.
- **The two files total 317 lines where one held 295.** The split costs 22 lines — a header
  docstring stating the seam, and the second import block. Neither file is near the cap now (163,
  154), but the honest statement is that C2 got *further* from being breached at the cost of more
  total text, not less.
- **The bare import is a rootdir-insertion behaviour, not a package import.** It works because
  pytest inserts the rootdir of a test file with no `__init__.py` onto `sys.path`. It is the
  established precedent in this suite, but it would break if `tests/` ever became a package, and
  nothing in the repo asserts that it will not.
- **A move cannot be proven identical by a green suite alone**, which is why the name-set diff is
  the headline and not the `34 passed`. I claim the tests are the same tests; I do not claim the
  *file* is byte-identical in the moved region — the extraction rstrips trailing blank lines.

## Status: ready-for-check
