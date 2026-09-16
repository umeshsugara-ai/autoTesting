# Verdict — at438-display-contents

**Checker:** /checker Mode A + Mode D (fresh subagent, bound to `D:/autoTesting`)
**Date:** 2026-09-16
**Manifest:** `qa/manifests/at438-display-contents.md` (Status: ready-for-check, Fix cycle: 1)
**Cycle checked: 1**
**Code under check:** commit `c687b73` (the maker committed the unit before this verdict; the tree's `visual_order.js` equals that commit)

```
VERDICT: FAIL
SCOREBOARD: 0/1 criteria met (U13 detector port), 2/2 invariants hold (C2, C7)
FAILURES:
- [U13] sev: high · the probe <span> restarts author CSS animations keyed on :last-child / :has(), so VISIBLE text outside the display:contents element is dropped and the real page visibly changes; the old detector (c687b73^) saw that text · answer "is this contents element rendered?" without inserting a node an author selector can match, and pin an animated :last-child / :has() neighbour in the fixture · issue: AT-442
CAPABILITY-COVERAGE: 3/3 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at438-display-contents-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-442, AT-443, AT-444, AT-445
EXPLANATION: The base fix works and the rejected walk-up candidate really leaks closed <details> and cv:hidden text, but "observing the page leaves it unchanged" is false. The probe adds a child to author DOM, and a forced style recalc turns that into a restarted animation. That drops visible text the previous detector reported, the false-negative-for-false-negative trade this module keeps making. innerHTML is byte-identical throughout, so the unit's own DOM assertion cannot see it.
```

## What I re-ran myself (bound tree, read-only)

| command | result |
|---|---|
| `uv run pytest` (bare) | `1312 passed, 2 skipped, 32 xfailed, 1 warning in 306.90s`. 0 failed. 32 xfailed matches the manifest. The count is higher than the manifest's 1296 because the other loop added tests to the shared tree |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `wc -l` | `visual_order.js` **300** (at the cap), `tests/test_browser_visual_order.py` 282 |
| `scripts/mutation_check.py` for at438 / at429 / at358 / at410 / at379 / at423 | `3/3`, `4/4`, `21/21`, `1/1`, `7/7`, `3/3`. No SURVIVED, no anchor-count refusal |

## Capability coverage (step 4b): reproduced in a throwaway copy

Copy: `src tests scripts pyproject.toml` tarred to the scratchpad, outside the bound root. **Proof that the copy tests its own code:** inside pytest in the copy, `autotester.browser.observe.__file__` resolves to `...scratchpad\copy\src\autotester\browser\observe.py`, not to `D:\autoTesting\src`. The runs also set `PYTHONPATH=<copy>/src`. Each edit was applied from the manifest's `mutations.json` (anchor count == 1, file changed).

| row | before (copy, unedited) | after edit | assertion that fired |
|---|---|---|---|
| 1 drop `&& !contentsRenders(el)` | `2 passed` (T1 + `[contents]`) | `2 failed` | `assert 'CONTENTS_PLAIN_S1' in ...` and `contents paints but was dropped` (the named reporting assertions) |
| 2 walk-up candidate | `2 passed` | `1 failed` | `assert 'CONTENTS_CLOSEDDETAILS_S3' not in ...`. The seen string also contained `CONTENTS_CVHIDDEN_S4` |
| 3 probe never removed | `2 passed` | `1 failed` | `assert page.evaluate("() => document.body.innerHTML") == before` |

Every cell is a single-hunk edit to `src/autotester/browser/visual_order.js`, a file listed under "What changed". I found no inadmissible cell.

## Judged points

**1. False positives from the fix. None found** (`report.json` → `hiding_and_visible_contexts`). The ground truth is a full-page screenshot hash taken before and after replacing the sentinel text node with glyphs of the same length in a monospace font. This avoids the `color:transparent` method. Each page has a positive control (seen on every page) and 0 console errors. Every case below was correctly dropped:
- closed `<details>`, and closed `<details>` with `contents` nested twice
- a `content-visibility:hidden` block
- `display:none` and the `hidden` attribute
- `hidden="until-found"`
- a `visibility:hidden` ancestor, and a `contents` element that is itself `visibility:hidden`
- an `opacity:0` ancestor
- zero-alpha colour on an ancestor and on the `contents` element itself
- an `overflow:hidden` clip
- an off-screen absolute container
- `text-indent:-9999px`
- a closed `<dialog>`
- an unslotted light child of a shadow host

These were correctly reported: plain, open details, a slotted child, inside `<ul>`, and inside `<tr>`.

Two rows that looked wrong were not caused by this unit:
- **`clip-path`:** the old detector gives the same result with a plain div. This is AT-418, which already exists.
- **`cv:auto` far below the fold:** the screenshot method cannot see it. The text is reachable by scrolling, so reporting it is the intended behaviour.

**2. Writes to author DOM**
- **`innerHTML`:** unchanged in all 28 layouts. **Confirmed.**
- **MutationObserver:** on `document.body` with subtree, childList, attributes and characterData, it records exactly `childList #c added [SPAN]` followed by `childList #c removed [SPAN]`, and nothing else. **The disclosure is accurate.**
- **`:last-child` / `:has()` recalc: FAILS (AT-442).** The recalc forced while the probe is present does not change a sibling's *measured rect*, because the probe is gone before any glyph is measured. But it cancels an animation that depends on the selector, and removing the probe starts a **new** one at `currentTime 0`. Measured against the parent commit on identical pages:
  - `:last-child` animation: old `POSCTRL_OKSIBLING_ANIM` (animation 2950→3000); new `POSCTRL_OKSENTZQ_KEY` (3017→**0**). The after-screenshot shows `SIBLING_ANIM` gone from the actual page.
  - `:has()` animation on a `<p>` **outside** the contents element: old sees `HAS_TARGET`, new drops it (2983→0).
  - Control page with the same CSS but no `display:contents`: no restart, and both detectors see the text.
  - A 20 s `opacity` transition on `:not(:last-child)` did **not** fire (`getAnimations()` empty, opacity 1, text seen).
- **Parents `<table>/<tr>`, `<ul>`, `<select>`:** no structural failure. In `<tr>` and `<ul>` the text paints and is reported. In `<select>` it does not paint and is not reported. All agree with the screenshot.
- **`appendChild` throws (AT-445, low):** there is no DOM-level restriction that makes `appendChild` throw on an element parent. A page override does: `c.appendChild = () => {throw}` makes the whole `visual_text` evaluate throw, and the positive control is lost with it. A no-op `Element.prototype.remove` leaves `<span></span>` in `#c`. The `try` starts after `appendChild`.
- **Also found (AT-443, medium):** author CSS that matches the probe hides it, while the real text stays visible (screenshot). Three rules do this: `span:empty{display:none}`, `*:empty{display:none}` and `#c>span{display:none}`. The result is the AT-438 false negative again.
- **Also found (AT-444, low):** a `contents` element with `opacity:0` still paints its text, but old and new code both drop it through `effectiveOpacity`. This is pre-existing.

**3. The rejected candidate.** Row 2 reproduced in the copy. With the walk-up version, the seen string contains **both** `CONTENTS_CLOSEDDETAILS_S3` and `CONTENTS_CVHIDDEN_S4`. My Mode D run confirms by screenshot that neither of those paints. The choice of the probe over the walk-up rests on measurement.

**4. Line cap.** 300 lines by `wc -l` (was 298 at `c687b73^`). The `reachOf` function, and the whole block from its leading comment to `function isReachable`, is **byte-identical** to `c687b73^` (`diff` empty). What the shortened comments keep:
- **AT-374:** keeps "SVG text IS reported, by accident", "nothing pins it, so it is not claimed", and "listing it as unseen was false". It drops the rationale that a false entry in a limits block is worse than none. That rationale is not a defect guard.
- **checkVisibility note:** keeps "DEFAULT options on purpose", "opacity/visibility flags would subsume the rules below", and "a rule another rule covers cannot be falsified (C7)". It drops the literal option names `{opacityProperty, visibilityProperty}`, which is a small loss of searchability but no loss of fact.

**5. Repointed neighbour specs.** `git show c687b73` shows exactly one changed line in each spec, the `old` anchor (`...&& !contentsRenders(el)) return false;`). Names, `kills` and bodies (`if (false) return false;`) are unchanged. The unit removes no identifier; it only adds `contentsRenders`. So no body can reference a missing name. Both specs re-ran clean (at429 `4/4`, at358 `21/21`), and neither raised an anchor-count error.

## Contract judgement

- **U13 (the positive rendering detector, AT-358 port): NOT MET.** The unit fixes AT-438's layouts. It also makes the detector drop text that the previous commit reported, and it changes the rendered state of the page it observes (AT-442). For a detector whose ranked-worse error is a missed credential, that is a regression in the direction this unit set out to fix.
- **C2: holds.** Doctor is clean, the JS is counted by hand at 300, and the test file has 282 lines.
- **C7: holds.** The mutation harness asserted anchor count and file change. I reproduced all three rows independently in a proven copy, and the named assertions fired.

**Issues addressed:** AT-438 **stays open**. The base case is fixed but the unit does not PASS.

**Open question (not a failure):** the unit's code was committed as `c687b73` before any checker verdict existed. The project's own flow commits after a PASS. The next sweep should decide whether that counts as a bypass.


---

# Cycle checked: 2

**Checker:** /checker Mode A + Mode D (fresh subagent, bound to `D:/autoTesting`)
**Date:** 2026-09-16
**Manifest:** `qa/manifests/at438-display-contents.md` (Status: ready-for-check, Fix cycle: 2)
**Code under check:** commit `ba30b71`. The maker committed it before a verdict again. `git diff HEAD` is empty for `visual_order.js`, the test and the fixture.
**Criteria applied:** U14 of `qa/contracts/ui.md`, plus C2 and C7. U14 was added in `b90a695` at 18:15:50, before this cycle was submitted in `ba30b71` at 18:18:27, so its scope-in-time clause charges it. The dispatch named U13. U14 is the detector's own acceptance line and replaces the per-verdict U13 charge that cycle 1 used.

```
VERDICT: FAIL
SCOREBOARD: 0/1 criteria met (U14: (a) holds, (b) fails, (c) respected), 2/2 invariants hold (C2, C7)
FAILURES:
- [U14(b)] sev: medium · the walk decides a closed <details> by tag (DETAILS && !open) instead of by what actually hides the body, so an author details::details-content{content-visibility:visible} (a responsive accordion expanded on desktop) paints display:contents text that visual_text drops; the cycle-1 probe reported it · read getComputedStyle(box, '::details-content').contentVisibility (measured: matches the screenshot for closed, open, the author override and details{display:contents}) and walk the flat tree via assignedSlot, with fixture rows for both · issue: AT-449
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at438-display-contents-2026-09-16-checker-c2/report.json
ISSUES-WRITTEN: AT-449, AT-450, AT-451
EXPLANATION: The write-free claim is true. Across 67 pages there were zero MutationObserver records and no animation clock went backwards, and all three sabotage overrides are harmless. AT-442, AT-443 and AT-445 no longer reproduce. But the walk has swapped one enumeration for another. Its claim that the nearest box covers everything above it holds only for the light tree and an unmodified <details>. Against the cycle-1 probe it loses one visible-text case (AT-449, charged) and gains four false positives (AT-450, filed low under the U14(b) tie-break).
```

## What I re-ran myself (bound tree, read-only)

| command | result |
|---|---|
| `uv run pytest` (bare) | `1316 passed, 2 skipped, 32 xfailed, 1 warning in 297.94s`. Matches the manifest |
| `uv run pytest` (bare, second run, loaded by 8 concurrent single-test runs) | `1316 passed, 2 skipped, 32 xfailed, 1 warning in 451.37s` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `wc -l` | `visual_order.js` **298**. `tests/test_browser_visual_order.py` **294**, not the manifest's 289, and still under the cap |
| `scripts/mutation_check.py`: at438 / at429 / at358 / at410 / at379 / at423 | `5/5`, `4/4`, `21/21`, `1/1`, `7/7`, `3/3`. The harness mutates a copy outside the repo (`mutation_check.py:135`) |
| U14 verify: `pytest tests/test_browser_scroll_invariance.py tests/test_browser_visual_order.py` | `50 passed, 32 xfailed`. Every xfail is `strict=True` (`test_browser_scroll_invariance.py:209`), and each reason is AT-416 (18), AT-417 (12) or AT-416 + AT-417 (2). All three are classes listed in U14(c) |

## Capability coverage (step 4b): reproduced in a throwaway copy

**The copy:** `src`, `tests`, `scripts`, `pyproject.toml` and `qa/evidence/at438-display-contents`, tarred into the scratchpad outside the bound root.

**Proof that the copy tests its own code:** a `-p pathproof` plugin prints `autotester.browser.observe.__file__` inside each pytest session. Every before run and every after run printed `...scratchpad\c2\copy\src\autotester\browser\observe.py`. `observe.py:17` loads `visual_order.js` from its own directory.

On every row the anchor count was 1 and the file changed. The scripts and raw output are `rows.py` and `rows.json` in the evidence directory.

| row | before (copy) | after | assertion that fired |
|---|---|---|---|
| 1 drop `&& !contentsRenders(el)` | 2 passed | 2 failed | `assert 'CONTENTS_PLAIN_S1' in ...` and `contents paints but was dropped` |
| 2 remove the DETAILS check | 1 passed | 1 failed | `assert 'CONTENTS_CLOSEDDETAILS_S3' not in ...` |
| 3 remove the content-visibility check | 1 passed | 1 failed | `assert 'CONTENTS_CVHIDDEN_S4' not in ...` |
| 4 cycle-1 probe `<span>` | 1 passed | 1 failed | `assert 'CONTENTS_PLAIN_S1' in 'Quarterly report for the trainers listopenclosed'` |
| 5 non-empty probe `<i>` | 1 passed | 1 failed | `assert 'LASTCHILD_SIBLING_S7' in '...CONTENTS_PLAIN_S1openCONTENTS_OPENDETAILS_S2closedCONTENTS_ANIMATED_S6'` |

**Rows 4 and 5 are admissible.** Each replaces the contiguous two-line loop header with a probe followed by that same header. That is one hunk in one file named under "What changed". The loop is unreachable after the `try/finally` return, which is the point: the probe answers instead of the walk.

**Row isolation (point 4).**
- **Row 5:** `CONTENTS_PLAIN_S1`, `S2` and `S6` are all present and only `S7` is missing. The failure is the sibling assertion, not row 4's defect.
- **Row 4:** the `:empty` mechanism is confirmed in the Mode D run. The probe drops the text on the page with the `:empty` rules (`:empty rules + contents`) and reports it on the same page without them (`plain contents`).

**The clock assertion (point 5).** `clock.py` ran these in the copy. The test was copied and edited there only.
- **Unmutated:** passes.
- **Row 5 applied, with `LASTCHILD_SIBLING_S7` removed from the test's `shown` tuple:** fails on the clock assertion itself, `AssertionError: ([416.719...], [0])`. So `before` is non-empty when the call is made, and a restart reddens the assertion on its own.
- **Under load:** 8 consecutive runs of the named test while a full suite ran concurrently: 8 passed (1.71–1.98 s).
- **Residual flake risk (not a failure):** `wait_for_timeout(400)` only bounds how far the clock has advanced. If a loaded browser samples `before` while the animation is still pending at `currentTime 0`, then `0 >= 0` passes and that run is blind to a restart. This lowers sensitivity. It can never produce a false red.

## Mode D (own Chromium, own pages; `moded2.py`, `classify.py`)

Every page ran three detector versions: **OLD** = `c687b73^`, **PROBE** = `c687b73` (cycle 1), **NEW** = the bound tree.
- **Ground truth:** a full-page screenshot hash taken before and after replacing the sentinel text node with glyphs of the same length. `color:transparent` is never used.
- **Controls:** every page has a positive control, and all three versions saw it on every page. Console errors were 0 everywhere.
- **Scale:** 60 layouts, 7 side-effect pages, and the unit's own fixture.

**Point 2 (write-free): CONFIRMED.**
- **MutationObservers.** One observes `document` and one the contents element, with subtree, childList, attributes and characterData. They recorded **0** records for NEW on all 60 layouts, on all 7 side-effect pages and on the fixture. PROBE produced 4 per probed layout, which proves the observers work.
- **`:last-child` animation.** NEW goes 2517→2533 and `SIBLING_ANIM` is seen. PROBE goes 2533→**0** and drops it.
- **`:has(span)` and `:has(*)` elsewhere.** NEW does not restart the animation and sees `HAS_TARGET`. PROBE restarts it to 0 and drops the text.
- **`:empty` rules.** NEW reports the text. PROBE drops it.
- **Sabotage overrides.** The page made `appendChild` and `insertBefore` throw (on the instance and the prototype), made `remove` and `removeChild` no-ops, and made `createElement` throw. NEW reported the text with the control seen, no exception and outerHTML unchanged. PROBE either threw or left a node behind.
- **Fixture `cvcontents.html` (the before/after report count U14(b) asks for):**

  | version | glyphs reported | animation clock | notes |
  |---|---|---|---|
  | OLD | 68 | — | |
  | PROBE | 48 | 417 → 0 | |
  | NEW | 128 | 417 → 433 | `CONTENTS_PLAIN_S1`, `S2`, `S6` and `S7` all present; 0 mutation records |

- **Cycle-1 `anim.py` and `moded.py`, re-run against the committed file.**
  - `anim.py`: NEW sees `SIBLING_ANIM` and `HAS_TARGET`, and the clock advances.
  - `moded.py`: 25/28 correct, `dom=True` on all 28, and every side-effect row is clean. The three wrong rows are `clip-path` (AT-418), `cv:auto` far below (a limit of the screenshot method) and `opacity:0` on the contents element itself (AT-444). This matches the manifest.

**Point 1 (is the walk complete?): NO.**

These attack cases are correct in NEW:
- `<summary>` itself `display:contents` in a closed `<details>`, and a contents span inside it.
- `hidden="until-found"` on a block box (hidden) and on an inline span box (painted and reported).
- Open non-modal `<dialog>`, and a modal one.
- `<fieldset>`: the legend itself `display:contents`, contents inside the legend, and contents in the body.
- `<table>`: a `display:contents` `<tr>`, a `<td>`, and tbody plus tr.
- A `<slot style=display:contents>`, a slot inside a visible div, and the slotted child that must be reported.
- Every nested `<details>` combination:
  - closed > closed, with contents at L1, at L2 and in the inner summary
  - closed > open, at L2
  - open > closed, in the inner summary (painted and reported) and at L2
  - a contents wrapper three deep

Regressions against the cycle-1 probe (PROBE right, NEW wrong):
- **False negative, charged (AT-449).** `details::details-content{content-visibility:visible}` on a closed details. The text paints, and both NEW and OLD drop it.
- **False positives, filed low (AT-450).** Four hidden layouts are reported:
  - a second `<summary>`
  - a closed `<details style=display:contents>`
  - a child slotted into a closed `<details>` inside a shadow root
  - a child slotted into a `content-visibility:hidden` box inside a shadow root

  There are three causes. The `SUMMARY` test accepts any summary, not only the first. The `continue` on `display:contents` skips a details that still hides its body. `parentElement` climbs to the shadow host instead of the slot.

Both PROBE and NEW wrong (pre-existing):
- **AT-451.** A zero-height `contain:paint` flex or grid box. A plain div child is reported too (`classify.json`).
- **AT-418.** A flex box with `clip-path` belongs to that existing class.

Correct in NEW:
- A 0-size grid track with overflow visible: the text paints and is reported.

**The fix direction was measured.** `getComputedStyle(details, '::details-content').contentVisibility` is `hidden` for a closed details and for a closed `display:contents` details, and `visible` for an open one and for the author override. It matches the screenshot in all four (`classify.json`).

**Point 3 (the dead-branch deletion): CONFIRMED.**
- **Not painted and not reported by NEW:** a `display:contents` child of `<video>` (with and without controls), `<audio>` (with and without controls), `<canvas>`, `<iframe>`, `<object>` with SVG data, `<textarea>`, `<select>`, `<img>` and `<input>`. The width guard holds well beyond the maker's fixture.
- **Painted and reported by NEW:** the fallback of an `<object>` with no data, which does render.
- **Slotted child:** reported.
- **No false positive** was introduced by the deletion.

## Contract judgement

- **U14 (the positive rendering detector): NOT MET.**
  - **(a) holds.** The invariance file is green, with every xfail strict and named.
  - **(c) is respected.** Nothing is charged against AT-416, AT-417 or AT-440.
  - **(b) fails, judged against the parent commit.**
    - **The baseline question.** `c687b73` is the unit's parent on master. It reports the `::details-content` text, and `ba30b71` stops. Against `c687b73^` this would not be new, because OLD dropped every contents text. I judge against the parent commit, as the dispatch does ("any case the walk gets wrong where the cycle-1 probe got it right is a regression").
    - **Why charge it.** The author pattern is a documented one: disclosure content forced visible on wide screens. The fix is small and has been measured.
- **C2: holds.** Doctor is clean. `visual_order.js` is 298 lines counted by hand, and the test file is 294.
- **C7: holds.** All 5 rows were reproduced in a proven copy, each on its named assertion, with the anchor-count and file-change assertions in place.

**Issues addressed:** AT-438, AT-442, AT-443 and AT-445 **stay open**, because the unit does not PASS. On `ba30b71`, AT-442, AT-443 and AT-445 do **not** reproduce, and the plain AT-438 layouts are fixed.

**Manifest accuracy (observations, not failures):**
- The Capability coverage section still pastes cycle 1's `3/3` mutation output under a 5-row table.
- It gives the test file as 289 lines; it is 294.
- The unit was again committed (`ba30b71`) before any verdict. This is the same open question cycle 1 raised.
