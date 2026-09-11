# Manifest — at355-refuse-bidi-overrides

**Unit:** AT-355 — refuse bidi overrides instead of folding them away
**Contract:** `qa/contracts/ui.md` (U8/U9; threat model pending as U11) ·
`qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-355 (high, fixed)

## Where this came from

`at345-346-fold-coverage` is **STALLED** after three cycles and three FAILs. It is not reopened.
The stall diagnosis (`qa/debug/at345-346-fold-coverage-cycle3.md`) put the failure on **loop
design, specifically the contract**, and raised a HUMAN_GATE on the guard's shape.

Umesh delegated that decision ("take the best decision as per the goal and keep going"). It is
answered in full at `qa/gates/at355-guard-shape.md`: **option C plus the narrow half of A.** This
unit is the narrow half. The threat model half is in `qa/feedback-inbox.md` for `/checker` to fold
as U11 — the maker never edits a contract.

## Why refusing, not folding

`U+202E` + a credential written backwards renders as plain type in the correct reading order, and
the guard could not see it **because it stripped the override**:

```
fold("ZEBRA_QUILT_APIKEY_31")   ->  zebraquiltapikey31
fold(RLO + its reverse)         ->  13yekipatliuqarbez
```

`_is_ignorable` deletes the character that *causes* the reordering, then compares a string that is
not the credential. Every other fix in this family worked by subtracting more; here that makes it
**strictly worse**, which is exactly why a fourth subtraction cycle would have been the wrong
call. So the override is refused on its own terms, before any credential comparison.

## Scope, and why it is bounded rather than another open-ended chase

Only the two **overrides**, `U+202D`/`U+202E`, which force direction per character regardless of
content. Deliberately NOT the rest of the bidi family:

- `U+200E`/`U+200F` (LRM/RLM) and the isolates are **ordinary punctuation in Hebrew and Arabic**
  and do not reverse a pure-ASCII run. Refusing them would cost real input for no security gain,
  and **false-positive rate is a term in this product's north star** — AT-078 and AT-086 are two
  prior occasions when this guard made a real project uneditable.
- A mutation pins this from the wrong side: widening `BIDI_OVERRIDES` to include LRM/RLM kills the
  legitimate-Hebrew test. The bound is enforced, not just described.

## What changed

- `src/autotester/core/redact.py` — `BIDI_OVERRIDES`, with the measured fold comparison in its
  docstring so the next reader sees why subtraction fails here.
- `src/autotester/ui/helpers.py` — `_refuse_direction_override(value, field)`, called from
  `_refuse_unsafe_value` **before** the credential comparison. Extracted to its own function
  because inlining it pushed `_refuse_unsafe_value` to 57 lines (doctor's 50-line cap).
- `tests/test_ui_credential_bidi.py` — **new file**, 9 tests.

**The message names the override, not a credential.** This refusal fires on text holding no
credential at all, so "looks like it contains a real credential" would send the user hunting for a
secret that is not there — the same false diagnosis the "split across" message made in AT-339. A
test and a mutation pin the message.

## How to verify (commands + expected)

- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_ui_credential_bidi.py -q` → expected: 9 passed
- `uv run python scripts/mutation_check.py qa/evidence/at355-refuse-bidi-overrides/mutations.json`
  → expected: `5/5 mutations killed` (C7)

## Actual outputs (from maker's own run)

```
$ uv run pytest          # first run, before the helper extraction
1164 passed, 2 skipped, 1 warning in 222.51s (0:03:42)

$ uv run pytest          # re-run after the extraction
2 failed, 1162 passed, 2 skipped, 1 warning in 215.43s (0:03:35)
FAILED tests/test_mutation_check.py::test_the_sandbox_is_removed_when_the_run_finishes
FAILED tests/test_mutation_check.py::test_the_sandbox_is_removed_even_when_the_run_is_refused
  ^ NOT this unit, and NOT a regression -- filed as AT-357. Those two tests assert
    that a GLOBAL `%TEMP%/mutation-check-*` glob is unchanged across a run, so any
    concurrent mutation run fails them. `ls %TEMP%/mutation-check-*` showed 2 live
    sandboxes belonging to the other maker loop, and both files under test are
    unmodified in git. Reported here rather than re-run until green, because
    re-rolling a suite until the number you want appears is how a flake becomes
    invisible. The checker should expect either result and judge AT-357 on its own.

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run python scripts/mutation_check.py qa/evidence/at355-refuse-bidi-overrides/mutations.json
KILLED  the override check never runs - AT-355 reopens at both doors
KILLED  only the RIGHT-to-left override is refused, LRO walks through
KILLED  the check is widened to LRM/RLM too - legitimate Hebrew is refused
KILLED  the refusal blames a credential instead of naming the override
KILLED  the override is checked AFTER the credential comparison, so the fold hides it first
5/5 mutations killed
```

## Live browser evidence

**SKIP — stated gap, not a pass.** AT-355's whole claim is about what a page *renders*, which a
`TestClient` cannot verify. **The checker must run Mode D and treat its own result as
authoritative**, and should use the `visualOrder` detector (glyphs sorted by screen x) that caught
this — asserting the home index and the Cases page no longer render the credential.

**That detector should be ported into this repo**, per the gate. It is not in this unit because it
is a test instrument, not part of the guard, and bundling it would put two concerns in one unit —
but it should not stay in a checker's scratch directory either. Queued, not forgotten.

## What remains out of scope, by decision rather than by omission

AT-352 (base64/hex/entities/double-encoding/reversal) and AT-349 (homoglyphs outside the curated
map) stay **filed and open**. Each requires deliberate construction by a party who already holds
the credential, and the answered gate's reasoning is that a guard cannot protect a secret from
someone who already has it. If `/checker` disagrees, the place to settle it is the U11 amendment —
**not this unit**, whose scope the gate fixed before it was built.

## Status: ready-for-check
