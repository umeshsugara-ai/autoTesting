# Verdict — at513-the-block-tests-leave-the-row-tests

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh subagent, bound to `d:/autoTesting`
**Commit under check:** 9ed3833 (parent b40f6f3, pre-split). Tip of master at dispatch was
d265357, a tick-stamp-only commit touching `qa/.last-tick`, not part of this unit.

## What I re-ran myself (not trusted from the manifest)

1. **Test-name identity, re-derived independently — not read from the manifest's own
   `names-before.txt`/`names-after.txt`.** Extracted `tests/test_ledger_checks.py` at `b40f6f3`
   (pre-split) into a scratch copy outside the bound tree, ran
   `pytest --collect-only -q -o addopts=` there (34 collected) and against the current
   `tests/test_ledger_checks.py` + `tests/test_marker_blocks.py` (34 collected), diffed the two
   node-id sets with the file prefix stripped: **identical, 0 added, 0 removed.**
2. **Verbatim-move check, function body by function body — not the manifest's AST-span diff.**
   Used my own `ast` parse to extract each of the 10 moved functions (decorator through
   `end_lineno`) from the pre-split source and from `tests/test_marker_blocks.py`: **all 10
   byte-identical** (docstrings, parametrize lists, assertions, assertion messages — nothing
   loosened in the move).
3. **The shared-helper seam.** Confirmed `from test_ledger_checks import ROW, _qa` is a live
   cross-file import by mutating `ROW` in the OLD file inside a throwaway copy and watching the
   NEW file's test go red (capability row 4, below — a copy would not have noticed). Also ran
   `tests/test_marker_blocks.py` alone from three different invocation shapes — repo root,
   `tests/` as cwd, and an absolute path from an unrelated cwd — all three: 15/15 passed, same
   bare-import resolution every time. The cited precedent (`tests/test_flake_probe_real_process.py`)
   does use the identical bare-import pattern and the reasoning holds, though at line 27, not the
   manifest's cited line 15 (filed as AT-517, low, citation-only — the file hasn't changed since
   its one commit).
