# Verdict — at495-the-probe-kill-is-proven-not-argued

**Cycle checked:** 1
**Date:** 2026-09-18
**Unit commit:** `eb48415` (cherry-picked from `5771b8b`, `-x` line present)
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`

## What I re-ran myself

- `uv run pytest -q -o addopts= tests/test_flake_probe_runner.py tests/test_flake_probe_real_process.py`
  → `13 passed in 12.07s` — matches.
- `uv run ruff check src tests scripts` → `All checks passed!` — matches.
- `uv run autotester doctor` → `doctor: clean` — matches.
- `uv run python scripts/mutation_check.py qa/evidence/at495-the-probe-kill-is-proven-not-argued/mutations.json`
  → ran it **twice**, independently of the maker's and coordinator's own re-runs. Both of mine:
  `3/3 mutations killed`, and for each mutation the `claims to kill` list matched the `actually
  failed` list exactly (no over- or under-attribution) — no benefit of the doubt taken, both full
  outputs inspected line by line.
- Whole suite: not required by the brief's item list beyond what's above; the manifest's cited
  `-qq`/no-summary-line defect (AT-503) is a known, filed, unrelated issue.

## Item-by-item

**1. Does the real-process test prove what it claims?** Yes.
`test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
(`tests/test_flake_probe_real_process.py:31-61`) writes the grandchild's own pid to a file from
inside the spawned process, then asserts `not _alive(int(pid_file.read_text()))` after `run_once`
returns — death is checked against a pid the test itself recorded, the same shape as the sound
precedent `test_mutation_check_judgement.py::test_a_hung_baseline_is_refused_even_when_a_child_
holds_the_output_open` (`_alive(int(pid_file.read_text()))` at line 221 there). This is strictly
stronger than "the call returned" and matches the AT-487-era regression the manifest names (a
mutation removing the tree kill once survived a check that only watched the outer process end).
`_alive` on Windows filters by exact pid (`tasklist /FI "PID eq {pid}"`), not by name or image, so
the assertion cannot be satisfied by an unrelated process.

**2. The disclosed non-reproduction.** I ran the mutation set twice more myself, both clean
(3/3 KILLED, exact per-mutation attribution both times). Combined with the coordinator's one
independent clean run and the maker's own three post-anomaly clean runs, that is **6 clean runs
against 1 anomalous one**, unreproduced by three separate agents on a shared, loaded machine (the
`tasklist` snapshot I pulled during this check showed ~19 concurrent `python.exe` processes). I
verified the safety argument in code rather than taking it on the manifest's word:
`is_kill(exit_code, expected, failures)` at `scripts/mutation_check.py:83-109` returns
`exit_code == 1 and expected <= failures` — an extra failing test only ever adds to `failures`, so
it can only make `expected <= failures` easier to satisfy, never harder. The direction the manifest
claims is safe (cannot manufacture a false KILLED-when-should-be-SURVIVED into a false PASS of the
*unit*) is correct by inspection, not just assertion. The honest verdict, per the brief's own
framing: **the attribution flake is unmeasured, not absent** — a single non-reproducing anomaly
under machine load is not nothing in a repo whose own `flake_probe.py` docstring says 13 clean runs
barely constrain a 1-in-14 rate, and 6 clean runs constrain even less. This is a fair note against
an otherwise-PASSing unit, not a FAIL: it does not change the mutation results this unit is judged
on, and the mechanism precludes the one failure direction (false PASS) that would matter here.

**3. New file justified?** Yes. `tests/test_flake_probe_runner.py` is 263 lines against the 300-line
cap (C2), confirmed by `wc -l`. The claimed precedent is real, confirmed via
`git log --oneline --diff-filter=A`: `test_flake_probe_runner.py` was itself split out of
`test_flake_probe.py` at `1e95b1a`, and `test_mutation_check_judgement.py` /
`test_mutation_sandbox.py` were split out of `test_mutation_check.py` at `baf56a1` / `de484fd`. This
is the same seam recurring a third time, not an invented excuse for the cap.

