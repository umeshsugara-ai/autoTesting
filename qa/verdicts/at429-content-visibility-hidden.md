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

---

# Cycle checked: 2

**Date:** 2026-09-16
**Checker:** /checker Mode A + Mode D, fresh subagent, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at429-content-visibility-hidden.md` (Fix cycle: 2, Status: ready-for-check)
**Cycle checked: 2**
**Contract:** `qa/contracts/ui.md` U13 · `qa/contracts/core-invariants.md` C2, C7
**Artifact state judged:** HEAD `3259b67` (the cycle-2 fix is committed; working tree has no diff on `visual_order.js`, `cvdisplay.html`, `test_browser_visual_order.py`, or the unit's evidence files; the other loop's uncommitted `ui/` edits were not touched)

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (U13, C2, C7), 0 invariants violated
FAILURES: none
CAPABILITY-COVERAGE: 4/4 rows reproduced (throwaway copy, imports proven from the copy, each check green before its edit, each red on the assertion it is named for)
LIVE-BROWSER: qa/evidence/browser-at429-content-visibility-hidden-2026-09-16-checker-c2/report.json
ISSUES-WRITTEN: AT-440 (low, false positive on 5 hiding displays missing from HIDES_ON); AT-429 and AT-437 moved open -> fixed; AT-438 stays open
EXPLANATION: I re-ran the ground truth and it matches the committed JSON and CV_PAINTS on all 20 cases. Two other paint methods (text removed, text replaced, full-page screenshots) agree with it on every one of those 20. On 63 probe layouts in my own Chromium, the fix drops no painted text that the pre-AT-429 detector reported. The only painted text still dropped is display:contents (AT-438), and I confirmed that predates this unit. The allow-list errs in the declared direction only: five displays that DO hide are reported, which is a false positive (AT-440, low) and never a missed credential.
```

## What I re-ran (my own output)

| command | result |
|---|---|
| `uv run pytest` (bare) | `1294 passed, 2 skipped, 33 xfailed, 1 warning in 206.78s`; no FAILED, no XPASS. The manifest expects 1287. The extra 7 come from the other loop's untracked `tests/test_ui_case_navigate_reachability.py` and uncommitted `tests/test_ui_cases.py`. xfailed matches exactly (32 scroll-invariance + AT-438). |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `wc -l` | `visual_order.js` 298 (≤300; doctor does not measure .js, AT-419) · `test_browser_visual_order.py` 267 · `paintsInk` about 30 lines |
| `mutation_check.py` at429 | `4/4 mutations killed`, each attributed to its named tests |
| regressions | at358 `21/21` · at410 `1/1` · at379 `7/7` · at423 `3/3` |
| `groundtruth.py` | 20/20 identical to `groundtruth.json` and to `CV_PAINTS`, case by case |

Note: the manifest's "Actual outputs" block still pastes the cycle-1 `2/2` mutation run, while its verify line expects `4/4`. My re-run gives `4/4`. This is stale text in the manifest and does not affect the result.

## Judge point 1: the ground truth, and its method

**Re-run:** all 20 cases agree across `groundtruth.py` (re-run), `groundtruth.json`, and `CV_PAINTS`. The 10 cases that hide are exactly the 10 entries in `HIDES_ON`.

**Second and third independent methods.** On every probe page I measured paint three ways, each on a fresh page: m1 is the maker's method (transparent colour, `#frame` clip); m2 is a full-page screenshot with the sentinel text node emptied; m3 is a full-page screenshot with the sentinel replaced by different glyphs. **All 20 measured display types agree on all three methods.** This goes beyond the "at least three cases" asked for. It also covers text painted outside the frame, because m2 and m3 use full-page shots on a 1000px viewport, and it separates a change in the text from any other change, because m2 and m3 do not touch colour.

