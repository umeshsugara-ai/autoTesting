# Verdict — at410-first-glyph-content-visibility

**Checker:** /checker Mode A + Mode D, fresh subagent, bound to `D:/autoTesting`
**Date:** 2026-09-16
**Manifest:** `qa/manifests/at410-first-glyph-content-visibility.md` (Status: ready-for-check, Fix cycle: 1)
**Cycle checked: 1**
**Artifact under check:** commit `77cba2d` (tree clean for `src/` and `tests/` at check time)

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (U13, C2, C7), 0 invariants violated
FAILURES: none
CAPABILITY-COVERAGE: 2/2 rows reproduced (each green-before / red-after in the checker's own throwaway copy)
LIVE-BROWSER: qa/evidence/browser-at410-first-glyph-content-visibility-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-436 (low); AT-410 open -> fixed; AT-398 open -> fixed
EXPLANATION: The warm-up query fixes the first-glyph drop on the committed fixture and on every harder shape probed (several text nodes, two skipped blocks, nested content-visibility:auto, closed <details> inside an off-screen block), and leaves a leading U+200B dropped exactly as before. Against the unfixed detector it changes no observable page state; it costs about 11 % more time on a 1000-node page of skipped blocks. The AT-398 revert is proven from both sides: the closed-details mutation kills now, and survives on the unfixed detector with the sentinel at character 0.
```

## What I re-ran myself (never the pasted outputs)

| command | result |
|---|---|
| `uv run pytest` (bare) | `1260 passed, 2 skipped, 32 xfailed, 1 warning in 207.21s`, exit 0, **0 XPASS** |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| `mutation_check.py …/at410-first-glyph-content-visibility/mutations.json` | `1/1 mutations killed`; claims = actually failed = `test_the_first_call_on_a_content_visibility_subtree_drops_no_glyph` |
| `… at358-visual-order-detector` | `21/21`; row "AT-372: a CLOSED <details> body…" KILLED, attributed to `test_text_a_reader_cannot_see_is_not_reported[closed-details]` |
| `… at379-scrollable-pane-reachability` | `7/7` |
| `… at423-scroll-invariance-probe` | `3/3` |
| `wc -l src/autotester/browser/visual_order.js` | **298** |

## The six judged points

**1. Does the fix fix it, and where does it stop.** My own Chromium 151.0.7922.34, a fresh page per trial, 3 trials each. UNFIXED is `git show 77cba2d^:…/visual_order.js` and FIXED is the bound tree:
- committed `cvauto.html`: UNFIXED first call `…VAUTO_SENTINEL_91…` 3/3, second call correct. FIXED first call `CVAUTO_SENTINEL_91` 3/3.
- **several text nodes** (4 `<p>` plus a mixed `<p>A<b>B</b>C</p>` in one skipped block, then a second skipped block): UNFIXED drops only the **first node of each skipped block** (`LPHA_SIB_11`, `OLF_BLOCK2_14`). Siblings stay intact, so one query warms the whole block and later nodes do not depend on order. FIXED is intact 3/3. Because the fix warms every node, it also covers a block whose first node is not the first one measured.
- **U+200B first:** both variants return `ZWSP_SENTINEL_33`, with the U+200B dropped and the `Z` kept. The warm-up changes nothing here.
- **nested `content-visibility:auto`:** UNFIXED `ESTED_INNER_41` 3/3. FIXED `NESTED_INNER_41` 3/3.
- **closed `<details>` inside an off-screen block:** neither variant reports the body. UNFIXED **also dropped the visible summary's first glyph** (`UMMARY_SEEN_51`), a false negative on visible text that this unit's fix removes. FIXED `SUMMARY_SEEN_51` 3/3.

**2. Side effects of the warm-up.** On every page I compared the state before a call, after the first call, and after the second: `scrollX/scrollY`, `checkVisibility({contentVisibilityAuto:true})` per block, recorded `contentvisibilityautostatechange` events, and body child count. All of them are **identical between UNFIXED and FIXED**. The per-glyph loop already forced the same layout, so the warm-up adds no new side effect. p4 fires the same two `skipped=true` events under both variants. With FIXED, first call == second call on every page. With UNFIXED they differed on p1, p2, p4 and p5. Timing is the median of 7 fresh pages. On 1000 nodes in 25 skipped blocks it went from 110.7 ms to 122.5 ms (about +11 %), and the output grew from 43351 to 43372 characters, meaning UNFIXED lost 21 glyphs there. On 1000 on-screen nodes it went from 98.0 ms to 103.2 ms (about +5 %). That is real but small, and it is not a finding.

**3. The fixture really reproduces.** `cvauto.html` drops the glyph on UNFIXED 3/3 in the live probe. In my copy, the named test goes red once the warm-up is removed, with `AssertionError: Quarterly report for the trainers listVAUTO_SENTINEL_91CVAUTO_SECOND_92`. It is not a test that passes both before and after the fix.

**4. The AT-398 revert, both halves**, run in my copy against the committed `unreadable.html` with the sentinel at character 0:
- FIXED JS: `[closed-details]` passes. With the `checkVisibility` bypass it **fails** on `assert 'DETAILSBODY_SENTINEL_77' not in …` (KILLED).
- UNFIXED JS: the test passes. With the same bypass it **still passes** (SURVIVED). The live probe shows why: the first call returns `…AppendixETAILSBODY_SENTINEL_77…`.
The revert is therefore evidence, not tidying.

**5. AT-429.** `content-visibility:hidden` → `CVHIDDEN_SENTINEL_92` is reported by UNFIXED and FIXED identically, 3/3 each. The defect predates this unit and is not made worse. The removed hidden-block assertion did not weaken the AT-410 test: point 3's kill and the harness's attributed 1/1 both stand. AT-429 stays open.

**6. Line cap.** Counted myself: **298** lines (cap 300). `glyphsOf` is about 34 lines (cap 50). Doctor does not see `.js` (AT-419, still open).

## Capability coverage (throwaway copy at `%TEMP%/…/scratchpad/copy`, src/tests/scripts/pyproject copied from the post-change tree; the bound tree was never edited: `git diff --quiet -- src` held)

| row | green before (copy) | falsifying edit (single hunk, `visual_order.js`) | red after (copy), on the named assertion |
|---|---|---|---|
| first call reads a skipped subtree whole | `1 passed` | remove the 3 warm-up lines (anchor matched once, file changed) | `1 failed`, `assert "CVAUTO_SENTINEL_91" in first` → `…listVAUTO_SENTINEL_91…` |
| closed-details guard holds alone | `1 passed` | `checkVisibility` line → `if (false) return false;` (matched once) | `1 failed`, `assert 'DETAILSBODY_SENTINEL_77' not in …` |

Both cells are admissible single-hunk edits to a file named in "What changed". No cell contained a command or an instruction.

I verified import isolation. With `PYTHONPATH=<copy>/src`, `observe.__file__` resolves inside the copy, and I ran the row-1 red both with and without that override.

## Criteria

- **U13**: holds. The unit does not touch `ui/helpers.py`, `core/redact.py`, or any strip or refusal in the in-scope floor. It improves `visualOrder`, the detector U13 names as still owed, and does not narrow it.
- **C2**: holds. 298 ≤ 300 lines, `glyphsOf` ≤ 50, doctor clean, new fixture 21 lines, test file 199.
- **C7**: holds. The added test was mutation-tested with a green asserted baseline and a named, attributed kill, and I re-ran it independently. The neighbouring specs are all killed, and the xfail corpus is unchanged (32, no XPASS).

## Ledger

- AT-410 → `fixed` (2026-09-16). AT-398 → `fixed` (2026-09-16). The same root cause is gone on the details path, per point 4.
- AT-429 remains open, as filed.
- **AT-436 (low, new):** AT-429 was filed in the alternate ledger schema (no `date`/`found_by`), repeating the AT-404 class.
