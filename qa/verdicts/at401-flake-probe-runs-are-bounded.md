# Verdict — at401-flake-probe-runs-are-bounded

**Cycle checked:** 1
**Checker date:** 2026-09-17
**Unit commit:** cf34933

## What I re-ran (not trusted from the manifest)

- `uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe.py`
  -> `27 passed in 0.29s` (matches manifest).
- `uv run ruff check src tests scripts` -> `All checks passed!` (matches).
- `uv run autotester doctor` -> `doctor: clean` (matches).
- `uv run python scripts/mutation_check.py qa/evidence/at401-flake-probe-runs-are-bounded/mutations.json`
  -> `5/5 mutations killed`, exit 0, run time ~51s. For every one of the 5 mutations, the
  script's own "claims to kill" list equals its "actually failed" list (correct kill
  attribution, not just a non-zero exit code). `mutation_check.py._sandbox` copies the
  repo into a `tempfile.mkdtemp` owned root before mutating — confirmed by reading
  `scripts/mutation_check.py:219-239` — so running the verify command directly in the
  bound tree is read-only toward the artifact; this doubles as the Capability-coverage
  re-run (5/5 rows reproduced independently, all single-hunk edits to the single file
  named in "What changed", `scripts/flake_probe.py`).
- `git show cf34933 -- tests/test_flake_probe_runner.py` and `-- scripts/flake_probe.py`,
  and `git show cf34933 --stat`.

## Judgment on the three questions asked

**1. The one pre-existing test line.** `git show cf34933 -- tests` shows exactly one
line touched in a pre-existing test: `fake_run_once`'s signature in
`test_the_probe_runs_every_trial_even_after_one_fails` gained `timeout: float = 0`.
Read the full function body (`tests/test_flake_probe_runner.py:118-133`): every
assertion (`calls == [1, 2, 3, 4, 5]`, `len(summary.runs) == 5`,
`[r.index for r in summary.failures] == [2]`) and its docstring reason are byte-identical
to before. Nothing weakened. Confirmed.

**2. The disclosed UNVERIFIED residual (communicate() blocking on a grandchild holding
the pipe) with no issue id.** This is admissible enumerated debt, not an unenumerated
claim: it sits in "Known limits (disclosed, not claimed)", outside the Capability-coverage
table (so it is not masquerading as a proven capability), it names the exact mechanism
and the exact precedent (`mutation_check.py`'s AT-487/AT-490 log-file + tree-kill pattern),
and it states plainly that filing is the checker's job. AT-401's own `expected` clause
(pass a timeout; map `TimeoutExpired` to a distinct `Run` outcome) is fully met regardless
of this residual, so it does not block PASS — but a real gap named with no ledger row is
exactly what C7's spirit forbids leaving unrecorded. Filed **AT-494** (medium, matching
AT-487's severity for the same shape in the sibling file) into `qa/issues.jsonl`, quoting
the manifest's own disclosure as evidence and naming the concrete remedy (move `run_once`
onto `mutation_check.py`'s `_run_pytest`/`_kill_tree` pattern).

**3. Do the new tests prove the mapping or only their own stubs?** The dispatch's premise
("every one stubs `subprocess.run`") does not hold on inspection — only 2 of the 5 new
tests stub `subprocess.run`
(`test_a_run_that_outlives_its_bound_is_a_failure_marked_timed_out`,
`test_the_probe_keeps_going_after_a_timed_out_run`), and even those two stub only the
OS-level call itself while executing the REAL `run_once`/`probe` code including the real
`try/except TimeoutExpired` branch, the real `Run(...)` construction, and the real
`_tail`/`_decode` calls — that is the mapping, and it is exercised for real,
not re-implemented in the test. The other two new tests
(`test_a_timed_out_run_says_so_in_the_report_and_the_description`,
`test_the_cli_refuses_a_timeout_that_is_not_positive`) touch no subprocess machinery at
all: the first builds a real `Run(returncode=TIMED_OUT, ...)` object and calls the real
`describe()`/`write_report()`; the second calls the real `main()` CLI parsing path.
What is genuinely untested — and the manifest's own "Known limits" says so, just with
imprecise phrasing — is whether `subprocess.run(..., timeout=N)` actually terminates a
real hung OS process; that is stdlib behaviour, not this unit's code, and driving a real
30-minute hang in a unit test is impractical. No finding: the mapping this unit owns is
proven by execution, not merely stubbed around, and the one thing that IS stubbed away
(the OS timeout mechanism itself) is honestly disclosed rather than silently assumed.

## Diff scope (C10 / step 4c)

`git show cf34933 --stat`: `scripts/flake_probe.py`, `tests/test_flake_probe_runner.py`,
`qa/manifests/at401-flake-probe-runs-are-bounded.md`,
`qa/evidence/at401-flake-probe-runs-are-bounded/{mutations.json,mutations.out}`. All five
paths are named in the manifest's "What changed" or are the unit's own evidence
directory/manifest. No existing function, class, export, test, or config key was deleted
or renamed; the diff is additive plus the one signature-only edit addressed above.

## Capability coverage

5/5 rows in the manifest's table reproduced independently via `mutation_check.py`'s own
sandboxed run (see above) — same 5 mutation names, same file, same kill sets, same
attribution. No unenumerated claims.

## Issues addressed

AT-401 (medium): verifiably fixed by this unit — `run_once`/`probe` now pass
`timeout=`, map `TimeoutExpired` to `Run(returncode=TIMED_OUT, ...)`, `describe`/
`write_report` name it, and the CLI's `--timeout` is validated. Ledger row flipped
`open -> fixed`.

## Live browser

Not UI-touching. Changed paths: `scripts/flake_probe.py`,
`tests/test_flake_probe_runner.py` (plus manifest/evidence). No UI surface, direct or
indirect, is affected.

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C7), 0 project invariants violated
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced (independently, via mutation_check.py's own sandbox)
LIVE-BROWSER: not-applicable (scripts/flake_probe.py, tests/test_flake_probe_runner.py — no UI surface, direct or indirect)
ISSUES-WRITTEN: AT-494 (medium, disclosed communicate()/grandchild-pipe residual, filed per the manifest's own instruction)
EXPLANATION: All four re-run verify commands reproduced exactly (pytest 27 passed, ruff clean, doctor clean, mutation_check 5/5 killed with correct kill-attribution, sandboxed so read-only toward the bound tree). The one pre-existing test line touched is a stub-signature addition only, no assertion weakened. The disclosed residual is real, honestly enumerated, and now has an issue id (AT-494); it does not block this unit's own narrow claim. The "every test stubs subprocess.run" framing overstates the gap — 3 of 5 new tests exercise real production code with no subprocess involvement at all, and the 2 that do stub only the unavoidable OS call, not the mapping logic.
```
