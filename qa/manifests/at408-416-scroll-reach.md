# Manifest — at408-416-scroll-reach

**Unit:** AT-408, AT-416 — `reachOf`/`isReachable` (now `src/autotester/browser/visual_order_reach.js`)
**Contract:** `qa/contracts/ui.md` U14(a) scroll-invariance floor, U14(b) north-star tie-break ·
`qa/contracts/core-invariants.md` C2 (300-line cap), C7 (falsification)
**Related:** `qa/gates/at416-clip-vs-reach-direction.md` (opened 2026-09-16, **`Answered: (pending)`**
at the time of this build — see "The open gate" below) · `qa/manifests/at379-scrollable-pane-reachability.md`
(STALLED status, the manifest this unit closes out) · `qa/issues.jsonl` AT-408, AT-416 (both high, open)
**Goal task:** none — issue-driven
**Date:** 2026-09-25
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-408 (high) · AT-416 (high)
**Branch/worktree:** `wave/at408-416-scroll-reach`, `D:/autoTesting/.worktrees/at408-416-scroll-reach`
**Commit:** `553e8fa` — code + tests (no manifest yet in that commit)

## The open gate — read this first

`qa/gates/at416-clip-vs-reach-direction.md` is a HUMAN_GATE Umesh has not answered
(`Answered: (pending)`). It recommends **option A** (stop the clip contributing at a scrollable
ancestor; re-accept AT-393's narrow false positive) *unless Umesh wants option B built as its own
unit* — and this dispatch's own instructions specified **option B verbatim** (test the innermost
scroller's own box against outer clips, not the glyph's rect), as a new, separate unit
(`at408-416-scroll-reach`), which is exactly the gate's stated exception. I have built what I was
assigned. I am not able to confirm from inside this build whether Umesh answered the gate
out-of-band or whether the orchestrator proceeded on the exception clause without a formal
`Answered:` line being written. **Flagging this explicitly rather than silently assuming either.**
The checker/orchestrator should reconcile the gate's `Answered:` line with the fact that option B now
exists as a built, tested unit before this ships further (into a wired-in crawl, in particular).

## What changed

