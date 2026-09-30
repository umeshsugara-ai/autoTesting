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
## Cycle 3 — independent attribution and headed runtime update

Still **VERDICT: IN_PROGRESS**, frozen source `085537cd549a6aa0ce522aee3d9a6486f2874c83`. Baseline handle `32505` reproduced the exact two metadata and ten hook failure IDs (12 failed / 6 passed). Direct identical PowerShell hook invocation confirmed execution-policy refusal before hook execution, including the cause hidden by six stdout-only hook tests. Baseline handle `53718` reproduced all ten mutation node-ID failure IDs (10 failed): workspace temporary nested repositories inherit the enclosing pytest root, producing ancestor-relative IDs. All implicated metadata/hook/mutation files and tests have empty baseline-to-source Git diff. **22 individually reproduced; two timeout/kill-tree failure causes still unverified.** No blanket waiver applies.

Headed handle `83967` stopped on an invalid synthetic slug after prior crawl assertions; fixture slug repair passed fresh senior review/syntax before retry. Headed retry `50052` reached and passed depth-one refusal/deeper control/login/abandoned sibling/dialog sibling/typing/three exact bound assertions, then failed the strict legacy-history row assertion. Rendered row cause remains **unknown**: detail, XLSX, console-final gate and historical-byte final gate were not reached. Both terminal headed runs have exact recorded-process cleanup readback zero. Diagnostic-only pre-assert URL/root/store/module/row-text/DOM/screenshot receipts were added without weakening assertions and fresh senior review approved; diagnostic retry awaits coordinated lane grant. No browser PASS is claimed.
## Cycle 3 — all failure IDs attributed; final browser error receipt pending

VERDICT: IN_PROGRESS. Baseline timeout handle `17286` terminated exit 1, reproducing both remaining exact timeout test IDs (2 failed in 98.96s). The unchanged baseline mutation script was asserted as the actual import. An exact-owned-PID/creation-matched default `taskkill /F /T` probe returned `ERROR: Access denied`; scoped cleanup then removed seven exact-owned leftovers with baseline exclusion and readback zero. Thus all **24/24 failure IDs are independently reproduced with specific causes**, not reclassified as a green suite. Rootdir-only baseline control `50053` made all ten node-ID tests pass (57.67s), isolating their environment cause without source or criterion changes.

Headed diagnostic `22602` proved history row count one and visible `ABORTED` versus underlying DOM `aborted`; its earlier failure was casing in the instrument. Three exact observed Google-font CSS requests were blocked by the local environment. Instrument correction asserts both raw and visible status/reason and locally fulfills only those three exact URLs; unknown errors still fail. Latest headed handle `32222` reached/passed all crawl scenarios, strict history/detail badge and qualifier checks, downloaded a 9430-byte XLSX with exact status/reason, and asserted raw historical bytes unchanged, but failed the final `assert not errors`. No overall browser PASS: final error events remain unknown until the reviewed diagnostic receipt executes. Exact recorded browser process readback zero; UI thread stop assertion passed. No source changes or external credentials/access.
# AT-113 crawl completion — checker B final cycle 3

Cycle checked: 3
Source checked: `085537cd549a6aa0ce522aee3d9a6486f2874c83`
Baseline: `c5596a0a6175a2ea10f8c7be80f1082e09b11ba8`
Bound project: `D:/autoTesting`

VERDICT: FAIL
SCOREBOARD: 4/5 applicable feature criteria met, 3/3 applicable invariants hold

Authoritative correction: the earlier cycle-3 PASS claim was premature. Own actual typing control establishes ordinary FILL behavior, but does not independently prove X4 before-every-action enforcement for depth-changing synthetic FILL followed by return-to/replay after the fired bound. This is an identified verification gap, not an inherited checker claim or a proven product defect. That missing proof blocks this unit's PASS; further independent source-derived verification is pending. The reached positive/negative receipts below remain valid within their actual scope.

