# Verdict — at044-entry-case-profile-isolation

**Date:** 2026-09-04
**Cycle checked:** 1
**Contracts:** qa/contracts/ui-run.md (RU1-RU4) + qa/contracts/execute.md (E2, E5)
**Verdict:** PASS

## What I re-ran myself (fresh context, no builder reasoning trusted)

- `uv run pytest tests/test_browser.py tests/test_execute.py tests/test_ui_runs.py -v` — 29
  passed, 0 failed (includes the manifest's claimed new tests:
  `test_settle_calls_wait_for_load_state_then_a_short_grace_wait`,
  `test_settle_still_takes_the_grace_wait_when_network_never_idles` in test_browser.py;
  `test_click_settles_before_the_screenshot_but_other_actions_do_not` in test_execute.py;
  `test_is_entry_case_matches_the_projects_own_base_url`,
  `test_entry_case_gets_an_isolated_wiped_profile_not_the_shared_one` in test_ui_runs.py).
- `uv run pytest -q` — full suite: 275 passed, 2 skipped, 0 failed. Includes
  `tests/test_agent_loop.py` (the test that would catch a reintroduction of the pre-ship
  regression this unit's own build hit and fixed) — green.
- `uv run ruff check src tests scripts` — All checks passed!
- `uv run autotester doctor` — doctor: clean.
- Read `src/autotester/browser/session.py::settle()` (lines 177-198) directly: BOTH
  `self.page.wait_for_load_state("networkidle", timeout=timeout_ms)` (line 196) and
  `self.page.wait_for_timeout(500)` (line 198) are each independently wrapped in their own
  `with contextlib.suppress(Exception):` block. Confirmed — not just the first one.
- Read `src/autotester/stages/agent_loop.py` directly: line 25 imports
  `from autotester.stages.execute import run_case`; lines 75 and 83 call it. Confirms
  `agent_loop.py` genuinely shares `execute.py::run_case` with the UI's own pipeline (via
  `run_case_pipeline.py`/`trigger_run`) — this class of bug really could recur for any future
  `FakePage`-style test double.
- Read `tests/test_agent_loop.py`'s `FakePage` (lines 36-62) directly: has real
  `wait_for_load_state(self, state="load", timeout=0)` and `wait_for_timeout(self, timeout_ms)`
  no-op methods — the AttributeError regression class is now covered, not just accidentally
  passing.
- **Live Docker verification (AT-044's specific claim: zero TimeoutErrors, not "every case
  deterministically PASSes"):**
  - `docker compose restart` on `autotesting-autotester-1`, then polled `curl
    http://localhost:8010/` until 200 (returned 200 on the first poll after restart completed).
  - `POST /projects/pathlynks/run` #1 → `303 See Other` → `run-01M1P0FJ7ENKDV2J15DDMBGDW1`. All
    3 `case_*.json` RawResults: `outcome: completed`. All 3 verdicts: `grader_provider: gemini`
    (real, never mock/rule). Results: FAIL, FAIL, INCONCLUSIVE (evidence-quality reasons per
    AT-046, not timeouts).
  - `POST /projects/pathlynks/run` #2 → `303 See Other` → `run-01M1P0J2Q718YH85RDYE6WFW7K`. All
    3 RawResults: `outcome: completed`. All 3 verdicts: real `gemini`. Results: FAIL,
    INCONCLUSIVE, PASS.
  - `grep -ri TimeoutError` across every JSON file in both new run directories: **no match**
    (exit 1) in either run.
  - Cross-checked `docker compose logs` timestamps: the one `TimeoutError`/`ConnectError`
    traceback visible in the log tail was from a stale pre-restart log line (DNS resolution
    failure for `gemini`, unrelated to AT-044's locator-timeout class), confirmed by `docker
    compose logs --since=2m` showing a clean post-restart sequence (`Started server process` →
    `Uvicorn running` → the actual `POST /projects/pathlynks/run` → `303`) with zero errors.

## Judgement per criterion

- **RU1** (real synchronous run, no second execution path) — MET. `trigger_run` still calls the
  same `run_and_grade_case` for every case, whether via the shared session or the new
  `_run_entry_case` helper (`routes_runs.py:56,94`) — both paths converge on the one real
  pipeline function, never a mock or a duplicate copy of run/grade logic.
- **RU2** (honest 400 before a browser starts) — MET, unaffected by this unit (unchanged
  lines 68-75, verified by reading).
- **RU3** (every case run and persisted) — MET. Both live reruns persisted a `RawResult` +
  `Verdict` per case and a `Run` record via the same `ProjectStore` methods; response redirected
  303 to `/report` both times.
- **RU4** (global provider keys visible) — MET, unaffected by this unit; the live runs used real
  Gemini credentials from the running Docker process, confirming this still holds.
- **E2** (every step composes existing session primitives) — MET. `settle()` is a
  `BrowserSession` method; `execute.py::run_case` calls it via `session.settle()`, never touches
  `session.page` directly.
- **E5** (never invents an extra click/submit/navigation) — MET. `settle()` is a passive wait
  with no page interaction beyond waiting; it is called after a CLICK step already in
  `case.steps`, not as a new step.

## Scope respected

Judged AT-044's specific claim only (guaranteed TimeoutErrors → zero TimeoutErrors), per the
dispatch's explicit instruction. AT-046 (residual evidence-timing flakiness — PASS/FAIL/
INCONCLUSIVE varying run to run for evidence-quality reasons) is correctly out of scope for this
unit and was not held against it; both live reruns independently reproduced exactly the
non-timeout variability AT-046 already documents (FAIL/FAIL/INCONCLUSIVE, then
FAIL/INCONCLUSIVE/PASS) — consistent with the manifest's own honest framing.

## Ledger

- **AT-044** — flipped `open → fixed` (this checker's independent live re-run evidence; not yet
  `verified` — a later re-check flips that).
- **AT-045** — the manifest's "Issues addressed" cites `AT-045 (fixed)`, but no `AT-045` row was
  ever filed in `qa/issues.jsonl` (only referenced descriptively inside `AT-046`'s text). The
  underlying code (`settle()`) is real and independently verified above, so this is not a
  functional gap — filed as **AT-047** (low severity, ledger bookkeeping only: a missing row for
  an id the manifest and a sibling issue both cite by name).

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (RU1-RU4, E2, E5), 0/0 invariants (none named beyond the criteria)
FAILURES (if any): none
ISSUES-WRITTEN: AT-047 (new, low) · AT-044 (status flipped open->fixed)
EXPLANATION: AT-044's specific claim (guaranteed TimeoutError -> zero TimeoutErrors on the UI
Run button's live pipeline) is confirmed on two fresh live reruns against the real Pathlynks
product after a container restart -- every case outcome=completed, zero TimeoutErrors, real
Gemini grading throughout. The regression-catch-and-fix is real: agent_loop.py genuinely shares
execute.py::run_case with the UI pipeline, settle()'s two waits are independently
exception-suppressed, and FakePage now has the methods that were missing. AT-046 (evidence-timing
flakiness) is honestly out of scope and was not held against this unit. One minor ledger
bookkeeping gap found and filed (AT-047, low) -- an issue id cited by the manifest and by AT-046
was never itself registered as a row.
```
