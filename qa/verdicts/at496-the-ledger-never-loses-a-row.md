# Verdict — at496-the-ledger-never-loses-a-row

**Date:** 2026-09-18
**Cycle checked:** 2
**Checker:** fresh Mode A subagent, no builder context.
**Unit commits this cycle:** 0af3ad8 (docstring rewrap + manifest correction, AT-498/AT-499).
**Read first:** cycle-1 verdict `qa/verdicts/at496-the-ledger-never-loses-a-row.md` (FAIL, commit
b437a85) — this check judges whether its two failures are actually resolved, not the underlying
measurement or guard design (both already accepted in cycle 1 and not re-litigated here).

## What I re-ran myself (bound tree, HEAD 0af3ad8, then again after my own ledger write)

- `uv run pytest -q -o addopts= tests/test_doctor.py` -> `19 passed`. Matches manifest.
- `uv run autotester doctor` -> `doctor: clean`. Matches.
- `uv run ruff check src tests scripts` -> **`All checks passed!`** — reproduces cleanly this
  cycle. `tests/test_doctor.py:207-209`'s docstring is rewrapped to three lines, all ≤ 100 chars
  (`git show 0af3ad8 -- tests/test_doctor.py` confirms the single-hunk rewrap). Cycle-1's FAIL on
  this item is resolved.
- `uv run python scripts/mutation_check.py qa/evidence/at496-the-ledger-never-loses-a-row/mutations.json`
  — re-run myself, not read — `5/5 mutations killed`, every kill's actual failure list matches its
  claimed `kills:` list exactly (verified against `mutations.json` directly, not just the summary
  line). This harness sandboxes each run in a `tempfile.mkdtemp` outside the repo (confirmed at
  `scripts/mutation_check.py`), so running it against the bound tree doubles as my step-4b
  capability-coverage reproduction in a throwaway copy, per the same reasoning the cycle-1 verdict
  used.
- `git show 0af3ad8 --stat` and `git show 0af3ad8 -- tests qa/manifests` (diff scope, see below).

## Item 1 — AT-498 (ruff reproducibility)

**Resolved.** The docstring line that caused `E501` at `tests/test_doctor.py:208` is rewrapped to
three lines under the 100-char limit. `ruff check` now exits clean, matching the manifest's
pasted output for the first time this unit. No new lint issue introduced by the rewrap.

## Item 2 — AT-499 (ledger single-writer + the dropped `fixed_by` field)

**The manifest's response is the right one, and I executed the remedy myself.**

What cycle 2 did: it did **not** touch `qa/issues.jsonl` again. Instead it (a) corrected the false
"restored verbatim, not re-judged" claim in "What changed", stating plainly that AT-401's
restoration was rebuilt from HEAD (which had already lost `fixed_by`) rather than from `9b5cbc5`,
and quoting the dropped field in full; (b) left the byte-restore itself to `/checker`, because
`qa/issues.jsonl` is the checker's own write surface per SKILL.md, and the cycle-1 verdict's own
named remedy was "`/checker` byte-restores AT-401 (including `fixed_by`)" — a second maker edit to
the ledger would have repeated the exact actor violation AT-499 was filed for, on the same row,
one cycle later.

I judge this correct rather than a deferral to reject: AT-499's finding was two-part (wrong actor +
dropped content), and a maker fix that touches the ledger a second time can only ever resolve the
content half while making the actor half worse (a second unauthorized write). The only way to close
both halves is for the actor to change — the checker performs the write. I confirmed, before
performing it, that the manifest's corrected narrative is itself accurate: I diffed
`git show 9b5cbc5:qa/issues.jsonl`'s AT-401 row against the working tree at HEAD (0af3ad8) field by
field — identical except `fixed_by` is missing at HEAD, exactly as the corrected manifest states.

**Action taken (this checker, this cycle):** replaced AT-401's line in `qa/issues.jsonl` (line 398)
with the byte-identical row from `git show 9b5cbc5:qa/issues.jsonl` — the same content already
carrying `status: fixed`, `fixed_date: 2026-09-17`, and the restored
`"fixed_by": "cf34933 (checker PASS cycle 1, qa/verdicts/at401-flake-probe-runs-are-bounded.md)"`.
Verified: `git diff` shows exactly one line changed for this edit, the file re-parses as valid
JSONL (498/498 lines), and the full verify suite (pytest/doctor/ruff) stays green after the write.
No other row was touched by this edit. I separately confirmed AT-490/AT-491's `fixed_by` -> `fix_note`
change (a different, pre-existing schema evolution from the unrelated at490-491 unit) is out of
scope for AT-496/AT-499 and untouched by either cycle.

