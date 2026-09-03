# Manifest — at036-screenshot-retry

**Contract:** qa/contracts/browser-and-secrets.md (B7 — screenshot masking; this fix doesn't
change what's masked, only makes capture itself resilient)
**Goal task:** none (`.goal/goal.json` is 20/20 done — issue fix)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-036

## Why this unit

AT-036 (filed in the previous unit): under Xvfb, `Page.screenshot` intermittently raised a CDP
protocol error ("Unable to capture screenshot") on the login case's post-click screenshot,
never on the simpler navigate-only homepage case. The fix direction named in the issue was:
retry once on this specific transient error, or a short wait before the post-click screenshot.

## What changed

`src/autotester/browser/session.py::BrowserSession.screenshot` — wraps the capture call in a
try/except that catches ONLY the exact known transient error (checks `"captureScreenshot" in
str(exc)`), waits 250ms, and retries exactly once. Any other exception, or a second consecutive
failure of the same kind, propagates unchanged — this never masks a real failure, it only
absorbs the one specific known-transient race.

`tests/test_browser.py` — 3 new tests:
- `test_screenshot_retries_once_on_the_known_transient_protocol_error` — a fake page that fails
  once with the exact error string then succeeds; asserts the screenshot still lands and exactly
  one 250ms wait happened.
- `test_screenshot_gives_up_after_a_second_consecutive_failure` — a fake page that fails twice;
  asserts the exception propagates (not silently swallowed).
- `test_screenshot_does_not_retry_a_different_error` — a fake page raising an unrelated error
  ("Target page, context or browser has been closed"); asserts no retry happens and the real
  error propagates immediately.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_browser.py -v
..............                                                          [100%]
14 passed
$ uv run pytest -q                        # all green
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

Real repro against the live Docker container (the actual environment AT-036 was found in),
3 consecutive runs, all clean (previously this flaked roughly every other run):

```
$ for i in 1 2 3; do docker compose exec autotester bash -c \
    "cd /app && rm -rf profiles/regression-demo && uv run python scripts/regression_proof.py"; done
=== run 1 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
=== run 2 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
=== run 3 === REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
```

## How to verify (commands + expected)

- `uv run pytest tests/test_browser.py -v` → 14 passed
- `uv run pytest -q` → all green
- `uv run ruff check src tests scripts` → clean
- `uv run autotester doctor` → clean
- `docker compose exec autotester bash -c "rm -rf profiles/regression-demo && uv run python scripts/regression_proof.py"` run several times → no more Protocol error / INCONCLUSIVE-empty flake

## Scope notes for the checker

- The retry is scoped as narrowly as possible: only the one named error string, only one retry,
  only inside `screenshot()` — no change to `execute.py`, no change to what gets masked (B7), no
  change to any other evidence-capture path.
- 3 clean runs is not a mathematical proof an intermittent race can never recur, but it's a
  genuine, real improvement over the prior every-other-run failure rate, with root cause
  (transient CDP compositor race right after a click) matching the well-known class of this
  error. If it recurs, the existing retry-once ceiling means a persistent version of the same
  error still surfaces honestly as an `ERRORED` outcome, not a silently-passed test.

## Status: checked-PASS — see qa/verdicts/at036-screenshot-retry.md, cycle 1 PASS
