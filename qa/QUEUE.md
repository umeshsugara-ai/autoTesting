# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-17T10:10:48+05:30**. The stamp comes from the system clock
(`date`), not typed (AT-399). Bound strictly to `D:/autoTesting`. Window since `2026-09-16T22:45:24+05:30`
is 34 commits, `d5335e4..562a80c`. Supersedes the 22:44 queue.

## Standing priority — Umesh, 2026-09-16T22:25+05:30 (folded as X17, X18, V7)

> "puura product map hona chiaye na aend to end testing . each possible route"

Progress against it: **X17 closed** (AT-457: 219556e, PASS 4472a0d). **X18 closed** (AT-458:
9d5775d, PASS cycle 3 at 8e2c216). **V7 in flight** (AT-459, fix cycle 2, its re-dispatched checker is
running; not a gap and not re-assigned). Its cycle-1 findings AT-470/471/472 belong to that unit.

## Findings — FINDINGS: 2 (+ 1 gate opened)

| Issue | Sev | What |
|---|---|---|
| **AT-474** | **high** | silent-failure. `explore_status.observed_signature` (`:54-57`) turns any exception into `None` without a log. X18(a) is then silently not judged, and a crawl stuck at login reads COMPLETED. Nothing in the crawl or the report says the check was skipped. |
| AT-475 | medium | Ledger hygiene. 10 ledger rows (AT-446/452/455/456/462/463/467/470/471/472) and 6 status flips exist only in the uncommitted working tree, although their verdicts are committed (1929e83, 4472a0d, 8e2c216, abbcc58). Not fixed here: those are other sessions' hunks. |

**Gate opened:** `qa/gates/post-login-forms.md`. X10 and D-016 forbid all typing, so post-login forms
are a CRITICAL human decision. It had lived only in an inbox fold note.

## Checks

1. **Bypass + handshake.** Every source commit in the window maps to a manifest and a verdict.
   at455 (d5335e4), at457, at419, at461, at458, at216 and at465-466 are all `checked-PASS` and closed out.
   `f7e83cd` and `ee98728` (AT-469 cycles 1 and 2) are on master before their verdicts: cycle 1 FAILed,
   and cycle 2 is `ready-for-check` with its checker dispatched at 04:10Z. That unit belongs to the other
   session and falls under `commit-before-verdict`, so it is **not re-ruled**. at459 is `ready-for-check`
   cycle 2 with its checker running, so it is not a gap. Stalled units (at015, at345-346, at379, at438)
   are unchanged and carried.
2. **Inbox:** no unfolded entries since the 22:25 fold.
3. **Contract staleness:** AT-467 shows that X18(a) under-fires, and it needs a routine tightening
   (below). That is not a staleness prune.
4. **Enforcement liveness: LIVE.** The last tick was 2026-09-17T04:40:43Z, fresh at sweep time. There is
   no `qa/.paused`. 4b data boundary: exit 1, `data_class` absent. That is already the open gate AT-365,
   so it was not re-filed.
5. **Goal coverage:** "each possible route" is **partial**. Click-reachable post-login screens are now
   covered by X17, X18 and V7 (pending). Form-gated screens are **missing** by X10, and only a human can
   source that, hence the gate. No product has a known route inventory to measure coverage against
   (proposal, unit 2).
6. **Goal-drift:** no gate was answered off-disk (grepped the 34 commit bodies and the gate files).
   No new GRILL.
7. **Silent-failure hunt** over the PASSed diffs: AT-474. doctor's `except UnicodeDecodeError` skip is
   disclosed in at419 and was verified by its checker, so it is not filed.
9. **Structural erosion:** `explore.py` is still at 300 lines (AT-460). `explore_node.py` is 245 lines
   plus at459's uncommitted edit. Signal only.
