# Verdict — at487-pytest-runs-are-bounded

**Cycle checked:** 1
**Date:** 2026-09-17
**Checker:** /checker Mode A, fresh subagent, bound to `D:/autoTesting`

## What I re-ran (never trusted the pasted output)

- `uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py
  tests/test_mutation_sandbox.py` → `............................................ [100%]`, exit 0
  (44 dots — matches the manifest's pasted count exactly).
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` (via `.venv/Scripts/autotester.exe doctor`) → `doctor: clean`.
- `uv run python scripts/mutation_check.py qa/evidence/at487-pytest-runs-are-bounded/mutations.json`
  in the bound tree (the script itself sandboxes to a temp dir, so this is read-only toward the
  repo) → `5/5 mutations killed`, exit 0. Output byte-for-byte matches the committed
  `mutations.out`.
- `git show f29c41a --stat` and `git show f29c41a -- scripts tests` — full diff read for scope
  (step 4c).
- `wc -l scripts/mutation_check.py tests/test_mutation_check_judgement.py` → 401 / 239 lines
  (matches the manifest's disclosed 401, already carried as AT-488; 239 < the 300-line cap C2
  states for `tests/`).

## Capability coverage — reproduced independently in 5 throwaway copies

Per row, in its OWN copy (`<scratch>/at487-row<k>`, scripts/+tests/+pyproject.toml only, deleted
after use, never the bound tree): confirmed the named check GREEN before the edit, applied the
manifest's exact single-hunk edit to `scripts/mutation_check.py` (each anchor matched exactly
once), then confirmed the SAME named test(s) turned red for the reason claimed.

| row | capability | green before | red after, real pytest output |
|---|---|---|---|
| 1 | every pytest run is bounded | `..` (2 passed) | Both `test_a_mutation_that_hangs...` and `test_a_hung_baseline...` FAILED with `AssertionError: still running after 120s: the pytest run is unbounded` — the mutation removed the timeout entirely, so my own re-run hung for the full 120 s bound and left an orphaned infinite-loop pytest process + a sleep(600) child, which I killed (`taskkill /F /T`) per the dispatch's process-hygiene filter. |
| 2 | a timed-out mutation is reported as timed out, never as a kill | `.` (1 passed) | `FAILED ... assert False is True` on `results[0]["timed_out"]` — fast (~20 s), no hang, no orphan (the real timeout logic was untouched). |
| 3 | the timeout kills pytest's children too | `.` (1 passed) | `FAILED ... AssertionError: the timeout killed pytest but not its child` — the surviving child (sleep 600) was killed by me afterward. |
| 4 | a zero or negative `timeout_s` is refused | `.....` (5 passed) | `[0]` and `[-5]` FAILED — `MutationError` never raised, execution fell through into `cannot collect ...: pytest exit -1` (the 0/-5 timeout itself now fires as a bogus immediate timeout, no hang). |
| 5 | a boolean `timeout_s` is refused | `.....` (5 passed) | `[True]` FAILED — `Failed: DID NOT RAISE MutationError` (True coerced to 1.0 s and the run just completed). |

`5/5 mutations killed` — twice independent (my 5 isolated single-hunk reproductions, plus my own
from-scratch re-run of the maker's bundled `mutations.json`), both matching the committed
`mutations.out` exactly. No unenumerated capability claim: the "What changed" prose describes
exactly these five behaviours and each has a row.

## Diff scope (step 4c)

`git show f29c41a --stat`: `scripts/mutation_check.py`, `tests/test_mutation_check_judgement.py`,
`qa/manifests/at487-pytest-runs-are-bounded.md`, and the unit's own `qa/evidence/at487-.../*`.
No file outside the manifest's "What changed" plus its own manifest/evidence. No existing
function, test, class, or config key was deleted or renamed — the diff is additive except for the
narrow single-purpose replacement of `_run_pytest`'s body (still the same function, same
signature plus one new keyword). C10 holds.

## Live browser

Not applicable — no UI surface touched (`scripts/`, `tests/` only, confirmed from the changed
paths, not from `qa/adapter.json`).

## The POSIX-branch disclosure (judged, per dispatch instruction)

The manifest marks `_kill_tree`'s POSIX arm (`os.killpg` + `start_new_session=True`) `UNVERIFIED`
with **no issue id**, reasoning "disclosure, not a claim." I judge that inadmissible as stated: the
manifest's own "What changed" prose asserts the POSIX arm "kills pytest AND its children," which
*is* a behavioural claim, and C7's own precedent (the unreachability clause, 2026-09-11) treats an
unproven property as something that must be **recorded**, not waived by relabelling it a
disclosure. The gap itself is real and reasonable to ship (CI is Windows-only today, and
`start_new_session` + `killpg` is the standard, well-understood Unix idiom) — this is not a
FAILURES-grade defect — but it needs a paper trail so a future POSIX CI run isn't the first time
anyone checks it. Filed **AT-491** below; does not block PASS.

## Additional finding: `_kill_tree`'s own cleanup wait is unbounded

`scripts/mutation_check.py:147-153` — after `taskkill /F /T` (whose failure is silently discarded,
`check=False`) or `os.killpg`, `_kill_tree` calls a bare `proc.wait()` with no timeout. If the
OS-level kill does not actually remove the immediate process (rare on Windows under `/F`, but not
impossible — a protected/unresponsive process), this call reproduces the exact unbounded-hang
class AT-487 exists to close, silently, one level down. Not exercised by any test here (killing an
unresponsive-to-`/F` process isn't practically simulatable), so it is not charged against this
unit's own claims, but it is a real residual gap in the fix's own safety net. Filed **AT-490**.

## Judgement

Both new findings are genuine but narrow edge cases layered on top of a fix that correctly closes
the reported defect (a hung mutation-induced pytest run) for the platform this project actually
runs on, proven twice over by independent re-derivation, not by trusting the manifest's paste.
Neither survives its own falsification, and neither is a claim this unit made and failed to prove.

```
VERDICT: PASS
SCOREBOARD: 3/3 relevant criteria met (C2 line cap, C7 verification independence + mutation duty, C10 commit scoping), 5/5 capability-coverage rows reproduced
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: scripts/mutation_check.py, tests/test_mutation_check_judgement.py)
ISSUES-WRITTEN: AT-487 (open -> fixed), AT-490 (new, low), AT-491 (new, low)
EXPLANATION: All 5 claimed capabilities reproduced independently in isolated throwaway copies (green before, named test red after, for the stated reason), and the maker's own bundled mutation spec re-ran clean (5/5 killed) in the bound tree. The 3-file targeted suite, ruff, and doctor are all green. Diff scope is additive and matches "What changed" exactly (C10 holds). Two new low-severity findings recorded (the disclosed-without-an-issue POSIX branch, and _kill_tree's own unbounded final wait) — neither invalidates a claimed capability or blocks PASS.
```
