# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-06 (sweep overdue since 2026-09-04T20:58+05:30 — this is
the first sweep in that gap; nothing to catch up on operationally, since only 8 commits landed
and every product-surface one is manifest+verdict backed).

## GRILL

- GRILL: whole-platform BFS crawl + video-corpus eval methodology — a requirement (AT-052) that
  no contract criterion and no prior inbox entry can source: found as an uncommitted addition to
  root `goal.md` at sweep time, asking (1) for an icon/button/screen BFS crawl of the whole
  dashboard beyond today's reviewed-FlowSpec scope, (2) to mine a local video folder
  (`C:\Users\Lenovo\Videos\Screen Recordings`, outside any project's `allowed_domains`) as
  testing-methodology ground truth, and (3) whether the report/test-strategy choice itself should
  be BFS- rather than DFS-driven, even after F-027/F-028/F-029 already shipped both
  visualizations. Only Umesh can scope this without redefining the north star unilaterally. Run
  `/grill "whole-platform BFS crawl + video-corpus eval methodology"`. (AT-052)

## What this sweep found

- **Bypass detection** — walked every commit since the last sweep (`5c0837f`, 2026-09-04T20:59):
  `a3f4c08` (chore: dashboard/tick churn, BACKLOG_EMPTY stamp — no manifest needed, docs-regen
  only), `85815c4` (feat: persistent sidebar US1-US5 — has a real manifest+contract+verdict,
  `qa/manifests/ui-sidebar.md` / `qa/contracts/ui-sidebar.md` / `qa/verdicts/ui-sidebar.md`, PASS
  cycle 1), `9e04db5`/`7be6b80` (checker PASS + close-out for that unit), `3d1cbe6` (chore stamp,
  no manifest needed), `bf9bf07` (D-012: rewrite hook commands `$`-free `-File` form),
  `051303e` (D-013: sync hook scripts, ASCII-escape JSON output). **No bypassed unit.** `bf9bf07`
  and `051303e` are Lab-Protocol enforcement/hook maintenance, not maker-checker product units —
  confirmed both carry `docs/DECISIONS.md` entries (D-012, D-013) with `Approved-by: Umesh`, so
  no manifest is expected and none is missing. `.claude/settings.json` now uses the `-File` form
  throughout for every hook (SessionStart ×2, PreToolUse ×2, SessionEnd) — verified by reading
  the file directly, matching D-012's authorized scope exactly (hook command strings only).
- **Ledger** — 52 rows now (was 51). 1 `open` before this sweep (AT-051, low, unchanged — no
  `goal_cli` ack subcommand exists yet, still correctly out of this project's binding scope per
  the last sweep's own finding). 18 `fixed`-not-yet-`verified` rows, all pre-existing steady
  state (each already carries embedded re-check evidence in its own text; none is new this
  sweep, none blocks anything). Filed **AT-052** (high, goal-drift) this sweep for the goal.md
  feedback gap above.
- **Feedback inbox** — folded the goal.md sidebar entry's missing `Status:` line (it had shipped
  and PASSed two sweeps ago with no close-out note); scribed the new BFS/video-corpus entry
  verbatim (marked unfolded, sourced AT-052 + this GRILL row).
- **`.goal/goal.json` / dashboard / SNAPSHOT.md churn** — the auto-monitor's own
  timestamp/velocity fields (`updated`, `last_deterministic_tick`, `analytics.velocity_per_day`)
  plus the dashboard's regenerated view and the snapshot's mirrored numbers. Safe to leave
  uncommitted — this is expected auto-monitor churn (confirmed via `git diff`: no task status,
  no north-star, no structural field changed), not drift needing a decision.
- **Contract staleness / goal-coverage / enforcement liveness / silent-failure hunt** — no new
  findings. `.goal/goal.json` is still 20/20 `done`; the sidebar commit touched only
  `src/autotester/ui/*` templating code (no new `except`/`catch`, no new I/O side effect) —
  read via `git show 85815c4` diff, clean.
- **`qa/loop.md` vs `qa/adapter.json`** — still byte-consistent (`uv run ruff check src tests
  scripts` in both); Loop-Doctor-lite check unchanged from last sweep.

## Top-3 recommended next units

1. **HUMAN_GATE — the GRILL above (AT-052).** Nothing else should get built against "whole
   platform" scope until Umesh scopes it; building ingest/expand changes ahead of that grill
   risks the exact goal-direction-reversal class this checker is not allowed to self-decide.
2. **AT-051 (low)** — ack the stale `stalled` notification once `goal_cli.py` grows an `ack`
   subcommand (still lives outside this project's root per the standing finding; not a build
   unit here).
3. **Backlog is otherwise genuinely empty** — 20/20 goal tasks done, zero other open issues,
   every shipped unit since the last sweep has a manifest + contract + PASS verdict. The next
   real work is whatever the grill in item 1 produces.

Terminal state: **FINDINGS: 1** (AT-052, high, goal-drift — GRILL demanded, not run by this
sweep).
