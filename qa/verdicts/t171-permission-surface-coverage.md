# Verdict - t171-permission-surface-coverage

**Cycle checked: 2**
**VERDICT: PASS**
Date: 2026-09-30 - Checker: claude-sonnet-subagent (fresh context) - Bound to `D:/autoTesting/.claude/worktrees/agent-a34c44eb5901959f8` (branch `worktree-agent-a34c44eb5901959f8`, cycle-2 commit `fdd1d90c`)
Judged against: `qa/contracts/permission-surface.md` PS1-PS4 (now present in the tree via the master merge; DRAFT, goes ACTIVE on this PASS) plus `qa/contracts/coverage.md` V9 (the criterion the manifest names) with V7(a)-(d). No contract file was edited.
Merge first: `git merge master` into the branch, clean, no conflicts (merge commit `8fdee498`).
Diff scope (step 4c): cycle-2 commit alone, `git diff fdd1d90c^1 fdd1d90c`: 5 src/tests files (`explore.py` +1, `explore_node.py` +4/-4, `explore_runtime.py` +3/-1, `explore_traversal.py` +64, `tests/test_permission_coverage.py` +26) plus the manifest and one evidence file. All listed in the manifest's cycle-2 "What changed" table. Removed lines: a 2-line AT-533 comment folded to 1 line and one blank line (net-zero to stay at the 300-line cap, disclosed), and the `explore_runtime` import line extended. No function, class, export, route, test or config key deleted or renamed.

SCOREBOARD: 5/5 criteria met (PS1, PS2, PS3, PS4, V9); permission-surface.md carries no [I*] invariants; V7(a)-(d) hold (their tests pass).

## What I re-ran (bound worktree, real output, none pasted from the manifest)

