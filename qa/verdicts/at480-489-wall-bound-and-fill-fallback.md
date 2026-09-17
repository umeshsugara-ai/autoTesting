# Verdict — at480-489-wall-bound-and-fill-fallback

**Cycle checked:** 1
**Date:** 2026-09-17
**Checked by:** /checker (Mode A, fresh context, no builder reasoning)
**Bound to:** `D:\autoTesting\.work\wave-at480-489` (worktree of `D:\autoTesting`, branch
`wave/at480-489-wall-bound-and-fill-fallback`, base `c890899`, build commits `44d2547`, `6d0112c`)
**Contract:** `qa/contracts/explore.md` X4, X18(a)/(b)/(c) · `qa/contracts/core-invariants.md`
C1-C10
**Manifest:** `qa/manifests/at480-489-wall-bound-and-fill-fallback.md`
**Issues claimed:** AT-480, AT-489 (= `ISS-x18a-1`, filed in
`qa/verdicts/x18a-login-both-directions.md`)

## What I re-ran myself

- `uv run pytest tests/test_explore_login_wall.py tests/test_explore_login_spa_live.py
  tests/test_crawl_status_surfaces.py tests/test_explore.py tests/test_explore_bounds_last_node.py
  tests/test_ui_crawl_login.py tests/test_explore_login_wall_bounds.py -p no:cacheprovider
  -o addopts= -q` → **69 passed, 1 warning in 58.06s** (0 failed). Manifest claimed 68 passed; my
  own re-run is +1, the same direction and same magnitude as the full-suite discrepancy below. Not
  chased to a specific test — plausibly an environment-conditional test (e.g. a chromium
  availability check in `test_ui_crawl_login.py`'s live-browser test) resolving differently between
  the maker's run and mine, since chromium is confirmed available here (`playwright.sync_api`
  launched successfully in this check). 0 failed in both runs is the property this line certifies.
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**
- `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py`
  → **1438 passed, 2 skipped, 2 deselected, 32 xfailed, 1 warning in 397.35s** (0 failed). Manifest
  claimed 1437 passed; my own re-run is +1 pass with the same 0-failed, 2-skipped, 32-xfailed
  shape. Not investigated further as a defect: this suite carries a documented flake
  (`core-invariants.md` amendment log, 2026-09-09, AT-196) whose failure direction is a false FAIL
  on a busy machine, never a false PASS/count drift that would hide a real failure, and 0 failed
  both times is the property that matters.
- `git diff c890899...HEAD --stat` and the full diff for `explore_status.py` and
  `tests/test_explore_login_wall.py` — matches the manifest's "What changed" exactly. No file
  outside the manifest's list is touched; no existing function, test, or export is deleted or
  renamed (step 4c clean).

## Capability coverage — reproduced in a throwaway copy (never the bound tree)

`git archive HEAD | tar -x` into a scratch dir, `rm -rf projects/erp projects/pathlynks
projects/vidysea-erp`, `uv sync`, `autotester.__file__` confirmed resolving inside the copy.

All 4 rows reproduced exactly as the manifest claims, each a single-hunk edit to
`src/autotester/stages/explore_status.py` (the only file named), green before, red after with the
exact assertion named, restored byte-identical (diffed, no residual) before the next edit:

1. `bound_suffix = ""` (dropping the conditional) → `test_max_actions_firing_on_a_walled_page_names_the_bound`
   goes red on `assert 'max_actions' in ...` — reproduced verbatim.
2. `wall_reason = LOGIN_WALL_REASON` (dropping the ternary) → same test reddens on
   `assert 'no link led anywhere else' not in ...` — reproduced verbatim.
3. Dropping the `submit_selector is not None and submit_selector in selectors` clause (restoring
   the pre-AT-489 body) → `test_a_dashboard_with_a_matching_field_but_no_sign_in_button_is_not_login_failed`
   reddens on `assert <LOGIN_FAILED> is <COMPLETED>` — reproduced verbatim; the AT-467 control
   (`test_a_sticky_wrong_password_banner_is_still_login_failed`) stays green under the same edit,
   confirming it does not ride this row's failure (matches manifest row 4's claim).

**CAPABILITY-COVERAGE: 4/4 reproduced.**

## Hunt 1 — does `_root_login_case()`'s new CLICK step make any pre-existing test vacuous?

