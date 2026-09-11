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

---

# Verdict — at345-346-fold-coverage (cycle 2)

**Cycle checked:** 2
**Date:** 2026-09-11
**Checker:** fresh Mode A + Mode D subagent, bound to `d:/autoTesting`. No maker reasoning, no
session context, no reading of the cycle-1 checker's scripts. Every command below was re-run by
this checker; nothing was taken from the manifest's pasted output.
**Contract:** `qa/contracts/ui.md` U8/U9 · `qa/contracts/core-invariants.md` C2, C7
**Evidence produced by this check:**
`qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker-cycle2/` (`report.json`,
`at353-nul-renders-credential-on-home-index.png`, `positive-control-planted-leak.png`, and my
four probes `di_audit.py`, `attack.py`, `fp.py`, `asym.py`).

---

```
VERDICT: FAIL
SCOREBOARD: 0/2 criteria met, 2/2 invariants hold
FAILURES:
- [U9] sev: high · U+0000 NUL interleaved between every character passes the guard, and the HTML
  parser DROPS U+0000 — so the home index renders the exact credential in plain type and
  `document.body.innerText` contains it verbatim · `_is_invisible` must implement its own stated
  definition ("renders as nothing"): add the C0/C1 controls, U+0000 at minimum · issue: AT-353
- [U8] sev: high · the same NUL spelling is accepted by the case form on `title`, `step_value`
  and `step_expected` and lands in git-tracked `cases.jsonl` (60 `\u0000` escapes; deleting the
  NULs yields the exact credential) · same one-line fix closes both · issue: AT-353
LIVE-BROWSER: qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker-cycle2/ (my own
Chromium via playwright, my own uvicorn on a scratch AUTOTESTER_ROOT; every console error is an
expected 400 from one of my attack POSTs, 0 unexplained)
ISSUES-WRITTEN: AT-353 (high), AT-354 (low)
EXPLANATION: Both cycle-1 failures are genuinely closed and I proved it with a working detector
rather than a silent negative — U+034F/U+FE00/U+FE0F are refused at both doors, the home-index
leaf scan finds 0 nodes rendering the credential, and a name planted directly into project.json
makes that same scan report 2, so the zero is real. The declared Default_Ignorable ranges are
CORRECT AND COMPLETE: audited against Unicode 14 data (Other_DI fetched from unicode.org, Cf from
this machine's unicodedata), the guard's strip set is a strict superset of DI — zero
under-inclusion — and every code point the FAIL-hunt named (U+180B-180F, the Hangul fillers,
U+17B4-17B5, the tag characters, the musical symbols) is refused live. Zero false positives in 44
probes: real Hindi, Arabic (incl. shadda and U+0600), Thai, Hebrew (incl. niqqud), Khmer, Korean,
and five emoji forms including U+FE0F and ZWJ sequences all pass and render correctly. But the
leak reopened a THIRD time on the same line: U+0000 is category `Cc`, so `_is_invisible` misses
it, and unlike base64 or U+2800 it needs no reader-side decoding at all — the renderer deletes it
for you.
```

---

## What I re-ran (Mode A, my own execution)

