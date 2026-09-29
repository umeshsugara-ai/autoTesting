# Verdict - t171-permission-surface-coverage

**Cycle checked: 1**
**VERDICT: FAIL**
Date: 2026-09-29 - Checker: claude-sonnet-subagent (fresh context) - Bound to `D:/autoTesting/.claude/worktrees/agent-a34c44eb5901959f8`
Judged against: **master's** `qa/contracts/permission-surface.md` (PS1-PS4; the worktree has no copy) plus `qa/contracts/coverage.md` V9 (the criterion the manifest names) with V7(a)-(d).
Diff scope: `b3060667..ffbea539`. Executor: manifest names none (claude build subagent); the checker is a different fresh subagent.

SCOREBOARD: 4/5 criteria met (PS1, PS3, PS4, V9; PS2 not). permission-surface.md carries no [I*] invariants; V7(a)-(d) still hold (their tests pass).

## What I re-ran (all in the bound worktree, real output, none pasted from the manifest)

| Command | Result |
|---|---|
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest tests/test_permission_coverage.py tests/test_crawl_coverage.py tests/test_crawl_coverage_bounds.py tests/test_coverage_wiring.py` | 46 passed |
| `uv run pytest` (once, redirected to a file, no `-q`) | **1 failed, 2174 passed, 6 skipped, 14 xfailed** in 26m42s. The one failure is `tests/test_goal_contract_registration.py::test_revised_goal_contract_is_registered`: `.goal/goal.json` has T-167 depending on `['T-166','T-110','T-179']` (D-057) while the test pins `['T-166','T-110']`. Neither `.goal/` nor that test is in the unit's diff, so it is red at the base too and **not attributable to T-171** (ISS-t171-3, medium, pre-existing). |

The manifest's Verify section contains the literal `PYTEST_OUTPUT_PLACEHOLDER` instead of suite output (ISS-t171-2, low). My own run above replaces it.

## Capability coverage (step 4b) - 11/11 rows reproduced

Each row in its own throwaway copy under the checker scratch dir (outside the worktree and outside D:/autoTesting; `.git`, `.venv` and caches excluded; the worktree's interpreter with `PYTHONPATH` pointed at the copy, and `autotester.__file__` confirmed to resolve inside the copy). Every copy was **GREEN before the edit** (11 green runs, exit 0, run in the copy), then one single-hunk edit to one file named in "What changed", then RED. The bound tree was never edited.

| Row | Edit (file) | Assertion that fired |
|---|---|---|
| R1 | delete the `coverage.percent = _percent(permitted...)` re-base (crawl_coverage.py) | `assert 100 == 25` "the figure must be a fraction of the permitted surface" |
| R2 | `continue` before `permitted_holes.append` (crawl_coverage.py) | `assert {} == {'#never': 'not_reached'}` "not reached is a REASON, not an absence of one" |
| R3 | count a `policy:` hole as exercised (crawl_coverage.py) | `assert [] == [('#pay', 'policy:deny-list: pay')]` |
| R4 | delete the destructive-under-tier branch (crawl_coverage.py) | `['not_reached'] == ['policy:destructive under read_only']` |
| R5 | drop the "NOT permission coverage" clause (crawl_report.py) | `'NOT permission coverage' in '100% of controls (1 of 1)'` |
| R6 | delete the "Coverage denominator" row (crawl_report.py) | `KeyError: 'Coverage denominator'` x2 plus the page assertion (3 red) |
| R6b | delete the permitted_holes loop in `_unreached_sheet` (crawl_report.py) | `assert set() == {'#b', '#pay'}` |
| R7 | `permitted=rt.project.permitted_surface` -> `None` (crawl_coverage.py) | `'screens-reached' == 'permitted'` |
| R8 | `return list(elements)` (explore_safety.py) | `'Delete account' != 'Open'` at index 0 |
| R9 | iterate `node.elements` again (explore_node.py) | `assert 2 == (6 - 1)`, recorded order has `button.del` at index 2 |
| R10 | `_key` returns `(url_template, selector)` (crawl_coverage.py) | `assert (0, 4) == (1, 4)` |

No row survived, and each fired the assertion its test is named for. **These rows prove the per-screen ordering and the V9 arithmetic are real. They do not prove PS2 as written**, because R8 and R9 assert only same-screen order (see the failure below).

## Criteria

- **PS1 - met, on its own terms.** On the declared-surface path every permitted control ends up exercised or carrying one closed-set reason, and `permitted_exercised + len(permitted_holes) == permitted_total` holds by construction (R2/R3/R4 pin it). Approval is reused from `explore_consent` (no second gate); the no-approval negative is `tests/test_explore.py::test_a_crawl_without_an_approval_refuses_and_writes_nothing`, which passes in my run. The manifest's PS1-vs-`write-policy-tier.md` disagreement is filed in `qa/feedback-inbox.md` and not silently resolved, which is correct handling.
- **PS2 - NOT MET.** See failure below.
- **PS3 - met.** Same `CoverageHole` model and closed reason set with one member added (`not_reached`); R3 shows a blocked control never counts as covered; the V7(c) tests still pass.
- **PS4 - met (one number).** A grep finds exactly one percent computation (`_percent`, called from `compute_coverage`); the crawl page, workbook and `crawl.json` all render that same field. The builder added rows and pills to existing V7 surfaces, not a new surface with its own figure.
- **V9 - met.** The denominator is the declared permitted set; every miss is listed with a reason (R1-R4, R6b, R7, R10); with no declaration the figure says "denominator is screens-reached, NOT permission coverage" (R5); nothing narrows a run (`_permitted_reason` reads the run's `write_policy`, never sets it). A question rather than a failure: V9 bullet 3 also says a screens-reached figure "never reports 100%"; the unit keeps V7(d)'s "100 only when the whole product was seen" and labels the figure. That reading matches V7's stated rule and is defensible.

## FAILURES

- **[PS2] sev: high.** PS2 is `[D-040 verbatim]`, "not arguable", and reads: "Every destructive action's position in the exercise sequence is after every non-destructive one." The unit reorders only **within one screen** (`explore_node._click_loop` calls `destructive_last` per node). I ran a real fake-site crawl under `ALLOW_WRITES` and printed the recorded edge order (`qa/evidence/browser-t171-permission-surface-coverage-2026-09-29-checker/ps2-global-order.txt`): edge 10 is `/settings button.del navigated` (destructive, actually pressed) and edge 11 is `/students/{id} button.edit same_screen` (ordinary). A destructive action ran **before** a non-destructive one. The manifest itself concedes this under "Known limits" ("`destructive_last` orders within one screen, not across the crawl ... a global destructive-last pass ... is not claimed here") while its PS table says "PS2: Yes". Per-screen ordering is the re-scope the contract forbids; the contract's Verify clause (a fixture ordering) does not license it, because the criterion text is global. Fix direction: defer destructive controls across the whole crawl (a destructive-last pass once the frontier is drained, or a deferred queue the traversal drains last), with a failing-first sabotage on that global order; or, if per-screen granularity is what Umesh wants, that is a superseding decision against D-040, not a maker call. Issue: **ISS-t171-1**.

Lower severity, not gating:
- **ISS-t171-2** (low): unfilled `PYTEST_OUTPUT_PLACEHOLDER`; `tests/test_permission_coverage.py` touched but missing from "What changed" (disclosed under "What I could NOT do" #6); no `Persona walk:` field on a post-2026-09-26 manifest.
- **ISS-t171-3** (medium): pre-existing suite red at the base, unrelated to this unit.

## Diff scope (step 4c)

`git diff b3060667..ffbea539 --stat`: 12 files, +696/-19. Every removed line is an in-place rewrite: the `by_reason()` body moved into `_tally`, the `percent=` expression moved into `_percent`, the `CoverageHole.reason` description was extended, and the test runtime stub was extended. **No function, class, export, route, test or config key was deleted or renamed.** The only touched file absent from the manifest's "What changed" table is the new `tests/test_permission_coverage.py` (ISS-t171-2).

## LIVE-BROWSER (Mode D, step 5b)

`qa/evidence/browser-t171-permission-surface-coverage-2026-09-29-checker/report.json`. My own Chromium against my own `uvicorn autotester.ui.app:app` from the worktree venv on 127.0.0.1:8151, with `AUTOTESTER_ROOT` at a scratch dir; two crawls of the fake site were seeded, one with a declared 6-control surface and one without. Asserted on the rendered DOM: the declared-surface page reads `33% of controls (2 of 6 the account's role permits)` with four "permitted but not exercised" reasons (4 + 2 = 6); the undeclared page reads `41% of controls (5 of 12) - denominator is screens-reached, NOT permission coverage` and shows no permitted pills. I clicked the Excel link (browser download) and read the same URL's workbook with openpyxl: Summary carries the denominator and permitted-by-reason rows, and Unreached carries the 4 named permitted holes. **Console errors: 0 on every page.** The crawl page is a read-only report with no control that changes the figure, so the interaction was navigation, download and reading the artifacts. Persona walk: not run (the manifest has no `Persona walk:` field; the product is an internal tool; low finding filed).

## GOAL wiring

FAIL, so T-171 stays open; no `goal_cli.py done` call.

## Return block

```
VERDICT: FAIL
SCOREBOARD: 4/5 criteria met, no invariants in this contract (V7(a)-(d) hold)
FAILURES:
- [PS2] sev: high - destructive-last is per-screen; a real ALLOW_WRITES crawl presses destructive button.del (edge 10) before ordinary button.edit (edge 11) - make the ordering crawl-global with a failing-first sabotage, or take a superseding decision on D-040 - issue: ISS-t171-1
CAPABILITY-COVERAGE: 11/11 rows reproduced
LIVE-BROWSER: qa/evidence/browser-t171-permission-surface-coverage-2026-09-29-checker/
ISSUES-WRITTEN: ISS-t171-1, ISS-t171-2, ISS-t171-3
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
```
