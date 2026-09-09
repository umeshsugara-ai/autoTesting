# Manifest — at278-min-distinctive-words-floor

**Unit:** AT-278 — AT-276's own STOPWORDS extension introduces a sharper false-positive mode
**Commit:** `7b5a167`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)
**Goal task:** none — issue-driven
**Issues addressed:** AT-278 (high)

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

- `src/autotester/stages/similarity_score.py` — new `MIN_DISTINCTIVE_WORDS = 2`. In `similarity()`,
  after computing the stopword-filtered word sets, if the **shorter** side has fewer than 2 distinct
  words remaining, return `0.0` — refuse to claim a match rather than let a near-empty denominator
  produce an artefact score.
- `tests/test_similarity_score.py` — four new tests: both AT-278 checker-constructed pairs now
  reject, a direct minimal case (`"Certificate upload fails"` vs `"Certificate renders correctly"`
  — exactly one shared word, must be `0.0` regardless of what that word is), and a genuine
  2-distinctive-word real match confirming the floor doesn't cost real short matches.

## How to verify (commands + expected)

- `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` → expected: exit 0, 41 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_similarity_score.py tests/test_score.py -v
[... 41 tests, all PASSED]

$ uv run pytest
942 passed, 2 skipped, 1 warning in 101.98s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), one mutation, restored immediately after:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted unit layered
onto the extract by hand, since it postdates HEAD — `similarity_score.__file__` verified inside
the extract, not the live tree). Removed the `MIN_DISTINCTIVE_WORDS` floor check entirely. Result:
**exactly 3 failures**, all three the floor guards, each landing at the predicted ceiling:

```
FAILED [export-corruption-vs-network-crash]: assert 1.0 < 0.3
FAILED [count-update-vs-photo-render]: assert 1.0 < 0.3
FAILED test_a_single_shared_word_is_never_evidence_of_a_match: assert 1.0 == 0.0
```

The other 10 tests in the file stayed green — confirming the floor is additive to AT-232/AT-276's
own mechanism, not a replacement.

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree confirmed
untouched (`grep -c MIN_DISTINCTIVE_WORDS` → 3, unchanged).

## Real-corpus regression check (measured, not argued)

Re-ran `scripts/score_video_issues.py` against the real `ERP_Issues_Trainers.xlsx`/`Trainer
module` sheet after the change. **Recall stays 3/7 (0.4286), unchanged** — the floor costs nothing
against the real matches AT-232/AT-276 already fixed; every one of them has well more than 2
distinctive words on its shorter side.

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

## Status: ready-for-check
