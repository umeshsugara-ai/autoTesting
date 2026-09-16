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
