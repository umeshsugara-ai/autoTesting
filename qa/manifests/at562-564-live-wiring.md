# Manifest — at562-564-live-wiring

**Contract:** qa/contracts/parallel-run.md (PR1-PR7) + qa/contracts/run-trace.md (RT1-RT7) +
qa/contracts/core-invariants.md
**Goal tasks:** T-172, T-173
**Date:** 2026-09-25
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-562, AT-564, AT-565 (scope-add, coordinator, mid-run: `_run_one`'s
`session_factory(case)` sat outside its own try/except)
**Executor:** claude-sonnet-subagent

## What the two goal-coverage gaps were

- **AT-562:** `stages/parallel_run.py::run_cases` (T-173) PASSed at unit level, but nothing in
  `src/` outside its own test suite called it. No real run could execute cases in parallel or
  record `Run.parallel_n`/`parallel_bound_by`.
- **AT-564:** the only trace writer is `stages/orchestrate.py`'s `StageContext`/`run_or_resume`
  (D-041), and nothing outside `stages/orchestrate*.py` constructed a `StageContext`. A real
  CLI/UI run wrote no `trace.jsonl`, so T-172's run-view trace card had nothing to show for a real
  run.

**Live entry point found:** `ui/routes_runs.py::trigger_run` (`POST /projects/{slug}/run`) — the
**only** live case-execution path in the whole repo. There is no `autotester run` CLI command
(`cli.py` has no `@app.command("run")`; `cli_crawl.py`'s `explore_cmd` drives DISCOVER, not
EXECUTE). Wiring `run_or_resume`'s full learn/explore pipeline in here would have been a much
larger redesign than these two issues ask for (this route already has its cases via a prior
EXPAND, and its entry-case/shared-session model predates the orchestrator) — per the brief's own
"if wiring the whole orchestrator turns out to be larger than these issues imply, STOP and build
the smallest safe slice", the slice built is exactly the one the brief itself named as an example:
*"the execute path builds a StageContext with secrets and writes a trace, and runs cases via
run_cases with n from plan_parallel_run."*

## What changed

