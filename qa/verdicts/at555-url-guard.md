# Verdict — at555-url-guard

**Date:** 2026-09-22
**Cycle checked:** 1
**Checker:** fresh Claude subagent (claude-sonnet-subagent), Mode A unit check
**Bound project root:** `D:/autoTesting/.worktrees/at555-url-guard`
**Base commit for diff scope:** a30f535 → unit commit `7f70536` (branch `wave/at555-url-guard`)

## What I re-ran myself

```
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 9 items
tests\test_execute_assertions.py .........                               [100%]
============================== 9 passed in 0.15s ==============================

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ PYTHONUTF8=1 uv run pytest        # full suite, bare (no CLI -q, AT-503)
... (whole-log scan for FAILED/ERROR/^E: zero hits outside expected xfail markers)
1535 passed, 5 skipped, 32 xfailed, 1 warning in 655.80s (0:10:55)
```

All match the manifest's pasted output.

## Diff scope (step 4c)

```
$ git diff a30f535..HEAD --stat
 qa/manifests/at555-url-guard.md      | 115 +++++
 src/autotester/browser/assertions.py |  32 +++++---
 tests/test_execute_assertions.py     |  40 ++++++

$ git show --name-only --format= 7f70536
qa/manifests/at555-url-guard.md
src/autotester/browser/assertions.py
tests/test_execute_assertions.py
```

Matches the manifest's "What changed" exactly (C10 satisfied: unit commit carries only its own
paths). Full diff of `assertions.py` read directly: no existing function, class, export, or test
was deleted or renamed. `_url_label()` was rewritten to call the new `_page_url()` helper instead
of its own separate `try/except` — this is a genuine dedup (confirmed by grep: `_page_url` is
defined exactly once, at `assertions.py:106`, called from both `met()` and `_url_label()`), not a
second guarded reader. `uv run autotester doctor` (duplicate-definition rule) is clean. No new file
was created.

## Capability coverage — independently reproduced (step 4b)

Row 1 — **an unreadable `page.url` makes a url expectation UNMET, never silently MET**
(`test_met_url_branch_fails_safe_on_an_unreadable_page`):

Reproduced in a THROWAWAY COPY (`git archive HEAD` extracted outside the bound tree, to the
session scratchpad), never the bound working tree.

```
# GREEN before, in the copy (proves the copy is real):
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page -v
tests\test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page PASSED [100%]
1 passed in 0.13s

# falsifying edit applied (single-hunk, single-file, exactly as the manifest describes):
#   met()'s guarded url block reverted to the raw pre-fix read:
#     if expected.url and expected.url not in session.page.url:
#         return False

# RED after, in the copy — for the right reason:
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page -v
>       assert assertions.met(session, ExpectedState(url="/success")) is False
E       AssertionError: assert True is False
E        +  where True = <function met at 0x...>(<BrowserSession ...>, ExpectedState(url='/success', ...))
1 failed in 0.16s
```

`met()` genuinely returned `True` on an unreadable page under the reverted code — the same
assertion the manifest names, failing for the same reason it claims.

**Honesty check on the manifest's disclosed finding** (that a `run_case`-level test would be a
false-positive falsifier because `_url_label`/`assert_expected` was already guarded by AT-552):
with the same falsifying edit in place, I ran the full `test_execute_assertions.py` file in the
copy — only the named `met()`-direct test reddens; the other 8 tests (including the `run_case`-
level url-assertion tests `test_a_met_expectation_keeps_the_run_completed` and
`test_errored_still_beats_assertion_failed`) stay green:

```
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py -v
FAILED tests/test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page
1 failed, 8 passed in 0.50s
```

This independently confirms the manifest's claim: `assert_expected`'s own `_url_label` reader
already masks the regression at the `run_case`/evidence layer, so only a direct `met()` probe can
isolate this capability — exactly what the maker chose to write. I also confirmed the test calls
`assertions.met()` directly (`test_execute_assertions.py:176`), not `run_case`, as claimed.

Row 2 — regression check (remaining 8 tests in the file, all pass together, confirmed above; also
reflected in the 1535-pass full suite).

## Issues addressed

`AT-555` (ledger, severity medium, found by checker-sweep 2026-09-22c): "met()'s url branch
remains fail-UNSAFE... disclosed but never given an issue id." The reproduction above directly
verifies the fix — the exact regression the issue describes is now caught by
`test_met_url_branch_fails_safe_on_an_unreadable_page`, and the guarded `_page_url` helper closes
the gap at the cause (`met()`'s url branch), not just at the evidence layer. Status flipped
`open → fixed` in `qa/issues.jsonl` (this checker's convention: `fixed` now, `verified` on a
later re-check per the checker protocol).

## Live browser

Not applicable. Changed paths this cycle are `src/autotester/browser/assertions.py` (pure
oracle-probe logic, no rendering) and `tests/test_execute_assertions.py`, confirmed from the diff
above — no UI surface, route, or rendered page changed, and no indirect ranking/retrieval change
that would alter what an app screen renders.

## Judgement against contracts

- `core-invariants.md` C1/C5/C6/C8/C9: not applicable (no schema, secret, artifact-format, model-call,
  or control-value change in this unit).
- **C2/C3/C4** — held: `uv run autotester doctor` clean (file sizes, duplicate-definition, root
  clutter), confirmed independently above.
- **C7** — held: re-ran the manifest's own verify commands myself, and independently reproduced the
  single capability-coverage row in a throwaway copy outside the bound tree (green-before,
  red-after, right assertion). No sabotage/mutation-vacuity trap found: the falsifying edit is a
  real single-hunk revert of the guarded block, not a nearby-string change, and it is exactly the
  hunk the pre-fix code had.
- **C10** — held: unit commit `7f70536` carries only `qa/manifests/at555-url-guard.md`,
  `src/autotester/browser/assertions.py`, `tests/test_execute_assertions.py` — a subset of the
  manifest's "What changed" plus its own qa/ paths.
- `execute.md` **E1** — holds unchanged: the assertion layer still records observations only
  (`met()`/`assert_expected` never grade); this unit only tightens `met()`'s own fail-safe
  behaviour, confirmed by the full 1535-pass suite with zero regressions.

No CRITICAL contract amendment implicated; no criterion softened.

VERDICT: PASS
SCOREBOARD: 5/5 applicable core-invariants criteria met (C2, C3, C4, C7, C10; C1/C5/C6/C8/C9 n/a), 1/1 execute.md invariant holds (E1)
FAILURES (if any): none
CAPABILITY-COVERAGE: 2/2 rows reproduced (row 1 independently falsified by the checker in a throwaway copy; row 2 regression check confirmed)
LIVE-BROWSER: not-applicable (changed paths: src/autotester/browser/assertions.py, tests/test_execute_assertions.py — no UI surface)
ISSUES-WRITTEN: none new; AT-555 flipped open -> fixed
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: met()'s url branch now reads through a shared, guarded _page_url helper and treats a read failure (None) as unmet rather than falling through the outer suppress to a bare `return True`; I independently reproduced the falsifying edit in a throwaway copy (green before, red after, `assert True is False` on the named test) and confirmed the manifest's honesty claim that a run_case-level test would not have caught this. Full suite (1535 passed), ruff, and doctor are all clean, and the unit's commit is correctly scoped (C10).
