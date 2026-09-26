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

---

# Verdict — at347-352-356-redact-fold, cycle 2 (primary)

**Date:** 2026-09-26 · **Cycle checked:** 2 · **Checker:** claude-sonnet-subagent + orchestrator reproduction

```
VERDICT: FAIL
SCOREBOARD: the cycle-1 adjacency bypass is fixed for b64 (real neighbour bytes, offsets 0-5, and b64("user:"+secret) all caught) and for hex, and ASCII_CONFUSABLES is re-exported; AT-352/AT-347 still open on three gaps in the same mechanism
FAILURES:
- [AT-352 + AT-347 / B2, C5] sev: high · MIN_FOLDED_LEN also gates the exact-encoding search: Redactor.__init__ (redact.py:62-65) and assert_no_raw_secrets (redact.py:134-137) only pass secrets whose FOLDED form is ≥8 on to the encoding search, and _contains_folded_secret returns False when none qualify. A declared 8-char secret with one punctuation mark ("Zq7!kP2x" folds to 7) gets no encoding protection at all, even isolated. Orchestrator reproduced: isolated b64 → MISS on both doors (primary: 70/70 misses across 7 encodings × 10 contexts). · Fix: run the exact-encoding search for every declared secret, gated on the raw value's length or the needle's length rather than the fold floor (the exact search is not a heuristic widening, AT-002's floorless-exact principle). · issue: AT-352
- [AT-352 / B2] sev: medium-high · base32 is only ever uppercase (redact_encodings.py:82-83); lowercase b32 of any secret misses both doors in every context (40/40). Orchestrator reproduced: isolated lowercase b32 → MISS, uppercase → caught. · Fix: also add b32.lower() and the unpadded variants, as hex already does. · issue: AT-352
- [AT-352 / B2] sev: high (from .b.md cycle 2, ab60d4e; orchestrator reproduced) · b32 has no alignment handling: b32encode(prefix+secret) misses both doors at prefix lengths 1-4. · Fix: needles at all 5 byte offsets, mixed edge groups dropped, as for b64. · issue: AT-352
CAPABILITY-COVERAGE: 3/9 rows independently spot-checked (needle-list zeroing, ASCII_CONFUSABLES import) and reproduced; the other 6 rows are unchanged from cycle 1 (8/8 there), and test_core stays 46 passed in the checker's copy
LIVE-BROWSER: not-applicable (core/redact*.py, tests/test_core.py)
ISSUES-WRITTEN: AT-598 (double b64 and UTF-16 hex not covered), AT-599 (a needle split by a newline or MIME wrap is not caught; undisclosed)
EXECUTOR: maker (checker: claude-sonnet-subagent)
EXPLANATION: The precomputed-needle design is sound and fixes cycle 1's adjacency class (b64 alignment and the Basic-auth shape hold). But the fold floor was left in front of it, and b32 got neither case variants nor alignment offsets. False positives: 0 on a 121 KB corpus with secrets on both sides of the floor. Perf: about 0.24 s per call at 50 KB, roughly linear, dominated by the pre-existing _is_ignorable scan. Diff scope is clean: the token regexes and _decode_block are fully removed, every core.redact importer resolves, and files are 142/261/86 lines. The dual check's mixed-case-hex claim did not reproduce (the orchestrator's interleaved-case hex was caught).
```
