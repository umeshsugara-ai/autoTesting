# Verdict — at379-scrollable-pane-reachability

**Date:** 2026-09-16
**Cycle checked:** 1
**Mode:** A (unit check) + D (live feature validation)
**Bound root:** `d:/autoTesting`
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Manifest:** `qa/manifests/at379-scrollable-pane-reachability.md` (Status: ready-for-check)

## VERDICT: FAIL

The fix is real, correct on the axis it claims, and its boundary holds — I reproduced all of that
independently. It fails on one thing: **`Issues addressed: AT-379 (medium, open → fixed)` is not
true.** AT-379's own filed evidence names two directions, and this unit closes one of them.

---

## What I re-ran myself (never read from the manifest)

| command | my result | manifest's claim | match |
|---|---|---|---|
| `uv run pytest` | `1226 passed, 2 skipped, 1 warning in 199.52s`, exit 0 | `1226 passed, 2 skipped` | ✔ |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 | same | ✔ |
| `uv run autotester doctor` | `doctor: clean`, exit 0 | same | ✔ |
| `uv run pytest tests/test_browser_visual_order.py tests/test_browser_unreadable.py -o addopts= -q` | `22 passed in 2.08s` | 22 passed | ✔ |
| `uv run python scripts/mutation_check.py qa/evidence/at379-…/mutations.json` | `3/3 mutations killed`, every `claims to kill` present in `actually failed` | 3/3 | ✔ |
| `uv run python scripts/mutation_check.py qa/evidence/at358-…/mutations.json` | `21/21 mutations killed`, all attributed | 21/21 | ✔ |

---

## Criteria

### U13 — the credential guard's threat model and its edge — **HOLDS, untouched**
`git diff def642e^..def642e --name-only` lists ten paths and **none** of them is
`src/autotester/core/redact.py` or `src/autotester/ui/helpers.py`. Every in-scope class U13 makes a
floor (`fold_credential`, `_is_ignorable`, `_DEFAULT_IGNORABLE`, `ASCII_CONFUSABLES`,
`_credential_variants`, `_refuse_direction_override`) is byte-unchanged. Nothing is softened; the
unit moves the `visualOrder` detector U13 explicitly declines to discharge, which is the safe
direction.

### C2 — readable by a human and an agent — **HOLDS**
`doctor: clean`. The split is what makes it hold: `test_browser_visual_order.py` 175,
`test_browser_unreadable.py` 145, `conftest.py` 107, `visual_order.js` 272 — all under 300.

### C7 — verification is independent — **HOLDS**
Both mutation specs re-run by me, in `mutation_check.py`'s own out-of-tree sandbox, which asserts a
green baseline, a unique anchor, a real file change, `exit == 1`, and `expected ⊆ failures` on full
nodeids. 3/3 and 21/21, every claimed nodeid appearing in the attributed failure list.

**The repointed AT-358 spec — checked the way the dispatch asked, not by the count.** I diffed
`git show def642e^:qa/evidence/at358-visual-order-detector/mutations.json` against the current file
field by field. 21 rows before, 21 after; **the row-name sets are identical**; the only field that
changed anywhere is `kills`, on 10 rows, and on every one of them the change is the **file prefix
only** — `tests/test_browser_visual_order.py::X` → `tests/test_browser_unreadable.py::X` with the
test name and the parametrize id byte-identical. Zero rows were retargeted to a different test. The
spec's `tests` key went from one file to both, which `_targets()` handles and which is necessary —
running only half the split suite would let a mutation look survived. **No silent retargeting.**

### Mode A step 5 — issues addressed — **FAILS**

`AT-379`'s ledger row (line 376) states its evidence in two halves:

> `overflow:auto pane, scrollTop 0 -> only PANE_FIRST_SENTINEL_55 reported; scrollTop 296 -> only PANE_LAST_SENTINEL_66. equal_before_after=False.`

and its expected clause is *"a reader CAN scroll an overflow:auto/scroll pane and read every line."*

The `scrollTop 0` half is fixed and I verified it. **The `scrollTop 296` half still reproduces.**
Measured in my own Chromium on my own page: `#scrolled` (`overflow-y:auto`, 400×50) reports both
`PANETOP` and `PANEBOT` at rest; after `scrollTop = 602`, **`PANETOP` is dropped** and `PANEBOT`
is reported. The same on the other axis: `#hscrolled` at `scrollLeft = 1200` reports `HPRIGHT`
(on screen) and **drops `HPLEFT`**. Positive control present in every state, 0 console errors.

Cause, `src/autotester/browser/visual_order.js::isReachable`:

```js
if (rect.right + window.scrollX <= 0) return false;
if (rect.bottom + window.scrollY <= 0) return false;
```

`clipRect`'s new unbounded box never reaches these two lines, and they add only the **window's**
scroll offset — so a glyph a scrolled **pane** pushed to a negative viewport coordinate still tests
as off the document. This is **not a regression**: I ran the pre-fix JS (`def642e^`) against the
same page in a throwaway copy and `PANETOP` was dropped there too. It is an **unclosed half**
claimed as closed, and it matters for the manifest's own reason for taking this unit ahead of the
queue — the next unit wires `visual_text` into a crawl, and **a crawl scrolls panes**.

