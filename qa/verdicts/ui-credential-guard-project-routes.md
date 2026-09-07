# Verdict — ui-credential-guard-project-routes

**Date:** 2026-09-07
**Contract:** qa/contracts/ui.md (U1–U8)
**Manifest:** qa/manifests/ui-credential-guard-project-routes.md
**Cycle checked: 2**
**Mode:** A (unit check), bound to `d:/autoTesting`. Treated as a **release gate**: the
operator is about to type real ERP credentials into the running app.

```
VERDICT: FAIL
SCOREBOARD: 7/8 criteria met, invariants: no U-invariant list in this contract; the build
            introduces no new breach by itself, but core-invariant C5 ("no raw credential
            in a git-tracked file") is reachable again through the case and project forms.
FAILURES:
- [U8] sev: high · the AT-078 fix narrowed the INPUT guard from "every value in `.env`" to
  "values some project has DECLARED as a SecretRef", so an UNDECLARED real credential is no
  longer refused: the operator's live GEMINI_API_KEY posted as a case title and as a step
  Value both returned 200 and the key was read back verbatim out of a git-tracked
  cases.jsonl; as a project `name` it landed in project.json. U8 requires "a raw `.env`
  value in any one of those fields is refused (400)". · fix: keep the full-`.env` scope for
  input and fix AT-078 the narrow way instead — exempt only text byte-identical to the
  value ALREADY persisted for that same field of that same project (a no-op re-save cannot
  be a new leak), or an explicit non-secret config allowlist; that satisfies U7 and U8
  together · issue: AT-083
ISSUES-WRITTEN: AT-083 (new, high), AT-084 (new, low), AT-085 (new, medium);
                AT-078 → fixed, AT-082 → fixed
EXPLANATION: The two things this cycle set out to do are genuinely done — AT-078 is fixed at
the root and AT-082 is fixed thoroughly, both re-derived live by me rather than taken from
the manifest. But the AT-078 fix paid for editability with coverage that U8 already owns,
and the price is a reproduced leak of a real API key into a public repo. That is a new hole,
not an acceptable trade, and a narrower fix satisfying both criteria was available. In
fairness to the maker, cycle 1's own fix direction proposed this scope — see "Whose defect
this is" below; it changes the blame, not the criterion.
```

## What I re-ran (every command executed by me, in the container)

| Command | Result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | 364 passed, 1 skipped, 0 failures |
| `… pytest -q tests/test_ui_credential_safety.py tests/test_ui_credential_safety_project.py` | 29 passed |
| `… uv run ruff check src tests scripts` | `All checks passed!` |
| `… uv run autotester doctor` | `doctor: clean` |

The manifest says "21 tests total across the two files" (cycle-1 text) and "9 new"; the
actual count is 29. Immaterial to the verdict, noted for accuracy.

## 1. Is AT-078 genuinely fixed, and fixed at the root?

**Fixed, and at the root — yes.** `helpers._declared_credential_redactor()` splits the two
scopes that were wrongly shared: output masking still covers every `.env` value (AT-004
untouched), input matching covers only declared `SecretRef`s. That is the correct
*diagnosis*: `.env` genuinely holds non-secret configuration, and equating "is in `.env`"
with "is a credential" is what bricked `pathlynks`.

Re-probed live after `docker compose restart autotester`, posting each project's own
unmodified `name`/`base_url`/`allowed_domains` straight back to `POST /projects/{slug}/edit`:

```
erp 200 · pathlynks 200 · regression-demo 200 · vidysea-erp 200
project.json byte-identical afterwards: True in all four
```

`pathlynks` — the cycle-1 FAIL — saves. And the guard keeps its teeth on a **declared**
credential, on every guarded route (real `PATHLYNKS_USER_PASSWORD`):

```
edit/name 400 · edit/base_url 400 · onboard/name 400 · secrets/description 400
case title 400 · target 400 · value 400 · expect 400 · split across 2 rows 400
declared EMAIL in title 400
```

Each refusal names the field, so AT-077 stays closed in a usable way.

### Interrogating the split itself — the basis is right, the scope is wrong

