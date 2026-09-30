# AT-113 crawl completion — primary independent check, current cycle 2

Date: 2026-09-30
Bound root: D:/autoTesting
Adapter: coding
Cycle checked: 2
Reviewed source SHA: f9052150f4cd2af19a5ed3888173e910fa1220ed
Comparison baseline: c5596a0a6175a2ea10f8c7be80f1082e09b11ba8

VERDICT: PASS
SCOREBOARD: 8/8 unit-specific adjudications met (C7, C10, C12, CR4, CR5, X4, X16, X18); retained global-gate exceptions below are not a green-suite claim.
FAILURES: none attributable to this submitted unit.
LIVE-BROWSER: PASS — own headed synthetic-local Mode D, seven scenarios, actual Explore form submissions and reopened downloads.
ISSUES-WRITTEN: none; existing AT-113 retained for maker close-out after both independent checks. Full T-165/T-145 NOT closed.
EXPLANATION: The exact frozen source distinguishes actual abandoned visits from completion and actual named bounds, retains sibling exploration and failed-login observation, preserves missing_unjudged under optimistic exhaustion, and uses only recorded legacy error holes as display evidence. Independent 17-mutation falsification and own browser checks support this diff-scoped verdict. C7 independently justifies the individually named baseline/setup exceptions, not blanket acceptance of red gates.

## Current cycle-2 criterion adjudication

| Criterion | Independent result |
|---|---|
| CR5/C12 — no false completion | `_bfs` drains deferred actions before deriving abandoned statuses; aborted_error/dialog do not exhaust frontier. Error/dialog, reason, deferred-order and sibling mutations killed named assertions. Own headed dialog visit showed ABORTED and abandoned cause, with independent sibling EXPLORED. Healthy static control completed. |
| X4 — actual bounds | Actual max_actions/max_screens/wall-clock/depth retain stopped_bound; other stop reasons do not invent a bound. Bound mutation killed controls. Own headed max_actions=1 crawl showed stopped_bound/max_actions. No limit was relaxed. |
| X18 — login precedence | Tests retained login-wall/not-left-login precedence without invented bound suffix and preserved failed login observation under both abandoned statuses; qualifier mutations killed the exact tests. Real authentication/production login was not performed. |
| CR4 — deletion stays unjudged | Both abandoned statuses force missing_unjudged despite optimistic caller exhaustion; healthy exhausted and genuine missing controls retained. Persona status/wording mutations killed intended assertions. |
| X16 — every status surface | CLI, workbook, detail and history use shared display status/reason; four separate call-site mutations killed their named surface tests. Own browser history/detail/download checks cover healthy, bound, dialog and four legacy records. Only specific recorded error holes change legacy display, never empty actions, issue count or low percentage; stored bytes remained unchanged. |
| C7 — independent gates/falsification | Full unpiped exact-source suite terminal; ruff terminal green; doctor terminal with individually reproduced outside-diff ledger exception. Own cache-free archive harness asserted 72 green baseline, applied 17 unique semantic edits with changed hashes, killed named expected assertions, restored each file and asserted 72 green restored tests plus byte-identical complete source hash mapping. |
| C10 — compliant recovery | Independently verified old/new full trees identical, same parent, declared path subset, clean tracked source and new exact SHA; approved explicit-path amend recovery disclosed. Cycle1 failure remains history, not inherited as a fresh failure after compliant recovery. Checker commits use coordinated --only verdict path; no source edit, merge or push. |
| C12 — fail-closed measurements | Actual terminal exit/counts retained; 14 baseline reproductions separated from one setup failure whose baseline passed. Unknown console/page errors and unexpected requests fail the instrument; six invalid arrangements rejected. Earlier instrument failures retained with cleanup, not reclassified as product PASS. |

Other core invariants and CR1–3/CR6–7/X1–3/X5–15/X17 are unchanged by this unit where outside the above mapping: no schema/dependency/provider/prompt/permission change, safety matrix not widened, and no approved persona overwritten. Doctor checks design/dependencies and full-suite safety/schema tests were rerun; unrelated C9/T171 bookkeeping defects remain explicitly open. This is not certification of every prior feature, production behavior, overall permission coverage, real login, or the whole T-165 goal.

