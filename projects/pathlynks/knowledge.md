# Pathlynks (pathlynks)

**Purpose:** what this system has learned about the Pathlynks product from real,
credentialed exploration — screens reached, auth boundaries, gotchas.
**Open me when:** onboarding a new flow, deciding what a video request should show,
or checking whether a screen was already seen.

## Quick Re-Run
```bash
uv run python scripts/onboard_pathlynks.py --role user
```

**Last successful run:** 2026-09-03 | role=user | run=onboard-01M1JQDHA8296D4EQ484CPKP1Z
**Output file(s):** projects/pathlynks/runs/onboard-01M1JQDHA8296D4EQ484CPKP1Z/

## Portal Profile
| Field | Value |
|-------|-------|
| URL | (see project.json base_url; redacted here where it overlaps a declared secret) |
| Type | saas |
| Intent explored | audit (onboarding) |
| AI involvement | Tier 2 -- agent + knowledge, deterministic once mapped |
| Browser tool used | Playwright via autotester.browser.session.BrowserSession |
| Auth | email + password, two roles observed (counsellor, user) |
| Write policy | read_only (no writes performed) |

## How it works
Sign-in form at the project's base_url takes an `identifier` (email) field and a
`password` field, submitted via a "Login" button. No 2FA/OTP was presented for
this dev-environment account on this run.

## Screens reached
- landing (signin page)
- post-login landing: https://pathlynks.vidysea.com/dashboard

## Gotchas & edge cases
- Two account roles exist for this product (counsellor and user/student); this
  run exercised the `user` role only. The other role's login page differs
  (see `.env.example` for both `*_LOGIN_URL` shapes) -- a separate run should
  cover it before this knowledge file is considered complete.
- Login URLs stored in `.env` are NOT declared as project secrets, so they are
  masked by the redactor as undeclared values (AT-004 behaviour) -- this is a
  known false-positive redaction of non-sensitive URLs, not a security issue;
  use `project.json::base_url` for the canonical, unmasked entry point instead.

## Change detection
- Re-run and diff the screenshot set; a materially different login form or a
  redirect to an unexpected host means this file needs a fresh pass.

## History
| Date | Intent | Findings | Duration | Tool | Notes |
|---|---|---|---|---|---|
| 2026-09-03 | audit | login form mapped, 3 screenshots | -- | BrowserSession | T-030 first pass |
