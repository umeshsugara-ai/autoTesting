# Verdict — at358-visual-order-detector

**Date:** 2026-09-11
**Cycle checked:** 1
**Manifest:** `qa/manifests/at358-visual-order-detector.md`
**Contract:** `qa/contracts/ui.md` U13 · `qa/contracts/browser-and-secrets.md` (B4, B7) ·
`qa/contracts/core-invariants.md` (C2, C7)
**Checker evidence (produced by this checker, not read):**
`qa/evidence/browser-at358-visual-order-detector-2026-09-11-checker/`

```
VERDICT: FAIL
SCOREBOARD: 3/5 criteria met, 4/5 invariants hold
FAILURES:
- [AT-361 / U13] sev: high · AT-361 is claimed fixed, but the ledger row's own coverage set ("text
  nodes + input/textarea values + placeholder and title/alt attributes") is not met: measured,
  placeholder text renders and is not reported. Alongside it the detector is blind to ::before/
  ::after generated content, open shadow DOM (text AND controls) and same-origin <iframe> content —
  four undisclosed channels of exactly the AT-355 false-negative class. · fix: extend coverage
  (shadow roots, same-origin frames, getComputedStyle(el,'::before').content, mirror placeholder
  when value is empty) or name each as a limit the way <select> already is · issue: AT-362
- [U13 / north star] sev: medium · The detector reports six kinds of text a reader cannot see:
  opacity:0, color:transparent, text-indent:-9999px, position off-screen, overflow-clipped text in
  full, and a type=password value in cleartext while the screen shows bullets. `isRendered` tests
  one CSS property. · fix: computed opacity/colour-alpha up the ancestor chain, intersect the glyph
  rect with the viewport and the nearest clipping ancestor, skip or mask type=password · issue: AT-363
- [C7] sev: low · One of the ten tests this unit adds (`test_the_dom_calls_the_bidi_page_clean`)
  carries no mutation; C7's duty is per added test. It is reachable — the checker wrote the
  mutation and it killed on the first attempt. · fix: paste
  `checker-mutations.json` from the checker evidence dir into the unit's `mutations.json` ·
  issue: AT-364
LIVE-BROWSER: qa/evidence/browser-at358-visual-order-detector-2026-09-11-checker/report.json
ISSUES-WRITTEN: AT-362, AT-363, AT-364
EXPLANATION: The core of this unit is sound and independently reproduced — the AT-355 shape, the
AT-345 shape, the AT-361 mirror, the page-left-alone property and 10/10 attributed mutation kills
all verified by the checker's own instruments. It fails on its own disclosure: the manifest states
exactly one known limit (<select>) and the module docstring asserts the result is "what a reader
sees", and a first pass of ordinary page constructs falsified that in both directions — four
rendered-text channels reported clean, six invisible constructs reported as seen. AT-361's ledger
row names placeholder coverage explicitly, so claiming it fixed is not yet earned.
```

## What the checker re-ran (nothing below is read from the manifest)