## Terminal independent evidence

- Full suite session 15904: exit 1, `15 failed, 2221 passed, 6 skipped, 14 xfailed, 15 warnings in 1586.20s`; `.work/check-at113-a-full.txt`.
- Ruff: exit 0, `All checks passed!`. Doctor session 27876: exit 1, `ledger-row-missing: T-171`, one violation. Baseline doctor independently reproduces T171; source snapshot fixes the baseline's two generated-document defects. Own runtime native debug.log was reversibly preserved, not a tracked-source edit.
- Nonbrowser baseline session 92288: `14 failed in 102.10s`; each exact ID reproduced on clean c559 archive and test/causal paths diff-identical. `.work/check-at113-a-base/report.json` lists all individual IDs; complete trace `.work/check-at113-a-base/pytest.txt`. Causes: goal total 81 vs 82, missing T171 permission-surface test, ten PowerShell UnauthorizedAccess/missing-signal hook checks, two surviving subprocess-tree timeout checks. These were correctly individually named in manifest and remain defects, not repaired here.
- Fifteenth ID: `tests/test_browser_scroll_invariance.py::test_what_is_reported_does_not_change_when_anything_is_scrolled[hidden+tall]`: direct fixture page.goto fails ERR_NO_BUFFER_SPACE before observe/assertions. Unchanged browser.observe/fixture/conftest paths and native socket10055 establish outside-diff local setup/resource failure. Exact-node baseline passed `1 passed in 1.66s`; NOT claimed baseline-reproduced. Amended manifest individually names this trace. Scroll behavior under full-run pressure remains unmeasured; no blanket waiver.
- Mutation session 49363: exit 0, `PASS 17`; baseline `72 passed`, restored `72 passed, 1 warning in 27.30s`; `.work/check-at113-a-mutation/report.json` contains every anchor/replacement, changed hash, killed node ID and complete source hashes; `source_restored_byte_identical=true`. Complete logs retained alongside it. No __pycache__ copied and no bound-source mutation occurred.
- Own Mode D session 69518: exit 0, seven scenarios; `qa/evidence/browser-at113-crawl-completion-2026-09-30-checker-a2/report.json`, own PNGs/XLSX files. Browser closed, both fixture/server threads stopped, ports54991/54993 closed. No pageerrors; exact denied Google font URL errors and successful workbook-download ERR_ABORTED requests only. Earlier attempts1–4 retained under .work; synthetic signing key and CSS casing were instrument corrections, not product defects.
- Verified orphan trees from full/baseline timeout tests were cleaned only after exact parent/command/trace attribution. Scoped PID/descendant readback empty. Final own instrument-command and owned-port queries returned no rows; no heavy/browser lane retained.
- Final source readback f9052150 unchanged; `git diff HEAD -- src tests` empty. All checks are own evidence; no maker/secondary browser scripts/screenshots or secondary verdict were read.

No merge/push, production calls, credentials, issue closure or whole-goal completion authorized by this primary verdict. Dual-check completion and maker close-out remain separate.

## Historical cycle 1 — preserved verbatim

# AT-113 crawl completion — primary independent check

Date: 2026-09-30
Bound root: D:/autoTesting
Adapter: coding
Cycle checked: 1
Reviewed source SHA: 3342f89afe4769b7de6dbb88b05661602bd64acf
Comparison baseline: c5596a0a6175a2ea10f8c7be80f1082e09b11ba8

VERDICT: FAIL
SCOREBOARD: 0/1 adjudicated criterion met (C10); remaining criteria and invariants NOT ASSESSED
FAILURES:
- [C10] sev: high · The submitted checkpoint was created using a bare git commit after staging, expressly forbidden by C10 even on an isolated branch. · Recreate the private checkpoint with an explicit --only pathspec, preserve its exact source/test contents and others' work, increment the manifest Fix cycle, and submit the new exact SHA for fresh independent checks. · issue: AT-113
LIVE-BROWSER: SKIP (decisive mandatory process failure; browser instrument was not launched)
ISSUES-WRITTEN: none (existing AT-113 retained; this matching-cycle verdict records the failure)
EXPLANATION: The path-subset check holds: the submitted commit contains only explore_status.py and test_explore_blocked.py, both named by the manifest. C10 separately requires every maker/checker commit to use --only/-o and explicitly forbids bare git commit after git add; the manifest's checkpoint disclosure admits that exact prohibited procedure. No contract waiver exists in this check, and absence of foreign committed paths does not satisfy the mandatory command clause.

