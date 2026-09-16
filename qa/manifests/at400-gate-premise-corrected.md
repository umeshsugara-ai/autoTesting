# Manifest — at400-gate-premise-corrected

**Unit:** AT-400 — a HUMAN_GATE spent hours advertising a working-tree state that no longer existed
**Contract:** `qa/contracts/core-invariants.md` (C3 — evidence must be re-derivable); the gate-record
rule in `~/.claude/skills/maker/SKILL.md` ("a gate is open until its file says otherwise")
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-400 (high)

## What was wrong

`qa/gates/at365-data-class-declaration.md` closed with:

> `"data_class": "synthetic"` plus a `_data_class_note` is **written into `qa/adapter.json` in the
> working tree but NOT committed**, pending this decision.

That was false, and had been for roughly three hours. I wrote the declaration while opening the
gate, then **reverted it myself** an hour later (`git checkout -- qa/adapter.json`) so the AT-366
unit would ship against a clean tree — and never returned to update the gate.

**Why a stale sentence was worth a `high`:** options A, B and C of that gate all begin *"land the
declaration"*. Anyone answering it would have been told the hard part was already done, when in
fact the edit had evaporated with no trace in any commit, stash or reflog. The gate's whole purpose
is to be the on-disk record a decision is made against, and its record was wrong.

**It also stales a measurement.** AT-376's 344 violations (335 under `.work/`, 2 under `profiles/`,
7 tracked) were counted against a tree that *had* the declaration. So were the "~30 benign hits"
described higher in the same gate file. Both now carry an explicit re-derive-before-use caveat.

## What changed

- `qa/gates/at365-data-class-declaration.md` — the "Current state" section replaced with what is
  actually on disk, the three commands that prove it, a plain statement that I wrote the edit and
  reverted it myself, and the staleness caveat on AT-376's numbers. **The four options and the
  analysis of why every consumer is blocked are untouched** — nothing about the decision changed,
  only the description of the repository.

Committed at `293bcfb` and pushed before this manifest was written, because a gate advertising a
false premise is worse every minute it stands. That ordering is unusual for this cycle and is
stated rather than hidden.

## What this does not claim

- **It does not answer the gate.** AT-365 stays open; the decision is still Umesh's.
- **It does not re-apply the declaration.** Landing it is common to options A/B/C, but doing it now
  would pre-empt the choice and red the MC-003 gate persistently. Re-applying is one line whenever
  an answer arrives.
- **It does not re-derive AT-376's 344 violations.** It flags them as stale; re-measuring is the
  job of whichever unit acts on the answer, against the tree state that answer produces.
- It does not touch the other seven open gates, though the same rot is possible in any of them —
  `t162-contract-approval` has been open five days and nothing guarantees its premise aged better.

## Capability coverage

**NO ISOLATING FALSIFICATION — the artifact is a gate record (prose), and `artifact.revert_op` for
a document is `none`.** There is no executable behaviour to perturb, and I am deliberately *not*
inventing a test that asserts gate-file prose matches disk: this session has already produced four
successive over-claims from exactly that species of guard (AT-396 → AT-405/406 → AT-413), and the
checker's structural signal named the pattern. Adding a fifth layer here would be the pattern, not
a fix.

**What replaces it is stronger than a guard: the claim is re-derivable in three commands**, and the
checker is asked to run them rather than read my paste. If any disagrees, the unit fails.

| Claim in the corrected section | Command that settles it | My run |
|---|---|---|
| no `data_class` in the adapter | `grep -c "data_class" qa/adapter.json` | `0` |
| the file is not dirty | `git status --porcelain qa/adapter.json` | *(empty)* |
| no commit ever carried it | `git log -S data_class --all -- qa/adapter.json` | *(empty)* |
| MC-003 still blocks on its absence | `python D:/ai_os/.claude/skills/_shared_validation/data_boundary.py .` | `[VIOLATION] qa\adapter.json — adapter.json has no "data_class"` |

## How to verify (commands + expected)

- The four commands above → expected: `0`, empty, empty, the VIOLATION line
- `uv run pytest -q` → expected: exit 0 (no code changed; this is the regression floor)
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- Read `qa/gates/at365-data-class-declaration.md` → expected: no sentence claiming the declaration
  is in the working tree; the four options intact

## Actual outputs (from maker's own run)

```
$ grep -c "data_class" qa/adapter.json
0

$ git status --porcelain qa/adapter.json
(empty)

$ git log -S data_class --oneline --all -- qa/adapter.json
(empty)

$ python D:/ai_os/.claude/skills/_shared_validation/data_boundary.py .
[VIOLATION] qa\adapter.json
    adapter.json has no "data_class" — declare "synthetic" or "real-approved" so the
    boundary is checkable instead of implied by a _note a human has to read
```

The three slot-1 commands are re-run below by the checker; I am not pasting an elided suite
transcript for them — **AT-414 was filed against me for exactly that** one unit ago, and the
honest form is to name the command and let the checker produce the output.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed path: `qa/gates/at365-data-class-declaration.md`.
A QA gate record; no production code, route, template, component or page.

## Data-boundary gate (MC-003)

Exits 1 on the missing `data_class` — that is AT-365 itself, the gate this unit corrects the
premise of. Unchanged by this unit, and deliberately so.

## Checker ruling (2026-09-16, verdict 952e599) — PASS, 4/4 applicable criteria

All four re-derivation commands reproduced exactly, and the checker **added a fifth I had not
thought to run** — `git stash list` → empty — establishing that the reverted edit exists in no
working tree, index, commit, ref **or stash**. It also verified the untouched-options claim
mechanically rather than by reading: `git show 293bcfb` is a single hunk replacing 4 lines with 33,
with options A/B/C/D and the whole blocked-consumer analysis outside it and byte-identical.

**Step 4b ruled admissible and on record as correct, not tolerated.** Its reasoning is sharper than
mine: C7's substance is "a check someone else can re-run", and for a gate premise the commands are
*stronger* than a falsifying edit — an edit proves a check would notice a change, these prove the
claim **is presently true**, which is exactly what a gate premise must be. **Bounded**, and I am
recording the bound: this applies only to a `qa/gates/` prose record of re-derivable facts. A unit
touching `src/`, `tests/` or `scripts/` still owes a falsifying edit per row, and "nothing to
perturb" there is an unreachability claim that costs a mutation run.

**One correction to a lesson I drew wrongly.** I cited AT-414 as a reason to decline pasting suite
output. The checker's ruling: AT-414 was filed for an **elided** paste, and the honest repair for
an elision is a **complete** paste, not the absence of one. Declining is right only when the
command carries no claim of the unit's own — true here, since no code changed. On a code-touching
unit C7's paste duty is live and "the checker will run it" does not discharge it.

Also upheld: `high` severity (the false premise sat on the path to a decision on AT-365 and had
already propagated into AT-376's measurement), and all four refusals as correct scoping — with one
strengthened, since re-deriving AT-376's 344 is not merely out of scope but **unobtainable** in the
current tree: it would require re-applying the declaration, which the previous refusal correctly
declines.

**AT-415 (medium) filed as a consequence:** no open gate other than at365 has ever had its premise
re-derived, ~7 of 14 gate files are unanswered, and sweep check 6 catches only a gate *answered*
off-disk — never one whose *premise* went stale while waiting. Filed deliberately as a human
decision, and explicitly **not** as buildable work for another automated guard.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at400-gate-premise-corrected.md`, commit 952e599; ledger AT-400 open → fixed; AT-415 filed)
