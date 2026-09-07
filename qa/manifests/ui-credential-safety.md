# Manifest — ui-credential-safety
**Contract:** qa/contracts/ui.md
**Goal task:** none (Track 0, Unit 0.2 of the approved plan)
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none filed — these are the holes found while planning Track 0, closed
before real credentials are entered.

## Why this exists
Unit 0.1 made credentials *declarable*. This makes the path *safe* before Umesh types real ERP
values into it. Four distinct holes, all silent:

1. **A pasted credential became plaintext in the repo.** The value box did no checking, and
   `projects/<slug>/cases.jsonl` is **not gitignored**. Worse, a literal carries no
   `{{SECRET:KEY}}` placeholder, so `session.fill` never tags the field with `MASK_ATTR` — the
   value would appear in cleartext in **every screenshot** too.
2. **A mistyped key failed only mid-run**, deep inside `_value_for`, arriving as a stringified
   `UndeclaredSecret` inside a generic `ERRORED` outcome.
3. **`assert_no_raw_secrets` had no production caller.** `SecretStore.guard_prompt` is documented
   "call before every model call"; `stages/grade.py::build_grade_prompt` did not use it, so
   protection rested entirely on evidence having been scrubbed earlier at `session._record`.
4. **A declared-but-unset key launched a browser first.** The UI run path loads secrets with
   `strict=False`, so a missing value surfaced as `BLOCKED_HITL` mid-run rather than as a
   precondition.

## What changed
- `src/autotester/ui/helpers.py` — new `_refuse_unsafe_value(value, project, secrets)`. If the
  value carries `{{SECRET:KEY}}` placeholders, every referenced key must be declared on the
  project (else 400 naming it). Otherwise the literal is checked against
  `secrets.redactor().is_clean(...)` and refused if it matches a real `.env` value, with a message
  telling the user to declare it and reference it instead. Lives in `helpers.py` because that
  module's stated job is shared request-validation — same home as `_require_reachable_base_url`.
- `src/autotester/ui/routes_cases.py` — `create_case` loads the project's `SecretStore` and
  threads it plus the project through `_build_steps`, which calls the guard per row.
- `src/autotester/ui/case_form.py` (new) — the form-rendering helpers (`_options`,
  `_step_row`, `_credential_datalist`, `STEP_ROWS`), split out when the picker pushed
  `routes_cases.py` to 302 lines, past doctor's 300 cap. `_credential_datalist` renders a plain
  `<datalist>` of the project's declared keys as `{{SECRET:KEY}}` options — **no JS**, per ui.md's
  no-fire list — so the safe thing to type is the easy thing to type. Absent entirely for a
  project that declares nothing, which keeps that case byte-identical to before.
- `src/autotester/stages/grade.py` — `grade(...)` gains an optional `secrets` param and calls
  `secrets.guard_prompt(prompt)` before the judge call. Optional so the three existing script
  callers are unchanged.
- `src/autotester/stages/run_case_pipeline.py` — passes `session.secrets` through, so the UI run
  path is now gated.
- `src/autotester/browser/secrets.py` — new `SecretStore.has_value(key)`, answering only whether a
  declared key currently has a usable value. It says nothing about the value.
- `src/autotester/ui/routes_runs.py` — new `_require_declared_values(...)`, called before a
  browser is launched: refuses the run and names the unset key(s) and where to fix them.
- `docs/MAP.md` regenerated.
- `tests/test_ui_credential_safety.py` (new) — 8 tests.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → exit 0, all pass
- `docker compose exec autotester uv run pytest -q tests/test_ui_credential_safety.py` → 8 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → exit 0
- `docker compose exec autotester uv run autotester doctor` → `doctor: clean`
- Real end-to-end after `docker compose restart autotester`, against the live app:
  an undeclared `{{SECRET:...}}` → 400 naming the key; a **real `.env` value** pasted into a step
  → 400; `GET /projects/erp/cases/new` → offers the declared keys; `POST /projects/erp/run` while
  the values are unset → 400 naming both keys.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q tests/test_ui_credential_safety.py
........                                                                 [100%]
$ docker compose exec autotester uv run pytest -q       # full suite, 0 failures
$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!
$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Live against the running app (the second probe used a **real** value read out of `.env`, to prove
the check fires on a genuine credential and not just on a lookalike):

```
1. POST /projects/erp/cases  step_value={{SECRET:NOT_DECLARED}}
   -> 400 "this project has not declared a credential called 'NOT_DECLARED'. Declare it in
           Project settings first, then use it here."

2. POST /projects/pathlynks/cases  step_value=<real PATHLYNKS_USER_PASSWORD from .env>
   -> 400 "that looks like a real credential. Do not paste the value into a test step — it
           would be stored in plain text and show up in screenshots. Declare it in Project
           settings, then reference it here as {{SECRET:KEY}}."

3. GET /projects/erp/cases/new
   -> offers {{SECRET:ERP_EMAIL}} and {{SECRET:ERP_PASSWORD}}

4. POST /projects/erp/run   (values still empty)
   -> 400 "these credentials have no value yet: ERP_EMAIL, ERP_PASSWORD. Enter them on the
           project's Credentials page (/projects/erp/env) before running."
```

No case was written in probes 1 or 2 — both projects' `cases.jsonl` are unchanged.

## Status: ready-for-check
