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

---

# Cycle 2 — /checker verdict

**Date:** 2026-09-25 · **Head checked:** dd442eb (fix 64fdf58, master merge 1bb436a) · **Cycle checked: 2** (manifest Fix cycle: 2 of 3) · **Issues addressed (claimed):** AT-562, AT-564, AT-565, AT-568, AT-569

```
VERDICT: FAIL
SCOREBOARD: PR 6/7 (PR2 evidence isolation broken on the live path), RT 7/7; core invariants hold
FAILURES:
- [PR2 / live path] sev: high · the parallel route's sessions (stages/parallel_run.py::default_session_factory) all write evidence into the SAME run_dir and each restarts browser/session.py's screenshot counter at 01, so sibling cases overwrite each other's screenshots (01-step01-navigate.png) and a case's judge can grade a sibling's screenshot -> silent wrong verdict. Reproduced live (Mode D run: 2 cases reference one file; 4 PNGs for 6 steps) and deterministically (real BrowserSession probe, cases run one after the other: two different pages -> one path). · fix: a per-case evidence namespace in the parallel factory (run_dir/<case_id>/ or a case-id prefix) that the grader + run view resolve; a test driving two cases with different first pages through default_session_factory asserting distinct paths with different bytes; a capability row. · issue: AT-572
- [PR6 reporting / AT-568 fallback] sev: medium · a grader/provider exception after run_case COMPLETED makes run_cases replace the real RawResult with outcome=errored; grade_errored_result then records "not judged: execution errored" and the run view shows "no screenshots captured" -- the real outcome and step evidence are discarded and the failure is misattributed to execution. · fix: in _run_and_grade, run the case and capture its RawResult first, then grade; on a grader error keep the real RawResult and save an INCONCLUSIVE verdict naming the grader failure. · issue: AT-573
CAPABILITY-COVERAGE: 3/3 cycle-2 rows reproduced (6, 7, 8), each in its own throwaway copy; green before, red on the named assertion after
LIVE-BROWSER: qa/evidence/browser-at562-564-live-wiring-2026-09-25-checker/report.json
ISSUES-WRITTEN: AT-572, AT-573
EXECUTOR: claude-sonnet-subagent (checker: claude-opus-session, checker seat)
EXPLANATION: Both cycle-1 failures are genuinely fixed: the route now survives a factory crash and a grader raise (3 results + 3 verdicts + the Run, judge never reached for the ERRORED case), and Provider.record is locked. But the first real parallel run in a browser shows the live path mixes up evidence between concurrent cases -- the same class of gap as AT-565/AT-568 (T-173 code proven only through fakes, broken once wired live). No run should grade on a sibling's screenshot, so this cannot merge.
```

## What I re-ran (cycle 2)

- **Crash probe, real objects** (`scratchpad/probe_at568_route_c2.py`: real `Case`s, real `ProjectStore` in a temp root, a `MockProvider` judge with NO queued response): factory raises for case 1 -> `results=3 verdicts=3`, bad case `errored` "browser context failed to launch", verdict INCONCLUSIVE by `rule`; `run_and_grade_case` raises for case 1 -> same, "judge provider exploded". The unqueued judge was never reached. (The cycle-1 probe's thin `SimpleNamespace` cases now fail only on `rubric_ref`, a probe artifact, since the fallback goes through the real rubric seam.)
- **Every non-browser test file** in a throwaway copy of dd442eb with master's fixed ledger overlaid: `1 failed, 1553 passed, 5 skipped`. The one failure, `test_ui_sources.py::test_uploaded_recordings_are_gitignored`, runs `git check-ignore` and the copy has no `.git`; it passes in the worktree (`1 passed`). Net: all green.
- `ruff check src tests scripts` -> All checks passed · `autotester doctor` (post-merge ledger) -> clean.
- **Capability rows** (each its own copy, `scratchpad/c2-row{6,7,8}`):
  - Row 6 (blind index back): `2 passed` -> `2 failed`, `KeyError: 'case_…'` at `routes_runs.py:158`.
  - Row 7 (lock replaced by `if True:`): `2 passed` -> red 3/3 runs (`assert 50 == 1` / `49 == 1`). Note: only the duplicate-row test fires; the lost-increment test stays green unlocked (GIL) -- the file is still reliably red.
  - Row 8 (ERRORED forced to COMPLETED before `grade`): `11 passed` -> `2 failed`, `ProviderError: mock provider has no queued response for role=judge`.
  - Row 9 not re-run (it's covered by pre-existing tests sharing the seam).
- **Diff scope** 1bb436a..dd442eb: 7 files, all listed in "What changed"; the only removed line in tests is a widened import. No deletions of functions, tests or routes.
- **Mode D** (real Chromium, branch app, isolated root, fixture on :46671, `max_parallel=2`, declared secret `RD_PASSWORD` filled via `{{SECRET:…}}`, judge swapped in-process for a mock that raises for one case): the run completes (303, no 500), `run.json` `parallel_n=2 parallel_bound_by=config`, 3 results + 3 verdicts, `trace.jsonl` = 2 judge `llm_call` + `execute/done`, the trace card renders, the secret value is in neither the run dir nor the DOM. 1 console error = the deliberate 400 from the unmocked first attempt ("no AI provider is configured"). Findings AT-572 (high) and AT-573 (medium) come from this run.

## Status: FAIL (cycle 2) — maker fix cycle 3 (last).