4. **Verify commands, re-run myself, not pasted:**
   - `pytest -q -o addopts= tests/test_ledger_checks.py tests/test_marker_blocks.py` → `34 passed`
   - `autotester doctor` → `doctor: clean`
   - `ruff check src tests scripts` → `All checks passed!`
   - `wc -l` → 163 / 154, matches the manifest, both under C2's 300-line cap
   - `scripts/mutation_check.py qa/evidence/.../mutations.json` → `4/4 mutations killed`, exit 0;
     row 4 names 1 test and 16 actually failed — confirmed this is intended, not a bug: `is_kill`
     at `scripts/mutation_check.py:110` is `exit_code == 1 and expected <= failures` (a subset
     check, per its own docstring), never equality.
   - **Full suite**, `uv run pytest` with no extra `-q` (so config's single `-q` gives a readable
     summary — see the AT-503 note below), redirected to a file, scanned whole, never tailed:
     `1 failed, 1483 passed, 2 skipped, 32 xfailed, 1 warning in 1078.94s`, exit 1. The one failure
     is `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_
     real_grandchild` (`FileNotFoundError` reading a spawned child's pid file) — a file this unit's
     diff never touches (`git diff b40f6f3..9ed3833 --name-only` lists only
     `tests/test_ledger_checks.py`, `tests/test_marker_blocks.py`, the manifest and its own
     evidence dir). Re-ran that file alone immediately after: `2 passed in 16.58s`. This is a real
     subprocess + pid-file + wall-clock-timeout test, and this project already carries two
     precedents for exactly that shape false-FAILing under machine contention (AT-196, AT-505) —
     confirmed via isolated re-run per that precedent before crediting anything to this unit. Filed
     as AT-518 (a third distinct test in the same class) rather than silently absorbed.

## Capability coverage — 4/4 rows reproduced in throwaway copies outside the bound tree

| row | green-before | red-after (right reason) |
|---|---|---|
| AT-504 marker recognition (`_is_marker_line` → `marker in line`) | 3 passed | 3 FAILED, the 3 named tests, on the marker/prose-vs-claim assertion itself |
| AT-511 field-label stop (`_NEW_FIELD` → the AT-509 form `[A-Z][A-Z0-9 -]*:`) | 1 passed | FAILED — `AT-901` leaks into `ISSUES-WRITTEN`'s block, the exact defect the test defends against |
| AT-508 claim grammar (drop the `_NOT_FIXED` negation) | 5 passed | 3 FAILED — `not yet fixed`/`not-fixed` misread as fix claims, plus the NOT-fix-stays-open test |
| Shared helper (`ROW` mutated in the OLD file) | 1 passed | FAILED — the NEW file's `test_a_fix_claim_on_a_continuation_line_is_read` breaks when the constant changes only in the old file: the import is live, not a copy |

Each edit was single-hunk, single-file, exactly as the manifest's table names it, applied only to a
scratch copy — never to the bound working tree.

## Diff scope (4c)

`git diff b40f6f3..9ed3833 --stat`: new evidence files, the new manifest,
`tests/test_ledger_checks.py` (132 deletions only, **zero additions**), `tests/test_marker_blocks.py`
(new, 154 lines). No `src/` file touched. No function/class/test/config-key deleted without being
accounted for — every one of the 21 function defs in the pre-split file exists in exactly one of
the two post-split files (confirmed by the AST-based re-derivation above, independent of the
manifest's own `at513_split.py`). Nothing outside "What changed" was touched.

## Disclosures verified (not accepted on the maker's word)

- **Mutation-harness equality overclaim in at508:97/at509:95/at511:96.** Confirmed the code: both
  the return statement and `is_kill`'s own docstring frame the second clause as a subset
  ("the tests that CLAIM to notice actually did"), never equality. Also independently confirmed,
  by reading every row of at508's/at509's/at511's `mutations.out`, that the "== exactly" framing
  was nonetheless a TRUE observation of those specific runs — zero extra failures in any row of
  those three files. Correct call by the maker: this is prose imprecision in three closed, PASSed
  manifests, not something to fix by editing them. Filed as AT-515 (low, documentation).
- **3-of-33 evidence specs made unrunnable by this split.** Reproduced directly: re-ran
  `scripts/mutation_check.py` against `at506`'s `mutations.json` and got the exact cited
  `MutationError` — confirmed it fails closed, not a silent mis-report. Confirmed by inspection
  that at509's and at511's `mutations.json` each name nodeids that have since moved to the new
  file. This is a genuine second occurrence of the AT-506→at504 pattern with no governing rule.
  Filed as AT-516 (medium, evidence-integrity) and flagged as HUMAN_GATE-worthy for a standing
  splitting policy — not a blocker on this otherwise-clean unit.

## Ledger

- **AT-513** (medium, structural-erosion): flipped `open → fixed` — this unit is exactly the fix
  it names; both files are now well under C2's 300-line cap and `doctor: clean`.
- **AT-503** (low, tooling): amended `expected` with a simpler remedy raised mid-check by the
  dispatching session (self-verified separately: a bare `uv run pytest` with no explicit `-q`
  already gets a single `-q` from `pyproject.toml`'s `addopts` and prints a readable summary).
  Not an AT-513 finding on its own merits; recorded because the ledger is the checker's surface
  and it surfaced during this check.
- **AT-515** (low, documentation) — mutation-harness equality overclaim, above.
- **AT-516** (medium, evidence-integrity) — the 3-of-33 broken-specs pattern, above.
- **AT-517** (low, documentation) — manifest cites `tests/test_flake_probe_real_process.py:15`;
  the actual import line is 27 (file unchanged since its one commit, eb48415). The precedent
  itself is real and was independently re-verified under three invocation shapes.
- **AT-518** (low, flake) — a third distinct test hitting the AT-196/AT-505 real-subprocess
  timing-flake class, confirmed unrelated to this unit's diff and non-reproducing in isolation.

## Live browser evidence

Not applicable — no UI surface changed, no `src/` file changed. Changed paths:
`tests/test_ledger_checks.py`, `tests/test_marker_blocks.py` (new),
`qa/evidence/at513-the-block-tests-leave-the-row-tests/*`, this manifest.

---

VERDICT: PASS
SCOREBOARD: 2/2 criteria met (C2 file-size cap, C7 mutation duty), all invariants hold (no behaviour change, verbatim move, ledger consistency, diff-scope clean)
FAILURES (if any): none
CAPABILITY-COVERAGE: 4/4 rows reproduced (throwaway copies, green-before confirmed, red-after for the named reason)
LIVE-BROWSER: not-applicable (no UI surface changed; changed paths: tests/test_ledger_checks.py, tests/test_marker_blocks.py, qa/evidence/at513-*, this manifest)
ISSUES-WRITTEN: AT-515, AT-516, AT-517, AT-518 (also amended AT-503's remedy and flipped AT-513 open -> fixed)
EXPLANATION: A pure test-move whose only real claim — "nothing changed" — held up under independent re-derivation on all three axes the manifest itself proposed (name-set identity, verbatim function bodies, live shared-helper import), plus my own diff-scope and full-suite checks. The one full-suite failure is a confirmed, unrelated, non-reproducing busy-machine flake in a file this unit never touches. Both of the maker's self-disclosed prose issues (mutation-harness equality overclaim; 3-of-33 broken evidence specs) checked out exactly as described and are now tracked in the ledger rather than left in prose.
