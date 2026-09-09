# Verdict — at226-already-authenticated-crawl

**Cycle checked:** 1
**Date:** 2026-09-09
**Checker:** fresh-context /checker, bound to D:/autoTesting

## Re-run evidence (all executed by the checker, not pasted)

- `uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py -v` → 22 passed
  (3 new bypass tests + 19 existing explore tests; manifest's "25" figure is off by 3 but
  immaterial — no test is missing or skipped).
- `uv run pytest -q` (full suite) → all green, 2 skipped, no failures.
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean.
- **Sabotage re-executed independently** (direct in-place edit, restored by direct in-place
  edit — no git stash/checkout, per AT-101): removed the `_already_past_login` guard so
  `_bootstrap_login` calls `run_case` unconditionally. Result:
  `test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated` FAILS with
  `CrawlStatus.LOGIN_FAILED`, `stop_reason == "login case did not complete"`, `screens=0` —
  exactly the AT-226 shape claimed. Restored; `git diff --stat` on `explore.py` shows no diff
  and the full suite (22/22 on the two test files) is green again.
- **Concurrent-commit collision independently verified:** `git show 2bb3270 -- src/autotester/stages/explore.py`
  does contain both `_already_past_login`/the NAVIGATE-redirect check (this unit, AT-226) and
  `_terminal_status`/`BLOCKED_NO_ACTIONS` (AT-242, correctly named in that commit's message).
  The manifest's disclosure is accurate — not an undisclosed bypass. The code under judgment is
  present and correct on current HEAD regardless of which commit message credits it.
- **Contract check (X1, X10):** `grep -n run_case src/autotester/stages/explore.py` shows exactly
  one call site, inside `_bootstrap_login`. `grep -n 'fill|select_option|upload' explore*.py`
  returns nothing — X10 intact. `urlparse` is imported and used for path-only comparison as
  claimed (no false negatives from query/trailing-slash).
- **Vacuous-guard check:** the fallback paths (no NAVIGATE step; a `goto`/`settle` exception
  during the check) fall through to `run_case` unconditionally — verified by reading the code
  and by the passing `test_a_login_case_with_no_navigate_step_falls_back_to_running_it`. Not a
  guard that always evaluates true — the happy-path test
  (`test_a_login_page_that_does_not_redirect_still_runs_the_case`) proves the case still runs
  when no redirect occurs.
- **Live browser:** not applicable — no UI/route/component/template path changed in this diff
  (D-024 gates on changed UI paths); correctly disclosed in the manifest.

## Criteria (checker-authored, from the manifest's request)

- [C1] Login case whose NAVIGATE target redirects elsewhere is skipped, not run to timeout — MET.
- [C2] Login case whose NAVIGATE target does not redirect still runs normally — MET.
- [C3] Check is generic (URL-path comparison, no product-specific marker) — MET.
- [C4] No NAVIGATE step, or a goto/settle exception, falls back to running the case as before — MET.

## Verdict

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, contract invariants X1/X10 hold
FAILURES: none
LIVE-BROWSER: not-applicable (src/autotester/stages/explore.py, tests/test_explore_login_bypass.py, tests/crawl_fake.py — no UI surface changed)
ISSUES-WRITTEN: none (AT-226 closed by this unit)
EXPLANATION: The fix correctly checks the login case's own NAVIGATE target after navigating, treats a
path mismatch as already-authenticated, and skips the case instead of running it to a guaranteed
timeout. Sabotage reproduces the exact AT-226 failure shape independently. The concurrent-commit
collision (code landed in 2bb3270, credited to AT-242's message) is accurately disclosed and
verified — not a bypass. Full verify chain is clean.
