# Manifest — at311-mutation-check

**Contract:** qa/contracts/core-invariants.md **C7**, as amended by the checker on the
`at306-verification-artifact-integrity` verdict — the mutation duty (a unit that adds or rewrites a
test owes a run showing each new test dies when the behaviour it names is reverted) plus the
kill-attribution clause.
**Goal task:** none (ledger issue batch)
**Date:** 2026-09-11
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-311 · AT-312 · AT-313 · AT-314 · AT-315

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

- **`tests/test_mutation_check.py` (new)** — one per refusal, against a synthetic two-test module,
  plus the live-tree-untouched guarantee and the JSON round trip. **Cycle 2 raised it to 18**, adding
  the direct `is_kill` table and the two escape refusals.

- `qa/evidence/at311-mutation-check/` — `mutations.json` (the migration unit's four, re-run through
  the new instrument), `mutations-self.json`, and both runs' output.

## The recursive obligation, discharged

C7 applies to this unit too, so the instrument was pointed at **itself**:

**Superseded by cycle 2 — this 5/5 run was real but incomplete: the checker's own mutation
`killed = code != 0 and not survivors` survived all of it (AT-315). The authoritative run is the
8/8 in the cycle 2 section below.**

Each line printed its claimed kills beside the tests that actually failed, and they match — the
attribution AT-311 was filed for, demonstrated on the fix for AT-311.

Worth recording: the **first** attempt at this self-run was **refused**, not reported — one anchor
had a mangled em-dash and matched 0 times, so the instrument rejected the whole run
(`MUTATION RUN INVALID … anchor matched 0 times`) instead of quietly proceeding with four of five.
That is the discipline working *on* the maker.

The four migration mutations were also re-run through the new instrument: **4/4 killed**, each
correctly attributed — including the M4 label that the old harness had been printing wrongly.

## How to verify (commands + expected)

- `uv run pytest -o addopts= -q` → `1072 passed, 2 skipped`, exit 0
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 1, exactly one violation (untracked root `AGENTS.md`, AT-283)
- `uv run python scripts/mutation_check.py qa/evidence/at311-mutation-check/mutations-self.json`
  → `8/8 mutations killed`, exit 0
- `uv run python scripts/mutation_check.py qa/evidence/at311-mutation-check/mutations.json`
  → `4/4 mutations killed`, exit 0
- `grep -c test_a_file_nested_below_the_project_is_still_judged_by_it tests/test_migrate_url_patterns.py`
  → `0` (the test the old harness claimed to be killing)

## Actual outputs (from maker's own run, after the final edit)

**Superseded — captured at cycle 1. The authoritative, freshly re-run outputs are in
"Cycle 2 verify" below.**

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

---

# Cycle 2 — the instrument failed its own check, which is the point

Cycle 1 FAILed. All three findings were reproduced by the checker against the committed code, and
all three are the same defect this instrument exists to refuse, one level up.

### AT-313 (high) — it refused a name that did not exist, and accepted no name at all
An empty `kills` list collapsed the verdict to `code == 1` — *"some test failed, attributed to
nothing"*. That is **verbatim AT-311's second failure mode, reachable inside the fix for AT-311**.
Now refused at spec validation *and* inside the decision itself, so neither path can produce an
unattributed kill.

### AT-314 (high) — the sandbox promise was documentation, not code
`work / mutation["file"]` looks contained and is not: pathlib **discards** the left operand for an
absolute right one, and `../` climbs out. The checker mutated a decoy file outside the sandbox and
watched it report SURVIVED, while `_sandbox`'s docstring said a mutation "can never touch the live
tree". Now `_inside()` resolves and refuses anything outside, and the defending test asserts the
decoy is **byte-unchanged** afterwards rather than merely that an error was raised.

### AT-315 (medium) — a vacuous test, inside the instrument built to catch vacuous tests
The checker's own mutation `killed = code != 0 and not survivors` **survived all 12 tests**, so
`test_a_mutation_that_breaks_collection_is_not_a_kill` passed for the *survivors* reason rather than
the exit-code reason it was named for.

**A better test was not available.** A mutation cannot reach that clause: a collection error yields
no `FAILED` lines, so `expected <= failures` fails too and the weakened form survives *every*
possible mutation. So the decision was **extracted** into a pure `is_kill(exit_code, expected,
failures)` and asserted head-on with a table — exit 1 kills; 0, 2, 3 and 4 do not.

The general rule, which is the thing this session actually taught:
**when a property cannot be reached by mutation, extract it until it can be asserted directly.**

## Cycle 2 — the recursive obligation, discharged again

The spec grew from 5 mutations to 8 (the three new guards each earn one), and the anchors for the
refactored decision were rebuilt — the first attempt was **refused** for a stale anchor rather than
reported, which is the discipline working on the maker for the second time in two cycles.

```
KILLED  kills-label existence check removed (AT-311)
KILLED  empty-kills guard removed (AT-313)
KILLED  baseline assertion removed (AT-307)
KILLED  kill redefined as any non-zero exit (AT-311/AT-315)
KILLED  kill no longer requires the NAMED test to fail
KILLED  sandbox containment removed (AT-314)
KILLED  anchor-count discipline removed
KILLED  sandbox removed - mutate the live tree
8/8 mutations killed
```

Every line's `claims to kill` is a subset of `actually failed`. The last mutation also fails an
unrelated test, which is correct and visible rather than hidden — that is what attribution is for.
The migration spec was re-run unchanged: **4/4 killed**.

## Cycle 2 verify (re-run after the final edit)

```
$ uv run pytest -o addopts= -q
1072 passed, 2 skipped, 1 warning in 109.64s       exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1

$ scripts/mutation_check.py … mutations-self.json   8/8 mutations killed   exit=0
$ scripts/mutation_check.py … mutations.json        4/4 mutations killed   exit=0
```

`tests/test_mutation_check.py` is 18 tests and ~22s; the suite is ~110s against a ~86s baseline.
Disclosed, and slightly worse than cycle 1's disclosure — the honest cost of testing an instrument
that runs pytest, rather than mocking the thing under test.

## What cycle 2 does NOT claim

- **The checker found three holes I did not, having just written the tool to find holes.** I have no
  basis for claiming there is not a fourth. The tool is better than the harness it replaced and
  worse than the next attack on it.
- **AT-319 (five duplicate ledger ids) is not addressed** — pre-existing, correctly not charged to
  this unit, and renumbering would break citations across a dozen verdicts.
- **AT-308/AT-309 remain open**, unchanged from cycle 1's judgement #4.

## Status: ready-for-check
