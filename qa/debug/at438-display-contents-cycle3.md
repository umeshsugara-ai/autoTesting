# Stall diagnosis: at438-display-contents, after cycle 3

**Dispatched by:** /maker on STALLED (fix cycle 3 of 3) · **Skill:** /agent-debugger, Phases 1–2 only
**Date:** 2026-09-16 · **Bound root:** `D:/autoTesting` · read-only toward code; this file is the only write
**Sources:** `qa/manifests/at438-display-contents.md`, `qa/verdicts/at438-display-contents.md` (cycles 1–3),
`qa/evidence/browser-at438-display-contents-2026-09-16-checker-c3/` (`report_moded3.json`, `report_attack3.json`,
`report_fixdir3.json`), `qa/issues.jsonl` AT-438…AT-454, `qa/contracts/ui.md` U14,
`qa/debug/at379-scrollable-pane-reachability-cycle3.md`, `git log -- src/autotester/browser/visual_order.js`

## Phase 1: Failure capture

| cycle | commit (time) | what the maker claimed | what the checker measured | charged |
|---|---|---|---|---|
| 1 | `c687b73` (17:44), verdict `da37ff0` 17:55 | an inserted probe `<span>` answers "is this contents element rendered?" | the probe restarts author `:last-child`/`:has()` animations, so visible sibling text is dropped (AT-442 high). Author `:empty`/`#c>span` hides the probe (AT-443). Page-patched DOM methods throw or leave the probe behind (AT-445). Also `opacity:0` on the contents element (AT-444, pre-existing) | U13 (AT-442) |
| 2 | `ba30b71` (18:18), verdict `4e36b06` 18:43 | a write-free walk up to the nearest box. A closed `<details>` is judged by tag (`DETAILS && !open`) | AT-442/443/445 no longer reproduce. An author `::details-content{content-visibility:visible}` paints but is dropped (AT-449). 4 FPs the probe got right (AT-450) | U14(b) (AT-449) |
| 3 | `9fc937d` (20:59), verdict `00fcdc3` 21:25 | "judge `<details>` by what the browser actually applies": `getComputedStyle(box,'::details-content').contentVisibility`, and a flat-tree walk via `assignedSlot` | 57/60 on the layout table (0 FN, 3 pre-existing FPs), write-free on all 95+ pages, 9/9 isolating mutations. But `::details-content{display:contents\|inline}` reports cv `hidden` while Chromium paints (A3.png/A4.png): AT-453. Closed-mode shadow leaves `assignedSlot` null: AT-454, low FP | U14(b) (AT-453) |

- **Error:** there is no tool, runtime or suite failure. In every cycle, pytest, ruff and doctor were green (cycle 3: `1326 passed, 2 skipped, 32 xfailed`; `doctor: clean`).
- **Last successful step:** cycle 3's code on master. On the 60-layout table it has 0 FN, against 22 for the pre-unit detector `c687b73^`.
- **Repeated pattern:** each cycle swapped one proxy for "does this subtree paint" for a finer one: probe box, then tag+`open`, then pseudo cv. Each time the checker found the next CSS knob that the proxy does not read. That makes 3 cycles and 3 proxies.
- **Environment assumptions verified:** the checker's harness reproduces the manifest's numbers exactly (cycle 3, Point 1: "The counts match the manifest exactly"). Chromium is 151.0.7922.34, and `CSS.supports('selector(::details-content)')` is true. The environment is not implicated.

## Phase 2: Root-cause diagnosis

### Root cause, in two parts

**1. (Loop design, primary) The U14(b) baseline moved with each committed failed cycle.** U14(b) charges a change that "stop[s] reporting text … where the **pre-change** detector reported it" (`qa/contracts/ui.md` U14). The maker committed each cycle before its verdict (`c687b73`, `ba30b71`, `9fc937d` all precede their FAIL commits). So from cycle 2 on, the checker took the *parent commit* as "pre-change", and that commit was a rejected cycle:
- Cycle 2's verdict says so directly: "Against `c687b73^` this would not be new, because OLD dropped every contents text. I judge against the parent commit".
- Cycle 3 inherited that baseline: "A case that cycle 3 gets wrong where an earlier committed version of this unit got it right counts against the unit."

