# Contract — Web UI (T-100)

**Covers:** goal task T-100. **Owner:** /checker. **Criticality:** HIGH — T-100's own note:
"full onboarding → report without touching the CLI."
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B1-B9 — the credential
boundary this UI's `.env` editor must respect), `execute.md`/`grade.md` (the `RawResult`/`Verdict`
shapes the report/run views read).

## Purpose

A thin FastAPI viewer/editor over the same project files the CLI reads and writes — design
principle 8: "the UI is a viewer/editor over those files, not a second source of truth." Every
route goes through `ProjectStore`/`SecretStore`, never a parallel store.

## Criteria

### U1 — Onboarding creates a real, CLI-compatible project
`POST /onboard` builds a `schema.project.Project` from form fields and persists it via
`ProjectStore.save_project` — the same file (`projects/<slug>/project.json`) and format the CLI
and every stage already read. No UI-only project representation exists.

### U2 — Project detail reflects real state, no caching/duplication
`GET /projects/{slug}` reads the project's actual `FlowSpec` (`review.status`) and case count
live via `ProjectStore` on every request — never a cached or UI-maintained copy. An unknown slug
is a 404, not a silently empty page.

### U3 — The env editor never renders a real secret value
`GET /projects/{slug}/env` shows, per declared `SecretRef`, only whether `.env` currently has a
non-empty value for that key (`"set"`/`"not set"`) — the actual value is never present anywhere
in the rendered HTML. `POST /projects/{slug}/env` writes a new value via
`ui/env_editor.py::set_env_value` (the one legitimate write path to the repo-root `.env`) and
never echoes the submitted value back in its response. Posting a key the project does not declare
is refused (400), never silently written.

### U4 — Run/report views read real persisted evidence, never invent it
`GET /projects/{slug}/runs/{run_id}` and `GET /projects/{slug}/report` read actual
`RawResult`/`Verdict` files via `ProjectStore.load_results`/`load_verdicts` — the outcome/result
values shown are exactly what was persisted by `execute.py`/`grade.py`, not recomputed or
guessed. A project with no runs yet reports that plainly (200 with a "no runs yet" message), not
an error.

### U5 — User-supplied values are HTML-escaped
Every string derived from user input or project data (`name`, `base_url`, slugs, case ids,
outcome/result values) is passed through `html.escape` before being placed in a response —
verified by reading `ui/app.py` in full, not merely tested against one payload.

### U6 — A test case is creatable from the UI, as a real CLI-compatible `Case`
`GET /projects/{slug}/cases/new` renders a plain server-rendered form and
`POST /projects/{slug}/cases` persists the result via `ProjectStore.add_case` as a
genuine `schema.case.Case` in `projects/<slug>/cases.jsonl` — the same file and format
`stages/expand.py` and every stage already read; no UI-only case representation exists.
`kind` is **derived** from `case_class` (`KIND_BY_CLASS`) and is never a form field, so
the two can never disagree. `rationale` is left `None`: it is a *claim*, not provenance
— `stages/run_case_pipeline.default_rubric` feeds it to the grader verbatim as the claim
to judge evidence against (AT-057 cycle, 2026-09-07) — and provenance lives in
`flow_id="manual"`. A blank title, zero surviving steps, an unknown `case_class`, an
unknown `action`, and an unknown project are each **refused (400/400/400/400/404) with
nothing written to disk**. A project with zero cases says so on its detail page and
offers the route to fix it, rather than showing only a disabled Run control.

### U7 — A project cannot be created or edited into a state where it can never run
Every route that writes `project.json` (`POST /onboard`, `POST /projects/{slug}/edit`) first calls
`ui/helpers.py::_require_reachable_base_url`, which **composes the same two functions the real
navigation gate uses** — `browser.secrets.host_of` and `Project.allows_domain`, exactly as
`browser/session.py::check_destination` does — so the validator can never be stricter or looser
than the boundary it guards (a subdomain of an allowed domain must still be accepted). A project
whose own `base_url` host falls outside its `allowed_domains` is refused **400 with the host named**
and **nothing is written to disk**. The edit route is not a back door: it runs the same validator,
refuses a blank name and an empty domain list, and **cannot change the slug** — the slug names the
directory every run, case, rubric and browser profile is already filed under. Editing preserves
every field the form does not offer (`secrets`, `write_policy`, `providers`) — the edit form reads
and writes `project.json` only and touches no `SecretRef` value and no `.env` (U3 boundary).
`allowed_domains` gets **no wildcard**: widening the browser's hard boundary is a decision for the
Approver, not a validation fix, and the user's real intent stays expressible because the refusal
names the exact host to add.

