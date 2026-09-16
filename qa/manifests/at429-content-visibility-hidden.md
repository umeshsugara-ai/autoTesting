# Manifest — at429-content-visibility-hidden

**Unit:** AT-429 — `visual_text` reports text inside `content-visibility:hidden`, which a reader cannot see
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-429 (medium, open → fixed) · verifies the ledger repair for **AT-404** and
**AT-436** (my three rows moved to the canonical schema in `e33b916`)

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
| text whose parent is `content-visibility:hidden` is not reported, and does not interleave with the visible line (AT-429) | `test_content_visibility_hidden_is_not_reported_nor_garbles_its_neighbour` | remove the parent guard | KILLED (row 1) |
| **nested** hidden text is covered by `checkVisibility()`, and the two guards split the work without overlap | same test + `…[closed-details]` | bypass `checkVisibility()` | KILLED (row 2): both named tests fail |

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

- `uv run pytest` → expected: `1268 passed, 2 skipped, 32 xfailed`
  *(`uv run pytest -q` resolves to `-qq` and suppresses the summary line.)*
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`. It does **not** measure `.js` files (AT-419), so count
  `visual_order.js` yourself: 295.
- `uv run python scripts/mutation_check.py qa/evidence/at429-content-visibility-hidden/mutations.json`
  → `2/2 mutations killed`
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
at429-content-visibility-hidden        2/2 mutations killed
at358-visual-order-detector            21/21 mutations killed
at410-first-glyph-content-visibility   1/1 mutations killed
at379-scrollable-pane-reachability     7/7 mutations killed
at423-scroll-invariance-probe          3/3 mutations killed

$ uv run pytest
1268 passed, 2 skipped, 32 xfailed, 1 warning in 209.33s (0:03:29)
```

The `1268` includes the other maker loop's tests in this shared tree. This unit adds one test.

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
