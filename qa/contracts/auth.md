# Contract — auth: team login, groups and permissions (T-204)

**Covers:** goal task T-204 (team login for the hosted UI). **Owner:** /checker. **Status:** ACTIVE (2026-10-07).
**Criticality:** HIGH — tier L (security/auth/tenancy), so a **dual check** applies (two blind coordinators, both must PASS).
**Serves:** D-072 items 3, 4, 5 and 12 (login, groups, secrets display, Host allow-list); D-066 (Origin guard); D-070/D-071 (go-live
blocker); intent O7; spec R16 (credential boundary) and R17 (consent) must not regress; AT-758, AT-760, AT-761.
**Depends on:** `core-invariants.md` (C5), `browser-and-secrets.md`, `consent.md`, `ui.md`. Reuses the D-066 guard in `ui/helpers.py`.
**Unit split:** the permission engine, accounts, groups and the admin UI are T-204. The video, access-request and comment objects that
use `own`/`assigned`/`shared` scoping are Group 10 (T-198); T-204 supplies the engine they call, not those objects.

## Purpose

A hosted AutoTester is reachable by anyone with the URL, and a run can use the provisioned test account. Umesh chose the simplest scheme
that keeps outsiders out (D-072): email + password, open signup, **zero access until an admin puts the account in a group**, and
AWS-IAM-like groups with checkbox permissions.

## Vocabulary (fixed here so criteria are falsifiable)

- **Permission** = a key from the closed catalogue below, optionally with a scope: `key@all`, `key@assigned`, `key@own`, `key@shared`.
  Unscoped keys (`users.manage`, ...) have no scope.
- **Effective permissions of a user** = the union of the permissions of every group the user belongs to. There is no deny. Additive only.
- **Resource** = `ResourceRef(project_slug, owner_email | None, assignees, shared_with, video_id | None)`.
  - `own`: `owner_email == user.email`. The creator of a project is its owner.
  - `assigned`: the user is in the project's `assignees`.
  - `shared`: the user is in the resource's `shared_with`.
  - `all`: no condition.
  - A project with no recorded owner (legacy, created before T-204) matches **only** `@all`. It fails closed.

### Permission catalogue (closed; a key not listed here cannot be saved into a group)

| key | scopes | what it gates |
|---|---|---|
| `project.view` | all, assigned, own, shared | see the project, its sources, flowspec, catalog, runs |
| `project.create` | (none) | onboard a new project; the creator becomes its owner |
| `project.edit` | all, assigned, own | edit project settings, sources, cases, models |
| `project.run` | all, assigned, own | press Run, enqueue a run |
| `project.assign` | all | assign sub-admins (assignees) to a project |
| `report.view` | all, assigned, own, shared | open a run report |
| `video.view` | all, assigned, own, shared | watch or open a recording |
| `video.upload` | all, assigned, own | upload a recording or give a Drive link |
| `video.share` | all, assigned, own | add or remove `shared_with` on a video or project |
| `access.approve` | all, assigned, own | approve an access request on a resource |
| `comment.create` | all, assigned, own, shared | add a comment |
| `credentials.view` | (none) | **see a saved credential value** (G4) |
| `credentials.edit` | all, assigned, own | write a new credential value (write-only) |
| `schedule.manage` | all, assigned, own | set a project's run schedule |
| `live.view` | (none) | open `/live` and the noVNC view |
| `live.control` | (none) | send input through noVNC (manual login, OTP) |
| `users.manage` | (none) | list, disable, enable, delete, reset any account; edit group membership |
| `groups.manage` | (none) | create, edit and delete groups and their permission ticks |
| `settings.manage` | (none) | server settings (run concurrency, upload limit, default model, SMTP view) |

Group 10 units may add keys to this catalogue through the registry in a later checker-approved amendment. A route or action that
needs a permission not listed here is a contract gap, not licence to invent one.

### Default groups (seeded once, idempotently; admins may edit them afterwards)

