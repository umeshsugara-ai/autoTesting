# T-171 — permission-surface coverage (AT-663, D-040)

## Status: ready-for-check

**Fix cycle:** 1
**Contract:** `qa/contracts/coverage.md` **V9** (the criterion this unit is formally judged
against), with V7(a)-(d) unchanged and still holding. Filed intent: **PS1-PS4** in
`qa/feedback-inbox.md` (heading "`qa/contracts/permission-surface.md` — PS1-PS4, covering T-171
(D-040)"), which is NOT a contract file — `qa/contracts/permission-surface.md` does not exist and
was not created; its authorization gate (`qa/gates/at638-four-contract-files-authorization.md`) is
still open and still the human's.
**Branch:** see the final report. **Worktree:** `.claude/worktrees/agent-a34c44eb5901959f8`.

---

## The problem, in one line

Coverage counted "controls the crawl happened to find". A bounded crawl that reached one screen
of a nine-screen product and pressed every button on it read **100 %**, while every control the
supplied account is entitled to press sat untouched and unlisted. V9 forbids exactly that: the
denominator may not be chosen by what was seen.

## What changed (file:line, all edits in place — no new src module)

| File | What |
|---|---|
| `src/autotester/schema/crawl.py:130` | `CoverageHole.reason` doc gains `not_reached` |
| `src/autotester/schema/crawl.py:134-154` | **new model `PermittedControl`** — one control the account's role permits (`url_template`, `selector`, `name`, `destructive`), `extra="forbid"` |
| `src/autotester/schema/crawl.py:175-186` | `CrawlCoverage` gains `denominator_basis` (`Literal["permitted","screens-reached"]`, default the honest one), `permitted_total`, `permitted_exercised`, `permitted_holes` |
| `src/autotester/schema/crawl.py:196-206` | `by_reason()` / new `permitted_by_reason()` share one `_tally` (C3: one concept, one place) |
| `src/autotester/schema/project.py:135-144` | `Project.permitted_surface: list[PermittedControl]` — the declaration. Empty = the permitted surface is UNKNOWN |
| `src/autotester/stages/crawl_coverage.py:30-35` | `REASONS` gains `not_reached` (the closed set stays closed) |
| `src/autotester/stages/crawl_coverage.py:103-116` | `_key()` — host-insensitive matching between a declared control and a crawled one |
| `src/autotester/stages/crawl_coverage.py:118-129` | `_permitted_reason()` — the ONE reason a permitted control was not exercised |
| `src/autotester/stages/crawl_coverage.py:131-149` | `_permitted_coverage()` — re-base the denominator, list every miss |
| `src/autotester/stages/crawl_coverage.py:160-166` | `of_run` reads `rt.project.permitted_surface` and the run's real `write_policy` (the wire) |
| `src/autotester/stages/crawl_coverage.py:171-175` | `_percent()` extracted — V7(d)'s "never 100 unless whole" rule, now applied to both bases from **one** place |
| `src/autotester/stages/crawl_coverage.py:207-210` | `compute_coverage` re-bases `percent` when a surface is declared |
| `src/autotester/stages/crawl_report.py:67-73` | `coverage_figure` states its basis; the screens-reached branch says **"NOT permission coverage"** in words |
| `src/autotester/stages/crawl_report.py:86-90` | `coverage_rows` gains `Coverage denominator` + `Permitted but not exercised, by reason` |
| `src/autotester/stages/crawl_report.py:163-166` | workbook `Unreached` sheet lists every permitted-but-unexercised control |
| `src/autotester/ui/crawl_view.py:44-48, 79-80` | the crawl page shows the permitted holes as pills beside the existing ones |
| `src/autotester/stages/explore_safety.py:120-145` | **PS2/D-040:** `is_destructive()` + `destructive_last()` — a stable partition, not a sort |
| `src/autotester/stages/explore_node.py:21, 235` | the click loop iterates `destructive_last(node.elements, rt.policy)` (net zero lines: the file was exactly at the 300 cap) |
| `tests/test_crawl_coverage_bounds.py:117-119` | the `SimpleNamespace` runtime stub gains `project` + `crawl.policy` — `of_run` now reads both. **This was a real regression my change caused and the suite caught** (2 failures), fixed by making the stub model the runtime, not by making production code defensive |
| `docs/MAP.md` | regenerated (`autotester map`) — `PermittedControl` row |
| `qa/feedback-inbox.md` | the PS1-vs-`write-policy-tier.md` disagreement, verbatim, plus PS3/PS4 as-built |

### The rule, as implemented

- A **declared** surface → `denominator_basis="permitted"`, `percent = permitted_exercised /
  permitted_total`. Every permitted control not exercised is a `CoverageHole` in
  `permitted_holes` with one reason from the closed set — `policy:<rule>` (the crawl met it and
  refused), `bound:<name>` / `unnamed` / `off_domain` / `error` / `login_wall` / `not_visited`
  (the crawl met it and something stopped it), `policy:destructive under <tier>` (declared
  destructive, run below `ALLOW_WRITES`), or `not_reached`.
- **A blocked control never counts as covered and never leaves the denominator.** It is a hole
  with the refusal as its reason; `permitted_exercised + len(permitted_holes) == permitted_total`.
- **No declared surface → the report says so**, in words, on the crawl page, in `crawl.json`,
  in the workbook Summary: `"… — denominator is screens-reached, NOT permission coverage"`.
- **Nothing is narrowed.** `_permitted_reason` reads the run's actual `write_policy` and reports
  it; it never sets, lowers, or prefers one. A sub-`ALLOW_WRITES` run that skipped a permitted
  destructive control reports that as **a gap in its own coverage** (V9 bullet 4,
  `qa/gates/write-policy-tier.md`).

## PS1-PS4, stated plainly

| | Verdict |
|---|---|
| **PS1** | **Partly.** The "exercised or blocked-with-reason, every one named" half is built and falsified below. The **approval** half is untouched by design: the exercise pass is the crawl's own loop, already gated by `stages/explore_consent.py`, and PS1 itself says reuse consent.md's gate rather than build a second. PS1's negative verify ("no approval → zero controls") is an assertion about `explore_consent`, not about anything T-171 changed, and was **not** re-derived here. PS1's `write_policy=TEST_ACCOUNT` clause **contradicts `qa/gates/write-policy-tier.md`** — filed verbatim in `qa/feedback-inbox.md`, not silently resolved. |
| **PS2** | **Yes.** `explore_safety.destructive_last`, wired into `explore_node._click_loop`. Rows R8/R9. |
| **PS3** | **Yes, by construction.** No second counting mechanism: same `CoverageHole` model, same closed reason set (one member added), same book-balance shape. `controls_discovered`/`controls_exercised`/`holes` are unchanged in meaning and V7(c) still holds over them. |
| **PS4** | **Satisfied by absence, recorded rather than dropped** (as PS4 asks). No new report surface exists. There is exactly **one** `percent` field and exactly **one** place that computes it (`compute_coverage`), rendered through the existing V7 surfaces. There is no second number that could disagree. |

---

## Capability coverage — every row falsified

Method: file copied to `.work/save_*.py`, the exact line the capability rests on broken, the named
test re-run, then the file restored **from the saved copy** (never `git checkout --`, AT-701).
`grep -rn SABOTAGE src tests` → *no sabotage left* after the last restore.

| # | Capability | Falsifying edit | Named test | Observed (RED) |
|---|---|---|---|---|
| R1 | The denominator IS the permitted surface | delete `coverage.percent = _percent(permitted_exercised, permitted_total, whole)` in `compute_coverage` | `test_the_denominator_is_the_permitted_surface_not_the_screens_reached` | `assert 100 == 25` — "the figure must be a fraction of the permitted surface". The 100 is the exact dishonesty V9 forbids |
| R2 | Every permitted-but-unexercised control is **listed** | `continue` before `permitted_holes.append(...)` | `test_a_permitted_control_no_entry_point_reached_is_listed_not_dropped` | `AssertionError: not reached is a REASON, not an absence of one` / `assert {} == {'#never': 'not_reached'}` (3 tests red) |
| R3 | A blocked control never counts as covered | count a control with a `policy:` hole as exercised | `test_a_blocked_control_is_reported_blocked_and_never_counts_as_covered` | `assert [] == [('#pay', 'policy:deny-list: pay')]` |
| R4 | A declared destructive control names the tier that stopped it | delete the `if control.destructive and policy is not ALLOW_WRITES` branch | `test_a_declared_destructive_control_names_the_write_policy_that_stood_in_the_way` | `assert ['not_reached'] == ['policy:destructive under read_only']` |
| R5 | Without a surface, the report says its denominator is screens-reached | drop the `— denominator is screens-reached, NOT permission coverage` clause | `test_without_a_declared_surface_the_report_says_its_denominator_is_screens_reached` | `assert 'NOT permission coverage' in '100% of controls (1 of 1)'` |
| R6 | The basis reaches the page **and** the workbook | delete the `("Coverage denominator", …)` row from `coverage_rows` | `test_the_crawl_page_shows_the_permitted_denominator_and_every_hole`, `…workbook_lists…`, `…names_the_account_role` | `KeyError: 'Coverage denominator'` ×2 + `assert 'Coverage denominator' in '<!doctype html>…'` (3 red) |
| R6b | The workbook lists the permitted holes themselves | delete the `permitted_holes` loop from `_unreached_sheet` | `test_the_workbook_lists_every_permitted_control_not_exercised` | `assert set() == {'#b', '#pay'}` |
| R7 | The wire: a real crawl reads the **project's** declaration | `permitted=rt.project.permitted_surface` → `permitted=None` in `of_run` | `test_the_crawl_reads_the_projects_declared_surface_end_to_end` | `assert 'screens-reached' == 'permitted'` |
| R8 | `destructive_last` really partitions (PS2) | `return list(elements)` | `test_a_destructive_control_is_attempted_after_every_ordinary_one_on_its_screen` | `assert ['Delete acco…'] == ['Open', 'Sav…']` — index 0 diff `'Delete account' != 'Open'` |
| R9 | The ordering is wired into the crawl, not just available (PS2) | `for el in explore_safety.destructive_last(...)` → `for el in node.elements` | `test_the_crawl_really_tries_the_destructive_control_last` | `assert 2 == (6 - 1)`, real recorded edge order `['input.displayname','select.grade','button.del','button.save','a.out','button.icon']` — `button.del` back at index 2 |
| R10 | A declaration is portable across environments | `_key` → `return (url_template, selector)` (host-exact) | `test_the_denominator_is_the_permitted_surface_not_the_screens_reached` (+2) | `assert (0, 4) == (1, 4)` — every control becomes `not_reached` when the node's host-ful `app.test/app` is compared to a declared `/app` |

**No row survived sabotage.** Two anti-vacuity checks I ran on myself:

1. **The fixture does not decide the outcome (AT-697 shape A).** R9 is asserted over the edges a
   *real* (fake-site) crawl recorded, not over a list the test built; R7 crawls the fake site with
   a project the test declared and reads the figure back off the finished `Crawl`. R10 exists
   *because* my first version of the tests used the same `url_template` string on both sides — a
   fixture whose construction would have hidden a host-matching bug. The node template is now
   deliberately host-ful (`app.test/app`) while the declaration is host-less (`/app`).
2. **The mechanism named is the mechanism deleted.** R1 names the re-base line and deletes exactly
   it; R7 names the wire and cuts exactly the argument; R9 names the loop and restores exactly the
   old iterable. Each row's RED output quotes the assertion the row is named for.

---

## Verify — real output, unpiped, no CLI `-q`

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

```
$ uv run pytest
PYTEST_OUTPUT_PLACEHOLDER
```

*(Interim, for the record: an earlier full-suite run on this branch produced **2 failures**, both
mine, both in `tests/test_crawl_coverage_bounds.py` —* `KeyError: 'bound'` *and*
`AttributeError: 'types.SimpleNamespace' object has no attribute 'project'` *— caused by `of_run`
newly reading `rt.project`. Fixed by extending the runtime stub at
`tests/test_crawl_coverage_bounds.py:117`, not by weakening `of_run`. Reported here rather than
quietly re-run into green.)*

Also re-run on request from the orchestrator: `uv run pytest tests/test_goal_done_checks.py`
— result in the final report; it is **not** a known-failing file on this branch.

---

## What I could NOT do

1. **No `RunApproval` work.** PS1's approval clause was deliberately not re-derived (see PS1 row).
   `ui/routes_runs.py::trigger_run` still checks no approval — **AT-570, open, untouched.**
2. **No live-browser proof.** Every test here uses the scripted fake site (`crawl_fake.py`). The
   real-browser inventory proof (`tests/test_crawl_inventory_live.py`, V8) was **not** extended to
   assert a permitted denominator; a checker wanting end-to-end V9 evidence against a real product
   would need a fixture project with a declared `permitted_surface`.
3. **No project declared a surface.** `projects/*/project.json` are untouched — `permitted_surface`
   defaults to empty everywhere, so **every existing project keeps its pre-V9 figure and now
   states, in words, that its denominator is screens-reached.** Populating `pathlynks`' permitted
   surface is a data task with an owner (it is a claim about what Umesh's account may do), not
   something a build subagent should invent. Flagging it as the obvious next unit.
4. **No `docs/DECISIONS.md` entry.** Append-only via `scripts/append_decision.ps1` and this is a
   real approach decision (a new project-config field; the denominator re-based). Left to the
   close-out, per the maker's own close-out ritual — **naming it so it is not forgotten.**
5. **`qa/contracts/` untouched**, as required. The PS1 disagreement went to
   `qa/feedback-inbox.md` verbatim.
6. **A new test file was created** — `tests/test_permission_coverage.py`. Not a new src module;
   `tests/test_crawl_coverage.py` is 251 lines against C2's 300-line cap and could not hold V9's
   ~14 tests. Same shape as `test_crawl_coverage_bounds.py` / `test_coverage_wiring.py`. If the
   checker reads C3's "a new module requires a stated reason in the manifest" as covering test
   files too: **this is that reason.**

## Known limits, disclosed rather than discovered later

- **A declared control is matched on `(path, selector)`.** If a product's selector changes, the
  declaration goes stale and the control reads `not_reached` — loudly (the figure drops), never
  silently. There is no fuzzy or name-based fallback, deliberately: guessing which control a
  declaration meant is how a coverage number becomes fiction.
- **`destructive_last` orders within one screen**, not across the crawl. A destructive control on
  screen 1 is still attempted before an ordinary control on screen 9, because the BFS frontier
  order is `crawl-traversal.md`'s territory, not this unit's. D-040's sentence is satisfied at the
  granularity the exercise loop has; a global destructive-last pass would be a traversal change and
  is **not** claimed here.
- **`is_destructive` reads `policy.deny_patterns`**, the same English-language vocabulary D-016
  defines. A `Löschen` button is not recognised as destructive unless the project extends its
  deny-list — the documented limit `policy_for` already carries, inherited, not introduced.
</content>
