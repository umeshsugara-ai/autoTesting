# Verdict — at429-content-visibility-hidden

**Date:** 2026-09-16
**Checker:** /checker Mode A + Mode D, fresh context, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at429-content-visibility-hidden.md` (Fix cycle: 1)
**Cycle checked: 1**
**Contract:** `qa/contracts/ui.md` U13 · `qa/contracts/core-invariants.md` C2, C7
**Artifact state judged:** HEAD `dbe6185` (the fix is already committed; working tree has no diff on the unit's files)

```
VERDICT: FAIL
SCOREBOARD: 2/3 criteria met (C2, C7 met; U13 detector obligation not met), 0 invariants violated
FAILURES:
- [U13 / manifest capability row 1] sev: medium · the new guard `style.contentVisibility === "hidden"` (visual_order.js:90) drops VISIBLE text wherever content-visibility:hidden has no effect: a non-atomic inline <span>, an inline custom element, a ruby <rt>. Live screenshot shows the text painted; pre-fix code reported it; fixed code does not. This fix for a false positive created a false negative of the AT-355 shape · fire the guard only where containment applies (not display inline / contents / ruby-* / non-cell table-internal), or decide by measurement; add a positive assertion for `<div><span style="content-visibility:hidden">X</span>VISIBLE</div>` to the unit's test · issue: AT-437
CAPABILITY-COVERAGE: 2/2 rows reproduced (both killed in a throwaway copy, green before the edit); row 1's claim is broader than what holds, see AT-437
LIVE-BROWSER: qa/evidence/browser-at429-content-visibility-hidden-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-437 (medium, created by this fix), AT-438 (medium, pre-existing); AT-404 and AT-436 moved open -> fixed
EXPLANATION: The fix does what it claims on block boxes: direct hidden text is dropped, nested hidden text is still caught by checkVisibility(), and the interleave is real and gone. But the guard reads computed style, and computed style says "hidden" even where the browser ignores it. On an inline span, an inline custom element, or a ruby <rt>, the text still paints, and the detector now drops it. AT-429 stays open.
```

## What I re-ran (my own output, not the manifest's)

| command | result |
|---|---|
| `uv run pytest` | `1268 passed, 2 skipped, 32 xfailed, 1 warning in 217.48s`; 0 XPASS |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `wc -l` | `visual_order.js` 295 · `test_browser_unreadable.py` 294 · `cvhidden.html` 17 |
| `mutation_check.py` at429 | `2/2 mutations killed`, both attributed to the named tests |
| regressions | at358 `21/21` · at410 `1/1` · at379 `7/7` · at423 `3/3` |

## Judge point 1: did the fix create a false negative? YES

My own Chromium ran my own 30 probe pages, each with a positive control. To get ground truth, I scrolled each sentinel into view, took a screenshot, blanked the sentinel's characters and took another. If the two screenshots differ, the text was painted. I ran OLD (`git show dbe6185^`) and NEW (the bound file, read-only) on every page. Console errors: 0 on all pages.

| probe | painted | old | new |
|---|---|---|---|
| `content-visibility:auto` on-screen | yes | yes | yes |
| `auto` off-screen, `contain-intrinsic-size:auto 40px` | yes | yes | yes |
| `auto` off-screen, px intrinsic size, nested `<p>` | yes | yes | yes |
| starts `hidden`, script sets `visible` before measuring (plus the following line) | yes | yes | yes |
| starts `hidden`, script sets `auto` (nested) | yes | yes | yes |
| **`<div><span style="cv:hidden">SPANX_G</span>VISIBLESIB_H</div>`**: the span | **yes** | yes | **NO: false negative** |
| the same, its visible sibling | yes | yes | yes |
| **`<x-card style="cv:hidden">` direct text** (inline by default) | **yes** | yes | **NO: false negative** |
| **`<rt style="cv:hidden">`** | **yes** | yes | **NO: false negative** |
| inline-block span `cv:hidden` | no | yes | no (fixed) |
| `<td>` `cv:hidden` | no | yes | no (fixed) |
| `<tr>` `cv:hidden` | yes | yes | yes |
| `<input style="cv:hidden">`, `<textarea>`, `<button>` | no | yes | no (fixed; the control-mirror path is right) |
| `<input>` without cv next to it | yes | yes | yes |
| `hidden="until-found"` | no | yes | no (fixed) |
| `display:contents; cv:hidden` | **yes** | no | no: pre-existing, see AT-438 |

Computed style for the three new misses: `display` is `inline` / `inline` / `ruby-text`, `contentVisibility` is `hidden`, and `checkVisibility()` is `true`. Size containment does not apply to non-atomic inline boxes or ruby-internal boxes, so the browser renders their contents. The guard only reads the computed value, so it drops them. The screenshot `false-negatives-new-code.png` shows SPANX_G, CUSTOMDIRECT_O and RUBYRT_AE on screen. On that page the new detector returns `CONTROLPOSITIVE_SEVENTYSEVEN1: VISIBLESIB_H2: 3: KANJI_AD4: 5: VISIBLESIB_J`.

Pre-existing, filed and not charged to this unit: AT-438. Text directly inside ANY `display:contents` element is painted but dropped, because `checkVisibility()` is false on an element with no box. I measured it without content-visibility too: `<div style="display:contents">PLAINCONTENTS_2</div>` gives `CTRL_1` only.

## Judge point 2: is the parent-only argument true? Yes, for every nested shape I tried

These nested shapes all paint nothing, and old and new both drop them: 3-4 levels deep (`div > div > section > article > p`); a `hidden` ancestor with a `cv:auto` element between it and a `<p>`; a `hidden` ancestor with `cv:auto` holding the text directly; a `hidden` ancestor with an inline `<span>`; a block custom element `<x-card style="display:block;cv:hidden"><p>`; an input inside a hidden block. No nested case gets past both guards.

The attribution holds. The new guard reads only the parent's own computed style, and in every nested case the parent is not `hidden`, so all nested exclusion belongs to `checkVisibility()`. In my copy, removing `checkVisibility()` made `CVHIDDEN_NESTED_SENTINEL_62` appear, and `[closed-details]` failed too.

One nested case is a positive, not a leak. An INLINE custom element with `cv:hidden` and a `<b>` inside paints its text, and both versions report it, which is correct. The parent-only choice is sound. The defect is only in which boxes the parent check fires on.

## Judge point 3: the interleave, reproduced on OLD code

- Manifest layout b (`hidden` then `auto`): OLD returns `CONTROLPOSITIVE_SEVENTYSEVENHAIUDTDOE_NS1_S2`, exactly as claimed. NEW returns `…AUTO_S1`, whole.
- The committed fixture `cvhidden.html`: OLD returns `…listCCVVAHUIDTDOE_NO_NDSICRREECETN__SSEENNTTININEELL__6613`. NEW returns `…listCVAUTO_ONSCREEN_SENTINEL_63`.
- `hidden` followed by a PLAIN div (no cv): OLD returns `HPLIDADINE_NS_3S2`, so the interleave does not need `auto`. A `<li cv:hidden>` followed by a normal `<li>` also garbles on OLD. NEW is whole in both.

The positive assertion is as strong as claimed. In my copy with the guard removed, the test failed on `assert 'CVAUTO_ONSCREEN_SENTINEL_63' in …` because the text interleaved. **Note:** on this fixture it is the positive assertion that fires, not the DIRECT negative. The interleave scrambles the direct sentinel, so `not in` holds. If a future layout change stops the interleave, only the direct negative would be left to catch a regression. It would still catch it.

## Judge point 4: the two condensed comments

- **Alpha regex:** kept: the anchor to the four-component form is deliberate; the first regex also matched `rgb(0,0,0)` and read the BLUE channel as alpha; black text counted as transparent and every page came back empty; only a same-page positive control caught it (AT-363). Lost: the literal text of the bad regex `rgba?\([^)]*,\s*([\d.]+)\s*\)`, and the point that every "is not reported" assertion would have passed on a blind detector. That second point survives only as "caught only by a same-page positive control". Enough to stop the bug coming back. Losing the literal regex is a small cost.
- **Width test:** kept: width alone, on purpose; `width === 0 && height === 0` is right for an element but a one-character Range keeps the full line height, so that form kept every U+200B. Lost: the provenance, which is where the bad form was copied from (`enumerate.js::isVisible`). Not needed to stop the bug coming back.
- Line count, counted myself: 295 (≤ 300). `paintsInk` is 29 lines (≤ 50).

## Judge point 5: ledger repair `e33b916` (AT-404, AT-436)

`git show e33b916 -U0 -- qa/issues.jsonl` has exactly 3 hunks, 3 lines removed and 3 added, at lines 395, 420 and 426: AT-398, AT-423 and AT-429. The commit's only other file is the at410 manifest. For each row I parsed the old line, applied opened→date, source→found_by, area→feature, detail→evidence, and compared it field by field with the new line. Every value is identical. The only other change is new `fixed_date` / `verified_date` keys with null values (AT-398: `verified_date`; AT-429: both). No row changed on any other key. Current ledger: no row lacks `found_by` or `date`, and AT-398 has no cp1252 mojibake left. **Decision: AT-404 and AT-436 are moved to `fixed`.**

## Capability coverage (my throwaway copies, outside the bound root)

I made copies of `src tests scripts pyproject.toml` in the scratchpad and ran them with `PYTHONPATH=<copy>/src` and the repo's venv interpreter. `autotester.browser.observe.__file__` resolved inside the copy, so the tests ran the copy's code. The bound tree was never edited: `git diff` on `visual_order.js` was empty afterwards.

| row | before the edit (copy) | edit (single hunk, `visual_order.js`) | after the edit | the assertion that failed |
|---|---|---|---|---|
| 1 | `2 passed` | removed `if (style.contentVisibility === "hidden") return false;` (anchor count 1) | `1 failed, 1 passed` | `assert 'CVAUTO_ONSCREEN_SENTINEL_63' in 'Quarterly…CCVVAHUIDTDOE_NO_N…6613'`, the interleave (AT-429's own test) |
| 2 | `2 passed` | removed the `checkVisibility()` line (anchor count 1) | both named tests failed | `'CVHIDDEN_NESTED_SENTINEL_62' not in …` and `'DETAILSBODY_SENTINEL_77' not in …` |

Both rows are reproduced. Row 1's capability as worded, "text whose parent is content-visibility:hidden is not reported", is broader than what is true. It holds only where containment applies, and the probes above falsify it for inline and ruby boxes (AT-437).

## Criteria

- **C2:** met. `doctor` is clean, the file is 295 lines, and the functions are within the cap.
- **C7:** met. The mutation harness checks its baseline and attributes each kill to the named test. I re-ran 2/2, and my own copy-based falsifications agree.
- **U13 (the positive rendering detector is owed, and its edge does not move):** not met. The unit makes the detector miss text a reader can see, on constructs it reported before (AT-437).
