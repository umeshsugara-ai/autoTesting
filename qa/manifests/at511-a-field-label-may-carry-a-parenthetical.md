# Manifest — at511-a-field-label-may-carry-a-parenthetical

**Unit:** AT-511 — `_marker_lines`'s stop condition could not recognise a field label that carries a
parenthetical before its colon, so `**ISSUES KEPT OPEN (claimed fixed, not fixed):**` was swallowed
as a continuation of `ISSUES-WRITTEN:` and its ids misattributed. Plus the same root cause letting a
closing code fence be swept in.
**Contract:** `qa/contracts/core-invariants.md` (C10)
**Goal task:** none (issue-driven; filed by the at509 cycle-1 checker)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-511 (medium, open -> fixed). Not closed here: AT-512 (low, the
single-line parenthetical limit) — a different mechanism, left for its own unit.

## The measurement first

AT-509 introduced `_NEW_FIELD` to stop a verdict block at the next labelled field. The regex was
`^[\s>#*_-]*[A-Z][A-Z0-9 -]*:` — no parenthetical allowed before the colon. Reproduced against the
shipped code at `qa/verdicts/at097-session-start-hook-regression.md:259-260`:

```
259: NEW_FIELD=True   **ISSUES-WRITTEN:** AT-106, AT-107
260: NEW_FIELD=False  **ISSUES KEPT OPEN (claimed fixed, not fixed):** AT-097, AT-029
```

So line 260 was read as a continuation and `AT-097`/`AT-029` counted as written by
`ISSUES-WRITTEN`. `FAILURES (if any):` is the same shape and appears in **every** verdict in this
repo.

**The obvious widening is badly wrong, and measuring is the only reason it did not ship.** Allowing
any parenthetical before the colon — `[A-Z][A-Z0-9 -]*(\([^)]*\))?\s*:` — matches **167 live
lines**, nearly all of them list items rather than fields:

```
AT-036 (filed in the previous unit): under Xvfb, `Page.screenshot` intermittently …
AT-038 (filed by the checker while verifying AT-037's fix): excluding a `.env` value …
**AT-335 (filed, high, NOT fixed):** the modal crawl is non-deterministic …
```

Every one would end a block early — re-creating the exact class of miss AT-509 had just closed, in
the unit fixing AT-509's own over-run. **The distinguishing feature is digits:** a field label has
none, an issue id always does.

Line counts are the wrong measure here, because a line only matters if it sits inside a marker
block. The decisive measurement is the id set actually read, per artifact
(`qa/evidence/.../at511_measure.py`, output in `before-after.out`):

```
verdicts/at097-session-start-hook-regression.md   no longer read: AT-029, AT-097
verdicts/at176-at178-render-not-scan.md           no longer read: AT-174, AT-176, AT-178, AT-189
artifacts changed: 2 | total ids dropped: 6 | added: 0
```

**Six misattributed ids removed, zero added.** A pure over-run removal: it cannot produce a new
violation, and `doctor` is clean before and after. All six already carry ledger rows, so nothing
was being reported — the defect was a false *attribution*, not yet a false accusation.

## What changed

- `src/autotester/ledger/checks.py`:
  - `_NEW_FIELD` → `^[\s>#*_-]*[A-Z][A-Z -]*(\([^)]*\))?\s*:` — the label may carry a parenthetical,
    and **contains no digits**, which is what keeps `AT-036 (…):` a list item. The reasoning, with
    both measured numbers, is in the constant's docstring.
  - `_marker_lines` also stops at a code fence (` ``` `), the same root cause the at509 checker
    found alongside the parenthetical shape.
- `tests/test_ledger_checks.py` — three new tests, one per direction plus the fence:
  - `test_a_field_label_carrying_a_parenthetical_still_ends_the_block`
  - `test_an_issue_id_with_a_parenthetical_is_not_a_field_label` — **the counter-direction, and the
    guard against the 167-line version.** Without it the naive widening passes every other test.
  - `test_a_code_fence_ends_the_block`

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py` → `46 passed`
- `uv run autotester doctor` → `doctor: clean`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at511-a-field-label-may-carry-a-parenthetical/mutations.json`
  → `4/4 mutations killed`, exit 0
- **Re-derive the 6-and-0 yourself.** `PYTHONUTF8=1 uv run python qa/evidence/at511-a-field-label-may-carry-a-parenthetical/at511_measure.py`
  compares the shipped `_marker_lines` against the proposed one; now that the proposal *is* shipped
  it must print `SHRINKS: 0 / GROWS: 0`. For the historical comparison, regenerate the pre-fix
  module with `git show 97fba9f:src/autotester/ledger/checks.py` and diff the id sets — that is what
  `before-after.out` records.
- Whole suite `uv run pytest -q` exits 0 — redirect to a **file** and scan it whole (AT-503).

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py
46 passed in 2.40s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run python scripts/mutation_check.py qa/evidence/at511-.../mutations.json
4/4 mutations killed        # exit 0; every row's actual failure set == its claim exactly
$ ... at511_measure.py      # after the fix
artifacts whose id set SHRINKS: 0
artifacts whose id set GROWS: 0
```

## Capability coverage (each new claim -> its isolating falsification)

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a label with a parenthetical ends the block | `..._carrying_a_parenthetical_still_ends_the_block` | `_NEW_FIELD` back to the AT-509 form | `KILLED` |
| an issue id with a parenthetical does NOT | `..._an_issue_id_with_a_parenthetical_is_not_a_field_label` | allow digits back into the label | `KILLED` |
| a plain label still ends the block | `..._verdict_block_ends_at_the_next_FIELD...` (AT-509's test) | make the parenthetical mandatory | `KILLED` |
| a code fence ends the block | `test_a_code_fence_ends_the_block` | drop the fence stop | `KILLED` |

`4/4 mutations killed`, each isolated to exactly one test. The second row is the one that matters:
it is the only thing standing between this fix and the 167-line version, and it is falsified on its
own rather than incidentally.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/ledger/checks.py`,
`tests/test_ledger_checks.py`, `qa/evidence/at511-a-field-label-may-carry-a-parenthetical/*`.

## Known limits (disclosed, not claimed)

- **`tests/test_ledger_checks.py` is now 295 lines against C2's 300 cap.** Five lines of headroom,
  and this is the fourth consecutive unit to add to it (AT-508, AT-509, AT-511). That is the AT-506
  shape exactly, one file later, and `doctor` will not say a word until 301. **The next unit
  touching this file should split it first.** I am not splitting mid-fix-cycle, and I am not
  recording this only in prose — it belongs in the ledger, which is the checker's surface.
- **`_NEW_FIELD` remains a heuristic about capitalisation.** A field label containing a digit
  (`PHASE 2 NOTES:`) would not be recognised and its ids would join the previous block — a false
  attribution, the same direction as the bug just fixed. None exists today; the digit rule is what
  buys safety on the far more common issue-id shape, and that is a trade, not a proof.
- **A fenced block *containing* the marker is not handled.** `_marker_lines` stops at the first
  fence it meets; it does not track whether the marker itself was inside one. `at500`'s verdict puts
  `ISSUES-WRITTEN` inside a fence and is read correctly, but by luck of ordering rather than design.
- **AT-512 is untouched** — the single-line parenthetical limit is a different mechanism
  (`claimed` matching within a line), confirmed live at
  `qa/manifests/at506-record-rules-leave-the-source-rules.md:13` and inert.
- **The six ids removed were all already correct in the ledger**, so this fixes an attribution that
  had not yet caused a wrong report. The value is that it cannot now.

## Status: ready-for-check