It also makes the **new** comment this unit wrote false in the same spot as the cycle-3 comment it
replaces:

> `clipRect` now answers that by refusing to report a scrollable pane as a clip at all, so by the
> time a box reaches here it really is a boundary a reader cannot cross.

The box is not the only gate here. The two document-edge lines below it are, and they are
window-scroll-only. That is the third consecutive false claim at this line, and the manifest's own
framing — *"the comment I wrote in cycle 3 asserted the opposite and was simply false"* — is the
standard I am applying.

---

## Where the fix works, and where it stops — measured, not accepted

I probed past what the maker tested, on my own pages, with a positive control on each.
Pre/post attribution comes from running `def642e^`'s and `def642e`'s `visual_order.js` against the
identical pages in a throwaway copy.

| construct | pre-fix | post-fix | judgement |
|---|---|---|---|
| horizontally scrollable pane, text off the right edge (`HSRIGHT`) | dropped | **reported** | fix works on x |
| per-axis `overflow-y:auto; overflow-x:hidden`, below-fold (`PAXBELOW`) | dropped | **reported** | per-axis claim **verified, not accepted** |
| same pane, off the right edge where x is `hidden` (`PAXRIGHT`) | dropped | dropped | per-axis edge really is per-axis |
| `overflow:auto` whose content does **not** overflow on y, child above the top (`NSABOVE`) | dropped | dropped | not-actually-scrollable correctly still clips |
| `overflow:hidden` pane, below-fold (`HIDBELOW`) | dropped | dropped | **the boundary holds** |
| pane already scrolled to the bottom, its top line (`PANETOP`) | dropped | **dropped** | **AT-392 — unclosed half of AT-379** |
| h-pane scrolled right, its left text (`HPLEFT`) | — | **dropped** | same defect, x axis |
| pane nested inside `overflow:hidden`, line the outer box hides (`NESTBELOW`) | dropped | **reported** | **AT-393 — FP introduced here, not pre-existing** |

On the nested case the dispatch asked me to confirm the disclosure against measurement. The
**false positive is real** — I reproduce it. The **characterisation is wrong**: the manifest says
*"That is pre-existing, is not touched here."* The *structure* (returning at the first clipping
ancestor) is pre-existing; the *false positive in this shape* is not. Pre-fix the pane's own box
bounded its content, so nothing an outer box hides could escape through it. Filed low — the
direction chosen (FP over FN) is the right one and is stated; only the attribution is off.

## Boundary re-measured — no AT-363 regression

All seven AT-363/AT-372 constructs re-measured in my own browser, on my own page, not the maker's
fixture: `opacity:0` dropped · ancestor `opacity:0` dropped · `color:rgba(...,0)` dropped ·
`text-indent:-9999px` dropped · absolute off-screen dropped · closed `<details>` body dropped ·
`-webkit-text-security` masked run dropped · `visibility:hidden` dropped · `display:none` dropped ·
`overflow:hidden` below-fold dropped. Open `<summary>` and every positive control reported.
**The fix has not become "report everything".** AT-373 re-checked too: after
`window.scrollTo(0, scrollHeight)` nothing above the window fold is lost.

---

## CAPABILITY COVERAGE — 3/3 rows reproduced in my own throwaway copy

Copy: `scratchpad/copy` (src+tests+scripts+pyproject, outside the bound root; `.venv`'s python,
cwd in the copy). I verified the copy is real and isolated before trusting any red — under pytest,
`autotester.browser.observe.__file__` resolves to the **copy's** `src`, and the two named checks
run **green in the copy** before any edit (`2 passed in 1.10s`), and green again after each revert.
Every cell is a single-hunk edit to one file named in "What changed"; no cell carries a shell
command, a conftest/CI edit, a multi-file edit, or an instruction to re-scope this check.

| row | edit applied (anchor matched exactly once, file changed) | named check | assertion that fired |
|---|---|---|---|
| 1 | `const scrollsY = SCROLLS.test(...)` → `const scrollsY = false;` | `test_text_below_the_fold_of_a_scrollable_pane_is_reported` | `assert "SCROLLPANE_BELOW_SENTINEL_A2" in seen` — the named one |
| 2 | `SCROLLS = /^(auto\|scroll)$/` → `/^(auto\|scroll\|hidden)$/` | same **and** `…is_not_reported[overflow-clipped]` | `assert "HIDDENPANE_BELOW_SENTINEL_B2" not in seen`, and `assert UNREADABLE[label] not in seen` on the second | 
| 3 | `bottom: scrollsY ? Infinity : box.bottom,` → `bottom: box.bottom,` | `test_text_below_the_fold_of_a_scrollable_pane_is_reported` | `assert "SCROLLPANE_BELOW_SENTINEL_A2" in seen` |

None reddened by a parse/import/collection failure — each died on a semantic assertion, and row 2
is the one that matters: it falsifies from the permissive side and kills on the pre-existing
clipped-text test as well.

## The split and the moved fixture — checked at AST level