- **`src/autotester/ui/routes_runs.py`** (238 lines, was 123)
  - `trigger_run` (:186-213, was :80-122) now:
    1. builds `ctx = StageContext(store=store, run_id=run_id, secrets=secrets)` — the project's
       **real** `SecretStore`, not a fixture — so the auto-built trace's redactor is real (AT-564,
       RT6; without `secrets=` the writer falls back to an unredacted `Redactor({})`, AT-561);
    2. attaches it to the judge provider (`judge.trace = ctx.trace`) so every LLM call the judge
       makes during grading joins this run's trace (RT4/RT5 — the only span-append site stays
       `Provider.record()`, nothing here writes a span itself);
    3. calls `plan_parallel_run(project)` (T-173) **before any case executes**, and always records
       the result — `Run.parallel_n=plan.n`, `Run.parallel_bound_by=plan.bound_by` — on every run,
       serial or not (AT-562, PR1);
    4. records one `StageSpan` for `StageName.EXECUTE` (`started`/`finished` wrapping the whole
       batch) once the cases are done (RT3 — a coarse span; see Gaps).
    Steps 1-4 live in the new `_execute_with_trace` (:155-179), extracted so `trigger_run` itself
    stays under the 50-line/function cap (C2); `trigger_run` calls it at :207-209.
  - New `_run_cases_serially(...)` (:88-114) — **the pre-existing behaviour, byte-for-byte, only
    moved into its own function.** One shared `BrowserSession` reused across every non-entry case
    (login continuity), one dedicated wiped profile per entry case (AT-044). Used whenever
    `plan.n <= 1` — the default (`Project.max_parallel=1`).
  - New `_run_cases_in_parallel(...)` (:119-153) — used only when `plan.n > 1`. Entry cases still
    run first, serially, each on its own dedicated wiped profile via the existing
    `_run_entry_case` (unchanged). Non-entry cases then fan out through
    `stages.parallel_run.run_cases(normal_cases, plan, session_factory, _run_and_grade)`
    (call at :152), with `session_factory = default_session_factory(project, secrets, run_dir)`
    (T-173's own isolated per-case `BrowserSession`, PR2) and `_run_and_grade` (:144-147) wrapping
    `run_and_grade_case` (a closure capturing each case's `Verdict` in a dict, since `run_cases`'s
    `RunFn` only returns `RawResult`).
  - Imports added: `StageCheckpoint`, `StageName` (schema.run_state); `StageContext`
    (stages.orchestrate); `ParallelPlan`, `default_session_factory`, `plan_parallel_run`,
    `run_cases` (stages.parallel_run).

- **`src/autotester/stages/parallel_run.py`** (AT-565, scope-add)
  - `_run_one` (:178-205): `session = session_factory(case)` used to sit **above** the
    `try`/`except` that guards `run_fn` — so a real `BrowserSession.start()` raising under N-way
    concurrency (exactly what `default_session_factory` now drives live, per the change above)
    propagated straight out of `run_cases`'s `[f.result() for f in futures]`, discarding every
    sibling's already-finished result instead of reporting just that one case as `ERRORED` (PR6).
    Fixed by moving the assignment inside the guarded region (`session: object | None = None`,
    then `session = session_factory(case)` as the try's first line); `finally` now closes it only
    `if session is not None`.

- **Tests (new files, split from the two files these tests naturally extend, at doctor's
  300-line cap — see "Split rationale" below):**
  - `tests/test_ui_runs_parallel_trace.py` — drives the REAL `/projects/{slug}/run` route (fakes:
    `BrowserSession.start`/`close`, `run_and_grade_case`, `LangChainFallbackProvider`; a temp
    project root via `AUTOTESTER_ROOT`, never the real `.env`/`projects/`):
    - `test_a_real_run_writes_a_trace_with_at_least_one_span` — asserts `trace.jsonl` exists and
      carries exactly one `kind="stage"` span, `stage="execute"`, `status="done"` (distinct from
      the `kind="llm_call"` span the fake grading call also leaves via `judge.record(...)`).
    - `test_a_declared_fake_secret_never_appears_raw_in_the_trace` — declares a fake `SecretRef`,
      writes its value to a temp `.env`, drives a fake LLM call whose `fed_id` embeds it; asserts
      the raw value never reaches `trace.jsonl` and `"REDACTED"` does.
    - `test_run_records_parallel_n_and_bound_by_even_when_serial` — default project
      (`max_parallel=1`): asserts the persisted `Run` has `parallel_n == 1` and a `parallel_bound_by`
      in `{"config","budget","write_policy"}`.
    - `test_with_max_parallel_2_two_cases_run_concurrently` — `max_parallel=2`, `plan_parallel_run`
      monkeypatched to a fixed `ParallelPlan(n=2, bound_by="config", ...)` (the plan's own
      RAM/CPU measurement is `test_parallel_run.py`'s concern, not this wiring test's — never
      falsify against live host memory); two fake case runs record their own concurrency peak via
      a lock — asserts `peak == 2` and `Run.parallel_n/parallel_bound_by == (2, "config")`.
  - `tests/test_parallel_run_session_crash.py` — the AT-565 regression:
    `test_pr6_a_session_factory_that_raises_for_one_case_does_not_abort_siblings` — a factory that
    raises for one of three cases; asserts that case is `ERRORED` with the raised exception's
    message, and the other two report their real outcomes.

**Split rationale (C2, 300-line file cap):** both host files
(`tests/test_ui_runs.py`, `tests/test_parallel_run.py`) were already near the cap; adding these
tests in place would have pushed them to 438 and 323 lines respectively. Split following the
repo's own established convention (`tests/test_execute_assertions.py`/`test_execute_new_actions.py`
importing shared fixtures from `test_execute.py`): the new files import `_onboard_demo`/
`_only_run_id` from `test_ui_runs` and `_case`/`_project` from `test_parallel_run`, and (for
`test_ui_runs_parallel_trace.py`) duplicate the `scratch_root`/`client` pytest fixtures exactly as
every other `test_ui_*.py` file in this repo already does (a pre-existing, accepted repo-wide
pattern, not something this unit introduces or is scoped to fix). `git diff` against `master`
confirms `tests/test_ui_runs.py` and `tests/test_parallel_run.py` are byte-identical to their
pre-unit state.

## Design decisions and why (for the checker)

1. **`plan.n <= 1` is NOT routed through `run_cases`.** `run_cases`'s own contract (via `_run_one`)
   starts and closes one session per case — correct for real isolation at `n>1`, but reusing that
   contract for the pre-existing single-shared-session serial loop would tear the shared session
   down after the first case. Rather than hack a close-suppressing proxy around a session object
   `run_cases` was never designed to receive twice, the pre-existing serial loop is kept verbatim
   (moved, not rewritten) and used whenever `plan.n <= 1` — which is every project until a human
   explicitly sets `max_parallel > 1` (default `1`, `schema/project.py:133-137`). Zero behavioural
   change to the default, overwhelmingly common path.
2. **Entry cases (AT-044) always run serially, before the fan-out**, in both branches — an
   entry-screen assertion is about one genuinely-logged-out state, not something concurrency
   helps, and this preserves the existing dedicated-wiped-profile guarantee unconditionally.
3. **`RunApproval`/consent is not newly gated here.** `trigger_run` consulted no `RunApproval`
   before this unit either (confirmed: `grep -n "RunApproval\|require_approval" ui/routes_runs.py`
   returned nothing pre-unit) — this unit does not invent a new gate. `run_cases` is called with
   `approval=None` (its default), so its internal `RunBudget` is unlimited — i.e., parallel width
   cannot multiply a budget that this route did not enforce to begin with. Wiring D-018 consent
   into this route is a separate, larger unit than these two goal-coverage gaps ask for.
4. **The EXECUTE stage span is coarse** — one span wrapping the whole case batch (run + grade for
   every case), not one span per pipeline sub-stage. `run_and_grade_case` bundles execute+grade in
   one call with no seam between them at this route's level; splitting that seam is out of scope
   for these two issues and is recorded under Gaps.

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_runs.py tests/test_ui_runs_parallel_trace.py tests/test_parallel_run.py tests/test_parallel_run_session_crash.py tests/test_run_trace.py tests/test_orchestrate.py tests/test_orchestrate_runners.py tests/test_execute.py tests/test_execute_assertions.py tests/test_execute_new_actions.py tests/test_consent.py tests/test_approval_signing.py` → exit 0
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 0
- Full non-browser suite (`uv run pytest` with the 16 browser-launching files `--ignore`d) once
  RAM/exclusivity allowed — see below.

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_runs.py tests/test_ui_runs_parallel_trace.py tests/test_parallel_run.py tests/test_parallel_run_session_crash.py tests/test_run_trace.py tests/test_orchestrate.py tests/test_orchestrate_runners.py tests/test_execute.py tests/test_execute_assertions.py tests/test_execute_new_actions.py tests/test_consent.py tests/test_approval_signing.py
95 passed, 15 warnings in 3.26s
(warnings are all the pre-existing, expected AT-561 RuntimeWarning from fixture StageContexts in
test_orchestrate.py/test_orchestrate_runners.py that intentionally declare no secrets)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Full `uv run pytest` (whole suite, 16 browser-launching files excluded — this project has no
registered pytest marker, so "the project's equivalent" of `-m "not live"` is `--ignore`ing every
test file matched by `grep -rl "BrowserSession(\|sync_playwright\|playwright.sync_api" tests/test_*.py`):**
Gated on ≥3.5 GB free RAM and no other `D:/autoTesting` pytest process, polled every 300s (a
background poller measured real `GlobalMemoryStatusEx` free RAM each cycle via the same mechanism
`stages/parallel_run.py::_free_ram_mb` uses). Conditions were never met until minute 30 of the
60-minute cap (free RAM ranged 2.09-3.18 GB across the first six checks); met at 06:56:12
(3.71 GB free, no other pytest process):

```
$ PYTHONUTF8=1 uv run pytest --ignore=tests/test_agent_loop.py --ignore=tests/test_browser.py --ignore=tests/test_browser_actions.py --ignore=tests/test_browser_navigation_secrets.py --ignore=tests/test_browser_scroll_invariance.py --ignore=tests/test_browser_settle.py --ignore=tests/test_crawl_inventory_live.py --ignore=tests/test_execute.py --ignore=tests/test_execute_new_actions.py --ignore=tests/test_explore_live.py --ignore=tests/test_explore_login_spa_live.py --ignore=tests/test_explore_modal.py --ignore=tests/test_explore_secret_scrubbing.py --ignore=tests/test_explore_typing.py --ignore=tests/test_network_assertions.py --ignore=tests/test_run_case_pipeline.py --ignore=tests/test_ui_crawl_login.py
1552 passed, 5 skipped, 15 warnings in 231.01s (0:03:51)
EXIT CODE: 0
```

**No pre-existing or unrelated failure to disclose this cycle** — clean exit 0, no failures at all
(the 15 warnings are all the same expected AT-561 `RuntimeWarning` from fixture `StageContext`s in
`test_orchestrate.py`/`test_orchestrate_runners.py`/`test_run_trace.py` that intentionally declare
no secrets; the 5 skips are pre-existing and unrelated to this unit).

## Capability coverage (each new claim -> its isolating falsification)

All 5 falsifications reproduced in throwaway copies outside the worktree
(`%TEMP%\claude\...\scratchpad\mutation-copy-565\` for AT-565's own fix,
`%TEMP%\claude\...\scratchpad\mutation-copy-routes\` for the four wiring tests) — never against the
bound worktree. Baseline asserted green before every edit; each edit reverted immediately after its
red run, suite re-confirmed green before the next row.

| # | Claim | Falsifying edit | Baseline | Result |
|---|---|---|---|---|
| 1 | AT-564/RT3: a real run's trace carries an EXECUTE stage span | `_execute_with_trace`: delete the `ctx.trace.record_stage(StageCheckpoint(stage=StageName.EXECUTE, ...))` call | `4 passed` (mutation-copy-routes) | RED — `assert [] == ['execute']` → reverted → `4 passed` |
| 2 | AT-564/AT-561/RT6: the project's real `SecretStore` is threaded into `StageContext`, so a declared secret is redacted | `StageContext(store=store, run_id=run_id, secrets=secrets)` → drop `secrets=secrets` | `4 passed` | RED — secret found raw in `trace.jsonl` (`'sk-fake-AT564-...' is contained here`), plus the AT-561 `RuntimeWarning` fires → reverted → `4 passed` |
| 3 | AT-562/PR1: every run records `Run.parallel_n`/`parallel_bound_by`, even the serial default | `store.save_run(Run(...))` → drop `parallel_n=plan.n, parallel_bound_by=plan.bound_by` | `4 passed` | RED — `assert None == 1` → reverted → `4 passed` |
| 4 | AT-562/PR1-PR2: `max_parallel=2` actually fans cases out through `run_cases`, not just records a wider N | `if plan.n > 1:` → `if False and plan.n > 1:` | `4 passed` | RED — `assert 1 == 2` (peak concurrency) → reverted → `4 passed` |
| 5 | AT-565/PR6: `session_factory`'s own raise is caught and reported as that case's ERRORED outcome, not propagated | `_run_one`: move `session = session_factory(case)` back above the `try` | `11 passed` (test_parallel_run.py, pre-split) | RED — `RuntimeError: boom starting the session` propagates out of `run_cases` uncaught → reverted → `11 passed` |

Row 5 was additionally shown red on the **unmodified pre-fix code** at the point AT-565 was filed
(before any fix was applied), reproduced verbatim in `mutation-copy-565`:
```
$ uv run pytest tests/test_parallel_run.py::test_pr6_a_session_factory_that_raises_for_one_case_does_not_abort_siblings
...
E           RuntimeError: boom starting the session
1 failed in 0.39s
```
then green after the real fix landed (`11 passed in 1.26s`).

## Live browser evidence

**SKIPPED.** Free RAM measured at the time of this run: **2.09-2.55 GB**, well under the ~3.5 GB
this project's own RAM-safety rule requires before launching a real Chromium instance (the same
floor `stages/parallel_run.py::_RAM_FLOOR_MB` reserves for the OS). Multiple other python processes
were already running on this host during this session. A real-browser smoke of the changed
`/projects/{slug}/run` route is deferred — see Gaps.

## Gaps (disclosed, not fixed here)

1. **No live-browser smoke of `routes_runs.py`'s changed code paths** (RAM-gated, see above). All
   verification here is through `TestClient` + mocked `BrowserSession`/`run_and_grade_case`. The
   route's control flow (case lookup, plan computation, trace/secret wiring, persistence, redirect)
   is exercised for real; the actual Chromium launch is not.
2. **The EXECUTE stage span is coarse** (design decision 4 above) — one span for the whole
   run+grade batch, not a separate span per case or per execute/grade sub-phase. If a future unit
   wants per-case or execute-vs-grade trace granularity through this route, `run_and_grade_case`
   needs its own seam between `run_case` and `grade` first.
3. **`RunApproval`/D-018 consent is still not consulted by `trigger_run`** (pre-existing, confirmed
   absent before this unit too — design decision 3). This route can still launch a real browser
   against a real project with no human-granted approval on disk. Flagging for a future unit; not
   introduced or worsened by AT-562/AT-564/AT-565.
4. **`_run_cases_in_parallel`'s per-case `Verdict` capture (`verdicts: dict[str, Verdict]`) is not
   thread-locked.** Each case writes to a distinct key (`case.id`), so under CPython's GIL a plain
   dict assignment from multiple worker threads is safe here (no read-modify-write), but this is
   worth a second look if `run_fn`'s contract ever changes to something less atomic.

## What changed (files touched)

- `src/autotester/ui/routes_runs.py`
- `src/autotester/stages/parallel_run.py`
- `tests/test_ui_runs_parallel_trace.py` (new)
- `tests/test_parallel_run_session_crash.py` (new)

## Status: ready-for-check
