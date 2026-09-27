# Manifest — at335-modal-determinism

**Contract:** `qa/contracts/explore.md` X3 (structural screen identity), X4 (the replay chain, and
now its tolerance, are both bounded)
**Goal task:** none named directly (bug-fix unit against a filed issue, same shape as
at265-gemini-schema-allowlist)
**Date:** 2026-09-27
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-335 (high, open → fixed here, pending checker)
**Executor:** maker build subagent (worktree `D:/autoTesting/.claude/worktrees/agent-a8a65680aeeabd41d`, branch `wave/at335-determinism-salvage`)
**Executor rationale:** salvage of work left uncommitted in a since-merged worktree
(`wave/at335-modal-determinism`, already fully in master; only its uncommitted diff was new) —
dispatched to a fresh build subagent so the salvaged fix gets independent critical review before
any checker sees it, not carried forward on trust from the session that wrote it.

## Provenance — this is a salvage, and the salvaged fix was NOT taken on trust

Rescued from a worktree one `git worktree remove` away from deletion: `explore_return.patch`
(33-line diff against `src/autotester/stages/explore_return.py`) and
`test_explore_return_determinism.py` (untracked, never run under the pair). The patch applied
cleanly against master's current `explore_return.py` (`git apply --check` clean, no conflict).

I was asked to judge the salvaged fix critically, not adopt it verbatim, against four named
questions. Findings:

**1. Does the bounded poll preserve X4 (a crawl must always terminate)?**
Yes, but the per-action overshoot ceiling grows, and that growth is real and disclosed, not
hand-waved. `return_to` recurses to `MAX_REPLAY_DEPTH = 3` (depths 0..3, 4 levels). Tracing the
actual call structure in `explore_return.py`:
- Every `return_to(depth=d)` call performs `go_back` and `goto`, each followed by
  `settle(timeout_ms=rt.bounds.settle_ms=2500)` then `_matches(...)` (bounded at
  `RETURN_SETTLE_TOLERANCE_MS=1500`) — 2 rung-instances per depth, 4000ms ceiling each.
- If both fail, `_replay_discovery(depth=d)` either bails immediately at `d==MAX_REPLAY_DEPTH`
  (no further recursion, no click) or recurses into `return_to(depth=d+1)` and then, on return,
  performs one more `click + settle(2500) + _matches(1500)` rung (4000ms ceiling).
- This gives **11 total rung-instances** in the absolute worst case (go_back+goto at each of
  4 depths = 8, plus click+settle+matches at each of the 3 depths that recurse = 3): depth 3
  contributes only its own go_back/goto (no click, since `_replay_discovery` bails before
  recursing further).
- `T(3) = 2×4000 = 8000ms`; `T(d) = T(d+1) + 3×4000` for `d<3` ⇒ `T(2)=20000`, `T(1)=32000`,
  `T(0)=44000ms`. **Worst-case added wall-clock for one pathological `return_to` call: ~44s**,
  split as **~27.5s pre-existing** (11 × the 2500ms `settle_ms` ceiling, unaffected by this fix)
  and **~16.5s newly added** (11 × the 1500ms tolerance ceiling this fix introduces).
- X4 is still satisfied: `explore.py`'s `stop_reason()` is checked before every node and before
  every action, never inside `return_to` itself, so the crawl still terminates within
  `wall_clock_s` plus one action's overshoot — that overshoot ceiling has simply grown from
  ~27.5s to ~44s. This is a genuine cost of the fix, not a correctness defect, and it is stated
  here rather than only in a code comment.

