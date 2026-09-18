# Verdict — at521-finish-the-q-sweep

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh subagent, bound to `d:/autoTesting`
**Commit under check:** `15a7ef1` (`fix(qa): finish the -q sweep across goal.json and the doc surfaces (AT-521/AT-522)`); HEAD has since advanced to `dae12d8` (`chore(qa): stamp the at521-dispatch tick`, no content change) plus this checker's own contract/ledger edits.

## What I re-ran myself (never trusted pasted output)

1. **`.goal/goal.json` diff, re-derived against the true parent commit `7f7eeeb`** (not `HEAD~1`,
   which is a tick-stamp commit that landed after this unit — resolved after an initial confusion).
   `git diff 7f7eeeb 15a7ef1 -- .goal/goal.json`: 47 insertions / 47 deletions. Independently
   isolated every changed line: **43 lines are exactly `-q` removed from a `"cmd"` string, nothing
   else on those lines**; the remaining 4 changed lines are `"updated"` timestamp (length-neutral),
   `velocity_per_day`/`eta_days` (analytics block), and `last_deterministic_tick` — all disclosed by
   the manifest as pre-existing dirty state from a separate live process, present before the unit
   started. No reordering, no reformatting, no task/status/deps field touched. Cross-checked the
   manifest's own byte-delta claim (129 = 43×3) against my own commit-level byte delta (43160→43030
   = 130): the 1-byte gap is exactly explained by `velocity_per_day` shrinking from `4.15` to `2.2`
   (one fewer character) in that same pre-existing, disclosed diff — both numbers are internally
   consistent, not a discrepancy. Task count confirmed 55→55 via `git show <rev>:.goal/goal.json`
   piped through `json.load`.
2. **No live `-q` doubling remains.** `grep -c ' -q' .goal/goal.json` → 0. `grep -n
   'pytest -q\|pytest.*-q"' CLAUDE.md AGENTS.md qa/loop.md` → only two hits, both in `CLAUDE.md:91`
   and `AGENTS.md:91`'s explanatory comment text ("stacking another -q makes pytest -qq") — prose
   about the bug, not a live command. Read `CLAUDE.md`, `AGENTS.md`, and `qa/loop.md` in full around
   the claimed lines: all corrected.
3. **Premise re-verified independently**, on a different row than the manifest used
   (`tests/test_coverage.py` rather than its own earlier pick): bare `uv run pytest
   tests/test_coverage.py` → `13 passed in 2.89s`; the same command with CLI `-q` added → dots only,
   no summary line. Confirms the doubling mechanism on a fresh example.
4. **The regression and its fix.**
   - `tests/test_goal_done_checks.py:229` now reads `f"uv run pytest {spec}"` (verified via
     `git diff 7f7eeeb 15a7ef1 -- tests/test_goal_done_checks.py`) — a single-hunk change that adds
     an explanatory comment and drops only the stale `-q` from the *expected* value; the assertion
     still requires exact equality of all ten `T-160..T-169` deps+cmd pairs. Nothing weakened.
   - Ran `tests/test_goal_done_checks.py` + `tests/test_goal_done_check_shapes.py` together myself:
     **9 passed**, no failures.
   - Read `tests/test_goal_done_check_shapes.py` in full: lines 23 and 53 are entries in
     `is_capable_of_failing`'s own `rejected`/`accepted` fixture lists — synthetic strings driven
     directly at the predicate to test its shape-recognition (whole-suite-as-a-path, `--collect-only`
     aliases, `||`/`;`/`&&` no-op tails, etc.), never read from `.goal/goal.json`. The manifest's
     judgment that these are correct as-is and not stale assertions about goal.json's content is
     right — confirmed by inspection, not taken on trust.
5. **Full suite**, bare, `PYTHONUTF8=1`, redirected to `qa/evidence/at521-finish-the-q-sweep/checker_full_suite.log`,
   judged by exit code plus a whole-log scan (`grep -nE 'FAILED|ERROR|^E '`, zero hits):
   **`1486 passed, 2 skipped, 32 xfailed, 1 warning in 969.43s`, exit 0.** The 2 extra passed vs. the
   stated `1484` baseline are attributed to the concurrently-running AT-520 build agent's work,
   which landed as commit `9ca9f99` (`feat(map): generate a Scripts section so scripts/ stops being
   invisible (AT-520)`, committed 08:58:01) — inside my full-suite run's own window (log started
   08:56, finished ~09:12 given the reported `969.43s` runtime), touching `docs/MAP.md` and
   `src/autotester/ledger/render.py`/`tests/test_ledger.py` (explicitly out of scope for me per the
   dispatch), not this unit. This unit's own diff (`7f7eeeb`→`15a7ef1`) touches no `src/` file and
   no test file other than the single disclosed hunk in `tests/test_goal_done_checks.py` above.
   No failure appeared in `tests/test_flake_probe_real_process.py` (the known AT-196/AT-505/AT-518
   timing flake) in this run, so no isolated re-run of it was needed. `uv run ruff check src tests scripts` → `All checks passed!`. `uv run autotester doctor` →
   `doctor: clean`.

## Diff scope (step 4c)

