# Manifest — d063-grant-budget (account-derived LIVE_CASE grant + one aggregate run budget)

Contract: qa/contracts/consent.md CN11 (adopted by the checker in the main tree, authorized by D-063); CN1-CN10 (CN10: a bound never means unlimited); qa/contracts/parallel-run.md PR7; core-invariants C5/C12
Authority: D-063 (docs/DECISIONS.md, main tree) — Approved-by: Umesh (AT-674 Answer, 2026-10-06)
Goal task: T-122 prerequisite (the USER-account end-to-end run is a separate later step)
Policy-Version: proportional-verification/2026-10-06.6
Fix cycle: 0 of 2
Phase: READY
Tier: L — security/auth (approval grant + signing-key creation)
Dual check: required — approval grant and key creation are security/auth
Persona walk: skip (backend-only: no screen, navigation path or user-facing flow changed)
Issues addressed: AT-674; AT-570 (grant path); AT-651 credential-scope follow-through
Executor: claude-sonnet-subagent (branch assembly of the uncommitted master work; the code was authored earlier by the root and its build workers)
Base: stacked on wave/pathlynks-exact-host tip 41ce907d (itself on bd2fe8f4)
Branch: wave/d063-grant-budget — commits f7adb2b9 (grant), 20594b23 (budget + fill receipt), 38f0f9bf (test setup), plus this manifest

## Dependency on files that are NOT on this branch

`docs/DECISIONS.md` (D-061..D-064 entries) and `qa/contracts/consent.md` (CN11) are still
uncommitted in the main tree. On this branch `autotester doctor` therefore reports the D-063
citations (here and in pathlynks-exact-host.md) as `decision-citation-dangling`. Land those two
files first (checker / append_decision.ps1 own them); this branch does not touch them.

## What changed

Commit f7adb2b9 — account-derived grant:
- src/autotester/core/consent.py — validate_account_scope, validate_account_bounds, prepare_account_live_case (new signed row, verified through require_approval).
- src/autotester/core/ids.py — ensure_approval_key (explicit, create-if-absent, refuses when signed history lost its key).
- src/autotester/ui/env_editor.py — create_env_value_if_absent (serialized, owner-only atomic write).
- src/autotester/cli_crawl.py — approve: positive finite default bounds, nonpositive refused.
- src/autotester/ui/routes_runs.py — _require_declared_values (only referenced keys gate), _require_live_case_approval (preflight before run id/dir/browser), trigger_run.
- tests: test_consent.py, test_core.py, test_ui_env_editor.py.

Commit 20594b23 — aggregate budget + fill receipt:
- src/autotester/stages/run_budget.py (RunBudgetExceeded, stop_reason, check/check_start/remaining_ms/matches), stages/parallel_run.py, stages/execute.py, ui/run_execution.py, ui/routes_runs.py::_execute_with_trace (one RunBudget; a stopped run is a failed EXECUTE span naming the brake).
- src/autotester/browser/session.py, assertions.py, evidence.py, video.py — budget-bounded timeouts; fill receipt (before/after, secret values never read).
- src/autotester/core/trace.py, schema/trace.py — optional StageSpan.error.
- tests: test_parallel_run_approval, test_browser_actions, test_browser_settle, test_execute_assertions, test_run_trace, test_ui_runs_parallel_crash_recovery, test_ui_runs_parallel_trace, test_ui_runs_serial_entry_screenshot_namespace.

Commit 38f0f9bf — setup-only test change (not a protected-oracle change; no assertion edited):
- tests/test_ui_runs_serial_entry_mix_live.py — `grant_live_case_approval(store, project="rd", target=project.base_url)` after the project is saved, like the sibling run tests. Without it the live test got 403 from the AT-570 gate.

## Acceptance (each maps to a CN11 clause)

