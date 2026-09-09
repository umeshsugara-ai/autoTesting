# Manifest — at231-adjudicate-duplicate-merge

**Contract:** qa/contracts/video-learning.md VL3/VL4
**Goal task:** none — issue-driven (AT-231)
**Date:** 2026-09-09
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-231 (high)

## What changed

- `src/autotester/stages/adjudicate.py`:
  - New `_same_model_duplicate(existing, label, issue)` — the SAME provider's second report,
    same category, within `SEAM_WINDOW_S`, merges even when the screen name differs.
  - `join_issues` now merges on `cross_model_match OR _same_model_duplicate` (was
    `cross_model_match` alone).
  - New `_apply_merge(existing, label, issue)` — extracted from `join_issues`'s body so the
    function stays under the 50-line cap; also fixes a second, subtler bug found while proving
    the first one on real data (see below): **the LONGER of the two titles/`what_is_wrong`
    strings now survives a merge, not the first-seen one.**
- `tests/test_adjudicate.py` — four new tests: the exact duplicate shape from the first real
  reading merges; the merge does not falsely count as cross-model agreement; a genuinely
  different model on a mismatched screen still does NOT merge (the negative case); and the
  longer, more specific wording survives the merge rather than whichever text happened to sort
  first.

## Why (AT-231, filed by maker-live-run against the FIRST real model reading)

Every recording is analysed under two prompts per provider — `ingest_video_v1` (maps the
product) and `video_issues_v1` (the dedicated bug-sweep). Both prompts can independently notice
the same fault on the same screen, described in slightly different words. `join_issues` merged
strictly on `(screen_key, category)` — but a model's own read of a screen name is exactly as
unreliable across its own two prompts as it is across two chunks (the reason `screen_key` never
keys on the URL in the first place), so the two reports of ONE fault kept their own, slightly
different screen names and never matched. The result on the first real ERP reading: **3 genuine
faults reported as 6**, and the ensemble's own founding premise — *agreement raises confidence*
— was inverted into *agreement doubles the noise*.

## A second bug found only by proving the first one against real data

Fixing the merge alone (first cycle of this fix, not committed separately) made the duplicate
issues collapse from 6 to 3 correctly — but re-scoring against the human ground-truth sheet
showed **recall dropped from 1/7 to 0/7**. The cause: `adjudicate`'s own sort key orders
`ingest_video_v1` before `video_issues_v1` alphabetically, so the merge always kept the FIRST
observation's title — the MAPPING prompt's terse, incidental note about the fault, not the
BUG-SWEEP prompt's dedicated, more thorough description. On the real `erp1.mp4` pair:

| Prompt | Title | Similarity to human sheet |
|---|---|---|
| `ingest_video_v1` (first-seen, kept by the naive fix) | "Rule T3 validation error prevents stage transition" | 0.180 (below the 0.30 threshold) |
| `video_issues_v1` (dedicated bug prompt) | "Rule T3 validation error blocks moving trainer to next stage" | 0.315 (above threshold, previously the ONE match) |

Keeping first-seen silently swapped the surviving title for the weaker one and turned a matched
finding into a missed one. Fixed by preferring the LONGER combined `title + what_is_wrong` on
merge — a blunt, deterministic, auditable proxy for "the prompt whose whole job is describing
this fault wrote more about it," consistent with this module's own stated preference for dumb,
auditable rules over a cleverer model-based tie-break.

## How to verify (commands + expected)

- `uv run pytest tests/test_adjudicate.py -x` → expected: exit 0, all pass (21 tests)
- `uv run pytest` → expected: exit 0, `917 passed, 2 skipped`
- `uv run ruff check src tests scripts` → expected: exit 0, "All checks passed!"
- `uv run autotester doctor` → expected: exit 0, "doctor: clean"

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_adjudicate.py -x
.....................                                                    [100%]
21 passed in 0.04s

$ uv run pytest
917 passed, 2 skipped, 1 warning in 87.65s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), two independent mutations, each restored immediately after:**

1. Reverted `join_issues`' merge condition from `cross_model_match or _same_model_duplicate(...)`
   back to `cross_model_match` alone → the three tests written for this exact behaviour fail
   (`test_the_SAME_model_...`, `test_the_merge_does_not_count_...`, `test_the_LONGER_wording_...`).
2. Removed the length-preference block from `_apply_merge`, leaving first-seen-wins →
   `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen` fails with exactly
   the predicted swap (`+ Rule T3 validation error prevents stage transition` /
   `- ... blocks moving trainer to next stage`).

Both anchors matched exactly once, both files were confirmed changed, both restored to the
committed content, full `test_adjudicate.py` re-confirmed green after each restore.

**Measured real-world impact (adjudicate is pure — re-running it against the three ERP
recordings' already-cached observations cost zero new model calls):**

| | Before this fix | After this fix |
|---|---|---|
| Issues reported (3 recordings) | 6 | 3 |
| Recall vs `ERP_Issues_Trainers.xlsx` | 1/7 (0.1429) | 1/7 (0.1429) — preserved |
| False positives | 5 | 2 |

The three duplicate pairs collapsed to exactly the three distinct faults, `models_agreeing`
correctly stayed at 1 for each (a model repeating itself under two prompts is not two models
agreeing), and the one true positive already found stayed found — the length-preference fix is
what kept it from being lost. This real-project data (`projects/erp/sources/*/analysis.json`)
was regenerated as a side effect of proving the fix and is **not** part of this commit; only the
library code and its unit tests are — the analysis files are separately-scoped real project
state, not manifest evidence artifacts, and are left for a maker/human decision on whether/when
that data is committed to the (public) repo.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/stages/adjudicate.py`,
`tests/test_adjudicate.py`. No route, template, component, or rendered output.

## Status: ready-for-check
