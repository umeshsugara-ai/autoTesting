# Verdict — at276-stopwords-second-tranche

**Cycle checked: 1**
**Date:** 2026-09-09
**Checker mode:** A (unit check)
**Commit checked:** `19247ae9004800b9a3c12b9217ad042fc4b0b1d4`
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance — this unit is issue-driven, AT-276,
not tied to a specific numbered `[VL*]` criterion)

## What I re-ran myself

All work done in an isolated `git archive 19247ae` extract with its own `uv sync` venv
(`similarity_score.__file__` confirmed to resolve inside the extract before trusting any result).

1. `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` → **37 passed**, matches
   manifest exactly.
2. `uv run pytest` → **938 passed, 2 skipped, 1 warning in 113.60s**, matches manifest exactly.
3. `uv run ruff check src tests scripts` → **All checks passed!**, matches.
4. `uv run autotester doctor` → **doctor: clean**, matches.
5. **Sabotage confirmation, done independently** (not the maker's pasted mutation — my own, in my
   own extract): removed the AT-276 block from `STOPWORDS`, leaving exactly AT-232's original
   33-word list. Re-ran `tests/test_similarity_score.py`:
   - **Exactly the 5 parametrized false-positive tests failed**, the other 4 (both real-match
     tests, the AT-232 boilerplate-reject test, the superset test) stayed green — matches the
     manifest's claimed shape exactly.
   - The one value the manifest pasted in full (`export-vs-import-corrupted-file` →
     `0.7142857142857143`) reproduced **byte-for-byte**. The other four failures reproduced with
     their own values (0.75, 0.8571428571428571, 0.625, 0.8571428571428571) — internally
     consistent, not independently checkable against the manifest since it only pasted one.
   - Restored the file from a saved copy (never `git checkout`), re-confirmed all 9 tests green,
     and confirmed the **live tree** (not the extract) was never touched:
     `grep -c '"changed", "change",' src/autotester/stages/similarity_score.py` → `1`.
6. **Real-corpus regression, re-run independently** (not pasted): copied the untracked
   `projects/erp/` data into the extract and ran
   `uv run python scripts/score_video_issues.py --project erp --truth "C:/Users/Lenovo/Videos/Screen Recordings/ERP_Issues_Trainers.xlsx" --sheet "Trainer module"`
   both with and without `--root .`. **Recall 0.4286 (3/7), unchanged**, both ways — matches the
   manifest's claim. (Ran both because the contract's own amendment log flags a historical
   `--root`-omission bug, AT-219; confirmed independently that AT-219 was already fixed by an
   earlier unit — `score_video_issues.py:99-105` — and is unrelated to this one, so the manifest's
   real-corpus command, run exactly as pasted with no `--root`, genuinely reads this repo's own
   `projects/erp/`, not `D:\`.)
7. **Scope check** — `git show --stat 19247ae`: exactly two files touched,
   `src/autotester/stages/similarity_score.py` (+32/-7) and `tests/test_similarity_score.py`
   (new, +107). No other production code, no UI surface. Not UI-touching; Mode D correctly
   skipped by the manifest — confirmed by the diff, not the manifest's own claim.

## Adversarial press beyond the 5 tested (this is the part worth reading)

The dispatch asked me to press specifically on whether this second STOPWORDS extension introduced
its own false-positive risk, the way the *previous* checker's press on AT-232 itself found AT-276.
It did, in a more severe form than what it fixed.

**First pass — six adversarial pairs on the newly-generic words directly** (count/wrong/message,
search/filter, export/file/large, change/changed, message, count/update), all built to differ in
screen/module (Programs vs Applicants, PDF vs CSV, trainer-certification vs applicant-visa,
sender vs recipient, archived vs rejected): 5 of 6 scored 0.5–0.75, comfortably above threshold.
**But** re-testing the same 6 pairs against the *pre-AT-276* (AT-232-only) stopword list showed
every one of them **already** scored as high or higher (0.33–0.78) before this unit. AT-276 never
increases these scores and mostly lowers them slightly — this is pre-existing, orthogonal residual
risk in the containment metric generally (exactly what the module's own docstring already
discloses: "a false positive in a NEW vocabulary not yet seen will recur"), not something this
unit caused or worsened. Not a finding against this unit.

**Second pass — pressing the actual mechanism, not just the vocabulary.** Containment is
`|shorter ∩ longer| / |shorter|`. Removing a word from consideration that occurs **only in the
shorter text** shrinks the denominator without touching the numerator, which can only raise the
score. AT-232's list was purely grammatical/domain boilerplate (field/validation/screen/edit);
AT-276 added many **content-bearing action words** (export/downloads/corrupted/when/large/
count/update/filter/message/change…) that can legitimately be the *entire* distinguishing content
of a short bug report. Constructed and measured in the isolated extract:

- `"Certificate export downloads corrupted when large"` vs `"Certificate generation crashes when
  the network is slow"` — two genuinely unrelated faults (data corruption on export vs. an
  infra/network crash). Under AT-232-only STOPWORDS: **0.3333** (correctly below threshold). Under
  this unit's STOPWORDS: **1.0000** — every word in the shorter sentence except `certificate` is
  now stripped, leaving `shorter={"certificate"}`, `shared={"certificate"}`, ratio 1/1.
