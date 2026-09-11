# Verdict — at102-merge-rediscovery-dedup

**Cycle checked:** 1
**Date:** 2026-09-11
**Checker:** /checker Mode A, fresh subagent, bound to `D:/autoTesting`
**Contracts:** `qa/contracts/explore.md` (X12 amendment / X14), `qa/contracts/coverage.md` (V1)
**Manifest:** `qa/manifests/at102-merge-rediscovery-dedup.md`
**Commit:** `c29d322` (fix + test), `652fed4` (tick stamp) already on `master` at check time.

## What I re-ran myself

- Changed-paths confirmation: `git show --stat c29d322` — only
  `src/autotester/stages/explore_merge.py`, `tests/test_explore_merge.py`, and the manifest
  itself changed. No route/template/UI file touched → **not UI-touching, Mode D not required**
  (confirmed independently, not trusted from the manifest's own claim).
- `uv run pytest tests/test_explore_merge.py -q` → **15 passed**, exit 0 (matches manifest).
- `uv run pytest -q` → **full suite green**, exit 0 (2 skipped, unrelated), ran to completion in
  the live tree.
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**.
- **Sabotage, independently reproduced** in my OWN isolated extract (`git archive HEAD` into a
  scratch dir, own `uv sync` venv; confirmed `autotester.__file__` resolved inside the extract,
  not the live tree): baseline `tests/test_explore_merge.py -q` → 15 passed. Mutated
  `_is_rediscovery` to `return False` (the exact revert of this fix). Re-ran →
  **exactly `test_a_same_named_rediscovery_merges_instead_of_duplicating` failed**
  (`AssertionError: assert 2 == 1`, the predicted defect shape), the other 14 stayed green — byte
  match to the manifest's own claimed reproduction.

## Logic review — `disagreement()` vs `_is_rediscovery()`

Enumerated every `(clash exists?, clash structural?, same name?)` combination by hand against the
code (not just the tests):

1. `clash is None` → `disagreement` → `None`; `_is_rediscovery` → `False` (requires `clash is not
   None`) → **add, no conflict.** New screen. Correct.
2/3. `clash` exists and **is structural**, name same or different → `disagreement`'s
   `_is_structural(clash)` clause short-circuits to `None` regardless of name;
   `_is_rediscovery`'s `not _is_structural(clash)` is `False` regardless of name → **add, no
   conflict** in both cases. This is the SPA path, and it is correctly **name-independent**: a
   structural clash carries its own distinct node id (different structural signature — an
   identical id would already have been filtered by the `known_ids` check earlier in the loop),
   so a coincidental name match between two structurally distinct SPA states is not evidence they
   are the same screen. X3 requires two structurally different states at one URL to be two
   screens; the code honours that even when they happen to share a name.
4. `clash` exists, **not structural**, same name → `_is_rediscovery` → `True` → **skip entirely**.
   This is the new AT-102 path, and it is exactly the case the manifest and its one new test
   target.
5. `clash` exists, **not structural**, different name → `_is_rediscovery` → `False`;
   `disagreement` → neither `clash is None` nor `clash.name == incoming.name` nor
   `_is_structural(clash)` holds → returns a `Conflict` → **add + Conflict**. Genuine conflict,
   unchanged from AT-103's scoping.

The question posed for review — "incoming is structural (always true for a crawled node) but
clash is not, same name" — is case 4 above: it is not a fourth, uncaught case; it **is** the
re-discovery path this unit adds, and it dispatches correctly (skip, no duplicate, no conflict).
All five combinations land in exactly one of the three documented outcomes (add/no-conflict,
add/conflict, skip) with no gap and no double-dispatch. This matches the manifest's own "What
this unit does not claim" section, which I independently re-derived rather than took on trust.

One pre-existing, out-of-scope structural note (not a defect of this unit, and not re-raised as a
finding): `by_pattern` is built once from `spec.screens` before the loop and is never updated
from `added` mid-loop, so two nodes in the *same* `merge_screens` call never see each other as a
`clash` — only a pattern already in the spec before the call can clash. The existing
`test_two_spa_states_at_one_url_are_two_screens_not_a_conflict` and
`test_spa_states_found_by_two_separate_crawls_still_do_not_conflict` already document and rely on
this (the latter explicitly across two separate calls). Nothing in this unit's diff touches that
behaviour, and neither X14 nor the manifest claims otherwise.

## Contract + ledger maintenance performed

- `qa/issues.jsonl` — `AT-102` flipped `open → fixed` (`fixed_date: 2026-09-11`), evidenced by
  the sabotage re-run above and the logic review.
- `qa/contracts/explore.md` X14 — the AT-102 residual paragraph removed and replaced with a
  **CLOSED** note (mirrors the precedent set when AT-103 was closed 2026-09-08); one amendment-log
  entry appended, routine (closes a residual, softens nothing; X1-X13, X15, X16 byte-unchanged).
- No goal task closed — manifest states `Goal task: none — issue-driven`, and no `.goal/goal.json`
  task matches this unit.

## VERDICT: PASS
SCOREBOARD: 3/3 criteria met (X12 amendment / X14 AT-102 residual closed, coverage.md V1
unaffected — no coverage-path code touched), 0/0 invariants newly at risk
FAILURES (if any): none
LIVE-BROWSER: not-applicable (changed paths: `src/autotester/stages/explore_merge.py`,
`tests/test_explore_merge.py` — pure stage logic + test, no route/template touched)
ISSUES-WRITTEN: none new; AT-102 flipped open → fixed in `qa/issues.jsonl`
EXPLANATION: The fix is narrowly scoped, sabotage-confirmed in an isolated extract to reproduce
exactly the original defect shape, the full suite and lint/doctor gates are clean, and a
by-hand exhaustive case analysis of `disagreement()`/`_is_rediscovery()` shows the three dispatch
paths are mutually exclusive with no fourth case falling through incorrectly. Contract (X14) and
ledger (AT-102) updated to reflect the closure.