The effective floor became the **union of every correct answer any cycle ever gave**. That union includes the cycle-1 probe, which was itself failed for a *high* regression (AT-442). Measured against the true pre-unit detector `c687b73^`:
- AT-449 is not a new FN (OLD is FN on it; cycle-2 verdict).
- A3/A4 (AT-453) are not new FNs (OLD is FN on both; `report_attack3.json`).
- AT-450/AT-454 are FPs, and U14(b) does not charge those.

On that reading, cycles 2 and 3 each met U14(b) literally. The loop could not converge, because the probe was the only version that got the `::details-content` override family right, and it is also the one version that can never ship.

**2. (Execution, secondary) Cycle 3 left out one known fact.** `HIDES_ON` sits eight lines below the new check (`visual_order.js:79`, used at :74 and :95). It exists because computed `content-visibility:hidden` does not hide on every display (AT-437). The maker applied it to boxes but not to the `::details-content` pseudo. The fix is one conjunct. This is a real miss, but a small one. On its own it would have cost one cycle, not a stall.

**Not the cause:**
- Tooling, environment and the verify commands: all were reproduced.
- The checker inventing criteria: U14 exists, and every charge cites (b) with screenshots.
- Scope creep inside the maker's diff: all hunks sit in `contentsRenders`/`flatParent`, and `reachOf` is byte-identical (cycle 3, Point 5).

### Classification: **LOOP DESIGN**, with a one-line execution miss on top

| sub-pattern | present? | evidence |
|---|---|---|
| Checker charges new edge cases against an ever-growing baseline | **yes, the decisive one** | the cycle-2 baseline note quoted above. Cycle 3 applies "any earlier committed version" |
| Recurring "proxy instead of the browser's answer" | yes | the same lesson recurs from AT-437 through AT-438/442/449/453. Manifest cycle 3: "I swapped one hand-written list for another" |
| Commit before verdict | yes, ×3 | flagged by all three verdicts. It is the mechanism that turned rejected cycles into baselines |
| Unit scope too broad | partly | one unit carried AT-438, 442, 443, 445, 449 and 450. Each FAIL widened the "Issues addressed" list, so the unit could only PASS by being perfect on a growing attack corpus (60 layouts, 29+6 attack pages, 7 side-effect pages, 13 fixture sentinels) |
| Unmeasurable-by-design class charged or filed without a (c) home | yes (AT-454) | a `mode:"closed"` shadow root is opaque to page script by spec. No in-page `visual_order.js` change can fix it |

**Comparison with at379 cycle 3** (`qa/debug/at379-…-cycle3.md`): that stall was also loop design. The detector had *no* acceptance line, so verdicts invented one each cycle, and the fix was U14. This stall is the next failure mode of the same module: U14 now exists, but **its baseline term is undefined when failed cycles land on master**. The recurrence is the finding. U14(b) needs one sentence, not a new criterion.

### Is the checker's candidate a sound starting point?

The candidate is `cv === "hidden" && HIDES_ON.test(pseudo.display)`, measured 26/26 on details pages in `report_fixdir3.json`.

**Yes, as a starting point, with four conditions:**
1. **The corpus was too narrow.** fixdir3 covered 26 details-shaped pages (A1–A7, B1–B6, flow-root/grid, the details rows of the 60). It was **not** re-run on the full 60 layouts, the 35 attack pages, the side-effect pages or the `cvcontents.html` fixture. "Breaks nothing NEW got right" is proven only on those 26. The next unit must re-run the full `moded3` + `attack3` + side-effect corpus.
2. **It applies an element-measured allow-list to a pseudo.** Pseudo displays measured so far: `contents`, `inline` (paint), `flow-root`, `grid`, `block`/default (hide), `none` (A5). Any unmeasured pseudo display (e.g. `flex`, `table`, or the AT-440 `-webkit-box` family) falls to "reported". That is the FP direction, which the U14(b) tie-break accepts. It is safe, but the gap should be disclosed.
3. **The unsupported-pseudo path fails toward FP.** It returns `""` (cycle 3, Point 2). It is safe under the tie-break and already pinned by fixture S3.
4. **The line cap.** `visual_order.js` is at exactly **300** (C2), and doctor still does not measure `.js` (`doctor.py:43,50` glob `*.py`; AT-419 open). The conjunct must be line-neutral. For example, one `hides(s)` predicate (`s.contentVisibility === "hidden" && HIDES_ON.test(s.display)`) reused at :71, :74 and :95 removes duplication and nets ≤ 0 lines.

