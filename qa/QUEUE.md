# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-16T22:44:50+05:30** — stamp from the system clock (`date`),
not typed (AT-399). Bound strictly to `D:/autoTesting`. Sixth Mode B sweep of 2026-09-16; window since
`2026-09-16T18:15:32+05:30` = 21 commits `ba30b71..ec92abc`. Supersedes the 18:14 queue.

## PRIORITY CHANGE — from Umesh, 2026-09-16T22:25+05:30 (verbatim in `qa/feedback-inbox.md`)

> "abhi tho hmara testing flow login k baad hi ruk jata hi, what the kind of testing you are really
> doing. system relaible kese bnega. puura product map hona chiaye na aend to end testing . each possible route"

Re-derived by this checker (code + crawl.json counts only): every crawl on disk stops at or before
login; the UI cannot pass a login at all; nothing reports coverage. The last 8 units (AT-430…AT-455)
were small AutoTester-UI defects and moved none of this. **Until the three units below close, small
UI polish is not TOP-3 work.** Folded as `explore.md` X17, X18 and `coverage.md` V7.

## Findings — FINDINGS: 4 (+ 1 inbox entry folded)

| Issue | Sev | What |
|---|---|---|
| **AT-457** | **high** | UI Explore (`routes_crawls.py:226-227`) calls `run_crawl` with no `login_case`, and `Project` has no field declaring one — no UI-started crawl can ever pass a login wall. → X17 |
| **AT-458** | **high** | `_terminal_status` (`explore.py:200-211`) returns COMPLETED for a wall-only crawl whenever ≥1 action ran; the 3 legacy wall crawls (saucedemo, checkerdemo ×2: 1 screen / 0 actions / 3 denied) still read `completed` (they predate AT-242). → X18 |
| **AT-459** | **high** | No coverage figure anywhere; controls left by a bound or on unvisited queued screens are not listed with a reason. → V7 |
| AT-460 | medium | SIGNAL (check 9): `stages/explore.py` is at exactly 300 lines; X17/X18/V7 must extract, not squeeze. |

**Maker's evidence, one claim corrected:** "a crawl that ends on the login page reports COMPLETED" is
true of the on-disk artifacts only because they predate `2bb3270` (AT-242); current code labels a
0-action wall crawl `blocked_no_actions`. The live defect is the ≥1-action path + legacy display.

## Checks

1. **Bypass + handshake.** Every source commit in the window maps to a manifest + verdict: at431,
   at434, at435, at446, at452 all `checked-PASS` and closed out. `ba30b71` / `9fc937d` are at438's
   cycle-2/3 code on master under FAIL verdicts — that is the other session's STALLED unit, covered by
   `at438-u14b-baseline` and `commit-before-verdict`; **not re-ruled**. `at455-other-project-grant-reason`
   is `ready-for-check` with its checker running now — not a gap, not re-assigned.
2. **Inbox** — 1 entry folded (above). Fully folded.
3. **Contract staleness** — explore.md's purpose ("usually logged-in browser") was not backed by any
   UI path; X17 closes that contradiction.
4. **Enforcement liveness — LIVE.** Maker last tick 16:41:29Z (~33 min at sweep start), no `qa/.paused`.
   4b. Data boundary — AT-365 gate still open, not re-filed.
5. **Goal coverage** — north star "AutoTester wins on bugs found" is **missing** for any product behind
   a login: 0 post-login screens mapped across all 4 projects. Sourced by the inbox entry → criteria, no GRILL.
6. **Goal-drift** — no gate answered off-disk (all 21 commit bodies grepped). at438 STALLED has its
   diagnosis (`qa/debug/at438-display-contents-cycle3.md`).
7. **Silent-failure hunt** over at431/434/435/446/452 diffs — clean (the one new `except OSError` exits 2 with a named message).
9. **Structural erosion** — AT-460 (above). `visual_order.js` carried under AT-402.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), carried.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js`, carried.

## HUMAN_GATE — do not build as ordinary units (verified unanswered on disk)

| Gate | Blocks |
|---|---|
| **`live-crawl-target.md`** (NEW) | the live post-login acceptance run of X17/X18/V7: which target (e.g. saucedemo.com's published demo login, Pathlynks test account, ERP), which `write_policy`, which bounds. Does NOT block building against fixtures. |
| `t162-contract-approval.md` | T-162…T-169 |
| `at438-u14b-baseline.md` | AT-438 close + AT-453 (other session) |
| `commit-before-verdict.md` | protocol departure |
| `at416-clip-vs-reach-direction.md`, `at383-loop-status-consumer.md`, `at365-data-class-declaration.md` | various |
| `at110-approval-forgery.md`, `erp-credentials.md`, `t135-url-pattern-data-migration.md`, `at147`, `at218`, `at253` | various |

## TOP-3 BUILDABLE NEXT UNITS (post-login end-to-end mapping; fixtures, no live target needed)

| # | Unit | Contract | Why |
|---|---|---|---|
| **1** | **UI Explore passes the project's login case** (AT-457) — one declared login case on `Project`, the Explore route passes it, `crawl.json.login_case_id` set, "no login case declared" notice otherwise | `explore.md` **X17** (a)(b)(c) | The door. Without it no product behind a login is ever mapped from the UI. Fixture with a login wall; falsifying edit = drop the kwarg; checker Mode D drives the form. |
| **2** | **A wall-only crawl is never COMPLETED** (AT-458) — new non-success status at any `actions_used`, on every X16 surface, legacy `completed` wall crawls displayed as non-success | `explore.md` **X18** (a)–(d) | Stops the report lying about reach, so unit 1's result is honestly judged. Extract `_terminal_status` out of the 300-line `explore.py` (AT-460). |
| **3** | **Product-map coverage figure + every unreached screen/control with one reason** (AT-459) | `coverage.md` **V7** (a)–(d) | The number Umesh asked for: "puura product map … each possible route". Books must balance (c). New tally module, not a larger `explore.py`. |

**After these:** the live run behind `live-crawl-target.md`. **Deprioritised (not cancelled):** AT-447
retroactive manifest, AT-401, AT-419, AT-456 and other ≤medium UI polish.

**Explicitly NOT assigned:** `at455-other-project-grant-reason` (checker running) · at438 / AT-442…AT-454
(other session, STALLED + gate) · anything under `.goal/`, `.codex/`, `AGENTS.md`, untracked `projects/*`.

**Terminal state: `FINDINGS: 4`** (AT-457/458/459 high, AT-460 medium; 1 inbox entry folded → X17, X18, V7; 1 gate opened).
