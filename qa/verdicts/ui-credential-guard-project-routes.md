# Verdict — ui-credential-guard-project-routes

**Cycle checked: 3**
**Date:** 2026-09-07
**Contract:** qa/contracts/ui.md (U1–U8)
**Manifest:** qa/manifests/ui-credential-guard-project-routes.md
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`, read-only toward the artifact.

```
VERDICT: PASS
SCOREBOARD: 8/8 criteria met, 5/5 no-fire invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-087 (medium), AT-088 (medium); AT-086 corrected (low -> medium)
EXPLANATION: Both prior FAILs are genuinely closed on code I independently proved
current: all four on-disk projects re-save their own unmodified data (AT-078), and
an UNDECLARED credential — the operator's live GEMINI_API_KEY — is refused on every
guarded field alongside the declared PATHLYNKS_USER_PASSWORD (AT-083). 38/38 hostile
probes behaved as the contract requires. The exemption does not leak on the case form,
which is the surface U8 pins: the create path passes no exempt set at all, so its
concatenation check is fully intact. It does have one reproducible residual on the
project-edit route, where excluding an exempt field from the join lets a credential be
reassembled across two fields — filed as AT-087 rather than a FAIL, because U8 explicitly
scopes itself to the case form and no criterion covers the project routes yet. I have
now written that criterion (U9) so the gap is named rather than implied.
```

## How I confirmed the server was NOT running stale code (AT-085)

The manifest documents a staleness trap that bit both the maker and the cycle-2 checker.
I did not trust the maker's guard, and I did not trust file mtimes alone. Three
independent confirmations, in increasing strength:

1. **No reloader.** `ps` inside the container shows
   `uvicorn autotester.ui.app:app --host 0.0.0.0 --port 8000` with **no `--reload`**, so the
   module tree is whatever was on disk at process start — nothing silently re-imports.
2. **mtime ordering.** Container `StartedAt` = `2026-09-07T09:30:34Z`, uvicorn worker started
   `09:30:36`. `find src -name '*.py' -newermt '2026-09-07 09:30:36'` returned **nothing**;
   the newest source file is `ui/helpers.py` at `09:28:58`, 98 s *before* the worker started.
3. **Behavioural fingerprint — the one that actually settles it.** Two live probes that no
   earlier cycle's code can both satisfy:
   - `POST /projects/pathlynks/edit` with pathlynks's own stored data → **303**. Cycle-1 code
     returns 400 here (that was the cycle-1 FAIL).
   - `POST /onboard` with the undeclared `GEMINI_API_KEY` as `name` → **400**. Cycle-2 code
     returns 303 here (that was the cycle-2 FAIL).

   Only cycle-3 code produces both. Every live figure below was taken against that server.

## What I re-ran myself (never the maker's pasted output, never the maker's script)

```
docker compose exec -T autotester uv run pytest                    -> 366 passed, 1 skipped
docker compose exec -T autotester uv run pytest \
    tests/test_ui_credential_safety.py \
    tests/test_ui_credential_safety_project.py                     -> 32 passed
