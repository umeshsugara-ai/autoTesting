# Verdict — at232-similarity-length-asymmetry

**Cycle checked:** 1
**Date:** 2026-09-09
**Mode:** A (unit check)
**Contract:** qa/contracts/video-learning.md (T-136 acceptance)
**Manifest:** qa/manifests/at232-similarity-length-asymmetry.md
**Commit:** cc16284

## What I re-ran myself

- Isolated extract: `git archive cc16284` into `.work/checker-at232-extract`, own `uv sync`
  venv. Confirmed `autotester.stages.similarity_score.__file__` resolves inside the extract
  before trusting anything.
- `uv run pytest tests/test_score.py -v` → 28 passed (matches manifest).
- `uv run pytest -q` (full extract suite) → all dots, 2 skipped, 0 failed (matches manifest's
  "928 passed, 2 skipped").
- `uv run ruff check src tests scripts` → All checks passed.
- `uv run autotester doctor` → doctor: clean.
- **Sabotage 1** (revert `similarity()` entirely to `SequenceMatcher.ratio()`): exactly 2
  failures, opposite directions —
  `test_a_terse_report_of_a_verbose_humans_fault_is_a_match` (found=0, too low) and
  `test_boilerplate_bug_report_phrasing_does_not_falsely_match` (similarity 0.8156, too high).
  Matches manifest exactly. Restored by file copy; `grep -c STOPWORDS` confirmed unchanged on
  the live tree afterward.
- **Sabotage 2** (remove only the `STOPWORDS` filter, keep containment): exactly 1 failure,
  `test_boilerplate_bug_report_phrasing_does_not_falsely_match`, similarity
  **0.7692307692307693** — matches the manifest's predicted 0.7692 to the decimal. Restored by
  file copy; confirmed `tests/test_score.py -q` clean afterward (28 passed).
- **File split** (`git show --stat cc16284` on `score.py`): diff is exactly the extraction —
  `similarity()`'s body and `from difflib import SequenceMatcher` removed, replaced by
  `from autotester.stages.similarity_score import similarity`. No other line in `score.py`
  changed. Genuinely just an extraction, no behavior change beyond the fix itself.
- **AT-275 scoping**: `git show -s --format=%cI 791512f` = `2026-09-09T12:50:20+05:30`;
  `projects/erp/issues.jsonl` mtime = `2026-09-09 09:33:41` (predates it by ~3h17m, untracked
  file). The manifest's claim that this stale-derived-data issue is real and correctly out of
  scope for AT-232 is confirmed — it was already filed (AT-275, open, found_by maker-unit) before
  this check.
- **Real-corpus recall**: re-ran `uv run python scripts/score_video_issues.py --project erp
  --truth "C:/Users/Lenovo/Videos/Screen Recordings/ERP_Issues_Trainers.xlsx" --sheet "Trainer
  module"` myself on the live tree (not the extract, since it needs the real corpus + cached
  observations). Output: `"recall": 0.4286` (3/7), E-01 (0.538), E-02 (0.778), E-03 (0.667) all
  `"found": true` with the exact similarity values the manifest quotes, 3 `false_positive_titles`
  matching the AT-231-staleness explanation. Genuinely 3/7, not a pasted number.
- **UI-touching**: confirmed from the diff — changed paths are `score.py`,
  `similarity_score.py` (new), `tests/test_score.py`, `docs/MAP.md` (regenerated). No route,
  template, or component. Mode D not applicable.

## My own adversarial pair (went past the manifest's own stress test)

Constructed 6 pairs of genuinely different faults (different screen, different root cause) that
share only incidental bug-report vocabulary the current 33-word `STOPWORDS` list does not cover
(button/respond/clicked/quickly, upload/fails/silently/exceeds,
notification/badge/count/wrong/messages, search/results/update/filter,
export/import/downloads/uploads/corrupted/file/large). All 6 scored well above the 0.30
threshold: 0.50, 0.75, 0.50, 0.75, 0.75, 0.8571. Example: "Login button does not respond when
clicked twice quickly on mobile" vs "Logout button does not respond when clicked twice quickly
on desktop" (different actions, different platforms) = 0.75.

This is the same false-positive shape the manifest's own boilerplate stress test found and
closed — but only for the one vocabulary set it tested. It recurs immediately outside that set,
because `STOPWORDS` is a curated list tied to the example tested, not a general defense against
shared-genre phrasing. **This does not sink the unit**: the module's own docstring already
discloses "Known limitation... Extend this list only on a measured false positive, never by
guess," and the manifest itself states "Does not claim the STOPWORDS list is complete." My
finding is exactly the measured false positive that discipline anticipates, not a broken promise
— AT-232's stated scope was fixing the length-asymmetry false-negative and closing the ONE
false-positive risk it found before shipping, and it does both, sabotage-confirmed. Filed as
**AT-276 (high)** — a real, easily-triggered residual risk in the scorer that judges T-136's
north-star number, worth a follow-up decision, not a defect in what this unit claimed.

## Judgment

The manifest's every specific, checkable claim reproduced exactly: both sabotages, the exact
0.7692 predicted value, the file-split diff, the AT-275 mtime ordering, and the 3/7 real-corpus
recall with matching per-row similarities. No pasted output could not be reproduced. The false-
positive risk the manifest describes finding and closing (boilerplate vocabulary) is real and is
closed by the shipped STOPWORDS filter — confirmed by sabotage 2. My own adversarial probing
found a broader, undisclosed-in-scope-but-anticipated-in-docstring residual risk in the same
class, filed as its own issue rather than blocking this unit, consistent with how this contract's
amendment log treats measured residuals that don't contradict a stated criterion.

```
VERDICT: PASS
SCOREBOARD: 7/7 manifest claims independently reproduced, 0/0 contract criteria contradicted (no VL* criterion in video-learning.md governs similarity()'s own false-positive completeness)
FAILURES (if any):
- none
LIVE-BROWSER: not-applicable (src/autotester/stages/score.py, src/autotester/stages/similarity_score.py, tests/test_score.py, docs/MAP.md -- no UI surface changed)
ISSUES-WRITTEN: AT-276 (high, informational -- residual false-positive class outside the current STOPWORDS coverage, disclosed limitation, not a broken claim)
EXPLANATION: Every reproducible claim in the manifest reproduced exactly, including the precise 0.7692 sabotage value and the real-corpus 3/7 recall. The file split is a pure extraction. AT-275's scoping is correct by mtime measurement. My own adversarial pairs found a real, high-severity residual false-positive class the manifest's stopword fix does not close, but it is explicitly disclosed as an incomplete-list limitation in both the code and the manifest rather than claimed as solved, so it does not fail this unit -- filed as AT-276 for a future fix cycle.
```
