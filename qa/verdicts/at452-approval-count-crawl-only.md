# Verdict — at452-approval-count-crawl-only

**Date:** 2026-09-16
**Cycle checked:** 1
**Checker:** /checker Mode A (fresh subagent), bound to `D:\autoTesting`
**Contracts:** `qa/contracts/ui.md` (U11), `qa/contracts/consent.md` (CN3, CN5), `qa/contracts/core-invariants.md` (C7, C10)

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 3/3 invariants hold
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 2/2 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at452-approval-count-crawl-only-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-455 (new, low); AT-452 open -> fixed
EXPLANATION: The crawl-approval card now counts only CRAWL-kind grants, so intact same-target READ, ADVERSARIAL and LIVE_CASE grants are neither listed nor counted. Both falsifying edits turned the named tests red for the named assertion in a throwaway copy that was green first, and my own headed browser showed the exact numbers with 0 console errors. One case is still wrong: an intact, unexpired, same-target CRAWL grant whose `project` names another project is still counted under a reason that is false for it. It is the same defect class, it predates this unit, and this unit does not claim it, so it is filed as AT-455 and does not fail the unit.
```

## What I re-ran (bound tree, read-only)

| Command | Result |
|---|---|
| `uv run pytest -p no:cacheprovider tests/test_ui_crawl_approval_list.py -o addopts= -q` | `10 passed` |
| `uv run pytest -p no:cacheprovider tests/test_ui_crawl_approval_list.py tests/test_ui_crawls.py tests/test_consent.py -o addopts= -q` | `52 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -p no:cacheprovider -o addopts= -q -rx` (once, background) | `1329 passed, 2 skipped, 32 xfailed, 1 warning in 454.74s`, exit=0. All 32 XFAILs are `test_browser_scroll_invariance.py` (AT-416/417, pre-existing). |

`git diff HEAD -- src tests` touches only the two files the manifest names (+4/-1 and +17).

## Capability coverage (throwaway copy)

- **Copy setup:** I ran `git archive HEAD` into `scratchpad/checker-at452/` and deleted `projects/erp`, `projects/pathlynks` and `projects/vidysea-erp` right away (only `regression-demo` remains). Then I copied in the 2 unit files and ran `uv sync`. `autotester.ui.routes_credentials.__file__` resolves inside the copy.
- **Harness (C7):** it asserts the baseline is green (exit 0), that each anchor matches exactly once, and that the file changed. It restores the file after each edit, attributes each failure by test name, and asserts green again at the end.

| Row | Named check green before the edit | Edit | After the edit | Assertion that fired |
|---|---|---|---|---|
| Another kind of grant is not counted | `10 passed` | `others = len(crawl) - len(active)` -> `len(approvals) - len(active)` | `3 failed, 7 passed` (read/adversarial/live_case params only) | `test_ui_crawl_approval_list.py:136 assert 'more on file' not in ...` |
| Unhonoured crawl grants are still counted | `10 passed` | `crawl = [...]` -> `crawl = list(active)` | `1 failed, 9 passed` (`test_expired_edited_and_other_target_grants_are_not_listed_as_in_force`) | `:119 say they exist, so nobody re-grants blindly` |

After restoring: `10 passed`. The copied file is byte-identical to the bound tree again.

## Mode D (my own live browser)

- **Setup:** headed Playwright Python (Chromium), launched by my own script, not the MCP. The server was uvicorn from the copy on 127.0.0.1:8047 with `AUTOTESTER_ROOT` set to `scratchpad/checker-at452-root`. That root holds only regression-demo's `cases.jsonl` and `project.json`, plus grants I seeded through `ProjectStore.add_approval`. I read no `.env`. The server was stopped and the browser closed afterwards.
- **Seeded mix, all for the exact `base_url` unless noted:**
  - intact READ, ADVERSARIAL and LIVE_CASE grants
  - a READ grant for another target
  - an expired CRAWL grant
  - an edited CRAWL grant (`max_actions` changed, id kept, `is_intact` False)
  - a CRAWL grant for `base_url + "/"`
  - one CRAWL grant in force

| Step | Listed | Note |
|---|---|---|
| seeded-mix | only SignerInForce; none of the READ/ADV/LIVE/other signers | **"3 more on file ..."** (expired + edited + other target) |
| after saving a crawl approval via the UI form | the "Crawl approval saved" banner; SignerInForce and SignerUI listed | **3** (unchanged) |
| PROBE: intact, unexpired CRAWL grant with `project="another-project"` and the same target | not listed (correct) | **4**, under the reason "expired, edited after granting, or for another target", which is false for it -> AT-455 |

Console errors: 0 across all pages.

**Is the wording now true for everything it counts?**
- **Other kinds of run:** true. They are no longer counted.
- **Expired, edited, other-target CRAWL grants:** true.
- **Other-project CRAWL grants (same target, intact):** not true. This is AT-455 (low, pre-existing).
- **Singular/plural nit ("1 more on file are"):** noted by the maker. It is cosmetic and not filed.

## Ledger

- **AT-452:** open -> fixed.
- **AT-455:** appended as a new low issue.
- `qa/issues.jsonl` also carries other sessions' uncommitted hunks, so this checker did **not** commit it. The rows sit in the working tree for that file's owner to commit.
