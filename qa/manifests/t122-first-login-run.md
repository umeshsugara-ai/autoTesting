# Manifest — t122-first-login-run (first logged-in Pathlynks run, D-068 account-derived approval)

## Status: ready-for-check

Goal task: T-122 · Branch: wave/t122-first-login-run · Base: af8f3218 (origin/master after the d063 + T-151 merges)
Policy-Version: proportional-verification/2026-10-06.6
Fix cycle: 0 of 2
Dual check: no
Tier: S (no product code, schema, config or test changed; the diff is this manifest plus qa/evidence/t122-first-login-run-2026-10-07/). The claim is a live-product result, so it is not a docs-lane close: only /checker can PASS it.
Executor: claude (main builder session, no delegation: the unit is a single live run)
Contract: none exists for T-122 itself. `qa/contracts/pathlynks-first-run.md` is T-050's contract (3 login cases); `qa/contracts/consent.md` CN* governs the approval path. Judged against the T-122 goal row below plus `core-invariants.md` and `browser-and-secrets.md`.
Gate answers that apply (word for word):
- `qa/gates/pathlynks-user-account-first.md`: "sabse phle pathlynks user account use krro, vo working credentials hai" (first target is the USER account, `PATHLYNKS_USER_*`, not the counsellor account).
- D-068 (docs/DECISIONS.md:2021): "provisioned credentials are the run approval ... Approval rows are still minted and HMAC-signed automatically, as an audit record, not as a human step." ADVERSARIAL still has no automatic grant.

## Acceptance criteria (verbatim from `.goal/goal.json` T-122)

- title: "Track 0 tail: login case + first logged-in Pathlynks run (credentials present; ERP is the second product)"
- done_check: `{"type": "cmd", "cmd": "uv run pytest tests/test_execute.py tests/test_run_case_pipeline.py", "expect_exit": 0}`
- note (CAVEAT, do not drop): "the same pair was rejected 401 on 2026-09-21 and the cause was never found, so any unit on this path must FAIL CLOSED naming AT-529 rather than assume authentication succeeds ... Write tier: ALLOW_WRITES is authorized (qa/gates/write-policy-tier.md, D-053); the supplied account's own permissions are the boundary. Each run still needs its own RunApproval." (the last sentence is superseded by D-068: the credential-derived row is the approval)
- Operating brief from the orchestrator: use only the `PATHLYNKS_*` keys the project declares; never print credential values; no adversarial cases; real visible browser; evidence under `qa/evidence/t122-*/`.

## Result per criterion

| # | Criterion | Result | Evidence |
|---|---|---|---|
| C1 | done_check green | MET. `uv run pytest tests/test_execute.py tests/test_run_case_pipeline.py` = 20 passed (run in this worktree at base af8f3218 before the live run; no code changed after) | command output in the builder log; re-run by the checker |
| C2 | Login case (`case_35b17ccece2d`, project `login_case_id`) exists and ran against production Pathlynks in a real visible browser (`project.json` `headed: true`) with the `PATHLYNKS_USER_*` pair | MET. Two live runs, each 4 steps, `duration_s` 21.6 and ~22; the browser reached the signed-in dashboard (screenshot `04-step04-click.png`: "Find your direction, PathLynks.", sidebar Dashboard, Logout). No 401, no login error on screen. | `qa/evidence/t122-first-login-run-2026-10-07/run-01M4ATYY74FJJNK62P3702JDZJ/` and `.../run-01M4AV0R6AKHH1M7C77FW2SV22/` |
| C3 | Fail closed naming AT-529 if authentication is not obtained | NOT EXERCISED, and not needed: authentication succeeded both times, so the AT-529 branch (the 2026-09-21 401) did not fire. The 401 cause is still unknown; this run is one more data point that the pair authenticates today (2026-10-07 09:26Z and 09:27Z). | same dirs; no 401 in either run |
| C4 | Approval: D-068 account-derived LIVE_CASE row minted by `core/consent.py::prepare_account_grant`, signed, verified | MET. Rows `appr_bad2891357df` and `appr_140cc431882e` (granted_by `account-derived:D-068`, kind `live_case`, 4 actions, 80 probes, 32 s, scope = the two declared USER keys on `pathlynks.vidysea.com`, not production-flagged). The second run minted a fresh row because the first expired after its 32 s window. | `approval-rows-minted.jsonl` (signature elided) |
| C5 | No adversarial case ran; no counsellor key used; no value printed | MET. Only the BEST login case ran (WORST wrong-password and EDGE empty-submit cases were not run). Keys named in the run: `PATHLYNKS_USER_EMAIL`, `PATHLYNKS_USER_PASSWORD`. Screenshots 02/03 show the email blurred and the password field masked. `scripts/check_no_secrets.py` over the evidence dir and `qa/manifests`: 298 files, 0 leaks. | screenshots + script output |
| C6 | The case verdicts PASS | NOT MET, and it is a finding, not a defect of the run. Both runs: `outcome=assertion_failed` ("expected to contain 'YOUR PROGRESS'" unmet) and, with the real judge (gemini, `grader_provider` not mock/rule), `Verdict.result=FAIL` ("Assertion for 'YOUR PROGRESS' failed on dashboard. Update assertion to match visible page text."). The signed-in dashboard no longer contains the text 'YOUR PROGRESS' (it shows "YOUR NEXT CHAPTER", "Your journey", "Your progress" is gone). The 2026-09-27 probe that saw the marker is stale. | `case_35b17ccece2d.json`, `.verdict.json` in run 02; screenshot 04 |