- **`src/autotester/browser/visual_order_reach.js`** (new, 158 lines) — `reachOf`/`isReachable`,
  moved out of `visual_order.js` (which sat at the 300-line cap, C2) so the fix had room. Not its own
  script: `observe.py` splices its text into `visual_order.js`'s IIFE at a marker comment, so
  `page.evaluate()` still receives exactly the one `(() => {...})();` shape it always has.

  **AT-408.** Already structurally fixed by the existing "walk all the way up" code (added in the
  at379 manifest's cycle 3, commit `fafe7e7`) — the loop never stops at the first scrollable
  ancestor, it accumulates `scrollX`/`scrollY` from every one. This build did not need to touch that
  part; it stays fixed and is exercised by the existing `test_a_scrolled_pane_inside_a_scrolled_pane_loses_nothing`
  (not duplicated here — see `tests/test_browser_scroll_reach_at408_416.py`'s docstring) and by a
  static unit check against the checker's own P1 (three-level nested scroll) geometry, below.

  **AT-416.** `reachOf` used to narrow ONE running `clip` from every ancestor's box on the way up,
  and `isReachable` tested the glyph's CURRENT (scroll-dependent) rect against it. That is correct
  for ancestors *between* the glyph and the first genuinely scrollable one — nothing there moves
  relative to the glyph when that scroller scrolls — but wrong for ancestors *outside* the scroller:
  the glyph moves inside the scroller's own box as it is scrolled, so testing the glyph's current
  position against an outer clip made the verdict flip with the scroller's own scroll offset —
  `reported=false` at rest, `reported=true` only once the pane happened to be scrolled to exactly the
  right spot. `qa/contracts/ui.md` U14(a) charges exactly this as a defect: the SET of glyphs
  `visual_text` reports must not depend on where anything scrollable currently sits.

  Fix: two running clips instead of one. `innerClip` narrows from the glyph up to and including the
  first (innermost) genuinely scrollable ancestor, and is tested against the glyph's rect (invariant,
  as before). `outerClip` narrows from there outward, and is tested against that scroller's own box
  (`scrollerBox`, captured once — the innermost only, "carry the innermost scroller's box forward" per
  the gate's option B) rather than the glyph — the scroller's own box does not move when its own
  content is scrolled, so this stays invariant too. A `clip-path` ancestor routes into whichever
  bucket is active exactly like an `overflow` ancestor (AT-427's warning against a partial fix that
  only touches the `overflow` branch).

- **`src/autotester/browser/observe.py`** — loads `visual_order_reach.js` and splices it into
  `visual_order.js`'s text at the `// AUTOTESTER:REACH_MODULE` marker before handing the combined
  string to `page.evaluate()`. Raises `RuntimeError` at import time if the marker is ever missing,
  rather than shipping a `reachOf is not defined` failure from inside the page.

- **`src/autotester/browser/visual_order.js`** — 300 → 228 lines. The `reachOf`/`isReachable` block
  (lines 106–187) is replaced by the splice marker and a short pointer comment; nothing else changed.

- **`tests/fixtures/bidi_site/at416_card.html`** (new) — reproduces the checker's own P6
  (`qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker-c3/p6-scroller-inside-hard-clip.json`,
  a ~42px band) and P7
  (`.../p7-card-wrapper.json`, a taller card) probes: an `overflow:hidden` card wrapping a genuinely
  overflowing `overflow:auto` body. Plus a negative control on the same page — a card wrapping a pane
  that does **not** overflow (AT-393's shape, not AT-416's), so the fix cannot be checked by simply
  reporting everything a card wraps.

- **`tests/test_browser_scroll_reach_at408_416.py`** (new) — two real-Chromium tests over that
  fixture: reported at rest, and reported (and scroll-invariant) after actually scrolling both bodies
  to their end. AT-408 is deliberately **not** duplicated here (see its docstring) — the existing
  `#outer`/`#inner` test in `tests/test_browser_unreadable.py` already is that exact shape.

- **`tests/test_browser_scroll_invariance.py`** — `_open_defects` no longer appends `"AT-416"`.
  18 of the 50 generated shapes were marked `xfail(strict=True, reason="AT-416")`; per the fix above
  they should now pass. **This edit is UNVERIFIED against a real browser** (see "The RAM gap" below)
  — see the in-file comment for the reasoning it rests on instead. `AT-417` is untouched.

## The RAM gap — no live-browser verification landed this cycle

Every browser-launching command in my instructions was gated on free RAM ≥ 3.5 GB, polled every
300s for up to 30 minutes. Six polls, none cleared the gate (other concurrent wave builders in this
shared session were holding memory throughout, per `qa/.last-tick`):

```
2026-09-25T16:18:18Z poll=1 free_ram_gb=1.47
2026-09-25T16:23:23Z poll=2 free_ram_gb=0.77
2026-09-25T16:28:29Z poll=3 free_ram_gb=0.62
2026-09-25T16:33:33Z poll=4 free_ram_gb=0.90
2026-09-25T16:38:35Z poll=5 free_ram_gb=0.81
2026-09-25T16:43:38Z poll=6 free_ram_gb=0.88
RAM_NEVER_FREED
```

Per my instructions ("If RAM never allows it, commit the tests anyway, mark those rows UNVERIFIED
with readings, and declare it as a gap") the new tests are committed but **never run against real
Chromium in this build**. Declared as a gap, not disclosed as a pass:

- `tests/test_browser_scroll_reach_at408_416.py` — both new tests, UNVERIFIED live.
- `tests/test_browser_unreadable.py::test_a_scrolled_pane_inside_a_scrolled_pane_loses_nothing`
  (AT-408 regression coverage) — UNVERIFIED live against the new code this cycle (it is a pre-existing,
  previously-green test; my code change is reasoned not to affect its shape, but "reasoned" is not "run").
- `tests/test_browser_scroll_invariance.py`'s 50-shape corpus, in particular whether the 18 AT-416-only
  shapes actually XPASS as predicted — UNVERIFIED.

### What stands in for it: a static unit harness against the checker's own geometry

Not a substitute for the real thing, but not nothing either: `visual_order_reach.js` is loaded
**verbatim** via Node's `eval()` (not reimplemented) and exercised against hand-built
`getBoundingClientRect`/`getComputedStyle` mocks constructed from the checker's own recorded numbers
in `qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker-c3/`:

```
$ node -e "... eval(fs.readFileSync('visual_order_reach.js')) ... P6 target (scrollable pane inside 42px hard clip) -> should be reachable"
PASS P6 target (scrollable pane inside 42px hard clip) -> should be reachable got= true expected= true
PASS P6 target AT REST (not yet scrolled) -> must STILL be reachable (invariance) got= true expected= true
PASS P1 three-level all-auto nested scroll, no hard clip -> reachable got= true expected= true
PASS P2 hidden-by-middle (real hard clip between glyph and outer scroller) -> excluded got= false expected= false
PASS P2 inner-top (inside the middle band) -> reported got= true expected= true
PASS non-overflowing auto box (not a real scroller) inside 40px hard clip, glyph below the 40px band -> excluded got= false expected= false
PASS same shape, glyph inside the 40px band -> reported got= true expected= true
```

Seven cases, covering: the exact P6 shape at rest AND after scroll (the crux of AT-416 — the SAME
verdict in both states); a three-level all-`auto` nest with no hard clip (AT-408, no regression); a
hard clip *between* the glyph and an outer scroller (must stay a real, glyph-tested boundary,
unaffected by the outer scroller's own scrolling — proves `innerClip` bucketing); and the
non-overflowing "NESTCLIP" shape from `tests/fixtures/bidi_site/scrolled_panes.html` that the
existing `test_a_pane_inside_a_clipping_box_does_not_leak_past_it` depends on (proves the fix does
not accidentally start treating a non-scrolling `auto` box as a genuine scroller).

**Known, disclosed shortfall of this fix, not covered by the harness above and not claimed:** the
gate's option B is deliberately coarse — once a glyph is inside a scroller whose own box overlaps an
outer clip at all, the fix reports the glyph reachable regardless of whether that SPECIFIC glyph's own
scroll range can actually align it with the overlap (a glyph near the very bottom of a very tall
scroller, with a small outer band near the scroller's top, may not really be reachable). This is the
`qa/contracts/ui.md` U14(b) north-star tie-break taken deliberately ("keeping the visible text wins" —
a false positive here costs a reviewer a look, a false negative costs a missed credential), not an
oversight; the checker's own P4a follow-up probe found exactly this edge case and separately concluded
its own initial expectation there was wrong, not the code.

## Verify

- `uv run ruff check src tests scripts` → `All checks passed!` (run against the final tree, below)
- `uv run autotester doctor` → `doctor: clean` (run against the final tree, below)
- `uv run pytest` minus every browser-touching test file (RAM gate — see above; this subset launches
  no browser and was safe to run at any RAM level) → **1591 passed, 5 skipped, 1 failed** in 463.32s
- The 1 failure, `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`,
  is unrelated to this unit (a real-subprocess-kill timing test, nowhere near `browser/`). Proven
  pre-existing/environmental, not a regression: it **passes in isolation** both on a clean detached
  `bb4be39` checkout (master, pre-this-unit) and in this worktree, run back to back:
  ```
  $ cd <throwaway bb4be39 copy> && uv run pytest tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild -o addopts=
  1 passed in 14.90s

  $ cd <this worktree> && uv run pytest tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild -o addopts=
  1 passed in 11.28s
  ```
  It only fails inside the full run, under the same system-wide RAM/CPU contention (six other
  concurrent wave builders, per `qa/.last-tick`) that kept the browser-test RAM gate from ever
  clearing — a timing flake in a process-kill test under load, not a code defect.
- `tests/test_browser_scroll_invariance.py --collect-only` → `50 tests collected`, no errors (proves
  the `_open_defects` edit is syntactically sound and does not change which shapes exist, only which
  are pre-marked `xfail`). **Not run for real** — see the RAM gap above.

## Actual outputs (from maker's own run, final tree)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest --ignore=tests/test_browser.py --ignore=tests/test_browser_scroll_invariance.py --ignore=tests/test_browser_scroll_reach_at408_416.py --ignore=tests/test_browser_unreadable.py --ignore=tests/test_browser_visual_order.py --ignore=tests/test_crawl_inventory_live.py --ignore=tests/test_explore_live.py --ignore=tests/test_explore_login_spa_live.py --ignore=tests/test_explore_modal.py --ignore=tests/test_explore_typing.py --ignore=tests/test_ui_crawl_login.py --ignore=tests/test_ui_runs_serial_entry_mix_live.py
1 failed, 1591 passed, 5 skipped, 15 warnings in 463.32s (0:07:43)
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild

$ uv run pytest tests/test_browser_scroll_invariance.py --collect-only -o addopts=
50 tests collected in 0.08s
```

## Live-browser evidence — what this unit does NOT have

This is browser-observation code (AT-358's `visual_text`, the instrument that catches credentials
rendering in plain type), not a UI route, and the honest statement is: **no live-browser run of the
new or existing behaviour happened in this build cycle.** Every claim of correctness above rests on
(a) the existing, previously-checker-verified "walk all the way up" AT-408 fix being untouched by this
diff, and (b) the static `eval()`-against-checker-geometry harness. Neither is a substitute for
`page.evaluate()` in a real Chromium against the new fixture and the 50-shape corpus, which is the
only way this module's own contract (U14a) has ever actually been checked, going back to AT-355's
original discovery. **This must be run for real before this unit can be considered verified,
independent of the open gate above.**

## What remains open, deliberately

- **The gate.** See "The open gate" at the top.
- **AT-417** (clip-path ancestor that also scrolls skips its own scroll accumulation) — untouched,
  stays open, pre-existing and uncharged against this unit.
- **AT-418** (clip-path ancestor clips to its border box, not its actual clip geometry) — untouched,
  stays open, pre-existing and uncharged against this unit.
- **The coarse-reachability trade-off** named above (U14b), inherent to option B, not new to this fix.
- **Live-browser verification of everything in this manifest** — the RAM gap.

## Status: ready-for-check
