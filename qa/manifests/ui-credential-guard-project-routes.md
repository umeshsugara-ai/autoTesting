# Manifest — ui-credential-guard-project-routes
**Contract:** qa/contracts/ui.md (U8)
**Goal task:** none (Track 0 follow-on)
**Fix cycle:** 3 of max 3
**Dual check:** no
**Issues addressed:** AT-073 (high, partial), AT-074, AT-075, AT-077, **AT-078 (the cycle-1 FAIL)**, AT-082 (medium)

## Why this exists
The previous unit closed the case form. The checker then found the guard **stopped there**, and
the worst of what it found is a trap this session's own Unit 0.1 created:

- **AT-073 (high)** — `POST /onboard` (name), `POST /projects/{slug}/edit` (name) and
  `POST /projects/{slug}/secrets` (**description**) all accepted a real credential and wrote it in
  cleartext to **git-tracked `project.json`**; a credential used as a project *name* then renders
  on **every page, including the home index**. Breaches core-invariants **C5**. The description
  box is the dangerous one: it sits one field from the Key box on the exact form the user was
  told to use for credentials.
- **AT-074 (medium)** — `Redactor.is_clean` is a plain substring test, so a **URL-encoded** value,
  or one broken by a stray space or newline, passed and was written to `cases.jsonl` —
  recoverable by one `unquote_plus` or a whitespace strip.
- **AT-075 (medium)** — `unknown case class '{x}'` / `unknown action '{x}'` echoed raw form input
  into the 400 body (the AT-068 pattern, third occurrence), and the class parse ran *before* the
  guard, so it was reachable.
- **AT-077 (low)** — a refusal named no field, so a user hitting the concatenation check was stuck.

## What changed
- `src/autotester/ui/helpers.py`
  - New `_credential_variants(text)` — the forms a pasted credential trivially arrives in:
    the literal, `unquote_plus`'d, whitespace-stripped, and both. Matching now runs over all of
    them (AT-074).
  - `_refuse_unsafe_value` takes a `field` label and names it in the refusal (AT-077), and its
    message now says plainly that only a step's **Value** is substituted — not a URL or a title —
    so the advice it gives is actually true (this is AT-076's misleading half; the deeper
    question of whether `goto` should resolve placeholders is left alone, see below).
  - `_refuse_unsafe_submission` takes `(label, text)` pairs and names the fields involved when the
    **concatenation** check fires.
- `src/autotester/ui/app.py::onboard_submit` — guards name / base_url / allowed_domains before the
  project is written (AT-073).
- `src/autotester/ui/routes_project_edit.py` — guards the same three on `edit`, and guards
  **description + scope** on `declare_secret` (AT-073).
- `src/autotester/ui/routes_cases.py` — new `_guard_submitted_case(form, project, secrets)`
  extracted so `create_case` stays inside doctor's 50-line function cap; the two raw-input echoes
  are gone (AT-075).
