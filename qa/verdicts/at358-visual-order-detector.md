# Verdict — at358-visual-order-detector

**Date:** 2026-09-11
**Cycle checked:** 1
**Manifest:** `qa/manifests/at358-visual-order-detector.md`
**Contract:** `qa/contracts/ui.md` U13 · `qa/contracts/browser-and-secrets.md` (B4, B7) ·
`qa/contracts/core-invariants.md` (C2, C7)
**Checker evidence (produced by this checker, not read):**
`qa/evidence/browser-at358-visual-order-detector-2026-09-11-checker/`

```
VERDICT: FAIL
SCOREBOARD: 3/5 criteria met, 4/5 invariants hold
FAILURES:
- [AT-361 / U13] sev: high · AT-361 is claimed fixed, but the ledger row's own coverage set ("text
  nodes + input/textarea values + placeholder and title/alt attributes") is not met: measured,
  placeholder text renders and is not reported. Alongside it the detector is blind to ::before/
  ::after generated content, open shadow DOM (text AND controls) and same-origin <iframe> content —
  four undisclosed channels of exactly the AT-355 false-negative class. · fix: extend coverage
  (shadow roots, same-origin frames, getComputedStyle(el,'::before').content, mirror placeholder
  when value is empty) or name each as a limit the way <select> already is · issue: AT-362
- [U13 / north star] sev: medium · The detector reports six kinds of text a reader cannot see:
  opacity:0, color:transparent, text-indent:-9999px, position off-screen, overflow-clipped text in
  full, and a type=password value in cleartext while the screen shows bullets. `isRendered` tests
  one CSS property. · fix: computed opacity/colour-alpha up the ancestor chain, intersect the glyph
  rect with the viewport and the nearest clipping ancestor, skip or mask type=password · issue: AT-363
- [C7] sev: low · One of the ten tests this unit adds (`test_the_dom_calls_the_bidi_page_clean`)
  carries no mutation; C7's duty is per added test. It is reachable — the checker wrote the
  mutation and it killed on the first attempt. · fix: paste
  `checker-mutations.json` from the checker evidence dir into the unit's `mutations.json` ·
  issue: AT-364
LIVE-BROWSER: qa/evidence/browser-at358-visual-order-detector-2026-09-11-checker/report.json
ISSUES-WRITTEN: AT-362, AT-363, AT-364
EXPLANATION: The core of this unit is sound and independently reproduced — the AT-355 shape, the
AT-345 shape, the AT-361 mirror, the page-left-alone property and 10/10 attributed mutation kills
all verified by the checker's own instruments. It fails on its own disclosure: the manifest states
exactly one known limit (<select>) and the module docstring asserts the result is "what a reader
sees", and a first pass of ordinary page constructs falsified that in both directions — four
rendered-text channels reported clean, six invisible constructs reported as seen. AT-361's ledger
row names placeholder coverage explicitly, so claiming it fixed is not yet earned.
```

## What the checker re-ran (nothing below is read from the manifest)

| Command | Checker's own result |
|---|---|
| `uv run pytest -q` | exit 0 — 1174 passed, 2 skipped |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json` | `10/10 mutations killed` |
| checker's own mutation spec (`checker-mutations.json`) | `1/1 mutations killed` |

`tests/test_mutation_check.py` was green in this run; `git status` showed no concurrent maker
edit in the tree, so AT-357 neither fired nor is attributed here.

## Mode D — the checker drove its own browser

Own headless Chromium, own HTTP server, own fixture pages (`pages/` in the evidence dir), calling
`autotester.browser.observe.visual_text` directly and screenshotting each page full-page. **Every
probe page carries a planted `CONTROL_ALPHA_11` and it was reported on every one of them**, so no
negative below is the detector simply returning nothing. Console errors: 0.

### False negatives — a human sees it, the detector is silent

| Construct | Rendered | Reported |
|---|---|---|
| `::before` / `::after` content | `PSEUDOBEFORE_SECRET_44`, `PSEUDOAFTER_SECRET_45` | no |
| open shadow root (text + `<input>`) | `SHADOW_SECRET_55`, `SHADOWINPUT_SECRET_56` | no |
| same-origin `<iframe>` | `IFRAME_SECRET_77` | no |
| `placeholder` on an empty field | `PLACEHOLDER_SECRET_A6` | no |
| `canvas` `fillText` | `CANVAS_SECRET_65` | no |
| `<select>` option text | `SELECT_SECRET_A3` | no — **disclosed** |
| SVG `<text>` | `SVGTEXT_SECRET_66` | **yes** |

The cause is structural and is the thing U13 names: the port is described as "the instrument that
does not enumerate", but it enumerates twice — `createTreeWalker(document.body, SHOW_TEXT)` and
`querySelectorAll("input, textarea")`. Generated content has no text node; neither API crosses a
shadow boundary or a frame boundary; `mirrorGlyphs` early-returns on an empty `value`.

### False positives — reported, but the screenshot shows nothing

`opacity:0` · `color:transparent` · `text-indent:-9999px` · `position:absolute;left:-9999px` ·
`overflow:hidden` clipped text returned in full (`CLIPPED_SECRET_95` where the reader sees
`CLIPP`) · `type=password` returned in cleartext where the reader sees bullets.

Correctly handled, and worth recording because they were not obvious: `font-size:0`,
`display:none`, `type=hidden`, an input inside a `visibility:hidden` wrapper, and — the subtle one
— `visibility:visible` nested inside `visibility:hidden`, which renders and is correctly kept.
Reading order is genuinely reconstructed: `float:right` source `S I H T D A E R` came back
`READTHIS`, grid `order` came back `YZ` from source `ZY`, absolute positioning came back by `x`,
and `writing-mode: vertical-rl` came back top-to-bottom. `transform: scaleX(-1)` / `rotate(180deg)`
come back in flipped screen order; the glyphs themselves are mirrored and unreadable, so that is
not an exposure channel and is not charged.

The password case deserves its own sentence: the mirror copies the control's font, `direction` and
`unicode-bidi` but not its masking, so the instrument un-masks exactly the field B7 masks before a
screenshot. It is **not** a B4/B7 breach today — `visual_text` has no caller anywhere in `src/` —
but it becomes one the moment the next unit wires it into the crawl, and the wiring must route the
result through `Redactor.scrub` / `assert_no_raw_secrets`.

## The page is genuinely left alone — this part is fully earned

Scrolled to `y=2732`, focused `#f1`, selected ten characters, snapshotted, called `visual_text`,
snapshotted again: `scrollY` 2732→2732, `activeElement` `f1`→`f1`, selection `'SELECTABLE'`
unchanged, both control values unchanged, `body.children` 5→5, `body.innerHTML.length` 228→228,
leftover `body > span` count 0, and a second call returned a byte-identical string.

