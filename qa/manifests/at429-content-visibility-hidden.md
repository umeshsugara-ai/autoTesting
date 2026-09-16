# Manifest — at429-content-visibility-hidden

**Unit:** AT-429 — `visual_text` reports text inside `content-visibility:hidden`, which a reader cannot see
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-16
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-429 (medium, open → fixed) · **AT-437** (medium, cycle-1 FAIL, created by
cycle 1's own fix) · AT-438 recorded as a strict xfail, not fixed · AT-404 / AT-436 already verified
fixed by the cycle-1 checker

## Cycle 2: my false-positive fix created a false negative, again

The cycle-1 verdict confirmed the fix works on block boxes: direct hidden text is dropped, nested
hidden text is still caught by `checkVisibility()`, and the interleave is real and gone. It then
failed the unit on the thing this module keeps doing:

> **AT-437 (medium).** The guard `style.contentVisibility === "hidden"` drops **visible** text
> wherever `content-visibility:hidden` has no effect: an inline `<span>`, an inline custom element,
> a ruby `<rt>`. A live screenshot shows the text painted, the old code reported it, and the fixed
> code drops it.

That is the **sixth** time a fix for a false positive in this file has created a false negative, and
it is the same mistake this file keeps recording. The guard trusted **computed style**, and computed
style says `hidden` on **every** box the property is set on, including boxes where the browser
ignores it and paints the text.

### The fix is decided by a screenshot, not by the spec

I did not write down a list of display types from memory or from the CSS Containment spec; I
measured every one. `qa/evidence/at429-content-visibility-hidden/groundtruth.py` builds one isolated
page per display type and takes a screenshot of a fixed frame. It then makes the element's text
transparent and takes a second screenshot. If the two are identical, the text was never painted; if
they differ, it was. This is the same ground-truth method the checker used, it does not depend on
computed style or `checkVisibility()`, and the checker can re-run it.

Measured in Chromium across 20 display types:

| display | with `content-visibility:hidden` |
|---|---|
| `block` | hides |
| `inline` | **paints** |
| `inline-block` | hides |
| `flex` | hides |
| `inline-flex` | hides |
| `grid` | hides |
| `inline-grid` | hides |
| `flow-root` | hides |
| `list-item` | hides |
| `table-cell` | hides |
| `table-caption` | hides |
| `table` | **paints** |
| `inline-table` | **paints** |
| `table-row` | **paints** |
| `table-row-group` | **paints** |
| `table-header-group` | **paints** |
| `table-footer-group` | **paints** |
| `contents` | **paints** |
| `ruby` | **paints** |
| `ruby-text` | **paints** |

**Measuring caught an error that reading the spec would have made.** `table` and `inline-table`
**paint** their text. A list written from the spec ("containment does not apply to non-atomic
inline, internal table boxes other than cells, internal ruby boxes") does not name the table box
itself. A guard built from the spec would have kept dropping visible text in tables. The only reason
that case is right is that it was measured.

### Why the guard is an ALLOW-list

`HIDES_ON` lists the display types that were measured to **hide** text, and the guard fires only for
those. A deny-list (fire everywhere except the types known to paint) and an allow-list give the same
answer on every measured display type. They differ only on a type nobody has measured, and there they
fail in opposite directions. A deny-list would drop text on an unmeasured type, which risks missing a
credential. An allow-list would report it, which is a false positive. This module has already written
down which of those costs more, so the guard is an allow-list.

### What changed in cycle 2

- `src/autotester/browser/visual_order.js`: added `HIDES_ON`, copied from the measurement, and changed
  the guard to `contentVisibility === "hidden" && HIDES_ON.test(display)`. The existing comment was
  rewritten rather than lengthened. **298 lines.**
- `qa/evidence/at429-content-visibility-hidden/groundtruth.py` and `groundtruth.json`: **new**. The
  re-runnable measurement and its output.
- `tests/fixtures/bidi_site/cvdisplay.html`: **new**. Each of the 20 display types sits in its own
  spaced block, so no two share a screen row and interleave.
- `tests/test_browser_visual_order.py`: one test parametrised over all 20 types. From the same
  measurement it asserts **both directions**: painted text must be reported (AT-437), and unpainted
  text must not be (AT-429). A guard that fired everywhere, or nowhere, would fail half the cases.
  267 lines.

### AT-438 is recorded, not fixed

`display:contents` paints its text, and the detector drops it. The cause is a different guard.
`checkVisibility()` returns **false** on a `contents` box, so the text is dropped before the
`content-visibility` guard ever runs. I checked that this predates this unit. In a throwaway copy
running the **pre-AT-429 detector** (`dbe6185^`), with imports confirmed to come from that copy, the
`[contents]` case fails the same way. It is marked `xfail(strict=True, reason="AT-438")`, so fixing
AT-438 later will fail loudly here instead of passing unnoticed. It was not folded into this unit.

### A mutation claim I had to correct

My first version of row 1 (drop the display condition) listed `[table]` and `[table-row]` among the
tests it kills, and **both survived**. I measured why. In those fixtures the text's parent is a `<td>`,
not the element carrying `content-visibility`. The guard checks only the parent, so it never runs
there, whether or not the display condition is present. Those cases are still correct assertions
(painted text is reported), but they do not test the allow-list. The row now lists the cases that do:
`inline`, `ruby` and `ruby-text`, where the text sits directly inside the element.

## Why this unit

AT-429 is the second of the two defects that must be fixed before `visual_text` can be used in the
crawl. (AT-410 is closed; AT-416 is waiting on a human decision.) It does not touch the gated
`reachOf` / clip logic. The change is in `paintsInk`.

## The filed diagnosis was only half right, and measuring showed a worse half

I filed AT-429 from a page where a `content-visibility:hidden` block sat directly after an
`auto` block. Before fixing anything, I re-measured on five layouts, running both the old and the
current detector on each:

| page | `auto` text | `hidden` text | output |
|---|---|---|---|
| `auto` first, then `hidden` | reported ✓ | **reported ✗** | `CONTROL_QAUTO_S1HIDDEN_S2` |
| `hidden` first, then `auto` | **missing ✗** | **missing ✗** | `CONTROL_Q`**`HAIUDTDOE_NS1_S2`** |
| `auto` alone | reported ✓ | — | `CONTROL_QAUTO_S1` |
| `hidden` alone | — | **reported ✗** | `CONTROL_QHIDDEN_S2` |
| `hidden` + sized `auto` | **missing ✗** | **missing ✗** | interleaved |

Old and new detectors gave identical output on every page, so the AT-410 fix is not involved.

**The false positive also destroys a true positive.** A `content-visibility:hidden` element has zero
height, so its unrendered text sits at the same screen position as the visible line that follows,
and the two **interleave** (`HAIUDTDOE_NS1_S2` is `HIDDEN_S2` woven into `AUTO_S1`). A substring
search then finds neither. So on these layouts the defect does more than report text a reader cannot
see: it also **hides text a reader can see**. That is the AT-355 kind of false negative, so this is
not only a false-positive problem.

## The cause, measured

`content-visibility:hidden` stops the browser rendering an element's **contents**, but the element's
own box stays in the layout. So `checkVisibility()` returns **true** on that element. The AT-372
guard in `paintsInk` calls `checkVisibility()` on the text's **parent**, and for direct child text
that parent is the hidden element itself, so the guard never fired.

## Why the fix checks only the parent: the first version failed its own mutation

My first fix walked **every ancestor** looking for `content-visibility:hidden`. Its mutation (check
only the parent, not ancestors) **survived**:

```
>>> SURVIVED  AT-429: only the text's own parent is checked, not the ancestors (nested case leaks)  (pytest exit 0)
    actually failed: (nothing)
```

Before changing anything I measured why:

```
direct {'parentCV': 'hidden',  'firstGlyphWidth': 10.67, 'parentCheckVisibility': True}
nested {'parentCV': 'visible', 'firstGlyphWidth': 10.67, 'parentCheckVisibility': False}
```

For **nested** text, `checkVisibility()` on the `<p>` already returns **false**, because
`checkVisibility()` checks ancestors for `content-visibility:hidden`. Only **direct** child text
gets past it. The ancestor walk repeated a check that already existed, so no test could ever show
it mattering.

This file already records the same lesson once, at `checkVisibility()`'s default options: "a rule
whose failure another rule covers cannot be falsified … Each rule answers for itself." The fix is
now the single missing condition, `style.contentVisibility === "hidden"` on the parent. It is
shorter, and every line of it can be falsified.

## What changed

- `src/autotester/browser/visual_order.js`, `paintsInk`: one guard,
  `if (style.contentVisibility === "hidden") return false;`, with a comment saying why only the
  parent is checked. To stay under the 300-line cap, two existing comments (the alpha regex and the
  width test) were shortened with their content kept. **295 lines.**
- `tests/fixtures/bidi_site/cvhidden.html`: **new**. It has a direct `hidden` block, a nested
  `hidden` block, and an on-screen `auto` block placed **after** them (the layout that interleaves).
- `tests/test_browser_unreadable.py`: one new test. 294 lines.
- `qa/evidence/at429-content-visibility-hidden/mutations.json`: 2 mutations.

## Capability coverage (each new claim → its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| painted text on a box where `hidden` has no effect is **reported** (AT-437) | `…reported_exactly_where_it_paints[inline]`, `[ruby]`, `[ruby-text]` | drop the display condition from the guard | KILLED (row 1) |
| hidden direct text is **not** reported and does not interleave (AT-429) | `…[block]`, `…[flex]`, `test_content_visibility_hidden_is_not_reported_nor_garbles_its_neighbour` | remove the guard entirely | KILLED (row 2) |
| the allow-list is the MEASURED set, and each entry is needed | `…[table-cell]` | remove `table-cell` from `HIDES_ON` | KILLED (row 3) |
| **nested** hidden text is `checkVisibility()`'s job, and the two guards do not overlap | `…not_reported_nor_garbles…`, `…[closed-details]` | bypass `checkVisibility()` | KILLED (row 4) |

```
$ uv run python scripts/mutation_check.py qa/evidence/at429-content-visibility-hidden/mutations.json
KILLED  AT-429 reopens: text whose own parent is content-visibility:hidden is reported  (pytest exit 1)
KILLED  AT-429 division of labour: without checkVisibility the NESTED hidden text leaks  (pytest exit 1)
    claims to kill : …::test_content_visibility_hidden_is_not_reported_nor_garbles_its_neighbour, …::test_text_a_reader_cannot_see_is_not_reported[closed-details]
    actually failed: …::test_content_visibility_hidden_is_not_reported_nor_garbles_its_neighbour, …::test_text_a_reader_cannot_see_is_not_reported[closed-details]
2/2 mutations killed
```

**The boundary is asserted in the test.** `content-visibility:auto` text must still be reported in
full. A fix that simply excluded all `content-visibility` content would pass both negative
assertions and bring AT-410 back. The positive assertion on `CVAUTO_ONSCREEN_SENTINEL_63` is also
what catches the interleave: before the fix it failed because the visible text was scrambled, not
because it was absent.

## How to verify (commands + expected)

- `uv run pytest` → expected: `1287 passed, 2 skipped, 33 xfailed` (the 32 scroll-invariance layouts plus AT-438)
  *(`uv run pytest -q` resolves to `-qq` and suppresses the summary line.)*
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`. It does **not** measure `.js` files (AT-419), so count
  `visual_order.js` yourself: 298.
- `uv run python scripts/mutation_check.py qa/evidence/at429-content-visibility-hidden/mutations.json`
  → `4/4 mutations killed`
- **Ground truth:** `uv run python qa/evidence/at429-content-visibility-hidden/groundtruth.py` must
  match `CV_PAINTS` in the test, case by case.
- **Regression on every spec that touches this module:** at358 `21/21`, at410 `1/1`, at379 `7/7`,
  at423 `3/3`. The scroll-invariance corpus is unchanged at **32 xfailed with no XPASS**.
- **Ledger (AT-404, AT-436):** AT-398, AT-423 and AT-429 in `qa/issues.jsonl` carry the canonical
  keys (`date`, `found_by`, `feature`, `evidence`) and none of the made-up ones (`opened`, `source`,
  `area`, `detail`). `e33b916` changed exactly those three lines.

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ (fix verified on the five measurement pages)
a_auto_first.html    AUTO=True (expected True ) HIDDEN=False(expected False) | 'CONTROL_QAUTO_S1'
b_hidden_first.html  AUTO=True (expected True ) HIDDEN=False(expected False) | 'CONTROL_QAUTO_S1'
c_auto_alone.html    AUTO=True (expected True ) HIDDEN=False(expected False) | 'CONTROL_QAUTO_S1'
d_hidden_alone.html  AUTO=False(expected False) HIDDEN=False(expected False) | 'CONTROL_Q'
e_auto_sized.html    AUTO=True (expected True ) HIDDEN=False(expected False) | 'CONTROL_QAUTO_S1'

$ mutation specs
at429-content-visibility-hidden        4/4 mutations killed
at358-visual-order-detector            21/21 mutations killed
at410-first-glyph-content-visibility   1/1 mutations killed
at379-scrollable-pane-reachability     7/7 mutations killed
at423-scroll-invariance-probe          3/3 mutations killed

$ uv run pytest
1287 passed, 2 skipped, 33 xfailed, 1 warning in 213.54s (0:03:33)
```

The `1287` includes the other maker loop's tests, which share this working tree. This unit adds 21 tests: 1 in cycle 1 and 20 parametrised cases in cycle 2.

## Live browser evidence

The unit's tests are the browser evidence: a real headless Chromium against a real HTTP server,
asserting on the measured glyphs. Separately, I measured the old and current detectors on five
layouts through direct Playwright runs before any fix, and re-measured after it (tables above), so
the before-and-after comparison does not rest only on the fixture I committed.

No product page, template or route changed.

## What this unit does NOT do

- **It does not touch the AT-416 line** (`reachOf` / clip), which is waiting on the human decision.
- **It does not wire `visual_text` into the crawl.** With AT-410 and AT-429 fixed, AT-416 is the only
  remaining blocker that I know of.
- **It does not close AT-404 / AT-436.** It asks the checker to verify the ledger repair; closing
  them is the checker's job.

## Status: ready-for-check
