# AT-113 independent second checker — cycle 2 FAIL

Cycle checked: 2
Bound root: D:/autoTesting
Source: f9052150f4cd2af19a5ed3888173e910fa1220ed
Baseline: c5596a0a
Date: 2026-09-30

Current final verdict: FAIL, because applicable X4's max_depth runtime requirement
is not met. The remaining text records independent verification and preserved history.
Own full pytest
is TERMINAL under actual session55836 (exit 1: 15 failed, 2222 passed, 5 skipped,
14 xfailed, 15 warnings in 1659.94s). Own reviewed headed Mode D runtime is completed;
selected baseline attribution session74963 is terminal.
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

## Final independent assessment (supersedes historical pending statements above)

VERDICT: FAIL
Cycle checked: 2
CRITERIA: X4 fails; the abandonment classification, retained named bounds,
persona unknown classification, legacy presentation and UI/workbook assertions pass.
FAILURES:
- [sev: medium] X4 max_depth=1 does not end the crawl with a named bound. On the
  scripted crawl fixture, /students/1 and /students/2 are depth2 beyond the bound.
  Actual f905 result: completed, frontier empty, 3 screens (/, /students, /settings).
  Required: stopped_bound with max_depth named. Source `_enqueue` drops deeper nodes
  without setting a stop cause; `_bfs` then treats the empty queue as complete.
  Independent c559 reproduction is identical, but that does not satisfy the
  explicitly applicable X4 criterion. This is not an AT-113 abandonment regression;
  it is an uncovered existing contract gap, not waived or reclassified as passing.

Reproduce in either own immutable archive with its src/tests in PYTHONPATH,
process-local synthetic AUTOTESTER_APPROVAL_KEY, installed root venv:
`python -c "from pathlib import Path; from crawl_fake import crawl_it; from autotester.schema.crawl import CrawlBounds; p=Path('<unique scratch>'); p.mkdir(exist_ok=True); c,s,page=crawl_it(p,bounds=CrawlBounds(max_depth=1)); print(c.status,c.stop_reason,c.screens,[(n.url_template,n.depth) for n in s.list_nodes(c.id)])"`.
Both source and baseline output: `completed frontier empty 3 [('/', 0), ('/students', 1), ('/settings', 1)]`.
Other own runtime bounds: max_actions=2 -> stopped_bound/max_actions/actions2;
max_screens=2 -> stopped_bound/max_screens/screens2; injected clock ->
stopped_bound/wall_clock_s/actions0. Initial bound harness directory setup failure
was corrected before these results; it is not a product failure or mutation kill.

Own full gate55836 terminal1: 15failed,2222passed,5skipped,14xfailed,15warnings,
1659.94s. Own c559 selected74963 terminal1:13failed,6passed,101.91s; earlier goal
baseline2failed/6passed supplies the remaining two IDs. Exact ten hook failures
are execution-policy refusal: four capture stderr directly, six lose stderr and
fail their no-signal assertion; direct baseline powershell -NoProfile -File hook
independently confirms scripts-disabled UnauthorizedAccess. Both mutation failures
are pytest process-tree-survived kill refusal, not a product assertion kill.
Serial live case independently reaches403/no live_case approval on both sources,
not303 and not500. Relevant causal paths are unchanged in the13-path unit diff.
No whole-suite green claim, resource guard weakening or approved live serial
workflow claim is made. Own residual descendants were creation-time revalidated
and closed; readback empty. Older unrelated mutation PIDs were left untouched.

LIVE-BROWSER: own headed positive31259 terminal0, report at
`qa/evidence/browser-at113-crawl-completion-2026-09-30-checker-b/report.json`.
Own synthetic local actual crawl reached aborted_dialog(/storm.html),
aborted_error(/volatile.html), explored(/sibling.html), aggregateABORTED and both
causes; persona previous/unreached stays unknown, never missing. Seven cases
clicked history→detail→Excel download; exact DOM status, warning/positive classes,
URL-bound node danger/positive classes, workbook Summary status/reason and actual
Screens URL/status pairs asserted. Visible uppercase labels were recorded in own
history_text and independently inspected in own actual-dialog screenshots.
Crawl manifest byte hashes stayed unchanged. Server20016/child42296 original
creation identities closed; port53993 closedtrue. Executed module SHA256
800e5c013a037c942175f8e1b1b35c75c52825a17931d056e6996f025ec1e615;
nonce/source/hash serving identity read twice. Own identity4708 terminal0 confirmed
all1765 tracked source bytes still exact f905 after browser runs.

