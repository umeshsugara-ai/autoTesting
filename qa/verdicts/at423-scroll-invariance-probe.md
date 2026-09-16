# Verdict — at423-scroll-invariance-probe

**Cycle checked: 1**
**Date:** 2026-09-16
**Checker:** /checker Mode A (fresh subagent, bound to `D:/autoTesting`), with Mode D
**Contract:** `qa/contracts/core-invariants.md` (C2, C7) · `qa/contracts/ui.md` (U13: the manifest itself says it gives this module no criterion, so it is not applicable)

```
VERDICT: FAIL
SCOREBOARD: 1/2 criteria met (C2 met; C7 not met), U13 not applicable
FAILURES:
- [C7] sev: medium · the xfail REASONS are a prediction (`"AT-417" if "+clip" in label else "AT-416"`) presented as a measurement. Checker-measured with model fixes: AT-416's mechanism covers 20 red shapes and AT-417's covers 14 (2 overlap). The claimed split is 10/22. 8 hidden-outer `+clip` shapes are labelled AT-417, but their clip-path box is not a scroll container, and 2 shapes need both fixes · derive each reason from the shape (hidden outside auto → AT-416; clip-path on a scrolling box → AT-417; both → both). Correct the docstring and the manifest counts, including the "judge option A by the 10 AT-416 xfails" guidance (option A flips 18) · issue: AT-425
CAPABILITY-COVERAGE: 3/3 rows reproduced (copy green before each edit; each named nodeid failed on the invariance assertion). One disclosure is false: 8 of row 2's 18 failures are XPASS(strict), not the assertion (AT-426, low)
LIVE-BROWSER: qa/evidence/browser-at423-scroll-invariance-probe-2026-09-16-checker/report.json (0 console errors on all 56 pages)
ISSUES-WRITTEN: AT-425 (medium), AT-426 (low)
EXPLANATION: The instrument works. KNOWN_RED is a real measurement: with it emptied, exactly those 32 failed, all on the invariance assertion. The set was identical across 5 runs while the full suite ran concurrently. My own browser confirms each is a genuine reader-reachable false negative, not a driver artefact. What fails is the attribution the unit sells: its stated purpose is to turn the AT-416 gate into a measurement, and it labels 10 of its 32 reds with the wrong defect.
```

## What I re-ran myself (bound tree, read-only)