**2. Is 1500ms/0.15s justified by evidence, or a guess?**
Downgraded rather than shipped as-is. The salvaged docstring's "measured live" framing bundled
two different claims: the 1-in-14 rate (which IS real — `qa/issues.jsonl` AT-335 itself, backed
by `qa/manifests/at335-flake-probe-harness.md`'s independent N=41 probe, AT-389's honest caveat
on that estimate's own wide interval) and the 1500ms/0.15s constants (which are NOT — no evidence
file records the real distribution of re-render lag past `settle()`'s grace). I reworded the
docstring in `explore_return.py` (kept in this commit) to say plainly: **"The 1500ms/0.15s values
below are NOT independently measured... a conservative, bounded guess at a threshold comfortably
above typical lag, not a proven-minimal one; tightening or loosening it later needs its own
measurement."** I did not ship a comment asserting a measurement nobody can find.

**3. Does every rung need the tolerance, or only some — does it mask a genuinely-wrong-screen
case as merely slow?**
Empirically checked against the repo's own pre-existing regression test for exactly this failure
mode, run against the FIXED code in the bound worktree (not a throwaway copy — this is the real
tree with the real fix applied):
```
uv run pytest tests/test_explore_modal.py::test_a_replay_that_lands_elsewhere_is_a_failure_not_a_near_miss -v
tests\test_explore_modal.py .                                            [100%]
============================= 1 passed in 25.85s ==============================
```
A genuinely-wrong-screen replay still correctly reports failure with the tolerance in place. I
also built a second, purpose-built test (`test_return_to_still_fails_when_the_lag_exceeds_the_bound`,
below) that proves the SAME thing more directly: a lag longer than `RETURN_SETTLE_TOLERANCE_MS`
still correctly fails to reach the target screen — the bound is a ceiling, not an unconditional
"assume success." The cost of applying the tolerance uniformly to all three rungs is **latency
only** (a genuinely-lost screen now takes up to 1500ms longer per rung to be correctly declared
lost), not a correctness regression.

**4. Does the salvaged test actually test the poll, or only that the function still returns
True — the AT-548/549/550 vacuous-guard failure mode?**
**Yes, this gap was real, and I closed it rather than disclosing it as unfixed.** Falsified in an
isolated throwaway copy (`git write-tree` + `git archive` of the staged index — never `tar` on
the working tree, so no stale `.pyc`/`__pycache__` path-baking) built at
`C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/aaf84a03-9a89-49ef-921f-f7d28b7dd443/scratchpad/at335-check-copy2`,
never inside the bound worktree:

- Mutating `_matches` to unconditionally `return True`: the ORIGINAL salvaged test
  (`test_return_to_tolerates_a_replayed_dismiss_that_lands_late`) **still passed** — it only
  proves a success path exists, not that the fingerprint is actually polled. This is exactly the
  filed failure shape (AT-548/549/550).
- I added a second test, `test_return_to_still_fails_when_the_lag_exceeds_the_bound`, configuring
  the fake page's replayed-dismiss lag to `RETURN_SETTLE_TOLERANCE_MS/1000 + 2.0` seconds (2s past
  the bound) and asserting `/reports.html` is NOT reached. Under the same unconditional-`True`
  mutation this new test **fails** (RED) — closing the gap. See Capability coverage below for the
  full falsification matrix (correct impl / single-check mutation / always-True mutation × both
  tests).
- The bound worktree was left untouched by this falsification work (verified via `git status
  --short` immediately after: only the two intended staged files, `M
  src/autotester/stages/explore_return.py` and `A tests/test_explore_return_determinism.py`, no
  mutation leaked back).

**Verdict: adopted with rework**, not adopted verbatim and not rejected. Kept: the `_matches`
poll mechanism, its three call sites, the bounded ceiling. Changed: the docstring's evidence
claim (downgraded to what can actually be supported), and the test file (added a second test that
closes the vacuous-guard gap the salvaged test alone left open).