Runtime limitations and failed instruments preserved honestly: initial negative
setup failed missing synthetic signing key; keyed negative14835 terminal1 reached
intentional malformed identity JSON after actual crawl assertions, then closed
server23572/child15860 and port62209. First positive49254 and diagnostic83927
failed lowercase inner_text oracle because CSS uppercases visible labels, not
because product status was wrong; reports/cleanup retained separately. Final exact
DOM comparison kept unchanged expected statuses, with visible uppercase evidence.
Fresh senior reviewer approved the PID-identity cleanup control-flow and corrected
CSS-sensitive assertion. Local UI page errors0; 42 Google font requests explicitly
stubbed as emptyCSS; external network/rendering path unverified. Actual fixture
crawl contains attributable favicon404 console issue, not blanket zero events.
Synthetic localhost only; no production calls or real credentials. Historical
preservation assertion covers crawl manifests, not every possible artifact.

No source edit, merge, push, issue/task closure or whole T165 certification.
# CHECK B — cycle 3, independent check IN PROGRESS (2026-10-01)

Cycle checked: 3
Bound project: D:/autoTesting
Source reviewed: 085537cd549a6aa0ce522aee3d9a6486f2874c83
Baseline: c5596a0a6175a2ea10f8c7be80f1082e09b11ba8
Status: IN PROGRESS — no PASS or FAIL issued; full pytest and headed runtime remain pending the shared heavy-lane grant.
VERDICT: IN_PROGRESS

Blind scope: contracts plus exact Git diff; no maker manifest, plan, probes, evidence, prior verdict content, or checker A artifacts read. The existing content below is retained as history without being used as evidence.

Owned archive: `.work/check-at113-c3-b-085537/tree`; own mutation copies `mutant-terminal`, `mutant-display`; own baseline archive `baseline`. Root installed venv reused with `uv run --offline --active --no-sync`, isolated `PYTHONPATH`, `UV_CACHE_DIR`, and unique `--basetemp`. Archive content matches all 14 changed Git blobs after explicitly normalizing CRLF to LF. Raw bytes differ due Windows archive line endings; no claim of raw Git-blob equality is made. Source import identity printed from the owned tree; mutant failures also identify their own source paths.

## Independently completed evidence

- Focused command: `uv run --offline --active --no-sync pytest tests/test_explore_blocked.py tests/test_explore_node_recovery.py tests/test_persona_changes.py tests/test_crawl_status_surfaces.py --basetemp=D:/autoTesting/.work/check-at113-c3-b-085537/temp-focused --tb=short`. Handle 94393: exit 0, **79 passed, 1 warning in 35.08s**. Includes both depth-refusal cases and all nine admission/dedup/bound-precedence cases. Initial handle 75796 hit default temporary-directory ACL denial; its environmental setup failures are excluded from product conclusions.
- Own `oracle.py`: exit 0, 20 abandoned/bound/completed combinations; forged-exhaustion refusals and healthy positive controls; public broken/unjudged versus healthy/missing classifications; legacy error-hole controls; model non-mutation and actual persisted fixture bytes unchanged. Fresh independent senior reviewer ran it and approved the revised instrument.
- Exact-source lint: `uv run --offline --active --no-sync ruff check src tests scripts`: exit 0, `All checks passed!`.
- Exact-source doctor: `uv run --offline --active --no-sync autotester doctor`: exit 1, only `ledger-row-missing: T-171 — closed high-value task has no live/updated row`.
- Independent baseline doctor: same command on own baseline archive: exit 1, same T-171 failure plus baseline-only stale SNAPSHOT and dangling D-061 snapshot citation. T-171 is already done/high on baseline. `check_ledger` derives the failure from `.goal/goal.json` and `docs/FEATURES.jsonl`; both inputs and the executing ledger implementation have no baseline-to-source diff. The T-171 cause is independently established outside this unit; no broad baseline waiver is claimed.

## Independent single-hunk mutations, each restored