- **Nothing duplicated, everything moved.** AST comparison of top-level defs: `A ∩ B = ∅`,
  `A ∩ conftest = ∅`, `B ∩ conftest = ∅`. The 122 lines removed from
  `test_browser_visual_order.py` reappear in `test_browser_unreadable.py`; no helper exists twice.
- **The seam is a real responsibility boundary, not a cut at line 300.** A asks "does the detector
  see what the DOM hides"; B asks "does it report what a reader cannot see". One residue:
  `test_text_that_occupies_layout_but_is_invisible_is_not_reported` (`visibility:hidden`) stayed in
  A although it is a B-shaped claim — but it is the one filter the module found *non*-redundant
  with the width test, its fixture is `invisible.html` rather than `unreadable.html`, and it is
  reasoning A's docstring carries. Not charged.
- **`page_factory` in conftest shadows, collides with, and slows nothing.** No other `page_factory`
  fixture exists in the repo; the only other files touching `serve_dir` are `test_explore_modal.py`
  and `test_explore_live.py`, neither of which references `page_factory`. It is a **lazy**
  `scope="module"` fixture — no test that does not request it pays for it, which the full-suite
  wall clock confirms (199.52 s here, 198.60 s in the manifest's pre-existing run). The one real
  residue of the move is a dead duplicate constant — **AT-394**.

## LIVE-BROWSER (Mode D)

`qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker/report.json`

My own Chromium, my own probe pages, the maker's screenshots not read. 5 page states, **36
assertions, 33 pass**, the 3 failures being AT-392 (×2, one per axis) and AT-393. Interactions, not
renders: the pane scrolled by `scrollTop`, the h-pane by `scrollLeft`, the window by `scrollTo`,
each followed by a re-measurement. **Console errors: 0 on every page state.** A positive control
(`CTLP1`/`CTLP2`) is asserted present in every single state, so no negative here is explained by
the detector returning nothing.

---

```
VERDICT: FAIL
SCOREBOARD: 3/3 contract criteria hold (U13, C2, C7) · 1/2 claims evidenced — the AT-379 issue-closure claim is not
FAILURES:
- [step 5 / AT-379] sev: high · AT-379's own filed evidence has two halves and only the scrollTop-0 half is fixed: a pane scrolled away from its origin still drops everything before its offset, on both axes (PANETOP dropped at scrollTop=602; HPLEFT dropped at scrollLeft=1200) · fix direction: isReachable's document-edge test must add the scrollable ancestor chain's accumulated offset, not only window.scrollX/Y — or defer it, name the case in WHAT THIS DOES NOT SEE, and leave AT-379 open instead of claiming it fixed · issue: AT-392
CAPABILITY-COVERAGE: 3/3 rows reproduced in a throwaway copy (green asserted in the copy before each edit; each kill attributed to the assertion the check is named for)
LIVE-BROWSER: qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker/report.json (36 assertions, 33 pass, 0 console errors, positive control in all 5 states)
ISSUES-WRITTEN: AT-392 (high), AT-393 (low), AT-394 (low) · AT-379 stays open
EXPLANATION: The code change is good and I verified every claim it makes: the per-axis handling is genuine (below-fold reported where y scrolls, off-right still dropped where x is hidden), an overflow:auto pane whose content does not overflow still clips, overflow:hidden still clips, and none of the AT-363/AT-372 constructs regressed — all re-measured in my own browser with a positive control. The mutation work is honest: 3/3 and 21/21 re-run by me, and the AT-358 repointing is a pure file-prefix move on 10 rows with every row still targeting the same named test, so no attribution was lost. What fails is narrower and specific: the manifest marks AT-379 open → fixed while half of AT-379's own filed evidence — the scrolled pane — still reproduces, because isReachable's document-edge rule is window-scroll-only and the new comment above it asserts the opposite. That is the third false claim at that line, and the crawl this detector is about to be wired into scrolls panes.
```

## For cycle 2 — the smallest thing that closes this

`isReachable` needs the scroll offset of the ancestor chain, not the window's. `clipRect` already
walks that chain and already knows which ancestors scroll; accumulating `node.scrollLeft` /
`node.scrollTop` while it walks and handing that back alongside the clip box is the cheap version.
A test that scrolls the pane and asserts `visual_text` is unchanged — the exact shape of
`test_the_result_does_not_depend_on_where_the_page_is_scrolled`, with the pane as the scroller
instead of the window — is what would have caught this, and it is one mutation away from being
non-vacuous. If you defer instead, that is a legitimate choice: say so in
`WHAT THIS DOES NOT SEE`, leave AT-379 open, and narrow the manifest's claim to the half delivered.
AT-393 and AT-394 are filed, not charged — do not spend a cycle on them.

---

# Cycle checked: 2

**Date:** 2026-09-16
**Mode:** A (unit check) + D (live feature validation)
**Bound root:** `d:/autoTesting`
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Manifest:** `qa/manifests/at379-scrollable-pane-reachability.md` (Status: ready-for-check, Fix cycle 2)

## VERDICT: FAIL

Cycle 1's charge is genuinely discharged — I reproduced both of its failures in my own browser and
both are gone. The unit then fails on the sentence it wrote in their place. `reachOf` does **not**
return "the accumulated scroll offset of the window **and** every scrollable ancestor". It returns
the window's offset plus the offset of the **nearest** one, because the walk `return`s at the first
ancestor that scrolls on one axis only — which is what an ordinary `overflow:auto` pane is. A pane
inside a scrolled pane silently drops everything before the outer offset. **That is the fourth
occurrence of the three-occurrence table this unit wrote at that very line**, and the new source
comment asserts the opposite, which is the third false comment to ship at that line in three cycles.

---

## What I re-ran myself (never read from the manifest)

| command | my result | manifest's claim | match |
|---|---|---|---|
| `uv run pytest` | `1233 passed, 2 skipped, 1 warning in 198.11s`, exit 0 | `1232 passed, 2 skipped` | exit 0 OK · count +1, see below |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 | same | OK |
| `uv run autotester doctor` | `doctor: clean`, exit 0 | same | OK |
| `uv run pytest tests/test_browser_visual_order.py tests/test_browser_unreadable.py -o addopts= -q` | `23 passed in 1.86s` | 23 passed | OK |
| `uv run python scripts/mutation_check.py qa/evidence/at379-.../mutations.json` | `5/5 mutations killed`, every `claims to kill` inside `actually failed` | 5/5 | OK |
| `uv run python scripts/mutation_check.py qa/evidence/at358-.../mutations.json` | `21/21 mutations killed` | 21/21 | count OK, **attribution NOT** — AT-409 |

The `+1` on the full suite is the other maker loop's in-flight work in this shared tree
(`tests/test_flake_probe.py` is modified on disk relative to its last commit), not this unit. Exit 0
is the signal; not charged.

---

## 1. AT-392 — the cycle-1 failures are gone. Verified, then probed past.

My own headless Chromium, my own probe pages; the maker's screenshots and evidence directories were
not read. A positive control is asserted present in **every** state, and there were **0 console
errors on every page**.

| construct | measured | judgement |
|---|---|---|
| `#scrolled` (`overflow-y:auto` 400x50) at `scrollTop=602` — cycle-1 failure | `PANETOP` **reported** (was dropped) | **FIXED** |
| `#hscrolled` (`overflow-x:auto`) at `scrollLeft=1200` — cycle-1 failure | `HPLEFT` **reported** (was dropped) | **FIXED** |
| both panes scrolled, whole-page glyph multiset | `sorted(scrolled) == sorted(at_rest)`, 106 -> 106 chars | nothing lost, nothing invented |
| pane scrolled, then **scrolled back** to 0 | result **byte-identical** to at-rest | no hysteresis |
| pane parked at a **mid** position (`scrollTop=297` of max 594) | all three sentinels reported, multiset unchanged | mid position is not a special case |
| scrollable pane inside a **non-scrollable** `overflow:hidden` box, then scrolled | multiset unchanged; `NESTBELOW` reported through the hard clip | AT-393's disclosed false positive, reproduced |
| **scrolled pane inside a scrolled pane** | `INNERTOP_SENTINEL_12` **DROPPED** | **the new defect — AT-408** |

### The nested case, measured rather than argued

`p2_nested.html`: `#outer` (`overflow:auto`, 500x120) contains `#inner` (`overflow:auto`, 300x60).
At rest all four sentinels are reported (111 chars). After `outer.scrollTop=500` and
`inner.scrollTop=400` the result is **91 chars** and `INNERTOP_SENTINEL_12` is gone. I then traced
`reachOf`'s own loop over the dropped glyph's ancestors in the live page:

```json
{"stoppedAt": "inner", "accumulatedScrollY": 400, "rectBottom": -814,
 "documentEdgeTest": -414, "neededToPass": "> 0",
 "trace": [{"tag": "P", "overflow": "visible"},
           {"tag": "DIV", "id": "inner", "overflowY": "auto",
            "scrollsX": false, "scrollsY": true, "scrollTop": 400}]}
```

`#outer`'s `scrollTop=500` is **never reached**. The cause is structural, in `reachOf`:

```js
if (scrollsX && scrollsY) continue;   // only a BOTH-axis scroller keeps walking
const clip = { ... };
return { clip, scrollX, scrollY };    // a one-axis pane ENDS the walk
```

An ordinary `overflow:auto` pane whose content overflows vertically only has `scrollsX === false`,
so it takes the `return`. Every ancestor above it — its offset **and** its clip — is invisible to
the detector. This is the same AT-355-shape false negative the unit exists to close, one level of
nesting further in, and a scrollable panel inside a scrollable panel is ordinary in exactly the
caller this detector is about to be wired into. **Charged, high.**

## 2. The fixture reasoning — half of it is true and load-bearing; the guard is not what it claims

Both halves tested in a throwaway copy of the post-change tree; the bound tree was never edited.

**The SURVIVED claim is TRUE, and the new fixture is not cargo-cult.** I moved the AT-392 test's
body onto the tall `unreadable.html`'s scrollable pane and ran it with and without the vertical
mutation (`if (scrollsY) scrollY += node.scrollTop;` -> `if (false) ...`):

```
[A] probe test on the TALL fixture, UNMUTATED:                exit 0  (1 passed)
[A] SAME probe test with the vertical mutation applied:       exit 0  (1 passed)   <- SURVIVES
[A] the SHORT-fixture AT-392 test with the same mutation:     exit 1  (1 failed)   <- KILLS
```

The maker's explanation is correct: on a tall page the window's own offset satisfies the
document-edge rule and masks the pane's contribution, and the short fixture is what isolates it.

**The `window.scrollY == 0` guard does NOT do what the manifest says it does.** The manifest: *"the
test asserts `window.scrollY == 0` before it measures — otherwise the fixture could silently drift
tall again and take the test's meaning with it."* I drifted it tall, both ways, with and without
the mutation:

| drift | unmutated | mutated | guard fired? |
|---|---|---|---|
| 2500px spacer **after** the panes | exit 0 | exit 1 (killed) | yes |
| 2500px spacer **before** the panes | exit 0 | **exit 0 — SURVIVES** | **no** |

Shape (b) is precisely the drift the manifest's own narrative names as hazard #1 — *"the pane sat
~2000px down a tall page, so scrolling it internally never pushed anything to a negative viewport
coordinate."* The panes sit below the fold, the pane's content never reaches a negative viewport y,
the document-edge rule is never consulted, the mutation survives — and `window.scrollY` is still 0,
because nothing scrolls the window, so the guard passes in silence. The guard catches hazard #2 (a
window that has been scrolled) and not hazard #1 (the panes pushed down the page), which is the one
the sentence describes. The test is correct today; the protection it is documented to carry does
not exist. **Charged, medium — AT-412.** The assertion that would actually hold the meaning is that
the pane's first line reaches a **negative viewport coordinate** once the pane is scrolled.

