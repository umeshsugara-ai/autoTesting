# Verdict — at278-min-distinctive-words-floor

**Cycle checked: 1**
**Date:** 2026-09-09
**Checker mode:** A (unit check)
**Commit checked:** `7b5a167cebcb3344d49d41f6120360d6cf6b4874`
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)

## What I re-ran independently

1. `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` -> **41 passed**.
2. `uv run pytest` -> **942 passed, 2 skipped, 1 warning in 121.47s**.
3. `uv run ruff check src tests scripts` -> **All checks passed!**
4. `uv run autotester doctor` -> **doctor: clean**.
5. Scope from `git show 7b5a167`: only `src/autotester/stages/similarity_score.py` and
   `tests/test_similarity_score.py` changed. Neither is a UI surface, so Mode D is not applicable.

## Independent sabotage and boundary press

I reconstructed the pre-floor calculation from the shipped `STOPWORDS` and compared it with the
live function. This does not trust the maker's pasted mutation:

- The manifest's erosion pair (`Certificate export downloads corrupted when large` versus
  `Certificate generation crashes when the network is slow`) is **1.0 without the floor** and
  **0.0 with it**. The submitted guard is real and the three floor tests are load-bearing.
- `Timeout` versus the identical `Timeout` is **1.0 without the floor** but **0.0 with it**.
  Through `score()`, at the same recording and exact same second, that becomes recall **0.0** and
  one false positive. This is a new short-title false negative introduced by the fix.
- `Invoice rejected` versus `Invoice approved` and `Password reset` versus `Password leaked`
  each score **0.5** both with and without the floor. Through `score()`, at the same recording and
  exact same second, both are accepted as matches: recall **1.0**, zero false positives. They are
  contradictory/different faults sharing only one generic subject token.

The mechanism claimed as structurally closed therefore remains immediately above the chosen floor.
At `MIN_DISTINCTIVE_WORDS = 2`, one shared word yields 1/2 = 0.5, already above the shipped 0.30
threshold. At the same time, the hard early return destroys the strongest possible short-content
case: exact identity. The scorer has recording and time evidence in addition to text, so the module
claim that a one-word text match is definitionally never evidence does not hold for the actual
three-part match used by VL11.

## Contract judgment

- **VL11: FAIL.** Same-recording, same-second, identical short content is missed, while
  contradictory two-token content is accepted on one shared token. The text leg of the required
  recording + time + text match is not reliable at the boundary introduced by this unit.
- **VL12: PASS.** The declared threshold remains observable and is applied; the defect is the
  similarity value presented to that threshold.
- **VL13: PASS.** The new rule is deterministic and content-only; permutations do not affect it.
- **I-VL7: PASS.** No provider, network, clock, or randomness was introduced.

AT-278 remains open because the named examples are suppressed but the submitted structural remedy
does not yet provide a contract-safe short-text rule. New finding **AT-279** records the independently
reproduced false-negative/false-positive boundary.

```
VERDICT: FAIL
SCOREBOARD: 2/3 applicable criteria met, 1/1 applicable invariants hold
FAILURES (if any):
- [VL11] sev: high · exact one-token reports are forced misses while contradictory two-token reports match at 0.5 on one shared word · add an exact-content path and require stronger shared-token evidence for non-exact short pairs, with full-score regressions · issue: AT-279
LIVE-BROWSER: not-applicable (src/autotester/stages/similarity_score.py, tests/test_similarity_score.py)
ISSUES-WRITTEN: AT-279
EXPLANATION: All declared checks pass and the floor genuinely suppresses the two named AT-278 examples. Independent full-scorer probes show the chosen boundary trades that defect for an exact-short-title false negative while leaving the same denominator artefact at two distinctive words, so VL11 is not met.
```