**The method challenge is real, but it does not affect these 20.** m1 disagrees with m2 and m3 on two of my extra layouts. On an open `<dialog>` and a `<select>` with `content-visibility:hidden`, m1 says "painted" and the other two say "not painted". Making the element transparent also recolours its `currentColor` border or arrow, which is exactly the non-text change you asked me to look for. So `groundtruth.py`'s method can call a hiding box "paints". On a future display type that would leave it OUT of `HIDES_ON`, which means it would be reported: a false positive, never a missed credential. No measured entry is affected. A future re-measurement should use m2 or m3. This goes in the explanation, not in a failure.

## Judge point 2: new false negatives or false positives from the allow-list?

The probe covers 63 layouts, each with a positive control (`POSCTRL_VISIBLE_OK` and `TAIL_OK`, seen on all 63 pages). Console errors: 0 in total. Each layout ran three detector versions: now (`3259b67`), cycle 1 (`dbe6185`), and pre-AT-429 (`dbe6185^`).

| display asked about | painted? (m1/m2/m3) | detector now | class |
|---|---|---|---|
| `-webkit-box` | no/no/no | reported | false positive |
| `-webkit-inline-box` | no/no/no | reported | false positive |
| `math` (text in `<mtext>`) | no | dropped | OK (checkVisibility) |
| `<mtext>` itself (`block math`) | no | reported | false positive |
| `inline list-item` | **yes**/yes/yes | reported | OK (paints; not in the list; reported) |
| `block ruby` | no | reported | false positive |
| `<summary>` (`list-item`) | no | dropped | OK |
| also: `flow-root list-item` | no | reported | false positive |

Other layouts probed, all correct now: `inline flow-root` (computed as `inline-block`), `button`, `fieldset`, `legend`, open `dialog`, a floated or absolutely positioned span (blockified), SVG `<text>` and SVG root, `input` value and placeholder, `textarea`, and `select`. None paints, and none is reported.

- **Unmeasured displays go to the reported side:** confirmed. All five that hide are reported (false positives). The one that paints (`inline list-item`) is reported (correct). **None is a false negative.** Filed as **AT-440 (low)**. `display:-webkit-box` is the usual line-clamp idiom, so this false positive can occur on real pages.
- **No painted text dropped:** across all 63 layouts, `new_false_negatives_vs_pre_at429 = []`. The only painted text dropped now is `contents`, and `dbe6185^` dropped it too. Paint results were stable across the three runs.

## Judge point 3: the parent-only limit

- **Direct text inside a hiding box whose display is not in `HIDES_ON`:** yes. There are exactly the five layouts above (`-webkit-box`, `-webkit-inline-box`, `flow-root list-item`, `block ruby`, `block math`). They are false positives the allow-list cannot catch, and all five are recorded in AT-440.
- **A hiding box with its text one level down, where `checkVisibility()` also misses it:** none found. I probed 20 nested shapes: block>span, td>b, li>a, flex>span, caption>b, inline-block>b, -webkit-box>span, summary>b, button>b, fieldset>legend, block>input, block(cv)>inline(cv), inline(cv)>block(cv), and others. Every one that hides was dropped. Every nested shape under a non-hiding box paints, and every one was reported: inline>div, inline>b, ruby>b, contents>span, table>td>b, tr>td>b, inline>input, table>input. `checkVisibility()` therefore agrees with paint on every nested case I built, including `inline(cv)>block(cv)`. Pre-AT-429 reported that case as a false positive, and it is now correctly dropped.

## Judge point 4: AT-438 strict xfail

Checked in throwaway copies, with imports from each copy confirmed by `observe.__file__`:
- Current detector, xfail mark removed: `FAILED [contents]`, `AssertionError: contents paints but was dropped`.
- **Pre-AT-429 detector (`dbe6185^` `visual_order.js`), xfail removed:** `FAILED [contents]` with the same assertion. The defect predates this unit, and my 63-layout probe agrees: `dbe6185^` reports `contents` = false.
- **AT-438 simulated as fixed** (`checkVisibility` skipped for `display:contents`), with the strict xfail kept: `1 failed`, an XPASS(strict). Fixing AT-438 will make this test fail. The at358 and at429 mutation runs back up the cause: removing `checkVisibility()` makes `[contents]` show up under "actually failed".