## What changed
- `src/autotester/stages/explore_return.py` (129 → 158 lines, well under the 300-line cap):
  - `import time` (new); `RETURN_SETTLE_TOLERANCE_MS = 1500` and `_RETURN_POLL_S = 0.15` (new
    module constants); `_matches(rt, node, timeout_ms=RETURN_SETTLE_TOLERANCE_MS)` (new function,
    ~13 lines): polls `_fingerprint(rt, node.depth) == node.id` every `_RETURN_POLL_S` up to the
    bounded deadline, returning immediately on the common case (already matches).
  - The three call sites that used to check `_fingerprint(...) == node.id` exactly once (after
    `go_back`+settle, after `goto`+settle, inside `_replay_discovery` after the replay click+settle)
    now call `_matches(rt, node)` instead.
  - Docstring on `RETURN_SETTLE_TOLERANCE_MS` reworded (my one intentional change beyond the raw
    salvaged patch) to separate the measured 1-in-14 rate from the unmeasured 1500ms/0.15s
    constants — see question 2 above for the exact wording.
- `tests/test_explore_return_determinism.py` (new file, 197 lines):
  - `_SlowModalPage`/`_Locator` fake-page fixture (from the salvage) — a real `BrowserSession`
    wired to a fake `page`, whose REPLAYED dismiss (only) lags by a configurable
    `replay_delay_s`; the first (ordinary-exploration) dismiss stays instant, isolating AT-335's
    mechanism from `try_action`'s own edge classification.
  - `_SlowModalPage.__init__` now takes `replay_delay_s: float = DISMISS_DELAY_S` (was hardcoded
    to the module constant) and `_session()` threads it through — my addition, needed to build the
    second test below without duplicating the fixture.
  - `test_return_to_tolerates_a_replayed_dismiss_that_lands_late` (from the salvage, unchanged):
    a lag of `DISMISS_DELAY_S=0.35s` (inside the 1.5s bound) is tolerated; the crawl reaches
    `/reports.html`.
  - `test_return_to_still_fails_when_the_lag_exceeds_the_bound` (new, mine): a lag of
    `RETURN_SETTLE_TOLERANCE_MS/1000 + 2.0 = 3.5s` (outside the bound) is NOT tolerated; the crawl
    must not reach `/reports.html`. This is the row that closes the vacuous-guard gap in question 4.

## How to verify
- `uv run pytest` (own command, no CLI `-q` — AT-503)
- `uv run ruff check src tests scripts`
- `uv run autotester doctor`
- Targeted: `uv run pytest tests/test_explore_return_determinism.py -v`
- Flake evidence: `uv run python scripts/flake_probe.py "tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal" --runs 20 --out .work/at335-flake-probe-post-fix.json`

## Actual outputs

### Targeted determinism tests (bound worktree, fixed code)
```
uv run pytest tests/test_explore_return_determinism.py -v
tests\test_explore_return_determinism.py ..                              [100%]
============================= 2 passed in 14.75s ==============================
```

### Pre-existing regression, fixed code, confirming no correctness regression (question 3)
```
uv run pytest tests/test_explore_modal.py::test_a_replay_that_lands_elsewhere_is_a_failure_not_a_near_miss -v
tests\test_explore_modal.py .                                            [100%]
============================= 1 passed in 25.85s ==============================
```

### Lint and design rules
```
uv run ruff check src tests scripts
All checks passed!

uv run autotester doctor
doctor: clean
```

### Full suite
```
uv run pytest
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
3 failed, 2034 passed, 6 skipped, 14 xfailed, 15 warnings in 1753.97s (0:29:13)
```
**All three failures are pre-existing and unrelated to this unit** — this unit's staged diff
touches exactly two files (`src/autotester/stages/explore_return.py`,
`tests/test_explore_return_determinism.py`), neither of which either failure's test exercises:
- `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` is the named, filed AT-627
  (low, open, load-sensitive) — expected, not chargeable here.
