# Manifest — at311-mutation-check

**Contract:** qa/contracts/core-invariants.md **C7**, as amended by the checker on the
`at306-verification-artifact-integrity` verdict — the mutation duty (a unit that adds or rewrites a
test owes a run showing each new test dies when the behaviour it names is reverted) plus the
kill-attribution clause.
**Goal task:** none (ledger issue batch)
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-311 · AT-312

## Why this unit exists

C7 now obliges every test-adding unit to run a mutation check. That makes the instrument a **gate**,
and the instrument we had could certify a lie.

**AT-311 — the kill was never attributed.** `KILLED` meant `exit != 0`. So:
- a mutation that broke the module's **syntax** exited non-zero having run *nothing*, and was
  reported `KILLED  1 error` with an empty failure list;
- an **unrelated** test failing counted as proof that *this* test noticed;
- and the `defends:` label was decorative prose. Mine named
  `test_a_file_nested_below_the_project_is_still_judged_by_it` — a test that **does not exist**
  (`grep -c` → 0); I renamed it during the AT-304 fix and never updated the label. It printed the
  wrong name confidently, four kills running, and neither I nor the run noticed, because nothing
  checked.

Every failure mode points the same way: a false KILLED becomes a false PASS.

**AT-312 — an instrument C7 requires cannot live in one closed unit's `qa/evidence/` directory.**

## What changed

- **`scripts/mutation_check.py` (new)** — replaces the ad-hoc harness. Takes a JSON spec
  (`{tests, mutations:[{name, file, old, new, kills:[...]}]}`), and **refuses** rather than
  reporting when the run would be invalid:

  | Refusal | The failure it exists for |
  |---|---|
  | a `kills` name that pytest cannot collect | AT-311 — my label named a renamed test for four runs |
  | a red baseline | AT-307 — an already-red suite certifies everything |
  | `MutationError` on anchor count ≠ 1, or a mutation that changes nothing | a no-op reported as a kill |

  A kill now requires **pytest exit 1 AND every named test present in `FAILED`**. A collection
  error (exit 2/3/4/5) is reported with `collected_nothing`, never as a kill. Output prints
  *claims to kill* beside *actually failed*, so a mismatch is visible rather than inferred.
  Mutations run in a `copytree` **outside** the repo and the target is restored byte-identically.

- **`tests/test_mutation_check.py` (new, 12 tests)** — one per refusal, against a synthetic
  two-test module, plus the live-tree-untouched guarantee and the JSON round trip.

- `qa/evidence/at311-mutation-check/` — `mutations.json` (the migration unit's four, re-run through
  the new instrument), `mutations-self.json`, and both runs' output.

## The recursive obligation, discharged

C7 applies to this unit too, so the instrument was pointed at **itself**:

```
KILLED  kills-label existence check removed (AT-311)
KILLED  baseline assertion removed (AT-307)
KILLED  kill redefined as any non-zero exit (AT-311)
KILLED  anchor-count discipline removed
KILLED  sandbox removed - mutate the live tree
5/5 mutations killed
```

Each line printed its claimed kills beside the tests that actually failed, and they match — the
attribution AT-311 was filed for, demonstrated on the fix for AT-311.

Worth recording: the **first** attempt at this self-run was **refused**, not reported — one anchor
had a mangled em-dash and matched 0 times, so the instrument rejected the whole run
(`MUTATION RUN INVALID … anchor matched 0 times`) instead of quietly proceeding with four of five.
That is the discipline working *on* the maker.

The four migration mutations were also re-run through the new instrument: **4/4 killed**, each
correctly attributed — including the M4 label that the old harness had been printing wrongly.

## How to verify (commands + expected)

- `uv run pytest -o addopts= -q` → `1066 passed, 2 skipped`, exit 0
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 1, exactly one violation (untracked root `AGENTS.md`, AT-283)
- `uv run python scripts/mutation_check.py qa/evidence/at311-mutation-check/mutations-self.json`
  → `5/5 mutations killed`, exit 0
- `uv run python scripts/mutation_check.py qa/evidence/at311-mutation-check/mutations.json`
  → `4/4 mutations killed`, exit 0
- `grep -c test_a_file_nested_below_the_project_is_still_judged_by_it tests/test_migrate_url_patterns.py`
  → `0` (the test the old harness claimed to be killing)

## Actual outputs (from maker's own run, after the final edit)

```
$ uv run pytest -o addopts= -q
1066 passed, 2 skipped, 1 warning in 104.22s        exit=0

$ uv run ruff check src tests scripts
All checks passed!                                   exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                       exit=1

$ scripts/mutation_check.py … mutations-self.json    5/5 mutations killed   exit=0
$ scripts/mutation_check.py … mutations.json         4/4 mutations killed   exit=0
```

Note the suite is ~17s slower: `test_mutation_check.py` spawns real pytest subprocesses. That is
the honest cost of testing an instrument that runs pytest, and it is disclosed rather than hidden.

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths: `scripts/`, `tests/`, `qa/`. Nothing under
`src/autotester/ui/`; `grep -rn mutation_check src/` returns nothing.

## Judgements offered to the checker (please rule)

1. **The old harness under `qa/evidence/at300-.../mutation_harness.py` is left in place.** It is
   evidence for a PASSed unit and rewriting a closed unit's evidence would falsify the record — but
   it is now superseded and could be copied by mistake. Should it carry a pointer to its
   replacement, or is the manifest enough?
2. **`_run_pytest` shells `sys.executable -m pytest`, not `uv run`.** Inside the venv these agree;
   under a different interpreter they might not. I judged inheriting the caller's interpreter more
   predictable than assuming `uv`, but the adapter's own commands all use `uv run`.
3. **Exit codes 2/3/4/5 are all treated as "collected nothing".** Strictly, 3 is an internal error
   and 4 usage error — neither is literally "no tests ran", but all three share the property that
   matters (no test result was produced, so no kill can be claimed). If you want them distinguished,
   say so.
4. **AT-308/AT-309 remain open** and are NOT addressed here. Your sequencing note said AT-309's
   lexical `parent == root` is a one-line `.resolve()` that shouldn't wait for its test — I left it
   rather than slip an unrelated fix into this unit. Say if you would rather it rode along.

## Status: ready-for-check
