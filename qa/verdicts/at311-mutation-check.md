# Verdict — at311-mutation-check

**Date:** 2026-09-11
**Manifest:** `qa/manifests/at311-mutation-check.md`
**Contract:** `qa/contracts/core-invariants.md` (C7, incl. the kill-attribution + mutation-duty
clauses amended on the `at306-verification-artifact-integrity` verdict)
**Commit checked:** `55efeac`
**Cycle checked: 1**

```
VERDICT: FAIL
SCOREBOARD: 6/7 applicable criteria met, 0/0 invariants (this contract declares no [I*])
FAILURES:
- [C7] sev: high · An EMPTY `kills` list returns the instrument to the exact AT-311 semantics it
  was built to end — a kill becomes "some test failed", attributed to nothing · refuse a
  missing/empty `kills` where the not-collected refusal already lives · issue: AT-313
- [C7] sev: high · Sandbox containment is not enforced on `mutation["file"]`: an absolute path
  collapses the `work / file` join and the harness mutates a file OUTSIDE its sandbox (reproduced
  against a decoy), reporting SURVIVED because the sandboxed suite never saw it · resolve the
  target and refuse unless `work` is a parent · issue: AT-314
- [C7] sev: medium · The `code == 1` half of the kill test is undefended: `killed = code != 0 and
  not survivors` SURVIVES all 12 tests, so
  `test_a_mutation_that_breaks_collection_is_not_a_kill` passes for the *survivors* reason, not
  the exit-code reason it is named for — vacuous for its named property, which is what C7's
  mutation duty exists to catch. Three further checker mutations also survive · add cases that
  separate the two conditions · issue: AT-315
LIVE-BROWSER: not-applicable (changed paths: scripts/, tests/, qa/ — no src/autotester/ui/,
and `grep -rn mutation_check src/` returns nothing; Mode D is NOT required)
ISSUES-WRITTEN: AT-313, AT-314, AT-315, AT-316, AT-317, AT-318, AT-319 (and AT-311, AT-312 →
fixed). AT-319 is PRE-EXISTING and not chargeable to this unit — see §8.
EXPLANATION: The instrument does what it says on its documented path — I reproduced 5/5 and 4/4
independently and every attribution line matches, and the four refusals the manifest lists are all
real. But this unit's own framing is that the instrument is now a GATE, and a gate is judged on
its undocumented paths. Two of them let a kill be reported with no attribution at all or let a
mutation reach outside the sandbox, and a third leaves the unit's headline property — "a kill is
exit 1, not any non-zero exit" — undefended by its own suite. All three are one-line fixes with
reproductions below. The manifest's pasted outputs, the AT-311 grep evidence, and every
protected-state claim reproduced exactly.
```

---

## 1. What I re-ran (nothing here is read from the manifest)

| Command | Manifest claim | My result |
|---|---|---|
| `uv run pytest -o addopts= -q` | 1066 passed, 2 skipped, exit 0 | **1066 passed, 2 skipped, 1 warning in 105.14s, exit 0** ✓ |
| `uv run ruff check src tests scripts` | exit 0 | `All checks passed!`, **exit 0** ✓ |
| `uv run autotester doctor` | exit 1, exactly one violation (AGENTS.md) | `root-clutter: AGENTS.md …` / `1 violation(s)`, **exit 1** ✓ |
| `mutation_check.py … mutations-self.json` | 5/5 killed, exit 0 | **5/5 mutations killed, exit 0** ✓ |
| `mutation_check.py … mutations.json` | 4/4 killed, exit 0 | **4/4 mutations killed, exit 0** ✓ |
| `grep -c test_a_file_nested_below_…_judged_by_it tests/test_migrate_url_patterns.py` | 0 | **0** ✓ |

**Attribution verified line by line, not in aggregate.** In all nine mutations the
`claims to kill` line and the `actually failed` line are identical sets — including M4 of the
migration spec, whose old harness label was the nonexistent test. The AT-311 record is now
independently established: the old label named a test that does not exist (grep → 0), and the test
that genuinely dies under M4 is `test_a_nested_artifact_under_a_flat_root_is_still_judged_by_its_project`.

**Doctor's one violation** (`AGENTS.md`, AT-283) is pre-existing and untracked, declared up front
by the manifest, and identical to the state under which `at306` was PASSed. Not charged here.

**Suite cost.** 105.14s against the 86–87s recorded for the 1042-test suite. I timed the new file
alone: `tests/test_mutation_check.py` → **12 passed in 18.26s**. So the disclosed "~17s slower" is
accurate and, if anything, slightly understated. **Judged acceptable and honestly disclosed**: the
cost buys real subprocess evidence, and a mocked pytest would reproduce the exact defect Mode D's
charter names — a test that mocks the component under test says nothing about it. Recorded, not
charged (see AT-318 note on where this may want a marker later).

---

## 2. The failures, with reproductions

### [C7-a] An empty `kills` list is an unattributed kill — AT-313 (high)

`killed = code == 1 and not survivors`. With `kills: []`, `expected` is empty, so `survivors` is
always empty and the verdict degenerates to `code == 1` — "any test in the selection failed".