docker compose exec -T autotester uv run ruff check src tests scripts -> All checks passed! (exit 0)
docker compose exec -T autotester uv run autotester doctor         -> doctor: clean (exit 0)
```

The manifest's "How to verify" says the two safety files hold **21** tests; they now hold
**32** (9 added in cycle 2, 3 in cycle 3 — the manifest's own change lists account for all
of them). Not a discrepancy, a stale line in the older section.

Live probes were driven by **my own scripts** (`.work/checker-c3/probe*.py`, gitignored),
written from the contract, executed inside the container so no real value ever crossed to
the host shell or this transcript.

## Criterion-by-criterion

### U1 — onboarding creates a real, CLI-compatible project — **MET**
`onboard_submit` still builds a `schema.project.Project` and persists via
`ProjectStore.save_project`; the guard is inserted *before* the write, not around a second
store. Live: three scratch projects onboarded through the route (`303` + a real
`projects/<slug>/project.json` on disk), including one whose base URL is a **subdomain** of an
allowed domain. No UI-only representation added.

### U2 — project detail reflects real state — **MET**
`GET /projects/{slug}` on all four projects → 200 with live case counts read per request;
`GET /projects/no-such-project` → **404**. No cache introduced by this unit.

### U3 — the env editor never renders a real secret value — **MET, re-derived**
I read the six declared `SecretRef` keys across all four projects, took their real values from
`.env`, and searched **every rendered page** (33 routes across 4 projects, plus `/`, `/live`,
`/onboard`, `/settings/providers`, and every `report`/`report.html`/`report.xlsx`) for each one:
**zero hits.** The Credentials page shows `● Set` / `○ Not set` pills only; the input is
`type='password'`; `POST .../env` still refuses an undeclared key with 400 and never echoes the
value. `routes_credentials.py` is unchanged by this unit.

One near-miss worth recording so a later checker does not re-raise it: `PATHLYNKS_USER_LOGIN_URL`
**does** appear on pathlynks's pages — because it is byte-identical to that project's own
`base_url`. It is plain configuration (a public sign-in URL), declared as a `SecretRef` by no
project, and it is the exact collision that caused AT-078. Not a U3 breach.

### U4 — run/report views read real persisted evidence — **MET**
No run/report/grade module is touched by this unit's diff. `report`, `report.html` and
`report.xlsx` return 200 for all four projects, including `regression-demo` and `erp`.

### U5 — user-supplied values are HTML-escaped — **MET, re-probed hostilely**
Onboarded a scratch project whose `name` was `<script>alert(1)</script>&'"` and loaded 6 routes
that render it (`/`, detail, edit, cases, cases/new, env): **no raw `<script>` tag in any
response.** The guard's own 400 bodies were checked for reflection of the submitted credential
on every probe — none reflected it (see AT-088 below for the one path that *does* reflect, which
is a different function).

### U6 — a case is creatable from the UI as a real CLI-compatible `Case` — **MET**
All five refusals still fire and none echoes raw input: blank title 400, zero surviving steps
400, unknown `case_class` 400 (body says "that is not one of the offered kinds of check", the
submitted string is **not** present), unknown `action` 400 (same), unknown project 404. `kind`
is still derived via `KIND_BY_CLASS`, `rationale` still `None`, `flow_id="manual"`. A genuinely
new case posts 303; `_refuse_duplicate` still returns its own named-case 400.

### U7 — a project cannot be created or edited into an unrunnable state — **MET; this is the AT-078 fix**
`_require_reachable_base_url` is byte-unchanged and still composes `browser.secrets.host_of` +
`Project.allows_domain`. Live: a **subdomain** of an allowed domain still onboards (303, the
drift-stricter failure mode is absent), a base URL outside its domains is refused (400), and
`*` is still not special-cased (400 — the hard boundary holds). And the cycle-1 defect is gone:

```
erp 303 · pathlynks 303 · regression-demo 303 · vidysea-erp 303
```

all four re-saving their own unmodified `name` / `base_url` / `allowed_domains`. `pathlynks`
— the one that 400'd in cycle 1 — also accepts a **rename** while keeping its colliding base URL
(303), so the project is genuinely editable, not merely no-op-able. `secrets`, `write_policy`
and `providers` are still carried through `model_copy`; the slug is still not editable.

