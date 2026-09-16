# Manifest — at438-display-contents

**Unit:** AT-438 — `visual_text` drops visible text inside `display:contents`
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-438 (open → fixed)

## Why this one

`display:contents` text is text a reader can see, and the detector drops it. That is a **false
negative**, the error this module ranks as worse (a missed credential), so it comes before AT-440
(false positives from an incomplete allow-list) and AT-419 (doctor ignores `.js`). It is in
`paintsInk`, not the `reachOf` code gated on AT-416.

AT-438 was filed by the at429 cycle-1 checker and recorded as a strict xfail in at429 cycle 2. This
unit fixes it and removes that xfail.

## The defect

A `display:contents` element has **no box of its own**. Its children lay out as if they belonged to
its parent. `checkVisibility()` on such an element always returns **false**, because there is no box
to check, even though its text is painted. `paintsInk` calls `checkVisibility()` on the text's parent,
so any text directly inside a `contents` element was dropped.

## The first fix was wrong, and measuring showed it before it shipped

I prototyped the fix as an in-memory patch and ran it against the cases that must stay hidden as well
as the ones that must be reported. The first candidate walked up to the nearest ancestor **with a
box** and called `checkVisibility()` on that:

```
contents direct                  want=reported | OLD=dropped  WRONG | PATCHED=reported OK
contents nested twice            want=reported | OLD=dropped  WRONG | PATCHED=reported OK
contents in display:none         want=dropped  | OLD=dropped  OK    | PATCHED=dropped  OK
contents in visibility:hidden    want=dropped  | OLD=dropped  OK    | PATCHED=dropped  OK
contents in closed details       want=dropped  | OLD=dropped  OK    | PATCHED=reported WRONG
contents in cv:hidden block      want=dropped  | OLD=dropped  OK    | PATCHED=reported WRONG
```

It fixed the false negative and **created two false positives**. A closed `<details>` and a
`content-visibility:hidden` block are each **visible themselves** while hiding their **contents**, so
walking up to their box asked the wrong question. That is this module's usual mistake in the opposite
direction: a fix for a false negative that manufactures a false positive. The measurement is the only
reason it was caught before the manifest.

## The fix: ask the actual question

The real question is: **would an element placed here be visible?** The fix asks the browser exactly
that. When `checkVisibility()` fails on a `display:contents` element, a probe `<span>` is appended
**inside** it, `checkVisibility()` is called on the probe, and the probe is removed in a `finally`.
The probe inherits the context, so it is invisible inside a closed `<details>`, a
`content-visibility:hidden` block or a `display:none` ancestor, and visible otherwise:

```
contents direct                  want=reported | OLD=dropped  WRONG | PROBE=reported OK
contents nested twice            want=reported | OLD=dropped  WRONG | PROBE=reported OK
contents in display:none         want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in visibility:hidden    want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in closed details       want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in cv:hidden block      want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents with opacity:0 parent   want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
plain display:none               want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in OPEN details         want=reported | OLD=dropped  WRONG | PROBE=reported OK
contents in cv:auto on-screen    want=reported | OLD=dropped  WRONG | PROBE=reported OK
```

**10/10 correct.** The old detector got **4** wrong, not the 2 AT-438 named: it also dropped `contents`
text inside an **open** `<details>` and inside on-screen `content-visibility:auto`. The prototype also
checked `document.body.innerHTML` before and after every call; it was **identical** in all 10 cases.

### This is a second write to the page, and it is disclosed as one

The module already makes one deliberate, cleaned-up write: the offscreen mirror `<span>` for form
controls, appended to `<body>`. The probe is the second, and it is more intrusive in one way: it is
appended **inside an author element**, so a page's `MutationObserver` watching that element would
see a child added and removed. Three things limit it:

- It happens only on the rare path: `checkVisibility()` has already failed **and** the element is
  `display:contents`.
- It is removed in `finally`, so an exception while measuring still leaves the page clean.
- The test asserts the page's `innerHTML` is byte-identical after the call, and a mutation that
  drops the removal is killed (row 3).

The same trade was made for the mirror span and recorded in the module.

## What changed