| Command | Manifest expected | My result |
|---|---|---|
| `uv run pytest` | 1140 passed, 2 skipped, 1 warning | **1140 passed, 2 skipped, 1 warning** in 196.28s (exit 0) |
| `uv run ruff check src scripts` | `All checks passed!` | **`All checks passed!`** |
| `uv run ruff check` (this unit's test files) | `All checks passed!` | **`All checks passed!`** |
| `uv run autotester doctor` | ONE violation, another loop's file | **`doctor: clean`** — see note below |
| `uv run pytest tests/test_ui_credential_transforms.py tests/test_ui_credential_unicode.py` | 26 passed | **26 passed** in 2.41s |
| `uv run python scripts/mutation_check.py …/mutations.json` | `9/9 mutations killed` | **`9/9 mutations killed`** |

**On `doctor`:** the manifest warned me to expect one violation from
`tests/test_explore_error_causes.py`. By the time I ran it, `doctor` was clean.
`git status --porcelain tests/test_explore_error_causes.py` returns ` M` — the file is indeed
another session's uncommitted in-flight work, and that session has since brought it under the cap.
Either way nothing is charged to this unit, and `git show --stat 7b5f55c` shows this unit's cycle-2
commit touching six files, all its own.

## C7 — kill ATTRIBUTION verified by hand, all nine

Not "9/9" read off a summary line. For each mutation I compared its `claims to kill` list against
the `actually failed` list; **every claimed nodeid appears in the observed failures for all nine**:

| Mutation | Claimed | Present in observed failures |
|---|---|---|
| format characters not stripped | `…is_refused[zero-width-interleaved]` | yes (plus 7 more) |
| NFKC dropped | `…is_refused[full-width-latin]` | yes |
| confusable map not applied | `…is_refused[turkish-dotless-i]` | yes |
| separator class narrowed | `[tilde-]`, `[slash-]`, `[colon-separator]` | yes, all three |
| fold stops composing (AT-346) | `…percent_encoded…blamed_on_that_field` | yes |
| strip AFTER normalise | `test_format_characters_are_stripped_before_normalising` | yes |
| **revert to `Cf`** | 3 x onboarding + 1 x case form | yes, all four (plus 2 more) |
| **strip ALL `Mn`** | `test_format_characters_are_stripped_before_normalising` | yes |
| **DI ranges emptied** | `…refused_at_onboarding[combining-grapheme-joiner]` | yes |

And I re-read `scripts/mutation_check.py` against C7's clauses myself: green-baseline assertion
(l.241), anchor-matched-exactly-once (l.248), file-actually-changed (l.256), and `is_kill`
requiring `exit_code == 1 and expected <= failures` (l.85) so a collection collapse cannot read as
a kill. **C7 holds.** One cosmetic note, not a finding: the ninth mutation is named *"the
default-ignorable ranges are emptied"* but removes only the `(0x034F, 0x034F)` entry. The mutation
is real and correctly attributed; the name overstates it.

## Are the declared Default_Ignorable ranges right? Audited, not trusted

`di_audit.py`. I did not take the hand-written tuple list on faith:

- `Other_Default_Ignorable_Code_Point` — fetched **verbatim** from
  `unicode.org/Public/14.0.0/ucd/PropList.txt` during this check.
- `Variation_Selector` — FE00-FE0F, 180B-180D, **180F** (added in Unicode 14), E0100-E01EF.
- `Cf` — enumerated from **this machine's** `unicodedata` (`unidata_version 14.0.0`).
- Exclusions per the DerivedCoreProperties definition (White_Space, FFF9-FFFB, the prepended
  concatenation marks, 13430-1343F).

```
DI code points : 4174        guard strips : 4199
DI NOT stripped by the guard (under-inclusion == leak) : (none)
stripped but NOT DI (over-inclusion == false positive) :
    U+0600..U+0605, U+06DD, U+070F, U+0890..U+0891, U+08E2,
    U+FFF9..U+FFFB, U+110BD, U+110CD, U+13430..U+13438
```

**Zero under-inclusion** — the strip set is a strict superset of Unicode 14's DI. The
over-inclusion is all `Cf` (Arabic/Syriac/Kaithi prepended concatenation marks, interlinear
annotation, Egyptian format controls); it pushes toward false positives, and I measured none,
including a name beginning with U+0600. Live, every code point the FAIL-hunt named is refused 400:
U+180B, U+180F, U+115F, U+1160, U+3164, U+FFA0, U+17B4, U+17B5, U+E0041 (tag), U+E0100, U+1D173,
U+1D17A, U+2065, U+FFF0 — 21 attack spellings, all refused, plus the plain control.

## The cycle-1 FAIL — both halves closed, with a proven detector

- **U9.** `POST /onboard` refused U+034F, U+FE00, U+FE0F (400 each); no `project.json` written.
- **U8.** `POST /projects/seed/cases` refused all three marks (and U+200B, U+3164, U+E0041) on
  **`title`, `step_value`, `step_expected` and `step_target`** — 24/24 at 400 — while a legitimate
  case carrying an emoji title, a Hindi name, an Arabic value and a Thai expectation was accepted
  and is the only invisible-free row in `cases.jsonl`.
- **The RENDERING claim, which is the one a POST status cannot answer.** In my own Chromium at
  `GET /`, scanning every leaf node with the invisibles stripped: **0 nodes render the credential**,
  and `innerText` contains it nowhere. Widths reproduce cycle 1 exactly — control 192.5px, U+034F
  192.5, U+FE00 192.5, U+FE0F 191.5.
- **Why that zero is trustworthy.** I planted a U+034F-spelled name **directly into
  `project.json`**, bypassing the guard, in my scratch root. The same scan then reported **2 leaf
  nodes rendering `ZEBRA_QUILT_APIKEY_31`** (`positive-control-planted-leak.png`). I restored the
  file and the scan went back to 0. The detector works; the negative is real.

## The FAIL — AT-353, the third cycle of the same defect

`_is_invisible` (redact.py:76) says in its own docstring: *"True when `ch` renders as nothing."*
It implements `Cf` **or** Default_Ignorable. **U+0000 is neither, and it renders as nothing** —
in fact worse than nothing: the HTML tokenizer **deletes** it.

```
POST /onboard  name = Z NUL E NUL B NUL R NUL A NUL _ NUL Q ... 3 NUL 1
  -> 303, projects/ctl-0/project.json written, 20 NULs preserved on disk

GET /  (my Chromium)
  the <a> text node  : U+005A U+0045 U+0042 U+0052 U+0041 U+005F ...   <- the NULs are GONE
  rendered text      : ZEBRA_QUILT_APIKEY_31
  rendered width     : 168.8px == a plain-credential control rendered identically
  document.body.innerText.includes("ZEBRA_QUILT_APIKEY_31")  ->  TRUE
  removing only the ctl-0 nodes  ->  FALSE   (the hit is attributable to that project alone)
```

Screenshot: `at353-nul-renders-credential-on-home-index.png`.

**U8 too.** `POST /projects/seed/cases` accepted the NUL spelling on `title`, `step_value` and
`step_expected` (303 each). Git-tracked `cases.jsonl` now carries **60 `\u0000` escapes**, and
three fields yield the exact credential the instant the NULs are deleted.

**Why this is chargeable and not another AT-352.** AT-352 (base64, hex, entities, reversal) needs
a decoding step a reader must deliberately take, which is why I agree with the previous checker
that it was filed rather than charged. U+0000 needs **no step at all** — the browser performs the
reassembly and prints the credential in plain type. That is word for word the harm AT-345 was
opened for and the harm this unit's own docstring claims closed. It is the same line, the same
predicate, and the third consecutive cycle.

Three near neighbours I checked and am **not** charging, because they are visible on screen and so
belong to the AT-352 class:

| spelling | accepted | rendered width vs 192.5px control | verdict |
|---|---|---|---|
| **U+0000 NUL** | yes | **192.5px — identical, NULs deleted by the parser** | **AT-353, charged** |
| U+0001 / U+0008 / U+001B | yes | 348px — visible tofu boxes | not a rendering leak |
| U+007F DEL | yes | 356.9px — visible tofu | not a rendering leak |
| U+2800 BRAILLE BLANK | yes | 405.2px — reads as a visibly spaced Z E B R A ... | not a rendering leak (AT-352) |

## The cost side — the wider strip did NOT start refusing real text

44 probes, **0 false positives** (`fp.py` at the fold level, and 17 more through the real UI):
Hindi, Hindi with ZWNJ, Arabic, Arabic with shadda, a name led by U+0600, Thai, Hebrew, Hebrew
with niqqud, Khmer, Korean, accented Latin, Turkish — and five emoji forms: plain, **U+FE0F
VS16**, a **ZWJ family sequence**, keycaps, and a flag. All accepted at `/onboard` and all render
correctly on the home index. **An emoji in a case title is not refused**, which was the specific
worry: the widened strip removes the variation selector only from the *comparison*, and
`fold_credential` never rewrites what is stored.

## The two self-corrections, judged independently

**1. "My first justification was wrong; the real harm is a LEAK, not corruption." — CORRECT, and
I reproduced the measurement** (`asym.py`):

```
stored  CAFE_QUILT_APIKEY_31 with precomposed U+00C9
input   the same value spelled  E + U+200B + U+0301
  keying on invisibility : stored 'cafequiltapikey31' (e-acute)  input the same   MATCH
  stripping all Mn       : stored keeps the accent, input loses it                MISS  <- leak
```

The maker is right on both counts: `fold_credential` only ever compares, so no stored text was
ever at risk, and stripping visible combining marks folds the two sides asymmetrically because a
stored value tends to carry the precomposed character while hostile input carries the decomposed
one. The corrected docstring says the true thing.

**2. "I deleted `test_real_combining_marks_are_not_stripped` as vacuous." — the right call, and
cheaper than it sounds.** `git show 7b5f55c -- tests/test_ui_credential_unicode.py` is **additions
only**: the vacuous test never reached a commit, so no committed coverage was lost. The test
asserted Hindi/Arabic names are *accepted*, and they are accepted under both the real predicate
and the mutant — it could not fail for the reason it named, which is exactly the class C7 refuses.
Crucially, the property it was *supposed* to defend is now pinned by something that CAN fail: the
`strip ALL Mn` mutation dies against `test_format_characters_are_stripped_before_normalising`,
which I re-ran and watched die. Relabelling would have been worse than deleting.

One residual, **filed as AT-354 (low), not charged**: after the deletion no standing test pins
acceptance of Indic / Arabic / Hebrew / Thai / emoji names —
`test_ordinary_unicode_text_is_still_accepted` covers Café, Japanese and Greek only. I measured
today's behaviour clean, so this is a regression-coverage gap rather than a defect: the next
widening of the strip could start refusing real names with nothing to catch it.

## Also verified (not re-charged)

- **C2** — `doctor: clean`; `redact.py` and both test files are inside the 300-line cap. Holds.
- **Isolation** — my server ran on a scratch `AUTOTESTER_ROOT` outside the repo. No repo project
  was created, edited, or deleted by this check; my two PNGs and four probes are the only files I
  wrote, all inside my own evidence directory.
- **AT-347, AT-349, AT-352** stay open and I agree with how each is scoped. My Armenian/Cherokee
  and braille findings land inside AT-349 and AT-352 respectively.

## What a cycle-3 fix needs to show me

1. `_is_invisible` covers U+0000 — and, since the predicate's own contract is "renders as
   nothing", state in the docstring which side of that line the remaining C0/C1 controls sit on
   rather than leaving it to the next checker to measure.
2. A mutation that removes exactly that addition, killed by a test naming U+0000 explicitly, at
   **both** doors (onboarding and the case form) — the case-form half is where `cases.jsonl` took
   the hit.
3. The false-positive probe re-run. This is the last cycle where "no test pins Indic/Arabic/emoji
   acceptance" (AT-354) is free.
4. Note for the contract's owner, not for the maker: three cycles have now been spent enumerating
   code points. The durable shape is a positive test — *"does this text, rendered, read as the
   credential?"* — rather than a list of things that do not render. That is a scope decision, so
   it is raised here and not imposed.

---

# VERDICT — cycle 3 (FINAL CYCLE THE PROTOCOL ALLOWS)

**Date:** 2026-09-11
**Unit:** at345-346-fold-coverage
**Contract:** `qa/contracts/ui.md` U8/U9 · `qa/contracts/core-invariants.md` C2, C7
**Cycle checked: 3**
**Checker:** fresh Mode A + Mode D subagent, bound to `d:/autoTesting`, no builder context

```
VERDICT: FAIL
SCOREBOARD: 0/2 criteria met, 2/2 invariants hold
```

I am saying it plainly, as asked: **this cycle FAILs, and the unit should flip to `STALLED` for
Umesh rather than take a fourth round.** Not because cycle 3's work was poor — it is the best of
the three, and I confirmed every claim it makes — but because a fourth character class walked a
live credential onto a rendered page, and that is now evidence about the *shape* of the guard
rather than about the class.

## What I re-ran (my own execution, nothing read from the manifest)

| Command | Manifest expected | My result |
|---|---|---|
| `uv run pytest -q` | 1145 passed, 2 skipped, 1 warning | **exit 0**, no failures (run twice) |
| `uv run ruff check src scripts` | `All checks passed!` | **`All checks passed!`** |
| `uv run autotester doctor` | `doctor: clean` | **`doctor: clean`** |
| `uv run pytest tests/test_ui_credential_transforms.py tests/test_ui_credential_unicode.py` | 31 passed | **31 passed** in 2.86s |
| `uv run python scripts/mutation_check.py …/mutations.json` | 10/10 killed | **10/10 mutations killed** |

**C2 holds** (`doctor: clean`; both test files and `redact.py` inside the 300-line cap).

## C7 — 10/10, attribution checked by hand, and it holds

Not read off the summary line. For each of the ten mutations I compared its `claims to kill`
list against the `actually failed` list in my own run; **every claimed nodeid appears in the
observed failures for all ten**, including cycle 3's new one:

> `AT-353 reverted: control characters are ignorable again only if Cf` — claims
> `…_refused_at_onboarding[nul]`, `[escape]`, `…_nul_spelling_is_refused_by_the_case_form`;
> observed failures contain all three (plus `[delete]` and `[start-of-heading]`).

Both doors are represented in that mutation's kill set, which is exactly what cycle 2 demanded.
**C7 holds.**

## 1. AT-353 is genuinely CLOSED — with a proven detector, not a silent negative

- `POST /onboard` with the NUL spelling: **HTTP 400**, no `project.json` written.
- `POST /projects/seed/cases` with the NUL spelling in `title`: **HTTP 400**.
- **The rendering claim, checked in my own Chromium.** I walked every text node looking for the
  credential *verbatim* — the AT-353 shape, where the parser has already deleted the NULs.
- **Positive control, matching cycle 2's technique.** I planted two projects **directly into
  `project.json`**, bypassing the guard: `ctlplain` (plain credential) and `ctlnul` (NUL-spelled).
  My scan found **both**, each with `domLength 21`, `verbatimInDom true`, and an identical
  **172.0px** text width — reproducing cycle 2's measurement that the parser deletes NUL.
- I then removed the planted controls and re-scanned: `document.body.textContent.includes(CRED)`
  → **false**. The detector fires when there is something to find, and its negative is real.

AT-353 is closed at both doors. AT-345, AT-346 and AT-351 remain closed (U+200B, U+034F, U+2066
and the percent-escape composition all refused 400 in my own run).

## 2. I kept attacking — and the fourth class is the sharpest one yet

**AT-355 (high) — `U+202E` RIGHT-TO-LEFT OVERRIDE plus the reversed credential is accepted by
both doors and renders as the exact credential in plain type.**

```
POST /onboard  name = U+202E + "13_YEKIPA_TLIUQ_ARBEZ"
  -> HTTP 200, projects/atk18/project.json written

GET /  (my Chromium, per-character Range rects, glyphs sorted by screen x)
  DOM order    : U+202E 1 3 _ Y E K I P A _ T L I U Q _ A R B E Z
  VISUAL order : Z E B R A _ Q U I L T _ A P I K E Y _ 3 1      <- 21 glyphs
  visualOrder.includes("ZEBRA_QUILT_APIKEY_31")  ->  TRUE
  plain-credential control: 21 glyphs, same reading order, same type
```

Screenshot `home-index-all-spellings.png`: that card is indistinguishable from the two planted
plain-credential controls at the bottom of the same page.

**The case form too.** `title`, `step_value` and `step_expected` each accepted it (HTTP 200), and
git-tracked `cases.jsonl` now carries **7 `\u202e` escapes**.
`at355-rlo-renders-credential-on-cases-page.png` shows **`ZEBRA_QUILT_APIKEY_31` in plain type
inside the case-title boxes** of the Cases page.

**Why the guard cannot see it, and this is the part that matters:**

```
fold_credential(U+202E + reversed)  ==  fold_credential(reversed)   ->  True
```

`_is_ignorable` strips `U+202E` as category `Cf`. **The guard deletes the one character that
makes the text render as the credential, and then compares a string that is not one.** The strip
is not merely blind to this attack; the strip *is* the attack's enabler.

**Why this is not already covered by AT-352.** AT-352's row does name "RTL-override reversal", and
I weighed leaving it there. I cannot: AT-352 is filed on the rationale that *each of its spellings
needs a decode step the reader must take* — and measured, this one needs **none**. The browser
performs the reordering and prints plain type. That is word for word the standard on which the
cycle-2 checker charged AT-353 ("it needs no decoding by the reader at all") and declined the rest
of AT-352. The scoping was right; the factual premise for this one arm of it was wrong, and I have
now measured it. AT-355 is filed as that arm, at high, with AT-352 keeping its other arms.

**Also accepted to disk, and NOT charged** (they render as something a reader must work at, which
is the AT-352 line the previous two checkers drew, and I am not moving that line in the final
cycle):

| spelling | accepted | what Chromium draws | call |
|---|---|---|---|
| **U+202E + reversed** | yes | **21 glyphs, plain type, identical to control** | **AT-355, charged** |
| U+0335 combining short stroke | yes | the credential **struck through**, 41 glyphs, zero added width | AT-356 (medium), filed |
| U+0301 combining acute | yes | accented letters, readable with effort | AT-356 |
| U+2800 braille blank | yes | visibly spaced `Z E B R A …` (matches cycle 2) | AT-352 class |
| U+E000 / U+F8FF / U+100000 PUA | yes | visible tofu, +10.33px each | AT-352 class |
| U+0378, U+05EB unassigned `Cn` | yes | visible tofu | AT-352 class |
| U+FDD0, U+FFFE noncharacters | yes | visible tofu | AT-352 class |
| U+A4A0 `So`, U+1D159 musical | yes | visible glyphs | AT-352 class |

Lone surrogates are **not reproducible** through this door — a urlencoded body is utf-8 decoded and
a lone surrogate cannot be encoded into one. Recorded as not-reachable, not as a finding.

**The exhaustive number, because it is the argument.** `enumerate.py` walked all 0x110000 code
points: **1,107,659 of them defeat the fold when interleaved** (Cn 826,065 · Co 137,468 ·
Lo 127,329 · So 6,605 · Mn 1,687 · …). The deny-list covers about **4,200**. Cycle 2 audited the
declared ranges against Unicode data and found zero under-inclusion *within* Default_Ignorable —
that audit was sound, and it is also the point: the set being audited is four thousand out of a
million.

## 3. False positives — 11 probes, ZERO refusals

The specific worry in the dispatch, tested through the real UI:

| probe | result |
|---|---|
| `expect` with a real newline (3 lines) | **accepted 200** |
| `expect` with a real tab | **accepted 200** |
| `expect` multi-line **and** tabs | **accepted 200** |
| `expect` with CRLF | **accepted 200** |
| title with emoji + **U+FE0F** (`Checkout ✔️ flow`) | **accepted 200** |
| title with a ZWJ family sequence | **accepted 200** |
| title with a keycap (`1️⃣`) | **accepted 200** |
| title Hindi · Arabic with shadda · Thai · accented Latin | **accepted 200** |

All eleven render correctly on the Cases page (see the screenshot). **The widened strip does not
brick legitimate multi-line text, and an emoji title is not refused.**

One methodological note that matters, because my first pass got this wrong and it is the trap the
cycle-2 checker also flagged: reusing one step target makes `add_case` idempotent and the form
answers **400 — "this project already has a case with exactly these steps"**. That is AT-060, not
the guard. Every probe above was given a unique step target, and I read the 400 bodies to tell the
two apart in both directions.

## 4. The rename `_is_invisible` → `_is_ignorable` — right diagnosis, and the new name is STILL wrong

The maker's claim that the wrong name was part of the defect is **correct and well argued**: a
predicate promising "renders as nothing" was measurably false (U+0001 and U+007F draw visible
boxes), and a security predicate that promises the wrong thing invites the next implementation to
chase the wrong rule. Renaming was the right move.

But the new stated rule — *"none of these characters can carry meaning a reader takes off the
screen"* — **is false for the characters the predicate itself strips.** U+202E carries meaning a
reader takes off the screen: it reorders everything after it. So does U+202B, and so do the
isolates in U+2066–U+2069. `_is_ignorable` is more honest than `_is_invisible` and still names a
property its members do not have. Twice the implementation chased a mis-stated rule; the rule is
still mis-stated, and AT-355 is what that costs. **The bidi controls are not ignorable — they are
*layout* characters, and the only safe handling is to refuse text containing them, not to erase
them before comparing.**

## 5. The AT-354 deferral — the reasoning is wrong, and there is a falsifiable version

The maker argues an acceptance test for Indic/Arabic/emoji names "cannot be killed by any
mutation of this guard, because the guard only ever refuses and over-stripping the input makes it
match *less*, not more."

**That is false, and C7 already says so in the sentence written for exactly this situation:**
*"An unreachability claim is INCONCLUSIVE, never a justification … it has been refuted on the first
attempt both times it was made here (AT-315, AT-321)."* This is the third time, and it is refuted
again — by a mutation of the very line this unit added:

> `strip ALL Mn` is already in this unit's spec as a mutation. Widen it a little differently —
> strip `Mn` **and** `Mc` (Devanagari and Thai vowel signs), or simply
> `unicodedata.category(ch).startswith("M")` — and a Hindi or Thai name folds down to a stub. The
> guard then refuses **more**, not less: `contains_folded` is a substring test evaluated on the
> *folded* value, so over-stripping shortens the candidate toward a collision instead of
> lengthening it away from one. An acceptance test naming `परीक्षण मामला` dies on that mutation.

So the falsifiable version it should have written is one line of spec plus one parametrised test:
*"strip every category beginning with `M`"* as the mutation, killed by
`test_ordinary_unicode_text_is_still_accepted[hindi|arabic|thai|emoji-vs16]`. That is cheap, it is
not decoration, and it would have cost less than the paragraph arguing it was impossible. AT-354
stays **open**, and its ledger row now records that the deferral's stated reason was tested and
does not hold.

I will say the fair half too: the *instinct* behind it — do not add a test that cannot fail — is
the right instinct and is exactly what C7 asks for. The error was stopping at "I could not think of
a mutation", which is the failure mode C7 names by name.

## My read on the shape, since you asked

**Character-class-at-a-time is the wrong shape for this guard, and AT-355 proves it more strongly
than a fourth unlucky class would.** Three cycles subtracted families that "do not render". AT-355
is not a family anybody forgot — it is a character the guard **already strips**, which leaks
*because* it strips it. No amount of widening the deny-list closes that; widening makes it worse,
since every newly-stripped format character is another character whose layout effect the
comparison is now blind to.

An **allow-list of readable characters is sounder**, and I would scope it this way:

1. **Canonicalise, then require.** NFKC the text, then require every remaining character to be in a
   small positive set — letters, marks and digits of the scripts the product actually stores, plus
   ordinary punctuation and whitespace. Anything outside it is refused **as unrenderable input**,
   with a message naming the offending code point. That refusal is honest and actionable in a way
   "looks like a credential" is not.
2. **Bidi controls get their own rule, not a strip.** Any of `U+202A`–`U+202E`, `U+2066`–`U+2069`,
   `U+200E`/`U+200F`, `U+061C` in a stored field is refused outright. They exist to change reading
   order; a project name never needs one.
3. **Keep the fold for what it was actually good at** — case, separators, confusables, percent
   escapes. Those are reversals a human performs, the fold catches them well, and all of that work
   from three cycles survives the change.
4. **Then write the positive test cycle 2 asked for:** *does this text, rendered in a real browser,
   read as the credential?* The `visualOrder` probe in this evidence directory is a working
   implementation — sort glyphs by screen x, compare — and it is the only detector in this thread
   that caught AT-355. It belongs in the repo, not in a checker's scratch directory.

That is a design conversation with Umesh, not a fourth patch, which is why the honest outcome here
is STALLED.

## FAILURES

- **[U8] sev: high** · `POST /projects/{slug}/cases` accepts `U+202E` + the reversed credential in
  `title`, `step_value` and `step_expected` (HTTP 200 each); git-tracked `cases.jsonl` carries 7
  `\u202e` escapes and the Cases page renders `ZEBRA_QUILT_APIKEY_31` in plain type in the title
  boxes · fix direction: refuse bidi-control characters outright instead of stripping them before
  the comparison; do not extend the deny-list · issue: **AT-355**
- **[U9] sev: high** · `POST /onboard` accepts the same spelling (HTTP 200, `project.json`
  written) and the home index renders the exact credential, 21 glyphs, visually identical to a
  planted plain-credential control · same fix direction · issue: **AT-355**

## Issues written

- **AT-355** (high, open) — bidi-override spelling accepted at both doors and rendered as the
  exact credential; the guard's own `Cf` strip erases the character that causes it.
- **AT-356** (medium, open) — zero-width **visible** combining marks (U+0335, U+0301) interleaved
  between every character are accepted at both doors and render the credential legibly (struck
  through / accented). Not charged: reading it takes looking past the marks, which is the AT-352
  line the previous two checkers drew and I am not moving it in the final cycle.
- **AT-354** (low) — note appended: the deferral's stated reason ("no mutation can kill it") was
  tested and does not hold; the mutation *strip every category beginning with M* kills such a test.
- **AT-352, AT-349, AT-347** — unchanged; I agree with how each is scoped.

## What I am NOT charging

The unit did everything cycle 2 asked for, and did it well. AT-353 is closed at both doors with a
mutation that names U+0000 explicitly and dies at both. The false-positive probe is clean at 11/11.
The rename was the right call even though the new name is still inaccurate. The mutation harness is
honest and its attribution holds on all ten. C2 and C7 both hold. None of that is in dispute — the
FAIL rests entirely on AT-355, which I reproduced in my own browser, with a positive control, and
which I would defend at well over 80% confidence.

**Evidence:** `qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker/` —
`report.json`, `enumerate.py`, `attack.py`, `caseform.py`, `attack-results.json`,
`caseform-results.json`, `home-index-all-spellings.png`,
`at355-rlo-renders-credential-on-cases-page.png`. My server ran on a scratch `AUTOTESTER_ROOT`
outside the repo; no repo project was created, edited or deleted by this check. Console errors: 0.
