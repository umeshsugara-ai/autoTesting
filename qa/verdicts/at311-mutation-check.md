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
