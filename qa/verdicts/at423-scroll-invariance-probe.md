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

---

# Cycle checked: 2

**Cycle checked: 2**
**Date:** 2026-09-16
**Checker:** /checker Mode A (fresh subagent, bound to `D:/autoTesting`), with Mode D. No access to the maker's reasoning beyond the manifest.
**Contract:** `qa/contracts/core-invariants.md` (C2, C7) · `qa/contracts/ui.md` (U13: not applicable, as in cycle 1)
**Commit judged:** `d4fb88c` (test file, manifest, ledger rows). `visual_order.js` untouched in the bound tree.

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (C2, C7), U13 not applicable
FAILURES: none
CAPABILITY-COVERAGE: 3/3 rows reproduced (each copy green first, 18 passed / 32 xfailed; every named nodeid failed on the invariance assertion "changed after L0:mid")
LIVE-BROWSER: qa/evidence/browser-at423-scroll-invariance-probe-2026-09-16-checker-c2/report.json (536 pages driven, 0 console errors)
ISSUES-WRITTEN: AT-427 (low), AT-428 (low); AT-423, AT-425, AT-426 moved open -> fixed
EXPLANATION: The structural rule is a real derivation, not the measured list rewritten as code. I tested it on 450 live shapes it was never fitted to (overflow scroll/clip, depth 4, clip-path on inner boxes). Each shape was attributed by stand-in fixes, and the rule mispredicted 0. On the 50, an option-A stand-in flips exactly the 18 AT-416-only shapes, leaves both dual shapes xfail and turns nothing red. That figure holds only if option A also stops clip-path ancestors from clipping. An A that edits only the overflow branch flips 10, which is filed for the gate as AT-427.
```

## What I re-ran myself (bound tree, read-only)

| command | result |
|---|---|
| `uv run pytest` (bare) | `1259 passed, 2 skipped, 32 xfailed, 1 warning in 201.91s`, matches the manifest |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean`. The file is **245** lines, so the manifest's doctor note "(255 lines)" is stale (AT-428) |
| `uv run pytest tests/test_browser_scroll_invariance.py -o addopts= -q -rx` ×3, XFAIL lines sorted and diffed | identical all three times: 32 xfail, reasons `18 AT-416 · 2 AT-416 + AT-417 · 12 AT-417`. Pass count 18 |
| `uv run python scripts/mutation_check.py qa/evidence/at423-scroll-invariance-probe/mutations.json` (self-sandboxed; asserts a green baseline) | `3/3 mutations killed`. Afterwards `git status` shows no change under `src/autotester/browser/` |

## 1. Is `_open_defects` a derivation or a lookup table? A derivation

**Method.** I used a throwaway copy of the post-change tree, green first (`18 passed, 32 xfailed`, imports confirmed from the copy). My own generator is byte-identical to the test's `_html` for outermost clip, which I asserted. It adds three extensions the rule was never fitted to:

- **OOS-values:** `overflow` ∈ {auto, hidden, **scroll**, **clip**}, depths 1–3, with at least one new value. 280 pages.
- **OOS-depth4:** four levels. 64 pages.
- **OOS-innerclip:** clip-path on L1..L(d-1), depths 2–4. 136 pages.

Each page was driven through the test's states, and `visual_text` was measured under four `visual_order.js` variants: base, option-A stand-in, AT-417 stand-in, and both. Each variant was built by anchor substitution, with the anchor asserted to match exactly once and the text asserted to have changed (C7). A shape counts as AT-416 when A alone fixes it, AT-417 when F417 alone fixes it, and both when only the pair does. Neither "fixed by either" nor "unexplained" occurred on any page.

**The structural rule, stated for any overflow value and any clip position:** AT-416 when a non-scrolling clipping box (`hidden`/`clip`) sits outside a scrolling one (`auto`/`scroll`); AT-417 when clip-path sits on a scrolling box.

| group | live pages | measured (pass · AT-416 · AT-417 · both) | rule mismatches | literal `_open_defects` mismatches |
|---|---|---|---|---|
| IN (the 50) | 50 | 18 · 18 · 12 · 2 | **0** | 0/50 |
| OOS-values | 258 (22 vacuous) | 78 · 110 · 56 · 14 | **0** | 136/258 |
| OOS-depth4 | 62 (2 vacuous) | 10 · 36 · 8 · 8 | **0** | **0/62** |
| OOS-innerclip | 130 (6 vacuous) | 26 · 36 · 20 · 48 | **0** | n/a (the code hard-codes the outermost clip) |

**Verdict on point 1.** The mechanism the docstring names predicts attribution exactly on 450 shapes it was not fitted to. The code applies unchanged at depth 4 and gets 62/62. That is a derivation, and the "self-checking" claim is not circular.

**Observation, not a failure.** The Python encoding is coupled to today's generator. It compares the literal strings `"auto"`/`"hidden"` and assumes clip-path sits at `shape[0]`. If `OVERFLOWS` gained `scroll` or `clip`, it would mispredict 136 of 258 shapes, even though `_shapes`' own docstring says `scroll` behaves as `auto` (true, measured). Strict xfail would make that loud rather than silent, so the self-check survives.

## 2. Per-defect attribution on the 50: exact, with one condition

