# Manifest — ui-credential-safety-all-fields
**Contract:** qa/contracts/ui.md
**Goal task:** none (Track 0 follow-on)
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-070 (high), AT-071 (medium)

## Why this exists
The previous unit (`ui-credential-safety`) PASSed, but the checker — asked to bypass the guard
rather than confirm it — found it protected **one box, not the form**:

- **AT-070 (high):** the guard was wired to `step_value` alone. The same credential typed into the
  case **title**, the **target** box or the **expect** box was accepted and written in cleartext
  to `projects/<slug>/cases.jsonl`, which is **git-tracked in a public repo**. The title was the
  worst of the three: U6 leaves `rationale=None`, so `claim_of` falls back to the title and feeds
  it into the grade prompt, where the `guard_prompt` that unit had just wired raised an
  **unhandled `ValueError`** — so the leak also 500'd every subsequent run, with no way back.
- **AT-071 (medium):** the guard ran once per row, so a value split across two rows passed both
  checks individually and reassembled byte-for-byte on disk.

This is the last thing standing between Umesh and entering real ERP credentials, so it is fixed
before he does.

## What changed
- `src/autotester/ui/helpers.py` — new `_refuse_unsafe_submission(texts, project, secrets)`:
  runs the existing per-field `_refuse_unsafe_value` over **every** user-supplied text of a case,
  then checks their **concatenation** as well, which is what closes the split-across-rows case. A
  false positive on the joined text costs a clear message asking for a placeholder; a false
  negative costs a committed credential — so it fails closed deliberately.
- `src/autotester/ui/routes_cases.py` —
  - `create_case` now guards `title` plus every `step_target`, `step_value` and `step_expected`
    in one call, before any `Case` is built. `_build_steps` goes back to its original signature
    (it no longer needs the project or secrets), so the guard lives in exactly one place.
  - `rename_case` guards the new title too — rename was a second door into the same field.
- `src/autotester/stages/grade.py` — a `guard_prompt` refusal now returns a **BLOCKED verdict**
  naming no value, instead of raising. Withholding the prompt was right; crashing the run was not.
- `tests/test_ui_credential_safety.py` — 7 new tests (15 total): a parametrized case proving
  title/target/expect each refuse a real credential, the split-across-rows case, the rename door,
  an ordinary multi-field case still succeeding, and a unit test that a poisoned rubric yields a
  BLOCKED verdict carrying no value rather than an exception.

## Not fixed here
**AT-072 (low)** — `is_clean` has no minimum length by deliberate design (AT-002) and fails
closed, so a short or word-like value in `.env` makes ordinary text refuse. That is a message and
`.env`-hygiene problem, not a leak, and changing the matching rule is a security-relevant change
that deserves its own unit rather than a ride-along.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → exit 0, all pass
- `docker compose exec autotester uv run pytest -q tests/test_ui_credential_safety.py` → 15 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → exit 0
- `docker compose exec autotester uv run autotester doctor` → `doctor: clean`
- Real end-to-end after `docker compose restart autotester`, posting a **real** `.env` value
  (`PATHLYNKS_USER_PASSWORD`, read inside the shell, never printed) into each field in turn.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q tests/test_ui_credential_safety.py
...............                                                          [100%]
$ docker compose exec autotester uv run pytest -q        # full suite, 0 failures
$ docker compose exec autotester uv run ruff check src tests scripts   -> All checks passed!
$ docker compose exec autotester uv run autotester doctor              -> doctor: clean
```

Live, each probe posting the genuine `PATHLYNKS_USER_PASSWORD` into a different field:

```
title   -> HTTP 400
target  -> HTTP 400
expect  -> HTTP 400
split   -> HTTP 400     (halves in two separate step rows)
```

And the guard does not block ordinary use — a genuinely new case on `erp` posts fine:

```
POST /projects/erp/cases  "Training lookup page loads" -> HTTP 303
erp cases: "Sign-in page loads and shows the login form", "Training lookup page loads"
```

(An identical re-post of the first case returns 400 from the *duplicate* check, not the guard —
verified by reading the error body, which names the clashing case.)

## Status: checked-PASS

Verdict: `qa/verdicts/ui-credential-safety-all-fields.md` (Cycle checked: 1, PASS, 7/7 criteria).
**AT-070 and AT-071 both closed**, and verified further than this manifest claimed: the checker
re-ran every bypass with the real `PATHLYNKS_USER_PASSWORD` and additionally proved a **three-row**
split and a split across **two different field types** (target+expect, title+target) are all
refused, and that the guard runs before any `Case` is built so a refusal writes nothing.

It also added **criterion U8** to `qa/contracts/ui.md` — the credential guard had no criterion at
all, so a later unit could have deleted it unnoticed.

**The check found the guard stops at the case form. Five new issues:**
- **AT-073 (high)** — `POST /onboard` (name), `POST /projects/{slug}/edit` (name) and
  `POST /projects/{slug}/secrets` (**description**) all accept a real credential and write it in
  cleartext to git-tracked `project.json`; a credential used as a project *name* then renders on
  **every page including the home index**. Breaches core-invariants **C5**. The description box is
  the dangerous one — it sits directly beside the Key box on the very form the user was told to
  use, so this is a trap introduced by Unit 0.1.
- **AT-074 (medium)** — `is_clean` is a plain substring test, so a **URL-encoded** value, or one
  split by a single space or newline inside one field, is accepted and written to `cases.jsonl`;
  recoverable with one `unquote`/whitespace-strip.
- **AT-075 (medium)** — `unknown case class '{x}'` and `unknown action '{x}'` echo raw form input
  into the 400 body (the AT-068 pattern again), and the class parse runs *before* the guard.
- **AT-076 (medium)** — the guard's advice is wrong for a navigate target: only `session.fill`
  resolves `{{SECRET:KEY}}`, `goto` does not, so a refused URL has no working alternative.
  Reachable today because the non-secret `PATHLYNKS_USER_LOGIN_URL` sits in `.env`.
- **AT-077 (low)** — 16 fields joined with no separator create 15 artificial boundaries; an
  innocent straddle is refused with a message naming no field, leaving the user stuck.

Source was uncommitted on arrival (the AT-055 pattern again — fifth time); the checker committed
the five paths itself (`b811366`), verdict/contract/ledger in `3312c78`, both pushed per D-007.
Repo-root `.env` was never written to; its scratch projects were deleted.
