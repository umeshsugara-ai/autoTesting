# Verdict — at490-491-tree-kill-is-bounded

**Cycle checked:** 1
**Date:** 2026-09-17
**Checker run:** fresh subagent, Mode A, bound to `D:/autoTesting`
**Unit commit:** 176a89c

## What I re-ran myself (bound tree)

- `uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py`
  → `...............................................` (47 passed), matches manifest.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at490-491-tree-kill-is-bounded/mutations.json`
  → `5/5 mutations killed`, exit 0. Reproduced independently (not pasted).

## Capability coverage — independently reproduced, all 5 rows

Each row reproduced in its own throwaway copy of the tree (scratch dir outside the repo, `.git`
excluded), never in the bound tree. Named check GREEN before the edit in every copy, red after
for the reason it is named for, then reverted (`diff` against the bound tree confirmed byte-identical
after every revert):

1. **Post-kill wait is bounded** — `proc.wait(timeout=KILL_GRACE_S)` → `proc.wait()`: both
   `test_a_process_that_survives...` and `test_the_posix_arm...` failed, both on the
   `waited_with[-1] is not None` assertion (the shared `_FakeProc` records the actual timeout
   argument, so both tests notice a stripped bound) — matches manifest's stated joint failure
   exactly, not a wrong-reason red.
2. **A survivor is refused, not ignored** — `raise MutationError(...) from exc` → `return`:
   `test_a_process_that_survives...` failed with `DID NOT RAISE MutationError`. Right reason.
3. **A POSIX group already gone does not crash the run** —
   `contextlib.suppress(ProcessLookupError)` → `contextlib.suppress(OSError if False else ())`:
   `test_the_posix_arm...` failed with an unhandled `ProcessLookupError` propagating out of
   `_kill_tree`. Right reason.
4. **The POSIX arm SIGKILLs the session** — `os.killpg(proc.pid, signal.SIGKILL)` →
   `os.killpg(proc.pid, 15)`: `test_the_posix_arm...` failed asserting `[(4242, 15)] == [(4242, 9)]`.
   Right reason.
5. **Non-ASCII pytest output survives the log round trip** — `PYTHONUTF8="1",` removed:
   `test_non_ascii_pytest_output_survives_the_log_round_trip` failed — the refusal text contained
   a literal replacement character in place of `café ✓` (`assert 'caf\xe9 \u2723' in '...baseline
   is NOT green... \u2014...'` — the café text was gone, replaced by `\ufffd`). Right reason.

`CAPABILITY-COVERAGE: 5/5 rows reproduced.`

## Diff-scope check (4c)

`git show 176a89c --stat` / full diff: touches only `scripts/mutation_check.py`,
`tests/test_mutation_sandbox.py`, plus the unit's own `qa/evidence/at490-491-tree-kill-is-bounded/`
and `qa/manifests/at490-491-tree-kill-is-bounded.md` — exactly the manifest's "What changed" plus
its own evidence/manifest. No function, test, export, or config key was deleted or renamed. No
file outside the claimed set was touched. Clean.

## Issues addressed — judged against each issue's own `expected`

