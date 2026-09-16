# Verdict — at432-off-domain-case-step

**Cycle checked:** 1
**Date:** 2026-09-16
**Checker:** independent /checker subagent (fresh context), Mode A + mandatory Mode D
**Bound root:** d:/autoTesting
**Contract:** `qa/contracts/ui.md` (U5, U6, U7, U8) + `qa/contracts/core-invariants.md` (C2, C3, C5, C7)

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (U6 refusal-writes-nothing extended to unreachable navigate steps, U7 composition via check_destination, U8/AT-088 no echo, U5 unchanged), 4/4 invariants hold (C2, C3, C5, C7)
FAILURES: none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at432-off-domain-case-step-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-432 open -> fixed; AT-441 (low, new)
EXPLANATION: Every verify command re-run green in the bound tree, all five falsifying edits reproduced in a throwaway copy with the exact failure sets the manifest claims, and my own browser drove the real /cases/new form and "Add case" button through 10 scenarios with case counts and cases.jsonl checked before and after. Relative targets never worked at run time (execute.py NAVIGATE -> session.goto(step.target) -> check_destination, no URL join), so refusing them agrees with run time and is not a regression. The disclosed gap (generated/expanded/CLI/agent-loop cases are not gated up front) fails safely at run time and is filed as AT-441.
```

## Step 3 — verify commands, re-run by me (bound tree)

- `uv run pytest tests/test_ui_case_navigate_reachability.py tests/test_ui_cases.py tests/test_ui_case_management.py -p no:cacheprovider -o addopts= -q` → `26 passed, 1 warning`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run pytest -q -p no:cacheprovider -rfEx` → `EXIT: 0`, 0 `FAILED`/`ERROR` lines, **33 XFAIL**: 32 in `tests/test_browser_scroll_invariance.py` (AT-416/AT-417) + 1 `tests/test_browser_visual_order.py::...[contents]` (AT-438). None in this unit's files. No other pytest process was running when I started (process list checked).
  - The concurrent session modified `src/autotester/browser/visual_order.js`, `tests/test_browser_visual_order.py` and added a fixture **during** my run; this unit's three changed files were `cmp`-identical before and after, and `tests/test_ui_cases.py` is identical to HEAD (`git diff --quiet HEAD`). The manifest's xfail id was `[ruby]`, mine is `[contents]` — that file is the other session's moving target, not this unit's.
- **Contention attribution (point 5): accepted.** The disclosed `net::ERR_NO_BUFFER_SPACE` was in a file this unit does not touch, did not recur in my independent full run, and the maker declined to cite the mixed capture rather than using it — correct handling.
- `wc -l src/autotester/ui/helpers.py` → **299** (point 7 verified; at the 300 budget, doctor clean; AT-403 already tracks the pressure).

## Judgements on the dispatch's specific questions

1. **Creation agrees with run time — verified by reading.** `browser/session.py:61-71` `check_destination` refuses when `host_of(url)` is empty; `host_of("/login")` parses `///login` → hostname `None` → `""`. `BrowserSession.goto` (`session.py:138-147`) calls `check_destination` then `page.goto(real)` with no join, and `stages/execute.py:27` maps NAVIGATE to `session.goto(step.target)` verbatim. (`urljoin` exists only in explore stages for crawled hrefs, not case steps.) A relative target never ran. No regression.
2. **Rows 2, 3, 4 each break exactly one test — reproduced.** Row 4 is real: with `if host:` the response detail contains the lowercased canary (`assert 'zq9-canary-...2-not-a-host' not in '{"detail":"...`), i.e. a pasted credential genuinely came back.
3. **Placeholder test reaches this unit's code path — proven by message, not only by count.** Probe in the copy: unmutated, declared `{{SECRET:DEMO_LOGIN_URL}}` → 200; under mutation 2 the same request → 400 `"this case could never run: step 1 needs a full URL..."` (this unit's message); an undeclared key → 400 `"this project has not declared a credential called 'NOPE_KEY'..."` in both states. So mutation 2 fails the test for this unit's reason.
4. **Row 5 disclosure: adequate.** It is explicitly labelled broad; the two state tests fail on their `nothing may be saved` assertion (`AssertionError: nothing may be saved`, lines 67/80), and the three extra failures are the route's `_refuse_duplicate` 400 as disclosed. The isolating evidence for "nothing saved" also comes independently from Row 1 plus my live disk counts.
5. See step 3 above.
6. **Scope gap: fails safely, filed.** `execute.py:82` catches the `NavigationRefused` as `Outcome.ERRORED`; no off-domain navigation occurs. Doors not gated up front: `/cases/generate` + `stages/expand.py`, `cli.py:238`, and `stages/agent_loop.py`'s persisted corrections (the last two found by me, not listed in the manifest). Filed **AT-441 (low)** — a UX/dead-on-arrival gap, not a boundary breach.
7. 299 lines, verified.

