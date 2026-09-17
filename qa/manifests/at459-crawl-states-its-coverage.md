# Manifest — at459-crawl-states-its-coverage

**Unit:** AT-459 / coverage.md **V7** — a crawl states its own coverage and names every hole with one reason
**Contract:** `qa/contracts/coverage.md` **V7** (a)(b)(c)(d) + Verify; `qa/contracts/explore.md` X16 (surfaces) and X18 (login_wall); core-invariants C1, C2, C3, C7
**Goal task:** none — Umesh's 2026-09-16 priority change ("puura product map … each possible route"); `qa/QUEUE.md` TOP-3
**Date:** 2026-09-17
**Fix cycle:** 3 of max 3 (last)
**Dual check:** no
**Issues addressed:** AT-459 (high); AT-470, AT-471, AT-472 (cycle 1, confirmed fixed by the cycle-2 checker); AT-476 (cycle 2)
**Status:** checked-PASS (qa/verdicts/at459-crawl-states-its-coverage.md, cycle 3, commit 3175e7a; cycles 1-2 FAIL, fixed)

## Cycle 3 — the fix for `qa/verdicts/at459-…md` "## Cycle 2" (FAIL)

**Quoted:** *"[V7b / step 4b] sev: medium · the manifest claims `_tried` skips policy/unnamed refusals
and links refused as off-domain before they are tried (the OFF_DOMAIN_LINK_REFUSED constant was added
for this). No test checks either skip, and the manifest has no Capability-coverage row for them.
Deleting `and e.outcome not in REFUSED_BEFORE_TRYING`, or the OFF_DOMAIN_LINK_REFUSED clause, leaves
the named test set at 25 passed … · add one crawl test per skip (a refusal, and separately an
off-domain link refused before it was tried, placed before the control a global bound cut short, on a
screen that did not use up its cap) and one coverage row for each · issue: AT-476"*

The checker was right. Both skips were claimed without a test that could fail. **No production logic
changed in cycle 3.** The two tests are shaped exactly as it prescribed, in
`tests/test_crawl_coverage_bounds.py`:
- **`test_a_policy_refusal_is_not_counted_as_a_try_against_the_per_node_cap`**: home = a
  deny-listed "Delete everything" button **first**, then links p1, p2, p3. With `per_node_action_cap=3`
  and `max_actions=2`, the crawl stops on max_actions after p1 and p2, and the cap is not spent (2 < 3).
  The untried `a.p3` must be **`bound:max_actions`**.
- **`test_an_off_domain_link_refused_before_trying_is_not_counted_against_the_cap`**: the same, with
  an off-domain link (`https://evil.test/`) first.

**The checker's low note, also fixed:** with `coverage.error` set, the Coverage tile read "0%". It now
shows "—" (`crawl_view.summary_stats`: `if cov and not cov.error`), pinned by
**`test_a_coverage_that_could_not_be_computed_shows_no_percentage`**.

**Not addressed here, named by the checker as pre-existing and not charged:** AT-477. With an invalid
flowspec.json, POST /explore and the crawl page return 500.

**Cycle-3 sabotage.** Run in a fresh `git archive HEAD` extract (`scratchpad/v7x3`) with erp,
pathlynks and vidysea-erp removed. All 11 unit files were copied in, with `uv sync`, and
`crawl_coverage.__file__` was confirmed inside the extract. Anchors were matched on
LF-normalised text, because the checker hit CRLF misses, and the original bytes were restored in a
`finally`. The baseline was **`28 passed`**, and `28 passed` again after restoring.