**It does not address AT-454, and should not try.** Closed-shadow slotting cannot be observed from page JS. Fixing it needs a CDP-side flat tree, which is a different module and a different unit.

**No revert.** Normally a regression would mean reverting. Here the last "good" state by the U14(b) literal baseline is `c687b73^`, which is strictly worse: 22 FN against 0. Reverting would reintroduce the missed-text class this detector exists to prevent. Keep `9fc937d`.

## Smallest recovery: proposed `qa/QUEUE.md` row (text only, not written)

> **AT-453: `::details-content` hides only on a display that takes containment (split from at438; max 2 cycles).**
> **Baseline, declared up front:** `9fc937d` (the tree on master), and no earlier cycle.
> **Change:** in `visual_order.js` `contentsRenders`, judge the `::details-content` pseudo with the same measured rule as boxes. Factor one `hides(style)` predicate (`contentVisibility === "hidden" && HIDES_ON.test(display)`) and use it at the details check, the box check and `paintsInk`, keeping the file ≤ 300 lines.
> **Fixture:** add `details::details-content{display:contents}` and `{display:inline}` sentinels (must be reported), plus a `{display:flow-root}` sentinel (must not be).
> **Mutation row:** drop the display conjunct on the pseudo. It must kill on exactly the two new sentinels.
> **Evidence:** a version table (`c687b73^`, `c687b73`, `9fc937d`, new) over the checker's full cycle-3 corpus (`moded3.py` 60 + `attack3.py` 35 + side-effect pages + fixture), with MutationObserver records = 0.
> **Out of scope:** AT-454 (closed shadow), AT-444, AT-451, AT-418, AT-440.
> **Commit only after the verdict (C10).**

Close-out for the parent: AT-438's base layouts, plus AT-442/443/445/449/450, are **measured fixed on `9fc937d`** (cycle-3 verdict, "Issues addressed"). They need a checker ruling, not another maker cycle. See the gate below.

## HUMAN_GATE: warranted (one decision, three parts; ask once, write to disk)

The first part re-rules how past verdicts were judged, and the third changes a contract-owned blind set (U14(c) says widening it is an amendment). Neither is the maker's call. The checker could make the amendment alone, but it would be ruling on its own ratchet.

1. **U14(b) baseline.** Option A (recommended): "pre-change" means the detector **before the unit's first cycle**. A unit's own failed cycles never become a baseline, and the committed tree only must not regress against itself in the next unit. Option B: keep the parent-commit reading, which accepts that any unit committing before its verdict can ratchet without end.
2. **Split and close.** Close the at438 unit as `checked-PASS-with-split`, or as a new checker Mode A re-judgement of `9fc937d` under Option A. AT-453 then becomes its own unit (the row above), and AT-438/442/443/445/449/450 move to `verified` only on that checker ruling.
3. **Accept AT-454 into U14(c)** as a disclosed FP class ("text slotted through a `mode:closed` shadow root into a hiding box"). It is unobservable from page script by spec, and on the FP side of the written tie-break. A CDP flat-tree walk is recorded as its only fix path, as a separate future unit.

## Preventive change to encode

- **U14(b)** needs one sentence defining the baseline as the pre-unit detector (gate item 1). Without it, every future detector unit that commits before its verdict stalls the same way.
- **C10 / manifest flow.** The maker committed before the verdict three cycles running. The ratchet ran on that, so the verify chain should refuse it rather than leave it as an "open question" in the verdicts.
- **Maker pre-flight for this module.** Before adding any computed-style check, grep `visual_order.js` for an existing measured rule (`HIDES_ON`) and apply it to every style source (element, pseudo, host). AT-453 is AT-437 again, on a pseudo.
- **AT-419** (doctor ignores `.js`) is still open, and it gates C2 on the file under the most churn.