## 3. AT-398 — the right call in form. The severity is understated, the stated cause is wrong, and I found the real one.

Reproduced in my own browser, the guard bypassed as a string inside my own process (the tree
untouched). Instrumenting `glyphsOf`'s two guards and evaluating the detector three times on one
page load:

```
run1: ...Appendix2 ETAILSBODY_SENTINEL_77 Appendix3 ody: SECONDBODY_SENTINEL_79...
run2: ...Appendix2 DETAILSBODY_SENTINEL_77 Appendix3 body: SECONDBODY_SENTINEL_79...
run3: ...Appendix2 DETAILSBODY_SENTINEL_77 Appendix3 body: SECONDBODY_SENTINEL_79...
```

Two things the manifest's account misses. It is **not** about index 0 being a sentinel: the second
`<details>`, whose text node starts `body: `, loses its **`b`**. The workaround works only because
the sacrificed character is no longer part of the sentinel. And it happens on the **first
evaluation only**.

**The cause, from the instrumented first run:**

```json
{"i": 0, "ch": "D", "w": 0, "h": 0, "x": 0, "y": 0, "widthDrop": true, "reachDrop": false}
{"i": 1, "ch": "E", "w": 9.78, "h": 17, "x": 19.5, "y": 84, "widthDrop": false}
```

