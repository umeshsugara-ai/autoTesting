# Verdict — at459-crawl-states-its-coverage

**Cycle checked:** 1
**Date:** 2026-09-17
**Checker:** /checker Mode A + Mode D (fresh subagent), bound to `D:\autoTesting`
**Contract:** `qa/contracts/coverage.md` V7 (a)(b)(c)(d) + Verify; `explore.md` X16, X18; core-invariants C1, C2, C3, C7
**Manifest:** `qa/manifests/at459-crawl-states-its-coverage.md` (Fix cycle 1)

```
VERDICT: FAIL
SCOREBOARD: 2/4 criteria met (V7 a, c met; b, d not met), 4/4 invariants hold (C1, C2, C3, C7)
FAILURES:
- [V7b/V7d] sev: high · screens that max_depth drops are not holes and get no reason. `bound:max_depth` is never emitted, and a crawl stopped by depth can show 100%. Probe: max_depth=0 gave "100% of controls (1 of 1)", status completed, 0 holes, with 2 screens never reached. Live run 03 (max_depth=1) shows 83%, and /app/order-1001.html is not listed anywhere · take the dropped screens from NAVIGATED edges whose to_node never became a node, record each as a `bound:max_depth` hole in the counts and the Unreached sheet, and cap the figure below 100 while any exist · issue: AT-470
- [V7b] sev: medium · the wrong bound is named. Controls the per-node cap left on an EARLIER screen are labelled with the global bound that fired later. Probe: per_node_action_cap=2, max_actions=3, and "/" a.p3 is labelled `bound:max_actions`. On a LOGIN_WALL crawl the rewritten stop_reason turns a real global bound into `bound:per_node_action_cap` · name the global bound only on the screen being visited when it fired, and read the bound's name before `_terminal_status` rewrites stop_reason · issue: AT-471
- [X11/C6] sev: medium · `_finish` now reads flowspec.json. If that file is invalid (for example after a hand edit), `_finish` raises before `save_crawl`, and crawl.json stays `running` with finished_at null. Before this unit, run_crawl never read the spec · if the spec cannot be read, record the cause and leave the spec counts None, so coverage can never lose the crawl record · issue: AT-472
CAPABILITY-COVERAGE: 12/12 rows reproduced (the manifest's 11 plus a second version of V7's named sabotage)
LIVE-BROWSER: qa/evidence/browser-at459-crawl-states-its-coverage-2026-09-17-checker/report.json
ISSUES-WRITTEN: AT-470, AT-471, AT-472
EXPLANATION: The totals balance and the figure is shown correctly on every surface. On 4 of my own UI crawls (max_actions=3 → stopped_bound 50%; default bounds → completed 85%; max_depth=1 → completed 83%; no login → login_wall 66%), the tile, the Run detail row, the workbook Summary and the Unreached sheet all matched crawl.json, with 0 console errors. The named sabotage (drop not_visited, or drop bound:*, from the tally) fails on the "(c) the books must balance" assertion. It fails V7 on two points. First, V7(b) lists `bound:max_depth` in its closed set and says "an unreached screen … with no reason fails". The manifest's disclosed depth gap is exactly that, has no issue id, and makes V7(d)'s "a crawl that stopped on a bound can never display 100%" false. Second, the per-node-cap reason is attributed wrongly. Questions, not failures: `is_candidate` restates visit_node's filter instead of visit_node calling it, which is a C3 drift risk. A COMPLETED crawl with 0 discovered controls reads "100% (0 of 0)", which is defensible. AT-459 stays open. Push held (origin/master..HEAD carries another session's unverified AT-419 commits).
```

## What was re-run (by the checker)

- **Bound tree:**
  - `uv run pytest tests/test_crawl_coverage.py tests/test_crawl_report.py tests/test_crawl_status_surfaces.py tests/test_ui_crawls.py tests/test_explore.py tests/test_explore_blocked.py tests/test_explore_login_wall.py -p no:cacheprovider -o addopts= -q` → `80 passed`.
  - `uv run ruff check src tests scripts` → `All checks passed!`
  - `uv run autotester doctor` → `doctor: clean`
