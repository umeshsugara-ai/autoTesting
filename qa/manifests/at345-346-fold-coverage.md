# Manifest — at345-346-fold-coverage

**Unit:** AT-345 / AT-346 — the transforms AT-339's fold still let through
**Contract:** `qa/contracts/ui.md` (U8/U9) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-345 (high, fixed) · AT-346 (medium, fixed) · AT-351 (high, fixed in cycle 2) · AT-349, AT-352 (filed, NOT fixed)

## What was wrong

A checker, attacking the fix I shipped one cycle earlier, walked a live `.env` credential past the
guard in six more forms. All were live-reproduced on its own server before this unit existed.

**The worst is not the one that sounds worst.** A **zero-width space between every character**
(U+200B) was accepted into git-tracked `project.json` — and because U+200B has no width, the
project name **renders as the exact credential on the home index**. A human reading the page sees
the secret, while every byte-comparison in the system says it is a different string. That is worse
than AT-339 itself.

The rest: `+`, `~`, `/`, `:` as separators; full-width Latin (`casefold` does not NFKC-normalise);
the Turkish dotless `ı`; and — separately, AT-346 — `zebra%5Fquilt%5Fapikey%5F31`, because
`contains_folded` was applied to the raw text only and never to `_credential_variants`, so each
guard covered exactly the half the other did not: the `%5F` survived folding intact, and the
`unquote_plus` form that would have exposed it was only ever compared byte-for-byte.

## What changed

- `src/autotester/core/redact.py::fold_credential` — strip Unicode format characters (category
  `Cf`), then NFKC, then `ASCII_CONFUSABLES`, then separators, then case. `_FOLD_STRIP` widened
  past `[\s-_.]` to the punctuation a human actually substitutes.
- `src/autotester/core/redact.py::ASCII_CONFUSABLES` — a curated homoglyph map (Cyrillic, Greek,
  the Turkish dotless i, dash-likes).
- `src/autotester/ui/helpers.py` — both call sites fold **every** variant, not just the raw text.
- `tests/test_ui_credential_unicode.py` — **new file** (C2 split at the 300-line cap): does the
  guard see through Unicode *spelling*? `test_ui_credential_transforms.py` keeps the ASCII-shaped
  substitutions. They fail for different reasons and are fixed in different lines.

## The confusable map is deliberately partial, and says so

`ASCII_CONFUSABLES` is a curated list, **not** an implementation of UTS #39. It covers the
homoglyph families that appear in Latin-script credentials and will not catch an exotic script
nobody has tried. **AT-349 is filed for the completeness gap** so the bound is visible rather than
assumed — this is the honest version of "state which transform classes are out of scope", which
the checker's own `expected` offered as an alternative to full coverage.

## What the mutation run corrected (first pass 3/6)

1. **`+` does NOT need the widened separator class.** `unquote_plus` turns `+` into a **space**,
   which AT-339's original `[\s-_.]` already stripped — so that case is caught by AT-346's
   composition, not by the widening. My `kills` claim was simply wrong, the harness refused it, and
   the parametrised table now carries a comment saying so, because the next reader would otherwise
   draw the same false conclusion I did.
2. **The AT-346 mutation touches one call site, and the joined guard still catches a single-field
   submission** — the same redundancy AT-339 hit. Only the *message* distinguishes them, so that is
   what the new test asserts.
3. **"Order is load-bearing" was an unproven claim in a docstring.** It is now measured: for `e` +
   U+200B + combining acute, strip-then-NFKC yields U+00E9 while NFKC-then-strip leaves a bare
   combining mark — different strings, so a credential containing an accented character can be
   spelled past a guard that gets the order wrong. Pinned by a test instead of asserted in prose.

## Deliberate scope boundaries

- `assert_no_raw_secrets` is still **not** folded — AT-347's question, filed by the checker and
  left for a decision rather than settled quietly here. Folding a gate that *raises* trades a leak
  for dead runs.
- The `MIN_FOLDED_LEN = 8` floor is unchanged and still means short credentials get no folded
  protection. The checker measured this last cycle (refused at 8+, accepted at 6–7) and did not
  charge it; nothing here changes that trade.

## How to verify (commands + expected)

