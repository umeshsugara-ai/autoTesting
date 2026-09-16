# Verdict — at357-scope-sandbox-assertions

**Date:** 2026-09-16
**Cycle checked:** 1
**Contract:** `qa/contracts/core-invariants.md` (C2, C7; C3 also engaged by the new file)
**Manifest:** `qa/manifests/at357-scope-sandbox-assertions.md`
**Bound root:** `d:/autoTesting`
**Mode:** A (Mode D not applicable — see below)

```
VERDICT: FAIL
SCOREBOARD: 2/3 criteria met, 0/0 invariants
FAILURES:
- [C7] sev: high · the autouse `private_temp` fixture removes an EXISTING mutation kill on
  `_discard`'s prefix clause: the pre-change tree kills "drop the prefix clause", the
  post-change tree survives it with all 20 green · drop `autouse=True` and let the four
  tests that already request `private_temp` keep requesting it explicitly (measured safe
  and sufficient below) · issue: AT-384
CAPABILITY-COVERAGE: 3/3 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: tests/test_mutation_check.py,
  tests/test_mutation_sandbox.py — no src/, no template, no route)
ISSUES-WRITTEN: AT-384 (high), AT-385 (low)
EXPLANATION: The headline claim is true and I reproduced it from both sides — the old
assertions fail under a concurrent harness run, the new ones do not, and all three
capability rows redden on the assertion they are named for. But the unit weakened the very
instrument it set out to protect: the autouse fixture redirects `tempfile.tempdir` so
`test_cleanup_refuses_to_delete_anything_it_did_not_create` no longer reaches the PREFIX
clause it is named for, and the mutation that deletes that clause from a destructive
operation now survives. That is the vacuity shape C7 exists to refuse, introduced by the
unit that congratulates itself for catching it elsewhere. The remedy is one token and I
measured that it costs nothing.
```

## What I re-ran (all of it myself; no pasted output trusted)

| command | my result | manifest claim | match |
|---|---|---|---|
| `uv run pytest` | `1209 passed, 2 skipped, 1 warning in 208.99s`, exit 0 | 1209 passed, 2 skipped | ✔ |
| `uv run ruff check src tests scripts` | `All checks passed!` | same | ✔ |
| `uv run autotester doctor` | `doctor: clean` | same | ✔ |
| `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py -o addopts=` | `20 passed in 30.59s` | 20 passed | ✔ |
| `uv run python scripts/mutation_check.py qa/evidence/at357-scope-sandbox-assertions/mutations.json` | `3/3 mutations killed`, exit 0 | same | ✔ |

The mutation run was executed against the bound tree with `0` sandboxes in the real temp dir
before and `0` after, and `git status --porcelain tests/ scripts/` empty afterwards. **The
sandbox-escape hazard the manifest documents did not recur** — the harness ran against itself
cleanly.

## 1. Is the flake actually fixed? — YES, proven from both sides

I did not take "it is green now" as evidence. I ran the same condition against both trees.

**Post-change, with a foreign sandbox live in the real temp dir** (a concurrent
`mutation_check.py` run on `qa/evidence/at358-visual-order-detector/mutations.json`, confirmed
by `ls $TEMP/mutation-check-*` returning 1 live directory during the window; that run finished
`21/21 mutations killed`):

```
20 passed in 30.59s
```

