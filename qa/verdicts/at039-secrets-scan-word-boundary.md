# Verdict — at039-secrets-scan-word-boundary

**Manifest:** qa/manifests/at039-secrets-scan-word-boundary.md
**Contract:** qa/contracts/core-invariants.md C5
**Cycle checked:** 1

## Verdict: PASS

## Evidence

Regex under test, `scripts/check_no_secrets.py:39`:
`_URL_KEY = re.compile(r"(?:^|_)URL(?:_|$)")`

1. Re-ran the full suite myself:
   ```
   $ uv run pytest tests/test_check_no_secrets.py -v
   tests\test_check_no_secrets.py .....                                     [100%]
   5 passed in 0.26s
   ```
2. `uv run pytest -q` → all green (2 pre-existing skips, unrelated).
3. `uv run ruff check src tests scripts` → All checks passed!
4. `uv run autotester doctor` → doctor: clean
5. `uv run python scripts/check_no_secrets.py projects/pathlynks/project.json` → `scanned 1 file(s); 0 leak(s)` — AT-037's original fix still holds.
6. AT-038's scenario (`test_a_coincidental_non_url_secret_still_flags_even_if_it_matches_a_base_url`) and AT-039's scenario (`test_a_key_that_merely_contains_the_letters_url_is_not_treated_as_a_url_key`) both pass in the same run — both hold simultaneously with AT-037.

## Independent adversarial pass on the regex

Ran the compiled pattern directly against a wider set of keys than the test file covers:

```
SOME_LOGIN_URL        True   (exempt — correct, whole URL token)
URL                   True   (exempt — correct)
LOGIN_URL_BASE        True   (exempt — correct)
HOURLY_BILLING_SECRET False  (not exempt — correct, AT-039's own case)
CURLY_BRACE_KEY       False  (not exempt — correct)
CURL_TOKEN            False  (not exempt — correct; "curl" is not a URL-boundary hit)
ALLOWED_URLS          False  (not exempt — plural breaks the right-hand boundary)
SOME_URLTOKEN         False  (not exempt — concatenated form breaks the right-hand boundary)
_URL                  True   (exempt — correct, degenerate case)
SECURLY               False  (not exempt — correct)
MY_CURLY_SECRET       False  (not exempt — correct)
OAUTH_CALLBACK_SECRET False  (not exempt — correct, AT-038's own case)
```

No case was found where a key that is *not* semantically a URL key wins the exemption. The
failure mode that does exist (`ALLOWED_URLS`, `SOME_URLTOKEN` — genuine URL-ish keys that fail to
qualify because they lack an underscore/start/end boundary around the literal token) only makes
the check *more* conservative: it can cause a legitimate URL value to be reported as a false-positive
LEAK, never allow a real secret to escape detection. That is the safe direction and is not a C5
violation (no-fire list: "Suggestions for future work that no criterion requires").

Structural argument for why this closes the chain: the new regex requires the literal substring
`"URL"` to be present, so its match set is a strict subset of the old `"URL" in k.upper()` check.
A regex that can only ever narrow a broken-too-broad predicate cannot reintroduce a
too-broad-key false exemption (AT-039's failure class) or a too-narrow-value false exemption
(AT-037/AT-038's failure classes, which are governed by the separate value-equality + `public`
set logic, untouched by this change).

## Judgment on iterating further

This specific small tool's exemption logic (base_url value match AND whole-token URL-named key)
is now sound. I did not find a genuine fourth gap, and manufacturing one would be relitigating a
narrowing fix that is provably a subset of its predecessor. Recommend closing this issue chain;
any future finding here should be a materially different failure class, not another boundary
variant of the same key-name check.
