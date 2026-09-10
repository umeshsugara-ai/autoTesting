# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-11T01:20:00+05:30**; bound strictly to
`D:/autoTesting`. Sweep window: `714348f..7a8d966` (8 commits). Supersedes the
2026-09-10T10:56 queue, whose top-3 is now stale: **T-161 is built, FAILed cycle 1, fixed,
PASSed cycle 2 and closed out — it is no longer a buildable unit.**

## Reconciliation

- **T-161 cycle 2 is clean and closed:** implementation `4c09990` + fix `d92af87`, cycle-1 FAIL
  `dfc5a03`, resubmit `ad755a4`, cycle-2 PASS `7381983` (22/22 criteria, 9/9 invariants, two
  independent checkers, fresh headed-browser attacks), goal close-out `7a8d966`. Manifest is
  `checked-PASS` at fix cycle 2 and the verdict's `Cycle checked: 2` matches. AT-284 (pre-guard
  hostname-secret echo) is `fixed`. Goal moved 33/55 → **34/55 done, 21 pending**.
- **The concurrent AT-278/AT-279 session LANDED — it was neither abandoned nor left uncommitted.**
  The 2026-09-09T11:16Z tick recorded the maker backing off rather than racing a live, uncommitted
  fix in the same two files. That work is now fully on disk and in history: `cbdfab1`
  (fix AT-278/AT-279) → `b848201` (resubmit cycle 2) → `44a7e84` (checker PASS cycle 2) →
  `7682c4c` (close-out). All four are ancestors of HEAD; the manifest reads
  `## Status: checked-PASS (cycle 2, verdict 44a7e84)`; the verdict file carries two independent
  cycle-1 FAILs followed by the cycle-2 PASS; both ledger rows are `fixed`. `git status` shows
  **no modified file under `src/` or `tests/`** — nothing from that session remains uncommitted.
  The stale `qa/.last-tick` is a maker-liveness problem (AT-280), not lost work.
- **Handshake clean:** 104 manifests / 106 verdict files; **every** manifest is `checked-PASS`;
  zero live `ready-for-check`, zero missing current-cycle verdicts, zero PASS-with-unclosed
  manifests. The two verdict-only files remain the deliberate campaign/live-release checks.
- **Bypass detection clean:** the only source-bearing commits in the window are `4c09990` and
  `d92af87`, both covered by the T-161 manifest, the tightened contracts, a matching-cycle verdict
  and a close-out. The other six commits are manifest, contract, verdict, browser-evidence and
  goal/docs records. `4c09990`'s `docs/DECISIONS.md` entry is **D-025** (supersedes D-024) with
  `Approved-by: Umesh` and a `Changes-authorized` list that covers every source file it touched —
  Lab Protocol authorization is intact.
- **Baseline re-derived by this checker, green:**
  `uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-sweep-0911 -q`
  → **exit 0, 100%**; `uv --cache-dir .work/uv-cache run ruff check src tests scripts` → exit 0,
  `All checks passed!`; `uv --cache-dir .work/uv-cache run autotester doctor` → exit 1 with
  **one** violation, the untracked root `AGENTS.md` (AT-283).
- **AT-282 does not reproduce and is closed `wontfix`.** This sweep ran the *literal* adapter
  commands: `uv run ruff check src tests scripts` → exit 0; `uv run autotester doctor` → exit 1
  reporting only AT-283, i.e. the instrument ran; `uv run pytest -q --collect-only` → exit 0. The
  default uv cache was reachable here, so the blocked-cache condition belongs to one managed
  checker sandbox, not to this repo, and the project has no fix to make. Recorded as closed with
  the non-reproduction rather than left open to be re-flagged every sweep. A future sweep runtime
  that hits it again files a fresh id.
- **Inbox clean:** the newest entry (2026-09-10, T-100 real-browser re-close) is marked FOLDED
  into `ui.md` U11 and `ui-report.md` UR5–UR6 at `7d4c848`. T-161's contract-maintenance request
  was folded in-cycle by the cycle-1 checker (`dfc5a03` amended `ui.md`, `browser-and-secrets.md`
  and `core-invariants.md`), and the cycle-2 verdict scores against the tightened U1–U12 / B1–B10 /
  C1–C9 — nothing weakened. No unfolded actionable entry remains; the older unfolded rows are the
  documented deliberate/external ones.
- **Contract staleness:** none new. No criterion references a removed feature, and U12/B10/C5 are
  the newest amendments rather than a contradiction of anything older.
- **Enforcement liveness:** `settings.json` carries the `mc-sessionstart` / `mc-precommit` hooks
  plus the Lab-Protocol session hooks and the DECISIONS append guard; `qa/hooks/` and
  `.claude/hooks/` both hold the referenced scripts; the repo has **581 commits**; `qa/loop.md`
  lists all seven terminal states with a real progress signal. Loop-design: it cannot spin, but
  it **can still Goodhart / run a wrong answer to completion on T-169**, because no human
  acceptance floor exists — that is AT-281, unchanged.