| Command | Checker's own result |
|---|---|
| `uv run pytest -q` | exit 0 — 1174 passed, 2 skipped |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json` | `10/10 mutations killed` |
| checker's own mutation spec (`checker-mutations.json`) | `1/1 mutations killed` |

`tests/test_mutation_check.py` was green in this run; `git status` showed no concurrent maker
edit in the tree, so AT-357 neither fired nor is attributed here.

## Mode D — the checker drove its own browser

Own headless Chromium, own HTTP server, own fixture pages (`pages/` in the evidence dir), calling
`autotester.browser.observe.visual_text` directly and screenshotting each page full-page. **Every
probe page carries a planted `CONTROL_ALPHA_11` and it was reported on every one of them**, so no
negative below is the detector simply returning nothing. Console errors: 0.

### False negatives — a human sees it, the detector is silent

| Construct | Rendered | Reported |
|---|---|---|
| `::before` / `::after` content | `PSEUDOBEFORE_SECRET_44`, `PSEUDOAFTER_SECRET_45` | no |
| open shadow root (text + `<input>`) | `SHADOW_SECRET_55`, `SHADOWINPUT_SECRET_56` | no |
| same-origin `<iframe>` | `IFRAME_SECRET_77` | no |
| `placeholder` on an empty field | `PLACEHOLDER_SECRET_A6` | no |
| `canvas` `fillText` | `CANVAS_SECRET_65` | no |
| `<select>` option text | `SELECT_SECRET_A3` | no — **disclosed** |
| SVG `<text>` | `SVGTEXT_SECRET_66` | **yes** |

The cause is structural and is the thing U13 names: the port is described as "the instrument that
does not enumerate", but it enumerates twice — `createTreeWalker(document.body, SHOW_TEXT)` and
`querySelectorAll("input, textarea")`. Generated content has no text node; neither API crosses a
shadow boundary or a frame boundary; `mirrorGlyphs` early-returns on an empty `value`.

### False positives — reported, but the screenshot shows nothing

`opacity:0` · `color:transparent` · `text-indent:-9999px` · `position:absolute;left:-9999px` ·
`overflow:hidden` clipped text returned in full (`CLIPPED_SECRET_95` where the reader sees
`CLIPP`) · `type=password` returned in cleartext where the reader sees bullets.

Correctly handled, and worth recording because they were not obvious: `font-size:0`,
`display:none`, `type=hidden`, an input inside a `visibility:hidden` wrapper, and — the subtle one
— `visibility:visible` nested inside `visibility:hidden`, which renders and is correctly kept.
Reading order is genuinely reconstructed: `float:right` source `S I H T D A E R` came back
`READTHIS`, grid `order` came back `YZ` from source `ZY`, absolute positioning came back by `x`,
and `writing-mode: vertical-rl` came back top-to-bottom. `transform: scaleX(-1)` / `rotate(180deg)`
come back in flipped screen order; the glyphs themselves are mirrored and unreadable, so that is
not an exposure channel and is not charged.

The password case deserves its own sentence: the mirror copies the control's font, `direction` and
`unicode-bidi` but not its masking, so the instrument un-masks exactly the field B7 masks before a
screenshot. It is **not** a B4/B7 breach today — `visual_text` has no caller anywhere in `src/` —
but it becomes one the moment the next unit wires it into the crawl, and the wiring must route the
result through `Redactor.scrub` / `assert_no_raw_secrets`.

## The page is genuinely left alone — this part is fully earned

Scrolled to `y=2732`, focused `#f1`, selected ten characters, snapshotted, called `visual_text`,
snapshotted again: `scrollY` 2732→2732, `activeElement` `f1`→`f1`, selection `'SELECTABLE'`
unchanged, both control values unchanged, `body.children` 5→5, `body.innerHTML.length` 228→228,
leftover `body > span` count 0, and a second call returned a byte-identical string.

The `finally` was tested rather than read: on a page whose only content is one `<input>`,
`document.createRange` was replaced with a thrower so `glyphsOf` raises **inside** `mirrorGlyphs`'
`try`. `page.evaluate` propagated `Error: boom` as it should, and afterwards `body > span` was 0
with `body.innerHTML` back to the bare input. The offscreen mirror also never reaches a screenshot:
`page.evaluate` completes within one page task, and the post-call screenshot of the password page
shows bullets and no span.

## C7 — mutation run, checked by hand

10/10 killed, reproduced. Attribution verified line by line: for all ten, every nodeid in
`claims to kill` appears in `actually failed`, and every exit code is 1 (tests ran and failed —
not a collection error reading as a kill).

**The vacuity fix is real, and proven by mutation rather than by reading.** The "drops
`unicode-bidi`" mutation failed exactly one test — `test_reversal_forced_by_css_alone_is_seen`, the
case whose sentinel was changed to `MARIGOLD_LEDGER_KEY_77`. Under the old shared `SECRET` that
test could not have been the one to notice, which is precisely the defect the manifest admits.

