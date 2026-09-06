# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-06 (second sweep today — prior sweep at 12:13:52+05:30
found AT-052 goal-drift and closed clean otherwise; this sweep specifically re-verifies the
AT-053/AT-054/AT-055 recovery this session made and re-confirms AT-052's HUMAN_GATE).

## GRILL

- GRILL: whole-platform BFS crawl + video-corpus eval methodology — **unchanged from the last
  sweep, still correctly gated, not dropped or re-litigated.** AT-052 (open) and this row persist
  because no grill has happened yet — `qa/.regrill-due` does not exist (grill not yet run), the
  goal.md feedback is still unfolded in `qa/feedback-inbox.md`, and the north star text is
  unchanged since the last sweep (confirmed byte-for-byte against `.goal/goal.json`), so nothing
  here regresses or auto-resolves. Only Umesh can scope this. Run
  `/grill "whole-platform BFS crawl + video-corpus eval methodology"`. (AT-052)

## What this sweep found

- **Bypass detection** — walked every commit since the last sweep's stamp (2026-09-06T12:13:52,
  commit `f403e55`): `26b1aab` (checker PASS, at053-navigate-settle, cycle 1 — manifest+contract-
  gap+verdict present, see below), `91924f3` (checker PASS, at054-live-watch-slowmo, cycle 1,
  same), `55befd8` (recovery commit landing the two units' actual source diffs — execute.py,
  test_execute.py, session.py, docker-compose.yml — that the two PASS commits above had missed;
  read in full, diff is exactly what both manifests describe, nothing extra), `02e2828` (chore:
  onboard `projects/vidysea-erp/{project.json,cases.jsonl}` under the same convention as
  `projects/pathlynks/`, plus `.gitignore` entries for `.playwright-mcp/`/`.handoffs/` scratch —
  data/config chore, not product code, no manifest expected), `616d8de` (ledger: file AT-055).
  **No bypassed unit.**
- **Handshake reconciliation (the specific ask this sweep was dispatched to answer):**
  independently confirmed the maker's/session's claimed recovery, not trusted the commit message —
  `git status --porcelain` on `src/autotester/stages/execute.py`, `tests/test_execute.py`,
  `src/autotester/browser/session.py`, `docker-compose.yml` is now clean, and
  `git diff HEAD -- <those 4 files>` is empty (fully committed, nothing left in the working tree
  one `git clean`/checkout away from loss). `git show --stat 55befd8` touches exactly those 4
  files plus the at054 manifest's close-out flip — matches both manifests' described changes.
  Read the actual diff (not just the stat): `execute.py`'s `if step.action is Action.CLICK` became
  `if step.action in (Action.CLICK, Action.NAVIGATE)` (AT-053), `session.py::launch_options` gained
  an `AUTOTESTER_SLOW_MO_MS` opt-in env var defaulting to `0` threaded into Playwright's `slow_mo`
  (AT-054) — no new silent-failure pattern introduced (no new bare/log-only except, no new
  default-value fallback masking an error). **Verdict: genuinely committed and matches both
  PASSed manifests.**
- **Contract amendment gap (found + fixed this sweep, filed as AT-056):** `qa/contracts/
  execute.md` and `qa/contracts/docker.md` amendment logs both ended at their prior rows
  (AT-045/AT-048 and ui-sidebar respectively) — neither AT-053 (NAVIGATE settle) nor AT-054
  (slow-mo env var) had a contract-side trace, the same gap class AT-043/AT-048 already named.
  This was an open question from an earlier senior-engineer review for AT-053 specifically, and
  turned out to apply to AT-054/docker.md too. **Fixed this sweep** — both contracts now carry a
  2026-09-06 routine amendment row recording the fix, the PASS verdict, and (docker.md) a pointer
  to AT-055. Both are routine (recording a shipped, already-PASSed fix; nothing weakened).
