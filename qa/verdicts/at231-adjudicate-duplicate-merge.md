# Verdict — at231-adjudicate-duplicate-merge

**Date:** 2026-09-09 · **Cycle checked:** 1 · **Bound to:** `d:/autoTesting`
**Commit checked:** `791512f` · **Contract:** `qa/contracts/video-learning.md` VL3/VL4

```
VERDICT: PASS
SCOREBOARD: 2/2 fixes evidenced, both sabotage-proven
FAILURES: none at >80% confidence
LIVE-BROWSER: not-applicable (changed paths: src/autotester/stages/adjudicate.py,
              tests/test_adjudicate.py — pure function, no route/template/component)
ISSUES-WRITTEN: none new
EXPLANATION: Both defects the manifest claims to fix are real, both fixes hold under sabotage I
ran myself in an isolated extract with its own venv, and the manifest's real-data numbers are
independently confirmed against the actual analysis.json files on disk — 3 recordings, 3 issues,
not 6, each models_agreeing=1, and the surviving title on the one true positive is the longer,
more specific wording the manifest predicted.
```

---

## What I re-ran myself

`uv run pytest tests/test_adjudicate.py -q` → **21 passed** · `uv run pytest` → **917 passed, 2
skipped** · `uv run ruff check src tests scripts` → clean · `uv run autotester doctor` → clean.

## The two sabotages, reproduced by me independently

Isolated extract: `git archive HEAD` into a scratchpad dir with its **own `uv sync` venv**
(verified `adjudicate.__file__` resolves inside the extract before trusting anything). Both
restored by overwriting with a saved copy, never `git checkout` (AT-101).

| # | Mutation | My result | Manifest claimed |
|---|---|---|---|
| 1 | `join_issues`'s merge condition: `cross_model_match or _same_model_duplicate(...)` → `cross_model_match` alone | **3 failures**, exact names: `test_the_SAME_model_reporting_the_same_fault_under_two_prompts_merges`, `test_the_merge_does_not_count_as_cross_model_agreement`, `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen` | same 3 |
| 2 | Removed the length-preference block from `_apply_merge` (first-seen wins again) | **1 failure**, `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen`, with the exact predicted swap: `- ...blocks moving trainer to next stage` / `+ ...prevents stage transition` | same, same swap |

Both anchors matched exactly once in my own run; both restorations confirmed by a clean re-run of
the full `test_adjudicate.py` suite. Live tree confirmed untouched throughout
(`git status --porcelain` empty on the two changed paths before and after).

## The real-data claim, checked against the actual files, not the pasted table

I read `projects/erp/sources/*/analysis.json` directly rather than trusting the manifest's table:

| Source | Issues | `models_agreeing` |
|---|---|---|
| `src_688a991f33ad` | 1 — "Document type dropdown option should be 'CITS Certificate'..." | 1 |
| `src_a6d5d1b66aa0` | 1 — "Rule T3 validation error blocks moving trainer to next stage" | 1 |
| `src_c6bb964cfff8` | 1 — "Home Location field presents training centers instead of personal loca..." | 1 |

**3 recordings, 3 issues** — matches the manifest's "6 → 3" claim exactly, and every
`models_agreeing` is correctly 1 (a model repeating itself under two prompts is not cross-model
agreement, which is the whole point of the fix). The T3 issue's surviving title is the **longer**
wording ("blocks moving trainer to next stage"), which is the one the manifest says scores 0.315
against the human sheet — above the 0.30 threshold, the one true positive. Had the shorter,
first-seen title survived instead, that match would have been lost, exactly as the manifest's
own "recall dropped from 1/7 to 0/7" mid-fix discovery describes.

## What this unit does not claim, and I do not certify beyond it

- **Not the recall number.** 1/7 with 2 false positives (down from 5) is still a bad number.
  AT-232 (the similarity threshold under-counting real matches) is explicitly untouched and stays
  open — this fix removed false positives, it did not add a missed true positive.
- **Not the committed analysis.json files.** The manifest states plainly they were regenerated as
  a side effect of proving the fix and are deliberately excluded from this commit, left for a
  human/maker decision on whether real project data belongs in a public repo. I did not check
  whether that data is currently git-tracked, which is outside this unit's stated scope.

## Ledger

`AT-231` → **verified**. No new issues — the manifest's own self-discovered second bug (the
sort-key/first-seen title regression) was fixed within this same cycle, before submission, and I
found no further defect in re-deriving both fixes independently.
