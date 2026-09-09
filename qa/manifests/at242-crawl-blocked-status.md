# Manifest — at242-crawl-blocked-status

**Contract:** qa/contracts/explore.md X4/X16
**Goal task:** none — issue-driven (AT-242)
**Date:** 2026-09-09
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-242 (high)

## What changed

- `src/autotester/schema/enums.py:274-282` — new `CrawlStatus.BLOCKED_NO_ACTIONS`, documented in
  the enum's own docstring: the frontier emptied with every reachable action refused by policy
  and none performed.
- `src/autotester/stages/explore.py:164-175` — new `_terminal_status(rt, completed)`, extracted
  out of `run_crawl` (which would otherwise cross the 50-line cap): `not completed` →
  `STOPPED_BOUND`; `completed and actions_used == 0 and denied > 0` → `BLOCKED_NO_ACTIONS`
  (and the reason string gets one clause appended); otherwise `COMPLETED`.
- `src/autotester/stages/explore.py:277-279` — `run_crawl`'s tail now calls `_terminal_status`
  instead of inlining the decision.
- `tests/test_explore_blocked.py` (new) — two tests, split out of `test_explore.py` to keep that
  file under the 300-line cap (it was already at 261 lines; the split follows the file's own
  established precedent, `crawl_fake.py` was split out for the same reason).

## Why (AT-242, filed by the business-truth checker campaign against a real unseen product)

A crawl of `saucedemo.com` (a login-gated product AutoTester had never seen) recorded 1 screen,
0 actions, 3 refusals in 3.4 seconds, and reported `status: completed`. Every reachable action —
an unnamed username field, an unnamed password field, a form-submit button under `read_only` —
was refused by design. The frontier genuinely emptied (nothing was left to visit), but nothing
was ever *done*, and the terminal state gave no way to tell that apart from a real, exhaustive
crawl of a fully-explored product. The sibling live Pathlynks crawl the same day reported
`login_failed` for the same substantive outcome under a different name.

## How to verify (commands + expected)

- `uv run pytest tests/test_explore.py tests/test_explore_blocked.py -q` → expected: exit 0, all pass
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0, "All checks passed!"
- `uv run autotester doctor` → expected: exit 0, "doctor: clean"

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_explore.py tests/test_explore_blocked.py -q
.....................
21 passed

$ uv run pytest
923 passed, 2 skipped, 1 warning in 96.69s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), one mutation, restored immediately after:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted unit was not
yet in HEAD, so I layered it onto the extract by hand before sabotaging — `explore.__file__`
verified inside the extract, not the live tree). Removed the `BLOCKED_NO_ACTIONS` branch from
`_terminal_status`, leaving `completed` fall straight through to `COMPLETED` unconditionally.
Result: **exactly 1 failure**, `test_a_login_gate_with_every_action_denied_is_not_reported_completed`,
with the exact predicted swap:

```
AssertionError: assert <CrawlStatus.COMPLETED: 'completed'> is <CrawlStatus.BLOCKED_NO_ACTIONS>
```

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Full
`test_explore.py` + `test_explore_blocked.py` re-confirmed green after restore.

**Note on this cycle's own process:** while building this unit I made a real mistake — I ran
`git stash` on the live shared tree while a concurrent maker session was actively editing
`explore.py` and `crawl_fake.py` for AT-226, temporarily removing my own uncommitted work from
disk. Caught immediately (`git stash pop`) before it could collide with anything; the concurrent
session's own work was unaffected and merged back cleanly. All sabotage after that point used a
`git archive` extract, never stash, on this tree.

## The negative case, deliberately tested

`test_a_page_with_no_controls_at_all_still_reports_completed` — a genuinely trivial page (nothing
to click, nothing denied) must still report `COMPLETED`. This is the floor the fix must not cross:
`BLOCKED_NO_ACTIONS` fires only when there *were* refusable controls and every one was denied, not
merely when a page happens to have nothing on it.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/schema/enums.py`,
`src/autotester/stages/explore.py`, `tests/test_explore.py`, `tests/test_explore_blocked.py`. No
route, template, component, or rendered output — `CrawlStatus.value` renders generically wherever
it's displayed (UI pill, CLI line, workbook `Status` column, crawl-page stat), confirmed by
grepping every consumer (`ui/routes_crawls.py`, `ui/crawl_view.py`, `cli_crawl.py`,
`stages/crawl_report.py`) before building — none pattern-match specific status strings, so no
downstream surface needed updating.

## What this unit does not claim

- **Not the escalation half.** AT-242's own "expected" line asks only for an honest terminal
  state, which this delivers. It does **not** make a `BLOCKED_NO_ACTIONS` crawl automatically
  request a video — the existing `diff_crawl`/`queue_requests` wiring (AT-240, already fixed)
  compares observed screens against the FlowSpec regardless of status and needs no second trigger
  for this fix; teaching it to also escalate specifically on "every action was refused" would be
  a real, separate, larger unit and is not silently claimed here.
- **Not AT-226/AT-227** (already-authenticated sessions, first-paint modals) — a different
  concurrent maker session is actively fixing AT-226 in this same file; this unit's diff does not
  touch that logic.

## Status: ready-for-check