- `tests/test_ui_credential_safety.py` + new `tests/test_ui_credential_safety_project.py` (split
  at doctor's 300-line file cap) — 21 tests total across the two files.

## Deliberately NOT fixed here
- **AT-076 (medium)** — a `{{SECRET:KEY}}` in a *navigate target* does not resolve, because only
  `session.fill` substitutes placeholders. This unit corrects the **advice** so it no longer
  points at something that cannot work, but does not make `goto` resolve secrets: putting a
  credential in a URL is a security-boundary change (it would land in browser history, referrers
  and every `EvidenceKind.URL` record), and that deserves its own decision, not a ride-along.
- **AT-072 (low)** — `is_clean`'s lack of a minimum length. Still a message/`.env`-hygiene problem,
  not a leak.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → exit 0, all pass
- `docker compose exec autotester uv run pytest -q tests/test_ui_credential_safety.py tests/test_ui_credential_safety_project.py` → 21 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → exit 0
- `docker compose exec autotester uv run autotester doctor` → `doctor: clean`
- Real end-to-end after `docker compose restart autotester`, posting the genuine
  `PATHLYNKS_USER_PASSWORD` (read inside the shell, never printed) into each newly-guarded route.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q      # 356 tests, 0 failures
$ docker compose exec autotester uv run ruff check src tests scripts   -> All checks passed!
$ docker compose exec autotester uv run autotester doctor              -> doctor: clean
```

Live, each probe posting the real credential:

```
AT-073   secrets description   -> HTTP 400
AT-073   project rename        -> HTTP 400
AT-073   onboard name          -> HTTP 400
AT-074   url-encoded value     -> HTTP 400
AT-074   space-broken value    -> HTTP 400

projects/ still holds exactly erp, pathlynks, regression-demo, vidysea-erp
grep for the credential across projects/  -> no project file contains it
```

## Cycle 1 — FAILED, and the failure was self-inflicted

Verdict: `qa/verdicts/ui-credential-guard-project-routes.md` (Cycle checked: 1, **FAIL**, 7/8).

> **[U7]** a no-op save of the existing `pathlynks` project's own stored base_url returns 400 —
> the guard this unit added to `POST /projects/{slug}/edit` refuses the project's own unmodified
> data, and the remedy it names cannot be applied to a base URL, so the project is uneditable
> with no expressible fix. (AT-078)

The cause is stated plainly: `pathlynks`'s `base_url` is byte-identical to the **non-secret**
`.env` entry `PATHLYNKS_USER_LOGIN_URL`, and the guard matched against every value in the shared
`.env`. Cycle 1's own manifest had **explicitly declined to fix AT-076** and then extended that
known-broken control to a higher-value surface. That is the whole defect: not a missed edge case,
but shipping a control whose flaw was already written down.

## Cycle 2 — what changed

- **`src/autotester/ui/helpers.py`: new `_declared_credential_redactor()`.** Masking OUTPUT and
  refusing INPUT now use different scopes, and the difference is the fix:
  - Output still masks **everything** in the shared `.env`, declared or not — an undeclared value
    is still a secret if it reaches a screenshot (AT-004, unchanged).
  - Input matches only values some project has **declared** as a `SecretRef`. A `SecretRef` is a
    human's own statement that a value is a credential; `.env` also holds plain configuration
    (a login URL, a Mongo URI), and refusing text equal to *those* is what bricked `pathlynks`.
  - The scope is **every project's** declarations, not just the one being edited, because at
    onboarding the project does not exist yet and has declared nothing — a per-project scope left
    that route unguarded. (Caught by my own test failing when I first scoped it per-project.)
- **`src/autotester/ui/env_editor.py`: new `_render_value()` (AT-082).** The writer stored values
  bare, so `parse_env`'s comment-stripping, rstrip and unquoting silently mangled them — `p@ss #1`
  was stored as `p@ss` — while the Credentials page still reported "Set". It now quotes with a
  character the value does not contain, **verifies the round-trip by re-parsing**, and **refuses**
  a value containing both quote characters rather than storing something different from what was
  typed. This sits directly on the route the ERP password will take.
- `tests/test_ui.py`, `tests/test_ui_settings.py` — two existing tests asserted the raw on-disk
  spelling (`KEY=value`). They now assert the **round-trip**, which is the actual contract and is
  independent of quoting.
- `tests/test_ui_credential_safety_project.py` — 9 new tests: the six mangling cases, the
  both-quotes refusal, and that setting one key leaves another's awkward value intact.

## Cycle-2 evidence

```
$ docker compose exec autotester uv run pytest -q      # 0 failures
$ docker compose exec autotester uv run ruff check src tests scripts   -> All checks passed!
$ docker compose exec autotester uv run autotester doctor              -> doctor: clean
```

**The cycle-1 FAIL, re-probed live — every project's own unmodified data saved back:**

```
erp 303 · pathlynks 303 · regression-demo 303 · vidysea-erp 303
```

`pathlynks` was the one that 400'd; it now saves. **And the guard still refuses a real declared
credential** on the same routes:

```
project rename  name=<real PATHLYNKS_USER_PASSWORD>  -> 400
onboard         name=<real password>                 -> 400
case            value=<real password>                -> 400
```

**AT-082, every previously-mangled value now round-trips:**

```
'p@ss #1'    -> 'p@ss #1'      (was 'p@ss')
'  spaced  ' -> '  spaced  '   (was 'spaced')
"'quoted'"   -> "'quoted'"     (was 'quoted')
'has"double' / 'tab	here' / 'plain-ok' -> exact
a value containing BOTH quotes -> REFUSED, not stored wrong
```

## Still open, deliberately
**AT-079/AT-080** (the `slug` and secret-`key` boxes are guarded only by their own regexes, not by
the credential guard), **AT-081** (double-encoded / base64 / markup-interleaved values are not
matched), **AT-072**, **AT-076** (a `{{SECRET:KEY}}` in a navigate target still does not resolve —
only the misleading *advice* was fixed). Each is recorded rather than quietly folded in.


## Cycle 2 — FAILED. The fix was too broad.

Verdict cycle 2: **FAIL**, [U7]/AT-083.

Cycle 2 fixed AT-078 by scoping the input guard to values some project had **declared** as a
`SecretRef`. That fixed the no-op re-save, and opened a real hole: an **undeclared** credential in
the shared `.env` — a provider API key — stopped being refused. The checker proved it with the
operator's **live `GEMINI_API_KEY`**: pasted as a case title and as a step Value, both accepted,
read back verbatim from a git-tracked `cases.jsonl`; as a project name it landed in
`project.json`. This repo is public.

The checker was fair about provenance: cycle 1's own fix direction offered two branches
("gate on declared values **or** exempt a value that is also a legitimate URL/host"), and cycle 2
took the first faithfully. The right branch was the second, sharpened — which is what cycle 3 does.

## Cycle 3 — what changed

**One narrow change, exactly as cycle 2's verdict prescribed:** matching is restored to **every**
value in `.env` (declared or not), and a field is exempt **only** when its text is byte-identical
to what is already persisted for that same field of that same project.

- `src/autotester/ui/helpers.py` — `_refuse_unsafe_value` / `_refuse_unsafe_submission` take an
  `exempt` frozenset; matching uses `secrets.redactor()` again (full `.env` breadth). The
  `_declared_credential_redactor` from cycle 2 is gone.
- **The concatenation check excludes exempt fields too.** Missing this is what made my first
  cycle-3 attempt still refuse `pathlynks`: each field passed individually, but the *join* still
  contained the exempt base URL. An exempt field holds data the system itself stored, so it cannot
  be half of a freshly-pasted credential.
- `src/autotester/ui/routes_project_edit.py` — `edit` exempts the project's own stored
  name / base_url / allowed_domains; `declare_secret` exempts the stored domains.
- `src/autotester/ui/routes_cases.py` — `rename_case` exempts the case's own current title.
- `src/autotester/browser/secrets.py` — removed the now-dead `declared_redactor()` (AT-084).
- `tests/test_ui_credential_safety_project.py` — 3 new tests: a project re-saves its own
  unmodified data; an **undeclared** `.env` value is still refused; and the exemption does not let
  a credential in through a *different* field of the same form.

## AT-085 — the process failure, and the guard I added for it

Cycle 2's checker found the running app was serving **stale code** when the live evidence was
gathered: `env_editor.py` postdated the server start by 111 s. It happened to me again in this
cycle — `docker compose restart` raced my edit, the container started 51 s *before* the file was
written, and `pathlynks` appeared to still fail. I only caught it because the same symptom
persisted while a direct in-container call to the same function accepted.

Every live figure below was taken after a **staleness guard** that compares the container's
`StartedAt` against the newest `src/**.py` mtime and refuses to report otherwise:

```
STALENESS GUARD: container=1788773434  newest_source=1788773338
  OK: server is running current code
```

## Cycle-3 evidence

```
$ docker compose exec -T autotester uv run pytest -q      # 0 failures
$ ruff check src tests scripts   -> All checks passed!
$ autotester doctor              -> doctor: clean
```

**AT-078 (cycle-1 FAIL) — every project re-saves its own unmodified data:**

```
erp 303 · pathlynks 303 · regression-demo 303 · vidysea-erp 303
```

**AT-083 (cycle-2 FAIL) — both an undeclared and a declared credential are refused:**

```
gemini key -> case title          400
gemini key -> project name        400
gemini key -> onboard name        400
gemini key -> secret description  400
password   -> case step value     400
password   -> split across 2 rows 400
```

**Ordinary work unaffected** — a genuinely new case posts fine (303). An identical re-post returns
400 from the *duplicate* check, confirmed by reading the body, which names the clashing case.
No credential appears in any file under `projects/`.

## Newly filed, not hidden
**AT-086 (low)** — a project whose `base_url` already appears in `.env` cannot be **onboarded**,
because at onboarding nothing is stored yet so the exemption is empty. Found by my own regression
test failing. It fails closed and has workarounds; fixing it means deciding whether base_url and
allowed_domains are config fields exempt from credential matching by nature, which is a scope
question rather than a bug fix — and this unit is at cycle 3 of 3.

Still open from earlier cycles: **AT-079/AT-080** (the `slug` and secret-`key` boxes are guarded
only by their own regexes), **AT-081** (double-encoded / base64 / markup-interleaved values),
**AT-072**, **AT-076**.

## Status: ready-for-check
