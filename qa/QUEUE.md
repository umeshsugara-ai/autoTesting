# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-10T07:14:00+05:30**; bound strictly to
`D:/autoTesting`. Sweep window: `dab532b..3ac043f` (27 commits).

## Reconciliation

- **T-160 cycle 2 is clean:** manifest `checked-PASS`, verdict `PASS`, cycle 2 matches, goal row
  is `done`, and the generated dashboard reports 32/55 done, 23 pending, 58%.
- **Handshake clean:** 102 manifests / 104 verdict files; zero `ready-for-check`, zero missing
  verdicts, zero PASS-with-unclosed-manifest. The two verdict-only files are deliberate campaign /
  live-release checks. The old AT-226 concurrent PASS/FAIL split is closed by the separate
  `at226-already-authenticated-crawl-at274-fix` PASS; it is not a dangling fix cycle.
- **Bypass detection clean:** every source-bearing change in the window is covered by the later
  AT-276, AT-277, AT-278, T-134 or T-160 manifest/verdict chain.
- **Baseline:** full suite passed with a repo-local cache/basetemp; Ruff passed. The literal adapter
  commands are not executable in this managed runtime without those flags (AT-282), and doctor is
  red only because the required project-level `AGENTS.md` is rejected as root clutter (AT-283).
- **Maker liveness:** `qa/.last-tick` is 14.4 hours old, no `qa/.paused`, while 23 goal tasks and
  79 ledger issues remained open when the sweep began (AT-280).

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered across 7+ sweeps (AT-218).
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (bugs found, false-positive
  ceiling, branch coverage and time), then let checker contracts encode them — the north star moved
  after the last contract amendment and a future test file alone can otherwise Goodhart completion
  (AT-281).

## HUMAN_GATE — do not build as ordinary units

- **AT-110:** choose consent-forgery posture (HMAC / audit line / accident-detection only).
- **AT-147:** choose start-of-day vs end-of-day approval expiry semantics.
- **AT-253:** wire model fallback into execution, correct the architecture claim, or defer.
- **ERP credentials:** T-122 and T-145 remain gated on a test account entered through the UI;
  never use Karun's or another real user's account. The old T-136 model-key gate is answered and
  is not a current human gate.

## TOP-3 BUILDABLE NEXT UNITS

1. **T-100 — re-close the no-CLI UI through a real independent browser.** It is already reopened
   and directly blocks T-161. Fold the live UI findings it owns (AT-244/245/247/251/252/257/259),
   then require Mode D evidence rather than another narrow `tests/test_ui.py` claim.

2. **AT-227 — dismiss or safely route around first-paint in-page modals during BFS.** This is the
   oldest open high-severity crawl stopper and sits on the T-165 completeness path. Native-dialog
   handling does not cover DOM modals.

3. **T-135 — reconnect coverage → FlowSpec merge → expansion.** T-134 is now done, so this unit is
   buildable and is a direct prerequisite of the learn-or-explore orchestrator T-163. Preserve
   reviewed truth and make every unknown screen/video request visible.

Next governance unblock after those: **T-126**, carrying AT-282/AT-283 plus the older fixed-ledger
backlog. Fixed rows still awaiting an issue-specific later re-check: AT-207/208/219/220/221/222/
223/225/228/230/250/254/264/269/272/276/277/278/279.

## Revised-goal coverage

- Intake: partial now, owned by T-161.
- Multi-source learning: video exists; Drive/audio/document/email/text missing, owned by T-162.
- Learn-or-explore orchestration: stages exist separately; unified resumable coordinator missing,
  owned by T-163.
- Portal Persona: missing, owned by T-164.
- BFS/frontier/API completeness: partial crawler exists; forward/back/network completeness missing,
  owned by T-165.
- Traceable best/worst/edge compiler: partial expansion exists; provenance matrix missing, T-166.
- Release-triggered regression: missing, T-167.
- Unified damage-control report: partial HTML/XLSX exists; cross-layer diff missing, T-168.
- Two-mode real acceptance: missing and threshold-gated by AT-281, T-169.

Terminal state: **FINDINGS: 4** (AT-280..AT-283); existing GRILL AT-218 carried.