The **first** `Range.getBoundingClientRect()` inside a `content-visibility`-skipped subtree returns
an **all-zero rect**, and `glyphsOf`'s `if (rect.width === 0) continue;` drops that glyph. That same
query is what forces Chromium to lay the skipped subtree out, so index 1 onward — and every later
run — measures correctly. This is why the maker's measurement showed `w=11.5625` and no cause: the
act of measuring the glyph is what repairs it. `isReachable` is innocent (`reachDrop: false`), so
the issue's own remedy would have sent the next person hunting in the wrong function.

**It is not confined to a bypassed guard or to a fixture.** On the **unmutated, shipping** detector,
on a plain page whose only unusual feature is `content-visibility:auto` — a mainstream performance
idiom, no `<details>` anywhere:

```
run1 (shipping detector, first call): CTLP7_CONTROL_AAAspacer VAUTO_SENTINEL_91 CVAUTO_SECOND_92 ...
run2 (same page, second call):        CTLP7_CONTROL_AAAspacer CVAUTO_SENTINEL_91 CVAUTO_SECOND_92 ...
```

`CVAUTO_SENTINEL_91` ships as `VAUTO_SENTINEL_91`. Callers call once. 0 console errors.

**Judgement on the question asked: filing it was the right call, not an evasion.** It was found by a
SURVIVED mutation rather than by reading; it is named in the manifest as a workaround rather than
presented as a fix; and the maker refused to absorb a silent glyph drop in the module whose core
failure mode is exactly that. The two things still wrong with it — a stated cause measured on the
wrong run, and `medium` for a live first-call glyph drop of the AT-355 shape — are filed as
**AT-410** and not charged against this unit, because the defect predates it. One structural note
for whoever fixes it: `test_text_a_reader_cannot_see_is_not_reported[closed-details]` is a `not in`
assertion, so it is satisfied **both** by the guard working and by the glyph being dropped — the
"a check asserting a state the bug also produces" trap named in the maker's own capability-coverage
reference.

## 4. The repointed AT-358 spec — the count survived; one row's ATTRIBUTION did not