Reproduced against a synthetic two-test module, mutating a branch the *other* test defends:

```
ATTACK A2 (kills: [], mutation the named-property test does not defend)
  killed=True exit=1 expected=[] failed=['test_big_values_are_big']
```

A kill, claimed by nothing, attributed to a test that asserts nothing about the mutation. That is
verbatim the AT-311 finding — *"an unrelated test failing counted as proof that this test
noticed"* — reachable in the replacement built to close it. The instrument refuses a `kills` name
that does not exist but accepts no name at all, and the refusal family exists precisely because a
label nobody compares against is a comment. An empty label is that label's limit case.

Not a guaranteed kill and not a guaranteed survival, to answer the question exactly: `kills: []`
plus a collection error is correctly **not** a kill (`A3`: exit 2, killed=False) — the `code == 1`
clause still holds that line. It is the *unrelated-failure* half of AT-311 that reopens, and a
flake landing during the mutation run is enough to trip it.

**Fix:** raise `MutationError` on a missing or empty `kills`, in the same loop as the
not-collected check, before the baseline runs.

### [C7-b] A mutation can escape the sandbox — AT-314 (high)

`target = work / mutation["file"]` performs no containment check, and `pathlib` join semantics
mean an absolute path **discards** `work` entirely:

```
sandbox: C:\...\Temp\mutation-check-2zml3yz7\repo
join(absolute) -> C:\...\Temp\LIVETREE-x7tygo1c\victim.py      # work is gone
join(../..)    -> C:\...\Temp\escaped.py
```

Both were driven end to end. With an absolute `file`, the harness read, mutated, and rewrote a
file outside its sandbox, then reported `killed=False exit=0` — because the mutation landed
somewhere the sandboxed suite never imports. A `../../` path onto an existing outside file did the
same (`ATTACK C2`: the harness "happily mutated a file OUTSIDE its sandbox"); onto a nonexistent
one it raises a bare `FileNotFoundError` rather than a `MutationError`, so the run dies with an
unhandled traceback instead of a refusal.

So `_sandbox`'s docstring — *"A copy OUTSIDE the repo, so a mutation can never touch the live
tree"* — and the manifest's *"Mutations run in a `copytree` outside the repo"* are both stronger
than the code. `tests/test_the_live_tree_is_never_touched` does not catch it because it only
exercises a well-formed relative path.

The certification direction is safe (a false SURVIVED, never a false KILLED). The damage direction
is not: a live-tree file is rewritten, and if the process dies between the mutation write and the
restore it stays mutated. In a repo whose AT-149/AT-150 history is path containment, this is the
finding that most deserves a test.

**Fix:** `target = (work / mutation["file"]).resolve()`; refuse unless `work.resolve()` is among
its parents. One line each, and the mutation that kills the new test writes itself.

### [C7-c] The unit's headline property is undefended by its own suite — AT-315 (medium)

C7 obliges a test-adding unit to mutate the branch each new test claims to defend. I pointed the
instrument at itself with four mutations of my own. **All four survived:**

```
>>> SURVIVED  CHECKER-M1: kill re-admits ANY non-zero exit (the AT-311 defect, restored)
>>> SURVIVED  CHECKER-M2: restore-verification removed
>>> SURVIVED  CHECKER-M3: collected_nothing narrowed to exit 2 only (3/4/5 mislabelled)
>>> SURVIVED  CHECKER-M4: sandbox stops copying src/ (src mutations become no-ops)
0/4 mutations killed
```

**M1 is the one that matters.** `killed = code == 1` → `killed = code != 0` survives, because every
non-1 exit the suite exercises *also* has a non-empty `survivors` set. So
`test_a_mutation_that_breaks_collection_is_not_a_kill` — the test named for "an exit code is not a
kill" — passes for the survivors reason, and would keep passing with the exit-code discipline
deleted. It is vacuous for the property in its own name. That is not a hypothetical: combined with
AT-313, M1 makes a collection error a kill outright.

M2 (nothing asserts the restore-verification exists), M3 (exits 3/4/5 never exercised) and M4
(nothing proves `src/` reaches the sandbox) are the same shape, one tier down.

The maker's five self-mutations are all real and all killed — this is not a claim that the self-run
was faked. It is that the mutation set was chosen from the refusals the maker had just written,
and the branch that decides what a kill *is* was not among them.

---

## 3. Attacks that found nothing (recorded so they are not re-run)

- **Two mutations in one spec, same file, sequential.** No residue. `original` is re-read per
  mutation and the restore is verified between them; both killed and attributed correctly.
- **`pyproject.toml` / `conftest.py` absent.** Handled — every synthetic repo above has neither.
  This repo has no root `conftest.py` at all, so only `pyproject.toml` is copied.
- **A mutated `src/` file is genuinely imported by the sandboxed run.** I expected the editable
  install (`.venv/…/autotester.pth` → `D:\autoTesting\src`) to shadow the copy and make every
  `src/` mutation a silent no-op. **It does not** — I forced a syntax error into
  `src/autotester/schema/base.py` and the traceback names the temp path:
  `E File "C:\...\Temp\mutation-check-hkl3218q\repo\src\autotester\schema\base.py", line 20`.
  Hypothesis disproved; the sandbox is real for `src/` too.