Both halves of AT-499 are now closed: the actor is corrected (the checker wrote it, not the maker),
and the content is corrected (byte-identical to the claimed source, `fixed_by` restored).

## Ledger housekeeping (this checker)

Flipped to `fixed` (2026-09-18), each with `fixed_by`/`fix_note` naming the evidence above:
- **AT-496** — the underlying incident is now fully reconciled: guard exists (mutation-proven
  5/5), and the ledger content itself is correct (AT-494 restored per the checker's own prior
  instruction; AT-401 now byte-identical to `9b5cbc5`, restored by the correct actor).
- **AT-498** — ruff reproduces clean, confirmed independently.
- **AT-499** — actor and content both corrected as above.

Left `open` (correctly, as enumerated debt, not re-litigated): **AT-500** (letter-suffixed ids
invisible to the guard's regexes) and **AT-501** (the manifest's proposed `merge=union` remedy does
not fit this failure's mechanism). Neither is claimed as fixed by this unit and both are properly
disclosed in "Known limits," not the capability-coverage table.

## Diff scope (4c)

`git show 0af3ad8 --stat`: exactly `qa/manifests/at496-the-ledger-never-loses-a-row.md` and
`tests/test_doctor.py` (a 3-line docstring rewrap, no assertion changed). No function, class,
export, test, or config key removed; no file touched outside the manifest's "What changed." My own
edit this cycle touches only `qa/issues.jsonl`, rows AT-401/AT-496/AT-498/AT-499 — the ledger is
named in C10's allowed handshake paths for a checker commit. No C10 violation.

## Capability coverage

5/5 rows reproduced via the project's own sandboxed mutation harness (`scripts/mutation_check.py`),
re-run independently this cycle, all kills correctly attributed to their named tests (checked
against `mutations.json`'s `kills:` lists, not just the summary count).

## Live browser

Not UI-touching. Changed paths this cycle: `qa/manifests/at496-the-ledger-never-loses-a-row.md`,
`tests/test_doctor.py`, plus this checker's own `qa/issues.jsonl` edit. No UI surface.

## Issues addressed

AT-496 (medium, open -> fixed): confirmed by this check. AT-498 (medium, open -> fixed): confirmed
by this check. AT-499 (high, open -> fixed): confirmed by this check, remedy executed by the
checker as specified. AT-500 (medium) and AT-501 (low) remain open, correctly enumerated as debt.

```
VERDICT: PASS
SCOREBOARD: 4/4 applicable criteria met, 0/0 invariants violated
FAILURES (if any): none
CAPABILITY-COVERAGE: 5/5 rows reproduced (project's own sandboxed mutation harness, re-run independently)
LIVE-BROWSER: not-applicable (qa/manifests/at496-the-ledger-never-loses-a-row.md, tests/test_doctor.py, qa/issues.jsonl only — no UI paths changed)
ISSUES-WRITTEN: none new. Closed: AT-496 (fixed), AT-498 (fixed), AT-499 (fixed). Left open as debt: AT-500, AT-501.
EXPLANATION: Both cycle-1 failures are resolved. AT-498 reproduces clean — the over-long docstring
is rewrapped and `ruff check` exits 0. AT-499's two-part finding (wrong actor, dropped `fixed_by`
field) is resolved the right way: the maker did not touch the ledger a second time, correctly
recognising that a second unauthorized write would repeat the actor half of the finding even if it
fixed the content; instead it corrected its manifest's false "restored verbatim" claim and left the
byte-restore to /checker, matching the cycle-1 verdict's own named remedy. I verified the corrected
claim against `9b5cbc5` field-by-field, then performed the byte-restore myself (one line changed,
file re-validated as JSONL, full verify suite stays green). The core measurement and the guard
itself were already accepted in cycle 1 and are unchanged here. AT-500/AT-501 are disclosed debt,
not re-litigated.
```
