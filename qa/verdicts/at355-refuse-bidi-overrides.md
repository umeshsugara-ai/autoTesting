# Verdict — at355-refuse-bidi-overrides

**Cycle checked: 1**
**Date:** 2026-09-11 · **Checker:** Mode A + Mode D, fresh context, bound to `d:/autoTesting`
**Contract:** `qa/contracts/ui.md` U8/U9 (and U13, folded by a concurrent checker while this check
ran) · `qa/contracts/core-invariants.md` C2, C7
**Manifest:** `qa/manifests/at355-refuse-bidi-overrides.md` (`Fix cycle: 1`, `ready-for-check`)

## VERDICT: PASS

```
SCOREBOARD: 2/2 criteria met, 2/2 invariants hold
LIVE-BROWSER: qa/evidence/browser-at355-refuse-bidi-overrides-2026-09-11-checker/report.json
ISSUES-WRITTEN: AT-360, AT-361 (both filed, neither charged); AT-355 (ui) open→verified
```

## Scope, and why AT-349/AT-352 are not charged here

The dispatch and `qa/gates/at355-guard-shape.md` both settle this: option C plus the narrow half
of A. While this check ran, a concurrent checker folded the threat model into `ui.md` as **U13**,
which now names the override refusal **in scope** and names base64/hex/entities/double-encoding/
plain reversal/exotic homoglyphs/combining marks **out of scope, filed never charged**, and states
that moving a class from filed to charged is an amendment rather than a measurement.

I agree with that reasoning and have nothing to raise against it. The load-bearing half is the
asymmetry the gate identified: the out-of-scope spellings must be *constructed from* the credential,
so their author read it out of `.env` first. I record one caveat for whoever revisits U13, as a
recommendation and not a finding: "already holds the value" is sound for a human adversary, but this
product's own agents write `cases.jsonl`, and an agent that has resolved a placeholder *does* hold
the value while still writing to a tracked file by accident. That argues for the rendering detector
(AT-358/AT-361) rather than for re-opening any enumeration, which is where U13 already points.

## What I re-ran myself (nothing below is read from the manifest)

| Command | My result | Manifest claimed |
|---|---|---|
| `uv run pytest -q` | **exit 0**, 0 failures, 2 skipped | `2 failed, 1162 passed`, blamed on AT-357 |
| `uv run ruff check src tests scripts` | `All checks passed!` | same |
| `uv run autotester doctor` | `doctor: clean` | same |
| `uv run python scripts/mutation_check.py qa/evidence/at355-refuse-bidi-overrides/mutations.json` | **5/5 killed**, attribution printed and hand-checked | same |

### The manifest's two failures — attribution verified independently, and it holds

The manifest reported `2 failed, 1162 passed` and attributed both to **AT-357** (the two
`test_the_sandbox_is_removed_*` tests assert that a *global* `%TEMP%/mutation-check-*` glob is
unchanged across a run, so a concurrent mutation run in the other loop reds them) rather than
re-running until green. Three independent facts confirm that, and none of them is the maker's word:

1. My own full-suite run, with no concurrent mutation run in flight, exited **0** — zero failures.
2. Reading `tests/test_mutation_check.py:170-193`, the assertion is a **set comparison** of a
   `tempfile.gettempdir()` glob taken before and after. Stale leftovers appear in both sets and
   cannot fail it; only concurrent creation/removal can. That is a defect in the test's isolation,
   not in anything this unit touched.
3. `git show --stat c1c8f63` touches neither `scripts/mutation_check.py` nor
   `tests/test_mutation_check.py`. The unit cannot be the cause.

The manifest's decision to report the red rather than re-roll the suite was the right one and is the
behaviour AT-196 asked for. Not charged.

## Criteria

### U8 — the case form cannot commit a raw credential · MET

Judged on my own probe, not the maker's tests
(`scratchpad/probe_bidi.py`, 53 assertions).

