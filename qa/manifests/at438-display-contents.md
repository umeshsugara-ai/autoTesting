# Manifest — at438-display-contents

**Unit:** AT-438 — `visual_text` drops visible text inside `display:contents`
**Contract:** `qa/contracts/ui.md` (U13) · `qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none (issue-driven)
**Date:** 2026-09-16
**Fix cycle:** 3 of max 3 — **the last one**
**Status:** STALLED — cycle 3 FAIL (`qa/verdicts/at438-display-contents.md`, AT-453 medium: a closed `<details>` whose `::details-content` is `display:contents`/`inline` paints its body, and the check reads only its `content-visibility`; AT-454 low: closed-mode shadow `assignedSlot` is null). Max cycles reached; diagnosis at `qa/debug/at438-display-contents-cycle3.md`.
**Dual check:** no
**Issues addressed:** AT-438 (open → fixed) · **AT-442** (high, cycle-1 FAIL: the probe restarted author animations) · **AT-443** (medium, cycle-1: author `:empty` hid the probe) · **AT-445** (low, cycle-1: `appendChild` throwing / `remove()` patched), which no longer applies because nothing is inserted · **AT-449** (medium, cycle-2 FAIL: <details> judged by its tag) · **AT-450** (low, cycle-2: four false positives, fixed here too)

## Cycle 3: I swapped one hand-written list for another

The cycle-2 verdict confirmed the detector really does write nothing now, and that AT-442, AT-443
and AT-445 no longer reproduce. It then failed the unit under the new contract criterion **U14(b)**,
which ranks missed text above false positives:

> **AT-449 (medium).** The walk decides a closed `<details>` by its tag (`DETAILS && !open`), not by
> what actually hides the body. An author rule `details::details-content{content-visibility:visible}`
> (a responsive accordion expanded on desktop) paints `display:contents` text, and `visual_text`
> drops it. The cycle-1 probe reported it.

It also filed **AT-450**: four false positives that were new relative to the probe (a second
`<summary>`, a closed `<details style=display:contents>`, and a child slotted into a closed
`<details>` or a `content-visibility:hidden` box inside a shadow root).

The cause is the one this module keeps teaching. The check trusted what an element **is** (its tag,
its `open` attribute) instead of what the browser **does** with it. Authors restyle `<details>`, and
a tag can't tell you that.

### The fix is the browser's own answer, and it is measured

- **`<details>` is judged by `getComputedStyle(box, '::details-content').contentVisibility`**, not by
  `!open`. That pseudo-element holds the body, and its computed `content-visibility` is what the
  browser actually applies, including an author override. The cycle-2 checker measured that it
  matches the screenshot for closed, open, the author override, and `details{display:contents}`.
- **Only the FIRST `<summary>` is exempt** (`box.querySelector(":scope > summary")`). A second
  `<summary>` is ordinary body content.
- **The `<details>` check runs BEFORE `display:contents` ancestors are skipped**, so a closed
  `<details>` that is itself `display:contents` still hides its body.
- **The walk follows the flat tree** (`assignedSlot`, then `parentElement`, then the shadow host). A
  slot sitting inside a closed `<details>` in a shadow root hides whatever is slotted through it, and
  `parentElement` jumps straight past that.

### Scored on the checker's 60 layouts, against every earlier version

I added my candidate as a fourth version to the cycle-2 checker's own harness (`moded2.py`,
screenshot ground truth made by replacing the text node). It then ran on exactly the pages that
failed the unit:

| version | ok | false negatives | false positives |
|---|---|---|---|
| pre-AT-438 | 38/60 | 22 | 0 |
| cycle-1 probe | 55/60 | 2 | 3 |
| cycle 2 | 52/60 | 1 | 7 |
| **cycle 3** | **57/60** | **0** | 3 |

**There is no layout where cycle 3 is wrong and an earlier version is right** (computed from the
harness output). Relative to cycle 2 it fixes **AT-449** (the charged false negative) and **all four
AT-450** false positives, and it changes nothing else. The 3 layouts it still gets wrong are the
`contain:paint` / `clip-path` flex and grid boxes. That is **AT-451**, which the cycle-1 probe and
cycle 2 also get wrong, and which the checker filed as pre-existing and did not charge. It has **zero
false negatives**, the class U14(b) ranks first.

### What changed in cycle 3

- `src/autotester/browser/visual_order.js`: new `flatParent(node)`. `contentsRenders` walks the flat
  tree, judges `<details>` by `::details-content`, exempts only the first `<summary>`, and checks
  `<details>` before skipping `contents` ancestors. The `HIDES_ON` comment was shortened (every fact
  kept, including the pointer to `groundtruth.py`). The `reachOf` block, gated on AT-416, is
  **byte-identical** (diffed). **300 lines.**
- `tests/fixtures/bidi_site/cvcontents.html`: four rows. **S10** is an author-expanded accordion
  (must be reported), with the `::details-content` override scoped by id so it cannot change the
  plain closed-details row. **S11** is a second `<summary>`, **S12** is `details{display:contents}`,
  and **S13** is a slot inside a closed `<details>` in a shadow root; all three must not be reported.
- `tests/test_browser_visual_order.py`: the four sentinels are added to the test's shown and hidden
  lists. 295 lines.
- `qa/evidence/at438-display-contents/mutations.json`: **9 rows**, one per claim (below).

### Every new claim has its own mutation

| capability | falsifying edit | observed |
|---|---|---|
| visible `display:contents` text is reported (AT-438) | drop `&& !contentsRenders(el)` | KILLED |
| a closed `<details>` does not leak its body | remove the `<details>` check | KILLED |
| a `content-visibility:hidden` box does not leak | the final check always `return true` | KILLED |
| **AT-449:** `<details>` is judged by `::details-content`, not its tag | go back to `!box.open` | KILLED |
| **AT-450:** only the FIRST `<summary>` is exempt | exempt every `SUMMARY` | KILLED |
| **AT-450:** `<details>` is checked before `contents` is skipped | skip `contents` first | KILLED |
| **AT-450:** the walk follows the flat tree | `flatParent` returns `parentElement` | KILLED |
| **AT-443:** no inserted node (`:empty` cannot hide it) | the cycle-1 probe `<span>` | KILLED |
| **AT-442:** no inserted node (`:last-child` cannot restart an animation) | a non-empty probe | KILLED |

Every row is a single-hunk edit to `src/autotester/browser/visual_order.js`. Each one names the one
test that pins the behaviour, and each is killed.

## Cycle 2: my fix changed the page it was observing

The cycle-1 verdict confirmed the base fix works, and that the rejected walk-up candidate really does
leak closed `<details>` and `content-visibility:hidden` text. It then failed the unit on the claim
that observing the page leaves it unchanged:

> **AT-442 (high).** The probe `<span>` restarts author CSS animations keyed on `:last-child` /
> `:has()`. Text a reader can see **outside** the `display:contents` element is dropped, and the
> real page visibly changes. `innerHTML` stays byte-identical, so the unit's own DOM assertion
> cannot see this.

Measured on identical pages: the pre-AT-438 detector returned `SIBLING_ANIM` with the animation still
running. The probe version dropped it and reset the animation clock from 3017 to 0. It also found
**AT-443**: author rules such as `span:empty{display:none}` and `*:empty{display:none}` hide the probe
itself, which brings the AT-438 false negative back.

So the fix I kept last cycle both **changed the app under test** and **reintroduced the defect it
fixed**. Any approach that inserts a node has this problem, because author selectors can match the
node. The only reason the problem was invisible is that I asserted on `innerHTML`, which a transient
node leaves identical.

### The fix: answer the question without writing anything

`contentsRenders` now walks from the `display:contents` element up to its nearest ancestor that
**has a box**, calls `checkVisibility()` on that box, and then checks the two ways a *visible* box
hides its **own** contents: a closed `<details>` whose non-summary contents are hidden, and
`content-visibility:hidden` on a hiding display (the measured `HIDES_ON`). Ancestors above that box
are already covered by `checkVisibility()`. Nothing is created, appended or removed, so there is
nothing for author CSS to match and nothing to clean up.

This is the walk-up I rejected in cycle 1, **completed**. It failed then because it asked the box only
whether *the box itself* was visible. The two added checks are exactly the gap cycle 1 measured.

### Scored against the checker's own ground truth, not mine

The cycle-1 checker's harness (`moded.py`, 28 layouts, a screenshot ground truth made by replacing
the text node, not by recolouring it) loads the detector from a file. I pointed a copy of it at my
candidate, so the comparison uses the checker's instrument:

| | correct | `innerHTML` unchanged | author `:empty` cases | animation restarts |
|---|---|---|---|---|
| cycle-1 probe | 22/28 | 28/28 | **3 wrong** (AT-443) | **yes** (AT-442) |
| **cycle-2 walk** | **25/28** | 28/28 | all correct | **none** |

The three layouts the walk still gets wrong are the ones the checker had already classified as not
this unit's:
- `clip-path` is AT-418, pre-existing (a plain div gives the same result).
- `cv:auto` far below the fold is a limit of the screenshot method. That text is reachable by
  scrolling, so reporting it is intended.
- `opacity:0` on the `contents` element itself is AT-444, pre-existing, and wrong on the old code too.

On the checker's animation pages (`anim.py`), the walk matches the pre-AT-438 detector exactly:
`SIBLING_ANIM` and `HAS_TARGET` are both seen, and no clock restarts.

The checker's two sabotage cases (a page overriding `appendChild` to throw, and patching `remove()`
to do nothing) are now harmless, because neither method is ever called.

### Two branches I wrote were dead code, and I deleted them

The first version of the walk also checked for an unslotted light child of a shadow host and for
elements whose children never render (`<select>`, `<video>`, …). Both mutations **survived**:
removing either branch changed nothing. I measured why rather than assuming. That text is never laid
out, so every glyph measures **0 px wide** and the width guard drops it first. On the checker's 28
layouts the walk without those branches still scores **25/28**. The module already records the rule
that applies here: a check that another check always covers cannot be falsified, so it should not
exist. Both branches are gone. The fixture keeps both cases as "not reported" boundaries and credits
them to the width guard.

### What changed in cycle 2

- `src/autotester/browser/visual_order.js`: `contentsRenders` no longer inserts a probe; it walks up
  to the nearest box and checks the two contents-hiding cases. To stay under the cap, the file-header
  `WHAT THIS DOES NOT SEE` block was condensed with **every entry kept**. The `reachOf` block, which is
  gated on AT-416, is **byte-identical** to the previous commit (diffed). **298 lines.**
- `tests/fixtures/bidi_site/cvcontents.html`: adds a `:last-child`-animated sibling and a
  `span:empty{display:none}` rule (the AT-442 and AT-443 conditions), plus a script-built unslotted
  shadow child and a `<select>` child.
- `tests/test_browser_visual_order.py`: the test now reads the **animation clock** before and after the
  call and asserts it never goes backwards, with `zip(..., strict=True)` so a change in the number of
  animations also fails. It also asserts the animated sibling's text is seen. The `innerHTML`-only
  assertion is gone, because it could not see this defect. 289 lines.
- `qa/evidence/at438-display-contents/mutations.json`: now 5 rows (below).

### The test now catches the cycle-1 probe

With the committed cycle-1 probe (`c687b73`) restored in a throwaway copy, and imports confirmed to
come from that copy, the new test **fails**. Rows 4 and 5 below reintroduce two variants of the probe.
Each fails on its **own** assertion:

- **Row 4** (a probe `<span>`) fails because `CONTENTS_PLAIN_S1` is missing: `:empty` hid the probe
  (AT-443).
- **Row 5** (a probe that `:empty` cannot match) fails because `LASTCHILD_SIBLING_S7` is missing: the
  restarted animation hid the sibling (AT-442). Reproduced by hand; `CONTENTS_PLAIN_S1` is still
  present in that failure, so row 5 is not riding on row 4's defect.

## Why this one

`display:contents` text is text a reader can see, and the detector drops it. That is a **false
negative**, the error this module ranks as worse (a missed credential), so it comes before AT-440
(false positives from an incomplete allow-list) and AT-419 (doctor ignores `.js`). It is in
`paintsInk`, not the `reachOf` code gated on AT-416.

AT-438 was filed by the at429 cycle-1 checker and recorded as a strict xfail in at429 cycle 2. This
unit fixes it and removes that xfail.

## The defect

A `display:contents` element has **no box of its own**. Its children lay out as if they belonged to
its parent. `checkVisibility()` on such an element always returns **false**, because there is no box
to check, even though its text is painted. `paintsInk` calls `checkVisibility()` on the text's parent,
so any text directly inside a `contents` element was dropped.

## The first fix was wrong, and measuring showed it before it shipped

I prototyped the fix as an in-memory patch and ran it against the cases that must stay hidden as well
as the ones that must be reported. The first candidate walked up to the nearest ancestor **with a
box** and called `checkVisibility()` on that:

```
contents direct                  want=reported | OLD=dropped  WRONG | PATCHED=reported OK
contents nested twice            want=reported | OLD=dropped  WRONG | PATCHED=reported OK
contents in display:none         want=dropped  | OLD=dropped  OK    | PATCHED=dropped  OK
contents in visibility:hidden    want=dropped  | OLD=dropped  OK    | PATCHED=dropped  OK
contents in closed details       want=dropped  | OLD=dropped  OK    | PATCHED=reported WRONG
contents in cv:hidden block      want=dropped  | OLD=dropped  OK    | PATCHED=reported WRONG
```

It fixed the false negative and **created two false positives**. A closed `<details>` and a
`content-visibility:hidden` block are each **visible themselves** while hiding their **contents**, so
walking up to their box asked the wrong question. That is this module's usual mistake in the opposite
direction: a fix for a false negative that manufactures a false positive. The measurement is the only
reason it was caught before the manifest.

## The fix: ask the actual question

The real question is: **would an element placed here be visible?** The fix asks the browser exactly
that. When `checkVisibility()` fails on a `display:contents` element, a probe `<span>` is appended
**inside** it, `checkVisibility()` is called on the probe, and the probe is removed in a `finally`.
The probe inherits the context, so it is invisible inside a closed `<details>`, a
`content-visibility:hidden` block or a `display:none` ancestor, and visible otherwise:

```
contents direct                  want=reported | OLD=dropped  WRONG | PROBE=reported OK
contents nested twice            want=reported | OLD=dropped  WRONG | PROBE=reported OK
contents in display:none         want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in visibility:hidden    want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in closed details       want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in cv:hidden block      want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents with opacity:0 parent   want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
plain display:none               want=dropped  | OLD=dropped  OK    | PROBE=dropped  OK
contents in OPEN details         want=reported | OLD=dropped  WRONG | PROBE=reported OK
contents in cv:auto on-screen    want=reported | OLD=dropped  WRONG | PROBE=reported OK
```

**10/10 correct.** The old detector got **4** wrong, not the 2 AT-438 named: it also dropped `contents`
text inside an **open** `<details>` and inside on-screen `content-visibility:auto`. The prototype also
checked `document.body.innerHTML` before and after every call; it was **identical** in all 10 cases.

### This is a second write to the page, and it is disclosed as one

The module already makes one deliberate, cleaned-up write: the offscreen mirror `<span>` for form
controls, appended to `<body>`. The probe is the second, and it is more intrusive in one way: it is
appended **inside an author element**, so a page's `MutationObserver` watching that element would
see a child added and removed. Three things limit it:

- It happens only on the rare path: `checkVisibility()` has already failed **and** the element is
  `display:contents`.
- It is removed in `finally`, so an exception while measuring still leaves the page clean.
- The test asserts the page's `innerHTML` is byte-identical after the call, and a mutation that
  drops the removal is killed (row 3).

The same trade was made for the mirror span and recorded in the module.

## What changed

- `src/autotester/browser/visual_order.js`: new `contentsRenders(el)` (the probe), and the
  `checkVisibility` guard becomes `!el.checkVisibility() && !contentsRenders(el)`. To stay within the
  300-line cap, three **non-gated** comments were shortened with every fact kept (the AT-374 SVG
  note, the checkVisibility default-options note, and the helper's own comment). The `reachOf` block
  was deliberately **not** touched, because it is the code gated on AT-416. **300 lines, at the cap.**
- `tests/fixtures/bidi_site/cvcontents.html`: **new**. Two cases that must be reported and three that
  must stay hidden (the trap), each in its own spaced block.
- `tests/test_browser_visual_order.py`: one new test covering both directions plus the DOM-unchanged
  assertion. **The AT-438 strict xfail on `[contents]` is removed**; that case now passes. 282 lines.
- `qa/evidence/at438-display-contents/mutations.json`: 3 mutations.
- `qa/evidence/at429-content-visibility-hidden/mutations.json` and
  `qa/evidence/at358-visual-order-detector/mutations.json`: **one anchor each repointed** to the
  changed `checkVisibility` line. Before writing, I checked that every row keeps the same name and
  the same `kills`, and that no mutation **body** (the `new` text) references a removed identifier.
  That was the AT-409 trap, where a stale body reddened every test while the count stayed at 21/21.

## Capability coverage (each new claim → its isolating falsification)

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| visible `display:contents` text is reported (AT-438) | `test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor`, `…reported_exactly_where_it_paints[contents]` | drop `&& !contentsRenders(el)` | KILLED (row 1) |
| a closed `<details>` does not leak its contents (it is visible itself) | same test | remove the `DETAILS` check | KILLED (row 2) |
| a `content-visibility:hidden` box does not leak its contents | same test | remove the `content-visibility` check | KILLED (row 3) |
| no inserted node: author `:empty` cannot hide it (AT-443) | same test, `CONTENTS_PLAIN_S1` | reintroduce the cycle-1 probe `<span>` | KILLED (row 4) |
| no inserted node: author `:last-child` cannot restart an animation (AT-442) | same test, `LASTCHILD_SIBLING_S7` + animation clock | reintroduce a probe `:empty` cannot match | KILLED (row 5), on its own assertion |

Each row is a single-hunk edit to `src/autotester/browser/visual_order.js`, which is listed under
"What changed". **Row 2 is the rejected candidate itself**, applied as a mutation, so the manifest's
claim that walking up would have leaked is a measured result the checker can re-run, not an argument.

```
$ uv run python scripts/mutation_check.py qa/evidence/at438-display-contents/mutations.json   (cycle 3)
KILLED  AT-438 reopens: display:contents text is dropped by checkVisibility again  (pytest exit 1)
KILLED  walk-up trap: no <details> check, so a closed details (visible itself) leaks its body  (pytest exit 1)
KILLED  walk-up trap: no content-visibility check, so a cv:hidden box leaks its contents  (pytest exit 1)
KILLED  AT-449 reopens: <details> judged by its TAG (!open), so an author-expanded accordion's text is dropped  (pytest exit 1)
KILLED  AT-450: every <summary> is exempt, so a SECOND summary (really body content) leaks  (pytest exit 1)
KILLED  AT-450: display:contents is skipped BEFORE the details check, so details{display:contents} leaks  (pytest exit 1)
KILLED  AT-450: the walk follows parentElement, not the flat tree, so a slot inside a shadow-root closed details leaks  (pytest exit 1)
KILLED  AT-443: the cycle-1 probe <span> returns - author :empty hides it, visible contents text is dropped  (pytest exit 1)
KILLED  AT-442: a NON-empty probe returns - :last-child matches it and the author's animation restarts  (pytest exit 1)
9/9 mutations killed
```

## How to verify (commands + expected)

- `uv run pytest` → expected: `1323 passed, 2 skipped, 32 xfailed`. That is **one fewer xfail** than
  before, because the AT-438 xfail was removed; the 32 left are the scroll-invariance layouts.
  *(`uv run pytest -q` resolves to `-qq` and suppresses the summary line.)*
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`. Doctor does not measure `.js` files (AT-419), so count
  `visual_order.js` by hand: **300**.
