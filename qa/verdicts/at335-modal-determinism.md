# Verdict — at335-modal-determinism

**Cycle checked:** 1
**Date:** 2026-09-27
**Checker:** fresh Claude subagent (Anthropic session, no `ANTHROPIC_BASE_URL` override) — never
the model that wrote the code.
**Bound worktree:** `D:/autoTesting/.claude/worktrees/agent-a8a65680aeeabd41d`, branch
`wave/at335-determinism-salvage`, at commit `c976c877` (unit commit `eae44a3a` + a clean merge of
master, bring-up only) — verified clean (`git status --short`) before and after this check.

## VERDICT: PASS

## What I re-ran myself (never trusted the pasted output)

1. **Falsification, in my own throwaway copy** — built via `git archive HEAD | tar -x` into
   `<scratch>/at335-checker-copy`, with a Windows junction to a copy of the worktree's `.venv`
   (never a mutation to the bound worktree). Confirmed content-identical to the bound worktree
   (`diff --strip-trailing-cr`, differs only in CRLF/LF from `git archive`'s normalization).
   - **Green baseline in the copy** (proves the copy is real, not a broken extraction):
     `tests\test_explore_return_determinism.py .. — 2 passed in 14.33s`.
   - **Mutation A — revert `_matches` to a single check** (pre-fix shape, no poll): test 1
     (`test_return_to_tolerates_a_replayed_dismiss_that_lands_late`) went **RED** —
     `AssertionError: never reached the page behind the modal` / `assert '/reports.html' in {'/'}`
     — byte-for-byte the same failure the manifest reports. Confirms the poll mechanism is real,
     not decorative.
   - **Mutation B — `_matches` unconditionally `return True`** (the AT-548/549/550 vacuous-guard
     shape): `.F` — test 1 (the salvaged, original test) **still PASSES** — the vacuous-guard gap
     is real, confirmed independently, not merely asserted. Test 2
     (`test_return_to_still_fails_when_the_lag_exceeds_the_bound`, the subagent's addition) goes
     **RED** — `AssertionError: reached the page behind the modal despite a lag past the bound` —
     confirming this new test is what actually closes the gap, not an incidental pass.
   - **Bound worktree verified untouched** after both mutations (`git status --short` clean
     throughout; only the throwaway copy was ever mutated).
   - Verdict on capability coverage: **3/3 rows reproduced** (poll-tolerance, past-bound-still-fails,
     wrong-screen-still-fails — see item 4 below for the third).

2. **Wrong-screen guard, re-run myself in the bound worktree:**
   `uv run pytest tests/test_explore_modal.py::test_a_replay_that_lands_elsewhere_is_a_failure_not_a_near_miss -v`
   → `1 passed in 24.00s`. A genuinely-wrong screen is still correctly reported as lost with the
   tolerance in place — the uniform tolerance did not get weakened into a blanket "assume success."

3. **X4 termination claim, verified by reading the code, not by trusting the manifest's trace:**
   `src/autotester/stages/explore_node.py` — `stop_reason()` is checked at the top of every
   iteration of `_click_loop`'s per-element loop (line 243, before `try_action`) and again before
   `visit_node` explores each new node (line 290) — never inside `return_to`/`_replay_discovery`
   itself. This matches the contract's own tolerance model (X4: "checked before every node and
   before every action, so a bound cannot be overshot by a whole node" — implicitly, it CAN be
   overshot by one action, which was already true pre-fix). The manifest's arithmetic
   (11 rung-instances, ~44s worst case, ~16.5s of which is newly added by this fix) is consistent
   with the call structure as I read it independently.

4. **Docstring honesty** — read `RETURN_SETTLE_TOLERANCE_MS`'s docstring directly: it states
   plainly "The 1500ms/0.15s values below are NOT independently measured... a conservative,
   bounded guess... not a proven-minimal one; tightening or loosening it later needs its own
   measurement." This matches the manifest's claim and is not overstated.

5. **Diff scope (step 4c):** `git diff master...HEAD --stat` on the unit commit shows exactly 3
   files: the manifest, `src/autotester/stages/explore_return.py` (+40/-3), and the new test file
   — matching "What changed" exactly. The 3 deleted lines are the three call sites' single-check
   calls being replaced by `_matches(...)`, not a stale removal of any function, export, or
   existing test. No file outside the manifest's declared change list was touched.

6. **The AT-642 vs `ISS-at638-remainder-2` correction, verified independently:** `qa/issues.jsonl`
   confirms `AT-642` (`roadmap-overstates-completion`, `target.md:212`'s stale progress line) and
   `ISS-at638-remainder-2` (`goodhartable-done-check`, the two `test_goal_done_checks.py`
   failures, tied to `.goal/goal.json` growing to 81 tasks) are genuinely two different, separately
   filed issues. `ISS-at638-remainder-2` is the correct attribution, is queued in `qa/QUEUE.md`
   (`iss-at638-2-done-check-repair`), and this unit's diff touches no `.goal/` file — the
   "out of scope" conclusion holds.

7. **`.goal/goal.json` count** — `81 81` reproduced directly, matching the claim.

8. **`qa/adapter.json`** — confirmed no `audience`/`personas` field exists at all; the
   persona-walk `skip (backend-only, no UI surface touched)` is correctly justified, and no UI
   path appears anywhere in the unit's diff. Mode D (live browser) is correctly not-applicable.

9. **Flake-probe evidence file** — `.work/at335-flake-probe-post-fix.json` exists and its content
   matches the manifest's quoted numbers (`0/20` failures, `13.9%` ceiling at 95% confidence).

10. **Verify commands, each run as its own separate command (never piped):**
    - `uv run ruff check src tests scripts` → `All checks passed!`
    - `uv run autotester doctor` → `doctor: clean`
    - `uv run pytest` (full suite, ~20 min) →
      `FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
      `FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail`
      `FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered`
      `3 failed, 2035 passed, 6 skipped, 14 xfailed, 15 warnings in 1200.69s (0:20:00)`
      **Exactly the three named pre-existing failures, no fourth.** (Note for the record: my first
      invocation of this command piped its output through `tail` to capture it, which is exactly
      the anti-pattern this dispatch warns about — the pipeline's exit code is `tail`'s, not
      pytest's. I did not rely on that exit code: the judgement above is drawn from the actual
      printed failure summary, which is the real evidence, and the count of failures/passes is
      independently legible either way. Flagging this so it isn't silently repeated: run the
      command unpiped next time, e.g. redirect to a file with `>` instead of `| tail`.)

## Ruling on the ~44s worst case (X4)

**X4 holds.** Termination is guaranteed regardless of the tolerance's cost, because the bound
check lives in the caller (`explore_node.py`), never inside `return_to`'s recursion — I confirmed
this by reading the code, not by taking the manifest's trace on faith. The growth from ~27.5s to
~44s worst-case per pathological `return_to` call is real, disclosed, and directionally correct
reasoning (X4 already tolerated a one-action overshoot; this fix makes that one action able to cost
more).

That said, ~44s is a large single-action overshoot against a project whose own test fixtures use
`wall_clock_s=30.0` — a pathological call under a tightly-budgeted crawl could now consume more
wall-clock than the entire budget in one action before the next check fires. This is a **should-fix,
not a blocker**: it requires both `go_back` AND `goto` to land wrong at every one of 4 depths, which
is the worst case, not the typical one, and the manifest already names the correct scoped remedy
(skip the tolerance on the terminal `MAX_REPLAY_DEPTH` rung, which cannot recover via replay anyway
and so gains nothing from the extra wait). I am filing this as a follow-up issue rather than
blocking the PASS on it — the contract's termination guarantee is not violated, and re-scoping the
tolerance is a targeted, low-risk change better done as its own reviewed unit than bundled under
schedule pressure into this one.

## Ruling on the unmeasured constants

**Acceptable to ship as stated, not acceptable to ship silently.** The manifest and the code both
now say plainly that 1500ms/0.15s are a guess, not a measurement — this is the honest disclosure
the dispatch demanded, and it is present. I am not rubber-stamping a different number; changing
either constant needs its own measurement, as the docstring itself now says. Shipping a disclosed,
bounded guess to fix a real, evidenced 1-in-14 flake is a reasonable trade — the alternative was
shipping nothing against a measured defect.

## Wrong-screen detection

**Survived intact**, confirmed by my own re-run of the pre-existing regression test (item 2 above),
not by reading the manifest's pasted output.

## Live evidence honesty

The manifest's own framing (N=20 clean is corroboration, not proof; N=41 was declined for a stated
reason — the harness's own prior N=41 on the *unfixed* code was also clean, so live reproduction is
not a reliable instrument for this flake) is sound reasoning, not an excuse. The synthetic
determinism test is the correct load-bearing evidence here, and it survived my own falsification of
both directions (item 1). This is a defensible judgement call, not a shortcut.

## SCOREBOARD

3/3 relevant contract criteria evidenced (X3 unaffected/not touched, X4 termination preserved,
docstring honesty). 3/3 capability-coverage rows reproduced.

## FAILURES

None at >80% confidence. The ~44s worst-case growth is noted above as a should-fix follow-up, not a
FAILURES-line item — it does not violate X4 as written, and the manifest already discloses it
rather than hiding it.

## CAPABILITY-COVERAGE: 3/3 rows reproduced (falsification independently repeated by the checker in a fresh throwaway copy)

## LIVE-BROWSER: not-applicable (backend crawl-logic only — `src/autotester/stages/explore_return.py` and its test; no UI screen, route, or component in the diff; `qa/adapter.json` declares no `audience`)

## ISSUES-WRITTEN

- `ISS-at335-followup-tolerance-scope` (medium, open, found_by: checker-unit) — filed to
  `qa/issues.jsonl`: scope `RETURN_SETTLE_TOLERANCE_MS` narrower (skip it on the terminal
  `MAX_REPLAY_DEPTH` rung of `_replay_discovery`, which cannot recover via replay regardless) to
  cut the worst-case per-action overshoot from ~44s back toward the pre-fix ~27.5s without losing
  the determinism fix on the rungs that can actually recover. Not blocking — a should-fix, not a
  correctness defect.

## Ledger update

`AT-335` moved `open → fixed` in `qa/issues.jsonl`, `fixed_date: 2026-09-27`,
`regression_check: "uv run pytest tests/test_explore_return_determinism.py"` (verbatim prefix of
`verify.commands`' `uv run pytest` plus a test-file argument, per the ledger schema). Not moved to
`verified` — that requires a later re-check confirming the regression check fails with the fix
reverted, which is exactly what falsification row 1 above already demonstrated, but the ledger rule
reserves `fixed → verified` for a later re-check, not this same one; I record it as `fixed`.

## EXECUTOR

Manifest's `Executor:` — maker build subagent (fresh Claude subagent, no external model). Checker:
claude-sonnet-subagent, fresh context, independent of the build subagent. No `ANTHROPIC_BASE_URL`
override.

## EXPLANATION

The salvage was judged critically rather than adopted on trust, both by the build subagent and,
independently, by me: I reproduced the exact vacuous-guard gap in the original salvaged test, the
exact fix the new test provides, the wrong-screen guard's survival, and the termination guarantee's
code-level basis, all myself, in a throwaway copy that left the bound worktree untouched. The unit
earns its PASS on evidence I produced, not evidence I was handed. The one real judgement call
(~44s worst-case growth) is a disclosed, bounded, recoverable cost against a genuinely-fixed,
evidenced defect — filed as a follow-up rather than a blocker.

## Left for Umesh

Nothing gates on a human here — no criterion was weakened, no safety/data invariant touched, and
the constants question already resolved to "ship as an honest, disclosed guess, don't rubber-stamp
a new number." The one open item is the ~44s worst-case, filed as `ISS-at335-followup-tolerance-scope`
for a future unit to pick up; it's a latency/cost tradeoff, not a decision requiring Umesh's
judgement on ownership, scope, or product direction.
