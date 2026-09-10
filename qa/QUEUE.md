# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-10T10:56:00+05:30**; bound strictly to
`D:/autoTesting`. Sweep window: `3ac043f..912aa12` (6 commits).

## Reconciliation

- **T-100 cycle 1 is clean:** implementation `c1f7cc0`, independent checker PASS `7ae89d6`,
  maker close-out `912aa12`; manifest `checked-PASS`, matching cycle, goal row `done`, and the
  dashboard/goal state reports 33/55 done and 22 pending. Its nine owned issues are `fixed` and
  remain for a later issue-specific re-check before `verified`.
- **Handshake clean:** 103 manifests / 105 verdict files; zero live `ready-for-check`, zero
  missing current-cycle verdicts, and zero PASS-with-unclosed manifests. The two verdict-only
  files remain deliberate campaign/live-release checks.
- **Bypass detection clean:** the only source-bearing commit in the window is T-100's `c1f7cc0`,
  covered by its manifest, tightened contracts, matching-cycle verdict, and close-out. The other
  commits are checker queue, manifest, contract, verdict/evidence, and maker close-out records.
- **Baseline:** the literal adapter commands still fail before their instruments run because the
  managed runtime cannot access the default uv cache (AT-282). With the documented repo-local
  cache/basetemp workaround, the full suite passed at 100% with 2 skips and Ruff passed. Doctor
  remains red only because it rejects the active untracked root `AGENTS.md` (AT-283).
- **Maker liveness remains open:** `qa/.last-tick` is 1089 minutes old, `qa/.paused` is absent,
  22 goal tasks and 74 ledger issues remain open, and the real SessionStart hook again emitted
  `AUTO-CONTINUE REQUIRED` (AT-280).

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218).
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (bugs found,
  false-positive ceiling, branch coverage and time), then let checker contracts encode them
  (AT-281).

## HUMAN_GATE — do not build as ordinary units

- **AT-110:** choose consent-forgery posture (HMAC / audit line / accident-detection only).
- **AT-147:** choose start-of-day vs end-of-day approval expiry semantics.
- **AT-253:** wire model fallback into execution, correct the architecture claim, or defer.
- **ERP credentials:** T-122 and T-145 remain gated on a test account entered through the UI;
  never use a live user's account. The T-136 model-key gate is answered and is not current.

## TOP-3 BUILDABLE NEXT UNITS

1. **T-161 — unified no-CLI project intake.** T-100 and T-160 are now both done, so this
   CRITICAL, high-user-value unit is newly unblocked. Keep credentials as domain-scoped
   `SecretRef`s and accept URL, evals, conditions, use cases, and source declarations through one
   operator-facing flow.

2. **T-135 — reconnect coverage → FlowSpec merge → expansion.** T-134 is done and this CRITICAL
   unit is the remaining prerequisite for the resumable learn-or-explore orchestrator T-163.
   Preserve reviewed truth and surface every unresolved screen/video request.

3. **AT-227 — handle first-paint in-page modals during BFS.** This is the oldest open high-severity
   crawl stopper and sits directly on T-165's completeness path. Native-dialog handling does not
   cover DOM modals.

Next governance unit: **T-126**, carrying AT-282/AT-283 and the older fixed-ledger backlog. Mode-D
retrospective debt AT-243 remains open: T-100 is the first compliant re-check, not evidence for all
historic UI PASSes.

## Revised-goal coverage

- Intake: partial, owned by newly unblocked T-161.
- Multi-source learning: video exists; Drive/audio/document/email/text missing, owned by T-162.
- Learn-or-explore orchestration: stages exist separately; unified resumable coordinator missing,
  owned by T-163 and dependent on T-135/T-162.
- Portal Persona: missing, owned by T-164.
- BFS/frontier/API completeness: partial crawler exists; first-paint modal recovery remains AT-227,
  with forward/back/network completeness owned by T-165.
- Traceable best/worst/edge compiler: partial expansion exists; provenance matrix missing, T-166.
- Release-triggered regression: missing, T-167.
- Unified damage-control report: partial HTML/XLSX exists; cross-layer diff missing, T-168.
- Two-mode real acceptance: missing and threshold-gated by AT-281, T-169.

Terminal state: **FINDINGS: 4** (AT-280..AT-283 persist; no new issue id); existing GRILL AT-218
and systemic Mode-D debt AT-243 carried.