"Declared by any project" is the right *basis* (a `SecretRef` is a human saying "this is a
credential") but the wrong *scope*, because it is applied to the wrong problem. AT-078 was
never "the guard is too broad"; it was "a no-op re-save of data already on disk is refused".
Those need different fixes, and the maker applied the broad one **globally** — including to
the case form, where no conflict with U7 exists at all, and where cycle 1's coverage had
already been PASSed under U8 by the previous unit.

What is now **not** caught (in-process probe of `_refuse_unsafe_value` over every `.env` key,
project `regression-demo`):

```
PATHLYNKS_COUNSELLOR_EMAIL / _PASSWORD   REFUSED     (declared)
PATHLYNKS_USER_EMAIL / _PASSWORD         REFUSED     (declared)
PATHLYNKS_USER_LOGIN_URL                 ALLOWED     (correct — non-secret config)
PATHLYNKS_COUNSELLOR_LOGIN_URL           ALLOWED     (correct — non-secret config)
PATHLYNKS_MONGO_URI                      ALLOWED     (arguable)
GEMINI_API_KEY                           ALLOWED     ← a real, live credential
ANTHROPIC_API_KEY                        ALLOWED     (currently empty, so untestable)
```

**This is a hole, not an acceptable trade.** Demonstrated end-to-end on a throwaway project,
live, with the real key:

```
POST /projects/<scratch>/cases   title=<GEMINI_API_KEY>       -> 200
POST /projects/<scratch>/cases   step_value=<GEMINI_API_KEY>  -> 200
   `GEMINI_API_KEY in projects/<scratch>/cases.jsonl` -> True
POST /projects/vidysea-erp/edit  name=<GEMINI_API_KEY>        -> 200, written to project.json
POST /projects/<x>/secrets       description=<GEMINI_API_KEY> -> 200
```

`cases.jsonl` and `project.json` are git-tracked in a **public** repo
(github.com/umeshsugara-ai/autoTesting). The Gemini and Anthropic keys are exactly the sort
of value a user pastes into the wrong box — they are entered one click away, on
Settings → Providers. Cycle 1 refused every one of these.

The fix that satisfies U7 *and* U8 is narrower and was available: exempt only a submission
byte-identical to the value already persisted for that field of that project. A value
already on disk cannot be newly leaked by writing it again. Filed as **AT-083** (high).

I am not amending U8 to fit this build. Narrowing a safety criterion is a CRITICAL
amendment that goes to the Approver, decided away from any pending verdict — and a failing
artifact is evidence about the artifact, not about the rule.

### Whose defect this is

Stated plainly, because it affects how this fix cycle should be counted: cycle 1's verdict
told the maker to "gate the guard on DECLARED secret values (or exempt a value that is also
a legitimate URL/host)". The maker took the first branch, faithfully. That fix direction was
under-specified and its first branch was the wrong one — this is in part a checker-authored
defect, and the right remedy is the second branch of that same sentence, sharpened into
AT-083. It does not change the verdict (U8 is the ground truth and it is not met, with a
reproduced leak), but the maker did not go off-script, and cycle 3 should be scoped as
"apply AT-083's narrow exemption", not as a redesign.

## 2. AT-082 / `_render_value` — verified independently, and it is good work

17 values through the production `set_env_value` + `parse_env` pair on a temp `.env` — the
6 the manifest lists plus every case I could think of:

```
'p@ss #1' OK · '  spaced  ' OK · "'quoted'" OK · 'has"double' OK · 'tab\there' OK
'plain-ok' OK · '   ' (whitespace only) OK · '' (empty) OK · 'secret\' (trailing
backslash) OK · '#notacomment' OK · '#' OK · 'a=b=c' OK · 4000 chars OK · unicode OK
'export FOO=bar' OK · "'half" (unmatched quote) OK · 'url#frag' OK
FAILURES: []
```

- **Both-quotes case: REFUSED, not mangled** — `InvalidEnvValue`, and the target file is
  **byte-identical after the refusal**. Nothing half-written, and that is structural rather
  than lucky: `_render_value` raises before `env_path` is read or opened.
- **Existing entries survive a write.** A realistic 6-line `.env` (comment, blank line, a
  quoted value containing `#`, a plain value, an `export `-prefixed line, a padded quoted
  value) came through all 17 writes with every prior key unchanged.
- Newline injection still refused.
- Re-verified through the **live route** `POST /projects/{slug}/env` post-restart, 8 values
  incl. `p@ss #1`, `  spaced  `, `'quoted'` and 300 chars — all exact; both-quotes → 400;
  all pre-existing `.env` keys intact afterwards.

This is the strongest part of the cycle, and it sits exactly where the ERP password will go.

## 3. The two changed existing tests — legitimate, verified by mutation

