# Stall diagnosis — at379-scrollable-pane-reachability (cycle 3)

**Skill:** `/agent-debugger`, Phases 1–2 only (read-only toward code; no `src/`, `tests/`,
`scripts/` or manifest touched by this report)
**Date:** 2026-09-16
**Bound root:** `d:/autoTesting`
**Unit:** `at379-scrollable-pane-reachability` — `Status: STALLED`, 3 of 3 fix cycles spent
**Inputs read:** `qa/manifests/at379-scrollable-pane-reachability.md` ·
`qa/verdicts/at379-scrollable-pane-reachability.md` (cycles 1–3, 916 lines) ·
`qa/gates/at416-clip-vs-reach-direction.md` · `qa/contracts/ui.md` (U13 + amendment log) ·
`qa/contracts/core-invariants.md` (C2, C3, C7) · `qa/adapter.json` ·
`src/autotester/browser/visual_order.js` · `tests/test_browser_unreadable.py` ·
`tests/fixtures/bidi_site/{unreadable,scrolled_panes}.html`

---

## Phase 1 — Failure capture

- **Session / task:** close AT-379 (`visual_text` drops text below the fold of a scrollable pane)
  before `visual_order.js` acquires its first crawl caller.
- **Goal in progress at stall:** cycle 3 answered AT-408 (walk to the top accumulating offsets) and
  AT-393 (intersect clips up the chain) in one edit to `reachOf`/`isReachable`.
- **Failure:** the AT-393 half re-opened AT-379. The running clip intersection is tested against the
  glyph's *current* viewport rect, so a scrollable pane inside any `overflow:hidden` ancestor drops
  everything below its own fold. Filed **AT-416 (high)**.
- **Last successful step:** every verify command, in all three cycles — `uv run pytest`
  (1226 → 1233 → 1235 passed), `ruff` (`All checks passed!`), `autotester doctor` (`doctor: clean`),
  and the mutation specs (3/3 → 5/5 → 7/7 for this unit; 21/21 for AT-358). The checker re-ran every
  one independently and every pasted number reproduced.
- **What actually failed:** nothing a command ran. The regression was found only by the checker
  driving its own headed Chromium over probe pages it authored (`P6`, `P7`), A/B'd against the
  pre-cycle-3 walk via `page.evaluate` in the same browser.
- **Repeated pattern:** five defects, one line, one direction. Every one a fix for a false POSITIVE
  that manufactured a false NEGATIVE of the AT-355 shape — a credential rendering in plain type
  while `visual_text` returns a clean string.

| id | the rule as written | what silently vanished | who found it |
|---|---|---|---|
| AT-373 | viewport-relative reachability test | everything above the window's fold | checker (browser) |
| AT-379 | scrollable pane's box read as a hard clip | everything below the pane's fold | checker (browser) |
| AT-392 | only `window.scrollX/scrollY` accumulated | everything before a scrolled pane's offset | checker (browser, cycle 1) |
| AT-408 | walk stopped at first one-axis scrollable ancestor | nested panes' outer offset | checker (browser, cycle 2) |
| AT-416 | outer clips intersected against the glyph's current rect | a pane inside any `overflow:hidden` card | checker (browser, cycle 3) |

- **Environment assumptions verified:** branch `master`; shared working tree with a second maker
  loop (`src/autotester/cli*.py`, `loop_status.py`, `scripts/flake_probe.py`,
  `tests/test_flake_probe.py`) — untouched by this diagnosis. `qa/debug/` exists and already holds
  the structurally identical precedent `at345-346-fold-coverage-cycle3.md`.

---

## Phase 2 — Root-cause diagnosis

### The call: **(a) LOOP DESIGN.** Not close.

Two independent lines of evidence, either of which is sufficient.

#### Evidence 1 — the verify step is structurally blind to the defect class (3 for 3)

`qa/adapter.json` `verify.commands` is exactly three shell lines: `uv run pytest -q`,
`uv run ruff check src tests scripts`, `uv run autotester doctor`. In **cycle 1, cycle 2 and cycle
3** all three were green, the unit's own mutation spec was green (3/3, 5/5, 7/7), and the AT-358
regression spec was green (21/21) — **while a real, reproducible, in-scope false negative shipped
each time.** Every single one of the five defects was found by a checker driving a browser at a
shape the maker had not written a fixture for. The instrument the loop grades with has never once
detected this defect class.

