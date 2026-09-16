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
