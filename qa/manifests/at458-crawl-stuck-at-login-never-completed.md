# Manifest — at458-crawl-stuck-at-login-never-completed

**Unit:** AT-458 / X18 — a crawl that never gets past the login wall never reads as COMPLETED, on any surface
**Contract:** `qa/contracts/explore.md` **X18** (a)(b)(c)(d) + Verify; X16 (surfaces), X4/AT-242 unchanged in intent; core-invariants C1, C2, C3, C7
**Goal task:** none — Umesh's 2026-09-16 priority change; `qa/QUEUE.md` TOP-2
**Date:** 2026-09-17
**Fix cycle:** 3 of max 3 (last)
**Dual check:** no
**Issues addressed:** AT-458 (high); AT-462 (cycle-1 and cycle-2 checker finding)
**Status:** checked-PASS (qa/verdicts/at458-crawl-stuck-at-login-never-completed.md, cycle 3, commit 8e2c216; cycles 1-2 FAIL on AT-462, fixed in cycle 3)

## Cycle 3 — the fix for `qa/verdicts/at458-…md` "## Cycle 2" (FAIL)

**Quoted:** *"[X18(a)] sev: medium · AT-462 only half fixed. The new guard `len({n.signature for n in
reached}) != 1` counts signatures instead of comparing against the login screen. A working login on a
single-page app whose post-login dashboard is ONE structural state … still ends LOGIN_FAILED … Reproduced
LIVE … · record the login screen's own signature at bootstrap (after the case's NAVIGATE, before FILL) and
fire (a) only when every node matches both the login template and that signature; add a test with ONE
post-login node at the login template that must stay COMPLETED"*

The checker was right. Counting signatures was a proxy for "is this the login screen", and it breaks
on exactly the single-state dashboard it reproduced. I adopted its fix direction.

**What changed in cycle 3:**
- **`stages/explore.py::_already_past_login`**, where the X10 login bootstrap already navigates to the
  case's login URL and settles before any FILL:
  - redirected away → `True` (AT-226, unchanged);
  - otherwise it records `rt.login_signature = explore_status.observed_signature(rt.session)` and
    returns `False`. That is the login screen's structure, **observed before the case types anything**.
  - New `ExploreRuntime.login_signature` field. `_terminal_status` passes it on.
  - I shortened two docstrings without dropping any fact they carried, so the file is 299 lines,
    under the cap.
- **`stages/explore_status.py`:**
  - `observed_signature(session)` returns `structural_signature(observe(session).elements)`, computed
    exactly as a crawled node's signature is, or `None` if observation raises. It never crashes a crawl.
  - `never_left_login(nodes, case, login_signature)` returns LOGIN_FAILED **only when every reached
    node has the login template and that observed signature**. The signature-count guard is removed.
    An unobserved login (`None`) never equals a node's signature, so it is never judged.
  - `terminal_status(..., login_signature=None)` is the new keyword. The file is 129 lines.
- **`tests/test_explore_login_wall.py`**: the two cycle-2 unit tests are replaced by five, driven by
  the observed signature.
  - **`test_a_single_page_app_whose_one_dashboard_state_shares_the_login_url_is_not_login_failed`**
    is the checker's exact case: ONE node at the login template, a different signature, COMPLETED.
  - Two post-login states → COMPLETED.
  - Every node **is** the observed login screen → LOGIN_FAILED. This is the positive case.
  - Unobserved login signature → COMPLETED, never judged.
  - Placeholder login URL → COMPLETED.
  - The file now has **12** tests.
- **`tests/fixtures/spa_login_site/index.html`** (new) is a real single-page app. Signed out, one URL
  renders a login form. A correct login swaps in a dashboard with exactly **one** structural state
  (a "Refresh numbers" button) at the **same URL**, like the checker's own fixture.
- **`tests/test_explore_login_spa_live.py`** (new, 2 tests) runs a **real headless Chromium** crawl
  with the login case:
  - correct password → **not LOGIN_FAILED, COMPLETED**;
  - wrong password → **LOGIN_FAILED** with "login page" in the reason.
  - Chromium is probed before the crawl, so a real failure can never read as a skip.
- **Removed as vacuous, found by sabotage (N5 below):** a `login_signature is None` early return. It
  was redundant, because a `None` signature never equals a node's. Deleting it changed nothing, so
  it was a guard that could never fail on its own (AT-218). The comparison carries that behaviour,
  and `test_an_unobserved_login_screen_is_never_judged_failed` pins it.

**Cycle-3 sabotage.** Run in the same extract (`scratchpad/x18x`) with every cycle-3 file synced in
and confirmed identical with `cmp`. The named set was `test_explore_login_wall.py`,
`test_crawl_status_surfaces.py`, `test_explore_blocked.py` and `test_explore_login_spa_live.py`,
with a baseline of **`26 passed`**. It was green after every restore, and still `26 passed` after
the N5 cleanup.

| Row | Falsifying edit (single hunk) | Observed |
|---|---|---|
| **N3 — the cycle-2 logic itself** | `explore_status.py`: the `any(n.url_template != template or n.signature != login_signature …)` line → `{n.url_template …} != {template} or len({n.signature …}) != 1` | **2 failed** — the single-state unit test (`LOGIN_FAILED is COMPLETED`) **and the live SPA test**: `the login case ran, but every screen reached was still the login page (/index.html) … assert LOGIN_FAILED is not LOGIN_FAILED` |
| **N4 — the login signature is never recorded** | `explore.py`: delete the `rt.login_signature = explore_status.observed_signature(rt.session)` line | **2 failed** — the fake-crawl `…never_leaves_the_login_page_is_login_failed` and the **live wrong-password SPA test** (`COMPLETED is LOGIN_FAILED`) |
| M1 — X18 Verify: pre-X18 body | `explore_status.py`: delete the (a)+(b) checks | **5 failed** — both walls, both (a) failures including the live wrong-password test, and the login-gate test |
| M2 — (a) never fires | `explore_status.py`: the comparison line → `if True:` | **3 failed** — the fake and unit LOGIN_FAILED tests and the live wrong-password test |
| N2 — placeholder templated raw | `explore_status.py`: `if step is None or PLACEHOLDER_RE.search(step.target):` → `if step is None:` | **1 failed** — the placeholder test |
| M3 / M4 / M9 | as in cycle 1 | **1 / 5 / 1 failed**, the same assertions |
| N5 — the `login_signature is None` early return | delete it | **26 passed. SURVIVED**, so the guard was removed as vacuous (see above) |

Rows M5–M8 are in the surface files, which cycle 3 did not change. The cycle-1 and cycle-2 checkers
both reproduced them.

**Probes the cycle-2 checker named but did not charge, with the result after cycle 3:**
- (1) A failed login whose page gains a new **control**, such as a dismissable error banner: the
  observed pre-typing signature has no banner, so this now reads as *not* the login screen →
  COMPLETED. It is still an under-fire. The checker said the signature-at-bootstrap fix would close
  it, but it does not, because the banner changes the signature after typing. **I do not claim to
  have fixed (1)** and name it for cycle-3 judgement.
- (2) A login case with no NAVIGATE step skips (a), as before.
- (3) `https://host/{{SECRET:PATH}}` skips (a), as before.

