# Verdict — at345-346-fold-coverage

**Cycle checked:** 1
**Date:** 2026-09-11
**Checker:** fresh Mode A + Mode D subagent, bound to `d:/autoTesting`. No maker reasoning, no
session context. Every command below was re-run by this checker; nothing was read from the
manifest's pasted output.
**Contract:** `qa/contracts/ui.md` U8/U9 · `qa/contracts/core-invariants.md` C2, C7
**Evidence produced by this check:** `qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker-b/`
(`report.json`, `home-index-renders-credential.png`, and the five probe scripts I wrote:
`fold_probe.py`, `attack.py`, `u8.py`, `fp2.py`, `plus.py`).

---

```
VERDICT: FAIL
SCOREBOARD: 0/2 criteria met, 2/2 invariants hold
FAILURES:
- [U9] sev: high · invisible category-Mn characters (U+034F, U+FE00-FE0F) are not stripped, so
  the AT-345 zero-width rendering leak reopens verbatim: POST /onboard accepts them and the home
  index renders the exact credential (pixel-identical, measured) · strip on INVISIBILITY, not on
  category Cf — add zero-width Mn (U+034F, U+FE00-FE0F, U+180B-U+180D) and the invisible Lo
  fillers (U+3164, U+2800, U+FFA0) to the strip, ideally via a width/default-ignorable test
  rather than a second hand-curated list · issue: AT-351
- [U8] sev: high · the same three spellings are accepted by the case form on `title`,
  `step_value` and `step_expected`, and land in git-tracked `cases.jsonl` · same fix; one change
  in `fold_credential` closes both · issue: AT-351
LIVE-BROWSER: qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker-b/ (own Chromium via
playwright, own uvicorn on a scratch AUTOTESTER_ROOT; 0 console errors, 0 warnings)
ISSUES-WRITTEN: AT-351 (high), AT-352 (medium)
EXPLANATION: Every command in the manifest reproduces exactly, all six AT-345 forms plus AT-346's
%5F are genuinely refused, C2 and C7 hold, and the widened fold caused zero false positives in 36
legitimate submissions — this is good work. But the unit's central fix strips category `Cf`, and
the invisible-character set is larger than `Cf`. U+034F COMBINING GRAPHEME JOINER and the
variation selectors U+FE00/U+FE0F are category `Mn`, survive the strip, survive NFKC, and render
PIXEL-IDENTICAL to the plain credential — 192.5px vs a 192.5px control in the page's own font.
I onboarded them and read the credential off the home index in a real browser. That is not the
AT-349 confusable gap; it is the same defect AT-345 was, one code point sideways, on the exact
line this unit rewrote.
```

---

## What I re-ran (Mode A, my own execution)

| Command | Manifest expected | My result |
|---|---|---|
| `uv run pytest -q` | exit 0, no failures | **exit 0**, 2 skipped, **1 warning** (the 45→1 `DeprecationWarning` claim holds) |
| `uv run ruff check src scripts` | `All checks passed!` | **`All checks passed!`** |
| `uv run autotester doctor` | `doctor: clean` | **`doctor: clean`** |
| `uv run pytest tests/test_ui_credential_transforms.py tests/test_ui_credential_unicode.py` | 20 passed | **20 passed** in 1.24s |
| `uv run python scripts/mutation_check.py qa/evidence/at345-346-fold-coverage/mutations.json` | `6/6 mutations killed` | **`6/6 mutations killed`**, every `claims to kill` test present in `actually failed` |

I honoured the manifest's request not to run a bare `ruff check tests`: `tests/test_explore_error_causes.py`
is another session's uncommitted in-flight edit and its unused imports are not this unit's. Nothing
outside this unit was touched.

## C7 — mutation kill ATTRIBUTION, verified by hand

Not merely "6/6". I read each kill's attribution line and confirmed the named test appears in the
observed failure list:

- `format characters` → `test_a_unicode_spelling_of_a_credential_is_refused[zero-width-interleaved]` ✓ (plus `test_format_characters_are_stripped_before_normalising`)
- `NFKC dropped` → `…[full-width-latin]` ✓
- `confusable map` → `…[turkish-dotless-i]` ✓
- `separator class narrows` → `[colon-separator]`, `[slash-separator]`, `[tilde-separator]` ✓ (all three)
- `fold stops composing` → `test_a_percent_encoded_credential_in_one_field_is_blamed_on_that_field` ✓
- `strip after normalise` → `test_format_characters_are_stripped_before_normalising` ✓

