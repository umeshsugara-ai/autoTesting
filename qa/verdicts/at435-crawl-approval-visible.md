# Verdict — at435-crawl-approval-visible

**Date:** 2026-09-16
**Checker:** /checker Mode A + Mode D (fresh subagent, bound to `D:\autoTesting`; a previous checker stalled without output, so this is a fresh start, not a concurrent check)
**Manifest:** `qa/manifests/at435-crawl-approval-visible.md` (Fix cycle 1)
**Cycle checked: 1**
**Contracts:** `qa/contracts/ui.md` (U5, U11), `qa/contracts/consent.md` (D-018, CN3/CN5), `qa/contracts/core-invariants.md` (C2, C3, C7, C10)

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (U5 escaping, U11 UI crawl approval, CN3/CN5 consistency with the gate, AT-435 fixed), 5/5 invariants hold (C1, C2, C3, C7, C10-at-commit)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 8/8 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at435-crawl-approval-visible-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-452 (low, new); AT-435 open -> fixed
EXPLANATION: The unit does what AT-435 asked. I checked it in my own headed browser: a save shows a confirmation naming the grant, an identical re-save writes nothing and says so, a change to one bound saves a second grant, and grants the gate would refuse are neither listed nor used to drive the banner. All 8 capability rows went red in a throwaway copy, each one on the assertion it is named for. The refusal to write a twin is consistent with D-018 and require_approval (see Design ruling). Filed separately and not charged: the "N more on file" line gives a false reason for an intact grant of another run kind (AT-452).
```

## Step 3 — verify commands, re-run by the checker in the bound tree

| Command | Observed |
|---|---|
| `uv run pytest tests/test_ui_crawl_approval_list.py -o addopts= -q` | `7 passed` |
| 5-file command from the manifest | `78 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` (routes_credentials.py is 234 lines) |
| `uv run pytest -p no:cacheprovider -o addopts= -q -rx` | `1323 passed, 2 skipped, 32 xfailed, 1 warning in 293.45s`, exit=0. All 32 XFAILs are `test_browser_scroll_invariance.py` AT-416/417. The tree also holds another session's uncommitted at438 work, and the suite was still green. |

## Step 4b — capability coverage, reproduced in a throwaway copy

The copy is at `scratchpad/checker2-at435/`. It was built with `git archive HEAD | tar -x`, then the 2 unit files were copied in and `uv sync` was run in the copy. `autotester.ui.routes_credentials.__file__` resolved to `...\scratchpad\checker2-at435\src\autotester\ui\routes_credentials.py`. The harness is `scratchpad/at435_mutate.py` and its output is `scratchpad/at435_mutations.json`. For each row the harness:
1. restored the original file;
2. required the named test to pass on its own (exit 0);
3. required the anchor to match exactly once and the file to change;
4. ran `test_ui_crawl_approval_list.py` + `test_ui_crawls.py` (27 tests) and recorded the failure list and the `E` lines.

After restoring, the 27 tests passed again.

| # | Row | Before | After the edit | Assertion that fired |
|---|---|---|---|---|
| 1 | Unconditional `store.add_approval(candidate)` | 1 passed | 1 failed, 26 passed. Only `test_a_second_identical_submit_saves_nothing_new_and_says_so` failed. | `assert 2 == 1` (rows on disk) |
| 2 | Drop `and bounds(a) == bounds(candidate)` | 1 passed | 1 failed. Only `test_a_grant_that_differs_in_any_bound_is_a_new_grant` failed. | `assert 1 == 2` |
| 3 | Insert `if saved: banner = f'<p>Crawl approval saved {saved}</p>'` | 1 passed | 1 failed. Only `test_the_saved_banner_is_driven_by_disk_not_by_the_query_string` failed. | `'<script>alert(1)</script>' not in ...` |
| 4 | `_in_force`: drop `and approval.is_intact` | 1 passed | 1 failed: the combined test | `assert 'Edited' not in ...`. The row shows `Edited … 9999`, and "Expired" and "Elsewhere" had already passed. |
| 5 | `_in_force`: drop the expiry clause | 1 passed | 1 failed: the combined test | `assert 'Expired' not in ...`. The row shows `Expired … 2000-01-01`. |
| 6 | `_in_force`: drop `approval.target == target` | 1 passed | 1 failed: the combined test | `assert 'Elsewhere' not in ...`. "Expired" passed first, and the row shows `Elsewhere`. |
| 7 | `{escape(a.scope)}` → `{a.scope}` | 1 passed | 1 failed. Only `test_approval_text_is_escaped_when_listed` failed. | `'<img src=x onerror=alert(1)>' not in ...` |
| 8 | Redirect without `?saved=` | 1 passed | 2 failed, 25 passed: the named test plus the existing-grant test | `'Crawl approval saved' in ...` / `'already on file' in ...` |

Rows 4-6 share one test. Each edit failed a different assertion, and that assertion is the one for its own row (the loop checks Expired, then Elsewhere, then Edited, so the earlier assertions passed before the one that fired). No row rode on another row's failure. Every cell was a single-hunk edit to `routes_credentials.py`, the one file in "What changed". There was no injection or re-scoping text in any cell.

## Design ruling (the manifest asked for scrutiny)

**Refusing to append a twin that differs only in `granted_at` is consistent with D-018 / consent.md and `core.consent.require_approval`.**
- The gate filters on `project`, `run_kind` and `target`, then returns the **first** candidate that is intact, unexpired and wide enough. A second row identical in every bound field, including `expires_at`, cannot change what any run is authorised to do. It adds no permission, extends no expiry and removes nothing.
- The match needs **every** field in `_bound_payload()` except `granted_at` to be equal, plus `note`. It also needs the existing grant to be intact and unexpired. So a tampered or lapsed row never absorbs a fresh grant; the fresh one is written. I re-derived that direction live: a one-bound change (max_actions 25 → 26) wrote a second row.
- Consent stays "a file a human writes once": the human's single decision exists on disk exactly once, and the page names the row that carries it. No auto-granting path is created (consent.md out-of-scope). The only information not recorded is a second signing time for an identical decision. No criterion asks for that audit trail.
- **Reusing `RunApproval._bound_payload()` from the UI is acceptable.** C3 (one concept, one place) is the governing criterion. If the UI re-listed the bound fields, the list would drift the next time a bound is added to the schema, and the idempotency check would then silently treat grants that differ in the new bound as twins. That is the worse failure, because it would swallow a real decision. The leading underscore is a naming matter that no criterion covers. Doctor is clean.
- `_in_force` runs the same filters as `require_approval` (same project/kind/exact target, `is_intact`, `is_expired(now UTC)`) and omits only the per-run bounds check, so the page never lists a grant the gate would refuse (CN5 exact target: live, a trailing-slash target was not listed).

## Mode D — own live browser (headed Playwright Python 1.62, Chromium, not the MCP)

Setup: uvicorn ran from the checker's copy on 127.0.0.1:8045. `AUTOTESTER_ROOT` was `scratchpad/at435root`, holding only `projects/regression-demo/{project.json,cases.jsonl}` (synthetic). The server was stopped and the browser closed afterwards. **14/14 steps passed** on the final run.
- Empty state reads "No crawl approval is in force for this target."
- Save → `?saved=appr_259895d139be#crawl-approval`. Banner: **"✓ CRAWL APPROVAL SAVED It is in force and listed below. appr_259895d139be"** (the badge is CSS-uppercased). 1 table row, 1 line on disk.
- Identical re-save → same id `&existing=1`. Banner: **"✓ CRAWL APPROVAL ALREADY ON FILE This approval was already on file — nothing new was saved."** Still 1 row and 1 line on disk.
- max_actions 26 → a new id, 2 rows, 2 lines on disk, "saved" banner, no existing flag.
- Seeded on disk: expired, other-target (trailing slash) and tampered (max_actions → 9999, id kept) grants. None was listed, 2 rows remained, and the page showed "3 more on file are expired, edited after granting, or for another target, and are not honoured."
- `?saved=<expired id>` and `?saved=<tampered id>` → no banner. The same selector found the banner in the positive steps, so these negatives are real.
- Scope `<img src=x onerror="window.__xss=1">` saved through the real form. The raw response contains `&lt;img src=x onerror=`, the raw tag does not appear, there are 0 `<img>` elements in the table, and the handler never ran.
- `?saved=` injections (`<script>`, a real id followed by `"><script>`, and a script with `&existing=1`) → no banner, canary not echoed, script not run.
- An existing id with `existing=1` → "already on file" banner naming that id. Without the flag → the "saved" wording for the same id (harmless: the id must be in force on disk).
- **Console errors: 0 on every one of the 14 page states.**
- Disclosed script defects, not product defects: the first run used a wrong banner selector (`.pill`), and the second compared case-sensitively against the CSS-uppercased badge. Both are fixed; only the third run's report is committed. Screenshots are in the same evidence directory.

## Findings filed, not charged

- **AT-452 (low).** `others = len(approvals) - len(active)` counts every row not listed, including an intact, unexpired `READ`/`ADVERSARIAL` grant for the same target. Live, a seeded READ grant moved the note to "4 more on file are expired, edited after granting, or for another target", which is a false reason for that row. No criterion covers the wording and the page never overstates what is in force, so this is filed and not a failure.

## Step 5 — issues addressed

AT-435 is fixed by this unit (live re-derivation above) and moves `open → fixed`. It is not `verified`: that needs a later re-check.

## Ledger and commit note

`qa/issues.jsonl` holds another session's uncommitted hunks (AT-431, AT-433, AT-446). My AT-435 status edit and the AT-452 row sit in the working tree **uncommitted**, so this commit does not sweep the other session's hunks (C10). Only this verdict and the Mode D `report.json` are committed.