- `src/autotester/browser/visual_order.js`: new `contentsRenders(el)` (the probe), and the
  `checkVisibility` guard becomes `!el.checkVisibility() && !contentsRenders(el)`. To stay within the
  300-line cap, three **non-gated** comments were shortened with every fact kept (the AT-374 SVG
  note, the checkVisibility default-options note, and the helper's own comment). The `reachOf` block
  was deliberately **not** touched, because it is the code gated on AT-416. **300 lines, at the cap.**
- `tests/fixtures/bidi_site/cvcontents.html`: **new**. Two cases that must be reported and three that
  must stay hidden (the trap), each in its own spaced block.
- `tests/test_browser_visual_order.py`: one new test covering both directions plus the DOM-unchanged
  assertion. **The AT-438 strict xfail on `[contents]` is removed**; that case now passes. 282 lines.
- `qa/evidence/at438-display-contents/mutations.json`: 3 mutations.
- `qa/evidence/at429-content-visibility-hidden/mutations.json` and
  `qa/evidence/at358-visual-order-detector/mutations.json`: **one anchor each repointed** to the
  changed `checkVisibility` line. Before writing, I checked that every row keeps the same name and
  the same `kills`, and that no mutation **body** (the `new` text) references a removed identifier.
  That was the AT-409 trap, where a stale body reddened every test while the count stayed at 21/21.

## Capability coverage (each new claim → its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| visible `display:contents` text is reported (AT-438) | `test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor`, `…reported_exactly_where_it_paints[contents]` | drop `&& !contentsRenders(el)` | KILLED (row 1) |
| it is NOT reported through a hiding ancestor (the walk-up trap) | `test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor` | replace the probe with a walk-up to the nearest box | KILLED (row 2) |
| observing the page leaves it unchanged | same test, `innerHTML` assertion | the probe is never removed | KILLED (row 3) |

Each row is a single-hunk edit to `src/autotester/browser/visual_order.js`, which is listed under
"What changed". **Row 2 is the rejected candidate itself**, applied as a mutation, so the manifest's
claim that walking up would have leaked is a measured result the checker can re-run, not an argument.

```
$ uv run python scripts/mutation_check.py qa/evidence/at438-display-contents/mutations.json
KILLED  AT-438 reopens: display:contents text is dropped by checkVisibility again  (pytest exit 1)
    claims to kill : …[contents], …test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
    actually failed: …[contents], …test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
KILLED  the measured trap: walk up to the nearest box instead of probing, so closed <details> / cv:hidden leak  (pytest exit 1)
    claims to kill : …test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
    actually failed: …test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
KILLED  the probe span is never removed, so observing the page changes it  (pytest exit 1)
    claims to kill : …test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
    actually failed: …test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
3/3 mutations killed
```

## How to verify (commands + expected)

- `uv run pytest` → expected: `1296 passed, 2 skipped, 32 xfailed`. That is **one fewer xfail** than
  before, because the AT-438 xfail was removed; the 32 left are the scroll-invariance layouts.
  *(`uv run pytest -q` resolves to `-qq` and suppresses the summary line.)*
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`. Doctor does not measure `.js` files (AT-419), so count
  `visual_order.js` by hand: **300**.
- `uv run python scripts/mutation_check.py qa/evidence/at438-display-contents/mutations.json` → `3/3`
- **Regression on every spec for this module:** at429 `4/4`, at358 `21/21`, at410 `1/1`, at379 `7/7`,
  at423 `3/3`.

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ wc -l src/autotester/browser/visual_order.js
300 src/autotester/browser/visual_order.js

$ uv run pytest "tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor" -o addopts= -q   (x3)
1 passed in 1.23s
1 passed in 1.14s
1 passed in 1.24s

$ mutation specs
at438-display-contents                 3/3 mutations killed
at429-content-visibility-hidden        4/4 mutations killed
at358-visual-order-detector            21/21 mutations killed
at410-first-glyph-content-visibility   1/1 mutations killed
at379-scrollable-pane-reachability     7/7 mutations killed
at423-scroll-invariance-probe          3/3 mutations killed

$ uv run pytest
1296 passed, 2 skipped, 32 xfailed, 1 warning in 220.84s (0:03:40)
```

The `1296` includes tests from the other maker loop, which shares this working tree. This unit adds
one test and turns one xfail into a pass.

## Live browser evidence

The unit's tests are the browser evidence: a real headless Chromium against a real HTTP server,
asserting on measured glyphs and on the page's `innerHTML`. Separately, the fix was prototyped as an
in-memory patch and measured on 10 layouts against the old detector **before** the file was edited
(tables above). That run exposed the walk-up trap and the old detector's two additional false
negatives.

No product page, template or route changed.

## What this unit does NOT do

- **It does not fix AT-440** (five hiding display types missing from the `content-visibility`
  allow-list, which leads to false positives).
- **It does not touch `reachOf`** (gated on AT-416).
- **`visual_order.js` is now exactly at its 300-line cap.** The next change to this file will need to
  trim or split it. AT-419 means doctor would not warn about that, so this manifest does.

## Status: ready-for-check
