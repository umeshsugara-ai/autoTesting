# Manifest — at379-scrollable-pane-reachability

**Unit:** AT-379 — `visual_text` silently drops text below the fold of a scrollable pane
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-379 (medium, open → fixed — **both halves now**) ·
AT-392 (high, cycle-1 FAIL) · AT-393 (low, cycle-1 FAIL) · AT-394 (low, cycle-1 FAIL) ·
AT-398 (medium, **filed by this cycle against itself**)

## Cycle 2 — I fixed half of what AT-379 was filed for

The cycle-1 verdict verified every claim the code made and then failed the unit on the half I had
not noticed I was leaving:

> **AT-392 (high)** — a pane scrolled away from its origin still drops everything before its offset,
> on both axes. `PANETOP` dropped at `scrollTop=602`; `HPLEFT` dropped at `scrollLeft=1200`.

`isReachable` added only `window.scrollX/scrollY`, so the **window** case worked and the **pane**
case did not — and AT-379's own filed evidence names the scrolled pane explicitly. Marking it
`open → fixed` was a claim the evidence did not support.

**That line has now been wrong three times in the same direction**, and the pattern is the finding:

| | the rule | what vanished |
|---|---|---|
| **AT-373** | tested `rect.right <= 0` against the viewport | everything above the window's fold |
| **AT-379** | treated a scrollable pane's box as a hard clip | everything below the pane's fold |
| **AT-392** | added only `window.scrollX/scrollY` | everything before a scrolled pane's offset |

Every one was a fix for false **positives** that manufactured a false **negative** of the AT-355
shape — a credential rendering in plain type while this returns a clean string. Every one asked
*"can a reader SEE this?"* and forgot *"can a reader REACH it?"*. That is written into the source
at the line itself now, as a table, because three occurrences is a pattern and the next person to
touch that line should meet it before they edit it.

`clipRect` is replaced by `reachOf`, which returns `{clip, scrollX, scrollY}` — the accumulated
scroll offset of the window **and** every scrollable ancestor. A glyph is unreachable only if it
sits before the document origin after everything scrollable is scrolled back.

### The test I wrote for it was weak twice, and the mutation run is what said so

Neither weakness came from reasoning; both came from a SURVIVED row.

1. **The pane sat ~2000px down a tall page**, so scrolling it internally never pushed anything to a
   negative viewport coordinate. Measured: first line at `top=302`, never negative.
2. **After moving it to the top of the viewport, the mutation still survived** — because the
   *window* was then scrolled ~1600px, and the document-edge rule adds `window.scrollY`, so every
   glyph tested as reachable on the window's offset alone. Measured: `top=-798`, but
   `-798 + 1602 > 0`.

The pane's own contribution is only isolated when the window contributes **nothing**. AT-392 now has
its own short fixture, `scrolled_panes.html`, and the test asserts `window.scrollY == 0` before it
measures — otherwise the fixture could silently drift tall again and take the test's meaning with it.

### AT-393 — the disclosure was wrong and I have corrected it

I called the nested-clip false positive "pre-existing". The checker measured that it is **introduced
here**: pre-fix `NESTBELOW` False, post-fix True, because before this change a scrollable pane's own
box bounded its content. The structure is pre-existing; the consequence is not. Corrected below.

### AT-398 — this cycle filed an issue against its own work

Restoring the AT-358 spec after the rename, the closed-`<details>` mutation **survived**. The cause
is not the rename: with the guard bypassed the detector returns `ETAILSBODY_SENTINEL_77` — exactly
one character short — so the `not in` assertion passed. The `D` at index 0 has a real rect
(`w=11.5625, x=8, y=182`), `reachOf` returns `clip=null`, and it still never enters `items`.

**Silently dropping a glyph is this module's core failure mode**, so I filed it as **AT-398** rather
than absorbing it. The fixture sentinel moved off index 0 (`<p>body: DETAILSBODY_SENTINEL_77</p>`),
which restored 21/21 — and that workaround is named here as a workaround, not presented as a fix.

## Why this one, ahead of the queue's top rows

`qa/QUEUE.md`'s top-3 are AT-357 (closed this session), AT-368 and AT-335. **AT-368 and AT-335 are
both in flight with the other maker loop** — `qa/manifests/at368-loop-liveness-visible.md` exists,
and `scripts/flake_probe.py` is AT-335's reproduction harness being built right now. Taking either
would be a double-assignment on a shared working tree.