- **AT-490** (expected: give the post-kill `proc.wait()` its own short timeout and raise/log
  distinctly rather than waiting silently forever; *consider* asserting taskkill's exit code) —
  **FIXED**. `proc.wait(timeout=KILL_GRACE_S)` + `except TimeoutExpired: raise MutationError(...)
  from exc` does exactly the required half; the "consider" clause on taskkill's exit code was
  explicitly declined with a stated reason (taskkill returns non-zero whenever any child had
  already exited — measured 128 this session — so its exit code cannot distinguish success from
  a merely-partial kill; the bounded `proc.wait()` is what actually decides). That is a judgement
  call within what the issue asked the maker to "consider," not a gap against the mandatory half.
- **AT-491** (expected: *either* a POSIX CI runner exercises the real hang tests, *or* an explicit
  code-level test mocks `os.name` to prove the killpg call shape, before the branch is trusted in
  production) — **FIXED at the level the manifest claims.** Neither literal option was taken;
  instead `_kill_tree` was refactored so `posix` is an explicit parameter
  (`posix: bool = os.name != "nt"`), and `test_the_posix_arm_kills_the_whole_session_and_tolerates_
  a_group_already_gone` calls `_kill_tree(proc, posix=True)` directly with `os.killpg` and `signal`
  stubbed. I judge this an acceptable substitute for "mocks os.name": mocking `os.name` would not
  even work against the *new* code, since the default argument `os.name != "nt"` is evaluated once
  at function-definition time (import), not per call — a test that monkeypatched `os.name` after
  import would have no effect on that default. The parameter refactor is the mechanism that makes
  the branch explicitly selectable and testable on one host, which is the same end the issue was
  asking for (proving the killpg call shape before trusting it on POSIX), reached by a cleaner
  route than the one the issue named. The manifest's own disclosure is accurate and I confirm it:
  **no POSIX host has run the real hang tests** (`tests/test_mutation_check_judgement.py`'s
  `test_a_mutation_that_hangs...` / `test_a_hung_baseline_...`), so `start_new_session=True` +
  real `killpg` on a live POSIX runtime is still unexercised end-to-end — the call *shape* is
  pinned, the real-OS *behaviour* is not. I am not filing a new low-severity issue for that
  narrower residual: it is the same gap AT-491 already named as its first (undone) option, already
  on record, and re-filing it as a new ledger row would just be AT-491's own text with a new
  number.

Both closed `open -> fixed` in the ledger (a later re-check would move `fixed -> verified`).

## Adversarial probes

- **Do the stubs prove the real code path, or only themselves?** All three new tests call the
  real `mutation_check._kill_tree` / real `mutation_check.check` — nothing under test is
  reimplemented. `test_a_process_that_survives...` and `test_the_posix_arm...` stub only the
  process handle and `os.killpg`/`signal`/`subprocess.run`, i.e. the OS boundary, and let the real
  function body run; confirmed above by seeing 5/5 rows redden the real code for the real reason
  in an isolated copy. `test_non_ascii_...` stubs nothing — it runs a real nested pytest
  subprocess through the real `_run_pytest`/`check`.
- **Does `PYTHONUTF8=1` change any pre-existing mutation spec's outcome?** Re-ran both sampled
  specs against the fixed harness, independently: `qa/evidence/at468-unreadable-reason-never-
  quotes-content/mutations.json` → still `3/3 mutations killed`; `qa/evidence/at481-report-path-
  fixed-at-plugin-load/mutations.json` → still `1/1 mutations killed`, exit 0. No change.
- **Is a `MutationError` raised inside `_run_pytest`'s `with open(log)` block handled cleanly?**
  Traced it: `_kill_tree`'s new `raise MutationError(...) from exc` happens inside the `except
  subprocess.TimeoutExpired:` clause, which is inside `with open(log, "w", ...) as sink:`. A `with`
  block closes its file on any exception, so the log handle is not leaked. The exception then
  propagates out of `_run_pytest`, through `collected_tests`/`_check_in`, through `check()`'s
  `try/finally` (the sandbox is still discarded — no leaked temp dir), and is caught cleanly by
  `main()`'s `except MutationError as exc: print("MUTATION RUN INVALID: ..."); return 2` — a
  distinct exit code from a normal 0/1 report. No unhandled propagation, no resource leak.

## Structural checks

- File sizes: `scripts/mutation_check.py` is 416 lines — `scripts/` is outside C2's 300-line rule
  (only `src/` and `tests/` are covered), and the manifest discloses this as a known limit
  (AT-488, structural-erosion signal, not a fail). `tests/test_mutation_sandbox.py` is 255 lines,
  within C2. `uv run autotester doctor` (re-run above) confirms clean.
- C7's pre-existing baseline/anchor/kill-attribution machinery in `check()`/`_check_in` is
  untouched by this unit and still present (`if code != 0: raise MutationError("baseline is NOT
  green...")`; anchor-match-exactly-once; `is_kill`'s exit==1-and-expected<=failures pairing) —
  confirmed by reading, not just assumed, since this unit's own mutation run exercises it live.
- C10 (commit carries only its own paths): `176a89c` touches exactly
  `scripts/mutation_check.py`, `tests/test_mutation_sandbox.py`,
  `qa/evidence/at490-491-tree-kill-is-bounded/*`, `qa/manifests/at490-491-tree-kill-is-bounded.md`
  — no other unit's paths. Clean.
- Not UI-touching (changed paths are `scripts/` and `tests/` only) — Mode D not applicable.
  No external-data collection — 5c not applicable.

## Note on AT-492

A later sweep (uncommitted at check time) filed AT-492 (high) for this manifest sitting
ready-for-check with no verdict since 176a89c — an accurate dispatch-gap finding at the time it
was raised. This verdict resolves it; I have not touched AT-492's ledger row myself since my
manifest's "Issues addressed" names only AT-490/AT-491, and AT-492 was never part of what this
unit claims to fix. The maker/next sweep can close AT-492 against this verdict's timestamp.

```
VERDICT: PASS
SCOREBOARD: 2/2 issues addressed evidenced, 0/0 unit-specific contract criteria (core-invariants
is project-wide; C2/C7/C10 all hold on evidence above), 5/5 capability-coverage rows reproduced
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: scripts/mutation_check.py, tests/test_mutation_sandbox.py)
ISSUES-WRITTEN: none
EXPLANATION: All four verify commands reproduced independently in the bound tree (47 tests, ruff
clean, doctor clean, 5/5 mutations killed). All 5 capability-coverage rows independently
reproduced green-before/red-after-for-the-right-reason in isolated throwaway copies, each reverted
byte-identical to the bound tree. Diff scope is exactly the claimed files plus the unit's own
evidence/manifest. AT-490 fixed in full; AT-491 fixed at the level of proving the killpg call
shape via an explicit posix parameter rather than an os.name mock (a stronger substitute, since
os.name is read only once at import time under the new code) — the disclosed residual (no real
POSIX-host run of the hang tests) is the same gap AT-491 already named as its other option, not a
new defect. PYTHONUTF8=1 does not change at468's or at481's pre-existing mutation outcomes.
MutationError raised inside _kill_tree during a timed-out kill propagates cleanly through
_run_pytest -> check()'s try/finally -> main()'s except clause with no leaked file handle or
sandbox directory.
```
