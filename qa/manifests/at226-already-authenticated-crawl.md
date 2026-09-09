# Manifest — at226-already-authenticated-crawl

**Unit:** AT-226 — an already-authenticated session must not abort the crawl as `login_failed`
**Commit:** `2bb3270` (code — see "Same-file concurrent-commit collision" below) +
this manifest/test commit
**Fix cycle:** 1
**Dual check:** no
**Contract:** `qa/contracts/explore.md` (login bootstrap, X10)
**Goal task:** none — issue-driven
**Issues addressed:** AT-226

## What was wrong

FIRST REAL CRAWL OF A REAL PRODUCT (2026-09-09T02:59:45Z, `crawl_01M221PSNXXAT5ZRXSTE288JKA`
against `https://pathlynks.vidysea.com/signin`): the persistent Chromium profile already held a
live session, so `/signin` redirected to the dashboard. `run_crawl` ran the login case anyway,
`Locator.evaluate` waited the full 30s for `input[name="identifier"]` — a field that page will
never render — then reported `ERRORED`, and the whole crawl aborted `status=login_failed` with
**0 screens explored**, on a session that was already authenticated and able to proceed.

## What changed

- `src/autotester/stages/explore.py::_bootstrap_login` now finds the login case's own NAVIGATE
  step and checks (new helper `_already_past_login`) whether the browser lands somewhere other
  than that URL. If it does, the case is skipped and bootstrap reports success immediately —
  no wasted wait, no `ERRORED` outcome, no aborted crawl.
- `_already_past_login` compares URL **paths** (`urlparse(...).path`), not full strings, so query
  params or trailing slashes on the login URL do not create false negatives; a `goto`/`settle`
  exception (e.g. a real navigation failure) is treated as "not past login" rather than raised,
  so a genuine problem still falls through to running the case and failing normally.
- **Deliberately generic:** the check needs no app-specific "am I on the dashboard" marker — a
  login page that redirects away from itself has already done its job, on any product.
- A login case with no NAVIGATE step (or an already-past-login check that errors) falls back to
  running the case exactly as before — this is additive, not a new failure mode.

## Tests

- `tests/test_explore_login_bypass.py` (new):
  - `test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated` — the case's
    NAVIGATE target redirects to the app's base URL; the field it names is only "fillable" at the
    login URL in the fake site, so if the case actually ran, it would error. Asserts
    `CrawlStatus.COMPLETED` / `"frontier empty"` — the crawl proceeds.
  - `test_a_login_page_that_does_not_redirect_still_runs_the_case` — no redirect staged, the field
    IS fillable there, the case runs to completion normally (the happy path is unaffected).
  - `test_a_login_case_with_no_navigate_step_falls_back_to_running_it` — an empty-steps case still
    completes via the old path.
- `tests/crawl_fake.py` — `FakeSitePage.redirects` (url -> url the fake site "redirects" to on
  `goto`) and `FakeSitePage.fillable` (url -> selectors that exist there) plus
  `FakeLocator.fill`, which raises `TimeoutError` for a selector not registered at the current
  URL — mirrors a real Playwright locator timing out on a field that was never rendered.

## Sabotage

Reverted `_bootstrap_login` to call `run_case` unconditionally (the pre-fix behaviour), by direct
edit in place (never `git stash`/`checkout`, AT-101) and restored by copy afterward.

- **Before the fix: `test_a_redirect_away_from_the_login_page_is_treated_as_already_authenticated`
  FAILS**, reproducing AT-226 exactly: `crawl.status == LOGIN_FAILED`,
  `stop_reason == "login case did not complete"` — the FILL step raises `TimeoutError` on the
  page it redirected to, exactly as the real Pathlynks crawl did.
- After restoring: all 3 new tests + the full `test_explore.py` suite (22 tests) pass.

## Live browser evidence

Not run against a live browser this cycle — `explore.py` has no UI surface (no route, component,
page or template changed); D-024's browser-evidence requirement gates on changed UI paths, and
none changed here. The original AT-226 finding itself came from a real headless-Chromium crawl
against `pathlynks.vidysea.com` (cited above); this fix is verified against the deterministic
fake-site harness the rest of `test_explore.py` uses for the same class of behaviour.

## Same-file concurrent-commit collision (disclosed, not hidden)

A concurrent maker session was working AT-242 in this exact file at the same time. It committed
`2bb3270` ("fix(AT-242): a crawl that could act on nothing must not report completed") from its
own working tree snapshot — which, being the same live tree, also contained this unit's
already-edited `_bootstrap_login`/`_already_past_login` code, uncommitted at the time. `2bb3270`'s
diff and message name only AT-242; AT-226's code rode along inside it without being credited or
reviewed as its own change. Verified directly: `git show 2bb3270 -- src/autotester/stages/explore.py`
contains both `_terminal_status`/`BLOCKED_NO_ACTIONS` (AT-242, correctly attributed) and
`_already_past_login`/the NAVIGATE-redirect check (AT-226, this unit, not mentioned in that
commit's message). Nothing to revert — the code is correct and independently tested by this
unit's own suite — but the record needs the correction: **AT-226's fix shipped inside a commit
titled for a different issue.** This manifest and its own commit (tests + manifest) are what let
a checker find and verify AT-226's change on its own terms rather than as an uncredited rider.

## Concurrency note (AT-101)

A concurrent maker session is actively working AT-242 in this same file (`run_crawl` /
`_terminal_status`, `BLOCKED_NO_ACTIONS`) and in `tests/test_explore_blocked.py`
(uncommitted, one pre-existing unused-import ruff nit, not touched by this unit). Read but never
reverted; this manifest's own sabotage was applied and restored by direct in-place edit, never a
git operation, so it could not touch their uncommitted work. Full suite (923 passed / 2 skipped)
and `ruff check` on every file this unit touches are clean; `autotester doctor` is clean.

## How to verify

```
uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py -q   → 25 passed
uv run pytest                                                                → 923 passed, 2 skipped
uv run ruff check src/autotester/stages/explore.py tests/crawl_fake.py \
                   tests/test_explore_login_bypass.py                       → All checks passed!
uv run autotester doctor                                                    → doctor: clean
```

## Contract criteria requested (checker to author)

- A login case whose NAVIGATE target redirects elsewhere is skipped, not run to a timeout.
- A login case whose NAVIGATE target does NOT redirect still runs normally (no regression on the
  genuine-login-required path).
- The check is generic (URL-path comparison), not tied to any product's own "logged in" marker.
- A login case with no NAVIGATE step, or a `goto`/`settle` exception during the check, falls back
  to running the case exactly as before the fix.

## Status: checked-PASS (cycle 1 verdict f718273)

Checker independently re-ran the sabotage (in-place edit, AT-101), confirmed byte-clean restore,
verified the disclosed concurrent-commit collision is real (not a bypass) by reading `2bb3270`'s
diff directly, ran the full verify chain clean (923 passed / 2 skipped, ruff clean, doctor clean),
and confirmed X1/X10 contract invariants hold plus both fallback paths are non-vacuous. No new
issues opened. AT-226 closed.
