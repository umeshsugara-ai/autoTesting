# Manifest — v8-known-route-inventory

**Unit:** QUEUE TOP-3 row 2 — measure the product map against ground truth. A local app sits behind a login and declares every route it has. A crawl with the login case must enter every route that can be reached by clicking, must not enter the form-gated route, and must name each miss with a reason.
**Contract:** `qa/contracts/coverage.md` — **proposed V8**. The queue row says the checker adds V8 as a routine criterion when the maker picks the unit; the maker has not edited contracts. Also V7 (reasons for holes), `explore.md` X4, X5/X6 (read_only refuses form submits) and X17 (login case), plus core-invariants C1, C2, C7.
**Goal task:** none. This is Umesh's 2026-09-16 22:25 priority: *"puura product map hona chiaye na aend to end testing . each possible route"* (`qa/feedback-inbox.md`).
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none filed. This builds the instrument the queue row asks for.
**Status:** checked-PASS (qa/verdicts/v8-known-route-inventory.md, cycle 1, commit cadef68; V8 adopted verbatim into coverage.md; the checker filed AT-483 (low): a crawl orphaned by a server kill stays `running` forever)

## Proposed V8 wording (for the checker to adopt, amend or reject)

> **V8 — the map is measured against a known inventory.** At least one local fixture product declares its full post-login route inventory. The inventory covers a nav menu, pagination, a route that appears only on a later page, hash routes, a nested page, a link inside a click-opened drawer, and a form-gated screen.
> A real-browser crawl with the login case must:
> - enter every route marked `reached`;
> - not enter the `policy` route, and name its refusal in V7 coverage.
>
> Under a bound, every missed route must be accounted for by a V7 reason, either on the control that leads to it or on a screen upstream that was itself missed. Routes that share a url template are told apart by a control only that route shows.

## What changed (no production code)

| Path | Change |
|---|---|
| `tests/fixtures/inventory_site/` (new) | **Pages.** `login.html` with tester / fixture-pass, `logout.html`, `app/guard.js` (redirects to login when signed out). Under `app/`: `home.html` (nav, plus a "Open help drawer" button that reveals a "Keyboard shortcuts" link), `shortcuts.html`, `projects.html` (page 1 or 2 from `?page=`; page 2 alone lists "Archived project"), `project-archived.html`, `reports.html` (hash router for `#/weekly` and `#/monthly`, each rendering distinct buttons), `settings.html`, `settings/security.html`, `search.html` (a GET form to results), `results.html`. |
| `tests/fixtures/inventory_site/inventory.json` (new) | **Ground truth.** 12 routes, each with `template`, `marker` (a control only that route shows, where a template is shared), `from`, `via`, `how` and `expect`. 11 are `reached` and 1 (`results`) is `policy`. |
| `tests/test_crawl_inventory_live.py` (new, 152 lines) | **Tests.** Two tests that run real headless Chromium with `run_crawl` and the login case. (1) `test_a_logged_in_crawl_maps_every_route_and_names_the_one_it_refused`: COMPLETED, every `reached` route entered, `results` not entered, a DENIED_POLICY edge with `FORM_SUBMIT_REFUSED` from the Search screen, and a V7 hole `policy:form submit under read_only` on `/app/search.html`. (2) `test_every_route_a_depth_bound_kept_out_is_accounted_for_by_coverage`: with max_depth=1, some routes are missed, each miss is explained by a hole or a not-entered screen named after its `via` control on its `from` template, or by its `from` route being missed too, and percent < 100. |

## What the measurement found

Unbounded, the crawl reached **all 11** reachable routes: 12 screens and 78 actions, COMPLETED, `frontier empty`. Coverage was 85% (78 of 91). The 13 holes were the form submit plus 12 Log out controls, which are never-click by design. No route was missed silently.
- **Page 2, the hash routes and the drawer state are distinct screens.** They share a url template but have different signatures.
- **Shortcuts and Archived project have the same signature** (`b13e3c16`, the nav-only pages). They stay separate by url template.
- **The one real gap is not a defect under current policy.** The search results screen can only be reached through a form submit, which read_only refuses. That gap belongs to the open `post-login-forms` gate.

## How to verify

