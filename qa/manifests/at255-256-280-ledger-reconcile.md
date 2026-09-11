# Manifest — at255-256-280-ledger-reconcile

**Unit:** AT-255/AT-256/AT-280 — three stale high-severity ledger rows, overtaken by later work
**Contract:** `qa/contracts/core-invariants.md` (C7 — verification-artifact integrity)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-255 (high), AT-256 (high), AT-280 (high)

## What was wrong (as originally filed)

- **AT-255** (2026-09-09): `99ea27d` shipped the AT-230 gemini-schema fix with no manifest, no
  verdict, and its guard test untracked — a BYPASS.
- **AT-256** (2026-09-09): the wiring line (`gemini.py:79`) was still unpinned even after the
  maker called it "INCONCLUSIVE" — same recognition-without-prevention class as AT-218.
- **AT-280** (2026-09-10): `qa/.last-tick` was 14.4h stale with a non-empty backlog — "maker
  asleep."

## What I found on re-check — all three are stale, overtaken by later units already on disk

- `qa/manifests/at230-gemini-schema.md` / `qa/verdicts/at230-gemini-schema.md` now exist, at
  **cycle 2, checked-PASS** (verdict `d14ce4c`). `tests/test_gemini_schema.py` is tracked
  (`git ls-files --error-unmatch` succeeds) and carries
  `test_the_PROVIDER_actually_sends_the_sanitised_schema`, which constructs a real
  `GeminiProvider` and asserts on its built `response_schema` kwarg — exactly the wiring line
  AT-256 says nothing covered.
- `qa/.last-tick` has been stamped on every tick this session (this is the fourth stamp in a
  row: `d5c8df3`, `c3cc52e`, `2e0e9c0`, and this unit's own).

## What changed

- `qa/issues.jsonl`: `AT-255` → `verified`, `AT-256` → `verified`, `AT-280` → `dismissed`, each
  with a note explaining the reconciliation and citing what re-derives the claim.

## How I verified this myself, not by trusting the later unit's docstring

Re-ran the ORIGINAL AT-255 sabotage independently, in a fresh isolated `git archive HEAD`
extract with its own `uv sync` venv (never the shared live tree — AT-101 discipline):

1. Extracted clean `HEAD` to an isolated scratchpad directory.
2. Confirmed the anchor `kwargs["response_schema"] = gemini_schema(schema)` matches exactly
   once in the extract's `src/autotester/providers/gemini.py`.
3. `uv sync` inside the extract; confirmed `uv run python -c "import autotester; print(autotester.__file__)"`
   resolves to a path **inside the extract**, not the live tree.
4. Mutated line 79 to `kwargs["response_schema"] = schema` (the AT-230 revert).
5. `uv run pytest tests/test_gemini_schema.py -q`.

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_gemini_schema.py -q          # baseline, live tree, unmutated
.............                                            [100%]  (13 passed)

--- isolated extract, sabotage applied ---
$ uv run python -c "import autotester; print(autotester.__file__)"
C:\Users\...\scratchpad\at255-sabotage\src\autotester\__init__.py

$ uv run pytest tests/test_gemini_schema.py -q
..........F..                                            [100%]

FAILED tests/test_gemini_schema.py::test_the_PROVIDER_actually_sends_the_sanitised_schema
AssertionError: the raw Pydantic class was sent (AT-230)
assert not True
 +  where True = isinstance(<class 'autotester.schema.observation.VideoObservation'>, type)
```

Exactly the predicted single test failed; the other 13 stayed green — the guard is real, not
decorative. Extract deleted after; live tree confirmed byte-unchanged
(`git status --porcelain -- src/autotester/providers/gemini.py tests/test_gemini_schema.py`
returned empty, before and after).

- `uv run pytest -q` → not re-run in full for this unit (data-only ledger edit, no `src/` or
  `tests/` path touched in the LIVE tree — the mutation happened only in the deleted isolated
  extract)
- `uv run ruff check src tests scripts` → not re-run for the same reason; left to the checker
- `uv run autotester doctor` → not re-run for the same reason; left to the checker

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `qa/issues.jsonl` only. Nothing under
`src/`, `tests/`, or `src/autotester/ui/` in the live tree (the sabotage mutation happened only
inside a deleted isolated extract, never the live tree).

## What this unit does not claim

- Does not claim AT-255's BYPASS process gap (no manifest/verdict at original ship time,
  `99ea27d`) was itself a good practice — only that it was closed after the fact by the later
  `at230-gemini-schema.md` cycle-2 unit, which is what "verified" now records.
- Does not claim `qa/.last-tick` can never go stale again — AT-280 is dismissed as a transient,
  now-resolved condition, not a structural fix; a fresh staleness would be a new finding.

## Status: checked-PASS (cycle 1, verdict qa/verdicts/at255-256-280-ledger-reconcile.md, commit bdf88f8)