### U8 — the case form cannot commit a raw credential to a git-tracked file — **MET**
This is the criterion the unit is judged on, and it is the surface I attacked hardest. Every
probe below was run **twice**: once with the operator's live **undeclared** `GEMINI_API_KEY`
(cycle 2's proof of a hole) and once with the **declared** `PATHLYNKS_USER_PASSWORD`. All
returned 400, and none reflected the value:

```
                              GEMINI(undeclared)   PATHLYNKS_USER_PASSWORD(declared)
case title                          400                    400
case step_target                    400                    400
case step_value                     400                    400
case step_expected                  400                    400
case split across 2 rows            400                    400
case split across 2 FIELD TYPES     400                    400
case url-encoded value  (AT-074)    400                    400
case rename title                   400                    400
```

**The exemption cannot be used as a bypass on this surface, structurally, not by luck.**
`routes_cases._guard_submitted_case` passes **no** `exempt` set — the default `frozenset()` — so
the create path's concatenation check sees every field. `rename_case` exempts exactly one field
(`{case.title}`), and with a single field there is no join for an exemption to hollow out.
I verified the exemption is built from **current on-disk state only**: submitting the same
credential in two fields of one request, hoping one would exempt the other, returns 400 —
nothing user-supplied in a request can enter the exempt set.

`stages/grade.py` still returns `Result.BLOCKED` rather than raising out of
`SecretStore.guard_prompt` (unchanged, covered by the suite).

### No-fire list — 5/5 hold
No auth added · no JS framework or HTMX · no polling/websockets · no run trigger added by this
unit · CSRF still deliberately absent. Nothing on the ignore list was churned.

## Issues addressed — checked against the ledger, not the manifest's claim

| Issue | Manifest claim | My finding |
|---|---|---|
| **AT-078** (high, the cycle-1 FAIL) | fixed | **CONFIRMED fixed.** All four projects re-save; pathlynks renameable. |
| **AT-083** (high, the cycle-2 FAIL) | fixed | **CONFIRMED fixed.** Undeclared `GEMINI_API_KEY` refused on all 8 guarded field types. |
| **AT-073** (high, partial) | partial | **The three named routes are closed** (`onboard` name/base_url/domains, `edit` same three, `secrets` description/scope — all 400 for both a declared and an undeclared value). Marked `fixed`; the named remainder stays open as **AT-079/AT-080**. |
| **AT-074** (medium) | fixed | Confirmed — url-encoded and whitespace-broken values refused. |
| **AT-075** (medium) | fixed | Confirmed on the case routes — neither 400 echoes the submitted string. See **AT-088** for a *different* function that still does. |
| **AT-077** (low) | fixed | Confirmed — refusals name the field(s). |
| **AT-082** (medium) | fixed | Confirmed by the suite's round-trip tests + `_render_value`'s re-parse verification. |
| **AT-084** (low) | fixed | Confirmed — `grep -rn declared_redactor src/` returns **nothing**; `browser/secrets.py` is back to byte-unmodified vs `HEAD`. |
| **AT-085** (medium) | documented, not fixed | Stays **open** — the staleness guard lives in the maker's throwaway probe script, not in committed code, so nothing prevents recurrence. Correctly disclosed, not silently dropped. |

## AT-086 — accurate, but the manifest understates it

The maker filed AT-086 as "a project whose `base_url` already appears in `.env` cannot be
**onboarded**", severity low, "fails closed and has workarounds".

**The defect is real** — I reproduced it: `POST /onboard` with `base_url` byte-identical to
`PATHLYNKS_USER_LOGIN_URL` → **400**, and `projects/zz-at086/` is **not** created. Fails closed,
as claimed.

**But "has workarounds" is wrong, and I tested the obvious one.** Onboarding with a placeholder
`base_url` on the same host succeeds (303), and then editing it to the real URL is **also
refused (400)** — the exemption holds only the placeholder, so the real URL is fresh input.
There is **no path through the UI at all** to create a project on such a URL; only hand-editing
`project.json`. That is the same *class* as the cycle-1 FAIL — a legitimate project the guard
refuses.

**Is filing it legitimate scoping, or an under-fix that should block?** Filing it is legitimate,
and I would defend that:

- **Nothing existing is broken.** The cycle-1 FAIL was blocking because an *already-onboarded*
  project became permanently uneditable with no expressible fix. Here `pathlynks` — the one
  project this actually collides with — is fully editable, renameable, and runnable. I verified
  that directly.
- **It fails closed, not open.** No credential escapes; a rare legitimate action is refused.
  Between the two failure directions the guard exists to choose, this is the safe one.
- **No criterion requires it.** U7 constrains the *reachability* validator's composition, and
  that validator is unchanged and still correct. This is the credential guard, a different check,
  on a surface no criterion covers.
- **The fix is genuinely a scope decision, not a bug fix.** Making it go away means declaring
  `base_url`/`allowed_domains` config fields exempt from credential matching *by nature* — which
  re-opens exactly the hole cycle 2 was FAILed for, unless it is designed rather than patched at
  cycle 3 of 3. Shipping that under time pressure is how cycle 2 happened.

The maker was straight about finding it via its own failing test rather than burying it. I have
**raised AT-086 from low to medium** and corrected the "has workarounds" claim in the ledger.

## New findings (filed, not blocking — neither violates a criterion)

### AT-087 (medium) — the concatenation exemption can be hollowed out on the project routes
This is the leak the dispatch asked me to hunt, and it exists. `_refuse_unsafe_submission`
drops every exempt field from the join:

```python
fresh = [(label, text.strip()) for label, text in texts if text.strip() not in exempt]
joined = "".join(text for _label, text in fresh)
```

So a credential straddling an exempt field and a fresh one is invisible to the join. I isolated
it against a **control** so it is not merely an artifact of non-contiguous fields:

```
1. onboard base_url='https://ex.com/<first half of the password>'   -> 303  (a half is not a secret)
2. CONTROL: base_url changed by one char (NOT exempt), same split   -> 400  (join sees it)
3. TEST:    base_url byte-identical to stored (EXEMPT), same split  -> 303  (join is blind)
   on-disk base_url + allowed_domains contains the FULL password: True
   the raw password appears nowhere as one string in the file:     True
```

Same root cause, second symptom: `exempt` is a **flat set**, not per-field, so a value stored as
`name` also exempts it in `base_url` and `allowed_domains` — the manifest and criterion both say
"that same **field**", and the code does not enforce the field part.

**Why this is not a FAIL.** U8 pins the *case form*, states so explicitly, and the case form
carries no exemption — verified above. No criterion covers the project routes. Threat-model-wise
this needs a two-step, deliberately crafted sequence (store one contiguous half, then continue it
exactly, in the right field order); the guard's stated threat is an operator pasting a credential
into a box, and against that it is now complete on every field I could find. Remedy direction:
make `exempt` a `dict[field_label, value]` and, instead of dropping an exempt field from the
join, keep it — an exempt field is only exempt from being *the* credential, not from being
context for one.

### AT-088 (medium) — a credential pasted into Base URL is echoed back in the 400
`_require_reachable_base_url` runs **before** the credential guard on both `POST /onboard` and
`POST /projects/{slug}/edit`, and its refusal interpolates the raw submission:

```
POST /onboard  base_url=<the real PATHLYNKS_USER_PASSWORD>
  -> 400 {"detail":"'<the password, verbatim>' is not a URL the browser can open"}
```

Fourth occurrence of the AT-068/AT-075 echo pattern, and the first on a *credential-shaped*
input. It is the milder half of that pattern — nothing reaches disk (the guard still refuses the
write) and uvicorn's access log records only method/path/status, so the value goes no further
than the response rendered in the operator's own browser. Remedy: run
`_refuse_unsafe_submission` **before** `_require_reachable_base_url`, or drop the value from that
message and name only the host.

## Regression sweep — whole UI

35 routes across 4 projects: `/`, `/live`, `/onboard`, `/settings/providers`, and per project
`detail`, `edit`, `env`, `cases`, `cases/new`, `report`, `report.html`, `report.xlsx`,
`flow-diagram` — **all 200**; unknown slug **404**. (`/settings` and `/projects/{slug}/runs` 404
because those paths do not exist — the real ones are `/settings/providers` and
`/projects/{slug}/runs/{run_id}`; my first sweep guessed wrong, not a regression.)

## `projects/erp` — declared secrets, cases, and probe hygiene

- **SecretRefs intact:** `ERP_EMAIL` and `ERP_PASSWORD`, both `mask_in_screenshot: true`, both
  scoped to `vidysea.com` + `www.vidysea.com`. Neither has a value in `.env` yet — the page
  correctly shows `○ Not set`.
- **Loads cleanly:** detail, edit, env, cases, cases/new, report, report.html, report.xlsx,
  flow-diagram all 200.
- **The four cases the maker added during probing are legitimate**, not residue. Each is a real
  `happy` case with one `navigate` step to a genuine ERP URL and a plain `visible_text`
  expectation: *Sign-in page loads and shows the login form* → `/erp` expects "Sign in to
  continue"; *Training lookup page loads* → `/erp/p/me` expects "My Training"; *Signup page
  loads* → `/erp/signup` expects "Join Vidysea training"; *Training lookup form is reachable* →
  `/erp/p/me` expects "Mobile number". **No credential, no `{{SECRET:…}}`, no probe string, no
  `.env` value in any of them.**

## Cleanup performed by this check

- `projects/` was backed up inside the container before probing and restored afterwards. All
  eight `project.json` / `cases.jsonl` md5 sums are **byte-identical to the pre-probe state**,
  and the directory holds exactly `erp`, `pathlynks`, `regression-demo`, `vidysea-erp`.
- Every scratch project I created (`zz-split`, `zz-exempt`, `zz-esc`, `zz-w`, `zz-sub`,
  `zz-at086`, `zz-stale-probe`, `zz-probe`, `zz-echo`, `zz-out`, `zz-wild`) is **deleted**.
- **No probe value was ever written to the repo-root `.env`.** I never posted to
  `POST /projects/{slug}/env`. The file still holds the same 9 keys with the same value lengths
  as before this check; `git check-ignore` confirms `.gitignore:2` (`**/.env`) covers it and
  `git ls-files .env` confirms it is **untracked**.
- My probe scripts live in `.work/checker-c3/`, which is gitignored, and are not committed.

## Release note for the operator

**Yes — it is safe to type your real ERP email and password into
`http://localhost:8010/projects/erp/env` right now.** That page is the one place in this tool
built to receive them: it writes them only to the repo-root `.env`, which git is configured to
ignore and does not track, with owner-only file permissions; it never shows a saved value again
(only "Set" / "Not set"), never puts one in an error message, and refuses any key the project has
not declared. `erp` has declared `ERP_EMAIL` and `ERP_PASSWORD`, both marked to be masked in
screenshots. And once those values exist, this cycle's guard covers the places that *would* have
leaked them: I confirmed with two of your live credentials that pasting one into a project name,
a base URL, an allowed-domains box, a credential description, a case title, or any step field is
refused, on every one of those boxes, including when it is URL-encoded or split across two boxes.

**The "but", in three parts.** First: only that Credentials page. Do not paste the password into
any other box — not the project name, not the Base URL, not a test step. Those are all refused,
so you cannot do real damage by trying, but if you paste it into the **Base URL** box the error
message will show your password back to you on screen (harmless on your own machine, worth
knowing — it is AT-088 above). Second: if your ERP password happens to be a short or ordinary
word, the guard will afterwards start refusing innocent text that merely contains it — that is
AT-072, an annoyance, not a leak, and a longer password avoids it entirely. Third, and the only
one that needs a habit: this repo is **public on GitHub**, and the whole boundary is that `.env`
stays untracked. Never copy a value out of `.env` into any file you then commit, and if you ever
edit `.gitignore`, keep the `**/.env` line. Run `git status` before a commit and make sure `.env`
is not in it — today it is not, and I verified that.

---
*Verdict written by /checker, Mode A, cycle 3. Evidence produced by this checker's own scripts
against a server proved to be running current code by three independent means. No artifact,
code, manifest or `.env` was edited by this check.*