All mutations act only inside own archive copies, excluding inherited `__pycache__`. Baselines were green; failure attribution uses the named assertions, not exit status alone. The terminal/display mutation anchors were independently asserted unique and the transformed contents compared; restoration of eight relevant files was compared with original source after explicit CRLF normalization.

| Mutated behavior | Green | Named red result | Restored |
|---|---:|---|---:|
| Suppress abandoned terminal branch | 8 | 2 `test_abandoned_visits_are_aborted_unless_an_actual_bound_fired[None-aborted_error/aborted_dialog]`: completed instead of aborted | 8 |
| Suppress legacy error-hole displayed status | 8 | 2 `test_legacy_completion_display_uses_only_recorded_error_holes[0-error/3-error]`: completed instead of aborted | 8 |
| Remove depth-refusal reason assignment | 11 depth cases | 4 `test_depth_admission_dedup_and_recorded_bound_precedence`: missing max_screens/max_actions/wall_clock_s/max_depth reason | 9 admission cases |
| Disable sticky recorded-bound guard | green depth cases | 4 same named precedence assertions: recorded actions/time/depth overwritten or lost | 9 |
| Disable known-node dedup guard | 9 | 1 same named `[True-None-none-None]`: spurious max_depth | 9 |
| Remove abandoned nodes from persona exhaustion predicate | 4 | 2 `test_a_bound_truncated_crawl_never_reports_missing_only_unjudged[aborted_error-True/aborted_dialog-True]`: fabricated `/unreached` deletion | 4 |
| Remove abandoned-node caller frontier predicate | 4 | 2 `test_a_bound_that_fires_mid_node_never_reads_as_an_exhausted_frontier[aborted_error-None/aborted_dialog-None]`: false frontier_exhausted | 4 |
| Drop legacy incomplete displayed reason | 4 | All 4 legacy_error_holes surface cases (history/detail/XLSX/CLI) falsely report frontier empty | 4 |
| Treat any nonempty reason as a fired bound | 2 | Both `test_login_precedence_over_abort_does_not_invent_a_bound[False/True]` fail on fabricated `abandoned visits bound fired` suffix | 2 |

## Still pending

Own full pytest gate and individual independent causes for any failures; own actual headed runtime for valid max_depth=1 refusing depth 2, successful deeper control, other bounds, real abandoned/error and dialog visits with explored siblings, deferred order, synthetic typing, login wall, UI history/detail/Excel download and unchanged historical crawl bytes. Own `browser_check.py` is fresh senior-reviewed for readiness (latest verdict Approve), not yet executed. Earlier instrument review caught fixture order and signature-truncation errors; both were corrected and the latest file re-reviewed. No browser/runtime acceptance is claimed. No source edits, merge, push, or full T-165 close performed.

LIVE-BROWSER: pending shared heavy-lane grant
ISSUES-WRITTEN: none

---
## Cycle 3 — full-suite runtime update (still IN_PROGRESS)

Source: `085537cd549a6aa0ce522aee3d9a6486f2874c83`. Actual full-suite handle `92346` terminated exit 1: **24 failed, 2223 passed, 6 skipped, 14 xfailed, 15 warnings in 1523.29s**. Command: `uv run --offline --active --no-sync pytest -p identity_b --basetemp=D:/autoTesting/.work/check-at113-c3-b-085537/temp-full-cycle3 --junitxml=D:/autoTesting/.work/check-at113-c3-b-085537/full-cycle3.xml --tb=short`, frozen archive cwd and PYTHONPATH, installed root venv, own TEMP/TMP/cache. Eight changed-module import origins passed inside the same pytest process at collection and finish. Raw log and 325335-byte JUnit retained in the owned archive.

Observed failures: two goal metadata checks; ten SessionStart hook checks; ten mutation node-ID/rootdir checks; two mutation process-tree timeout checks. Each exact failure ID is in the raw summary/JUnit. Individual independent baseline/cause attribution is **pending**; these counts are not a blanket waiver. Terminal cleanup matched fresh PID plus creation-time receipts, excluded the prelaunch baseline, stopped only eleven owned leftovers, and read back zero remaining. Own headed synthetic probe is now running as handle `83967` (shell 31288 / Python 34464); no headed result claimed yet.

VERDICT: IN_PROGRESS