| group | permissions | meaning |
|---|---|---|
| **Admin/CEO** | every key above, every scope at `@all` | sees every project and video, approves anyone |
| **Sub-admin** | `project.view/edit/run`, `report.view`, `video.view/upload/share`, `access.approve`, `comment.create`, `credentials.edit`, `schedule.manage` all at `@assigned`; `live.view` | manages only the projects assigned to them |
| **Developer** | `project.create`; `project.view/edit/run`, `report.view`, `video.view/upload/share`, `access.approve`, `comment.create`, `credentials.edit`, `schedule.manage` at `@own`; `project.view`, `report.view`, `video.view`, `comment.create` at `@shared`; `live.view` | works on their own projects and videos; approves access requests for their own videos |
| **Tester** | `project.view`, `report.view`, `video.view`, `comment.create` at `@shared` only | sees only what was shared with them, and can comment |

`credentials.view` is held by **Admin/CEO only** by default (D-072 item 5). The Developer, Tester and Sub-admin default grants for
`credentials.edit`, `schedule.manage`, `live.view` and `project.create` are the checker's reading of Umesh's role answer, not stated in
D-072; they are editable by any admin, and a different answer from Umesh is a routine amendment of the table above.

## Criteria

### Accounts, passwords, sessions

- **AU1 — Passwords are hashed with a vetted slow KDF, never stored or logged.** The stored value is an argon2id or bcrypt hash with a
  per-user salt (argon2id memory >= 19 MiB and t >= 2, or bcrypt cost >= 12). No plaintext password, and no reversible form, exists in the
  store, in any log line, the audit file, a response body, an error message or an exception text. Verification is constant-time.
  *Dependency:* `uv.lock` has neither library today, and D-072 does not authorize one. A D-entry whose `Changes-authorized` names the
  library must exist **before the unit's first commit**, and `pyproject.toml`/`uv.lock` change only for it. If Umesh declines a new
  dependency, stdlib `hashlib.scrypt` (N >= 2^15, r=8, p=1) is the one accepted alternative, by routine amendment of this line.
  `serves:` D-072#3, O7. *Re-derive:* unit test reads the raw store after signup with a canary password and asserts the canary is
  absent from every file under the data root and from `caplog`; asserts the hash prefix is `$argon2id$` or `$2b$`; mutation: store the
  password as given -> test fails.
- **AU2 — Login does not reveal which half was wrong.** `POST /auth/login` with an unknown email, a wrong password, and a disabled
  account all return the same status and the same body text, and take comparable work (the unknown-email path still computes a hash
  against a dummy). A correct email + password creates a session and redirects to a same-site relative `next` or `/`.
  `serves:` D-072#3. *Re-derive:* three requests, compare status+body byte for byte; mutation: return "no such user" -> fails.
- **AU3 — Session cookie and server-side session.**
  - The session id is >= 128 bits from `secrets`, a **new id is issued at every login** (no fixation), and the session is looked up
    server-side so a disable, delete, group change or password reset takes effect on the **next request** with an unexpired cookie.
  - Cookie flags: `HttpOnly`, `SameSite=Lax`, `Path=/`, no `Domain`. `Secure` is set whenever the request is HTTPS (or
    `X-Forwarded-Proto: https` from a configured proxy) or `AUTOTESTER_HOSTED=1`; with `Secure` it also carries the `__Host-` prefix.
    The only way to omit `Secure` in hosted mode is the explicit `AUTOTESTER_COOKIE_SECURE=0`, which the deploy guide documents as the
    pre-domain, private-network interim (see `hosting.md` HO13).
  - Absolute lifetime <= 12 h by default (configurable, never unlimited). A cookie that is tampered, truncated, unknown, or expired is
    refused (302/401) and creates nothing.
  `serves:` D-072#3. *Re-derive:* header assertions; parametrized bad-cookie test; test that disabling a user makes their next request
  with a live cookie fail.