**Looking for the same defect elsewhere in the file** (the dispatch's point 5 — a shared `SECRET`
across fixtures is the shape that hides it): no second vacuous test. `SECRET` is shared by
`plain.html`, `hidden.html`, `zerowidth.html`, `invisible.html` and two fields of `inputs.html`,
but each assertion is pinned by something the sentinel alone cannot satisfy —
`test_a_secret_in_a_form_control_value_is_seen` dies when form controls stop being measured
(mutation 7), `test_a_direction_override_...` asserts `count(SECRET) == 2`, and both
"not visible" tests carry a distinct positive control (`Quarterly report`) on the same page.
Nine of the ten tests appear in at least one attributed failure list; the tenth,
`test_the_dom_calls_the_bidi_page_clean`, appears in none, which is AT-364.

## The `<select>` limit — judging the reasoning, as asked

The reasoning holds **for U13's threat model and only there.** U13's in-scope accident is "a hurried
human pasting a credential into a text box"; a `<select>` presents a fixed authored list and cannot
be pasted into, so a credential cannot arrive there by that accident. Accepted, not charged.

It does not generalise to what `visual_text` actually is. This is an **observation** capability —
the module docstring says so: "reading other people's rendered pages is what this product does" —
and on a third-party page under test an option's text is authored by someone else and can say
anything. So the sentence is right about the guard and incomplete about the instrument; the honest
form of the limit is "option text is not measured", without the justification that makes it sound
closed. The same wording problem is what turns AT-362 from a documentation nit into a finding: a
limits section that reasons one channel closed while four others go unmentioned reads as a survey,
and it is not one.

## Issues

- **AT-362** (high, open) — four undisclosed false-negative channels, placeholder among them.
- **AT-363** (medium, open) — six false-positive constructs, password cleartext among them.
- **AT-364** (low, open) — the one added test with no mutation; the checker supplied one.
- **AT-358** stays **open**: the port landed and its core works, but the unit did not pass.
- **AT-361** stays **open**: the mirror is real and correct for non-empty `input`/`textarea`
  values, but the ledger row's own coverage set includes placeholder and `title`/`alt`.
- **AT-357** untouched — not reproduced this run, and not fixed by this unit.

## What a PASS needs next cycle

Not a rewrite. Either extend the two enumerations (shadow roots, same-origin frames, generated
content, placeholder) or write the limits down honestly in the module docstring **and** the
manifest, with the same specificity the `<select>` sentence has; handle the cheap false positives
(computed opacity, colour alpha, viewport/clip intersection, `type=password`); and add the one
missing mutation. The maker chooses between extending and disclosing — a checker charges the gap
between claim and measurement, not a scope.

---

# Verdict — at358-visual-order-detector (cycle 2)

**Date:** 2026-09-16
**Cycle checked:** 2
**Manifest:** `qa/manifests/at358-visual-order-detector.md` (Fix cycle: 2 of max 3)
**Contract:** `qa/contracts/ui.md` U13 · `qa/contracts/browser-and-secrets.md` (B4, B7) ·
`qa/contracts/core-invariants.md` (C2, C7)
**Checker evidence (produced by this checker, not read):**
`qa/evidence/browser-at358-visual-order-detector-2026-09-16-checker/`
(own pages, own server, own headless Chromium, own screenshots, own mutation re-run).
The cycle-1 checker's evidence directory was **not** opened for this verdict; the maker's
screenshots and pasted outputs were **not** read as evidence.