- **A non-deterministic test (the AT-196 shape) across baseline and mutation.** A flake landing on
  the *baseline* refuses the whole run — the safe direction, and exactly what AT-307 bought. A
  flake landing during the *mutation* run co-fails alongside a genuine kill without disturbing the
  verdict (`failed=['test_flaky','test_small_values_are_small']`, killed=True, correctly
  attributed). No false-PASS path except via AT-313.
- **A narrow `tests` selector (a bare `::nodeid`).** Works and attributes honestly. It does narrow
  what "baseline green" covers to the selection, but a narrow selector cannot manufacture a kill —
  the named test still has to fail. Not a finding.
- **Performance.** `_sandbox` over the real repo: 268 entries in **0.14s**. `src/` being large is
  not a concern here.

## 4. One limitation worth stating rather than filing as a defect — AT-317 (low)

"The named test failed" is **necessary but not sufficient**, and I proved it: a mutation replacing
an unrelated helper's body with `raise RuntimeError("unrelated")` killed the named test
(`killed=True`, `failed=['test_big_values_are_big','test_small_values_are_small']`). The
instrument shows a test is sensitive to *some* change in that file, not that it defends the
property it is named for. No instrument can close that — C7 puts the discipline on the human
choosing the mutation, and it should stay there.

But the run has the signal and discards it: in that example a test the spec never claimed also
failed, and nothing said so. **Recommendation** (not a criterion, not required to close this
unit): print `unexpected also-failed: …` when `failures - expected` is non-empty. It would have
surfaced the collateral break above and the flake in §3 at zero cost.

## 5. Rulings on the four judgements offered

**#1 — the superseded harness under `qa/evidence/at300-…/mutation_harness.py`.** Leave it
**byte-untouched**; the maker's instinct is correct and it is the same reasoning that made AT-306's
gate edits acceptable and closed-unit evidence off-limits. Editing a PASSed unit's evidence to
annotate it makes the record say something it did not say at the time. The manifest is *not* quite
enough on its own, though, because a future maker reaches for the file before the manifest. I have
put the supersession pointer where that maker actually looks — the **AT-312 ledger row**, which is
checker-owned and closed by this unit. Record is now three-deep (manifest · this verdict · ledger)
with the artifact untouched.

**#2 — `sys.executable -m pytest` rather than `uv run`. UPHELD, and for a stronger reason than the
one offered.** This is not a toss-up about interpreters; `uv run` would be actively wrong. `uv`
resolves its project from the **current working directory**, and `_sandbox` copies `pyproject.toml`
into the sandbox — so a `uv run` executed with `cwd=work` binds to the *sandbox* as a project, not
this repo. Measured:

```
$ cd <tmp with the copied pyproject.toml> && uv run --no-sync python -c "print(sys.prefix)"
Using CPython 3.12.13
Creating virtual environment at: .venv
sys.prefix= C:\Users\Lenovo\AppData\Local\Temp\tmp.qg8QaxzefD\.venv
```

Every mutation run would execute against a **fresh, empty, differently-resolved environment**, and
would litter the sandbox with a `.venv` on the way. Inheriting the caller's interpreter is the only
correct choice. The adapter's `uv run` prefix belongs on the *outer* invocation, which is exactly
where the manifest puts it. Worth a line in the module docstring so the next reader does not
"fix" it.

**#3 — folding exit 2/3/4/5 into `collected_nothing`. UPHELD, with evidence the maker did not
have.** Distinguishing them would have mislabelled a real case: my syntax-error mutation of a
`src/` module produced pytest exit **4**, not 2 —

```
E   SyntaxError: invalid syntax
RESULT killed=False exit=4
```

— so "3 is an internal error and 4 a usage error, neither is literally *no tests ran*" is true of
the docs and false of the behaviour. The property that matters (no test result was produced, so no
kill can be claimed) is the right one to group on. Two notes: the field is **advisory only** — it
prints a NOTE and never affects `killed` — and per CHECKER-M3 it is untested for 3/4/5, which is
part of AT-315.

**#4 — leaving AT-308/AT-309 out. UPHELD, unreservedly.** Not slipping an unrelated one-line fix
into a unit is the discipline, and my sequencing note was a note about ordering, not a licence to
widen a unit's diff. AT-309 rides in its own unit with the test that kills its mutation.

## 6. Protected state — confirmed unchanged

- `projects/erp/screenmap.json` sha256 =
  `46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf` — **byte-identical** to the
  value recorded in `qa/verdicts/at306-verification-artifact-integrity.md`, both before and after
  every command in this check.
- **The migration has NOT been run.** The dry run still reports the three
  `'/vidysea.com/erp/trainers' -> '/erp/trainers'` rows and `would repair 3 url_pattern(s) across
  1 file(s)` / `dry run — re-run with --write to apply`, exit 0; hash unchanged afterwards.
