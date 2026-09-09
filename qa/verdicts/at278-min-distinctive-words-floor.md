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

---

## INDEPENDENT CONCURRENT CHECK

**Cycle checked: 1**
**Date:** 2026-09-09
**Checker mode:** A (unit check), run blind to the verdict above until after independent verification completed
**Commit checked:** `7b5a167cebcb3344d49d41f6120360d6cf6b4874`
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)

### What I re-ran independently

Own isolated extract: `git archive HEAD` into a scratch directory with its own `uv sync` venv;
confirmed `autotester.stages.similarity_score.__file__` resolved inside the extract before
trusting any result.

1. `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` -> **41 passed**.
2. `uv run pytest` -> **942 passed, 2 skipped, in 98.83s**, exit 0.
3. `uv run ruff check src tests scripts` -> **All checks passed!**
4. `uv run autotester doctor` -> **doctor: clean**.
5. Live-repo real-corpus regression:
   `uv run python scripts/score_video_issues.py --project erp --truth "C:/Users/Lenovo/Videos/Screen Recordings/ERP_Issues_Trainers.xlsx" --sheet "Trainer module"`
   -> **recall 0.4286 (3/7), unchanged**, matching the manifest's claim.
6. `git show --stat 7b5a167` -> only `src/autotester/stages/similarity_score.py` and
   `tests/test_similarity_score.py` changed. Not UI-touching; Mode D not applicable.

### Independent sabotage confirmation

Removed the `if len(shorter) < MIN_DISTINCTIVE_WORDS: return 0.0` guard in the isolated extract.
`uv run pytest tests/test_similarity_score.py -v` -> **exactly 3 failures**, the other 10 tests in
the file stay green:

- `test_a_report_eroded_to_almost_nothing_does_not_falsely_match[export-corruption-vs-network-crash]`:
  `assert 1.0 < 0.3` fails, landing at the predicted 1.0 ceiling.
- `...[count-update-vs-photo-render]`: same, 1.0.
- `test_a_single_shared_word_is_never_evidence_of_a_match`: `assert 1.0 == 0.0` fails, 1.0.

Restored by patch (never `git checkout`); `grep -c MIN_DISTINCTIVE_WORDS` -> 3, unchanged, matching
the manifest's own restoration discipline.

### The critical press — is the floor structural, or does it push the same failure to a higher word count?

Constructed pairs at shorter-side word counts of 2, 3, and 4, all genuinely unrelated faults
sharing nothing but one incidental domain noun that recurs across many different bug reports in
the same product ("trainer", "certificate", "payment", "video", "dashboard"):

| shorter side (n words) | pair | similarity |
|---|---|---|
| 2 | `Trainer login fails` vs `Trainer avatar blurry` | **0.5** |
| 2 | `Certificate download broken` vs `Certificate font tiny` | **0.5** |
| 3 | `Trainer login page crashes` vs `Trainer avatar photo blurry` | **0.333** |
| 3 | `Payment gateway timeout` vs `Payment icon misaligned` | **0.333** |
| 3 | `Video player buggy` vs `Video thumbnail broken` | **0.333** |
| 4 | `Trainer login times out repeatedly` vs `Trainer avatar image is blurry` | 0.25 (below threshold) |
| 4 | `Dashboard widget crashes constantly` vs `Dashboard color scheme looks ugly` | 0.25 (below threshold) |

At exactly the floor (shorter=2) and one word above it (shorter=3), one incidentally shared
distinctive word between two genuinely unrelated faults still clears the shipped 0.30 threshold
(0.5 and 0.333 respectively). Only at shorter=4 does a single incidental shared word fall below
threshold in these constructions. This independently reproduces and corroborates the primary
verdict's finding (`Invoice rejected`/`Invoice approved` = 0.5, `Password reset`/`Password leaked`
= 0.5) with a different word class — not adjective-pair contradiction but a shared domain-entity
noun, which is arguably the more common real shape in this corpus (recordings repeatedly say
"Trainer ..." across unrelated screens). **The floor is not structural**: it moves the guaranteed-
failure case from 1 word (0.0/1.0 ceiling, always wrong) to "the floor value + a bit," where a
false positive is now merely *likely* rather than *certain*, but is not closed. This is the same
instance-patch shape AT-218 names, wearing the form of a threshold rather than a word list —
confirmed independently rather than assumed from the primary verdict's own examples.

### Is refusing to score (0.0) itself defensible against real corpus data?

Checked whether any real match in the ERP corpus sits at exactly 1 distinctive word on its shorter
side (which the floor would now wrongly refuse). All three `found: true` matches in the current
real-corpus run score 0.636, 0.778, and 0.667 — comfortably away from the floor boundary, and by
inspection of the truth titles none is a genuine 1-distinctive-word match. **No real false negative
was found in this corpus from the floor itself**; this narrow part of the manifest's claim holds
independently. The defect is on the false-positive side (documented above and in the primary
verdict), not on the disclosed false-negative trade the manifest owns.

### Contract judgment (concurs with primary verdict)

- **VL11: FAIL**, independently reproduced by a different construction (shared domain noun, not
  shared adjective) at both shorter=2 and shorter=3. Same-recording/same-second matching is not
  reliable at exactly the boundary this unit introduces.