| Command | Result |
|---|---|
| `uv run pytest tests/test_permission_coverage.py tests/test_crawl_coverage.py tests/test_crawl_coverage_bounds.py tests/test_coverage_wiring.py tests/test_explore.py tests/test_explore_safety.py` | 133 passed in 169 s (`.work/checker-c2-pytest-unit.txt`) |
| neighbours: 24 further `test_explore_*`, `test_crawl_*`, `test_coverage`, `test_store_crawl`, `test_goal_contract_registration`, `test_ui_crawls`, `test_consent` files (live-browser files excluded) | 210 passed in 1507 s (`.work/checker-c2-pytest-neighbours.txt`) |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` on the merged tree | 1 violation: `stale-generated: docs/SNAPSHOT.md`. **Not attributable to T-171**: (a) the same command on an archive of the unit's own commit `fdd1d90c` prints `doctor: clean`; (b) the same command on an archive of master `bc25ad17` prints the same single violation, so master's committed SNAPSHOT is already stale. The maker regenerates it with `autotester snapshot` at merge. |
| full suite | NOT run, by instruction (RAM); the maker runs one after merge. The manifest's claim `2190 passed` was not re-derived by me. |

## PS2 - the cycle-1 failure, re-derived on a real crawl

I ran the fake-site crawl myself under `ALLOW_WRITES` from a copy of the merged tree: the recorded edge order ends `10 /students/{id} button.edit same_screen`, `11 /settings button.del navigated`. The destructive press is now the LAST action across the whole crawl; cycle 1 had it at edge 10, before `button.edit`. `drain_deferred` runs once after the frontier drains (`explore.py:168`), parked controls are pressed in park order, each after `return_to` its screen.
Behaviour checked beyond the manifest's test:
- `max_actions=6`: the destructive control is never pressed and lands as a hole `bound:max_actions`; book balance `exercised + holes == discovered` holds (6 + 6 == 12).
- `READ_ONLY`: `button.del` is denied in place (`policy:destructive-name deny-list`), not deferred; book balance holds (5 + 7 == 12).
- `ALLOW_WRITES`, full: the screen first reached BY the destructive press (`/deleted`) stays `queued`, `stop_reason` reads `destructive_last (1 screen(s) first reached by a destructive press were recorded, not explored)`, status `stopped_bound`, percent 58 not 100. Disclosed in the manifest's limits; never reads "complete".
- `try_action` has exactly two callers (`explore_node._click_loop`, `explore_traversal.drain_deferred`); no other path presses controls.

## Capability coverage (step 4b) - 12/12 rows reproduced

Each row in its own throwaway copy (`git archive HEAD` of the merged tree, lean copy, outside the bound root; the worktree interpreter with `PYTHONPATH` at the copy; `autotester.__file__` printed and confirmed to resolve inside each copy). Every copy was GREEN before the edit, then one single-hunk edit to one file named in "What changed" (hunk occurrences = 1 asserted before writing), then RED. Bound tree never edited.

| Row | Edit (file) | GREEN before -> assertion that fired |
|---|---|---|
| R1 | delete the permitted `coverage.percent = _percent(...)` re-base (crawl_coverage.py) | 1 passed -> `assert 100 == 25` "the figure must be a fraction of the permitted surface" |
| R2 | `continue` before `permitted_holes.append` (crawl_coverage.py) | 1 passed -> `assert {} == {'#never': 'not_reached'}` "not reached is a REASON, not an absence of one" |
| R3 | count a `policy:` hole as exercised (crawl_coverage.py) | 1 passed -> `assert [] == [('#pay', 'policy:deny-list: pay')]` |
| R4 | `if control.destructive and policy is not ALLOW_WRITES` -> `if False` (crawl_coverage.py) | 1 passed -> `'not_reached' != 'policy:destructive under read_only'` |
| R5 | drop the `denominator is screens-reached, NOT permission coverage` clause (crawl_report.py) | 1 passed -> `'NOT permission coverage' in '100% of controls (1 of 1)'` |
| R6 | delete the `Coverage denominator` row (crawl_report.py) | 3 passed -> 3 failed (`KeyError: 'Coverage denominator'` x2, page assertion) |
| R6b | permitted_holes loop -> `for hole in []` in `_unreached_sheet` (crawl_report.py) | 1 passed -> `assert set() == {'#b', '#pay'}` |
| R7 | `permitted=rt.project.permitted_surface` -> `None` (crawl_coverage.py) | 1 passed -> `'screens-reached' == 'permitted'` |
| R8 | `return list(elements)` in `destructive_last` (explore_safety.py) | 1 passed -> `'Delete account' != 'Open'` at index 0 |
| R9 | iterate `node.elements` instead of `destructive_last(...)` (explore_node.py) | 1 passed -> `assert 2 == (6 - 1)`, real recorded order shows `button.del` at index 2 |
| R10 | `_key` returns the host-exact `(url_template, selector)` (crawl_coverage.py) | 1 passed -> `assert (0, 4) == (1, 4)` |
| **R12** | `if not is_destructive(...)` -> `if True or not is_destructive(...)` in `defer_destructive` (explore_traversal.py) | 1 passed -> `assert not True` over the recorded sequence `[... ('button.save', 'navigated', False), ('button.del', 'navigated', True), ...]`: the crawl-global assertion the row is named for, not a load/parse failure |

No row survived. R9 still bites after the deferral change (it guards the per-screen order that remains in place). Traps considered: R12's test reads the edges a real fake-site crawl recorded (not a list the test built) and asserts more than one source screen and that both kinds were pressed, so the fixture cannot decide the outcome; the check does not read live state to judge live state. A blind spot, not a failure: the test counts only NAVIGATED/SAME_SCREEN edges as presses, so a destructive press that ended DIALOG/ERRORED would not be ordered by it.

## Criteria

- **PS1 - met** (unchanged since cycle 1; `test_explore_consent`, `test_consent` pass). Approval half reused from `explore_consent`, not rebuilt.
- **PS2 - met.** Crawl-global ordering evidenced on a real crawl and by R12. `[D-040 verbatim]` is honoured, not re-scoped: every destructive press is after every non-destructive one; a denied destructive control is recorded in place because a refusal is not an exercise.
- **PS3 - met.** Same `CoverageHole` model and closed reason set; R3; V7(c) tests pass; the deferred-then-unpressed case still balances (probe above).
- **PS4 - met.** One percent computation (`_percent` via `compute_coverage`); no new surface with its own figure.
- **V9 - met** (R1-R7, R10; live page/workbook proof from the cycle-1 Mode D; nothing under `ui/` or the report code changed since).

## Issues addressed (step 5)

- ISS-t171-1 (PS2 per-screen): fixed by this unit -> `fixed`, regression_check `uv run pytest tests/test_permission_coverage.py` (fails with the fix reverted: R12).
- ISS-t171-2 (manifest hygiene): placeholder replaced with real output, `tests/test_permission_coverage.py` in "What changed", `Persona walk: skip (...)` present and its reason is true (no screen/route/control added) -> `fixed`.
- ISS-t171-3 (`test_goal_contract_registration`): cleared by the master merge; passes in my neighbour run -> `fixed`, regression_check `uv run pytest tests/test_goal_contract_registration.py`.
`fixed -> verified` remains a later re-check.

## Questions (not failures)

- Under `ALLOW_WRITES`, any crawl where a destructive control navigates to a new screen now ends `stopped_bound` with `stop_reason destructive_last (...)`, though no bound fired. The reason string is honest; the status label is not. Worth a wording decision by the maker/Umesh.
- `drain_deferred` on a dialog storm drops the node's remaining parked controls; their hole reason then falls to the generic `_untried_reason` (`bound:per_node_action_cap` when no global bound is set), which may mislabel a dialog abort. Not exercised by any test; I did not reproduce a wrong reason.

## LIVE-BROWSER (Mode D, step 5b)

not-applicable: cycle-2 changed paths are `src/autotester/stages/explore*.py` and `tests/` only; nothing under `ui/`, no template, no report renderer. The playwright MCP failed to connect this session, so I did not open a browser and do not claim one. The cycle-1 checker's Mode D evidence (`qa/evidence/browser-t171-permission-surface-coverage-2026-09-29-checker/`, 0 console errors) covers the UI surface, which is byte-unchanged. Untested: the rendering of the new `destructive_last (...)` stop_reason string on the crawl page.

## Return block

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, no invariants in this contract (V7(a)-(d) hold)
FAILURES: none
CAPABILITY-COVERAGE: 12/12 rows reproduced
LIVE-BROWSER: not-applicable (src/autotester/stages/explore*.py + tests only; cycle-1 Mode D stands)
ISSUES-WRITTEN: none new; ISS-t171-1, -2, -3 moved open -> fixed
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
```

---

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
