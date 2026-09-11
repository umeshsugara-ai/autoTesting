# Manifest — at324-mutation-check-leak-and-remedy

**Contract:** qa/contracts/core-invariants.md C7 (mutation duty · kill attribution · the
unreachability clause added on the `at311-mutation-check` cycle-3 verdict)
**Goal task:** none (ledger issue batch)
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-324 · AT-325

## Why this unit exists

Both came from the cycle-3 PASS verdict on `at311-mutation-check`. Both **fail closed** — they
refuse a valid run rather than certify an invalid one — which is why they were filed rather than
charged, and why this is a separate unit rather than a fourth cycle.

### AT-324 — a guard whose own prescribed remedy was rejected
The ambiguity guard tells the author *"name the full nodeid"*. `collected_tests` keyed only on
`nodeid.split("::")[-1]`, so naming a full nodeid was then refused as **"not collected"**. The
instruction and the code disagreed, and the instruction was the one printed to a human.

Live in this repo today: `test_act_without_a_schema_raises` exists in two test files, so the guard
fires there and its remedy does not work.

### AT-325 — the sandbox was never cleaned up
`_sandbox` copied `scripts/ tests/ src/` per run and removed nothing. **1824
`mutation-check-*` trees had accumulated.** C7 makes this instrument mandatory for every
test-adding unit, so the leak is structural rather than incidental.

## What changed

- `collected_tests` now keys **both** ways — bare name *and* full nodeid — so the guard's own
  remedy works (AT-324).
- `_sandbox` returns `(work, owned_root)`; `check()` discards `owned_root` in a `finally`, so a
  **refused** run cleans up too — the common case while an author is still writing a spec.
- New `_discard(owned_root)` refuses to delete anything that is not under the system temp dir with
  this module's own prefix.

## The fix for the leak introduced a footgun, and the mutation run caught it

The first version was `shutil.rmtree(work.parent, ignore_errors=True)`. That is correct **only
while `work` really is a sandbox** — and this instrument's own spec contains the mutation
`work = repo`, which would have turned cleanup into *"delete the real tree's parent."*

A destructive operation keyed on an unverified path is **AT-314 wearing different clothes**, in the
unit written one cycle after AT-314 was fixed.

I did not find it by reading my diff. The self-mutation run reported
`>>> SURVIVED  sandbox removed - mutate the live tree`, and a survivor means a test stopped
detecting something; chasing *why* led to the footgun. **This is the first time in this sequence
that the instrument caught a defect of mine before a checker did.**

`_discard` now owns only what `_sandbox` created, and
`test_cleanup_refuses_to_delete_anything_it_did_not_create` hands it a `precious/` directory and
asserts the contents survive.

## Mutation evidence (C7)

```
16/16 mutations killed        (0 SURVIVED)
```

Three new mutations, one per new guard: the nodeid key (AT-324), the cleanup call (AT-325), and the
containment check (the footgun). The two pre-existing cleanup-adjacent anchors were rebuilt for the
new `(work, owned_root)` signature.

## How to verify (commands + expected)

- `uv run pytest -o addopts= -q` → `1081 passed, 2 skipped`, exit 0
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 1, exactly one violation (untracked root `AGENTS.md`, AT-283)
- `uv run python scripts/mutation_check.py qa/evidence/at311-mutation-check/mutations-self.json`
  → `16/16 mutations killed`, exit 0
- `uv run python scripts/mutation_check.py qa/evidence/at311-mutation-check/mutations.json`
  → `4/4 mutations killed`, exit 0

## Actual outputs (from maker's own run, after the final edit)

```
$ uv run pytest -o addopts= -q
1081 passed, 2 skipped, 1 warning in 119.54s       exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1

$ scripts/mutation_check.py … mutations-self.json   16/16 mutations killed   exit=0
```

The 1824 pre-existing leaked sandboxes were deleted. **Measurement discrepancy, disclosed rather
than resolved:** the cycle-3 verdict reported ~1.8 GB standing; I measured **0.06 GB** over the same
1824 directories. I could not reproduce the larger figure and am not repeating it. The *count* is
agreed; the size is not.

## A leak this unit does NOT close, and why not

A full self-mutation run still leaves ~38 sandboxes, because the spec **deliberately mutates
cleanup off** — that mutation's run cannot clean up, by construction. The count is bounded by
(cleanup-disabling mutations × inner runs), not unbounded.

I considered an end-of-run sweep of every `mutation-check-*` directory and **rejected it**: checkers
run this instrument too, so a global sweep could delete a *concurrently running* checker's sandbox.
That is the same destructive-operation-on-an-unverified-target class this unit just fixed. A
disclosed bounded leak is better than a new footgun. If you want it closed, the safe shape is
per-run ownership tracking, which is a unit of its own.

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths: `scripts/mutation_check.py`, `tests/`, `qa/`.
Nothing under `src/autotester/ui/`; `grep -rn mutation_check src/` returns nothing.

## Judgements offered to the checker (please rule)

1. **Keying `collected_tests` both ways** means a bare name and a full nodeid can both appear in
   `kills`. A bare name that is ambiguous is still refused, so there is no false-KILL path — but the
   map now holds two entries per test, and a *test named exactly like a nodeid* would collide. I
   judged that unreachable in pytest's own id grammar; attack it.
2. **The ~38-sandbox residue is disclosed, not fixed** (above). If you would rather it be closed
   now, say so and name the shape you want.
3. **The size discrepancy in AT-325** (1.8 GB vs 0.06 GB) is unresolved. If your figure is right I
   would like to know what I measured wrongly, because I used it to judge the severity.
4. **AT-326/AT-327** (duplicate `spec` across `conftest.py` and `tests_mutation_fixtures.py`, and
   C3's enforcement scope over `tests/`) are NOT addressed here — you filed them for a decision
   rather than charging them, and that decision is yours.

## Status: ready-for-check
