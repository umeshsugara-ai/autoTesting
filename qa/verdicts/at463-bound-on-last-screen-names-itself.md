# Verdict — at463-bound-on-last-screen-names-itself

**Date:** 2026-09-17
**Cycle checked:** 1
**Checker:** /checker Mode A + Mode D, fresh subagent, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at463-bound-on-last-screen-names-itself.md` (Fix cycle 1, ready-for-check)
**Contract:** `qa/contracts/explore.md` X4, X18 · `qa/contracts/core-invariants.md` C1, C2, C7

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (X4 on the last-screen path, X18 surfaces unchanged), 3/3 invariants hold (C1, C2, C7)
FAILURES (if any):
- none against this unit
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at463-bound-on-last-screen-names-itself-2026-09-17-checker/report.json
ISSUES-WRITTEN: AT-480 (medium, pre-existing, not a failure of this unit); AT-463 open -> fixed
EXPLANATION: visit_node now splits the per-node cap (still just breaks) from a crawl bound (records rt.stop_reason, then breaks), and _bfs keeps it over "frontier empty", so a bound firing on the last queued screen ends STOPPED_BOUND with the bound named. Every row's falsifying edit went red in a scratch copy on the assertion the check is named for, and a live UI crawl with max_actions=2 on a one-screen fixture showed stopped_bound/max_actions on the crawl page, crawls table and report.xlsx while an in-bounds control crawl still read COMPLETED. The disclosed login-wall override does breach X4's literal wording when both apply; it predates this unit and is filed as AT-480.
```

## What I re-ran (step 3, bound tree, my own runs)

| # | Command | Result |
|---|---|---|
| 1+2 | `uv run pytest tests/test_explore_bounds_last_node.py tests/test_explore.py tests/test_crawl_coverage.py tests/test_crawl_coverage_bounds.py tests/test_explore_blocked.py tests/test_explore_login_wall.py tests/test_crawl_status_surfaces.py -p no:cacheprovider -o addopts= -q` | `69 passed, 1 warning` (matches the manifest) |
| 3 | `uv run ruff check src tests scripts` | `All checks passed!` |
| 4 | `uv run autotester doctor` | `doctor: clean` |
| 5 | full suite | not re-run (per dispatch); the maker's recorded run is `1412 passed, 2 skipped, 32 xfailed` |

Diff read: `git diff -- src/autotester/stages/explore_node.py` is a single hunk at `visit_node` (lines 226-231). `tests/test_explore_bounds_last_node.py` is new and untracked. No schema, UI or explore.py change.

## Capability coverage (step 4b), in a throwaway copy

Copy: `git archive HEAD | tar -x` into `scratchpad/checker-at463`. Then, as a separate command, `projects/erp`, `projects/pathlynks` and `projects/vidysea-erp` were removed (only `projects/regression-demo` stayed). I copied in the 2 unit files and ran `uv sync`. The imported module was `...scratchpad\checker-at463\src\autotester\stages\explore_node.py`. The named test was green first: `4 passed`. Harness `_falsify.py` asserts each anchor matches exactly once and the file changed, and it restores the file afterwards (`restored: 4 passed`).

| Row | Edit | Before (copy) | After | Assertion that fired |
|---|---|---|---|---|
| max_actions named | delete `rt.stop_reason = reached` | 4 passed | 2 failed | `test_max_actions_...`: `assert 'frontier empty' == 'max_actions'` (line 41) |
| wall_clock_s named | same edit | 4 passed | (same run) | `test_wall_clock_...`: `assert 'frontier empty' == 'wall_clock_s'` (line 55) |
| guard can say COMPLETED | `if reached:` -> `if True:` | 4 passed | 4 failed | `test_a_last_screen_..._still_completed`: `assert 0 == 3` (line 65, the actions assertion the manifest predicted) |
| per-node cap is not a crawl bound | cap branch sets `rt.stop_reason = "per_node_action_cap"` | 4 passed | 1 failed | `test_the_per_node_cap_...`: `assert 'per_node_action_cap' == 'frontier empty'` (line 76) |

Trap hunt. The bound tests assert `stop_reason` and `status`, not an end state the bug also produces: the pre-fix code gives `frontier empty`/COMPLETED, and they go red on it. The wall-clock test uses an injected clock, not live time.

## Mode D (own browser, Playwright MCP)

- Fixture: a checker-built synthetic one-screen page (3 buttons that do not navigate, no links), served by `http.server` on 127.0.0.1:8791. UI: uvicorn from the copy on 127.0.0.1:8792, `AUTOTESTER_ROOT` set to a scratch root. Project `boundlast` and its CRAWL approval were seeded via ProjectStore.
- Bound run: I filled the crawls-page form (max_actions=2) and clicked **Explore now**. Crawl page: `STOPPED_BOUND · stopped: MAX_ACTIONS`, STATUS `stopped_bound`, STOPPED BECAUSE `max_actions`, left queued 0, no "completed" anywhere. Crawls table: `STOPPED_BOUND` with `badge-blocked` and `max_actions`. report.xlsx Summary: Status `stopped_bound`, Stopped because `max_actions`.
- Control run (max_actions=10): `COMPLETED · stopped: FRONTIER EMPTY`, 3 actions, `badge-pass`.
- Console errors: 0 on every AutoTester page. Each crawl also filed one product CONSOLE issue for the fixture's own missing favicon (a 404 from http.server), which is a fixture artefact.
- Not driven through the UI: wall_clock_s firing mid-node, because the timing cannot be pinned through the form. It is covered by the injected-clock test, which was reproduced above.
- Both servers were stopped (pids 40536 and 39268), leaving 0 listeners on 8791/8792.

## The disclosed limit: a login wall replaces stop_reason after a bound fired

I reproduced it in the copy with my own probe. The page was [textbox, form-submit, textbox, self-link]:
- max_actions=1 gave `stopped_bound 'max_actions'`.
- max_actions=2 gave `login_wall`, actions=2, and stop_reason = the wall sentence, with no bound named.
- max_actions=5 gave `login_wall`, actions=3.

**Do X4/X18 require otherwise? Yes, as written.** X4 says "the one that fired is named in `Crawl.stop_reason`", and X18(b) says the status names "the wall in `stop_reason`". Neither yields to the other, and both can hold at once. At N=2 the wall sentence also says "no link led anywhere else", but the bound left the link untried, so the advice ("declare a login case") may be the wrong remedy. The status is still non-success and coverage still counts the bound hole (AT-471), so there is no false success. **Filed as AT-480, severity medium.** It is pre-existing since AT-458 and honestly disclosed, so it does not fail this unit, whose scope is the last-screen bound path.

## Question, not a finding

The bound check runs before every *element*, not before every *candidate*. With max_actions=3, a 3-button screen plus a trailing policy-denied control ("Delete account") ends `stopped_bound 'max_actions'`, while max_actions=4 ends `completed` with the same 3 actions (probe in the copy). The trailing control really was never evaluated, so naming the bound is defensible and errs toward non-success. I note it for the maker, not as a defect.