- `qa/gates/t135-url-pattern-data-migration.md` is **still unanswered** — line 68 still reads
  `_(unanswered — append `Answered: …` below before acting)_`, and no `Answered:` line exists.
- **Not UI-touching, confirmed from the changed paths** (`git show --name-only HEAD`): `qa/`,
  `scripts/mutation_check.py`, `tests/test_mutation_check.py`. Zero paths under
  `src/autotester/ui/`; `grep -rn mutation_check src/` → 0 hits. **Mode D is not required.**

## 7. Two things recorded, not charged

- **`restored byte-identically` is not literally true — AT-316 (low).** `original` is read through
  `read_text()` (universal newlines) and restored with `newline="\n"`, so a **CRLF** target comes
  back as LF, and the restore self-check is blind to it because it compares through the same lossy
  decode. Demonstrated on a CRLF source: `b'def classify(value):\r\n…'` → `b'def
  classify(value):\n…'`, `restored byte-identically? False`, no error raised. Every `.py` in this
  repo is LF so nothing is reachable today — but `_sandbox` copies `pyproject.toml`, which **is**
  CRLF here. Read/write bytes and the claim becomes true.
- **`scripts/` is outside every `doctor` rule — AT-318 (medium).** `doctor._python_files` walks
  `root/src` only (`check_file_sizes` adds `tests/*.py`), so file-length, function-length and
  drift-filename checks never see `scripts/`. By doctor's own metric `check()` in
  `scripts/mutation_check.py` is **56 lines**, over C2's `MAX_FUNCTION_LINES = 50`. **I am
  deliberately not charging this to the unit:** whether C2's unqualified "no function exceeds 50
  lines" governs `scripts/` is a contract-scope question, and settling it against a pending
  artifact is the mirror image of softening a criterion to pass one — the contract says such a
  decision is made separately. Filed for its own ruling and its own unit.

## 8. Found while writing this verdict, in the checker's own house — AT-319 (high)

Appending this check's rows tripped a uniqueness assertion I ran over `qa/issues.jsonl`:
**AT-282, AT-288, AT-289, AT-290 and AT-291 each appear twice, and no pair is identical.** These
are five collisions between *genuinely different findings* — e.g. AT-289 is both "Only the CLI
video seam closes VideoRequests" and "resolve_requests is wired to the CLI merge", AT-291 both
"resolve_requests closes and attributes requests" and "url_template is STILL not idempotent".

**Pre-existing and not chargeable to this unit** — I confirmed against `git show
HEAD:qa/issues.jsonl`, where all five are already present before any write of mine. But it is the
checker's own ledger, the skill's rule is *"IDs sequential, never reused"*, and the consequence is
concrete: a citation to one of those five ids is ambiguous, and any reader that keys the ledger by
id silently drops one finding per collision — five findings closable by fixing the other one. All
five sit inside the AT-282..AT-291 band, which reads like two sessions appending against the same
tail rather than five independent slips.

I have **not** renumbered anything: every verdict and manifest citing those ids would then point
at the wrong row. The remedy is in the AT-319 row, and the recurrence guard belongs in the next
Mode B sweep (a duplicate-id assertion — checker-owned, read-only, no code change).

---

**Re-check on cycle 2 will need:** AT-313, AT-314, AT-315 fixed with a mutation run showing the new
tests die (AT-314's and AT-313's mutations write themselves; AT-315's needs a case that separates
`code == 1` from `not survivors`). AT-316/AT-317/AT-318 are not blockers for this unit.

**Checker re-ran:** full pytest · ruff · doctor · both committed mutation specs · the AT-311 grep ·
the migration dry run + sha256 before/after · 6 adversarial attack scripts (empty-kills ×3,
absolute-path + traversal escape, CRLF restore, narrow selector, unrelated-runtime-break, flake,
two-mutation residue, sandbox perf) · 4 checker-authored mutations of `scripts/mutation_check.py` ·
`uv run` project-discovery probe · `doctor.py` rule scoping.

---

# Cycle 2 — independent re-check

**Date:** 2026-09-11
**Manifest:** `qa/manifests/at311-mutation-check.md` (Fix cycle: 2 of max 3)
**Contract:** `qa/contracts/core-invariants.md` C7, incl. the kill-attribution clause and the
mutation duty (2026-09-11 amendment), and the zero-failure clause (2026-09-08 amendment)
**Commit checked:** `80ccf66` (code at `2ac4c21`; `80ccf66` is the manifest correction)
**Checker:** fresh Mode A subagent, bound to `D:/autoTesting`
**Cycle checked: 2**

