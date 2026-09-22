# Verdict — at540-assertion-layer

**Date:** 2026-09-22 · **Checker:** /checker Mode A, fresh subagent (claude-sonnet) · **Bound root:** D:/autoTesting
**Cycle checked: 2** (manifest Fix cycle: 2 of max 3) · **Dual check:** no (single check)

> **Landing note (orchestrator).** This verdict was rendered by the fresh cycle-2 checker subagent
> `a6b0b72c1083333ae` (full Mode A, all evidence independently re-derived). The checker was blocked
> by a plan-mode restriction before it could write this file or push, so it handed back the verbatim
> block below. The orchestrator transcribes it here — this is the checker's judgment, not a maker
> self-PASS (QA-1445 / stranded-verdict recovery class; cf. b7ffb27, 00e36a8). The checker's own
> ledger + contract fold-in already landed in `bbd030d`.

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (E1-E5), 1/1 applicable invariant holds (C7)
FAILURES: none
CAPABILITY-COVERAGE: 10/11 rows reproduced (rows 1,2,4,5,8,9 unchanged since cycle 1 and still green;
  rows 3,6,7 independently re-falsified by this checker in a throwaway copy — edit -> named test
  reddens for the named reason -> revert -> green again; row 10/AT-551 fail-safe also independently
  re-falsified the same way) | 1 disclosed, non-blocking gap: row 11 (url-probe defensive fix) has
  no isolating test — low severity, honestly disclosed by the manifest, judged as debt, not a fail
LIVE-BROWSER: not-applicable (changed paths: src/autotester/browser/assertions.py,
  tests/test_execute.py, tests/test_execute_assertions.py, tests/test_grade.py — no UI surface of the
  app itself)
ISSUES-WRITTEN: AT-553 (new, ledger-integrity, high); flipped open->fixed: AT-547, AT-548, AT-549,
  AT-550, AT-552 (this unit's own cycle-1 duplicate rows) and AT-551 (the sweep's fail-open duplicate row)
EXECUTOR: claude-sonnet-subagent (manifest carries no Executor: line; checker: claude-sonnet-subagent,
  self != any external executor)
EXPLANATION: All three cycle-1 FAIL causes are closed and independently re-verified outside the bound
  tree. Full suite 1528 passed / 5 skipped / 32 xfailed / 0 failed, exit 0, 735s (+7 over the prior
  1521 baseline, exactly matching net new/restored tests). ruff clean. doctor was red from a stranded
  pre-existing amendment (not this unit's diff) and is now clean after a scoped fix. Diff scope
  confirmed exact to the manifest's 5 files. A real ledger-ID-collision defect was found and resolved
  during reconciliation.
```

## What the checker independently re-ran (not trusted from the manifest)

- `PYTHONUTF8=1 uv run pytest tests/test_execute.py tests/test_execute_assertions.py tests/test_grade.py` → 30 passed
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → was `architecture-too-long: 152 > 150`; fixed by the checker (wording-only
  trim of the D-032-authorized note, 3 lines → 1, meaning unchanged) → now `doctor: clean`
- **Full suite** (bare `uv run pytest`, no `-q`, per AT-503/C7): **1528 passed, 5 skipped, 32 xfailed,
  exit 0, 735.30s.** Whole-log scan for `FAILED`/`ERROR`/`^E ` found nothing — no AT-505/AT-518 flake.
- `git show d7d8405 --stat` → fix commit touches exactly the 5 files the manifest names, nothing else.
- The 3 restored E3/AT-341 tests collected and passing individually; `tests/test_execute.py` = 300/300.

## Capability-coverage rows the checker personally falsified (throwaway copy, bound tree never touched)

Copied the working tree (excluding `.git`/`.venv`), green baseline first (30 passed), then per row:
single-hunk edit → named test reddens for the named reason → revert → green; edited files confirmed
byte-identical to the bound tree afterward.

- **Row 3 (AT-548, dom_asserts):** `assertions.py` `found = selector_exists(...)` → `found = True`.
  `test_dom_asserts_is_unmet_when_the_selector_is_absent` FAILED (`COMPLETED` vs `ASSERTION_FAILED`). Reverted → green.
- **Row 6 (AT-550, ERRORED precedence):** except-branch returns ASSERTION_FAILED before the ERRORED return.
  `test_errored_still_beats_assertion_failed` FAILED (`ASSERTION_FAILED` vs `ERRORED`). Reverted → green.
- **Row 7 (AT-549, C7):** `grade.py::_outcome_verdict` ASSERTION_FAILED short-circuit added.
  `test_assertion_failed_run_still_reaches_the_judge...` FAILED (judge never called). Reverted → green.
- **Row 10 (AT-551, fail-safe):** `body_text()` `except: return None` → `return ""` (pre-fix behaviour).
  `test_absent_text_on_an_unreadable_page_fails_safe_not_silently_met` FAILED (`COMPLETED` vs `ASSERTION_FAILED`).
  Reverted → green (the exact fail-open bug the fix closes).

## Ledger reconciliation (separate governance defect found + resolved)

`qa/issues.jsonl` carried **six duplicate ids** (AT-547..AT-552 each twice, unrelated content) — a
Mode-B sharded sweep and this unit's cycle-1 checker both allocated ids from the same next-free number
with no coordination. Resolved **by content, not blind id-match**: flipped open→fixed this unit's own
cycle-1 rows (AT-547/548/549/550/552) + the sweep's real fail-open AT-551; left the cycle-1 checker's
*other* AT-551 (BOM/mojibake, still present, untouched by this diff) and every other sweep row open.
Filed **AT-553** (ledger-integrity, high) documenting the collision pattern + a coordinated-allocation
recommendation. The reconciliation + the D-032 E1 contract fold-in committed narrow in `bbd030d`.
