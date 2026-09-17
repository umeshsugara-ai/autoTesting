# Verdict — at458-crawl-stuck-at-login-never-completed

**Date:** 2026-09-17
**Checker:** /checker Mode A + Mode D (fresh subagent, bound to `D:\autoTesting`)
**Manifest:** `qa/manifests/at458-crawl-stuck-at-login-never-completed.md`
**Cycle checked: 1**

```
VERDICT: FAIL
SCOREBOARD: 3/4 criteria met (X18 b, c, d met; a over-fires), 5/6 invariants hold (X4 bound-naming gap is pre-existing, not charged; X3 screen identity not respected by (a))
FAILURES (if any):
- [X18(a)] sev: medium · never_left_login compares url_template only, so a SUCCESSFUL login whose post-login screens share the login start template (hash-routed SPA `/#/login` -> `/#/dashboard`, same-URL SPA, or a `{{SECRET:KEY}}` NAVIGATE target, which templates to `/`) ends LOGIN_FAILED "still the login page" although a different screen (X3: template + signature) was reached · compare screen identity (template AND the login screen's single signature), add a two-`/`-nodes-different-signature test that must stay COMPLETED, and skip (a) when the NAVIGATE target is an unresolved placeholder · issue: AT-462
- [manifest] sev: low · the pasted verify expectation "20 passed" and "test_explore_login_wall.py (new, 8 tests)" do not reproduce: 19 passed; collect-only shows 7 + 9 + 3 · correct the counts on resubmit · issue: none (manifest accuracy)
CAPABILITY-COVERAGE: 9/9 rows reproduced (plus the unclaimed "every node walled" edit: also red, 2 failed in test_explore_blocked.py)
LIVE-BROWSER: qa/evidence/browser-at458-crawl-stuck-at-login-never-completed-2026-09-17-checker/report.json (14/14 steps PASS, 0 console errors)
ISSUES-WRITTEN: AT-462, AT-463
EXPLANATION: X18(b)/(c)/(d) are genuinely delivered and load-bearing: the literal X18 sabotage (the pre-X18 `_terminal_status` body) turns 3 tests red, every surface row isolates, and my own headed browser saw login_wall / login_failed / legacy blocked_no_actions in non-success colour and a correct login go green with 4 post-login screens. The one failure is (a) over-firing on SPA-shaped products, a false "your credentials are wrong" on a working login, reproduced at unit level. AT-463 (inner max_actions bound reported as "frontier empty") is pre-existing and not charged to this unit.
```

## What was re-run

- Bound tree: `pytest test_explore_login_wall + test_crawl_status_surfaces + test_explore_blocked` -> **19 passed** (manifest said 20); the 8-file set -> **78 passed**; `ruff check src tests scripts` -> All checks passed!; `autotester doctor` -> doctor: clean. Full suite NOT re-run.
- Throwaway copy `scratchpad/checker-at458`: `git archive HEAD`, projects/erp, pathlynks and vidysea-erp deleted at once (only `regression-demo` left), 12 unit files copied in (cmp-identical), `uv sync`, and `explore_status` / `crawl_view` / `explore` `__file__` all resolve inside the copy. Named check baseline **19 passed**, and green again after every restore.

## Capability coverage (checker-reproduced, one anchor per edit, count asserted == 1)

| Row | Edit | Result, and the assertion that fired |
|---|---|---|
| X18 Verify (literal) | `explore.py::_terminal_status` body replaced by the pre-X18 body | 3 failed: `COMPLETED is LOGIN_WALL` (login_wall.py:60), `COMPLETED is LOGIN_FAILED` (:138), `BLOCKED_NO_ACTIONS is LOGIN_WALL` (blocked.py:43) |
| (a) | `templates != {template}` guard -> `if True:` | 1 failed: `COMPLETED is LOGIN_FAILED` |
| (b) M3 | `False and e.outcome is NAVIGATED` | 1 failed: `LOGIN_WALL is COMPLETED` (:102) |
| (b) every-node-walled (unclaimed) | delete the `any(n.id not in walled)` return | 2 failed: blocked.py:60 and :77 |
| (d) | legacy condition -> `if False:` | 5 failed: unit, table, page, workbook, CLI |
| (c) table | `_tone` -> positive | 2 failed: "nothing in the row may be coloured success" |
| (c) page | tone -> positive | 2 failed: `'badge-pass' not in` |
| (d) workbook | `displayed_status(crawl).value` -> `crawl.status.value` | 2 failed: page Run detail `>completed<` and workbook `'completed' != 'completed'` |
| (c) CLI | fg -> GREEN | 2 failed: `'green' != 'green'` |
| guard says yes | `is_success` -> False | 1 failed: `'badge-pass' in` row |

## The changed existing assertion (test_explore_blocked.py)

**Justified, not a softening.** The fixture is a sign-in form (a refused submit plus an unnamed control) with no navigation, which is X18(b)'s shape exactly, and X18(b) demands a *distinct* status that names the wall. The never-COMPLETED intent and the `"denied" in stop_reason` assertion still hold, because the wall reason contains "denied by read_only". AT-242's BLOCKED_NO_ACTIONS keeps its own non-login test (deny-listed "Delete everything"), and that test is load-bearing: it went red under the unclaimed every-node-walled sabotage.

## Probes beyond the manifest (in the copy)

- **A public search page whose only control is a search form** -> `login_wall` (actions 1, denied 1), with the reason "stopped at a login wall ... declare a login case". This meets X18(b)'s literal wording, so it is **not a failure as written**. Still, the label is false for a public search page. QUESTION for the contract owner: should (b)'s reason say "only a refused form submit, no way onward (often a login wall)" rather than asserting a login?
- **A single contact page** ("Send message") -> `completed`, because "Send" hits the destructive-name deny-list rather than FORM_SUBMIT_REFUSED, so the wall check never sees it. That is not a false wall, but it shows the wall rule is keyed to one refusal string only.
- **Login start URL with a query string or trailing slash** (`/signin/?next=/dashboard`, `/signin/`, `/signin?x=1`, schemeless `app.test/signin`) -> `/signin` in every case. The comparison works.
- **`{{SECRET:LOGIN_URL}}` NAVIGATE target** -> no crash, but it templates to `/`. That feeds the AT-462 false LOGIN_FAILED.
- **Wall check before bound check** -> correct in effect. A bound recorded by `_bfs` needs a non-empty queue, so an unvisited node exists and "every node walled" is false; public-site bound runs stayed `stopped_bound` (max_screens=1, max_actions=0/1). The real gap is pre-existing: the mid-node action bound in `explore_node.py:221` never sets stop_reason, so a single login page with max_actions=1 reads `completed / frontier empty` (**AT-463**, not charged).
- **Does `displayed_status` reach anything that writes crawl.json?** No. Its callers are cli_crawl (echo), crawl_report.crawl_summary (xlsx and page rows), crawl_view and routes_crawls. In Mode D the legacy crawl.json was byte-identical before and after rendering.
- **X16 surface list vs changes:** crawl page, crawls table, CLI line, workbook Summary and crawl.json (new status persisted by `_finish`) are all covered. A grep for other `crawl.status` renderers in ui/ and cli found none. No surface missed.

## Mode D (my own headed Playwright Python, Chromium; LOCAL only)

Fixture `tests/fixtures/login_site` from the copy on 127.0.0.1:8766. UI from the copy on 127.0.0.1:8064, with AUTOTESTER_ROOT set to a fresh scratch root seeded through ProjectStore (synthetic project `wallprobe`, base_url `/app/dashboard.html`, allowed_domains 127.0.0.1, one CRAWL approval, two synthetic login cases). Login cases were declared through the real "Login for crawls" select, and every crawl was started from the real Explore form.
1. With no login declared, the notice rendered before the crawl. The crawl ended `login_wall` (actions 2, denied 1). On the crawl page both pills were `badge-blocked`. In the crawls table the row read `login_wall` / `badge-blocked`. The downloaded Excel Summary reads **Status = login_wall**.
2. A legacy crawl.json I wrote myself (completed, 0 actions, 3 denied) shows `blocked_no_actions` / `badge-blocked` in the table and on the page. The file was not rewritten.
3. With the WRONG-password case declared, the crawl ended `login_failed`, with the reason "... every screen reached was still the login page (/login.html) ...", non-success in both places.
4. With the CORRECT case declared, the crawl ended `completed`, with `badge-pass` on the page and in the table. Its screens were /app/dashboard.html, /app/orders.html, /app/order-1001.html and /app/profile.html.

Console errors: 0 on the final run. An earlier aborted attempt logged one 403 on POST /explore, caused by my own form bounds exceeding the seeded approval (a driver error). My first assertion pass also mis-flagged the `.badge-pass` CSS rule and the per-node "explored" pills; I tightened those assertions to crawl-level pills and re-ran everything from a fresh root. Both servers were stopped and the browser closed.

## Ledger / push

- AT-462 and AT-463 were appended to `qa/issues.jsonl`. **That file is not committed:** it holds another session's uncommitted hunks, and committing it would sweep them in.
- AT-458 stays `open`.
- **Push HELD:** `origin/master..HEAD` carries another session's AT-419 commits.

## Cycle 2

**Date:** 2026-09-17
**Checker:** /checker Mode A + Mode D (fresh subagent, bound to `D:\autoTesting`)
**Manifest:** `qa/manifests/at458-crawl-stuck-at-login-never-completed.md` (Fix cycle 2)
**Cycle checked: 2**

```
VERDICT: FAIL
SCOREBOARD: 3/4 criteria met (X18 b, c, d met; a still over-fires on a working same-URL login), 5/6 invariants hold (X3 screen identity still not respected by (a))
FAILURES (if any):
- [X18(a)] sev: medium · AT-462 is only half fixed. The new guard is `len({n.signature for n in reached}) != 1`, which counts signatures instead of comparing against the login screen. A working login on a single-page app whose post-login dashboard is ONE structural state (or a hash-routed /#/login -> /#/dashboard with one dashboard state) still reaches one node at the login template with one signature, and ends LOGIN_FAILED "still the login page". Reproduced LIVE through the real UI: my SPA fixture, correct credentials, crawl_01M2PKD40X4963FH7GNN8KYMXQ = 1 node /index.html sig bdc67e3b34fd whose elements are the dashboard's "Refresh numbers" button and whose screenshot reads "Dashboard / Signed in as tester", status login_failed. Also reproduced at unit level (probes P4, P5). The cycle-2 test passes only because it hand-builds TWO nodes · capture the login screen's own signature at bootstrap (observe after the case's NAVIGATE, before FILL) and fire (a) only when every node equals (login template, login signature); add a test with ONE post-login node at the login template that must stay COMPLETED · issue: AT-462 (stays open)
CAPABILITY-COVERAGE: 11/11 rows reproduced (M1, M2, N1, N2, M3, M4, M9, M5-M8), all attributed to the named tests, baseline 21 passed and green after every restore
LIVE-BROWSER: qa/evidence/browser-at458-crawl-stuck-at-login-never-completed-2026-09-17-checker-c2/report.json (4/5 steps PASS; step 04 SPA correct login -> login_failed = the FAIL above; 0 console errors on all 5)
ISSUES-WRITTEN: AT-462 annotated with the cycle-2 reproduction, kept open (no new id)
EXPLANATION: The manifest counts are now correct (21 passed), the placeholder half of AT-462 is really fixed (including a placeholder mixed into a URL), and X18(b)/(c)/(d) plus the login_site behaviours all hold live. The SPA half is not fixed: "more than one signature" is a proxy for "a screen other than the login screen", and it fails exactly when the logged-in app has one state, which is the plainest SPA shape and the one I was asked to try. Separately, and not charged: a failed login whose login page gains a new CONTROL (a dismissable error banner, a "Try again" link) now yields two signatures and reads COMPLETED. Under X3 that is literally a second screen, so X18(a) as written allows it, but the signature-at-bootstrap fix above would close it too.
```

## What was re-run (cycle 2)

- Bound tree: the named 3 files -> **21 passed** (matches the corrected manifest); the 8-file set -> **80 passed**, exit 0; `ruff check src tests scripts` -> All checks passed!; `autotester doctor` -> doctor: clean. `explore_status.py` is 112 lines, `explore.py` 300. Full suite not re-run.
- Throwaway copy `scratchpad/checker-at458c2`: `git archive HEAD`, then projects/erp, pathlynks and vidysea-erp deleted at once (only `regression-demo` left). All 12 unit files copied and cmp-identical, `uv sync` run, and the `explore_status`, `crawl_view` and `explore` `__file__` paths all resolve inside the copy.

## Capability coverage (checker harness: anchor count == 1, file changed, baseline exit 0 asserted, named test must appear in the FAILED list, green re-asserted after restore)

| Row | Edit | Result |
|---|---|---|
| M1 X18 Verify | delete the (a)+(b) block in `terminal_status` | 3 failed: followable-link-back, never-leaves-login, login-gate (blocked.py) |
| M2 (a) | condition line -> `if True:` | 1 failed: never_leaves_the_login_page_is_login_failed |
| N1 AT-462 | drop ` or len({n.signature ...}) != 1` | 1 failed: single_page_app_that_logged_in_on_the_same_url |
| N2 AT-462 | `if step is None or PLACEHOLDER_RE.search(...)` -> `if step is None:` | 1 failed: placeholder_login_url_is_never_compared_as_the_root_page |
| M3 (b) | `False and e.outcome is NAVIGATED` | 1 failed: form_on_every_page_is_still_completed |
| M4 (d) | legacy condition -> `if False:` | 5 failed: unit + table + page + workbook + CLI |
| M9 guard says yes | `is_success` -> `return False` | 1 failed: really_completed_crawl_is_still_green_everywhere |
| M5 table | `_tone` -> positive | 2 failed |
| M6 page | tone -> positive | 2 failed |
| M7 workbook | `displayed_status(crawl).value` -> `crawl.status.value` | 2 failed (workbook + page Run detail) |
| M8 CLI | fg -> GREEN | 2 failed |

N1 is load-bearing for the test it names, but the test pins a two-node graph. A real crawl of a one-state SPA produces a one-node graph, and no row covers that shape (see FAILURE).

## Probes (in the copy, `explore_status.terminal_status`, completed=True)

| Probe | login_template | Status | Judgement |
|---|---|---|---|
| P1 failed login, login page gains a 2nd signature (error banner with a control) | /login | **completed** | UNDER-fires. Named, not charged: X3 makes it a second screen, so it is allowed by X18(a) as written. A text-only banner leaves the signature unchanged (live step 02 confirms login_failed on login_site). |
| P1b failed login, one signature | /login | login_failed | correct |
| P2 login case with no NAVIGATE | None | completed | (a) is skipped entirely, and (b) is gated on `login_case is None`, so a navigate-less case that never leaves the login page reads COMPLETED. Residual, not charged: `_bootstrap_login` also keys on NAVIGATE, and a login case without a start page is malformed authoring. |
| P3 `https://app.test/{{SECRET:LOGIN_PATH}}`, stuck on /login | None | completed | The placeholder fix under-fires here: the stuck login is not detected. Acceptable, because the template cannot be known before fill. Recorded. |
| P3b same, product at / | None | completed | correct (no false login_failed) |
| **P4 same-URL SPA, working login, one dashboard state** | / | **login_failed** | **the FAILURE** |
| **P5 hash route /#/login -> one dashboard state** | / | **login_failed** | **the FAILURE** (the fragment is stripped by url_template) |
| P6 lowercase `{{secret:x}}` | / | login_failed | Not a finding: the placeholder grammar is uppercase-only everywhere (`PLACEHOLDER_RE`), so this is not a placeholder. |

## Mode D (my own headed Playwright Python, Chromium; LOCAL 127.0.0.1 only; synthetic data)

- `tests/fixtures/login_site` from the copy on :8767. My own SPA fixture (`scratchpad/spa_fixture/index.html`, outside the repo) on :8768: the form submit swaps the DOM to a dashboard at the same URL, and auth persists in localStorage. `?tabs=1` adds Overview/Reports tabs, which give a second state. The UI ran from the copy on :8065 with a fresh AUTOTESTER_ROOT (`scratchpad/at458c2_root`) seeded through ProjectStore: projects loginprobe, spaprobe and spatabs, each with its own CRAWL approval and synthetic login cases. Login cases were declared through the real "Login for crawls" select, and each crawl was started from the real Explore form.
- **01** login_site, no login -> `login_wall` (actions 2, denied 1), no badge-pass on the page or the row. PASS.
- **02** login_site, wrong password -> `login_failed`, "still the login page (/login.html)", non-success. PASS.
- **03** login_site, correct login -> `completed`, badge-pass on the page and the row, with 4 screens behind the login (/app/dashboard, orders, profile, order-{id}). PASS.
- **04** SPA, correct login -> **`login_failed`**. The one node is the Dashboard (screenshot `05-node-3589de.png` shows "Signed in as tester"). **FAIL.**
- **05** SPA with tabs, correct login -> `completed` (2 signatures at /index.html). PASS. This shows the fix works only when the app happens to have a second state.
- Console errors: 0 on every step. Servers were stopped (`servers_stopped: true`), and the browser was closed.

## Ledger / push

- AT-462 stays **open**, with a `cycle2_recheck` note added to its row. `qa/issues.jsonl` is **not committed**: it holds other sessions' uncommitted hunks.
- AT-458 stays open. Fix cycle 3 of 3 remains.
- **Push HELD:** `origin/master..HEAD` carries another session's unverified AT-419 commits.

## Cycle 3

**Date:** 2026-09-17
**Checker:** /checker Mode A + Mode D (fresh subagent, bound to `D:\autoTesting`)
**Manifest:** `qa/manifests/at458-crawl-stuck-at-login-never-completed.md` (Fix cycle 3 of 3)
**Cycle checked: 3**

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (X18 a, b, c, d), 6/6 invariants hold (X3 screen identity now respected by (a); X10 bootstrap still types only via run_case; X16 surfaces unchanged and still load-bearing)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 7/7 rows reproduced (manifest N3, N4, M1, M2, N2 + checker-own X1 observe->None and N5-pin), baseline 26 passed in the copy and green after every restore; M3-M9 not re-run (cycle 3 did not touch those files; cycles 1 and 2 reproduced them)
LIVE-BROWSER: qa/evidence/browser-at458-crawl-stuck-at-login-never-completed-2026-09-17-checker-c3/report.json (5/5 required steps PASS + 1 informational probe; 0 console errors on all 6; servers stopped, browser closed)
ISSUES-WRITTEN: AT-458 -> fixed, AT-462 -> fixed, AT-467 (new, medium: the disclosed sticky-banner under-fire, needs a contract decision)
EXPLANATION: The cycle-2 failure is really fixed. (a) now compares every node against the login template AND the signature observed on the login page before the case types, so a working single-page-app login whose dashboard is one state at the same url reads COMPLETED (live, on my own fixture), while a wrong password still reads LOGIN_FAILED (live, on both fixtures). Re-inserting the cycle-2 signature-count logic turns the live SPA test red, so that test is not vacuous. The disclosed under-fire, where a failed login leaves a persistent control on the login page and reads COMPLETED, reproduces live. X18(a) as written only demands LOGIN_FAILED when no screen other than the login start screen is reached, and under X3 a different signature is a different screen, so it is filed as AT-467 for a contract decision and not charged.
```

## What was re-run (cycle 3)

- **Bound tree:**
  - The 4 named files (login_wall, crawl_status_surfaces, blocked, login_spa_live) gave **26 passed**, matching the manifest.
  - The 8-file set plus the SPA live file gave **85 passed**.
  - `ruff check src tests scripts` gave All checks passed!, and `autotester doctor` gave doctor: clean.
  - `explore.py` is 299 lines and `explore_status.py` is 129 lines.
  - The checker did NOT re-run the full suite.
- **Throwaway copy `scratchpad/checker-at458c3`:**
  - Built with `git archive HEAD`. Projects erp, pathlynks and vidysea-erp were deleted at once, leaving only `regression-demo`.
  - All 14 unit files were copied in and are cmp-identical, including `tests/fixtures/spa_login_site/index.html`.
  - `uv sync` ran, and the `explore_status`, `explore` and `crawl_view` `__file__` paths all resolve inside the copy.
  - The harness's Python restore rewrote files with CRLF endings. I re-copied them from the bound tree, re-asserted cmp-identical, and re-greened the copy (14 passed) before Mode D.

## Capability coverage (checker harness: anchor count == 1, baseline exit 0 asserted, restore in `finally`, green re-asserted)

| Row | Edit | Result |
|---|---|---|
| N3: cycle-2 logic re-inserted | comparison line -> `{templates} != {template} or len({signatures}) != 1` | **3 failed**: the one-state SPA unit test, the unobserved-signature test, and the **live** `test_a_correct_login_on_a_single_page_app_is_not_login_failed`. The manifest said 2; the extra red is the None test. |
| N4: signature never recorded | `explore.py`: delete `rt.login_signature = explore_status.observed_signature(...)` | **2 failed**: the fake-crawl never_leaves_the_login_page test and the **live** wrong-password SPA test |
| M1: X18 Verify | delete the (a)+(b) block in `terminal_status` | **5 failed**: followable-link-back, never-leaves-login, every-screen-is-observed-login, login-gate (blocked.py), live wrong-password SPA |
| M2: (a) never fires | comparison line -> `if True:` | **3 failed**: never-leaves-login, every-screen-is-observed-login, live wrong-password SPA |
| N2: placeholder | `if step is None or PLACEHOLDER_RE...` -> `if step is None:` | **1 failed**: the placeholder test |
| X1 (checker's own): observation silently broken | `observed_signature` returns None | **2 failed**, the same two as N4, so a broken recording cannot hide |
| N5 pin (checker's own) | `n.signature != login_signature` -> `(login_signature is not None and n.signature != login_signature)`, which makes a None signature get judged | **1 failed**: `test_an_unobserved_login_screen_is_never_judged_failed` (`LOGIN_FAILED is COMPLETED`), so the behaviour stays pinned after the early-return guard was removed |

## Judgements asked for

- **X10 / AT-226.**
  - The signature is recorded in `_already_past_login` after goto+settle, only on the not-redirected branch, and before `run_case`.
  - `observe()` only reads url, title and the enumerated elements. Nothing is typed.
  - The redirect branch still returns True before recording. The exception branches still return False and set `login_precheck_error`. The return values are unchanged.
  - `test_explore_login_bypass.py` passed within the 85.
- **observed_signature raising or returning None.**
  - `except Exception` returns None, and a None signature never equals a node's, so (a) is not judged and the crawl falls through to the other checks. It cannot crash; it can only under-fire.
  - LOGIN_FAILED needs every node to match both the login template and the exact pre-typing structure. A working login cannot produce that unless the product shows the login form again.
- **Disclosed under-fire (1).**
  - Reproduced live in step 06: with a persistent "Login failed [Dismiss]" banner, a wrong password gives `completed`, coloured green.
  - X18(a) as written requires "no screen other than the login case's own start screen". Under X3 a screen is template + signature, and the banner page has a different signature. As written, this is **not a failure**.
  - It is still a false green that the X18 title's intent arguably covers. I filed it as **AT-467** (medium) for a contract decision instead of charging it on the last cycle.
- **Is the live SPA test non-vacuous?** Yes. N3 turns the correct-login live test red, and N4, M1, M2 and X1 each turn the wrong-password live test red.

## Mode D (my own headed Playwright Python, Chromium; LOCAL 127.0.0.1 only; synthetic data)

**Setup:**
- `tests/fixtures/login_site` was served from the copy on :8769.
- **My own SPA fixture**, `scratchpad/spa_fixture_c3/app.html`, is outside the repo and differs from the maker's. It runs on :8770 at one url:
  - signed out: a "Welcome" login form;
  - signed in: an "Overview" with exactly one control ("Export report");
  - `?sticky=1`: a failed-login banner with a Dismiss button that persists.
- The UI ran from the copy on :8066 with a fresh AUTOTESTER_ROOT (`scratchpad/at458c3_root`), seeded through ProjectStore with projects loginprobe, spaok, spabad and spasticky. Each project has its own CRAWL approval and synthetic login cases.
- Each login case was chosen through the real "Login for crawls" select, and each crawl was started from the real Explore form.

**Steps:**
- **01** login_site, no login -> `login_wall` (actions 2, denied 1), no badge-pass on the page or the row. PASS.
- **02** login_site, wrong password -> `login_failed`, "still the login page (/login.html)", non-success. PASS.
- **03** login_site, correct login -> `completed`, badge-pass on the page and the row, 4 screens behind the login (/app/dashboard, orders, profile, order-1001). PASS.
- **04** own SPA, correct login -> **`completed`**, badge-pass. One node, /app.html, sig ffc077940906; the screenshot shows the dashboard with 0 refused. The cycle-2 logic would have called this login_failed. PASS.
- **05** own SPA, wrong password -> **`login_failed`**, "still the login page (/app.html)", node sig 2285ebd6e7af, non-success. PASS.
- **06** (informational) own SPA ?sticky=1, wrong password -> `completed`, green. This is the AT-467 under-fire.

**Console and cleanup:**
- Console errors: 0 on every step.
- One earlier attempt aborted before any browser action, on a driver typo: the wait URL named index.html instead of app.html. I deleted the root and repeated the full run fresh.
- Servers stopped (`servers_stopped: true`, no listeners left on 8769/8770/8066), and the browser was closed.

## Ledger / goal / push

- In `qa/issues.jsonl`, AT-458 and AT-462 are now `fixed` (fixed_date 2026-09-17, cycle3_recheck note), and AT-467 was appended. **The file is not committed:** it holds other sessions' uncommitted hunks.
- No goal task matches this unit, so there is no goal close.
- The checker does not commit the unit's code; the maker closes it out.
- **Push HELD:** `origin/master..HEAD` carries another session's unverified AT-419 commits.