```
VERDICT: FAIL
SCOREBOARD: 6/7 applicable criteria met, 0/0 invariants (this contract declares no [I*])
FAILURES:
- [C7] sev: medium · The cycle-2 argument is false. A mutation CAN reach the `exit_code == 1`
  clause: pytest exit 2 (INTERRUPTED) carries real FAILED lines, so a mutation making the NAMED
  test fail and a later test raise KeyboardInterrupt gives `exit==2` with `expected <= failures`
  — the weakened `exit_code != 0` says killed, the correct form says not-killed. Reproduced. A
  `check()`-level test WAS available; the manifest's "a better test was not available" and the
  same claim in `scripts/mutation_check.py::is_kill`'s docstring and in
  `tests/test_mutation_check.py`'s AT-315 comment block are all false as committed · add the
  interrupted-run case at `check()` level and correct the three prose claims · issue: AT-321
- [C7] sev: medium · Fourth hole, kill-attribution: a `kills` NAME is not a unique test
  identifier. `collected_tests` and `failed_tests` both reduce a nodeid to `split("::")[-1]`, so
  a same-named test in a DIFFERENT file (selector = a directory) or a different class in the same
  file satisfies the attribution check. Reproduced: mutating `tests/test_unrelated.py` — leaving
  `scripts/mod.py` untouched — reported `killed=True, survivors=[]` for
  `tests/test_mod.py::test_small_values_are_small`, which could not have failed. Verbatim AT-311
  failure mode #2, reachable inside the fix for AT-311 · compare full nodeids, or refuse a `kills`
  name that collects more than once · issue: AT-320
- [C7] sev: medium · The report calls a survivor "vacuous for its property" on evidence C7's
  zero-failure clause says is insufficient. `report()` prints
  `SURVIVING : <test>  <- vacuous for its property` for ANY survival, including a mutation that
  landed on a line no assertion reads — the AT-151 shape the clause was written for. C7: "When a
  sabotage yields 0 failures the harness must report it as INCONCLUSIVE — mutation not shown to
  change behaviour … It must never be reported as 'the guard test is vacuous' on that evidence
  alone." · print INCONCLUSIVE, not a vacuity finding · issue: AT-323
LIVE-BROWSER: not-applicable (changed paths: qa/, scripts/mutation_check.py,
tests/test_mutation_check.py — zero paths under src/autotester/ui/; `grep -rn mutation_check src/`
returns 0 hits. Mode D is NOT required.)
ISSUES-WRITTEN: AT-320, AT-321, AT-322, AT-323 (and AT-313, AT-314, AT-315 → fixed)
EXPLANATION: All three cycle-1 findings are genuinely closed — I re-ran each attack against the
committed code and each was refused, with the absolute-path decoy verified byte-identical by
sha256 rather than by the raised error. Both mutation specs and all four verify commands
reproduce exactly, per-mutation, and the manifest carries no stale figure. It FAILs on what the
dispatch asked me to test rather than accept: the claim that no mutation can reach the exit-code
clause is false, so the extraction was not forced and the general rule being proposed rests on a
falsified premise; and the fourth hole the maker said it had no basis to rule out is real.
```

## 1. What I re-ran (nothing below is read from the manifest)

| Command | My result | Manifest's claim | |
|---|---|---|---|
| `uv run pytest -o addopts= -q` | `1072 passed, 2 skipped, 1 warning in 110.64s`, exit 0 | 1072 / 2, exit 0 | ok |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 | exit 0 | ok |
| `uv run autotester doctor` | `root-clutter: AGENTS.md …` · `1 violation(s)`, exit 1 | exit 1, exactly one (AGENTS.md, AT-283) | ok |
| `scripts/mutation_check.py … mutations-self.json` | `8/8 mutations killed`, exit 0 | 8/8, exit 0 | ok |
| `scripts/mutation_check.py … mutations.json` | `4/4 mutations killed`, exit 0 | 4/4, exit 0 | ok |
| `grep -c test_a_file_nested_below_the_project_is_still_judged_by_it tests/test_migrate_url_patterns.py` | `0` | `0` | ok |
| `pytest tests/test_mutation_check.py --collect-only` | `18 tests collected` | 18 | ok |

**Attribution was checked per-mutation, not in aggregate.** For all 12 lines across the two specs
the printed `claims to kill` set is a subset of `actually failed`, and for 11 of the 12 it is
equal. The one asymmetry is the manifest's own disclosed case — `sandbox removed - mutate the live
tree` also fails `test_it_refuses_an_absolute_file_path` — which is correct and, as the maker
says, visible rather than hidden. The migration spec's four are exact equalities, including M4,
whose old label named a test that does not exist (re-confirmed, `grep -c` returns 0).

## 2. The three cycle-1 attacks, re-run against the committed code

Driven through `check()` / `is_kill()` imported from `D:/autoTesting/scripts/mutation_check.py`.

```
A1  empty kills via check()   REFUSED -> mutation 'threshold broken' names no test in 'kills'.
                                        An unattributed kill is exactly the defect this
                                        instrument exists to refuse (AT-313).
A1b empty kills via is_kill() REFUSED -> a kill claimed by no test is not a kill (empty 'kills')
A2  '../../../etc/passwd'     REFUSED -> file '../../../etc/passwd' resolves outside the sandbox
                                        (C:\Users\Lenovo\AppData\Local\etc\passwd).
A3  absolute path             REFUSED -> file 'C:\...\decoy-atk-lzwvtq4m.py' resolves outside
                                        the sandbox.
    decoy sha256 before = 3c3130ae81b2fe35...   after = 3c3130ae81b2fe35...   BYTE-UNCHANGED = True
