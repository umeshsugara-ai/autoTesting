# Manifest — at480-489-wall-bound-and-fill-fallback
**Contract:** qa/contracts/explore.md X4, X18(a)/(b) · qa/contracts/core-invariants.md C1/C2/C7
**Goal task:** none
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-480, AT-489

## What changed
- `src/autotester/stages/explore_status.py:32-39` — added `LOGIN_WALL_REASON_BOUND`, the
  bound-honest variant that drops "no link led anywhere else".
- `src/autotester/stages/explore_status.py:75-82` — new `login_submit_selector(case)`: the
  selector of the login case's last CLICK step, or `None` if it has none (AT-489).
- `src/autotester/stages/explore_status.py:95-118` — `never_left_login`'s `_still_login`
  fallback now additionally requires `login_submit_selector(case)` to be present on the node's
  elements, alongside every FILL target; a case with no CLICK step never fires the fallback.
  Docstring updated to state the narrower, true claim.
- `src/autotester/stages/explore_status.py:144-179` — `terminal_status` now computes a
  `bound_suffix` (`" -- the <bound> bound fired before every control was tried"`) whenever
  `completed` is False and a bound is named, and appends it to BOTH the `LOGIN_FAILED` reason
  and the `LOGIN_WALL` reason; the wall reason swaps to `LOGIN_WALL_REASON_BOUND` (no "no link
  led anywhere else" claim) when a bound fired. Completed-crawl sentences are byte-unchanged
  (no `bound_suffix`, `LOGIN_WALL_REASON` unchanged). The AT-474 not-judged qualifier still
  appends after the status/reason are otherwise decided (untouched code path).
- `tests/test_explore_login_wall.py:166-170` — `_root_login_case()` gained a `CLICK` step
  (`#go`) so the AT-489 submit-control requirement has something to match; reformatted onto one
  fewer line to hold the file at its 300-line cap. No test in this file was deleted, renamed, or
  had its assertions weakened — `test_a_sticky_wrong_password_banner_is_still_login_failed`
  (the AT-467 control this issue's dispatch names) stays green unmodified.
- `tests/test_explore_login_wall_bounds.py` (new, 219 lines) — 8 new tests: `max_actions` and
  `wall_clock_s` firing on a walled page (AT-480b), a control pinning today's completed-wall
  sentence unchanged, a `max_screens` control (see "Known limits"), a `LOGIN_FAILED` case where
  a bound fires before the frontier naturally empties (AT-480a), and three AT-489 tests (a
  coincidental-field-only dashboard stays `COMPLETED`, a case with no CLICK step never fires the
  fallback, and the closed-gap control: submit control + every FILL target together still reads
  `LOGIN_FAILED`).

## How to verify (commands + expected)
- `uv run pytest tests/test_explore_login_wall.py tests/test_explore_login_spa_live.py tests/test_crawl_status_surfaces.py tests/test_explore.py tests/test_explore_bounds_last_node.py tests/test_ui_crawl_login.py tests/test_explore_login_wall_bounds.py -p no:cacheprovider -o addopts= -q` → expected: all pass, 0 failures.
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py` (background) → expected: ~1421 passed + 8 new = ~1429, 32 xfailed, 0 failures.

## Actual outputs (from maker's own run)
```
$ uv run pytest tests/test_explore_login_wall.py tests/test_explore_login_spa_live.py tests/test_crawl_status_surfaces.py tests/test_explore.py tests/test_explore_bounds_last_node.py tests/test_ui_crawl_login.py tests/test_explore_login_wall_bounds.py -p no:cacheprovider -o addopts= -q
68 passed, 1 warning in 72.18s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py
(see report below — run in background, appended once complete)
```

### RED before the fix, GREEN after (real re-run, not described)
Reverted `explore_status.py` to `HEAD` (`git show HEAD:... > explore_status.py`), ran the new
file plus the old one:
```
5 failed, 18 passed in 1.84s
FAILED tests/test_explore_login_wall_bounds.py::test_max_actions_firing_on_a_walled_page_names_the_bound
FAILED tests/test_explore_login_wall_bounds.py::test_wall_clock_firing_on_a_walled_page_names_the_bound
FAILED tests/test_explore_login_wall_bounds.py::test_login_failed_bound_names_the_bound
FAILED tests/test_explore_login_wall_bounds.py::test_a_dashboard_with_a_matching_field_but_no_sign_in_button_is_not_login_failed
FAILED tests/test_explore_login_wall_bounds.py::test_a_login_case_with_no_click_step_never_fires_the_fallback
```
Restored the fixed file, same command:
```
23 passed in 1.79s
```
(The `max_screens` and completed-wall control tests were written after this RED/GREEN pass and
independently verified green against the fixed code — see "Capability coverage" row 2 for the
`max_actions` row's own two-line evidence, reproduced separately in an isolated copy.)

## Capability coverage (each new claim -> its isolating falsification)

Reproduced in a throwaway copy — see the shell transcript below this table for the exact
commands and pasted output (anchor counts, before/after lines).

| capability (one line) | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| (1) bound named on a walled crawl (AT-480b) | `test_max_actions_firing_on_a_walled_page_names_the_bound` | revert `bound_suffix` to `""` unconditionally | see below, row 1 |
| (2) bound-honest wall sentence (no "no link led anywhere else" when a bound fired) | same test's last assertion | revert `wall_reason` to always `LOGIN_WALL_REASON` | see below, row 2 |
| (3) submit-control requirement in the fallback (AT-489) | `test_a_dashboard_with_a_matching_field_but_no_sign_in_button_is_not_login_failed` | drop the `submit_selector is not None and submit_selector in selectors` clause from `_still_login`'s `return` | see below, row 3 |
| (4) sticky-banner LOGIN_FAILED still caught (control) | `test_a_sticky_wrong_password_banner_is_still_login_failed` (existing file) | same edit as row 3 (the one clause both rows share) | see below, row 4 |

### Reproduced in an isolated copy (never the bound tree)
```
$ cd <scratchpad>/cov && git -C <worktree> archive HEAD | tar -x -C .
$ rm -rf projects/erp projects/pathlynks projects/vidysea-erp
$ uv sync   (in the copy)
$ python -c "import autotester; print(autotester.__file__)"   -> resolves inside the copy
```

Row 1 — anchor `if not completed and current_stop_reason else ""` occurs once in
`explore_status.py`; before:
```
tests/test_explore_login_wall_bounds.py::test_max_actions_firing_on_a_walled_page_names_the_bound PASSED
```
Edit: `bound_suffix = ""` (single-hunk, single line). After:
```
FAILED ...test_max_actions_firing_on_a_walled_page_names_the_bound - assert 'max_actions' in
'stopped at a login wall: every screen reached only offers a form submit denied by read_only,
and no link led anywhere else -- declare a login case to crawl past it'
```
Restored byte-identical (diffed against the pre-edit copy: no diff) before the next edit.

Row 2 — anchor `wall_reason = LOGIN_WALL_REASON if completed else LOGIN_WALL_REASON_BOUND`
occurs once; before: same PASSED line as row 1. Edit: `wall_reason = LOGIN_WALL_REASON`
(drops the ternary). After:
```
FAILED ...test_max_actions_firing_on_a_walled_page_names_the_bound - assert 'no link led
anywhere else' not in "stopped at a login wall: ... and no link led anywhere else -- ..."
```
Restored byte-identical.

Row 3/4 — anchor `return (submit_selector is not None and submit_selector in selectors` occurs
once. Before:
```
tests/test_explore_login_wall_bounds.py::test_a_dashboard_with_a_matching_field_but_no_sign_in_button_is_not_login_failed PASSED
tests/test_explore_login_wall.py::test_a_sticky_wrong_password_banner_is_still_login_failed PASSED
```
Edit: drop the submit-selector clause, i.e.
`return bool(fill_targets) and fill_targets <= selectors` (the pre-AT-489 body, single-hunk).
After:
```
FAILED ...test_a_dashboard_with_a_matching_field_but_no_sign_in_button_is_not_login_failed -
assert <CrawlStatus.LOGIN_FAILED> is <CrawlStatus.COMPLETED>
```
Row 4's own test (`test_a_sticky_wrong_password_banner_is_still_login_failed`) is unaffected by
this specific edit (it already carries the submit control, so removing the *requirement* does
not change its outcome) — it is listed as the control that the row-3 tightening did not regress
it, re-run PASSED both before and after row 3's edit. Restored byte-identical (diffed against
the pre-edit copy: no diff) after both edits.

**CAPABILITY-COVERAGE: 4/4 reproduced**, each edit a single-hunk change to
`explore_status.py`, named in "What changed", restored to the pre-edit copy byte-for-byte
(diffed) before the next.

## Live browser evidence
**Maker smoke: not run.** This unit changes `Crawl.stop_reason` text only — no new UI surface,
no new status value, no new badge tone (`_STOP_TONE` untouched). The existing `login_wall` and
`login_failed` badges (verified live by the checker in `x18a-login-both-directions`,
`qa/evidence/browser-x18a-login-both-directions-2026-09-17-checker/report.json`) render the same
way; only the `stop_reason` string they display gained a suffix in the bound-fired case, which
is not independently render-tested by a badge-tone check. Not UI-touching under the qa/loop
narrower definition (no `.tsx/.html/.css`, no `routes/`/`pages/`/`components/` path changed) —
changed paths: `src/autotester/stages/explore_status.py`,
`tests/test_explore_login_wall.py`, `tests/test_explore_login_wall_bounds.py`.
Suggested checker Mode D: serve `tests/fixtures/login_site/login.html` as a synthetic project's
`base_url` with no login case declared and a tiny `CrawlBounds(max_actions=1)` (via the UI
Explore form's advanced bounds, if exposed, or a project-level default) so the crawl page shows
`login_wall` with `max_actions` named in the stop-reason text. Local fixtures only.

## Known limits (disclosed, not blocking)
- **`max_screens` cannot fire while X18(b) reads `LOGIN_WALL`** — structural, not a gap this
  unit could close: `_enqueue` only declines a new node once `screens_found` has ALREADY
  reached the cap from an earlier successful enqueue in the SAME crawl step, so the node whose
  own discovery pushed the count to the cap is always left `queued`, never visited, and
  therefore never carries its own `DENIED_POLICY` edge — `is_login_wall` requires every
  discovered node to be walled, so it always returns `False` the instant `max_screens` is the
  bound that fires. Verified live (`test_max_screens_on_a_would_be_wall_correctly_stays_a_plain_bound`):
  a two-branch walled site with `max_screens=2` reads `stopped_bound`/`max_actions`... `max_screens`,
  never `login_wall` — today, unchanged by this fix, and correctly so (there is no false claim to
  fix here; `STOPPED_BOUND` with `stop_reason="max_screens"` is already X4-honest on its own).
  Not filed as a new issue: this is the *bound-wall combination this fix could not have covered
  even in principle*, not a regression or an uncovered claim of this unit's own capability rows.
- The AT-474 not-judged qualifier's interaction with a bound-suffixed `LOGIN_FAILED`/`LOGIN_WALL`
  reason was not separately tested — `login_observe_error` is only read in the branch AFTER the
  early `never_left_login`/`is_login_wall` returns, so the qualifier cannot currently combine
  with the bound suffix in the same string (they are mutually exclusive branches, unchanged by
  this fix). `test_a_login_page_that_cannot_be_observed_is_not_an_unqualified_success` (existing,
  unmodified) still passes, confirming the qualifier path itself is untouched.

## Proposed X18(a) wording (for the checker to adopt, tighten, or reject)
Append to X18(a)'s existing text: *"When a crawl bound (`max_screens`/`max_actions`/
`wall_clock_s`) fires before the frontier empties, a `LOGIN_FAILED` or `LOGIN_WALL` status keeps
naming the bound in `stop_reason` (X4) via an appended clause `-- the <bound> bound fired before
every control was tried`, and the wall sentence's "no link led anywhere else" claim is dropped in
that case (a bound can leave controls genuinely untried). A completed crawl's sentences are
unchanged. Known structural gap: `max_screens` cannot itself be the bound named on a `LOGIN_WALL`
crawl, because the node whose discovery trips the cap is always left unvisited and therefore
never walled -- such a crawl correctly reads `STOPPED_BOUND`/`max_screens` instead, which is
already X4-honest without X18(b) needing to apply."* Also append to the fill-target fallback
clause: *"AND the login case's own submit control (the selector of its last CLICK step) is also
present as an element `selector` on the node; a login case with no CLICK step never fires this
fallback (signature rule only)."* This closes ISS-x18a-1 as filed (the coincidental-field-only
case) while keeping the AT-467 sticky-banner catch intact (its node also carries the submit
control).

## Status: ready-for-check
