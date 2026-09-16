# Manifest — at435-crawl-approval-visible

**Unit:** AT-435 — saving a crawl approval gave no confirmation, listed nothing, and a second click saved a duplicate grant
**Contract:** `qa/contracts/ui.md`, `qa/contracts/consent.md` (D-018); core-invariants C2, C3, C7
**Goal task:** none — issue-driven (found by the independent live-browser validation, `qa/verdicts/live-2026-09-16-ui.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-435 (low)
**Status:** checked-PASS (qa/verdicts/at435-crawl-approval-visible.md, cycle 1, commit 6eb36db; first dispatched checker stalled with no verdict and was re-dispatched)

## What was wrong

"Save crawl approval" on `/projects/<slug>/env` returned 303 to `/env#crawl-approval`, and that page
was identical to the one before saving: no message and no list of grants. The live checker clicked
twice and `approvals.jsonl` gained two rows (`appr_cb56131280f5`, `appr_6795c4e50735`). D-018 treats
consent as a file a human writes once. A page that hides the file makes it impossible to do that
on purpose.

## What changed (`src/autotester/ui/routes_credentials.py` only, 234 lines)

- **`_in_force(approval, slug, target)`** decides which grants are listed. A grant is listed only if
  it has the same project, is a `CRAWL`, has the exact target, is `is_intact` and is not expired.
  These are the conditions `core.consent.require_approval` checks before it will honour a grant, so
  the page never reassures anyone about a grant the gate would refuse. (The gate also checks the
  bounds against the run, which the page cannot know.)
- **`_approvals_card(...)`** renders an "Approvals in force" card: a table with signer, scope,
  max actions, wall clock, expiry (UTC) and id, every text field `escape`d. Grants on file that are
  not in force get one line: *"N more on file are expired, edited after granting, or for another
  target, and are not honoured."* That line is there so nobody re-grants without knowing they exist.
- **Confirmation banner.** It is driven by `?saved=<id>` but looked up **on disk**: it appears only
  when that id belongs to a grant in force. The query string is never echoed.
  `&existing=1` changes the wording to "already on file — nothing new was saved".
- **`_matching_grant(approvals, candidate)`** implements idempotency. If an intact, unexpired grant
  matches the new one in every bound field except `granted_at` (it reuses
  `RunApproval._bound_payload()`, the schema's own definition of the bounds, plus `note`), nothing
  is appended and the redirect names the existing grant. A grant that differs in **any** bound is a
  new decision and is saved.
- `env_editor_view` takes `saved`/`existing` query params and renders the card after the form.
- `tests/test_ui_crawl_approval_list.py` (new, 7 tests). It is a separate file because
  `test_ui_crawls.py` is at 300 lines; that file proves a grant is saved correctly, this one proves
  the human can see it.

**Design judgement to scrutinise:** refusing to write a twin is a behaviour change to a consent
artifact. I judged it safe for two reasons. The consent gate honours any covering grant, so a twin
adds no permission. And the twin differs only in `granted_at`, which is not a decision. If the
checker disagrees, the alternative is to keep appending and only show the confirmation.

**Known limit:** `_bound_payload` has a leading underscore and is called from the UI module. I
chose that over re-listing the bound fields a second time (C3, one concept in one place).

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_ui_crawl_approval_list.py -o addopts= -q` | `7 passed` (at HEAD before the fix: `5 failed, 2 passed`, observed; the 2 were the acceptance test and the no-echo test, both shown able to fail by M7 and M2) |
| `uv run pytest tests/test_ui_crawl_approval_list.py tests/test_ui_crawls.py tests/test_consent.py tests/test_ui_credential_safety.py tests/test_ui_credential_safety_project.py -o addopts= -q` | `78 passed` (maker: observed) |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract with the 2 unit files copied in
and its own `uv sync`. `autotester.ui.routes_credentials.__file__` was confirmed inside the extract.
Each anchor matched exactly once. The baseline was `27 passed` (`test_ui_crawl_approval_list.py` +
`test_ui_crawls.py`) before the edits and again after restoring. All edits are to
`routes_credentials.py`.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| A repeated identical submit writes no twin | `test_a_second_identical_submit_saves_nothing_new_and_says_so` | `if already is None: store.add_approval(candidate)` → unconditional `store.add_approval(candidate)` | **1 failed, 26 passed** — exactly that test |
| A grant differing in any bound is still saved | `test_a_grant_that_differs_in_any_bound_is_a_new_grant` | `_matching_grant`: drop `and bounds(a) == bounds(candidate)` | **1 failed** — exactly that test |
| The banner comes from disk, never the query string | `test_the_saved_banner_is_driven_by_disk_not_by_the_query_string` | insert `if saved: banner = f'<p>Crawl approval saved {saved}</p>'` | **1 failed** — exactly that test |
| Edited grants are not listed as in force | `test_expired_edited_and_other_target_grants_are_not_listed_as_in_force` | `_in_force`: drop `and approval.is_intact` | **1 failed** — that test |
| Expired grants are not listed | same test | `_in_force`: drop `not approval.is_expired(...)` | **1 failed** — that test |
| Other-target grants are not listed | same test | `_in_force`: drop `approval.target == target` | **1 failed** — that test |
| Listed approval text is escaped | `test_approval_text_is_escaped_when_listed` | `{escape(a.scope)}` → `{a.scope}` | **1 failed** — exactly that test |
| Saving shows a confirmation naming the grant | `test_saving_shows_a_confirmation_naming_the_saved_grant` (+ the existing-grant test) | redirect → `/env#crawl-approval` without `?saved=` | **2 failed, 25 passed** |

**Honest note on rows 4-6:** all three are guarded by one combined test, so each edit reddens the
same node. The assertion differs per edit (`"Edited"`, `"Expired"` or `"Elsewhere"` found in the
text), but I did not paste the per-edit assertion lines, so the checker should confirm which one
fired.

After sabotage and the smoke, the banner body for a new save changed from "Crawl approval saved."
(which repeated the pill) to "It is in force and listed below.". No mutation anchor touches that
line. The tests were re-run afterwards: 27 passed, ruff clean, doctor clean.

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at435-2026-09-16-maker-smoke/report.json`: server from the extract, synthetic-only root.
- Empty state: "No crawl approval is in force for this target."
- Save (signer, scope, 2099-12-31T10:00, max 25) → `?saved=appr_d08cc4897b50`, banner, one row with
  the expiry correctly converted to UTC (the IST offset was auto-detected).
- Identical second save → `?saved=appr_d08cc4897b50&existing=1`, "already on file", still one row;
  `approvals.jsonl` holds 1 line.
- `?saved=<script>alert(1)</script>` → no banner, nothing echoed. 0 console errors across the journey.

## Full suite

One clean run, output redirected in full to a fresh file (60 lines), started after sabotage, the
smoke and the wording change had finished. The command was
`uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its final line is
`1323 passed, 2 skipped, 32 xfailed, 1 warning in 456.99s (0:07:36)`, exit=0. That is 1316 + this
unit's 7. All 32 XFAIL lines are `tests/test_browser_scroll_invariance.py` cases whose reasons name
AT-416 / AT-417, which are pre-existing. The warning is starlette's anyio deprecation.
