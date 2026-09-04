# Manifest — at037-secrets-scan-false-positive

**Contract:** qa/contracts/core-invariants.md C5 (secrets never reach a log/artifact) — this fix
is about the *scanner* that enforces C5, not C5 itself
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-037

## Why this unit

AT-037 (filed in the previous unit): `scripts/check_no_secrets.py` flagged
`projects/pathlynks/project.json` as a "leak" because its own public `base_url`
(`https://pathlynks.vidysea.com/signin`) happens to also be stored as a convenience `.env`
value. Not a real credential leak — a sign-in page URL is meant to be public — but a false
positive in the exact tool this project's own maker-checker cycle runs before every commit,
worth fixing so it doesn't get silently ignored or waste a future investigation.

## What changed

`scripts/check_no_secrets.py` — new `_public_base_urls(root)`: loads every project's
`project.json` via `ProjectStore` and collects each declared `base_url` into a set.
`real_values()` now excludes any `.env` value that **exactly** equals one of those URLs before
building the scan list — an exact string match only, never a prefix/substring rule (so a real
secret that happens to merely *contain* a base URL as a fragment would still be caught).

`tests/test_check_no_secrets.py` (new, 3 tests):
- a project's own base URL is excluded from the scan values even when it's also in `.env`, while
  a genuinely different secret in the same `.env` still appears in the scan list;
- a real secret unrelated to any base_url still flags a file that contains it (proves the fix
  doesn't over-broadly suppress real leaks);
- the exact AT-037 regression case — `project.json` itself no longer flags.

## Real verification performed (not simulated)

```
$ uv run python scripts/check_no_secrets.py projects/pathlynks/project.json
scanned 1 file(s); 0 leak(s)          # was: LEAK, before this fix

$ uv run pytest tests/test_check_no_secrets.py -v
...                                                                       [100%]
3 passed
$ uv run pytest -q        # all green, 214 collected
$ uv run ruff check src tests scripts   # All checks passed!
$ uv run autotester doctor              # doctor: clean
```

## How to verify

- `uv run python scripts/check_no_secrets.py projects/pathlynks/project.json` → 0 leaks
- `uv run pytest tests/test_check_no_secrets.py -v` → 3 passed
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean

## Scope notes for the checker

- The exclusion is exact-string-match only, scoped to values that literally equal a declared
  `base_url` — verify this doesn't create a bypass (e.g. a real secret that happens to start with
  a base_url as a substring must still be caught; `test_a_real_secret_that_happens_to_differ...`
  covers the "still catches a real leak" side, but double-check the exact-match logic yourself in
  `_public_base_urls`/`real_values`).
- No change to what counts as a "real" `.env` value otherwise, no change to the dot-escaping
  logic (AT-025's fix, untouched), no change to any file this scanner is run against elsewhere in
  the project's workflow.

## Status: checked-PASS — see qa/verdicts/at037-secrets-scan-false-positive.md, cycle 1 PASS (checker filed AT-038 as a follow-up; see qa/manifests/at038-secrets-scan-key-scoped.md)
