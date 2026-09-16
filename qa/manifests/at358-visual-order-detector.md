# Manifest — at358-visual-order-detector

**Unit:** AT-358 — port the glyph-order detector into the repo
**Contract:** `qa/contracts/ui.md` (U13 names this as the non-enumerating instrument) ·
`qa/contracts/browser-and-secrets.md` (B4, B7) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 3 of max 3 — **the last one**
**Dual check:** no
**Issues addressed:** AT-358 (medium) · AT-361 (medium) · AT-362, AT-363, AT-364 (cycle-1 FAIL,
verified fixed by the cycle-2 checker) · AT-371, AT-372, AT-373, AT-374 (cycle-2 FAIL)

## Cycle 3 — the four cycle-2 findings, all answered

The cycle-2 verdict confirmed every cycle-1 failure was genuinely answered and then failed the unit
on a second independent sweep of ordinary page constructs. It also stated its own bound: *"I probed
28 constructs across 6 pages… I will not extend the list again on cycle 3 — a channel found after
this is a new issue against the next unit, not a FAIL of this one."* This cycle takes all four
findings at face value and fixes rather than argues.

| Finding | sev | Answer |
|---|---|---|
| **AT-373** — the `isReachable` rule added in cycle 2 made the result **scroll-dependent** | medium | **Fixed in code + pinned by a test.** The one I would not have accepted as prose either. |
| **AT-372** — a closed `<details>` body reported; a `-webkit-text-security` run returned in cleartext | medium | **Fixed in code + pinned**, both of them. |
| **AT-371** — the limits block named `::before`/`::after` and stopped, missing `::marker` | medium | **Disclosed** — the block now names the generated-content **class**, not two members of it. |
| **AT-374** — `<svg><text>` was listed as not seen, and is seen | low | **Corrected.** Moved out of the limits block under a heading that does not lie about it. |

### AT-373 is the one that mattered, and it was self-inflicted

The cycle-2 fix for the false positives manufactured a false **negative of the AT-355 shape** — the
exact defect this whole module exists to catch. A client rect is viewport-relative, so testing
`rect.right <= 0` meant that on a scrolled page everything above the fold tested as unreachable and
silently vanished from the result. The next unit wires this into a crawl **that scrolls**, so it
would have shipped directly into the one caller that triggers it.

Fixed by taking the two axes against the document (`+ window.scrollX` / `+ window.scrollY`). The
clipping-ancestor intersection stays viewport-relative, which is correct — a clipping ancestor and
its content scroll together. The test asserts **equality** of the whole string before and after
scrolling to the bottom, not a substring: it pins that nothing moves in *or* out.

### The password branch turned out to be dead code — and it is staying

`test_a_password_field_is_reported_as_the_bullets_it_shows` **survived** the mutation that removes
the `type === "password"` branch, because Chromium implements password masking *as*
`-webkit-text-security`, so the new `masksText()` rule already covers it. Measured directly rather
than inferred:

```
$ (playwright probe)
input[type=password]         -webkit-text-security = 'disc'
input[name=plain]            -webkit-text-security = 'none'
```

```
>>> SURVIVED  AT-363: a password field's value is reported in cleartext  (pytest exit 0)
    claims to kill : …::test_a_password_field_is_reported_as_the_bullets_it_shows
    actually failed: (nothing)
    SURVIVING      : …::test_a_password_field_is_reported_as_the_bullets_it_shows
                     <- INCONCLUSIVE: this mutation did not make them fail
```

**The redundant branch is kept deliberately**, and this is the one place in the unit where I did not
delete dead code on finding it. Cycle 1 deleted a dead tag deny-list and was right to; this is
different, because the thing making it dead is a **UA-stylesheet implementation detail of one
browser**. Staking credential masking on Blink's choice to implement `type=password` through a
`-webkit-` property is a bet I am not willing to make silently on a credential path. So it stays as
defence in depth, and the redundancy is **disclosed with its evidence** rather than hidden —
C7's rule for exactly this case.

The *capability* is still pinned. The spec row no longer tries to attribute masking to one branch;
it removes masking entirely (`const masked = false`), which kills both the password test and the
`-webkit-text-security` test. What is unfalsifiable is the attribution, not the behaviour.

### What changed in cycle 3

- `src/autotester/browser/visual_order.js` — `isReachable` takes the scroll offsets (AT-373);
  `paintsInk` consults `Element.checkVisibility()` with **default** options (AT-372 `<details>`);
  new `masksText()` applied to both text runs and control values (AT-372); limits block rewritten
  for AT-371 and AT-374. 241 lines.
- `tests/fixtures/bidi_site/unreadable.html` — a closed `<details>` and a 2000px spacer so the page
  is taller than the viewport and can actually be scrolled.
