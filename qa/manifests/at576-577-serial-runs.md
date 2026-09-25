# Manifest — at576-577-serial-runs

**Contract:** qa/contracts/execute.md E4 + qa/contracts/ui-run.md RU1-RU4 + qa/contracts/core-invariants.md C7
**Issues addressed:** AT-576, AT-577
**Date:** 2026-09-25
**Fix cycle:** 1 of 3
**Dual check:** no
**Executor:** claude-sonnet-subagent (maker build subagent)
**Branch/worktree:** `wave/at576-577-serial-runs`, `D:/autoTesting/.worktrees/at576-577-serial-runs`
**Base:** master `80256c3`

## The bugs

**AT-576** — `ui/routes_runs.py::_run_cases_serially` started the shared, run-wide `BrowserSession`
FIRST (for login continuity across ordinary cases), then looped over every case; hitting an entry
case mid-loop called `_run_entry_case`, which starts a SECOND sync Playwright driver on the same
thread while the shared session's driver was still live. Playwright's sync API detects this and
raises `"It looks like you are using Playwright Sync API inside the asyncio loop"`, 500ing the
whole run before the remaining cases ran or the `Run` record was saved. Reproduced live on master
with no judge outage (`qa/verdicts/at574-serial-resilience.md` Mode D run 1); the ordering dates to
`939af44` (AT-044). Every unit test faked `BrowserSession.start`, so none could see it.