- **AU4 — Logout.** `POST /auth/logout` (Origin-guarded) deletes the server-side session and clears the cookie; the old cookie value is
  refused afterwards. A GET to the logout path changes nothing. `serves:` D-072#3.
- **AU5 — Login rate limit.** After 5 failed attempts for one account, or 20 from one client address, inside 10 minutes, further login
  attempts for that scope are refused with 429 **even with the correct password** until the window passes. The constants are named in
  the module and documented in `.env.example`. A lock is time-based and never permanent, and the 429 body does not say whether the
  account exists. The counters survive a request, not necessarily a restart. `serves:` D-072#3.
  *Re-derive:* 6 bad logins then a good one -> 429; advance the injected clock -> allowed; mutation: remove the check -> fails.

### Signup, first admin, account management

- **AU6 — Open signup, zero permissions.** `GET/POST /auth/signup` is reachable unauthenticated. Email is trimmed, lowercased, and
  validated; password length 10..128 (the upper bound limits hashing cost); a duplicate email is refused without touching the existing
  account. A new account has **no group**, and an authenticated user with an empty effective-permission set can reach only the
  "waiting for an admin" page and logout; every other route returns 403. That page says which role to ask (an administrator) and lists
  no users. `serves:` D-072#3, D-072#4. *Re-derive:* signup as user 2, request every non-public route from `app.routes`, assert 403.
- **AU7 — The first account becomes admin, atomically.** When the user store is empty, the first signup is placed in Admin/CEO.
  Two simultaneous first signups yield exactly one admin. Every later signup gets no group. Optional hardening (checker-derived, not in
  D-072): when `AUTOTESTER_FIRST_ADMIN_EMAIL` is set, only that email may become the first admin and any other early signup gets no group.
  `serves:` D-072#4. *Re-derive:* threaded double-signup test with a barrier; mutation: grant admin to every signup -> fails.
