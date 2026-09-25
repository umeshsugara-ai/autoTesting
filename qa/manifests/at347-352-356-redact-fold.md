# Manifest — at347-352-356-redact-fold
**Contract:** qa/contracts/core-invariants.md C5 (secrets never reach a model, log, or artifact) ·
qa/contracts/browser-and-secrets.md B2 ("any string headed for a provider passes
`core.redact.assert_no_raw_secrets` first")
**Goal task:** none (security-hardening fix against open checker findings)
**Date:** 2026-09-25
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-347 (medium, open), AT-352 (medium, open), AT-356 (medium, open)

## Issues addressed

- **AT-347** — `core.redact.assert_no_raw_secrets`, the hard gate before every model prompt
  (`browser/secrets.py::SecretStore.guard_prompt` is its only caller path), tested `value in text`
  only. A folded/case/punctuation-varied spelling of a live credential reached an external model
  provider verbatim even though the UI intake door (`Redactor.contains_folded`) already folded.
- **AT-352** — that fold itself covered only the literal text, so a credential spelled in base64,
  base32, hex, HTML numeric/hex entities, double percent-encoding, or plain reversal passed both
  the UI door and (once AT-347 is fixed) would still have passed the model-prompt door.
- **AT-356** — a credential with a VISIBLE combining mark interleaved between every character
  (U+0301 combining acute, U+0335 combining short stroke overlay) rendered legibly (accented /
  struck-through) but was not `Default_Ignorable`, so `_is_ignorable` correctly left it alone
  (that is AT-351's fix, not a gap in it) and the fold never stripped it.

## What changed

- `src/autotester/core/redact_fold.py` (new file) — the folding/decoding internals, split out of
  `redact.py` because the fix would otherwise cross the C2 300-line cap:
  - `fold_credential` (redact_fold.py:139) — switched from NFKC to **NFKD-then-strip-`Mn`**
    (AT-356). NFKD decomposes a precomposed accented character the same way a hostile decomposed
    spelling already arrives, so stripping every remaining `Mn` mark afterward is symmetric on
    both sides — unlike stripping `Mn` *before* composition (AT-351's rejected approach, which
    made a decomposed hostile spelling lose its accent while a precomposed stored value kept its).
  - `_decode_block` (redact_fold.py:196), `_obfuscated_spellings` (redact_fold.py:215),
    `_B64_TOKEN_RE`/`_B32_TOKEN_RE`/`_HEX_TOKEN_RE` (redact_fold.py:191-193) — new. Reversed,
    HTML-unescaped, up to 4 passes of percent-decoded, and base64/base32/hex-decoded candidate
    spellings of the input (AT-352). Percent-decoding, HTML-unescape and reversal are substring-
    safe and run once over the whole text; base64/base32/hex are not (a decoder needs the *entire*
    input to be valid alphabet), so those three additionally scan for base64/base32/hex-**shaped**
    runs inside a larger string and decode each — needed because `assert_no_raw_secrets`'s real
    callers pass full prompt text, not bare field values, and an embedded encoded credential broke
    whole-text decoding in testing (see Actual outputs below).
  - `_contains_folded_secret` (redact_fold.py:261) — new. Folds the text and every
    `_obfuscated_spellings` candidate, checks each against the caller's already-folded,
    `MIN_FOLDED_LEN`-gated secret list. One shared implementation for both hard gates.
- `src/autotester/core/redact.py` (rewritten as the thin public façade + gate logic):
  - `Redactor.contains_folded` (redact.py:83) now delegates to `_contains_folded_secret` — same
    method name/signature, strictly widened behaviour (AT-352 fix reaches the UI door for free,
    since `ui/credential_guard.py` already calls this method — no other file needed editing).
  - `assert_no_raw_secrets` (redact.py:112) — AT-347's actual fix: after the existing floorless
    exact check, it now also folds `text` and its secrets and raises on a widened match, using the
    same `MIN_FOLDED_LEN` floor `Redactor` already applies (so a short secret stays exact-match
    only, per AT-002).
  - `__all__` + re-exports (redact.py:15-35) so `BIDI_OVERRIDES`, `fold_credential`,
    `MIN_FOLDED_LEN` and everything else any other module imports from `autotester.core.redact`
    still resolves — no other file's import line changed.
- `tests/test_core.py` — 12 new tests: `test_fold_credential_strips_visible_combining_marks_after_decomposition`,
  `test_fold_credential_keeps_precomposed_and_decomposed_accents_symmetric` (AT-351 regression),
  parametrized `test_contains_folded_catches_encoded_and_reversed_spellings` (7 cases),
  parametrized `test_assert_no_raw_secrets_blocks_obfuscated_spelling_in_prompt_text` (9 cases,
  each payload embedded in a sentence, matching real caller shape),
  `test_assert_no_raw_secrets_does_not_false_positive_on_ordinary_prose`,
  `test_assert_no_raw_secrets_short_secret_stays_floorless_on_exact_match` (AT-002 regression).
- `docs/MAP.md` — regenerated (`autotester map`); one new row for `core/redact_fold.py`.

## Red-first (throwaway copy, current code, before any edit)

Scratch dir (outside the worktree): `probe_red.py` imported the **unfixed**
`src/autotester/core/redact.py` (copied out, never edited in place) via `importlib` and ran the 9
target vectors through both `Redactor.contains_folded`/`is_clean` and `assert_no_raw_secrets`
(payload embedded in a sentence, matching the real caller shape):

```
BYPASS  base32                           ui_guard_caught=False model_gate_raised=False
BYPASS  base64                           ui_guard_caught=False model_gate_raised=False
BYPASS  combining-acute-U+0301           ui_guard_caught=False model_gate_raised=False
BYPASS  combining-short-stroke-U+0335    ui_guard_caught=False model_gate_raised=False
BYPASS  double-percent                   ui_guard_caught=False model_gate_raised=False
BYPASS  hex                              ui_guard_caught=False model_gate_raised=False
BYPASS  html-dec-entities                ui_guard_caught=False model_gate_raised=False
BYPASS  html-hex-entities                ui_guard_caught=False model_gate_raised=False
BYPASS  plain-reversed                   ui_guard_caught=False model_gate_raised=False

ANY BYPASS FOUND: True
```

All 9 confirmed red before the fix landed.

## How to verify

- `uv run pytest tests/test_core.py tests/test_secrets.py tests/test_ui_secrets_declaration.py tests/test_check_no_secrets.py`
- `uv run pytest tests/test_db.py tests/test_network_assertions.py tests/test_portal_persona.py tests/test_run_trace.py tests/test_source_adapters_drive.py tests/test_prompt_skills.py` (other `Redactor`/`assert_no_raw_secrets`/`PLACEHOLDER_RE` importers, to confirm the public surface stayed compatible)
- `uv run ruff check src tests scripts`
- `uv run autotester doctor`

## Actual outputs (maker's run, commit a95ca6a)

```
$ uv run pytest tests/test_core.py tests/test_secrets.py tests/test_ui_secrets_declaration.py tests/test_check_no_secrets.py
........................................................................ [ 94%]
....                                                                     [100%]
76 passed, 1 warning in 3.50s
```

```
$ uv run pytest tests/test_db.py tests/test_network_assertions.py tests/test_portal_persona.py tests/test_run_trace.py tests/test_source_adapters_drive.py tests/test_prompt_skills.py
.....s...................................................                [100%]
56 passed, 1 skipped, 5 warnings in 6.62s
```
(1 skip and the 5 warnings are pre-existing/unrelated — `test_run_trace.py`'s AT-561 no-`secrets=`
fixture warning — not caused by this change.)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Full non-browser suite: NOT RUN.** RAM was ~0.7-1.2 GB free throughout this session (measured via
`Get-CimInstance Win32_OperatingSystem`), below the 3.5 GB ceiling for a full-suite run. Declared
gap per the dispatch brief. No browser tests run (not applicable to this unit).

## Capability coverage

Mutation-tested in a throwaway scratch copy (`autotester/core/redact.py` + `redact_fold.py` copied
into a standalone mini-package outside the worktree, imported via `sys.path`, never pytest against
a mutated copy — the venv's editable install points at the worktree, and re-pointing it risked
touching tracked state; the runner instead mirrors the exact assertions `tests/test_core.py` makes,
same payloads, same functions, so a checker can re-derive the same result against the real pytest
suite by applying the same one-line edits to the tracked file). Baseline (unmutated) asserted green
first — printed, not just claimed:

```
BASELINE: {'base64': True, 'base32': True, 'hex': True, 'html-entities': True,
           'double-percent': True, 'reversed': True, 'combining-marks': True}
-- all caught, asserted green
```

| capability | falsifying edit (single-hunk, scratch copy only) | check that goes red | other families stay green |
|---|---|---|---|
| AT-356 combining marks (U+0301/U+0335) fold to the plain spelling | `redact_fold.py`: `unmarked = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")` → `unmarked = decomposed` | `combining-marks: True → False` | yes |
| AT-352 base64 (standard + URL-safe) | remove both `base64.b64decode(...)`/`base64.urlsafe_b64decode(...)` `out.append` lines in `_decode_block` | `base64: True → False` | yes |
| AT-352 base32 | remove `base64.b32decode(...)` `out.append` line | `base32: True → False` | yes |
| AT-352 hex | remove `bytes.fromhex(...)` `out.append` line | `hex: True → False` | yes |
| AT-352 HTML numeric/hex entities | `forms = [text[::-1], html.unescape(text)]` → `forms = [text[::-1]]` | `html-entities: True → False` | yes |
| AT-352 double (and triple) percent-encoding | `for _ in range(4)` → `for _ in range(1)` (single decode pass) | `double-percent: True → False` | yes |
| AT-352 plain reversal | `forms = [text[::-1], html.unescape(text)]` → `forms = [html.unescape(text)]` | `reversed: True → False` | yes |
| AT-347 — `assert_no_raw_secrets` itself became fold-aware (not just the UI door) | reverted `assert_no_raw_secrets`'s body in `redact.py` to its pre-fix exact-match-only form | **every** family flips to red on the model-gate side alone (UI door still catches; the AND collapses every row) | n/a — this row IS the cross-family check |

Full runner output (`mutation_runner.py`, scratch dir):

```
combining-marks  targeted_check_red=True  other_checks_still_green=True
base64           targeted_check_red=True  other_checks_still_green=True
base32           targeted_check_red=True  other_checks_still_green=True
hex              targeted_check_red=True  other_checks_still_green=True
html-entities    targeted_check_red=True  other_checks_still_green=True
double-percent   targeted_check_red=True  other_checks_still_green=True
reversed         targeted_check_red=True  other_checks_still_green=True
AT-347-gate-itself targeted_check_red=True  (every family red because assert_no_raw_secrets stopped folding)

ALL FAMILIES PROPERLY DEFENDED: True
```

One false start recorded rather than hidden: the first base64 mutation removed only
`base64.b64decode`, and the check stayed GREEN because `base64.urlsafe_b64decode` alone still
decodes this test vector (`ZEBRA_QUILT_APIKEY_31`'s base64 encoding happens to contain no `+`/`/`
characters for `urlsafe_b64decode` to need translating). Widened to a single hunk removing both
lines, which then reddened correctly — noted here rather than only shown fixed, per C7's spirit on
reporting real experiments.

**False-positive check** (not in the family table, but load-bearing for AT-347's own "would this
turn every prompt into a run-killing exception" concern): ~12 KB of ordinary grading-prompt-style
prose with no secret present did not raise (`assert_no_raw_secrets` and `contains_folded` both
returned clean), at ~0.1s per call — see `test_assert_no_raw_secrets_does_not_false_positive_on_ordinary_prose`
in the committed suite.

## LIVE-BROWSER: not-applicable

No UI/route/browser surface touched — `core/redact.py` and `core/redact_fold.py` are pure-Python,
`ui/credential_guard.py` and every other caller are unchanged (they get the AT-352 UI-door fix for
free via `Redactor.contains_folded`, without their own files changing).

## Gaps

- Full non-browser `pytest` suite not run (RAM below the 3.5 GB ceiling all session — declared,
  not silently skipped); targeted files covering every `Redactor`/`assert_no_raw_secrets`/
  `PLACEHOLDER_RE` importer were run instead (13 files, 132 tests total, all green).
- The mutation/capability-coverage run used a standalone script mirroring the pytest assertions
  (same payloads, same functions), not `pytest` itself against a mutated copy, for the reason
  stated above (editable-install path). A checker wanting a literal pytest-attributed kill can
  apply the same one-hunk edits to the tracked file in its own throwaway copy and run
  `tests/test_core.py -k <family>` directly.
- Token-shaped base64/base32/hex scanning (`_B64_TOKEN_RE` etc.) matches any 8+/16+-character
  alphanumeric run, including ordinary English words — deliberate over-triggering (see
  `_obfuscated_spellings`'s docstring): every failed decode contributes nothing, and a decode that
  happens to succeed still has to survive `fold_credential` + the `MIN_FOLDED_LEN`-gated substring
  check. Not scoped as a false-positive risk given the empirical prose check above, but flagged in
  case a checker wants to measure it on a different/larger corpus.
- AT-347's own issue text offered "leave it byte-exact, document the residual" as an equally valid
  alternative to fixing it. This manifest took the fix path per the dispatch brief; if a checker
  judges the availability argument (a false positive now raises inside a model-call path) as
  requiring the WARNING-not-raise shape instead, that is cycle 2's redesign, not a defect in what
  shipped — the false-positive check above found no live case, but the checker's own Mode D/live
  probing is a stronger instrument than this manifest's synthetic prose sample.

## Status: ready-for-check