- **VL12: PASS** — threshold remains observable and applied.
- **VL13: PASS** — deterministic, content-only.
- **I-VL7: PASS** — no provider/network/clock/randomness introduced.

I concur with the primary verdict's FAIL and AT-279's framing, and add corroborating evidence
(recall regression re-run, and a second, distinct construction of the same-mechanism false
positive at shorter=2 and shorter=3) rather than a new issue — AT-279 already covers this defect
class.

```
VERDICT: FAIL
SCOREBOARD: 2/3 applicable criteria met, 1/1 applicable invariants hold
FAILURES (if any):
- [VL11] sev: high · at MIN_DISTINCTIVE_WORDS=2, one incidentally shared domain-noun word between genuinely unrelated faults scores 0.5 (shorter=2) or 0.333 (shorter=3), both above the shipped 0.30 threshold — corroborates AT-279 with an independent construction · same fix direction as AT-279 (exact-content path + stronger shared-token requirement for non-exact short pairs, tested through score()) · issue: AT-279
LIVE-BROWSER: not-applicable (src/autotester/stages/similarity_score.py, tests/test_similarity_score.py)
ISSUES-WRITTEN: none (corroborates existing AT-279, no new issue filed)
EXPLANATION: Independently re-ran every verify command, the sabotage (3 failures at predicted 1.0 ceiling), and the real-corpus regression (recall 3/7 unchanged) in my own isolated extract. The floor genuinely suppresses the two AT-278-named examples but is not structural: it relocates the guaranteed-failure ceiling from 1 shared word to "floor value, one incidental shared word," which a shared domain noun (not just a contradictory adjective) still clears at the shipped threshold. Concurs with the primary verdict's FAIL.
```

---

## Cycle 2 re-check

**Cycle checked: 2**
**Date:** 2026-09-09
**Checker mode:** A (unit check)
**Commit checked:** `cbdfab13057a8f137f037c864f7eed94665f98b9`
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)

### Evidence re-run independently

1. `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` -> **44 passed**.
2. `uv run pytest` -> **945 passed, 2 skipped, 1 warning in 101.99s**.
3. `uv run ruff check src tests scripts` -> **All checks passed!**
4. `uv run autotester doctor` -> **doctor: clean**.
5. The exact `cbdfab1` archive resolved imports from its own `src/`; its focused baseline was
   **44 passed**, and after restoration its scorer file hash matched the commit blob exactly
   (`1a3677dd6497e0897c4882fec96e58f2b6085c01`).
6. The shipped real ERP scorer against `ERP_Issues_Trainers.xlsx` / `Trainer module` reports
   **3/7 recall (0.4286), 3 false positives, 6/6 observations, complete coverage**. The same
   three rows remain matched at 0.636, 0.778, and 0.667; no real-corpus semantic result moved.

### Independent score-path sabotage

- Disabled the exact-normalized-token branch in the isolated commit. The real `score()` regression
  failed exactly as required: `Timeout` / `timeout!` fell to recall **0.0** and the issue became a
  false positive. The full focused pair had exactly **1 failure**.
- Weakened the two-shared-distinctive-token gate to one. Both real `score()` contradiction
  regressions failed: `Invoice rejected` / `Invoice approved` and `Password reset` / `Password
  leaked` each returned recall **1.0**, similarity **0.5**, and no false positive. The focused pair
  had exactly **5 failures**: those two, both AT-278 erosion cases at **1.0**, and the direct
  one-shared-word guard.
- Restored the isolated artifact and re-ran the 44 tests green before judging it.

### New nearby boundary and semantic-change check

Through `score()` at the same recording and second, `Timeout` / `The timeout` remains a miss
(0.0), while `Invoice payment rejected` / `Invoice payment approved` remains a lexical match
(0.667). These are the declared deterministic lexical trade-off at the next boundary, not a cycle-2
regression: the new code changes only exact normalized-token equality and one-shared-token admission,
and the real ERP report is unchanged. An exact multi-token punctuation/case variant (`Invoice payment
rejected` / `invoice payment rejected!`) correctly returns 1.0.

### Contract judgment

- **VL11: PASS.** Exact normalized one-token content now survives through `score()`, while every
  non-identical match requires at least two shared distinctive tokens; both branches are
  independently mutation-discriminating.
- **VL12: PASS.** The shipped 0.30 threshold remains observable and applied.
- **VL13: PASS.** The change is deterministic and content-only; no ordering state was introduced.
- **I-VL7: PASS.** The changed scorer module introduces no provider, network, clock, or randomness.

AT-278 and AT-279 move `open -> fixed` in the checker-owned ledger. Per ledger policy, a later
independent re-check may move them from `fixed` to `verified`.

```
VERDICT: PASS
SCOREBOARD: 3/3 applicable criteria met, 1/1 applicable invariants hold
FAILURES (if any):
- none
LIVE-BROWSER: not-applicable (src/autotester/stages/similarity_score.py, tests/test_similarity_score.py)
ISSUES-WRITTEN: none (AT-278 and AT-279 moved open -> fixed)
EXPLANATION: All manifest commands reproduce, both cycle-2 branches are independently load-bearing through the real score() path, and the real ERP scorer remains 3/7 with the same matched rows and full 6/6 coverage. The new adjacent lexical cases expose the already-declared matcher trade-off but no unexpected cycle-2 semantic regression, so VL11-VL13 and I-VL7 pass.
```