**AT-577** — `stages/execute.py::run_case` returned `RawResult(evidence=list(session.state.
evidence))` — the session's WHOLE evidence history, not this case's own. The serial route reuses
one `BrowserSession` across every non-entry case in a run, so by the time case 2 ran, `session.
state.evidence` already held case 1's screenshots too; case 2's `RawResult` (and case 3's, etc.)
carried every earlier case's evidence in addition to its own. The grader judged later cases partly
on earlier cases' pages, and the run view rendered earlier cases' steps under the wrong card.
Reproduced live (`qa/verdicts/at574-serial-resilience.md` Mode D run 2): "Homepage loads" case
listed evidence 01-05 where 01-04 belonged to the login case.

## Fix

**AT-577 — `src/autotester/stages/execute.py`**
- `run_case` (line ~104): added `evidence_start = len(session.state.evidence)` at entry, before any
  step runs — the index into the (possibly already non-empty) session evidence list where THIS
  case's own items begin.
- `_result` (line ~140): new `evidence_start: int = 0` keyword param; the returned `RawResult` now
  carries `list(session.state.evidence[evidence_start:])` instead of the full list. Every call site
  of `_result` inside `run_case` (BLOCKED_HITL, ERRORED, ASSERTION_FAILED, COMPLETED) passes its own
  `evidence_start`.
- `_assertions_unmet` (unchanged) already took a `pre` index scoped to a single STEP within the same
  `run_case` call — unaffected by the case-level slice, since it always reads live, un-sliced
  `session.state.evidence` at a point captured during the same call.
- **This is the one fix that repairs every reader at once**: `stages/grade.py`, `stages/
  report_export.py`, `stages/agent_loop.py` and `ui/routes_report.py` all read `result.evidence`
  (the `RawResult`'s own field), never `session.state.evidence` directly — confirmed by grep across
  `src/` (only `browser/assertions.py`, `browser/session.py`, `stages/parallel_run.py` and
  `stages/execute.py` itself touch `session.state.evidence`; none of those four are report/grade
  readers). Screenshot filenames stay unique across cases on a reused session because `session.
  state.screenshots` is a session-wide counter untouched by this fix (01, 02, 03… never resets) —
  no filename-collision risk, only the *RawResult's own list* is now scoped.
- **Independent corroboration found while fixing this:** three call-site scripts
  (`scripts/bench_trial.py:97-101`, `scripts/regression_proof.py:140-144`,
  `scripts/run_pathlynks_first_cases.py:125-137`) already work around this exact defect by hand —
  each captures `start = len(session.state.evidence)` BEFORE calling `run_case`, then overwrites
  `result.evidence = list(session.state.evidence[start:])` AFTER. `run_pathlynks_first_cases.py`
  even carries an explicit comment naming the bug: *"execute.py::run_case snapshots ALL of
  session.state.evidence, which is cumulative for the whole (reused) session, not scoped per case
  -- slice to just what THIS case adds, else case 2's RawResult would also carry case 1's evidence
  (found running this for real)."* This independently confirms both the defect and the shape of the
  fix. **Not touched here** — each script's own re-slice still does something `run_case` itself
  does not (folding in evidence recorded AFTER `run_case` returns, e.g. a post-submit screenshot),
  so it stays correct and is simply redundant-but-harmless for the portion `run_case` now already
  scopes correctly. Left as-is; changing three working scripts to remove a no-op is not this unit's
  scope.

**AT-576 — `src/autotester/ui/routes_runs.py::_run_cases_serially`** (line ~114)
- Old order: start the shared session (if any non-entry case exists) → loop over `cases` in their
  original order, branching per-case into `_run_entry_case` (own session) or the shared session.
- New order: loop over `cases` ONCE and run every entry case to completion first (own dedicated
  session, started and closed inside `_run_entry_case`, exactly as before) — **before** the shared
  session is ever constructed. Only after every entry case has finished does the shared session get
  built and started, then every non-entry case runs against it. This is the same entry-cases-first
  shape `_run_cases_in_parallel` (a few lines below in the same file) already uses — AT-576 brings
  the serial path in line with it, not a new pattern.
- Consequence: the shared session's sync Playwright driver is never live while an entry case's own
  driver starts, because the entry cases have already started AND closed their own drivers by the
  time the shared one exists. No two sync Playwright drivers are ever alive on the thread at once.
- Case order in `Run.case_ids` (built in `trigger_run` from the original `cases` list) is unaffected
  — only the *execution* order changed, not what gets recorded or in what order results are read
  back by any caller (`store.load_results` returns by case id, not insertion order).

## What changed (files touched)

- `src/autotester/stages/execute.py` — AT-577 fix (see above)
- `src/autotester/ui/routes_runs.py` — AT-576 fix (see above)
- `tests/test_execute_serial_evidence_scope.py` — **new**, 2 tests (AT-577, fast/fake)
- `tests/test_ui_runs_serial_entry_order.py` — **new**, 1 test (AT-576 ordering decision, fast/fake)
- `tests/test_ui_runs_serial_entry_mix_live.py` — **new**, 1 test (AT-576 the real live defect, real
  Chromium, RAM-gated)

No existing test file was modified.

## New tests (TDD, red first on unfixed code)

### AT-577 — `tests/test_execute_serial_evidence_scope.py`

1. `test_two_cases_on_one_shared_session_get_disjoint_evidence` — two cases run back-to-back on one
   shared fake-page `BrowserSession`; asserts `result1.evidence` and `result2.evidence` share no
   path, and that the session's own accumulated evidence equals the sum of both results' evidence
   (proves the split is a partition, not a loss).
2. `test_a_third_case_still_only_sees_its_own_slice` — three cases on one session, pairwise
   disjoint, guards the off-by-one at the second/third boundary.

**Red on unfixed code** (`git stash` of the `execute.py` fix only, both new tests run against it):
```
AssertionError: case 2's evidence must not include case 1's: shared={'01-step01-click.png', 'clicked #a'}
AssertionError: case 0 and case 1 overlap: {'01-step01-click.png', 'clicked #c0'}
2 failed in 0.76s
```
**Green after the fix** (`git stash pop`):
```
tests/test_execute_serial_evidence_scope.py ..                          [100%]
2 passed in 0.20s
```

### AT-576 (ordering decision) — `tests/test_ui_runs_serial_entry_order.py`

`test_entry_cases_start_before_the_shared_session_starts` — drives the real `/projects/demo/run`
route (`TestClient`), fakes only `BrowserSession.start`/`.close` (recording which session's
`ProjectPaths.slug` started, in order) and the provider/pipeline seams (`run_case`, `grade`) —
never the ordering logic itself. Asserts `starts == ["demo-entry-test", "demo"]` for a run mixing
one entry case with one ordinary case.

**Red on unfixed code** (`git stash` of the `routes_runs.py` fix only):
```
AssertionError: the entry case's own session must start before the shared session: ['demo', 'demo-entry-test']
assert ['demo', 'demo-entry-test'] == ['demo-entry-test', 'demo']
1 failed in 2.29s
```
**Green after the fix** (`git stash pop`):
```
1 passed
```

### AT-576 (the real defect) — `tests/test_ui_runs_serial_entry_mix_live.py`

`test_a_serial_run_mixing_an_entry_case_with_ordinary_cases_does_not_500` — the checker's own
requirement: a fake `BrowserSession.start` cannot reach AT-576 at all (Playwright's sync-API guard
only fires inside a REAL `sync_playwright().start()` call), so this test never fakes the browser.
Real `BrowserSession` driven through the real `/projects/rd/run` route (`TestClient`, which — like
`uvicorn` — runs a sync FastAPI path operation via `anyio`'s worker-thread pool, so `trigger_run`
executes on one real thread exactly as it would in production) against a local fixture site
(`tests/fixtures/regression_site`, served over real HTTP via the `serve_dir` conftest fixture) on an
isolated `AUTOTESTER_ROOT` (`tmp_path`). Only the AI provider is faked:
`routes_runs_module.LangChainFallbackProvider` → a `MockProvider` seeded with 10 queued PASS
`Judgment`s (same "swap the judge, keep the browser real" seam
`test_ui_runs_parallel_trace.py::test_a_real_run_writes_a_trace_with_at_least_one_span` already
uses). 1 entry case (navigates to `base_url`) + 2 ordinary cases (navigate to `login.html` / click
the sign-in link on `index.html`). Asserts `response.status_code == 303`, exactly one `Run` saved,
and 3 results (one per case).

**RAM-gated** (project convention, `qa/contracts/core-invariants.md`; mirrors `parallel_run.py`'s
own `_RAM_FLOOR_MB = 2048.0` plus the `/maker` dispatch prompt's stricter 3.5 GB floor for launching
a real Chromium): the test itself checks free RAM via `stages.parallel_run._free_ram_mb()` at the
top and `pytest.skip`s with the measurement below the floor, rather than launching a browser under
memory pressure on a shared host. **Live-browser evidence and disposition are in the section below.**

## Verify — targeted (real worktree, uncommitted changes at time of writing)

```
$ uv run pytest tests/test_execute.py tests/test_execute_assertions.py tests/test_execute_new_actions.py \
    tests/test_execute_serial_evidence_scope.py tests/test_ui_runs.py tests/test_ui_runs_serial_resilience.py \
    tests/test_ui_runs_serial_entry_order.py tests/test_ui_runs_serial_entry_mix_live.py \
    tests/test_ui_runs_parallel_trace.py tests/test_ui_runs_parallel_crash_recovery.py \
    tests/test_coverage_wiring.py tests/test_run_case_pipeline.py tests/test_run_case_pipeline_resilient.py \
    tests/test_grade.py tests/test_grade_evidence.py tests/test_agent_loop.py tests/test_network_assertions.py \
    tests/test_report_export.py tests/test_ui_report.py tests/test_ui_report_no_runs.py \
    tests/test_parallel_run_evidence_namespace.py tests/test_run_trace.py
134 passed, 1 skipped, 6 warnings in 8.14s
```
(1 skip = the live test, RAM-gated at collection time; 6 warnings are the pre-existing, unrelated
`test_run_trace.py` `secrets=` advisory — present on master too, not introduced here.)

Every reader of `RawResult.evidence` named by the dispatch prompt is covered: `test_grade.py`/
`test_grade_evidence.py` (grade.py), `test_report_export.py` (report_export.py), `test_ui_report.py`/
`test_ui_report_no_runs.py` (routes_report.py), `test_agent_loop.py` (agent_loop.py). The parallel
path's own tests (`test_ui_runs_parallel_trace.py`, `test_ui_runs_parallel_crash_recovery.py`,
`test_parallel_run_evidence_namespace.py`) pass unchanged — `_run_cases_in_parallel`,
`stages/parallel_run.py` and `default_session_factory`'s `evidence_prefix` (AT-572) were not
touched by either fix.

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

## Capability coverage (mutation, C7)

Never edited the worktree in place. Throwaway copy of `src/`, `tests/`, `scripts/`, `pyproject.toml`,
`uv.lock` (plus a placeholder `README.md`) at
`%TEMP%\claude\d--autoTesting\<session>\scratchpad\at576-577-capability-copy`, `uv sync --frozen`'d
independently (own `.venv`), never touching the bound worktree or `origin`; deleted after use.

**Baseline asserted green first** (C7's baseline clause):
```
$ uv run pytest tests/test_execute_serial_evidence_scope.py tests/test_ui_runs_serial_entry_order.py \
    tests/test_ui_runs_serial_resilience.py tests/test_ui_runs.py tests/test_ui_runs_parallel_trace.py \
    tests/test_ui_runs_parallel_crash_recovery.py tests/test_coverage_wiring.py
26 passed in 4.31s
```

Each mutation applied by an exact anchored string replace (a small Python script asserting
`text.count(old) == 1` before writing, refusing a silent no-op per C7's anchor clause), re-run, then
reverted by the exact inverse replace, re-run green, and the reverted file diffed byte-identical
against the real worktree's fixed file (`diff -u` → no output, `IDENTICAL`).

| # | Mutation (file, single-hunk) | Reverted behaviour | Kills (named, re-run confirmed) | Survives |
|---|---|---|---|---|
| A | `execute.py`: `_result`'s evidence line reverted to `list(session.state.evidence)` (the pre-fix full-history return; `evidence_start` computed but unused) | AT-577 exactly — every case's `RawResult` carries the whole session's evidence again | `test_two_cases_on_one_shared_session_get_disjoint_evidence`, `test_a_third_case_still_only_sees_its_own_slice` (real pytest run, `2 failed`, both assertion messages naming the exact overlapping evidence items) | All 24 other tests in the baseline set — `24 passed` alongside the 2 failures |
| B | `routes_runs.py`: `_run_cases_serially` reverted to the pre-fix shape (shared session started first when any non-entry case exists, entry/non-entry branch inline in one loop) | AT-576 exactly — the shared session starts before an entry case is ever reached | `test_entry_cases_start_before_the_shared_session_starts` (real pytest run, `1 failed`, `starts == ['demo', 'demo-entry-test']` — the exact pre-fix order) | All 25 other tests in the baseline set, **including every AT-574 resilience test** (`test_ui_runs_serial_resilience.py`'s 3 tests, `test_ui_runs_parallel_crash_recovery.py`'s 2) — confirms this mutation touches only the ordering, not AT-574's crash-guard behaviour |

Both mutations run independently (A applied+reverted, confirmed identical, before B was applied) —
never combined in one pass, so each kill is attributable to its own named test with nothing else
mutated at the same time.

## Live browser evidence — UNVERIFIED (RAM-gated)

`tests/test_ui_runs_serial_entry_mix_live.py` is written, committed, and self-gates on free RAM
(`stages.parallel_run._free_ram_mb()` vs the 3.5 GB floor) rather than ever faking `BrowserSession`
— per the dispatch instruction, never faked to force a green result.

**Measured, bounded poll** (every 300s, ≤30 min, `Get-CimInstance Win32_OperatingSystem.
FreePhysicalMemory`), run in the background for ~20 of its ≤30 minutes before being stopped once the
pattern was clear and corroborated (see root cause below), plus one final spot check:

```
12:05:56 free_mb=150.5
12:10:59 free_mb=3090.3
12:16:01 free_mb=1029.8
12:21:04 free_mb=636.7
12:23:xx free_mb=1737.4  (final spot check, after stopping the stalled full-suite background run)
```

Never once reached the 3.5 GB (3584 MB) floor across 5 measurements spanning ~20 minutes — peak was
3090 MB, still 494 MB short. Root cause confirmed, not guessed: `Get-CimInstance Win32_Process`
during this cycle showed a **second, independent Claude session actively running its own pytest
suite against this same repo concurrently** (a different session id under
`C:\Users\Lenovo\AppData\Local\Temp\claude\d--autoTesting\909303db-...`), plus unrelated live work
from `D:\tracker`, `D:\counsellor_validation_judge`, and a `hermes-agent` venv, and dozens of
pre-existing `chrome.exe` processes none of which this unit started. This is a shared, busy host,
not a dedicated runner — the same condition `at574-serial-resilience`'s manifest recorded, worse
this cycle.

**Given the shortfall's size and persistence, no Chromium was launched** — starting one under this
pressure risks a wedged process on a host other sessions depend on. Confirmed after stopping this
unit's own background tasks: `Get-CimInstance Win32_Process | Where CommandLine -match autoTesting`
shows no `python`/`pytest`/`chrome` process tied to this unit's worktree path or command line —
nothing was left running.

**Disposition: UNVERIFIED, not fixed-and-proven live.** The route-level fake-session test
(`test_ui_runs_serial_entry_order.py`) and the mutation-coverage row B above prove the ORDERING
decision is correct and load-bearing; only the claim "a REAL nested-Playwright 500 no longer
happens" is unverified this cycle. The checker's own Mode D recipe (real Chromium, `MockProvider`
swapped in-process, isolated `AUTOTESTER_ROOT`) is the standing gate for this, same as
`at574-serial-resilience`.

## Gaps (disclosed, not fixed here)

1. **The full non-browser `uv run pytest` suite (slot-1's actual verify command) did not complete
   this cycle.** Launched under the same RAM pressure described above; after 10+ minutes it had
   produced zero output (pytest itself starting is near-instant on this repo normally), consistent
   with the host thrashing under concurrent load rather than this unit's tests hanging — the
   134-test targeted subset (every touched file, every evidence reader, both new fake-session
   tests) is the evidence in its place, `134 passed, 1 skipped` (the live test), plus the
   independent mutation-coverage run against a fully `uv sync`'d throwaway copy (`26 passed`
   baseline, both mutations behaving exactly as predicted, clean revert). Stopped cleanly
   (`TaskStop`), confirmed no orphaned process. The checker's own re-run is the real gate for the
   full suite, same convention `at574-serial-resilience` recorded.

2. **`browser/assertions.py::_network_met` scans the WHOLE `session.state.evidence` for a matching
   NETWORK item**, not scoped to the current case — on a reused serial session, a later case's
   `network` deterministic assertion (D-032/T-170) could in principle read as `met` against a
   PRIOR case's captured network traffic, the same class of cross-case contamination AT-577 fixed
   for the RawResult's own evidence list, but this one lives inside a single `run_case` call's live
   assertion evaluation, not in what gets returned. Not in scope here — the dispatch prompt named
   `grade`, `report_export`, `routes_report` and `agent_loop` as the readers to check, all of which
   read `result.evidence` (fixed); `assertions.py` reads live `session.state.evidence` for a
   different purpose (a same-request deterministic check, not a report). Flagged to
   `qa/feedback-inbox.md` for the checker to judge whether it is real and in-scope for a follow-up
   unit — no case in either new test exercises a `network`-kind expected state, so this manifest
   makes no claim either way about whether it is reachable in practice.
3. **`qa/contracts/execute.md` E4's wording** ("every `Evidence` the session recorded") predates
   this fix and is now imprecise — it should read "every `Evidence` the session recorded for this
   case." Not editable by the maker (contracts are checker-owned); noted in
   `qa/feedback-inbox.md` for the checker to amend.

## Status: ready-for-check

Code + tests committed: `f30b2ac` (base master `80256c3`). This manifest and the
`qa/feedback-inbox.md` entry commit separately, after this line.
