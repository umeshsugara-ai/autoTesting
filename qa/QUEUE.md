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

---

## Sweep refresh — 2026-09-22 (this sweep supersedes the top-3 above; full sweep report: qa/verdicts/sweep-2026-09-22.md)

**AT-539 confirm:** maker retarget (3da1f56) verified — `uv run pytest tests/test_approve_cli.py`
10 passed; FULL SUITE `uv run pytest` **1514 passed, 5 skipped, 32 xfailed, 0 failed, exit 0**
(831.61s, whole-log scan, .work/checker_sweep_full_suite.txt). AT-539 -> fixed.

**Inbox fold (2026-09-22 TestSprite audit):** 6 new ledger rows + 1 dup-resolution. New rows:
AT-540 high (dead assertion layer: ExpectedState's absent_text/dom_asserts/visual_signal/network
zero read sites, Action.ASSERT no-op), AT-541 medium (REGRESSION_ANCHOR unreachable),
AT-542 medium (F-039 ensemble claim vs models_agreeing:1 in all 3 erp rows), AT-543 medium
(bench duration_s=300.0 literal), AT-544 medium (feature ledger 12 days stale, last row F-043),
AT-545 low (orphaned running crawl), AT-546 low (contract staleness: explore.md/consent.md name
the removed stages/explore.py seam for require_consent; line anchors drifted). The
ARCHITECTURE.md script-first claim folds into existing high row AT-253 (duplicate — same greps
re-verified, not re-filed).

**Contract staleness (X17/X18-era references):** explore.md:266 names `require_consent` without
the new `stages/explore_consent.py` module; line anchors `explore.py:200-211` (X18) and
`:298-300` drifted (file now 285 lines; `_terminal_status` at :207, call site at :285). Filed
AT-546 low; the contract is NOT edited by this sweep (checker-owned but this sweep files, the
next contract-touching unit or amendment applies the re-point).