`test_ui.py` and `test_ui_settings.py` swapped `assert "KEY=value" in written` for
`assert parse_env(written)["KEY"] == value`. I did not take that on trust. I re-ran the suite
with the old bare writer forced back in at runtime
(`env_editor._render_value = lambda v: v`, via a read-only `-p` plugin on `PYTHONPATH` — no
repo file touched):

```
FAILED test_ui_credential_safety_project.py::test_a_stored_credential_reads_back_exactly[p@ss #1]
FAILED …[  spaced  ]
FAILED …['quoted']
FAILED …::test_a_value_that_cannot_round_trip_is_refused_not_mangled
FAILED …::test_setting_one_value_leaves_the_others_intact
```

Five failures — the new tests are load-bearing and do catch a broken writer.

Honest nuance: the two *changed* assertions themselves still pass under that mutation,
because their values (`new-real-value`, `new-real-key`) round-trip fine bare. So those two
did not become stronger; they became **spelling-independent**, which they had to, since the
on-disk spelling legitimately changed. The mangling coverage moved into dedicated new tests
rather than being deleted. That is a legitimate generalisation, not a test weakened to fit
the code — no assertion was left that the code could break silently.

## 4. Regression across the whole UI (live, post-restart)

Every route 200s; unknown slug 404s. Full lifecycle on a throwaway project:

```
onboard 200 · detail/edit/env 200 · declare secret 200 · env page lists the key True
set value 200 + exact round-trip · value never echoed back True
undeclared key on env route 400 · add case 200 · duplicate case 400 (AT-060 holds)
{{SECRET:KEY}} placeholder accepted 200 · undeclared placeholder 400
rename 200 · blank rename 400 · delete case 200 · undeclare secret 200
report / cases / flow-diagram 200 · base_url outside allowed_domains 400 (host named)
subdomain of an allowed domain still accepted 200 (U7's anti-over-strictness clause)
unknown project on POST cases 404
```

**U5 re-probed hostilely** — a project whose `name` and `base_url` carried
`<script>alert(1)</script>&'"` — zero raw `<script>` across `/`, detail, edit, cases,
cases/new, env and report.

**`projects/erp` intact:** 2 cases in `cases.jsonl`, 2 `SecretRef`s (`ERP_EMAIL`,
`ERP_PASSWORD`, both `mask_in_screenshot: true`), `write_policy: read_only`, loads fine.

**U3 re-verified:** no real `.env` value appears in the HTML of `/`, `/settings/providers`,
or any erp/pathlynks page. The one string that matches is `pathlynks`'s own `base_url`,
which equals the non-secret `PATHLYNKS_USER_LOGIN_URL` — displayed by design, and the very
coincidence that caused AT-078.

### Criterion-by-criterion
U1 ✅ · U2 ✅ · U3 ✅ (strengthened by AT-082) · U4 ✅ · U5 ✅ · U6 ✅ · U7 ✅ (AT-078 fixed) · **U8 ❌**

## Two further findings

- **AT-084 (low)** — `SecretStore.declared_redactor()` was added in this unit and is **never
  called and never tested**; `helpers._declared_credential_redactor()` is the one actually
  wired in. Two implementations of one concept; `doctor` misses it because the names differ.
- **AT-085 (medium)** — the container's uvicorn runs without `--reload`, and
  `env_editor.py` (mtime 08:56:53) postdated the server start (08:55:02). The app was serving
  a **mix** of old and new modules, and the live route really did still mangle
  (`PROBE_Q=fake #value 'x' ` written unquoted, read back as `fake`) while a direct call to
  the same function quoted correctly. The manifest's cycle-2 live AT-082 evidence therefore
  cannot have come from the route in that state. Cycle 1's instructions did say
  `docker compose restart autotester`; the cycle-2 section dropped it. I restarted and
  re-derived every live result above afterwards.

## Cleanup performed

- Every probe project deleted: `probe-scratch`, `probe-life`, `probe-life2`, `probe-fresh`,
  `probe-xss`. `projects/` holds exactly `erp`, `pathlynks`, `regression-demo`, `vidysea-erp`.
- One probe wrote a real `GEMINI_API_KEY` into `projects/vidysea-erp/project.json` — that 200
  **is** the AT-083 finding. Reverted immediately with `git checkout --`; the file is back to
  its committed content, confirmed by re-reading it.
- **No real value was ever written into the repo-root `.env`.** The two probes that used that
  route wrote a *fake* value under a throwaway key, and `.env` was restored **byte-identical**
  afterwards (verified `read_bytes() == before`), with no `PROBE_*` key remaining.
