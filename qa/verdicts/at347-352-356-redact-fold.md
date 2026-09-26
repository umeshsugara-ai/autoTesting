# Verdict — at347-352-356-redact-fold

**Date:** 2026-09-26 · **Cycle checked:** 1 · **Checker:** claude-sonnet-subagent (primary; independent of `.b.md`)
**Base:** bb4be39 (merge-base with origin/master)

```
VERDICT: FAIL
SCOREBOARD: AT-347 and AT-356 mechanisms met; AT-352 (encoded spellings) NOT met — base64 embedded next to token-alphabet characters bypasses both doors
FAILURES:
- [AT-352 / B2] sev: medium→high (security gate) · _B64_TOKEN_RE = r"[A-Za-z0-9+/_-]{8,}={0,2}" (src/autotester/core/redact_fold.py:191) swallows adjacent `_`, `-` and alphanumerics into one greedy span; the whole-span decode fails, and the credential escapes BOTH Redactor.contains_folded (UI door) and assert_no_raw_secrets (model gate). Reproduced: `filename_<b64>.png`, `prefix_<b64>_suffix`, `prefix-<b64>-suffix`, `prefixXX<b64>YYsuffix` → BYPASS. Hex has a narrower form of the same flaw (`abc<hex>def`). · Fix: substring-match each declared secret's own precomputed encodings (b64 at its 3 alignment offsets, std + urlsafe, b32, hex upper/lower) instead of decoding greedy regex spans; or retry decode over shrinking windows. · issue: AT-352
CAPABILITY-COVERAGE: 8/8 rows reproduced (own copy c347a-baseline, 29 passed green-before; each mutation red on its named rows only; byte-identical after revert)
LIVE-BROWSER: not-applicable (changed paths: core/redact.py, core/redact_fold.py, tests/test_core.py, docs/MAP.md — no UI surface)
ISSUES-WRITTEN: none new (the finding stays under AT-352, open)
EXECUTOR: maker builder (checker: claude-sonnet-subagent)
EXPLANATION: The fold is real and well isolated: all 8 capability rows falsify cleanly, the public names of core.redact still import for every in-tree importer, the diff matches "What changed", and a 50 KB realistic corpus produced no false positives (~0.21 s/call, roughly linear). Raising, not warning, is contract-mandated (browser-and-secrets B2). But AT-352's own scope, base64, has a realistic bypass (an id-derived filename), so the cycle cannot close. The independent .b.md check reached the same finding by another route (b32/hex adjacency too) — fix both in one cycle.
```

## Security probes (primary)
ZWJ-separated caught · fullwidth caught · double-percent caught · split across newline caught · case variants caught · **base64 mid-word MISSED**. Delimiters outside the token alphabet (space, `:`, `/`, `&`, `=`) bound the match correctly.

## Re-run evidence
- `uv run pytest tests/test_core.py tests/test_secrets.py tests/test_ui_secrets_declaration.py tests/test_check_no_secrets.py -p no:cacheprovider` → 76 passed
- `uv run pytest tests/test_db.py tests/test_network_assertions.py tests/test_portal_persona.py tests/test_run_trace.py tests/test_source_adapters_drive.py tests/test_prompt_skills.py -p no:cacheprovider` → 56 passed, 1 skipped
- ruff: All checks passed · doctor: clean · redact.py 136 lines, redact_fold.py 277 lines
- Mutation rows (tests/test_core.py): combining 3 red · base64 2 · base32 2 · hex 2 · html-entities 4 · reversed 2 · double-percent 2 · gate-itself 9 red (UI door test stays green)
- Diff scope: `git diff bb4be39..HEAD --stat` → docs/MAP.md, manifest, core/redact.py, core/redact_fold.py (new), tests/test_core.py (+98/-0, additive). Nothing outside the manifest.
