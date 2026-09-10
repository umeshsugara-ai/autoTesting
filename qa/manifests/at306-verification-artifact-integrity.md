# Manifest — at306-verification-artifact-integrity

**Contract:** qa/contracts/core-invariants.md (C7 — as tightened by the checker on the
`at300-migration-config-hardening` verdict, requiring a mutation run to assert a green baseline)
**Goal task:** none (ledger issue batch)
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-306 (second occurrence) · AT-307

## Why this unit exists

Both defects are in the artifacts this project uses to *check* things, not in the product. Both
were filed by the checker, and both are mine.

### AT-307 — a mutation harness that could certify a lie
`KILLED` is `exit != 0`. My harness **printed** the baseline and never asserted it, so a suite that
was already red would have reported every mutation as KILLED and certified every test non-vacuous —
exactly when it matters most, since this repo has a documented flake (AT-196). The harness whose
whole purpose is to stop me trusting a green tick was itself trusting a green tick.

### AT-306 — the same stale count, twice
The human gate said "9 tests" when the suite had 14; I corrected it to "14"; the suite is now 21 and
it went stale again within one unit. **Correcting the number was the wrong fix.** A count is a
derived fact that every new test invalidates while the prose sits still, so the document is
guaranteed to drift and a human decides from a false statement. Fixed by removing the count
entirely and referencing the file that can be re-run.

## What changed

- `qa/evidence/at300-migration-config-hardening/mutation_harness.py` — asserts the baseline is
  green before reporting any mutation, with the reason inline. Module docstring generalised: this
  is a harness for a unit's tests, not for one unit.
- `qa/gates/t135-url-pattern-data-migration.md` — both test counts removed (lines 26 and 39), plus
  a short "A note on this file" recording *why* it states no count, so the next person to edit it
  does not helpfully add one back.

No `src/` change. No behaviour change to the migration itself.

## How to verify (commands + expected)

- `uv run pytest -o addopts= -q` → `1054 passed, 2 skipped`, exit 0
  (note: `pyproject.toml` already sets `addopts="-q"`, so a bare `-q` is `-q -q` and prints no
  summary line — the checker flagged this on the previous unit)
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 1, exactly one violation (untracked root `AGENTS.md`, AT-283)
- `uv run python qa/evidence/at300-migration-config-hardening/mutation_harness.py` → baseline
  asserted green, 4/4 KILLED
- `grep -n "tests in" qa/gates/t135-url-pattern-data-migration.md` → no test-count claim remains

**The AT-307 guard was proved to bite, not asserted to:** a copy of the harness pointed at a
non-existent test selector (forcing a red baseline) exits 1 with
`AssertionError: baseline is NOT green - every KILLED below would be a lie: no tests ran`.
That is the whole lesson of this session applied to my own fix — run the mutation, do not re-read
the guard.

## Actual outputs (from maker's own run, after the final edit)

```
$ uv run pytest -o addopts= -q
1054 passed, 2 skipped, 1 warning in 86.67s        exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1

$ uv run python qa/evidence/.../mutation_harness.py
BASELINE: exit=0  21 passed in 0.14s
M1..M4  all KILLED

$ (red-baseline copy of the harness)
exit: 1
AssertionError: baseline is NOT green - every KILLED below would be a lie: no tests ran in 0.05s
```

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths are `qa/evidence/` and `qa/gates/`. No
`src/`, no `tests/`, no `ui/`.

## Judgements offered to the checker (please rule)

1. **Removing the count instead of correcting it** is the substance of the AT-306 fix. If you would
   rather the gate state a count kept fresh by a generator, say so — but I judged that a document a
   human decides from should reference what can be re-run rather than restate what rots, and the
   evidence is that it rotted twice in one session.
2. **The harness still lives under `qa/evidence/`, not `scripts/`.** Unchanged from the previous
   unit's judgement #3 and deliberately so: whether mutation becomes a required slot-1 verify step
   is the standing proposal in `qa/feedback-inbox.md`, and that is yours to fold in. I have not
   pre-empted it. If you do fold it in, this harness is the obvious seed and AT-307 is the first
   thing its contract should require.
3. **AT-308/AT-309 are NOT addressed here** (undefended defensive branches: the `ValueError` guard,
   the `_project_dir_of` root-containment `break`). You classified them as undefended branches
   rather than vacuous tests, and they are unreachable through `main()`. Left open deliberately.

## Status: ready-for-check