- **AT-052 (goal-drift GRILL) still correctly gated** — re-confirmed `qa/.regrill-due` absent,
  `AT-052` still `status: open` in the ledger, the `GRILL:` row still present above the TODO
  table, and the goal.md feedback entry in `qa/feedback-inbox.md` still marked unfolded. Not
  silently dropped, not re-litigated, not auto-resolved by this session's unrelated work.
- **Checker dispatch-protocol recommendation (not applied — outside this project's bound root):**
  the root cause of AT-055 is that Mode A step 7 in the global `checker/SKILL.md` only says
  "commit the verdict file too, with a narrow pathspec" — it never tells the checker to confirm
  the maker's source diff is *also* committed in the same handshake, so a checker can correctly
  follow its own protocol to the letter and still leave the maker's real fix stranded in the
  working tree (exactly what happened twice, at053 and at054, before this session's manual
  recovery). This checker judges the fix genuinely warranted, but **does not apply it** — that
  file lives outside `D:/autoTesting` (`C:/Users/Lenovo/.claude/skills/checker/SKILL.md`), and
  "Mode B sweep never leaves the bound root" / "all reads and writes stay inside the bound root"
  are hard rules in the checker's own charter. Recommended wording for Umesh to apply globally:
  Mode A step 7, after "commit the verdict file too" — add "and, in the same commit or an
  immediately adjacent one, confirm `git status --porcelain` is clean for every file the manifest's
  `What-changed` section names; if it is not, commit those too (or note explicitly why they are
  intentionally left uncommitted) before returning the verdict." This is a recommendation, not an
  applied change.
- **Ledger** — 56 rows now (was 52 two commits ago in this session's own recovery pass, 54 before
  this sweep). AT-055 flipped `fixed → verified` (independently reproduced above, not merely
  re-asserted). AT-056 filed and closed same-sweep (contract amendment applied immediately, per
  the criticality gate: routine amendments are auto-apply-and-commit). AT-051 (low, stale
  unacked notification) still `open`, unchanged — still correctly out of this project's binding
  scope (fix lives in the shared `D:/ai_os` `goal_cli.py`, not this repo).
- **`.goal/goal.json`** — still 20/20 tasks `done`, project `status: active`; north star text
  byte-identical to the version already on record when AT-052 was filed (re-read and compared),
  so no *new* goal-drift trigger fired this sweep beyond the one already gated.
- **Enforcement liveness** — re-confirmed `.claude/settings.json`'s 5 hook command strings all
  still use the `-File` form (D-012) — unchanged since the last sweep, no regression.
- **Silent-failure hunt** — read the full diff of `55befd8` (the only code-bearing commit since
  the last sweep): no new bare/log-only `except`, no new default-value fallback masking an error,
  no new un-timed/un-rolled-back side effect. Clean.

## Top-3 recommended next units

1. **HUMAN_GATE — the GRILL (AT-052), still standing.** Nothing whole-platform-scoped should get
   built until Umesh scopes it. Unchanged priority from the last sweep.
2. **Recommendation for Umesh (not a build unit in this project) — tighten `checker/SKILL.md`
   Mode A step 7** per the wording above, so the AT-055 failure mode (PASS-commit lands paperwork,
   leaves the real fix uncommitted) cannot recur across any maker-checker project, not just this
   one. Global file, human-approved change, outside this sweep's authority to apply.
3. **AT-051 (low)** — ack the stale `stalled` notification once `goal_cli.py` (shared skill)
   grows an `ack` subcommand. Still out of this project's root; not a build unit here. Backlog is
   otherwise empty: 20/20 goal tasks done, only AT-051 (low, out-of-scope) and AT-052
   (HUMAN_GATE) open.

Terminal state: **FINDINGS: 2** (AT-055 verified closed for real this sweep; AT-056 found and
fixed same-sweep as a routine contract amendment). AT-052's GRILL gate reconfirmed standing, not
a new finding.
