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

---

# Verdict — at358-visual-order-detector (cycle 3)

**Date:** 2026-09-16
**Cycle checked:** 3
**Checked by:** /checker, Mode A + Mode D, fresh context, bound to `d:/autoTesting`
**Manifest:** `qa/manifests/at358-visual-order-detector.md` (Fix cycle 3 of max 3 — the last)

## VERDICT: PASS

Cycles 1 and 2 above are left byte-intact; this section is appended.

## What I re-ran myself — nothing below is read from the manifest

The unit was already committed at `acc8d4e` when I arrived, so the bound tree's `src/` and `tests/`
matched `HEAD` exactly (`git diff HEAD -- src/autotester/browser/visual_order.js
tests/test_browser_visual_order.py tests/fixtures/bidi_site` → empty).

| command | my result | manifest claimed |
|---|---|---|
| `uv run pytest` (bare — `-q` twice is `-qq` and eats the count) | `1191 passed, 2 skipped, 1 warning in 198.08s`, exit 0 | `1191 passed, 2 skipped` ✓ |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 — **see the concurrency note** | `All checks passed!` ✓ |
| `uv run autotester doctor` | `doctor: clean`, exit 0 — **see the concurrency note** | `doctor: clean` ✓ |
| `uv run python scripts/mutation_check.py qa/evidence/at358-visual-order-detector/mutations.json` | `21/21 mutations killed`, exit 0, every row attributed | `21/21` ✓ |

`tests/test_mutation_check.py` was green in my full run. **AT-357 stays open and is judged on its
own**, exactly as the manifest asks — not charged here.

### Concurrency note (this is not this unit's failure, and I checked rather than assumed)

Mid-check the shared tree went red: `ruff` reported `F821 Undefined name 'loop_status'` at
`src/autotester/cli.py:65` and `doctor` died on the same `NameError`, which also broke pytest
collection. That is the **other maker loop's uncommitted AT-368 work** — `git status` showed
`M src/autotester/cli.py` with an untracked `src/autotester/loop_status.py`, and their mtimes were
`12:12:08` and `12:12:14`, i.e. seconds before my run, against `visual_order.js` last written at
`11:55`. My full-suite, mutation and browser runs all completed **before** that edit landed.

I did not charge it and I did not edit the tree. I extracted `HEAD` (`f0632b1`) with `git archive`
into a scratch dir **outside** the bound root and re-ran both there:

```
$ git archive HEAD | tar -x -C <scratch>/at358head     # f0632b1
$ ruff check src tests scripts   -> All checks passed!   (exit 0)
$ autotester doctor              -> doctor: clean        (exit 0)
```

`HEAD` contains cycle 3 in full, so this is the unit's own state, not a baseline. C2 is evidenced.
(For the record: my first attempt copied the *working tree* instead and inherited both the broken
`cli.py` and the untracked `loop_status.py`; its 3 ruff errors and 9 doctor violations were copy
artifacts — a missing root `CLAUDE.md` and unregenerated `docs/` — and I discarded them rather than
report a red obtained from a broken copy.)

## Capability coverage — 21/21 reproduced, not read

I ran `scripts/mutation_check.py` myself. It builds its own sandbox under `%TEMP%` **outside** the
repo, asserts `exit == 0` on the unmutated copy before any mutation, refuses an anchor that does not
match exactly once, refuses a file that did not change, and requires the **named** test to appear in
that run's `FAILED` list — so a syntax-error mutation that reddens everything cannot read as a kill.
All 21 rows came back `KILLED` with `actually failed` containing `claims to kill`. The four rows the
cycle-2 FAIL bought are the ones I looked at hardest:

- **row 18** (`masked = control.type === "password"`, i.e. drop `masksText`) → killed
  `test_a_masked_run_is_reported_as_the_bullets_it_shows` **and** the password test. Worth naming:
  the password test dies here because the *masked input* on `controls.html` carries the same
  sentinel, not because of the password field. That is consistent with — and independent support
  for — the dead-branch disclosure below.