```
VERDICT: FAIL
SCOREBOARD: 4/5 criteria met, 4/5 invariants hold
FAILURES:
- [U13 / limits-block completeness] sev: medium · `::marker` generated content — including an
  ordinary `<ol>`'s own "1."/"2." numbering — renders and is not reported, and the limits block
  names only `::before`/`::after`. The disclosure under-names the class it discloses, so it is
  not complete for a first pass of ordinary page constructs. · fix: name the CLASS
  ("::before / ::after / ::marker generated content, including an ordinary list's numbering") or
  read `getComputedStyle(el,'::marker').content` · issue: AT-371
- [U13 / north star — false-positive rate] sev: medium · A CLOSED `<details>`'s body is returned
  as text a reader saw: `details.open === false`, `checkVisibility() === false`, the screenshot
  shows only the summary, and `DETAILSBODY_16` is in the string. Same page, same run: a
  `-webkit-text-security:disc` run renders as bullets and comes back in cleartext. Both are the
  AT-363 class on constructs AT-363 never named; neither is disclosed and neither is tested. ·
  fix: consult `Element.checkVisibility()` in the walk, or disclose both with a pinning test ·
  issue: AT-372
- [U13 / the claim vs the measurement] sev: medium · The `isReachable` rule ADDED this cycle makes
  the result depend on scroll position: on the same loaded page, `window.scrollTo(0,
  document.body.scrollHeight)` removes the positive control and everything above the viewport from
  the string. `visual_order.js:78` justifies it with "Off the left edge or above the top cannot be
  scrolled to", which is false for a page that is already scrolled. The next unit wires this into
  a crawl that scrolls. · fix: take the two scroll axes against the document rather than the
  viewport (keep the clipping-ancestor intersection, which is correct), or state that the result is
  what a reader sees AT THE CURRENT SCROLL POSITION and pin it with a test · issue: AT-373
- [I — the module's stated limits are true] sev: low · `<svg><text>` is listed under "WHAT THIS DOES
  NOT SEE", under the sentence "Each is a page where a credential could render in plain type while
  this returns a clean string". Measured independently in cycle 1 and again here: it IS reported. ·
  fix: move the manifest's own honest sentence into the module (unpinned behaviour, do not rely on
  it) or add the test that pins it and delete the entry · issue: AT-374
CAPABILITY-COVERAGE: 17/17 rows reproduced (green-before asserted in an out-of-tree sandbox,
red-after attributed to the named test)
LIVE-BROWSER: qa/evidence/browser-at358-visual-order-detector-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-371, AT-372, AT-373, AT-374
EXPLANATION: Every cycle-1 failure is genuinely answered — AT-363's six false positives and the
password are fixed and independently re-measured, AT-362's placeholder is measured and its four
named channels are now written limits, AT-364's missing mutation is row 17 and it kills. The unit
fails on the same standard cycle 1 set and not a new one: a second independent first-pass sweep over
ordinary page constructs found the limits block is not complete (`::marker`), contains one statement
measurement contradicts (`<svg><text>`), and does not mention two behaviours this cycle's own fix
introduced or left — a closed `<details>` reported as seen, and a result that silently loses
everything above the current scroll position. Three of the four close with a disclosure edit if the
maker chooses disclosure again; AT-373 is the one I would not accept as prose alone, because it is a
new false negative of the AT-355 shape created by the AT-363 fix.
```

## What the checker re-ran (nothing below is read from the manifest)

| Command | Checker's own result |
|---|---|
| `uv run pytest` | **exit 0** — `1183 passed, 2 skipped, 1 warning in 218.02s` |
| `uv run ruff check src tests scripts` | `All checks passed!` (exit 0) |
| `uv run autotester doctor` | `doctor: clean` (exit 0) |
| `uv run pytest tests/test_browser_visual_order.py -o addopts= -v` | **18 passed** in 1.67s, all named individually |
| `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json` | `17/17 mutations killed`, exit 0 — full output at `…-2026-09-16-checker/checker-mutation-rerun.out` |

The manifest's note about `-q` is correct and was confirmed: `addopts = "-q"` plus a command-line
`-q` is `-qq` and suppresses the count line. Bare `uv run pytest` prints it.

`tests/test_mutation_check.py` was green in the full run. **AT-357 stays open and is not
attributed here** — it did not fire, and not firing is not fixed.

## Capability coverage — 17/17, reproduced, not read

The unit's own harness (`scripts/mutation_check.py`) is itself the throwaway-copy mechanism this
step requires: `_sandbox()` copies `src/ tests/ scripts/ pyproject.toml conftest.py` to a fresh
`%TEMP%/mutation-check-*` **outside** the bound root, `_check_in()` **refuses to proceed unless the
unmutated copy exits 0** (`baseline is NOT green … every kill below would be meaningless`), applies
one single-hunk replacement with an `occurrences != 1` anchor guard, and scores a kill only on
`exit == 1 AND expected ⊆ failures`. I re-ran it myself against the post-change tree and read every
`claims to kill` / `actually failed` pair by hand: for all 17, every claimed nodeid appears in the
failure list. No row survived, none exited on a collection error, and the bound working tree was
never edited.

