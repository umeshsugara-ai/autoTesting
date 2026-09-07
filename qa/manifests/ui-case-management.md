# Manifest — ui-case-management
**Contract:** qa/contracts/ui.md
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-060

## What changed
- `src/autotester/store/filestore.py` — new `delete_jsonl_row(path, model_cls, row_id, key="id")`,
  returning whether a row was removed. Same whole-file atomic rewrite as the neighbouring
  `upsert_jsonl`, and the same stated caveat: for a small curated collection, never for
  append-only history.
- `src/autotester/store/project_store.py` — four case methods, all thin:
  `get_case(id)`, `has_case(id)` (the check `add_case` already makes silently, exposed so a
  caller can tell "created" from "already existed" — `add_case`'s idempotence is deliberate and
  is unchanged), `update_case(case)` (via `upsert_jsonl`, keeping the id), and
  `delete_case(id)`. `update_case`/`delete_case` keep the `_case_ids` cache consistent.
- `src/autotester/ui/routes_cases.py` — now creates, lists, renames and deletes:
  - New `_refuse_duplicate(store, case)`: a submission whose steps match an existing case is a
    **400 naming the existing case's title**, instead of being silently swallowed.
  - New `GET /projects/{slug}/cases` — the case list: title (as an inline rename field), class,
    step count, delete. Empty state points at the add form.
  - New `POST /projects/{slug}/cases/{case_id}/rename` — title only. Title sits outside
    `Case.compute_id()`, so the id survives and every past run, verdict and rubric stays
    attached.
  - New `POST /projects/{slug}/cases/{case_id}/delete` — removes the case. Past runs and
    verdicts are history and are deliberately left on disk.
  - `create_case` now redirects to the cases list rather than the project page, so the user
    lands on the thing they just made with its controls beside it.
- `src/autotester/ui/app.py` — project page gains a `🧪 Cases` action beside `+ Add case`.
- `src/autotester/ui/theme_style.py` — `.btn-danger` (using the existing `--danger`/`--danger-bg`
  tokens) and `.row-form` for the inline rename.
- `docs/MAP.md` — regenerated (new store/filestore functions).
- `tests/test_ui_cases.py` — one updated assertion for the new redirect target, with the reason
  in a comment.
- `tests/test_ui_case_management.py` (new) — 10 tests: duplicate steps refused with the
  existing title named and nothing written; list shows every case; empty list points at the add
  form; rename keeps the id; blank rename refused with the stored title unchanged; rename and
  delete of an unknown case are 404; delete removes only its own row; and **delete-then-re-add
  works**, which is what proves `delete_case` genuinely clears the id cache rather than leaving
  the duplicate guard to refuse a legitimate re-add.

## How it was found
Filed by the checker during `ui-add-case`: `add_case` is idempotent on the content id, so a
second submission with identical steps was discarded while the user was redirected as if it had
worked. Because `title` is outside `compute_id`'s payload, re-submitting the form was also the
natural way a user would try to fix a typo'd title — and it failed silently, with no case list
to inspect and no rename or delete anywhere in the UI.

## The identity rule this unit is built on
`Case.compute_id()` hashes `(project, flow_id, case_class, steps)`. So:
- **Renaming is safe** and keeps the id — history stays attached. Offered.
- **Changing steps or class is a different case** by definition, so it is not offered as an
  "edit"; the message on a duplicate says so ("Change a step to make it a different case").
  A user who genuinely wants different steps adds a case and deletes the old one, which is now
  possible for the first time.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → expected: exit 0, all tests pass
- `docker compose exec autotester uv run pytest -q tests/test_ui_cases.py tests/test_ui_case_management.py` → expected: exit 0, 19 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: exit 0
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Real end-to-end: `docker compose restart autotester`, then re-post `projects/erp`'s existing
  case with a different title but identical steps → expected: HTTP 400 naming the existing
  title; and `GET http://localhost:8010/projects/erp/cases` → expected: the case listed with
  working Rename and Delete controls.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q tests/test_ui_cases.py tests/test_ui_case_management.py
...................                                                      [100%]

$ docker compose exec autotester uv run pytest -q
(full suite: all pass, 1 skip, no failures)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end against the live app:

```
$ curl -X POST .../projects/erp/cases  (same steps, different title)
{"detail":"this project already has a case with exactly these steps: 'Sign-in page loads and
 shows the login form'. Change a step to make it a different case, or rename the existing one
 from the cases list."}
HTTP 400

GET /projects/erp/cases  (screenshot .work/cases-list.png)
  -> "Sign-in page loads and shows the login form" | HAPPY | 1 step | Rename · Delete
```

## Status: ready-for-check