- **Full suite:** run once in the checker copy (`git archive HEAD` plus the unit's 8 files; projects/erp, pathlynks and vidysea-erp deleted right after extraction). Result: `2 failed, 1391 passed, 2 skipped, 32 xfailed`. Both failures come from the environment, not the unit, and each passed when re-run in the bound tree (`2 passed`):
  - `test_uploaded_recordings_are_gitignored`: the copy is not a git repo.
  - `test_a_scrolled_pane_inside_a_scrolled_pane_loses_nothing`: Windows `net::ERR_NO_BUFFER_SPACE`.
- **Capability coverage:** reproduced in a second copy (`checker-at459-sab`), where `crawl_coverage.__file__` was asserted inside the copy. The named set was green before (`17 passed`). Each row got a single-hunk edit and was restored in `finally`. Every row went red on its own named assertion:
  - the (c) balance message, for both tally drops
  - `assert 100 < 100`
  - `{'policy:form…read_only': 1} == {'login_wall': 1}`
  - `(2 >= 1 and 0 >= 1)`
  - `assert 0 >= 1`
  - `{'bound:per_n…': 2} == {'error': 2}`
  - `(None, 2) == (1, 2)`
  - `None is not None`
  - the headline-tile message
  - `assert 0 == 7`
  - `'not recorded' in …`

  After the restore: `11 passed` and `17 passed`. **Disclosure:** an accidental second, killed run of the harness left two files in that scratch copy sabotaged. I detected this with `cmp` against the bound tree, restored both files, got the copy green again, and then re-ran the whole harness cleanly. The results above come from the clean run. The bound tree was never edited.
- **Probes** (fake site plus `compute_coverage`, results in report.json `probes_fake_site`):
  - Duplicate selectors on one screen: counted once, correct.
  - DIALOG outcome: counted as exercised, and the rest of the aborted screen is `error`.
  - ERRORED then performed, and performed then ERRORED(BACK): both exercised.
  - DENIED then performed: cannot happen in real code (deny_reason is per element), and even synthetically it is exercised.
  - 0 discovered: 100 only for COMPLETED, 0 for every other status.
  - A legacy crawl.json with no `coverage` key loads with `None`.
  - An invalid flowspec loses the envelope (AT-472).
- **Mode D:** headed Playwright Python (Chromium), with my own driver. Setup:
  - The login_site fixture was served from the copy on 127.0.0.1:8772, and the UI from the copy on 127.0.0.1:8067.
  - A fresh scratch AUTOTESTER_ROOT was seeded through ProjectStore with synthetic `covprobe`, which declares its login case through `Project.login_case_id`, and `wallprobe`, which has no login. Each has a CRAWL approval.
  - Both servers were stopped by PID afterwards and the browser was closed.

## Not committed by the checker

`qa/issues.jsonl` holds another session's uncommitted hunks. I appended AT-470, AT-471 and AT-472 to it and did **not** commit it. The unit's code is not committed.

## Cycle 2

**Cycle checked:** 2
**Date:** 2026-09-17
**Checker:** /checker Mode A + Mode D (fresh subagent), bound to `D:\autoTesting`. An earlier cycle-2 checker died on a network error and wrote no verdict. Nothing it produced was reused: I made a new copy, `scratchpad/checker-at459c2b`, and replaced its three partial PNGs in the evidence folder.
**Manifest:** `qa/manifests/at459-crawl-states-its-coverage.md` (Fix cycle 2)

```
VERDICT: FAIL
SCOREBOARD: 4/4 criteria met (V7 a, b, c, d), 4/4 invariants hold (C1, C2, C3, C7) -- failed on capability coverage (Mode A step 4b)
FAILURES:
- [V7b / step 4b] sev: medium · the manifest claims `_tried` excludes policy/unnamed refusals and pre-refused off-domain links (the OFF_DOMAIN_LINK_REFUSED constant was added for it), but no check isolates either exclusion and there is no Capability-coverage row for them. Deleting `and e.outcome not in REFUSED_BEFORE_TRYING`, or the OFF_DOMAIN_LINK_REFUSED clause, leaves the named set at 25 passed, while a real fake-site crawl (cap 3, max_actions 2, "/" = a refused control, then p1, p2, p3) then labels a.p3 `bound:per_node_action_cap` instead of `bound:max_actions` · add a crawl test per exclusion (a refusal, and separately a pre-refused off-domain link, before the control a global bound cut short on a screen that did not spend its cap) and a row for each · issue: AT-476
CAPABILITY-COVERAGE: 12/12 manifest rows reproduced (V1 in three variants, C1-C6, V8, plus X3); 2 claimed-but-unenumerated sub-capabilities SURVIVED (X1, X2 -> AT-476)
LIVE-BROWSER: qa/evidence/browser-at459-crawl-states-its-coverage-2026-09-17-checker-c2/report.json
ISSUES-WRITTEN: AT-476, AT-477; AT-470, AT-471, AT-472 set to fixed; AT-459 stays open
EXPLANATION: All three cycle-1 findings are really fixed. My probes: max_depth=0 with one exercised link now reads 99 and lists the screen as bound:max_depth. With cap 2 and max_actions 3, "/" a.p3 is bound:per_node_action_cap. A real LOGIN_WALL crawl stopped by max_actions still names bound:max_actions. An invalid flowspec.json still finishes the crawl, with spec_error set. Live, in headed Chromium, the max_depth=1 crawl lists the screen behind "Order 1001" as not entered with bound:max_depth on the page, in Run detail, in the workbook Summary and on the Unreached sheet, at 83%, with 0 console errors. The only failure is one untested claim in the AT-471 fix. The code is correct today, but nothing in the tests stops that exclusion from regressing.
```

## What was re-run (by the checker, cycle 2)

- **Bound tree:**
  - The 8-file pytest set (coverage, coverage_bounds, crawl_report, crawl_status_surfaces, ui_crawls, explore, explore_blocked, explore_login_wall) gave `88 passed`.
  - `uv run ruff check src tests scripts` gave `All checks passed!`.
  - `uv run autotester doctor` gave `doctor: clean`.
- **Full suite** (once, bound tree, sequential, in the background): `uv run pytest -p no:cacheprovider -o addopts= -q -rx` gave `1404 passed, 2 skipped, 32 xfailed, 1 warning in 549.25s`, exit 0.
- **Copy setup:** `git archive HEAD` went into `scratchpad/checker-at459c2b`. projects/erp, pathlynks and vidysea-erp were deleted immediately; only `regression-demo` was left. Then:
  - all 11 unit files were copied in and checked with `cmp`;
  - `uv sync` was run;
  - `crawl_coverage.__file__` and `crawl_view.__file__` were asserted to be inside the copy.
- **Capability coverage** (in the copy). The named set (`test_crawl_coverage.py`, `test_crawl_coverage_bounds.py`, `test_crawl_report.py`) was green before the edits at `25 passed` and green after them at `25 passed`. Each edit was a single hunk and was restored in `finally`.

  | Row | Edit | Result |
  |---|---|---|
  | V1a (V7 Verify) | drop `not_visited` from the `by_reason` tally | 4 failed, `(c) the books must balance...` first |
  | V1b | drop the `not_visited` hole | 3 failed, `(c) the books must balance...` |
  | V1c | drop `bound:*` from the tally | 6 failed, the balance message first |
  | C1 | `not_entered = []` | `the dropped screens must be listed` and `[] == ['bound:max_depth']` |
  | C2 | `whole = status is COMPLETED` | `a crawl a bound kept out of a screen can never read 100 (V7d)` |
  | C3 | per-node cap ignored | `a.p3 ... reason='bound:max_actions'` |
  | C4 | `bound=rt.stop_reason` | `'stopped at a...a form submit' == 'max_actions'` |
  | C5 | no try around `load_flowspec` | `ValueError ...flowspec.json: 1 validation error` |
  | C6 | `except ZeroDivisionError` | `RuntimeError: graph was unreadable` |
  | V8 | delete the `"coverage"` line in explore.py | 11 failed, `None is not None` |
  | X3 | depth reason always `max_screens` | `{'bound:max_screens'} == {'bound:max_depth'}` |
  | **X1** | drop the refusal exclusion from `_tried` | **SURVIVED (25 passed)** |
  | **X2** | drop the off-domain exclusion from `_tried` | **SURVIVED (25 passed)** |

  - **Disclosure:** my first V1b edit, `(None if ... else holes.append)(...)`, reddened for the wrong reason. It raised TypeError, which `of_run` recorded as `coverage.error`. I discarded that result and re-ran V1b as `if reason != 'not_visited': holes.append(...)`.
  - The first V1a, V1c and V8 anchors missed because those files use CRLF line endings. They were re-run with CRLF-aware anchors, and the results above come from that re-run.
- **Probes** (in the copy; stored in report.json under `probes_scratch_copy`):
  - **P1:** max_depth=0 with one link reads `99% (1 of 1)`, and the screen is not entered with bound:max_depth. On the default site the result is 66, with both links' screens listed.
  - **P2:** with cap 2 and max_actions 3, "/" a.p3 is `bound:per_node_action_cap` and /p1 a.l12 is `bound:max_actions`.
  - **P3:** a real LOGIN_WALL crawl stopped by max_actions=2 names `button.c` `bound:max_actions` and `button.go` `login_wall`.
  - **P4:** with an invalid flowspec.json, the saved crawl is `completed`, finished_at is set, spec_error is set, and the other numbers are computed.
  - **P5:** the clock jumps past wall_clock_s after a completed crawl, and no hole says wall_clock_s.
  - **P6:** the clock jumps after a max_actions stop, and the bound named is still max_actions.
  - **P7:** `is_candidate` equals the old inline filter on all 8 visible/enabled/obscured combinations.
- **Judgements asked for:**
  - **(1) The `bound:max_screens` screens-not-entered branch really is unreachable.** `visit_node` checks `stop_reason` (max_screens first) before every action. `_enqueue` only runs after an action taken while `screens_found < max_screens`, so it can only drop a screen for depth. V7(b) is then met by the untried control carrying `bound:max_screens`: the unknown screen behind an untried link has no identity to list, and its control carries the reason.
  - **(2) Keeping `screens_not_entered` separate is consistent with V7.** V7(a)/(c) define the identity over controls on screens reached. The link that led to a dropped screen WAS exercised, and the dropped screen carries its own reason. The figure is capped below 100 while any exist, and it is shown on the page, in Run detail, in the Summary and on the Unreached sheet.
  - **(3) `_tried` counts what visit_node's cap counts.** `try_action` writes exactly one edge per counted action (ERRORED, NavigationRefused OFF_DOMAIN with the exception text, DIALOG, SAME_SCREEN, NAVIGATED). `_candidate_denial` writes DENIED_POLICY, SKIPPED_UNNAMED or OFF_DOMAIN with the constant, and none of those are counted. BACK is written only on nodes that are later ABORTED. This is correct, but the exclusions are untested (AT-476).
  - **(4) `stop_reason(rt)` at `_finish` can return `wall_clock_s` on a crawl that completed (P5), but no hole can carry it.** A no-edge candidate on an EXPLORED screen with tried < cap exists only when visit_node broke on `stop_reason`. After that the counters are frozen, and wall_clock_s has the lowest precedence.
  - **(5) Moving the filter to `is_candidate` does not change crawl behaviour** (P7, and 88 explore/crawl tests green).
- **Mode D:** headed Playwright Python (Chromium), with my own driver.
  - **Setup:**
    - The login_site fixture was served from the copy on 127.0.0.1:8774, and the UI from the copy on 127.0.0.1:8069.
    - A fresh scratch AUTOTESTER_ROOT was seeded through ProjectStore with two synthetic projects, `covtwo` and `covbadspec`. Each has a declared login case and a CRAWL approval.
  - **max_depth=1 crawl:** status completed, **83% (5 of 6)**.
    - The first tile is "83% COVERAGE".
    - The page line reads "screens not entered: BOUND:MAX_DEPTH: 1".
    - Run detail and the workbook Summary both show "Screens not entered, by reason = bound:max_depth: 1".
    - The Unreached sheet has the row "screen behind 'Order 1001' -- not entered | bound:max_depth".
    - 0 console errors.
  - **max_actions=3 crawl:** stopped_bound, **50% (3 of 6)**, with bound:max_actions 1, not_visited 1 and policy 1. The Unreached rows equal the holes, and there were 0 console errors.
  - **Invalid flowspec (covbadspec):** crawl.json is `completed` with finished_at set and spec_error set. The workbook's "FlowSpec screens reached" says "could not read the FlowSpec -- ValueError ...".
    - But POST /explore returns 500 after the crawl is saved, and the crawl page returns HTTP 500.
    - The 2 console errors are exactly those two 500s. They come from `routes_crawls.py:247` and `:154`, which call `load_flowspec()` without a guard. That file is not touched by this unit and the behaviour predates it, so it is filed as **AT-477** and not charged to this unit.
  - Both servers were stopped by PID (13152 and 62740), and the ports were confirmed free. The browser was closed.
- **Question, not a failure:** when `coverage.error` is set, `crawl_view.summary_stats` still renders the headline tile from `cov.percent`, which reads "0%", beside the line "could not be computed". Should the tile show "--"?

## Not committed by the checker (cycle 2)

`qa/issues.jsonl` holds other sessions' uncommitted hunks. I set AT-470, AT-471 and AT-472 to fixed, appended AT-476 and AT-477, and did **not** commit it. The unit's code is not committed. The push is held because origin/master..HEAD carries 9 commits from other sessions that I have not verified.
