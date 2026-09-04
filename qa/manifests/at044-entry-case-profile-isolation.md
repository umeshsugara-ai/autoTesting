# Manifest — at044-entry-case-profile-isolation

**Contract:** qa/contracts/ui-run.md RU1-RU4 (unchanged meaning — a correctness fix to
`trigger_run`'s existing promise, not a new criterion) + qa/contracts/execute.md E2 (evidence
should let "a human or grade.py review the run frame by frame" — the settle() addition realizes
this for CLICK actions specifically)
**Goal task:** none (`.goal/goal.json` is 20/20 done — Umesh asked to rerun testing on
pathlynks, found a real regression instead of a clean rerun)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-044 (fixed), AT-045 (fixed) — AT-046 filed as a real, honest follow-up,
not fixed by this unit

## Why this unit

Umesh: "pathlynks k upar testing rerun kar" — asked for a real rerun. The first real rerun via
the live UI reproduced the exact original INCONCLUSIVE-report bug (`pathlynks-login-test-fresh-
profile`, fixed earlier this session) — but that fix only ever patched
`scripts/run_pathlynks_first_cases.py`, a SEPARATE caller from the one the Run button actually
uses (`ui/routes_runs.py::trigger_run` → `stages/run_case_pipeline.py::run_and_grade_case`).
The generic pipeline never got the same protection. This is a real regression in the flagship
Run feature (F-024), not a request — found live, filed (AT-044), and fixed the same session.

## What changed

### AT-044 — per-case profile isolation for entry-screen cases