Reproduced live, not merely reasoned: in the same throwaway copy, reverted ONLY the test-helper
edit (`_root_login_case()` back to no CLICK step, `tests/test_explore_login_wall.py` alone) and
ran the whole file. Result: **1 failed, 15 passed** — the single failure is
`test_a_sticky_wrong_password_banner_is_still_login_failed` (the AT-467 control), every other test
using the helper (both AT-462 SPA controls, the observed-failure test, the partial-fill control,
the placeholder-URL test) is unaffected, because none of them reach the `submit_selector` branch
of `_still_login` — they resolve on the signature check or the `fill_targets` check first. This
confirms the CLICK step was a **necessary tightening** (the sticky-banner fixture already carried
`#go`; the case needed to declare it via a CLICK step so `login_submit_selector` can name it), not
a workaround that switches a check off, and the AT-467 control still correctly discriminates its
own defect (reverting the whole fallback mechanism, not merely this fixture, is what the earlier
`x18a-login-both-directions` checker already proved reddens it — unchanged by this unit). **No
FAIL.**

## Hunt 2 — spurious bound suffix on a naturally-completed wall?

Traced (not merely read) `terminal_status`'s only production caller,
`src/autotester/stages/explore.py:298-300`: `completed = rt.stop_reason == "frontier empty"` and
that exact string is passed through as `current_stop_reason`. `rt.stop_reason` at that point is
set only by `_bfs`/`stop_reason(rt)` to one of `"frontier empty"`, `"max_screens"`,
`"max_actions"`, or `"wall_clock_s"` — never an unrelated value — because the two OTHER paths that
set `rt.stop_reason` to something else (`_login_failed_reason`, the seed-error string) both
`return _finish(...)` directly and never call `_terminal_status` at all. So "frontier emptied
naturally but carries an unrelated stop_reason" is not reachable through the shipped call path;
`bound_suffix` can only fire when `current_stop_reason` genuinely names a fired bound. Confirmed
live in Mode D below (a genuinely bound-cut wall reads the suffix; the existing
`test_a_completed_walled_crawl_keeps_todays_sentence_unchanged` control, re-run in step 3 above,
pins the naturally-emptied case keeps the byte-identical old sentence). Also traced: the AT-474
not-judged qualifier and the bound suffix cannot combine, because the `LOGIN_FAILED`/`LOGIN_WALL`
branches both `return` before the qualifier's own `if` is reached — matching the manifest's "Known
limits" disclosure exactly. **No FAIL.**

## Hunt 3 — the disclosed `max_screens`/`LOGIN_WALL` non-co-occurrence claim

Traced `_enqueue` (`stages/explore_node.py:104-115`) and `stop_reason`/`_bfs`
(`stages/explore.py:88-97,175-187`): `_enqueue` only declines a new node once `screens_found` has
**already** reached `max_screens` from an earlier enqueue in the same step, so the node whose own
discovery just pushed the count to the cap (and any node still queued behind it) is added to
`rt.nodes` but left in the queue; the very next `_bfs` iteration's `stop_reason(rt)` check fires
`"max_screens"` before that node is ever popped and visited, so it never earns a `DENIED_POLICY`
edge of its own. `is_login_wall` requires every node in its `nodes` argument to be in the `walled`
set (built only from nodes with their own `DENIED_POLICY` edge), so it returns `False` the instant
`max_screens` is the firing bound — confirmed by the manifest's own pinning test
`test_max_screens_on_a_would_be_wall_correctly_stays_a_plain_bound`, re-run in step 3 above. The
claim is accurate, and structurally slightly *stronger* than stated (every still-queued node
behind the cap, not only the cap-reaching one, is affected the same way) — this does not weaken
the claim, it only broadens the mechanism that makes it true. **Claim CONFIRMED, not refuted.**

## Live browser (Mode D) — driven by the checker's own script, not the maker's

Playwright MCP was unavailable; used a Python `sync_playwright` script (`uv run python`) from the
isolated throwaway copy. `tests/fixtures/login_site/login.html` has no extra clickable elements
and structurally **cannot** exercise a bound firing mid-wall (a bound tight enough to fire before
the one page is visited loses that page's own `DENIED_POLICY` edge and produces `STOPPED_BOUND`,
not `LOGIN_WALL` — see Hunt 3), so I authored a small local-only fixture (never touching the bound
tree): one denied form submit (`#go`) plus 3 same-page self-links, served on `127.0.0.1:58211` via
`python -m http.server` (stdout/stderr to log files, no PIPE). The real UI app
(`uv run uvicorn autotester.ui.app:app`, isolated copy, `AUTOTESTER_ROOT` pinned to a scratch
root) ran on `127.0.0.1:59704`, logs to file. Drove the Crawls page with headless Chromium: filled
the bounds form (`max_actions=2`), submitted, and read the resulting crawl page and crawls table.

