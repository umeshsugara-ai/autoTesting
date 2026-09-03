# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-04 (overdue sweep — prior sweep was `2026-09-03T16:31:54+0530`,
~11.5h old; threshold is 2h). This sweep re-verified the reconciliation commit `f6814b4` (2026-09-04
04:03:28, "reconcile 8 manifests stuck at ready-for-check despite PASS verdicts on disk") rather than
trusting its own commit message.

## What changed since the last sweep, and what was actually re-verified this time

- **`docker-live-ui`** (Docker containerization + noVNC live-watch + shared UI theme) shipped and
  checker-PASSed, commit `4207cff`. New files present and accounted for: `Dockerfile`,
  `docker-compose.yml`, `.dockerignore`, `docker/`, `qa/contracts/docker.md`,
  `qa/manifests/docker-live-ui.md`, `src/autotester/ui/theme.py`.
- **`issue-batch-at012-023-024`** (real O(n)→O(1) perf fix in `ProjectStore`) shipped and
  checker-PASSed, commit `cc1c5bc`. Verdict `qa/verdicts/issue-batch-at012-023-024.md` cycle 1 = PASS,
  manifest status = `checked-PASS` — matches.
- **Disk-hygiene reconciliation** (commit `f6814b4`) flipped 8 stale `ready-for-check` manifests to
  `checked-PASS`: T-050, T-055, T-060, T-065, T-070, T-090, T-100's addendum, T-110.
  **Independently re-verified 3 of the 8 this sweep** (not trusted from the reconciliation's own
  commit message):
  - `qa/manifests/t055-langchain-fallback.md` — manifest claims `Fix cycle: 1`; verdict
    `qa/verdicts/t055-langchain-fallback.md` shows `Cycle checked: 1`, `VERDICT: PASS`. Match.
  - `qa/manifests/t100-ui.md` — manifest is at `Fix cycle: 2` (plus a post-PASS security addendum);
    verdict `qa/verdicts/t100-ui.md` shows `Cycle checked: 2`, `VERDICT: PASS`, **and** a second PASS
    block further down confirming the post-PASS addendum (newline-injection + unvalidated-slug-as-path
    fixes). Match.
  - `qa/manifests/t110-regression-proof.md` — manifest claims `Fix cycle: 1`; verdict
    `qa/verdicts/t110-regression-proof.md` shows `Cycle checked: 1`, `VERDICT: PASS`. Match.
  All three PASS claims are real and the cycle numbers the manifest itself states line up exactly with
  the verdict file's `Cycle checked` — the reconciliation was accurate, not just self-consistent.
- **Full manifest sweep for the same drift class** (`grep -l "## Status: ready-for-check"
  qa/manifests/*.md`) — **zero hits** across all 22 manifests. `grep -n "^## Status" qa/manifests/*.md`
  confirms every manifest reads `checked-PASS` (one variant: `at015-at028-hook-adapter-fix.md` reads
  `STALLED (recovery applied, see below)`, which is a legitimate different terminal state, not drift —
  its recovery verdict `qa/verdicts/at015-at028-hook-adapter-fix.md` (`Cycle checked: RECOVERY
  (post-STALL)`) is `VERDICT: PASS (stall recovery confirmed)`, and the issue flips it claims
  (AT-015/AT-029/AT-030/AT-031 → `fixed`, AT-032 resolved via commit) match `qa/issues.jsonl`'s current
  state). **No other manifest has the same ready-for-check/PASS-verdict drift the last sweep found.**

## Issue ledger — re-verified against current disk state

`qa/issues.jsonl` has 35 rows (AT-001 through AT-035). Only **AT-026** is `open`:
"T-080 delivers a corrected Case, not a durable Script artifact" — a deliberate `HUMAN_GATE`.
Confirmed still accurate: `schema/case.py`'s `Script`/`script_ref` surface is still unused by
`stages/agent_loop.py` (no `Script(...)` construction, no `script_ref` assignment found), and the
question Umesh was asked (build a script-execution engine — a new arbitrary-code-execution surface —
vs. keep the corrected-Case approach) has not been answered on disk (no DECISIONS entry, no
feedback-inbox fold-in, no goal-task scoping it). Correctly still gated; not re-litigated.

All other issues (AT-001 through AT-025, AT-027 through AT-035) are `verified` or `fixed` — every
`fixed`-status row traces to a real PASS verdict for the unit that fixed it (spot-checked above plus
prior sweeps' own checks). None are actionable TODOs; `fixed → verified` promotion for the remaining
rows would need a dedicated re-check pass, which is optional housekeeping, not a gap.

## Goal backlog

`.goal/goal.json`: **20/20 tasks `status: "done"`**, `progress.percent: 100`, `in_progress: 0`,
`blocked: 0`, `pending: 0` — confirmed by direct parse of every task's `status` field.

## Re-grill check

`qa/.regrill-due` does not exist. `north_star` text is byte-identical across every revision in
`.goal/goal.json`'s git history (checked via `git log -p -- .goal/goal.json`) — never edited since
genesis. No reopen-escalation exists (no unit re-PASSed twice on the same evidence). **No `GRILL:`
row needed.**

## Health checks (re-run by this sweep, not pasted from elsewhere)

- `uv run pytest -q` → all pass (2 skipped — one Windows-incompatible POSIX-permission test, one other
  pre-existing skip), 0 failed.
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"

## Bottom line: genuinely idle

The goal backlog is closed (20/20), the disk-hygiene reconciliation this sweep was asked to audit is
accurate (3/3 spot-checked manifests match their verdicts exactly, and no other manifest carries the
same drift), and the only open issue (AT-026) is a real `HUMAN_GATE` still correctly waiting on
Umesh's answer — not something a maker tick can act on. **No TODO rows below**, because inventing
busywork against a closed backlog and a single human-gated issue would be worse than an honest empty
queue.

| # | Status | Unit | Issues | Why now |
|---|--------|------|--------|---------|
| — | none | — | — | Nothing buildable is queued. AT-026 remains the only real open item and it is human-gated (see above). |
