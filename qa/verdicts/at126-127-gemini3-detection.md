# Verdict — at126-127-gemini3-detection

**Cycle checked:** 1
**Date:** 2026-09-11
**Checker:** fresh /checker Mode A, no builder context

## Re-run (my own, not pasted)

```
$ uv run pytest tests/test_gemini_config.py -q
........                                                                 [100%]  (8 passed)

$ uv run pytest -q
[all dots] exit 0 (1145+ collected, 2 pre-existing skips, unrelated)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/
(no output — C8 satisfied)
```

## Sabotage — independently reproduced, isolated `git archive HEAD` extract

Extracted `HEAD` (fa3dfa1, unit already merged) to a scratch dir outside the repo,
`uv sync`'d its own venv, confirmed `autotester.__file__` resolved inside the extract
(not the live tree). Baseline asserted green first (8 passed) before trusting any mutation.

- **Mutation A** — reverted `_is_gemini_3` to bare `model.startswith("gemini-3")`. Anchor
  matched exactly once, file changed. Result: **exactly 2 tests failed**
  (`test_is_gemini_3_recognises_the_fully_qualified_sdk_form`,
  `test_config_applies_media_resolution_for_the_fully_qualified_form`), other 6 green.
  Matches the manifest's claim exactly.
- Restored the file from `git show HEAD:...` (byte-identical, confirmed via diff), then:
- **Mutation B** — removed the `thinking_config` block from `_config`. Anchor matched
  exactly once, file changed. Result: **exactly 2 different tests failed**
  (`test_config_applies_thinking_level_for_a_3x_model`,
  `test_config_thinking_level_follows_the_declared_option`, both
  `AttributeError: 'NoneType' object has no attribute 'thinking_level'`), other 6 green.
  Matches the manifest's claim exactly.

Both mutations reproduced independently with the predicted, non-overlapping failure sets —
C7's anchor/baseline/attribution clauses all satisfied.

## Criteria judged

No ingest.md criterion is numbered C8 — C8 lives in `core-invariants.md` ("Provider-agnostic"),
which the manifest's own header cites. Judged against that plus the sibling C7 mutation duty
(this unit adds a new test file, so C7's mutation-testing duty applies). No ingest.md `I*`
criterion targets model-version detection specifically (I9 governs upload/error-shape only, and
the no-fire list explicitly deferred `thinking_level` application until this unit).

- **C8 (provider-agnostic):** met. `providers/gemini.py` is still the only importer of
  `google.genai`; the grep instrument returns nothing; no prompt file was touched.
- **C7 (mutation duty + anchor/baseline/attribution):** met, evidenced above.

SCOREBOARD: 2/2 criteria met, 0/0 invariants in scope hold (none apply to this seam).

## Adversarial questions from the dispatch

1. **False-positive risk in `_is_gemini_3`** (e.g. `"gemini-30-something"` or
   `"not-gemini-3-really"`): real, but **pre-existing and unchanged by this unit**. The original
   code was `self._model.startswith("gemini-3")` — the same substring-match risk existed before
   AT-126/127. `removeprefix("models/")` only extends which *prefixed* forms are recognised; it
   does not touch the `startswith` matching logic itself, so this unit neither introduces nor
   worsens the risk. Matches the manifest's own disclosure ("not a complete model-name parser").
   Not filed as a new issue — it would be re-litigating a pre-existing, disclosed gap.

2. **`opts.thinking_level.upper()` safety:** `.upper()` itself never raises (any `str` supports
   it), but I confirmed by direct experiment that `VisionOptions.thinking_level` is an
   unvalidated bare `str` (`schema/observation.py:93`, no `Literal`/enum/validator) and that
   `types.ThinkingConfig(thinking_level="BANANA")` succeeds silently, producing a nonsense
   `ThinkingLevel.BANANA` enum member with only a `UserWarning` — nothing in this repo's error
   path catches it, and a malformed value would reach a real API call unnoticed. This gap
   predates the unit (the field existed, undeclared-as-applied, per ingest.md's own no-fire
   list), but **this unit is the first code to actually exercise it**, so it is newly reachable
   as of this change. Filed **AT-355** (medium) — does not fail this unit (no criterion requires
   value-level validation of `thinking_level`), but is real and worth a home now that the field
   is live.

3. **Live-API reachability without a key:** confirmed safe. `GeminiProvider.available()` returns
   `bool(self._api_key)`, and `_structured` raises `ProviderError` before calling `_config` or
   touching the network when `available()` is false. The changed behaviour (media_resolution /
   thinking_config now applying to more model-name inputs) is reachable only from inside
   `_structured`/`_config`, which is unreachable without `GEMINI_API_KEY`/`GOOGLE_API_KEY` set.
   No currently-running part of the system depends on the OLD (broken) detection to avoid a live
   call — the fix is inert if somehow wrong.

## Scope check

Not UI-touching, confirmed independently: `git show 7ef68b1 --stat` shows exactly
`qa/manifests/at126-127-gemini3-detection.md`, `src/autotester/providers/gemini.py`,
`tests/test_gemini_config.py`. No route, template, or rendered surface touched. Mode D not
required.

## Issues ledger

- Checked "Issues addressed": AT-126, AT-127 — both genuinely fixed, evidenced by the sabotage
  above; not yet marked in `qa/issues.jsonl` under those ids (they were issue-driven, not
  ledger-tracked prior entries in this file — no `AT-126`/`AT-127` rows exist in
  `qa/issues.jsonl` to flip).
- New: **AT-355** (medium) — see above, written to `qa/issues.jsonl`.

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met, 0/0 invariants hold
FAILURES (if any): none
LIVE-BROWSER: not-applicable (changed paths: src/autotester/providers/gemini.py, tests/test_gemini_config.py)
ISSUES-WRITTEN: AT-355
EXPLANATION: Both fixes are real and independently sabotage-confirmed in an isolated extract with
matching, non-overlapping failure sets exactly as the manifest claimed. C8 (provider-agnostic)
and C7 (mutation duty) are the only criteria this seam maps to and both are met. Two adversarial
risks investigated: the model-name false-positive is pre-existing and unworsened (no finding);
the thinking_level value is unvalidated and newly reachable for the first time by this unit,
filed as AT-355 (medium, does not block PASS). Confirmed the changed code path cannot reach a
live API call without a real key.
```