The `finally` was tested rather than read: on a page whose only content is one `<input>`,
`document.createRange` was replaced with a thrower so `glyphsOf` raises **inside** `mirrorGlyphs`'
`try`. `page.evaluate` propagated `Error: boom` as it should, and afterwards `body > span` was 0
with `body.innerHTML` back to the bare input. The offscreen mirror also never reaches a screenshot:
`page.evaluate` completes within one page task, and the post-call screenshot of the password page
shows bullets and no span.

## C7 — mutation run, checked by hand

10/10 killed, reproduced. Attribution verified line by line: for all ten, every nodeid in
`claims to kill` appears in `actually failed`, and every exit code is 1 (tests ran and failed —
not a collection error reading as a kill).

**The vacuity fix is real, and proven by mutation rather than by reading.** The "drops
`unicode-bidi`" mutation failed exactly one test — `test_reversal_forced_by_css_alone_is_seen`, the
case whose sentinel was changed to `MARIGOLD_LEDGER_KEY_77`. Under the old shared `SECRET` that
test could not have been the one to notice, which is precisely the defect the manifest admits.

**Looking for the same defect elsewhere in the file** (the dispatch's point 5 — a shared `SECRET`
across fixtures is the shape that hides it): no second vacuous test. `SECRET` is shared by
`plain.html`, `hidden.html`, `zerowidth.html`, `invisible.html` and two fields of `inputs.html`,
but each assertion is pinned by something the sentinel alone cannot satisfy —
`test_a_secret_in_a_form_control_value_is_seen` dies when form controls stop being measured
(mutation 7), `test_a_direction_override_...` asserts `count(SECRET) == 2`, and both
"not visible" tests carry a distinct positive control (`Quarterly report`) on the same page.
Nine of the ten tests appear in at least one attributed failure list; the tenth,
`test_the_dom_calls_the_bidi_page_clean`, appears in none, which is AT-364.

## The `<select>` limit — judging the reasoning, as asked

The reasoning holds **for U13's threat model and only there.** U13's in-scope accident is "a hurried
human pasting a credential into a text box"; a `<select>` presents a fixed authored list and cannot
be pasted into, so a credential cannot arrive there by that accident. Accepted, not charged.

It does not generalise to what `visual_text` actually is. This is an **observation** capability —
the module docstring says so: "reading other people's rendered pages is what this product does" —
and on a third-party page under test an option's text is authored by someone else and can say
anything. So the sentence is right about the guard and incomplete about the instrument; the honest
form of the limit is "option text is not measured", without the justification that makes it sound
closed. The same wording problem is what turns AT-362 from a documentation nit into a finding: a
limits section that reasons one channel closed while four others go unmentioned reads as a survey,
and it is not one.

## Issues

- **AT-362** (high, open) — four undisclosed false-negative channels, placeholder among them.
- **AT-363** (medium, open) — six false-positive constructs, password cleartext among them.
- **AT-364** (low, open) — the one added test with no mutation; the checker supplied one.
- **AT-358** stays **open**: the port landed and its core works, but the unit did not pass.
- **AT-361** stays **open**: the mirror is real and correct for non-empty `input`/`textarea`
  values, but the ledger row's own coverage set includes placeholder and `title`/`alt`.
- **AT-357** untouched — not reproduced this run, and not fixed by this unit.

## What a PASS needs next cycle

Not a rewrite. Either extend the two enumerations (shadow roots, same-origin frames, generated
content, placeholder) or write the limits down honestly in the module docstring **and** the
manifest, with the same specificity the `<select>` sentence has; handle the cheap false positives
(computed opacity, colour alpha, viewport/clip intersection, `type=password`); and add the one
missing mutation. The maker chooses between extending and disclosing — a checker charges the gap
between claim and measurement, not a scope.