- Full repo re-scan for every `.env` value outside `.env` itself: the only hits are the
  non-secret `PATHLYNKS_*_LOGIN_URL` and, inside `profiles/` browser state, the pathlynks
  email. `profiles/`, `.work/` and `**/.env` are all confirmed gitignored and nothing under
  `profiles/` is tracked. No contamination from my probes remains anywhere.
- `projects/pathlynks/project.json` shows as modified in `git status`; the diff is
  **line-endings only** (LF→CRLF) and it was already in that state before this check.

## Release note for the operator

Typing the real ERP email and password at `http://localhost:8010/projects/erp/env` is **safe
now**. That route is U3-clean (the value is never rendered or echoed back, only "Set"/"Not
set"), AT-082-verified end to end so a password with a space, a `#` or a quote is stored
exactly as typed, and `.env` is gitignored. `ERP_EMAIL` and `ERP_PASSWORD` are declared
`SecretRef`s on the `erp` project with `mask_in_screenshot: true` and scoped to
`vidysea.com`, so once entered they are covered by the input guard everywhere and masked in
screenshots; `erp` is `write_policy: read_only`. Two things to avoid: (1) a password
containing **both** a single and a double quote will be refused — pick another or edit `.env`
directly; (2) do **not** paste a model-provider API key (Gemini / Anthropic) into a project
name, a secret description, or any case box — AT-083 means those are not refused and the
file is public. Only the *declared* ERP and Pathlynks credentials are guarded there.

## Source commit

Not committed by this checker — the AT-055 rule applies on PASS, and this is a FAIL. The
maker's working tree is untouched by me; only `qa/verdicts/` and `qa/issues.jsonl` were
written.

---
---

# Superseded — cycle 1 verdict, retained verbatim below

# Verdict — ui-credential-guard-project-routes

**Date:** 2026-09-07
**Contract:** qa/contracts/ui.md (U1–U8)
**Manifest:** qa/manifests/ui-credential-guard-project-routes.md
**Cycle checked: 1**
**Mode:** A (unit check), bound to `d:/autoTesting`. Treated as a **release gate**: the operator is
about to type real ERP credentials into the running app.

```
VERDICT: FAIL
SCOREBOARD: 7/8 criteria met, invariants: no U-invariant list in this contract
FAILURES:
- [U7] sev: high · a no-op save of the existing `pathlynks` project's own stored
  base_url now returns 400 — the guard this unit added to POST /projects/{slug}/edit
  refuses the project's own unmodified data, and the remedy the message names
  ({{SECRET:KEY}} in a step's Value box) cannot be applied to a base URL, so the
  project is uneditable through the UI with no expressible fix · gate the guard on
  DECLARED secret values (or exempt a value that is also a legitimate URL/host) before
  extending it to project.json routes; i.e. fix AT-076 first, then re-land this ·
  issue: AT-078
ISSUES-WRITTEN: AT-078, AT-079, AT-080, AT-081, AT-082 (and AT-074, AT-075, AT-077 → fixed;
  AT-073 annotated PARTIAL, stays open)
EXPLANATION: The guard genuinely works — every one of the six newly guarded fields refused
the real credential live, AT-074's two named encodings and AT-075's two raw echoes are
closed, and the concatenation refusal now names fields. But the unit extended a control
that was already known to be broken (AT-076, open, deliberately not fixed here) onto the
routes that write project.json, and that broke a real project on disk: `pathlynks` can no
longer be saved from its own settings form, and a project whose base_url is the Pathlynks
login URL can no longer be onboarded at all. That is the same dead-end U7 and AT-058 exist
to prevent, re-created on a new route. AT-073 is also not fully closed — `slug` on
/onboard and `key` on /secrets still write unguarded user text into git-tracked
project.json.
```

---

## What I re-ran (all inside the container; nothing trusted from the manifest)

| Command | My result | Manifest claim | Match |
|---|---|---|---|
| `docker compose exec -T autotester uv run pytest` | `355 passed, 1 skipped` | "356 tests, 0 failures" | yes |
| `… pytest -q tests/test_ui_credential_safety.py tests/test_ui_credential_safety_project.py` | `21 passed` | 21 passed | yes |
| `… uv run ruff check src tests scripts` | `All checks passed!` | same | yes |
| `… uv run autotester doctor` | `doctor: clean` | same | yes |
| Live HTTP probes against the running app (`http://localhost:8000` in-container) | see below | see below | mostly — one contradiction |

Live probes were driven by four scripts I wrote myself (`.work/checker-cred-routes/probe*.py`,
gitignored), reading the real `PATHLYNKS_USER_PASSWORD` / `PATHLYNKS_USER_LOGIN_URL` out of
`/app/.env` at run time and never printing them. Every probe response was additionally scanned
for the raw value before being displayed.

---

## 1. Are AT-073 / 074 / 075 / 077 genuinely closed?

**AT-073 — partially. Four of six doors are shut; two are still open.**

All six fields the manifest claims, probed with the real credential:

```
onboard   name             -> 400 "the name looks like it contains a real credential…"
onboard   base_url         -> 400 "the base URL looks like…"
onboard   allowed_domains  -> 400 "allowed domains looks like…"
edit      name             -> 400 "the name looks like…"
secrets   description      -> 400 "the description looks like…"
secrets   domains (scope)  -> 400 "the scope looks like…"
```

Nothing was written on any refusal (`projects/` still held exactly `erp, pathlynks,
regression-demo, vidysea-erp`, and a byte-grep of every file under `projects/` for the credential
returned zero hits).

But **AT-073's own text is "routes that write a raw .env value into git-tracked project.json"**,
and two such fields were not guarded:

- **`slug` on `POST /onboard`** (AT-079, medium). It is written into `project.json`, becomes the
  *directory name*, the URL of every page, and the text on the home index. My probe returned 400 —
  but from `_SLUG_RE`, not from the guard (that particular password is not lowercase-alphanumeric).
  A password matching `^[a-z][a-z0-9-]*$` — an entirely ordinary password shape — passes. Filed on
  code evidence, honestly labelled as not reproducible with the current `.env`.
- **`key` on `POST /projects/{slug}/secrets`** (AT-080, medium). This is the *first* box on the
  form; the maker guarded the box next to it and not this one. An uppercase-alphanumeric secret (a
  common API-token shape) satisfies `SecretRef`'s `^[A-Z][A-Z0-9_]*$` and is written verbatim. My
  probe's 400 came from that pattern validator, not from a guard.

**AT-074 — closed as written.** Both forms AT-074 names are refused (see §2).
**AT-075 — closed.** With the real credential in `case_class` and in `step_action`, the 400 bodies
were `"that is not one of the offered kinds of check"` and `"that is not one of the offered step
actions"` — no echo, verified by scanning the response bodies for the value.
**AT-077 — closed.** The straddle probe returned
`"a real credential appears to be split across a Target box, a Value box, an Expect box, the title"`.
Field-*type* granularity, not per-row — a 5-row form still leaves the user guessing which row, but
the user now knows which kind of box, which is what AT-077 asked for.

---

## 2. Does `_credential_variants` actually close AT-074? Where is the boundary?

Probed live through `POST /projects/<scratch>/cases`, one form per variant, real credential:

| Variant | Result |
|---|---|
| literal | **400 refused** |
| URL-encoded (`quote_plus`) | **400 refused** |
| whitespace-split (space) | **400 refused** |
| whitespace-split (tab) | **400 refused** |
| whitespace-split (CRLF) | **400 refused** |
| double URL-encoded | 303 — **written to disk** |
| uppercased | 303 — **written to disk** |
| base64 | 303 — **written to disk** |
| split by an inserted `<b>` tag | 303 — **written to disk** |

Two rows in my first probe pass looked like coverage and are **not**: this `.env` value is already
all-lowercase and contains no HTML-special characters, so "lowercased" and "html-escaped" are
byte-identical to the literal. I re-derived the value's properties (`islower`, `html.escape`
identity) rather than reporting those as caught.