## Cycle 2 — fixes for `qa/verdicts/at458-crawl-stuck-at-login-never-completed.md` (cycle 1 FAIL)

Each failure from the verdict is quoted below, followed by what I changed.

1. **"[X18(a)] sev: medium · `never_left_login` … compares only the URL template. A login that works
   can still end LOGIN_FAILED ("still the login page") when the screens after login share the login
   page's template. That happens on hash-routed apps (/#/login then /#/dashboard), on single-page apps
   that stay at the same URL, and when the login case's first NAVIGATE is a {{SECRET:KEY}} placeholder,
   which templates to "/" … issue: AT-462"**
   - `explore_status.never_left_login` now needs every reached node to be **one screen** in X3's
     sense before it returns LOGIN_FAILED: all nodes share the login template, **and** there is
     exactly one structural signature (`len({n.signature for n in reached}) == 1`). Two signatures at
     the login template are two screens, so the login worked.
   - `explore_status.login_template` returns `None` when the first NAVIGATE target contains a
     `{{SECRET:KEY}}` placeholder (`core.redact.PLACEHOLDER_RE`, the same regex `browser.secrets`
     uses). That target resolves only at fill time. A `None` template means (a) is not applied, so
     the crawl falls through to the other checks and can never be misjudged against "/".
   - New tests in `tests/test_explore_login_wall.py`:
     - `test_a_single_page_app_that_logged_in_on_the_same_url_is_not_login_failed`: two "/" nodes
       with different signatures and a login case navigating to "/" must stay COMPLETED. This is the
       checker's own reproduction.
     - `test_a_placeholder_login_url_is_never_compared_as_the_root_page`: a `{{SECRET:…}}` login URL
       with one "/" node must stay COMPLETED.
   - `explore_status.py` is now 112 lines.
