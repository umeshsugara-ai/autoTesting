# Manifest — at555-url-guard

**Unit:** AT-555 — guard `met()`'s url branch (fail-safe, not fail-open).
**Contract:** qa/contracts/core-invariants.md C7 + qa/contracts/execute.md.
**Date:** 2026-09-22
**Fix cycle: 1 of max 3**
**Dual check:** no
**Issues addressed:** AT-555

## The defect

`browser/assertions.py::met()`'s url branch read `session.page.url` raw, INSIDE the outer
`with contextlib.suppress(Exception):`. On a crashed/closed page that read raises, the suppress
swallowed it, execution fell through to the final `return True` — a url-bearing expectation on an
unreadable page recorded SATISFIED instead of failing safe. Exact twin of AT-551 (`body_text`/
`absent_text`, already fixed via the `None`-on-read-failure pattern); the url branch was the one
left unguarded, disclosed as debt in `qa/verdicts/at540-assertion-layer.md` row 11.

## What changed

- `src/autotester/browser/assertions.py` (140 lines):
  - `met()` (line 23): the url branch now reads through a new guarded helper, `_page_url`, and
    treats `None` (read failure) as unmet — `if expected.url: current = _page_url(session); if
    current is None or expected.url not in current: return False`.
  - `_url_label()` (line 92, `assert_expected`'s evidence path, AT-552) rewritten to call the
    same `_page_url` helper instead of its own separate try/except — **reuse, not duplication**:
    `met()` and `assert_expected` now share ONE guarded raw url read.
  - `_page_url(session) -> str | None`  (new, line 104): mirrors `body_text`'s shape exactly —
    returns the raw url (or `""`) on success, `None` on any exception.
- `tests/test_execute_assertions.py` (225 lines): added
  `test_met_url_branch_fails_safe_on_an_unreadable_page` — see Capability coverage below for why
  it probes `met()` directly rather than through `run_case`.

## Why `met()` was probed directly, not via `run_case`

`assert_expected()` records each field's DOM evidence via its OWN independently-guarded reader
(`_url_label` for url, `_text_label`/`body_text` for visible_text/absent_text — both already fixed
in earlier AT-551/AT-552 cycles). `met()` is called only as the poll loop's early-exit condition
(`while elapsed < timeout_ms and not met(...)`); its return value never reaches the recorded
evidence or the run's final `Outcome` directly. Confirmed empirically: reverting only `met()`'s
guard while leaving `_url_label` guarded still produced `Outcome.ASSERTION_FAILED` with
`"assert url: unmet (url unreadable)"` evidence through `run_case` — a `run_case`-level test would
have silently passed against the pre-fix, buggy `met()`. The actual contract `met()` makes (and
that `session._met()` — currently unused but present as a direct-probe entry point — or any future
caller relies on) can only be pinned by calling `assertions.met()` itself.

## How to verify (commands + expected)

```
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
...
collected 9 items

tests\test_execute_assertions.py .........                               [100%]

============================== 9 passed in 0.07s ==============================

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

## Capability coverage

| row | capability | check | falsifying edit | pasted result |
|---|---|---|---|---|
| 1 | **an unreadable `page.url` makes a url expectation UNMET, never silently MET** | `test_met_url_branch_fails_safe_on_an_unreadable_page` | `met()`'s guarded url block reverted to the raw pre-fix read: `if expected.url and expected.url not in session.page.url: return False` (inside the same outer suppress) | see full RED/GREEN transcript below — assertion name that fires: `test_met_url_branch_fails_safe_on_an_unreadable_page` |
| 2 | pre-existing url/visible_text/absent_text/dom_asserts capabilities untouched | remaining 8 tests in `tests/test_execute_assertions.py` | n/a — regression check | all 9 pass together (see verify output above); nothing else in the file changed behavior |

### Row 1 — GREEN (fix) / RED (falsifying edit) / GREEN (restored)

```
# fix in place
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page -v
tests\test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page PASSED [100%]
1 passed in 0.12s

# falsifying edit: assertions.py met() url branch reverted to the raw pre-fix read
#   if expected.url and expected.url not in session.page.url:
#       return False
#   (i.e. _page_url()/None-guard removed, matching the code exactly as it stood before this fix)

$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_met_url_branch_fails_safe_on_an_unreadable_page -v
...
>       assert assertions.met(session, ExpectedState(url="/success")) is False
E       AssertionError: assert True is False
E        +  where True = <function met at 0x...>(<BrowserSession ...>, ExpectedState(url='/success', ...))
1 failed in 0.12s

# restored (the committed fix)
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py -v
tests\test_execute_assertions.py .........                               [100%]
9 passed in 0.13s
```

## Not touched (hard constraints honored)

- `qa/contracts/*`, `qa/issues.jsonl` — checker-owned; not edited.
- No new file created — the fix lives entirely inside the existing `assertions.py`; the new
  helper (`_page_url`) is factored so `met()` and `_url_label` share it (one-concept-one-place),
  not a second guarded reader.
- File sizes: `assertions.py` 140/300 lines, `test_execute_assertions.py` 225/300 lines — both
  well under the doctor cap; no split needed.

## Live browser evidence

Not UI-touching — pure oracle-probe logic in `src/autotester/browser/assertions.py`; no app UI
surface changed. Changed paths this cycle: `src/autotester/browser/assertions.py`,
`tests/test_execute_assertions.py`, `qa/manifests/at555-url-guard.md`.

## Status: checked-PASS

Checker `a8ce8b47` returned **VERDICT: PASS** (Cycle checked: 1) — see `qa/verdicts/at555-url-guard.md`.
Independently reproduced the falsification, confirmed the `_page_url` dedup (one definition, doctor
clean), validated the run_case false-positive finding, full suite 1535 passed / 0 failed. AT-555
flipped open→fixed. Verdict + ledger committed on the wave branch (62a0fef); merged here.