### U8 — The case form cannot commit a raw credential to a git-tracked file
Every user-supplied text of a case — the `title` and every `step_target`, `step_value` and
`step_expected` — passes `ui/helpers.py::_refuse_unsafe_submission` **before any `Case` is
built**, on both doors into a title (`POST /projects/{slug}/cases` and
`POST /projects/{slug}/cases/{case_id}/rename`). A `{{SECRET:KEY}}` placeholder naming an
undeclared key is refused (400); a raw `.env` value in any one of those fields is refused (400);
and their **concatenation** is checked too, so a value split across two or more rows — or across
two different field types — cannot reassemble byte-for-byte in `projects/<slug>/cases.jsonl`,
which is git-tracked in a public repo. Nothing is written to disk on a refusal. A refusal that
reaches the grading prompt anyway (a credential already inside a rubric) yields a
`Result.BLOCKED` `Verdict` naming no value — `stages/grade.py` never raises out of
`SecretStore.guard_prompt`, because crashing every subsequent run leaves no way back.
This criterion pins the *case form only*. The equivalent hole on the three routes that write
`project.json` is **not** covered here and is tracked as **AT-073**.

### U9 — The three routes that write `project.json` cannot commit a raw credential either
`POST /onboard` (`name`, `base_url`, `allowed_domains`), `POST /projects/{slug}/edit` (the same
three) and `POST /projects/{slug}/secrets` (`description`, `domains`) each pass their
user-supplied text through `ui/helpers.py::_refuse_unsafe_submission` **before** `project.json`
is written — the same guard U8 pins on the case form, on the file that a project *name* renders
from on every page including the home index. Matching runs against **every** value in the shared
`.env`, declared as a `SecretRef` or not: an undeclared provider key is still a credential and
this repo is public (AT-083 — scoping input matching to declared values only was a real hole and
is the one thing this criterion must never be softened back to).
The guard must **not** brick a project's own data. A field is exempt **only** when its submitted
text is byte-identical to what is already persisted for that project — data the system itself
stored, never fresh input, and never anything derived from the same request (AT-078: `pathlynks`'s
`base_url` is byte-identical to the non-secret `.env` entry `PATHLYNKS_USER_LOGIN_URL`, and
without this every project whose config collides with a `.env` value became uneditable with no
fix the user could express). Every on-disk project must be able to re-save its own unmodified
`name` / `base_url` / `allowed_domains`, and to be renamed while keeping a colliding base URL.
Two residuals are deliberately **outside** this criterion and tracked instead, because closing
either is a scope decision rather than a bug fix: **AT-087** — exempt fields are excluded from
the *concatenation* check and the exempt set is flat rather than per-field, so a credential
straddling an exempt field and a fresh one is not caught (the case form is unaffected: it passes
no exempt set at all); and **AT-086** — a project whose `base_url` is byte-identical to an `.env`
value cannot be created through the UI at all, by onboarding or by editing a placeholder. Both
fail closed.

## No-fire list

- Authentication/authorization — this is a local, single-operator tool for now (matches the
  plan's "Out of scope v1: multi-tenant SaaS").
- A JS framework or HTMX wiring — plain server-rendered HTML strings for this cycle; the plan
  names HTMX as a future refinement, not required to satisfy this contract.
- Live-updating run views (polling/websockets) — `GET /projects/{slug}/runs/{run_id}` is a
  point-in-time snapshot; "live" in T-100's title is satisfied by reading current persisted state
  on every request, not by push updates.
- Triggering a run or an onboarding video from the UI — this contract covers viewing/editing
  existing project state and creating a bare project record; kicking off `execute.py`/
  `ingest.py` from a UI button is a future enhancement.
- CSRF protection on the POST forms — acceptable for a local single-operator tool; flagged as a
  known gap if this UI is ever exposed beyond localhost.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-100 — no contract existed before this cycle.
- 2026-09-03 · /checker (docker-live-ui unit) · shared-layout invariant: every route in
  `ui/app.py` now returns its HTML fragment wrapped by `ui/theme.py::page(title, body)` — a
  shared nav + stylesheet, visual only. U1-U5 are unaffected: `page()` prepends/wraps the
  caller's already-escaped fragment and never removes, reorders, or unescapes it (verified —
  see `qa/verdicts/docker-live-ui.md` D5). A new presentation-only route, `GET /live` (renders
  an iframe onto the container's noVNC client; no `ProjectStore`/`SecretStore` call, triggers no
  run), now exists alongside U1-U5's routes — covered by `qa/contracts/docker.md` D4, not a U-item
  itself since it reads no project state. Routine, non-weakening; folds the flagged
  `qa/feedback-inbox.md` 2026-09-03 "Docker + live-watch + UI polish" entry.