## Evidence independently obtained

- Read the checker skill, coding adapter and C10 directly. C10 at qa/contracts/core-invariants.md:221 requires explicit commit paths, and :222 prohibits bare commit after staging.
- Read qa/manifests/at113-crawl-completion.md:156-158: the pinned checkpoint used a staged two-path index audit followed by bare git commit rather than the required --only pathspec. This is a disclosed procedural fact, not a test result accepted as passing evidence.
- Ran `git -C .worktrees/at113-crawl-completion rev-parse HEAD`: returned exactly 3342f89afe4769b7de6dbb88b05661602bd64acf.
- Ran `git -C .worktrees/at113-crawl-completion show --name-only --format= 3342f89afe4769b7de6dbb88b05661602bd64acf`: returned exactly src/autotester/stages/explore_status.py and tests/test_explore_blocked.py.
- Ran `git -C .worktrees/at113-crawl-completion show --format=fuller --stat 3342f89afe4769b7de6dbb88b05661602bd64acf`: two files, 73 insertions and 3 deletions. This establishes scoped contents, not the commit invocation.
- Ran source-worktree status: no tracked changes; two untracked maker evidence directories. Did not read their scripts/screenshots or any other final checker verdict.
- Ran root HEAD/status and cached-path inspection before writing: root remained c5596a0a, cached paths empty, existing unrelated dirty paths preserved.

## Deliberate limits

No full pytest, ruff, doctor, baseline failure attribution, capability falsification, mutation harness, or headed Mode D browser run was launched. No behavioral PASS, C7 waiver, baseline-failure classification, or independent browser claim is made. The mandatory C10 failure is sufficient to reject this cycle; the parent explicitly requested avoiding a heavy run solely to seek PASS after a decisive procedural failure. No live jobs/handles were created, and the heavy lane is released.

The checker did not edit product code, source checkpoint, manifest, contracts, goal state, or production data. AT-113 remains unresolved by this verdict; T-165 and T-145 are not closed. Fresh checks after compliant resubmission must still establish every applicable behavioral criterion, independent C7 attribution and falsification, and Mode D evidence; fixing the commit procedure alone is not completion.

## Recovery boundary

The maker owns recovery on the private branch. Preserve/recover the exact current patch using a non-destructive private-checkpoint procedure with explicit pathspecs; do not reset the shared root or rewrite this verdict. A changed SHA must receive a new matching cycle and fresh independent checks, as C10 requires. This checker grants no permission to merge or push.

## Historical cycle-2 partial checkpoint — retained measurement trail

Bound root: D:/autoTesting; adapter: coding.
Cycle checked: 2
Source SHA: f9052150f4cd2af19a5ed3888173e910fa1220ed
Baseline: c5596a0a6175a2ea10f8c7be80f1082e09b11ba8

State: IN PROGRESS — full gates and own headed Mode D are terminal; independent baseline attribution and capability falsification remain live. This is durable partial state under C12, not PASS or FAIL.

Independent command launched: `uv run --active --no-sync pytest -o pythonpath=src --basetemp=D:/autoTesting/.work/check-at113-a-temp -o cache_dir=D:/autoTesting/.work/check-at113-a-cache > D:/autoTesting/.work/check-at113-a-full.txt 2>&1`, working directory the isolated source worktree, VIRTUAL_ENV the installed root venv, PYTHONPATH the isolated source. Tool handle 15904; owned pytest PID 19096, parent 41280, confirmed by read-only CIM. No pipe or additional `-q`.

