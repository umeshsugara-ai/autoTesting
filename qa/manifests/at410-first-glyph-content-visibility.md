# Manifest — at410-first-glyph-content-visibility

**Unit:** AT-410: `visual_text` drops the first character of text inside a skipped subtree, on the first call
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-410 (high, open → fixed) · AT-398 (medium, the same defect's first sighting;
its fixture workaround is **reverted** here) · files **AT-429** (a separate false positive found
while reproducing)

## Why this unit

AT-410 is one of the two defects that must be fixed before `visual_text` is used in the crawl (the
other is the gated AT-416). It is **high** severity because it is a false negative of the AT-355 kind
in the shipped detector: text a reader can see, missing from the result. Callers call the detector
once, and the drop happens on exactly that first call.

It is in `glyphsOf`, a different function from the `reachOf` / clip logic that the AT-416 gate
covers, so it does not wait on that decision.

## The defect

When the browser has **skipped rendering** a subtree (off-screen `content-visibility:auto` with a
placeholder `contain-intrinsic-size`, or the body of a closed `<details>`), the first rect query
inside it returns all zeros **and that query itself forces layout**. `glyphsOf` measured character
by character, so character 0 took that first query, the width guard (`rect.width === 0`) dropped it,
and every later character measured correctly.

Measured against the unmodified detector, on the checker's own reproduction page
(`qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker-c2/pages/p7_cvauto.html`):

```
trial 0: FIRST has full sentinel=False  SECOND=True  | 'cerVAUTO_SENTINEL_91CVAUTO_SECOND_92CTLP'
trial 1: FIRST has full sentinel=False  SECOND=True  | 'cerVAUTO_SENTINEL_91CVAUTO_SECOND_92CTLP'
trial 2: FIRST has full sentinel=False  SECOND=True  | 'cerVAUTO_SENTINEL_91CVAUTO_SECOND_92CTLP'
```

`CVAUTO_SENTINEL_91` comes back as `VAUTO_SENTINEL_91` on the first call and correct on the second.
A second call hides the defect, and that is why AT-398's first investigator found a real rect and
no cause.

## The two fixtures that did not reproduce it, and why that matters

**I nearly shipped a test that proved nothing.** My first two fixtures read the text in full on the
first call:

1. A `content-visibility:auto` block **on screen.** Visible content is never skipped.
2. The same block **off screen, but with no `contain-intrinsic-size`.** Without a placeholder size
   the block renders anyway.

Both would have passed before the fix **and** after it. A test written against either would have
"proved" a fix for a defect the page never triggers. I found this out by measuring the unfixed
detector on each page first, not by reasoning about which page should trigger it. Then I stopped
building pages and took the **exact** page the checker had used, which does reproduce the drop
(3/3 above).

The committed fixture `tests/fixtures/bidi_site/cvauto.html` follows that page's layout, and its
comment explains why each of the three parts is required.

## What changed

- `src/autotester/browser/visual_order.js`, in `glyphsOf`: before the per-character loop, measure the
  whole text node once with a Range over its contents and **discard** the result. That throwaway
  query takes the all-zero rect and forces the layout, so character 0 is measured on real geometry.
  +11 lines, 298 in total.
- `tests/fixtures/bidi_site/cvauto.html`: **new**, the reproducing layout.
- `tests/test_browser_visual_order.py`: one new test, which asserts on the **first call of a fresh
  page** (a second call passes even on the unfixed detector). It also asserts the second line and a
  positive control.
- `tests/fixtures/bidi_site/unreadable.html`: **the AT-398 workaround is reverted.** At379 cycle 2
  moved the `<details>` sentinel off character 0 (`<p>body: DETAILSBODY_SENTINEL_77</p>`) because the
  first-glyph drop let a mutation survive. With the drop fixed, the sentinel goes back to
  `<p>DETAILSBODY_SENTINEL_77</p>`.
- `qa/evidence/at410-first-glyph-content-visibility/mutations.json`: 1 mutation.

### Why the revert is evidence, not tidying

The AT-410 issue pointed out that the closed-`<details>` test is a `not in` assertion, **so the
first-glyph drop could satisfy it as easily as the guard it is named for.** Moving the sentinel off
character 0 was a workaround that left that trap in place.

With the sentinel back at character 0, **the AT-358 mutation spec still kills 21/21.** The row
"a CLOSED `<details>` body is reported as text a reader saw" is killed and attributed to its own test:

```
claims to kill : tests/test_browser_unreadable.py::test_text_a_reader_cannot_see_is_not_reported[closed-details]
actually failed: tests/test_browser_unreadable.py::test_text_a_reader_cannot_see_is_not_reported[closed-details]
```

At379 cycle 2 recorded that **same row SURVIVING** with the sentinel at character 0, because the
dropped `D` satisfied the `not in`. It now kills there, so the drop is gone on this path as well, and
the `<details>` assertion again holds only because the guard works.

