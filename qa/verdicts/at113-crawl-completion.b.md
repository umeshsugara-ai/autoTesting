# AT-113 independent second checker — cycle 2 IN PROGRESS

Cycle checked: 2
Bound root: D:/autoTesting
Source: f9052150f4cd2af19a5ed3888173e910fa1220ed
Baseline: c5596a0a
Date: 2026-09-30

This is partial progress, not a PASS or final verdict. Current state: own full pytest
is TERMINAL under actual session55836 (exit 1: 15 failed, 2222 passed, 5 skipped,
14 xfailed, 15 warnings in 1659.94s). Own headed Mode D remains pending reviewed
instrument runtime; selected baseline attribution is RUNNING under session74963.
Earlier statements about the first checker owning the lane are historical and superseded
by the explicit lane release and 55836 launch recorded below.
No master merge, public push or whole T-165 closure is certified.

Current terminal gate evidence: `.work/at113-check-b/full-pytest.log`. Exact failures
are two goal registration/done-check cases, four `test_mc_sessionstart_loop_status`
cases, six `test_mc_sessionstart_unclosed` cases, two hung-run mutation judgement
cases, and `test_ui_runs_serial_entry_mix_live::test_a_serial_run_mixing_an_entry_case_with_ordinary_cases_does_not_500`.
The last reached HTTP 403 with a missing live_case approval; this is not a browser
500 nor a passing serial workflow. Independent c559 attribution is pending.
Owned residual PID creation identities were freshly checked; 37772, 51144 and
37484 were stopped, others had exited; readback of all ten recorded PIDs was empty.
Probe3 found cleanup PID-reuse and exact warning-tone assertion gaps. These are
being fixed and re-reviewed before runtime. No final PASS is implied.

Independent evidence so far:

- Exact source HEAD confirmed and own git archive made at `.work/at113-check-b/source`.
- Ruff: exit 0, `All checks passed!`.
- Doctor in submitted worktree: exit 1, untracked `debug.log` root clutter and T-171
  missing ledger row. Own clean archive doctor: exit 1, only T-171 missing ledger row.
- Pure terminal/display subset: 22 passed, 7 deselected.
- Independent synthetic contract oracle: 25 asserted distinctions, exit 0.
- Own oracle harness: three named assertion kills, unique anchors asserted, on-disk
  mutation asserted, SHA256 originals/mutations recorded, exact restore and restored
  green per case. `.work/at113-check-b/mutation-results.json` and associated logs.
- Fake crawl/persona/presentation suite: 39 passed, one external Starlette deprecation.
- Named-test caller harness initial attempt stopped safely on unmatched detail anchor;
  first workbook-reason mutation failed its named workbook assertion and was restored
  green. Historical60507 is an anchor failure, not a completed kill proof.
  Corrected harness46569 is terminal exit0: four caller mutations killed by their exact
  named test assertions; each applied unique anchor, SHA256 change and byte restore
  asserted, baseline/restored39 PASS. `.work/at113-check-b/test-mutation-results.json`.
- Own clean c5596a0a archive goal-control checks: 2 failed, 6 passed. Independently
  reproduced `test_revised_goal_contract_is_registered` (81 total versus 82 tasks) and
  `test_no_done_task_has_a_done_check_naming_a_file_that_does_not_exist`
  (T-171's missing tests/test_permission_surface.py). These do not yet discharge
  full-suite attribution: remaining failures must be reproduced and traced independently.
- Own headed browser instrument prepared and syntax checked, not launched. It includes
  an actual local dialog-storm crawl with independent sibling plus report interactions.

No maker probe, maker screenshot, primary verdict or other checker instrument was read.

Additional independently completed checks:

- Same3419 terminal exit0: six additional status/caller mutations killed by their named
  JUnit assertion IDs (actual named bound, login precedence, failed-observation qualifier,
  real-node frontier caller, deferred drain ordering, CLI displayed reason). Asserted
  baseline48 PASS; each single unique anchor applied and bytes changed; each restored
  baseline48 PASS; no collection-only kill. Own status-mutation-results.json and13 logs.
- Total independent mutation cases completed:13 (3 contract-oracle +4 presentation/persona
  named-test caller +6 status/caller). Each has an asserted green baseline and exact restore.
- Own c559 clean-archive doctor exit1: T-171 missing ledger, stale snapshot and danglingD061.
  Exactf905 clean archive retains only T-171 missing ledger. The snapshot diff removesD061.
- Goal/ledger files and two failing goal-test blobs are unchanged between baseline and source;
  full-suite failure attribution remains pending independently, rather than broadly waived.
- Final full-archive comparison detected newline-only divergence left by the initial exploratory
  apply_patch restore in own throwaway explore_status.py. Per-case harness byte restores were
  exact to their captured originals; whole-commit identity was therefore separately corrected
  by re-extracting the immutable source ZIP. Final1765 tracked archive files are byte-identical;
  independent25-assertion oracle rerun passed afterward. The submitted source was never edited.
  Historical13 mutation kills are not exact-commit proofs and are not retroactively upgraded
  by that restore. Exact-source rerun of all13 is required and remains pending.

Exact-source rerun completed subsequently (supersedes only the pending statement above):

- Fresh3 oracle kills and4 named-test caller kills re-ran from the byte-exact archive.
  Current artifacts retained separately at exact-oracle-run and exact-caller-run.
- Fresh6 status/caller kills ran under session78809, terminal exit0. Startup and end
  both asserted all1765 archived tracked files byte-identical to submitted f905 ZIP.
  Baseline and each restored run48 PASS; each mutation killed its exact named JUnit
  assertion (no collection-only failure); original CRLF preserved for single-hunk edits.
  Artifacts: `.work/at113-check-b/exact-status-run/`.
- Old oracle/caller logs were overwritten during the initial rerun; their historical
  bytes were not preserved. They are excluded from final exact-source evidence.
- Exact completed independent count is13 new kills, not a carryover of historical13.
  Full suite and actual headed Mode D remain pending. No final PASS.

Heavy lane released by orchestrator after first checker's terminal cleanup. Own unpiped
full suite launched with actual session55836 against immutable f905 clean archive at
`.work/at113-check-b/source`, installed root venv, `uv --active --no-sync`, isolated
PYTHONPATH/src and unique pytest temp/cache. Full output `.work/at113-check-b/full-pytest.log`.
No terminal result yet; own headed Mode D follows its terminal and owned cleanup.
