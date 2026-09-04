# Manifest — at039-secrets-scan-word-boundary

**Contract:** qa/contracts/core-invariants.md C5
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-039

## Why this unit

AT-039 (filed by the checker verifying AT-038's fix): the `"URL" in k.upper()` check was a bare
substring test, so a key like `HOURLY_BILLING_SECRET` would coincidentally qualify for the
base_url exemption (the letters "u-r-l" sit inside "hourly") even though its value is a genuine
secret, not a URL. Same failure class as AT-038, reached through the key-name side this time
instead of the value side.

## What changed

`scripts/check_no_secrets.py` — replaced the substring check with a word-boundary regex,
`_URL_KEY = re.compile(r"(?:^|_)URL(?:_|$)")`: matches only a whole `URL` token bounded by the
start/end of the key or an underscore (`SOME_LOGIN_URL`, `URL`, `LOGIN_URL_BASE` all match;
`HOURLY_BILLING_SECRET` does not, since "URL" there is neither preceded nor followed by a
boundary).

`tests/test_check_no_secrets.py` — new
`test_a_key_that_merely_contains_the_letters_url_is_not_treated_as_a_url_key`, reproducing the
checker's exact `HOURLY_BILLING_SECRET` scenario and confirming its coincidental leak is caught.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_check_no_secrets.py -v
.....                                                                     [100%]
5 passed
$ uv run pytest -q                        # all green
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
$ uv run python scripts/check_no_secrets.py projects/pathlynks/project.json
scanned 1 file(s); 0 leak(s)              # AT-037's original fix still holds
```

## How to verify

- `uv run pytest tests/test_check_no_secrets.py -v` → 5 passed
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean
- `uv run python scripts/check_no_secrets.py projects/pathlynks/project.json` → 0 leaks

## Scope notes for the checker

- Three things must hold simultaneously now: AT-037 (project.json's own base_url doesn't
  self-flag), AT-038 (a coincidental non-URL-key value collision is still caught), AT-039 (a
  coincidental URL-substring key name is still caught). Re-verify all three, not just the newest.
- This is a narrowing fix (word-boundary regex is strictly more conservative than a bare
  substring) — it cannot reopen AT-037 or AT-038 by construction, since it only ever REMOVES
  matches the old substring check would have made, never adds new ones.

## Status: ready-for-check