## Filed, not fixed: AT-429, a false positive found while reproducing

My first fixture included a `content-visibility:hidden` block as a boundary check, and **its text was
reported**. Measured: the element's box is 1264×0, `checkVisibility()` on it returns **true**, and
`visual_text` returns its sentinel on both calls.

`content-visibility:hidden` skips rendering an element's **contents** while its own box stays in
layout, so `checkVisibility()` on the element itself is true. The AT-372 guard calls
`checkVisibility()` on the text's parent, which here is that element, so the guard never fires.

This defect has the **opposite sign** from AT-410 (false positive, not false negative). It predates
this unit and belongs to a different guard, so it is filed as **AT-429 (medium)** with the
measurement, not folded in. The boundary assertion was removed from this unit's test, so the test
covers only the defect this unit fixes.

## Capability coverage (each new claim → its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| the first call reads the whole of a skipped subtree (AT-410) | `test_the_first_call_on_a_content_visibility_subtree_drops_no_glyph` | remove the warm-up query | KILLED (at410 row 1) |
| the closed-`<details>` guard holds on its own, with no drop covering for it (AT-398 trap closed) | `…is_not_reported[closed-details]`, sentinel back at character 0 | bypass `checkVisibility` (existing at358 row) | KILLED; this same row SURVIVED at character 0 in at379 cycle 2 |

Both are single-hunk edits to `src/autotester/browser/visual_order.js`, which is listed in "What
changed".

```
$ uv run python scripts/mutation_check.py qa/evidence/at410-first-glyph-content-visibility/mutations.json
KILLED  AT-410 reopens: the warm-up query is removed, so the first glyph of a skipped subtree drops  (pytest exit 1)
    claims to kill : tests/test_browser_visual_order.py::test_the_first_call_on_a_content_visibility_subtree_drops_no_glyph
    actually failed: tests/test_browser_visual_order.py::test_the_first_call_on_a_content_visibility_subtree_drops_no_glyph
1/1 mutations killed
```

## How to verify (commands + expected)

- `uv run pytest` → expected: `1260 passed, 2 skipped, 32 xfailed`
  *(`uv run pytest -q` resolves to `-qq` and suppresses the summary line.)*
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`. Doctor does **not** measure `.js` files
  (AT-419); `visual_order.js` is 298 lines, 2 under the 300-line cap.
- `uv run python scripts/mutation_check.py qa/evidence/at410-first-glyph-content-visibility/mutations.json`
  → `1/1 mutations killed`
- **Regression on the neighbouring specs:** `at358-visual-order-detector` → `21/21`,
  `at379-scrollable-pane-reachability` → `7/7`, `at423-scroll-invariance-probe` → `3/3`.
- **The scroll-invariance corpus is unaffected:** still exactly `32 xfailed` with **no XPASS**. The
  warm-up query does not accidentally fix or break any AT-416/AT-417 layout.

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ (first call on the reproducing page, AFTER the fix, 5 fresh pages)
trial 0: FIRST call full sentinel=True  second line=True  control=True
trial 1: FIRST call full sentinel=True  second line=True  control=True
trial 2: FIRST call full sentinel=True  second line=True  control=True
trial 3: FIRST call full sentinel=True  second line=True  control=True
trial 4: FIRST call full sentinel=True  second line=True  control=True

$ uv run pytest "tests/test_browser_visual_order.py::test_the_first_call_on_a_content_visibility_subtree_drops_no_glyph" -o addopts= -q   (x3)
1 passed in 0.98s
1 passed in 0.91s
1 passed in 0.95s

$ mutation specs
at410-first-glyph-content-visibility   1/1 mutations killed
at358-visual-order-detector            21/21 mutations killed
at379-scrollable-pane-reachability     7/7 mutations killed
at423-scroll-invariance-probe          3/3 mutations killed

$ uv run pytest
1260 passed, 2 skipped, 32 xfailed, 1 warning in 210.10s (0:03:30)
```

The `1260` includes tests from the other maker loop in this shared tree. This unit adds one test.

## Live browser evidence

The unit's tests are the browser evidence: a real headless Chromium against a real HTTP server,
asserting measured glyphs on the first call of a fresh page. The defect was also reproduced and the
fix confirmed by a direct Playwright run on the **checker's own** reproduction page (outputs above),
so the before and after comparison does not rely on a fixture I wrote.

No product page, template or route changed. `visual_text` still has no caller in `src/`.

## What this unit does NOT do

- **It does not fix AT-429** (reporting `content-visibility:hidden` contents). Filed.
- **It does not touch the AT-416 line** (`reachOf` / clip), which is waiting on the human gate.
- **It does not wire `visual_text` into the crawl.** That still waits on AT-416, and now also on
  AT-429, since a crawl would raise that false positive on real pages.

## Status: ready-for-check