- 2026-09-07 · /checker (ui-back-nav-and-live-clarity unit) · shared back-navigation invariant:
  every route that is not the home page now builds its trail with
  `ui/theme.py::breadcrumb(*crumbs)` — one helper replacing 8 hand-written
  `<div class='breadcrumb'>` blocks across 5 modules — which renders a real `← Back` anchor
  targeting the **last crumb carrying an href** (the natural parent), plus the same trail as
  before. U5 is unaffected and re-verified: `breadcrumb()` adds no escaping of its own (same
  caller-escaping discipline as `page()`), all 8 call sites pass `escape()`d labels, and every
  href is a literal or `/projects/{escape(slug)}` where the slug is already `_require_slug`
  regex-validated — so no user-controlled string reaches an `href=`. Verified live against a
  project named `<script>alert(1)</script>&'"` on 5 routes (see
  `qa/verdicts/ui-back-nav-and-live-clarity.md` U5). Also in this unit: `GET /live`'s tip text
  replaced — the stale `scripts/regression_proof.py` instruction (which predated the ▶ Run tests
  button) is gone, replaced by the honest "a black screen is normal, it is the container's real
  and idle display" note plus the AT-054 `AUTOTESTER_SLOW_MO_MS` opt-in; presentation-only, no
  `ProjectStore`/`SecretStore` call added. Routine, non-weakening. Known gap deliberately NOT
  covered by any criterion here and now tracked as ledger issue **AT-057**: an onboarded project
  with zero cases has no UI path to add one, so its ▶ Run tests button is permanently disabled —
  it needs its own contract-scoped cycle and a scoping decision (add-a-case flow vs explicit
  next-step prompt) before a criterion can be written for it.