**Admissibility, checked cell by cell.** All 17 are single-hunk edits to a single file. Fifteen
target `src/autotester/browser/visual_order.js`. Two do not, and both are accounted for rather than
waved through: row 2 edits `src/autotester/browser/observe.py`, which is this unit's other source
file and was in cycle 1's "What changed" (the cycle-2 section lists only cycle-2 edits); row 17
edits `tests/fixtures/bidi_site/hidden.html`, and it is this checker role's own cycle-1 mutation,
pasted in verbatim as the cycle-1 verdict instructed — the claim it falsifies *is* a claim about the
fixture, which is why no mutation of `src/` can reach it. No cell contained a shell command, a
conftest/CI edit, a multi-file edit, or an instruction to soften or re-scope the check.

Two rows are worth naming as weak-but-honest rather than as findings: row 2 (`observe.py` returns
`inner_text("body")`) and row 5 (`return ""`) redden 13 and 16 tests respectively. They are still
attributed — the named tests are inside the failure list — but they isolate little, and the manifest
does not claim otherwise.

## Mode D — the checker drove its own browser (own pages, own server, own Chromium)

`qa/evidence/browser-at358-visual-order-detector-2026-09-16-checker/` — 6 fixture pages I wrote,
served from a throwaway `http.server`, driven in headless Chromium, calling
`autotester.browser.observe.visual_text` directly, with a full-page screenshot per page.
**Every probe page carries a planted `CONTROL_CHECKER_77` and it was reported on every one**, so no
negative below is the detector simply returning nothing. **Console errors: 0 on
`extras.html`, `falsepos.html`, `scroll.html`, `interact.html`; 1 on `disclosed.html`** — that one is
my own deliberate 404 on `<img src="/definitely-missing.png" alt="ALTTEXT_08">`, which is how the
`alt` channel is probed at all. No page produced an unexplained error.

### Interaction, not just rendering

On `interact.html` I typed and clicked rather than looked:

| Interaction | Assertion | Result |
|---|---|---|
| before typing | placeholder `PLACEHOLDERGONE_50` reported | yes — AT-362's placeholder fix, live |
| `fill("#typed", "TYPEDSECRET_52")` | typed value reported | yes |
| same | placeholder **gone** from the string | yes — the mirror follows the control's real state, it does not concatenate value+placeholder |
| `click("#reveal")` | DOM-inserted `REVEALED_51` reported | yes |
| call `visual_text` twice after that | byte-identical | yes |
| after all of it | `body > span` count | **0** — no mirror left behind |

### Cycle-1 AT-363 false positives — re-measured, all six fixed

`FPOPACITY_31` (`opacity:0`), `FPTRANSPARENT_32` (`color:transparent`), `FPRGBAZERO_33`
(`rgba(0,0,0,0)`), `FPINDENT_34` (`text-indent:-9999px`), `FPOFFSCREEN_35` (absolute off-left),
`FPCLIPPED_36_LONGTAIL` (clipped to 40px — the full string is gone, only the visible prefix
survives), `FPNESTED_37` (`opacity:0` on an ancestor), plus `FPVISHIDDEN_38`, `FPDISPLAYNONE_39`,
`FPFONTZERO_40`, `FPHIDDENINPUT_41` and `FPPASSWORD_42` (password value): **none reported**, while
the same page's control was. The regex anchored to the four-component `rgba()` form is correct:
ordinary black `rgb(0,0,0)` text is still reported, which is what the control proves on every page.

### Cycle-1 AT-362 false negatives — re-measured, all six limits hold as written

`PSEUDOBEFORE_01`, `PSEUDOAFTER_02`, `SHADOWTEXT_03`, `SHADOWINPUT_04` (an `<input>` inside an open
shadow root), `SELECTOPT_05`, `CANVASTEXT_06`, `ALTTEXT_08`, `TITLETIP_09`, `IFRAMEBODY_10`
(`src=`) and `SRCDOCTEXT_24` (`srcdoc=`): **none reported.** Each is now a named limit. I also
probed the `<select>` limit at its strongest: a `<select size="4">` renders its options
**permanently, with no interaction**, and `LISTBOXOPT_20`/`20B` and an `<optgroup label>` are all
unreported — the limit as written ("a `<select>`'s rendered option text") covers that case, so the
wording is sufficient.