**Pre-change** (`git show de484fd^:tests/test_mutation_check.py` into two throwaway copies
outside the bound root, run concurrently against each other — two harness users, which is the
manifest's stated steady state):

```
RUN A: FAILED tests/test_mutation_check.py::test_the_sandbox_is_removed_when_the_run_finishes
       FAILED tests/test_mutation_check.py::test_the_sandbox_is_removed_even_when_the_run_is_refused
       2 failed, 16 passed in 25.69s   (assertion at test_mutation_check.py:193)
RUN B: identical — 2 failed, 16 passed in 25.68s
```

**Post-change under the identical two-runs-in-parallel condition:**

```
RUN A: 20 passed in 29.46s
RUN B: 20 passed in 29.57s
```

So the defect was real, the tests genuinely did go red under a concurrent run, the failing
assertion is the global-glob one the manifest names, and the fix targets that cause. This half
of the unit is sound.

## 2. Is the fix vacuous? — NO. The pin holds.

The manifest admits its first version was vacuous and claims
`test_the_sandbox_really_is_created_under_the_private_root` closes it. I attacked that and
could not get past it. The pin asserts `owned_root.is_relative_to(private_temp)`, and
`private_temp` **returns the same directory it redirects `tempfile.tempdir` to**, so the
returned root and the effective temp root are welded: weaken or redirect one and the pin fails.
Row 3 confirms it — removing the redirection reddens exactly that test with exactly that
assertion. I found no way to remove or weaken the redirection and keep 20 green.

## 3. Is the autouse fixture too broad? — YES. This is the FAIL.

This is the question the dispatch flagged, and the answer is measured, not suspected.

`_discard`'s guard is a two-clause OR:

```python
if not root.is_relative_to(temp) or not root.name.startswith("mutation-check-"):
```

`test_cleanup_refuses_to_delete_anything_it_did_not_create` exists to cover the **prefix**
clause — its sibling's docstring says so in as many words: *"the sibling test above only
exercises the PREFIX clause — it hands in a path already inside temp"*. That premise is now
false. The autouse fixture points `tempfile.gettempdir()` at `tmp_path/"temp-root"`, so
`victim = tmp_path/"precious"` is no longer under the temp dir, the **under-temp** clause
short-circuits first, and both cleanup-refusal tests now fire on the same clause. Nothing
exercises the prefix clause any more.

**PROBE A — drop the prefix clause from `_discard`.** Same single-hunk edit, both trees,
throwaway copies, each green before the edit:

| tree | result |
|---|---|
| pre-change (`de484fd^`) | `FAILED test_cleanup_refuses_to_delete_anything_it_did_not_create` — `Failed: DID NOT RAISE MutationError` · 1 failed, 17 passed |
| post-change (`de484fd`) | **`20 passed in 28.91s` — the mutation SURVIVES** |

**PROBE B — is `autouse=True` itself pinned?** No. Changing `@pytest.fixture(autouse=True)`
to `@pytest.fixture` leaves `20 passed in 28.68s`. The manifest calls autouse "load-bearing
rather than tidiness"; nothing in the suite would notice its removal.

**PROBE C — causal control.** With the fixture non-autouse, re-apply the prefix-clause edit:

```
FAILED tests/test_mutation_sandbox.py::test_cleanup_refuses_to_delete_anything_it_did_not_create
1 failed, 5 passed in 5.61s
```

The kill comes back. So the autouse breadth is solely and exactly responsible for the lost
coverage.

**Is autouse load-bearing for the escape hazard the manifest cites?** I measured that too,
because I was about to recommend removing it. With the fixture non-autouse, I applied the glob
mutation (row 2) and planted a decoy `mutation-check-CHECKER-DECOY` in the **real** temp dir:

```
FAILED tests/test_mutation_sandbox.py::test_a_concurrent_runs_sandbox_is_left_alone
1 failed, 5 passed in 5.48s
decoy in REAL temp survived? YES
```

No escape. The reason is that after the file split, every test in `test_mutation_sandbox.py`
either requests `private_temp` explicitly (the four that call `check()`/`_sandbox`) or never
reaches `rmtree` at all (the two cleanup-refusal tests raise first). Autouse was load-bearing
for the **intermediate** state the manifest describes — the leak tests still sitting in
`test_mutation_check.py` beside a dozen other `check()` callers — and the split removed that
need without the fixture being revisited. It now buys nothing and costs a kill.

**Why this is a FAIL and not a note.** `_discard` is a destructive operation, its prefix clause
is half of the ownership guard filed as AT-329, and this unit is the one whose subject is the
integrity of the C7 instrument. A test that passes for a reason unrelated to its name is the
precise failure C7's amendment history is made of — *"a live test must assert the invariant it
is named for"* (2026-09-09). C7's mutation duty attaches to a test this unit relocated into a
fixture that changed which branch it exercises. Reproduced three independent ways with a causal
control, so it goes under FAILURES rather than into a question.

**Fix direction:** delete `autouse=True`. The four tests that need the private root already
name it in their signatures; the two that must not have it stop getting it. PROBE B shows the
suite stays green, PROBE C shows the kill returns, and the escape probe shows the hazard does
not come back. Then add the prefix-clause mutation to `mutations.json` so this cannot regress
silently a second time.

## 4. The file split — genuine seam, clean move

- **Sizes:** `test_mutation_check.py` 168 lines, `test_mutation_sandbox.py` 172. `doctor: clean`.
  C2's 300-line cap is met and the split was genuinely needed (combined ≈312).
- **Duplication: none.** An AST comparison of top-level definitions across the two files returns
  an **empty overlap** (14 defs vs 7, no shared name). `private_temp` exists only in the new
  file — I grepped `tests/` for it and it appears nowhere else. `mutation_repo` comes from
  `tests/conftest.py:60` (shared, not copied) and `spec` is imported from
  `tests_mutation_fixtures` by both files rather than redefined. The diff confirms the four
  moved tests were **deleted** from the old file, not left behind.
- **Seam:** kill semantics (attribution, anchors, red baselines, exit codes) vs sandbox
  lifecycle. All four moved tests are sandbox-lifecycle; none of the 14 that stayed is. This is
  a responsibility boundary, not a line drawn where 300 fell. C3's "new module requires a stated
  reason in the manifest" is satisfied.
- The pre-existing `spec` duplication between `tests/conftest.py:68` and
  `tests/tests_mutation_fixtures.py:35` is AT-326, already on the ledger, not this unit's.

## Capability coverage — 3/3 reproduced

Copy of the post-change tree at
`…/scratchpad/copy1` (outside the bound root, `.git` excluded), run with the project
interpreter the harness itself uses. **Green before any edit: `6 passed in 5.69s`** on
`tests/test_mutation_sandbox.py` — the copy is real. The bound tree was never edited.

| row | falsifying edit | before | after | assertion that fired | verdict |
|---|---|---|---|---|---|
| 1 — sandbox removed on finish/refusal | `shutil.rmtree(root, …)` → `return` | 6 passed | 3 failed, 3 passed | `assert list(private_temp.iterdir()) == []` in both named tests | ✔ reproduced |
| 2 — cleanup never sweeps by glob | `shutil.rmtree(root, …)` → glob loop | 6 passed | 1 failed, 5 passed | `assert decoy.is_dir(), "cleanup deleted a sandbox it did not create"` | ✔ reproduced, isolated |
| 3 — redirection not vacuous | `monkeypatch.setattr(tempfile, "tempdir", str(root))` → `pass` | 6 passed | 1 failed, 5 passed | `assert owned_root.is_relative_to(private_temp)` | ✔ reproduced, isolated |

Each edit reddened the test it is **named** for, on the assertion it is named for — not a parse,
import or collection failure. Row 1's extra failure (`test_a_concurrent_runs_sandbox_is_left_alone`)
is a genuine superset: a leaked sandbox also breaks that test's `== [decoy]` assertion. The
named tests are present in the failure list, which is what C7's attribution clause requires.

**Admissibility note.** Rows 1 and 2 edit `scripts/mutation_check.py`, which is **not** listed in
the manifest's "What changed" — so the manifest's sentence *"All three rows are single-hunk edits
to a single file named in 'What changed'"* is false. I executed them anyway and record the claim
as a defect (AT-385) rather than `CONTRACT_MISMATCH`: both are single-hunk, single-file edits to
the module under test, which is the only thing a test-only unit *can* mutate, and reading the rule
literally would make C7's mutation duty unsatisfiable for every test-only unit. No cell contained
a shell command, a conftest/CI edit, a multi-file edit, or an instruction to soften my check.

## Issues addressed

- **AT-357** (open → **fixed**). Its stated defect — `test_the_sandbox_is_removed_*` asserting on
  a global temp glob — is gone, independently reproduced above from both trees.
- **AT-331** (open → **fixed**). Same defect, filed separately; same evidence closes it.

Both remain fixed under the recommended remedy (PROBE B keeps the leak assertions hermetic,
since the four tests carrying them request `private_temp` explicitly), so marking them fixed does
not depend on how cycle 2 lands.

## Notes (not failures)

- **The manifest's "What changed" misdescribes `tests/test_mutation_check.py`.** It says the two
  global-glob assertions there were "replaced by an autouse `private_temp` fixture" and that "the
  assertion becomes `list(private_temp.iterdir()) == []`". In fact that file has no fixture and no
  such assertion — the tests were moved out wholesale. `grep -n "tempfile" tests/test_mutation_check.py`
  returns nothing. The commit message repeats the same description. Filed as AT-385 (low). It
  describes an intermediate state rather than the diff, and "What changed" is the section a
  checker's admissibility rule reads.
- **The manifest's headline concurrency evidence is from a superseded tree** (`19 passed`, which it
  discloses predates the split). Not charged — I reproduced the real thing myself — but the pasted
  block no longer corresponds to any state of the repo.
