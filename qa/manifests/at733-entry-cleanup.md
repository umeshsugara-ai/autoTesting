# AT-733 — logged-out entry-profile cleanup honesty

Status: building
Fix cycle: 1
Criticality: HIGH
Dual check: required (false-PASS prevention)
Contract: qa/contracts/ui-run.md RU1/RU3, entry-profile amendment; core-invariants C7/C12
Issues addressed: AT-733 (existing canonical open issue)
Goal: reliable generic release regression; this repair does not close any full pending goal task.
Worktree: C:/Users/Lenovo/.codex/worktrees/at733-entry-cleanup/autoTesting
Baseline: 0b7908a7ff4254d376f2cfe081a7d3ea2fd92a1d
Submitted candidate: 6e0134b7558cd4a67efbfbc72e620ebc16c78506 (private branch only, not released)
Plan: D:/autoTesting/.work/at733-cleanup-plan.md

## Independent plan approval

Fresh reviewer /root/approve_next_seed_recovery first issued Warning, requiring error-sensitive lstat, narrow filesystem exception handling, contained fixture paths, real deterministic ERRORED grading, entry construction tracking, actual serial/parallel selection and mandatory healthy/failure controls. Maker revised the existing plan accordingly. Fresh rereview returned Approve on 2026-10-01; approval covers AT-733 plan only, not AT-113 recovery or completion. Reviewer performed inspection only, no test execution.

## Exact existing-file implementation scope

src/autotester/ui/run_execution.py:55::_run_entry_case; tests/test_ui_runs_serial_resilience.py existing helpers/parameterized route tests. No new source/test module, alternate grade/store path, schema/contract/architecture/enforcement change. AT-736 browser-start lifecycle remains separate.

## Preflight

Isolated worktree source clean and baseline recorded by actual git status/rev-parse. Ledger relitigation actual command with workspace-local UV_CACHE_DIR: uv run --offline autotester ledger relitigation 'AT-733 logged-out entry-profile cleanup honesty: fail-closed cleanup before browser startup' exited0, no gate / no retired features (rule). Earlier default uv cache ACL failure retained; it was not a relitigation verdict.

## Evidence pending

Red-first actual evidence (2026-10-01): .work/at733-maker-red/entry-red.xml records 13 tests, 6 failures, 0 errors, 0 skipped. Maker reports six cleanup arms (raising/leftover/inspection x serial/parallel) fail and four healthy/absent controls plus three existing tests pass. Root independently reread XML counts, imported-module binding to the isolated worktree, and entry-red-ownership.json: direct pytest exit1, two captured PID+creation identities both alive:false, no cleanup failure. The wrapper's exit0 is not the pytest result. Production source was untouched during this red run. Test file budget reported 300 lines, test function50; exact final diff budgets require checker verification. Approved narrow source correction now proceeds; no green/PASS claimed.

Initial focused green: .work/at733-maker-green/entry-green.xml records13 tests,0 failures,0 errors,0 skipped; root independently reread these counts and entry-green-ownership.json direct_exit0 with two captured PID+creation identities alive:false. Maker reports13 passed/1 warning in2.44s. Narrow source diff adds lstat inspection/removal/postcondition and an ERRORED tuple through existing grade_errored_result before browser construction. Source/function reported207/37 lines. Focused lint found seven formatting/import/line-length issues after its initial default-cache ACL denial; correction is in progress, so this initial green does not certify final formatted source.

Remaining: final formatted source-bound focused green/lint, fresh source review, actual Windows locked-file cleanup sabotage, headed synthetic local report acceptance, independent mutations, full adapter verification and matching-cycle independent verdicts are NOT yet complete. Ownership readbacks are proven only for their respective runs, not future verification. Maker execution continues; no ready-for-check/PASS/commit/push/release claim.

Final formatting checkpoint: maker entry-final pytest exited0,13 passed/1 warning in2.29s, ownership identities read back alive:false; focused ruff exited0. Fresh independent senior reviewer /root/review_at733_source APPROVE: no source findings, real ERRORED grading and caller persistence retained. Reviewer independently ran the exact isolated source via PYTHONPATH:13 passed/1 warning in2.36s. This is source approval only, not unit PASS. Reviewer identified missing post-removal inspection-denied test coverage and stronger cause/note equality assertions; maker is extending those existing test arms before final freeze. Current source function remains the approved narrow cleanup correction; live locked-profile/report and full independent acceptance remain pending.

