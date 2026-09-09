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

---

## INDEPENDENT CONCURRENT CHECK

**Cycle checked:** 1
**Date:** 2026-09-09
**Checker:** fresh-context /checker, bound to D:/autoTesting (second, independent pass, no access
to the first checker's reasoning)

### Re-run evidence (executed by this checker independently)

- `git show 2bb3270 -- src/autotester/stages/explore.py`: re-read directly. Confirms both
  `_already_past_login` (AT-226, this unit, uncredited in that commit's message) and
  `_terminal_status`/`BLOCKED_NO_ACTIONS` (AT-242, correctly credited) are present, and they are
  **not entangled** — different functions, `_already_past_login` touches only `_bootstrap_login`'s
  early-return; `_terminal_status` touches only `run_crawl`'s final status computation. Neither
  reads nor writes state the other depends on. Manifest's disclosure is accurate.
- `uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py -q` → 22 passed (twice).
- `uv run pytest -q` (full suite): **first run showed 1 failure**
  (`test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated`,
  `LOGIN_FAILED` vs expected `COMPLETED`) — traced to this checker's own concurrent background
  pytest process racing the foreground run on Windows' shared `%TEMP%\pytest-of-<user>` tmp_path
  counter, **not a defect in the unit**. Stopped the background process; three consecutive clean
  full-suite reruns followed (all green). Recorded here per the re-run-yourself rule rather than
  silently discarded.
- `uv run ruff check src/autotester/stages/explore.py tests/crawl_fake.py tests/test_explore_login_bypass.py` → All checks passed.
- `uv run autotester doctor` → clean.
- `grep -n 'fill\|select_option\|upload' src/autotester/stages/explore*.py` → no calls, only
  docstring/reference text and one `_already_past_login`/`fill.py`-unrelated comment; X10 intact.
  `grep -n run_case src/autotester/stages/explore.py` → exactly one call site, inside
  `_bootstrap_login`.
- No route/template/component in the diff (`explore.py`, `tests/crawl_fake.py`,
  `tests/test_explore_login_bypass.py`, the manifest) — Mode D / live browser correctly
  not-applicable, confirmed from the changed paths directly, not from the manifest's claim.

### Independent sabotage, own isolated extract

`git archive HEAD` into a fresh scratch directory outside the repo, `uv sync` there, confirmed
`autotester.stages.explore.__file__` resolves inside the extract before trusting anything.

- **Direction (a) — break the redirect check so it never skips** (`_already_past_login` body
  replaced with `return False`): `test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated`
  FAILS exactly as AT-226's original defect — `CrawlStatus.LOGIN_FAILED`,
  `stop_reason == "login case did not complete"`. Matches the manifest and the prior verdict.
- **Direction (b) — break it so it always skips** (`_already_past_login` body replaced with
  `return True`, in a *second*, separately re-extracted copy so direction (a)'s edit could not
  leak into it): **all 22 tests in both files still pass**, including
  `test_a_login_page_that_does_not_redirect_still_runs_the_case` — the test the prior verdict
  cites as proof "the case still runs when no redirect occurs." It does not prove that. It only
  asserts the terminal `crawl.status`/`stop_reason`, and the fake site's post-skip and post-fill
  states are structurally identical for crawl purposes, so an always-skip regression is invisible
  to the suite.

### Disagreement with the first verdict (f718273)

The first verdict's "Vacuous-guard check" paragraph asserts C2 ("does not redirect still runs
normally") is MET and specifically claims the happy-path test "proves the case still runs" —
but never sabotage-confirmed *that* direction, only direction (a). Doing so here shows the claim
does not hold: the test cannot detect an always-skip regression. Filed as **AT-274** (severity:
medium — current code is correct on direct reading, this is a verification gap, not a live
defect: a future regression collapsing `_already_past_login` to `return True` would ship
undetected).

C1, C3, C4 independently re-verified and MET, consistent with the first verdict. The
concurrent-commit collision disclosure is independently confirmed accurate.

### Verdict

VERDICT: FAIL
SCOREBOARD: 3/4 criteria met, 2/2 invariants hold (X1, X10)
FAILURES:
- [C2] sev: medium · "login case does not redirect, still runs normally" is asserted by a test
  that cannot detect an always-skip regression (sabotage direction (b) passes all 22 tests) ·
  fix direction: assert the FILL step actually executed (e.g. via `FakeLocator`'s recorded state
  or `rt.store.save_result` being called for the login case), not only terminal `crawl.status` ·
  issue: AT-274
LIVE-BROWSER: not-applicable (src/autotester/stages/explore.py, tests/test_explore_login_bypass.py, tests/crawl_fake.py — no UI surface changed)
ISSUES-WRITTEN: AT-274
EXPLANATION: The redirect-skip fix itself is correct and independently sabotage-confirmed in
both directions in an isolated extract; the concurrent-commit collision is real but harmless and
accurately disclosed. The finding is narrower: the genuine-login-still-runs test the contract
relies on to close C2 is decorative against an always-skip regression, so C2 is not actually
evidenced. This disagrees with the first checker's PASS (f718273), which asserted the same test
proved the opposite without sabotage-testing that specific direction.
