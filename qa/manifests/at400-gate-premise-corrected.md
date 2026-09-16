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

## Status: ready-for-check
