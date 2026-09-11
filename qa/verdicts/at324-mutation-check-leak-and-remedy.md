# Verdict — at324-mutation-check-leak-and-remedy

**Date:** 2026-09-11
**Manifest:** `qa/manifests/at324-mutation-check-leak-and-remedy.md` (Fix cycle: 1 of max 3)
**Contract:** `qa/contracts/core-invariants.md` — C7 (kill-attribution · the mutation duty · the
baseline, anchor and zero-failure clauses · the unreachability clause added on the
`at311-mutation-check` cycle-3 verdict), plus C2/C3/C4 via `doctor`
**Commit checked:** `69f2f6c`
**Checker:** fresh Mode A subagent, bound to `D:/autoTesting`
**Cycle checked: 1**

```
VERDICT: PASS
SCOREBOARD: 7/7 applicable criteria met, 0/0 invariants (this contract declares no [I*])
FAILURES: none at >80% confidence
LIVE-BROWSER: not-applicable (changed paths: scripts/mutation_check.py,
  tests/test_mutation_check.py, qa/*. `git show --name-only 69f2f6c` touches nothing under
  src/; `grep -rn mutation_check src/` returns nothing. Mode D is NOT required)
ISSUES-WRITTEN: AT-329, AT-330, AT-331, AT-332
  (status moved: AT-324 open→fixed, AT-325 open→fixed)
EXPLANATION: Both issues I filed on the at311 cycle-3 PASS are genuinely closed in code, and I
verified each by reproducing the exact live collision I named — the full nodeid
`tests/test_providers.py::test_act_without_a_schema_raises` is now accepted where it was refused
as "not collected". All five verify commands reproduce exactly, with kill attribution checked
per-mutation rather than in aggregate. Judgement #1 survives every collision I could build,
including a parametrised id that literally spells another test's nodeid: the two key-spaces are
disjoint by construction, not by an unreachability claim. Judgement #2 (the residual) is accepted
as disclosed — I measured it at 19, not ~38, and a full `pytest -q` now leaks ZERO. Judgement #3
is resolved AGAINST my own cycle-3 figure: the maker's 0.06 GB is right and my ~1.8 GB was wrong.
I found one real coverage gap in the new cleanup guard (AT-329) — a surviving mutation — but C7's
mutation duty is written per-branch and the maker discharged it, so it is filed, not charged.
```

---

## 1. What I re-ran (nothing below is read from the manifest)

| Command | My result | Manifest claim | Match |
|---|---|---|---|
| `uv run pytest -o addopts= -q` | `1081 passed, 2 skipped, 1 warning in 120.53s`, exit 0 | 1081 / 2, exit 0 | yes |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 | exit 0 | yes |
| `uv run autotester doctor` | `root-clutter: AGENTS.md …` / `1 violation(s)`, exit 1 | exit 1, exactly one violation (AT-283) | yes |
| `scripts/mutation_check.py … mutations-self.json` | **16/16 killed, 0 SURVIVED**, exit 0 | 16/16, exit 0 | yes |
| `scripts/mutation_check.py … mutations.json` | **4/4 killed**, exit 0 | 4/4, exit 0 | yes |

**Attribution checked per-mutation, not in aggregate.** For all 20 mutations across the two specs,
`claims to kill` ⊆ `actually failed`, every id on both sides is a full nodeid (never a bare name),
and every run exited **1** — never 2/3/4/5, so no kill is read off a suite that failed to collect.
Three mutations reported collateral failures beyond their claim (`kills-label existence check
removed` also failed `test_the_sandbox_is_removed_even_when_the_run_is_refused`; `attribution
reverted to bare names` failed 7 while claiming 2; `sandbox removed - mutate the live tree` failed
2 while claiming 1). All three are correct and **visible rather than inferred**.

Three of the sixteen are new this unit, one per new guard, and each dies alone:

```
KILLED  nodeid key removed - the guard's own remedy rejected (AT-324)  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_a_kills_entry_may_be_the_full_nodeid_the_guard_asks_for
    actually failed: tests/test_mutation_check.py::test_a_kills_entry_may_be_the_full_nodeid_the_guard_asks_for
KILLED  sandbox cleanup removed (AT-325)  (pytest exit 1)
    claims to kill : …test_the_sandbox_is_removed_even_when_the_run_is_refused, …test_the_sandbox_is_removed_when_the_run_finishes
    actually failed: …test_the_sandbox_is_removed_even_when_the_run_is_refused, …test_the_sandbox_is_removed_when_the_run_finishes
KILLED  cleanup containment check removed (AT-325 footgun)  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_cleanup_refuses_to_delete_anything_it_did_not_create
    actually failed: tests/test_mutation_check.py::test_cleanup_refuses_to_delete_anything_it_did_not_create
```