```

**AT-313 — closed, on both paths.** The dispatch's "refused at spec validation AND inside the
decision" is accurate: `check()` refuses before the baseline runs, and `is_kill()` refuses
independently of it, so neither path can produce an unattributed kill.

**AT-314 — closed, and the decoy check is a byte check.** I deliberately gave the decoy **CRLF**
content so that any write-and-restore would show up as a hash change even where a text comparison
would not (that is AT-316's blind spot). The sha256 is identical before and after. The unit's own
`test_it_refuses_an_absolute_file_path` asserts the decoy's content too, which is the right shape.
I also tried a **symlink inside the sandbox pointing out**: `_sandbox`'s `copytree` follows it and
copies the *content* as a regular file, so the mutation lands in the copy and the outside victim
is byte-unchanged (verified by sha256). No hole there.

**AT-315 — the mechanism is closed; the argument for it is not.** Mutation 4 of the self-spec
(`kill redefined as any non-zero exit`) is now killed by
`test_is_kill_requires_pytest_to_have_actually_run_tests`, reproduced above. The property is
defended. Section 3 is about the reasoning, which is a separate thing.

## 3. Priority 1 — the AT-315 argument, tested rather than accepted. It is false.

The manifest and the shipped docstring both assert:

> A mutation cannot reach that clause: a collection error yields no `FAILED` lines, so
> `expected <= failures` fails too and the weakened form survives *every possible* mutation.

The premise silently assumes that every non-1 non-zero exit is a **collection** error. It is not.
**pytest exit 2 is INTERRUPTED**, and an interrupted run prints the FAILED lines of the tests that
already failed. So a mutation only has to make the named test fail *and* a later test interrupt
the session. Constructed on the unit's own synthetic fixture, one anchor, one replacement:

```json
{"name": "exit-2-with-a-real-FAILED-line", "file": "scripts/mod.py",
 "old": "    if value > 10:\n        return \"big\"\n    return \"small\"\n",
 "new": "    if value > 10:\n        return \"small\"\n    raise KeyboardInterrupt\n",
 "kills": ["test_big_values_are_big"]}
```

Result from the committed `check()`:

```
{"killed": false, "exit": 2,
 "expected": ["test_big_values_are_big"],
 "failed":   ["test_big_values_are_big"],
 "survivors": [], "collected_nothing": true}

weakened `exit_code != 0` would say: True
correct  `exit_code == 1` says:      False
```

`expected <= failures` **holds** and the exit code is **2**. The two clauses are separated by a
real mutation, at `check()` level, with no extraction. So:

- **A better test WAS available.**
  `test_an_interrupted_run_is_not_a_kill_even_though_the_named_test_failed` would have asserted
  `result["killed"] is False` and died under `exit_code != 0`.
- **The extraction was not forced.** It is still *fine* — a pure decision function with a table is
  readable and I am not asking for it to be reverted — but it was a choice, not a necessity, and
  the manifest presents it as a necessity.
- **The direct table is the weaker answer here, and this check proves it concretely.** A
  `check()`-level test exercises the whole path: exit code, FAILED parsing, `survivors`, **and the
  `collected_nothing` field**. The table asserts `is_kill` in isolation and therefore cannot see
  that the same exit-2 run sets `collected_nothing: true` and makes the report print *"that exit
  code means pytest ran nothing — not a kill"* about a run in which pytest ran two tests and one
  failed. The instrument states something false about what happened. That is filed as **AT-322**,
  and it is exactly the class of defect an end-to-end assertion catches and a unit-level table
  does not.

**Therefore the general rule is NOT confirmed.** I am ruling on it explicitly, because the
dispatch says it will shape later units:

> *"When a property cannot be reached by mutation, extract it until it can be asserted directly."*

The rule itself is sound as a **last resort** and I would not forbid it. What must not carry
forward is the standard of proof used here. "I could not think of a mutation" is not "no mutation
exists", and this is the second time in two cycles that a confident unreachability claim from this
pair has been falsified by one attempt. **Amendment I am NOT making:** none. This is a ruling on a
manifest's reasoning, not a contract change; C7's existing text ("mutate the specific branch it
claims to defend and require at least one failure") already demands the search, and I will not
amend a contract against a pending verdict. If the maker wants the extraction rule written into
C7, it comes as its own inbox entry with the burden stated: **an unreachability claim must name
the exit-code / state space it searched and why that search is exhaustive** — here the space was
pytest's exit codes, and 2 was never considered.

The three prose claims to correct as committed artifacts, not just in the manifest:
`scripts/mutation_check.py` `is_kill.__doc__` ("a mutation cannot prove the first clause"), and
`tests/test_mutation_check.py`'s AT-315 comment block ("A mutation cannot prove the exit-code
clause"). A false statement in a docstring is what AT-311 was: a label nobody compares against.

## 4. Priority 3 — the fourth hole. It exists: `kills` names are not unique identifiers.

`collected_tests()` returns `line.split("::")[-1]` and `failed_tests()` returns
`nodeid.split("::")[-1]`. Both discard the file and the class. So the attribution check compares
**bare function names**, and a bare function name is not unique in a pytest selection.

Reproduced end to end. `scripts/mod.py` is **never mutated**; the mutation edits an unrelated test
file that happens to contain a test of the same name; the selector is a directory:

```
tests/test_mod.py::test_small_values_are_small        <- what the `kills` label MEANS
tests/test_unrelated.py::test_small_values_are_small  <- what actually fails