`SVGTEXT_07` is **reported** — the one entry in the block that is not true. See AT-374 below.

### The seventh channel — what a fresh first pass over ordinary constructs found

Reported correctly (no gap): `<button>` text, `<input type=submit|button value>`, `<summary>`,
`<caption>`, `<output>`, `<legend>`, `<ruby><rt>`, MathML `<mi>`, a `<textarea>`'s text child and a
`<textarea>`'s placeholder.

Not reported, and **not** named by the limits block:

| Construct | Renders | In the string |
|---|---|---|
| an ordinary `<ol>`'s markers — "1.", "2." | yes (screenshot) | **no** |
| `li::marker { content: "MARKERTEXT_11 " }` | yes (`getComputedStyle(li,'::marker').content` == `"MARKERTEXT_11 "`, visible) | **no** |

That is AT-371. `::marker` has no text node, which is the same structural cause as the
`::before`/`::after` entry the block already names — so this is one word missing from a class, not a
new kind of blindness. It is nonetheless a page where a credential renders and this returns clean,
which is the block's own stated test.

Probed and NOT charged: `content:` on a plain element computes to `"CSSCONTENT_19"` but did not
render anything visible in Chromium here, so there is nothing a reader sees to miss; `<datalist>`
options and `aria-label` do not render as page text; two absolutely-positioned overlapping runs come
back interleaved glyph-by-glyph rather than missing, which is a measurement artefact of identical
`x`, not a channel.

### And the two behaviours that are neither in the block nor in a test

**A closed `<details>` (AT-372).** `details.open === false`,
`checkVisibility({checkVisibilityCSS:true,contentVisibilityAuto:true,opacityProperty:true}) ===
false`, `getComputedStyle(p).display === "block"` and `getBoundingClientRect()` still reports
`984×18` — so the glyphs pass the width filter, `paintsInk` and `isReachable`, and
`DETAILSBODY_16` lands in the result while the screenshot shows only `▶ SUMMARYTEXT_15`. A
collapsed accordion is on a very large fraction of real pages, and false-positive rate is a scored
term in the north star. Same page, same run: `-webkit-text-security:disc` renders as bullets and is
returned in cleartext — the masking case the `type === "password"` branch handles for `<input>`
only.

**Scroll dependence (AT-373).** Same loaded page, two measurements:

```
scroll 0                          -> CONTROL_CHECKER_77 yes  ABOVEFOLD_60 yes  BELOWFOLD_61 yes
after scrollTo(0, scrollHeight)   -> CONTROL_CHECKER_77 NO   ABOVEFOLD_60 NO   BELOWFOLD_61 yes
```

`isReachable` drops `rect.right <= 0 || rect.bottom <= 0`, both viewport-relative. The comment
above it — "Off the left edge or above the top cannot be scrolled to" — is true at scroll 0 and
false afterwards. I want to be exact about the charge: **cycle 1 asked for viewport intersection and
the maker supplied it**, so the mechanism is not the finding. The finding is that a new
false-negative channel of precisely the AT-355 shape now exists, is undisclosed, and is untested,
in the unit whose entire subject is that gap. The clipping-ancestor half of the same rule is correct
and separately verified: content scrolled out of an `overflow:auto` panel is dropped, and reappears
when the panel is scrolled to it.

## The two changed claims the dispatch asked me to rule on

**The `<select>` justification, withdrawn — correct, and the right call.** Cycle 1 accepted the
reasoning for U13's threat model and rejected it for the instrument, because `visual_text` reads
other people's pages where option text is authored by someone else. Removing the justification and
keeping the limit is exactly the repair. Re-measured above, including the `size="4"` listbox that
renders with no interaction at all: the limit is real and the wording covers the strong case.

