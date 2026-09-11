# Manifest — at102-merge-rediscovery-dedup

**Unit:** AT-102 — a same-name screen re-discovery is added as a silent duplicate, not merged
**Contract:** `qa/contracts/explore.md` (X12 amendment), `qa/contracts/coverage.md` (V1)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-102 (medium)

## What was wrong

`explore_merge.merge_screens` raised a `Conflict` only when a clashing screen's name DIFFERED
from the incoming crawled screen's name (`disagreement()`). When a screen was re-discovered at an
already-known `url_pattern` under the SAME name (a genuine re-discovery — the same page, found by
a fresh crawl, minted with a new structural node id), `disagreement()` correctly returned `None`
(no conflict — the docstring's own reasoning about SPAs held), but `merge_screens` still
unconditionally appended the incoming screen to `added`. Result: the `FlowSpec` ended up with two
identically-named `Screen` rows on one `url_pattern`, and nothing — no `Conflict`, no log, no
review note beyond a generic "N screen(s) added" — told a human why.

## What changed

- `src/autotester/stages/explore_merge.py` — new helper `_is_rediscovery(clash, incoming) -> bool`:
  true when an existing screen at the same pattern has the same name and no structural identity
  (i.e., it's neither a new screen nor a real disagreement — see `disagreement()`'s own SPA
  reasoning, which this reuses via `_is_structural`). `merge_screens`'s loop now skips adding
  (`continue`) when `_is_rediscovery` is true, instead of always appending.
  Extracting the helper also kept `merge_screens` under the 50-line function cap (C2) — the inline
  check alone pushed it to 54 lines.
- `tests/test_explore_merge.py` — new test
  `test_a_same_named_rediscovery_merges_instead_of_duplicating`: seeds a spec with one
  non-structural `Screen`, merges a crawled node with the same name at the same pattern, asserts
  the spec still has exactly one screen (the original, untouched — `scr_old`) and no conflict.

## What this unit does not claim

- Does not touch `disagreement()` itself or the genuine-conflict path (different names, no
  structural identity) — that stays exactly as AT-103 left it, still covered by
  `test_a_name_clash_on_the_same_url_keeps_both_and_records_a_conflict`.
- Does not touch the SPA path (`_is_structural(clash)` true) — still adds normally, still no
  conflict, unchanged, still covered by `test_two_spa_states_at_one_url_are_two_screens_not_a_conflict`.
- If `added` ends up empty because the only node(s) in a merge were all re-discoveries, the spec
  is returned unchanged (`if not added: return spec`) — no version bump, no review reset. This
  falls out of the existing idempotence path (`merge_screens`'s own docstring) rather than being a
  new decision; not separately asserted here beyond the one new test's own screens/conflicts checks.

## How to verify (commands + expected)

- `uv run pytest tests/test_explore_merge.py -q` → expected: exit 0, 15 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_explore_merge.py -q
...............                                                          [100%]  (15 passed)

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

1. Extracted clean `HEAD`, layered my uncommitted diff on with `git apply`.
2. `uv sync`; confirmed `autotester.__file__` resolves inside the extract.
3. Baseline: `uv run pytest tests/test_explore_merge.py -q` → 15 passed, exit 0.
4. Mutated `_is_rediscovery` to always `return False` (the exact revert of this fix — dedup logic
   disarmed, behaving as it did before).
5. **Exactly the predicted single test failed**
   (`test_a_same_named_rediscovery_merges_instead_of_duplicating`,
   `AssertionError: assert 2 == 1`, the exact original defect shape — two screens where the spec
   should show one), the other 14 stayed green.
6. Extract deleted; live tree confirmed to carry only the two real edits.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/stages/explore_merge.py`,
`tests/test_explore_merge.py`. Pure stage logic + test, no route/template touched.

## Status: ready-for-check