**Result:** `login_wall` status, `badge-blocked` (warning/non-success) tone on BOTH the
crawl-status pill and the stop-reason pill (confirmed from each element's own `outerHTML`, not a
page-wide substring match — one `badge-pass` span present elsewhere on the page is the visited
node's own unrelated "explored" per-node marker), `stop_reason` names `max_actions` and does
**not** contain "no link led anywhere else", same on the crawls table row. Zero console errors.
Also exported the same crawl's `report.xlsx` (`export_crawl_excel`) and read its Summary sheet
directly with `openpyxl`: the "Stopped because" cell is byte-identical to the crawl page's
`stop_reason` — X16 workbook parity holds for the new bound-suffixed sentence. Servers verified
started (own log files show only my own requests) and verified stopped afterward (`curl` to both
ports fails after `TaskStop`; nothing else running on those ports was touched).

Evidence: `qa/evidence/browser-at480-489-wall-bound-and-fill-fallback-2026-09-17-checker/report.json`

## Contract maintenance

Adopted the manifest's proposed X18(a) wording with one addition, in `qa/contracts/explore.md`
(amendment log entry dated 2026-09-17, routine — tightens only, softens nothing):

- **ISS-x18a-1 closed "as filed"**, not closed outright: the originally-filed defect (a node
  reusing every FILL-target selector alone misclassified `LOGIN_FAILED`) is genuinely fixed and
  independently re-verified (capability row 3 above). A narrower residual survives by design (a
  node coincidentally matching every FILL target **and** the submit control is still classified
  `LOGIN_FAILED`) — the manifest's own new control test pins this as intentional, so the
  amendment states it explicitly rather than letting "CLOSED" imply no residual at all, consistent
  with how every earlier closure in this contract's log states its own residual.
- New X18 point **(e)** documents the bound-suffix mechanism (AT-480), the invariant that makes a
  "spurious suffix on a natural completion" structurally unreachable (Hunt 2), and the disclosed
  `max_screens` structural gap (Hunt 3), now stated with the broader/stronger mechanism the
  tracing found.
- No criterion is removed or weakened; X1-X17 and the untouched parts of X18 are byte-unchanged.

## Issues (ledger, not edited in this worktree per dispatch)

`qa/issues.jsonl` was not read or edited here. Both claimed issues are genuinely closed by this
unit's evidence and should move `open → fixed` at the next ledger-writing pass:
- **AT-480** (`qa/issues.jsonl:477`, currently `open`) — closed by capability rows 1/2 and the
  Mode D live-browser reproduction above.
- **ISS-x18a-1 / AT-489** (`qa/issues.jsonl:160`, currently `open`) — closed **as filed** by
  capability row 3, with the narrower residual now recorded in the contract rather than reopened
  as a new issue.

## New issues

None at >80% confidence.

```
VERDICT: PASS
SCOREBOARD: 8/8 criteria met (X4, X18(a), X18(b), X18(c), C1, C2, C3, C7), 0/0 invariants violated
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 4/4 reproduced
LIVE-BROWSER: qa/evidence/browser-at480-489-wall-bound-and-fill-fallback-2026-09-17-checker/report.json
ISSUES-WRITTEN: none
EXPLANATION: Every manifest verify command re-ran green (0 failed on the full suite, +1 pass count
vs the manifest attributable to the repo's own documented flake, never a false pass); all 4
capability-coverage rows reproduced with correct isolation; diff scope clean (no unclaimed
deletions/touches); all three checker hunts (vacuous test-helper edit, spurious bound suffix,
max_screens/login_wall non-co-occurrence) were independently traced and/or empirically reverted
and none found a defect — the unit's own disclosures held up under adversarial re-derivation. A
real Playwright script against the checker's own local-only fixture (the shipped fixture cannot
reach this state) confirmed live: login_wall status, non-success tone on both pills, the bound
named without the untried-links claim, and workbook parity. Contract amended to close ISS-x18a-1
"as filed" with its narrower residual now stated, plus a new X18(e) for the bound-suffix mechanism.
```
