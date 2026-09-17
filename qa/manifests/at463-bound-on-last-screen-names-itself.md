# Manifest — at463-bound-on-last-screen-names-itself

**Unit:** AT-463: a crawl bound that fires mid-screen on the last queued screen names itself instead of reading "frontier empty" / COMPLETED
**Contract:** `qa/contracts/explore.md` **X4** ("the one that fired is named in `Crawl.stop_reason`. Bounds are checked before every node and before every action"); X18 (status surfaces); core-invariants C1, C2, C7
**Goal task:** none. Follow-on to Umesh's 2026-09-16 priority change (an honest post-login map); issue filed by the at458 checker
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-463 (medium)
**Status:** checked-PASS (qa/verdicts/at463-bound-on-last-screen-names-itself.md, cycle 1, commit 8b2b9e4; the checker filed AT-480, the login wall hiding a bound, as pre-existing)

## What changed

| Path | Change |
|---|---|
| `src/autotester/stages/explore_node.py` (`visit_node`, ~line 226) | The per-action check was `if tried >= per_node_action_cap or explore.stop_reason(rt): break`. It is now split. The per-node cap still just breaks, because it ends a screen, not the crawl. A crawl bound now sets `rt.stop_reason = reached` before breaking. `_bfs` already keeps `rt.stop_reason or "frontier empty"`, so the named bound survives when the queue is empty. |
| `tests/test_explore_bounds_last_node.py` (new, 77 lines) | Four tests on a one-screen fake site with three safe, non-navigating buttons, so nothing is ever queued after it. max_actions=2 → `max_actions`/STOPPED_BOUND. wall_clock_s with an injected clock → `wall_clock_s`/STOPPED_BOUND. Control: max_actions=10 → `frontier empty`/COMPLETED. Control: per_node_action_cap=2 → still COMPLETED (the cap is not a crawl bound). |

No schema, UI or explore.py change (explore.py stays at 300 lines). `explore_node.py` is now 249 lines.

## Why

The existing X4 tests crawl the default fake site, where screens are still queued when a bound fires, so the next loop-top check in `_bfs` named the bound. On the last queued screen, `_bfs` exited on an empty queue and wrote "frontier empty". `terminal_status(completed=True)` then returned COMPLETED for a crawl that had run out of actions.

## How to verify

| # | Command | Expected |
|---|---|---|
| 1 | `uv run pytest tests/test_explore_bounds_last_node.py -p no:cacheprovider -o addopts= -q` | 4 passed |
| 2 | `uv run pytest tests/test_explore_bounds_last_node.py tests/test_explore.py tests/test_crawl_coverage.py tests/test_crawl_coverage_bounds.py tests/test_explore_blocked.py tests/test_explore_login_wall.py tests/test_crawl_status_surfaces.py -p no:cacheprovider -o addopts= -q` | 69 passed (maker run) |
| 3 | `uv run ruff check src tests scripts` | All checks passed |
| 4 | `uv run autotester doctor` | doctor: clean |
| 5 | Full suite `uv run pytest -p no:cacheprovider -o addopts= -q -rx` | see "Full suite" below |

**The checker's own probe from the at458 verdict, re-run by the maker.** Script: `scratchpad/at463_probe.py`. It sets up one login-shaped page (textbox, `is_form_submit` button, textbox, a self-link) and runs `crawl_it` with max_actions N:
- N=1 → `stopped_bound 1 'max_actions'` (the issue recorded `completed`, `frontier empty`).
- N=2 → `login_wall` with the wall sentence as stop_reason.
- N=5 → `login_wall`, 3 actions.

## Capability coverage

| Capability | Check | Falsifying edit (single hunk, `src/autotester/stages/explore_node.py`) | Result |
|---|---|---|---|
| max_actions firing on the last screen is named | `test_max_actions_firing_on_the_last_screen_names_itself` | delete the line `rt.stop_reason = reached` | Maker: before the fix was applied, both bound tests failed with `assert 'frontier empty' == 'max_actions'` / `== 'wall_clock_s'`, and both controls passed. That pre-fix code is exactly this edit's behaviour. It was run in the bound tree before the edit, not in an extract. **The checker should reproduce it in a copy.** |
| wall_clock_s firing on the last screen is named | `test_wall_clock_firing_on_the_last_screen_names_itself` | same edit | same |
| the guard can say COMPLETED | `test_a_last_screen_that_finishes_inside_its_bounds_is_still_completed` | replace `if reached:` with `if True:` (always stop) | expected red: actions 0 ≠ 3. Not run by the maker. |
| the per-node cap is not promoted to a crawl bound | `test_the_per_node_cap_is_not_a_crawl_bound` | in the cap branch, add `rt.stop_reason = "per_node_action_cap"` before `break` | expected red: stop_reason ≠ "frontier empty". Not run by the maker. |

## Known limits, disclosed rather than hidden

- **A login wall still replaces stop_reason with its sentence** even when a bound fired (probe N=2). This is by design in `explore_status.terminal_status`: the wall checks come first. The bound that fired still reaches coverage through the counters (AT-471, `crawl_coverage.of_run`). Whether LOGIN_WALL should also name the bound is not claimed by this unit. It is a question for the checker, not a hidden gap.
- `max_screens` mid-node was already named: a newly found screen is queued, so `_bfs`'s loop-top check sees it. No test was added for it.

## Browser

This unit touches the status shown on the crawl page, the crawls table and report.xlsx, through `displayed_status`. So the UI is touched indirectly, and **the checker should run Mode D in its OWN browser**.
- Suggested target: LOCAL fixtures only, `tests/fixtures/login_site` served on 127.0.0.1. No external site (the live-crawl-target gate is open).
- Suggested setup: a synthetic project with bounds that exhaust max_actions on the last reachable screen, and the UI started from an isolated extract.
- **Maker smoke: not run this cycle.** This is stated as a gap, not claimed.

## Full suite

Maker run, exit 0: `1412 passed, 2 skipped, 32 xfailed, 1 warning in 440.45s`. The 32 XFAILs are AT-416/417, as before. The pass count includes tests from other sessions' working-tree files and is not claimed by this unit.

## Commit / push

Commit after PASS with a narrow pathspec. The push stays held: origin/master..HEAD contains another session's unverified commits.