## Judge point 5: mutation row 1's narrowed kills

In the copy, with the display condition dropped (`if (style.contentVisibility === "hidden") return false;`), I ran **all 20** cases, not only the named ones: `3 failed, 16 passed, 1 xfailed`. The failures are exactly `[inline]`, `[ruby]` and `[ruby-text]`. Every other painted case passes whether or not the display condition exists: `table`, `inline-table`, and the 4 `table-row*` cases, because their text's parent is a `<td>` (`table-cell`), and `contents`, which is dropped earlier. So the narrowed set is the complete set of cases that isolate the display condition. Nothing that would die was dropped from the claim.

**Coverage gap, not a failure.** The allow-list is tested only by the 3 kills above and by `table-cell`. I also removed `table-caption` from `HIDES_ON` in the copy: `1 failed ([table-caption])`, so that entry is falsifiable as well. With the whole guard removed, though, `[table-caption]` does not fail. Its sentinel interleaves with the caption's table cell `c` (`...SCcVD_TABLE_CAPTION...`), so its `not in` assertion passes by accident. This is the same interleave weakness the cycle-1 verdict noted, and it does not change this verdict.

## Capability coverage (my throwaway copy, outside the bound root)

Setup: copied `src tests scripts pyproject.toml` to the scratchpad and ran the repo venv with `PYTHONPATH=<copy>/src`. `autotester.browser.observe.__file__` resolved inside the copy for every run. All 20 cases were green in the copy before any edit (`19 passed, 1 xfailed`). Each edit was a single hunk in `visual_order.js`, applied with its anchor matched exactly once, then restored and confirmed green again.

| row | before (copy) | edit | after | assertion that fired |
|---|---|---|---|---|
| 1 | `5 passed` (inline, ruby, ruby-text, table, table-row) | drop `&& HIDES_ON.test(style.display)` | `3 failed` of all 20: inline, ruby, ruby-text | `inline paints but was dropped` (and the same for ruby and ruby-text) |
| 2 | `3 passed` | remove the guard | `3 failed` | `block hides but was reported`, `flex hides but was reported`, `'CVAUTO_ONSCREEN_SENTINEL_63' in …` (interleave) |
| 3 | `1 passed` | remove `table-cell` from `HIDES_ON` | `1 failed` | `table-cell hides but was reported` |
| 4 | `2 passed` | `checkVisibility` line → `if (false)` | `2 failed` | `'CVHIDDEN_NESTED_SENTINEL_62' not in …`, `'DETAILSBODY_SENTINEL_77' not in …` |

No cell was a shell command, a conftest edit, or a multi-file edit. `git diff` on `src/autotester/browser/visual_order.js` in the bound tree was empty afterwards.

## Criteria

- **U13:** met. AT-437 is fixed: painted text on inline and ruby boxes is reported again. AT-429 is fixed: direct hidden text on the 10 measured hiding displays is dropped. 63 layouts show no painted text dropped relative to `dbe6185^`. The remaining false negative (`contents`, AT-438) predates this unit and is held by a strict xfail that will fail if it is fixed. The remaining false positive (AT-440) falls on the side the module has declared.
- **C2:** met. `doctor: clean`, `visual_order.js` is 298 lines, the test file 267, `paintsInk` under 50 lines.
- **C7:** met. `4/4` mutations with attributed kills, plus 4 of 4 rows reproduced independently in a copy.

## Ledger

- AT-429 open → fixed · AT-437 open → fixed (both `fixed_date` 2026-09-16, with `fix_evidence` citing this verdict)
- AT-438 stays open (not fixed by this unit; the strict xfail is recorded)
- AT-440 new (low, `false-positive`), written in the canonical schema: `date`, `found_by`, `feature`, `evidence`, `expected`, `fixed_date`, `verified_date`