1. Grant identity/scope: a new grant derives only from declared, provisioned, in-scope credentials for the exact project/target/cases; an out-of-scope key, wrong project or undeclared key refuses.
2. Selected credentials only: keys actually referenced by the requested case set gate the run; unused role keys do not.
3. Positive finite brakes: nonpositive or nonfinite actions, probes, wall clock refuse (grant path and CLI).
4. Key preparation: explicit, create-if-absent, preserves existing key/overrides/other entries, refuses without writing when signed history lost its key.
5. One aggregate RunBudget across serial, entry and parallel; a shared budget must match the approval; every brake is named.
6. A stopped/truncated run is reported failed with the named brake, never as completed E2E.
7. The fill receipt records before/after values redacted; secret values are never read.

## Verification scope

Policy-Version: proportional-verification/2026-10-06.6
Tier: L (security/auth). Base / checked state: tip of wave/d063-grant-budget at the manifest commit (see git log).
Affected tests / full-suite trigger: affected files only; the builder ran no full suite. Full suite, two blind checkers (Dual check) and senior review are mandatory before PASS.
Metrics: start=2026-10-07 end=2026-10-07 wall_min=unavailable agent_min=unavailable blocked_min=0 suite_runs=0 repeat_runs=0 mutations=9 cycle=0 resumes=0 tokens=unavailable policy=proportional-verification/2026-10-06.6

## How to verify (commands + expected)

- `uv run ruff check src tests scripts` -> All checks passed
- `uv run pytest tests/test_consent.py tests/test_core.py tests/test_ui_env_editor.py` -> 60 passed, 1 skipped
- `uv run pytest tests/test_parallel_run_approval.py tests/test_browser_actions.py tests/test_browser_settle.py tests/test_execute_assertions.py tests/test_run_trace.py tests/test_ui_runs_parallel_crash_recovery.py tests/test_ui_runs_parallel_trace.py tests/test_ui_runs_serial_entry_screenshot_namespace.py tests/test_ui_runs_live_case_approval.py tests/test_ui_runs.py tests/test_ui_runs_serial_entry_order.py tests/test_ui_runs_serial_resilience.py` -> all pass
- `uv run pytest tests/test_ui_runs_serial_entry_mix_live.py` -> NOTE: the test hard-codes `RAM_FLOOR_MB = 3584` and ignores the env var, so it SKIPs under low RAM (2767 MB free here). To run it, set that constant to 0.0 in a throwaway copy.
- `uv run autotester doctor` -> see Actual outputs.

## Actual outputs (maker's own run, 2026-10-07, worktree D:/autoTesting/.worktrees/d063-grant-budget)

- ruff at tip: `All checks passed!`
- commit 1 state: `60 passed, 1 skipped, 1 warning in 2.93s`.
- commit 2 state, 12 run/browser files plus mix_live: `110 passed, 1 failed in 6.53s`; the one failure was tests/test_ui_runs_serial_entry_mix_live.py (403 "no approval exists", the AT-570 gate), fixed by commit 3.
- mix_live on a throwaway copy with the floor at 0.0 and real Chromium: `1 passed, 1 warning in 14.84s`.
- doctor at tip (manifest included): 16 violations: ledger-row-missing T-171; stale-generated docs/MAP.md; stale-generated docs/SNAPSHOT.md; 13 decision-citation-dangling (D-061/D-063/D-064). The base bd2fe8f4 plus exact-host already shows 9 of them (T-171, MAP/SNAPSHOT, 6 dangling incl. D-063 in pathlynks-exact-host.md); this manifest adds 7 dangling citations of D-061/D-063/D-064. None is caused by product code on this branch: the DECISIONS.md entries and regenerated MAP/SNAPSHOT/FEATURES are uncommitted in the main tree and the dangling set clears when DECISIONS.md lands. Root-clutter (at113-fixture-*, pytest-of-unknown) is a main-tree-only pre-existing condition and does not appear in a fresh worktree.

## Capability coverage (each new claim -> its isolating falsification)

Method: `git archive` of the branch tip into a throwaway copy outside the tree, one edit at a
time, original restored byte-identical after each, runner re-run before/after/restored. Neither
D:/autoTesting nor the worktree was mutated.

