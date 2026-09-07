# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` 2026-09-07T18:40 (overdue routine sweep — prior sweep 2026-09-06
20:15:00, >20h ago). Since then: 8 more Track 0 units shipped and closed checked-PASS
(ui-secrets-declaration, ui-credential-safety, ui-credential-safety-all-fields x2 cycles,
ui-credential-guard-project-routes x3 cycles), AT-052's GRILL gate was answered on disk (not via
`/grill` — Umesh answered directly, captured in `qa/gates/at052-bfs-video-corpus-grill.md`), a
16-task Track A/B backlog was registered (T-121..T-145, commit `fc6aa70`), and Track A1 (T-130)
schema work has started but is mid-flight and uncommitted.

## GRILL

**Resolved this sweep — row removed.** AT-052 is `status: fixed` in the ledger (fixed_date
2026-09-07). The gate carries a proper `**Answered:**` line dated 2026-09-07 naming option (1)
(scope both capabilities, plus the discovered Track 0 prerequisite), the plan is approved and
on disk (`C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md`), and
D-014/D-015/D-016 record the resulting schema/architecture authorizations. `qa/.regrill-due`
remains absent (correct — nothing further to re-grill). Not dropped silently: verified the
`**Answered:**` block itself, not just the ledger status field, before removing the row (the
D-006 "gate answered off-disk" failure mode this check exists to catch would have been an
`Answered:` line missing despite a real answer existing elsewhere — the opposite is not a
concern, and here the line is present and matches the ledger).

## What this sweep found

- **Bypass detection** — walked every commit since the last sweep's stamp (2026-09-06T20:15:00,
  commit `f403e55`) through `HEAD` (`a3d0be4`): `f930306`/`8ab3f5a` (ui-case-management PASS +
  source), `f36ebfd`/`c431f1c`/`7e1863b` (close-out, AT-066 test-only fix, tick stamp),
  `3b91d1e` (AT-052 gate answered), `876367a`/`877f015`/`f8fcba9` (ui-secrets-declaration: build,
  PASS, AT-068 fix), `a61e3bf`/`1bd5091`/`e55f386` (ui-credential-safety: build, PASS,
  close-out), `b811366`/`3312c78`/`8f50c5a` (ui-credential-safety-all-fields: build, PASS,
  close-out), `a3a9b4a`/`1acf35a`/`b49904e`/`db072a3` (ui-credential-guard-project-routes: FAIL
  cycle 1, FAIL cycle 2, PASS cycle 3, AT-088 echo fix), `123bc77` (tick: Track 0 complete),
  `fc6aa70` (governance: plan.md + 16 goal tasks + D-014/D-015/D-016 — docs/config, not product
  code, no manifest expected), `a3d0be4` (tick: T-121 "closed" — see finding below, this claim
  does not match `.goal/goal.json`). **Every code-bearing commit has a matching manifest +
  PASS verdict with the correct `Cycle checked`. No bypassed unit.**
- **Handshake reconciliation** — checked all 4 units closed since the last sweep
  (ui-secrets-declaration, ui-credential-safety, ui-credential-safety-all-fields,
  ui-credential-guard-project-routes): every manifest ends `## Status: checked-PASS`, every
  verdict's `Cycle checked` equals the manifest's final `Fix cycle` (1, 1, 1, 3 respectively),
  no `ready-for-check` manifest sits without a matching verdict. `qa/.last-tick` is fresh
  (2026-09-07T11:47:03Z, well under the 2h staleness bar) and `qa/.paused` does not exist —
  maker is not asleep. Ledger `fixed`-vs-`verified` counts are not runaway (AT-088 `fixed`
  pending its own next-sweep verification is normal lag, not a claims-outrunning-checks pattern).
- **NEW FINDING (AT-089, medium) — a tick claim that does not match the tracked state.**
  `qa/.last-tick`'s 2026-09-07T11:47:03Z line says *"T-121 governance registration closed"*, but
  `.goal/goal.json`'s own `T-121` row is `status: pending` in both `git show HEAD:.goal/goal.json`
  and the current working copy — byte-diffed, unchanged. No `goal_cli.py done --task-id T-121`
  call appears in history since `fc6aa70`. T-121 was never a checker-PASSed unit (no manifest/
  verdict exists for it — it was a governance/docs commit), so this isn't a checker close-out
  miss; the tick's own narration overclaimed. Every task depending on T-121 (T-122..T-145) is
  therefore also correctly still `pending`, which is fine — the mismatch is only in what the tick
  *said* happened.