Finding for the human or `/checker` (PROPOSED-ISSUE, the maker did not edit the case): the login case's step-4 oracle `visible_text: ['YOUR PROGRESS']` is stale against the current production dashboard, so a correct login verdicts FAIL (a false positive, the failure the north star refuses). Smallest fix: re-author the step-4 expectation to a marker the page shows today (for example "Your journey" or the "Logout" control), which changes the content-addressed case id and `project.json` `login_case_id`. Both live under `projects/pathlynks/` (tracked project data), so it is not done in this diff.

Second finding (judge availability): `LangChainFallbackProvider().available()` is False unless `core.env.load_repo_env()` ran first. The UI and CLI call it; my first driver did not, which produced run 01M4ATYY... with `INCONCLUSIVE` "grader failed" (not a product defect). Run 01M4AV0R... is the real-judge run. Kept both as evidence of the two states.

## What ran (no code changed)

- Worktree `D:/autoTesting/.worktrees/t122-first-login-run` off origin/master (af8f3218), `uv sync`, `AUTOTESTER_ROOT` pointed at the worktree and the repo-root `.env` copied in (gitignored; removed after the run) so the main working tree was not touched.
- `driver-single-case-run.py` is the UI `trigger_run` path (`ui/routes_runs.py`: `_require_declared_values` -> `_require_live_case_approval` -> `_execute_with_trace` -> `store.save_run`) restricted to the project's one `login_case_id`, because `trigger_run` itself runs every case and would include the wrong-password WORST case.
- Approval rows and run dirs were written under the worktree's `projects/pathlynks/` (runs dir is gitignored; `approvals.jsonl` is tracked and is left uncommitted).

## Falsification rows (in a copy, `AUTOTESTER_ROOT` = a scratch dir with only project.json, cases.jsonl and a dummy `.env`; no real credentials; driver `falsification-consent.py`)

| Claim | Falsifying edit | Observed | Restored |
|---|---|---|---|
| C4: only account-derived kinds get an automatic grant | ask `prepare_account_grant(kind=ADVERSARIAL)` | red: `ApprovalRequired: no automatic account grant exists for adversarial runs` | n/a, no file edited |
| C4: the grant is bound to declared keys | ask for a grant naming an undeclared key `NOT_DECLARED_KEY` | red: `ApprovalRequired: referenced account key NOT_DECLARED_KEY is unavailable or out of scope` | n/a |
| C4/C2: control, a declared pair with a key present mints a row | LIVE_CASE with the two declared keys | green: row minted | n/a |
| C4: signing key missing refuses | unset `AUTOTESTER_APPROVAL_KEY` (and none in `.env`) | NOT refused: the key is auto-provisioned into the repo-root `.env` (the AT-674 `ensure_approval_key` design; the scratch `.env` gained an `AUTOTESTER_APPROVAL_KEY=` line). So "missing key refuses" is not a property of this path; do not claim it. | n/a |
| C6: the verdict reflects the oracle | run 01 and run 02 both red on the same stale 'YOUR PROGRESS' marker while the screenshot shows a successful login | red in both (reproduced, not flaky: p measured 2 of 2) | n/a |

## Test scope

Builder ran only the T-122 done_check files (S): `tests/test_execute.py tests/test_run_case_pipeline.py` = 20 passed. No removed or renamed names (no code diff). No full suite. Production writes: none beyond the login session itself (BEST login case only; the account's own permissions are the boundary, D-053).

Metrics: start=2026-10-07T09:10:00Z(approx) end=2026-10-07T09:32:00Z(approx) wall_min=22 agent_min=unavailable blocked_min=0 suite_runs=0 repeat_runs=1 mutations=0 cycle=0 resumes=0 tokens=unavailable policy=proportional-verification/2026-10-06.6