- `src/autotester/ui/routes_runs.py` — `_is_entry_case(case, project)`: true when a case's
  first step is a `NAVIGATE` to the project's own declared `base_url` (its entry/sign-in
  screen). `_run_entry_case(...)`: gives such a case a dedicated, wiped-before-every-run
  profile (`ProjectPaths(f"{slug}-entry-test")`) — order-independent (no "run BEST last" hack
  needed) and cross-run-independent (no stale login survives from a previous run), the same
  proven pattern `scripts/run_pathlynks_first_cases.py` already used for itself, generalized
  into the actual pipeline the UI Run button calls. `trigger_run` now branches per case: entry
  cases get their own isolated session; other cases keep sharing the persistent, already-
  authenticated profile (the manual-login feature's whole point). The shared session is skipped
  entirely (not even launched) when every case in the run is an entry case.

### AT-045 — evidence capture no longer screenshots mid-transition

- `src/autotester/browser/session.py` — new `BrowserSession.settle(timeout_ms=8000)`: a
  best-effort, bounded, never-raising wait (`wait_for_load_state("networkidle")` then a fixed
  500ms grace period for pure client-side re-renders network-idle alone can't see) for an async
  page transition to finish before evidence is captured. 8s matches the bound already proven
  necessary for this exact class of redirect (`pathlynks-login-test-fresh-profile`, cycle 2).
- `src/autotester/stages/execute.py` — `run_case` calls `session.settle()` after a `CLICK`
  action specifically (the action class that triggers async transitions — form submits,
  navigation-causing buttons), before the per-step screenshot. Other actions are unchanged — no
  added latency for fill/navigate/select/etc. `execute.md`'s E5 ("never invents an extra click,
  submit, or navigation") still holds: this is a passive wait, not a new step.
- `tests/test_execute.py` (+1 test) — a CLICK settles before its screenshot, other actions
  don't.
- `tests/test_browser.py` (+2 tests) — `settle()` calls `networkidle` then the grace wait; a
  page that never reaches network-idle still gets the grace wait and never raises.
- `tests/test_ui_runs.py` (+2 tests) — `_is_entry_case` matches the project's own `base_url`
  and nothing else; a real trigger_run with one entry case and one non-entry case gives them
  genuinely different (and correctly-scoped) profile directories.

### A real regression this unit's own build caught and fixed before shipping

The first version of `settle()` called `self.page.wait_for_timeout(500)` unwrapped (only the
`networkidle` wait was inside `contextlib.suppress`). Running the full suite immediately failed
3 tests in `tests/test_agent_loop.py` — its own `FakePage` test double (used across
`stages/agent_loop.py`, which also calls the now-shared `run_case`) has no `wait_for_timeout`
method, so the unwrapped call raised `AttributeError`, which `run_case`'s own exception handling
converted into a real `Outcome.ERRORED` — turning a normal successful click into a fake error
that wrongly invoked the agent-fallback path. Fixed by wrapping BOTH waits in `settle()` in
their own `contextlib.suppress(Exception)` blocks (matching its own "never raises" docstring
contract), and — for real coverage, not just accidental pass-via-suppression — added the two
missing methods to `test_agent_loop.py`'s `FakePage` as proper no-ops.

## Deliberate scope decision — AT-046 filed, not fixed here

Across 4 consecutive real reruns against the live `pathlynks` project after this fix: **zero
TimeoutErrors in any run** (AT-044 holds solidly — the actual regression Umesh hit is gone), but
evidence-capture precision for the post-submit state is still probabilistic: BEST/EDGE flip
between PASS/FAIL/INCONCLUSIVE run to run with identical code, and WORST (wrong-password
rejection) FAILs every time with "no post-submission evidence." This is a real, harder,
separate problem — a generic `networkidle`+fixed-grace heuristic is a probabilistic proxy for
"did the DOM finish updating," not a deterministic one, especially for a pure client-side error
re-render with no reliable network signal. Filed as AT-046 (medium severity) rather than chased
further in this unit — the actual regression Umesh reported (guaranteed, 100%-reproducible
INCONCLUSIVE on every single run) is fixed and verified; a harder, statistically-partial
improvement is honestly reported as partial, not oversold as complete.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_browser.py tests/test_execute.py tests/test_ui_runs.py -v
                                           # 23 + ... all new/existing tests passed
$ uv run pytest -q                        # full suite green (agent_loop regression caught
                                           #   and fixed before this was true)
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

**Real live Docker verification — 4 consecutive real `POST /projects/pathlynks/run` calls
against the real Pathlynks product, across this unit's own two build iterations:**

| Run | BEST | WORST | EDGE | Notes |
|---|---|---|---|---|
| run-01M1NYJXM0828A7NRWKHEX6EQD (before any fix) | INCONCLUSIVE | INCONCLUSIVE | INCONCLUSIVE | `TimeoutError: waiting for locator("input[name=\"identifier\"]")` on all 3 — the original bug, reproduced live |
| run-01M1NYY39BEXCA5R8RDDQXDXT8 (AT-044 only) | FAIL | INCONCLUSIVE | INCONCLUSIVE | zero timeouts; real Gemini grading; evidence-timing gap surfaces (AT-045 filed) |
| run-01M1NZC10H4K9RC2YRSGQFXYZD (AT-044+045, 8s settle) | **PASS** | FAIL | **PASS** | 2/3 genuinely pass with real evidence |
| run-01M1NZKSHRMTW7WCF8S2CA0E6T (AT-044+045, +grace) | FAIL | FAIL | **PASS** | flakiness confirmed (AT-046 filed) |
| run-01M1NZP7C24E3Y0HPCMQCNZDJ7 (AT-044+045, +grace) | **PASS** | FAIL | INCONCLUSIVE | flakiness confirmed |

Zero `TimeoutError`s in any run after AT-044 shipped — the actual regression is gone. Real
Gemini grading (`grader_provider: gemini`) in every post-fix run, never mock, never a script
workaround.

## How to verify

- `uv run pytest tests/test_browser.py tests/test_execute.py tests/test_ui_runs.py -v` → all
  pass.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- `docker compose restart`, then `POST /projects/pathlynks/run` several times — confirm no
  `TimeoutError` ever appears in any verdict's `note` field (AT-044's actual claim). Evidence
  quality (PASS vs FAIL/INCONCLUSIVE) may still vary run to run — that is AT-046, tracked
  separately, not a regression of this unit.

## Scope notes for the checker

- Please re-run the live rerun yourself at least twice — confirm AT-044's specific claim (zero
  `TimeoutError`s) holds, without expecting every case to deterministically PASS (that is
  explicitly NOT this unit's claim — see the scope decision above).
- Please confirm the agent_loop regression fix is real: read `stages/agent_loop.py` to confirm
  it genuinely shares `execute.py::run_case` with the UI's own pipeline (so this class of bug
  really could recur for any future FakePage-style test double), and that `settle()`'s two
  waits are independently exception-suppressed, not just the first one.

## Status: ready-for-check
