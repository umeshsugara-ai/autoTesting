# Manifest — at079-080-credential-guard-gaps

**Unit:** AT-079/AT-080 — two fields AT-073's credential guard never covered
**Contract:** `qa/contracts/ui.md` (U8 — credential safety on routes that write `project.json`)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-079 (medium), AT-080 (medium)

## What was wrong

AT-073 fixed the credential guard on project name/rename and secret description/scope, but two
sibling fields on the same forms were never added to the same check:

- **AT-079**: `POST /onboard`'s `slug` field is checked only for SHAPE (`_require_slug`, a regex),
  never for CONTENT. A credential that happens to be slug-shaped (lowercase/digits/hyphens — an
  ordinary password shape) becomes the git-tracked directory name, every page's URL, and text on
  the home index.
- **AT-080**: `POST /projects/{slug}/secrets`'s `key` field — the FIRST box on the very form the
  user is told to use for credentials — was never checked at all. An all-uppercase-with-underscore
  credential satisfies `SecretRef`'s own key pattern (`^[A-Z][A-Z0-9_]*$`) and would be written
  verbatim into git-tracked `project.json::secrets[].key`.

## What changed

- `src/autotester/ui/app.py::_guard_intake` — added `("the slug", project.slug)` to the
  `_refuse_unsafe_submission` field list, ahead of name/base_url/allowed_domains.
- `src/autotester/ui/routes_project_edit.py::declare_secret` — added `("the key", key)` to its
  `_refuse_unsafe_submission` field list, ahead of description/scope.
- `tests/test_ui_credential_safety_project.py` — two new regression tests:
  `test_a_credential_shaped_slug_at_onboarding_is_refused` (AT-079) and
  `test_a_credential_shaped_key_is_refused` (AT-080), following the existing AT-073 test shapes
  exactly.

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_credential_safety_project.py -q` → expected: exit 0, 16 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_credential_safety_project.py -q
................                                                         [100%]  (16 passed)

$ uv run pytest -q
[all dots, exit 0 — no F anywhere]
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. Extracted clean `HEAD`, layered my uncommitted diff on with `git apply`.
2. `uv sync`; confirmed `autotester.__file__` resolves inside the extract.
3. Baseline: `uv run pytest tests/test_ui_credential_safety_project.py -q` → 16 passed, exit 0.
4. Reverted the AT-079 fix (`slug` removed from the guard list) → **exactly**
   `test_a_credential_shaped_slug_at_onboarding_is_refused` failed (`303 != 400`), all others green.
5. Restored AT-079, reverted the AT-080 fix (`key` removed from the guard list) → **exactly**
   `test_a_credential_shaped_key_is_refused` failed (`200 != 400`), all others green.
6. Extract deleted; live tree confirmed to carry only the two real edits + test file.

## Live browser evidence

**UI-touching — full live check, real Chromium via Playwright MCP, against the real dev server**
(`uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8123`, real `projects/` store —
not a scratch fixture):

| did | observed |
|---|---|
| onboarded a real project `smoketest-orig` with credential `SMOKE_PASSWORD=my-fake-secret-value-98765` | 200, project created normally |
| onboarded a second project with `slug=my-fake-secret-value-98765` (the known credential value) | **HTTP 400**, body: `"the slug looks like it contains a real credential..."` — no raw value echoed |
| checked disk | no `projects/my-fake-secret-value-98765` directory created |
| onboarded a fresh project `smoketest-key` with credential `SMOKE_ORIGINAL_KEY=SMOKE_LEAKY_VALUE_555` | 200, project created normally |
| declared a new secret with `key=SMOKE_LEAKY_VALUE_555` (the known credential value, key-pattern-shaped) | **HTTP 400**, body: `"the key looks like it contains a real credential..."` — no raw value echoed |
| checked disk | `SMOKE_LEAKY_VALUE_555` does not appear anywhere in `projects/smoketest-key/project.json` |
| console messages | 1 entry, the expected 400 network-status log for the refused POST — no app-side JS error |

Both smoke-test projects (`smoketest-orig`, `smoketest-key`) deleted after (`rm -rf`, untracked
directories, no git impact) — this ran against the real dev store, so cleanup matters.

**This is the maker's own smoke pass and is NOT this unit's validation.** The checker runs its
own, with its own script, per the standing rule.

## What this unit does not claim

- Does not claim every field on every credential-adjacent form is now covered — only the two
  specific gaps AT-079/AT-080 named. A future sweep may find a third sibling field; that would be
  its own issue, the same discipline the AT-073 family has followed throughout.
- Does not change `_refuse_unsafe_submission`'s matching logic itself (still a substring/variant
  check against known values) — only which fields are passed into it.

## Status: ready-for-check
