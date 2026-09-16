# Verdict — at396-isolation-flag-claims

**Date:** 2026-09-16
**Mode:** A (unit check)
**Bound root:** `d:/autoTesting`
**Contract:** `qa/contracts/core-invariants.md` (C2, C7 named; C1–C9 judged as project-wide)
**Manifest:** `qa/manifests/at396-isolation-flag-claims.md`
**Cycle checked: 1**
**Adapter:** `qa/adapter.json` (coding) — slot-1 re-run in full by me.

```
VERDICT: PASS
SCOREBOARD: 9/9 criteria met, 0/0 invariants hold (this contract has no separate [I*] section)
FAILURES: none
CAPABILITY-COVERAGE: 3/3 rows reproduced in a throwaway copy outside the bound root, plus the
  AT-395 row supplied in the at386 manifest verified independently (4/4 total)
LIVE-BROWSER: not-applicable (changed paths: tests/test_flake_probe.py,
  qa/manifests/at386-flake-probe-subprocess-coverage.md — no route, template, component or page)
ISSUES-WRITTEN: AT-405, AT-406, AT-407 (all low/medium, none blocking); AT-395 open→fixed,
  AT-396 open→fixed
EXPLANATION: I re-derived both measurements myself rather than inheriting either. The corrected
docstring is now weaker than the facts in both places, which is the right direction, and the new
pin is demonstrably non-vacuous — three independent mutations each reddened exactly the named
test on the assertion it is named for. The survived mutation is correctly classified as mis-aimed,
and AT-395's supplied row reproduces exactly as written. Three residual findings are filed, none
of them a criterion violation: the two refuted claims still stand verbatim as assertion messages
at :243-244 where the new guard cannot see them, the pin is whitespace-sensitive in a way the
manifest's disclosure understates, and the file carrying every one of these guards is untracked
in git.
```

## Slot-1 verify — re-run by me, not read

```
$ uv run pytest tests/test_flake_probe.py -q
......................                                                   [100%]
EXIT: 0          (22 dots = 22 tests, matching the manifest's "22 passed (was 21)")

$ uv run pytest -q
... 13 full lines of dots + 11, one 's' skip, no F
EXIT: 0          (warnings summary: the pre-existing starlette/anyio DeprecationWarning only)

$ uv run ruff check src tests scripts
All checks passed!
EXIT: 0

$ uv run autotester doctor
doctor: clean
EXIT: 0
```

AT-391's shared-tree breakage did not bite this run either; nothing outside the unit's two paths
failed, so nothing had to be attributed to it.

## 1. The `-o addopts=` measurement, re-derived independently

The manifest claims its own replacement wording was measured, and that `-o addopts=` is **not**
load-bearing for capturing failure output. I did not read that number. I wrote my own deliberately
failing test in the scratchpad and ran it both ways with `-c pyproject.toml`, so `pyproject.toml`
(`addopts = "-q"`, line 62) is the rootdir config exactly as it is for `run_once`, and with
`-q -p no:cacheprovider` to mirror `run_once`'s argv (`scripts/flake_probe.py:137-139`):

```
WITHOUT -o addopts= : exit 1, 12 lines, assert text present
  E       AssertionError: assert '/settings.html' in {'/'}
  FAILED ::test_deliberate_failure - AssertionError: assert '/settings.html' in...

WITH    -o addopts= : exit 1, 13 lines, assert text present
  (identical output, plus one trailing line:)
  1 failed in 1.18s
```