- `uv run python scripts/mutation_check.py qa/evidence/at438-display-contents/mutations.json` → `9/9`
- **Regression on every spec for this module:** at429 `4/4`, at358 `21/21`, at410 `1/1`, at379 `7/7`,
  at423 `3/3`.

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ wc -l src/autotester/browser/visual_order.js
300 src/autotester/browser/visual_order.js

$ diff <(git show c687b73:…visual_order.js | sed -n '/const SCROLLS/,/function isReachable/p') <(sed -n … current)
reachOf (gated) byte-identical

$ uv run pytest "tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor" -o addopts= -q   (x3)
1 passed in 1.23s
1 passed in 1.14s
1 passed in 1.24s

$ mutation specs
at438-display-contents                 9/9 mutations killed
at429-content-visibility-hidden        4/4 mutations killed
at358-visual-order-detector            21/21 mutations killed
at410-first-glyph-content-visibility   1/1 mutations killed
at379-scrollable-pane-reachability     7/7 mutations killed
at423-scroll-invariance-probe          3/3 mutations killed

$ uv run pytest
1323 passed, 2 skipped, 32 xfailed, 1 warning in 427.44s (0:07:07)
```

The `1323` includes tests from the other maker loop, which shares this working tree. This unit adds
one test and turns one xfail into a pass.

## Live browser evidence

The unit's tests are the browser evidence: a real headless Chromium against a real HTTP server,
asserting on measured glyphs and on the page's `innerHTML`. Separately, the fix was prototyped as an
in-memory patch and measured on 10 layouts against the old detector **before** the file was edited
(tables above). That run exposed the walk-up trap and the old detector's two additional false
negatives.

No product page, template or route changed.

## What this unit does NOT do

- **It does not fix AT-440** (five hiding display types missing from the `content-visibility`
  allow-list, which leads to false positives).
- **It does not touch `reachOf`** (gated on AT-416).
- **`visual_order.js` is at exactly its 300-line cap.** The next change to this file will need to trim
  or split it. AT-419 means doctor would not warn about that, so this manifest does.
- **It does not fix AT-444** (`opacity:0` set on a `display:contents` element itself: the text still
  paints, and both old and new code drop it) or **AT-418** (`clip-path`). Both are pre-existing, and
  both show as wrong on the checker's harness for the old code too.
- **It does not fix AT-451** (a zero-height `contain:paint` / `clip-path` flex or grid box reports its hidden child). It is pre-existing and wrong in the cycle-1 probe and cycle 2 alike; these are the 3 layouts cycle 3 still gets wrong.

## Status: ready-for-check