**Honest statement of the boundary:** the control is a substring test over exactly four
strings — literal, one `unquote_plus`, whitespace-stripped, and both. It is one decode deep and
case-sensitive. AT-074 named URL-encoding and whitespace-splitting; both are closed, so the issue
is genuinely fixed. It is **not** an encoding-proof control, and the manifest reads as if it
were. Recorded as **AT-081 (low)** — not a FAIL: no substring guard can cover arbitrary encodings,
and the durable control is the declared-`SecretRef` + placeholder path, not recognition.

---

## 3. False-positive surface — this is where the unit breaks

`SecretStore.redactor()` returns `Redactor(self._all_values())`, i.e. **declared ∪ shadow** — every
non-empty value in the shared repo-root `.env`, including other projects' keys and keys that are
not secrets at all. This repo's `.env` holds `PATHLYNKS_USER_LOGIN_URL` and
`PATHLYNKS_COUNSELLOR_LOGIN_URL`, both ordinary URLs. Matching now runs over 4 variants × every
field × plus the concatenation, on the routes that write `project.json`.

Measured consequences:

```
POST /projects/pathlynks/edit   (its OWN stored name/base_url/domains, unchanged)  -> 400
POST /onboard  base_url = PATHLYNKS_USER_LOGIN_URL                                 -> 400
POST /projects/<p>/cases  navigate target = PATHLYNKS_USER_LOGIN_URL               -> 400
POST /projects/<p>/cases  value          = PATHLYNKS_USER_LOGIN_URL                -> 400
```

