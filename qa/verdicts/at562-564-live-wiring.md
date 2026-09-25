# Verdict — at562-564-live-wiring

**Date:** 2026-09-25 · **Checker:** /checker Mode A, supervising checker (in-session, real re-runs + probe) · **Bound root:** D:/autoTesting/.worktrees/at562-564-live-wiring
**Head checked:** eba71a2 (code 001aa92, base 8a97eca) · **Cycle checked: 1** (manifest Fix cycle: 1 of 3) · **Issues addressed (claimed):** AT-562, AT-564, AT-565

## VERDICT: FAIL

```
VERDICT: FAIL
SCOREBOARD: AT-562 wiring present (trigger_run -> plan_parallel_run -> run_cases when n>1; parallel_n/bound_by recorded); AT-564 wiring present (StageContext(secrets=...) per run, judge.trace attached, EXECUTE span); AT-565 fixed INSIDE run_cases but broken again at the live route (FAIL below). Diff scope clean (5 files, all in the manifest, nothing removed). Non-browser suite 1550 passed, 5 skipped, 0 failed.
FAILURES:
- [PR6 / AT-565, live route] sev: high · ui/routes_runs.py::_run_cases_in_parallel saves `verdicts[result.case_id]` blindly, but a verdict is captured only when run_and_grade_case completes. An ERRORED result from a session_factory crash (the exact AT-565 case) or from any exception in run_and_grade_case (it catches nothing — e.g. a grader/provider error) has no verdict -> KeyError. Checker probe (scratchpad/probe_at565_route.py: 3 cases, n=2, the factory raises for case_1, stub grader) -> "KeyError: 'case_1'": case_0 saved with its verdict, case_1's result saved WITHOUT a verdict, case_2 never saved, and store.save_run (which follows) never runs -> the route 500s and the Run record is lost. PR6 requires every other case to complete and report its own outcome. · fix: never index the capture dict blindly — for any result without a captured verdict, produce one through the same grade path the serial route uses for an ERRORED result (or an explicit ERRORED verdict); add a ROUTE-level test where the factory raises for one of three cases (all three results + verdicts and the Run saved; siblings keep their real outcomes) and a capability row that reverts the handling and goes red. · issue: AT-568
- [concurrency, introduced by sharing one judge across worker threads] sev: medium · providers/base.py::Provider.record has no lock: `entry.calls += 1` / `+= tokens` on shared ProviderUsage rows and the not-matched -> append path race when grades finish concurrently -> lost usage/cost increments or a duplicate role row. · fix: a threading.Lock around the accumulation in record(), or one judge per worker. · issue: AT-569
CAPABILITY-COVERAGE: not re-run this cycle (FAIL established by a direct probe of the live route); the run_cases-level AT-565 fix is confirmed working by the same probe (run_cases returned an ERRORED RawResult for case_1 instead of raising). All capability rows to be reproduced in cycle 2.
LIVE-BROWSER: not run this cycle — the FAIL is independent of rendering. MANDATORY for cycle 2 (ui/routes_runs.py is the live Run button): drive a real run through the UI on an isolated AUTOTESTER_ROOT with a fixture site, with max_parallel=2, and assert the run completes, trace.jsonl is written, the trace card shows it, Run.parallel_n is recorded, and no secret value appears.
ISSUES-WRITTEN: AT-568 (high), AT-569 (medium), AT-570 (medium); AT-562 / AT-564 / AT-565 stay open
EXPLANATION: The wiring itself is right — the serial path is preserved exactly, secrets are threaded into the per-run StageContext, the width is recorded, and fan-out is opt-in (max_parallel defaults to 1). But the parallel consumer of run_cases re-breaks the isolation AT-565 just added: one crashed case aborts the whole live run. The full non-browser suite is green because no test drives a crash through the route — the gap this cycle's fix must close.
```

## Judgements on the maker-raised gaps

1. **Live-browser smoke skipped** — see LIVE-BROWSER; required at cycle 2.
2. **Coarse EXECUTE span (one per run)** — acceptable: RT3 is one span per finished StageCheckpoint, and EXECUTE is one stage.
3. **SECURITY FLAG: trigger_run consults no RunApproval** — confirmed PRE-EXISTING (master's trigger_run checks only `_require_declared_values`). qa/contracts/consent.md "Out of scope" defers gating run_case to T-122's live-case gate, and fan-out is opt-in (max_parallel default 1; ALLOW_WRITES forces serial, PR3). Not charged to this unit. Filed for visibility as AT-570 (medium): with no approval, RunBudget(None) is unbounded, so an opted-in N-way fan-out against a live target has no consent bound — PR7 is not violated (nothing to widen), but D-018's "nothing outward-facing starts without an approval" is not yet true for case runs.
4. **Unlocked verdict-capture dict** — each worker writes only its own key and a dict store is atomic under the GIL, so the dict itself is fine; the defect is the MISSING keys (AT-568).
5. **AT-564 "real CLI/UI runs" scope** — accepted: the only CLI `run` command is `autotester ingest run` (video -> FlowSpec, no run_id, no case execution), so ui/routes_runs.py::trigger_run is the only case-run entry point. Observation, not a finding: ingest-CLI model calls are still outside any trace.

## What I re-ran

- Diff scope 8a97eca..HEAD: qa/manifests/at562-564-live-wiring.md, src/autotester/stages/parallel_run.py, src/autotester/ui/routes_runs.py, tests/test_parallel_run_session_crash.py, tests/test_ui_runs_parallel_trace.py — no removed def/class/route/test.
- Every non-browser test file on the branch (142 files): **1550 passed, 5 skipped, 0 failed**.
- Route probe (read-only toward the tree; patches module attributes in-process only): KeyError as above. `git status` clean after.
- Read master's trigger_run, Project.max_parallel (default 1), plan_parallel_run (ALLOW_WRITES -> 1), Provider.record (no lock), run_and_grade_case (no exception handling), cli_video.py `run` (video ingest).

## Status: FAIL (cycle 1) — maker fix cycle 2.