- `tests/fixtures/bidi_site/controls.html` — a masked `<span>` and a masked `<input>`.
- `tests/test_browser_visual_order.py` — 18 → **21** tests. 297 lines.
- `qa/evidence/at358-visual-order-detector/mutations.json` — 17 → **21** mutations.

**`checkVisibility()` is called with default options on purpose.** `{opacityProperty: true,
visibilityProperty: true}` would have subsumed the opacity and visibility rules below it — and a
rule whose failure another rule covers cannot be falsified, so both of those mutations would have
started surviving and C7's kills would have quietly gone vacuous. Each rule answers for itself.

## Cycle 2 — what the checker charged, and what I did with it

The cycle-1 verdict (`qa/verdicts/at358-visual-order-detector.md`) ended on a sentence that set this
cycle's shape:

> The maker chooses between extending coverage and disclosing the limits; I charged the gap between
> the claim and the measurement, not a scope.

So the three findings were answered differently, on purpose:

| Finding | sev | Answer |
|---|---|---|
| **AT-363** — six constructs reported that a reader cannot see | medium | **Fixed.** Every one. |
| **AT-362** — placeholder | high (part) | **Fixed** — it renders, so it is measured. |
| **AT-362** — shadow roots, same-origin frames, `::before`/`::after`, `<canvas>`, `<svg><text>`, `title`/`alt` | high (rest) | **Disclosed**, in the module docstring, with the same specificity the `<select>` sentence had — and with the `<select>` justification *removed*, because the checker was right that it reasons the channel closed for U13's guard while saying nothing about the instrument. |
| **AT-364** — one added test carried no mutation | low | **Fixed** — the checker's own mutation is now row 17 of the spec. |

**Why disclose rather than extend, for those six.** Crossing a shadow boundary and a frame boundary
is a different walk with its own failure modes (closed roots, cross-origin frames that throw,
`::before` content that is a `counter()` or an `attr()` rather than a string). Bundling it here
would put two units in one and hand the checker a second large surface to judge against an
already-contested claim. The limits are now written where the next reader meets them, so a clean
result is read for what it is rather than for what the docstring used to promise.

## What changed in cycle 2

- `src/autotester/browser/visual_order.js` — `paintsInk` (computed opacity up the ancestor chain +
  colour alpha), `clipRect`/`isReachable` (viewport-left/top and nearest clipping ancestor),
  `mirrorGlyphs` (password → bullets, empty control → placeholder), and a
  `WHAT THIS DOES NOT SEE (AT-362)` block naming every unmeasured channel. 185 lines.
- `tests/fixtures/bidi_site/unreadable.html` — **new**; six invisible constructs, one sentinel each,
  plus a planted positive control on the same page.
- `tests/fixtures/bidi_site/controls.html` — **new**; a password field and an empty placeholder field.
- `tests/test_browser_visual_order.py` — 10 → **18** tests (a 6-way parametrisation for AT-363 plus
  the placeholder and password cases). 254 lines.
- `qa/evidence/at358-visual-order-detector/mutations.json` — 10 → **17** mutations.

## Three defects my own tests found inside the cycle-2 fix

1. **The alpha regex read the BLUE channel as the alpha.** The first version was
   `rgba?\([^)]*,\s*([\d.]+)\s*\)`, which matches plain `rgb(0, 0, 0)` too and captured `0` from the
   blue component — so ordinary black text was classed transparent and `visual_text` returned `''`
   for **every page**. Every "is not reported" assertion in the file would have passed on a detector
   that saw nothing at all. The same-page positive control is the only reason this was caught; it is
   the technique the cycle-1 checker used, and it fired on its author. Now anchored to the
   four-component form.

2. **The off-left reachability rule killed the detector's own mirror.** The mirror span sits at
   `left:-99999px` by design, which is exactly what `isReachable` rejects — so adding the AT-363 rule
   silently un-did the AT-361 fix. Fixed with an explicit `checkReachable` parameter: the mirror's
   internal order is a measurement, and the **control's own** position is what decides whether a
   reader can reach it.

3. **Two adjacent inputs interleaved** into `PLACEHOLDER_SENTINEL_8•8••••`. Re-seating each mirrored
   glyph at its own `x` and letting the global sort take over is wrong: a long value overflows its
   box in the mirror where the control itself clips it, so two controls' runs overlap in `x`. A
   control's value is now **one atomic item** at the control's position.

None of the three is a mutation kill — each was found by a test that was written for a different
reason and went red. That is the argument for the same-page positive control, stated as evidence
rather than as a principle.

## Capability coverage (each new claim → its isolating falsification)