The first line is the failure. I read each on-disk project's `project.json` and posted its own
values straight back:

```
checkprobe       no-op edit -> 303
erp              no-op edit -> 303
pathlynks        no-op edit -> 400   env-collision=['PATHLYNKS_USER_LOGIN_URL']
regression-demo  no-op edit -> 303
vidysea-erp      no-op edit -> 303
```

**Can a user be left unable to create a legitimate case?** Yes — and worse, unable to *save a
project they already have*. `git diff` confirms the `_refuse_unsafe_submission` call in
`routes_project_edit.edit_project_submit` is new in this unit, so before it that same POST
returned 303. The root cause is the already-open **AT-076**, which this unit explicitly chose not
to fix; extending the broken control to a new, higher-value surface is what turned a known
annoyance into a bricked project. Filed as **AT-078 (high)** and the basis of the FAIL.

**Is the error actionable now that it names a field?** Better, but not on this path. The message
says *"Declare it in Project settings and use `{{SECRET:KEY}}` in a step's Value box — note that
only a Value is substituted, not a URL or a title."* On the project-settings form there is no
Value box and no step; the sentence correctly warns the advice does not apply, and then offers no
alternative. The user is told what will not work and nothing that will. The message is now
*honest* (an improvement over the previous cycle) but for a project-route refusal it is
**unactionable**.

---

## 4. The throwaway `Project` in the onboard guard — is it sound?

Verified by probe, not by reading. `onboard_submit` builds
`Project(slug=slug, name=slug, base_url=…, allowed_domains=…)` with **no `secrets`**, then
`SecretStore.load(that, ProjectPaths(slug).env_file, strict=False)`.

- `ProjectPaths.env_file` is `repo_root()/.env` — the shared file, **not** `projects/<slug>/.env`.
  So it exists even though the project does not yet.
- `SecretStore.load` splits parsed keys into `usable` (declared) and `shadow` (undeclared). With
  zero declarations, **every** `.env` value lands in `shadow`.
- `redactor()` uses `_all_values()` = `shadow | usable`.

So the guard does work at onboarding — in fact it is the **broadest** possible form of it, matching
against all nine `.env` keys including non-secrets. Confirmed live: `onboard name = real password`
→ 400, and `onboard base_url = real login URL` → 400 (the same breadth that produced the AT-078
regression). `strict=False` is required and present — `strict=True` would raise `MissingSecret`
here for any project declaring a key with no value. The construction is sound; its breadth is the
problem, not its shape.

---

## 5. Regression

| Check | Result |
|---|---|
| Ordinary onboarding (clean values) | 303, `project.json` written, re-loadable via `ProjectStore.load_project` |
| U7 subdomain still onboards (`sub.example.com` under `example.com`) | 303 — validator has not drifted stricter |
| U7 host outside domains refused | 400 |
| Project rename (edit) preserves `secrets` / `write_policy` | yes — `['PROBE_KEY']`, `read_only` after edit |
| Secret declaration | 303, written to `project.json::secrets` |
| Case creation (ordinary case, no credentials) | 303 |
| Case creation with `{{SECRET:ERP_EMAIL}}` / `{{SECRET:ERP_PASSWORD}}` on `erp` | 303 — **the operator's real next flow works** |
| Case with an undeclared placeholder | 400, names the key |
| Case rename (clean title / credential title) | 303 / 400 |
| All 5 GETs on all 4 projects (detail, edit, cases, cases/new, env) | 200 |
| Home + `/settings/providers` | 200 |
| **`pathlynks` no-op edit** | **400 — REGRESSION (AT-078)** |
| `projects/erp/project.json` md5 | `fa42702d…` unchanged |
| `projects/erp/cases.jsonl` md5 | `15ec4cad…` unchanged, 2 cases, 2 SecretRefs intact |