---

## 2. Priority 1 — AT-324, closed, verified on the live collision I named

I re-ran **the two commands from my own cycle-3 verdict**, against the real repo, on the real
collision (`test_act_without_a_schema_raises` in `tests/test_providers.py:32` and
`tests/test_langchain_fallback.py:186`):

```
=== BARE NAME (the ambiguous one) ===
MutationError: mutation 'probe' names test(s) that collect more than once:
  {'test_act_without_a_schema_raises': ['tests/test_langchain_fallback.py::test_act_without_a_schema_raises',
                                        'tests/test_providers.py::test_act_without_a_schema_raises']}.
  A bare name is not an identifier — name the full nodeid.

=== FULL NODEID (the guard's prescribed remedy) ===
MutationError: mutation 'probe': anchor matched 0 times in scripts/mutation_check.py (need exactly 1)
```

The second spelling now travels **past** the `not collected` check, past the ambiguity check, and
past the green-baseline assertion, dying only on my own deliberately bogus anchor. At `baf56a1` it
died at `names test(s) that are not collected`. **The guard's own printed instruction is now
executable.** AT-324 closed.

### Attack on judgement #1 — "two entries per test could collide"

The maker judged a collision unreachable and asked me to attack it. I did, three ways.

**(a) By construction — and this is a proof, not an unreachability claim.** The bare key is
`nodeid.split("::")[-1]`, which cannot contain `::`; the nodeid key is admitted only by
`if "::" in nodeid`, so it always does. The two key-spaces are **disjoint by the two lines that
build them** (`scripts/mutation_check.py:118-125`). This matters for C7's unreachability clause:
the clause forbids resting on *"no mutation can reach this"*, an unfalsifiable negative. This claim
is falsifiable and I tried to falsify it — see (b) and (c) — and it is additionally backed by a
mutation of the caller (`nodeid key removed …`, killed above). The clause is satisfied.

**(b) Measured over the whole suite** (`collected_tests(REPO, "tests")`):

```
total keys=2165  bare=1082  full-nodeid=1083
key-space intersection (bare keys that are also full nodeids): set()
any bare key containing '::'? []
any full-nodeid key whose value set has len>1? []
ambiguous bare names still flagged: 1  -> ['test_act_without_a_schema_raises']
```

1083 vs 1082 is the one collapsed ambiguous bare name. The AT-320 ambiguity guard is **not**
weakened by the second key: it still fires on exactly the name it fired on before.

**(c) The nastiest synthetic I could build** — a parametrised id whose *parameter value is another
test's full nodeid*, in a file that also has a bare/class-method name clash:

```
'test_q[plain]'                                          -> ['tests/test_mod.py::test_q[plain]']
'test_r'                                                 -> ['tests/test_mod.py::TestA::test_r', 'tests/test_mod.py::test_r']
'test_r]'                                                -> ['tests/test_mod.py::test_q[tests/test_mod.py::test_r]']
'tests/test_mod.py::TestA::test_r'                       -> ['tests/test_mod.py::TestA::test_r']
'tests/test_mod.py::test_q[tests/test_mod.py::test_r]'   -> ['tests/test_mod.py::test_q[tests/test_mod.py::test_r]']
'tests/test_mod.py::test_r'                              -> ['tests/test_mod.py::test_r']
INTERSECTION: set()
```

No collision. **No false-KILL path.** `_nodeids` is `next(iter(collected[t]))` over a set the
ambiguity guard has already proved to be a singleton, so a bare name still cannot attribute to two
places, and a full nodeid maps only to itself.

**Ruling on judgement #1: upheld, and the fix is strictly better than the maker claims.** In case
(c) the bare name `test_r` was previously refused with *no legal spelling at all* — the exact
AT-324 dead end. Both `tests/test_mod.py::TestA::test_r` and `tests/test_mod.py::test_r` are now
legal. One spelling is still missing (`TestA::test_r`, the intermediate form), which is refused as
"not collected"; the message says *"name the full nodeid"*, so the author is pointed at a spelling
that works. Not a defect.