AT-379 is the right unit instead, and not merely because it is free: **it is a hole my own unit left,
and it must close before `visual_text` acquires its first caller.** The AT-358 cycle-3 checker found
it, declined to fail cycle 3 on it (the cycle-2 checker's scope bound was already written down), and
filed it against the follow-up crawl-wiring unit. Wiring the detector into a crawl while this is
open would ship a known false negative into the exact caller that triggers it.

## The defect

A credential rendered below the fold of an `overflow:auto` pane returned a **clean string**. That is
the AT-355 shape — the thing this entire module exists to catch — and it is the **second time in
this module that a fix for false positives manufactured a false negative**. AT-373 was the first
(text above the scroll fold). The pattern is worth naming: every one of these came from tightening
"what a reader can see" without asking what a reader can *reach*.

The module's own rule is reachability, stated in its own comment — *"further down or right can be
scrolled to, so those stay"* — and a reader can scroll an `overflow:auto` pane and read every line
of it. `clipRect` did not distinguish a pane from a clip. The comment I wrote in cycle 3 asserted
the opposite and was simply false:

> the clip intersection stays viewport-relative and is correct that way: a clipping ancestor and its
> content scroll together

They scroll together when the **window** scrolls. When the **pane** scrolls, they do not — that is
what scrolling a pane means.

## What changed

- `src/autotester/browser/visual_order.js` — `clipRect` is replaced by **`reachOf`**, which returns
  `{clip, scrollX, scrollY}`: it no longer reports a genuinely scrollable ancestor as a clip
  (AT-379), and it accumulates the scroll offset of the window **and** every scrollable ancestor
  (AT-392). The false comment in `isReachable` is replaced by the three-occurrence table. 297 lines.
- `tests/fixtures/bidi_site/unreadable.html` — a scrollable pane and an `overflow:hidden` pane, same
  shape, different overflow, one sentinel per line. The `<details>` sentinel moved off index 0 —
  a disclosed workaround for **AT-398**, not a fix for it.
- `tests/fixtures/bidi_site/scrolled_panes.html` — **new**; AT-392's own short page, deliberately
  too short for the window to scroll (see above for why that is load-bearing).
- `tests/test_browser_unreadable.py` — **new file**; the false-positive half split out under
  doctor's 300-line cap (see below). Carries both new tests.
- `tests/conftest.py` — the `page_factory` fixture moved here, so the two halves share one copy.
  The dead `SITE` constant it duplicated is deleted from the old file (**AT-394**).
- `qa/evidence/at379-scrollable-pane-reachability/mutations.json` — **5** mutations.
- `qa/evidence/at358-visual-order-detector/mutations.json` — 4 anchors repointed after the
  `clipRect` → `reachOf` rename. Re-run below: **21/21 still kill**, same named tests.

### Scrollable vs clipping is measured, not guessed

A pane scrolls only if its computed overflow is `auto`/`scroll` **and** its content actually
overflows (`scrollHeight > clientHeight`). `overflow:hidden` with nothing to scroll still clips, and
**the boundary is asserted in the same test as the fix** — a change that simply reported everything
would satisfy the positive assertions on its own, so the hidden pane's below-fold line must still be
absent.

Per axis, deliberately: `overflow-y:auto; overflow-x:hidden` is an ordinary pane, and it really does
hide what runs off its right edge while really exposing what runs off its bottom. The scrollable
axis is unbounded in the returned box; the other keeps the element's real edge.

### The file split, and why the fixture moved

The new test pushed `tests/test_browser_visual_order.py` to 321 lines. The seam is the one the
module already has: that file asks whether the detector **sees what the DOM hides** (bidi overrides,
zero-width interleaving, control values, reading order); `tests/test_browser_unreadable.py` asks the
opposite question, which is a different kind of claim — a box can be painted and show nothing, and
reporting it costs the false-positive rate in this product's north star.

Both halves need a real Chromium page over the same fixture directory, so `page_factory` moved to
`tests/conftest.py` rather than being copied. A copy in each file would be the "one concept, two
places" the design rules call a bug — and the cycle-1 checker of the previous unit checked exactly
that property with an AST overlap comparison.

## Capability coverage (each new claim → its isolating falsification)

All three rows are single-hunk edits to `src/autotester/browser/visual_order.js`, named in "What
changed". `observed` is the pasted runner output below; the runner refuses to start against a red
baseline, so each named test is green before its edit, and it prints `claims to kill` against
`actually failed` so the kill is attributed rather than merely a non-zero exit.

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| text below the fold of a scrollable pane is reported (AT-379) | `test_text_below_the_fold_of_a_scrollable_pane_is_reported` | `const scrollsY = false` | KILLED (row 1) |
| an `overflow:hidden` pane still clips — the boundary holds | same, **and** `…is_not_reported[overflow-clipped]` | widen `SCROLLS` to include `hidden` | KILLED (row 2) |
| the scrollable axis is genuinely unbounded, not merely detected | `test_text_below_the_fold_of_a_scrollable_pane_is_reported` | `bottom: box.bottom` | KILLED (row 3) |
| a vertically scrolled pane loses nothing before its offset (AT-392) | `test_a_pane_the_reader_already_scrolled_loses_nothing` | drop `scrollY += node.scrollTop` | KILLED (row 4) |
| a horizontally scrolled pane loses nothing before its offset (AT-392) | same | drop `scrollX += node.scrollLeft` | KILLED (row 5) |

Row 2 is the one that matters most: it falsifies the fix **from the other side**, by making the
detector too permissive rather than too strict, and it kills on both the new test and the existing
clipped-text test.

## How to verify (commands + expected)

- `uv run pytest` → expected: `1232 passed, 2 skipped`
  *(`uv run pytest -q` resolves to `-qq` — `pyproject.toml` `addopts` already carries `-q` — and
  suppresses the summary line. Exit 0 is the signal.)*
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_browser_visual_order.py tests/test_browser_unreadable.py` → expected:
  23 passed (real Chromium; skips cleanly if the browser binary is absent)
- `uv run python scripts/mutation_check.py qa/evidence/at379-scrollable-pane-reachability/mutations.json`
  → expected: `5/5 mutations killed` (C7)
- **Regression on the unit this one amends:**
  `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json`
  → expected: `21/21 mutations killed`. The split moved test nodeids, so both specs were repointed;
  this run is what proves none of AT-358's twenty-one kills was lost in the move.

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest
1232 passed, 2 skipped, 1 warning in 200.98s (0:03:20)

$ uv run pytest tests/test_browser_visual_order.py tests/test_browser_unreadable.py -o addopts= -q
.......................                                                  [100%]
23 passed in 2.26s

$ uv run python scripts/mutation_check.py qa/evidence/at379-scrollable-pane-reachability/mutations.json
KILLED  AT-379 reopens: a scrollable pane is treated as a hard clip again  (pytest exit 1)
KILLED  AT-379: the overflow:hidden boundary collapses - hidden panes count as scrollable  (pytest exit 1)
KILLED  AT-379: the scrollable axis is not unbounded, so the pane still clips downward  (pytest exit 1)
KILLED  AT-392: a vertically scrolled pane's earlier lines are dropped again  (pytest exit 1)
KILLED  AT-392: a horizontally scrolled pane's earlier columns are dropped again  (pytest exit 1)
5/5 mutations killed

$ uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json
21/21 mutations killed
```

Per-mutation attribution is in each evidence directory's `mutations.out`.

The `1232` total includes tests belonging to the **other maker loop** (AT-368 liveness and AT-335's
flake probe, in flight in this shared tree). This unit adds **one** test; the rest is not mine and
is not claimed.

## Live browser evidence

The unit's own tests **are** the live browser evidence: a real Chromium against a real HTTP server,
asserting measured glyph positions, which is the only way this claim can be checked at all. The
cycle-3 checker of AT-358 independently reproduced the defect in its own browser before filing it —
`qa/evidence/browser-at358-visual-order-detector-2026-09-16-checker-c3/report.json`.

## What remains open, deliberately

The module's `WHAT THIS DOES NOT SEE` block is unchanged and still accurate: shadow roots,
same-origin frames, the generated-content class, `<select>` option text, `<canvas>`, `title`/`alt`.
This unit closes a false negative inside the territory the detector already claims; it does not
widen that territory.

`reachOf` returns at the **first** clipping ancestor rather than intersecting every clip up the
chain, so a pane nested inside a second clipping box can report text the outer box hides.

**This false positive is INTRODUCED by this unit, not pre-existing** (AT-393). Cycle 1 of this
manifest called it pre-existing and the checker measured otherwise: before the change, a scrollable
pane's own box bounded its content, so the outer clip never had to be consulted. The structure is
old; the consequence is new. The direction is the deliberate one — a false positive costs the north
star's false-positive term, a false negative costs a missed credential — but calling a new cost an
old one is the kind of disclosure error this unit has now been charged for twice.

## Status: ready-for-check