| command | result |
|---|---|
| `uv run pytest` | `1265 passed, 2 skipped, 32 xfailed, 1 warning in 209.33s` — matches manifest |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` (file is 255 lines ≤ 300) |
| `uv run pytest tests/test_browser_scroll_invariance.py` ×3 (while full suite ran concurrently) | `24 passed, 32 xfailed` each time |
| `git diff 7b1f9c3 -- src/autotester/browser/visual_order.js` | empty: byte-identical. Commit `ce90fe4` touches only the test, the manifest and 2 evidence files; no `src/` |
| `grep content-visibility tests/test_browser_scroll_invariance.py` | 0 hits: the AT-410 scope disclosure is true |

C2: met. C7 suite green, mutation duty discharged, baseline asserted by `scripts/mutation_check.py`: met on the mechanics. It is not met on the claim that the classification is a measurement (below).

## Point 1: is the xfail list a measurement? The SET is; the LABELS are not

**Set.** I ran the file in a throwaway copy (`scratchpad/copy`, `PYTHONPATH` pinned to the copy's `src`, and the copy ran green first: `24 passed, 32 xfailed`) with `KNOWN_RED` emptied. The full suite was running concurrently for load. Result: 5 runs, 32 failures each, and a diff against `KNOWN_RED` of **0 lines** every run. All 32 failures are `AssertionError: <label> changed after <state>`, with no errors, timeouts or collection failures. Determinism (point 3) holds under load.

**Classification.** I patched the copy's `visual_order.js` with a model AT-417 fix (a clip-path ancestor that scrolls accumulates its offset instead of clipping), a model AT-416 option-A fix (no clip contribution on an axis outside a scrollable ancestor), and both:

| variant | still red |
|---|---|
| AT-417 fix only | 20: all 10 "AT-416" shapes **plus** `hidden-auto+clip`, `hidden-auto-auto+clip`, `hidden-auto-hidden+clip`, `hidden-hidden-auto+clip` (each ±tall) and `auto-hidden-auto+clip`(±tall) |
| AT-416 fix only | 14: the 12 outer-`auto` `+clip` shapes plus `auto-hidden-auto+clip`(±tall) |
| both | 0 |

The copy was restored and `cmp`-checked afterwards. The geometry confirms the mechanism. In `hidden-auto+clip`, L0 carries the clip-path, is `overflow:hidden` and is not reader-scrollable, so AT-417's own definition ("clip-path AND its own scroll container") cannot apply. Mutation row 2 corroborates this independently: it turns `hidden-auto+clip` and `hidden-hidden-auto+clip` into XPASS(strict) together with the AT-416-labelled shapes. The xfail list does not hide a defect (strict xfails still flip loudly). But it mis-explains 10 of 32, and the manifest tells the AT-416 gate to judge a fix by a count that is wrong. That is the failure.

## Point 1, Mode D: per-class spot checks in my own Chromium

My own script, own HTTP server, pages generated from the test's `_html()`. For `hidden-auto` (AT-416), `auto+clip` (AT-417) and `hidden-auto+clip` (the mislabelled one), with an `auto` control:

- **At rest,** `visual_text` omits `INNER_BOTTOM` in all three red shapes. The `auto` control reports it.
- **Pane scrolled to 334,** so `INNER_BOTTOM` sits inside the pane: `elementFromPoint` hits `INNER_BOTTOM` and the screenshot shows it. The detector now reports it, and drops `INNER_TOP`. A reader can reach both, so this is a real false negative, not a driver artefact.
- **Axes decoupled:** vertical-only reproduces the drop (`missing = EINNOPRT_`). Horizontal-only changes nothing.
- **Console errors:** 0 on every page (56 corpus pages plus the spot pages).

## Point 2: does the driver measure itself?

- `_SCROLLERS` filters on computed `overflowX/Y ∈ {auto, scroll}` and real overflow. For example, in `hidden-auto` it returns only `L1`, and L0 (`hidden`, sh 340 > ch 40) is excluded. The overflow:hidden fix is real.
- **Axis coupling:** every box has `scrollWidth == clientWidth` (300/300; overlay scrollbars in headless), so `scrollLeft = scrollWidth` is a no-op. It cannot hide or invent a failure here. It also means the X axis is never exercised, which is undisclosed (AT-426).
- **Reset to 0:** the pages have no initial scroll, anchors or script, so 0/0 plus window 0 is the load state for every shape.
- The driver scrolls one container at a time, never outer and inner together. This is not an artefact, but a coverage question for the maker: AT-408-style accumulation is only pinned by mutation, not by a combined-offset state.

## Point 4: vacuity

- The positive control is asserted on every page: `assert "CONTROL_QUARTERLY_REPORT" in visual_text(page)` before the loop, and the multiset equality afterwards implies it survives each state. Confirmed present.
- **Of the 24 passing shapes,** 12 have no reader-scrollable container. Six of those are short pages where `document.scrollHeight <= innerHeight`, so they perform **no scroll at all**: `hidden`, `hidden-hidden`, `hidden-hidden-hidden`, each ±clip. No mutation row kills any of them. The other six (`+tall`) exercise only the window, and row 3 does kill those. This is undisclosed and filed as AT-426 (low).

## Point 5 / Capability coverage (step 4b)

The `visual_order.js` rows are admissible under the at357 cycle-2 ruling in the core-invariants amendment log: a test-only unit, single-hunk edits, one file, named explicitly. No cell contains a command or a conftest/CI edit.

I re-ran `scripts/mutation_check.py qa/evidence/at423-scroll-invariance-probe/mutations.json --repo <copy>` in the throwaway copy. The copy was green first: `24 passed, 32 xfailed` for this file. The harness asserts its own baseline.

| row | named nodeid(s) in failure list | result |
|---|---|---|
| AT-392 class | `[auto]`, `[auto-auto]` present | KILLED, 12 failures |
| AT-408 class | `[auto-auto-auto]` present | KILLED, 18 failures |
| AT-373 class | `[auto]`, `[auto-auto]` present | KILLED, 18 failures |

Every named nodeid failed on the invariance assertion. The manifest also says "None of the extra failures is ... They are all the invariance assertion." That is **false for row 2**: applying it directly gives `[XPASS(strict)]` ×8 among the 18 (`hidden-auto`, `hidden-hidden-auto`, each ±clip ±tall). The rows still stand, and the misstatement is filed as AT-426.

## Point 6: scope honesty

Confirmed: there is no `content-visibility` in the corpus, `visual_order.js` is byte-identical to `7b1f9c3`, and no `src/` file is in `ce90fe4`.

## Observations (questions, not failures)

- The unit was already committed (`ce90fe4`) before any checker verdict. That runs against "the maker commits only after PASS". Was this deliberate for a test-only unit?
- AT-423 stays **open** (not fixed): this is a FAIL.

## Ledger

- AT-425 (medium, open): xfail reasons predicted, not measured; 10/32 mislabelled.
- AT-426 (low, open): two false manifest claims (row 2 extras include XPASS(strict); 6 passing shapes scroll nothing), plus the X axis is never exercised.