I diffed `git show fafe7e7^:qa/evidence/at358-visual-order-detector/mutations.json` against the
current file, field by field. 21 rows before, 21 after; **the row-name sets are identical**; the
`tests` key is unchanged; **no row was retargeted to a different test**. Three rows changed, and on
each the only field that moved is `old`, the anchor, `clipRect` -> `reachOf`. Good, as far as it goes.

The manifest says **four** anchors were repointed. Three were. The fourth occurrence of `clipRect`
in that spec is the one that was missed, and it is not an anchor — it is a **mutation body**:

```json
{"name": "AT-372: a masked TEXT RUN is reported in cleartext",
 "new": "      const glyphs = glyphsOf(node, clipRect(parent), true, false);"}
```

It is the only surviving `clipRect` in the repo. The function no longer exists, so the mutated
detector throws a `ReferenceError` on every page instead of reporting a masked run in cleartext.
Measured, before vs after, from the committed `mutations.out` and from my own re-run:

| | tests this mutation fails |
|---|---|
| before the rename | **1** — `...::test_a_masked_run_is_reported_as_the_bullets_it_shows`, the named one |
| now | **23** — every test in both files |

`expected <= failures` still holds, so the harness still prints `KILLED` and the headline is still
`21/21`. But C7's rule is *"a harness must attribute its kill to the test that claims the
property"*, and Mode A 4b's is *"an edit that breaks parsing, importing or loading reddens
everything and isolates nothing."* This row now proves only that the detector runs. The count a
careless reader checks is intact; the evidence under it is not. **Charged, high — AT-409.** It is
one string, and the manifest counted it and then did not change it.

Verified in the same pass and *not* a second stale reference: the `[closed-details]` row's extra
failure (`test_the_result_does_not_depend_on_where_the_page_is_scrolled`) is a real consequence of
the `body: ` fixture prefix.

## 5. AT-393 / AT-394 — both confirmed

- **AT-393.** The manifest now says the nested-clip false positive is *"INTRODUCED by this unit, not
  pre-existing"*, which is what I measured at cycle 1 and re-measured here: on
  `p5_nonscroll_clip.html`, `NESTBELOW_SENTINEL_32` is reported although the outer `overflow:hidden`
  box hides it. Disclosure now matches measurement. **Fixed.**
- **AT-394.** `grep -rn '\bSITE\b' src tests scripts` returns only `tests/crawl_fake.py`'s live
  `SITE` dict and its two real users (`crawl_fake.py:98,129`, `test_explore_blocked.py:33`). The dead
  duplicate in `tests/test_browser_visual_order.py` is gone and nothing references it. **Fixed.**

## 6. The `tests/test_flake_probe.py` residue — the repair did not restore the prior state

The disclosure says the file is *"untracked again, which is the state its own loop left it in"*. It
is untracked, and its contents on disk are byte-identical to what `fafe7e7` committed — I verified
both. The second half is false, and it cost the other loop something:

```
git log --oneline -- tests/test_flake_probe.py
  b177076  chore: untrack ...                     <- git rm --cached
  fafe7e7  fix(AT-392/393/394) ...                <- the wide `git add tests/`
  ef9e819  test(AT-386): cover the flake probe's subprocess halves
  4be4503  feat(AT-335): measure the crawl flake instead of guessing at it

git cat-file -e HEAD:tests/test_flake_probe.py     ->  ABSENT from HEAD
git cat-file -e ef9e819:tests/test_flake_probe.py  ->  present
```

The file was **tracked** before `fafe7e7` — added by the other loop at `4be4503` and extended at
`ef9e819`, whose five new tests were `/checker`-PASSed as AT-386 at `6e8681a`. What `fafe7e7` swept
in was that loop's *uncommitted* delta; `git rm --cached` then removed **the whole file** from the
repository rather than that delta. The other loop's committed, PASSed AT-386 coverage is no longer
in `HEAD`, and 285 lines of it now survive only as an untracked working-tree file, one
`git clean -fd` from gone. **Charged, medium — AT-411.** The disclosure is honest about the mistake
and wrong about the repair, and the repair is the part still owed.

---

## Criteria

### U13 — the credential guard's threat model and its edge — **HOLDS, untouched**
`git show --name-only fafe7e7` lists twelve paths and none is `src/autotester/core/redact.py` or
`src/autotester/ui/helpers.py`; both are byte-unchanged since `c1c8f63` / `eb75e61`, well before
this unit. Every class U13 makes a floor is intact. The unit moves only the `visualOrder` detector
that U13 explicitly declines to discharge, which is the safe direction.

### C2 — readable by a human and an agent — **HOLDS**
`doctor: clean`, exit 0. `visual_order.js` 297, `test_browser_unreadable.py` 197,
`test_browser_visual_order.py` 172, `conftest.py` 107 — all under 300.