Strengthened checkpoint: post-removal inspection arm and exact cause/note/rule grading assertions added in the existing test. Fresh reviewer APPROVE, independently15 passed/1 warning in2.19s, no remaining gap within the authorized simulated-cleanup scope; actual Windows lock/live browser remain unproven. Maker strengthened run15 passed/1 warning in3.62s, focused lint0, PID+creation readbacks alive:false at .work/at733-maker-strengthened/entry-strengthened-ownership.json. Source unchanged from approved implementation. Private immutable candidate commit authorized for exactly the two source/test paths; its initial index ACL denial is not a commit and narrow escalation is in progress. No root integration/push/PASS. Full adapter verification and real locked-profile/browser checks will bind to the successful candidate SHA.

Candidate checkpoint succeeded after authorized narrow escalation: 6e0134b7558cd4a67efbfbc72e620ebc16c78506, exactly two approved files; root independently verified git show/stat, HEAD and empty worktree/index. Source blob b91aede0fb072419af391b4b758c8c290af60f62; test blob8280be5fe55fdabaaefa25dc24a96a6bf9fb9b44. Actual full offline uv --active --no-sync pytest session36134 launched against this frozen candidate; .work/at733-maker-full-6e0134b7/candidate-full* holds log/JUnit/module binding/ownership receipts. Terminal outcome pending. Earlier in-memory PowerShell parse failure launched no process and is not test evidence. No push/release/independent unit verdict.

Running-gate update: owning36134 poll confirmed live, wholelog16% with one failure marker (ID/cause not yet terminally classified). Collection module binding exists; ownership helper tracks creation identities in memory and emits final receipt on natural terminal, so no durable live roster was yet established. Full ruff on frozen candidate exited0, All checks passed. Doctor exited1 with five reported violations: missing T-171 ledger row, stale docs/SNAPSHOT and dangling D-061 citations at existing secondary AT-113 verdict lines209/281 and SNAPSHOT44. No regeneration, waiver or baseline attribution yet. Two fresh blind AT-733 checkers dispatched for independent read-only preparation, heavy/headed/full execution explicitly held until owning maker suite terminates; this is not ready-for-check acceptance or a verdict.

AT-113 remains cycle3 STALLED with independent FAIL and unanswered recovery disposition. This independent repair neither grants an extra AT-113 cycle nor weakens its bounds.

Independent cheap ancestry inspection: checker A compared exact baseline/candidate Git blobs and found doctor.py, ledger/checks.py, ledger/render.py, ARCHITECTURE, MAP, SNAPSHOT, FEATURES, DECISIONS, goal.json and issues.jsonl byte-identical. Source/test line counts are207/297; changed source function remains below50. This supports scope attribution only; it does not establish doctor cleanliness, waive its five failures, or replace an independent exact-tree runtime rerun. Maker session36134 remains the sole heavy lane; fresh root log inspection progressed to25%, with terminal outcome still pending.

Independent doctor runtime evidence now exists: .work/check-at733-a/baseline-binding.txt and candidate-binding.txt bind doctor.py and repo_root to separate exact-SHA archives. Baseline/candidate-doctor.txt each report the same five exact diagnostics (T-171 missing ledger row, stale SNAPSHOT, missing D-061 citations at secondary AT-113 verdict209/281 and SNAPSHOT44); doctor-results.json records baseline0b7908a7/candidate6e0134b7 and each command exit1. Root independently reread bindings, all diagnostic lines and SHA/exit fields. This proves these five doctor failures predate the AT-733 source diff; it does NOT make the adapter exit0 gate green, authorize a waiver, or certify runtime/browser acceptance. Owning comparison session85737 terminal acknowledgement remains to be recorded separately.

Checker A confirmed actual85737 terminal tool response exit_code0/no session_id (orchestration only), both underlying doctor commands exit1, exact Compare-Object output empty. Import/root assertion subprocesses each exit0. Thus the comparison completed; the doctor gate remains red and no independent unit verdict was issued.
