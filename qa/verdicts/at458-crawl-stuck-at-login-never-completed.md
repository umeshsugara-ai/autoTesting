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