And I re-read `scripts/mutation_check.py` against C7's five clauses: it asserts a **green
baseline** (`baseline is NOT green (pytest exit …)`, line ~241), asserts the anchor matched
**exactly once** (line ~248), asserts the **file changed** (line ~256), and `is_kill` requires
`exit_code == 1 and expected <= failures` (line ~85) — a syntax-error collapse (exit 2) is not a
kill, and an unrelated failure cannot stand in for the named test. C7 holds.

### The `+` claim — CONFIRMED, and the correction was the right one

The manifest says `+` is caught by `unquote_plus` composition, not by the widened separator class,
and that its original `kills` claim was wrong. I measured it independently (`plus.py`), folding
with AT-339's original `[\s\-_.]` class:

```
plus    caught-with-NARROW-class+variants=True   caught-with-NARROW-class-raw-only=False  caught-with-WIDE=True
tilde   caught-with-NARROW-class+variants=False  caught-with-NARROW-class-raw-only=False  caught-with-WIDE=True
slash   caught-with-NARROW-class+variants=False  caught-with-NARROW-class-raw-only=False  caught-with-WIDE=True
colon   caught-with-NARROW-class+variants=False  caught-with-NARROW-class-raw-only=False  caught-with-WIDE=True
```

`unquote_plus` turns `+` into a space, which the narrow class already stripped — so `+` is the one
form of the four that the widening does **not** account for. The correction is exactly right, the
harness was right to refuse the original claim, and the in-table comment is worth keeping. Two of
the three self-reported corrections (`+`, and the now-measured order-is-load-bearing test) I
re-derived; the third (the AT-346 mutation distinguishable only by message) I read in the test and
found consistent with the mutation run.

## The six AT-345 forms, re-attacked on my own server

All genuinely closed. This is not read from the manifest — these are POSTs to my own `uvicorn`:

```
REFUSED  zero-width-U+200B      (400)      REFUSED  plus-separator    (400)
REFUSED  fullwidth              (400)      REFUSED  tilde-separator   (400)
REFUSED  turkish-dotless-i      (400)      REFUSED  slash-separator   (400)
REFUSED  percent5F (AT-346)     (400)      REFUSED  colon-separator   (400)
```

AT-345 and AT-346 are, on their own terms, fixed. The FAIL below is a **new** finding, not a
re-charge of the old one.

## The FAIL — AT-351, and why it is chargeable rather than AT-349's problem

`fold_credential` line 77: `"".join(c for c in text if unicodedata.category(c) != "Cf")`.

`Cf` is not the set of invisible characters. **U+034F COMBINING GRAPHEME JOINER** and the
**variation selectors U+FE00–U+FE0F** are category `Mn`, are not touched by NFKC, are not in the
confusable map, and are zero-width. Interleaved between every character of a live `.env` value
they produce a string that is byte-different from the credential and **visually identical** to it.

I measured this rather than asserting it. In the page's own font, against a plain-credential
control of 192.5px:

| spelling | rendered width | verdict |
|---|---|---|
| plain `ZEBRA_QUILT_APIKEY_31` (control) | 192.5px | — |
| U+200B interleaved (**closed by this unit**) | 192.5px | refused, correctly |
| **U+034F interleaved** | **192.5px** | **accepted** |
| **U+FE00 interleaved** | **192.5px** | **accepted** |
| **U+FE0F interleaved** | **191.5px** | **accepted** |
| U+180B interleaved | 196.9px | accepted (visibly different) |
| U+17D2 interleaved | 369.4px | accepted (visibly different) |

Then I drove a real browser at the home index and scanned the DOM: **14 leaf nodes render as the
exact credential**, while `document.body.innerText` contains the literal value **nowhere**. The
screenshot `home-index-renders-credential.png` shows the project cards reading
`ZEBRA_QUILT_APIKEY_31` in plain type. This is, word for word, the thing the manifest calls "the
worst thing found in this whole credential thread" — "a human reading the page sees the secret,
while every byte-comparison in the system says it is a different string."

On disk, both doors:

