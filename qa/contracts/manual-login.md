# Contract — Manual one-time login (new, 2026-09-04)

**Covers:** ad-hoc unit `manual-login` (no `.goal` task). **Owner:** /checker.
**Criticality:** MEDIUM — a credential-handling path, judged with the same care as
`browser-and-secrets.md`.
**Depends on:** `browser-and-secrets.md` (B5 real visible browser, B9 targeted cleanup — reused
unchanged).

## Purpose

Umesh: "for login you should only need id+password, right? Either take it from the user, or
better — open the browser and let the human log in themselves." A project should never be
*required* to hand the system a password. `autotester login <slug>` opens the real, visible
browser to the project's base URL, waits for a human to log in by hand, then closes — saving the
session into the project's persistent profile (`profiles/<slug>/`) so every future run reuses it
without ever touching a stored credential.

This is additive, not a replacement: `.env` auto-fill (existing, `browser/secrets.py`) and the
OTP/2FA `blocked_hitl` pause (existing, `browser-and-secrets.md` B8) are both unchanged and stay
fully available — Umesh explicitly asked to keep all three mechanisms (manual login, `.env`
auto-fill, OTP pause), not to remove any.

## Criteria

### ML1 — No secret is required to log in manually
`manual_login(project, paths)` never reads, resolves, or requires any `SecretRef`/`.env` value.
It starts a headed `BrowserSession` against `project.base_url` and stops there — the human does
everything else directly in the real browser window.

### ML2 — Blocks for a real human action, not a fixed sleep
The function waits for an explicit human signal (an injectable `wait_for_human` callable,
defaulting to a blocking prompt) before proceeding — never a fixed `time.sleep()` guess at how
long a login takes.

### ML3 — The session is genuinely persisted
Closing the session (`BrowserSession.close()`, unmodified — B9) after the human logs in leaves
the login state in `profiles/<slug>/`'s persistent Chromium profile, exactly like every other
session this system opens — the next `BrowserSession.start()` against the same profile reuses it.

### ML4 — Reachable from the CLI, not code-only
`autotester login <slug>` (new Typer command in `cli.py`) is the operator-facing entry point —
matches the existing `autotester flowspec ...` command-group pattern, no new invocation style.

### ML5 — Unused DB-assertion credential is not force-declared
`projects/pathlynks/project.json` no longer declares `PATHLYNKS_MONGO_URI` as a `SecretRef` —
confirmed unused by any real case (`browser/db.py`'s capability stays in the codebase for a
future case that specifically needs it, unit-tested in isolation per `qa/contracts/db-assert.md`,
just not force-requested from every Pathlynks user by default).

## No-fire list

- Removing or weakening `.env` auto-fill (`browser/secrets.py`) — Umesh explicitly asked to keep
  it, specifically for Pathlynks where he provides credentials directly.
- Removing or changing OTP/2FA `blocked_hitl` behavior (`browser-and-secrets.md` B8) — unchanged.
- Removing `browser/db.py`/`ReadOnlyCollection` itself — the capability stays for future use,
  only the forced-by-default `SecretRef` declaration on Pathlynks is removed.
- Auto-detecting "is the human done logging in yet" (polling the DOM for a dashboard URL, etc.) —
  out of scope; the human's own confirmation is the signal, matching this project's standing HITL
  pattern (OTP already works this way).

## Amendment log (append-only; git history is the version)

- 2026-09-04 · init · contract created for the manual-login unit.