---

## 3. Priority 2 — AT-325, the footgun, and whether the maker's account of it is true

### 3a. Is the claim "the SELF-MUTATION caught this, not a checker" flattery?

Two halves, judged separately.

**The verifiable half is true.** The committed `_discard` really does refuse an uncreated path, and
I proved it on six targets rather than reading the maker's test:

| Probe | Target | Result | Survived? |
|---|---|---|---|
| A1 | `$TEMP/precious-…` (under temp, wrong name) | **REFUSED** | contents intact |
| A2 | `D:/autoTesting/.work/mutation-check-decoy` (right name, outside temp) | **REFUSED** | contents intact |
| A3 | `$TEMP/mutation-check-…` created by someone else | **DELETED** | — see AT-329 |
| A4 | `D:/autoTesting` (the live repo root) | **REFUSED** | repo intact |
| A5 | `D:/` (the live repo's PARENT — the footgun's target) | **REFUSED** | repo intact |
| A6 | `$TEMP/mutation-check-symlink` → a real tree | **REFUSED** (`resolve()` runs before the check, so the symlink cannot be used to escape) | target intact |

**And the `work = repo` mutation genuinely kills its test today** — I did not read this, I ran it:

```
KILLED  sandbox removed - mutate the live tree  (pytest exit 1)
    claims to kill : tests/test_mutation_check.py::test_the_live_tree_is_never_touched
    actually failed: tests/test_mutation_check.py::test_the_live_tree_is_never_touched,
                     tests/test_mutation_check_judgement.py::test_it_refuses_an_absolute_file_path
```

**The unverifiable half stays unverifiable, and I am saying so rather than crediting it.** The
first fix (`shutil.rmtree(work.parent, ignore_errors=True)`) was never committed — `69f2f6c` is the
only commit — so the record contains no `>>> SURVIVED sandbox removed - mutate the live tree`
line and I cannot confirm the instrument beat me to it. The account is *coherent* (a `work = repo`
mutation plus `rmtree(work.parent)` does make cleanup delete a directory it does not own) and its
outcome is on disk. I neither charge it nor certify it.

**One precision correction to the narrative**, because the manifest overstates the blast radius:
under the mutated code, `work` is whatever `repo` argument the inner tests pass, which is the
`mutation_repo` **tmp_path fixture** — so `work.parent` would have been pytest's tmp base, not
`D:/`. Destructive, and the right class of defect (AT-314 again); not "the real tree's parent"
unless the mutation had been committed as real code. The class is what matters and the class is
correctly named.

### 3b. Attacks on `_discard` itself — the four axes the dispatch named

- **Symlinked temp dir (A6).** Safe, and safe for the right reason: `owned_root.resolve()` runs
  **before** the containment check (`mutation_check.py:168`), so a symlink under temp pointing at a
  real tree resolves to the real tree's name and is refused. macOS `/tmp` → `/private/tmp` is the
  same shape and is handled because *both* sides are `.resolve()`d. On Windows this also normalises
  8.3 short names on both sides; `gettempdir()` and `resolve()` agreed exactly on this machine
  (`C:\Users\Lenovo\AppData\Local\Temp`).
- **`TMPDIR` pointing inside the repo (A7).** Forced `tempfile.tempdir` to
  `D:/autoTesting/.work/faketmp`: the sandbox was created there and `_discard` removed **only** the
  directory it made; `pyproject.toml` and the repo were intact afterwards. The guard degrades
  correctly — it is relative to wherever temp *is*, not to a hardcoded root. (A misconfigured
  `TMPDIR` inside the repo has a separate consequence — the sandbox copy would be visible to the
  outer `pytest -q` collection and to C4's root-clutter rule — but that is a property of the
  misconfiguration, not of this unit, and `_inside` still contains every mutation.)
- **A `mutation-check-*` name sitting elsewhere (A2/A4/A5).** Refused. This is the clause the
  footgun turned on, and it holds.
- **`gettempdir()` differing between caller and module (A8).** Within one process it cannot:
  `tempfile.gettempdir()` caches into `tempfile.tempdir`, and `mkdtemp` reads the same value.
  Forcing it to move mid-run makes `_discard` **refuse**, which fails closed — but see AT-330: the
  refusal is raised from inside `check()`'s `finally`, so it replaces the run's real result.

