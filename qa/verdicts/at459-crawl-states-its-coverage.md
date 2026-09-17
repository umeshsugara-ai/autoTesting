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