**The positive control came first, and it earned its place.** My first run reported the case door
refusing everything — which would have read as a clean pass. The control said otherwise: with
`BIDI_OVERRIDES` neutered the door *still* refused, which is impossible if the door works. The cause
was my own probe (`case_class="best_case"` is not a `CaseClass`, so the route 400s before the guard
is ever reached). Every case-door negative in that run was worthless. Fixed and re-run:

```
[OK] P0 case door leaks AT-355 spelling when guard is neutered   status=200 leaked=True
[OK] P0 onboard door leaks AT-355 spelling when guard is neutered status=200 leaked=True
```

With the control passing, the guard's own results mean something:

- `U+202E` and `U+202D`, each in the **AT-355 spelling** (override + reversed credential) and in a
  **credential-free** string, across **title, step_value, step_expected, step_target** — 16/16
  refused **400**, and `cases.jsonl` contains the payload in **none** of them.
- The override check sits at `ui/helpers.py:164`, *before* the placeholder branch, the AT-078
  exempt branch and the credential comparison, so no early return can skip it.

### U9 — the routes that write `project.json` cannot either · MET

- `POST /onboard`: `name`, `base_url`, `allowed_domains`, both overrides — 6/6 refused **400**, and
  `projects/<slug>/project.json` was **not created** in any of them.
- Live, in a real browser: the form filled and the real submit button clicked → **400** with the
  override message, and the project absent from the home index.

### The false-positive side — the decisive risk, and it is clean

This is the whole justification for the narrow scope, so I tested it hardest. `U+200E`/`U+200F`
(LRM/RLM) and the isolates `U+2066`/`U+2067`/`U+2068`/`U+2069` in real Hebrew and Arabic:

- **Project names:** 5/5 accepted **and** persisted byte-identical into `project.json`.
- **Case fields:** all four field types, all five legitimate strings — accepted.
- **Live:** a Hebrew project name carrying RLM *and* an `U+2067…U+2069` isolate pair
  (`5de 5e2 5e8 5db 5ea 20 200f 20 2067 41 43 4d 45 2069 20 5d1 5d3 5d9 5e7 5d4`) was created
  through the real browser, redirected to its page, rendered verbatim in the title, and listed on
  the home index with both the RLM and the isolate preserved in the HTML.

I could not produce a single legitimate string that is now refused. Nothing chargeable here.

### The refusal message is true · MET

> *the name contains a text-direction override character. It makes text render in a different order
> than it is stored, so what you see is not what is saved. Remove it and type the value plainly.*

Captured live from the browser on text holding **no credential at all**. It does not say
"credential", "secret" or "password"; it names the override; it names the field it came from; it
tells the user what to do; and it echoes no value. This is the AT-339 false-diagnosis failure
correctly avoided.

## Invariants

### C2 — readable · HOLDS
`doctor: clean`. The extraction of `_refuse_direction_override` into its own function is exactly
right: the manifest says inlining pushed `_refuse_unsafe_value` to 57 lines against the 50-line cap,
and `doctor` agrees with the result.

### C7 — verification is independent · HOLDS, with one filed finding

I re-ran the mutation harness myself. **5/5 killed**, and I hand-verified the attribution clause on
all five: for every mutation, each node id in `claims to kill` appears in that run's
`actually failed` list. The harness asserts its own green baseline (the AT-307 clause) before
believing anything. The duty in C7's newest clause — a unit that adds a test must mutation-test it —
is discharged: all five test functions carry at least one attributed kill.

**One thing does not survive scrutiny, and I filed it rather than charging it (AT-360).** M1 and M5
produced **byte-identical** failure lists, which is what a duplicate looks like. M5 is named *"the
override is checked AFTER the credential comparison, so the fold hides it first"*, but its patch
deletes the call outright — it never moves it. So I performed the mutation it is named for in an
isolated copy (call moved past both the placeholder and the exempt early-returns), with an asserted
green baseline first:

```
--- BASELINE (unmutated copy): exit=0 failures=0
mutation applied: call MOVED past the placeholder + exempt early-returns
--- MUTATED (ordering actually inverted): exit=0 failures=0
```