### 3c. The one real gap — a surviving mutation (AT-329, filed, not charged)

`_discard`'s guard is a two-clause `or`, and the committed test defends only one of them. The
committed test hands `_discard` a `tmp_path / "precious"`, which is **inside** temp, so it can only
exercise the *name* clause. I mutated each clause separately, in the project's own instrument:

```
>>> SURVIVED  CHECKER: drop ONLY the under-temp clause of _discard  (pytest exit 0)
    claims to kill : tests/test_mutation_check.py::test_cleanup_refuses_to_delete_anything_it_did_not_create
    actually failed: (nothing)
KILLED      CHECKER: drop ONLY the prefix clause of _discard  (pytest exit 1)
1/2 mutations killed
```

**This survivor is not INCONCLUSIVE**, and I am discharging C7's zero-failure clause on my own
finding rather than leaning on it: I showed the mutation changes behaviour, directly. Under the
mutated predicate, probe A2's out-of-temp `mutation-check-decoy2` is **deleted**; under the
committed predicate it is **refused**. The behaviour moves and no test notices.

**Why this is filed and not charged.** C7's mutation duty reads *"mutate the specific branch it
claims to defend and require at least one failure"*. The branch is the `if`; the maker mutated it
and got an attributed kill. Requiring one mutation per *clause* of a compound condition would be
strengthening a criterion mid-verdict to fail an artifact, which the checker's one absolute forbids
in exactly the same way it forbids softening one. It is worth noting that this file already holds
the better standard voluntarily — `is_kill`'s docstring says *"Both clauses are load-bearing and
neither implies the other"* and the spec gives it **two** mutations (entries 6 and 7) — so the
remedy is one the maker already knows how to write. **AT-329 (medium).** The fix is ~6 lines: a
test handing `_discard` an out-of-temp `mutation-check-*` path (my A2), plus a second spec entry.

AT-329 also carries the docstring half: `_discard` promises *"the only deletable thing is the
directory this module made"*, but the code enforces **under-temp AND our prefix**, which is
ownership by convention, not by creation. Probe A3 shows a `mutation-check-*` directory created by
a *different process* is deleted without complaint. No live path reaches it — `_discard` has one
caller and it passes `mkdtemp` output — so this is a promise the code does not enforce, which is
the C9 shape and the same sentence `_inside`'s own docstring warns about.

---

## 4. Ruling on judgement #2 — the ~38-sandbox residual

**The disclosure is ACCEPTABLE. It does not have to be closed now.** Three reasons, measured:

1. **It is smaller than disclosed, and I measured it rather than accepting the estimate.** Sandbox
   count immediately before my self-mutation run: **0**. Immediately after: **19**, not ~38. The
   manifest over-states its own residue, which is the conservative direction.
2. **The structural half of AT-325 is fully closed.** The thing that made the leak grow with every
   unit was that *every* `check()` leaked, and the suite calls `check()` ~15 times. After a
   complete `uv run pytest -o addopts= -q`, I counted `mutation-check-*` trees in `$TEMP`: **0**.
   The residue now requires someone to *deliberately mutate cleanup off*, which happens only in
   this one self-spec, run rarely and by hand.
3. **The rejection reasoning is correct, and my own probe proves it.** The maker rejected an
   end-of-run global sweep because a concurrently running checker's sandbox could be deleted.
   Probe A3 is that exact scenario executed: a `mutation-check-*` directory under temp created by
   another process, deleted without complaint. A global sweep would be a destructive operation on
   an unverified target — AT-314 a third time — and trading a bounded 19-directory residue for that
   is a bad trade.

**If it is ever closed, the shape I want is the one the maker already named, made concrete:**
ownership by construction, never by glob. `check()` exports the run's `owned_root` in the
environment (e.g. `MUTATION_CHECK_OWNED_DIR`) for the duration of the run; `_sandbox` creates its
temp directory *inside* that value when it is set, and falls back to `mkdtemp()` when it is not.
Every nested sandbox then lives under the outer run's own root, the outer `finally: _discard` takes
all of them in one `rmtree`, the containment guard is unchanged (the outer root is still a
`mkdtemp` under temp with the prefix), and **no other process's directory is ever a candidate.**
That is a unit of its own; nothing in C7 requires it, and this unit should not grow to hold it.

---

