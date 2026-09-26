# Verdict (B — independent second check) — at347-352-356-redact-fold

**Date:** 2026-09-26 · **Head checked:** 0c56c5b (fix a95ca6a, base bb4be39) · **Cycle checked: 1** · **Issues addressed (claimed):** AT-347, AT-352, AT-356
**Independence:** a blind checker subagent that never read the primary verdict. The orchestrating checker reproduced the failing case itself before writing this file.

```
VERDICT: FAIL
SCOREBOARD: 22/22 whole-secret obfuscations caught (NFKD, combining marks, fullwidth, zero-width, reversed, HTML named/numeric/hex entities, percent x1/x2/x3, base64/base32/hex whole, case variants, whitespace-split); no false positive on ~53 KB of prose/JSON/data-URI/hash text (~0.27 s); FAILS the embedded mid-token encoded family the unit claims to cover
FAILURES:
- [AT-352 / AT-347] sev: high · an encoded credential embedded next to characters of its own encoding alphabet bypasses assert_no_raw_secrets (and contains_folded). _B64_TOKEN_RE / _B32_TOKEN_RE / _HEX_TOKEN_RE in core/redact_fold.py match greedily across the neighbours, so the single oversized run fails to decode and the secret is never recovered. The unit's own docstring claims to "scan for base64/base32/hex-shaped runs inside a larger string". · fix: when a whole-run decode fails, also try the sub-runs, bounded by the encoded length of each declared secret (e.g. slide a window of exactly len(encode(secret)) and its padding variants over each run); or search for each secret's own encodings directly (compute b64/b32/hex of every declared secret, plus the 3 base64 alignment offsets, and do substring matching), which is exact, cheap and immune to adjacency. Add parametrized tests for tok_<b64>_end, prefix<b64>suffix, SECRET<b32>CODE and cafe<hex>beef. · issue: AT-352 (stays open)
CAPABILITY-ISOLATION: 3/3 own falsifying edits red on the named assertions (Mn strip removed; base64 decode removed; assert_no_raw_secrets reverted to exact-match), each green before in an own-venv copy
LIVE-BROWSER: not-applicable (changed paths: core/redact.py, core/redact_fold.py, tests/test_core.py, docs/MAP.md)
ISSUES-WRITTEN: none (AT-352 stays open with this evidence)
EXECUTOR: claude-sonnet-subagent (checker B: claude-sonnet subagent; reproduction: claude-opus-session)
EXPLANATION: The fold and whole-token decoding are solid, with no false positives. But ordinary variable-name-style adjacency (tok_…_end) defeats the embedded-encoding scan, and that is exactly the AT-352 shape this gate exists to close before a prompt reaches an external model.
```

## Orchestrator reproduction (own run, the c347b-1 copy, whose core/ matches the worktree)

Secret `Sup3rS3cretValue!42`, gate `assert_no_raw_secrets(text, [secret])`:

```
b64 isolated         caught (ValueError)
b64 tok_x_end        MISS
b64 prefix/suffix    MISS
b32 isolated         caught (ValueError)
b32 SECRETxCODE      MISS
hex isolated         caught (ValueError)
hex cafe..beef       MISS
```

## Also noted (low, not scored)

`ASCII_CONFUSABLES` was a public name in the pre-split `core/redact.py`. `from autotester.core.redact import ASCII_CONFUSABLES` now raises ImportError, although the manifest says every previous import still resolves. No current caller exists (grepped). Re-export it, or state the change.

## Status: FAIL (cycle 1)