2. **"[manifest] sev: low · The pasted counts do not reproduce. The manifest expects "20 passed" and
   says test_explore_login_wall.py has 8 tests; I got 19 passed, and collection shows 7 + 9 + 3"**
   - The checker was right. `test_explore_login_wall.py` had **7** tests in cycle 1. My "8" and "20"
     were wrong: I counted the added M3 gap test twice. With the 2 AT-462 tests it now has **9**.
     The three files collect **9 + 9 + 3 = 21**. I read `21 passed` from the cycle-2 sabotage
     baseline, not from arithmetic.
   - The corrected table rows are in "How to verify" and "Capability coverage" below.

**Not changed in cycle 2, answered by the checker and not charged:**
- The public search-form-only page gets `login_wall`. The checker judged this matches X18(b) as
  written and put the label question to the contract owner.
- AT-463 was pre-existing and is not charged to this unit.

## What was wrong

`_terminal_status` returned COMPLETED whenever the frontier emptied and at least one action ran.
AT-242's BLOCKED_NO_ACTIONS covered only `actions_used == 0`, so a crawl stuck on a login page
still came out COMPLETED once it clicked anything there, such as focusing an input or following a
link that leads back. The three on-disk crawls stopped at login still displayed `completed`.

Measured in the maker smoke, which reproduces the bug before the fix: on
`tests/fixtures/login_site` with no login declared, a real crawl clicked `#username` and `#password`
(2 actions) and was refused the submit. Pre-X18 logic calls that COMPLETED.

## What changed

- **`src/autotester/stages/explore_status.py` (new, 102 lines)** is where a finished crawl is judged
  and a stored one is shown. It is split out because `explore.py` sits at the 300-line cap (AT-460).
  - `terminal_status(...)` returns `(status, reason)` in this order:
    1. **X18(a)** `never_left_login`: with a declared login case, if every node's `url_template`
       equals the login case's own start template (templated with the crawler's own
       `url_template(absolute_url(...), keep_host=False)`), the result is **LOGIN_FAILED** with the
       reason "the login case ran, but every screen reached was still the login page (…)".
    2. **X18(b)** `is_login_wall`: with no login case, if every reached node has a `DENIED_POLICY`
       edge whose reason is `FORM_SUBMIT_REFUSED`, **and** no `NAVIGATED` edge reaches a node whose
       signature differs from the seed's, the result is **LOGIN_WALL** with a reason naming the wall.
       This holds regardless of `actions_used`.
    3. Otherwise the result is STOPPED_BOUND, AT-242's BLOCKED_NO_ACTIONS, or COMPLETED, as before.
  - The wall checks come **before** the bound check, because a crawl stuck at login is stuck whether
    the frontier emptied or a bound stopped it.
  - **X18(d)** `displayed_status(crawl)`: a stored `completed` with `actions == 0 and denied > 0` is
    shown as BLOCKED_NO_ACTIONS. The file itself is never rewritten.
  - `is_success(crawl)` is the one test every surface uses to decide success colouring.
- `src/autotester/schema/enums.py`: new `CrawlStatus.LOGIN_WALL = "login_wall"`, with a docstring.
- `src/autotester/stages/explore_safety.py`: the literal `"form submit under read_only"` became the
  constant `FORM_SUBMIT_REFUSED`, read by `deny_reason` and by the wall check (C3). Behaviour is
  unchanged.
- `src/autotester/stages/explore.py`: `_terminal_status` now delegates to
  `explore_status.terminal_status` with the graph (`rt.nodes`, `store.list_edges`) and the login
  case, and writes back the named reason. AT-242's "-- every reachable action was denied by policy"
  suffix is kept. The file stays at 300 lines.