## 5. Ruling on judgement #3 — the size discrepancy. It is resolvable, and I was wrong.

**The maker's 0.06 GB is right. My cycle-3 figure of ~1.8 GB was wrong.** I can say this even
though both populations are deleted, because the *unit sizes* are reproducible today:

```
full-repo sandbox :   250 files   1426.4 KB  (1.39 MB)   <- what a CLI run creates
fixture sandbox   :     2 files      0.0 KB              <- what tests/test_mutation_check*.py create, ~15x per suite run
1824 x full-repo  =  2.481 GB
1824 x fixture    =  0.000 GB
```

**What I measured wrongly, precisely:** I sampled 20 directories, got ~1 MB each, and multiplied
across all 1824. That per-directory figure is correct — for a *CLI* sandbox, which copies the real
`src/ tests/ scripts/`. But the population of 1824 is dominated by **fixture** sandboxes: the tests
call `check()` with a synthetic two-file `mutation_repo`, so their sandboxes are ~0 KB. My sample
was not representative of the population, and the extrapolation inherited the error. Arithmetic
check in the maker's favour: ~40 CLI runs × 1.39 MB ≈ 0.056 GB, which lands on the measured
0.06 GB almost exactly.

**Severity is unchanged and the maker's judgement of it was right on the right number.** What made
AT-325 worth fixing was never the bytes — it was the *count* (1824 directory entries, agreed by
both of us) and the *rate*, which C7's mutation duty had just made structural. AT-325's ledger row
carries my wrong figure in its evidence field; I have appended a correction to it as its writer.

---

## 6. Rulings on the manifest's remaining judgement

**#4 — AT-326 / AT-327 deliberately not addressed.** Correct, and they stay open. Both were filed
for a decision, not for a fix: AT-327 (C3's text is wider than C3's gate — `doctor`'s duplicate
rule globs `src/` only, while `tests/` holds 29 duplicated public top-level names) is a contract
question, and answering it inside a fix unit would be the maker writing its own rule. They remain
`open`, unqueued here.

---

## 7. Attacks that found nothing (recorded so they are not re-run)

| Probe | Result |
|---|---|
| Can the bare key and the nodeid key ever collide? | No — disjoint by construction, verified over 2165 real keys and a hostile synthetic |
| Does the second key weaken the AT-320 ambiguity guard? | No — the ambiguous set is built by `.add` on the bare key alone; still exactly 1 ambiguous name in the repo |
| Can a full nodeid resolve `_nodeids` to something else? | No — `collected[nodeid] == {nodeid}`, a singleton by construction |
| Can `_discard` be aimed at the repo, its parent, or `/`? | No — A2/A4/A5 all refused |
| Can a symlink walk the guard out of temp? | No — `resolve()` precedes the check |
| Does a repo-internal `TMPDIR` break containment? | No — A7 deleted only its own creation |
| Does a full `pytest -q` still leak? | **No — 0 sandboxes after a complete suite run** |
| Is `projects/erp/screenmap.json` touched? | No — see §8 |

---

## 8. Protected state — confirmed unchanged

