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
