# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-04 — routine safety-net sweep across the six units shipped
since the prior sweep (`2026-09-04T04:15:00+05:30`): docker-live-ui, issue-batch-at012-023-024, a
manifest reconciliation, ui-redesign-and-docker-hardening, at036-screenshot-retry, and
ui-status-vocabulary-fix. All were checker-PASSed individually; this pass re-verifies nothing
drifted across all of them together.

## What this sweep re-verified itself (not trusted from prior commit messages)

- **`qa/issues.jsonl`** — read in full (36 rows, AT-001..AT-036). **Zero rows `open`.** Status
  split: 27 `verified`, 9 `fixed` (a `fixed` row only needs a dedicated re-check to promote to
  `verified`; none block anything). Spot-checked the two most recently touched rows:
  - **AT-026** ("T-080 ships a corrected Case, not a durable Script artifact") — the prior
    `HUMAN_GATE` is now **closed**: Umesh decided in chat 2026-09-04 to keep the corrected-Case
    approach and not build a Script-execution engine (new attack surface for no real gain). No
    DECISIONS entry needed — a decision *not* to build something touches no enforcement path or
    architecture. Row is `verified`.
  - **AT-036** ("intermittent `Page.screenshot` Protocol error under Xvfb") — independently
    re-read `src/autotester/browser/session.py::screenshot()` (lines 187-207): retries exactly
    once after a 250ms wait on the literal `captureScreenshot` error, propagates any other error
    or a second consecutive failure. Matches the manifest's claim and `qa/verdicts/
    at036-screenshot-retry.md`. Promoted `fixed → verified` this sweep (the checker's own
    re-derivation, not the maker's paste).
- **`.goal/goal.json`** — direct parse: **20/20 tasks `status: "done"`**, `progress.percent: 100`.
  `north_star` text is byte-identical to every prior revision (no goal-drift).
- **`qa/manifests/*.md`** — `grep -l "## Status: ready-for-check"` across all 25 manifests →
  **zero hits**. Nothing left dangling across the last several units.
- **Verdict files git-tracked** — `git status --porcelain` on `qa/verdicts/docker-live-ui.md`,
  `qa/verdicts/ui-redesign-and-docker-hardening.md`, `qa/verdicts/at036-screenshot-retry.md`, and
  `qa/verdicts/ui-status-vocabulary-fix.md` each returned **empty** (committed, no working-tree
  drift).
- **Re-grill check** — `qa/.regrill-due` does not exist; north star unedited since last contract
  amendment (contracts last touched 2026-09-03 23:15, goal.json working-tree diff today is
  timestamp/analytics fields only); no reopen-escalation on any unit. **No `GRILL:` row.**
- **Enforcement liveness** — `.claude/settings.json` SessionStart hooks (`mc-sessionstart.ps1`,
  `lab-session-start.ps1`) present and wired; repo has 91 commits (not a dead gate).

## Health checks (re-run by this sweep)

- `uv run pytest -q` → all pass (2 skipped, pre-existing platform skips), 0 failed.
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"

## Live Docker demo server

- `docker compose ps` → `autotesting-autotester-1` **Up** (3 min into this check, container
  40 min old), ports `8010→8000` and `6080` (noVNC) both mapped.
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/` → **200**.
- Confirmed healthy for the live-demo use case.

## Bottom line: genuinely idle

Goal backlog closed (20/20), issue ledger has **zero open rows** (the last open item, AT-026,
was resolved by Umesh's explicit decision this session and is now `verified`), no manifest is
stuck at `ready-for-check`, all four named verdict files are committed, health checks are clean,
and the live Docker demo is serving 200s. **No TODO rows below** — there is nothing buildable
queued and inventing busywork against a fully closed backlog would be worse than an honest empty
queue.

| # | Status | Unit | Issues | Why now |
|---|--------|------|--------|---------|
| — | none | — | — | Nothing buildable is queued. All 36 ledger rows are verified/fixed, 0 open. |
