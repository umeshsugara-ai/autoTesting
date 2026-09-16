# Manifest — at455-other-project-grant-reason

**Unit:** AT-455 — a crawl grant naming another project was counted under a reason that is false for it
**Contract:** `qa/contracts/ui.md` (U11), `qa/contracts/consent.md`; core-invariants C7
**Goal task:** none — issue-driven (filed by the at452 checker, `qa/verdicts/at452-approval-count-crawl-only.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-455 (low)
**Status:** checked-PASS (qa/verdicts/at455-other-project-grant-reason.md, cycle 1, commit 1929e83)

## What was wrong

After AT-452 the Credentials page counts crawl grants that are not in force, under *"N more on file
are expired, edited after granting, or for another target, and are not honoured."* `_in_force` also
requires `approval.project == slug`. So an intact, unexpired, same-target CRAWL grant whose
`project` field names **another project** is rightly not honoured and rightly counted, but none of
the three stated reasons is true of it.

## What changed

- `src/autotester/ui/routes_credentials.py::_approvals_card` — the reason now reads
  "… or for another target **or project**, and are not honoured." A two-line comment cites AT-455.
  The count logic is unchanged.
- `tests/test_ui_crawl_approval_list.py` — one new test. A CRAWL grant for `another-project` is not
  listed, it is counted ("1 more on file"), and the reason names "another target or project".

**Design choice:** I considered excluding other-project grants from the count instead, which is
mutation M2 below. I rejected it. A grant sitting in this project's `approvals.jsonl` but naming
another project is exactly the kind of row a human should be told exists, rather than having it
hidden. That matches the card's own purpose: "say they exist, so nobody re-grants blindly".

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_ui_crawl_approval_list.py -o addopts= -q` | `11 passed` (before the fix: `1 failed, 10 passed` — `'another target or project' in …`) |
| `uv run pytest tests/test_ui_crawl_approval_list.py tests/test_ui_crawls.py tests/test_consent.py -o addopts= -q` | `53 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract. I removed `projects/erp`,
`pathlynks` and `vidysea-erp` right after extraction. `routes_credentials.py` and the test were
copied in, with its own `uv sync`, and `autotester.ui.routes_credentials.__file__` was confirmed
inside the extract. Each anchor matched exactly once, and each edit was restored in a `finally`.
The baseline was `11 passed`, and `11 passed` again after restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `routes_credentials.py`) | Observed |
|---|---|---|---|
| The reason is true of an other-project grant | `test_a_crawl_grant_naming_another_project_is_counted_with_a_true_reason` | `"another target or project, …"` → `"another target, …"` | **1 failed, 10 passed** — `'another target or project' in …` |
| Such a grant is still counted, not hidden | same test (`"1 more on file"`) | `crawl = [...]` adds `and a.project == slug` | **1 failed, 10 passed** — `'1 more on file' in …` (the page showed only "No crawl approval is in force") |

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at455-2026-09-16-maker-smoke/report.json`. The server ran from the extract on a
synthetic root whose approvals were read back as READ (this project), expired CRAWL (this project)
and intact unexpired CRAWL (`another-project`).
- /env → "No crawl approval is in force for this target." + **"2 more on file are expired, edited
  after granting, or for another target or project, and are not honoured."** That counts the expired
  grant and the other-project grant, not the READ grant. 0 console errors.

## Full suite

One clean run, output redirected in full to a fresh file (60 lines), started after sabotage and the
smoke had finished. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its
final line is `1334 passed, 2 skipped, 32 xfailed, 1 warning in 259.16s (0:04:19)`, exit=0. That is
1333 + this unit's 1. All 32 XFAIL lines are `tests/test_browser_scroll_invariance.py` cases whose
reasons name AT-416 / AT-417, which are pre-existing.
