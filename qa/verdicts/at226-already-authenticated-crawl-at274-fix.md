# Verdict — at226-already-authenticated-crawl-at274-fix

**Date:** 2026-09-09
**Cycle checked:** 1
**Contract:** qa/contracts/explore.md (login bootstrap, X10)
**Manifest:** qa/manifests/at226-already-authenticated-crawl-at274-fix.md
**Commit checked:** b48a871

## Scope

AT-274 only — the vacuous-assertion finding filed by the prior checker on
`qa/verdicts/at226-already-authenticated-crawl.md` (INDEPENDENT CONCURRENT CHECK, FAIL). Does
not re-litigate AT-226's own criteria (already settled by two prior checks).

## What I re-ran myself

- `uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py tests/test_explore_blocked.py -q`
  → `24 passed` (matches manifest).
- `uv run pytest` → `923 passed, 2 skipped` (matches manifest).
- `uv run ruff check src tests scripts` → `All checks passed!` (matches manifest).
- `uv run autotester doctor` → `doctor: clean` (matches manifest).
- `git show --stat b48a871` — confirmed the commit touches only `tests/crawl_fake.py` (+5) and
  `tests/test_explore_login_bypass.py` (+7); `src/autotester/stages/explore.py` is not in the
  diff. Live tree genuinely untouched, as claimed.

## Independent sabotage-confirm (own isolated extract)

`git archive 66e975a` into `D:/autoTesting/.work/checker-extract-at274/`, own `uv sync` venv
(separate from the main repo's `.venv`). Verified isolation before trusting anything:
`python -c "from autotester.stages import explore; print(explore.__file__)"` resolved to
`D:\autoTesting\.work\checker-extract-at274\src\autotester\stages\explore.py` — inside the
extract, not the main tree.

Baseline (unsabotaged): `uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py -q`
→ 22 passed.

Applied the exact same mutation the prior checker used — replaced `_already_past_login`'s body
with `return True` (anchor matched exactly once in
`src/autotester/stages/explore.py`). Re-ran the same two files:

```
.F....................                                                   [100%]
FAILED tests/test_explore_login_bypass.py::test_a_login_page_that_does_not_redirect_still_runs_the_case
assert (IDENTIFIER, "someone") in page.fills
E   assert ("input[name='identifier']", 'someone') in []
```

Exactly 1 failure, exactly the named test — every other test in both files stayed green. This
reproduces the manifest's claimed result independently, not by trusting the pasted output.

## Other sabotage direction — false-failure check on the legitimate path

Read `tests/test_explore_login_bypass.py` directly:
`test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated` (the genuine
already-authenticated skip) asserts only `crawl.status`/`stop_reason` — it never asserts
`page.fills`, so the strengthened assertion cannot fire a false failure on the legitimate skip
path; it isn't in scope there by construction. On the legitimate non-skipped path (the test the
fix targets), the baseline (unsabotaged) run above already showed the new
`assert (IDENTIFIER, "someone") in page.fills` passing — the FILL step's real side effect landed
as expected, with no floor effect introduced on the happy path.

## Judgment against AT-274's specific finding

The prior FAIL was: the test only asserted `crawl.status`, so it could not distinguish "the case
genuinely ran" from "the case was always-skipped by a regression." The fix adds `FakeSitePage.fills`
(mirroring the existing `.clicks` pattern) as a real side-effect record from `FakeLocator.fill`,
and asserts the exact `(selector, value)` pair the login case names. My own sabotage run confirms
this closes the gap precisely: the exact mutation that previously left all 22 tests green now
fails exactly the one test that should catch it, and only that one.

Live tree confirmed untouched — this is a test-infrastructure-only fix, no UI surface changed
(Mode D not applicable).

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (AT-274 closed), 0/0 invariants (none named for this narrow fix)
FAILURES (if any): none
LIVE-BROWSER: not-applicable (tests/crawl_fake.py, tests/test_explore_login_bypass.py — test infrastructure only, no UI surface changed)
ISSUES-WRITTEN: none (AT-274 closes; see ledger)
EXPLANATION: Independently re-ran the manifest's verify commands and reproduced them exactly. In my own isolated git-archive extract with its own venv (file identity verified before trusting results), the checker's exact sabotage mutation (_already_past_login -> return True) now fails exactly test_a_login_page_that_does_not_redirect_still_runs_the_case and nothing else, closing the gap the prior FAIL named. The legitimate already-authenticated skip path does not assert page.fills at all, so the strengthened assertion introduces no false failure there. src/autotester/stages/explore.py is confirmed untouched by commit b48a871 (diff shows only test files).
```
