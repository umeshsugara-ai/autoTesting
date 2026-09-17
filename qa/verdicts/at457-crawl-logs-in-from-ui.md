# Verdict: at457-crawl-logs-in-from-ui

**Cycle checked:** 1
**Date:** 2026-09-17
**Checker:** /checker Mode A + Mode D, fresh subagent, bound to `D:\autoTesting`. A previous checker for this unit hit an API rate limit and wrote no verdict. Nothing from that run was used, and its partial evidence folder was deleted and rebuilt.
**Contract:** `qa/contracts/explore.md` X17, with X5, X6 and X10 unchanged; `qa/contracts/ui.md`; `qa/contracts/core-invariants.md`
**Manifest:** `qa/manifests/at457-crawl-logs-in-from-ui.md` (Fix cycle 1, ready-for-check)

```
VERDICT: PASS
SCOREBOARD: 8/8 criteria met (X17a, X17b, X17c, X17-Verify, X5, X6, X10, U5), 4/4 invariants hold (C1, C2, C3, C7)
FAILURES: none
CAPABILITY-COVERAGE: 8/8 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at457-crawl-logs-in-from-ui-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-457 open -> fixed (no new issues)
EXPLANATION: A crawl started from the UI now logs in with the one case declared on the project. In my own headed browser, the undeclared crawl reached only /login.html (1 screen). The declared crawl reached dashboard, orders, profile and order-1001 (4 screens), and crawl.json recorded login_case_id. "Log out" was denied by the never-click pattern. Every falsifying edit turned its named test red on the assertion it names, and the test went green again when the edit was restored.
```

## Verify commands I re-ran myself (in the bound tree)

| Command | Result |
|---|---|
| `uv run pytest tests/test_ui_crawl_login.py -o addopts= -q -rs` | `10 passed` in 31.57s; `-rs` listed no skips |
| `uv run pytest tests/test_ui_crawl_login.py tests/test_ui_crawls.py -o addopts= -q` | `30 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -p no:cacheprovider -o addopts= -q -rx` (run once, in the background) | `1346 passed, 2 skipped, 32 xfailed`, exit=0 |

The full suite ran on a tree that also held another session's uncommitted `src/autotester/doctor.py` and `tests/test_doctor.py` edits. They are not part of this unit, which is why the count is 1346 and not the manifest's 1344.

## Capability coverage: reproduced in a copy outside the tree

**How the copy was built**
- `git archive HEAD` was extracted into `scratchpad/checker2-at457/`.
- `projects/erp`, `projects/pathlynks` and `projects/vidysea-erp` were deleted right after extraction. Only `projects/regression-demo` remained.
- I copied in the 7 unit files, `docs/MAP.md` and `tests/fixtures/login_site/`, then compared them with `cmp` / `diff -r`: all identical.
- I ran `uv sync` in the copy. `routes_crawl_login`, `cli_crawl`, `routes_crawls` and `schema.project` all have `__file__` inside the copy.

**How each row was run**
- The anchor had to match exactly once.
- Named test green → edit applied → named test red → file restored → named test green.
- The restore ran in a `finally` block.

| # | Edit | Before | After (assertion that fired) | Restored |
|---|---|---|---|---|
| 1 | `routes_crawls.py` `bounds=bounds, login_case=case, crawl_id=crawl_id)` → without `login_case=case` (the mutation X17 names) | 2 passed | 2 failed. Real-browser test: `assert None == 'case_…'` on `crawl.login_case_id`. Hand-over test: `KeyError: 'login_case'` | 2 passed |
| 2 | `if project.login_case_id and case is None:` → `if False:` | 1 passed | `assert 404 == 400` | 1 passed |
| 3 | notice `No login case declared.` → `Crawl settings.` | 1 passed | `assert 'No login case declared' in …` | 1 passed |
| 4 | delete the `store.save_project(...)` line in `declare_login_case` | 2 passed | `None == 'case_b9e…'` and `'case_b9e…' is None` | 2 passed |
| 5 | `if chosen is not None and store.get_case(chosen) is None:` → `if False:` | 1 passed | `assert 200 == 400` | 1 passed |
| 6 | `{escape(declared.title)}` → `{declared.title}` | 1 passed | `'<img src=x …>' not in …` | 1 passed |
| 7 | `case_id = login_case or proj.login_case_id` → `case_id = login_case` | 1 passed | `assert (None is not None)` | 1 passed |
| 8 | → `case_id = proj.login_case_id or login_case` | 1 passed | `the flag wins for one run` | 1 passed |

