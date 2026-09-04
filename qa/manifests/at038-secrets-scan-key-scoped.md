# Manifest — at038-secrets-scan-key-scoped

**Contract:** qa/contracts/core-invariants.md C5 (secrets never reach a log/artifact)
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-038

## Why this unit

AT-038 (filed by the checker while verifying AT-037's fix): excluding a `.env` value from the
secrets scan by bare VALUE identity meant a genuinely different secret that happened to
coincide (byte-for-byte) with a project's public `base_url` would go uncaught if it leaked into
some other file — a real, if currently inert, regression in scanner coverage versus before
AT-037's fix. The checker reproduced this with two different `.env` keys sharing one value.

## What changed

`scripts/check_no_secrets.py::real_values()` — the exclusion is now scoped to **both** the value
matching a public base_url **and** the specific `.env` key's name containing `"URL"`
(case-insensitive). A password-shaped key (e.g. `OAUTH_CALLBACK_SECRET`) never matches the
exemption regardless of its value, so a coincidental collision with a base_url string is still
caught if it leaks elsewhere.

`tests/test_check_no_secrets.py` — new
`test_a_coincidental_non_url_secret_still_flags_even_if_it_matches_a_base_url`, reproducing the
checker's exact adversarial scenario (two `.env` keys, one `SOME_LOGIN_URL`, one
`OAUTH_CALLBACK_SECRET`, both holding the same value as a declared `base_url`) and asserting the
non-URL key's leak into an artifact file is still flagged.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_check_no_secrets.py -v
....                                                                      [100%]
4 passed
$ uv run pytest -q                        # all green
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run python scripts/check_no_secrets.py projects/pathlynks/project.json
scanned 1 file(s); 0 leak(s)              # AT-037's original complaint still stays fixed
```

## How to verify

- `uv run pytest tests/test_check_no_secrets.py -v` → 4 passed (including the new adversarial test)
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean
- `uv run python scripts/check_no_secrets.py projects/pathlynks/project.json` → 0 leaks (AT-037
  regression still holds)

## Scope notes for the checker

- This directly closes the exact gap the previous checker cycle found and filed — re-verify by
  constructing the same two-key adversarial scenario yourself (don't just trust the new test),
  and confirm AT-037's original complaint (`project.json` no longer flagging) still holds
  simultaneously — both must be true at once.
- The `"URL" in key.upper()` convention is a heuristic, not a schema-enforced contract — worth
  noting for anyone declaring a new convenience `.env` key that mirrors a base_url in the future:
  name it with `URL` in it, or it won't be exempted (a false positive again, but never a false
  negative — the fail-safe direction is correct).

## Status: checked-PASS

Checker verdict: `qa/verdicts/at038-secrets-scan-key-scoped.md` (Cycle checked: 1, PASS). AT-038's
specific gap (value-only exclusion, no key link) is genuinely closed. A narrower residual gap in
the "URL"-substring heuristic (a coincidentally URL-containing key name, e.g. `HOURLY_...`) was
found during the check and filed separately as AT-039 (low severity, does not block this PASS).