---

## 6. Complete inventory of write paths (the asked-for deliverable)

Every route under `src/autotester/ui/` that writes user-supplied text to a file under `projects/`
or to `.env`:

| Route | Field | Writes to | Guarded? |
|---|---|---|---|
| `POST /onboard` | `name` | `projects/<slug>/project.json` | **yes** (verified 400) |
| `POST /onboard` | `base_url` | project.json | **yes** (verified 400) — but over-fires, AT-078 |
| `POST /onboard` | `allowed_domains` | project.json | **yes** (verified 400) |
| `POST /onboard` | **`slug`** | project.json **+ directory name + every URL + home index** | **NO** — AT-079 |
| `POST /projects/{slug}/edit` | `name` | project.json | **yes** (verified 400) |
| `POST /projects/{slug}/edit` | `base_url` | project.json | **yes** — but over-fires, AT-078 |
| `POST /projects/{slug}/edit` | `allowed_domains` | project.json | **yes** |
| `POST /projects/{slug}/secrets` | **`key`** | project.json `secrets[].key` | **NO** — AT-080 |
| `POST /projects/{slug}/secrets` | `description` | project.json | **yes** (verified 400) |
| `POST /projects/{slug}/secrets` | `domains` | project.json | **yes** (verified 400) |
| `POST /projects/{slug}/secrets/{key}/delete` | path `key` | project.json (removal only) | n/a — writes no new text |
| `POST /projects/{slug}/cases` | `title` | `cases.jsonl` | **yes** (U8, re-verified) |
| `POST /projects/{slug}/cases` | `step_target` ×5 | cases.jsonl | **yes** (re-verified) |
| `POST /projects/{slug}/cases` | `step_value` ×5 | cases.jsonl | **yes** (re-verified) |
| `POST /projects/{slug}/cases` | `step_expected` ×5 | cases.jsonl | **yes** (re-verified) |
| `POST /projects/{slug}/cases` | all of the above, concatenated | cases.jsonl | **yes** (re-verified, names fields) |
| `POST /projects/{slug}/cases` | `case_class`, `step_action` | cases.jsonl | n/a — closed enums, parsed before write, no echo (AT-075 fixed) |
| `POST /projects/{slug}/cases/{id}/rename` | `title` | cases.jsonl | **yes** (verified 400) |
| `POST /projects/{slug}/cases/{id}/delete` | — | cases.jsonl | n/a |
| `POST /projects/{slug}/env` | `value` | repo-root `.env` | **by design** — key must be a declared `SecretRef` of this project (400 otherwise, verified); value refused only if it contains `\n`/`\r` (verified). Nothing checks a *wrong* value for a *right* key, and nothing can — see AT-082 |
| `POST /projects/{slug}/env` | `key` | `.env` | closed to the project's declared refs (verified: `NOPE` → 400) |
| `POST /settings/providers` | `key` | `.env` | closed 6-key allowlist (verified: `NOT_A_KEY` → 400) |
| `POST /settings/providers` | `value` | `.env` | newline injection refused (verified: `x\ny=1` → 400 "value must not contain a newline"). Unguarded otherwise — correct, it *is* the value |
| `POST /projects/{slug}/run` | — | `projects/<slug>/runs/…` (gitignored) | n/a — takes no user text |

**On the credentials page specifically** (the one that writes a value by design): what stops the
wrong key/value pair is that the key must be one this project declared; what stops a newline is
`env_editor.set_env_value`'s explicit `\n`/`\r` refusal, which I re-verified. What stops *nothing*
is a value the `.env` reader will silently rewrite — I round-tripped values through the production
`set_env_value` → `parse_env` pair in a temp file and found `'pa ss #word'` → `'pa ss'`,
`'p@ss #1'` → `'p@ss'`, `'end '` → `'end'`, `'"quoted"pw'` → `'quoted'`, all while the page still
renders "● Set". Pre-existing, not this unit's doing, but it sits directly on the path the
operator is about to walk. Filed as **AT-082 (medium)**.

---