- The two `test_goal_done_checks.py` failures both assert `.goal/goal.json`'s task count against
  a **hardcoded `70`** (`assert progress["total"] == len(data["tasks"]) == 70`); the real file in
  this worktree holds **81** tasks (verified directly: `python -c "import json;
  d=json.load(open('.goal/goal.json')); print(len(d['tasks']), d['progress']['total'])"` →
  `81 81` — internally consistent, just grown past the test's stale literal). `git status --short
  .goal/goal.json` shows no modification by this unit; the worktree's copy is exactly what
  commit `72513124` (this branch's parent) already had. This is the SAME drift already filed
  **today** as **AT-642** (medium, open, found by a checker-sweep dated 2026-09-27: "target.md's
  progress line reads '47/70' while .goal/goal.json holds 81 tasks... roadmap-overstates-completion")
  — concurrent maker-checker traffic on other units grew the task list from 70 to 81 without the
  test's literal being updated in lockstep. Not this unit's regression to own or fix.

### Real-world flake evidence (flake_probe.py, N=20, patched code)
```
uv run python scripts/flake_probe.py "tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal" --runs 20 --out .work/at335-flake-probe-post-fix.json
tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal: 0 failure(s) in 20 run(s)
  zero failures bounds the true rate at 13.9% (95% confidence) -- NOT at zero
  the suspected 7.1% rate is inside that bound, so this probe does NOT exclude it; 41 runs are needed for a 95% chance of seeing it
report: .work/at335-flake-probe-post-fix.json
```
Per-run timing (`.work/at335-flake-probe-post-fix.json`, real Chromium crawls): 63-106s each,
~30 minutes total for N=20.

**Honest statistical read, not rounded up:** this alone does NOT prove the fix works — 20 clean
runs only bounds the true failure rate at 13.9% (95% confidence), which does not exclude the
suspected 7.1% rate. I deliberately did **not** extend this to the full N=41 the harness computes
as necessary, for a stated reason rather than an unstated shortcut: `qa/manifests/at335-flake-probe-harness.md`
already ran the full N=41 against the **ORIGINAL, unfixed** code and also got 0 failures — the
flake's own filed history is "13 green, 1 red" out of the original ~14 attempts, i.e. even a
statistically-adequate sample on the KNOWN-BUGGY code could not reliably reproduce it. Spending
another ~70 minutes running N=41 on the fixed code would not yield a meaningfully different
statistical conclusion than N=20 already gives, because the rate is too rare and too irreproducible
on-demand for this harness to be the decisive evidence either way. **The decisive evidence for
this unit is the synthetic determinism test** (`tests/test_explore_return_determinism.py`), which
reproduces AT-335's exact suspected mechanism on demand, every time, and is proven (via mutation
falsification above) to actually exercise the fix rather than a vacuous success path. The real
N=20 clean run is offered as corroboration that the fix introduces no new visible instability in
the real crawl, not as statistical proof the flake is gone.

## Capability coverage

Falsification performed entirely in a throwaway copy outside the bound worktree
(`C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/aaf84a03-9a89-49ef-921f-f7d28b7dd443/scratchpad/at335-check-copy2`),
built via `git write-tree` (staged index) + `git archive <tree-sha>` + `tar -x` — never `tar`
directly on the working tree, and never a mutation applied to the bound worktree. Bound worktree
verified intact afterwards (`git status --short` showed only the two intended staged files).

| capability | covering test | falsifying edit | observed |
|---|---|---|---|
| a rung whose fingerprint hasn't caught up yet is tolerated within the bound | `test_return_to_tolerates_a_replayed_dismiss_that_lands_late` | revert `_matches` to a single check (`return _fingerprint(rt, node.depth) == node.id`, no poll — the pre-fix shape) | correct impl (bound worktree): GREEN (`2 passed in 14.75s`). Mutated copy: **RED** — `AssertionError: never reached the page behind the modal`, `assert '/reports.html' in {'/'}` |
| a lag genuinely PAST the bound is still correctly declared a failure, not falsely tolerated forever | `test_return_to_still_fails_when_the_lag_exceeds_the_bound` (new, mine) | mutate `_matches` to unconditionally `return True` (the vacuous-guard shape AT-548/549/550 warned about) | correct impl: GREEN. Mutated copy: **RED** — `assert '/reports.html' not in {'/', '/reports.html'}` fails because the always-True mutation lets the crawl "succeed" despite the lag |
| the same always-True mutation does NOT redden the first test alone | `test_return_to_tolerates_a_replayed_dismiss_that_lands_late` under the always-True mutation | (same mutation as above) | **still PASSES** (confirmed in the same run as the row above: `tests\test_explore_return_determinism.py .F [100%]` — `1 failed, 1 passed in 1.39s`, the `.` is this test) — this is the vacuous-guard gap itself, made visible on purpose: the first test cannot detect this mutation; only the second one can. Documented here rather than hidden, and closed by adding the second test rather than left as a known gap |
| a genuinely-wrong-screen replay (not just a slow one) still correctly fails with the tolerance in place | pre-existing `tests/test_explore_modal.py::test_a_replay_that_lands_elsewhere_is_a_failure_not_a_near_miss` | none applied — run as-is against the fixed code (this IS the falsifying condition: a screen the tolerance must not paper over) | fixed code: **PASSED** (`1 passed in 25.85s`) — the uniform tolerance does not mask a genuinely-wrong screen as merely slow (cost is latency only, per question 3) |

Full matrix, for the honest record (impl × mutation × test):

| impl / mutation | test 1 (tolerate late lag) | test 2 (fail past-bound lag) |
|---|---|---|
| correct (bound worktree) | PASS | PASS |
| single-check, no poll (pre-fix) | **FAIL** (proves test 1 needs the poll) | PASS (unaffected — still correctly fails past-bound lag even with no poll, since no poll ever waits) |
| unconditional `_matches() -> True` | PASS (the vacuous-guard gap — test 1 alone cannot see this mutation) | **FAIL** (proves test 2 closes the gap) |

## Live browser evidence
Not UI-touching — no surface changed. `src/autotester/stages/explore_return.py` and its test are
backend crawl-logic only; no UI screen, route or component was added or modified. Persona walk:
skip (backend-only, no UI surface touched). `qa/adapter.json`'s `verify.commands` declares no
`audience` field, consistent with this being outside its scope.

## Gaps stated, not hidden
- **Full suite: 3 failed, 2034 passed, 6 skipped, 14 xfailed (1753.97s).** All three failures are
  pre-existing and outside this unit's diff (AT-627 + the two `test_goal_done_checks.py` failures
  now also traced to today's already-open AT-642 governance-drift finding) — see Actual outputs
  above for the full trace. Flagged here rather than silently excluded: a checker should
  independently confirm the `.goal/goal.json` count-drift explanation rather than take it on
  trust, since two unexpected failures beyond the one named pre-condition (AT-627) is a bigger
  surface than the brief anticipated.
- **flake_probe N=20 came back clean (0/20)**, which does NOT statistically exclude the suspected
  7.1% rate (needs N=41 for that) — and, per the reasoning above, N=41 would not meaningfully
  change this picture either, since the harness's own prior N=41 run against the UNFIXED code was
  also clean. The real-world flake is not reliably reproducible on demand at any feasible N with
  this harness; the synthetic determinism test is this unit's actual proof, not the live probe.
  A checker should weigh this honestly rather than read "0 failures" as "flake confirmed fixed."
- **The 1500ms/0.15s constants remain an unmeasured, conservative guess**, not a proven-minimal
  threshold (question 2). Tightening or loosening them later needs its own measurement — this is
  now stated explicitly in the code, not asserted as settled.
- **Worst-case added latency per pathological action is ~16.5s (44s combined with the
  pre-existing settle chain)** — a real, disclosed cost of this fix, not zero. X4's termination
  guarantee is preserved (bound-checking happens before every node/action, never inside
  `return_to`), but the per-action overshoot ceiling has grown roughly 60%. If this cost proves
  unacceptable in practice, the fix should be revisited to scope the tolerance more narrowly
  (e.g., skip it on the `MAX_REPLAY_DEPTH` rung, which cannot recover anyway) rather than assumed
  fine because the crawl still terminates.
- No live product traffic or network calls beyond the local fake-page fixture and the real local
  Chromium crawl already exercised by `test_explore_modal.py`'s existing fixtures.

## Status: ready-for-check
