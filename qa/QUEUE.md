# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-11T13:45:00+05:30**; bound strictly to
`D:/autoTesting`. Sweep window: `7a8d966..eb75e61` (~63 commits, 21 source-bearing). Supersedes
the 2026-09-11T01:20 queue: **T-135 landed (dual-check PASS cycle 3) and AT-227 landed
(concurrent-checker PASS cycle 1) — neither is buildable anymore.**

## Reconciliation

- **Massive window, clean handshake.** 119 manifests / 122 verdicts (2 deliberate verdict-only
  campaign/live-release files + 1 `.b.md` dual-check for `t135-coverage-merge-expand`, same as
  every prior sweep). Exactly **one** manifest is not `checked-PASS`:
  `at345-346-fold-coverage.md`, at `ready-for-check`, fix cycle 3 of 3 (the last one), verdict on
  disk carries only cycles 1 and 2 (both FAIL). This is **disclosed, in-flight work** (the maker's
  own dispatch note at `.last-tick` 07:20:36Z names it as the third and final cycle, submitted as
  commit `eb75e61`) — not a dispatch gap, not a bypass.
- **Bypass detection, 21 source-bearing commits, CLEAN.** 19 map directly to a manifest
  (`at102`, `at339`, `at076` ×2, `at079-080`, `at345-346` ×2, `at324`, `at311` ×3, `at298`,
  `at300`, `at283`, `t135` — its fix commit `cc00e9b` inside the same unit whose manifest landed
  in a sibling commit). The two that don't:
  - `d21440c` (`feat(coverage): close the self-extension loop`, T-135 cycle-2 fix) is inside the
    T-135 unit's own history (between "submit cycle 2" `191be93` and its cycle-3 PASS) — commit
    granularity, not a bypass.
  - `508d164` (`fix(AT-338)`, one-line schema docstring correction, doc-only, no behaviour
    change) landed without its own manifest. Disclosed honestly in the commit body ("found by the
    second independent checker on at227, not by me"). Judged **acceptable trivial-mode work**
    under this project's own CLAUDE.md ("typo, single command, read-only → normal mode, no
    ceremony") — a docstring correction with no behaviour change is the same class. **Independently
    re-verified by this sweep**: `structural_signature()` (`stages/screen_identity.py`) still
    filters on `el.visible and not el.in_row` only (obscured NOT excluded), matching the corrected
    schema description exactly. AT-338 promoted `fixed → verified`.
- **AT-283 also independently re-verified and promoted `fixed → verified`:** `uv run autotester
  doctor` → **clean, exit 0**, no root-`AGENTS.md` violation. This sweep's own doctor run (not a
  pasted claim) confirms the fix.
- **Baseline, green:** `uv run pytest -q` → full suite, exit 0, 2 skipped, 0 failed. `uv run ruff
  check src tests scripts` → exit 0, "All checks passed!". `uv run autotester doctor` → clean.
- **Fixed-ledger backlog: 55 rows (was 11 at the last sweep), NOT independently re-derived this
  sweep beyond AT-338/AT-283.** This is the same shape flagged by 5+ consecutive prior sweeps
  ("next sweep's first job") — this sweep chose breadth (bypass/handshake/gates/goal coverage
  across a 63-commit window) over re-deriving 55 fixed claims by sabotage, which would have
  consumed the whole budget on one channel. **Disclosed as a persistence flag, not a new finding.**
  The backlog is concentrated in the mutation-check tooling chain (AT-207/208/219-223/228,
  AT-298b/300-304/306/307/320-325) and the credential-guard chain (AT-076/079/080/102/339). Every
  row in the credential-guard and at345-346 chains already carries a matching-cycle checker PASS
  with its own sabotage/mutation evidence in the verdict — re-deriving them is lower-value than
  the still-untouched older rows.
- **No reopens.** Nothing this sweep proved unbacked by evidence.
- **Inbox clean:** all entries folded (checked 2026-09-09 flaky-test entry and 2026-09-10 T-100
  entry, both `FOLDED` with commit references; nothing new since).
- **Contract staleness:** none new found this window.
- **Enforcement liveness, confirmed by execution:** `.claude/settings.json` carries `SessionStart`
  / `PreToolUse` / `SessionEnd` hooks; repo at **661 commits**; `docs/DECISIONS.md` has **26**
  entries (non-empty, alive); doctor/ruff/pytest all ran clean under this session's own start.
- **Silent-failure hunt over the window's `src/` diff:** the four new `except Exception as exc`
  blocks (`explore.py::return_to`/`_replay_discovery`/`_recover`) all name the exception type and
  message and propagate it into `rt.return_error` / a typed return — none swallow. No new finding.