### C7 — verification is independent — **FAILS**
Both specs re-run by me in `mutation_check.py`'s own out-of-tree sandbox — 5/5 and 21/21, green
baselines asserted, anchors unique, files verified changed, `exit == 1`, `expected <= failures`. The
at379 spec is sound and its five rows are precise. The at358 spec is not: its `masked TEXT RUN` row
no longer isolates anything (section 4), which is the attribution clause C7 spells out by name. A
21/21 that includes one row killing 23 tests by `ReferenceError` is the shape C7 was written to
refuse. Section 2's guard finding sits beside it: a test whose documented safeguard does not fire
against the drift it names.

### Mode A step 5 — issues addressed
- **AT-392 (high)** — genuinely **fixed**, both axes, reproduced in my own browser.
- **AT-393 (low)** — disclosure corrected to match measurement. **Fixed.**
- **AT-394 (low)** — dead constant gone, nothing references it. **Fixed.**
- **AT-398 (medium)** — correctly filed by the maker against its own work. Stays **open**; amended
  by AT-410 with the real cause and a severity raise.
- **AT-379 (medium)** — stays **open**. Its two filed halves are fixed and I verified both, but its
  `expected` clause is *"a reader CAN scroll an `overflow:auto`/`scroll` pane and read every line"*,
  and under one level of nesting that is still false (AT-408).

---

## CAPABILITY COVERAGE — 5/5 rows reproduced in my own throwaway copy

Copy: `<scratchpad>/copy` — `src` + `tests` + `scripts` + `pyproject.toml`, **outside** the bound
root, driven by `.venv`'s python with `PYTHONPATH=<copy>/src`. Isolation asserted before trusting
any red: under pytest, `autotester.browser.observe.__file__` resolves to
`...\scratchpad\copy\src\autotester\browser\observe.py`. Every row: **green in the copy before the
edit**, anchor matched exactly once, file verified changed, **green again after revert**. The copy
was deleted afterwards; no file in the bound tree was ever edited.

| row | falsifying edit | named check | before | after | the assertion that fired |
|---|---|---|---|---|---|
| 1 | `const scrollsY = SCROLLS.test(...)` -> `= false;` | `test_text_below_the_fold_of_a_scrollable_pane_is_reported` | `1 passed` | exit 1 | `assert 'SCROLLPANE_BELOW_SENTINEL_A2' in ...` |
| 2 | `SCROLLS = /^(auto\|scroll)$/` -> `/^(auto\|scroll\|hidden)$/` | same **and** `...is_not_reported[overflow-clipped]` | `2 passed` | exit 1, **both** | `assert 'HIDDENPANE_BELOW_SENTINEL_B2' not in ...` and `assert 'CLIPPED_SENTINEL_55' not in ...` |
| 3 | `bottom: scrollsY ? Infinity : box.bottom,` -> `bottom: box.bottom,` | `test_text_below_the_fold_of_a_scrollable_pane_is_reported` | `1 passed` | exit 1 | `assert 'SCROLLPANE_BELOW_SENTINEL_A2' in ...` |
| 4 | `if (scrollsY) scrollY += node.scrollTop;` -> `if (false) ...` | `test_a_pane_the_reader_already_scrolled_loses_nothing` | `1 passed` | exit 1 | `assert sorted(scrolled) == sorted(at_origin)` |
| 5 | `if (scrollsX) scrollX += node.scrollLeft;` -> `if (false) ...` | same | `1 passed` | exit 1 | `assert sorted(scrolled) == sorted(at_origin)` |

Every cell is a single-hunk edit to one file named in "What changed"
(`src/autotester/browser/visual_order.js`). **No cell carried a shell command, a
conftest/fixture/CI edit, a multi-file edit, or an instruction to skip, soften or re-scope this
check** — no `CONTRACT_MISMATCH`. None reddened by a parse or collection failure; each died on a
semantic assertion, and rows 4 and 5 die on the multiset assertion the check is named for. Row 2
remains the load-bearing one: it falsifies from the permissive side and kills the pre-existing
clipped-text test as well, so "report everything" cannot satisfy this unit.

