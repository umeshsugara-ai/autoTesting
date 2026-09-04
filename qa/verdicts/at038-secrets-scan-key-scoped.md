# Verdict — at038-secrets-scan-key-scoped

**Manifest:** qa/manifests/at038-secrets-scan-key-scoped.md
**Contract:** qa/contracts/core-invariants.md C5
**Cycle checked: 1**

## VERDICT: PASS

## What was checked

1. `qa/contracts/core-invariants.md` C5 — secrets never reach a log/artifact; verify command is
   `uv run pytest tests/test_core.py -q` plus `git ls-files | grep -E "\.env$"` returns nothing.
   `scripts/check_no_secrets.py` is this project's own pre-commit secrets scan, not named
   verbatim in C5 but the concrete mechanism the maker/checker cycle relies on for the same
   guarantee (established in AT-025/AT-037/AT-038's own history).

2. `qa/manifests/at038-secrets-scan-key-scoped.md` — claims `real_values()` now excludes a value
   only when BOTH (a) it matches a public base_url AND (b) its key name contains `"URL"`
   (case-insensitive).

3. `scripts/check_no_secrets.py::real_values()` (lines 38-61), read in full:

   ```python
   values = [
       v for k, v in present.items()
       if v and not (v in public and "URL" in k.upper())
   ]
   ```

   This genuinely checks the `(key, value)` pair, not the value alone — confirmed by reading the
   dict comprehension iterating `present.items()` (key+value together) rather than `present.values()`
   as AT-037's original fix effectively did via `_public_base_urls()`'s value-only set. AT-037's
   original fix (`_public_base_urls()`, lines 21-35) is untouched — still an exact-match set of
   declared `base_url` strings, no substring logic there. The two fixes compose correctly: a value
   must be in the base_url set *and* sit under a URL-marked key to be excluded.

4. `tests/test_check_no_secrets.py::test_a_coincidental_non_url_secret_still_flags_even_if_it_matches_a_base_url`
   (lines 63-84) — reproduces the checker's exact original adversarial scenario faithfully: two
   `.env` keys (`SOME_LOGIN_URL`, `OAUTH_CALLBACK_SECRET`) holding the identical value as a
   declared `base_url`, one artifact file leaking that value, asserting `outcome[leaked] is False`
   (leak caught). This is not weakened or substituted — it is byte-for-byte the scenario AT-038's
   evidence field describes.

## Independent reproduction

```
$ uv run pytest tests/test_check_no_secrets.py -v
tests\test_check_no_secrets.py ....                                      [100%]
4 passed in 0.24s

$ uv run pytest -q
............................................................s..................... [full suite]
2 skipped, rest passed

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run python scripts/check_no_secrets.py projects/pathlynks/project.json
scanned 1 file(s); 0 leak(s)
```

All four commands the manifest cites match what the maker reported. AT-037's original complaint
(`project.json`'s public `base_url` no longer flagged) still holds simultaneously with AT-038's
gap being closed — both true at once, as the manifest's own scope note demanded.

## New adversarial angle attempted (my own, not the manifest's scenario)

The manifest itself flags a residual question: what if a real secret's `.env` KEY name
*coincidentally* contains the substring `"URL"` (its example: `TUMBLR_API_KEY`, `OAUTH_URL_TOKEN`)
but the value is not actually a URL? I constructed a `tmp_path` reproduction using a key that
contains `"URL"` purely as a substring inside an unrelated English word — `HOURLY_BILLING_SECRET`
(`H-O-U-R-L-Y` contains the letters `u-r-l` consecutively) — holding a value identical to a
declared `base_url`:

```python
(tmp_path / ".env").write_text(
    "SOME_LOGIN_URL=https://app.example.com/signin\n"
    "HOURLY_BILLING_SECRET=https://app.example.com/signin\n",
    encoding="utf-8",
)
# project base_url = https://app.example.com/signin
leaked = tmp_path / "some_artifact.json"
leaked.write_text("secret: https://app.example.com/signin", encoding="utf-8")

values = cns.real_values(tmp_path)
outcome = cns.scan([leaked], values)
```

Result:
```
HOURLY_BILLING_SECRET value in real_values? False   (i.e. excluded from the scan)
outcome[leaked] = True   (i.e. reported CLEAN -- the leak is NOT caught)
```

This reproduces AT-038's exact failure mode (a coincidental value-match escaping detection)
through a different route: `"URL" in k.upper()` is a bare substring test, not a word-boundary
check, so `HOURLY` satisfies it. This directly contradicts the manifest's own safety claim
("a false positive again, but never a false negative — the fail-safe direction is correct") — the
manifest anticipated only the false-positive direction (a legitimate convenience-URL key not
named with `URL`) and asserted no false-negative could occur; this test shows one can.

**Filed as AT-039** (severity `low`, `status: open`) in `qa/issues.jsonl`. Not filed as a blocker
on this unit: it requires two independent coincidences (a key name that happens to contain the
letters `u-r-l` consecutively, AND that key's value happening to collide with a declared
base_url) — today's live repo-root `.env` has zero such keys (confirmed structurally, no live
leak). It is a genuinely different, narrower gap than AT-038 (which required no coincidence at
all — any non-URL-named key was affected), not a reopening of AT-038 under a different name.

## Judgment

- AT-038's specific, filed gap — a value excluded by bare identity regardless of which key held
  it — is **genuinely closed**. The fix checks `(key, value)` together; a password-shaped key
  with no `URL`-like substring is never exempted, exactly as the manifest claims and as I
  independently reproduced with a fresh test of the same scenario in a fresh `tmp_path`.
- AT-037's original fix (project's own `base_url` not flagged in `project.json`) **still holds**
  simultaneously — reproduced independently against the live `projects/pathlynks/project.json`.
- The new heuristic (`"URL" in key.upper()`, a substring test) has a real, narrower residual
  gap — filed as AT-039 — but it is a materially smaller and rarer failure surface than what
  AT-038 closed, and the manifest was transparent that the exclusion is "a heuristic, not a
  schema-enforced contract." Per this checker's own instruction not to let a low-severity
  heuristic trade-off block a PASS when the fix genuinely closes the specific filed gap: it does,
  so this unit **PASSes**, with AT-039 tracked separately for a future cycle (word-boundary check
  instead of substring).

## Evidence sweep

No secret values were pasted or printed anywhere in this verdict, the ad hoc adversarial script,
or `qa/issues.jsonl` — all reproductions used synthetic `tmp_path` fixtures with placeholder
strings (`https://app.example.com/signin`, `hunter2-trombone-staple`-style stand-ins), consistent
with `check_no_secrets.py`'s own design (never accepts/prints a real value as an argument).
