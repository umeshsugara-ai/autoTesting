# Verdict — at015-at028-hook-adapter-fix

**Cycle checked:** RECOVERY (post-STALL)
**Date:** 2026-09-03
**Checker:** fresh subagent, stall-recovery confirmation (not a numbered fix cycle), no builder
context, bound to `d:/autoTesting`

## Context

This unit hit its 3-cycle fix budget and STALLED (cycle-3 FAIL, `AT-031`: D-010's `Approved-by`
line recycled the old AT-015/AT-028 batch quote under an "explicitly extended here" framing
instead of citing a fresh, cap-specific approval exchange). A dispatched `/agent-debugger`
(`qa/debug/at015-at028-hook-adapter-fix-cycle3.md`) diagnosed this as a simple execution gap and
named the recovery: append a new D-011 that directly quotes the real approval exchange verbatim.
This is a one-time verification that the named recovery was actually applied — not a fourth fix
cycle.

## 1. D-011 form check

Read `docs/DECISIONS.md` D-011 in full (lines 166-190). It has all required fields: **What**,
**Why**, **Result**, **Changes-authorized**, **Approved-by**, **Links** — structurally complete
per `append_decision.ps1`'s V1-V7 gates, and it correctly does NOT re-litigate or edit D-010
(append-only respected; D-011 explicitly says "D-010's code/text is otherwise accurate and is NOT
re-litigated").

The point that actually mattered: does `Approved-by` now **directly quote** a specific exchange,
rather than restate/infer an extension the way D-010's did? Yes:

- **Result** states the exchange verbatim: Question — *"Separately: the hook fix for AT-015
  needed a follow-on correction (raising an injection cap from 100 to 150 lines) that the checker
  says needs its own explicit sign-off, not just an extension of your original 'approve both'
  batch answer. Approve this specific cap change?"* — Answer: *"Yes, approve the cap change."*
- **Approved-by** reads: *"Umesh — direct answer, this session, 2026-09-03, quoted verbatim
  above."* — it points at the Result's verbatim quote rather than manufacturing a second,
  possibly-drifting paraphrase, and contains no "extended here" / inferential language.

This is categorically different from D-010's defect: D-010's Approved-by cited the *old*
AT-015/AT-028 batch quote and asserted an extension; D-011's Approved-by cites *this* entry's own
freshly-quoted, cap-specific exchange. Per the task's scope, I cannot independently verify the
underlying AskUserQuestion exchange happened in the maker's session (no transcript access) — but
the ENTRY's form is exactly what AT-031 required: a direct quote, not an inferred extension.
**AT-031's process defect is resolved on the form check.**

## 2. Independent re-verification of the technical fix (4th re-run, same method as cycles 1-3)

Extracted the literal filter block from `.claude/hooks/lab-session-start.ps1` on disk (lines
109-127; the `-ge 150` cap, unchanged since cycle 2) and ran it standalone against the real
`docs/ARCHITECTURE.md`:

```
TOTAL_KEPT: 139
headings kept: # AutoTester - architecture / ## What it does / ## Pipeline / ## Concept... /
## Data model... / ## Execution model / ## Security... / ## Storage / ## Design rules... /
## Commands / ## Status
truncation marker present: 0
```

139 lines kept, no truncation marker, all 10 headings present through `## Status`. Identical
result to cycles 1-3 (accounting for cycle 1's pre-fix 100-line cap). The technical fix still
holds.

## 3. Commands run myself

- `uv run pytest -q` → clean (1 skip, rest pass).
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"

All three clean, same as every prior cycle.

## 4. Commit (addresses AT-032)

`git status --porcelain` before commit showed this unit's files uncommitted across all 3 prior
cycles, plus several unrelated in-flight files (`.goal/rubrics/`, `projects/pathlynks/*`,
`qa/contracts/pathlynks-first-run.md`, `scripts/run_pathlynks_first_cases.py` — a different,
unrelated unit's work-in-progress, correctly left alone).

Committed this unit's files only, via a narrow explicit pathspec (no `git add -A`):
`.claude/hooks/lab-session-start.ps1`, `qa/adapter.json`, `CLAUDE.md`, `docs/DECISIONS.md`
(D-008-D-011), `qa/loop.md`, `docs/SNAPSHOT.md`, `qa/manifests/at015-at028-hook-adapter-fix.md`,
`qa/debug/at015-at028-hook-adapter-fix-cycle3.md`, `qa/issues.jsonl` (this verdict's status
flips), `qa/verdicts/at015-at028-hook-adapter-fix.md` (this file), `.goal/goal.json`,
`.goal/dashboard.html`, `goal.md`, `qa/.last-tick`, `qa/feedback-inbox.md`.

This resolves **AT-032** — the unit's changes are now in git history, so `docs/DECISIONS.md`'s
append-only guarantee is backed by version control rather than resting on unauditable
working-tree state.

## Issue flips

- **AT-015**: `open` -> `fixed` (technical fix independently re-verified a 4th time; authorization
  chain now sound per #1 above).
- **AT-029**: `open` -> `fixed` (functional claim — 139 lines, all headings, no truncation —
  independently reproduced true again this cycle).
- **AT-030**: `open` -> `fixed` (D-010's authorization gap is superseded in effect by D-011, which
  supplies the missing verbatim citation without editing D-010, per the Lab Protocol's
  append-only rule).
- **AT-031**: `open` -> `fixed` (D-011's Approved-by now directly quotes a specific approval
  exchange rather than asserting an inferred extension — the form defect AT-031 identified no
  longer exists).
- **AT-028**: already `fixed` since cycle 1, unchanged.
- **AT-032**: resolved by the commit in step 4 above (not a tracked issues.jsonl row — filed only
  in verdict text originally; addressed via the commit itself).

```
VERDICT: PASS (stall recovery confirmed)
SCOREBOARD: 7/7 criteria met, 3/3 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: none new. Flipped to fixed: AT-015, AT-029, AT-030, AT-031.
EXPLANATION: The named recovery (append D-011 quoting the real approval exchange verbatim) was
applied correctly — D-011 has all required fields, does not re-litigate D-010, and its
Approved-by line now directly quotes a specific cap-only exchange instead of restating/inferring
an extension of the old AT-015/AT-028 batch approval, which is exactly the form defect AT-031
identified. The underlying technical fix (ARCHITECTURE.md filter, 139 lines kept, no truncation,
all headings through Status) was independently re-verified a 4th time and still holds. pytest,
ruff, and doctor are all clean. All of this unit's files (hook, adapter.json, CLAUDE.md,
DECISIONS.md D-008-D-011, manifest, debug report, issues.jsonl, verdict) have now been committed
together with a narrow explicit pathspec, resolving AT-032 (nothing had been committed across 3
cycles). AT-015, AT-029, AT-030, and AT-031 are flipped to fixed; AT-028 was already fixed. The
stall is resolved — this unit passes.
```

## Ledger

No goal task matches this unit (manifest states "Goal task: none"), consistent with prior cycles
— no `docs/FEATURES.jsonl` entry to append.
