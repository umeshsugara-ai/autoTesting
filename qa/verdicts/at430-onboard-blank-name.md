# Verdict — at430-onboard-blank-name

**Date:** 2026-09-16
**Manifest:** `qa/manifests/at430-onboard-blank-name.md` (Fix cycle: 1)
**Cycle checked: 1**
**Checker:** independent /checker subagent, fresh context, Mode A + mandatory Mode D. Bound to `d:/autoTesting`.
**Contracts:** `qa/contracts/ui.md` (U1, U5, U7, U9, U12) + `qa/contracts/core-invariants.md` (C1–C9)

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (U1, U5, U7, U9, U12), 9/9 invariants hold (C1–C9; C4/C6/C8/C9 untouched by the diff)
FAILURES: none
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at430-onboard-blank-name-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-439 (low, new); AT-430 open -> fixed
EXPLANATION: I tested the fix in my own Chromium against my own server on an isolated root. Blank and whitespace-only names are now refused through the real "Create project" button: nothing is written, no ghost link appears, and the refused slug returns 404. The edit route refuses a whitespace-only name live too, and the stored name stays unchanged. All four capability rows reddened on the assertion each one names, and both reasons the manifest gives for not using a schema validator hold up when tested.
```

## What I re-ran (bound tree, working state)

- `uv run pytest -q` → **EXIT: 0**. The `-qq` output shows 32 `x` and 2 `s`, with no F or E.
- `uv run pytest -o addopts= -q -rx` → **32 XFAIL, all in `tests/test_browser_scroll_invariance.py`**. That file was last touched by `d4fb88c` (AT-425/426) and is clean in git. None of the xfails come from this unit, so the manifest's attribution is correct.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`. Line counts: helpers 270, app 291, routes_project_edit 256, new test 93. All are under 300.

## Step 4b — capability coverage (throwaway copy outside the bound root)

The copy was `git archive HEAD` plus the 4 changed files (cmp-identical) and its own `uv sync`. `autotester.ui.helpers.__file__` resolved **inside the copy**. For every row, the harness asserted a green baseline (`7 passed`), an anchor count of exactly 1, and that the file actually changed. It restored the file afterwards and asserted it was byte-identical.

| Row | Edit | Result | Assertion that fired |
|---|---|---|---|
| 1 onboard refuses | delete the `_require_project_name(name)` call in `app.py` | 5 failed, 2 passed | `assert 200 == 400` ×4 (parametrized) + the ghost-link `'/projects/ghost' not in …` |
| 2 edit still refuses | delete the call in `routes_project_edit.py` | 1 failed (`test_edit_still_refuses_…`) | `assert 200 == 400` |
| 3 whitespace = blank | `name.strip()` → `name` in `helpers.py` | 5 failed | the 3 whitespace cases, ghost-link, edit. The `""` case stays green, as it should |
| 4 save first, then refuse | save `Project(...)` right after the duplicate-slug check, then call the helper | **5 failed, 2 passed** | **`AssertionError: nothing may be saved`** ×4 (line 53, reached only after the 400 and `detail` asserts passed) + ghost-link line 67 |

Row 4 is confirmed load-bearing. The status and detail assertions pass under the mutation, and the tests fail only on the state assertions. My first version of row 4 put the save *before* the duplicate-slug check. That also reddened `test_a_named_project_still_onboards`, because the check then refused the project it had just saved. That test failing was a side effect of my mutation, not a hole in the tests, so I re-ran row 4 with the save placed after the check, and it matches the manifest exactly.

## Judgement 1 — the design choice (verified, not taken on the manifest's word)

In the copy, I added a real `field_validator` on `Project.name` that rejects blank names and removed both helper calls:
- **(a) holds:** onboarding with `name='  '` returned **HTTP 500**. `app.py:229` builds `Project(...)` outside any `try`, and `ui/` has no `exception_handler`.
- **(b) holds, and the real outcome is worse than the manifest says:** Pydantic 2.13 `model_copy(update=...)` skipped the validator, so edit **saved `name=''` to `project.json`**. Then `ProjectStore.load_project()` raised `ValueError … Value error, blank`, so the project could no longer be loaded. A schema validator alone would have turned this defect into a project that cannot be loaded at all. Keeping the rule in a route-level helper is the right call.

## Judgement 4 — raw-JSON refusal (pre-existing; does not block)

It really does predate this unit. The diff adds a check that raises the same `HTTPException` every other onboard refusal already raises, and it changes no rendering. I confirmed it live: a duplicate slug, a refusal path this diff does not touch, renders `{"detail":"a project with this slug already exists"}` with no themed nav, exactly like the new refusal. No U-criterion requires themed refusals on `/onboard`. U10 explicitly declines to claim them, and U11's themed-refusal clause covers the crawl and review-gate routes only. Blocking this unit on it would charge the unit against a criterion nobody wrote. I filed it separately as **AT-439** (low). That issue also records that edit with `name=''` returns FastAPI's own raw 422 from `Form(...)` before the helper runs. That also happened before this unit, and the state stays unchanged.

## Judgement 5 — AT-088 (no echo)

The helper's message is a constant. Live results:
- A blank name together with the sentinel credential value got a 400 whose body does not contain the sentinel, and the sentinel was not written to `.env`.
- A name equal to a `.env` sentinel was refused by the existing U9 guard, and the sentinel was not in the response.
- The server access log contains the sentinel **0** times.

## Mode D summary

The full table is in the report. Onboard was driven through the real form and the real "Create project" button: blank with `required` removed, whitespace with `required` **intact**, tab, blank plus a credential row, and a positive control. Every refused slug returns 404, the sidebar gains no empty link, and only `ck-named` and `regression-demo` exist on disk afterwards.

**New observation that raises the severity of the original bug:** `required` does not stop a whitespace-only name. Before this fix, any user could create the ghost project **with no bypass at all**.

The edit route was driven through the real "Save changes" button, which closes the gap the manifest disclosed. `'   '` returned 400 with the heading, title and sidebar unchanged. The positive control rename worked.

All 8 console errors are my own deliberate 400 and 422 probes. Page code produced 0.

## Ledger

- AT-430 is now `open → fixed`. Only a later re-check moves it to `verified`.
- New: **AT-439** (low, ui): onboard and edit refusals render as raw JSON, replacing the page and losing the values the user typed.

## Not claimed

- Names that are not blank are still stored unstripped on onboard (AT-062 stays open, and this unit does not claim it).
- AT-431 to AT-435 are not covered by this unit.
- MC-003's data-boundary exit 1 (AT-365) is known and not charged to this unit.
