# Contract — Pathlynks onboarding (T-030)

**Covers:** goal task T-030. **Owner:** /checker. **Criticality:** HIGH — the first unit that
drives a real browser against real (dev) credentials for the actual first target product.
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B1-B9, all already built).

## Purpose

Declare Pathlynks as a project, log in with the dev-environment test accounts already loaded
into `.env`, and produce `projects/pathlynks/knowledge.md` — the first real evidence that the
credential boundary and browser session hold up against a live product, not just fixtures.

## Design decision this contract locks in

`/portal-explorer`'s default mechanism drives Playwright **MCP** tools directly — which means a
raw credential would appear as a literal string argument in an MCP tool call, i.e. **in this
session's own transcript**. That is precisely the leak T-011/T-010 were built to prevent (a
secret must never appear in a prompt, a log, or anywhere outside `SecretStore.resolve`'s return
value, used immediately and only inside `BrowserSession.fill`).

**O1 — No raw secret in any tool call, MCP argument, prompt, or transcript, ever.** The
onboarding script uses `SecretStore` + `BrowserSession` exclusively — it never calls a
Playwright MCP tool with a literal password/email, and it never prints one. Only `{{SECRET:KEY}}`
placeholders may appear in the script's own source or logs. **This bars raw secret values from
every file the maker itself writes by hand during the unit, not only the script** — the evidence
manifest (`qa/manifests/t030-pathlynks-onboarding.md`), the human-gate narrative, and any other
maker-authored prose. A manifest is a transcript of the unit and manifests in this project are
git-tracked (T-005/T-010/T-011/T-020 precedent) — a raw credential pasted into one to "prove" a
human gate was cleared is the same leak this contract exists to prevent, just carried by a
different file than the script.

## Criteria

### O2 — Project declared correctly
- `projects/pathlynks/project.json` validates as `schema.Project`: `slug="pathlynks"`,
  `base_url` on the `vidysea.com` domain, `allowed_domains=["vidysea.com"]` (covers both the
  counsellor and user subdomains actually used), `write_policy=READ_ONLY`, `headed` explicit.
- `secrets[]` declares exactly the keys present in `.env` for this project
  (`PATHLYNKS_COUNSELLOR_EMAIL/PASSWORD`, `PATHLYNKS_USER_EMAIL/PASSWORD`, `PATHLYNKS_MONGO_URI`),
  each scoped to `vidysea.com`.

### O3 — Real login, evidence captured, nothing leaked
- The script logs in as at least one role using `BrowserSession.fill()` for the credential
  fields (never a literal value).
- At least 2 masked screenshots are captured to `projects/pathlynks/runs/<run>/` via
  `BrowserSession.screenshot()`.
- `grep` of the script's own stdout/log output and of every captured screenshot's filename for
  any of the four real secret values returns nothing.
- `write_policy=READ_ONLY` is respected: no form is submitted beyond the login itself, no data
  is created or modified.

### O4 — Knowledge file produced
- `projects/pathlynks/knowledge.md` exists, following the `/portal-explorer` template shape
  (Quick Re-Run, Portal Profile, How it works, Endpoints, Gotchas, History) but sourced from
  this script's run, not a generic MCP-driven exploration.
- Records which role logged in, the login URL, screens reached, and any anti-bot/2FA signal
  observed (informational — `request_human` exists for a future run if OTP appears).

**Verify:** `uv run pytest tests/test_onboard_pathlynks.py -q` (structural/unit-level checks
against a script that can run for real or be exercised with a recorded flag) + a real run's
transcript reviewed for O1 by the checker.

## Out of scope
Exploring every screen (that's ongoing, self-extending coverage — T-090); writing test cases
(T-070); the counsellor vs user role split beyond capturing that it exists.

## No-fire list
- Which specific screens beyond login+one authenticated page were reached.
- Performance of the login flow.
- Whether both roles were exercised in this first pass (one is enough to prove the mechanism).

## Amendment log (append-only; git history is the version)

- 2026-09-03 · routine · O1: explicitly extended to cover every file the maker writes by hand
  during the unit (manifest, human-gate narrative), not only the script's own code/logs · why:
  cycle-1 check (checker) found the two real dev passwords pasted in plaintext into
  `qa/manifests/t030-pathlynks-onboarding.md`'s "Human gate cleared" section while narrating that
  Umesh's values looked dev-like — a real O1 leak into a file this project's own history shows
  gets git-tracked (T-005/T-010/T-011/T-020 manifests are all committed). Tightening only; the
  header line ("ever") already implied this, the amendment makes it explicit so it can't recur.
