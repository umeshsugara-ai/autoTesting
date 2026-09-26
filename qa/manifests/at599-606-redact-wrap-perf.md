# Manifest — at599-606-redact-wrap-perf (AT-599 + AT-606)

**Unit:** AT-599 (an encoded needle split by a newline or MIME 76-char wrap is missed) + AT-606
(the folded-secret scan is superlinear: 518 KB took 11.8 s). Both filed against the merged
at347-352-356-redact-fold work (`qa/verdicts/at347-352-356-redact-fold.md`).

**Contract:** `qa/contracts/core-invariants.md` (project-wide; C5/C7 especially) and
`qa/contracts/browser-and-secrets.md` (B2/B4 — this is the security credential gate before every
model call).
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk:** skip (backend security, no UI surface)
**Issues addressed:** AT-599 (medium, open → fixed here), AT-606 (medium, open → fixed here).
Neither flipped by me — `qa/issues.jsonl` is the checker's write surface.
**Executor:** claude-sonnet-subagent

## Root cause (found by profiling, not guessed)

Profiled `Redactor.contains_folded` on a ~530 KB synthetic corpus in a throwaway copy before
touching any file (`cProfile`, full table in
`qa/evidence/at599-606-redact-wrap-perf/perf_and_mutation.log`). `_is_ignorable`
(`redact_fold.py:88`, unchanged logic) accounted for 86% of total time: it is called once per
character of every string `fold_credential` folds — the text itself, its reversal, and its
HTML-unescape, so ~1.59M Python-level calls for one 530 KB input — each doing an
`unicodedata.category` lookup plus a fresh `any(...)` generator scanning a 17-tuple ignorable-range
table. That work is O(1) per call but real text repeats the same few hundred distinct characters
far more than it grows, so the *character-by-character Python call overhead* is what scales badly,
not the underlying algorithm. `declared_secret_encodings` (`redact_encodings.py:78`) is a second,
smaller offender: a pure function of one secret string, recomputed from scratch on every single
scrub/gate call regardless of text size.