- `"Trainer count updates wrong after filter change"` vs `"Trainer profile photo fails to render
  after refresh"` — **0.2857 → 1.0000** under the same mechanism.

This is not the same false positive AT-276 fixed — it is a **new, more severe (score-ceiling)**
instance the fix itself introduces, reproducible, outside the 6 pairs AT-276 was measured against.
Filed as **AT-278** (high) in `qa/issues.jsonl`.

## Judgment on the manifest's own restraint

The manifest declined to add the sixth word group (fragment only, no full sentence pair given),
citing the module's own "never by guess" discipline. **This is the right call, not an unreasonable
gap.** The discipline is explicit in the module's docstring, this unit's own diff didn't invent
it, and AT-278 above is direct evidence of the cost of guessing: adding words without a measured
sentence risks exactly the erosion mechanism that produced AT-278, and doing it on a guess (no
sentence to check the erosion against) would be worse, not better.

## Does AT-278 block this unit?

No. AT-276's own claimed scope — five demonstrated false-positive pairs closed, the two real
corpus matches and the AT-232 boilerplate case still holding, the extension additive-only — is
every one of it evidenced, independently reproduced, sabotage-confirmed. AT-278 is real and
high-severity, but it is evidence about the underlying containment metric's growing fragility as
STOPWORDS accumulates content-bearing words, not evidence that this unit failed to do what it
said. No contract criterion demands STOPWORDS completeness or immunity to future erosion; the
module explicitly disclaims that. Filed for the next fix cycle rather than argued into this one,
same posture the AT-276 finding itself was given against AT-232.

```
VERDICT: PASS
SCOREBOARD: 6/6 verify items met (pytest subset, full suite, ruff, doctor, sabotage, real-corpus
regression), 0 contract criteria directly at issue (issue-driven unit, no numbered VL* criterion
claimed)
FAILURES (if any):
- none — AT-278 (new finding) does not fail this unit; see "Does AT-278 block this unit?" above
LIVE-BROWSER: not-applicable (src/autotester/stages/similarity_score.py, tests/test_similarity_score.py — no UI surface changed)
ISSUES-WRITTEN: AT-278 (high — AT-276's own STOPWORDS extension can strip a short bug report to
near-nothing, inflating similarity() to 1.0 for genuinely unrelated faults; does not block this PASS)
EXPLANATION: Every verify command, the sabotage confirmation, and the real-corpus regression check
reproduced independently and exactly as the manifest claimed, in an isolated extract. The unit's
scope is genuinely narrow (one source file, one new test file). The adversarial press beyond the
5 tested pairs found a real, more severe false-positive mode this fix introduces (score-ceiling
1.0 via near-total erosion of the shorter text), filed as AT-278 rather than failed here because
it is not within this unit's claimed or contracted scope and the manifest's own restraint (not
guessing the sixth word group) is independently vindicated by exactly this mechanism.
```