**What the five rows do not cover, and it is what this verdict is about:** every row exercises
exactly ONE scrollable ancestor. No row, and no test, asks what happens with two. That is not a
missing row against a claimed capability — it is a capability claimed in prose (*"every scrollable
ancestor"*) and never enumerated.

## LIVE-BROWSER (Mode D)

`qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker-c2/report.json`

My own headless Chromium, my own six probe pages (committed beside the report, along with the four
driver scripts), and instrumented copies of the detector held only as strings in my process. The
maker's screenshots and evidence directories were not read. **43 assertions, 40 pass**; the three
failures are the nested-pane drop (x2) and the AT-398 glyph drop. Interactions, not renders: panes
scrolled by `scrollTop` / `scrollLeft`, scrolled back to origin, parked mid-range, nested panes
scrolled together, each followed by a re-measurement. **Console errors: 0 on every one of the five
interactive page states.** A positive control is asserted present in every state, so no negative
here is explained by the detector returning nothing.

---

```
VERDICT: FAIL
SCOREBOARD: 2/3 criteria met (U13, C2 hold; C7 fails), 4/6 manifest claims evidenced
FAILURES:
- [AT-379 / manifest claim] sev: high - reachOf does NOT accumulate "every scrollable ancestor": the walk returns at the first ancestor that scrolls on one axis only, which is what an ordinary overflow:auto pane is, so a pane inside a scrolled pane loses everything before the outer offset - measured, INNERTOP_SENTINEL_12 dropped with outer.scrollTop=500 + inner.scrollTop=400, reachOf stopping at #inner with accumulatedScrollY=400 and documentEdgeTest=-414 - fix: `continue` past a scrollable ancestor carrying the running offset AND the running clip intersection (which closes AT-393 in the same edit), returning only at a clipPath ancestor or documentElement; add a nested-pane capability row - issue: AT-408
- [C7] sev: high - the at358 spec's "AT-372: a masked TEXT RUN is reported in cleartext" row kept a stale `clipRect(` in its mutation BODY, so it now throws a ReferenceError and fails all 23 tests instead of the 1 it names; 21/21 preserved, attribution destroyed - fix: change that one string to `reachOf(parent)` and re-run, the row must fail exactly the named test again - issue: AT-409
- [C7 / test integrity] sev: medium - the AT-392 test's `window.scrollY == 0` guard does not protect it from the drift the manifest says it does: with a 2500px spacer ABOVE the panes the vertical mutation SURVIVES (exit 0) and the guard never fires, which is hazard #1 in the manifest's own narrative - fix: assert the pane's first line reaches a NEGATIVE viewport coordinate after scrolling, and keep the window.scrollY assertion beside it - issue: AT-412
- [git hygiene] sev: medium - b177076 did not restore the pre-fafe7e7 state: tests/test_flake_probe.py was TRACKED (4be4503, ef9e819 - the AT-386 work PASSed at 6e8681a) and `git rm --cached` removed the whole file from HEAD, so the other loop's committed coverage is gone from the repository and survives only as an untracked file - fix: restore the ef9e819 blob to the index with a narrow pathspec, leave that loop's uncommitted delta uncommitted, and coordinate rather than decide for it - issue: AT-411
CAPABILITY-COVERAGE: 5/5 rows reproduced in my own throwaway copy (isolation asserted, green in the copy before each edit, green again after each revert, every kill attributed to the assertion the check is named for)
LIVE-BROWSER: qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker-c2/report.json (43 assertions, 40 pass, 0 console errors on every page state, positive control in all 5 interactive states)
ISSUES-WRITTEN: AT-408 (high), AT-409 (high), AT-410 (high, amends AT-398), AT-411 (medium), AT-412 (medium) - AT-392/AT-393/AT-394 -> fixed - AT-379 and AT-398 stay open
EXPLANATION: Cycle 1's charge is discharged - I reproduced PANETOP at scrollTop=602 and HPLEFT at scrollLeft=1200 in my own browser and both are now reported, the round trip is byte-identical, a mid position is unremarkable, and the fixture reasoning is half true in the half that matters: I put the AT-392 test body against unreadable.html in a throwaway copy and the vertical mutation really does survive there while the short fixture kills it, so the new page is load-bearing rather than cargo-cult. What fails is the sentence written in place of the old one. reachOf returns at the first one-axis scrollable ancestor, so it accumulates the nearest pane's offset and not "every scrollable ancestor" as the manifest, the commit message and the new source comment all state; a scrolled pane inside a scrolled pane silently drops its earlier lines, which is the fourth occurrence of the pattern this unit's own table documents, in the module about to be wired into a crawl that scrolls panes. Separately the AT-358 repointing missed the one occurrence of clipRect that was not an anchor, converting a precise mutation into a ReferenceError that reddens all 23 tests while the 21/21 headline is untouched - the exact attribution loss C7 names - and the new test's window.scrollY guard does not fire against the drift shape the manifest credits it with. AT-398 was the right call to file rather than absorb, and I found the cause the maker could not: the first Range rect taken inside a content-visibility-skipped subtree comes back all-zero and the width guard drops that glyph, the query itself repairing the layout so every later measurement hides the evidence - and it reproduces on the unmutated shipping detector on any content-visibility:auto page, which makes it a live false negative rather than a fixture artefact.
```

## For cycle 3 — the smallest thing that closes this

Two strings and a test. In `reachOf`, stop returning at a scrollable ancestor: carry the running
`{clip, scrollX, scrollY}` and `continue` up the chain, intersecting each clip box into the running
one and adding each scroller's offset, returning only at a `clipPath` ancestor or at
`documentElement`. That closes AT-408 and AT-393 in the same edit and makes the source comment true
for the first time in three attempts. In `qa/evidence/at358-visual-order-detector/mutations.json`,
change the one remaining `clipRect(parent)` to `reachOf(parent)` and re-run — the row must fail
exactly `test_a_masked_run_is_reported_as_the_bullets_it_shows` again, not 23 tests. Add a
capability row for the nested case whose falsifying edit reddens only it, and swap the AT-392 test's
`window.scrollY == 0` guard for an assertion that the pane's first line is at a negative viewport
coordinate after scrolling (keep both). AT-410 and AT-411 are filed, not charged: AT-410 now carries
the cause, so the AT-398 fix is small — force the layout before the glyph loop, or measure, discard
and measure again — and it belongs in its own unit, not this one.
