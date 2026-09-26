# Verdict — at597-pin-issue-caller

**Date:** 2026-09-26 · **Cycle checked:** 1 · **Checker:** claude-sonnet-subagent (Mode A + Mode D) + orchestrator reproduction

```
VERDICT: FAIL
SCOREBOARD: the UI pin route is sound and fully guarded; the CLI `issues pin` path fails C5 and AT-597's "human-confirmed steps" purpose
FAILURES:
- [C5 / B2, AT-597] sev: high · cli_issues.py::pin_cmd (line 101) runs no credential guard (no SecretStore, _guard_submitted_case or _refuse_unsafe_submission equivalent). `autotester issues pin demo <id> --step "fill:#password:SuperSecretRaw123"` exits 0 and writes "value":"SuperSecretRaw123" in plain text to cases.jsonl, a git-tracked file in a public repo. The UI route refuses the same input with a 400. · Fix: pin_cmd loads the project's SecretStore and runs the same guard the UI uses over every parsed step's target, value and expect before pin_issue_as_case; add a CLI test with a raw declared value → non-zero exit and nothing written. · issue: AT-597
- [AT-597] sev: high · _parse_step (cli_issues.py:83) does raw.split(":", 3), so a URL target is corrupted and still reported as success: "navigate:https://example.com/login" becomes target='https', value='//example.com/login' (orchestrator reproduced by calling _parse_step directly). The pinned "repro" can never navigate to the bug, and the CLI does not run _require_reachable_navigate_steps either. · Fix: split the action off first and parse target so an embedded "scheme://" survives (or take --target/--value/--expect per step); run the same reachable-navigate check as the UI; add tests with https:// targets and values. · issue: AT-597
CAPABILITY-COVERAGE: 8/8 rows reproduced (copy c597-1; each single-hunk mutation red on its named test; restored 16/16)
LIVE-BROWSER: qa/evidence/browser-at597-pin-issue-caller-2026-09-26-checker (visible Chromium against the real uvicorn app: pin link → form → 303 → case pinned with pinned_issue_id; the pill replaces the link; delete gives 409 and the case survives; a truly blank form gives 400 (row-0 Target is pre-filled with base_url like the case form, so it must be cleared); 1 console line = the expected 409 log, AT-596)
ISSUES-WRITTEN: AT-604 (medium: re-pinning an already-pinned issue with different steps creates a second pinned case)
EXECUTOR: maker (checker: claude-sonnet-subagent)
EXPLANATION: UI probes all hold: a raw secret is refused 400, a declared {{SECRET:KEY}} is stored as the placeholder, an undeclared placeholder is refused, an XSS title is escaped, path traversal in issue_id gives 404, another project's issue gives 404, and an identical double pin is refused. No CSRF guard, but no existing POST route has one either, so it is not a regression. 4c clean: every removed line has a successor, and the issues page renders the same 13 columns in order plus "Regression" at the end (base vs branch rendered side by side). Files 161/156 lines.
```

Evidence: 143 passed, 1 skipped · ruff clean · doctor clean (c597-1) · CLI probes: unknown project/issue, zero --step, malformed step and unknown action all exit 2 cleanly; the URL target and the raw secret exit 0 with wrong data.