This is an independent, blind, **diff-scoped AT-113 completion-honesty judgment**, not a green whole-repository suite, a T-165 closure, deployment approval, or authority to push. No maker manifest/plan/evidence or other checker verdict/instrument was read. Parent coordinated manifest naming of the exact 24 independently derived failure IDs; that coordination is not substituted for any runtime proof below.

| Criterion | Independent evidence |
|---|---|
| X4 | Eleven focused depth cases; named red mutations kill omitted depth-bound assignment, forgotten sticky bound, and dedup bypass, then restored green. Actual headed valid `max_depth=1` stops `stopped_bound/max_depth`, no depth-2 node admitted, sibling remains queued; deeper control reaches `/deep` and `/later` at depth 2. Actual max-actions/max-screens/wall-clock scenarios each stop with the exact named bound. Injected-clock regression checks passed in the full suite. |
| X16 | Legacy recorded error hole renders exactly one warning `badge-blocked`, raw status `aborted` and visible `ABORTED`, exact historical-error qualifier in history/detail; no completion badge or frontier-empty language. Actual click downloads XLSX; parsed status and reason match. CLI/history/detail/XLSX legacy-reason mutation killed all four named surface checks, restored green. |
| X18 | Actual read-only login wall stays `login_wall`; actual abandoned error and dialog visits terminate `aborted`, naming `/unstable` and `/storm`, while sibling is explored. Healthy deeper/typing controls complete. Login-with-abandonment bound-invention mutation green 2 / red 2 / restored 2. |
| CR4 | Independent public persona oracle distinguishes reached broken `/lost` from absent/unjudged `/absent`, never inventing missing deletion; healthy exhaustion positive control reports missing. Broken-status exhaustion guard mutation green 4 / red 2 / restored 4; caller exhaustion mutation green 4 / red 2 / restored 4. Full persona regressions passed. |
| CR5 | Abandoned frontier never claims exhaustion; named actual bounds and queued siblings remain represented. Independent terminal oracle covers 20 abandoned/bound/completed combinations. Abandonment terminal mutation green 8 / red 2 / restored 8; unchanged/skip/persona completeness regressions passed in the source full suite. |
| C7 | Own archive, installed root venv, offline active/no-sync, isolated source import checks inside actual pytest at collection and finish, independent oracle and nine named mutation/red/restored proofs; actual positive and negative headed runs below. Full required gates executed, with each outside-unit failure independently traced, not broadly waived. |
| C10 | Frozen source plus baseline Git diff only; source unchanged; all checker commits use `git commit --only` for this `.b.md` path. Index ownership coordinated, cache empty before/after; no merge/push/goal closure. |
| C12 | Unknown/missing evidence is not re-labelled green. Historical stored completion is display-qualified only, raw persisted bytes are identical. Browser classifier accounts for at most one exact successful attachment navigation in the actual click interval; unrelated error remains unmatched and kills the actual negative run. |

## Actual terminal gates and independent failure attribution

- Source full suite handle `92346`, exact command `uv run --offline --active --no-sync pytest -p identity_b --basetemp=D:/autoTesting/.work/check-at113-c3-b-085537/temp-full-cycle3 --junitxml=D:/autoTesting/.work/check-at113-c3-b-085537/full-cycle3.xml --tb=short`: **exit 1; 24 failed, 2223 passed, 6 skipped, 14 xfailed, 15 warnings in 1523.29s**. This result remains red. Actual collection/finish receipts pin eight changed runtime modules to the source archive. Focused handle `94393`: 79 passed.
- `uv run --offline --active --no-sync ruff check src tests scripts`: exit 0, `All checks passed!`.
- `uv run --offline --active --no-sync autotester doctor`: exit 1, only T-171 missing live ledger row. Baseline independently reproduces that same cause; goal/feature rows and ledger implementation unchanged, no T-171 feature row exists. Baseline-only stale snapshot/D-061 citation are not attributed to the source.
- Exact failure IDs are authoritative in own `full-cycle3.xml` and `full-cycle3.log`, individually matched to baseline receipts, not inferred from totals. Metadata/hook baseline `32505`: exact 12 failures, 6 passed; two metadata causes are progress total 81 versus 82 tasks and done T-171 naming absent `tests/test_permission_surface.py`. Ten hook cases are Windows execution-policy refusal before the unchanged hook runs; direct identical invocation exposed stderr hidden by six stdout-only tests.
- Mutation node-ID baseline `53718`: all exact 10 IDs fail identically because nested workspace test repos discover ancestor pytest root. Rootdir-only causal control `50053`: those same 10 pass in 57.67s with process-local `PYTEST_ADDOPTS=--rootdir=.`; no source/test/criterion change.
- Timeout baseline `17286`: the two remaining exact IDs fail in 98.96s in unchanged baseline `scripts/mutation_check.py`; verified-owned default `taskkill /F /T` returns `ERROR: Access denied`, causing the surviving-tree message. Scoped exact-identity cleanup succeeds. All implicated goal/hook/mutation/test/pyproject baseline-to-source Git diffs are empty. These 24 individual outside-unit causes satisfy C7's narrow carve-in; they are not a blanket waiver or a claim the repository is healthy.