- **AU8 — The admin can act on any account.** A holder of `users.manage` can list accounts, disable, enable, **delete**, reset a
  password (sets a new hash and revokes that user's sessions), change the display name, and add or remove group membership, for any
  account. A disabled or deleted user's next request fails and their login is refused with the AU2 text. Deleting a user keeps the audit
  rows that name them and does not delete projects they owned: ownership of those becomes "no owner" (visible only at `@all`).
  A caller without `users.manage` gets 403 from every such route. `serves:` D-072#3.
- **AU9 — Last-admin protection.** The last enabled account in Admin/CEO cannot be disabled, deleted, removed from the group, or have
  the group's `users.manage` tick removed; the attempt is refused with a message and changes nothing. `serves:` D-072#3, D-072#4
  (checker-derived lockout guard). *Re-derive:* one admin, try each action; mutation: drop the guard -> fails.

### Groups and permissions

- **AU10 — Groups with checkbox permissions, additive.** A holder of `groups.manage` can create, rename and delete groups and tick
  or untick any catalogue permission (with its allowed scopes) per group; a holder of `users.manage` adds users to groups. The
  permission form is rendered as labelled checkboxes grouped by area. The effective permissions are the union over groups; unticking
  a permission removes it from every member on their next request. Saving an unknown key, or a scope the key does not allow
  (`users.manage@own`), is refused and stores nothing. A group in use by users can be deleted only after the admin is told how many
  members lose access, and those members then have the permissions of their remaining groups only. `serves:` D-072#4.
  *Re-derive:* two groups, union test; untick -> member refused next request; unknown key -> 4xx and store unchanged.
- **AU11 — Default groups are seeded once and editable.** On first start the four default groups exist with exactly the grants in the
  table. Restarting the server does not reset an admin's edits and does not recreate a deleted default group. `serves:` D-072#4.
- **AU12 — One authorization function, scoping resolved by it.** Every route calls a single `authorize(user, key, resource)` (the
  one place that evaluates scopes); no route compares emails or group names itself (a grep of `ui/` for group-name literals, other than
  the seed table, finds nothing). The scope tests are: `all` always, `assigned` iff the user is an assignee, `own` iff the owner,
  `shared` iff in `shared_with`; a missing owner matches only `all`. `serves:` D-072#4.
  *Re-derive:* a table-driven test over (group, key, resource relation) for all four default groups and all four relations;
  mutation: treat `shared` as `all` -> fails.
- **AU13 — Visibility follows scope, and existence is not leaked.** Home, sidebar, project list, report lists and search list only
  resources the user may view. A direct URL for a project the user may not view returns the same 404 as a project that does not exist;
  a visible resource on which the user lacks the action returns 403. An Admin sees every project and video. A Sub-admin sees only assigned
  projects. A Developer sees their own projects plus anything shared with them. A Tester sees only shared items and can add comments.
  `serves:` D-072#4 and the Group 10 roles answer (2026-10-07). *Re-derive:* four users x two projects x list and direct URL.
- **AU14 — Default deny for routes.** A route-enumeration test walks `app.routes` and requires each route to be either in the closed
  public set (AU16) or to declare a required permission through the central policy table; a route added after import with neither is
  refused at request time (403) and fails the test. Applies to every method the route declares. `serves:` D-072#3.
  *Re-derive:* the enumeration test; mutation: add an undeclared route -> test fails.
- **AU15 — Approval and consent are not bypassed by a role.** Holding `project.run@all` never skips a `RunApproval`, `write_policy`, or
  model-spend gate: the existing `consent.md` behaviour is unchanged for every group, including Admin/CEO. `serves:` spec R17, D-072#4.
  *Re-derive:* admin triggers a run on a project whose approval is missing -> the same refusal a non-admin gets.

### Unauthenticated surface

- **AU16 — Unauthenticated users reach only login and signup.** The closed public set is exactly `GET/POST /auth/login`,
  `GET/POST /auth/signup`, and a minimal `GET /healthz` that returns only `{"ok": true}` (needed by the container health check; the
  current `/healthz` also prints process start time and source mtimes, so unauthenticated callers get the minimal form and the detailed
  freshness probe requires `settings.manage`). Any other path, any method, answers an unauthenticated request with 302 to
  `/auth/login?next=<same-site relative path>` for a browser (`Accept: text/html`) or 401 JSON otherwise; the body never echoes the
  input. A `next` that is an absolute URL, `//host`, or `javascript:` is dropped. No file under the data root changes on any refused
  request. `serves:` D-072#3. *Re-derive:* enumerate `app.routes` unauthenticated, diff the data root before/after.
- **AU17 — The gate cannot be switched off by accident.** Auth is on by default. `AUTOTESTER_AUTH_DISABLED=1` (for legacy tests and a
  single-user laptop) is refused at startup when `AUTOTESTER_HOSTED=1` or when the bind address is not loopback, and prints a one-line
  warning when honoured. `AUTOTESTER_HOSTED=1` with a missing required setting (`AUTOTESTER_ALLOWED_HOSTS` or `AUTOTESTER_ALLOWED_ORIGINS`
  naming the server, per AU20) makes the app refuse to start. The auth tests run with the gate ON. `serves:` D-072#3, D-072#12.
  *Re-derive:* startup tests for each combination.

### Guard layering

- **AU18 — Every state-changing route stays behind the D-066 Origin guard, including auth routes.** `POST /auth/login`, `/auth/signup`,
  `/auth/logout` and all admin routes are guarded. The guard runs **before** authentication: a cross-origin POST carrying a valid session
  cookie is 403. Two further gaps in the same code are closed because the hosted server exposes them: an `Origin` whose port part is
  not numeric (`http://localhost:8000.evil.com`, AT-760) is refused, and a request with more than one `Origin` header (AT-761) is refused.
  `*` in `AUTOTESTER_ALLOWED_ORIGINS` is ignored. `serves:` D-066, D-072#12, AT-760, AT-761.
  *Re-derive:* extend `tests/test_ui_origin_guard.py`; mutation: reorder middleware so auth runs first -> a 403 test fails.
- **AU19 — Host allow-list (AT-758).** Every request, GET included, has its `Host` header checked: it must be loopback
  (`localhost`, `127.0.0.1`, `::1`, any port), or the host of an origin in `AUTOTESTER_ALLOWED_ORIGINS`, or an exact entry of
  `AUTOTESTER_ALLOWED_HOSTS` (comma or space separated, no wildcard, case-insensitive, port compared when given). Anything else is refused
  (400/403) before routing, and in particular `GET /projects/{slug}/env` with `Host: evil.example` returns no body that contains a saved
  value. `serves:` D-072#12, AT-758. *Re-derive:* `Host: evil.example`, `Host: localhost.evil.com`, `Host: 127.0.0.1.evil.io`,
  and a listed host; mutation: skip the check -> the first three fail.
- **AU20 — Hosted configuration is explicit.** With `AUTOTESTER_HOSTED=1` at least one of `AUTOTESTER_ALLOWED_HOSTS` /
  `AUTOTESTER_ALLOWED_ORIGINS` must be set, and the server's own origin must be an allowed one; otherwise startup raises. Both keys are
  documented in `.env.example` (`hosting.md` HO9). `serves:` D-072#12.

### Secrets display

- **AU21 — Saved credential values are shown only to `credentials.view` (G4).** On `/settings/providers` and the per-project
  `/projects/{slug}/env` page, a viewer **without** `credentials.view` sees only "set" / "not set" per key: no value in the HTML,
  the `value=` attribute, inline script, a data attribute, a redirect URL, a flash message or any JSON/export, and no length or
  prefix hint. A viewer **with** it sees the D-034 show/hide behaviour unchanged. Writing a new value needs `credentials.edit` on that
  project (or `settings.manage` for the global keys) and works without `credentials.view`; the value is never echoed back after the
  POST. Provider keys present only in the server's process environment show as "set". By default only Admin/CEO holds
  `credentials.view`. `serves:` D-072#5, spec R16, O7, core-invariants C5 (amended 2026-10-07).
  *Re-derive:* seed a sentinel value, render both pages as Tester, Developer, Sub-admin and Admin, grep the HTML; mutation: render the
  value for everyone -> the non-admin tests fail.

### Observability and hygiene

- **AU22 — Audit without secrets.** Every state-changing request appends one line `{ts, email, method, path template, status}` to
  `<data>/.work/audit.jsonl`; admin actions (disable, delete, reset, group edit, setting change) add `{actor, target, action}`. Lines hold
  no body, query string, password, cookie or hash. A login failure line names the attempted email only after normalization and never
  the password. The uvicorn access log is disabled in `docker/entrypoint.sh` (cookies and `next` values travel in URLs and headers).
  `serves:` D-072#3, O7. *Re-derive:* canary password and cookie through login, grep logs and audit file.
- **AU23 — Auth data lives under the data root, never in git or the image.** Users, groups, sessions and settings are stored under
  `repo_root()` (which honours `AUTOTESTER_ROOT`), in a path that `git check-ignore` and `.dockerignore` both cover, with atomic writes
  and owner-only permissions where the platform supports them (best effort on Windows, asserted on Linux). New shapes are Pydantic
  models in `schema/` with `extra="forbid"`; no second `.env`-style store. `serves:` O7, docker.md D6, `core-invariants.md` C1-C5.
- **AU24 — Windows dev and Ubuntu prod.** Paths use `pathlib` / `core.paths`; no POSIX-only module (`fcntl`, `pwd`) is imported at
  module top level, and no Windows-only call is made without a guard. The concurrency-sensitive code (first-admin, session store, rate
  limit) is correct under both: it relies on the store's own atomicity or a portable lock, not on `flock` alone. The auth tests pass
  on Windows (the checker's host) **and** inside the project's Docker image on Linux; the Linux run is recorded as evidence
  (`qa/evidence/t204-linux-run.md`), and it may come from the T-203 rehearsal or any Linux host. `serves:` D-072#7.
- **AU25 — Existing UI behaviour is unchanged for an authorized user.** With the gate on and an Admin session, the existing UI
  contract suite (`tests/test_ui*.py`) passes; the shared layout (`theme.page`) gains only a signed-in identity chip, a logout control,
  and the admin links the user may use. `serves:` D-072#3, `ui.md` U1-U12.

### Human-facing walks (Mode D, interactive)

- **AU26 — Signup, login, pending and admin flows work in a real browser.** Mode D with the checker's own browser: sign up a first
  account (lands as admin), sign up a second (sees the waiting page), admin ticks a group for it (second account reaches its default
  page on its next click), disable it (next click returns to login), delete it. Zero unexplained console errors. Persona walks for the
  spec user types touching these flows: **tester** reaches the shared-with-me page in <= 2 clicks from login, **dev** reaches their own
  project, **lead** is not shown admin controls. Every form control has a visible label and is keyboard-operable. Evidence under
  `qa/evidence/browser-t204-*-checker/`. `serves:` D-072#3, D-072#4, spec user types.

## Out of scope / ignore

- Group 10 objects and workflows that *use* the engine: video upload, access-request creation and approval screens, comments, share
  links, tracker integration (T-197..T-201). T-204 owes only `authorize()`, the catalogue, scope resolution and project assignment/sharing
  data.
- Google or any other OIDC/SSO, an LDAP/directory sync, MFA, passkeys, "remember me", self-service password change, and a
  forgot-password email flow (an admin resets passwords; email sending belongs to `hosting.md`).
- A deny rule, group nesting, time-limited grants, per-field permissions.
- TLS and proxy setup (`hosting.md`); noVNC proxying itself (`hosting.md` HO12 uses `live.view` / `live.control` from here).
- Judging the strength of an individual user's password beyond the length bounds in AU6.
- Wording of messages, colours, and layout beyond AU26's labelled-control and keyboard checks.

## No-fire list (must NOT happen)

- No plaintext or reversible password anywhere; no password, hash, session id or cookie in a log, audit line, error, or response.
- No route reachable unauthenticated beyond AU16's set; no "temporary" debug route or bypass header.
- No account with zero groups reaching a product page.
- No role or permission that skips `RunApproval`, `write_policy` or the credential boundary.
- No stored credential value rendered to a viewer without `credentials.view`, on any page, API or export.
- No change to `stages/`, `schema/` models other than the new auth/permission/settings models, or `providers/`.
- No new dependency except the one hashing library named by a D-entry (AU1).
- No `*_v2` / `*_new` files; files <= 300 lines; functions <= 50; one-job docstring per new module (D-072#2 authorizes the new
  modules under `ui/`, `schema/` and a store; the checker judges them against the doctor rules).

## Amendment log (append-only; git history is the version)

- 2026-10-07 · init · contract created for T-204 from D-072 and the Group 10 roles answer (Admin/CEO and developer-for-own-videos).
  Replaces the maker's Google-OIDC proposal (`.work/plan-golive/T-204-contract-proposal.md`, TL1-TL17): D-072#3 chose email + password
  and open signup. Kept from it: default deny (TL1 -> AU14/AU16), refused requests change nothing (TL2), cookie integrity and flags
  (TL4/TL5 -> AU3), Origin guard before auth (TL13 -> AU18), no secret in logs (TL10 -> AU22), audit (TL11 -> AU22), hosted fail-closed
  startup (TL9 -> AU17/AU20), hosted secret display (TL12 -> AU21, now `credentials.view`-gated instead of hosted-only). Dropped:
  OIDC claim checks (TL6-TL8), `/auth/check` proxy hook (re-added by `hosting.md` HO12 as an authenticated route).
