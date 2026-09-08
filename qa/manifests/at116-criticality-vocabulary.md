# Manifest — at116-criticality-vocabulary
**Contract:** `qa/contracts/core-invariants.md` C6 (artifacts are human-editable files, and the
system still loads them) — this is the inverse failure: a human-editable field that loaded fine
and was silently ignored. No feature contract governs `.goal/goal.json`'s vocabulary; **that gap
is part of the finding** and is filed for the checker to rule on.
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** **AT-116** (high — found by the T-124 cycle-2 checker)

## The defect
The shared classifier (`goal/scripts/criticality.py`) orders criticality off
`_ORDER = {"low", "medium", "high", "critical"}` and its `base_criticality()` ends
`return b if b in _ORDER else "low"` — a **case-sensitive** membership test with a silent
fallback. This project's `.goal/goal.json` has written `"HIGH"`, `"CRITICAL"`, `"MEDIUM"`,
`"LOW"` and a fifth value `"NORMAL"` since the file was created.

So every task's declared floor has been discarded since day one. Nothing errored; the field simply
never did anything. **41 of 44 rows derived `low`** — the only three that did not got there via
`classify()`'s side-effect keyword rules, bypassing `base_criticality` entirely.

**How it surfaced, which is the part worth keeping:** I "fixed" T-145's criticality two units ago
by setting `base_criticality: "CRITICAL"`, wrote it up as done, and it changed nothing. The
checker executed `classify(T-145)` rather than reading my diff, got `low`, and filed this.

## What `"NORMAL"` meant, and why it maps to `low`
`"NORMAL"` has no equivalent in the classifier's vocabulary at all — it is not a case variant, it
is a fifth value. Checked all 12 rows carrying it: **11 also carry `user_value: normal`**. It was
never a risk level; it meant "no elevated floor", which is exactly `low`. The one exception
(T-125, `user_value: high`) is a value judgement about worth, not risk, so it maps the same way.

## What changed
- `.goal/goal.json` — 45 tasks normalised: `LOW/MEDIUM/HIGH/CRITICAL → lowercase`, `NORMAL → low`.
  Derived `criticality` refreshed via `monitor.py`.
- **New** `tests/test_goal_criticality_vocabulary.py` — two tests. The vocabulary conformance
  check, and the consequence check (T-145 and T-154 must derive `critical`). It duplicates the
  classifier's four-value set with a comment naming the source rather than importing it, because
  `criticality.py` is a shared AIOS skill **outside this repo** and this project's suite must not
  depend on a path it does not own.

## The result — pending work, which is what matters
| Derived | Pending tasks |
|---|---|
| `critical` | 4 — **T-145** (live production ERP crawl), **T-154** (adversarial pass), T-122, T-135 |
| `high` | 6 |
| `low` | 7 |

`critical` means a **dual check**: two blind checkers, both must PASS. T-145 and T-154 are the two
highest outward-facing risks in the backlog and were both getting a single checker.

## Two things I got wrong, corrected here rather than quietly dropped
1. **My pre-build simulation predicted `12 low / 7 medium / 18 high / 8 critical`. The real result
   is `33 low / 6 high / 5 critical`.** I ran `classify()` uniformly over all 45 tasks; `monitor.py`
   leaves **completed** work at `low` (26 of 27 done tasks), which is correct — a finished task
   carries no forward risk. My simulation was over-counting by escalating history.
2. **T-135 derives `critical` from `base_criticality: low`.** Not my mapping — `classify()`
   escalates on side-effect keywords, and T-135's title contains *"merge"* (FlowSpec merge, not a
   git merge or a deploy). It is a keyword false positive. Left as-is deliberately: it fails
   **safe** (an extra dual check costs a checker, a missed one costs a production incident), and
   suppressing it would mean editing the shared classifier from inside one project. Flagged for
   the checker to rule on rather than silently tuned.

## Sabotage
```
$ SABOTAGE: uppercase vocabulary restored, derived reset to low
FAILED test_every_base_criticality_is_a_value_the_classifier_recognises
FAILED test_the_highest_risk_pending_work_actually_derives_critical
2 failed in 0.13s
$ RESTORE
2 passed
```

## How to verify (commands + expected)
**Docker is down; the project runs natively.** `cd "D:/autoTesting" && uv run …`
- `uv run pytest -q` → **586 passed, 2 skipped** (584 before; the 2 skips are the POSIX-only
  permissions test and the live-Mongo opt-in, both expected on Windows)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- Worth doing yourself: execute `classify()` from
  `D:/ai_os/.claude/skills/goal/scripts/criticality.py` against the live `goal.json` and confirm
  T-145 and T-154 return `critical` — **do not** read the JSON field, compute it.

## What this does NOT fix, deliberately
`criticality.py` still fails **silently** on an unrecognised value — the next project to write
`"HIGH"` will hit exactly this, and this test only guards *this* repo's data. Making the shared
classifier reject unknown values instead of downgrading them is the real fix, and it belongs in
`D:/ai_os`, outside this project's root. Not done from inside a session bound here.

## Status: checked-PASS
