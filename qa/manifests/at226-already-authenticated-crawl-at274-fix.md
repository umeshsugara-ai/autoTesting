# Manifest — at226-already-authenticated-crawl-at274-fix

**Unit:** AT-274 — strengthen the vacuous "genuine login still runs" test found by /checker's FAIL
on `at226-already-authenticated-crawl`
**Commit:** `b48a871`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/explore.md` (login bootstrap, X10)
**Goal task:** none — issue-driven
**Issues addressed:** AT-274 (medium)

## Read this first

This is a separate, self-contained manifest for **AT-274 only** — the concrete finding a
concurrent checker filed on `qa/verdicts/at226-already-authenticated-crawl.md` (FAIL, appended as
an `INDEPENDENT CONCURRENT CHECK` alongside an earlier PASS from a different checker). It does not
re-litigate or re-submit AT-226 itself: the redirect-skip fix (`_already_past_login`,
`_terminal_status` is unrelated/AT-242) was independently confirmed correct by both checkers via
sabotage in the *other* direction (breaking the skip so it never fires reproduces AT-226's
original failure exactly). Only the gap — the negative direction was never sabotage-tested — is
this unit's scope.

## What was wrong (quoted from the FAIL verdict, `qa/verdicts/at226-already-authenticated-crawl.md`)

> `test_a_login_page_that_does_not_redirect_still_runs_the_case` is vacuous against an always-skip
> regression: it never asserts the login FILL step actually ran... sabotaged
> `_already_past_login`'s body with `return True` (always report already-past-login, i.e. always
> skip the login case including when it genuinely needs to run) -- all 22 tests in
> `tests/test_explore_login_bypass.py` + `tests/test_explore.py` still pass.

Confirmed independently before fixing anything: re-ran the exact same mutation myself in a fresh
isolated extract and reproduced the same single-clean-pass result the checker reported.

## What changed

- `tests/crawl_fake.py` — `FakeSitePage` gains a `fills: list[tuple[str, str]]` attribute,
  mirroring the existing `clicks: list[str]`. `FakeLocator.fill` appends `(selector, value)` on
  every successful fill — the FILL step's own real side effect, not an inference from crawl
  status.
- `tests/test_explore_login_bypass.py::test_a_login_page_that_does_not_redirect_still_runs_the_case`
  — one new assertion: `assert (IDENTIFIER, "someone") in page.fills`. Everything else in the test
  is unchanged; the existing `crawl.status`/`stop_reason` assertions stay, since they are still
  correct, just insufficient alone.

## How to verify (commands + expected)

- `uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py tests/test_explore_blocked.py -q` → expected: exit 0, all pass
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_explore_login_bypass.py tests/test_explore.py tests/test_explore_blocked.py -q
........................
24 passed

$ uv run pytest
923 passed, 2 skipped, 1 warning in 88.86s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7) — the checker's own exact mutation, reproduced by me independently:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted fix layered
onto the extract by hand, since it postdates HEAD — `explore.__file__` verified inside the
extract before trusting anything). Replaced `_already_past_login`'s body with `return True`
(anchor matched exactly once, file re-read as changed). Result: **exactly 1 failure**,
`test_a_login_page_that_does_not_redirect_still_runs_the_case`:

```
AssertionError: assert ("input[name='identifier']", 'someone') in []
```

The other 24 tests across `test_explore_login_bypass.py` and `test_explore.py` stayed green —
confirming the strengthened assertion catches exactly the regression it targets, without floor
effects on the legitimate already-authenticated skip path (which this same mutation is *supposed*
to make look correct, and does — every other test still passes under it, exactly as the checker
found).

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree
(`src/autotester/stages/explore.py`) was never touched by this unit — the fix is entirely in the
test fixture and the test itself; no production code changed.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `tests/crawl_fake.py`,
`tests/test_explore_login_bypass.py`. Test infrastructure only.

## What this unit does not claim

- Does not re-verify AT-226's own criteria (C1, C3, C4, X1, X10) — those were already
  independently confirmed by both checkers and are unaffected by this change.
- Does not claim the concurrent-commit-collision disclosure (AT-226's code riding inside `2bb3270`)
  is resolved further — that was already correctly recorded as harmless-but-disclosed and needs no
  action.

## Status: ready-for-check