spec: {"tests": "tests", "mutations": [{"file": "tests/test_unrelated.py",
        "old": "FLAG = True", "new": "FLAG = False",
        "kills": ["test_small_values_are_small"]}]}

{"killed": true, "exit": 1, "expected": ["test_small_values_are_small"],
 "failed": ["test_small_values_are_small"], "survivors": [], "collected_nothing": false}
```

`killed=True`, `survivors=[]`, and the intended test cannot have failed because the module it
tests was not touched. **This is verbatim AT-311's second failure mode — "an unrelated test
failing counted as proof that this test noticed" — surviving inside the fix for AT-311.** It is
the same shape as AT-313, which cycle 1 graded high; I grade this **medium** only because AT-313
was reachable with an empty label while this needs a name collision, and because both of this
unit's own specs use single-file selectors with unique names, so **neither the 8/8 nor the 4/4 is
affected**. Nothing already certified is in doubt.

The within-file variant is real too: two classes in one file both yield `test_method`, so
`TestB::test_method` failing satisfies a `kills` claiming `TestA::test_method`. Confirmed
(`failed: ["test_big_values_are_big", "test_method"]`, `killed=True`).

Fix direction: compare full nodeids, or — cheaper and backward-compatible — keep bare names but
**refuse a `kills` entry that collects more than once**, in the same loop as the not-collected
refusal. The refusal family's own logic applies: a label that could mean two things is a comment.

### The rest of the attack list, and what it found

| Attack | Result |
|---|---|
| symlink inside the sandbox pointing out | **Safe.** `copytree` follows it; the copy is a regular file inside; outside victim sha256 unchanged. |
| `tests` selector naming a directory | **Works, and is the carrier for AT-320.** No refusal, correctly — but it is what makes name collisions reachable. |
| parametrised id, `kills: ["test_p"]` | **Safe.** Refused — `not collected`. Collect-only yields `test_p[50-big]`, so a bare name cannot silently match a parametrised test. |
| parametrised id, `kills: ["test_p[50-big]"]` | **Safe.** Collected and attributed correctly. |
| class-based id | Collected as `test_method`; correct in isolation, unsafe on collision (AT-320). |
| mutation whose `new` contains `old` | **Safe.** `replace(old, new, 1)` runs on a fresh read of the original each iteration; `original` is snapshotted before the write; the restore uses the snapshot. Killed correctly. |
| CRLF anchors / unicode | **AT-316 still open, unchanged, still confined.** `read_text` / `write_text(newline="\n")` converts a CRLF sandbox copy to LF, and the restore self-check compares through the same lossy decode so it cannot fire. Live tree byte-unchanged (verified). Not re-charged — an open row from cycle 1 this manifest never claimed to fix. |
| spec with duplicate mutation names | **Accepted silently** — two results printed under one name. Cosmetic; the run is still correct because each mutation re-reads and restores independently. Not filed. |
| exit 2 mislabelled `collected_nothing` | **AT-322** (see section 3). |
| `report()` calling a survivor "vacuous" | **AT-323** (see below). |

### AT-323 — the zero-failure clause, in the instrument that C7 makes mandatory

C7 (2026-09-08): *"When a sabotage yields 0 failures the harness must report it as
**INCONCLUSIVE — mutation not shown to change behaviour** … It must never be reported as 'the
guard test is vacuous' on that evidence alone."* `report()` prints, for any survival:

```
    SURVIVING      : <name>  <- vacuous for its property