- **Silent-failure hunt** over the T-161 source diff (`schema/enums.py`, `ui/app.py`,
  `ui/env_editor.py`, `ui/project_view.py`, `ui/routes_project_edit.py`, `ui/routes_sources.py`):
  **no new finding.** The new `except BaseException` in `env_editor.set_env_values` closes the
  stray fd, unlinks the temp file and **re-raises**; the `InvalidEnvValue` / `ValidationError` /
  `ValueError` handlers all surface a refusal to the caller; no default-value fallback masks a
  failure.
- **Maker liveness remains the standing failure:** `qa/.last-tick` is **~1945 minutes (32.4 h)
  stale**, `qa/.paused` is absent, and the backlog is non-empty (21 pending goal tasks, 74 open
  ledger issues). AT-280 persists and is now worse than at the last sweep.
- **Working tree:** modified `.goal/dashboard.html`, `.goal/goal.json`, `qa/.last-tick`; untracked
  `.codex/`, root `AGENTS.md` (AT-283), `projects/{checkerdemo,saucedemo,xssprobe,t161-final-smoke,t161-pushed-live}/`
  and several `projects/{erp,pathlynks}` run artifacts. All are runtime/scratch output, not
  unlanded source. This sweep committed with a narrow pathspec only.
- **Mode-D debt (AT-243) is shrinking, not closed:** T-100-reclose and now T-161 are the first two
  units with genuine independent `LIVE-BROWSER:` evidence. They are not retroactive evidence for
  the historic UI PASSes; AT-243 stays open.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218).
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (bugs found, false-positive
  ceiling, branch coverage and time), then let checker contracts encode them (AT-281).

## HUMAN_GATE — do not build as ordinary units

- **AT-110:** choose consent-forgery posture (HMAC / audit line / accident-detection only).
  `qa/gates/at110-approval-forgery.md` still has no `Answered:` line at all.
- **AT-147:** choose start-of-day vs end-of-day approval expiry semantics. The gate file's
  `**Answered:**` line at `qa/gates/at147-expiry-end-of-day.md:67` is an **empty stub** — the
  three options (A keep / B move / C end-of-day for new grants only, the checker's recommendation)
  are on disk, the decision is not. No commit, manifest or verdict in the window answers it
  off-disk.
- **AT-253:** wire model fallback into execution, correct the architecture claim, or defer.
- **ERP credentials:** T-122 and T-145 remain gated on a test account entered through the UI;
  never use a live user's account.
- *Not current:* the T-136 model-key gate **is answered** (2026-09-09, "the gate was wrong — the
  credentials were already in `.env`"). Its file still carries a contradictory stale
  `**Answered:** _(pending)_` line above the real answer — filed this sweep as **AT-285** (low).

## TOP-3 BUILDABLE NEXT UNITS

1. **T-135 — reconnect coverage → FlowSpec merge → expansion.** CRITICAL, unblocked (T-134 done),
   and the remaining prerequisite for the resumable learn-or-explore orchestrator T-163. Preserve
   reviewed truth and surface every unresolved screen/video request. Promoted from #2 now that
   T-161 has closed.

2. **T-162 — multi-source adapters: Google Drive, video, audio, document, email and text.**
   Newly the largest uncovered slice of the D-023 north star: T-161 now accepts every source
   *declaration* through one form, but only video is actually ingested, so the intake promise
   currently outruns the pipeline. It is the second prerequisite for T-163 alongside T-135, and it
   is buildable today with no human gate.

3. **AT-227 — handle first-paint in-page modals during BFS.** The oldest open high-severity crawl
   stopper, sitting directly on T-165's completeness path. Native-dialog handling does not cover
   DOM modals.

Next governance unit: **T-126**, now carrying AT-283 and AT-285 plus the older fixed-ledger backlog
(AT-282 is closed and drops off it). Deferred-with-cause: AT-110/AT-147/AT-253 are gate-blocked,
T-122/T-145 are credential-gated, T-169 is threshold-gated behind AT-281.

## Revised-goal coverage

- Intake: **covered** — T-161 closed with independent Mode-D evidence (was `partial`).
- Multi-source learning: partial — video exists; Drive/audio/document/email/text missing, owned by
  T-162. Widened by T-161: declarations are now accepted for sources nothing can yet ingest.
- Learn-or-explore orchestration: stages exist separately; unified resumable coordinator missing,
  owned by T-163 and dependent on T-135 + T-162.
- Portal Persona: missing, owned by T-164.
- BFS/frontier/API completeness: partial crawler exists; first-paint modal recovery remains AT-227,
  with forward/back/network completeness owned by T-165.
- Traceable best/worst/edge compiler: partial expansion exists; provenance matrix missing, T-166.
- Release-triggered regression: missing, T-167.
- Unified damage-control report: partial HTML/XLSX exists; cross-layer diff missing, T-168.
- Two-mode real acceptance: missing and threshold-gated by AT-281, T-169.

Terminal state: **FINDINGS: 4** — AT-280 (high, maker asleep, worse), AT-281 (high, GRILL),
AT-283 (medium, doctor vs root `AGENTS.md`, reproduced), AT-285 (low, new: self-contradicting
T-136 gate file). AT-282 closed `wontfix` (did not reproduce). GRILL AT-218 and systemic Mode-D
debt AT-243 carried. No reopens: nothing this sweep proved a claim unbacked by evidence.
