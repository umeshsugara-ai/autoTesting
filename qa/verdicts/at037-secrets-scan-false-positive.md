# Verdict — at037-secrets-scan-false-positive

**Cycle checked: 1**
**Verdict: PASS** (with a new low-severity issue filed for a residual edge case — see below)

## Contract

`qa/contracts/core-invariants.md` C5 — this unit is about the scanner tool
(`scripts/check_no_secrets.py`) that enforces C5, not C5 itself.

## What I verified

### 1. The claimed fix matches the code

- `scripts/check_no_secrets.py:21-35` `_public_base_urls(root)` — iterates every
  `projects/<slug>/project.json` via `ProjectStore`, collects each `project.base_url` into a
  `set()`. No regex, no substring logic — a plain `set`.
- `scripts/check_no_secrets.py:38-53` `real_values(root)` — line 50:
  `v for v in parse_env(...).values() if v and v not in public`. This is Python `in` against a
  `set` of strings — **exact string equality only**. Confirmed no `.startswith`, no
  substring/regex matching anywhere in either function. The manifest's claim ("exact string
  match only, never a prefix/substring rule") is accurate.

### 2. Independent reproduction (re-ran myself, not trusted from the manifest)

```
$ uv run python scripts/check_no_secrets.py projects/pathlynks/project.json
scanned 1 file(s); 0 leak(s)
EXIT:0
```
Matches manifest's claim (was LEAK before this fix, per AT-037's original issue row and the
`| FIXED 2026-09-04` note now in `qa/issues.jsonl`).

```
$ uv run pytest tests/test_check_no_secrets.py -v
tests\test_check_no_secrets.py ...                                       [100%]
3 passed in 0.22s
```
All 3 tests read and independently judged:
- `test_a_projects_own_base_url_is_excluded_even_if_also_in_env` — genuinely proves the base_url
  string is excluded while a *different* value (`hunter2-trombone-staple`) in the same `.env`
  survives into `real_values()`. Sound.
- `test_a_real_secret_that_happens_to_differ_from_base_url_still_flags` — proves a secret whose
  value is **not** any base_url still gets caught by `scan()`. This is real coverage, but it does
  **not** exercise the "same value, two different keys" collision case (see finding below) — its
  name promises more than it tests.
- `test_a_project_base_url_no_longer_flags_project_json_itself` — the literal AT-037 regression
  case, reproduced clean. Sound.

```
$ uv run pytest -q                        # 214 collected, all pass (2 skipped, pre-existing)
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```
All three clean, matching the manifest.

### 3. Adversarial case — the one the manifest asked me to check carefully

**Question:** does excluding-by-value create a way to launder a real secret past the scanner
when a *different* `.env` key happens to hold the same string as a declared `base_url`?

**Answer: yes, this is a real (if narrow and currently inert) gap.** `real_values()` filters by
raw value membership in the `public` set (`check_no_secrets.py:50`), with zero connection back to
*which* `.env` key produced that value. Exclusion is value-scoped, not (key, value)-scoped.

Reproduced with an ad hoc script (`tmp_path`, own construction, not from the maker's tests):

```python
# .env:
#   SOME_LOGIN_URL=https://app.example.com/signin       (the intended convenience copy)
#   OAUTH_CALLBACK_SECRET=https://app.example.com/signin (stand-in for a genuinely different secret
#                                                          that coincidentally matches)
# project base_url == https://app.example.com/signin
# an artifact file contains that same string (simulating OAUTH_CALLBACK_SECRET leaking)

values = cns.real_values(tmp_path)
# -> "https://app.example.com/signin" not in values  ==> True (excluded)

outcome = cns.scan([leaked_artifact], values)
# -> outcome[leaked_artifact] == True  ==> reported CLEAN, i.e. the leak is missed
```

Output:
```
real_values excludes the shared value? True
scan result for leaked_artifact (True=clean/no-leak-detected): True
```

This is a genuine regression in scan coverage versus pre-fix behavior: before AT-037's fix, a
coincidentally-identical value was *always* scanned (causing the false positive on
`project.json`, but also correctly catching a genuine coincidental leak of that same string under
a different key). After the fix, that value is invisible to the scanner everywhere, for any key.

**Live-repo check (structural only — did not print any secret value):** confirmed the current
`.env` has no such collision right now (2 declared base_urls, 0 keys sharing a base_url's exact
value across multiple keys). So this is a **latent design gap, not an active leak** in this repo
today.

**Severity call:** low. It requires a real credential to be byte-identical to a project's public
sign-in URL, which is very unlikely for a generated token/password, and it does not currently
exist in this repo's `.env`. The stated goal of this unit (fix the `project.json` false positive,
verified by 3 tests plus my reproduction) is met and does not regress anything the existing tests
or contract cover. I am not failing the cycle over a non-active, low-probability edge case the
maker's own manifest explicitly asked the checker to scrutinize (and got half-right — the
substring case is genuinely closed; the same-value-different-key case was missed by both the
maker's reasoning and its test suite).

**Action taken:** filed `AT-038` in `qa/issues.jsonl` (severity low, status open) with the full
adversarial reproduction and a fix direction (scope exclusion to specific `.env` keys known to
mirror a base_url, not to the bare value). Also flipped `AT-037`'s ledger row from
`fixed`/`verified_date: null` to `verified`/`verified_date: 2026-09-04` since this cycle's
independent reproduction confirms the stated fix.

## Verdict

**PASS** — cycle 1. The fix is correctly scoped, exact-match only, does not weaken C5 for any
value currently in this repo's `.env`, and is proven by both the maker's tests and my own
independent reproduction (including the adversarial one requested). A new low-severity issue
(AT-038) is filed for the residual value-vs-key-provenance gap; it does not block this unit.

**Cycle checked: 1**