**4. Cross-file test imports.** `_alive`/`_within` come from `test_mutation_check_judgement.py`,
`_FakePopen` from `test_flake_probe_runner.py` — genuine reuse, no redefinition. `doctor`'s
duplicate-concept check (`check_duplicate_definitions`, `src/autotester/doctor.py:113-126`) walks
`_python_files(root)`, which globs `root / "src"` only (`doctor.py:41-46`) — it does not look at
`tests/` at all, and even if it did, it skips any name starting with `_` (`doctor.py:121`), which
`_alive`/`_within`/`_FakePopen` all are. So this reuse is invisible to `doctor` either way, but it
is not duplication — it is exactly the pattern the 2026-09-16 C7 amendment already ruled admissible
for test-only units. The coupling (three test modules now share two helpers) is sound: the helpers
are tiny, single-purpose, and the alternative (redefining `_alive` a third time) is the actual C3
violation.

**5. Process safety.** Grepped `tests/test_flake_probe_real_process.py`, `scripts/flake_probe.py`,
`scripts/mutation_check.py`, and the two test modules it imports from, for
`taskkill|tasklist|psutil|process_iter|wmic|cmdline|Get-Process|Get-CimInstance`. The only hits are
`kill_tree`'s own `taskkill /F /T /PID <pid>` (production code, pre-existing, exact-pid) and
`_alive`'s `tasklist /FI "PID eq {pid}"` (exact-pid filter). Nothing in this unit's new file or its
imports enumerates by name, image, or command-line substring. The orphaned `sleep(600)` children
mutations 1 and 3 deliberately leave alive when applied are never targeted by anything except their
own bounded lifetime — confirmed by reading, not assumed.

## Diff scope (C10 / step 4c)

`git show --stat eb48415`: exactly `tests/test_flake_probe_real_process.py` (new, 88 lines),
`qa/manifests/at495-the-probe-kill-is-proven-not-argued.md` (new), and the unit's own
`qa/evidence/.../mutations.{json,out}` — matches "What changed" exactly. Nothing deleted, nothing
renamed, no production file touched. Not UI-touching — confirmed from the changed paths above, no
Mode D needed.

## Capability coverage

4/4 rows reproduced. `scripts/mutation_check.py` is itself the sandboxing instrument (`_sandbox`
copies the tree outside `.git` before mutating, restores after — the project's established pattern
for mutation-based capability evidence, not a manual throwaway copy): baseline asserted green
before any mutation (`_check_in`, `scripts/mutation_check.py:332-336`), each anchor matched exactly
once and the file changed and was restored (asserted by the harness itself, `mutation_check.py:342-
350, 360-362`), and across my two independent re-runs every mutation's claimed `kills:` list
equalled its actual failure list exactly — no wrong-reason kill, no syntax-error false-KILLED, no
`defends:`-names-nothing case.

## Ledger

AT-495 closed `open -> fixed`.

## Block

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, C7 and C2 hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 4/4 rows reproduced (own re-run of scripts/mutation_check.py, sandboxed by the instrument itself; 2 independent runs, exact attribution both times)
LIVE-BROWSER: not-applicable (changed paths: tests/test_flake_probe_real_process.py, qa/manifests/at495-the-probe-kill-is-proven-not-argued.md, qa/evidence/at495-the-probe-kill-is-proven-not-argued/{mutations.json,mutations.out} — no UI surface touched)
ISSUES-WRITTEN: none (AT-495 closed open->fixed in the ledger; no new issue — the kill-attribution anomaly is recorded above as an unmeasured, non-reproducing flake, not a filed defect, since it cannot manufacture a false PASS and did not reproduce across 6 further runs by three agents)
EXPLANATION: Both AT-495 gaps are genuinely closed by isolating, mutation-verified tests — the real-process test asserts the grandchild's death by a pid it recorded itself, not merely that the call returned, and all 3 mutations killed cleanly and attributably across my own two re-runs. The new file is a real seam with two prior precedents in this exact file family, and its cross-module imports are reuse, not duplication (doctor doesn't even scan tests/ for this). Process-kill safety holds: everything greps to exact-pid filters. The one disclosed soft spot — one anomalous mutation-attribution run in seven total — is real but not disqualifying: the safety property the manifest claims (expected<=failures cannot manufacture a false PASS) checks out from the code, and it remains unreproduced rather than explained.
```
