# Manifest — at232-similarity-length-asymmetry

**Unit:** AT-232 — the 0.30 similarity threshold under-counts real matches (length asymmetry)
**Commit:** `cc16284`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)
**Goal task:** none — issue-driven, but directly unblocks T-136's own real recall number
**Issues addressed:** AT-232 (high)

## What was wrong

> The 0.30 SequenceMatcher threshold under-counts real matches because the human writes 200 words
> and the model writes 20 — length asymmetry crushes the ratio... E-03 vs our erp3 issue: SAME
> recording, 2s apart, semantically the same fault — scored a MISS. Reported recall 1/7 = 0.143;
> by reading, at least 2 of 7 are genuinely found.

`similarity()` used `SequenceMatcher(None, left, right).ratio()`, which is length-symmetric: it
punishes the shorter side for brevity regardless of content overlap. Verified on the real corpus
before touching anything: `similarity(E-03.text, erp3_issue_text)` under the old measure = **0.023**
— a genuine finding, reported as a miss.

## What changed

- New `src/autotester/stages/similarity_score.py` (extracted from `score.py`, which crossed the
  300-line cap adding this): `similarity()` now computes **containment over stopword-filtered word
  sets** — what fraction of the shorter text's distinct (non-stopword) words also appear in the
  longer text. Brevity is no longer penalised; a terse, accurate report scores as well as a
  verbose one covering the same fault.
- `STOPWORDS`: a curated, in-file, documented constant — the bug-report boilerplate two
  *unrelated* faults share by accident of genre ("field", "error", "validation", "prevents",
  "form", "screen", "edit"), stripped so containment measures distinctive content only.
- `tests/test_score.py` — two new tests, self-contained (no real corpus needed):
  `test_a_terse_report_of_a_verbose_humans_fault_is_a_match` (reproduces the real asymmetric-length
  case) and `test_boilerplate_bug_report_phrasing_does_not_falsely_match` (the false-positive
  stress case I found while validating the fix, not something the original finding named).

## A false-positive risk found and closed before shipping, not after

Pure containment (no stopword filter) was my first candidate. Before committing to it I stress-
tested it against two **genuinely different** bugs sharing only generic phrasing ("field validation
error prevents form submission on the ... screen") — it scored **0.77**, comfortably above
threshold. That would have traded one false-negative class (crushed-by-length) for a false-positive
class (matched-by-boilerplate), which is not a fix, it's a different bug. The stopword filter
closes this; both cases are now dedicated tests, not just a fixed anecdote.

## How to verify (commands + expected)

- `uv run pytest tests/test_score.py -v` → expected: exit 0, 28 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_score.py -v
[... 28 tests, all PASSED]

$ uv run pytest
928 passed, 2 skipped, 1 warning in 98.62s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), two mutations, restored immediately after each:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted unit layered
onto the extract by hand, since it postdates HEAD — `similarity_score.__file__` verified inside
the extract, not the live tree).

1. **Reverted to `SequenceMatcher.ratio()` entirely.** **Exactly 2 failures**, both new tests, in
   **opposite directions** — proving the old measure fails both ways this fix cares about:
   - `test_a_terse_report_...`: `similarity=0.0...` far below threshold (too low — the original bug)
   - `test_boilerplate_...`: `similarity=0.8156` — the two DIFFERENT bugs falsely matched (too high
     — SequenceMatcher on two short, similarly-shaped sentences happens to match structure closely)
2. **Removed only the `STOPWORDS` filter, kept containment.** **Exactly 1 failure**,
   `test_boilerplate_bug_report_phrasing_does_not_falsely_match`, similarity **0.7692** — the exact
   number from my own pre-commit stress test, confirming the stopword filter is load-bearing, not
   decorative.

Both restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree
confirmed untouched after each (`grep -c STOPWORDS` unchanged).

## Real-corpus validation (measured, not argued)

Re-ran `scripts/score_video_issues.py` against the real `ERP_Issues_Trainers.xlsx`/`Trainer
module` sheet, using the already-cached observations (zero new model calls):

| | Before this fix | After this fix |
|---|---|---|
| Recall | 1/7 (0.1429) | **3/7 (0.4286)** |
| E-01 (Rule T3) | missed | found, similarity 0.538 |
| E-02 (Document type) | found (0.37, barely over floor) | found, similarity 0.778 |
| E-03 (Home location) | **missed** (0.023, the finding's own example) | **found, similarity 0.667** |

**A separate, pre-existing issue found during this validation, NOT this unit's scope:** the run
still shows 3 residual false positives — but `projects/erp/issues.jsonl` (mtime 09:33 IST) predates
the AT-231 duplicate-merge fix (landed 12:50 IST). Each of the 3 recordings still carries 2 reported
issue rows from before that merge, not 1. Regenerating this derived data costs zero model calls
(per AT-231's own manifest) and would very likely clear these false positives — but that is
housekeeping over a separate module's output, not a defect in `similarity()`, and I did not fold it
into this unit's diff. Filed as its own follow-up finding (AT-275) rather than silently
absorbed.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/stages/score.py`,
`src/autotester/stages/similarity_score.py` (new), `tests/test_score.py`, `docs/MAP.md`
(regenerated, not hand-edited, per `autotester map`). No route, template, component, or rendered
output.

## What this unit does not claim

- Does not regenerate `projects/erp/issues.jsonl` — a separate, disclosed, zero-cost housekeeping
  action left for a maker/human decision, exactly as AT-231's own manifest already deferred it.
- Does not change `score()`'s matching logic, `window_s`, or the `threshold=0.30` default — only
  what `similarity()` measures. All existing `test_score.py` assertions pass unchanged.
- Does not claim the STOPWORDS list is complete — its own docstring states the limitation plainly
  and says to extend it only on a measured false positive, never by guess.

## Status: checked-PASS (cycle 1, verdict e660b45)
