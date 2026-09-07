# Manifest — ui-secrets-declaration
**Contract:** qa/contracts/ui.md
**Goal task:** none (Track 0, Unit 0.1 of the approved plan)
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none filed yet — this is the prerequisite found while planning Track 0.

## Why this exists
Umesh: *"mai account ki credentials dunnga na tujhe test krne ko. point ye hai ki tune maanga hi
nhi mujh see"* — I would have given you the credentials; you never asked. He then chose
*"platform mai hoga credentials input krne ka option"* as the handover method.

That method did not exist. Nothing anywhere wrote `project.json::secrets`: `POST /onboard` and
`routes_project_edit.py` set only name/base_url/allowed_domains. So every project declared zero
credentials, `GET /projects/<slug>/env` rendered *"This project declares no credentials"*, and
`POST` 400d on every key (`routes_credentials.py:62-63`). Confirmed on disk before this change:
`projects/erp/project.json` had `"secrets": []`. **Setting up a logged-in test through the UI was
impossible**, which is the real reason the credentials were never requested.

## What changed
All in `src/autotester/ui/routes_project_edit.py` (78 → 190 lines), which already owns
`project.json` editing — no new module, no second write path.
- `_secret_row(safe_slug, ref)` — renders one declared key: key, description, scope, mask state,
  Remove. Shows **key and scope only**; a `SecretRef` holds no value and this module never sees one.
- `_secrets_card(safe_slug, project)` — the card: the table (or an honest empty state saying the
  project can only test pages needing no login), plus the declare form. The scope field is
  **prefilled with the project's `allowed_domains`**, since a credential scoped to a host the
  browser may not even visit is a mistake waiting to happen.
- `POST /projects/{slug}/secrets` — builds a real `SecretRef` and appends it. Validation is
  **`SecretRef`'s own validators** (`_reject_value_like`, `_reject_blank_domains`, the
  `^[A-Z][A-Z0-9_]*$` pattern) — this route only catches `ValidationError` and turns it into a
  readable 400 instead of a 500. It additionally refuses an **empty scope**: `SecretRef` permits
  `domains=[]`, but such a key can never resolve and would fail only later as a
  `SecretScopeError`. Duplicate key → 400.
- `POST /projects/{slug}/secrets/{key}/delete` — undeclares. Any value already in `.env` is left
  untouched (this module never handles values); the key simply becomes unusable, which is the
  point — an undeclared key is refused at typing time.
- `edit_project_form` renders the card.
- `docs/MAP.md` regenerated.

`tests/test_ui_secrets_declaration.py` (new) — 11 tests, including the two that matter most:
declaring makes `/env` genuinely usable (asserts the "declares no credentials" text is there
before and gone after), and **posting an extra `value` field is inert** — asserted by checking the
string never appears anywhere in the persisted project JSON.

## What this unit deliberately does NOT do
It does not touch values. `ui/env_editor.py` remains the only write path to `.env`, and the
Credentials page remains the only place a value is entered. This unit only makes that page
reachable.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → exit 0, all pass
- `docker compose exec autotester uv run pytest -q tests/test_ui_secrets_declaration.py` → 11 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → exit 0
- `docker compose exec autotester uv run autotester doctor` → `doctor: clean`
- Real end-to-end: `docker compose restart autotester`, confirm
  `curl -s localhost:8010/projects/erp/env` says "declares no credentials"; declare two keys via
  `POST /projects/erp/secrets`; confirm `/env` now lists them as "Not set" and that
  `projects/erp/project.json::secrets` holds both with the right scope.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q tests/test_ui_secrets_declaration.py
...........                                                              [100%]
$ docker compose exec autotester uv run pytest -q            # full suite, 0 failures
$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!
$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end against the live app, after restart:

```
BEFORE  GET /projects/erp/env      -> "declares no credentials"
        POST /projects/erp/secrets  ERP_EMAIL    -> 303
        POST /projects/erp/secrets  ERP_PASSWORD -> 303
AFTER   GET /projects/erp/env      -> ERP_EMAIL, ERP_PASSWORD, both "Not set"
        projects/erp/project.json::secrets -> both keys, domains
                                              ["vidysea.com","www.vidysea.com"], masked
        GET /projects/erp/edit     -> both rows render with scope + Remove
```

The Credentials page is now genuinely usable for `erp`; Umesh can type the two values in and
nothing else is needed from the code side.

## Status: checked-PASS

Verdict: `qa/verdicts/ui-secrets-declaration.md` (Cycle checked: 1, PASS, 7/7 criteria met).

The checker proved the no-leak property harder than this manifest claimed it. Its strongest
evidence was **`pathlynks`**, which declares four `SecretRef`s *and* holds four real values in
`.env`: it scanned the rendered HTML of every page for each real value. The single hit it found
it ran down and dismissed correctly — `PATHLYNKS_USER_LOGIN_URL` is byte-identical to that
project's own `base_url`, so it appears in the edit form as a URL, not as a credential. It also
posted `value`, `secret` and `password` canaries at the declare route (all inert), probed the key
pattern at its boundary (`A' onmouseover=x`, `A"><img src=x>`, `A/../../etc`, spaces, lowercase,
leading digit, a 70-char key — all 400, nothing written), and confirmed `.env`'s md5 was identical
before and after the entire check. It never exercised `POST /env` at all, so no probe value
reached `.env`.

It also verified the one rule this unit adds beyond `SecretRef`'s own validators is justified, by
executing `SecretRef(key='EMPTY_SCOPE', domains=[])` and confirming it validates today and would
fail only later at resolve time.

Source was uncommitted on arrival (the AT-055 pattern); the checker committed it itself
(`876367a` source+tests+manifest+MAP, `877f015` verdict+ledger) and pushed per D-007.

**Two low-severity issues filed, both mine, both fixed immediately after the verdict** — before
any real credential is entered, since one of them touches credential handling:
- **AT-068** — the declare 400 echoed the raw submitted key back, and the form's own hint named
  pasting the *value* there as a likely error. If a user pastes a password into the Key box, that
  response body and the access log would contain it. Now the 400 reads "cannot declare this
  credential: <reason>" and never quotes the input; the hint was reworded to say the box wants a
  NAME and that the value is entered later. Regression test:
  `test_a_rejected_key_is_never_echoed_back`.
- **AT-069** — the module docstring cited ledger id `AT-068` as this unit's tracker, but no such
  row existed when it was written, so the pointer later resolved to an unrelated defect. Now cites
  the plan and the gate file instead.
