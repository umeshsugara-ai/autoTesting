# Manifest — at379-scrollable-pane-reachability

**Unit:** AT-379 — `visual_text` silently drops text below the fold of a scrollable pane
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-379 (medium, open → fixed)

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

- `src/autotester/browser/visual_order.js` — `clipRect` no longer reports a genuinely scrollable
  ancestor as a clip, and the false comment in `isReachable` is replaced by one that says what is
  actually true. 272 lines.
- `tests/fixtures/bidi_site/unreadable.html` — a scrollable pane and an `overflow:hidden` pane, same
  shape, different overflow, one sentinel per line.
- `tests/test_browser_unreadable.py` — **new file**; the false-positive half split out under
  doctor's 300-line cap (see below). Carries the new test.
- `tests/conftest.py` — the `page_factory` fixture moved here, so the two halves share one copy.
- `qa/evidence/at379-scrollable-pane-reachability/mutations.json` — 3 mutations.

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

Row 2 is the one that matters most: it falsifies the fix **from the other side**, by making the
detector too permissive rather than too strict, and it kills on both the new test and the existing
clipped-text test.

## How to verify (commands + expected)

- `uv run pytest` → expected: `1226 passed, 2 skipped`
  *(`uv run pytest -q` resolves to `-qq` — `pyproject.toml` `addopts` already carries `-q` — and
  suppresses the summary line. Exit 0 is the signal.)*
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_browser_visual_order.py tests/test_browser_unreadable.py` → expected:
  22 passed (real Chromium; skips cleanly if the browser binary is absent)
- `uv run python scripts/mutation_check.py qa/evidence/at379-scrollable-pane-reachability/mutations.json`
  → expected: `3/3 mutations killed` (C7)
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
1226 passed, 2 skipped, 1 warning in 198.60s (0:03:18)

$ uv run pytest tests/test_browser_visual_order.py tests/test_browser_unreadable.py -o addopts= -q
......................                                                   [100%]
22 passed in 2.05s

$ uv run python scripts/mutation_check.py qa/evidence/at379-scrollable-pane-reachability/mutations.json
KILLED  AT-379 reopens: a scrollable pane is treated as a hard clip again  (pytest exit 1)
KILLED  AT-379: the overflow:hidden boundary collapses - hidden panes count as scrollable  (pytest exit 1)
KILLED  AT-379: the scrollable axis is not unbounded, so the pane still clips downward  (pytest exit 1)
3/3 mutations killed

$ uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json
21/21 mutations killed
```

Per-mutation attribution is in each evidence directory's `mutations.out`.

The `1226` total includes tests belonging to the **other maker loop** (AT-368 liveness and AT-335's
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

`clipRect` still returns at the **first** clipping ancestor rather than intersecting every clip up
the chain. A pane nested inside a second clipping box can therefore report text the outer box hides.
That is pre-existing, is not touched here, and is stated rather than left to be found — it is a false
positive, the cheaper direction of the two.

## Status: ready-for-check