Every row's `observed` is the pasted `mutation_check.py` output below, which prints the named test
as PASSING in the pre-mutation baseline (the runner **refuses to start against a red baseline**) and
then names the test that actually failed after the edit — the attribution check, not just a non-zero
exit. All 21 rows are single-hunk edits to a single file named in "What changed".

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| text is returned in screen order, not document order | `test_the_detector_sees_what_the_dom_hides` | remove the `items.sort` | KILLED (row 1) |
| the result is measured, not read off the DOM | same + `test_a_zero_width_interleaved_secret_is_seen…` | `observe.py` returns `inner_text("body")` | KILLED (row 2) |
| unpainted characters are dropped | `test_a_zero_width_interleaved_secret_is_seen…` | `if (false) continue` | KILLED (row 3) |
| the width test is not the element form | same | regress to `width===0 && height===0` | KILLED (row 4) |
| a clean result is not vacuous | `test_the_detector_sees_a_plainly_rendered_secret` | `return ""` | KILLED (row 5) |
| `visibility:hidden` text is not swept in | `test_text_that_occupies_layout_but_is_invisible…` | `if (false) return false` | KILLED (row 6) |
| form-control values are measured at all (AT-361) | `test_a_secret_in_a_form_control_value_is_seen` | selector matches nothing | KILLED (row 7) |
| the value is mirrored, not read | `test_a_direction_override_inside_a_form_control…` | synthesise glyphs from `shown` | KILLED (row 8) |
| the mirror copies `unicode-bidi` | `test_reversal_forced_by_css_alone_is_seen` | force `unicodeBidi="normal"` | KILLED (row 9) |
| the page is left exactly as it was | `test_measuring_the_page_leaves_it_exactly_as_it_was` | drop `span.remove()` | KILLED (row 10) |
| zero colour-alpha is not reported (AT-363) | `…is_not_reported[transparent-colour]` | `if (false) return false` | KILLED (row 11) |
| opacity is consulted (AT-363) | `…[opacity-zero]`, `…[opacity-zero-ancestor]` | `return true` | KILLED (row 12) |
| opacity is read up the ancestors (AT-363) | `…[opacity-zero-ancestor]` | loop over `[el]` only | KILLED (row 13) |
| off-screen and clipped glyphs are dropped (AT-363) | `…[text-indent-offscreen]`, `…[absolute-offscreen]`, `…[overflow-clipped]` | `if (false) continue` | KILLED (row 14) |
| a control the screen masks reports bullets, not the value (AT-363/AT-372) | `…password_field_is_reported_as_the_bullets…`, `…masked_run_is_reported_as_the_bullets…` | `const masked = false` | KILLED (row 15) |
| a masked INPUT is not returned in cleartext (AT-372) | `test_a_masked_run_is_reported_as_the_bullets_it_shows` | drop `masksText` from the control rule | KILLED (row 18) |
| a masked TEXT RUN is not returned in cleartext (AT-372) | same | pass `false` as the walker's mask argument | KILLED (row 19) |
| a closed `<details>` body is not reported (AT-372) | `…is_not_reported[closed-details]` | `if (false) return false` on `checkVisibility` | KILLED (row 20) |
| the result does not depend on scroll position (AT-373) | `test_the_result_does_not_depend_on_where_the_page_is_scrolled` | test reachability against the VIEWPORT again | KILLED (row 21) |
| an empty control's placeholder is measured (AT-362) | `test_a_placeholder_is_reported_because_it_renders` | drop `|| control.placeholder` | KILLED (row 16) |
| the bidi fixture really does store the secret reversed (AT-364) | `test_the_dom_calls_the_bidi_page_clean` | store it forwards in `hidden.html` | KILLED (row 17) |

Row 17 is the **checker's own mutation**, pasted in verbatim from
`qa/evidence/browser-at358-visual-order-detector-2026-09-11-checker/checker-mutations.json` as the
verdict instructed. It is the only row whose edit is to a fixture rather than to source, because the
claim it falsifies is a claim about the fixture.

## How to verify (commands + expected)

- `uv run pytest` → expected: `1191 passed, 2 skipped`
  **(note: `pytest -q` prints no count here — `addopts = "-q"` in `pyproject.toml` plus a second
  `-q` on the command line is `-qq`, which suppresses the summary line. Exit 0 still holds; the
  earlier manifests in this repo quote a count because they ran it a different way.)**
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_browser_visual_order.py` → expected: 21 passed (real Chromium; skips
  cleanly if the browser binary is absent)
- `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json`
  → expected: `21/21 mutations killed` (C7)

## Actual outputs (from maker's own run, 2026-09-16 — cycle 3)

```
$ uv run pytest
1191 passed, 2 skipped, 1 warning in 212.99s (0:03:32)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest tests/test_browser_visual_order.py -o addopts= -q
.....................                                                    [100%]
21 passed

$ uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json
KILLED  glyphs are not sorted by screen position - document order returns  (pytest exit 1)
KILLED  the detector reads innerText instead of measuring glyphs  (pytest exit 1)
KILLED  unpainted characters are kept - the AT-345 blindness returns  (pytest exit 1)
KILLED  the width test regresses to the enumerate.js element form  (pytest exit 1)
KILLED  the detector returns nothing at all - every clean result is vacuous  (pytest exit 1)
KILLED  invisible-but-laid-out text is swept in as if a reader saw it  (pytest exit 1)
KILLED  AT-361 reopens: form controls are not measured at all  (pytest exit 1)
KILLED  the control's value is READ instead of mirrored and measured  (pytest exit 1)
KILLED  the mirror keeps the control's direction but drops unicode-bidi  (pytest exit 1)
KILLED  the offscreen mirror is left in the page  (pytest exit 1)
KILLED  AT-363: zero-alpha colour is reported as if a reader saw it  (pytest exit 1)
KILLED  AT-363: opacity is never consulted  (pytest exit 1)
KILLED  AT-363: opacity is read on the element only, not up the ancestors  (pytest exit 1)
KILLED  AT-363: unreachable glyphs are reported (off-left and clipped)  (pytest exit 1)
KILLED  AT-363: a control the screen masks is reported in cleartext  (pytest exit 1)
KILLED  AT-362: an empty control's placeholder is not measured  (pytest exit 1)
KILLED  AT-364 (checker-written): the bidi fixture stores the secret forwards  (pytest exit 1)
KILLED  AT-372: a masked INPUT (-webkit-text-security) is reported in cleartext  (pytest exit 1)
KILLED  AT-372: a masked TEXT RUN is reported in cleartext  (pytest exit 1)
KILLED  AT-372: a CLOSED <details> body is reported as text a reader saw  (pytest exit 1)
KILLED  AT-373: reachability is tested against the VIEWPORT, so scrolling loses text  (pytest exit 1)
21/21 mutations killed
```

Per-mutation attribution (`claims to kill` vs `actually failed`, both printed per row) is in
`qa/evidence/at358-visual-order-detector/mutations.out`.

`tests/test_mutation_check.py` was green in this run. **AT-357 stays open**: those two tests assert
on a global `%TEMP%/mutation-check-*` glob and go red when the other maker loop in this repo runs a
mutation check concurrently. Not recurring is not the same as fixed, and the checker should judge
AT-357 on its own rather than as this unit's flake.

## Live browser evidence

This unit's own tests **are** the live browser evidence — they drive a real Chromium against a real
HTTP server and assert measured glyph positions, which is the only way the central claim can be
checked at all. Fixtures: 8 pages under `tests/fixtures/bidi_site/`. The cycle-1 checker drove its
own browser independently and its report is at
`qa/evidence/browser-at358-visual-order-detector-2026-09-11-checker/report.json` (console errors: 0).

## What this instrument does NOT see — named, not discovered

Copied here from the module docstring so a reader of the manifest meets the same list:

- text inside an **open shadow root**, and text in a **same-origin `<iframe>`**;
- **CSS generated content — the whole class**: `::before`, `::after`, **`::marker`** (an ordinary
  `<ol>`'s own "1." / "2." numbering is generated content), `::first-letter` / `::first-line`.
  AT-371 was filed because cycle 2 named two members and stopped;
- a **`<select>`'s** rendered option text — including `<select size="4">`, which shows its options
  permanently with no interaction, the hard case the cycle-2 checker measured;
- text painted into **`<canvas>`**;
- a **`title`** tooltip (renders on hover) or an **`alt`** string (renders only on image failure).

**`<svg><text>` has been removed from that list (AT-374).** It IS reported, measured twice by the
checker, and listing it was a false statement in a limits block — worse than no block, because the
block's own preface promises every entry is a page where a credential renders while this returns
clean. It now sits under a separate heading in the module saying it works *by accident* of SVG text
nodes being text nodes, with nothing pinning it, so it is not claimed as a capability either.

Each is a page where a credential could render in plain type while this returns a clean string.

**The `<select>` justification from cycle 1 is withdrawn.** It argued that a credential cannot
arrive in an option by U13's pasting accident, which is true of the *guard* and says nothing about
the *instrument*: `visual_text` reads other people's pages, where option text is authored by someone
else and can say anything. The limit stands; the reasoning that made it sound closed is gone.

## What is still not done, by decision

Wiring `visual_text` into the crawl so every screen is checked in reading order. The cycle-1 verdict
flagged the consequence precisely: the password field is masked to bullets **here**, but the moment
this has a caller its result must route through `Redactor.scrub` / `assert_no_raw_secrets` before it
reaches a log, an artifact or a model. That is a behaviour change to the explorer with its own
failure modes and it belongs to the next unit, which should carry that B4/B7 requirement in its
contract line rather than inherit it as folklore.

## Status: checked-PASS (cycle 3, verdict qa/verdicts/at358-visual-order-detector.md — pushed by the checker per D-007)
