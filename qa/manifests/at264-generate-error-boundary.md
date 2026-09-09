# Manifest — at264-generate-error-boundary

**Contract:** qa/contracts/ui.md (U1-U6), review-gate R1-R3, expand.md X1
**Goal task:** none — issue-driven (AT-264)
**Date:** 2026-09-09
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-264 (high)

## What changed

- `src/autotester/ui/routes_learn.py:35` — import `ProviderError` from `autotester.providers.base`
- `src/autotester/ui/routes_learn.py:212-227` — wrap the `expand(spec, provider, RepoDocs())` call
  in `generate_cases` with `try/except ProviderError`, returning the same `_refusal()` themed page
  every sibling failure path in this function already uses, instead of letting the exception
  propagate to a raw `text/plain` 500.
- `tests/test_ui_learn.py` — new test
  `test_generate_when_the_model_fails_midway_is_refused_as_a_page_not_a_500`, starving a
  `MockProvider`'s response queue for role `agent` (exactly how `providers/gemini.py` raises
  `ProviderError` on an unparsed response or schema mismatch) and asserting the response is a 400
  themed HTML page, not a 500, and that `store.list_cases()` stays empty (no partial write).

## Why (AT-264, filed by checker-sweep)

Every OTHER refusal in `generate_cases` (no flowspec, unapproved flowspec, no provider configured)
returns a themed page via `_refusal()` — the pattern this exact route was built to enforce (AT-244:
"a refusal an operator reaches by clicking is part of the interface"). But the one step that runs
*after* all three gate checks pass — the actual model call inside `expand()` — was unguarded. A
`ProviderError` raised mid-generation reached the operator as a raw `text/plain` 500 with no themed
page, no way onward, and no clue what happened.

This is not hypothetical: `providers/gemini.py` genuinely raises `ProviderError` on an unparsed
response or schema mismatch (lines 107, 109, 123, 128, 144), and this project's own measured recall
today — **1/7 real, model-graded matches** against the ERP Trainer ground truth — is direct evidence
the model already misbehaves on paths adjacent to this exact one.

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_learn.py -x` → expected: exit 0, all pass (12 tests)
- `uv run pytest` → expected: exit 0, `913 passed, 2 skipped`
- `uv run ruff check src tests scripts` → expected: exit 0, "All checks passed!"
- `uv run autotester doctor` → expected: exit 0, "doctor: clean"

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_learn.py -x
............                                                             [100%]
12 passed, 1 warning in 1.03s

$ uv run pytest
913 passed, 2 skipped, 1 warning in 88.61s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7):** reverted the fix to the exact pre-fix code
(`for case in expand(spec, provider, RepoDocs()): store.add_case(case)`, no try/except) in the live
file, re-ran the new test alone:

```
E       autotester.providers.base.ProviderError: mock provider has no queued response for role=agent
1 failed, 1 warning in 2.05s
```

Confirmed the anchor matched, the file changed, and the test fails without the fix as designed — not
a C7-INCONCLUSIVE zero-failure result. Restored the fix immediately after (`git diff` shows only the
intended net change).

## Live browser evidence

`qa/evidence/browser-at264-generate-error-boundary-2026-09-09/report.json` — real headless Chromium
against a live `uvicorn` process serving a scratch project with an **approved FlowSpec** (the
Generate-cases button's precondition).

- 2 pages visited, 2/2 interactions passed.
- Confirmed live: the Generate-cases form exists on an approved flowspec; clicking it with no model
  provider configured in this scratch environment returns a **themed `AutoTester` page**, not a raw
  500 or a `"detail"` JSON blob — proving the new `try/except` wrapper imports, compiles, and runs
  correctly in a real server process without breaking the pre-existing sibling refusal paths.
- **Stated scope gap, honestly:** the *exact* failure AT-264 names — a `ProviderError` raised
  *mid-generation* by an otherwise-available provider — needs monkeypatching a provider instance
  inside a live server process, which a black-box browser client cannot do. That branch is instead
  verified by the sabotage-confirmed pytest above, using the identical reproduction technique
  (`checker-sweep`'s own `.work/checker-sweep-provider-error-test.py`) that found the bug.
- One console-error entry recorded and explained in the report: Chromium logging the page's own
  intentional HTTP 400 navigation response — not a JS error, not a defect.

## Status: checked-PASS (cycle 1 verdict 2f11c94)