Three amplifiers of the same point:

- **`autotester doctor` never measured the artifact at all (AT-419).** `src/autotester/doctor.py`
  `_python_files()` globs `(root/"src").rglob("*.py")`; `check_file_sizes()` adds
  `(root/"tests").glob("*.py")`. `visual_order.js` is a `.js` file. `doctor: clean` printed at 316
  lines and at 287 alike. The maker spent part of cycle 3's budget on a file split to satisfy a cap
  that was never being enforced on this file.
- **The mutation harness (C7) is self-certifying here.** Capability row 1 — *"text below the fold of
  a scrollable pane is reported (AT-379)"* — has an honest mutation that genuinely kills, against a
  fixture whose pane has no clipping ancestor. The mutation, the test and the row are all green and
  the capability they name is false. C7 asserts that a sabotage was *applied and attributed*; it
  cannot assert that the fixture exercises the claim, and the checker said exactly this
  ("the row that does not isolate its claim is row 1").
- **The fixture already contained the failing shape, tuned to the one value that cannot fail it.**
  `tests/fixtures/bidi_site/scrolled_panes.html:43-48` is literally `overflow:hidden` height 40
  wrapping `overflow:auto` height 200 — the AT-416 / P7 structure. It cannot exhibit AT-416 because
  the inner box does not overflow (`scrollHeight <= clientHeight`), so `scrollsY` is false and the
  pane is correctly treated as a clip. Changing one number (inner `height:200px` → `40px`, or the
  second paragraph's `margin-top:100px` → `500px`) turns that existing fixture into the checker's
  P7 and turns cycle 3 red. The maker was looking at the shape and picked the parameterisation that
  proves the opposite property.

#### Evidence 2 — the unit has no acceptance line of its own, and the line moved every cycle

`qa/contracts/ui.md` U13 is the *credential guard's spelling threat model*. It names this module
exactly twice, both times as something it does **not** cover:

> "…and an enumeration is itself a deny-list, so this criterion does not discharge the positive
> rendering detector (`visualOrder`, the only instrument that caught AT-355 and still living in a
> checker's evidence directory) — that port is tracked as **AT-358** and is owed regardless of
> anything written here." — `qa/contracts/ui.md:237-240`

and in the amendment log: *"**Not discharged by this amendment:** the `visualOrder` positive
detector, filed as **AT-358** (medium)"* (`ui.md:441-442`). `grep -n "visual_text\|visual_order"`
over `qa/contracts/` returns **nothing**. There is no criterion anywhere stating what `visual_text`
must do.

So each cycle was judged against C2 (file size), C3 (one concept one place), C7 (mutation
discipline) — none of which is about reachability — plus the **manifest's own capability table and
the module's own docstring**, both written by the maker. The substantive charge in each cycle was
therefore a fresh construct nobody had written down as required:

| cycle | what was charged | where that requirement was written before the verdict |
|---|---|---|
| 1 | a **scrolled** pane drops its earlier lines (AT-392) | nowhere — derived from AT-379's ledger evidence string |
| 2 | a pane inside a **scrolled** pane (AT-408) | nowhere — a new construct |
| 3 | a pane inside a **clipping** ancestor (AT-416) | nowhere — a new construct |

Each charge is *correct* and each is a genuine AT-355-class defect. That is not the point. The point
is that the acceptance line was discovered by the judge, one construct per cycle, with no written
boundary telling the maker when it was done — which is non-termination by construction, whatever
the maker builds.

**This repo has already diagnosed this exact failure mode, in this exact contract file.** U13's own
rationale (`ui.md:228-232`):

> "This clause exists because the opposite happened: three fix cycles and three FAILs on one line of
> `fold_credential`, each charging a class no written criterion covered, with the boundary redrawn at
> cycle 3 on a fresh measurement (`qa/debug/at345-346-fold-coverage-cycle3.md`, gate
> `qa/gates/at355-guard-shape.md`). **A loop whose acceptance line the judge moves mid-cycle cannot
> terminate, whatever the maker builds.**"

That is a verbatim description of at379 cycles 1–3. The remedy U13 invented — write the in-scope
classes down, make charging an unlisted class an amendment rather than a measurement — was applied
to `fold_credential` (the deny-list) and **never applied to `visualOrder` (the positive detector),
which U13 explicitly left undischarged.** The stall is the predicted consequence of the half of that
fix that was never built.

#### What would have to be true for (b) EXECUTION / TOOL / ENVIRONMENT

(b) would be the right call if **either**:

1. a written property existed that covers all five defects, the maker had it, and still shipped five
   violations — i.e. the acceptance line was fixed and the reasoning failed against it; **or**
2. the instrument that caught these was unavailable to the maker, so only the checker could ever have
   found them.

Neither holds. (1) fails on the grep above — no such property is written anywhere. (2) fails harder,
and in a way that is worth being precise about: **the maker has exactly the checker's instrument.**
`tests/conftest.py::page_factory` gives real Chromium over a real HTTP server; the maker wrote
`test_a_pane_the_reader_already_scrolled_loses_nothing` and
`test_a_scrolled_pane_inside_a_scrolled_pane_loses_nothing`, which scroll panes with
`eval_on_selector` and compare `sorted(scrolled) == sorted(at_origin)` — the same technique, in the
same browser, as the checker's probes. The gap is not the instrument. It is that the maker aims the
instrument at shapes it imagined, and the defect always lives in the shape it did not.

And in the maker's favour, on the record: it did not reason its way out of its own fixture
weaknesses either — the manifest documents **six** occasions across cycles 2 and 3 where a weak
fixture was exposed by a mutation `SURVIVED` row rather than by reading the code, each one correctly
diagnosed and repaired. That is competent execution inside a loop that cannot terminate, not
incompetent execution.

**Diagnosis-table row:** *"`/outcome-grader` returns `needs_revision` every iteration → rubric too
vague OR writer can't actually satisfy criterion."* Both halves apply: the rubric for this module
does not exist, and the verify step cannot observe the criterion the verdicts actually apply.

---

## Answers to the four questions

### 1. Was the regression findable by any command the manifest lists?

**No, in all three cycles.** The manifest lists six commands (`pytest`, `ruff`, `doctor`, the
scoped browser-test run, and two mutation specs). Cycle-by-cycle, every one was green and reproduced
under the checker's independent re-run, while the charged defect was live:

| cycle | manifest commands | what actually found the defect |
|---|---|---|
| 1 | `1226 passed` · ruff clean · `doctor: clean` · 22 passed · 3/3 · 21/21 — all reproduced by the checker | checker's Chromium: `#scrolled` at `scrollTop=602` drops `PANETOP`; `#hscrolled` at `scrollLeft=1200` drops `HPLEFT` (36 assertions, 33 pass, positive control in all 5 states) |
| 2 | `1233 passed` · ruff clean · `doctor: clean` · 23 passed · 5/5 · 21/21 — all reproduced | checker's Chromium: pane-inside-scrolled-pane loses the outer offset (AT-408); plus the AT-409 dead-identifier mutation body, found by reading per-row attribution rather than the total |
| 3 | `1235 passed` · ruff clean · `doctor: clean` · 25 passed · 7/7 · 21/21 — all reproduced | checker's headed Chromium, 7 probe pages: P6/P7 card-wrapped pane (AT-416), A/B'd against the pre-cycle-3 walk in the same browser on the same DOM |

**Is that instrument available to the maker?** Yes — `page_factory`, real Chromium, and the maker
uses it. The missing thing is not access, it is a *property to point it at that does not require
imagining the failing shape first*.

### 2. Is there a single property all five defects violate?

**Yes, and it is already written in this repo three times — each time bound to one hand-authored
fixture, and only ever generalised over the window.**

> **Scroll-invariance:** the multiset of glyphs `visual_text` reports must not change when the
> window, or any scrollable container on the page, is scrolled to any position in its range.

Checked against all five:

| id | violation, as a scroll-invariance failure |
|---|---|
| AT-373 | scroll the window down → text above the fold leaves the report |
| AT-379 | pane `scrollTop 0` reports only the first line, `scrollTop 296` only the last — this is literally how AT-379 was filed: `equal_before_after=False` |
| AT-392 | pane scrolled off origin → earlier lines leave the report |
| AT-408 | outer pane scrolled → lines before the outer offset leave the report |
| AT-416 | **the checker's own P7 measurement is a scroll-invariance failure verbatim**: target line *not reported at rest*, *reported after scrolling only the inner pane* |

It is testable in a real browser **by performing the scrolls**, not by computing offsets — which is
the crucial part, because computing offsets is precisely the reasoning that has been wrong five
times. The primitive already exists: `test_the_result_does_not_depend_on_where_the_page_is_scrolled`
(window only) and the `sorted(scrolled) == sorted(at_origin)` assertion in the two pane tests. What
does not exist is the generalisation: **enumerate every scrollable container on the page at runtime
(`document.querySelectorAll('*')` filtered by `scrollHeight > clientHeight || scrollWidth >
clientWidth`), drive each through `{0, mid, max}` on each axis, and assert the reported multiset is
identical in every state.** Run over a small generated corpus of container shapes —
`{auto, scroll, hidden, clip-path}` × `{nested 1–3 deep}` × `{content overflows, does not overflow}`
× `{window scrolled, not scrolled}` — it catches a defect **without anyone having imagined the
specific failing shape**, which is the only property of it that matters here.

**Honest limit, stated so it is not oversold:** scroll-invariance is a one-sided property. A detector
that reports *everything* is perfectly scroll-invariant. It polices the false-negative half only, and
must be paired with the existing "unreachable text is not reported" assertions
(`…is_not_reported[overflow-clipped]`, the hidden-pane boundary row) which already exist and already
work. The false-negative half is the half that has failed five times, and it is the half the north
star weights as a missed credential.

Cost: one test module and one generated fixture. No production-code change. Compare with the actual
spend — three fix cycles, five defects, four verdicts, ~900 lines of verdict prose, three full-suite
runs at ~200s each per cycle.

### 3. Does U13 give this module a criterion?

**No.** U13 is titled *"The credential guard's spelling threat model is written down, and its edge
does not move"* and governs `ui/helpers.py::_refuse_unsafe_submission` and `core/redact.py`. It
mentions this module only to say it is **not** covered — the checker in cycle 1 confirmed the same
by diff: *"`git diff def642e^..def642e --name-only` lists ten paths and none of them is
`src/autotester/core/redact.py` or `src/autotester/ui/helpers.py`… U13 — HOLDS, untouched."* Quoted
in full above (`ui.md:237-240`, `ui.md:441-442`).

Yet cycle 3 marks **U13 ❌** and charges it:

> "U13 exists because an enumeration is a deny-list and the detector is the positive instrument. A
> detector that returns a clean string for a credential below the fold of a card body is that
> instrument failing at its one job."

That is sound *reasoning* and it is not a *criterion*. U13's own amendment-log text forbids exactly
this move — *"Moving a class from FILED to CHARGED is an amendment, not a measurement"* — and U13
placed `visualOrder` on the filed side by name. The acceptance line being applied to this module is
the module's docstring plus the manifest's capability table, both authored by the maker, which is
the moving line the stall is made of.

**Recommendation (a recommendation only — `qa/contracts/` belongs to `/checker`, and this report
does not edit it):** a new criterion, **U14 — the positive rendering detector**, owning
`visual_order.js` / `visual_text`, whose body is (i) the scroll-invariance property above stated as
the floor, (ii) the false-positive boundary (genuinely unreachable text is not reported) stated as
its counterweight with the north-star tie-break written down — *a false negative costs a missed
credential, a false positive costs a metric; when they conflict, prefer the false positive* — and
(iii) a `WHAT THIS DOES NOT SEE` list that is the contract's, not the module's, so widening it is an
amendment rather than a maker edit. With (iii) in place, AT-410, AT-417 and AT-418 become filed
rather than chargeable, and the loop can terminate. Criticality: this is a **new** criterion over a
module no criterion covers, softening nothing — the routine lane, on U13's own precedent.

### 4. Is the maker's escalation correct?

**Partly. The gate is correctly *opened* and wrongly *blocking*.**

Correct: refusing a fourth cycle of the same reasoning on the same line is the right call, and
saying so in a gate rather than trying again is exactly what should happen at 3 of 3.

Wrong: the gate as written blocks all recovery on a human answer, and the choice it presents is
already decided by two things on disk. (i) **Severity:** AT-416 is `high`, AT-393 is `low` — option A
trades a high false negative for a low false positive. (ii) **The tie-break is already written**, in
the module's own stated direction and in U13's rationale, and the checker, the maker and the gate's
own Recommendation section all reach A independently. A human asked to choose A here would be
re-affirming a rule the repo already wrote down, which is not a direction call.

There is also a **contained, reversible recovery that needs no answer at all**, and it is not any of
A/B/C: **build the scroll-invariance probe first, as a test-only unit.** It touches `tests/` only,
changes no shipped behaviour, is `git revert`-able in one commit, and it converts the A-vs-B choice
from a reasoning contest — which this line has lost five times out of five — into a measurement. It
also answers a question nobody can currently answer: **does option A actually close AT-416 without
re-opening AT-373 / AT-379 / AT-392 / AT-408?** Today that is an assertion; with the probe it is a
run. Given the record, an unmeasured A is the sixth confident move on this line.

**If the human does answer the gate, my evidence favours A**, for the reasons above — with one
correction to how A is described. The gate says A is "revert to the unbounded scrollable axis, as in
cycle 2". A literal revert of cycle 3 would also un-fix **AT-408**, which cycle 3 genuinely closed
(the checker's P1 three-level-nesting probe passes). The minimal form of A is narrower: **keep the
full walk and the accumulating `scrollX`/`scrollY` (AT-408 stays closed); make the clip stop
contributing at a scrollable ancestor** — i.e. `narrow()` no longer intersects past a scroller. Side
effects to book, not hide: `test_a_pane_inside_a_clipping_box_does_not_leak_past_it` and its
mutation row 7 must be retired with the behaviour they lock in, and **AT-393 flips back to `open`**.
B is worth building, but as its own unit *after* the probe exists, never as cycle 4 of this one.

---

## Smallest recovery — one `qa/QUEUE.md` row

> **AT-420 — scroll-invariance probe for `visual_text` (test-only; blocks nothing, unblocks AT-416).**
> Add one browser test module that, for each page in a small generated corpus of container shapes
> (`overflow` ∈ {auto, scroll, hidden} × `clip-path` × nesting depth 1–3 × content-overflows ∈
> {yes, no} × window-scrolled ∈ {yes, no}), enumerates every scrollable container at runtime, drives
> each through `{0, mid, max}` on each axis, and asserts the reported glyph multiset is identical in
> every state. Seed the corpus with the five known shapes (AT-373, AT-379, AT-392, AT-408, AT-416/P7
> — the last is `tests/fixtures/bidi_site/scrolled_panes.html:43-48` with the inner pane made to
> overflow) and the AT-416 case is expected RED, marked `xfail(strict=True)` against AT-416. No
> change to `src/`. Add the corpus run to the AT-358/AT-379 mutation specs' `tests` key so future
> units cannot move a nodeid out from under it.

**This step is contained and reversible, and that is not a hedge:** it writes only under `tests/`,
it cannot change what the shipping detector returns, its one new failure is declared `xfail` so the
suite stays green, and undoing it is a single `git revert` of a test-only commit. It touches none of
the second maker loop's files (`src/autotester/cli*.py`, `loop_status.py`, `scripts/flake_probe.py`,
`tests/test_flake_probe.py`).

**It does not need the human.** The gate (`qa/gates/at416-clip-vs-reach-direction.md`) should stay
open and should be **decoupled** from this row: A, B and C all become measurable once the probe
exists, and A in its minimal form — clip stops at a scroller, offsets keep walking, AT-393 back to
`open` — is the direction the evidence favours when the answer comes.

**Second row, for `/checker`, not for the maker:** U14 as recommended in Q3. Until it exists, the
next unit on this line has no acceptance line either, and the sixth defect will be found the same
way as the first five.

---

## Preventive change to encode

1. **`qa/adapter.json` `verify` cannot see this project's defect class.** Three shell commands that
   are green through five shipped false negatives is not a verify step, it is a lint step. Any unit
   whose artifact is browser-observable needs a property run, not a suite run.
2. **`autotester doctor` globs `*.py` only (AT-419).** The repo ships exactly two `.js` files
   (`visual_order.js` 287, `enumerate.js` 150); widening the glob is a one-line change. More
   important than the line cap itself: `doctor: clean` was read as coverage when it was silence.
3. **U13's termination fix was applied to the deny-list and not to the positive detector.** The
   stall is the predicted consequence. `qa/debug/at345-346-fold-coverage-cycle3.md` is the same
   report about the same failure mode one module over — that recurrence is itself the finding.
4. **A capability row whose mutation kills is not a capability that holds.** C7 proves a sabotage was
   applied and attributed; it proves nothing about whether the fixture exercises the claim. The
   manifest's capability table needs a "which shape does this fixture NOT contain" column, or C7
   needs the property-corpus companion above.