- 2026-09-07 · /checker (ui-add-case unit) · **new criterion U6 added** — the contract-scoped
  cycle the AT-057 row above demanded has now happened, and the scoping decision came back
  "both": `ui/routes_cases.py` adds the add-a-case form AND `app.py::_actions_card` adds the
  empty-state prompt, so the criterion is finally writable. Routine, non-weakening (adds a
  criterion, softens none). U1-U5 re-verified in the same check and unaffected: the new routes
  go through `ProjectStore` only (U1's no-second-store rule), read live state per request (U2),
  touch no `SecretStore`/`.env` (U3), touch no run/report code (U4), and escape every
  user-derived value — probed hostilely against a project whose `name` and `base_url` carried
  `<script>`, `'` and `"`, with zero raw tags in the response (U5). Two real defects found
  during that cycle were correctly filed rather than folded in here, because neither is a
  U-criterion: **AT-058** (onboarding accepts an `allowed_domains` that excludes the project's
  own `base_url` host, and no route can edit it afterwards — a security-model decision, not a
  bug fix) and **AT-059** (a case's persisted rubric is keyed on a case id that deliberately
  excludes `rationale`, so a changed claim keeps grading against the stale one — a `grade`
  bug the UI flow can no longer trigger now that `rationale` is `None`). Also filed:
  **AT-060** — the form silently discards a submission whose steps duplicate an existing case
  (`add_case` is idempotent on the content id and `create_case` never checks the return), so a
  user cannot correct a mistyped title and gets no feedback. See
  `qa/verdicts/ui-add-case.md`.
- 2026-09-07 · /checker (ui-project-edit-and-domain-validation unit) · **new criterion U7 added**
  — the AT-058 row above named a defect no U-criterion covered; the unit fixed both halves
  (validate at onboarding, and an edit route to recover a project already broken), so the
  criterion is now writable. Routine, non-weakening (adds a criterion, softens none). The
  criterion deliberately pins the *composition* (`host_of` + `allows_domain`, the same pair
  `browser/session.py::check_destination` uses) rather than the validation behaviour, because the
  real risk here is a validator that drifts stricter than the boundary and bricks a legitimate
  project — verified live: a subdomain still onboards, and all four on-disk projects
  (`pathlynks`, `vidysea-erp`, `regression-demo`, `erp`) still pass. U1-U6 re-verified in the same
  check and unaffected: the edit route goes through `ProjectStore` only (U1), reads live per
  request and 404s an unknown slug (U2), imports no `SecretStore` and preserves `secrets` through
  `model_copy` (U3), touches no run/report code (U4), escapes every rendered value — probed with a
  project whose `name` and `base_url` carried `<script>`, `'` and `"`, zero raw tags and every
  `value='…'` attribute escaped including `'`→`&#x27;` (U5), and leaves the add-a-case flow
  untouched (U6). The refused wildcard is recorded as correct: `allowed_domains` stays a hard
  boundary. Two low-severity gaps found in the same probe were filed rather than folded in, since
  neither violates a criterion: **AT-061** (`host_of` returns a pseudo-host for garbage, so a
  schemeless or nonsense `base_url` still onboards) and **AT-062** (onboarding stores `name`/
  `base_url` unstripped while the edit form strips them). See
  `qa/verdicts/ui-project-edit-and-domain-validation.md`.
- 2026-09-07 · /checker (ui-credential-safety-all-fields unit) · **new criterion U8 added** —
  the credential guard the two previous units built had no criterion at all, so a later unit
  could have deleted it and no check would have noticed. Routine, non-weakening (adds a
  criterion, softens none). U8 records exactly what this checker re-derived live against a real
  `.env` value: title / target / expect / value each refuse (closing **AT-070**), and a value
  split across two rows, three rows, or two *different* field types is refused by the
  concatenation check (closing **AT-071**). U1–U7 re-verified in the same check and unaffected:
  onboarding and edit still go through `ProjectStore` only (U1), unknown slug still 404s (U2),
  the env editor is untouched and imports nothing new (U3), no run/report code changed (U4),
  escaping unchanged (U5), all five U6 refusals still fire and the duplicate-check 400 was
  confirmed to be the duplicate check and not the guard misfiring (U6), and
  `_require_reachable_base_url` is byte-unchanged (U7). Five defects found in the same probe were
  filed rather than folded in, because none is a U-criterion violation by this unit:
  **AT-073** (high — `POST /onboard`, `POST /projects/{slug}/edit` and
  `POST /projects/{slug}/secrets` still write a raw `.env` value in cleartext to git-tracked
  `project.json`, breaching core-invariants C5; this is the next unit),
  **AT-074** (a URL-encoded or whitespace-split value still gets through, recoverable in one
  step), **AT-075** (the `unknown case class` / `unknown action` 400s echo raw form input, the
  AT-068 pattern), **AT-076** (any `.env` value — including another project's undeclared one —
  blocks its own literal text, so a login URL in `.env` cannot be a navigate target and the
  suggested `{{SECRET:KEY}}` remedy does not work there because only `session.fill` resolves
  placeholders) and **AT-077** (the concatenation refusal names no field, so an innocent
  straddle across 15 artificial boundaries leaves the user with nothing to change). See
  `qa/verdicts/ui-credential-safety-all-fields.md`.
- 2026-09-07 · /checker (ui-credential-guard-project-routes unit, cycle 3) · **new criterion U9
  added** — the U8 amendment above named AT-073 as "the next unit"; this was it, and it took
  three cycles because the two obvious fixes each broke the other half. U9 records what finally
  held, and pins **both** directions so neither regression can recur silently: matching over the
  **full** `.env` (cycle 2 was FAILed for scoping it to declared values — proved with the
  operator's live `GEMINI_API_KEY` landing in a git-tracked `cases.jsonl` and `project.json`),
  **and** a byte-identical-to-stored exemption (cycle 1 was FAILed for refusing `pathlynks`'s own
  unmodified `base_url` and making the project uneditable). Routine, non-weakening — it adds a
  criterion, softens none, and the two residuals it names are recorded as tracked issues rather
  than written out of the rule. U1–U8 re-verified in the same check and unaffected: onboarding
  and edit still go through `ProjectStore` only and a subdomain still onboards (U1/U7), unknown
  slug still 404s (U2), no declared `SecretRef` value appears in any of 35 rendered routes and
  the env editor is unchanged (U3), no run/report code touched and every `report`/`.html`/`.xlsx`
  is 200 (U4), escaping re-probed live against a project named `<script>alert(1)</script>&'"`
  with zero raw tags on 6 routes (U5), all five case-form refusals still fire with no raw echo
  (U6), and the case form's own concatenation check is **structurally** unexemptable because
  `routes_cases._guard_submitted_case` passes no `exempt` set — 32 hostile probes against a
  declared *and* an undeclared live credential all refused (U8). Three defects found in the same
  probe were filed rather than folded in, none a criterion violation: **AT-087** (medium — the
  exemption hollows out the concatenation check on the project routes; isolated against a
  control), **AT-088** (medium — `_require_reachable_base_url` runs before the guard and echoes a
  credential pasted into Base URL back in its 400, the AT-068/AT-075 pattern's fourth occurrence)
  and **AT-086** raised low→medium (the manifest's "has workarounds" was tested and is wrong —
  onboarding a placeholder then editing is refused too). See
  `qa/verdicts/ui-credential-guard-project-routes.md`.
