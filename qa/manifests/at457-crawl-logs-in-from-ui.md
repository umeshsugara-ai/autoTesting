# Manifest — at457-crawl-logs-in-from-ui

**Unit:** AT-457 / X17. A crawl started from the product UI logs in with the project's declared login case and maps the screens behind it.
**Contract:** `qa/contracts/explore.md` **X17** (added by sweep b7dfa46, folding Umesh's 2026-09-16 22:25 feedback); X5, X6 and X10 are unchanged; `qa/contracts/ui.md`; core-invariants C1, C2, C3, C7
**Goal task:** none. Priority change by Umesh, verbatim in `qa/feedback-inbox.md` (FOLDED); `qa/QUEUE.md` TOP-1
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-457 (high)
**Status:** checked-PASS (qa/verdicts/at457-crawl-logs-in-from-ui.md, cycle 1, commit 4472a0d; the first checker was killed by an API rate limit and re-dispatched)

## What was wrong

> "abhi tho hmara testing flow login k baad hi ruk jata hi … puura product map hona chiaye na aend to end testing . each possible route" (Umesh)

Every crawl on disk stopped at or before the login page:
- saucedemo and both checkerdemo crawls: 1 screen and 0 actions;
- pathlynks: `login_failed` with 0 screens.

`POST /projects/{slug}/explore` called `run_crawl` with no `login_case`, and `Project` had no field to
name one. No crawl started from the UI could reach a single post-login screen. The explorer already
logs in correctly when handed a case (`stages.explore._bootstrap_login`, X10); nothing handed it one.

## What changed

**(a) One declared source.**
- `src/autotester/schema/project.py`: new optional `Project.login_case_id: str | None = None`. It is
  backward-compatible because existing `project.json` files load unchanged, and `extra="forbid"` is
  kept. `docs/MAP.md` was regenerated with `autotester map`.
- `src/autotester/ui/routes_crawl_login.py` (new, 78 lines, one job: declaring the crawl login):
  - `login_card(slug, project, cases)` shows one of three states: the declared case (escaped title);
    a declared id that no longer exists; or **"No login case declared. A crawl will only see pages a
    signed-out visitor can open …"**. It also carries a select-and-save form.
  - `POST /projects/{slug}/login-case` declares the case, or clears it when the value is empty. An id
    that is not one of the project's cases gets a themed 400 that does not echo the id, and nothing is
    saved.
  - It is a separate module because an HTML form cannot sit inside the Explore form, and
    `routes_crawls.py` would otherwise pass the 300-line cap.
- `src/autotester/ui/app.py`: registers the router.
- `src/autotester/cli_crawl.py::_resolve_crawl_target`: `case_id = login_case or proj.login_case_id`.
  The declaration is the default and `--login-case` overrides it **for one run** without re-declaring.
  This follows X17(a): "may override it for one run; it may not be a second, drifting default".

**(b) The UI uses it.**
- `src/autotester/ui/routes_crawls.py` (261 lines):
  - The crawls page renders `login_card` above the Explore form, in both the empty and populated
    states.
  - `start_crawl` resolves `project.login_case_id` and passes the `Case` as `run_crawl(..., login_case=case, ...)`.
  - A declared id whose case no longer exists gets a themed **400 "Login case not found"**, before
    consent, before `BrowserSession` and before `run_crawl`. It never crawls signed out.
  - The form has no per-crawl login field, so there is exactly one source.

**(c) Nothing else widens.** Consent, `write_policy`, X6 and X10 are untouched. In the smoke run the
crawler still refused "Log out".

**Fixture.** `tests/fixtures/login_site/` is a local product where every `/app/` page runs `guard.js`,
which redirects to `/login.html` unless `localStorage.auth` is set:
- `login.html` sets it only for `tester` / `fixture-pass`;
- `app/dashboard.html` links to orders, profile and **Log out**;
- `app/orders.html` links to `app/order-1001.html`;
- `logout.html` clears the session.

**Tests.** `tests/test_ui_crawl_login.py` (new, 10 tests) replaces the per-crawl dropdown this unit
first built. That version never reached a checker; it was reshaped when X17 required a declaration.
The last test is X17's load-bearing verify. It uses a **real headless Chromium** on the fixture and
a crawl POSTed **through the UI route**. It must record `login_case_id`, reach `/app/dashboard.html`,
`/app/orders.html` and `/app/profile.html`, and never visit `/logout.html`. Chromium availability is
probed **before** the crawl. My first draft skipped on any 500, which would have hidden a real crash,
so I removed that.

**Stub caught by the full suite, not by my targeted runs.** `tests/test_coverage_wiring.py::_crawl_reaching`
fakes `run_crawl`, and its signature did not accept `login_case`, which the real `run_crawl` has
always taken. After this unit the UI route passes that keyword, so full-suite run 1 failed 2 tests
with `TypeError: fake_run_crawl() got an unexpected keyword argument 'login_case'`. I added
`login_case=None` to the stub so it mirrors the real signature. That is a 3-line change. No other
`run_crawl` stub in `tests/` uses a fixed signature; the other two take `**kwargs`.

**Not in this unit:**
- X18: a crawl stuck at the login page still reads COMPLETED when it performed an action (AT-458).
- V7: coverage number and unreached-with-reason (AT-459).
- Forms after login under read_only, which is a D-016 human decision.
- The live external target, gated by `qa/gates/live-crawl-target.md`.

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_ui_crawl_login.py -o addopts= -q -rs` | `10 passed`, **no skips**, about 26 s because one real browser crawl runs |
| `uv run pytest tests/test_ui_crawl_login.py tests/test_ui_crawls.py -o addopts= -q` | `30 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` (MAP.md regenerated) |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract (`scratchpad/x17x`). I removed
`projects/erp`, `pathlynks` and `vidysea-erp` right after extraction. The unit's 7 files and
`tests/fixtures/login_site/` were copied in, with its own `uv sync`, and
`autotester.ui.routes_crawl_login.__file__` and `autotester.cli_crawl.__file__` were confirmed inside
the extract. Each anchor matched exactly once, and each edit was restored in a `finally`. The
baseline was `30 passed` (`test_ui_crawl_login.py` + `test_ui_crawls.py`), and `30 passed` again after
restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, single file) | Observed |
|---|---|---|---|
| **X17 verify:** a UI-started crawl logs in and maps screens behind the login | `test_a_ui_started_crawl_maps_screens_behind_the_login_in_a_real_browser` (+ `test_the_declared_case_reaches_the_crawl`) | `routes_crawls.py`: `bounds=bounds, login_case=case, crawl_id=crawl_id)` → `bounds=bounds, crawl_id=crawl_id)` (X17's named mutation) | **3 failed, 27 passed** — the real-browser test `assert None == 'case_1cabbbe4d48f'` (crawl.json has no login_case_id), plus `KeyError: 'login_case'` in both hand-over tests |
| A vanished declared case is refused before a browser opens | `test_a_declared_case_that_no_longer_exists_is_refused_before_a_browser_opens` | `routes_crawls.py`: `if project.login_case_id and case is None:` → `if False:` | **1 failed** — `assert 404 == 400` |
| With nothing declared, the page says so before a crawl | `test_with_nothing_declared_the_crawl_page_says_so_before_a_crawl` | `routes_crawl_login.py`: notice `No login case declared.` → `Crawl settings.` | **1 failed** — `'No login case declared' in …` |
| Declaring saves on the project, and empty clears it | `test_declaring_a_login_case_saves_it_on_the_project` + `test_an_empty_choice_clears_the_declaration` | `routes_crawl_login.py`: delete the `store.save_project(...)` line | **2 failed** — `None == 'case_b9e…'`, `'case_b9e…' is None` |
| An unknown case is not declared | `test_an_unknown_case_is_not_declared_and_not_echoed` | `routes_crawl_login.py`: `if chosen is not None and store.get_case(chosen) is None:` → `if False:` | **1 failed** — `assert 200 == 400` |
| The declared title is escaped | `test_the_declared_case_is_named_on_the_crawl_page_escaped` | `routes_crawl_login.py`: `{escape(declared.title)}` → `{declared.title}` | **1 failed** — `'<img src=x …>' not in …` |
| The CLI defaults to the declared case | `test_the_cli_uses_the_declared_case_and_the_flag_overrides_it` | `cli_crawl.py`: `case_id = login_case or proj.login_case_id` → `case_id = login_case` | **1 failed** — `assert (None is not None)` |
| …and `--login-case` overrides it for one run | same test | `cli_crawl.py`: → `case_id = proj.login_case_id or login_case` | **1 failed** — `the flag wins for one run` |

**Honest notes:**
- **Row 1's real-browser test:** its first failing assertion is `login_case_id`, not the template set,
  because pytest stops at the first failing assert. Separately, the smoke below shows the declared
  crawl mapping 4 post-login screens. With no login the fixture redirects every `/app/` page to
  `/login.html`, so the template assertions would fail too.
- **Not asserted by any new mutation:** the refusal of `/logout.html` is the existing X6 guard. It
  appears in the real-browser test as a regression check, and this unit does not claim it.

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at457-2026-09-16-maker-smoke/report.json`. **LOCAL target only**:
`tests/fixtures/login_site` was served on `127.0.0.1:8762`. The server ran from the extract on a
synthetic root with project `loginwall`, a case and an approval, and **no login declared at seed time**.
1. /crawls showed **"No login case declared …"** before any crawl.
2. I selected "Sign in as tester" and clicked **Save login for crawls**. The card now reads
   **"✓ Logs in first · Crawls log in with Sign in as tester"**.