Per C7's zero-failure clause that is **INCONCLUSIVE**: the ordering property is unproven, not false.
It is behaviourally real — a declared `{{SECRET:KEY}}` placeholder combined with an override takes
the placeholder early-return, so the moved version would accept it — and no test covers that input.

**Why filed and not charged.** C7's mutation duty is stated per added-or-rewritten test, and every
test here has an attributed kill; `5/5 killed` is arithmetically true. The defect is in one
mutation's *label*, and charging a unit for a labelling defect on the same day the contract gained
the clause would be judging it harder than the clause is written — the mirror of softening a
criterion, which the checker's one absolute forbids in both directions. Also folded into AT-360:
`test_ordinary_bidi_punctuation_is_still_accepted` has four parametrised cases and only the two
*mark* cases appear in any kills list; the two isolate cases are mutation-uncovered.

## Mode D — live feature validation (REQUIRED here, and performed)

`qa/evidence/browser-at355-refuse-bidi-overrides-2026-09-11-checker/report.json`. Own browser
(Playwright/chromium) against `uvicorn autotester.ui.app:app` on a scratch `AUTOTESTER_ROOT`. No
maker screenshot was read; the maker's own live section is a declared SKIP.

**The detector was proven twice before any negative was trusted.**

1. *Synthetic control:* a planted `U+202E` + reversed credential node — `textContent` does **not**
   contain the credential, glyph order **does** (`ZEBRA_QUILT_APIKEY_31`). The AT-355 leak,
   reproduced in a real browser.
2. *Page-level control:* planted into `input[name=title]` on `/projects/demo/cases` itself — the
   detector fired there too, so the clean reading on that page is a real negative.

**Result:** home index and Cases page — `dom_contains_credential: false`,
`visual_order_contains_credential: false`, `visual_contains_reversed: false`, no `U+202D`/`U+202E`
anywhere in the HTML, and the refused project not listed. **Console: 2 errors, both the deliberate
400s this run triggered. Zero unexplained.**

### On porting `visualOrder` into the repo — I agree, and it needs one correction

The manifest queues the port and defers it as a separate concern; that is correct unit hygiene and I
would have objected to it being bundled here. A concurrent checker has already filed the port as
**AT-358**, so it is tracked and I am not re-filing it.

**Where it belongs:** a test helper, not a runtime guard — `tests/` alongside the credential-guard
tests, exercised by the UI tests. It answers *"does this text, rendered, read as a known `.env`
value?"* without enumerating a character class, which is precisely the gap U13 admits an enumeration
leaves open. It should not become a request-path check: it needs a live browser, and putting a
browser in the refusal path of a form POST would be a worse trade than the deny-list it replaces.

**The correction, measured today, filed as AT-361.** Every existing copy of `visualOrder` walks text
nodes only. On the Cases page the case title renders **exclusively** inside `input[name=title]`, and
an input's value is not a text node — so a text-node-only detector reads a clean string from that
page no matter what the title holds. That is a guaranteed false negative on the single field U8 is
written about. I had to extend the detector (mirror each control's value into an offscreen span
carrying its computed font/direction/unicode-bidi, then measure per-character rects) before my own
negative meant anything. The port must cover form-control values, and must ship with a planted
positive control.

## Recommendations (none blocking, none charged)

1. **AT-360** — relabel M5 to what it patches, add a genuine ordering mutation and a
   placeholder-plus-override test; cover the two isolate parametrisations.
2. **AT-361** — fold the form-control-value requirement into AT-358 before the port is built.
3. For U13's next amendment only: consider whether "the adversary already holds the value" needs a
   sentence about this product's *own agents*, which hold resolved credentials and write tracked
   files. Not an objection to the current text.

## Working tree note

This tree carries the other loop's uncommitted work (`tests/test_goal_done_checks.py` modified,
`tests/test_goal_done_check_shapes.py` untracked, `.goal/` modified). My full-suite run was green
**with** those present. This verdict is committed with a narrow pathspec covering only checker-owned
files.
