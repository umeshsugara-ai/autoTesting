# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-09T~16:00 IST (~10:30Z)** (bound to `D:/autoTesting`).
Prior sweep 2026-09-09T08:26:43Z. Window covers 47 commits (880297b..HEAD): at231 cycle-2 close,
AT-269/270/271 mislabel correction, at242, at226 (+ its own at274-fix follow-up), at273, at215,
at232 (+ its own AT-276 follow-up), AT-253 gated (not built), at260. **Everything named in the
prior QUEUE's top-3 (AT-273, AT-227-adjacent, AT-215) is now stale** — AT-273 and AT-215 closed
checked-PASS this window; refreshed below against `qa/issues.jsonl` directly rather than carried
forward.

## Concurrency note

Read-only sweep, no stash/checkout/restore. All 47 commits in the window carry a manifest+verdict
pair for every code-bearing fix (at231, AT-269/270/271, at242, at226, at274-fix, at273, at215,
at232, at260) — bypass detection CLEAN. No manifest was left dangling at `ready-for-check`.

---

## TOP-3 RECOMMENDED NEXT UNITS (refreshed this sweep, from live `qa/issues.jsonl` open/high)

1. **AT-227 (high, explore) — the first-paint modal that nothing dismisses.** Unchanged across
   this entire window and several sweeps before it. A Pathlynks-style mood-check modal on first
   paint blocks the crawl's first observation; `grep -rn "modal|dismiss" stages/explore*.py`
   still returns nothing. On the critical path of every downstream stage — the oldest real
   crawl-stopper still open.

2. **AT-276 (high, video-learning, filed this window as AT-232's own follow-up) —
   containment-over-STOPWORDS `similarity()` still false-positives on genuinely different bugs
   that happen to share vocabulary.** Fresh, concrete, and adjacent to code the maker just
   touched (AT-232 landed cc16284 this window) — cheapest next move on the same file while
   context is warm.

3. **AT-243 (high, core-invariants, process debt) — Mode D has NEVER run in this repo: 86+
   verdicts, zero `LIVE-BROWSER:` lines.** Every UI-touching unit this window (at242, at226,
   at273, at215's ffmpeg path) still went through without an independent browser drive. This is
   a standing protocol gap, not a code defect — worth a deliberate unit rather than continuing
   to carry it silently.

**Gated, not queued (HUMAN_GATE, do not build without the decision):** AT-110
(approval-forgery — `qa/gates/at110-approval-forgery.md`, still an empty template stub),
AT-253 (agent-fallback wiring — gated this window, `qa/gates/at253-agent-fallback-wiring.md`,
`Answered: (pending)`), AT-147 (expiry-end-of-day, empty stub), erp-credentials (empty stub).
AT-218's GRILL row (vacuous-guard class) carries forward below — now open across many
consecutive sweeps with no `/grill` session run.

- GRILL: the recurring vacuous-guard class (AT-218) — still open, unanswered, carried forward
  again this sweep. `qa/gates/at218-vacuous-guard-class.md` confirms `**Answered:** _(not yet —
  gate remains open)_` verbatim. This has now spanned at least seven consecutive sweeps
  (2026-09-08 through this one) without a `/grill "AT-218"` session. Not re-filed as a new issue
  — same ISS-id, carried.

**Fixed backlog (ledger status `fixed`, awaiting a sweep's independent re-verification before
promotion to `verified`) — 15 rows remain after this sweep promoted AT-215/AT-232/AT-260/AT-273/
AT-274 (all independently checker-PASSed with sabotage evidence *this window*, promoted on that
basis):** AT-207, AT-208, AT-219, AT-220, AT-221, AT-222, AT-223, AT-225, AT-228, AT-230, AT-250,
AT-254, AT-264, AT-269 (real underlying id, see AT-271 mislabel note), AT-272. Several of these
(AT-207/208/219-223/228/230) have now been carried unworked across **four or more consecutive
sweeps** — this sweep did not re-verify them either (time-boxed to the window's own churn); they
remain the next sweep's first job, as flagged repeatedly before.