- **X18(c)/(d) surfaces:**
  - `ui/routes_crawls.py` crawls table: the status pill shows `displayed_status`, with tone
    `positive` only when `is_success`. It used to be a neutral pill showing the stored status.
  - `ui/crawl_view.summary_stats` crawl page: tone follows `is_success`, not the stop-reason wording.
    The old `_STOP_TONE={"frontier empty": "positive"}` coloured a legacy stuck crawl green. A
    status pill is added.
  - `stages/crawl_report.crawl_summary`, used by the workbook Summary and the page's Run detail:
    `("Status", displayed_status(crawl).value)`.
  - `cli_crawl.echo_crawl_summary`: prints `displayed_status`, in green only when `is_success`,
    otherwise yellow.
- `docs/MAP.md` was regenerated; it gained one line for the new module.
- **Tests:**
  - `tests/test_explore_login_wall.py` (new; **7 tests in cycle 1**, **9 in cycle 2**): (b) positive;
    (b) public-site negatives (one with a sign-in box, one with a form on **every** page); (a)
    positive and negative; (d) unit ×2. Cycle 2 adds the AT-462 single-page-app and placeholder tests.
  - `tests/test_crawl_status_surfaces.py` (new, 9 tests): the crawls table, crawl page, workbook and
    CLI for both stuck shapes, plus "a real completed crawl is still green".
  - `tests/test_explore_blocked.py`: **one existing assertion changed.**
    `test_a_login_gate_with_every_action_denied_is_not_reported_completed` is literally the X18(b)
    login-gate shape, so it now expects `LOGIN_WALL` instead of `BLOCKED_NO_ACTIONS`. Its name, its
    `"denied" in stop_reason` assertion and its intent (never COMPLETED) are unchanged.
  - Also in `tests/test_explore_blocked.py`, a **new** test keeps AT-242's own status covered by a
    non-login shape: a page whose only control is a deny-listed "Delete everything" button gives
    BLOCKED_NO_ACTIONS.

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_explore_login_wall.py tests/test_crawl_status_surfaces.py tests/test_explore_blocked.py -o addopts= -q` | **`21 passed`** in cycle 2 (9 + 9 + 3; cycle 1 was 19, and my cycle-1 "20" was wrong) |
| `uv run pytest tests/test_explore_login_wall.py tests/test_explore_blocked.py tests/test_explore.py tests/test_explore_login_bypass.py tests/test_ui_crawls.py tests/test_ui_crawl_login.py tests/test_crawl_report.py tests/test_crawl_status_surfaces.py -o addopts= -q` | all pass (maker: 52 + the added tests) |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract (`scratchpad/x18x`). I removed
`projects/erp`, `pathlynks` and `vidysea-erp` right after extraction. The 12 unit files were copied
in, with its own `uv sync`, and `explore_status.__file__` and `crawl_view.__file__` were confirmed
inside the extract. Each anchor matched exactly once, and each edit was restored in a `finally`. The
named tests are `test_explore_login_wall.py`, `test_crawl_status_surfaces.py` and
`test_explore_blocked.py`. The baseline was `18 passed`, which became `19 passed` once the M3 gap test
was added, and it was green again after every restore.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, single file) | Observed |
|---|---|---|---|
| **X18 Verify:** a login page with a followable link, no login case, is not COMPLETED with actions ≥ 1 (and (a)) | `test_a_login_page_with_a_followable_link_back_is_not_completed`, `test_a_login_case_that_never_leaves_the_login_page_is_login_failed`, `test_a_login_gate_…` | `explore_status.py`: delete the 5 lines of the (a)+(b) checks (the pre-X18 body, X18's named sabotage) | **3 failed** — `COMPLETED is LOGIN_WALL`, `COMPLETED is LOGIN_FAILED`, `BLOCKED_NO_ACTIONS is LOGIN_WALL` |
| (a) a declared login case that never leaves the login page is LOGIN_FAILED | `test_a_login_case_that_never_leaves_the_login_page_is_login_failed` | `explore_status.py`: `if template is None or not templates or templates != {template}:` → `if True:` | **1 failed** — `COMPLETED is LOGIN_FAILED` |
| (b) a link to a structurally different screen means it is NOT a wall | `test_a_public_site_with_a_form_on_every_page_is_still_completed` | `explore_status.py`: `e.outcome is EdgeOutcome.NAVIGATED and …` → `False and e.outcome …` | **1 failed** — `LOGIN_WALL is COMPLETED` (see note) |
| (d) a legacy completed no-op is never displayed as success | legacy unit test + the 4 `[legacy_completed_no_op]` surface tests | `explore_status.py`: `if crawl.status is CrawlStatus.COMPLETED and crawl.actions == 0 and crawl.denied > 0:` → `if False:` | **5 failed** — the unit test, table (`status word itself must not say completed`), page (`badge-pass`), workbook (`'completed' != 'completed'`), CLI (`': completed '`) |
| (c) crawls table never green for a stuck crawl | `test_the_crawls_table_does_not_show_a_stuck_crawl_as_success[both]` | `routes_crawls.py`: `_tone` → `return "positive"` | **2 failed** — `nothing in the row may be coloured success` |
| (c) crawl page never green for a stuck crawl | `test_the_crawl_page_does_not_colour_a_stuck_crawl_as_success[both]` | `crawl_view.py`: `tone = "positive" if is_success(crawl) else "warning"` → `tone = "positive"` | **2 failed** — `'badge-pass' not in …` |
| (d) workbook Summary shows the displayed status | `test_the_workbook_summary_does_not_say_completed[legacy]` | `crawl_report.py`: `displayed_status(crawl).value` → `crawl.status.value` | **2 failed** — the workbook (`'completed' != 'completed'`) and the page's Run detail (`'>completed<' not in …`), which reads the same summary rows |
| (c) CLI line never green for a stuck crawl | `test_the_cli_line_does_not_say_completed_or_print_green[both]` | `cli_crawl.py`: `fg=… if is_success(crawl) else …` → `fg=typer.colors.GREEN` | **2 failed** — `'green' != 'green'` |
| The guard can say yes: a real completed crawl stays green | `test_a_really_completed_crawl_is_still_green_everywhere` | `explore_status.py`: `is_success` → `return False` | **1 failed** — `'badge-pass' in …` (the row showed `badge-blocked`) |

**Note on row 3, a gap the sabotage found:** M3 **survived** at first. My only negative had a
pricing page with **no** form, so the "every screen carries a refused submit" half made it not a
wall, and the signature half was never tested alone. My first repair still survived. I debugged the
actual graph and found that an extra `Plans` link reached a third screen with no form. The final
test puts a newsletter form on every page with no form-less screen reachable, so only the
structural-difference condition separates it from a wall. The M3 run after that:
`1 failed, 18 passed — LOGIN_WALL is COMPLETED`.

**Correction from the cycle-1 checker:** I wrote that removing only the "every node is walled"
requirement had no isolating test. The checker applied that edit and it **did** go red (2 failed in
`test_explore_blocked.py`), so the requirement is covered. I still add no row of my own for it,
because I did not observe it myself.

**Cycle-2 re-run of the `explore_status.py` rows.** The fix moved these anchors, so I re-ran them in
the same extract with the cycle-2 `explore_status.py` and test file synced in (`cmp` identical). The
baseline was **`21 passed`**, and green again after every restore.
- **M1** (X18 Verify: pre-X18 body) → **3 failed**, the same three assertions as above.
- **M2** (a): the new condition line → `if True:` → **1 failed**, `COMPLETED is LOGIN_FAILED`.
- **N1 (AT-462)**: drop ` or len({n.signature for n in reached}) != 1` so only templates are
  compared → **1 failed**, `test_a_single_page_app_that_logged_in_on_the_same_url_is_not_login_failed`
  with `LOGIN_FAILED is COMPLETED`.
- **N2 (AT-462)**: `if step is None or PLACEHOLDER_RE.search(step.target):` → `if step is None:` →
  **1 failed**, `test_a_placeholder_login_url_is_never_compared_as_the_root_page` with
  `LOGIN_FAILED is COMPLETED`.
- **M3** (b) → **1 failed**. **M4** (d) → **5 failed**. **M9** (guard says yes) → **1 failed**.
  Each has the same assertions as in the cycle-1 table.
- **M5–M8** (the surface files `routes_crawls.py`, `crawl_view.py`, `crawl_report.py`,
  `cli_crawl.py`) were **not re-run**. Cycle 2 did not touch those files, and the cycle-1 checker
  reproduced all four.

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at458-2026-09-17-maker-smoke/report.json`. **LOCAL target only**: the
`login_site` fixture on 127.0.0.1:8765, with a synthetic project and **no login declared**, plus a
hand-written legacy-shaped `crawl.json`.
- I clicked **Explore again**. The real crawl ended **`login_wall`** with 2 actions (clicks into the
  two inputs) and 1 refusal. Pre-X18 logic would call this COMPLETED.
