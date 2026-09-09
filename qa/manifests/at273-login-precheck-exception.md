# Manifest — at273-login-precheck-exception

**Unit:** AT-273 — `_already_past_login` (AT-226's own precheck) swallows every exception silently
**Commit:** `ad6259c`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/explore.md` (login bootstrap, X10)
**Goal task:** none — issue-driven
**Issues addressed:** AT-273 (high)

## What was wrong (from the sweep that found it)

> `_already_past_login` (AT-226's own precheck) has a bare `except Exception: return False` —
> no `as exc`, nothing logged or stored — while its sibling `_seed` 15 lines below (AT-098's fix)
> names `NavigationRefused` separately and records the message in `rt.seed_error`. A transient
> nav failure during the precheck is silently reclassified as "not authenticated" and falls
> through to `run_case`'s own `goto`, so the crawl can still hit the exact step-timeout AT-226
> exists to prevent, with no signal the precheck itself failed.

## What changed

- `src/autotester/stages/explore.py` — `ExploreRuntime` gains `login_precheck_error: str | None`,
  a scratch field matching the existing `seed_error`/`return_error` pattern.
- `_already_past_login` now catches `NavigationRefused` separately from generic `Exception`
  (matching `_seed`'s own discipline exactly), storing the message rather than dropping it.
  **The fallback value is unchanged** — still `False`, still falls through to running the login
  case normally. This is a diagnostic addition, not a new failure mode.
- New `_login_failed_reason(rt)` helper: builds the `stop_reason` string, appending
  `(precheck also failed: <cause>)` only if `login_precheck_error` is set — so the cause surfaces
  only when it's actually relevant (the login case also genuinely failed afterward), not on every
  precheck exception (most of which correctly fall through to a successful login run).
- `run_crawl`'s login-failure branch now calls this helper instead of a bare string literal —
  kept the function under the 50-line cap without a second violation.
- `tests/test_explore_login_bypass.py` — one new test: monkeypatches the fake page's `goto` to
  raise for the login URL specifically (nothing else), runs a crawl, and asserts `stop_reason`
  names both "precheck also failed" and the underlying exception text.

## How to verify (commands + expected)

- `uv run pytest tests/test_explore_login_bypass.py -q` → expected: exit 0, 4 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_explore_login_bypass.py -q
....
4 passed

$ uv run pytest
924 passed, 2 skipped, 1 warning in 84.94s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), one mutation, restored immediately after:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted unit layered
onto the extract by hand, since it postdates HEAD — `explore.__file__` verified inside the
extract, not the live tree). Reverted the two named-exception branches back to a bare
`except Exception: return False`. Result: **exactly 1 failure**,
`test_a_transient_precheck_failure_is_named_not_swallowed`:

```
AssertionError: assert 'precheck also failed' in 'login case did not complete'
```

The other 24 tests across `test_explore_login_bypass.py`, `test_explore.py` and
`test_explore_blocked.py` stayed green after restore — confirming the fallback behaviour (still
`False`, still runs the case) is genuinely unaffected; only the cause's visibility changed.

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree confirmed
untouched — the sabotage never left the isolated extract (`git diff` against the live tree before
and after the sabotage showed only my own already-known uncommitted work, and
`rt.login_precheck_error = f"refused by the domain guard: {exc}"` was confirmed still present in
the live file before proceeding).

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/stages/explore.py`,
`tests/test_explore_login_bypass.py`. No route, template, component, or rendered output —
`stop_reason` is already displayed generically wherever `Crawl.stop_reason` renders (confirmed by
the earlier AT-242 unit's own audit of every consumer); this change only makes the string longer
in one specific, rare case.

## What this unit does not claim

- Does not re-open or re-litigate AT-226 itself — that unit's own criteria were independently
  confirmed correct by two checkers already. This is a narrowly-scoped hardening the sweep found
  on top of it.
- Does not claim every silent-exception pattern in `explore.py` is now fixed — only this one
  named function, matching the sweep's own specific finding.

## Status: checked-PASS (cycle 1, verdict a08118d)