3. I set bounds 10 / 60 / 120 and clicked **Explore now**. `crawl.json` has
   `login_case_id=case_628223274750` and **4 screens, all behind the login**: `/app/dashboard.html`
   (depth 0), `/app/orders.html` and `/app/profile.html` (depth 1), and `/app/order-1001.html`
   (depth 2). `/login.html` is not a node. **"Log out" was refused**
   (`never-click pattern (logout/sign-out)`). The crawl page lists all 4 with how each was reached.
   0 console errors on the UI pages.

**For comparison:** before this unit, the best crawl on disk reached 1 screen.

## Full suite

**Two runs, both disclosed.** The command for each was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`,
with output redirected in full to a fresh file.
1. **RED:** `2 failed, 1342 passed, 2 skipped, 32 xfailed`, exit=1. Both failures are in
   `tests/test_coverage_wiring.py`, with `TypeError: _crawl_reaching.<locals>.fake_run_crawl() got an unexpected
   keyword argument 'login_case'`. This was caused by this unit; the stub fix is described in "What changed".
2. **GREEN** after the stub fix: `1344 passed, 2 skipped, 32 xfailed, 1 warning in 263.53s (0:04:23)`,
   exit=0. That is 1334 + this unit's 10. All 32 XFAIL lines are `tests/test_browser_scroll_invariance.py`
   cases whose reasons name AT-416 / AT-417, which are pre-existing.

**Files in this unit:**
- `src/autotester/schema/project.py`
- `src/autotester/ui/routes_crawl_login.py` (new)
- `src/autotester/ui/routes_crawls.py`
- `src/autotester/ui/app.py`
- `src/autotester/cli_crawl.py`
- `docs/MAP.md` (generated)
- `tests/test_ui_crawl_login.py` (new)
- `tests/test_coverage_wiring.py` (stub signature)
- `tests/fixtures/login_site/` (new)
