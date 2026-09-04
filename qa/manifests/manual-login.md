# Manifest — manual-login

**Contract:** qa/contracts/manual-login.md (ML1–ML5, new this cycle) + qa/contracts/browser-and-secrets.md (B5, B9, reused unchanged)
**Goal task:** none (`.goal/goal.json` is 20/20 done — ad-hoc feature request)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly (new capability; AT-037 filed as a side finding, not fixed here)

## Why this unit

Umesh, looking at the live credentials page: "why do you need Mongo DB — a tester should just
watch the real browser" and "for login, better to open the browser and let the human log in
themselves" — then, when asked whether to make this the only option, clarified he wants all
three mechanisms kept: manual login (new), `.env` auto-fill (kept, he'll keep using it for
Pathlynks specifically), and the existing OTP/2FA pause (kept, untouched).

## What changed

- `qa/contracts/manual-login.md` (new) — ML1 (no secret required) · ML2 (blocks on a real human
  signal, never a fixed sleep) · ML3 (session genuinely persists via the existing profile
  mechanism) · ML4 (reachable via CLI) · ML5 (unused Mongo credential no longer force-declared).
- `qa/feedback-inbox.md` — Umesh's verbatim request + reading, both messages.
- `src/autotester/stages/manual_login.py` (new, 43 lines) — `manual_login(project, paths,
  wait_for_human=...)`: loads `SecretStore` with `strict=False` (never requires a secret to be
  present), starts a headed `BrowserSession`, navigates to `project.base_url`, blocks on the
  injectable `wait_for_human` callable (default: a blocking `input()` prompt), always closes the
  session in a `finally` (so a `KeyboardInterrupt` mid-wait still leaves no dangling browser).
- `src/autotester/cli.py` — new `autotester login <slug>` command, matching the existing
  `flowspec` command-group pattern; 404s cleanly on an unknown project.
- `projects/pathlynks/project.json` — removed the `PATHLYNKS_MONGO_URI` `SecretRef` (confirmed
  unused by any real case; `browser/db.py`'s read-only capability stays in the codebase for a
  future case that specifically needs it — see `qa/contracts/db-assert.md`, unchanged).
- `tests/test_manual_login.py` (new, 4 tests) — no secret read even when one is declared but
  missing (ML1); navigates to the base URL; blocks on the human signal in the correct order
  (start → goto → wait → close, ML2); still closes if the wait itself raises (no dangling
  browser on Ctrl-C).
- `tests/test_cli_login.py` (new, 2 tests) — unknown project refused with exit 1; a real project
  calls through to `manual_login` and reports success.
- `docs/ARCHITECTURE.md` — one new concept→file row (merged with the existing db-assert row to
  stay in budget); 150 lines (at cap).
- `docs/MAP.md` regenerated.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_manual_login.py tests/test_cli_login.py -v
......                                                                   [100%]
6 passed
$ uv run pytest -q       # all green, 211 collected
$ uv run ruff check src tests scripts   # All checks passed!
$ uv run autotester doctor              # doctor: clean
```

**Real, non-mocked run** — a genuine headed browser, no secret anywhere, against the live UI
server as a real destination:
```
$ uv run python /tmp/test_manual_login_real.py
[auto-confirmed] A browser window is open at http://localhost:8010/.
Log in by hand, then press Enter here to save the session...
OK: manual_login completed without needing any secret
```
Confirmed a real persistent Chromium profile was created:
`profiles/manual-login-demo/` contained `Default/`, `Local State`, `Crashpad/`, etc. — the same
real profile structure every other project's session produces. Cleaned up afterward
(`rm -rf profiles/manual-login-demo projects/manual-login-demo`) since it was a throwaway
verification project, not a real one.

Secrets scan on all changed files: clean, except a **pre-existing, unrelated false positive** on
`projects/pathlynks/project.json` — `check_no_secrets.py` flags the file because its own public
`base_url` (`https://pathlynks.vidysea.com/signin`) happens to also be stored as a convenience
`.env` value; confirmed via direct value-match inspection this is not a real credential and is
completely unrelated to this unit's diff (`git diff projects/pathlynks/project.json` shows only
the `PATHLYNKS_MONGO_URI` block removed, `base_url` untouched). Filed as AT-037 (low), not fixed
here — out of scope for a login-mechanism unit.

## How to verify (commands + expected)

- `uv run pytest tests/test_manual_login.py tests/test_cli_login.py -v` → 6 passed
- `uv run pytest -q` → all green
- `uv run ruff check src tests scripts` → clean
- `uv run autotester doctor` → clean
- `uv run autotester login <slug>` against a real project (headed browser) → opens the browser to
  `base_url`, waits at the terminal prompt, closes and persists the profile on Enter
- `grep PATHLYNKS_MONGO_URI projects/pathlynks/project.json` → no match

## Scope notes for the checker

- `.env` auto-fill (`browser/secrets.py`) is completely untouched — Umesh explicitly asked to
  keep using it for Pathlynks. OTP/2FA `blocked_hitl` (`browser-and-secrets.md` B8) is also
  completely untouched.
- `browser/db.py`/`ReadOnlyCollection` itself is NOT removed — only the forced-by-default
  `SecretRef` declaration on the Pathlynks project is removed, per ML5's exact wording.
- AT-037 (the secrets-scanner false positive) is a real, pre-existing finding surfaced while
  verifying this unit, filed honestly rather than silently worked around or hidden — judge this
  unit on ML1-ML5, not on whether AT-037 is fixed (it isn't, by design — separate scope).

## Status: checked-PASS — see qa/verdicts/manual-login.md, cycle 1 PASS