```

The instrument's anchor-count and changed-nothing refusals give it the *necessary* half — the
patch applied and the file moved — which is precisely what the 2026-09-08 amendment says is **not
sufficient**, because an anchor can match once inside a comment, a docstring, or a line no
assertion reads. That amendment exists because a checker's sabotage U did exactly that. The
instrument is now the mandated route for every test-adding unit, so it is where this wording does
the most damage: the next maker reads "vacuous for its property" and rewrites a correct test,
which is the AT-140 incident the clause was written to prevent. The fix is one string.

## 5. Priority 5 — manifest staleness. Clean; no contradictory claim remains.

The maker corrected the cycle-1 body in place at `80ccf66`. I checked every superseded figure:

- **The 5/5 run** — the code block is gone, replaced by an explicit `Superseded by cycle 2` note
  naming the reason (AT-315) and pointing at the authoritative 8/8. The surviving prose under it
  ("the four migration mutations were also re-run … 4/4 killed") is still true today; I re-ran it.
- **"survived all 12 tests"** (line 135) — **verified accurate as history**, not stale. At
  `55efeac` the file held exactly 12 tests (`grep -n "^def test_"` returns 14 hits, two of which
  are inside the `TESTS` fixture string literal). "Cycle 2 raised it to 18" reconciles: 12 + 6 new
  (3 `is_kill` table + 1 empty-`kills` + 2 escape refusals) = 18, and pytest collects 18.
- **1066** — no occurrence anywhere in the file. The only suite figures are `1072 passed,
  2 skipped`, in both the How-to-verify and the Cycle-2 verify blocks, and both reproduce.
- **"Actual outputs (from maker's own run…)"** — reduced to a superseded pointer with no numbers.

AT-288's failure mode (a corrected manifest still carrying the claim it corrected) does **not**
recur here. This is a clean in-place correction.

## 6. Rulings on the cycle-1 judgements #1–#4

All four were ruled in this file's cycle-1 section 5 and I **uphold all four unchanged** — #1
leave the superseded harness byte-untouched with the pointer in the AT-312 ledger row; #2
`sys.executable` upheld (`uv run` with `cwd=work` would resolve the *sandbox* as its project); #4
leaving AT-308/AT-309 out upheld unreservedly.

**#3 is upheld with an amendment, on evidence cycle 1 did not have.** Folding 2/3/4/5 into one
group is still right *for `killed`* — the field is advisory and never affects the verdict, and
`is_kill`'s `exit_code == 1` is what actually holds the line. But the grouping's stated
justification ("no test result was produced") is **false for exit 2**, and the report says so out
loud. Section 3's reproduction has pytest exit 2 with a genuine `FAILED` line and a real assertion
failure. So: keep the grouping in `is_kill`; **remove 2 from `collected_nothing`**, or reword the
NOTE so it stops asserting something the run disproves. Filed as AT-322 (low), not a FAIL line —
it is a false statement in output, not a false verdict.

## 7. Ruling on the cycle-2 disclosure

> *"The checker found three holes I did not, having just written the tool to find holes. I have no
> basis for claiming there is not a fourth."*

**Correct, honest, and now confirmed by measurement** — there was a fourth (AT-320), and a fifth
and sixth of a smaller kind (AT-322, AT-323). Recording this as the right disclosure to make: it
is the difference between a manifest that claims completeness it cannot have and one that states
its own limit. It does not soften this verdict — a disclosed unknown is not a discharged
obligation — but it is the reason this FAIL costs a cycle rather than trust.

Set against it, one thing the maker got right twice and should keep doing: **both cycles' first
self-run attempt was REFUSED rather than reported** (a mangled em-dash anchor in cycle 1, a stale
anchor in cycle 2). The instrument disciplining its own author is the property that makes it worth
having.

## 8. Protected state — confirmed unchanged

- `projects/erp/screenmap.json` sha256 =
  `46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf` — **byte-identical** to the
  value recorded in this file's cycle-1 section 6 and in
  `qa/verdicts/at306-verification-artifact-integrity.md`. Unchanged before and after every command
  in this check. mtime `2026-09-11 02:45:01 +0530`, i.e. **before** both of this unit's commits
  (`2ac4c21` and `80ccf66`, both `04:54`).
- **The migration has NOT been run.** The file still holds the un-migrated
  `'/vidysea.com/erp/trainers'` form (6 matching lines) and **zero** occurrences of the repaired
  `"/erp/trainers"`.
- `qa/gates/t135-url-pattern-data-migration.md` is **still unanswered** — line 68 still reads
  `_(unanswered — append Answered: … below before acting)_`; no `Answered:` line exists.
- **Not UI-touching, confirmed from the CHANGED PATHS** (`git diff --name-only 2ac4c21~2 HEAD`):
  `qa/.last-tick`, `qa/evidence/at311-mutation-check/*`, `qa/issues.jsonl`,
  `qa/manifests/at311-mutation-check.md`, `qa/verdicts/at311-mutation-check.md`,
  `scripts/mutation_check.py`, `tests/test_mutation_check.py`. Zero paths under
  `src/autotester/ui/` or any other rendering surface; `grep -rn mutation_check src/` returns 0
  hits. Nothing here alters what any page renders, directly or indirectly. **Mode D is NOT
  required**, and the manifest's claim is verified rather than accepted.

## 9. Not charged to this unit

- **AT-316** (CRLF restore) and **AT-317** (collateral-failure signal) — open from cycle 1, never
  claimed fixed by this manifest, and re-confirmed still open. Correctly out of scope.
- **AT-318** (`scripts/` outside every doctor rule) — still a contract-SCOPE question about C2,
  and settling it against a pending artifact is the mirror image of softening a criterion to pass
  one. Unchanged from cycle 1.
- **AT-319** (five duplicate ledger ids) — pre-existing, the checker's own house, and the manifest
  is right not to touch it. My new rows continue the sequence from AT-319 without reuse.
- **AT-308 / AT-309** — remain open, unchanged.

## 10. What cycle 3 needs

Three FAIL lines, all narrow. AT-320 is one refusal in the loop that already refuses uncollected
names. AT-321 is one `check()`-level test plus three corrected prose claims. AT-323 is one string.
AT-322 is a low, not a FAIL line, but it rides in the same edit. None of them touches the parts
that are now demonstrably sound: the sandbox containment, the empty-`kills` refusal on both paths,
the baseline assertion, the anchor discipline, or the attribution logic on unique names.
