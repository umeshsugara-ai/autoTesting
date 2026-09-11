# Manifest — at311-mutation-check

**Contract:** qa/contracts/core-invariants.md **C7**, as amended by the checker on the
`at306-verification-artifact-integrity` verdict — the mutation duty (a unit that adds or rewrites a
test owes a run showing each new test dies when the behaviour it names is reverted) plus the
kill-attribution clause.
**Goal task:** none (ledger issue batch)
**Date:** 2026-09-11
**Fix cycle:** 3 of max 3 (LAST)
**Dual check:** no
**Issues addressed:** AT-311 · AT-312 · AT-313 · AT-314 · AT-315 · AT-320 · AT-321 · AT-322 · AT-323

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

**Superseded by cycle 3 — this 8/8 run was real but measured a tool with four more defects in it (AT-320..AT-323). The authoritative run is the 13/13 below.**

Every line's `claims to kill` is a subset of `actually failed`. The last mutation also fails an
unrelated test, which is correct and visible rather than hidden — that is what attribution is for.
The migration spec was re-run unchanged: **4/4 killed**.

## Cycle 2 verify (re-run after the final edit)

```
$ uv run pytest -o addopts= -q   # SUPERSEDED, see cycle 3
1072 passed, 2 skipped

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1

$ scripts/mutation_check.py … mutations-self.json   8/8 killed  # SUPERSEDED by 13/13
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

---

# Cycle 3 — the last one

Cycle 2 FAILed. The checker reproduced every finding against the committed code, and one of them
demolished this unit's central argument.

### AT-321 — my "unreachable clause" claim was FALSE, and it was my second
Cycle 2 argued that no mutation could reach `exit_code == 1`, so the decision had to be **extracted**
into `is_kill` and asserted directly. The premise silently assumed every non-1 non-zero exit is a
*collection* error. **pytest exit 2 is INTERRUPTED and prints the FAILED lines of tests that already
failed.** The checker built the mutation in one attempt.

`test_an_interrupted_run_with_real_failures_is_not_a_kill` is now that mutation, at `check()` level:
one test fails normally, a later one raises `KeyboardInterrupt`, the run exits 2 **with** real
failures — so a weakened `!= 0` calls it killed and the correct `== 1` does not.

**The extraction stays, but its justification does not.** `is_kill` is a cheap direct assertion
beside the mutation, not proof that no mutation exists. And the proposed general rule — *"when a
property cannot be reached by mutation, extract it until it can be asserted directly"* — is
**withdrawn**. The checker declined to adopt it and was right: this was the second unreachability
claim from me falsified by a single attempt. *"I could not think of a mutation" is not "no mutation
exists."*

### AT-320 — the fourth hole: a bare name is not an identifier
`collected_tests` and `failed_tests` both did `split("::")[-1]`, so a same-named test in another
file or class satisfied attribution and a mutation could be reported killed by a module it never
touched — **verbatim AT-311's second failure mode, inside the fix for AT-311.** Names now resolve to
full nodeids at validation, and a name that collects more than once is refused outright.

### AT-322 / AT-323 — two false statements in the report
`collected_nothing` claimed pytest ran nothing about an interrupted run that produced results; it is
now `no_test_results`, true only when no failures were reported. And every survivor was labelled
"vacuous for its property" — the exact phrasing C7's zero-failure clause forbids on that evidence.
Survivors now read **INCONCLUSIVE**.

## What the C2 split exposed, which no finding named

`tests/test_mutation_check.py` hit 310 lines, so it split by responsibility (what the instrument
**refuses** vs what it **concludes**). That immediately exposed a real false-negative: `tests`
accepted a **single file**, so a suite split at the very cap this project enforces would only
half-run — and **a mutation could look survived because the test that notices lives in the other
half.** Same class as everything else here. `tests` now takes a list, with a test and its own
mutation.

## Cycle 3 — the recursive obligation, discharged again

```
13/13 mutations killed        (0 SURVIVED)
```

One mutation per guard, including the four new ones. Every line's `claims to kill` is a subset of
`actually failed`, now in **full nodeids**. The migration spec re-ran unchanged: **4/4 killed**.

The run was repeated **after** the fixture refactor, because the earlier 13/13 measured a tree that
no longer existed — evidence certifies the tree it was measured on, which is AT-288's lesson applied
without being told.

## Cycle 3 verify (re-run after the final edit)

```
$ uv run pytest -o addopts= -q
1077 passed, 2 skipped, 1 warning in 115.23s       exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1   (AT-283 only)

$ scripts/mutation_check.py … mutations-self.json   13/13 mutations killed   exit=0
$ scripts/mutation_check.py … mutations.json         4/4 mutations killed    exit=0
```

## Two defects I caught in my own work this cycle, and how

Recorded because the *how* is the only technique that has worked all session — inspect the artifact,
not the intention:

1. **A 0-byte evidence file.** A backgrounded `&` subshell died with its parent, so a run I was about
   to cite had never executed. Caught by checking the file's SIZE, not the exit code.
2. **A test that passed for the wrong reason.** The first interrupted-run attempt re-indented the
   line into a `SyntaxError`, so `exit == 2` came from a *collection error*, not an interrupt —
   AT-322's exact confusion, reproduced inside the test written to fix it. The assertions now pin the
   reason (`failed` non-empty, `no_test_results is False`), not just the code.

Ruff and doctor each caught one more (F811 on an imported fixture; the 300-line cap).

## What cycle 3 does NOT claim

- **That there is no fifth hole.** The checker has found four in three cycles, in a tool built to
  find exactly this. I have no basis for the claim and am not making it.
- **That the extraction in cycle 2 was necessary.** It was a choice; the mutation existed.
- **AT-308 / AT-309 / AT-319** remain open and untouched.

**If this cycle fails, the unit is `STALLED`** — max cycles reached. `/agent-debugger` runs, its
report goes to `qa/debug/`, and it stops for the human rather than a fourth patch.

## Status: checked-PASS

Checker PASS at cycle 3, `qa/verdicts/at311-mutation-check.md` — 7/7 applicable criteria, all six
verify commands reproduced with attribution checked per-mutation. Cycles 1 and 2 both FAILed.
AT-311 · AT-312 · AT-313 · AT-314 · AT-315 · AT-320 · AT-321 · AT-322 · AT-323 closed.

**The withdrawn general rule is settled.** The checker ruled the withdrawal correct — the rule was
keyed on an unfalsifiable negative and was refuted on the first attempt both times it was asserted
(AT-315, AT-321) — and folded a narrow form into C7 instead: *an unreachability claim is
INCONCLUSIVE, never a justification, and extraction never discharges the mutation duty; the
extracted decision must still be exercised by at least one mutation of its caller.* Stronger than
what I proposed: mine let the claim license skipping the mutation, this one makes the claim worth
nothing and keeps the duty.

**Fifth hole found (AT-324)** — the ambiguity guard's own prescribed remedy was rejected — plus
**AT-325** (1824 leaked sandboxes) plus AT-326 (low) and AT-327 (medium) — duplicate `spec` and C3's
scope over `tests/`, filed for a decision rather than charged — and AT-328 (low), a stale forward
pointer in the cycle-1 block. Both new holes **fail closed**, the opposite direction from all four earlier ones.

AT-324 and AT-325 are addressed in `qa/manifests/at324-mutation-check-leak-and-remedy.md`.
