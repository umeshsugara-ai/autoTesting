# Verdict — at455-other-project-grant-reason

**Date:** 2026-09-16
**Checker:** /checker Mode A (fresh subagent), bound to `D:\autoTesting`
**Manifest:** `qa/manifests/at455-other-project-grant-reason.md`
**Cycle checked: 1**

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (U11 note truthful · consent exact project matching unchanged · C7 sabotage asserted), 3/3 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 2/2 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at455-other-project-grant-reason-2026-09-16-checker/report.json
ISSUES-WRITTEN: none (AT-455 open -> fixed)
EXPLANATION: The note now names every condition `_in_force` checks for a crawl grant (expired, edited, another target, another project), so it is true of every grant it counts; counting other-project grants rather than hiding them is the right call, since consent.md matches `project` exactly and a human should know such a row sits in this project's approvals.jsonl. Both falsifying edits turned the named test red on its own assertion in an isolated copy, and my own headed browser showed exactly one listed row and the exact "2 more on file ... another target or project" note with 0 console errors. My one full-suite run had 1 failure, and it is not this unit's: another session edited `routes_crawls.py` at 22:42 while the suite was running, which tripped the fingerprint check in `test_cli_harness_safety`. That file passes 4/4 in the copy.
```

## What I re-ran (bound tree, working-tree state with the 2 unit files modified)

| Command | Result |
|---|---|
| `uv run pytest tests/test_ui_crawl_approval_list.py -o addopts= -q -p no:cacheprovider` | `11 passed` |
| `uv run pytest tests/test_ui_crawl_approval_list.py tests/test_ui_crawls.py tests/test_consent.py -o addopts= -q -p no:cacheprovider` | `53 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -p no:cacheprovider -o addopts= -q -rx` (once, sequential, backgrounded to a file) | `1 failed, 1333 passed, 2 skipped, 32 xfailed` in 271s. The single failure is `tests/test_cli_harness_safety.py::test_running_every_command_leaves_the_repository_untouched`: "running the CLI surface rewrote ['src\\autotester\\ui\\routes_crawls.py']". That file is not in this unit. It was not modified at session start, and its mtime of 22:42:24 falls inside the suite run, so a concurrent session edited it. The same test file gives `4 passed` in my isolated copy. The manifest claims 1334 passed. My figure is 1333 passed plus 1 failure from the concurrent edit, which is consistent with that claim. |

## Design judgement

`_in_force` (routes_credentials.py:57-61) requires `project == slug`, `run_kind is CRAWL`,
`target == target`, `is_intact` and `not is_expired`. The count is now filtered to CRAWL only
(AT-452), so an uncounted-but-crawl grant fails one of: project, target, intact ("edited after
granting"), or expiry. `is_expired` also returns True for an unparseable expiry, and "expired" is
a fair reading of that. The new wording covers all four failure modes, so it is true of every
grant it counts. Hiding other-project grants would be mutation M2. That goes against the card's
purpose ("say they exist, so nobody re-grants blindly"). consent.md:71 (exact project matching)
and :127 (no multi-project approvals) confirm that such a grant is never honoured, so the reason
is accurate.

## Capability coverage (throwaway copy)

The copy was made with `git archive HEAD` into
`scratchpad/checker-at455/`. I deleted `projects/erp`, `projects/pathlynks` and
`projects/vidysea-erp` right after extraction; only `regression-demo/` remained. I copied in the
2 unit files and ran `uv sync`. `autotester.ui.routes_credentials.__file__` resolved to
`...\scratchpad\checker-at455\src\autotester\ui\routes_credentials.py`. For each edit, the anchor
count was asserted to be 1 and the file was confirmed changed. Each edit was restored in a
`finally` block, and I confirmed the file afterwards was byte-identical to the original.

| Row | Before (copy) | After edit | Assertion fired |
|---|---|---|---|
| M1 `"another target or project, and are not honoured.` → `"another target, and are not honoured.` | 11 passed | 1 failed, 10 passed | `assert 'another target or project' in ...` in `test_a_crawl_grant_naming_another_project_is_counted_with_a_true_reason` (page: "1 more on file are expired, edited after granting, or for another target, and are not honoured.") |
| M2 `crawl = [...]` adds `and a.project == slug` | 11 passed | 1 failed, 10 passed | `assert '1 more on file' in ...` in the same test (page: "No crawl approval is in force for this target." with no note) |

Restored: 11 passed.

Traps: the test asserts the rendered note text and count against a seeded on-disk grant. The
buggy state renders different text, so the check does not read live state to judge live state,
and no fallback produces the same end state.

## Mode D (my own live browser)

- Instrument: headed Playwright Python (Chromium) running my own script. It is not the maker's script.
- Server: uvicorn `autotester.ui.app` from the copy on port 8049. Its `AUTOTESTER_ROOT` was a
  scratchpad root holding only regression-demo's `cases.jsonl` and `project.json`. All four grants
  were seeded through `ProjectStore.add_approval`:
  - CRAWL for `project=another-project` (intact, unexpired, exact target)
  - CRAWL that expired in 2020
  - READ grant
  - CRAWL in force
- Step 1, /projects/regression-demo/env: the only listed row was `InForceCrawl`. The note read
  exactly "2 more on file are expired, edited after granting, or for another target or project,
  and are not honoured." None of OtherProjectCrawl, ExpiredCrawl or ReadGrant appeared. Console
  errors: 0.
- Step 2 (interaction): I saved a new crawl grant through the form. The banner said "Crawl
  approval saved". The listed rows became InForceCrawl and CheckerSaved. The note was still
  exactly "2 more on file ...", so the new in-force grant was not counted. Console errors: 0.
- Instrument note: in run 1, the step 2 banner assertion read `inner_text`, which applies the
  pill's CSS text-transform, so it wrongly reported the banner as missing. The rows and note were
  identical to run 2. I reseeded and ran again using `text_content`, and run 2 is the recorded
  report (result PASS).
- Server stopped and browser closed.

## Ledger

AT-455 is now `open → fixed` (fixed_date 2026-09-16). I did not commit `qa/issues.jsonl`: it also
holds other sessions' uncommitted hunks, and committing it would sweep them in. Whoever commits
next should include the AT-455 line change.
