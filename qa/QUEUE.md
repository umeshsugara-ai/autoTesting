# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-25T06:07:48+05:30**. The stamp comes from the system clock
(`date`), not typed (AT-399). Bound strictly to `D:/autoTesting`. **Sharded** sweep (140 source files):
three read-only shards (checks 1-1b-2-3 · 4-4b-5-6 · 7-9 + token ledger + fixed-row reverify) and one
consolidation checker as the single writer. Window `f1b8569..8a97eca`, 103 commits (master moved on to
`a49c3b8` during the sweep; those later commits are the T-172 close-out and this sweep's own writes).
Supersedes the `2026-09-18T01:41:32+05:30` queue — its top-3 (at496 close-out, AT-483 wave, three
HUMAN_GATEs) resolved: at496 and the AT-483 wave closed; the HUMAN_GATEs are the GRILL rows below.
The 2026-09-24T16:29Z sweep stamped `.last-sweep` but never refreshed this file — that drift is the
"QUEUE drift" item in T-126, closed by this refresh.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy (AT-218). Unanswered, carried. (Two fresh instances
  this window: AT-561's empty-redactor gate and AT-565's unguarded factory — both caught, both fixed or in fix.)
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281). Carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js`. Carried.

## Top-3 recommended next units

1. **at562-564-live-wiring** (in build) — wire the CLI/UI run entry points through `StageContext` with
   `secrets=` and through `run_cases`, AND fix **AT-565** (PR6: `session_factory` outside the try) before
   parallel execution reaches real runs. Closes AT-562, AT-564, AT-565; re-closes T-173. Checker bar:
   every non-browser test file green; real Mode D (UI entry points change); a PR6 test where the FACTORY raises.
2. **AT-566** — cap `BLOCKED` in `qa/loop.md` the way HUMAN_GATE is capped (loop-design "can it spin").
   Small, maker/init-owned.
3. **AT-567** — split `ui/helpers.py` (300/300 lines after six credential-guard fixes in 14 days)
   by responsibility BEFORE the next credential fix lands; `stages/explore_node.py` is in the same state.
   Signal only, never a blocker — but the next fix to either file has zero headroom.

## Findings this sweep — FINDINGS: 3

| Issue | Sev | What |
|---|---|---|
| AT-565 | high | PR6 crash isolation covers `run_fn` only: `_run_one` calls `session_factory(case)` outside its try, so one case's context-launch failure aborts `run_cases` and discards every sibling's result. Missed by the t173 checker PASS (its PR6 row only mutated the `run_fn` except-clause). **T-173 reopened.** |
| AT-566 | medium | `qa/loop.md:53` — `BLOCKED` re-arms `ScheduleWakeup 300s` with no cap, unlike HUMAN_GATE (max 8) / STALLED (3 cycles) / EXHAUSTED (stop). |
| AT-567 | medium (erosion signal) | `ui/helpers.py` and `stages/explore_node.py` both at the C2 300-line cap after 6 and 9 commits in 14 days. |

**Extended, not re-filed:** AT-564 now also names T-163 — the resumable orchestrator has no CLI/UI caller,
and unlike T-172/T-173 this is undisclosed (FEATURES F-045 is `live`, target.md M8 ticks T-163 with no
caveat). Maker to add the caveat until at562-564 lands.

## Applied this sweep (checker-owned surfaces)

- **Reopen-power / reverify sample:** 8 highest-severity recently-`fixed` rows re-derived against today's
  code with a green test run — all 8 **VERIFIED**, none reopened: AT-528, AT-531, AT-532, AT-540, and the
  at540-cycle1 rows of AT-547..AT-550. (AT-532's shipped pin is weak — passes with FILL_TARGETS emptied —
  a pre-existing caveat already in its checker note, not a regression.)
- **Contracts DRAFT -> ACTIVE** (each pre-authorized by its own status line; precedent network-assertions.md):
  `parallel-run.md` (T-173), `run-trace.md` (T-172), `skills.md` (T-175).
- **Inbox fold:** the 2026-09-24T23:00 D-042 entry -> `agent-layer.md` AL2/AL3/AL4 (already drafted there).
- **Gate bookkeeping:** `qa/gates/at110-approval-forgery.md` header OPEN -> ANSWERED/built/merged.
- **Token ledger:** appended; opus sub-agent share 0.0 (all sub-agents on Sonnet), no unit reached fix cycle 3.
- **T-126 closed** (adapter allowlist, SNAPSHOT drift, ledger backfill, QUEUE drift all met; done_check green).

## Non-findings confirmed, not re-filed

- **Bypass (all 103 commits):** every src/tests/scripts commit traces to a manifest -> matching-cycle PASS
  verdict (t172 c2, at110 c2, at560, t173, at086-087, t175, d042-registration, t170, fix-t175-criticality)
  or is a scoped chore/docs/goal/merge commit. CLEAN.
- **Pair state:** no ready-for-check manifest without a verdict; building worktrees (at335, at562-564,
  t125-catalog) correctly have no manifest yet. `.last-tick` fresh, not paused.
- **Delegation:** every window manifest is `claude-sonnet-subagent`; no (task_class, executor) reaches the
  10-unit quarantine floor.
- **Data boundary:** exit 1 = the accepted AT-365 `data_class` signal (No-fire list); no new real-data file.
- **Enforcement:** all 5 hooks in `.claude/settings.json` exist and are D-037-authorized; `qa/loop.md` Stop
  lists the seven terminal states. Loop-design "can it Goodhart the verifier": yes, already evidenced by
  AT-562/AT-564/F-045 (unit-level PASS, feature not user-reachable) — the proposed remedy is an orchestrator
  contract OR7 "reachable from a real entry point (CLI command or UI route), not test-only"; a contract
  criterion needs an authorizing D-entry, so it is PROPOSED here, not applied.
- **Goal drift:** no `.regrill-due`; north star not edited after the last contract amendment; every
  STALLED stamp has its `qa/debug/` report; no gate answered off-disk this window.
