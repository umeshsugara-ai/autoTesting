# Manifest — at423-scroll-invariance-probe

**Unit:** AT-423 — a scroll-invariance probe for `visual_text`, over generated shapes
**Contract:** `qa/contracts/core-invariants.md` (C2, C7) · `qa/contracts/ui.md` (U13, which does not
yet give this module a criterion of its own; see U14 in `qa/feedback-inbox.md`)
**Goal task:** none (issue-driven; the stall diagnosis's smallest recovery)
**Date:** 2026-09-16
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-423 (open → fixed) · AT-425 (medium, cycle-1 FAIL) · AT-426 (low, cycle-1 FAIL) ·
**measures** AT-416 and AT-417 without fixing either

## Cycle 2: I measured which shapes fail and guessed why

The cycle-1 verdict confirmed the probe itself is sound. With the xfail list emptied, exactly the
same 32 shapes failed in 5 runs out of 5, with the full suite running at the same time. In the
checker's own browser the missed text is really there for a reader. So the unit did not fail on the
instrument. It failed on the label:

> **AT-425 (medium).** The xfail list is measured, but the reason each entry carries was a guess:
> `"AT-417" if "+clip" in label else "AT-416"`. **10 of the 32 reasons were wrong.** In reality,
> AT-416 covers 20 of the failing shapes, not 10. AT-417 covers 14, not 22. Two shapes need both
> fixes.

This matters more than a mislabel usually would. The point of the unit is to turn the AT-416 gate
into a measurement, and my manifest told the gate that option A "flips 10". **It flips 18.** I had
written advice for a decision on the strength of a guess, inside a unit whose whole argument was
"measure, don't guess".

The error is concrete. `_html` puts `clip-path` on the **outermost** box. For the 8 shapes whose
outer box is `hidden`, that box does not scroll, so AT-417 cannot apply, and I labelled all 8 AT-417.

### What changed in cycle 2

- **Defects are derived from the shape's structure.** The new `_open_defects` function marks
  AT-416 when a `hidden` box sits outside an `auto` box, and AT-417 when `clip-path` sits on a box
  that scrolls. Before editing anything I checked this rule against the measured set. It predicts
  exactly the 32 failing shapes, with no extra and no missing ones. It gives AT-416 on 20, AT-417 on
  14 and both on 2, which matches the checker's own count taken by fixing each defect in turn.
- **The rule is self-checking.** Every derived defect is an `xfail(strict=True)`, so a wrong rule
  fails the run in either direction. A shape wrongly marked red XPASSes, and a shape wrongly marked
  green fails outright. It is re-verified on every run.
- **AT-426: six vacuous shapes removed.** An all-`hidden` shape on a short page gives a reader
  nothing to scroll: no scrollable box, and a window that does not move. Six such shapes passed with
  no mutation able to catch them, and I had counted them as coverage. They are gone, taking the
  corpus from 56 shapes to 50.
- **AT-426: a vacuity guard.** The test now asserts that at least one scroll state actually **moved**
  the window or a container. A shape added later that cannot scroll will fail on that assertion
  instead of joining the passing count.

Reported by pytest:

```
$ uv run pytest tests/test_browser_scroll_invariance.py -o addopts= -q -rx | uniq -c (reasons)
     18 AT-416
      2 AT-416 + AT-417
     12 AT-417
```

That is AT-416 on 20 and AT-417 on 14, which is right.

### AT-426, second half: row 2's superset was not what I said

I wrote that every extra failure in the mutation rows was "the invariance assertion, failing on
shapes that exercise the mutated line". **That was not true for row 2.** I reproduced this myself
before writing it here. I applied row 2's mutation in a throwaway copy, confirmed the imports came
from the copy, and got `18 failed, 8 passed, 24 xfailed`. **8 of the 18 failures are
`XPASS(strict)`**, which matches the checker's count.

The mutation is still correctly killed: the named shapes fail on the invariance assertion, and the
harness attributes that. But 8 of the "extra" failures come from the **other** direction. The
mutation *fixes* some AT-416 shapes by accident, so they unexpectedly pass and strict xfail turns
that into a failure. That is informative in its own right: it is a stand-in fix for AT-416 showing
up in the corpus exactly as the strict marks were meant to show a real one.

### Disclosed, not fixed: two things this corpus does not test

The checker found both. Neither is charged. I am stating them so a green corpus is not read as
covering them:

- **Sideways scrolling is never tested.** `scrollLeft = scrollWidth` does nothing, because no
  generated box is wider than its content (300 of 300 px). Horizontal reachability is covered only
  by the hand-written `scrolled_panes.html` tests from at379.
- **An outer and an inner box are never scrolled at the same time.** Each state resets everything
  and scrolls one container. A defect that appears only when two nested offsets combine would not
  show up here.

### The checker's question: committing before a verdict

The checker noted that I committed `ce90fe4` before any verdict existed, and left it as a question
rather than a charge. That is correct. The maker protocol says the maker commits after PASS, and I
have committed before dispatch all session. I did it so each checker could compare commits exactly
(`git show <sha>^`) and so the other loop could not overwrite work sitting uncommitted in a shared
tree. That is a reason, not a permission, and it is a process choice for Umesh. I have recorded it
here rather than changing course silently in the middle of a cycle.

## Why this unit exists

`at379-scrollable-pane-reachability` is **STALLED** after three cycles. The stall diagnosis
(`qa/debug/at379-scrollable-pane-reachability-cycle3.md`) put the failure on **loop design**. Across
three cycles, every command in the manifest stayed green: the suite, ruff, doctor and both mutation
specs. A real false negative still shipped every time. All five defects on that one line
(AT-373/379/392/408/416) were found by a checker driving a browser at a shape the maker had no
fixture for.

All five violate one property:

> the multiset of glyphs `visual_text` reports must not change when the window or **any** scrollable
> container is scrolled anywhere in its range.

This unit adds an instrument for that property. **It changes no `src/` file**, so it cannot change
what the detector reports. It was the diagnosis's contained, reversible recovery. It also turns the
open AT-416 direction gate into a measurement, where before it was an argument.

## What changed

- `tests/test_browser_scroll_invariance.py`: **new**, 245 lines. A generated corpus of **50** pages
  (56 in cycle 1; six vacuous shapes removed in cycle 2).
  Nesting depths 1–3 × `overflow` ∈ {auto, hidden} per level × clip-path on/off × a short or tall
  page. For each page it finds the **reader-scrollable** containers at runtime, then drives each one
  to mid and max, plus the window to the bottom. It asserts that the sorted glyph multiset matches
  the at-rest measurement.
- `qa/evidence/at423-scroll-invariance-probe/mutations.json`: 3 mutations.

**No `src/` change.** `visual_order.js` is byte-identical to `7b1f9c3`.

## Three choices, each made because the alternative was measured to fail

**1. The scrolls are performed, not computed.** Computing offsets from `getBoundingClientRect` is the
reasoning that got this line wrong five times in a row. The probe drives the browser and compares
the result.

**2. The shapes are generated, not imagined.** `scrolled_panes.html` already **is** the AT-416
shape. It could not show the defect only because its inner box does not overflow. So the shape was
on screen, and the one parameterisation chosen proved the opposite property.

**3. The corpus is deterministic, and that took two corrections to reach:**

- **The first driver measured itself.** 50 of 56 shapes came back red. The driver used
  `el.scrollTop = n` on `overflow:hidden` boxes. Chromium accepts that from a script, but no reader
  can scroll those boxes, so the detector correctly reported different text. The driver now
  enumerates only containers whose **computed** overflow is `auto`/`scroll` and whose content
  actually overflows. That is the same distinction the module under test makes.
- **The second run was flaky.** It failed 33 shapes once and 32 the next time. A scroll is committed
  asynchronously, and `visual_text` measures rects. A layout flush and a 30 ms settle are now part
  of the probe, not a retry loop. After that, **three runs in a row produced the identical set of
  32**, which I diffed rather than only counted.

## What the probe found, as measured

**18 shapes pass and 32 fail today** (cycle 2 figures; cycle 1's split below was wrong and is
corrected here). The defect on each shape is **derived from its structure**, and the strict xfail
marks check that derivation on every run:

| defect | shapes | the common feature |
|---|---|---|
| **AT-416** | **20** (18 alone + 2 with AT-417) | a `hidden` box **outside** an `auto` one: a scrollable pane inside a clipping ancestor |
| **AT-417** | **14** (12 alone + 2 with AT-416) | `clip-path` on a box that **scrolls**. Only the `auto`-outermost `+clip` shapes qualify |

AT-416 is the shape a checker found by hand in at379 cycle 3. AT-417 was filed as pre-existing and
uncharged, after a checker noticed it by **reading** the code. Here it is **measured**, and it is
the larger class of the two.

**The 32 are recorded as `xfail(strict=True)`, not accepted.** The suite stays green while the
defects are open. When either one is fixed, the unexpected PASS fails loudly, so the fix cannot land
unnoticed. `KNOWN_RED` was taken from a run, not a prediction, because predicting which shapes fail
is the reasoning that lost five times.

## Capability coverage (each new claim → its isolating falsification)

All three rows are single-hunk edits to `src/autotester/browser/visual_order.js`. That file is **not**
in "What changed", because this is a test-only unit. The contract amendment log recorded a reusable
ruling for this case in the `at357-scope-sandbox-assertions` cycle-2 verdict: a test-only unit may
mutate the module under test, provided each edit is single-hunk, touches one file and is named here.

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| a scrolled pane's own offset is honoured (AT-392 class) | `…scrolled[auto]`, `…scrolled[auto-auto]` | drop `scrollY += node.scrollTop` | KILLED (row 1) |
| offsets accumulate across nested panes (AT-408 class) | `…scrolled[auto-auto-auto]` | return at the first clipping ancestor | KILLED (row 2) |
| the document-edge test uses the accumulated offset (AT-373 class) | `…scrolled[auto]`, `…scrolled[auto-auto]` | `rect.bottom <= 0` | KILLED (row 3) |

**Disclosed: these rows kill a superset.** Each mutation reddens between 12 and 18 shapes, not only
the ones it names. That is the corpus working as intended: one regression in `reachOf` breaks every
shape that routes through it. Every named nodeid is in the attributed failure list. None of the
extra failures is a collection error or an import break. They are all the invariance assertion,
failing on shapes that exercise the mutated line. The full per-row attribution is in
`mutations.out`.

**The probe's one-sided limit.** A detector that reported every node on the page would be perfectly
scroll-invariant. So this property says nothing about false positives. It is a **floor** beneath the
"text a reader cannot see is not reported" assertions in `test_browser_unreadable.py`, never a
replacement for them. The module docstring says the same.

## How to verify (commands + expected)

- `uv run pytest` → expected: `1259 passed, 2 skipped, 32 xfailed` (six vacuous shapes removed)
  *(`uv run pytest -q` resolves to `-qq`, because `pyproject.toml` `addopts` already carries `-q`,
  and that suppresses the summary line.)*
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`. Note AT-419: doctor measures only `*.py`.
  This unit's file **is** Python, so the cap genuinely applies here (255 lines).
- `uv run pytest tests/test_browser_scroll_invariance.py` → expected: `18 passed, 32 xfailed` (50 shapes)
- **Determinism, the claim that matters most:** run the line above three times; the set must not move.
- `uv run python scripts/mutation_check.py qa/evidence/at423-scroll-invariance-probe/mutations.json`
  → expected: `3/3 mutations killed`

## Actual outputs (from maker's own run)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest tests/test_browser_scroll_invariance.py -o addopts= -q     (x2)
18 passed, 32 xfailed in 7.26s
18 passed, 32 xfailed in 7.53s
18 passed, 32 xfailed in 7.49s

$ (before the xfails were recorded, three runs, failing set diffed not counted)
(cycle 1, 56 shapes) 32 failed, 24 passed in 8.25s
32 failed, 24 passed in 7.90s
32 failed, 24 passed in 7.60s
IDENTICAL SET across runs: 32 shapes

$ uv run python scripts/mutation_check.py qa/evidence/at423-scroll-invariance-probe/mutations.json
KILLED  AT-392 class: a scrolled pane's own offset is not accumulated  (pytest exit 1)
KILLED  AT-408 class: the walk stops at the first clipping ancestor  (pytest exit 1)
KILLED  AT-373 class: the document-edge test ignores the accumulated offset  (pytest exit 1)
3/3 mutations killed

$ uv run pytest
1259 passed, 2 skipped, 32 xfailed, 1 warning in 198.14s (0:03:18)
```

The `1259` includes tests belonging to the **other maker loop**, which shares this working tree. This
unit adds 50 parametrised cases (18 passing, 32 xfail). Nothing else in the total is claimed.

## Live browser evidence

The unit's tests **are** the browser evidence: a real headless Chromium over 50 generated pages
served by a real HTTP server (50 generated pages), with performed scrolls and measured glyphs. Every generated page
carries a planted positive control, `CONTROL_QUARTERLY_REPORT`, asserted present. Without it, a
detector that returned nothing would be trivially invariant and would pass the whole corpus. Since
cycle 2, every page must also show that at least one scroll state actually moved something.

No `src/`, template or route changed, so there is no product page to open. The instrument is the
browser run.

## What this unit does NOT do

- **It fixes neither AT-416 nor AT-417.** It measures both. The AT-416 direction gate
  (`qa/gates/at416-clip-vs-reach-direction.md`) stays open for Umesh, now with data. A fix for
  option A can be judged by whether the **18** AT-416-only xfails flip to xpass, the **2** shapes that also need AT-417
  stay xfail, and **none** of the 18 passing shapes goes red. (Cycle 1 said 10 flip; see AT-425.
  AT-416 is on 20 shapes, but option A fixes only AT-416, so the 2 dual shapes keep failing.)
- **It does not write U14.** That is `/checker`'s and is in `qa/feedback-inbox.md`.
- **It does not touch AT-410** (the first-glyph drop in `content-visibility` subtrees). This
  corpus uses no `content-visibility`, so it cannot see that defect. That limit is stated here so
  a green corpus is not read as covering it.

## Status: ready-for-check