**Confirmed.** The traceback, the `E   AssertionError` line and the short-summary `FAILED` line all
survive `-qq`; the entire delta is the one summary line `1 failed in Xs`. My absolute counts are
12/13 against the manifest's 11/12 because `wc -l` counts newlines where the maker's harness used
`splitlines()`; **the delta — exactly one line — is identical**, and it is the delta the claim rests
on. So the maker's replacement claim is **not** a third over-claim: it is accurate, and it is
deliberately weaker than the evidence would even allow ("worth pinning as a deliberate choice; not
load-bearing"). Worth adding, since it strengthens the corrected wording rather than the refuted
one: `run_once` keeps only the last 25 lines of the tail, and both outputs fit inside 25, so the
flag cannot change what the probe records even at the margin.

## 2. The ORIGINAL refutation, re-derived rather than inherited

My predecessor's finding (AT-396) is that pytest's cache informs *selection* only under
`--lf`/`--ff`/`--sw`. I re-measured it from scratch in a throwaway project outside the bound root,
cacheprovider **active**, two tests, one red:

```
RUN 1                 -> 1 failed, 1 passed
  .pytest_cache/v/cache/lastfailed = {"tests/test_pair.py::test_red": true}
RUN 2 (identical cmd) -> 1 failed, 1 passed          <- every test still collected and run
RUN 3 (--lf added)    -> 1 failed, 1 deselected
RUN 4 --collect-only          -> 2 tests collected
RUN 5 --collect-only --lf     -> 1/2 tests collected (1 deselected)
```

**Confirmed, independently.** The cache is written; the next identical invocation is unaffected by
it; only `--lf` deselects. `run_once` passes none of those flags, and it passes a single explicit
nodeid, so selection is doubly moot. `-p no:cacheprovider` is hygiene, not the precondition for the
binomial bound — the refutation holds and the corrected docstring states it correctly.

(Incidental, not a finding: my first attempt redirected `cache_dir` so the experiment could not
write into the bound tree. `d:/autoTesting/.pytest_cache/` does exist, but it is gitignored and is
created by the adapter's own `uv run pytest -q`, not by me.)

## 3. Capability coverage — 3/3 reproduced, in a copy, green before each edit

Copy: `tests/ scripts/ src/ pyproject.toml` copied to a scratchpad dir **outside** `d:/autoTesting`,
`.git` and `.venv` excluded. Byte identity asserted before use — `git hash-object` on the live and
copied subjects matched (`55a68a22…` for the test file, `cddc3877…` for `scripts/flake_probe.py`).

**Import resolution asserted inside the copy** (the `.venv/autotester.pth` trap in the dispatch):

```
flake_probe -> ...\scratchpad\copy\scripts\flake_probe.py     <- inside the copy
autotester  -> D:\autoTesting\src\autotester\__init__.py      <- live, via the .pth
```

`tests/test_flake_probe.py` never imports `autotester`; it reaches `flake_probe` through its own
`sys.path.insert(… parents[1]/"scripts")` (line 16), which resolved to the copy. The live tree is
therefore not the subject of any mutation below. My harness asserts, per C7: **baseline exit 0**
before every mutation, **anchor matched exactly once**, **file on disk actually changed**, and it
reads the failure list by node id rather than the exit code.

Baseline in the copy, from the copy, before any edit: `22 passed in 0.85s` (whole file) and
`1 passed` (named check alone).

| Row | Falsifying edit applied | Result |
|---|---|---|
| 1 — the refuted binomial-bound claim cannot return | restored "A probe whose trials are not independent cannot support a binomial bound at all." into the docstring | exit 1, **1 failed, 21 passed**, failure list = `::test_the_isolation_flags_are_not_described_as_load_bearing`, at `test_flake_probe.py:283` (= the `:282` assertion, shifted one line by the edit), message `the refuted claim is back` |
| 2 — the refuted output-suppression claim cannot return | restored "Without it the failing output this probe exists to capture is suppressed." into the `-o addopts=` paragraph, leaving "not load-bearing" in place | exit 1, **1 failed, 21 passed**, same node id, at `:284` (= the `:283` assertion, same one-line shift), `assert 'output this…s suppressed' not in …` |
| 3 — the measured verdict on `-o addopts=` stays stated | `not load-bearing` → `it keeps the capture honest` (same line count) | exit 1, **1 failed, 21 passed**, same node id, at **`:285` exactly as the manifest states**, `assert 'not load-bearing' in …` |

Each kill is attributed: one failing test, and the assertion that fired is the one the row is named
for. No row broke collection or import — the 21 remaining tests passed in every case, which is the
positive control that these edits isolate rather than redden everything.

The manifest's cited lines are accurate. Rows 1 and 2 cite `:283`; the true assertions are at `:282`
and `:283` and each edit inserts one line above itself, which is why both the maker and I observe
`:283`/`:284` respectively. Row 3, whose edit shifts nothing, lands on `:285` on the nose.

### 4. Ruling on the SURVIVED mutation

Reproduced. Deleting the closing sentence *"Both are pinned anyway: a flag nobody asserts is a flag
a future edit drops for free…"* → **exit 0, 22 passed**, zero failures.

**The maker's reasoning holds, and reporting it was the correct move.** The unit's three capability
claims are: two refuted sentences cannot return, and one measured verdict must stay stated. The
deleted sentence carries neither a refuted claim nor a measured verdict; it is the unit's rationale
for leaving the *test body* alone. Nothing in the claimed capability set asserts its presence, so
nothing should have reddened, and a red here would have meant the guard was pinning prose the unit
does not claim. This is precisely C7's zero-failure clause one level down: *"an anchor can match once
inside a comment, a docstring, or a line no test exercises, so the patch applies, the file changes,
and nothing semantically moves"* — evidence about the mutation, not about the test. Substituting the
correctly-aimed edit **and** recording the miss is the behaviour the clause was written to produce,
and the correctly-aimed replacement (row 3) does kill.

### 5. AT-395's supplied row — verified, both halves

The row was credited to my predecessor rather than to the maker; I re-derived it anyway. Same copy,
same harness, mutating **`scripts/flake_probe.py`** (admissible under the 2026-09-16 C7 edge-case
amendment: single-hunk, single-file, the module the changed tests directly exercise, named in the
manifest's capability section):

```
[AT395-if-arm]  baseline GREEN asserted (exit 0)
  mutate the IF-arm of run_once's tail ternary (the "" branch) -> (proc.stdout + proc.stderr)
  exit=1  failures=['tests/test_flake_probe.py::test_a_clean_run_keeps_no_output']
  test_flake_probe.py:191: AssertionError: assert '............................' == ''

[at386-row2-wholesale]  baseline GREEN asserted (exit 0)
  replace the whole ternary with  tail = ""
  exit=1  failures=['::test_a_failure_tail_is_bounded_rather_than_the_whole_log',
                    '::test_a_nonzero_return_code_is_what_makes_a_run_count_as_failed']
  test_flake_probe.py:179 / :203   <- test_a_clean_run_keeps_no_output NOT among them
```

**Both halves of the row are accurate.** The if-arm mutation reddens *exactly*
`test_a_clean_run_keeps_no_output`, at `:191`, on its own `assert run.tail == ""`; and row 2's
wholesale `tail = ""` reddens the two failure-tail tests and leaves the clean-run test green, so it
demonstrably could not have stood in for it. The two tests pin opposite arms of one ternary and are
cross-immune, exactly as the row claims and exactly the shape the 2026-09-16 amendment recorded for
`_discard`'s two-clause `or`. AT-395 is **fixed** by this unit.

### 6. Ruling on the pin: is a string assertion on prose the AT-218 vacuous-guard class?

**No — measured, not argued.** A vacuous guard is one that cannot fail; this one failed under three
separate mutations, each on a different assertion, each attributed to the right node id. It also
sits at the correct altitude: the property it defends *is* a string in a docstring, so a string
assertion is the direct assertion of that property, not a proxy for it. AT-218's class is a guard
that asserts something the bug also satisfies. This guard reads the exact artifact that was wrong.

The manifest's disclosure ("it stops the two refuted sentences returning verbatim; it cannot stop a
third, differently-worded over-claim") is honest and, in substance, adequate. I confirmed the
disclosed limit rather than assuming it: a **paraphrase** of the binomial claim — *"Independence of
trials would collapse without it."* — survives, 22 passed.

But the disclosure is **one notch too generous to itself**, and this is worth recording in a unit
whose subject is claims stronger than facts. I re-introduced the output-suppression sentence in the
*same words*, differing only by a line wrap between "capture is" and "suppressed" — the wrap this
file's own 78-column docstrings would naturally produce — and the guard **did not fire**: 22 passed.
So the pin does not stop the refuted sentences "returning verbatim"; it stops them returning verbatim
*on one line*. Filed as **AT-406** (low). The general defence the manifest names — measure before
writing — remains the real one, and I agree with it.

### 7. Finding: the two refuted claims never actually left the function

The unit corrected the docstring and states plainly that the test body is unchanged. What the
manifest does not notice is that the test body carries **both refuted claims verbatim**, as the
assertion messages of the very function whose docstring was corrected:

```
tests/test_flake_probe.py:243  assert "no:cacheprovider" in seen[0], "runs must not inform each other"
tests/test_flake_probe.py:244  assert "addopts=" in seen[0], "the project's -q must not suppress the failure output"
```

Line 243 states the refuted mechanism (that without the flag runs inform each other) and line 244
states the refuted consequence (that the project's `-q` suppresses the failure output) — the exact
two propositions this unit exists to retract, two lines below the corrected prose, and both of them
printed to the reader at the moment the assertion fails. The new guard reads
`test_each_run_is_isolated_from_the_ones_before_it.__doc__` only, so it is structurally incapable of
seeing them; I confirmed that by reading the guard rather than inferring it.

**Filed (AT-405, low), not charged.** It is a prose over-claim, and this repo's settled precedent for
prose over-claims is a low-severity ledger row rather than a burned fix cycle (AT-388, AT-389, and
AT-396 itself, which is how this unit exists). Charging here would also judge this unit harder than
the one that created the defect. It does mean the unit's headline — "the two refuted claims cannot
return" — is true of the docstring and false of the function.

### 8. Finding: the file holding every one of these guards is untracked

`tests/test_flake_probe.py` is **untracked** in git (`?? tests/test_flake_probe.py`), removed from
the index by `b177076` on 2026-09-16 by a different session correcting its own wide-pathspec commit.
Every guard AT-386 built and everything this unit pins therefore exists in exactly one working tree:
a `git clean -fdx`, a worktree teardown, or a fresh clone loses all 22 tests, and the docstring they
defend goes with them. "A flag nobody asserts is a flag a future edit drops for free" is the unit's
own argument; an assertion nobody tracks is an assertion a `git clean` drops for free.

**Filed (AT-407, medium), not charged** — it predates this unit and was done by another session
under the narrow-pathspec discipline, not by this maker, and this checker does not commit code.
Flagged here because it is the single largest threat to this unit's value and nothing else on disk
says it.

## Issues addressed — checked against the ledger

- **AT-396 (low, open)** — expected remedy was: *"Restate the reason to what is true: the flag keeps
  trials from sharing `.pytest_cache` writes … It is not what makes the trials independent."* The
  docstring at `:219-228` now says exactly that, naming AT-357 as the precedent for the race it does
  guard. Re-measured by me in §2. → **fixed**.
- **AT-395 (medium, open)** — expected remedy was: *"Every behaviour a manifest claims in 'What
  changed' gets its own capability row … each arm needs its own edit."* The row is supplied in
  `qa/manifests/at386-flake-probe-subprocess-coverage.md`'s corrections block with the original table
  left byte-intact (verified: the diff is pure insertion, no deletions), and I reproduced both of its
  claims in §5. → **fixed**.

## Contract judgement

- **C2 (readable)** — `tests/test_flake_probe.py` is 286 lines, under the 300 limit; the new test is
  ~18 lines; module docstring intact. `autotester doctor` clean. **Met.**
- **C3 (one concept, one place)** — edit in place, no new file, no drift filenames. `doctor` clean.
  **Met.**
- **C4 (clean root)** — nothing added at the root; my own scratch lived outside the repo entirely.
  **Met.**
- **C7 (independent verification)** — the load-bearing one here, and met in every clause. The unit
  adds a test and mutation-tested it before submitting; the manifest pastes real output rather than a
  summary; the zero-failure mutation is reported as a mis-aim rather than as "the guard is vacuous";
  no unreachability claim is made anywhere. I re-ran all of it in my own harness, with an asserted
  green baseline, exactly-once anchors, verified byte changes and kills attributed by node id.
  **Met.**
- **C1, C5, C6, C8, C9** — untouched by this unit; green under the full suite and `doctor`. **Met.**

## Scope, boundaries, concurrency

- No file in the bound tree was edited by me. Post-check `git hash-object` on both subjects still
  reads `55a68a22…` / `cddc3877…`, and `git status --porcelain` is unchanged from the start of the
  check apart from the concurrent session's own `.goal/*` and `qa/.last-tick`, which I did not touch.
- All mutation work happened in a scratchpad copy outside `d:/autoTesting`, deleted after use.
- Data-boundary gate (MC-003): exits 1 on the missing `data_class` — AT-365, HUMAN_GATE, known and
  not introduced here. Not charged.
- Not UI-touching; Mode D not applicable.
- No external data collected; 5c not applicable.