**Row 1 depends on the fixture's guard.** Pytest stops at the first failed assert, so the red I saw was on `login_case_id`. Could the template assertions pass even without a login? No: Mode D ran an undeclared crawl on the same fixture, and it mapped only `/login.html`. `/app/dashboard.html` would therefore also fail. This is also X18's (AT-458) shape: `completed`, 1 screen, 2 actions and 1 denied submit.

## Probes beyond the manifest

- **Signed-out crawl sees nothing behind the guard.** Without a declared case, the only screen mapped was `/login.html`. The crawler clicked the Username and Password fields, which is a click and not typing, and "Sign in" was `denied_policy: form submit under read_only`. The real-browser test is therefore not vacuous.
- **Old `project.json` still loads.** `projects/regression-demo/project.json` has no `login_case_id` key. It loads with `login_case_id=None`, and `extra="forbid"` still rejects an unknown key.
- **CLI path.**
  - `_resolve_crawl_target(slug, None)` with nothing declared → `None`.
  - Declared id deleted → `no case 'case_gone'` and `Exit 1`. The CLI never falls back to a signed-out crawl.
  - The test covers "declared is the default" and "the flag overrides it without re-declaring".
- **Nothing is widened (X17c).**
  - `git diff HEAD` shows no change under `src/autotester/stages/`, `browser/`, `schema/approval.py` or `schema/crawl.py`.
  - `require_consent` still runs before `BrowserSession`. The new 400 for a missing case comes before consent and opens no browser, so the test's `launched == []` holds.
  - `grep 'fill\|select_option\|upload' src/autotester/stages/explore*.py` returns nothing (X10).
  - The only `run_crawl` call sites are `cli_crawl.py:90` and `routes_crawls.py:234`.
  - In the live run, "Log out" was refused by `never-click pattern (logout/sign-out)` (X6), and a submit was denied under read_only (X5).
- **Escaping (U5).** The declared title and the option values and titles are passed through `escape`. An unknown id gets a 400, the id is not echoed back, and nothing is saved.
- **C2.** File sizes: `routes_crawls.py` 261 lines, `routes_crawl_login.py` 78, the test file 232. Doctor is clean.

## Mode D: my own live browser

Instrument: headed Playwright Python (Chromium, `headless=False`), driven from the copy's venv. The crawler's own browser was headless.

**Setup**
- Servers ran from the copy only:
  - `python -m http.server 8764 --bind 127.0.0.1` serving `tests/fixtures/login_site`;
  - `uvicorn autotester.ui.app:app` on `127.0.0.1:8063`.
- `AUTOTESTER_ROOT` was a fresh scratchpad root.
- Seeded through `ProjectStore`:
  - a synthetic project `loginwall` with base_url `http://127.0.0.1:8764/app/dashboard.html` and allowed_domains `127.0.0.1`;
  - the login case "Sign in as tester" (`case_7fb484d25724`);
  - a CRAWL approval.
- Nothing was declared at seed time.

**Steps, all asserted**
1. `/projects/loginwall/crawls` shows "No login case declared" (01).
2. **Explore now**, undeclared, with bounds 10/60/120/4: `login_case_id=null`, 1 screen `/login.html`, status `completed`, `frontier empty` (02).
3. Picked "Sign in as tester" in the form and clicked **Save login for crawls**. `project.json` now holds `login_case_id=case_7fb484d25724`, the card reads "✓ LOGS IN FIRST Crawls log in with Sign in as tester", and the notice is gone (03).
4. **Explore again**: `crawl.json login_case_id=case_7fb484d25724`, 4 screens, 6 actions and 1 denied.
   - Templates: `/app/dashboard.html`, `/app/orders.html`, `/app/profile.html`, `/app/order-1001.html`.
   - Neither `/login.html` nor `/logout.html` appears.
   - The "Log out" edge is `denied_policy`, `never-click pattern (logout/sign-out)`.
   - The crawl page names all 4 templates (04).
5. Selected "No login — the product is public" and saved. `login_case_id=null` and the notice is back (05).

**Console errors:** 0 across every UI page visited.

**Instrument note:** my first run stopped at step 3. I had written a case-sensitive `"Logs in first"` check, and the pill is rendered uppercase by CSS. That was my own script's mistake, not a product defect. I fixed it and re-ran the whole script from a fresh root, and the report is from that second run.

Both servers were terminated in `finally`, and a later `netstat` showed nothing listening on 8764 or 8063. The browser was closed.

## Questions, not failures

- Once a case is declared, the CLI has no way to run a single signed-out crawl without clearing the declaration. X17 does not require one.
- Any case can be declared as the login case, so a human could choose a case that does more than log in. The CLI's `--login-case` already allowed that, so this unit opens no new door.