- **U9** — `POST /onboard` returned 200 and wrote git-tracked `projects/<slug>/project.json` for
  U+034F, U+FE00, U+FE0F, U+180B, U+17D2, U+3164 (Hangul filler — renders as blank gaps), U+2800
  (Braille blank), RTL-override reversal, plain reversal, base64, HTML entities, regional
  indicators, Armenian and Cherokee homoglyphs. 13/13 written.
- **U8** — `POST /projects/<slug>/cases` accepted U+034F / U+FE00 / U+FE0F on **`title`**,
  **`step_value`** and **`step_expected`** (200 each) and the resulting git-tracked `cases.jsonl`
  contains a string that renders as the credential. The same value as U+200B was refused on all
  four paths, so this is the strip predicate and nothing else.

**Why this is not covered by AT-349.** AT-349 is scoped to `ASCII_CONFUSABLES` — homoglyph-map
completeness. I judge that filing **honest and correctly scoped**: my Armenian (`Օ`, `բ`) and
Cherokee (`Ꮓ`, `Ꭼ`, `Ꭺ`) bypasses land squarely inside it, they are visibly different on screen
(`ZEBRA_բUILT_APIKEY_31` on the rendered card), and low severity is the right call. It is not
chargeable now. AT-351 is a different line: the `Cf` strip, which is this unit's own headline fix
and whose docstring claims the zero-width class as closed.

## AT-352 — the declared bound is narrower than the actual bound

The manifest offers AT-349 as "the honest version of *state which transform classes are out of
scope*". It states the confusable-map gap and nothing else. But base64, base32, hex, HTML decimal
and hex numeric entities, double percent-encoding, and plain/RTL reversal all write to git-tracked
`project.json` at 200, and none of them is declared anywhere. These are **not** criterion
violations — U8/U9 pin byte-for-byte reassembly and these forms need a decoding step a reader must
perform deliberately — so they are filed (medium) rather than charged. But the declaration should
either cover them or the code should. A bound that names one of three open classes is not yet the
honest version.

## The cost side — the widening did NOT brick real work

I tried hard to make the wider fold refuse legitimate input, across `title`, `step_target` and
`step_expected`, with a long credential in `.env`: **36 submissions, 0 refused by the credential
guard.** URL with query + fragment, JSON body, CSS selector with `>`/`:nth-child`/`[data-id='x']`,
XPath with `//`/`@`/`contains()`, a code snippet containing `(a + b) == c`, French, Turkish
(including `I`/`İ`-shaped uppercase), Hindi, Cyrillic and Greek names, a regex with `^[A-Z]{3}-[0-9]{4}$`,
a bcrypt `$2b$12$` prefix, a markdown table, emoji, SQL with `LIKE '%zebra%'`, a semver
`v1.2.3-rc.1+build.31`, a Windows path with backslashes, and a JWT-shaped token. All accepted.
The `MIN_FOLDED_LEN = 8` floor is doing its job and I have no false-positive finding to report.

## Also verified (not re-charged)

- **C2** — `redact.py` 149, `helpers.py` 231, `test_ui_credential_unicode.py` 146,
  `test_ui_credential_transforms.py` 295 lines; `doctor: clean`. The new test file's split at the
  300-line cap is stated in the manifest, as C3 requires for a new module. Holds.
- **Scope discipline** — `git show --stat 80d915f` touches 9 files, all this unit's. No
  cross-session file was modified.
- **Isolation** — my server ran on a scratch `AUTOTESTER_ROOT`; `git status projects/` is
  unchanged from the pre-check state. No repo project was created or edited by this check.

## What a cycle-2 fix needs to show me

1. `fold_credential` strips on **invisibility**, not on `unicodedata.category(c) == "Cf"`. The
   durable predicate is the Unicode **Default_Ignorable_Code_Point** property plus the zero-width
   `Mn` marks; a second hand-curated list will lose the same race a third time.
2. A mutation that reverts that strip to `Cf`-only, killed by a test that names U+034F and a
   variation selector explicitly.
3. The false-positive probe re-run — widening to `Mn` is the risky direction, because ordinary
   accented and Indic text is full of `Mn` combining marks. Stripping **all** `Mn` would fold
   `Café` to `Cafe` and could start refusing real names. Strip only the **zero-width, non-combining**
   ones; do not take my finding as a licence to strip every mark.
4. AT-352 either closed or explicitly declared, in the code's own docstring, alongside AT-349.