## Step 4b — capability coverage (throwaway copy outside the bound root)

Copy: `git archive HEAD` + the three changed files layered on (cmp-identical), own `uv sync`; `autotester.ui.helpers.__file__` resolved inside the copy. Harness asserts, per row: baseline exit 0 with no failures **in the copy**, anchor count == 1, file bytes changed, pristine restored afterwards.

| Row | Edit | Before (copy) | After | Failing tests |
|---|---|---|---|---|
| 1 | `routes_cases.py`: call → `pass` | 7 passed | 4 failed, 3 passed | off_domain, offending_step, relative, pasted_credential (all `assert 200 == 400`) |
| 2 | `helpers.py`: drop placeholder skip | 7 passed | 1 failed, 6 passed | secret_placeholder (`assert 400 in (200, 303)`) |
| 3 | `helpers.py`: skip → placeholder only | 7 passed | 1 failed, 6 passed | non_navigate (`assert 400 in (200, 303)`) |
| 4 | `helpers.py`: `if host:` | 7 passed | 1 failed, 6 passed | pasted_credential (canary in response) |
| 5 | `routes_cases.py`: `store.add_case(Case(...))` before the call | 7 passed | 5 failed, 2 passed | off_domain + offending_step (`nothing may be saved`), in_domain, placeholder, non_navigate (duplicate 400) |

All match the manifest. Raw results: `qa/evidence/browser-at432-off-domain-case-step-2026-09-16-checker/mutations.json`.

## Mode D — my own live browser

Own uvicorn on :8022 against the isolated copy (pathlynks/erp/vidysea-erp deleted, no `.env`); maker evidence not read. 10/10 scenarios through the real form and "Add case" button, row counts checked before/after each and cross-checked against `cases.jsonl`:
off-domain refused (0→0), step-2 off-domain refused naming step 2, relative `/login` refused, canary refused and **absent from the response, rendered page, server log and cases.jsonl**, in-domain saved (0→1), subdomain saved, declared placeholder saved **as the placeholder** (resolved value not on disk), click with an off-domain selector saved, and on `regression-demo` (127.0.0.1) off-domain refused 44→44, in-domain saved 44→45.
Console: 5 errors = exactly the 5 deliberate 400s; 0 unexplained. Browser closed, server stopped, scratch copy deleted.

## Invariants

- **C2** doctor clean; new test file 162 lines; helper < 50 lines with docstring. **C3** no duplicate concept — the decision is delegated to `check_destination`, not re-implemented. **C5** credential never echoed (row 4 + live canary). **C7** the unit added tests and pasted a mutation run with asserted anchors/baseline; reproduced independently.

## Ledger

- AT-432: open → fixed (a later re-check moves it to verified).
- AT-441 (low): the non-form doors still store unreachable navigate steps; fail safely at run time.
- Known, not charged: raw-JSON refusal rendering (AT-439); MC-003 `data_class` (AT-365).