## Actual headed positive and negative evidence

Own reviewed instrument: `.work/check-at113-c3-b-085537/browser_check.py`. Earlier fixture failures and their actual reached/unreached limits remain below; no source was repaired to satisfy the instrument. Fresh senior review approved the final classifier/control/negative-mode code and independently executed its eleven pure negative controls.

- Positive handle `59767` **terminal exit 0**, shell 58164 / Python 24712. All nine crawl scenarios, exact warning classes/raw-and-visible texts, workbook checks and historical bytes assertions reached. `positive-artifacts/report.json`, `ui-final-receipt.json`, visible `legacy-history.png`/`legacy-detail.png`, raw DOM and `legacy.xlsx` are preserved independently. Workbook: 9430 bytes, SHA256 `aa167b98b0e66b28ac0747f1ec79ca338b6ab408ce204aed5c7661a033d74770`; historical before/after SHA256 both `8b7c8bef0a3437708d4f4893eb242cc2c635cf72be0baeca04847d9faf72dd8f`.
- Only accounted request event: exact local XLSX URL, GET/document/navigation, `net::ERR_ABORTED`, timestamp inside recorded click start/end; same successful `download.url`, `download.failure=null`, nonempty saved hash, exact workbook/raw-byte checks. Raw/excluded/unmatched lists retained; unmatched is empty. Only three explicitly observed Google-font CSS URLs are locally fulfilled as empty CSS, recorded individually; no external font delivery is claimed. All other page/console/request/HTTP errors fail.
- Negative handle `83564` **terminal exit 1 at the final unmatched-error assertion**, shell 40324 / Python 59584. `browser-artifacts/ui-negative-receipt.json` retains the deliberate `console:checker-b-independent-negative` as the sole unmatched error; only the separate successful attachment event is accounted. This is an actual reached negative-gate kill, not a setup/timeout failure. Independent controls reject failed save, failed workbook readback, empty save, changed historical bytes, absent receipt, wrong URL, non-navigation, wrong failure, out-of-click timestamp, duplicate abort, and unknown console error.
- Exact PID/creation-time receipts and prelaunch baseline exclusion used for owned cleanup. Full-suite eleven leftovers and timeout seven leftovers were removed narrowly; readback zero. Positive and negative recorded descendants absent on readback; known negative UI port no longer listens. Browser closes on assertion failure through `ExitStack`; own UI server thread must stop after join. No active owned heavy handle remains.

LIVE-BROWSER: `D:/autoTesting/.work/check-at113-c3-b-085537/positive-artifacts` and `D:/autoTesting/.work/check-at113-c3-b-085537/browser-artifacts/ui-negative-receipt.json`
ISSUES-WRITTEN: none
EXPLANATION: Applicable completion-honesty criteria pass on the frozen source through independent oracle, named red/restored mutations, full required gates with individual outside-unit attribution, and actual headed positive/negative evidence. Historical bytes are unchanged and unknown browser errors still fail closed. Whole-suite health and full T-165 closure are not claimed.

---