| Criterion | capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|---|
| 1 | grant refuses a credential outside its domain scope | tests/test_consent.py::test_account_grant_is_new_exact_and_bounded[scope] | core/consent.py::validate_account_scope: replace the `_host_matches(...)` clause with `False` | before `36 passed in 0.33s`; after `FAILED ...test_account_grant_is_new_exact_and_bounded[scope]`, `1 failed, 35 passed in 0.55s`; restored `36 passed in 0.31s` |
| 3 | zero/negative actions refused | same test, `[actions]` | core/consent.py::validate_account_bounds: drop `actions <= 0 or` | before `36 passed in 0.15s`; after `FAILED ...[actions]`, `1 failed, 35 passed in 0.34s`; restored `36 passed in 0.16s` |
| 4 | lost verification key refuses instead of regenerating | tests/test_core.py::test_explicit_approval_key_preparation[lost] | core/ids.py::ensure_approval_key: `if any(row.signature ...)` -> `if False` | before `14 passed in 1.72s`; after `FAILED ...[new] ...[lost] ...[malformed]`, `3 failed, 11 passed in 1.75s`; restored `14 passed in 1.35s` |
| 5 | shared budget must match the approval | tests/test_parallel_run_approval.py::test_explicit_budget_has_no_reservation_and_must_match_approval | stages/parallel_run.py::run_cases: `if budget is not None and not budget.matches(approval)` -> `if False` | before `22 passed in 0.23s`; after `FAILED ...must_match_approval`, `1 failed, 21 passed in 0.32s`; restored `22 passed in 0.17s` |
| 5 | max_actions brake enforced | tests/test_parallel_run_approval.py::test_budget_spends_cannot_replenish_or_bypass | stages/run_budget.py::_consume: `if actions_after > approval.max_actions` -> `if False` | before `22 passed in 0.13s`; after `8 failed, 14 passed in 1.21s` (first `FAILED ...[nan-actions]`); restored `22 passed in 0.12s` |
| 7 | fill receipt never reads secret values | tests/test_browser_actions.py::test_fill_receipt_observes_values_but_never_reads_secrets | browser/evidence.py::_field_sample: `if secret or locator in ...secret_locators` -> `if False` | before `24 passed in 0.27s`; after `FAILED ...[placeholder] ...[previous]`, `2 failed, 22 passed in 0.45s`; restored `24 passed in 0.23s` |
| 2 | only referenced keys gate a run | tests/test_ui_runs_parallel_trace.py::test_a_declared_fake_secret_never_appears_raw_in_the_trace | ui/routes_runs.py::_require_declared_values: `if cases is None` -> `if True` (all declared keys gate) | before `29 passed, 1 warning in 4.39s` (6 UI run files); after `2 failed, 27 passed` (`...never_appears_raw_in_the_trace[False]`, `[True]`); restored `29 passed in 3.08s` |
| 6 | a stopped run is a failed EXECUTE span | tests/test_ui_runs_parallel_trace.py::test_a_real_run_writes_a_trace_with_at_least_one_span | ui/routes_runs.py::_execute_with_trace: `status="failed" if budget.stop_reason else "done"` -> `status="done"` | before `29 passed in 3.31s`; after `2 failed, 27 passed` (`...at_least_one_span[True-1]`, `[True-2]`); restored `29 passed in 3.27s` |
| 5 | serial path takes the shared budget | tests/test_ui_runs_serial_resilience.py | ui/routes_runs.py::_execute_with_trace: drop `budget=budget` from the serial call | before `29 passed`; after `12 failed, 17 passed` (first `test_a_grader_crash_for_one_of_three_serial_cases...`); restored `29 passed in 3.20s`. Caveat: this fails because the helper requires the budget, so it proves the wiring is required, not a numeric brake |

Gaps stated, not hidden: no isolated falsification for criterion 3's CLI default path, for
`create_env_value_if_absent` concurrency (covered by the cross-process test in test_core.py but
not mutated here), or the wall-clock brake in a real browser. These go on the checker's mutation list.

## Live browser evidence

SKIP — no screen, template or navigation path changed (backend run gate + budget). The route's
real-Chromium fixture test passed once on a throwaway copy with the RAM floor zeroed: `1 passed,
1 warning in 14.84s`. No live Pathlynks account run was performed; that is the later T-122
USER-account step and needs provisioned credentials.

## Status: ready-for-check
