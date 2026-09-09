# Manifest — at276-stopwords-second-tranche

**Unit:** AT-276 — a second measured false-positive tranche in `similarity()`
**Commit:** `19247ae`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/video-learning.md` (T-136 acceptance)
**Goal task:** none — issue-driven
**Issues addressed:** AT-276 (high)

## What was wrong

> `similarity()` still false-positives on genuinely different bugs sharing common bug-report
> vocabulary not covered by the curated STOPWORDS list. Constructed 6 pairs of genuinely different
> faults (different screen, different root cause) sharing incidental bug-report phrasing outside
> the current 33-word STOPWORDS set: similarity scored 0.50–0.8571, all comfortably above the 0.30
> threshold.

Found by a checker during `at232-similarity-length-asymmetry`'s own review — exactly the shape
AT-232's own stress test found and closed for one vocabulary set, recurring in a different one.
The module's own docstring anticipates this: *"extend this list only on a measured false positive,
never by guess."*

## What changed

- `src/autotester/stages/similarity_score.py` — `STOPWORDS` extended with the demonstrated words
  from five of the six reported pairs (button/respond/clicked/twice/quickly, upload/fails/
  silently/exceeds, notification/badge/count/wrong/messages, search/results/update/filter/
  changed, export/import/downloads/corrupted/file/large). The sixth word group in the finding's
  evidence had no full sentence pair given, only word fragments — not added on guess, per the
  module's own discipline.
- `tests/test_similarity_score.py` (new) — nine tests: five parametrized false-positive pairs
  (the checker's own login/logout and notification examples verbatim, three constructed from its
  named word groups since no full sentences were given for those), the two real ERP-corpus
  matches AT-232 fixed re-asserted at their real text, AT-232's own original boilerplate case
  re-confirmed still rejecting, and a superset check that this edit only *adds* words.

## How to verify (commands + expected)

- `uv run pytest tests/test_similarity_score.py tests/test_score.py -v` → expected: exit 0, 37 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_similarity_score.py tests/test_score.py -v
[... 37 tests, all PASSED]

$ uv run pytest
938 passed, 2 skipped, 1 warning in 93.60s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), one mutation, restored immediately after:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted unit layered
onto the extract by hand, since it postdates HEAD — `similarity_score.__file__` verified inside
the extract, not the live tree). Removed the AT-276 word additions entirely, leaving AT-232's
original list. Result: **exactly the 5 parametrized false-positive tests fail**, each with the
exact predicted similarity value —

```
FAILED [login-vs-logout-button]
FAILED [badge-count-marking-vs-deleting]
FAILED [upload-fails-file-vs-video]
FAILED [search-filter-trainers-vs-applicants]
FAILED [export-vs-import-corrupted-file]:
  AssertionError: assert 0.7142857142857143 < 0.3
```

The other 4 tests (both real matches, the original boilerplate case, the superset check) stayed
green — confirming the extension is additive and doesn't touch anything else.

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree confirmed
untouched (`grep -c '"changed", "change",'` → 1, unchanged).

## Real-corpus regression check (measured, not argued)

Re-ran `scripts/score_video_issues.py` against the real `ERP_Issues_Trainers.xlsx`/`Trainer
module` sheet after the change. **Recall stays 3/7 (0.4286), unchanged** — the extension costs
nothing against the real matches AT-232 fixed.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/stages/similarity_score.py`,
`tests/test_similarity_score.py` (new). Pure function + tests.

## What this unit does not claim

- Does not claim STOPWORDS is now complete — the finding itself, and the module's own docstring,
  both predict this will recur in a third vocabulary set someday. That is the stated, disclosed
  cost of a curated list rather than a structural (e.g. corpus-relative) weighting scheme; a
  structural fix is a larger design question, not resolved here.
- Does not add the sixth word group from AT-276's evidence (a fragment with no full sentence
  pair given) — adding words on a guessed sentence would violate the module's own "never by
  guess" discipline. If that specific pair is ever measured for real, it becomes its own
  follow-up, the same way this unit was.

## Status: checked-PASS (cycle 1, verdict 4bf3327)