- **row 19** (walker's mask argument forced `false`) → killed, attributed.
- **row 20** (`checkVisibility` neutered) → killed `…[closed-details]`, attributed.
- **row 21** (reachability back against the VIEWPORT) → killed
  `test_the_result_does_not_depend_on_where_the_page_is_scrolled`, attributed.

**Admissibility.** Every cell is a single-hunk edit to a single file; none is a shell command, a
conftest/CI edit, a multi-file edit, or an instruction to soften my check. Two rows touch files
named in no "What changed" list — row 2 (`browser/observe.py`, the unit's own caller) and row 17
(`tests/fixtures/bidi_site/hidden.html`). Row 17 is a **fixture** edit, which the protocol flags by
default; I am not calling CONTRACT_MISMATCH on it, and the reason is on disk rather than charitable:
it is the **cycle-1 checker's own mutation**, pasted in verbatim because the cycle-1 verdict
instructed it, the manifest discloses it as the one fixture row, and the claim it falsifies ("the
bidi fixture really does store the secret reversed") is a claim *about the fixture*, so no source
edit could reach it. The fixture-edit rule exists to stop a **builder** self-servicing a row; a row
a prior checker wrote is not that. The blanket sentence is still wrong, and is filed as **AT-380**
(low).

## Mode D — I drove my own browser

Own Chromium (headed, 800x600), own probe pages, own throwaway HTTP server, and I did **not** open
the maker's screenshots. `CTRL_POSITIVE_AAA` planted on every page and seen on all six, so no
negative below is explained by the detector returning nothing.

**Evidence:** `qa/evidence/browser-at358-visual-order-detector-2026-09-16-checker-c3/report.json`
**Console errors: 1 total** — a `favicon.ico` 404 from my own throwaway server on `p1` only.
Explained. Every other page 0.

### 1. AT-373, the scroll fix — probed past where the maker stopped

The maker's test scrolls to the bottom on one axis. I probed the three cases it does not.

| probe | result |
|---|---|
| **horizontal scroll** (3000px-wide page) | byte-identical at `scrollX` 0, 2600 and 4210 |
| **mid position, not the bottom** (`scrollY` 900 of 2400) | byte-identical to top and to bottom |
| off-**document**-left text (`left:-9999px`) | correctly dropped at *every* scroll position |

So the fix is genuinely scroll-invariant on both axes and at an interior position, not just at the
one the pinning test happens to visit. `rect.right + window.scrollX` is a document coordinate and
document coordinates do not move when the window scrolls. **AT-373 is answered.**

### 2. The clipping ancestor — the maker's claim is false, and I measured it

The source says the viewport-relative clip intersection "is correct that way: a clipping ancestor
and its content scroll together." **It is not, when the container is what scrolled** — that is
precisely what scrolling a pane means. Measured on `p3_container.html`:

```
overflow:auto pane, scrollTop 0   -> "CTRL_POSITIVE_AAAPANE_FIRST_SENTINEL_55"
overflow:auto pane, scrollTop 296 -> "CTRL_POSITIVE_AAAPANE_LAST_SENTINEL_66"
equal_before_after = False
overflow:hidden pane              -> HIDDEN_PANE_SENTINEL_77 correctly absent in both
```

A credential rendering in plain type inside a scrollable pane returns a clean string — **the AT-355
shape** — and the module's own stated rule is reachability ("further down or right can be scrolled
to, so those stay"), which a scrollable pane satisfies. The `overflow:hidden` case stays correctly
dropped, so the two are distinguishable and the fix is narrow.

**I am not charging this against cycle 3, and the reason is on disk.** The clip rule is cycle-2
code, unchanged by cycle 3; the cycle-2 checker bound its own scope in this same file — *"I probed
28 constructs across 6 pages… I will not extend the list again on cycle 3 — a channel found after
this is a new issue against the next unit, not a FAIL of this one."* This is a 29th construct, not a
cycle-3 regression, and a bound a checker wrote down is not one a later checker may quietly reclaim
because the stakes changed. Filed as **AT-379** (medium) against the follow-up crawl-wiring unit —
which is the caller that will actually scroll panes, so it is also where it belongs. The false
justifying sentence travels with it in the same issue; it should be corrected, and the scrollable
pane named in the limits block, which does not name it today.

### 3. AT-372 — verified by interacting, not by looking

Clicked the `<summary>`: body absent while closed → `open=true` → `DETAILS_BODY_SENTINEL_88` now
reported. The rule discriminates on state rather than blanket-dropping `<details>`. Masking
re-verified on my own page: password value absent and rendered as 17 bullets, the
`-webkit-text-security` span and input both masked, the unmasked input on the same page still
reported.

### 4. The disclosure block — I checked whether it tells the truth

A limits block is a claim, so I measured all of it rather than reading it.

| disclosed | measured |
|---|---|
| `::before` / `::after` not seen | not seen ✓ |
| **`::marker`** — an `<ol>`'s own "1." numbering (AT-371) | "1." **not** seen, while the `<li>` text IS — same-page control ✓ |
| `<select size="4">` option text not seen | not seen ✓ |
| `<canvas>` text not seen | not seen ✓ |
| **`<svg><text>` IS seen** (AT-374's correction) | **seen** ✓ |

All five true. **AT-371 and AT-374 are answered**, and AT-374's correction was the right call — the
old entry was a false statement in the one block whose job is that a clean result is read for what
it is.

## The two things the dispatch asked me to rule on

### `checkVisibility()` default options — the maker's reason is TRUE, and I verified rather than accepted it

The source claims wider flags "would subsume the two rules below" and make their C7 kills vacuous.
If that were wrong the comment would be wrong. Measured in my own Chromium:

| element | `checkVisibility()` | with the wider flag |
|---|---|---|
| `visibility:hidden` | `true` | `{visibilityProperty:true}` → **`false`** |
| `opacity:0` element | `true` | `{opacityProperty:true}` → **`false`** |
| `opacity:1` span inside an `opacity:0` **ancestor** | `true` | `{opacityProperty:true}` → **`false`** |
| `color:transparent` | `true` | both flags → `true` (**not** subsumed) |

So `{opacityProperty:true, visibilityProperty:true}` would have subsumed the `visibility` rule, the
element-opacity rule **and** the ancestor-opacity rule — mutations 6, 12 and 13 would all have
started surviving — while leaving the zero-colour-alpha rule independent, which is why that one
correctly stays separate. The comment is accurate. Claim verified, not credited.

### The disclosed INCONCLUSIVE — C7 does NOT require deleting the `type === "password"` branch

I reproduced both halves myself.

```
$ (my own Chromium)
input[type=password]  -webkit-text-security = 'disc'
input[name=plain]     -webkit-text-security = 'none'

$ uv run python scripts/mutation_check.py <my own spec> --repo <scratch>/at358head
>>> SURVIVED  CHECKER PROBE: the type===password branch is REMOVED, masksText kept  (pytest exit 0)
    claims to kill : …::test_a_password_field_is_reported_as_the_bullets_it_shows
    actually failed: (nothing)
    SURVIVING      : …::test_a_password_field_is_reported_as_the_bullets_it_shows
                     <- INCONCLUSIVE: this mutation did not make them fail
```

(My own spec, not the maker's — the maker's spec does not contain this mutation. Green baseline
asserted by the harness before it ran.)

**Ruling: keeping it is acceptable, and deleting it would be the worse engineering call.**

1. **C7 has no delete-dead-code rule.** What C7 demands of an unreachability claim is that it
   "costs one mutation run, not one paragraph" and is "reported as INCONCLUSIVE, never as a
   justification." The maker paid the run, pasted it, and labelled it INCONCLUSIVE. That duty is
   discharged in exactly the form C7 specifies.
2. **The capability itself is still falsifiable.** Row 15 (`const masked = false`) kills both the
   password test and the masked-run test — I ran it. What is unfalsifiable is the *attribution* to
   one disjunct, not the behaviour, and the manifest says precisely that.
3. **The branch is not dead in general — it is dead in one engine.** `-webkit-text-security` is a
   vendor-prefixed property and `masksText()` is its only reader; the disjunct is load-bearing on
   any engine that does not implement password masking through it. Deleting it would stake
   credential masking on a UA-stylesheet implementation detail of Blink, on the one code path whose
   failure prints a credential in cleartext. (I could not measure a second engine — the Firefox and
   WebKit binaries are not installed here — so I state the engine-dependence from the property's
   prefix, not from a measurement I did not make.)
4. **The cycle-1 deletion was a different case and the maker's distinction is sound, not
   self-serving.** The cycle-1 tag deny-list was dead by a *measurement of layout* that holds in any
   engine — `display:none`, `<script>` and `<style>` all report zero-width rects. This one is dead
   by one vendor's stylesheet. Those are not the same kind of dead.

The one thing C7 *would* have refused is prose in place of a run, and that is not what happened.

## The four cycle-2 findings

| issue | answered? | my evidence |
|---|---|---|
| **AT-373** scroll-dependence | **yes** | scroll-invariant at `scrollX` 0/2600/4210 and `scrollY` 0/900/bottom, in my browser; row 21 killed with attribution |
| **AT-372** closed `<details>` + `-webkit-text-security` | **yes** | clicked the summary and watched the state change; masking verified on my own page; rows 18/19/20 killed |
| **AT-371** `::marker` / the generated-content class | **yes** | the block now names the class; I measured that `<ol>` numbering really is unreported while the `<li>` text is |
| **AT-374** `<svg><text>` falsely listed | **yes** | `<svg><text>` **is** reported — measured; moved under a heading that does not claim it as a capability |

## Contract criteria

| criterion | verdict | evidence |
|---|---|---|
| **U13** — the positive rendering detector `visualOrder`, owed regardless of the deny-list narrowing | **met** | the instrument measures glyph rects; there is no character deny-list anywhere in it. It is the non-enumerating instrument U13 names |
| **B4 / B7** — a credential the screen masks never reaches an observation string | **met** | my own browser: password value absent, 17 bullets present; `-webkit-text-security` masked on both a `<span>` and an `<input>`. `visual_text` has **no production caller** (`grep` over `src/` + `scripts/`: only `observe.py` defines it, only the test file calls it), so the `Redactor.scrub` / `assert_no_raw_secrets` routing really is the next unit's debt, as the manifest states — not a gap shipping today |
| **C2** — ≤300 lines/file, ≤50 lines/function, module docstring | **met** | `doctor: clean` at `HEAD`; `visual_order.js` 241 lines, `test_browser_visual_order.py` 297 |
| **C7** — independent verification, mutation duty, attribution, green baseline, INCONCLUSIVE discipline | **met** | 21/21 reproduced by me with per-row attribution and a harness-asserted green baseline; the one unfalsifiable attribution is disclosed with its run, per the clause that governs it |

## Issues

- **AT-379** (medium, open) — `visual_text`'s result is CONTAINER-scroll-dependent; text in a
  scrolled `overflow:auto`/`scroll` pane is silently dropped. Against the follow-up crawl-wiring
  unit, not against this one. Carries the correction to the false "scroll together" comment.
- **AT-380** (low, open) — the manifest's blanket "all 21 rows edit a file named in What changed" is
  wrong for rows 2 and 17. Both rows are admissible; only the sentence is.
- **AT-361, AT-371, AT-372, AT-373, AT-374** → `open` → `fixed` (2026-09-16), each re-verified by me
  rather than taken from the manifest.
- **AT-357** left open and untouched, judged on its own as the manifest asks.
- IDs were allocated by re-reading the ledger immediately before appending. **AT-376, AT-377 and
  AT-378 already existed** — the dispatch's "AT-365 through AT-374 are taken" was stale by three.
  AT-375 is open about exactly this.

## Why this is a PASS on the last cycle

All four charged findings are answered, and I confirmed each in my own browser rather than from the
manifest. The mutation discipline is the strongest in this repo and I reproduced all 21 rows with
attribution. The two claims the dispatch told me to verify rather than accept both held: the
`checkVisibility` subsumption argument is measurably true, and the dead-branch disclosure is
measurably reproducible and is the form C7 asks for. The one real divergence I found — the scrolled
overflow container — is a 29th construct outside the bound the cycle-2 checker wrote into this file,
is not a cycle-3 regression, and is filed against the unit that will first have a caller able to
trigger it.

Softening a criterion to avoid a stall would have been wrong; so would inflating a pre-existing
channel into a FAIL because it was the last cycle. Neither was necessary.