- On the crawls table, the legacy row reads **BLOCKED_NO_ACTIONS** and the new row **LOGIN_WALL**.
  Both pills are `badge-blocked` and neither is green.
- The crawl page shows `LOGIN_WALL · stopped: STOPPED AT A LOGIN WALL …`, both pills `badge-blocked`.
- 0 console errors.

## Full suite

**Cycle 3:** one clean run, output redirected in full to a fresh file (61 lines), started after the
cycle-3 sabotage and the N5 cleanup. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`,
and its final line is **`1376 passed, 2 skipped, 32 xfailed, 1 warning in 279.43s (0:04:39)`**, exit=0.

Against cycle 2's 1368, this unit adds a net **+5**: 12 − 9 = +3 in `test_explore_login_wall.py`,
plus the 2 new live SPA tests. That gives 1373. The other **+3 are not attributed to this unit**: the
other session's AT-216 unit landed meanwhile (`b889b53`/`bcbba40`). All 32 XFAIL lines are
AT-416 / AT-417.

**Files in this unit as of cycle 3:**
- `src/autotester/schema/enums.py`
- `src/autotester/stages/explore_safety.py`
- `src/autotester/stages/explore_status.py` (new)
- `src/autotester/stages/explore.py`
- `src/autotester/stages/crawl_report.py`
- `src/autotester/ui/crawl_view.py`
- `src/autotester/ui/routes_crawls.py`
- `src/autotester/cli_crawl.py`
- `docs/MAP.md`
- `tests/test_explore_login_wall.py` (new)
- `tests/test_crawl_status_surfaces.py` (new)
- `tests/test_explore_blocked.py`
- `tests/test_explore_login_spa_live.py` (new)
- `tests/fixtures/spa_login_site/index.html` (new)

**Cycle 2:** one clean run, output redirected in full to a fresh file (61 lines), started after the
cycle-2 sabotage re-run. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and
its final line is **`1368 passed, 2 skipped, 32 xfailed, 1 warning in 409.80s (0:06:49)`**, exit=0.
The count is +5 over cycle 1's 1363: the **2** AT-462 tests from this unit, and **3 not attributed to
it**. The other session's doctor work has since landed as commits `8edaf17` / `bfd081d` (AT-461). All
32 XFAIL lines are AT-416 / AT-417.

**Cycle 1:** one clean run, output redirected in full to a fresh file (61 lines), started after sabotage and the
smoke had finished. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its
final line is `1363 passed, 2 skipped, 32 xfailed, 1 warning in 324.47s (0:05:24)`, exit=0.

*Count correction (cycle 2):* cycle 1 added 17 tests (7 + 9 + 1 new) and changed 1 assertion, not
18. On top of the last green 1344 that gives 1361, so **two** extras in 1363 are **not attributed to
this unit**. The shared tree holds another session's
uncommitted `doctor.py`/`test_doctor.py` work (the AT-457 checker also noted it), and that is the
likely source. All 32 XFAIL lines are `tests/test_browser_scroll_invariance.py` cases whose reasons
name AT-416 / AT-417, which are pre-existing.

**Files in this unit:**
- `src/autotester/schema/enums.py`
- `src/autotester/stages/explore_safety.py`
- `src/autotester/stages/explore_status.py` (new)
- `src/autotester/stages/explore.py`
- `src/autotester/stages/crawl_report.py`
- `src/autotester/ui/crawl_view.py`
- `src/autotester/ui/routes_crawls.py`
- `src/autotester/cli_crawl.py`
- `docs/MAP.md`
- `tests/test_explore_login_wall.py` (new)
- `tests/test_crawl_status_surfaces.py` (new)
- `tests/test_explore_blocked.py`
