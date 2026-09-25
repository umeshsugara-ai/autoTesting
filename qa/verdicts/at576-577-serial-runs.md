# Verdict — at576-577-serial-runs

**Date:** 2026-09-25 · **Head checked:** 8295b79 (fix f30b2ac, base master 80256c3) · **Cycle checked: 1** (manifest Fix cycle: 1 of 3) · **Issues addressed (claimed):** AT-576, AT-577

```
VERDICT: FAIL
SCOREBOARD: AT-576 met (live 303 with an entry case + 2 ordinary cases); AT-577 partly met (RawResult evidence is scoped per case) but its expected clause "keep screenshot names unique" is not met
FAILURES:
- [AT-577 / evidence integrity] sev: high · on the serial path an entry case's screenshots are overwritten by the first ordinary case: _run_entry_case gives each entry case a fresh BrowserSession in the SAME run_dir with its screenshot counter at 0, and now that entry cases run first, the shared session also starts at 0, so both write 01-step01-navigate.png. Live (run-01M3BNKR295JN0DPMR3HM888BZ): 'Homepage loads' (index.html) records 01-step01-navigate.png but that file's sha1 f3a69799 is the login page; 5 PNGs on disk for 6 steps; the run view and HTML report show the login page under 'Homepage loads'. · fix: give every entry-case session its own namespace (the AT-572 mechanism: SessionState.evidence_prefix = case.id in _run_entry_case), or carry one run-wide counter; a test running an entry case + an ordinary case whose first steps both screenshot, asserting distinct paths with different bytes; capability row. · issue: AT-577
CAPABILITY-COVERAGE: not re-run this cycle (the FAIL is decided by Mode D; rows A/B re-run on the fix cycle)
LIVE-BROWSER: qa/evidence/browser-at576-577-serial-runs-2026-09-25-checker/report.json
ISSUES-WRITTEN: AT-578 (the builder's inbox item b)
EXECUTOR: claude-sonnet-subagent (checker: claude-opus-session, checker seat)
EXPLANATION: The reorder fixes AT-576 for real (live 303 where master 500s) and the per-case slice fixes the cumulative-evidence half of AT-577 (Login page loads now carries only its own 05-...). But the reorder makes an existing name collision certain: the entry case's session and the shared session both number from 01 in one directory, so the entry case's evidence is silently replaced by another case's page. The parallel path's evidence_prefix (AT-572) is the ready-made fix.
```

## Answers to the maker's questions

1. **`_assertions_unmet` index math:** still correct. `pre = len(session.state.evidence)` is an absolute index into the unsliced session list, and `_assertions_unmet(session, pre)` scans `session.state.evidence[pre:]`; only `_result` slices. The three scripts that re-slice (`bench_trial`, `regression_proof`, `run_pathlynks_first_cases`) slice `session.state.evidence[start:]` from their own start index, not `result.evidence`, so they are redundant and harmless.
2. **Inbox items.** (a) The execute.md E4 wording ("every Evidence the session recorded" -> "for this case") will be folded when this unit passes. (b) `_network_met` reading other cases' NETWORK evidence does not block this unit, since it predates it and was disclosed; it's filed as **AT-578** (high). Scoping it may reuse the same `evidence_start`, so it could fold into cycle 2 if the builder wants, but it isn't required.

## What I re-ran

- Code read of f30b2ac: the entry-first loop, the `evidence_start` slice at every `_result` exit, and the script call sites.
- **Mode D** (real Chromium, serial n=1 chosen by budget, mock judge): 303, 3 results + 3 verdicts, evidence scoped per card, 12/12 images load, no secret in the DOM. The collision above shows in both the file hashes and the run view.
- Full suite and rows were not re-run: the verdict is FAIL on live evidence, and they'll be run on cycle 2.

## Status: FAIL (cycle 1) — maker fix cycle 2.