- pytest was not run: two other sessions have uncommitted src/tests edits (at459 working tree), so a red
  test could not be attributed.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy (AT-218). Unanswered, carried.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281). Carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js`. Carried.

## HUMAN_GATE — do not build as ordinary units (verified unanswered on disk)

| Gate | Blocks |
|---|---|
| `live-crawl-target.md` | The live post-login acceptance run of X17/X18/V7 (target, write_policy, bounds). |
| **`post-login-forms.md`** (NEW) | Any crawler typing, selecting or uploading after login (X10, D-016). |
| `t162-contract-approval.md` | T-162…T-169 |
| `at438-u14b-baseline.md`, `commit-before-verdict.md` | Other session's AT-438; protocol departure. |
| `at416-clip-vs-reach-direction.md`, `at383-loop-status-consumer.md`, `at365-data-class-declaration.md` | Various |
| `at110-approval-forgery.md`, `erp-credentials.md`, `at147`, `at218`, `at253`, `t136-model-credentials.md` | Various |

## TOP-3 BUILDABLE NEXT UNITS (post-login end-to-end mapping; local fixtures, no live target)

Start all three only **after at459 closes**. They touch `explore_node.py`, `explore_status.py` and the
report, which the at459 working tree is editing now.

| # | Unit | Contract | Why |
|---|---|---|---|
| **1** | **A bound that fires mid-node on the last queued screen names itself** (AT-463). The per-action bound check in `visit_node` (`explore_node.py:221`) sets `rt.stop_reason`, so a crawl that ran out of actions reads `stopped_bound`, not "frontier empty"/COMPLETED. Add one test per bound. | `explore.md` **X4** (already failing) | This bug is in the reach number itself. With it, V7's coverage figure and X18's wall check can both be judged on a crawl that silently stopped. The checker's probe hit it with `max_actions=1` on a login-shaped page. |
| **2** | **Known-inventory post-login fixture: the product map is measured against ground truth.** A local fixture app has a login plus N declared routes: nav menu, hash route, nested page, paginated list, a screen behind a click-opened drawer, and one form-gated screen. A UI-started crawl with the login case must reach every click-reachable route. V7 lists each miss with its reason, and the form-gated one as `policy`. | proposed `coverage.md` **V8** (checker adds it as a routine criterion when the maker picks the unit) | Proves "each possible route" measurably without a live target. Today nothing checks the crawl's reached set against what actually exists. The misses it surfaces become the next units. |
| **3** | **X18(a) is honest in both directions** (AT-467 + AT-474). (a) A failed login that leaves a sticky banner or Dismiss control is still LOGIN_FAILED. (b) If the login page cannot be observed, the crawl says X18(a) was not judged, and the verdict is not an unqualified COMPLETED. | `explore.md` **X18(a)**. AT-467 first needs a routine tightening by the checker, for example: "no reached node leaves the login template AND the login case's fill targets are still present". The maker proposes it in the manifest, and the checker folds it before the build. | The green badge is what Umesh reads. Both issues make a crawl that never got past login look like a success. |

**After these:** the live run behind `live-crawl-target.md`, then whatever `post-login-forms.md` decides.
**Deprioritised (not cancelled):** AT-460 extraction (do it inside unit 1 or 3 if `explore.py` must grow),
AT-464, AT-468, AT-475 (the owning sessions should commit their ledger hunks), AT-456, and other
≤medium UI polish.

**Explicitly NOT assigned:** at459 (cycle 2, checker running) · at469 (other session, cycle 2
pending) · at438 / AT-442…AT-454 (other session, STALLED + gate) · anything under `.goal/`,
`.codex/`, `AGENTS.md`, untracked `projects/*`.

## Unpushed local commits (origin/master = 7252f47; 8 ahead)

With no checker PASS: **`f7e83cd`** (AT-469 cycle 1, verdict FAIL 2894f4e; its AT-473 false-KILLED
defect in `scripts/mutation_check.py` is live at HEAD) and **`ee98728`** (AT-469 cycle 2, no verdict yet).
The other six are paperwork: `eb909eb`/`562a80c`/`730ca05` are tick stamps, `2894f4e`/`abbcc58` are FAIL
verdicts, and `700f0be` is the at465-466 close-out of PASS 7252f47, which is already on origin.

**Terminal state: `FINDINGS: 2`** (AT-474 high, AT-475 medium; 1 gate opened: post-login-forms).