- **Goal coverage: 35/55 done, 20 pending** (was 34/55). T-135 closing moved it by one. No drift —
  matches disk exactly.
- **Gates reconciled:**
  - `next-unit-scope.md` **is answered** (2026-09-11, Option C then B — Umesh, in conversation).
    Option C (AT-227) is now closed. Option B (T-163) is correctly still blocked, because its own
    declared prerequisite T-162 has no contract.
  - `t162-contract-approval.md` genuinely unanswered — real, current HUMAN_GATE, correctly not
    idling anything else (the maker worked 10+ smaller open-issue units instead, exactly as the
    gate's own "What is NOT blocked" section said it would).
  - `at110-approval-forgery.md`, `at147-expiry-end-of-day.md` (empty `**Answered:**` stub),
    `at253-agent-fallback-wiring.md`, `erp-credentials.md`, `t135-url-pattern-data-migration.md`
    (superseded in substance by cycle-3 evidence but never formally answered) — all still
    genuinely open, no off-disk answer found in this window's 63 commits.
  - `at218-vacuous-guard-class.md` GRILL — still open, no `/grill` run against it. Now the **6th+**
    consecutive sweep carrying it unchanged.
  - `t136-model-credentials.md` — answered but self-contradicting (AT-285, carried, unchanged).

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), 6th+ consecutive sweep.
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.

## HUMAN_GATE — do not build as ordinary units

- **T-162 contract approval** (`qa/gates/t162-contract-approval.md`, NEW since last sweep):
  Umesh picks Option A (interview now) / B (CTO-brief HLD first) / C (different next unit) / D
  (pause). Blocks T-162 and therefore T-163.
- **AT-110:** consent-forgery posture. Still no `Answered:` line.
- **AT-147:** start-of-day vs end-of-day expiry. `Answered:` line is an empty stub.
- **AT-253:** wire model fallback, correct the ARCHITECTURE claim, or defer.
- **ERP credentials:** T-122/T-145 gated on a test account entered through the UI.
- *Not current:* T-136 model-key gate is answered; its stale contradictory stub is AT-285.

## TOP-3 BUILDABLE NEXT UNITS (non-gated)

1. **AT-335 (high) — the modal crawl is non-deterministic**, ~1 run in 14 loses the
   dismissed-dashboard screen after a modal closes. Freshly relevant: lands right after AT-227
   (first-paint modal handling) just closed, and is the next real crawl-completeness defect on
   T-165's path, no gate.
2. **Fixed-ledger reconciliation** — re-derive a batch of the 55 `fixed` rows by sabotage,
   starting with the oldest untouched cohort (AT-207/208/219-223/228), promoting what holds and
   reopening what doesn't. Flagged by 5 consecutive sweeps as "next sweep's first job"; this
   sweep again did not clear it (see Reconciliation above) — pure checker/governance work, no
   gate, buildable by a sweep immediately.
3. **AT-243 (high) — Mode D systemic debt.** Shrinking (T-100-reclose, T-161, several
   concurrent-checker units now carry real `LIVE-BROWSER:` evidence) but still open; the historic
   UI-PASS backlog before that point has no retroactive live-browser evidence.

Separately, **answering `qa/gates/t162-contract-approval.md`** unblocks the largest single slice
of value (T-162 → T-163, both `criticality: critical`) — not a "unit" but the highest-leverage
single action available.

## Revised-goal coverage

- Intake: covered (T-161).
- Multi-source learning: partial — video only; T-162 gated on contract approval.
- Learn-or-explore orchestration: T-135 done; T-163 blocked on T-162.
- Portal Persona: missing, T-164.
- BFS/frontier/API completeness: partial; AT-227 (first-paint modal) closed this window; AT-335
  (modal non-determinism) is the next crawl-completeness defect; forward/back/network completeness
  still T-165.
- Traceable best/worst/edge compiler: partial, T-166.
- Release-triggered regression: missing, T-167.
- Unified damage-control report: partial, T-168.
- Two-mode real acceptance: missing, threshold-gated by AT-281, T-169.

Terminal state: **FINDINGS: 0 new** — every channel checked this sweep (bypass, handshake,
inbox, contract staleness, enforcement, goal coverage, gates, silent-failure) came back clean or
matched a previously-disclosed, still-accurate carried item (AT-218, AT-281, AT-285, AT-243, the
fixed-ledger backlog, the t162 gate). Two ledger promotions made (AT-338, AT-283:
`fixed → verified`, independently re-derived). No reopens. Ledger after this sweep: 202 verified /
90 open (6 high, 27 medium, 57 low) / 55 fixed / 2 wontfix / 2 dismissed.