Source tracking clean; untracked maker evidence directories were not read. Own mutation harness: `.work/check-at113-a-mutations.py`; own headed browser instrument: `.work/check-at113-a-browser.py`; neither launched while the full suite owns the heavy lane. No maker/browser scripts, screenshots or second verdict were read.

Terminal full-suite readback: session 15904 exit 1; `15 failed, 2221 passed, 6 skipped, 14 xfailed, 15 warnings in 1586.20s`. Exact output: `.work/check-at113-a-full.txt`. Ruff exit 0, `All checks passed!`. Doctor after reversibly preserving the suite-generated Chromium native `debug.log` in `.work/check-at113-a-native-debug.log`: exit 1, exactly `ledger-row-missing: T-171 — closed high-value task has no live/updated row`, one violation. Clean baseline doctor independently reports the same T-171 omission plus two snapshot defects absent from this source.

New full-suite failure initially absent from the submitted manifest: `tests/test_browser_scroll_invariance.py::test_what_is_reported_does_not_change_when_anything_is_scrolled[hidden+tall]`. The maker subsequently individually named it and its measured trace without changing source SHA or ready status; checker re-read that clause. Actual failure is fixture direct Playwright `page.goto` before observation/assertions: `net::ERR_NO_BUFFER_SPACE` at local fixture URL. Native socket log records Windows 10055. The test imports unchanged browser.observe; the test, conftest, and browser subtree are unchanged across baseline/source. No changed exploration/status/report function participates in the failed setup. An independent clean baseline exact-node run passed (`1 passed in 1.66s`), so this is NOT claimed as a reproduced baseline failure. C7's outside-diff setup/resource exception is independently justified; scroll behavior under full-run resource pressure remains unmeasured, no blanket waiver or complete-suite green claim is granted.

Own headed Mode D: final instrument session 69518 exit 0, seven checked scenarios. Three actual Explore form crawls: healthy completed/frontier empty, max-actions bound stopped_bound/max_actions, repeated-dialog abandoned visit aborted with named reason while independent sibling was explored. Four stored legacy controls: recorded error hole displayed aborted; empty/high-issue/low-percent records without that hole remained healthy. Each checked real history/detail status, tone, reason and downloaded/reopened Excel workbook. Historical crawl bytes unchanged. Report: `qa/evidence/browser-at113-crawl-completion-2026-09-30-checker-a2/report.json`; own screenshots and workbooks alongside it. No page errors; only individually recorded blocked Google font errors and exact successfully downloaded workbook ERR_ABORTED requests accepted. Fail-closed discriminator rejected six invalid instrument arrangements. Earlier instrument attempts (missing synthetic signing key; CSS uppercase assertions) were retained under `.work/check-at113-a-browser-attempt1` through `attempt4`, with server cleanup true, not product failures. Final browser closed, UI/fixture threads stopped; ports 54993/54991 had no sockets afterward.

Completed-suite orphan cleanup: verified pytest children 30744/52000 self-exited; exact owned trees 47360 and 52212 with descendants were terminated after parent/command revalidation, and CIM readback found no captured owned processes/descendants. Heavy/browser lane released before independent B work. Baseline attribution session 92288 terminal: all 14 nonbrowser failure IDs reproduced (`14 failed in 102.10s`), every test identical; goal progress 81 vs 82, absent T171 done-check file, ten PowerShell UnauthorizedAccess/missing-signal hook failures, and two mutation subprocess-tree timeout failures. Their relevant goal/ledger/hook/mutation paths are unchanged. Baseline pytest PIDs 47036/43424 named in trace were independently verified and cleaned with descendants; scoped readback empty. Fake-only mutation harness session 49363 remains live. Mutation baseline asserted green (`72 passed`); first six named mutations killed expected tests with individual restoration asserted. Final all-source hash restoration and restored green remain pending.

Recovery independently checked: old/new full tree ids both `2c96e96237bdcc4a7c05ed23c95136581bdaa9d0`; old/new parent both `d219f03add5df490b9fa068b03f9037016526295`; `git diff --exit-code 3342f89a f9052150` returned no differences. New tip's two paths are both declared. Cycle 1 FAIL above remains byte-intact; no inherited behavioral PASS is credited.