- `projects/erp/screenmap.json` — untracked, md5 **`4a73116d792b26226bc499be43b4cd8b`** (byte-identical
  to the cycle-3 verdict's recorded hash), still carries **3** `"url_pattern":
  "/vidysea.com/erp/trainers"` rows. **The migration was NOT run.**
- `qa/gates/t135-url-pattern-data-migration.md:68` still reads
  `_(unanswered — append `Answered: <ISO date> — <choice> — <where>` below before acting)_`.
  **The T-135 gate is unanswered**, and nothing in this unit or its commit message answered it
  off-disk.
- `git show --name-only 69f2f6c` touches only `qa/`, `scripts/mutation_check.py` and
  `tests/test_mutation_check.py`. No `src/`, no UI, no `projects/` data.
- `git status --porcelain` after all my probes is byte-identical to before them (the two `.goal/`
  modifications are another session's in-flight work, untouched by me).

## 9. Mode D — explicitly NOT required

The manifest claims "Not UI-touching". **Verified, from the changed paths rather than from the
adapter and rather than from the manifest's say-so** (D-024): `69f2f6c` changes
`scripts/mutation_check.py`, `tests/test_mutation_check.py` and files under `qa/` — nothing under
`src/`, so nothing under `src/autotester/ui/`. `grep -rn mutation_check src/` returns nothing, so
there is no indirect surface either: no retrieval, ranking, or rendering path can reach this
module. This is a developer-facing script invoked from a terminal and from `tests/`. **Mode D is
not required, and its absence is not a gap in this PASS.**

## 10. The `at311-mutation-check` close-out — correctly closed, with one severity misstatement

- **Status is `checked-PASS`** and cites `qa/verdicts/at311-mutation-check.md`, cycle 3. Correct.
- **"7/7 applicable criteria"** matches my cycle-3 scoreboard line verbatim. Correct.
- **"Cycles 1 and 2 both FAILed"** — correct.
- **The C7 unreachability clause is quoted accurately.** The close-out renders it as *"an
  unreachability claim is INCONCLUSIVE, never a justification, and extraction never discharges the
  mutation duty; the extracted decision must still be exercised by at least one mutation of its
  caller"*, against the contract's *"…must still be exercised end-to-end by at least one mutation
  of its CALLER, or the property is recorded as unproven."* No drift, and the maker's gloss
  ("stronger than what I proposed: mine let the claim license skipping the mutation, this one makes
  the claim worth nothing and keeps the duty") is a fair reading of the ruling, not a softening of
  it. **The close-out does not misstate my cycle-3 ruling.**
- **One misstatement, filed as AT-332 (low).** The close-out calls AT-326/AT-327/AT-328 "three low
  residuals". **AT-327 is medium**, in both my cycle-3 verdict and the C7 amendment log. A
  close-out that downgrades a checker-assigned severity is the C9 shape applied to the ledger — a
  declared control value silently replaced by a weaker one — in the repo whose C9 exists for
  exactly that. Cosmetic in effect (the ledger row itself is correct at `medium`), so: low.

## 11. Two things recorded, not charged

- **AT-330 (low) — a `_discard` refusal inside `finally` replaces the run's real result.**
  `check()` (`mutation_check.py:204-208`) calls `_discard` in a `finally`, so a raised
  `MutationError` from cleanup supersedes both a successful return and any original
  `MutationError`, which survives only as `__context__` and is never printed by `main()`.
  Demonstrated in isolation. Reachable only if `gettempdir()` moves mid-run, so it is narrow and it
  fails closed — the user sees `MUTATION RUN INVALID: refusing to delete …` rather than a false
  KILLED — but the real diagnosis is lost and the sandbox leaks anyway. One `except MutationError`
  around the cleanup, re-raised only when nothing else is in flight, closes it.
- **AT-331 (low) — the two new sandbox-count tests are cross-process fragile.**
  `test_the_sandbox_is_removed_when_the_run_finishes` and `…_even_when_the_run_is_refused` snapshot
  `glob("mutation-check-*")` in the shared system temp dir and assert set equality. A second
  process running this instrument during that window — which is exactly what the maker-checker pair
  does, and what I did to this repo today — makes them fail on a foreign directory. No xdist is
  configured, so the in-process risk is nil. The failure direction is a **false FAIL**, never a
  false PASS, same as AT-196. The fix is to assert on the run's *own* `owned_root` rather than on a
  glob of shared temp, and it composes with the AT-325 residual shape in §4.

## 12. What PASS here does and does not mean

It means both issues I filed on the cycle-3 PASS are closed in code, verified on the live collision
I named rather than on a synthetic, with every verify command reproduced and every kill attributed
per-mutation to a full nodeid. It means the new destructive operation is contained on every axis I
could attack — the repo, its parent, a symlink, and a relocated temp — and that the instrument now
cleans up after itself completely on a normal suite run.

It does not mean the cleanup guard is fully defended: half of its condition survives a mutation
(AT-329), and that is a real gap that the next test-adding unit should close. It also means I am
correcting one of my own numbers: the leak was 0.06 GB, not 1.8 GB, and the maker was right to
refuse to repeat a figure it could not reproduce.

**Goal wiring:** the manifest declares `Goal task: none`, so nothing to close. `.goal/goal.json`
and `.goal/dashboard.html` are modified in the working tree by another session's in-flight work and
a checker does not rewrite state it did not author — not refreshed, deliberately, same as cycle 3.

**Residue left by this check:** 19 `mutation-check-*` trees in `$TEMP` from the self-spec's
cleanup-disabling mutations (the disclosed residual of §4), left in place as the evidence for that
measurement.