| # | Command | Expected (maker run) |
|---|---|---|
| 1 | `uv run pytest tests/test_crawl_inventory_live.py -p no:cacheprovider -o addopts= -q` | `2 passed in 320.15s` (bound tree). The same 2 passed in the scratch copy: 228.01 s + 128.30 s. |
| 2 | `uv run ruff check src tests scripts` | All checks passed |
| 3 | `uv run autotester doctor` | doctor: clean |
| 4 | full suite with `--deselect tests/test_crawl_inventory_live.py` (the whole suite plus these tests passes the 600 s tool limit; the file is run by #1) | see Full suite |

## Capability coverage

**Setup.** Run in a `git archive HEAD` extract (`scratchpad/v8x`), with erp, pathlynks and vidysea-erp removed. The fixture and test file were copied in and `uv sync` was run. The module loaded from the copy (`…\scratchpad\v8x\src\autotester\__init__.py`).
- **Baseline in the copy:** `['1 passed in 228.01s']` for the full-crawl test and `['1 passed in 128.30s']` for the depth test.
- **Each edit:** single hunk, anchor counted once with CRLF normalised, original bytes restored in `finally`.
- **Script:** `scratchpad/v8x/sabotage.py`. Output: `mut.out`.

| Capability | Check | Falsifying edit | Observed (after) |
|---|---|---|---|
| Routes that share a url template (page 2, hash routes, drawer) are mapped as their own screens | full-crawl test, `assert not missed` (line 117) | `explore_node.py::_enqueue`: also drop a new screen when any known node has the same `url_template` | `E AssertionError: routes the crawl never entered: ['project-archived', 'projects-page-2', 'reports-monthly', 'reports-weekly', 'shortcuts']` — 1 failed in 111.83s |
| read_only never submits the form, so the gated route is not entered | full-crawl test, line 122 | `explore_safety.py`: `if policy.write_policy == WritePolicy.READ_ONLY and el.is_form_submit:` becomes `if False and el.is_form_submit:` | `E AssertionError: read_only must never submit the search form` — 1 failed in 234.83s |
| Every route a depth bound kept out has a V7 reason | depth test, `assert not silent` (line 151) | `crawl_coverage.py::_screens_not_entered`: `return list(holes.values())` becomes `return []` | `E AssertionError: routes missed with no reason in coverage: ['projects-page-2', 'reports-monthly', 'reports-weekly', 'security', 'shortcuts']` — 1 failed in 110.36s |

**Not covered by its own row.** The line 123-127 assertions (the DENIED_POLICY edge and the policy hole on search) are only reached once line 122 holds. No separate edit was run for them, so they are claimed as supporting asserts, not as isolated capabilities.

## Known limits, disclosed

- **Speed: about 2.8 s per crawl action on a local static site.** In `session.settle`, networkidle plus a fixed 500 ms grace runs 2-3 times per action. That puts the two live tests at about 5.5 min and pushes the full suite past the 600 s tool limit. This is the crawler's real pace; this unit does not change it. A product with 1,000 actions would take about 47 min. The checker may want to file that separately.
- **The inventory is hand-declared.** V8 measures the crawler against a product whose routes the author knows. It does not prove coverage on an unknown product.
- **Coverage holes point at the source, not the destination.** A hole names the source screen's template plus the control, not where the control leads, which is why the inventory carries `from`/`via`. A human reading coverage cannot see *which screen* a not-entered control led to.
- **Duplicate holes per template.** Home, and Reports in its three hash states, each list their own "Log out" hole. That is correct per screen, but it looks repetitive on the page.

## Live browser evidence

**Maker smoke: not run through the UI this cycle.** It is stated as a gap. The two tests drive a real headless Chromium through `run_crawl`, but not through the AutoTester UI.

The queue row says "a UI-started crawl". **The checker should run Mode D in its OWN browser:**
- Serve `tests/fixtures/inventory_site` on 127.0.0.1.
- Run the UI from an isolated extract with a synthetic project: base_url `/app/home.html`, a login case navigating to `/login.html` with #username / #password / #sign-in, and a crawl approval.
- Start a crawl from the Crawls page.
- Check that the crawl page and report.xlsx show all 11 routes reached and the form submit as a policy hole.

Local fixtures only; no external site (the live-crawl-target gate is open).

## Full suite

The maker ran `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py` and it exited 0: `1413 passed, 2 skipped, 2 deselected, 32 xfailed, 1 warning in 502.86s`.
- The 32 XFAILs are AT-416/417.
- The 2 deselected are this unit's tests. They were run separately (verify #1).
- Some passing tests come from other sessions' working-tree files and are not claimed by this unit.

## Commit / push

Commit after PASS with a narrow pathspec. The push stays held (other sessions' commits that nobody has verified are in origin/master..HEAD).