| Row | Falsifying edit (single hunk) | Observed |
|---|---|---|
| **X1, AT-476: policy/unnamed refusals counted as tries** | `crawl_coverage.py`: delete `and e.outcome not in REFUSED_BEFORE_TRYING` (the checker's own edit) | **1 failed** — `test_a_policy_refusal_…`: `'bound:per_node_action_cap' == 'bound:max_actions'` |
| **X2, AT-476: pre-refused off-domain links counted as tries** | `crawl_coverage.py`: delete the `and not (e.outcome is EdgeOutcome.OFF_DOMAIN_REFUSED and e.reason == OFF_DOMAIN_LINK_REFUSED)` clause (the checker's own edit) | **1 failed** — `test_an_off_domain_link_refused_…`: `'bound:per_node_action_cap' == 'bound:max_actions'` |
| **T1: the tile shows a number when coverage failed** | `crawl_view.py`: `if cov and not cov.error else` → `if cov else` | **1 failed** — `test_a_coverage_that_could_not_be_computed_shows_no_percentage` |

All cycle-2 rows (V1, V2, C1–C6, V3–V11) are unaffected by cycle 3, whose only product change is the
tile expression. The cycle-2 checker reproduced 12 of 12.

**Live browser (cycle 3): SKIP for the tile change, a stated gap.** "Coverage could not be computed"
is reachable only if `compute_coverage` raises, which no honest UI action produces. The rendered-page
test above covers it. The cycle-1 and cycle-2 maker smokes, and the cycle-2 checker's own Mode D,
exercised every other surface this unit touches.

## Cycle 2 — fixes for `qa/verdicts/at459-crawl-states-its-coverage.md` (cycle 1 FAIL)

### 1. AT-470 (high): screens a bound dropped were not holes

**Quoted:** *"screens that max_depth drops are not holes and get no reason. `bound:max_depth` is
never emitted, and a crawl stopped by depth can show 100% … Probe: max_depth=0 gave "100% of controls
(1 of 1)" … Live run 03 (max_depth=1) … /app/order-1001.html is not listed anywhere · take the dropped
screens from NAVIGATED edges whose to_node never became a node, record each as a `bound:max_depth`
hole in the counts and the Unreached sheet, and cap the figure below 100 while any exist"*

- **`crawl_coverage._screens_not_entered`**: for every NAVIGATED edge whose `to_node` never became a
  node, it records one `CoverageHole` per dropped screen (deduplicated by `to_node`), taking the
  selector and name from the link that led there.
  - The reason is `bound:max_depth` when `source.depth + 1 > max_depth`, else `bound:max_screens`.
  - Measured: the `max_screens` branch is **not reachable by a real crawl**. `explore.stop_reason`
    checks max_screens before every action, so the crawl stops before following the link.
    `test_a_screen_bound_names_the_controls_it_left_untried` pins what does happen: that control is
    an untried `bound:max_screens` hole. The branch stays as defence and **is not claimed as tested**.
- **New schema field** `CrawlCoverage.screens_not_entered: list[CoverageHole]`, kept **separate from
  control `holes`**, so V7(c)'s control identity (`exercised + holes == discovered`) is unchanged.
  A dropped screen is not a discovered control of a reached screen.
- **The cap:** `percent` may reach 100 only when `status is COMPLETED and not screens_not_entered`.
- **Surfaces:**
  - crawl page: a "screens not entered: <reason pills>" line;
  - workbook Summary and Run detail: a new row, "Screens not entered, by reason" (`screens_by_reason`);
  - the **Unreached sheet**: one row per dropped screen, "screen behind '<link>' — not entered".

### 2. AT-471 (medium): the wrong bound was named

**Quoted:** *"the wrong bound is named. Controls the per-node cap left on an EARLIER screen are
labelled with the global bound that fired later. Probe: per_node_action_cap=2, max_actions=3, and "/"
a.p3 is labelled `bound:max_actions`. On a LOGIN_WALL crawl the rewritten stop_reason turns a real
global bound into `bound:per_node_action_cap` · name the global bound only on the screen being visited
when it fired, and read the bound's name before `_terminal_status` rewrites stop_reason"*

- **Per-screen attribution:** `_tried(node_id, edges)` counts the actions `visit_node` spent on that
  screen. It excludes policy and unnamed refusals, pre-refused off-domain links (now the constant
  `explore_safety.OFF_DOMAIN_LINK_REFUSED`, also used by `explore_node`) and BACK edges.
  `_untried_reason` returns `bound:per_node_action_cap` when **this screen** spent its cap, and names
  the global bound only otherwise.
- **The bound's name comes from the crawl's counters, not the text:** `of_run` passes
  `bound=explore.stop_reason(rt)` (screens_found, actions_used, clock). That is the same function
  that ended the crawl, and it does not read the stop reason `_terminal_status` may have rewritten.

### 3. AT-472 (medium): coverage could cost the crawl its record

**Quoted:** *"`_finish` now reads flowspec.json. If that file is invalid … `_finish` raises before
`save_crawl`, and crawl.json stays `running` with finished_at null … if the spec cannot be read,
record the cause and leave the spec counts None, so coverage can never lose the crawl record"*

- `of_run` wraps `load_flowspec()`. On failure it sets `spec_error` (scrubbed through the session's
  secrets) and continues with `spec=None`, so the other coverage numbers are still computed.
- `of_run` also wraps the whole computation. On any failure it returns `CrawlCoverage(error=…)`
  instead of raising, so `_finish` always saves.
- New fields `spec_error` and `error`. The page and workbook show "could not be computed (…)" or the
  spec error instead of a number.

### Also: the checker's C3 question

`is_candidate` restated `visit_node`'s filter. `explore_node.visit_node` now **calls
`crawl_coverage.is_candidate`**, so the crawl and its coverage share one definition.

### Tests (cycle 2)

`tests/test_crawl_coverage.py` would have gone past 300 lines, so the cycle-2 tests are split into
**`tests/test_crawl_coverage_bounds.py`** (new, 8 tests). It imports the helpers from the first file,
the same way these tests already import `crawl_fake`.
- AT-470:
  - `…depth_bound_kept_the_crawl_out_of_are_holes…` (max_depth=0 on the default site);
  - **`test_a_depth_bound_alone_keeps_an_otherwise_full_crawl_below_100`**, the checker's exact probe:
    one link, exercised, 1 of 1, and its screen beyond max_depth=0 must read < 100.
- AT-470/max_screens: `test_a_screen_bound_names_the_controls_it_left_untried`.
- AT-471:
  - **`…per_node_cap_on_an_earlier_screen_is_not_blamed_on_a_later_global_bound`**, the checker's probe
    (cap 2, max_actions 3): the home screen's `a.p3` must be `bound:per_node_action_cap`;
  - `…login_wall_crawl_still_names_the_real_global_bound` (unit);
  - **`…bound_named_comes_from_the_crawls_counters_not_the_rewritten_stop_reason`** (`of_run` with a
    stand-in runtime whose stop_reason is the wall sentence).
- AT-472:
  - **`test_an_unreadable_flowspec_never_costs_the_crawl_its_record`** (a hand-broken `flowspec.json`,
    real crawl: finished, not running, `spec_error` set, other numbers computed);
  - `test_a_failure_inside_coverage_is_recorded_never_raised`.
- The four cycle-1 unit tests switched to the new `compute_coverage(status, bound, bounds, …)`
  signature through a `_compute` helper. Their assertions are unchanged.

### Cycle-2 sabotage

Run in a fresh `git archive HEAD` extract (`scratchpad/v7x2`) with erp, pathlynks and vidysea-erp
removed right after extraction. All 11 unit files were copied in, with `uv sync`, and
`crawl_coverage.__file__` was confirmed inside the extract. The named set was
`test_crawl_coverage.py`, `test_crawl_coverage_bounds.py` and `test_crawl_report.py`, with a baseline
of **`24 passed`**, and `25 passed` once the C2 test existed. It was green after every restore.

| Row | Falsifying edit (single hunk, `crawl_coverage.py` unless named) | Observed |
|---|---|---|
| **V1, V7 Verify: drop a reason class from the tally** | append a hole only `if reason != "not_visited"` | **3 failed** — `(c) the books must balance…` fired first, plus the page test and the max_screens test's balance |
| V2 (d) not completed may read 100 | `percent=percent,` | **1 failed** — `assert 100 < 100` |
| **C1 AT-470 dropped screens not listed** | `not_entered = []` | **1 failed** — `the dropped screens must be listed` |
| **C2 AT-470 dropped screens don't cap the figure** | `whole = status is CrawlStatus.COMPLETED` | first run: **SURVIVED** (24 passed), because the default site's other holes kept it under 100. I added the checker's exact 1-of-1 probe test, and the re-run gave **1 failed** — `a crawl a bound kept out of a screen can never read 100 (V7d)` |
| **C3 AT-471 per-node cap ignored** | `if tried >= bounds.per_node_action_cap or bound is None:` → `if bound is None:` | **1 failed** — the home hole `a.p3` read `bound:max_actions` |
| **C4 AT-471 bound read from the rewritten text** | `bound=explore.stop_reason(rt)` → `bound=rt.stop_reason` | **1 failed** — `'stopped at a…a form submit' == 'max_actions'` |
| **C5 AT-472 unreadable FlowSpec raises** | remove the try around `load_flowspec()` | **1 failed** — `ValueError: …flowspec.json: 1 validation error for FlowSpec` |
| **C6 AT-472 coverage failure raises** | `except Exception` → `except ZeroDivisionError` | **1 failed** — `RuntimeError: graph was unreadable` |
| V3 login_wall / V4 not_visited / V6 abandoned=error / V7 spec counts | as cycle 1 | **1 / 2 / 1 / 1 failed**, the same assertions |
| V8 coverage not persisted (`explore.py`) | delete the `"coverage": …` line | **10 failed** |
| V9 Coverage tile (`crawl_view.py`) / V10 Unreached rows (`crawl_report.py`) / V11 invented number (`crawl_report.py`) | as cycle 1 | **1 / 1 / 1 failed** |

## What was wrong

`Crawl` carried `screens`, `actions`, `denied`, `issues`, `tool_failures` and `noise_counts`. **No
coverage figure existed anywhere.** A control never tried because a bound fired, or never seen
because its screen was left queued, was not listed at all. So a report of what a crawl found read as
the whole product.

## What changed

- **`src/autotester/schema/crawl.py`** (182 lines):
  - `CoverageHole(node_id, url_template, selector, name, reason)`.
  - `CrawlCoverage(controls_discovered, controls_exercised, screens_reached,
    screens_queued_unvisited, percent, holes, spec_screens_reached, spec_screens_total)`, with
    `by_reason()`.
  - `Crawl.coverage: CrawlCoverage | None = None`. `None` means a crawl recorded before V7, and
    old `crawl.json` files still load.
- **`src/autotester/stages/crawl_coverage.py`** (new, 117 lines). The computation is **pure and
  post-hoc, over the graph a crawl already persists**; the BFS is untouched.
  - **Candidate** is the same filter `explore_node.visit_node` uses: `visible and enabled and not
    obscured`. It is distinct per `(node, selector)`.
  - **Exercised** means an edge from that node with that target whose outcome is NAVIGATED,
    SAME_SCREEN or DIALOG.
  - **Otherwise, exactly one reason from the closed set** (`REASONS`):

    | Case | Reason |
    |---|---|
    | edge SKIPPED_UNNAMED | `unnamed` |
    | edge OFF_DOMAIN_REFUSED | `off_domain` |
    | edge DENIED_POLICY | `policy:<the deny reason>`, except a form-submit refusal on a `LOGIN_WALL` crawl, which is `login_wall` |
    | edge ERRORED | `error` |
    | no edge, screen still QUEUED | `not_visited` |
    | no edge, screen abandoned (ABORTED_*) | `error` |
    | no edge, screen EXPLORED | `bound:<stop_reason>` for max_screens, max_actions or wall_clock_s, otherwise `bound:per_node_action_cap` |

  - `percent = floor(exercised·100/discovered)`, **capped at 99 for any crawl that did not
    complete** (V7d).
  - With a FlowSpec, `spec_screens_reached/total` come from V5's `unreached_screens`.
  - `of_run(rt, status)` is the one-line entry `explore._finish` calls.
- **`src/autotester/stages/explore.py`**: `_finish` sets `"coverage": crawl_coverage.of_run(rt, status)`.
  The import joins the existing `from autotester.stages import` line. The file is **300 lines**, at
  the cap.
- **Surfaces (V7d):**
  - `stages/crawl_report.py`:
    - `coverage_figure()` gives "N% of controls (x of y)", or "not recorded (this crawl predates
      coverage)" for an old crawl, never an invented number.
    - `coverage_rows()` adds Coverage, "Screens reached / left queued", "Not exercised, by reason"
      and FlowSpec screens reached. These rows sit **directly after "Stopped because" and "Write
      policy"** in `crawl_summary`, which feeds both the workbook Summary and the crawl page's Run
      detail.
    - A new **"Unreached"** workbook sheet has one row per hole (URL template, control, selector,
      reason). The file is 193 lines.
  - `ui/crawl_view.summary_stats` adds a **"Coverage" headline tile first in the stat row**, plus a
    "coverage: … · not exercised: <reason pills>" line under the status/stop line. The file is 203
    lines.
- `docs/MAP.md` was regenerated; it gained the new module and the two new models.
- **Tests:**
  - `tests/test_crawl_coverage.py` (new, 13 tests).
  - `tests/test_crawl_report.py`: the pinned sheet list `SHEETS` gains **"Unreached"**. That is an
    existing assertion updated for a new sheet. I also fixed the stale "Six sheets" docstring in
    `export_crawl_excel`.

**Not in this unit:**
- A control can have its own `max_depth` reason, but depth-limited screens are dropped by
  `_enqueue` before they become nodes, so their controls are never discovered. They are neither
  counted nor listed. **Named for the checker:** V7(b) lists `bound:max_depth`, and this unit never
  emits it.
- AT-463 (a bound hit on the last page reads "frontier empty") is pre-existing and affects which
  `bound:` a hole is given there.

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_crawl_coverage.py tests/test_crawl_report.py -o addopts= -q` | `17 passed` |
| `uv run pytest tests/test_crawl_coverage.py tests/test_crawl_report.py tests/test_crawl_status_surfaces.py tests/test_ui_crawls.py tests/test_explore.py tests/test_explore_blocked.py tests/test_explore_login_wall.py -o addopts= -q` | all pass |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract (`scratchpad/v7x`). I removed
`projects/erp`, `pathlynks` and `vidysea-erp` right after extraction. The unit's 8 files were copied
in, with its own `uv sync`, and `autotester.stages.crawl_coverage.__file__` and
`autotester.ui.crawl_view.__file__` were confirmed inside the extract. Each anchor matched exactly
once, and each edit was restored in a `finally`. The named set was `test_crawl_coverage.py` and
`test_crawl_report.py`, with a baseline of `17 passed`, green after every restore.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, single file) | Observed |
|---|---|---|---|
| **V7 Verify / (c):** the books balance | `test_a_crawl_with_a_small_max_actions_states_less_than_full_coverage` | `crawl_coverage.py`: count a hole only `elif reason != "not_visited":`, dropping one reason class from the tally | **2 failed** — `(c) the books must balance: exercised + every hole == discovered`, plus the page test (`not_visited` no longer rendered) |
| (d) a crawl that did not complete never reads 100 | `test_a_crawl_that_did_not_complete_never_reads_100` | `crawl_coverage.py`: `_percent` returns `value` uncapped | **1 failed** — `assert 100 < 100` |
| (b) the login-wall refusal is named `login_wall` | `test_a_refused_submit_on_a_login_wall_is_named_login_wall` | `crawl_coverage.py`: the LOGIN_WALL condition → `if False:` | **1 failed** — `{'policy:form…read_only': 1} == {'login_wall': 1}` |
| (a)(b) queued screens counted as `not_visited` | the V7 verify test | `crawl_coverage.py`: delete the QUEUED → `not_visited` branch | **2 failed** — `(2 >= 1 and 0 >= 1)` and the page test |
| (b) the per-node cap is named | `test_the_per_node_cap_is_named_when_it_leaves_controls_untried` | `crawl_coverage.py`: `return "bound:per_node_action_cap"` → `return f"bound:{stop_reason}"` | **1 failed** — `assert 0 >= 1` |
| (b) an abandoned screen's controls are `error` | `test_an_abandoned_screen_names_its_untried_controls_error` | `crawl_coverage.py`: delete the non-EXPLORED → `error` branch | **1 failed** — `{'bound:per_n…': 2} == {'error': 2}` |
| (a) FlowSpec screens reached are counted | `test_flowspec_screens_reached_are_counted_when_a_spec_exists` | `crawl_coverage.py`: delete the `spec_screens_reached = …` line | **1 failed** — `(None, 2) == (1, 2)` |
| (a) coverage is persisted on every crawl | the 4 fake-crawl tests + page + workbook | `explore.py`: delete the `"coverage": crawl_coverage.of_run(rt, status),` line | **6 failed** — `None is not None` / `'NoneType' … 'percent'` |
| (d) the crawl page shows a Coverage headline tile | `test_the_crawl_page_shows_the_coverage_figure_and_reasons` | `crawl_view.py`: delete the `theme.stat(… "Coverage")` line | **1 failed** — `a headline tile beside Screens/Actions, same billing as the stop (V7d)` |
| (d) the workbook Unreached sheet lists every hole | `test_the_workbook_has_the_figure_and_an_unreached_sheet` | `crawl_report.py`: the Unreached `ws.append(...)` → `pass` | **1 failed** — `assert 0 == 7` |
| (d) an old crawl says "not recorded", never a made-up number | `test_a_crawl_recorded_before_coverage_says_so_instead_of_inventing_a_number` | `crawl_report.py`: the not-recorded text → `"0% of controls (0 of 0)"` | **1 failed** — `'not recorded' in …` |

**Two gaps the sabotage found, fixed before this manifest:**
- **Row 1, V7's named sabotage:** it first went red on the "≥ 3 reason classes" assertion, not the
  balance identity, because that assertion ran first. I moved the balance assertion first, with its
  own message, so the named check is the one that fires.
- **Row 9 SURVIVED at first:** the page test found the percentage in the "coverage:" text line, so
  deleting the headline tile went unnoticed. The test now asserts the tile's exact markup.

The re-run after both fixes: row 1 → `2 failed — (c) the books must balance…`, row 9 →
`1 failed — a headline tile…`, and restored → `17 passed`.

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

**Cycle 2 (AT-470), in the same evidence file.** The cycle-2 extract was served on 8061 with the same
synthetic root and the login declared. Bounds were 10 screens / 60 actions / 120 s / **max_depth 1**,
the checker's live run 03. The result was **83% (5 of 6)**, and the screen behind **"Order 1001"** on
`/app/orders.html` is now listed as **not entered, `bound:max_depth`**:
- on the crawl page ("screens not entered: BOUND:MAX_DEPTH: 1");
- in Run detail and the workbook Summary ("Screens not entered, by reason = bound:max_depth: 1");
- on its own row in the **Unreached** sheet.

0 console errors.

`qa/evidence/browser-at459-2026-09-17-maker-smoke/report.json`. **LOCAL target only**: the
`login_site` fixture on 127.0.0.1:8771, with a synthetic project whose **login case is declared**
(AT-457).
- **Capped crawl, 3 actions** → stopped_bound, **50% (3 of 6)**. The holes are
  `policy:never-click (logout)` 1, `bound:max_actions` 1 and `not_visited` 1, which balances as
  3 + 3 = 6. Screens reached/queued are 2 / 1.
  - The crawl page shows the **"50% COVERAGE" tile first** and the coverage line with reason pills.
  - `report.xlsx` has Summary `Coverage = 50% of controls (3 of 6)`, and its **Unreached** sheet names
    each control: Log out → policy, Order 1001 → bound:max_actions, the Profile page's Dashboard
    link → not_visited.
- **Uncapped crawl** → completed, **85% (6 of 7)**, with all **4 screens behind the login** reached.
  Its only hole is **Log out**, which is deliberately never pressed. The figure is honestly not 100.
- 0 console errors.

## Full suite

**Cycle 3:** one clean run, output redirected in full to a fresh file (62 lines; the extra line is
only a wrapped progress row), started after the cycle-3 sabotage. The command was
`uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its final line is
**`1407 passed, 2 skipped, 32 xfailed, 1 warning in 454.04s (0:07:34)`**, exit=0. Cycle 3 adds 3
tests, taking 1403 to 1406. The other **+1 is not attributed to this unit**: the cycle-2 checker's own
run was already at 1404 with only this unit's cycle-2 files. All 32 XFAIL lines are AT-416 / AT-417.
The files are the same 11 as in cycle 2; cycle 3 changed `src/autotester/ui/crawl_view.py` and
`tests/test_crawl_coverage_bounds.py`.

**Cycle 2:** one clean run, output redirected in full to a fresh file (61 lines), started after the
cycle-2 sabotage and smoke. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`,
and its final line is **`1403 passed, 2 skipped, 32 xfailed, 1 warning in 315.70s (0:05:15)`**,
exit=0. Cycle 2 adds **9** tests: `test_crawl_coverage_bounds.py` has 9, and the first file keeps its
13. That takes 1393 to 1402. The other **+1 is not attributed to this unit**: the other session's
AT-469 landed meanwhile (`f7e83cd`). All 32 XFAIL lines are AT-416 / AT-417.

**Files in this unit as of cycle 2:**
- `src/autotester/schema/crawl.py`
- `src/autotester/stages/crawl_coverage.py` (new)
- `src/autotester/stages/explore.py`
- `src/autotester/stages/explore_node.py`
- `src/autotester/stages/explore_safety.py`
- `src/autotester/stages/crawl_report.py`
- `src/autotester/ui/crawl_view.py`
- `docs/MAP.md`
- `tests/test_crawl_coverage.py` (new)
- `tests/test_crawl_coverage_bounds.py` (new)
- `tests/test_crawl_report.py`

**Cycle 1:** one clean run, output redirected in full to a fresh file (61 lines), started after the sabotage and
smoke had finished. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its
final line is **`1393 passed, 2 skipped, 32 xfailed, 1 warning in 290.44s (0:04:50)`**, exit=0.

This unit adds 13 tests (1376 → 1389). The other **+4 are not attributed to it**: the other session's
AT-465/466 unit landed meanwhile (`eb8d617`). All 32 XFAIL lines are AT-416 / AT-417.

**Files in this unit:**
- `src/autotester/schema/crawl.py`
- `src/autotester/stages/crawl_coverage.py` (new)
- `src/autotester/stages/explore.py`
- `src/autotester/stages/crawl_report.py`
- `src/autotester/ui/crawl_view.py`
- `docs/MAP.md`
- `tests/test_crawl_coverage.py` (new)
- `tests/test_crawl_report.py`