| stand-in | flips (xfail → xpass) | newly red among the 18 passing |
|---|---|---|
| **A** (overflow and clip-path branches) | **18**, set-equal to the rule's AT-416-only set | none |
| still red under A | 14: the 12 AT-417-only shapes plus `auto-hidden-auto+clip`(±tall), i.e. **both dual shapes stay** | |
| A, overflow branch only | **10** (the non-clip AT-416 shapes) | none |
| F417 | 12 | none |
| both | 32 | none |

The manifest's figure for the gate (18 flip, 2 dual stay, 0 red) is **exact** for an option A that also stops clip-path ancestors contributing outside a scroller. The gate text for A says only that it "changes which ancestors contribute to the clip". An implementation touching only the overflow branch leaves the 8 `hidden…+clip` AT-416 shapes red. The corpus reports that correctly, since those shapes stay xfail under AT-416, but a reader judging "did A work?" by the number 18 needs the condition. Filed as **AT-427 (low)** for the gate, not charged to this unit.

## 3. The vacuity guard: adequate for what it claims

- `_MOVED` is page-level ("some state moved something"), not per-container. **Can a container under test fail to move while the window moves?** Not in this driver. `_SCROLLERS` enumerates only boxes with computed overflowY `auto`/`scroll` **and** `scrollHeight > clientHeight`, so `scrollTop = scrollHeight` always moves an enumerated box. A box that is not enumerated is, by the probe's own definition, not reader-scrollable. Measured: every shape in the 50 that has a reader-scrollable container actually moved a container. The only shapes that pass the guard on window movement alone are the 6 `hidden…+tall` shapes, which have no scroller, and mutation row 3 kills those.
- `scrollLeft` is never checked. On all 530 generated pages it **never moved** (0 of 530), so the guard claims nothing for the X axis. The manifest now discloses that sideways scrolling is untested. That is true, and the guard claims no more.
- I also added a combined state (all scrollers at max at once). It added no extra failures on any page, base or both-fixed. That is consistent with the disclosed "never scrolled together" limit, not a hidden defect.

## 4. The removed shapes: all six genuinely vacuous

Of the full product of 56, the filter `"auto" in shape or tall` removes exactly 6: `hidden`, `hidden-hidden`, `hidden-hidden-hidden`, each ±clip, short page. In my own Chromium, each has `_SCROLLERS == []`, `documentElement.scrollHeight == innerHeight == 720`, and `window.scrollY == 0` after `scrollTo(bottom)`. Nothing that exercised anything was removed, and all 50 remaining shapes moved something.

## 5. Ledger hygiene: verified clean

- `HEAD:qa/issues.jsonl` (blob `96f460c`, equal to the index entry) holds AT-423, AT-425 and AT-426 and **not** AT-424. The working tree holds AT-424.
- `git diff 47f35cb 96f460c --numstat` → `2 0`: the commit added exactly two rows and changed no other row. `git diff HEAD --numstat -- qa/issues.jsonl` → `1 0` (only AT-424).
- Line endings: 0 CR bytes in HEAD's 422 lines and 0 in the working tree, with a trailing LF. All LF, not mixed.

## 6. Committing before a verdict: the framing is right, with one gap

Raising it for Umesh rather than deciding it is correct. The maker cannot license its own deviation from "commit after PASS", and a unilateral reversal mid-cycle would also have been a decision. The reason given is plausible and bears on the shared-tree risk. Two things remain. The deviation **continued** in this cycle (`d4fb88c` was committed before this verdict), so the question is being asked while the practice carries on. And the question lives only in a manifest paragraph. Under the D-006 lesson, a question that lives off the gates path gets re-asked or lost, so it belongs in a `qa/gates/` file with an `Answered:` line. That is a maker action and is noted here, not charged.

## Capability coverage (step 4b)

The rows edit `src/autotester/browser/visual_order.js`, which is not in "What changed". This is admissible under the at357 cycle-2 test-only ruling recorded in the core-invariants amendment log: single-hunk, one file, each named. No cell is a shell command or a conftest/CI edit. I reproduced each row in its own throwaway copy, `scratchpad/mut{1,2,3}`, each green before the edit and each anchor asserted to match once and change the file:

| row | before (copy) | after | named nodeid(s) → assertion that fired |
|---|---|---|---|
| AT-392 class | 18 passed, 32 xfailed | 12 failed, 6 passed, 32 xfailed | `[auto]`, `[auto-auto]` → `AssertionError: … changed after L0:mid` |
| AT-408 class | 18 passed, 32 xfailed | 18 failed, 8 passed, 24 xfailed (10 assertion + 8 `XPASS(strict)` AT-416) | `[auto-auto-auto]` → `changed after L0:mid` |
| AT-373 class | 18 passed, 32 xfailed | 18 failed, 32 xfailed | `[auto]`, `[auto-auto]` → `changed after L0:mid` |

The guard assertion (`no scroll state moved`) fired in none of them. The cycle-2 correction about row 2's 8 XPASS(strict) is accurate. The original sentence it corrects, "They are all the invariance assertion", is **still present** in the manifest's Capability coverage section. That is AT-428 (low), together with the stale 255-line figure.

## Issues addressed

- **AT-425 → fixed.** Reasons are now derived from structure, and the derivation holds out of sample (point 1).
- **AT-426 → fixed.** The vacuous shapes are removed, the guard is added, and the X-axis and row-2 disclosures are made. A residual stale sentence is split out as AT-428.
- **AT-423 → fixed.** The probe exists, is deterministic, and turns the AT-416 gate into a measurement.
- AT-416 and AT-417 stay open (measured, not fixed), as the manifest says.