- `uv run pytest -q` → expected: exit 0, no failures
- `uv run ruff check src scripts` → expected: `All checks passed!`
  (**not** a bare `ruff check tests` — `tests/test_explore_error_causes.py` is another session's
  uncommitted in-flight edit and reports unused imports that are not this unit's)
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_ui_credential_transforms.py tests/test_ui_credential_unicode.py -q`
  → expected: 20 passed
- `uv run python scripts/mutation_check.py qa/evidence/at345-346-fold-coverage/mutations.json`
  → expected: `6/6 mutations killed` (C7)

## Actual outputs (from maker's own run)

```
$ uv run pytest
1133 passed, 2 skipped, 1 warning in 187.46s (0:03:07)

$ uv run ruff check src ... scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest tests/test_ui_credential_transforms.py tests/test_ui_credential_unicode.py
20 passed, 1 warning in 1.22s

$ uv run python scripts/mutation_check.py qa/evidence/at345-346-fold-coverage/mutations.json
KILLED  format characters are no longer stripped - the zero-width leak reopens
KILLED  NFKC normalisation dropped - full-width Latin walks through
KILLED  the confusable map is never applied - the dotless i walks through
KILLED  the separator class narrows back to AT-339's (not the + form: unquote_plus makes that a space)
KILLED  the fold stops composing with the variants (AT-346) - percent-escapes walk through
KILLED  stripping happens AFTER normalising - order is load-bearing, not decorative
6/6 mutations killed
```

One more thing the run caught: my first docstrings contained `\s` in non-raw strings, which emitted
45 `DeprecationWarning: invalid escape sequence` across the suite (1 → 45). Fixed; back to 1.

## Live browser evidence

**SKIP — stated gap, not a pass.** The maker did not run a live browser this cycle. The zero-width
case in particular has a *rendering* claim — that the home index shows the exact credential — which
a `TestClient` cannot verify and which was originally demonstrated by a checker in a real browser
with a screenshot. **The checker must run Mode D and treat its own result as authoritative**, and
should specifically re-check that the rendering leak is closed, not merely that the POST is refused.


## Cycle 2 — the checker FAILed cycle 1, and it was right

**Verdict:** `qa/verdicts/at345-346-fold-coverage.md`, cycle 1, **FAIL**, 0/2 criteria.
The checker confirmed everything cycle 1 claimed — all six AT-345 forms and AT-346's
percent-escape composition genuinely closed, verified by its own POSTs, 6/6 mutations
re-killed, 0 false positives in 36 legitimate submissions — and then **reopened the same
rendering leak one code point sideways**.

**AT-351.** `fold_credential` stripped `unicodedata.category(c) == "Cf"`. U+034F (combining
grapheme joiner) and U+FE00–U+FE0F (variation selectors) are category **`Mn`**. They survive
that strip and NFKC, they render as nothing, and the checker measured them at
192.5/192.5/191.5px against a 192.5px plain-credential control — pixel-identical — then read
the credential off the home index in a real browser. It also found the same three spellings
reaching git-tracked `cases.jsonl` through `title`, `step_value` and `step_expected`.

Fixed by keying on **invisibility** — Unicode's `Default_Ignorable_Code_Point` ranges, listed
explicitly because Python exposes no predicate for them — rather than on a category.

### The justification I first wrote for that was wrong, twice

I claimed keying on invisibility mattered because stripping all `Mn` "would silently mangle
every Hindi, Arabic and accented-Latin string the system stores". Both halves were false:

1. **`fold_credential` never rewrites anything.** It is a comparison function; stored text is
   untouched either way. There was no corruption to fear.
2. **The mutation proved it.** Stripping all `Mn` did not make my Hindi/Arabic test fail —
   that test asserts those names are *accepted*, and they still are. The test could not fail
   for the reason it named, which is the vacuous class C7 exists to refuse. **Deleted, not
   relabelled**; ordinary non-ASCII acceptance is already covered elsewhere in the file.

Measured, the real harm runs the **other way — a leak, not a false positive**:

```
stored   CAFE_QUILT_APIKEY_31 with a precomposed U+00C9
spelled  the same value, with E + U+200B + combining acute

keying on invisibility:  both fold to cafequiltapikey31 (e-acute)   MATCH
stripping all Mn:        the spelled form loses its accent          MISS
```

Stripping *visible* combining marks folds the two sides **asymmetrically**, because a stored
value tends to carry a precomposed character while a hostile input carries a decomposed one —
reopening the very class of bypass this fold exists to close. The mutation is re-attributed to
the test that actually dies, and the docstring now says this instead of the wrong thing.

### Cycle 2 verification

- `uv run pytest` → **1140 passed, 2 skipped, 1 warning**
- `uv run ruff check src scripts <this unit's three test files>` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at345-346-fold-coverage/mutations.json`
  → **9/9 mutations killed** (three added this cycle: revert to `Cf`; strip all `Mn`; empty
  the default-ignorable ranges)

`uv run autotester doctor` reports one violation — `tests/test_explore_error_causes.py` at 330
lines. **That file is the other maker loop's uncommitted in-flight work**, not this unit's;
this unit's files are clean. Verify with `git status --porcelain tests/test_explore_error_causes.py`.

### Still open, and the checker should weigh them

- **AT-352 (medium, filed by the checker, NOT fixed):** base64/base32/hex, HTML entities,
  double percent-encoding and reversal all still write to disk. Not closed here because U8/U9
  pin byte-for-byte reassembly and each of these needs a decode step the guard does not
  currently take — a scope decision, not an oversight.
- **AT-349 (low, filed by me):** the confusable map is curated, not UTS #39. The checker
  independently agreed this was filed honestly and landed its Armenian/Cherokee probes inside
  it.
- The live browser pass is again a maker **SKIP**; the checker's own Mode D is authoritative,
  and should re-check the **rendering** of the three new spellings, not only that the POST is
  refused.

## Status: ready-for-check