**`<svg><text>` listed as NOT seen while it is reported — this is a false statement, not honest
disclosure.** The distinction I am drawing is not about the maker's motive, which is sound: there is
no test pinning it, it works by accident of SVG text nodes being text nodes, and claiming coverage
you cannot defend is the error this whole unit exists to correct. But the block is not a coverage
claim in reverse — it is prefaced by "Each is a page where a credential could render in plain type
while this returns a clean string", and for this entry that sentence is false. A reader who trusts
the block will treat an SVG-rendered credential as a hole this instrument cannot see and go build a
second one; a reader who sees SVG text in the output will conclude the block is unreliable. The
manifest already contains the honest form, word for word — "reported by accident … nothing in the
suite pins it, so claiming it would be a claim with no check behind it". That sentence belongs in
the module, under a heading that is not "what this does not see". Low severity, one-line remedy,
and I would not have charged it alone.

## Cycle-1 findings — answered?

| Finding | Answered | Evidence |
|---|---|---|
| **AT-362** placeholder half | **yes** | measured on `controls.html` and on my own `interact.html`, before and after typing |
| **AT-362** disclosure half | **yes for the four channels it named**, and the limits now live in the module | all four re-measured unreported; block present at `visual_order.js:16-28` |
| **AT-363** all six + password | **yes, every one** | own page, own screenshots, same-page control reported |
| **AT-364** missing mutation | **yes** | row 17, KILLED, attributed to `test_the_dom_calls_the_bidi_page_clean` alone |

All three are flipped `open → fixed` in `qa/issues.jsonl` with the evidence recorded. The new rows
are new rows, not reopens: none of AT-371/372/373/374 is one of the constructs those three name.

**AT-361 stays open, and it is not charged.** Its `expected` clause names the coverage set "text
nodes + input/textarea values + placeholder **and title/alt attributes**". Placeholder is now
covered and the positive-control requirement is met; `title`/`alt` are covered by disclosure
instead, which is the choice cycle 1 licensed. That makes the ledger row and the shipped instrument
disagree by intent rather than by defect — it needs a decision (re-scope the row, or extend), not a
fix cycle. I am flagging it rather than deciding it, because re-scoping a row to match what shipped
is the move a checker should never make quietly.

**AT-358 stays open** — the port exists, works, and is now well-disclosed; the unit has not PASSed.

## The structural observation, offered rather than charged

`visual_text` has **no criterion of its own**. U13 mentions it only in a parenthesis ("this
criterion does not discharge the positive rendering detector … tracked as AT-358 and is owed"), so
every cycle of this unit has been judged against the module's own docstring and the north star's
false-positive term. That is why the acceptance line looks like it moves: the only written bar is a
sentence the maker also writes. The termination device is a criterion that pins the *shape* rather
than the list — something like *"the limits block is complete as of the last independent sweep, each
entry is either pinned by a test or explicitly marked unpinned, and a new channel found later is a
new issue rather than a FAIL of the unit that disclosed honestly"*. I am **not** amending the
contract toward a pending verdict. I am recording the proposal so it can be decided after this
verdict is closed, which is where an amendment belongs.

## What a PASS needs in cycle 3

Bounded, and I am stating the bound so this can terminate: **the sweep above is finished.** I probed
28 constructs across 6 pages and four of them produced findings; I will not extend the list again on
cycle 3, and a channel found after this is a new issue against the next unit, not a FAIL of this one.

1. **AT-371** — one word in the limits block (name the generated-content class, `::marker` included,
   and say that an ordinary list's numbering is an instance). Disclosure is acceptable.
2. **AT-374** — move the manifest's own sentence about `<svg><text>` into the module and out of
   "what this does not see". Disclosure is acceptable.
3. **AT-372** — a closed `<details>` and `-webkit-text-security`. Disclosure is acceptable **with a
   test that pins the current behaviour**, because this one is a false positive against a north-star
   term and an untested disclosure decays into folklore. `Element.checkVisibility()` is the cheap
   code fix if the maker prefers it.
4. **AT-373** — prose alone is not enough here. Either take the two scroll axes against the document,
   or state the scroll-0 precondition **and** add a test that fails if a later change makes the
   result silently scroll-dependent in a different way. This is a new false negative of the AT-355
   shape in the instrument built to close AT-355, and the next unit wires it into a crawl that
   scrolls.

Nothing else. The core is sound, independently reproduced twice now, and the mutation discipline on
this unit is the strongest in the repo.
