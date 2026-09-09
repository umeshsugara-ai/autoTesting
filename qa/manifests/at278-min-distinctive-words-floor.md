# Manifest — at278-min-distinctive-words-floor

**Unit:** AT-278 — AT-276's own STOPWORDS extension introduces a sharper false-positive mode
**Commit:** `cbdfab1`
**Fix cycle:** 2 of 3
**Dual check:** no
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)
**Goal task:** none — issue-driven
**Issues addressed:** AT-278, AT-279 (high)

## Why this is a structural fix, not a third STOPWORDS patch

This is the **second consecutive cycle** where extending `STOPWORDS` created a *new* false-positive
class rather than only closing the one it targeted:

- **AT-232**'s original stress test found and closed one boilerplate vocabulary set.
- **AT-276** closed a second, different vocabulary set — and in doing so, added *content-bearing*
  words (`export`, `downloads`, `corrupted`, `count`, `update`, `filter`, `message`...) whose
  removal can strip a short report down to almost nothing.
- **AT-278** (this unit): a checker pressed exactly that seam and found the mechanism —
  `containment = |shorter ∩ longer| / |shorter|` shrinks its denominator every time a shared word
  gets stopworded, without necessarily shrinking the numerator. Erode the shorter side down to one
  word and the ratio becomes 0.0 or 1.0 by construction — **never real evidence either way.**
  Measured: two genuinely unrelated pairs both hit **1.0**, worse than the 0.50–0.86 range AT-276
  itself was fixing.

Repeating the AT-232→AT-276 pattern a third time (add more words, close two instances, leave the
mechanism to produce a fourth) is exactly the instance-patching shape this repo's own AT-218
finding names as its top recurring risk. This unit closes the **mechanism** instead: a floor on
how few distinctive words a match may be built from.

## What changed

- Cycle 1 added a two-word shorter-side floor. The checker proved that boundary internally
  inconsistent: exact `Timeout` missed, while `Invoice rejected`/`Invoice approved` matched at 0.5.
- `src/autotester/stages/similarity_score.py::similarity` now gives exact normalized token content
  an explicit `1.0` path. Every non-identical pair must share at least two distinctive tokens before
  containment can score it at all; denominator size alone no longer licenses a one-token overlap.
- `tests/test_similarity_score.py` retains the AT-278 erosion cases and adds full `score()` regressions
  for the exact one-token positive plus both contradictory two-token negatives from AT-279.

## How to verify (commands + expected)

- `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` → expected: exit 0, 44 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_similarity_score.py tests/test_score.py -q
44 passed

$ uv run pytest
945 passed, 2 skipped, 1 warning

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Independent review before resubmission:** senior-software-engineer APPROVE and data-engineer
APPROVE. Both independently ran the 44 focused tests; the data review confirmed the new cases
exercise `score()` and recommended the deterministic exact-path + two-shared-token rule over an
embedding/LLM matcher. The cycle-2 checker is explicitly asked to perform the independent sabotage.

## Real-corpus regression check (measured, not argued)

Re-ran `scripts/score_video_issues.py` against the real `ERP_Issues_Trainers.xlsx`/`Trainer
module` sheet after cycle 2. **Recall stays 3/7 (0.4286), unchanged**, with 3 false positives and
complete 6/6 observation coverage.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/stages/similarity_score.py`,
`tests/test_similarity_score.py`. Pure function + tests.

## What this unit does not claim

- Does not claim the containment measure is now immune to every possible erosion case — a floor
  of 2 is a measured, defensible minimum (1 word is *definitionally* unfalsifiable; 2 admits real
  discrimination), not a proof that no smaller failure mode exists at higher word counts. If one is
  measured, it becomes its own follow-up, the same discipline this whole AT-232→276→278 chain has
  followed throughout.
- Does not touch `score()`'s matching logic, `window_s`, or the `threshold=0.30` default — only
  what `similarity()` refuses to score at all.

## Status: checked-PASS (cycle 2, verdict 44a7e84)
