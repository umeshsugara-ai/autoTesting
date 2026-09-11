# Manifest — at358-visual-order-detector

**Unit:** AT-358 — port the glyph-order detector into the repo
**Contract:** `qa/contracts/ui.md` (U13 names this as the non-enumerating instrument) ·
`qa/contracts/browser-and-secrets.md` · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-358 (medium, fixed)

## Why this exists

Every instrument in `browser/observe.py` read **document order** — `innerText`, element names, the
enumerated controls. A bidi override makes document order and reading order disagree, and AT-355
exploited exactly that: a credential stored backwards behind `U+202E` renders forwards, so every
DOM-order check called the page clean while a human could read the secret off it in plain type.

Three checker cycles missed it. A per-glyph measurement caught it — and that measurement lived in
a checker's scratch evidence directory, where the next unit could not use it. U13 says explicitly
that the spelling enumeration does **not** discharge this port: an enumeration is a deny-list, and
this is the instrument that does not enumerate.

## What changed

- `src/autotester/browser/visual_order.js` — **new**. One `Range` per character, its client rect
  taken, glyphs bucketed into rows by `y` and sorted by `x`. Returns what a reader sees.
- `src/autotester/browser/observe.py::visual_text(page)` — **new**. In `browser/` rather than in a
  test helper because reading other people's rendered pages is what this product does.
- `tests/fixtures/bidi_site/` — **new**: `plain` (positive control), `clean` (negative control),
  `hidden` (the AT-355 shape), `zerowidth` (the AT-345 shape), `invisible` (`visibility:hidden`).
- `tests/test_browser_visual_order.py` — **new**, 6 tests.

**Every "not visible" assertion is paired with a planted positive control**, because a detector
that always returned nothing would pass every clean-page assertion in the file. That is the
technique two checkers used on this repo, and it is the only reason to trust a negative.

## Two defects the tests found in the detector itself

1. **The zero-box filter was wrong.** I wrote `rect.width === 0 && rect.height === 0`, copied from
   `enumerate.js::isVisible` where it is right for an *element*. For a one-character `Range` it is
   wrong: a zero-width character still reports the full **line height**, so the condition never
   matched, every `U+200B` was kept, and the new instrument reproduced *exactly the blindness it
   exists to remove*. The zero-width test caught it. Now `rect.width === 0` alone.

2. **A filter I assumed was load-bearing was dead, and one I nearly deleted was not.** The
   surviving mutation said the `script`/`style` tag check killed nothing. Rather than invent a test
   to justify it, I measured against a real Chromium:

   ```
   display:none / <script> / <style>   -> zero-width rects; the width filter already drops them
   visibility:hidden                   -> REAL width; swept in without the style check
   ```

   So the tag deny-list was **deleted as dead code**, and the `visibility` check is kept with a
   test that pins it. The intuitive guard (a tag list) was the wrong one; the one that mattered was
   invisible until measured. Without that check the detector would have reported text nobody can
   see as text a reader saw — the same class of error as the DOM-order tools it replaces, pointed
   the other way.

## How to verify (commands + expected)

- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_browser_visual_order.py -q` → expected: 6 passed (real Chromium;
  skips cleanly if the browser binary is absent)
- `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json`
  → expected: `6/6 mutations killed` (C7)

## Actual outputs (from maker's own run)

```
$ uv run pytest
1170 passed, 2 skipped, 1 warning in 228.58s (0:03:48)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json
KILLED  glyphs are not sorted by screen position - document order returns
KILLED  the detector reads innerText instead of measuring glyphs
KILLED  unpainted characters are kept - the AT-345 blindness returns
KILLED  the width test regresses to the enumerate.js element form
KILLED  the detector returns nothing at all - every clean result is vacuous
KILLED  invisible-but-laid-out text is swept in as if a reader saw it
6/6 mutations killed
```

The earlier `2 failed` in `tests/test_mutation_check.py` (AT-357 — those tests assert on a global
`%TEMP%` glob and go red when the other maker loop runs a mutation check concurrently) did not
recur in this run. AT-357 stays open: not recurring is not the same as fixed.

## Live browser evidence

This unit's own tests **are** the live browser evidence — they drive a real Chromium against a
real HTTP server and assert measured glyph positions, which is the only way the central claim can
be checked at all. `qa/evidence/at358-visual-order-detector/mutations.out` carries the run.

What is **not** done here: wiring `visual_text` into the crawl so every screen is checked in
reading order. That is a behaviour change to the explorer with its own cost and its own failure
modes, and bundling it would put two concerns in one unit. The detector exists and is tested;
using it is the next unit.

## Status: ready-for-check
