# Verdict — at494-probe-output-is-a-file-not-a-pipe

**Date:** 2026-09-18
**Cycle checked:** 1
**Checker:** fresh Mode A subagent (no builder context; prior checker for this unit was terminated
by a session rate limit before writing anything, so this is the first verdict on disk).
**Unit commit:** 0ed84a7 (HEAD at check time: 41fa431, one tick-stamp commit later, no code drift —
confirmed `git diff HEAD -- scripts/flake_probe.py scripts/mutation_check.py
tests/test_flake_probe_runner.py tests/test_mutation_sandbox.py` is empty).

## What I re-ran myself

- `uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe.py tests/test_mutation_sandbox.py`
  → `36 passed in 87.39s`. Matches the manifest.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at494-probe-output-is-a-file-not-a-pipe/mutations.json`
  → `3/3 mutations killed`, each attributed to the named test(s) in pytest's own failure report
  (re-run independently; output byte-for-byte consistent with the manifest's claim). This tool
  sandboxes every run in a temp copy outside the repo (`mutation_check._sandbox`), which is the
  required throwaway-copy discipline for step 4b — verified by reading `_sandbox`/`_discard`.
- `uv run python scripts/mutation_check.py qa/evidence/at490-491-tree-kill-is-bounded/mutations.json`
  (the sibling unit's own evidence, re-run to confirm the `_kill_tree`→`kill_tree` rename did not
  weaken it — **not pasted in the manifest's "Actual outputs" section**, only claimed) → **`5/5
  mutations killed`**, all five correctly attributed. Took ~10 minutes wall-clock (real nested
  pytest-in-pytest via `mutation_repo`/`check()` fixtures in `test_mutation_sandbox.py`), which is
  why it timed out twice under a 120–290s cap before I let it run to completion in the background.
  Confirms the rename is a true no-op for that unit's own capability coverage.
- Full CLI smoke test: `uv run python scripts/flake_probe.py "tests/test_flake_probe.py::test_that_does_not_exist" --runs 1 --timeout 10` ran end-to-end, exit 0, proving the module-level
  `sys.path.insert` + `from mutation_check import kill_tree` works both as a script invocation and
  (via the full pytest run above) as a test import. Read `mutation_check.py` in full: no module-level
  side effects beyond constants/classes/functions — the import costs nothing at either call site.
- `wc -l` on the four touched files: all under the 300-line cap that applies to `src/`+`tests/`
  (`doctor._capped_files` does not walk `scripts/`, confirmed by reading `doctor.py` — so
  `mutation_check.py`'s 416 lines is a pre-existing, out-of-scope condition, not something this
  unit introduced or that C2 as actually enforced covers).

## Judging the four specific questions

1. **Rename `_kill_tree`→`kill_tree`.** `git show 0ed84a7 -- scripts/mutation_check.py` is exactly
   two line-changes (the `def` and its call site inside `_run_pytest`), no body change.
   `tests/test_mutation_sandbox.py` diff is exactly its two call-site renames, no assertion change.
   AT-490/491 evidence re-run above: 5/5 still killed. **Clean rename, no regression.**

2. **Four pre-existing tests, `_FakeCompleted`→`_FakePopen`.** Read the full current file and
   diffed against the pre-image in `git show`: `test_a_nonzero_return_code_is_what_makes_a_run_count_as_failed`,
   `test_a_clean_run_keeps_no_output`, `test_a_failure_tail_is_bounded_rather_than_the_whole_log`
   each changed exactly one `monkeypatch.setattr` line — same docstring (where present), same
   assertions, same names. `test_each_run_is_isolated_from_the_ones_before_it`'s `capture` helper
   necessarily changed shape (it must write into `kwargs["stdout"]` now) but its assertions
   (`len(seen)==1`, the three `in seen[0]` checks) are byte-identical to before. The manifest's
   claim is accurate; it does not over-claim onto the two tests it separately (and correctly)
   discloses as gaining a new assertion (`test_a_run_that_outlives_its_bound...`) or a renamed
   helper (`_timing_out`→`_hanging`).
   **Could `_FakePopen` pass what the real code would fail?** Traced the substitution: `_FakePopen`
   replaces the `subprocess.Popen` *class* with a callable *instance*; `__call__` writes straight
   into the real `kwargs["stdout"]` file handle opened by `run_once`'s own `with open(log, "w")`,
   so the file-round-trip (`log.read_text(...)` after the block closes) is exercised for real, only
   the OS process launch is stubbed. If `run_once` regressed to `stdout=subprocess.PIPE`, `kwargs["stdout"]`
   would be the int constant `-1`, `.write()` would raise `AttributeError`, and the mutation run
   above shows exactly this: all six tests in the file fail under that mutation (only two are
   *named*, but `expected <= failures` is what `is_kill` checks, matching C7's kill-attribution
   clause). I found no scenario where the fake's behaviour is looser than the real `Popen`'s in a
   way that would matter to any assertion in this file.

3. **Module-level `from mutation_check import kill_tree`.** Verified both directions: the CLI smoke
   test above runs `flake_probe.py` as `__main__` end-to-end (module import succeeds, `sys.path`
   trick works without a `conftest.py`), and the full pytest run exercises it as a plain module
   import (pytest already has `scripts/` on `sys.path` via `tests/conftest.py:23`, so `import
   flake_probe` succeeds and `flake_probe`'s own `sys.path.insert` is redundant-but-harmless in
   that context — it is there for the CLI path, where no conftest runs). `mutation_check.py` has no
   top-level statements beyond `def`/`class`/constant assignments (`if __name__ == "__main__"` gates
   the only executable line), so importing it is inert. **Sound both ways.**

4. **Disclosed gap — no test drives a real hung OS process.** The manifest states this plainly
   under "Known limits (disclosed, not claimed)" and does not put it in the Capability-coverage
   table as a claim — so it is not an unenumerated claim under step 4b, and C7's disclosure
   precedent (recorded debt, not silent claim) is satisfied. But per the same precedent that
   produced AT-494 itself (the at401 checker filed AT-494 from *that* manifest's disclosed,
   un-issued gap), a disclosed-but-un-filed gap should not just live in a manifest's prose forever.
   **Filed as AT-495** (low; the underlying mechanism, `kill_tree`, is shared and already proven
   against a real hang in `mutation_check`'s own AT-487 evidence, which is why this is lower
   severity than AT-494's original defect, not equal to it).

## Diff scope (step 4c)

`git show 0ed84a7 --stat` / full diff: exactly the 7 paths the manifest names — `scripts/flake_probe.py`,
`scripts/mutation_check.py`, `tests/test_flake_probe_runner.py`, `tests/test_mutation_sandbox.py`,
plus the unit's own `qa/evidence/at494-.../{mutations.json,mutations.out}` and
`qa/manifests/at494-....md`. One function, `_decode`, was deleted from `flake_probe.py`; confirmed
via repo-wide grep it has zero remaining callers anywhere (`tests`, `src`, `scripts`) — it existed
solely to decode `TimeoutExpired.stdout`/`.stderr` under the old `subprocess.run` pipe design, which
this unit's own declared rewrite eliminates, so its removal is intrinsic to the claimed change, not
an unrelated deletion of a live concept. No other function/class/test/export was removed or renamed
outside the declared `_kill_tree`→`kill_tree` rename. **Diff scope clean.**

## C10 (commit scoping)

`git show --name-only --format= 0ed84a7` is exactly the manifest's "What changed" set plus this
unit's own evidence/manifest paths — no other unit's files. Clean.

## Capability coverage (step 4b)

All three rows in the manifest's table re-run in `mutation_check.py`'s own sandbox (a temp copy
outside the repo — read `_sandbox`/`_discard` to confirm this, satisfying the throwaway-copy rule):

| capability | re-run result |
|---|---|
| tree kill, not just pytest | KILLED — matches manifest exactly |
| output to file, never a pipe | KILLED (all 6 tests in the file fail under the mutation; the two named tests are a subset, satisfying `is_kill`) |
| hung run still recorded TIMED_OUT | KILLED — matches manifest exactly |

`3/3 mutations killed`, independently reproduced. Sibling evidence (AT-490/491, `5/5`) re-verified
unaffected by the rename. No unenumerated capability claims found — the one narrative claim beyond
the table ("a browser grandchild can no longer block the probe") is explicitly hedged as argued, not
measured, in the manifest's own words, and is now carried forward as AT-495.

## Live browser

Not-applicable. Changed paths are `scripts/` and `tests/` only; no UI surface touched.

## Ledger housekeeping

- **AT-494**: verifiably fixed by commit 0ed84a7 (evidenced above). **Could not flip its ledger row
  to `fixed`**: the working-tree `qa/issues.jsonl` is currently missing the AT-494 row entirely
  (present in HEAD, absent from the live file — see AT-496 below), an apparent concurrent edit by
  another loop sharing this tree. Rather than hand-edit a contested shared line mid-write, I filed
  **AT-496** (medium) naming the exact discrepancy and the remedy (restore AT-494's row as `fixed`,
  citing this verdict; stop the AT-401/AT-490/AT-491 reversion from `fixed` back to `open`). This is
  a ledger-integrity observation, not a defect in AT-494's own code, and does not bear on this PASS.
- **AT-495** (low): filed per question 4 above.

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 9/9 applicable criteria met (C1/C4/C5/C6/C8/C9 not implicated by this unit), 0 invariants violated
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 3/3 rows reproduced (AT-494); sibling AT-490/491 evidence re-verified 5/5, unaffected by the rename
LIVE-BROWSER: not-applicable (scripts/ and tests/ only, no UI paths changed)
ISSUES-WRITTEN: AT-495 (low, disclosed-gap-to-issue), AT-496 (medium, ledger concurrent-edit discrepancy, not a code defect)
EXPLANATION: The AT-494 fix (Popen + log file + kill_tree, reusing mutation_check's own
bounded-kill instead of a second copy) is fully evidenced: 36/36 tests pass, ruff and doctor are
clean, and I independently reproduced both this unit's 3/3 mutation kills and the sibling AT-490/491
unit's 5/5 kills in mutation_check's own throwaway sandbox, with every kill correctly attributed to
its named test. The diff is scoped to exactly what the manifest declares (the one incidental deletion,
`_decode`, is dead code made dead by this unit's own declared rewrite, confirmed by a repo-wide
grep for remaining callers). The one residual claim beyond the tested table — resilience to a real
browser grandchild — is honestly hedged as argued-by-analogy rather than measured, and is now
tracked as AT-495 rather than left as untracked prose.
```
