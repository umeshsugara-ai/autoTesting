# Manifest — at452-approval-count-crawl-only

**Unit:** AT-452 — the Credentials page counted a grant for another kind of run under a reason that is false for it
**Contract:** `qa/contracts/ui.md` (U11), `qa/contracts/consent.md`; core-invariants C7
**Goal task:** none — issue-driven (filed by the at435 checker, `qa/verdicts/at435-crawl-approval-visible.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-452 (low)
**Status:** checked-PASS (qa/verdicts/at452-approval-count-crawl-only.md, cycle 1, commit ff02b73)

## What was wrong

`_approvals_card` lists **crawl** grants that are in force, then says *"N more on file are expired,
edited after granting, or for another target, and are not honoured."* It computed
`N = len(approvals) - len(active)`, so an intact, unexpired, same-target **READ / ADVERSARIAL /
LIVE_CASE** grant was counted too. Every clause of that reason is false about such a grant. It is
not unhonoured either; it is simply a different gate.

## What changed

- `src/autotester/ui/routes_credentials.py::_approvals_card` — the count is now taken over crawl grants
  only (`crawl = [a for a in approvals if a.run_kind is ApprovalKind.CRAWL]`,
  `others = len(crawl) - len(active)`), with a two-line comment citing AT-452. It is 3 lines of
  logic; the file is 237 lines.
- `tests/test_ui_crawl_approval_list.py` — one new test parametrized over READ, ADVERSARIAL and
  LIVE_CASE: an intact, unexpired, same-target grant of that kind is neither listed nor counted.
  The file is 157 lines.

**Not changed:** other kinds of grant are not shown anywhere on this page, before or after. The card
is about crawl approvals. "1 more on file are" is a singular/plural wording nit I noticed and did
not fix or file.

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_ui_crawl_approval_list.py -o addopts= -q` | `10 passed` (before the fix: `3 failed, 7 passed` — exactly the 3 new cases, `'more on file' not in …`) |
| `uv run pytest tests/test_ui_crawl_approval_list.py tests/test_ui_crawls.py tests/test_consent.py -o addopts= -q` | `52 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract. I removed `projects/erp`,
`pathlynks` and `vidysea-erp` right after extraction. `routes_credentials.py` and the test were
copied in, with its own `uv sync`, and `autotester.ui.routes_credentials.__file__` was confirmed
inside the extract. Each anchor matched exactly once. The baseline was `10 passed`, and `10 passed`
again after restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `routes_credentials.py`) | Observed |
|---|---|---|---|
| A grant of another kind is not counted | `test_a_grant_for_another_kind_of_run_is_not_counted_with_a_false_reason[read/adversarial/live_case]` | `others = len(crawl) - len(active)` → `len(approvals) - len(active)` | **3 failed, 7 passed** — exactly the three params, `'more on file' not in …` |
| Unhonoured crawl grants are still counted (the fix did not just silence the line) | `test_expired_edited_and_other_target_grants_are_not_listed_as_in_force` ("3 more on file") | `crawl = [...]` → `crawl = list(active)` | **1 failed, 9 passed** — `say they exist, so nobody re-grants blindly` |

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at452-2026-09-16-maker-smoke/report.json`. The server ran from the extract on a
synthetic root. It holds regression-demo plus two seeded grants for the exact base_url: an intact,
unexpired READ grant and an expired CRAWL grant.
- /env → "No crawl approval is in force for this target." + **"1 more on file …"**, which counts the
  expired crawl grant only. The READ grant's signer is absent. 0 console errors.

## Full suite

One clean run, output redirected in full to a fresh file (60 lines), started after sabotage and the
smoke had finished. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and
its final line is `1329 passed, 2 skipped, 32 xfailed, 1 warning in 312.46s (0:05:12)`, exit=0.
That is 1326 + this unit's 3 parametrized cases. All 32 XFAIL lines are
`tests/test_browser_scroll_invariance.py` cases whose reasons name AT-416 / AT-417, which are
pre-existing. The warning is starlette's anyio deprecation.