`git diff 7f7eeeb 15a7ef1 --stat`: `.goal/goal.json`, `AGENTS.md` (new, untracked→tracked),
`CLAUDE.md`, `qa/evidence/at521-finish-the-q-sweep/*`, `qa/loop.md`, `qa/manifests/at521-*.md`,
`tests/test_goal_done_checks.py`. No file outside this set touched; no function, class, export,
route, test, or config key deleted or renamed. The one test-file edit is disclosed prominently in
the manifest's own Step 4 (attributed explicitly to the orchestrating maker, with rationale) rather
than hidden — I treat that disclosure as satisfying the spirit of a "What changed" declaration even
though the manifest has no literal header by that name.

## Capability coverage

| capability | check | falsifying condition | reproduced |
|---|---|---|---|
| Per-file pytest `cmd` rows print a summary once fixed | `uv run pytest tests/test_coverage.py` bare vs. with `-q` restored | put `-q` back | yes — bare `13 passed in 2.89s`, doubled: dots only |
| `.goal/goal.json` otherwise byte-identical | byte delta, JSON validity, task count, full diff | any unrelated change | yes — 43 `-q` removals + 4 disclosed pre-existing lines, nothing else, delta reconciled exactly |
| No doc surface still instructs the doubled command | grep across CLAUDE.md/AGENTS.md/qa/loop.md | live command match | yes — zero live matches, only historical prose |
| doctor/ruff unaffected | `uv run autotester doctor`, `uv run ruff check src tests scripts` | either non-clean | yes — both clean |

Prose-edit rows carry `revert_op: none` (same as AT-503's own precedent) — reverting wording changes
nothing pytest does; this is a legitimate, disclosed exemption, not an unenumerated claim.

CAPABILITY-COVERAGE: 4/4 rows reproduced by me.

## Contract amendment (routine, my write-surface)

Confirmed the manifest's disclosed residual: `qa/contracts/core-invariants.md` carried the same
stale CLI `-q` on three Verify clauses other than C7 — **C1** (`tests/test_schema.py -q`, line 23),
**C5** (`tests/test_core.py -q`, line 56), **C9** (`tests/test_goal_criticality_vocabulary.py
tests/test_goal_done_checks.py -q`, line 139). Re-grepped the whole file afterward — no other Verify
clause carries a bare `-q` (the two remaining hits are historical amendment-log prose about the old
bug, not live clauses). Folded all three in as a routine amendment (shell string only, no criterion
weakened) and appended a dated amendment-log entry, exactly as the AT-503 checker did for six other
contract files.

## Ruling on the AT-523 extension recommendation

Agree with the manifest's argument: this unit is direct proof the defect is not self-healing (it
survived two weeks in 43 rows of a second file after AT-503's fix), `.goal/goal.json` has far more
edit surface than the single `qa/adapter.json` string AT-523 already guards, and the natural home
for the guard (`tests/test_goal_done_check_shapes.py`, which already hosts predicate-correctness
fixtures) is uncontroversial. Filed **AT-524** (low, tooling) capturing the recommendation as a
fast-follow, referencing AT-523. Not built here — it requires a `tests/` edit and no urgency; the
unit's own stale expectation is already fixed and green.

## Ledger

- **AT-521**: open → **fixed** (`fixed_date: 2026-09-18`). Verified: no live `-q` remains in
  CLAUDE.md/AGENTS.md/qa/loop.md.
- **AT-522**: open → **fixed** (`fixed_date: 2026-09-18`). Verified: 0 remaining `-q` in
  `.goal/goal.json`; 43/43 rows corrected, nothing else touched.
- **AT-524**: new, open, low — AT-523-extension recommendation (see above).
- Edited only the two target lines plus one appended line in `qa/issues.jsonl`; `git diff --stat`
  confirms `2 insertions(+), 2 deletions(-)` for the flips and a clean append for AT-524 — no
  reformatting, `\uXXXX` escaping preserved throughout (unaffected, since only `status`/`fixed_date`
  values were touched).
- Next free id after this check: **AT-525**.

## Live browser

Not UI-touching. Changed paths: `.goal/goal.json`, `CLAUDE.md`, `AGENTS.md`, `qa/loop.md`,
`qa/contracts/core-invariants.md`, `qa/issues.jsonl`, `qa/manifests/at521-*.md`,
`qa/evidence/at521-*/*`, `tests/test_goal_done_checks.py`. No `src/`, no UI route, no retrieval/
ranking surface.

## Push

D-007: pushing `origin master` myself after this commit, no confirmation asked (public repo,
narrowly-scoped, independently verified commit).

---

VERDICT: PASS
SCOREBOARD: 5/5 falsifiable claims met, 4/4 invariants hold (C1, C5, C7, C9 Verify clauses all
correct and green; C2–C4, C6, C8, C10 unaffected by this unit's scope)
FAILURES (if any): none
CAPABILITY-COVERAGE: 4/4 rows reproduced by checker
LIVE-BROWSER: not-applicable (no UI/src surface changed — see Changed paths above)
ISSUES-WRITTEN: AT-524 (new) · AT-521, AT-522 flipped open→fixed
EXPLANATION: The `.goal/goal.json` edit is exactly the 43 disclosed `-q` removals plus pre-existing,
disclosed dirty state (byte math reconciled independently); no live doubling remains in any of the
four named surfaces; the premise was reproduced fresh on a different row than the manifest used; the
Step-4 regression fix is correct, narrowly scoped, and both affected test files pass; the full bare
suite is green (1486 passed, 0 failed, exit 0) with the 2-test surplus attributed to a disclosed
concurrent unit outside this scope. I additionally folded three residual contract Verify clauses
(C1/C5/C9) that carried the same stale `-q`, and filed AT-524 for the manifest's guard-extension
recommendation, which I agree with.
