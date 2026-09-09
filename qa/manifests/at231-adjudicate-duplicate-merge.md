# Manifest — at231-adjudicate-duplicate-merge

**Contract:** qa/contracts/video-learning.md VL3/VL4
**Goal task:** none — issue-driven (AT-231)
**Date:** 2026-09-09
**Fix cycle:** 2 of 3
**Dual check:** no
**Issues addressed:** AT-231 (high), AT-269 (high — this cycle), AT-270 (low — this cycle)

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
BUG-SWEEP prompt's dedicated, more thorough description.

**Correction (cycle 2 — AT-269, filed by a checker, independently re-verified before writing this
paragraph).** The table below originally named the wrong pair: the `erp1.mp4` "Rule T3" pair,
with similarity figures (0.180/0.315) that I had approximated by hand rather than computed from
the real truth sheet — neither figure is reproducible, and that pair never crosses the scorer's
0.30 threshold against ANY truth row in any of the three states (pre-fix, naive-merge, shipped
fix). Its best truth match is `E-07` at similarity 0.234, well below threshold. **The real
mechanism, reproduced exactly by loading the actual cached observations and the actual
`ERP_Issues_Trainers.xlsx` sheet, is the `erp2.mp4` document-type pair, matched against `E-02`:**

| Prompt | Title | Similarity to `E-02` |
|---|---|---|
| `ingest_video_v1` (first-seen, kept by the naive fix) | "Incorrect document type option" | 0.247 (below the 0.30 threshold) |
| `video_issues_v1` (dedicated bug prompt) | "Document type dropdown option should be 'CITS Certificate' instead of 'CIPSA Certificate'" | 0.369 (above threshold — the ONE match) |

Keeping first-seen silently swapped the surviving title for the weaker one and turned a matched
finding into a missed one. Fixed by preferring the LONGER combined `title + what_is_wrong` on
merge — a blunt, deterministic, auditable proxy for "the prompt whose whole job is describing
this fault wrote more about it," consistent with this module's own stated preference for dumb,
auditable rules over a cleverer model-based tie-break.

**The lesson, stated plainly:** I asserted specific similarity figures for a specific pair without
loading the real truth sheet to compute them, and they looked precise enough (0.180/0.315,
straddling the 0.30 threshold) to read as measured fact. They were an approximation typed by hand
against a hand-typed approximation of the truth text, for the wrong pair entirely. The aggregate
headline numbers (6→3, 5→2, recall preserved at 1/7) were genuinely reproduced with the real
pipeline and remain correct; only the specific causal story was wrong, and it is the exact kind of
claim that must be re-derived, not pasted, before it goes in a manifest.

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

## Cycle 2 — fixing the checker's FAIL, not arguing it

**Verdict on cycle 1: FAIL, 1 of 6 pressure points.** The checker was right, and their own
methodology — independently reloading the real cached observations and the real truth sheet
rather than trusting the pasted table — is exactly what caught it. Two checkers ran concurrently on
cycle 1: one PASSed without re-deriving the specific evidence claim, the other FAILed after doing
so. Per the concurrent-verdict protocol the FAIL stands as this cycle's instruction, since it is
the one backed by independent re-derivation of the exact claim in question, not a disagreement on
the same evidence — the PASS verdict simply never checked that one paragraph.

**AT-269 (high) — fixed.** The manifest's causal table above now names the correct pair (`erp2`
document-type, matched against `E-02`, similarity 0.247 → 0.369) with figures I re-derived myself
before writing them, using the same method the checker used: load the real cached
`ModelObservation`s, load the real `ERP_Issues_Trainers.xlsx` sheet, and call `similarity()`
directly — no hand-typed approximation. Confirmed the `erp1` "Rule T3" pair never crosses threshold
against any truth row in any state, so it was never the mechanism.

**AT-270 (low) — fixed.** `_apply_merge`'s tie-break (`incoming_len > existing_len`, not `>=`) is
now stated explicitly in its docstring, with the structural reason the two real prompts are
unlikely to tie in practice (`ingest_video_v1` has no dedicated issues-writing instruction;
`video_issues_v1` does). A new test, `test_an_exact_length_tie_keeps_the_first_seen_text`, pins the
tie case directly; sabotage-confirmed (`>` → `>=` makes it fail exactly as predicted, restored
immediately after).

**What did not need fixing.** The code itself — `_same_model_duplicate`'s merge bound and the
length-preference rule — was confirmed correct and necessary by BOTH checkers, and the aggregate
headline numbers (6→3 issues, 5→2 false positives, recall preserved at 1/7) were independently
reproduced exactly by the FAIL checker using the real pipeline. Nothing in `adjudicate.py`'s
substantive logic changed this cycle; only the manifest's supporting narrative and one
now-documented-and-tested edge case.

### Re-verification (cycle 2)

```
$ uv run pytest tests/test_adjudicate.py -x
......................                                                   [100%]
22 passed in 0.09s

$ uv run pytest
917 passed, 2 skipped

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage (new, cycle 2):** reverted `_apply_merge`'s tie-break from `>` to `>=`, confirmed
`test_an_exact_length_tie_keeps_the_first_seen_text` fails with the exact predicted swap
(`BBBB` winning instead of `AAAA`); restored, all 22 `test_adjudicate.py` tests green again.

## Status: checked-PASS (cycle 2, verdicts 9611ada + aa66986, reconciled ab1f7fe)
