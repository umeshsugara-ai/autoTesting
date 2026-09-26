# Manifest — at347-352-356-redact-fold
**Contract:** qa/contracts/core-invariants.md C5 (secrets never reach a model, log, or artifact) ·
qa/contracts/browser-and-secrets.md B2 ("any string headed for a provider passes
`core.redact.assert_no_raw_secrets` first")
**Goal task:** none (security-hardening fix against open checker findings)
**Date:** 2026-09-25 (cycle 1) / 2026-09-26 (cycle 2)
**Fix cycle:** 2 of 3
**Dual check:** no
**Issues addressed:** AT-347 (medium, open), AT-352 (medium, open), AT-356 (medium, open)

## Cycle 2 — both cycle-1 verdicts were FAIL

`qa/verdicts/at347-352-356-redact-fold.md` (primary, commit 010c2e2) and
`qa/verdicts/at347-352-356-redact-fold.b.md` (independent blind second, commit e956664) both FAILed
cycle 1 on the same root cause, found independently by two different routes. This section answers
every finding of both verdicts, one row per finding, before the rest of this manifest (which is
cycle 1's original text, kept as history rather than rewritten) is read.

| Verdict finding | Where | Answer |
|---|---|---|
| Primary: `_B64_TOKEN_RE = r"[A-Za-z0-9+/_-]{8,}={0,2}"` swallows adjacent `_`, `-` and alphanumerics into one greedy span; whole-span decode fails; bypasses both doors. Repro: `filename_<b64>.png`, `prefix_<b64>_suffix`, `prefix-<b64>-suffix`, `prefixXX<b64>YYsuffix`; hex has a narrower form (`abc<hex>def`). | `src/autotester/core/redact_fold.py` (cycle 1) | **Fixed.** Removed `_B64_TOKEN_RE`/`_B32_TOKEN_RE`/`_HEX_TOKEN_RE`/`_decode_block` entirely — the decode-the-text-then-compare direction is gone for these three encodings. Replaced with `redact_encodings.declared_secret_encodings(value)`: precompute the DECLARED secret's own base64 (std + URL-safe, 3 byte-alignment offsets, padding-free — `_base64_alignment_needles`), base32, and hex (upper+lower) encodings, and search for each as an exact literal substring of the raw text. Substring search doesn't care what sits next to the match, so adjacency can't break it. |
| Blind second (independent route): same family — `tok_<b64>_end`, `prefix<b64>suffix`, `SECRET<b32>CODE`, `cafe<hex>beef` all MISS in the orchestrator's own reproduction (`Sup3rS3cretValue!42`). | same | **Fixed**, same change — re-verified with the checker's own secret value and exact failing shapes (see Cycle 2 verification below); all 8 named repro strings from both verdicts now caught by both doors. |
| Blind second, "Also noted": `ASCII_CONFUSABLES` was public on pre-split `core/redact.py`; `from autotester.core.redact import ASCII_CONFUSABLES` now raises `ImportError`. No current caller, but the manifest claimed every prior import still resolved. | `src/autotester/core/redact.py` | **Fixed.** `ASCII_CONFUSABLES` added to `redact.py`'s import-from-`redact_fold` block and `__all__`. Pinned by `tests/test_core.py::test_ascii_confusables_still_importable_from_redact`. |
| Both verdicts: capability coverage (8/8 rows), no false positives (50-53 KB corpora), diff scope, and raise-not-warn (B2) all held — no change requested there. | — | Unchanged from cycle 1; re-verified this cycle (see below), nothing regressed. |

### What changed in cycle 2

- `src/autotester/core/redact_fold.py` — `_B64_TOKEN_RE`, `_B32_TOKEN_RE`, `_HEX_TOKEN_RE`,
  `_decode_block` removed; `_obfuscated_spellings` now only produces reversed / HTML-unescaped /
  percent-decoded candidates (all substring-safe, unchanged behaviour, per the brief: "keep
  reversed, HTML and percent-encoded handling as it is"). `_contains_folded_secret`'s signature
  changed from `(text, folded_secrets: Sequence[str])` to
  `(text, widened_secrets: Sequence[tuple[str, str]])` — `(raw_value, folded_value)` pairs, because
  the new exact-encoding search needs the RAW secret bytes (folding would destroy base64's
  case-significant output), checked first, before falling through to the existing fold-based check.
- `src/autotester/core/redact_encodings.py` (new file) — `_base64_alignment_needles` (the
  YARA-style 3-offset technique: pad the secret with 0/1/2 leading zero bytes standing in for
  "however many unknown bytes precede it", pad the tail to a multiple of 3 so no `=` appears, drop
  the leading/trailing 4-character group whenever it mixes in an unknown byte — correctness over a
  couple of characters of needle length) and `declared_secret_encodings` (base64 std+urlsafe via
  the above, plus base32 and hex upper/lower).
- `src/autotester/core/redact.py` — `Redactor.__init__` now builds `self._widened: list[tuple[str,
  str]]` (was `self._folded: list[str]`) so both the raw value and its fold travel together;
  `contains_folded` and `assert_no_raw_secrets` pass `_widened`/`widened` through unchanged
  otherwise. `ASCII_CONFUSABLES` re-exported (see table above).
- `tests/test_core.py` — added `test_ascii_confusables_still_importable_from_redact`, and two new
  parametrized tests covering the exact 8 failing inputs named across both verdicts
  (`test_contains_folded_catches_encoded_secret_next_to_its_own_alphabet` and
  `test_assert_no_raw_secrets_blocks_encoded_secret_next_to_its_own_alphabet`, one door each).
- `docs/MAP.md` — regenerated; new row for `core/redact_encodings.py`.

### Cycle 2 verification

Reproduced the checker's own secret (`Sup3rS3cretValue!42`) and all 8 named failing inputs plus the
3 isolated (non-adjacent) forms, through both doors, in a throwaway scratch copy before touching the
tracked worktree:

```
OK   filename_<b64>.png       ui=True  gate=True
OK   prefix_<b64>_suffix      ui=True  gate=True
OK   prefix-<b64>-suffix      ui=True  gate=True
OK   prefixXX<b64>YYsuffix    ui=True  gate=True
OK   tok_<b64>_end            ui=True  gate=True
OK   SECRET<b32>CODE          ui=True  gate=True
OK   cafe<hex>beef            ui=True  gate=True
OK   abc<hex>def              ui=True  gate=True
OK   isolated b64             ui=True  gate=True
OK   isolated b32             ui=True  gate=True
OK   isolated hex             ui=True  gate=True

ALL CAUGHT: True
```

Re-ran every cycle-1 vector (`CRED = "ZEBRA_QUILT_APIKEY_31"`) to confirm no regression — still all
9 CAUGHT (base64/base32/hex isolated, html dec/hex entities, double-percent, plain-reversed,
combining-acute, combining-short-stroke) — and the ~12-15 KB false-positive prose check (this time
including filename/token-shaped decoys like `filename_abcxyz123.png`, `cafefeedbeefdeadf00dbabe1234`
to specifically probe the new needle search for over-triggering) still raised nothing, ~0.07 s.

```
$ uv run pytest tests/test_core.py
46 passed in 0.24s

$ uv run pytest tests/test_core.py tests/test_secrets.py tests/test_ui_secrets_declaration.py tests/test_check_no_secrets.py tests/test_db.py tests/test_network_assertions.py tests/test_portal_persona.py tests/test_run_trace.py tests/test_source_adapters_drive.py tests/test_prompt_skills.py
149 passed, 1 skipped, 6 warnings in 4.19s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

(The 1 skip and 6 warnings are the same pre-existing/unrelated `test_run_trace.py` AT-561 items
noted in cycle 1 — not caused by this change.)

**Full non-browser suite: still NOT RUN.** RAM measured 0.7-1.7 GB free at various points this
session (`Get-CimInstance Win32_OperatingSystem`), never reaching the 3.5 GB ceiling. Same declared
gap as cycle 1.

### Cycle 2 capability coverage (mutation-tested, scratch copy only)

Same method as cycle 1 (throwaway mini-package under scratch, `sys.path`-imported, never pytest
against a mutated copy — see cycle 1's note on why). Baseline asserted green first:

```
BASELINE: {'combining-marks': True, 'html-entities': True, 'double-percent': True, 'reversed': True,
           'base64-isolated': True, 'base32-isolated': True, 'hex-isolated': True,
           'base64-adjacent': True, 'base64-adjacent-filename': True, 'base32-adjacent': True,
           'hex-adjacent': True} -- all caught, asserted green
```

| capability | falsifying edit (single-hunk, scratch copy only) | targeted rows go red | others stay green |
|---|---|---|---|
| combining marks (AT-356, re-verified) | `redact_fold.py`: strip-`Mn` line → no-op | `combining-marks` | yes |
| HTML entities (re-verified) | `forms = [text[::-1], html.unescape(text)]` → drop `html.unescape` | `html-entities` | yes |
| double/triple percent-decoding (re-verified) | `range(4)` → `range(1)` | `double-percent` | yes |
| plain reversal (re-verified) | drop `text[::-1]` from `forms` | `reversed` | yes |
| base64 needle search (std+urlsafe, all offsets) — **new** | `redact_encodings.py`: `needles: list[str] = [...]` → `needles: list[str] = []` | `base64-isolated`, `base64-adjacent`, `base64-adjacent-filename` (all 3, one hunk) | yes |
| base32 needle search — **new** | `redact_encodings.py`: drop the `b32 = ...` / `needles.extend((b32, ...))` lines | `base32-isolated`, `base32-adjacent` | yes |
| hex needle search — **new** | `redact_encodings.py`: drop the `hexed = ...` / `needles.extend((hexed, ...))` lines | `hex-isolated`, `hex-adjacent` | yes |
| AT-347 gate itself (re-verified against the new `_widened`-pair signature) | `redact.py`: `assert_no_raw_secrets` body reverted to exact-match-only | every family (UI door alone still catches — the AND collapses every row) | n/a |
| `ASCII_CONFUSABLES` re-export — **new** | `redact.py`: drop `ASCII_CONFUSABLES,` from the `redact_fold` import block | mutant import raises `ImportError`; fixed copy imports cleanly | n/a |

Full runner output (`mutation_runner_cycle2.py`, scratch dir):

```
combining-marks                                          targeted_red=True  others_green=True
html-entities                                            targeted_red=True  others_green=True
double-percent                                           targeted_red=True  others_green=True
reversed                                                 targeted_red=True  others_green=True
base64-isolated+base64-adjacent+base64-adjacent-filename targeted_red=True  others_green=True
base32-isolated+base32-adjacent                          targeted_red=True  others_green=True
hex-isolated+hex-adjacent                                targeted_red=True  others_green=True
AT-347-gate-itself                                       targeted_red=True  (every family red)
ASCII_CONFUSABLES-reexport                               fixed_copy_imports=True  mutant_import_broke=True

ALL FAMILIES PROPERLY DEFENDED: True
```

One false start recorded rather than hidden (same C7 spirit as cycle 1): the ASCII_CONFUSABLES
mutation test's first version only re-imported the whole `autotester.core.redact` *module* (which
succeeds regardless of whether `ASCII_CONFUSABLES` is bound in it) instead of the specific `from
autotester.core.redact import ASCII_CONFUSABLES` a real caller would write, so it read
`mutant_import_broke=False` on a mutation that should have broken it. Fixed by asserting the actual
`from ... import ASCII_CONFUSABLES` form; re-ran and it correctly flipped to `True`.

### Cycle 2 gaps

- Same full-non-browser-suite and standalone-mutation-runner-vs-pytest gaps as cycle 1, for the same
  reasons (RAM ceiling; editable-install path) — not repeated in full here.
- The 3-alignment-offset base64 technique is coarse (drops a whole 4-character group where only 1-2
  characters are actually affected by an unknown neighbouring byte), so the needle is a few
  characters shorter than the theoretical maximum in the offset-1/offset-2 cases. Not scoped as a
  risk: exact substring matching on even a shortened needle (still many characters for any
  realistic secret) carries no meaningful false-positive exposure, and correctness (never including
  an unstable character) was prioritized over needle length.
- This fix only searches for a secret encoded ALONE next to arbitrary surrounding text (the shape
  every reproduced failing input used). A secret byte-concatenated with OTHER real secret material
  before the whole blob is base64-encoded (e.g. `base64(nonce + secret + suffix)` as one encode
  call) is exactly what the 3-alignment-offset technique is built to catch too, and was not
  separately re-tested with a non-zero, non-secret neighbour — the mutation/verification above uses
  zero-byte neighbours (per the technique's own construction) and plain-text neighbours (per the
  reproduced attack shape), not a THIRD real-secret-byte neighbour. Flagged for a checker who wants
  to push on it specifically.

---

## Cycle 1 (original, kept as history)

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