- **NEW FINDING (AT-090, medium) — WIP mid-migration, uncommitted, doctor currently RED.**
  `git status --porcelain` shows `src/autotester/schema/enums.py` modified (Action gains
  BACK/HOVER/PRESS_KEY/SCROLL, correctly per D-014) plus three new untracked files —
  `schema/analysis.py`, `schema/media.py`, `schema/observation.py` (the D-014 item-2 move
  target). `uv run autotester doctor` right now reports **5 violations**: 4x duplicate-concept
  (`ObservedStep`/`ObservedFlow`/`ObservedScreen`/`VideoObservation` now defined in BOTH the new
  `schema/observation.py` AND their original `schema/flowspec.py` — D-014 says *move*, and only
  the copy half has happened) + 1x stale-generated (`docs/MAP.md` differs from source).
  `uv run pytest -q` is clean (75 passed, 2 skipped) — only doctor is red, and doctor is the exact
  instrument T-121's AND T-130's own `done_check` re-runs. No manifest exists for this yet
  (correctly — it's unfinished, not a bypass), but it sits uncommitted, one `git clean`/checkout
  away from loss — the AT-055 risk class one step earlier (unfinished-and-uncommitted rather than
  finished-and-uncommitted). Not fixed by this sweep (sweep never builds); filed so the next
  tick finishes the migration (delete the four class bodies from `flowspec.py`, re-export if
  anything still imports the old path, run `autotester map`) instead of starting fresh work on
  top of a half-moved schema.
- **Contract coverage** — no gap: `qa/contracts/video-learning.md` and `qa/contracts/explore.md`
  (authorized by D-014/D-015) correctly do not exist yet — they're checker-authored on first
  PASS, and T-130/T-140 haven't shipped. `ui.md`'s amendment log is current through U8/AT-088.
  No stale criteria found.
- **Stale manifests** — none. All 29 manifests on disk end in a terminal `## Status:` line
  matching their verdict's `Cycle checked`.
- **Enforcement liveness** — `.claude/settings.json`'s 5 hook command strings still use the
  `-File` form (D-012), unchanged. Repo has 204 commits (not an empty-history dead gate). Lab
  Protocol wiring: `docs/DECISIONS.md` present, D-000's `Approved-by: Umesh` covers it — no
  approval-required finding. `qa/loop.md`'s `Stop` line lists all 7 terminal states and its
  `Human gate` section is not contradicted by `qa/adapter.json`'s `isolation.done` (still
  `audit-pass`, no deploy claim to check against). Loop-design questions: can it spin — no, each
  tick's Stop line reads a real progress signal (a unit closed or a criterion newly evidenced);
  can it Goodhart the verifier — no, slot-1 is real pytest/ruff/doctor plus checker-judged
  contract criteria, not a proxy; can it run a wrong answer to completion — no, every `done_check`
  sampled this sweep is at least as strong as its contract criterion. No medium finding raised.
- **Silent-failure hunt** — read the diffs of every code-bearing commit since the last sweep
  (the Track 0 units above): no new bare/log-only `except`, no new default-value fallback masking
  an error, no new un-timed/un-rolled-back side effect. The credential-guard work in this window
  is itself hardening, not a new silent-failure surface. Clean.
- **Goal-coverage gap analysis** — `.goal/goal.json` now 36 tasks (20 done, 16 pending, all
  T-121..T-145 correctly `pending` per the AT-089 finding above). North-star text unchanged since
  the version already on record. Track A/B tasks map cleanly onto D-014/D-015/D-016's
  authorizations; no requirement found `missing` beyond what those decisions and the plan already
  scope. No new goal-drift trigger.

## Top-3 recommended next units

1. **AT-090 (medium) — finish the T-130 schema migration before starting anything else in that
   area.** Delete `ObservedStep`/`ObservedFlow`/`ObservedScreen`/`VideoObservation` from
   `schema/flowspec.py` now that `schema/observation.py` holds them, fix any import, run
   `autotester map`, confirm `uv run autotester doctor` is clean, then let T-130's own manifest
   proceed to checker. This clears both the doctor-red state and is a prerequisite for T-121
   actually being closeable (see #2).
2. **AT-089 (medium) — reconcile or correct the T-121 claim.** Either run
   `goal_cli.py done --task-id T-121` if `uv run autotester doctor` is clean at the time (it
   isn't right now, per AT-090), or amend the tick understanding that T-121 is genuinely still
   open. Low effort, clears a real state mismatch before it compounds across 15 dependent tasks.
3. **T-140 (Track B1: observation primitives)** — independent of T-130 (both depend only on
   T-121, not on each other), so it can proceed in parallel per the original plan once someone is
   free to pick it up. T-122 stays correctly `HUMAN_GATE` (needs Umesh to enter
   ERP_EMAIL/ERP_PASSWORD on `/projects/erp/env` before the logged-in ERP run can happen).

Backlog is not empty and not human-gated overall: T-130 and T-140 are both buildable now: AT-090
is what should happen next.

Terminal state: **FINDINGS: 2** (AT-089 tick/goal-state mismatch on T-121; AT-090 mid-flight
schema migration currently failing `autotester doctor`). AT-052's GRILL gate is resolved and its
row removed — not a new finding, a correct close.