## TOP-3 BUILDABLE NEXT UNITS (2026-09-22 refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-540 (high)** — the dead assertion layer: wire `absent_text`/`dom_asserts` into `_poll_for_expected` so a settled-but-unmet expectation records a failure instead of returning normally, and give `Action.ASSERT` a real evaluator; DECISIONS entry first (ARCHITECTURE.md Execution-model prose correction is its prerequisite per the inbox). Umesh approved assertions-first order. | Highest-leverage open product defect; the sweep's re-derivation confirms it blocks the oracle-quality north-star axis. |
| **2** | **AT-529 (high, HUMAN_GATE)** — PATHLYNKS_USER_* dev credentials 401; only Umesh can supply valid test-account values in the env editor, then re-run the stage-1 crawl to reach the post-login surface. | Unchanged; blocks the entire live-crawl-target acceptance run and X17/X18 Mode-D proof. |
| **3** | **AT-546 (low) + AT-253 (high, DECISIONS-gated):** AT-546 is the checker's own one-amendment re-point of require_consent references + line anchors in explore.md/consent.md (routine, this checker next contract touch); AT-253's resolution is the D-entry correcting the Execution-model prose (human-approved, bundled with AT-540's design decision). | Cheap checker-owned housekeeping + the human gate the assertions work must pass through first. |

**Deprioritised (not cancelled):** AT-497 (orphaned running crawl heartbeat — now AT-545 joins it as
a second on-disk instance, same fix unit can close both), AT-460, AT-488, AT-502 signals.

## HUMAN_GATE — do not build as ordinary units (verified unanswered on disk)

| Gate | Blocks |
|---|---|
| `live-crawl-target.md` | The live post-login acceptance run of X17/X18/V7. |
| `post-login-forms.md` | Any crawler typing, selecting or uploading after login (X10, D-016). |
| `erp-credentials.md` / AT-529 | Valid Pathlynks test-account values. |
| `t162-contract-approval.md` | T-162–T-169. |
| `at438-u14b-baseline.md`, `commit-before-verdict.md` | Other session's AT-438; protocol departure. |
| `at416-clip-vs-reach-direction.md`, `at383-loop-status-consumer.md`, `at365-data-class-declaration.md` | Various |
| `at110-approval-forgery.md`, `at147`, `at218`, `at253` (ARCHITECTURE Execution-model D-entry), `t136-model-credentials.md` | Various |

**Terminal state: `FINDINGS: 7`** (AT-540 high; AT-541/542/543/544 medium; AT-545/546 low;
AT-539 flipped fixed; 0 new gates opened; ARCHITECTURE.md fold deduped onto AT-253).

---

## Sweep refresh — 2026-09-22b (sharded Mode B; consolidation of 3 read-only shards; full report: qa/verdicts/sweep-2026-09-22b.md)

Window `3833218..00e36a8` (7 commits) + working tree. Full suite at this tree: **1521 passed, 5 skipped, 32 xfailed, 0 failed, exit 0** (1113.89s, `.work/full-suite-2026-09-22-1549.txt`); doctor + ruff CLEAN at 00e36a8 (shard 3). The **at540-assertion-layer Mode A checker is IN FLIGHT** (dispatched 15:38; no verdict on disk at 16:10) — expected pending handshake, not a finding; its files untouched.

**GRILL — human decision, not a build row (carried):**
- GRILL: recurring vacuous-guard prevention policy (AT-218). Unanswered, carried.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281). Carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js`. Carried.

### Findings this sweep — FINDINGS: 6

| Issue | Sev | What |
|---|---|---|
| AT-547 | high | **Bypass:** AT-541+AT-542 fixes (df529f2) and AT-543 (a5e5b81) landed as bare commits — no manifest, no verdict; all three ledger rows stay open (a flip needs a verdict). Remediation: retro-manifests + Mode A checks. |
| AT-548 | medium | df529f2's message claims "+ F-044 ledger correction appended" — no F-044 row exists in docs/FEATURES.jsonl and the commit never touches the file (shards 1+2 deduped to one row). |
| AT-549 | medium | x10b-form-typing terminal-STALLED (manifest :230) at cycle 3 of 3 with FAIL verdict and NO qa/debug/x10b-form-typing* diagnosis — its sole FAIL cause (AT-539) is since fixed; stall without diagnosis. |
| AT-550 | medium | AT-542's ensemble wiring silently shrinks: routes_sources.py:237-241 drops uncredentialed providers with no recorded signal; project.py:61-70 substitutes ["gemini"] for empty config (extends open AT-542). |
| AT-551 | medium | browser/assertions.py met() swallows probe errors into True and body_text() returns "" on a broken page — absent_text-only expectation on a crashed page records met and completes clean; visible_text/dom_asserts fail safe. Ruled defect-not-contract vs D-032's Result (no-raise is satisfiable failing-safe). |
| AT-552 | low | Inbox residual: umesh's 2026-09-06 home-page-dashboard ask never filed (the two sibling 2026-09-07 asks were delivered — Status lines annotated, entry folded onto this row). |

**Deduped / not filed:** opus_sub_share — shard 3 measured **0.289 (over the 0.25 line)** at 15:54:51; consolidation re-read **0.153 (UNDER)** at 16:10:25 — volatile around the threshold; scan line appended to `qa/token-ledger.jsonl` and open **AT-486** extended with both numbers (its Opus-dispatch audit is still not performed; no new row). grade.md **G2** ("Only Outcome.COMPLETED results are sent to the judge") + execute.md **E1** — both D-032-wave staleness, folded into the in-flight at540 checker's contract touch (no row; the next sweep files if its verdict lands without them). AT-541/542/543 got evidence notes (fixes in-tree, UNVERIFIED) — **no flips this sweep**; AT-253 NOT flipped (D-031 prose landed, wiring question still gated); AT-415 re-confirmed; AT-488/AT-502 unchanged in window (no refile); data-boundary gate still fires (no `data_class`) — standing **AT-365**; no graph.json → blast radius NOT-APPLICABLE.

### TOP-3 BUILDABLE NEXT UNITS (2026-09-22b)

| # | Unit | Why |
|---|---|---|
| **1** | **at540-assertion-layer Mode A check** — in flight (dispatched 15:38), not to be raced. Its contract touch (execute.md E1 per D-032) should also absorb the grade.md G2 line and, if convenient, the AT-546 require_consent re-point. | The pending handshake the board waits on; its verdict lets AT-540 close. |
| **2** | **AT-547 (high) bypass remediation** — retro-manifests + Mode A checks for AT-541/AT-542/AT-543. | The only high row filed this sweep; three open rows carry real in-tree fixes awaiting a check. |
| **3** | **The buildable tail:** AT-529 (high, HUMAN_GATE — Umesh's test-account credentials) · AT-546 checker re-point (bundle with the at540 contract touch if its verdict allows) · AT-544 via the F-044 remediation (AT-548) · AT-545+AT-497 heartbeat unit · T-123 medium batch · AT-550/AT-551 as natural follow-ons to at540. | Ordered by severity + unblocking value. |

### HUMAN_GATE — do not build as ordinary units (carried from the 2026-09-22 refresh, verified unchanged)

live-crawl-target · post-login-forms · erp-credentials/AT-529 · t162-contract-approval · at438-u14b-baseline + commit-before-verdict · at416-clip-vs-reach-direction · at383-loop-status-consumer · at365-data-class-declaration · at110-approval-forgery · at147 · at218 · at253 (ARCHITECTURE Execution-model D-entry) · t136-model-credentials.

**Terminal state: `FINDINGS: 6`** (AT-547 high; AT-548/549/550/551 medium; AT-552 low; 0 flips; AT-486 extended with the token reading; sweep report: qa/verdicts/sweep-2026-09-22b.md).

---

## Sweep refresh — 2026-09-22c (sharded Mode B; consolidation of 3 read-only shards, HEAD `93fad7b`)

Window `00e36a8..93fad7b`. The at540-assertion-layer Mode A check landed **cycle-2 checked-PASS**
(`d7d8405` fix, `41ff0e1` close-out) since the prior sweep — AT-547/548/549/550/552 (checker-unit
set, its own cycle-1 findings) flipped `fixed`; AT-551 (sweep set, met()/body_text fail-unsafe)
also flipped `fixed`. `target.md` milestone tracker landed (`93fad7b`), routed at `CLAUDE.md:24`.

**GRILL — human decision, not a build row (carried):**
- GRILL: recurring vacuous-guard prevention policy (AT-218). Unanswered, carried.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281). Carried.
- GRILL (AT-402): structure-before-code review of `visual_order.js`. Carried.

### Findings this sweep — FINDINGS: 3 new + 1 reconciled (no renumber) + aging restatement

| Issue | Sev | What |
|---|---|---|
| AT-555 | medium | `assertions.py::met()`'s url branch stays fail-UNSAFE (blanket `contextlib.suppress` → `return True` on a `page.url` read failure) — the AT-540 fix closed the `body_text`/`absent_text` half of AT-551 but not this one; disclosed as "row 11" debt in `qa/verdicts/at540-assertion-layer.md:21-23` but carried no issue id until now. |
| AT-556 | low | One `ScheduleWakeup` call blocked today by a `glm-5.3-flash` classifier outage (6 outages total) — same failure shape as AT-368's multi-day dead loop; loop did not visibly stall this time, leading-indicator only. |
| AT-557 | low | `uv run autotester doctor` not clean: `docs/SNAPSHOT.md` stale vs its own regeneration — likely the `target.md` commit or at540's landing not re-running `autotester snapshot`. |

**AT-553 (dup-id pattern) — reconciled by judgment, NOT renumbered.** Evaluated the dispatch's
preferred renumber (keep at540-set AT-547..552 `found_by=checker-unit`, renumber sweep-set
AT-547..552 `found_by=checker-sweep` to fresh ids) and rejected it: the sweep-set AT-551 content
(met()/body_text fail-unsafe) is cited by id inside `src/autotester/browser/assertions.py` and two
test files — files this role is barred from editing — so a clean renumber isn't achievable without
orphaning permanent code comments. Every one of the twelve colliding rows (AT-547..552 ×2,
AT-288..291 ×2) already carries a `found_by`/`checker` discriminator, mirroring the precedent
AT-293 (2026-09-11, verified) already set for the AT-288..291 case — that ruling stands, not
re-litigated. Full reasoning recorded in AT-553's own `evidence` field. Old→new id mapping: **none
— no renumber performed.**

**Non-findings confirmed, not re-filed:** AT-541/542/543 (bypass-fixed-but-unverified) re-derived
independently by shard 3 as still legitimately OPEN — no manifest/verdict exists for any of the
three; AT-550 (ensemble silent-shrink) confirmed still reproduces in code, unchanged. Gate-answered-
off-disk sweep over all 21 `qa/gates/*.md` found zero violations (one cosmetic stray placeholder at
`t136-model-credentials.md:44`, not filed). `target.md`'s north-star framing is not literally
covered by check 6's trigger (goal.json's `north_star` field itself is unedited) but is
un-reconciled with a second, higher-visibility statement of the goal — noted, not filed as a new
row this sweep (informational only, folded into the TOP-3 below instead). Data-boundary (AT-365),
loop.md agreement, and structural erosion (session.py at 299/300 lines, watch-item) all re-confirmed
unchanged.

### TOP-3 BUILDABLE NEXT UNITS (2026-09-22c refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-541/542/543 retro-remediation** — verify-or-revert the bare commits `df529f2`/`a5e5b81` (no manifest, no verdict, per AT-547) through the maker-checker pair properly: retro-manifest the three fixes (What changed + verify commands), dispatch Mode A, let the rows flip only on a real verdict. Bundle the **AT-550** fix (silent ensemble-shrink at `routes_sources.py:236-244` / `schema/project.py:70` — record which provider was skipped instead of a silent drop; refuse or note the empty-config `["gemini"]` default) into the same unit since it extends the same AT-542 surface. | The only high-severity row with real in-tree fixes still awaiting a check; unblocks three open ledger rows plus AT-550 in one pass. |
| **2** | **AT-529 (high, HUMAN_GATE)** — PATHLYNKS_USER_* dev credentials 401; only Umesh can supply valid test-account values. | Unchanged; blocks the entire live-crawl-target acceptance run. |
| **3** | **AT-555 (medium, new)** — guard `met()`'s url-read the same way `body_text()`/`selector_exists()` are now guarded, with a falsifying test that a raising `page.url` does not leave `met()` returning `True`. Cheap, same file already touched by at540. | Closes the last disclosed gap from the at540 fix cycle; small, isolated, well-scoped. |

**Aging (not new, restated for priority):** AT-110 (14d, high, RunApproval tamper-check defeat) is
the oldest untouched high-severity row on the board — no code change this sweep, still needs a
build slot. AT-218/AT-281 (GRILL rows, 13d/12d) remain HUMAN_GATE, not buildable.

**Deprioritised (not cancelled):** AT-544 (feature-ledger stale, via the F-044 remediation AT-548,
already fixed by at540's cycle-2 close-out — re-check on next ledger touch) · AT-545/AT-497
(orphaned-running-crawl heartbeat) · AT-488/AT-502 structural-erosion signals · AT-556/AT-557 (low,
no urgency).

### HUMAN_GATE — do not build as ordinary units (carried, verified unanswered on disk)

live-crawl-target · post-login-forms · erp-credentials/AT-529 · t162-contract-approval ·
at438-u14b-baseline + commit-before-verdict · at416-clip-vs-reach-direction ·
at383-loop-status-consumer · at365-data-class-declaration · at110-approval-forgery · at147 · at218 ·
at253 (ARCHITECTURE Execution-model D-entry) · t136-model-credentials.

**Terminal state: `FINDINGS: 3`** (AT-555 medium; AT-556/557 low; AT-553 dup-id pattern reconciled
by judgment, no renumber; 0 new gates opened; sweep report: this consolidation, shards at
`qa/sweeps/shard-{1,2,3}-2026-09-22c.md`).

---

## Sweep refresh — 2026-09-22d (focused reconcile; not a full sweep — delta since 18:56/6b0e744,
now HEAD `370a017`)

Targeted reconcile of the 4 checker-verified units merged since the last full sweep (`93fad7b`
onward): the ledger already carried the correct flips from those units' own verdicts —
re-verified rather than re-derived from scratch, per the dispatch's bounds.

**Ledger state re-confirmed against `qa/verdicts/`:**
- **AT-541, AT-542, AT-543, AT-547** — `qa/verdicts/at541-543-ensemble-honesty.md` = PASS (cycle 1).
  Already `status: fixed` on disk with the verdict's own retro-coverage notes; confirmed, not
  re-flipped to `verified` (this checker's convention: `fixed` now, `verified` only on a later
  independent re-check, per the checker protocol — not this reconcile).
- **AT-550** (the `checker-sweep` ensemble-shrink row, line 547) — confirmed **OPEN**, partial-fix
  note intact: record-the-shrink half fixed+verified in `7c3626b`
  (`schema/analysis.py:59-93` → `adjudicate()` → `routes_sources.py:252`, mutation-tested 3/3 in
  the verdict), the empty-config half (`schema/project.py:70` `return seen or ["gemini"]`) still
  untouched. Left open, not closed.
- **AT-555** — `qa/verdicts/at555-url-guard.md` = PASS (cycle 1). Already `status: fixed` on disk
  (`met()`'s url branch now guarded via `_page_url()`, independently falsified in a throwaway copy).
- **AT-557** (docs/SNAPSHOT.md stale) — `uv run autotester doctor` re-run at HEAD `370a017` →
  **`doctor: clean`**. Flipped `open → fixed` this reconcile (evidence: "doctor clean at 370a017,
  SNAPSHOT regenerated" — the ensemble unit's landing evidently re-ran `autotester snapshot`).
- **AT-556** (ScheduleWakeup blocked by classifier outage) — loop-resilience observation, not a
  code defect. Left **open, low**; annotated that this session's tick survived via
  subagent-notification + heartbeat (no dead loop observed).

No other rows touched. `qa/issues.jsonl` re-validated line-by-line as valid JSON after edits (560
lines, unchanged count).

### TOP-3 BUILDABLE NEXT UNITS (2026-09-22d refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-110 (high)** — RunApproval tamper-check defeat, now the oldest untouched high-severity row on the board (~14 days). | No mechanical blocker; the highest-severity buildable defect with no human gate in front of it. |
| **2** | **AT-550 empty-config remainder** — make `schema/project.py:70`'s `return seen or ["gemini"]` explicit (refuse, or default-with-note) instead of a silent substitution; the record-the-shrink half is already done and verified, this is the narrow remainder. | Small, well-scoped, closes the last disclosed gap on a row already half-fixed. |
| **3** | **AT-554 (HUMAN_GATE, not a buildable unit)** — `/settings/providers` + env editor serve the real credential VALUE in the HTTP response/DOM, contradicting `browser-and-secrets.md:59`/`core-invariants.md:47`; CRITICAL-class (weakening a credential boundary needs Umesh + a D-entry). Noted here as a gate row so it stays visible, not picked up as ordinary work. | Blocks nothing else buildable but is high-severity and needs a human decision before any code touches it. |

**GRILL — human decision, not a build row (carried, unanswered):**
- GRILL: recurring vacuous-guard prevention policy (AT-218).
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281).
- GRILL (AT-402): structure-before-code review of `visual_order.js`.

**Terminal state: `focused reconcile — 0 new findings, 6 rows reconciled`** (AT-541/542/543/547/555
confirmed `fixed`; AT-550 confirmed `open`/partial; AT-557 flipped `open → fixed` on a clean
doctor; AT-556 annotated, left `open`/low; HEAD `370a017`).

---

## Sweep refresh — 2026-09-23 (Mode B safety-net, reconcile after T-162/T-163/D-037 merge burst)

Window `370a017..24043b8` (48 commits): T-162 fast-follow phases AUDIO/EMAIL/DRIVE landed and
closed (F-044, `checked-PASS` each, dual-checked), T-163 resumable orchestrator landed and closed
(D-036, F-045, dual-checked cycle 1), the `EnterWorktree`/`ExitWorktree` allowlist fix landed
(D-037, `Approved-by: Umesh`), and a `test_goal_done_checks.py` registration guard was corrected
twice (`bfb8c48`, `b8c2297`) to match the widened T-162 `done_check` and the actual T-163 test
file names.

**Bypass detection — CLEAN, no new bypasses.** Every `feat`/`fix` commit in the window traces to a
manifest→verdict handshake: t162-source-adapters-1a (`5e243b7`→`14b6830`/`fb18d13`→`f2f2f9a`),
t162-audio-1b (`efbb17e`→`994d698`/`54a2935`→`3b32871`), t162-email-2a (`53adcc8`→`e22df4f`/
`d8d4c9c`→`f4a8c54`), t162-drive-2b (`2485ca2`→`46a7094`→FAIL`f4ec8c0`→cycle-2`b602226`→
`d650eaf`→`15804a1`), t163-orchestrator (`6cad8e0`+merged-in `4f84b45`/`bfb8c48`/`b8c2297`→
`71badf2`/`00036af`→`75bad93`). `4f84b45` (settings.json allowlist) is the one config change with
no manifest of its own — correctly so: it is an **enforcement-path** change authorized by
`D-037` with `Approved-by: Umesh` per the Lab Protocol's own rule (a DECISIONS entry, not a
maker-checker unit, is the gate for `.claude/settings.json`). `bfb8c48`/`b8c2297` (test registration
+ `.goal/goal.json` done_check strings) were committed straight to master, then merged into
`wave/t163-orchestrator` at `daafba4` *before* the dual check ran — both checkers' diff-scope step
(step 4c) explicitly inspected them and recorded them as "changed only outside judged scope …
confirmed by inspection" (`qa/verdicts/t163-orchestrator.b.md:69-70`), i.e. reviewed and
consciously scoped, not silently skipped. No unreviewed code/schema/contract change found.

**Ledger reconciliation:**
- **`ISS-t162-drive-2b-1`** (T-162 done_check too narrow) → **CLOSED, `open → fixed`.**
  `.goal/goal.json` T-162.done_check.cmd is now the 4-file form
  (`tests/test_source_adapters.py tests/test_source_adapters_audio.py
  tests/test_source_adapters_email.py tests/test_source_adapters_drive.py`, via `b8c2297`), and
  `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered` expects the identical
  string (via `bfb8c48`) — read directly, both match byte-for-byte.
- **`ISS-t163-1`** (stale `docs/SNAPSHOT.md`) → **CLOSED, `open → fixed`.** `uv run autotester
  doctor` at HEAD `24043b8` → `doctor: clean`; `docs/SNAPSHOT.md`'s "Last decisions" list now
  reads through `D-037` (grep-confirmed).
- No other open row references T-162/T-163/adapters/orchestrator as stale — `AT-420`/`AT-447`
  (the older `t162-contract-approval.md` gate-premise pair) are unrelated to this burst and still
  legitimately open, left untouched.

**Contract staleness/liveness — CLEAN.** `qa/contracts/source-adapters.md` header reads ACTIVE,
finalized by /checker under D-035, phase-1a + phase-2a/2b all cite their real verdict files —
matches shipped code (adapters seam + TEXT/DOC/AUDIO/EMAIL/DRIVE all present under
`src/autotester/sources/`). `qa/contracts/orchestrator.md` header reads ACTIVE (was DRAFT,
authorized by D-036, taken ACTIVE by /checker on T-163 cycle-1 PASS) with OR1-OR6 each carrying a
falsifying-edit row in its own amendment log — matches `stages/orchestrate.py` +
`schema/run_state.py` on disk.

**Enforcement liveness — CLEAN.** `.claude/settings.json` `permissions.allow` contains both
`"EnterWorktree"` and `"ExitWorktree"` (D-037's fix is actually installed, not just decided).
SessionStart/PreToolUse/Stop hook files it references
(`qa/hooks/mc-sessionstart.ps1`, `.claude/hooks/lab-session-start.ps1`,
`qa/hooks/mc-precommit.ps1`, `.claude/hooks/decisions-append-guard.ps1`,
`.claude/hooks/lab-session-end.ps1`) all exist on disk. Repo has commits (HEAD `24043b8`, not an
empty-history gate). `uv run ruff check src tests scripts` → `All checks passed!`.

**Goal-coverage gap — no drift.** `.goal/goal.json` progress = **37/55 done (67%)**, matching the
dispatch's stated 37/55. T-164 (Portal Persona, deps `["T-163"]` ✓) and T-165 (deps
`["T-163","T-144"]`, both ✓) are now mechanically ready — no dependency gap. `qa/.regrill-due`
absent, `qa/.paused` absent, `qa/.last-tick` fresh (`2026-09-23T00:59:10Z`, names this exact
reconcile + the T-164/T-165 fork) — no re-grill trigger fired (north star unedited this window, no
requirement newly `missing` with no source, no unit re-PASSed twice on the same evidence).

**Doctor — CLEAN.** `uv run autotester doctor` → `doctor: clean` at HEAD `24043b8`. Full-suite
`pytest` not re-run per dispatch (already green at 1568 passed on master).

### TOP-3 BUILDABLE NEXT UNITS (2026-09-23 refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **T-164 — Portal Persona** (deps `T-163` ✓, `done_check`: `uv run pytest tests/test_portal_persona.py`) | Newly unblocked this window; the next roadmap milestone unit with no mechanical or human blocker. T-165 (deps `T-163`+`T-144`, both ✓) is equally ready as an alternative/parallel pick. |
| **2** | **AT-110 (high)** — RunApproval tamper-check defeat; oldest untouched high-severity row on the board (~15 days), no human gate in front of it. | Carried unchanged from the 2026-09-22d refresh; still the highest-severity buildable defect. |
| **3** | **AT-529 (high, HUMAN_GATE)** — PATHLYNKS_USER_* dev credentials 401; only Umesh can supply valid test-account values, then re-run the stage-1 crawl. | Unchanged; blocks the entire live-crawl-target acceptance run (X17/X18/V7 Mode-D proof) — named here so it stays visible, not picked up as ordinary work. |

**Deprioritised (not cancelled):** AT-497/AT-545 (orphaned running-crawl heartbeat, same fix unit
closes both) · AT-488/AT-502 (structural-erosion signals, advisory only) · AT-556 (loop-liveness
observation, low) · AT-546 (checker-owned `require_consent` contract re-point, routine, next
contract touch).

**GRILL — human decision, not a build row (carried, unanswered):**
- GRILL: recurring vacuous-guard prevention policy (AT-218).
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281).
- GRILL (AT-402): structure-before-code review of `visual_order.js`.

### HUMAN_GATE — do not build as ordinary units (carried, verified unanswered on disk)

live-crawl-target · post-login-forms · erp-credentials/AT-529 · t162-contract-approval ·
at438-u14b-baseline + commit-before-verdict · at416-clip-vs-reach-direction ·
at383-loop-status-consumer · at365-data-class-declaration · at110-approval-forgery · at147 ·
at218 · at253 (ARCHITECTURE Execution-model D-entry) · t136-model-credentials.

**Terminal state: `FINDINGS: 0`** (no new issues opened; 2 closed — `ISS-t162-drive-2b-1`,
`ISS-t163-1`, both `open → fixed`; 0 bypasses; contracts + enforcement + goal-coverage all CLEAN;
HEAD `24043b8`).