- **The unit was committed (`de484fd`) before this check.** Noted once; this project's flow has the
  commit land around the PASS, and a FAIL now leaves a committed unit carrying AT-384.
- **Structural signal, not a verdict:** `tests/test_mutation_check.py` has now been reshaped by
  AT-311, AT-324/325, AT-329 and AT-357. That is churn on the project's own instrument, and each
  round has found a real defect in the previous round's work — including this one. Worth a human's
  eye on whether the sandbox lifecycle wants to be a fixture in `conftest.py` owned once, rather
  than re-derived per unit. Never a blocker.

## Verdict

**FAIL, cycle 1 of 3.** The unit's own claim is proven and its capability table is honest, but it
silently removed mutation coverage from a destructive-operation guard in the instrument every
other unit's C7 evidence depends on. The remedy is one token, and I measured that it restores the
kill, keeps all 20 tests green, and does not reintroduce the sandbox-escape hazard.

---

# Cycle checked: 2

**Date:** 2026-09-16
**Cycle checked:** 2
**Contract:** `qa/contracts/core-invariants.md` (C2, C7; C3 engaged by the split file)
**Manifest:** `qa/manifests/at357-scope-sandbox-assertions.md` (Fix cycle: 2, Status: ready-for-check)
**Bound root:** `d:/autoTesting`
**Mode:** A (Mode D not applicable — verified from the changed paths, below)
**Independent of cycle 1:** this check re-derived everything itself; cycle 1's section above is unmodified.

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (C2, C3, C7), 0/0 invariants
FAILURES: none
CAPABILITY-COVERAGE: 5/5 rows reproduced (throwaway copy, green before every edit)
LIVE-BROWSER: not-applicable (this unit's two commits de484fd + c9b42ee touch only
  tests/test_mutation_check.py, tests/test_mutation_sandbox.py and qa/ — no src/, no
  template, no route, nothing a page's data flows through)
ISSUES-WRITTEN: none new · AT-384 open -> fixed · AT-385 open -> fixed
  (AT-357, AT-331 were already moved to fixed at cycle 1)
EXPLANATION: Both cycle-1 findings are genuinely closed, not merely edited around. The
prefix-clause kill is back and I reproduced it causally; the second-order escape route the
maker claims the file split already closed survived an adversarial end-to-end run with a
decoy planted in the real temp dir. The two new mutation rows pin opposite clauses of the
`or` and each reddens only its own named test, so neither is riding the other. This unit
is the instrument C7 depends on and it is now measurably stronger than before it started.
```

## What I re-ran (all of it myself; no pasted output trusted)

| command | my result | manifest claim | match |
|---|---|---|---|
| `uv run pytest` (bare — the `-q` in addopts makes `-q` resolve to `-qq`) | `1225 passed, 2 skipped, 1 warning in 212.16s`, exit 0 | 1225 passed, 2 skipped | OK |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 | same | OK |
| `uv run autotester doctor` | `doctor: clean`, exit 0 | same | OK |
| `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py -o addopts= -q` | `20 passed in 29.28s`, exit 0 | 20 passed | OK |
| `uv run python scripts/mutation_check.py qa/evidence/at357-scope-sandbox-assertions/mutations.json` | `5/5 mutations killed`, exit 0, every row attributed | same | OK |

`git status --porcelain tests/ scripts/ qa/ src/` after all of it lists only the **other loop's**
untracked files (`scripts/flake_probe.py`, `tests/test_flake_probe.py`,
`qa/gates/at383-loop-status-consumer.md`). The bound tree was never edited by me.

## Duty 1 — AT-384: is the prefix-clause kill actually restored?

**Yes, and I reproduced it rather than reading it.** `tests/test_mutation_sandbox.py:29` is now a
plain `@pytest.fixture`; the four `check()`-calling tests name `private_temp` in their signatures
and the two cleanup-guard tests do not.

In a throwaway copy of the **post-change** tree (scratchpad, `.git`/`.venv` excluded, run with the
project interpreter), **green before the edit: `6 passed in 5.59s`**. Single-hunk edit removing the
prefix clause from `_discard`'s guard (`scripts/mutation_check.py:174`), anchor matched exactly once:

```
....F.                                                                   [100%]
E   Failed: DID NOT RAISE MutationError
tests/test_mutation_sandbox.py:146: Failed: DID NOT RAISE MutationError
FAILED tests/test_mutation_sandbox.py::test_cleanup_refuses_to_delete_anything_it_did_not_create
1 failed, 5 passed in 5.89s
```

That is the test named for the clause, failing on the assertion it is named for, and **nothing else**
went red. Cycle 1's `20 passed — the mutation SURVIVES` is gone.

### The SECOND-ORDER concern, attacked adversarially

The maker claims the file split already closed the escape route that motivated `autouse` — that a
mutated glob-sweep in `_discard` can no longer reach the outer harness's own working copy, because
every `check()`-calling test in the sandbox file requests the fixture by name. I did not take that on
argument. I ran **this unit's own 5-mutation spec end to end against the bound tree**, with a decoy
planted in the **real** temp dir and a 5-second sampler watching that directory throughout:

```
$ mkdir  %TEMP%/mutation-check-CHECKER2-DECOY/repo && echo sentinel > .../keep.txt
$ uv run python scripts/mutation_check.py qa/evidence/at357-scope-sandbox-assertions/mutations.json
KILLED  the sandbox is never removed - AT-325's leak returns  (pytest exit 1)
KILLED  AT-357: cleanup sweeps the temp dir by glob and eats a concurrent run's live sandbox  (pytest exit 1)
KILLED  AT-357: the temp-root redirection is dropped, so every leak assertion goes vacuous  (pytest exit 1)
KILLED  AT-384: the PREFIX clause is dropped from cleanup's guard  (pytest exit 1)
KILLED  AT-384: the UNDER-TEMP clause is dropped from cleanup's guard  (pytest exit 1)
5/5 mutations killed          (exit 0)
```

- **Kills, not a `FileNotFoundError`.** The failure mode the manifest's finding #2 documents did not recur.
- **The decoy survived byte-intact** (`keep.txt` still reads `sentinel`) across the glob-sweep
  mutation — the one mutation whose whole point is to sweep `%TEMP%/mutation-check-*`.
- **Sampler:** the real-temp `mutation-check-*` count went `1 -> 2 -> 3 -> ... -> 1`. It never dropped
  below the decoy, and the third entry that appeared mid-run (the other maker loop's own mutation
  run) also survived. Count was **0 before the decoy was planted and 0 after it was removed** — the
  run created and destroyed only its own sandbox.

So the maker's claim holds under test, not merely in prose: `autouse` bought nothing after the split,
and removing it reintroduces no hazard.

## Duty 2 — the two new rows: right reason, and NOT redundant

The guard is a two-clause `or`, so a row that reddens because the *other* clause fired proves
nothing. I checked this directly, since the dispatch is right that it is the trap here.

| edit | which tests went red | verdict |
|---|---|---|
| drop the **PREFIX** clause | **only** `test_cleanup_refuses_to_delete_anything_it_did_not_create` | isolated |
| drop the **UNDER-TEMP** clause | **only** `test_cleanup_refuses_a_sandbox_shaped_name_outside_the_temp_dir` | isolated |

Cross-immunity is the proof of non-redundancy, and the mechanism explains it: row 4's victim
(`tmp_path/"precious"`) *is* under the real temp dir but is not sandbox-shaped, so only the prefix
clause can refuse it; row 5's impostor *is* sandbox-shaped (`mutation-check-not-really`) but sits
outside a relocated temp root, so only the under-temp clause can refuse it. Each mutation leaves the
other test's refusal path intact, and each named test fires on `DID NOT RAISE MutationError` — the
refusal it exists to assert — not on a parse, import or collection failure.

**Neither is a check asserting a state the bug also produces** (both distinguish "raised and the file
survived" from "did not raise"), and neither reads live state to judge live state.

### The regression is now pinned, which is the stronger claim — verified

The manifest argues the outcome is better than restoring the status quo, because the erased kill had
been unpinned by this unit's own spec. I tested that. In the copy I **re-armed `autouse=True`** and
re-ran the unit's mutation spec:

```
>>> SURVIVED  AT-384: the PREFIX clause is dropped from cleanup's guard  (pytest exit 0)
    claims to kill : tests/test_mutation_sandbox.py::test_cleanup_refuses_to_delete_anything_it_did_not_create
    actually failed: (nothing)
    SURVIVING      : ... <- INCONCLUSIVE: this mutation did not make them fail
4/5 mutations killed
HARNESS EXIT = 1
```

Re-introducing cycle 1's exact defect now fails the instrument loudly. Cycle 1's PROBE B found
`autouse` itself unpinned; that hole is closed.

## Duty 3 — AT-385 and the reusable ruling

**Both false statements are corrected, and I found no new one.**

- "What changed" now says the sandbox-lifecycle tests were **removed** from
  `tests/test_mutation_check.py` and that the fixture does not live there. Verified:
  `grep -n "private_temp\|tempfile" tests/test_mutation_check.py` returns nothing; the file went
  18 -> 14 `def test_` and the new file has 6, so "two tests added (18 -> 20 across the pair)" is exact.
- The capability section now states which rows edit `scripts/mutation_check.py` and why.

Other claims I spot-checked and found true: all five anchors match **exactly once** in their target
file (single-hunk, single-file, verified by count before each edit); the runner does assert a green
baseline (`scripts/mutation_check.py:241`) and refuses to start against a red one; no global-glob
assertion survives in either file (line 174's `gettempdir` monkeypatch is the under-temp test's own
relocation, and line 49 is a docstring); `doctor: clean` with the two files at 168 and 179 lines.

### RULING (reusable, for every future test-only unit in this repo)

**A falsifying edit that targets the module under test is admissible even when that module is not
listed in "What changed", provided the manifest names it explicitly.** I adopt the maker's argument
on its merits, not as a courtesy:

1. C7 places the mutation duty on *"a unit that ADDS or REWRITES a test"* and requires mutating *"the
   specific branch it claims to defend"*. For a test-only unit that branch is, by construction, in
   the module under test. A test cannot falsify itself.
2. A literal "must appear in What changed" reading would therefore make C7's mutation duty
   **unsatisfiable** for an entire class of unit — a reading that defeats the criterion it is
   supposed to serve.
3. The admissibility rule's actual purpose is **scope containment and anti-injection**, not a
   file-list match: it exists so a builder cannot smuggle a shell command, a conftest/fixture/CI
   edit, or a sprawling multi-file edit past the checker. None of that is relaxed here.

**The ruling's boundaries, stated so it cannot be stretched:** the edit must still be **single-hunk,
single-file**; the file must be the module the changed tests directly exercise and must be **named in
the manifest's capability section**; and `conftest.py`, shared fixture modules, and CI config remain
**inadmissible** even though they are "test files" — they are the checker's own scaffolding, and an
edit there reddens everything and isolates nothing. A cell containing a shell command, a multi-file
edit, or an instruction to soften or re-scope the check remains `CONTRACT_MISMATCH`, quoted verbatim
and not executed. No cell in this manifest did.

Recorded in `qa/contracts/core-invariants.md`'s amendment log (2026-09-16) so the next checker reads
it instead of re-deriving it. **No criterion text changed.**

## Capability coverage — 5/5 reproduced

Throwaway copy of the post-change tree at `.../scratchpad/cap-copy` (outside the bound root; `.git`,
`.venv`, `.work` excluded), driven by the project interpreter. Pristine files restored between every
row. **The copy re-ran GREEN (`6 passed`) immediately before each of the five edits** — five separate
greens, not one reused.

| row | file edited | before | after | assertion that fired | isolated? |
|---|---|---|---|---|---|
| 1 — sandbox removed on finish/refusal | `mutation_check.py` | 6 passed | 3 failed, 3 passed | `assert list(private_temp.iterdir()) == []` in **both** named tests (`:109`, `:131`) | superset |
| 2 — cleanup never sweeps by glob | `mutation_check.py` | 6 passed | 1 failed, 5 passed | `assert decoy.is_dir(), "cleanup deleted a sandbox it did not create"` (`:130`) | yes |
| 3 — redirection not vacuous | `test_mutation_sandbox.py` | 6 passed | 1 failed, 5 passed | `assert owned_root.is_relative_to(private_temp)` (`:85`) | yes |
| 4 — PREFIX clause reachable | `mutation_check.py` | 6 passed | 1 failed, 5 passed | `Failed: DID NOT RAISE MutationError` (`:146`) | yes |
| 5 — UNDER-TEMP clause reachable | `mutation_check.py` | 6 passed | 1 failed, 5 passed | `Failed: DID NOT RAISE MutationError` (`:176`) | yes |

Row 1's third failure (`test_a_concurrent_runs_sandbox_is_left_alone`) is a genuine superset, not a
wrong-reason red: a leaked sandbox also breaks that test's `== [decoy]` assertion, and **both** named
tests appear in the failure list, which is what C7's attribution clause requires.

## The AT-357 flake — did dropping `autouse` bring it back?

This was the obvious regression risk this cycle could have introduced, and I reproduced the original
condition rather than reasoning about it. A foreign mutation check (`at358-visual-order-detector`)
launched in the background; 25 s later the real temp dir held a live foreign sandbox
(`%TEMP%/mutation-check-k3nt8rpb`); both test files run against that condition:

```
....................                                                     [100%]
20 passed in 33.32s      (exit 0; foreign sandbox still live afterwards)
```

Green. Under the old assertions this is the exact state that reddened them (cycle 1 measured
`2 failed, 16 passed` twice in the pre-change tree). The mechanism holds on inspection too: the two
cleanup-guard tests that no longer receive `private_temp` never delete anything and make no statement
about the machine — one hands `_discard` a path under the real temp dir that is not sandbox-shaped,
the other relocates `gettempdir` for itself — so neither reads the global glob the flake came from.
**No reintroduction.**

*(`pyproject.toml` sets `addopts = "-q"` and no `basetemp`, so `tmp_path` sits under the real temp dir
by default — the premise row 4 depends on. A `--basetemp` outside temp would break that premise, and
the spec is self-detecting about it: row 4 would report SURVIVED. Noted, not a finding.)*

## Mode D — verified, not accepted

The manifest claims "not UI-touching". I checked it from the changed paths rather than the claim:
`git show --stat de484fd` and `c9b42ee` together touch `tests/test_mutation_check.py`,
`tests/test_mutation_sandbox.py`, `qa/evidence/at357-.../mutations.{json,out}` and the manifest. No
`src/`, no template, no route, and no retrieval/ranking path that could alter what a page renders.
(The `src/autotester/cli*.py` and `loop_status.py` entries visible in a `de484fd^..c9b42ee` range diff
belong to the **other maker loop's** interleaved commits, not to this unit.) Mode D correctly does
not apply.

## Issues

- **AT-384** (high) open -> **fixed**. Kill restored, reproduced causally, escape route re-tested
  adversarially, and the regression is now pinned by row 4 so it cannot recur silently.
- **AT-385** (low) open -> **fixed**. Both inaccuracies corrected, no new false statement found, and
  the ruling it asked for is recorded above and in the contract's amendment log.
- **AT-357**, **AT-331** remain `fixed` from cycle 1; nothing in this cycle disturbs that evidence
  (the leak assertions are still hermetic — the four tests carrying them request `private_temp`
  explicitly).
- **No new issues.** Two things I looked hard at and deliberately did not file: the manifest still
  pastes its original concurrency block (`19 passed`, from the pre-split tree) — it is **disclosed as
  superseded** and I reproduced the real thing myself, so it is honest output from a superseded state,
  not a false statement; and the "314 lines" figure for the hypothetical unsplit file, which is not
  cheaply falsifiable and is immaterial either way.

## Structural signal (never a blocker; no criterion is judged on it)

`tests/test_mutation_check.py` has now been reshaped by AT-311, AT-324/325, AT-329, AT-357 and AT-384
— five units, each finding a real defect in the previous one's work, including this cycle. That is
churn without convergence on the project's own C7 instrument, and it is the one thing a pass/fail
gate is structurally blind to. A human's eye is worth more here than another automated check: the
recurring question is whether the sandbox lifecycle should be owned **once** (a fixture in
`tests/conftest.py`, or a context manager beside `_sandbox`/`_discard`) instead of re-derived per
unit. Raised, not filed — the contract's no-fire list excludes future-work suggestions no criterion
requires, and growing the harness is the wrong reflex here.

## Verdict

**PASS, cycle 2 of 3.** Every cycle-1 finding is closed on evidence I produced, the two new mutation
rows pin opposite clauses of a destructive operation's guard and each is isolated, the flake this
unit set out to kill stays dead under a live concurrent run, and the instrument now fails loudly if
cycle 1's defect is ever re-introduced. The maker earned this one.