AT-599 is a separate, correctness (not perf) gap in the same mechanism: `declared_secret_encodings`
needles are literal, case-significant substrings of an encoded secret — exactly what makes them
immune to adjacent characters (AT-352 cycle 2) — but that same literalness means a needle broken by
a `\n`/`\r\n` (deliberately mid-token, or by MIME's fixed 76-character line wrap) no longer appears
as one contiguous substring, so the exact search cannot see it.

## What changed

- **`src/autotester/core/redact_wrap.py`** (new file, 61 lines) — `contains_wrapped_encoding()`:
  strips every line break from `text` and re-runs the exact-encoding needle search
  (`declared_secret_encodings`) against the unwrapped copy. Early-exits before any work when `text`
  has no `\n`/`\r` at all. Split out rather than inlined into `redact_fold.py` because that file was
  already at 292 of its 300-line C2 cap before this unit (same reason `redact_encodings.py` was
  split out of it in AT-352 cycle 2 — a distinct concern, own docstring, own tests).
- **`src/autotester/core/redact_fold.py`**:
  - `:18` `import functools`; `:26` `from autotester.core.redact_wrap import
    contains_wrapped_encoding`.
  - `:90` `@functools.lru_cache(maxsize=4096)` on `_is_ignorable` (AT-606) — pure per-character
    function, so caching changes nothing it returns, only how often the work reruns; docstring note
    added at `:109`.
  - `:295` `_contains_folded_secret` gains one more OR branch after the existing exact-encoding
    search: `if contains_wrapped_encoding(text, widened_secrets, MIN_FOLDED_LEN): return True`
    (AT-599), reusing the same raw-length floor (`MIN_FOLDED_LEN`) the existing exact search already
    uses, per AT-352 cycle 3's "gate the exact search on raw length" ruling.
  - File is now exactly 300 of its 300-line cap (`uv run autotester doctor` confirms clean).
- **`src/autotester/core/redact_encodings.py`**:
  - `:17` `import functools`; `:77` `@functools.lru_cache(maxsize=256)` on
    `declared_secret_encodings` (AT-606) — pure function of `value` alone; callers only ever
    iterate the returned list, never mutate it, so sharing the cached list is safe. Docstring note
    at `:113`.
- **`tests/test_redact_wrap_perf.py`** (new file, 148 lines) — split out of
  `tests/test_redact_obfuscation.py` (already at 290 of its own 300-line cap) rather than added
  there: 8 AT-599 detection tests (mid-token newline × {base64, hex} × {`\n`, `\r\n`} where
  applicable, plus real MIME 76-char wrapping via `base64.encodebytes`, each through both
  `contains_folded` and `assert_no_raw_secrets`), 1 benign-wrapped-prose negative test, and 2
  AT-606 perf tests (absolute bound, growth ratio).

No other file touched. `docs/MAP.md` regenerated (`autotester map`) because `doctor` flagged it
stale from the new module; no `docs/ARCHITECTURE.md` prose change (no new concept row —
`redact_wrap.py` is an internal implementation detail of the same "secret redaction" concept
`redact.py`/`redact_fold.py`/`redact_encodings.py` already occupy, same as the AT-352 cycle-2
split did not add a row either).

## Verify — actual outputs

```
$ uv run pytest tests/test_actuator_chokepoint.py tests/test_cli_orchestrate.py tests/test_core.py \
    tests/test_coverage.py tests/test_db.py tests/test_execute.py tests/test_ids.py \
    tests/test_network_assertions.py tests/test_onboard_pathlynks.py \
    tests/test_parallel_run_evidence_namespace.py tests/test_portal_persona.py \
    tests/test_prompt_skills.py tests/test_redact_obfuscation.py tests/test_redact_wrap_perf.py \
    tests/test_run_pathlynks_first_cases.py tests/test_run_trace.py tests/test_secrets.py \
    tests/test_source_adapters_drive.py tests/test_ui_error_pages.py tests/test_ui_runs_parallel_trace.py
218 passed, 1 skipped, 6 warnings in 4.95s
```

(Every test file under `tests/` whose contents mention "redact" — confirmed via
`grep -rl redact tests/*.py`, 20 files including `test_ids.py` itself (it mentions "redact" only in
a comment about its own split-out history) — plus `test_core.py`, both named explicitly in the
brief. The 1 skip and 6 warnings are pre-existing and unrelated — AT-561's disclosed `TraceWriter`
fallback warning in `test_run_trace.py`, not touched by this unit.)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

### Before/after timing (AT-606)

Same 500 KB corpus (`tests/test_redact_wrap_perf.py::_make_corpus`, fixed seed), same 5 secrets,
`contains_folded` + `assert_no_raw_secrets` combined:

| state | 500 KB combined call |
|---|---|
| BEFORE (both `@lru_cache` decorators removed, reproducing the pre-fix code exactly) | **4.19s** |
| AFTER (this unit's code) | **0.619s** |

Cold-process (fresh interpreter per row, no warm-cache carryover), `contains_folded` alone, AFTER:

| size | time | ratio vs previous row |
|---|---|---|
| 250 KB | 0.353s | — |
| 500 KB | 0.670s | 1.90x for 2x size |
| 1000 KB | 1.504s | 2.25x for 2x size |

Full profiling table and methodology: `qa/evidence/at599-606-redact-wrap-perf/perf_and_mutation.log`.

## Capability coverage (each claim → its isolating, single-hunk falsifying edit)

| claim | falsifying edit | test | before | after |
|---|---|---|---|---|
| A wrapped encoded needle (mid-token newline or MIME wrap) is caught by `contains_folded`/`assert_no_raw_secrets` (AT-599) | `redact_fold.py:295` `if contains_wrapped_encoding(text, widened_secrets, MIN_FOLDED_LEN): return True` → `if False:  # AT-599 SABOTAGE\n        return True` | `tests/test_redact_wrap_perf.py` (8 AT-599 detection tests) | 11 passed | **8 failed** (all 8 AT-599 detection tests, by name), 3 unrelated tests (negative + 2 perf) stayed green |
| The 500 KB scan stays under a generous bound (AT-606) | `redact_fold.py:90` remove `@functools.lru_cache(maxsize=4096)`, and `redact_encodings.py:77` remove `@functools.lru_cache(maxsize=256)` (anchors matched exactly once each, both files changed) | `test_redact_scan_stays_under_a_generous_bound_on_a_500kb_corpus` | 1 passed (0.619s) | **FAIL**: `500 KB scan took 4.19s, expected under 3s` |

Both edits reverted after the run; `diff` against the worktree's committed files exits 0
(byte-identical) for all four touched files.

**INCONCLUSIVE, disclosed per core-invariants.md C7:** the same AT-606 mutation above did NOT kill
`test_redact_scan_time_roughly_doubles_not_quadruples_with_input_size` at its own sizes (250 KB /
500 KB) — the large/small ratio was ~2.04x even with both caches removed, so growth stays close to
linear in that specific window on this machine even for the pre-fix code. The sibling bound test's
kill is what shows this test file is not vacuous; the ratio test is kept because the brief asks for
it and it remains a real assertion (it would fire on a return to the checker's originally measured
49x-for-10x-size magnitude of superlinearity), just not independently proven-killed by this one
mutation at this size window. Not reported as "the test is vacuous" — the property C7 forbids
inferring from a single zero-failure result.

**No isolating falsification for the benign-wrapped-prose negative test**
(`test_line_wrapped_benign_prose_has_no_false_positive`) — its job is to show the fix does NOT fire
on ordinary line-wrapped text, and the only mutation that would meaningfully break it is loosening
`contains_wrapped_encoding`'s exact-substring match into something fuzzier, which is not a change
this unit makes anywhere. Same shape as the "revert_op: none" rows other manifests in this repo
record for pure guard/negative tests (e.g. `qa/manifests/at521-finish-the-q-sweep.md`).

## Live browser evidence

Not UI-touching. Changed paths: `src/autotester/core/redact_wrap.py` (new),
`src/autotester/core/redact_fold.py`, `src/autotester/core/redact_encodings.py`,
`tests/test_redact_wrap_perf.py` (new), `docs/MAP.md` (regenerated),
`qa/manifests/at599-606-redact-wrap-perf.md`,
`qa/evidence/at599-606-redact-wrap-perf/perf_and_mutation.log`.

## Known limits (disclosed, not claimed)

- **AT-598** (double base64 encoding and UTF-16 hex not covered) and **AT-607** (a raw secret of 7
  or fewer characters gets no encoding protection by design; an 8-character secret misses base32
  only at alignment offset 1) both stay open and out of scope — neither is touched by this unit.
- The AT-606 fix targets the specific hot path profiling identified (`_is_ignorable` and
  `declared_secret_encodings`); it does not restructure `fold_credential`'s NFKD-decompose-then-
  strip-`Mn` pass or `_obfuscated_spellings`' percent-decode loop, which the profile showed were not
  the dominant cost on this corpus. A corpus with very different character diversity (e.g. many
  distinct non-ASCII code points, defeating the `lru_cache`'s hit rate) would see a smaller speed-up
  than the ~7x measured here, though still no worse than the pre-fix baseline.
- `contains_wrapped_encoding` (AT-599) strips line breaks unconditionally across the whole text,
  not only inside runs that already look base64/hex/base32-shaped, because a wrapped needle by
  definition does not look encoded yet on either side of the break. The false-positive risk this
  could reopen is bounded, not eliminated by construction: it needs the exact needle bytes (still an
  8+ character case-significant substring of a real secret's computed encoding) to reappear right at
  a line join by coincidence, which `test_line_wrapped_benign_prose_has_no_false_positive` probes
  once but does not exhaustively rule out for every possible text.
- The ratio-based perf test's mutation status is INCONCLUSIVE at its own two sizes, as disclosed
  above in Capability coverage — it is a real, brief-requested assertion, not a proven-killed one.

## Status: ready-for-check
