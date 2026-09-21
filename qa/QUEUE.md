# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-18T01:41:32+05:30**. The stamp comes from the system clock
(`date`), not typed (AT-399). Bound strictly to `D:/autoTesting`. Single-agent sweep (measured
ceiling this tick: 2.3 GB free RAM, an at496 checker concurrently in flight — not sharded per
dispatch instruction). Window `246c026..130e0c7`, 20 commits. Supersedes the
`2026-09-17T23:30:00+05:30` queue — its top-3 (dispatch checker on at490-491 / AT-483 wave /
the three HUMAN_GATEs) resolved as follows inside or just after this window: AT-492 (at490-491
dispatch gap) closed via `992f03f`/`4d00d58` (checker PASS + close-out, both inside this window);
the AT-483 wave closed via `9e11559` (checked-PASS cycle 1, filed a narrower residual AT-497); the
three HUMAN_GATEs remain open, unchanged.

**Note on scope:** while this sweep ran, the live `at496-the-ledger-never-loses-a-row` checker
(explicitly out of scope for this dispatch — "do not judge, dispatch, or write anything for it")
closed cycle 2 `checked-PASS` at commits `d115c0a`/`a0155f2`, just past this window's `130e0c7`
end. No governance problem found in its handshake (manifest → FAIL → fix cycle 2 → PASS →
close-out, each with a matching-cycle verdict); not judged technically, per instruction.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy (AT-218). Unanswered, carried.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281). Carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js`. Carried.

## Findings this sweep — FINDINGS: 1

| Issue | Sev | What |
|---|---|---|
| AT-502 | medium (structural-erosion signal, never a blocker) | `scripts/flake_probe.py` rewritten across 3 separate units in <24h (AT-335 build, AT-401 fix, AT-494 fix): 186→244 lines (+31%), each re-touching `run_once`'s subprocess-invocation core (bare `subprocess.run` → timeout-wrapped → `Popen`+file-log+shared `kill_tree`). Still under the 300-line cap and under `scripts/`'s existing zero-size-cap gap (AT-488/AT-419) either way — noted so the next touch considers whether the design has actually settled. |

**Not filed (dedupe):** `scripts/mutation_check.py`'s structural-erosion signal is unchanged in
size this window (still 416 lines; the one diff was a rename `_kill_tree`→`kill_tree` to make it
importable, +1 commit) — same signal `AT-488` already carries, numbers updated: **416 lines / 12
commits** (was 361/9 when filed, 416/11 last sweep).

**Non-findings confirmed, not re-filed:**
- **Bypass check (all 20 commits):** every commit touching `src/`, `tests/`, or `scripts/` traces
  to a manifest→verdict handshake (at401: `cf34933`→`9b5cbc5`→`05cc388`; at490-491:
  `176a89c`(prior window)→`992f03f`→`4d00d58`; at494: `0ed84a7`→`1688da3`→`f8f304d`; at496 cycle
  1-2: `385fec1`/`67a61ec`→`b437a85`(FAIL)→`0af3ad8`→`d115c0a`(PASS, just past window)→`a0155f2`)
  or is a correctly-scoped `chore(qa): stamp the … tick` commit. CLEAN.
- **Handshake integrity:** no manifest sat `ready-for-check` with a missing/stale-cycle verdict
  at sweep time (AT-492's dispatch gap from the prior sweep closed inside this window). The only
  `ready-for-check` string match left on disk is the known phantom at
  `qa/manifests/at438-display-contents.md:385` (header says STALLED at line 8) — confirmed still
  live, this is **AT-485**, already open, not re-filed.
- **Ledger hygiene (AT-475/496 class):** `qa/issues.jsonl` is clean at HEAD (no working-tree
  divergence) as of this sweep — the very unit built to catch this class (AT-496,
  `check_qa_issue_rows` in `doctor.py`) closed `checked-PASS` while this sweep ran. AT-401/490/
  491/494/496/498/499 rows all verified present with correct terminal status, matching their
  verdicts field-by-field.
- **Data boundary (MC-003):** `python .../data_boundary.py D:/autoTesting` still exits 1, no
  `data_class` in `qa/adapter.json` — already **AT-365** (open, high), not re-filed.
- **Contract staleness:** none found; no criterion in `qa/contracts/*.md` contradicts what this
  window shipped (C10's ledger-handshake language is exactly what AT-496 implements).
- **Inbox:** `qa/feedback-inbox.md` (691 lines) has no entry dated after 2026-09-16, and every
  entry through that date already carries a `**FOLDED:**` line. CLEAN.
- **Gates:** 19 total (unchanged count — the 14→19 growth and the "most lack an Answered line"
  rot pattern is already **AT-415**, not re-filed). Of the 19, only 7 carry an `Answered:` field
  at all and every one of those 7 reads blank or `(pending)` — **zero of 19 gates are actually
  answered on disk**, same state as prior sweeps. The three blocking all further buildable work:
  `post-login-forms.md`, `live-crawl-target.md`, `erp-credentials.md` — all three still
  `Answered: (pending)` / no `Answered:` line.
- **Doctor + ruff, re-run at HEAD:** `uv run autotester doctor` → `doctor: clean`; `uv run ruff
  check src tests scripts` → `All checks passed!`.
- **Silent-failure hunt** over code touched by units PASSed since the last sweep (at401,
  at490-491, at494): none found. AT-490/AT-491/AT-494 were themselves exactly this class and are
  now closed with tested, non-swallowing exception handling (`kill_tree`'s `MutationError` on an
  unkilled survivor; `flake_probe.run_once`'s file-backed output with the kill failure surfaced
  in the run's `tail`, not discarded).

## Token spend (re-measured this sweep)

`opus_sub_share=0.22` over the last day (55 sub-agents) — **now UNDER the 25% diet threshold**,
continuing the fall from 0.624 → 0.539 → 0.299 → 0.22 across four consecutive re-reads. Same
ongoing day-window as `AT-486` (open, low) — left open rather than closed by this sweep: its
`expected` clause calls for an audit of the day's Opus dispatches for stated heavy-reasoning
justification, which this sweep did not perform; the number alone crossing the line is not that
audit.

## TOP-3 BUILDABLE NEXT UNITS (re-ranked — AT-492 and the AT-483 wave both closed this window)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-497** (low) — a crawl killed before its first action completes (during `_seed`, login bootstrap, or mid-first-action) never gets a heartbeat write and displays RUNNING forever. Disclosed residual, narrower scope than AT-483 (fixed). `src/autotester/stages/explore.py:277-287`, `explore_node.py:119-137,266-267`. | The only open, mechanically-buildable, non-gated defect left on the board this sweep found. |
| **2** | **The three open HUMAN_GATEs still block everything else buildable:** `qa/gates/post-login-forms.md` (X10/D-016, any post-login typing/select/upload), `qa/gates/live-crawl-target.md` (the live acceptance run of X17/X18/V7), `qa/gates/erp-credentials.md`. All three `Answered:` lines remain unfilled placeholders. | Unchanged from the last two sweeps — every mechanism buildable without a human call is built and fixture-proven; further progress on the product surface needs Umesh to answer one of these three. |
| **3** | **Structural-erosion signals, advisory only, never blockers:** `AT-488` (`scripts/mutation_check.py`, now 416 lines / 12 commits) and `AT-502` (new this sweep — `scripts/flake_probe.py`, 3 units / 186→244 lines). Neither needs a dedicated unit; both are a note for whoever next touches either file. | Named so a future maker doesn't grow either file past its natural stopping point without noticing. |

**Deprioritised (not cancelled):** `AT-460` (`explore.py` at the 300-line cap), `AT-464`,
`AT-456`.

**Explicitly NOT assigned:** `at438` / `AT-442…AT-454` (other session, STALLED + gate) · anything
under `.goal/`, `.codex/`, `AGENTS.md`, untracked `projects/*`.

## HUMAN_GATE — do not build as ordinary units (verified unanswered on disk unless noted)

| Gate | Blocks |
|---|---|
| `live-crawl-target.md` | The live post-login acceptance run of X17/X18/V7 (target, write_policy, bounds). |
| `post-login-forms.md` | Any crawler typing, selecting or uploading after login (X10, D-016). |
| `t162-contract-approval.md` | T-162…T-169 |
| `at438-u14b-baseline.md`, `commit-before-verdict.md` | Other session's AT-438; protocol departure. |
| `at416-clip-vs-reach-direction.md`, `at383-loop-status-consumer.md`, `at365-data-class-declaration.md` | Various |
| `at110-approval-forgery.md`, `erp-credentials.md`, `at147`, `at218`, `at253`, `t136-model-credentials.md` | Various |
| `at052-bfs-video-corpus-grill.md` | **Answered 2026-09-07** — kept in this table only as the record of what unblocked Tracks 0/A/B; not an open gate. |

**Terminal state: `FINDINGS: 1`** (AT-502 medium, structural-erosion signal; 0 new gates opened,
AT-488/AT-365/AT-485/AT-415/AT-486 dups avoided).