## Criterion-by-criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| U1 onboarding creates a real CLI-compatible project | **met** | clean onboard 303; `project.json` on disk; `ProjectStore.load_project` returns it with `write_policy=read_only`; no UI-only representation added |
| U2 live state, unknown slug 404 | **met** | `/projects/nosuchproject` 404, `/edit` 404, `POST …/cases` 404; no caching added |
| U3 env editor never renders a value | **met** | untouched by this unit (no diff); `GET /projects/pathlynks/env` and `/` scanned against all 9 `.env` values → no hit |
| U4 run/report read persisted evidence | **met** | no diff in `routes_report.py` / `routes_runs.py` / `execute.py` / `grade.py` |
| U5 HTML-escaping | **met** | no escaping changed; new refusals are FastAPI JSON `detail`, not HTML; AT-075 removed the two raw echoes |
| U6 case creation + its five refusals | **met** | blank title 400, zero steps 400, unknown class 400, unknown action 400, unknown project 404, valid case 303 |
| U7 no project creatable/editable into an unrunnable state | **FAIL** | `_require_reachable_base_url` is byte-unchanged and its composition clause still holds (subdomain 303, outside-host 400) — but the new guard on the same route refuses `pathlynks`'s own stored data (400) with no expressible remedy, which is the outcome this criterion exists to prevent. Called plainly: the *literal composition clause* passes; the criterion's *purpose*, on its own route, does not |
| U8 case form cannot commit a raw credential | **met** | title / target / value / expect each 400; concatenation 400 naming fields; nothing written; `grade.py::guard_prompt` path unchanged |

---

## Answer to the question actually being gated

**Is it safe to type real ERP credentials into the running app?** For the credential-entry route
itself, yes: `POST /projects/erp/env` writes only to the repo-root `.env` (gitignored, opened
`0o600`), never echoes the value, and the page shows only set/not-set — I scanned the rendered
page and the home index against every `.env` value and found none. `erp` already declares
`ERP_EMAIL` and `ERP_PASSWORD`, and a case using `{{SECRET:ERP_EMAIL}}` / `{{SECRET:ERP_PASSWORD}}`
is accepted (303) while an undeclared placeholder is refused — the intended flow works end to end.

Two things to know before doing it:

1. If the password contains ` #`, a leading/trailing space, or starts with a quote, it will be
   stored as a **different** value with no warning and the login will fail for reasons the UI will
   not explain (AT-082).
2. The moment those two values exist in `.env`, **any** UI text that literally contains them is
   refused everywhere — including project names, base URLs and navigate targets. That is the same
   mechanism that just bricked `pathlynks`. If `ERP_EMAIL` is a plain address it is unlikely to
   collide; a short or word-like value would be a problem (AT-072, still open).

---

## Not counted against this unit

- **AT-076** (medium, open) — deliberately out of scope per the manifest, and the manifest is
  right that making `goto` resolve placeholders is a security decision, not a ride-along. But
  AT-076 is the *root cause* of the AT-078 regression, so it is now blocking: the guard cannot
  safely stay on the project routes until it is fixed.
- **AT-072** (low, open) — no minimum length on `is_clean`. Correctly deferred.
- The 4 tests' pass, ruff and doctor results all reproduced exactly as claimed. The maker's
  reporting was accurate about what it did; the gap is in what it did not check.

## Fix direction for cycle 2

Smallest change that closes the FAIL and the two open AT-073 halves, in one unit:

1. Build the guard's `SecretStore` from **declared** values on the project routes (or exempt any
   `.env` value that parses as a URL/host, which is what a non-secret `LOGIN_URL` is), so
   `pathlynks` saves again. Re-verify by re-running the no-op-edit sweep over all four projects —
   all must return 303.
2. Add `('the project id', slug)` to `onboard_submit`'s `_refuse_unsafe_submission` call.
3. Add `('the key', key)` to `declare_secret`'s call, before `SecretRef(...)`.
4. Give the project-route refusal a remedy sentence that applies to a project route (there is no
   Value box on that form).

---

*Checked by /checker, Mode A, fresh context, bound to `d:/autoTesting`. Probes:
`.work/checker-cred-routes/probe.py`, `probe2.py`, `probe3.py`, `probe4.py`, `cleanup.py`
(gitignored). Cleanup performed and verified: no probe value was written to the repo-root `.env`
(key set and value lengths identical before and after); every scratch project (`checkprobe*`) was
deleted; the one case my probe added to `projects/erp` was removed through the UI's own delete
route and both `erp` files are byte-identical to their pre-check md5s (2 cases, 2 SecretRefs); a
byte-grep of every file under `projects/` for the real credential returns nothing.*

*Maker source was **NOT** committed by this checker — the AT-055 rule applies on PASS, and this is
a FAIL. `src/autotester/ui/*`, `tests/test_ui_credential_safety*.py` and the manifest remain
uncommitted in the working tree for the maker's cycle-2 fix.*
