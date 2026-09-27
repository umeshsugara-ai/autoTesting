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
- HUMAN_GATE (ISS-at638-remainder-1, 2026-09-27): approve a DECISIONS entry naming
  `qa/contracts/permission-surface.md`, `eval-compiler.md`, `release-regression.md` and
  `damage-control-report.md` as checker-owned DRAFT deliverables (draft text in
  `qa/verdicts/at638-remainder.md`) — none of the four is named by D-040/D-041/D-042, breaking this
  repo's 5/5 practice of naming a contract file in a decision before it is written. 17 criteria
  (PS1-PS4/EC1-EC4/RR1-RR5/DC1-DC4) are already filed and checker-reviewed in
  `qa/feedback-inbox.md`, waiting only on this approval — no further analysis needed once it lands.

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

---

## Sweep refresh — 2026-09-24 (sharded Mode B; consolidation of 3 read-only shards; full report:
`qa/verdicts/sweep-2026-09-24.md`)

Window `761982d..087ab84` (12 commits: D-038 T-164 build → checked-PASS → close-out → reuse spike →
D-039 gate write). HEAD at consolidation `2263e9a` (tick stamp only). T-123 build
(`.worktrees/t123-medium-batch`) and the AT-483 re-land (fix cycle 2,
`.worktrees/at483-reland`, branch `wave/at483-reland`) both running concurrently — out of scope,
not judged or touched.

**GRILL — human decision, not a build row (carried, unanswered):**
- GRILL: recurring vacuous-guard prevention policy (AT-218).
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281).
- GRILL (AT-402): structure-before-code review of `visual_order.js`.

### Findings this sweep — FINDINGS: 0 new · 1 reopened · 1 evidence-refresh

| Issue | Sev | What |
|---|---|---|
| **AT-483** | low (reopen) | Its 2026-09-18 checked-PASS (`9e11559`) certified a fix that never reached master — `git merge-base --is-ancestor 9673f6b master` = NOT-ANCESTOR, `grep heartbeat src/autotester/stages/explore_status.py` on master = no match. Reopened `fixed → open` with `reopen_reason`; re-land already in progress on `wave/at483-reland` (not touched by this sweep); `.work/wave-at483` left unpruned. |
| **AT-415** | medium (evidence refresh, no flip) | Gate-rot count re-derived: `qa/gates/` now 24 files (was 14 at filing), only 6 carry an `Answered:` line, only 1 (`at554`, D-034) is truly answered. `checker_note` appended; row stays open. |

**Inbox:** `qa/feedback-inbox.md`'s 2026-09-23T07:30:10 Umesh entry got a missing `**Status:**`
line added — GATED at `qa/gates/t165-d039-traversal-scope.md` (D-039), T-164 portion folded to
`portal-persona.md` (PASS `05fc732`).

**Non-findings confirmed, not re-filed:** 0 bypasses (t164-portal-persona manifest/verdict
reconcile clean, cycle 1 PASS `05fc732`, closed `3ceb7b9`); delegation health n=1 external unit
(`at119-vocab`), below the ≥10-unit sample threshold, no finding; contracts not stale; data
boundary still fires — standing **AT-365**, not re-filed; enforcement liveness CLEAN (`doctor:
clean`, ruff `All checks passed!`, `.last-tick` fresh, no `.paused`); goal-coverage **38/55
(69%)**, up from 37/55 (T-164 closed), no drift; silent-failure hunt over T-164's new code — none
found. Token scan re-run: `opus_sub_share=0.0`, 8 sub-agents, 0 compactions — well under the 25%
diet threshold; no unit at fix cycle 3 this window. Line appended to `qa/token-ledger.jsonl`.
Worktrees `checker-at540/row1..row10`, `.work/t161-primary-4c09990`,
`.claude/worktrees/agent-a6095f6e2fc40863a` confirmed merged/content-identical, safe to prune —
**report only, not pruned** this sweep.

**Bypass-detection gap noted (not filed as a row):** a checker-PASS + close-out on a wave branch
that never merges to master is currently invisible to the bypass check, which reads handshake
existence rather than master-ancestry. AT-483 is the live example; folded into that row's own
evidence rather than filed separately.

### TOP-3 BUILDABLE NEXT UNITS (2026-09-24 refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-483 re-land (fix cycle 2)** — in progress on `wave/at483-reland`; the next Mode A check re-verifies the heartbeat/liveness fix actually reaches master (same ancestor + grep check used this sweep) before flipping the row back to `fixed`. | The false-fixed claim is the highest-severity live governance issue on the board; re-land already started, needs its check dispatched when ready. |
| **2** | **T-165 HUMAN_GATE (D-039)** — `qa/gates/t165-d039-traversal-scope.md`, 4 spike questions awaiting Umesh (traversal strategy, permission-surface scope, Playwright Healer, API-capture ordering). | Blocks T-165/T-166/T-167/T-168/T-169 downstream; highest-leverage open gate. |
| **3** | **AT-110 (high)** — RunApproval tamper-check defeat, oldest untouched high-severity row with no human gate in front of it. | Carried unchanged across multiple prior sweeps; still the highest-severity buildable defect. |

**Deprioritised (not cancelled):** AT-497/AT-545 (orphaned-running-crawl heartbeat — folds into
the AT-483 re-land, same fix class) · AT-488/AT-502 (structural-erosion signals, advisory only) ·
AT-556 (loop-liveness observation, low) · AT-546 (checker-owned `require_consent` contract
re-point) · AT-529 (HUMAN_GATE, Pathlynks test-account credentials).

### HUMAN_GATE — do not build as ordinary units (carried, verified unanswered on disk unless noted)

live-crawl-target · post-login-forms · erp-credentials/AT-529 · t162-contract-approval ·
at438-u14b-baseline + commit-before-verdict · at416-clip-vs-reach-direction ·
at383-loop-status-consumer · at365-data-class-declaration · at110-approval-forgery · at147 ·
at218 · at253 (ARCHITECTURE Execution-model D-entry) · t136-model-credentials ·
**t165-d039-traversal-scope** (new this window — D-039, 4 spike questions).

**Terminal state: `FINDINGS: 0`** (0 new issue ids; 1 reopened — AT-483 high-severity governance
finding on a low-severity defect row; 1 evidence-refresh — AT-415; 1 inbox status line added; 0
bypasses; contracts + enforcement CLEAN; goal-coverage 38/55, no drift; HEAD `2263e9a`).

---

## Sweep refresh — 2026-09-24b (single-agent Mode B, not sharded — RAM tight, per dispatch;
full report: `qa/verdicts/sweep-2026-09-24b.md`)

Window `2263e9a..f1b8569` (26 commits: T-123/AT-483-reland merges + PASS, gate answers `b8d14bd`,
D-039/D-040/D-041 appended + T-170..T-178 registered, six DRAFT contracts authored, tick stamps).
**Out of scope, not judged/touched:** `.worktrees/t170-network-assertions`,
`.worktrees/at110-approval-signing`, `.worktrees/at335-modal-determinism`.

**GRILL — human decision, not a build row (carried, unanswered):**
- GRILL: recurring vacuous-guard prevention policy (AT-218).
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281).
- GRILL (AT-402): structure-before-code review of `visual_order.js`.

### Findings this sweep — FINDINGS: 0 new · 1 closed (wontfix) · 3 annotated

| Issue | Sev | What |
|---|---|---|
| **AT-365** | high → **wontfix** | Gate answer (`qa/gates/at365-data-class-declaration.md`, 2026-09-24) not yet reflected on the ledger row. Closed `open → wontfix`: Umesh declined both a shared `data_boundary.py` fix and a `.work/` purge — a tester-supplied test account's own data exposure is that account provider's responsibility, not this repo's own scratch-boundary gate. `data_class` stays undeclared by design; MC-003 will keep firing (expected, not a new finding each sweep). Folded → `qa/contracts/core-invariants.md` amendment log + No-fire list; `qa/feedback-inbox.md` 2026-09-24T16:33 entry partially folded. |
| AT-110 | high (unchanged, open) | `checker_note` appended: gate answered 2026-09-24 (option 1, HMAC keyed from `.env`); build already dispatched to `.worktrees/at110-approval-signing` (out of scope this sweep). Row correctly stays open — design decided, fix not yet merged. No inconsistency found. |
| AT-086 | medium (unchanged, open) | `checker_note` set: gate answered 2026-09-24 ("go with the best" → option a, explicit declared `.env` public-key allowlist). Not yet built; queued. No inconsistency found. |
| AT-087 | medium (unchanged, open) | `checker_note` set: gate answered 2026-09-24 (option a, per-field exemption kept in the concatenation join). Not yet built; queued. No inconsistency found. |

**AT-483-class gap re-check (per dispatch item c) — CLEAN, no new findings.** Sampled 24 distinct
commit SHAs cited as evidence across 18 `fixed`/`verified` rows closed since 2026-09-17 (AT-216,
AT-401, AT-461, AT-478, AT-483, AT-495, AT-539, AT-541, AT-555, `ISS-t162-drive-2b-1`,
`ISS-t163-1`, plus AT-065/AT-085 via `18ff2a9` already visible in this window's own log) —
`git merge-base --is-ancestor <sha> master` returned **ANCESTOR for all 24**, including AT-483's
own `9673f6b` (now merged via the `wave/at483-reland` re-land, `2d58215`). The class of bug this
check hunts (a close-out that flips the ledger without the merge reaching master) is not present
elsewhere in the sampled window; AT-483 itself is the one known instance and it is now resolved.

**Non-findings confirmed, not re-filed:**
- **Bypass check (26 commits):** only two touch `src/`/`tests/` — `d5db88b` (T-123: AT-085
  `/healthz` + AT-065 rubric-stamp migration; manifest `qa/manifests/t123-medium-batch.md` →
  verdict `97d74d7` → close-out `17a8a3d` → merge `18ff2a9`) and `9673f6b` (AT-483, already
  reconciled by the prior sweep and re-landed `87e247b`/`2d58215`). Both trace to a proper
  manifest→verdict handshake. All other commits are decisions (`ea6b7c3`/`310e7c1`, both
  `Approved-by: Umesh` per the Lab Protocol), contract DRAFTs (checker-owned surface), gate/inbox
  writes, or tick stamps. CLEAN.
- **Pair-state reconciliation:** no manifest on master sits at `Status: ready-for-check` (both
  in-flight units live in their own worktrees, out of scope). `qa/.last-tick` fresh
  (`2026-09-24T21:50:55+05:30`, this session). No `qa/.paused`. CLEAN.
- **Delegation health:** `qa/delegation-ledger.jsonl` — no run-dispatch gap (the one external
  `ollama/deepseek-v4.1-flash` unit, `at119-vocab`, carries a matching `run` row); weak-executor
  check `n=1` for that `(task_class, executor)` pair, below the ≥10-unit sample floor — no finding.
- **Gate-answered-off-disk:** all five gates touched this window
  (`t125-d039-entry-draft`, `t165-d039-traversal-scope`, `at086-at087-credential-exemption-scope`,
  `at365-data-class-declaration`, `at110-approval-forgery`) carry a real `Answered:` line dated
  2026-09-24T16:32:17+05:30. Zero found answered-off-disk.
- **Contract staleness:** the six new DRAFT contracts (`catalog.md`, `network-assertions.md`,
  `crawl-traversal.md`, `run-trace.md`, `parallel-run.md`, `skills.md`) are correctly `DRAFT` —
  authored this window, no unit has built against any yet. No stale criterion found elsewhere.
- **Enforcement liveness:** `.claude/settings.json` hooks (`SessionStart`, `PreToolUse`,
  `SessionEnd`) all resolve to files on disk (`qa/hooks/mc-sessionstart.ps1`,
  `.claude/hooks/lab-session-start.ps1`, `qa/hooks/mc-precommit.ps1`,
  `.claude/hooks/decisions-append-guard.ps1`, `.claude/hooks/lab-session-end.ps1`); `qa/loop.md`'s
  Stop/Human-gate lines uncontradicted by `qa/adapter.json`; repo has commits (HEAD `f1b8569`).
  CLEAN.
- **Data-boundary (MC-003):** still fires — `qa/adapter.json` has no `data_class`, by design now
  (see AT-365 close-out above). Not re-filed as a fresh finding; codified in the contract's No-fire
  list.
- **Goal-coverage:** `.goal/goal.json` = **38/64 done (59%)** — done count unchanged (T-164 last
  closed it), total rose 55→64 via D-041's T-172..T-178 registration (+9, all `pending`, deps
  satisfied or `[]`). No drift: no requirement newly `missing` with no source, north star unedited.
- **Goal-drift / re-grill:** `qa/.regrill-due` absent. No new GRILL trigger.
- **Silent-failure hunt** over `d5db88b`'s new code (`ui/routes_live.py::healthz`,
  `_newest_source_mtime`): none found — the one fallback (`if not mtimes: return
  _PROCESS_STARTED_AT`) is a benign empty-directory case, not an error swallow.
- **Doctor + ruff, re-run at HEAD `f1b8569`:** `uv run autotester doctor` → `doctor: clean`;
  `uv run ruff check src tests scripts` → `All checks passed!`. Full `pytest` NOT run per dispatch
  (RAM; a build running).
- **Token ledger:** re-measured, `opus_sub_share=0.0` (0/250,154,319 sub-agent tokens are Opus; 16
  sub-agents, all `claude-sonnet-5`), 0 compactions, no unit at fix cycle 3 this window — under the
  25% diet threshold, no finding. Line appended to `qa/token-ledger.jsonl`.
- **Structural erosion:** no new signal — only `ui/routes_live.py` (first touch) and the already
  known `explore_*` files (AT-483 saga, unchanged this window) were edited; `AT-488`/`AT-502`
  carried, numbers unchanged.

### TOP-3 BUILDABLE NEXT UNITS (2026-09-24b refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **T-172 — Run trace** (`trace.jsonl` per run: stage + LLM spans, model/tokens/latency/cost/fallback/verdict + UI panel; D-041, deps `T-163` ✓) | Newly registered, dependency satisfied, no human gate; contract `run-trace.md` (DRAFT) already authored this window. |
| **2** | **T-173 — Parallel case execution** (N isolated browser contexts bounded by measured RAM/CPU + `project.max_parallel`; write-policy cases serial; D-041, deps `T-163` ✓) | Same readiness as T-172; contract `parallel-run.md` (DRAFT) already authored this window. |
| **3** | **AT-086/AT-087 (medium×2)** — both gate-answered ("go with the best": AT-087 per-field exemption kept in the join; AT-086 explicit declared `.env` public-key allowlist), deferred by T-123, not yet built. | Decision no longer blocks; smallest well-scoped buildable unit left with a resolved gate. |

**Queued after top-3, per the standing build-order plan:** T-175 (Prompts as SKILL.md, deps `[]`,
no contract yet), T-126 (adapter allowlist, gate-answered "allow krr dee"), AT-335 (modal crawl
determinism — worktree already prepared at `.worktrees/at335-modal-determinism`). **In flight,
not re-queued:** T-170 (network-assertions, `.worktrees/t170-network-assertions`), AT-110
(approval signing, `.worktrees/at110-approval-signing`).

**Deprioritised (not cancelled):** AT-497/AT-545 (orphaned-running-crawl heartbeat, folded into
the now-merged AT-483 fix) · AT-488/AT-502 (structural-erosion signals, advisory only) · AT-556
(loop-liveness observation, low) · AT-546 (checker-owned `require_consent` contract re-point) ·
AT-529 (HUMAN_GATE, Pathlynks test-account credentials).

### HUMAN_GATE — do not build as ordinary units (re-verified on disk this sweep)

| Gate | Status |
|---|---|
| `live-crawl-target.md`, `post-login-forms.md`, `erp-credentials.md`/AT-529 | Still unanswered — blocks the live post-login acceptance run. |
| `t162-contract-approval.md` | Still unanswered (T-162…T-169 umbrella; individual chains since split and separately gated/answered). |
| `at438-u14b-baseline.md`, `commit-before-verdict.md` | Other session's AT-438; protocol departure. Unchanged. |
| `at416-clip-vs-reach-direction.md`, `at383-loop-status-consumer.md` | Still unanswered. |
| `at147-expiry-end-of-day.md`, `at218-vacuous-guard-class.md`, `t136-model-credentials.md` | Still unanswered. |
| `at253-agent-fallback-wiring.md` | Still unanswered (ARCHITECTURE Execution-model D-entry). |
| ~~`t165-d039-traversal-scope.md`~~ | **Answered 2026-09-24** (D-040 approved) — removed from this table. |
| ~~`t125-d039-entry-draft.md`~~ | **Answered 2026-09-24** (D-039 appended) — removed from this table. |
| ~~`at365-data-class-declaration.md`~~ | **Answered 2026-09-24** — AT-365 closed wontfix, removed from this table. |
| ~~`at110-approval-forgery.md`~~ | **Answered 2026-09-24** (option 1) — build dispatched; removed from this table (no longer a *decision* blocker, tracked as an in-flight unit instead). |
| ~~`at086-at087-credential-exemption-scope.md`~~ | **Answered 2026-09-24** ("go with the best") — removed; tracked as TOP-3 #3 above instead. |

**Terminal state: `FINDINGS: 0`** (0 new issue ids; 1 closed `open → wontfix` — AT-365; 3 rows
annotated — AT-110/AT-086/AT-087 gate-answered notes; 0 bypasses; AT-483-class ancestry re-check
CLEAN across 24 sampled SHAs; contracts + enforcement + delegation health CLEAN; goal-coverage
38/64, no drift; 5 gates newly answered and removed from the open-HUMAN_GATE table; HEAD
`f1b8569`).


## Sweep refresh — 2026-09-25 (sharded Mode B; 3 read-only shards + consolidation, single writer)

Refreshed **2026-09-25T06:07:48+05:30** (system clock, AT-399). Window `f1b8569..8a97eca`, 103
commits (master moved on during the sweep: the T-172 close-out `d03fdfb` and this sweep's own writes).
**This section supersedes every TOP-3 and HUMAN_GATE table above it.** The 2026-09-24b sweep stamped
`.last-sweep` without appending a queue section — that drift was T-126's "QUEUE drift" item, closed here.

**GRILL — human decision, not a build row (carried, unanswered):**
- GRILL: recurring vacuous-guard prevention policy (AT-218). Two fresh instances this window —
  AT-561's empty-redactor gate and AT-565's unguarded session factory — both caught by checks.
- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281).
- GRILL (AT-402): structure-before-code review of `visual_order.js`.

### Findings this sweep — FINDINGS: 3

| Issue | Sev | What |
|---|---|---|
| **AT-565** | high | PR6 crash isolation covers `run_fn` only: `stages/parallel_run.py::_run_one` calls `session_factory(case)` outside its try, so one case's context-launch failure aborts `run_cases` and discards every sibling's result. Missed by the t173 checker PASS (its PR6 row only mutated the `run_fn` except-clause). **T-173 reopened**; fix folded into at562-564-live-wiring. |
| AT-566 | medium | `qa/loop.md:53` — `BLOCKED` re-arms `ScheduleWakeup 300s` with no cap, unlike HUMAN_GATE (max 8) / STALLED (3 cycles) / EXHAUSTED (stop): "can it spin" = yes. |
| AT-567 | medium (erosion signal, never a blocker) | `ui/helpers.py` (223→300 over 6 credential-guard commits in 14 days) and `stages/explore_node.py` (9 commits in 14 days) both at the C2 300-line cap. |

**Extended, not re-filed:** AT-564 now also names T-163 — the resumable orchestrator has no CLI/UI
caller, and unlike T-172/T-173 this is undisclosed (FEATURES F-045 is `live`, target.md M8 ticks T-163
with no caveat). Maker to add the caveat until at562-564 lands.

**Applied this sweep (checker-owned surfaces):** reverify sample 8/8 VERIFIED → `verified` (AT-528,
AT-531, AT-532, AT-540, at540-cycle1 rows of AT-547..AT-550; AT-532's pin stays weak, pre-existing
note) · contracts `parallel-run.md`, `run-trace.md`, `skills.md` DRAFT→ACTIVE (each pre-authorized by
its own status line) · inbox 2026-09-24T23:00 D-042 entry folded → `agent-layer.md` AL2/AL3/AL4 ·
`at110-approval-forgery.md` header closed · token ledger appended (opus sub-agent share 0.0, no unit at
fix cycle 3) · **T-126 closed** (allowlist, SNAPSHOT drift, ledger backfill, QUEUE drift all met).

**Non-findings (not re-filed):** bypass CLEAN across all 103 commits (every src/tests/scripts commit
traces to a manifest → matching-cycle PASS: t172 c2, at110 c2, at560, t173, at086-087, t175,
d042-registration, t170, fix-t175-criticality) · pair state CLEAN (building worktrees at335,
at562-564, t125-catalog correctly have no manifest yet; `.last-tick` fresh; not paused) · delegation
CLEAN (all `claude-sonnet-subagent`; no pair at the 10-unit floor) · data boundary = the accepted
AT-365 signal only · enforcement CLEAN (5 hooks present, D-037-authorized; `qa/loop.md` Stop lists the
seven states) · goal drift CLEAN (no `.regrill-due`, north star unedited since the last amendment,
every STALLED stamp has its `qa/debug/` report, no gate answered off-disk) · **proposed, not applied:**
orchestrator contract OR7 "reachable from a real entry point (CLI command or UI route), not
test-only" — the remedy for loop-design "can it Goodhart the verifier" (AT-562/AT-564/F-045); a new
criterion needs an authorizing D-entry.

### TOP-3 BUILDABLE NEXT UNITS (2026-09-25 refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **at562-564-live-wiring** (in build) — CLI/UI run entry points through `StageContext(secrets=...)` and `run_cases`, **plus the AT-565 PR6 fix** | Closes AT-562, AT-564, AT-565 and re-closes T-173; must land before parallel execution reaches real runs. Checker bar: every non-browser test file green; real Mode D (UI entry points change); a PR6 test in which the FACTORY raises. |
| **2** | **AT-566** — cap `BLOCKED` in `qa/loop.md` like HUMAN_GATE | Small; stops the loop spinning on a persistent environment block. |
| **3** | **AT-567** — split `ui/helpers.py` by responsibility before the next credential-guard fix (then `stages/explore_node.py`) | Zero headroom under the 300-line cap; a split under deadline pressure is how guards get dropped. |

**In flight, not re-queued:** at335-modal-determinism, t125-catalog. **Deprioritised (unchanged):**
AT-497/AT-545 · AT-488/AT-502 (erosion, advisory) · AT-556 · AT-546.

### HUMAN_GATE — do not build as ordinary units (re-derived on disk this sweep)

Re-derived strictly: a gate is open only if it has **no line beginning `Answered:` + a date** (a plain
grep for "Answered:" also matches each gate's own how-to-answer text and wrongly reads every gate as
answered).

| Open gate (11) | Blocks |
|---|---|
| `erp-credentials.md` / AT-529 | the live logged-in ERP runs (T-122, T-136, T-145) |
| `at147-expiry-end-of-day.md` | whether a bare-date approval expiry means start or end of day (CN4) |
| `at218-vacuous-guard-class.md` | the vacuous-guard prevention policy (GRILL above) |
| `at253-agent-fallback-wiring.md` | the ARCHITECTURE execution-model D-entry for the agent fallback |
| `at383-loop-status-consumer.md`, `at416-clip-vs-reach-direction.md` | carried |
| `at438-u14b-baseline.md`, `commit-before-verdict.md` | the other session's AT-438; protocol departure |
| `at516-evidence-spec-splitting-policy.md`, `at520-scripts-line-cap.md` | carried |
| `t135-url-pattern-data-migration.md` | the one-off url_pattern backfill |

**Correction to the tables above:** `live-crawl-target.md`, `post-login-forms.md` (both answered
2026-09-21), `t136-model-credentials.md` (answered 2026-09-09) and `t162-contract-approval.md`
(answered 2026-09-21) were still listed as "unanswered" by the 2026-09-24b table. They carry dated
`Answered:` lines and are **not** blockers. Also closed since that table: `d042-deep-agents.md`
(2026-09-24).

**Terminal state: `FINDINGS: 3`** (AT-565 high, AT-566, AT-567; AT-564 extended; T-173 reopened;
T-126 closed; 8/8 sampled fixed rows verified; bypass CLEAN; HEAD at stamp `8a97eca`-window, commit
`89f5b3a` + this correction).


## Meeting-input refresh — 2026-09-26 (checker goal-coverage review of the 2026-09-25 counselor-tool meeting)

Source: Umesh shared the transcript of the counselor-tool meeting. It asks for exactly AutoTester's job: a tester agent
separate from the builder, testing "as a tier-2 counselor", happy AND negative paths on every release, a reviewable
video, "run the 50 cases", and written checklists so a known bug never comes back. The checker mapped each ask against
the repo with file:line evidence and filed **AT-581..AT-589**. Contracts were tightened by **D-045**: execute.md E6 and
report-export.md RE6.

### TOP-3 BUILDABLE NEXT UNITS (meeting refresh)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-581** — enact VIEWPORT_MOBILE / LOCALE_I18N (per-case viewport/locale), or report not-run | High. These cases pass today at desktop size in the default locale, a false-pass class the north star counts. Closes execute.md E6. |
| **2** | **AT-582** — show each failure's reason, fix_hint and repro steps in both exports | Medium and cheap. The judge already writes these; the developer report drops them. Closes report-export.md RE6. |
| **3** | **AT-585** — known bug -> pinned p0 regression case in every release run | High. Answers "why does this bug keep coming back" (e.g. Google sign-in dropping signup data). |

**Extend existing tasks rather than creating new ones:** T-166 += structured scenario variants (AT-586); T-125 += standard
packs for OAuth sign-up carry-over, month/year pickers and Excel column-mapping upload (AT-588); T-180 += an explicit
judge vendor with a warning when judge == agent (AT-589).

### HUMAN_GATE (new, open)

| Gate | Blocks |
|---|---|
| `meeting-user-persona-ux-judging.md` | AT-583 user personas, AT-584 advisory UX/comprehension judging |
| `meeting-run-video-scope.md` | AT-587 run video recording (always vs on-FAIL, retention, secret masking) |

**Out of scope for this repo (noted only):** the seminar-capture agent, audio-first counselor UX, and removing the Gemini
dependency from VTC belong to other Vidysea projects.

## Sweep 2026-09-26

Mode B, sharded (3 shards + consolidation), window `a49c3b8..HEAD`. Full report:
`qa/verdicts/sweep-2026-09-26.md`. 4 new rows filed (AT-613..AT-616), 0 fixed→verified flips, 1
instrument gap (shard 1 returned empty — checks 1/2/3/1c did not run this cycle).

### TOP-3 NEXT UNITS (this sweep)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-616** — reproduce the AT-608/AT-609 regression-check red/green split cleanly, then flip both `fixed -> verified` | Blocks closing out two already-fixed secret-leak rows; the discrepancy itself (real-path pytest run stays green with the fix reverted) is worth a second pair of eyes before it's dismissed as tooling noise. |
| **2** | **AT-614** — split `src/autotester/core/redact_fold.py` off the 300-line cap | Same remedy AT-567 already proved out for helpers.py/session.py/routes_runs.py; do it before the next redact fix has to work in a file with zero headroom. |
| **3** | **AT-613** — re-run the real `autotester snapshot` generator over `docs/SNAPSHOT.md` | The file every SessionStart hook injects is currently missing F-057/058/059 and T-182/183/184; cheap, high-leverage fix. |

### GRILL: (carried, unchanged by this sweep)

- AT-218, AT-281, AT-402 — untouched this window, out of scope for shards 2/3 (check 6 owns them,
  ran but did not re-verify; still open, not re-litigated here).

### Proposed folds for the standing checker (not applied by this sweep)

- **AT-582**: stale — its named fix shipped via T-183 (checker-PASSed) and is confirmed live in
  `stages/report_export.py`. Flip to `fixed`/`fixed_by: T-183`, or narrow the title to the
  still-open must-fix/suggestion split noted in `docs/FEATURES.jsonl` F-057.

---

## Sweep 2026-09-27 (Mode B, sharded — 3 read-only shards + consolidation; window `a49c3b8..HEAD` + working tree)

14 new rows (AT-630..AT-631, AT-634, AT-636..AT-644 — AT-632/633/635 were filed then retracted
mid-sweep, see below), 4 existing rows updated (AT-218 open→fixed, AT-253 checker_note + gate
answered, AT-567 scope widened, AT-614 open→fixed resolved-by-at611), and one new contract
invariant (`core-invariants.md` C12). 0 reopens: AT-408/AT-416 already `open`, so reopen-power was
not applied — stated per the dispatch's own instruction rather than reopened a second time.

**Corrections applied mid-sweep (live orchestrator input, verified before acting on any of it):**
- **AT-253**'s gate was reported by shard 2 as "18 days stale, no answer" — in fact
  `docs/DECISIONS.md` D-031 (2026-09-22) already answered it ("wire, not retire — Umesh
  2026-09-22") off-disk; filed as AT-637 `gate-answered-off-disk`, gate file now carries the
  `Answered:` line.
- **`wave/at408-416-scroll-reach` and `wave/t125-catalog`** were reported by shard 1 as abandoned
  (filed AT-632/AT-633, severity high) — the maker orchestrator confirmed both are actively being
  built right now. Retracted; replaced by ONE row, AT-643, severity medium, type
  `unmerged-work-unsurfaced` — the real finding is that nothing surfaced the 2-day-old unmerged
  state until a human enumerated worktrees, not that the work was abandoned. Neither branch is
  queued as work here; the maker owns them.
- **`qa/.last-tick`**'s truncation was reported by shard 2 as an open defect (filed AT-635) —
  by the time this sweep read the file it was already restored and committed. Retracted; replaced
  by AT-644, severity high, type `last-tick-unguarded-write`, aimed at the missing guard rather
  than the (already-fixed) symptom. Verified live this sweep: `uv run autotester loop-status
  --strict` now correctly reports `SLEEP 34.3h 2026-09-25T15:37:11Z -> 2026-09-27T01:55:02Z`
  instead of a false all-clear.
- **`verdict-lost-on-death`** (AT-641) was filed claiming two consecutive losses on
  `at621-exit-call-aliases` — the second attempt had in fact completed and PASSed (verdict
  `14f13a22`, ledger flipped, T-195 closed). Corrected to ONE confirmed loss, severity downgraded
  medium→low, and a second instance of the same failure MODE folded in instead: that checker's own
  `qa/delegation-ledger.jsonl` append sat uncommitted in the shared tree at consolidation time
  (confirmed via `git status`/`git diff`).
- **AT-621/AT-626/AT-627** were NOT touched by this sweep at any point (a concurrent Mode A check
  owned them and completed independently); re-verified untouched at the end.
- Bypass window extended to include `c473ceb8..HEAD` per the orchestrator's note — the PLAN-gate
  backfill commit `f73d9071` (`docs/intent.md`/`spec.md`/`plan.md`/`qa/gates/plan-approved.md`)
  falls inside it and traces to a real, disclosed backfill, not a bypass.

**New this consolidation, at the orchestrator's request:** `qa/contracts/core-invariants.md` C12
— "every health signal the loop reports must fail closed" — naming AT-644/AT-641/AT-643 as its
three measured instances (one criterion for the class; the three fix units below stay separate,
per C7's own no-vague-multi-file-unit shape).

### GRILL — human decision, not a build row (carried; AT-218 removed — answered and folded this sweep)

- GRILL: real two-mode acceptance thresholds for D-023/T-169 (AT-281). Carried, now also
  corroborated by AT-638 (goal-coverage-gap: 5 north-star capabilities with zero checkable
  criteria, T-169 itself among the consequences).
- GRILL (AT-402): structure-before-code review of `visual_order.js`. Carried, untouched this
  sweep (out of scope for shards 2/3, not re-verified).

### TOP-3 BUILDABLE NEXT UNITS (2026-09-27 sweep, re-ranked after corrections)

| # | Unit | Why |
|---|---|---|
| **1** | **AT-644** — a write guard on `qa/.last-tick` that refuses a truncating write (C12's namesake instance). Needs a `docs/DECISIONS.md` entry with `Approved-by: Umesh` first — it touches an enforcement path. | Highest-severity buildable item this sweep produced; the AT-368 dead-loop detector is worthless if its own input file can be silently truncated, and it already happened once. |
| **2** | **AT-639** — add `timeout=` (+ a narrow `except subprocess.TimeoutExpired`) to `src/autotester/media/chunks.py::encode_chunks`'s `subprocess.run` call, matching the pattern already proven in `media/frames.py`/`media/transcribe.py`. | High severity, small and mechanical, no gate — copy the sibling pattern. |
| **3** | **AT-638 / T-150** — register the Track C tasks and file `docs/ai-target.md` + `docs/adversarial.md` criteria (governance-only, per the task's own scope). | Cheapest unblock for the 5-capability goal-coverage gap (T-166/167/168/171/150-155); no gate, no design question. |

**C12's other two child units evaluated, do not outrank the above (per the orchestrator's own
instruction not to let them displace higher-severity items just for arriving last):** the
incremental-verdict-write fix behind AT-641 is severity **low** (already being applied by
convention in the in-flight third at621-class attempts) · the worktree-enumeration fix behind
AT-643 is severity **medium**, real but not urgent. Both stay queued below top-3.

**Deprioritised (not cancelled):** AT-643's worktree-enumeration remedy (medium) · AT-641's
incremental-verdict-write remedy (low) · AT-630 (hook regex fix — enforcement path, needs its own
DECISIONS entry + `Approved-by: Umesh`) · AT-634 (31-row regression_check backfill, medium,
opportunistic).

### HUMAN_GATE — do not build as ordinary units (re-verified this sweep unless noted)

| Gate | Blocks |
|---|---|
| `at218-vacuous-guard-class.md` | **Answered 2026-09-26, folded this sweep** — removed as a gate; the guard-authoring rule is now embodied in Mode A step 4b. |
| `at253-agent-fallback-wiring.md` | **Answered 2026-09-22 (D-031), gate file corrected this sweep** — no longer a standing gate; AT-253 (wiring itself) is now an ordinary buildable unit. |
| `at281-...` (no gate file; GRILL only) | Real two-mode acceptance thresholds for T-169 — carried, unanswered. |
| AT-644's DECISIONS-entry prerequisite | Not a gate FILE, but the write-guard unit cannot build without one — named here so it isn't picked up as an ungated fix. |
| Everything else in the 2026-09-26b table above | Unchanged, not re-verified individually this sweep (out of scope — this sweep targeted the shards' own findings, not a full gate resweep). |

**Terminal state: `FINDINGS: 11`** (AT-630 medium; AT-631 low; AT-634 medium; AT-636 medium→fixed
(folded); AT-637 high→fixed (gate corrected); AT-638 high; AT-639 high; AT-640 low; AT-641
low (corrected, single-loss + uncommitted-ledger instance); AT-642 medium; AT-643 medium
(supersedes retracted AT-632/AT-633); AT-644 high (supersedes retracted AT-635) — 11 rows stand,
3 filed-then-retracted (AT-632/633/635) removed cleanly before being seen anywhere else; 4
existing rows updated (AT-218 fixed, AT-253 noted, AT-567 rescoped, AT-614 fixed); 1 new contract
invariant (core-invariants.md C12); 0 reopens; token-ledger line appended; AT-621/626/627
untouched throughout.

## Added 2026-09-27 by the maker orchestrator (not a sweep finding — an owned regression)

| Unit | Issue | State | Note |
|---|---|---|---|
| `iss-at638-2-done-check-repair` | `ISS-at638-remainder-2` (high) | **QUEUED — blocked on the in-flight wave, not on a decision** | Two tests in `tests/test_goal_done_checks.py` are red on `master`. Reproduced by the orchestrator directly, not taken on the filing checker's word. |

**Two distinct defects under one issue:**

1. **The pin was never carried out for T-185..T-195.** `test_revised_goal_contract_is_registered`
   asserts `progress["total"] == len(data["tasks"]) == 70`; `goal.json` now holds **81**.
2. **Five PENDING tasks carry `done_check`s that cannot fail** — T-186, T-189, T-190, T-191, T-192.
   Four are `uv run pytest tests/ -k <keyword>` matching pre-existing unrelated tests; T-192's is
   literally `uv run autotester doctor`. None carries a `done_check.waiver`. This is the AT-100
   shape the failing test's own docstring names.

**Owned, because it is mine.** `git log -S` traces the 70→81 jump to **`f9e7d406`** (2026-09-27
15:23), my own commit earlier this session, landing goal state that earlier sessions had left
unclaimed in the working tree. **Every prior registration in this repo pinned its rows in the same
commit** — `5374567c` ("pin T-170/T-171 deps + done_check"), `36c357fc`, `7913387d` all did. Mine
did not. Worse, its message says *"Validated before landing: progress block matches the task list
exactly, no duplicate task ids, analytics.json parses"* — three validations, none of them the test
that exists to guard this exact file. The suite has been red on `master` since 15:23 today.

**Why it stayed invisible:** every check since has seen the suite through a partial or truncated
run. The `at638-remainder` checker was the first to let it finish, and only caught it after noticing
its own near-miss (it had piped pytest through `| tail -40`, which reports the pipeline's exit code
rather than pytest's — the masking `qa/adapter.json` warns about, and the second instance of that
exact trap this session).

**Why it is not being fixed right now, with the dependency named:**
`SERIAL: iss-at638-2-done-check-repair waits on the checkers of T-186, T-189, T-191 and T-192.`
Defect 2 rewrites the acceptance criterion of four units whose checks are running this minute.
Changing a `done_check` under a live check is changing the rules mid-judgement, which is worse than
a red suite that is already understood and recorded. Defect 1 alone is safe to fix but would leave
the file half-green, and would collide with the unit that fixes the rest — so both wait together.

**Do not fold this into any of the four in-flight units.** Their manifests must not claim a
`done_check` as acceptance (the T-192 manifest states this explicitly and its dispatch told the
checker so). The repair is its own unit with its own check.

## ISS-at542-lost-correction — a ledger correction has been sitting in an orphan stash for 5 days

**Found:** 2026-09-27 by the maker, while verifying the tree after the T-189 checker's stash/merge
dance. **Not created by that checker** — the stash predates it by five days.
**Severity:** high (the ledger is the honesty surface; this is a false claim left standing, not a
missing nicety). **Owner:** unassigned. **Blocks:** nothing.

`git stash list` carries one entry, `stash@{0}: On master: checker-temp-at540`, dated
**2026-09-22 15:19:15 +0530**. It contains three files, and one of them is real lost work:

```
.goal/dashboard.html | 2 +-      <- stale, superseded
.goal/goal.json      | 8 ++--    <- stale, superseded
docs/FEATURES.jsonl  | 1 +       <- NEVER LANDED
```

The `FEATURES.jsonl` row is an **`event: updated` correction to F-039**, written for **AT-542**
(checker sweep 2026-09-22). Its substance: F-039 shipped claiming "two-model ensemble … counting
where two models independently agreed", when the honest state was **ensemble-capable code,
ensemble-of-one practice** — the UI built `[providers.get(vision)]` and the CLI defaulted
`--models` to gemini alone, and all 3 erp issue rows carry `models_agreeing=1`,
`model_labels=[gemini]`.

**Why this is worth a unit rather than a note:**

1. **`AT-542` is marked `fixed` in `qa/issues.jsonl`** — closed on the strength of a correction
   that never reached the file. The issue ledger and the feature ledger disagree, and the feature
   ledger is the one a human reads.
2. **F-039 on `master` still carries the overstated claim today**, unamended.
3. **The id was silently reused.** The stashed row was `F-044`; `F-044` on master is now
   `source-adapters` (T-162, 2026-09-23). So the correction cannot be applied as-is — it needs a
   fresh id (next free is **F-061**).

**What I deliberately did NOT do.** `docs/FEATURES.jsonl` is append-only and the project rule is
that a ledger row is added via `autotester ledger add` with a **prefilled reason shown to Umesh to
confirm or edit** (D-004). Hand-applying a five-day-old stashed line into an append-only file, on
my own authority, is exactly the move that rule exists to prevent — and an append is not
reversible. The stash is **left in place**, not dropped, so the original wording survives.

**Residual risk while this sits:** another checker doing the same stash-merge-pop dance may stash
on top of it, and a future `git stash clear` would destroy the only copy. The wording is quoted in
full in this queue row as a second copy for exactly that reason.

**Next action:** one small unit — re-add the correction as `F-061` via
`autotester ledger add`, with the AT-542 wording as the prefilled reason, then drop the stash once
the row is on master.

---

## Sweep 2026-09-27b (bookkeeping-only, five-priority dispatch)

Bound to `D:/autoTesting`. Scope: `qa/issues.jsonl` re-triage + gate fact-check + manifest audit
only -- no product-code fixes, no unit PASS, `.goal/goal.json`/`.goal/dashboard.html` left
untouched (concurrent orchestrator ownership), `docs/DECISIONS.md` and all `wave/*` branches
untouched.

**P1 -- ISS-at638-remainder-2 diagnosis: HOLDS, framing is stale.** `f9e7d406` landing 81 goal
tasks (parent had 70) without pinning the new test is confirmed the root cause --
`tests/test_goal_done_checks.py` reproduces both named failures live
(`test_no_pending_task_has_a_done_check_that_cannot_fail`,
`test_revised_goal_contract_is_registered`), exactly the expected/pre-existing count. But the
row's "five pending tasks, blocked on an in-flight wave" framing no longer matches
`.goal/goal.json`: T-186/T-189/T-192 are already `done`, T-191 has no build currently in flight,
and T-190 isn't even named on the row's own SERIAL dependency line. Not corrected in the row
itself (`.goal/goal.json` cross-checks only, no edit made to the issue) -- flagging for whoever
next reads it so the staleness doesn't get taken as current.

**P2 -- re-triage of the open/fixed tail.** Promoted to **`verified`** with a genuine isolated
green-before/red-after/restored falsification (scratch copy outside the bound tree, `.venv`'s
forced `sys.path` `.pth` entry stripped and reasserted per row so the copy's own code ran, not
the real repo's -- confirmed via `autotester.__file__`):
- **AT-284** (`ui/helpers.py::_require_reachable_base_url` + `app.py` guard ordering) --
  `uv run pytest tests/test_ui_credential_exemption.py::test_a_credential_pasted_into_base_url_is_not_echoed_back`
- **AT-341** (`browser/session.py::check_destination`) --
  `uv run pytest tests/test_browser_navigation_secrets.py::test_goto_still_refuses_a_resolved_destination_outside_project_domains`
- **AT-350** (`stages/explore.py::_finish` scrub) --
  `uv run pytest tests/test_explore_secret_scrubbing.py::test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl`

Flipped `open -> fixed` (existing independent PASS/regression evidence found, but not the
personal-falsification bar `verified` needs):
- **AT-408/AT-416** -- `qa/verdicts/at408-416-scroll-reach.md` cycle 1 PASS (13/14 + 5/5), own
  re-run of `tests/test_browser_scroll_reach_at408_416.py` green.
- **AT-368** -- live `uv run autotester loop-status --strict` behavior + `tests/test_loop_status.py`
  all green.
- **AT-420** -- gate-text correction commit `7d98b64d`; `regression_check: null` per the project's
  own prose-fix precedent (AT-218/AT-636/AT-637).
- **AT-447** -- this sweep itself is "the pair seeing it", which was the procedural complaint.

**New finding -- AT-647** (medium, `done-check-cannot-pass`): found while re-checking AT-408/AT-416
-- `.goal/goal.json` T-185's `done_check.cmd` names `tests/test_scroll_reach.py`, which does not
exist (the real file is `tests/test_browser_scroll_reach_at408_416.py`); the command can never
exit 0 as written, mirror-image of ISS-at638-remainder-2's always-passes shape. Not fixed here --
`.goal/goal.json` is off-limits this run.

**P3 -- four HUMAN_GATE files, zero false claims.** Independently re-derived every citation in
`t125-stalled-at-cycle-cap.md`, `t125-ct6-tiered-dispatch-vs-ru3.md`,
`at638-four-contract-files-authorization.md`, and `t192-narrowed-command-ratification.md`: commit
hashes exist/don't-exist exactly as claimed, file:line quotes match verbatim
(`explore_merge.py:50-51`, `schema/case.py:22`, `stages/expand.py:55-56`,
`schema/catalog.py` on `wave/t125-catalog`), the at638 gate's five-row precedent table checks out
against `docs/DECISIONS.md` D-017/D-018/D-039/D-040/D-041/D-042 exactly, the t192 gate's mtime
claim and its `.work/t192/screenmap.before.json` sha256 prefix (`46e97134a8...`) both reproduce
exactly. No option text touched -- the decision stays Umesh's.

**P4 -- ISS-at542-lost-correction reading confirmed accurate.** `git diff stash@{0}^ stash@{0} --
docs/FEATURES.jsonl` shows the stash adds one row, id **F-044**, `event: updated`, dated
2026-09-22T08:18:13Z, correcting F-039's "two-model ensemble" claim to "ensemble-capable code,
ensemble-of-one practice" (AT-542's own wording). Confirmed live: F-039 on master today is still
the original, unamended overstated claim (line 39); F-044 on master today is a *different*,
unrelated row -- `source-adapters` (T-162, 2026-09-23) -- so the id was reused by unrelated work
before the correction could land under it; the next free id is **F-061**. Stash left untouched
(neither applied nor dropped) per instruction -- `docs/FEATURES.jsonl` append-only discipline
(D-004) means this needs a prefilled-reason `autotester ledger add` shown to Umesh, not a
checker-authority stash-pop.

**P5 -- manifest audit (256 files), read every hit, not just grepped.** `Status: ready-for-check`
hits: only `at621-exit-call-aliases` and `t182-viewport-locale`, both confirmed genuinely
`checked-PASS` further down the same file (the two named false positives held). `STALLED`
mentions: 13 files, of which 9 are prose referencing a *different* manifest's stall or a
hypothetical ("if this cycle fails...") with their own status resolved to `checked-PASS` --
false positives, same shape as the ready-for-check ones. `EXHAUSTED`: 1 hit
(`at011-loop-md`), prose naming the terminal-state vocabulary, own status `checked-PASS` -- false
positive.

Four **genuinely terminal STALLED** manifests, all with a matching `qa/debug/<slug>-cycle3.md`
report as the project's own convention requires: `at015-at028-hook-adapter-fix` (STALLED then
recovered -> `checked-PASS`, closed correctly), `at345-346-fold-coverage` (STALLED after 3 cycles,
correctly handed to Umesh, not reopened), `at379-scrollable-pane-reachability` (STALLED after 3
cycles, correctly handed off) -- no action needed on these three.

The fourth, **`at438-display-contents`, is a dangling handshake**: its blocking
`qa/gates/at438-u14b-baseline.md` was **answered by Umesh on 2026-09-26T22:34:22+05:30** ("a + b +
c" -- rebaseline U14(b) against the pre-unit detector, close AT-438 under it, split AT-453 into its
own capped unit, accept AT-454 as a documented limitation) -- but nothing has acted on the answer
since: `git log --since="2026-09-26 22:30"` on the manifest/gate/ledger shows no commits, AT-438
still reads `status: fixed` (not closed under the new baseline), no AT-453 split-off manifest
exists, AT-454 isn't documented as an accepted limitation anywhere. Not actioned by this sweep --
rebaselining U14(b) and closing AT-438 is unit work, not bookkeeping. Flagging so it isn't lost
under `T-191`/`T-190` activity.

**New finding -- AT-648** (medium, `dangling-handshake`): `qa/manifests/x10b-form-typing.md` is
also terminally `STALLED` (cycle 3 of 3), but unlike the three genuine STALLEDs above it has **no**
matching `qa/debug/x10b-form-typing-cycle3.md` report, and its blocking defect (AT-539) was
**already fixed and independently reconfirmed** the same day by a checker sweep
(`qa/issues.jsonl` AT-539's own `checker_note`: "sweep 2026-09-22 ... FULL SUITE uv run pytest ->
1514 passed ... 0 failed ... Slot-1 instrument green again"), reproduced again live this sweep
(`tests/test_approve_cli.py tests/test_explore_typing.py` -> all green). The manifest was never
re-submitted for a cycle-4 check or closed on a verdict. AT-533/AT-536/AT-537/AT-539 (the four
x10b-cycle issues) all still read `status: fixed`, not `verified`, despite their own
`checker_note`s already describing a cycle-3 sabotage/restore falsification -- left as-is (`fixed`
is defensible; promoting to `verified` on someone else's already-embedded note rather than a
falsification run by me this sweep would be exactly the unverified-status-change P2 forbids).

**Left deliberately alone:** `.goal/goal.json`, `.goal/dashboard.html` (concurrent orchestrator
writes), `docs/DECISIONS.md` (append-only, not this sweep's write path), all `wave/*` branches, the
four gate files' options (Umesh's decision), the `checker-temp-at540` stash, and no `git push`
(sweep bookkeeping, D-007 doesn't apply here).

FINDINGS: 2 new (AT-647, AT-648) - 8 re-triaged (3 -> verified, 5 -> fixed) - 0 false gate claims -
1 confirmed-accurate stash reading, unapplied - 1 dangling human-gate answer surfaced (at438) -
1 dangling stalled-but-fixed manifest surfaced (x10b-form-typing)

## AT-648 — x10b-form-typing needs a verdict, not a fix cycle

**Source:** checker sweep 2026-09-27b (`bd69565d`). **Severity:** medium. **Blocks:** nothing.
**Diagnosis report (now written):** `qa/debug/x10b-form-typing-cycle3.md`.

`qa/manifests/x10b-form-typing.md` is `STALLED` at cycle 3 of 3, scoring **16/17**. Its single red
was **AT-539** (three stale imports of the removed `explore.require_consent` in
`tests/test_approve_cli.py` — the fourth sibling seam file). The follow-on retarget landed, and
AT-539 has since been confirmed green **twice by parties other than the maker**: a checker sweep
the same day (full suite, 0 failed) and again live in sweep 2026-09-27b.

**The stalling condition no longer exists.** What is missing is a verdict, not work.

**Next action — a checker re-pass, explicitly NOT a cycle 4.** A fix cycle is for a maker defect
and none remains. The re-pass judges one question: *is criterion 17 now met?* If yes, the unit
closes `checked-PASS (cycle 3)`. Until a checker says so the manifest stays `STALLED` — the
orchestrator does not promote it on its own reading, which is the same rule that correctly stopped
the maker self-certifying AT-539 in the first place.

**Held only by the RAM ceiling** (2.42 GB free at the time of writing → ceiling 0, two builds
live). Dispatch when a slot frees.

## at438-display-contents — an answered gate nobody acted on

**Source:** checker sweep 2026-09-27b. **Severity:** medium. **Blocks:** nothing directly.

`qa/gates/at438-u14b-baseline.md` was **answered by Umesh on 2026-09-26T22:34:22+05:30** ("a+b+c")
and nothing has moved on it since: no commit touches it, **AT-438 is still `fixed` rather than
closed under the new baseline**, and **AT-454 is undocumented**.

Worth stating plainly: this is the answered-gate failure mode, which is worse than an unanswered
one. Umesh spent the decision and the system did not collect it. Part of the answer *was* consumed
— D-048's 2-cycle cap was applied to T-186, which passed under it at cycle 1 — and the AT-453
split-off did happen as T-186. So the gate was partly acted on and then dropped, which is exactly
how the remainder became invisible.

**Next action:** one small bookkeeping unit — close AT-438 under the new baseline and document
AT-454. Not actioned by the sweep, correctly: it is unit work, not bookkeeping.

## AT-647 — T-185's done_check names a test file that does not exist

**Source:** checker sweep 2026-09-27b. **Severity:** medium. **Blocks:** nothing.

The mirror image of `ISS-at638-remainder-2`. Where those five `done_check`s can never **fail**
(Goodhartable), T-185's names a **nonexistent test file**, so it can never **pass**. Both are the
same underlying defect — a registered check that does not measure the thing it claims to — and
both should be repaired by the same unit. The sweep could not fix it: `.goal/` was off-limits to
it this run, deliberately, because the orchestrator holds uncommitted changes there.

**Fold into `iss-at638-2-done-check-repair`** rather than queueing separately — same file, same
defect class, and two units editing `.goal/goal.json` concurrently is the collision this queue
keeps warning about.

## Correction to ISS-at638-remainder-2's own framing

The sweep confirmed the **root cause holds** — `f9e7d406` landed 81 goal tasks against a parent of
70 without pinning the new test, and `uv run pytest tests/test_goal_done_checks.py` reproduces both
failures live. But its **"five pending tasks, blocked on an in-flight wave" framing is now stale**:
T-186, T-189 and T-192 are `done`; T-191 is mid-cycle-2; T-190 is not even named on the row's own
dependency line. The sweep flagged rather than edited it, which was right. Recorded here so the row
is not read as a current description of the backlog.

## ISS-ledger-duplicate-ids — qa/issues.jsonl carries 10 duplicated ids

**Found:** 2026-09-27 by the maker orchestrator while resolving an append-only merge conflict on
`qa/issues.jsonl`. **Pre-existing on `master`, not caused by that merge** — verified by counting ids
on the merge parents before committing the resolution.
**Severity:** medium. **Blocks:** nothing. **Owner:** unassigned.

`master`'s `qa/issues.jsonl` has **657 rows but only 647 unique ids**. Ten ids appear twice:

```
AT-288  AT-289  AT-290  AT-291  AT-547
AT-548  AT-549  AT-550  AT-551  AT-552
```

`CLAUDE.md` names this file **canonical** for open issues, and a canonical store with duplicate
primary keys means any consumer that indexes by id silently sees one row and not the other. Which
one wins depends on iteration order, so two readers can legitimately disagree about an issue's
status. Note that four of the duplicates — **AT-548/549/550** plus AT-547 — are the
*vacuous-guard/unisolated-capability* rows this project cites constantly as precedent; a reader
resolving them by id could pick up the stale copy of exactly the rows most often used as authority.

**Not fixed here, deliberately.** Deduplicating means choosing which copy is authoritative, and the
two copies may differ in `status` or `regression_check` — that is a judgement about issue history,
not a mechanical cleanup, and it is checker territory rather than the maker's. Doing it during a
live wave with three agents writing the file would also be the worst possible moment.

**Next action:** a small `/checker` unit that, for each of the ten, diffs the two rows, states which
is authoritative and why, collapses them, and adds a `doctor` check asserting id-uniqueness so the
class cannot recur. **Hold until the current wave drains** — `qa/issues.jsonl` has had three
concurrent writers this session and already produced one merge conflict.


### CLOSED as already-ruled — `ISS-ledger-duplicate-ids` was a relitigation, and I filed it

**Closed by:** the maker orchestrator, 2026-09-27, on evidence that pre-dates the row.

The ten ids are real, and `qa/issues.jsonl` does carry 662 rows against 652 unique ids. Everything
after that in the row above is wrong, and the row should never have been filed:

- **All ten colliding rows already carry an `id_collision` field** explaining the collision and naming
  the disambiguator (`checker`). Not one of them is an undetected duplicate.
- **They are not duplicate copies — they are unrelated issues sharing an id**, minted concurrently by
  two checkers in a dual check. AT-547 is both "three ledger-row fixes landed as bare commits" and
  "at540 unit deleted three existing tests". That is worse than a duplicate, and it is precisely what
  the annotations exist to flag.
- **A checker already ruled on this and a whole unit already reconciled it**:
  `qa/verdicts/at319-issue-id-collision-reconcile.md`. The ruling is explicit — *"Not renumbered, per
  the AT-293 ruling (verdicts and manifests cite ids by number); disambiguate by the `checker` field."*
  Renumbering would silently invalidate every citation in every verdict and manifest that already
  names those ids. The collision is the lesser harm and was chosen deliberately.

**So the backlog item was a phantom** — work proposed against a question that had been decided, with
the decision written on the very rows I counted. Removing it is worth more than the row was.

**Why it got filed, which is the part worth keeping.** `docs/FEATURES.jsonl` has 61 rows, 61 unique,
zero duplicates. The duplicates are in `qa/issues.jsonl`. I filed this row against the wrong file,
carried that error into two `SERIAL:` hold lines that blocked other work on a non-existent write
conflict, and never ran `autotester ledger relitigation` — the gate that exists for exactly this and
that D-004 requires before picking up a unit. Four wrong assertions from me this session, all the same
shape: **asserting without looking.** See the generalised rule under
`ISS-sweep-unverified-negative` above; this instance extends it from *negative* existence claims to
positive ones.

**Standing consequence:** before any future unit is queued against a ledger or an id set, run
`autotester ledger relitigation "<title>"` first and paste the result into the row. A row that cannot
show that check is not ready to dispatch.

## Correction — the `at438-display-contents` answered-gate finding was mostly wrong

**Corrects:** the `at438-display-contents — an answered gate nobody acted on` row above, filed by
checker sweep 2026-09-27b and repeated by the maker orchestrator in wave 14 and wave 15.
**Verified by:** the orchestrator, on master, 2026-09-27, before the `at438-answered-gate-remainder`
unit handed back — the unit's own reading is what prompted the re-check.

The sweep's row made four claims. **Three are false**, and each was falsifiable with one command:

| Sweep claim | Truth on master | How to see it |
|---|---|---|
| "no commit touches it" | `6d2eb0bd qa(checker): re-rule at438 cycle 3 PASS under D-048/D-049; amend U14(b)/(c)` — **on master** | `git branch --contains 6d2eb0bd` |
| "AT-454 is undocumented" | `AT-454` is **`wontfix`**, filed as a disclosed U14(c) limitation per gate option (c) | one read of `qa/issues.jsonl` |
| (implied) the gate answer was dropped | `qa/contracts/ui.md` U14(b)/(c) amended, `D-049` appended, AT-438/449/450 → `fixed`, AT-454 → `wontfix`, AT-453 split into `t186-details-content` which **PASSED at cycle 1** and is now `verified`, and the verdict gained a `VERDICT: PASS` re-ruling section at line 415 | `grep -n "VERDICT: PASS" qa/verdicts/at438-display-contents.md` |
| "AT-438 is still `fixed` rather than closed under the new baseline" | **stands** — and is the only ledger-side remainder | compare with AT-453's `verified` |

**What was actually dropped is one thing, not a gate answer:** `qa/manifests/at438-display-contents.md`
still read `**Status:** STALLED — cycle 3 FAIL` after the checker re-ruled it PASS. The checker's
re-ruling commit touched the ledger, the contract, the decisions log and the verdict — but not the
manifest header, because **flipping a manifest's terminal status is the maker's job, not the
checker's.** So the handshake worked exactly as designed and then nobody performed the maker's half.
That is a much narrower defect than "Umesh's decision was spent and lost", which is how both the
sweep and the orchestrator described it.

**Why this matters more than the bookkeeping it corrects.** The sweep asserted a *checkable* fact —
"no commit touches it" — without running the check, and the orchestrator repeated it twice without
running it either. A sweep's authority comes from its claims being mechanically verifiable; an
unverified negative existence claim ("nothing happened") is the weakest possible form of one, because
absence is what you see when you do not look. Filed as **`ISS-sweep-unverified-negative`** (low, and
against the sweep discipline rather than any unit): a sweep row asserting that nothing touched a
file, issue or gate must paste the command that establishes it.

**The remainder is therefore:** (1) the manifest header flip — which the
`at438-answered-gate-remainder` unit has done and is the whole of its diff, and (2) the open question
of whether AT-438 should move `fixed` → `verified` to match AT-453, now that a re-ruled PASS exists
for it. (2) is for that unit's checker to rule on, not for this row to assert.

### Third instance in one session, and this one was the orchestrator's — generalising `ISS-sweep-unverified-negative`

The rule filed above was written against **sweeps**. It is not a sweep problem. Three instances landed
in a single session, each an unverified negative existence claim from a non-exhaustive search:

1. **The sweep**, on `at438-display-contents`: *"no commit touches it"* — `6d2eb0bd` did, and was on
   master. One `git branch --contains` would have killed it.
2. **The `at438-answered-gate-remainder` maker**, cycle 1: *"this project's gates have no `Status:`
   header convention"* — it checked four gates that lack one; `at106`, `at110` and `at355` all have it.
   Caught by its checker, cycle-1 FAIL.
3. **The maker orchestrator (me)**, in the dispatch brief for `at638-done-check-repair`: I told the
   checker, as verified fact, that `done_check.waiver` was *"newly invented"* and appeared *"nowhere"* —
   and made it the **headline attack point** of the whole check. It was wrong. I had grepped
   `src/autotester/` and `git log -S waiver -- .goal/goal.json src/autotester`, and never looked in
   `tests/` — which is where the code that reads `goal.json` obviously lives. The mechanism has existed
   since `90e4219d` with `waiver_of()`, `_waiver_offenders()`, a 20-character hollow-waiver floor, and
   its own written rationale at `tests/test_goal_done_checks.py:44,70,158`. The checker re-derived this
   before accepting my framing and told me so.

**The generalised rule, replacing the sweep-only wording:** *any* actor — sweep, maker, checker or
orchestrator — asserting that a thing does not exist must paste the command that establishes it, and
that command must cover the whole search space, not the part that was convenient. A negative claim
from a partial search is indistinguishable from not having looked.

**The cheap procedural fix, since the expensive one is discipline:** for a repo-wide "does X exist"
question, search the repo — `git grep -n X` or `git log -S X` with no pathspec — and only *then*
narrow. Every one of the three failures above came from a pathspec that silently excluded the answer.

**What made instance 3 recoverable is worth naming:** the checker was told my claim was verified fact
and re-derived it anyway. A checker that had deferred to the orchestrator's framing would have written
a confident ruling on a mechanism that does not need one, and the unit's real merits would have gone
unexamined behind a manufactured headline. Deference to the dispatcher is a failure mode of checking,
not a courtesy.

---

## NEXT UNIT (queued 2026-09-28, maker) — `at570-live-case-approval` · T-122 precondition

**Why it is first:** Umesh named production Pathlynks the first target and the `allow_writes` flip is
pending. T-122 is a **case** run, and the case-run path is the one path with no approval check at all.
Fixing it after the first live run would mean the run that mattered was the unguarded one.

**Not blocked by anything.** Serial only on the RAM ceiling (0 while t191's check runs).

### The defect is two-sided, and the second half is the one that lasts

1. **`ui/routes_runs.py::trigger_run` (`:96-132`) requires no approval.** `grep -n 'approval\|Approval'
   on that file returns **nothing** (verified twice, maker + peer checker).
2. **`stages/parallel_run.py::RunBudget.try_consume` FAILS OPEN.** It opens with
   `if approval is None: return True`, and its own docstring says *"`None` means no approval was
   supplied (unlimited)"*. A guard granting permission by the **absence** of permission — the C12
   principle inverted. Unlimited actions, unlimited wall-clock, unlimited probes.

**The full production chain, traced rather than assumed:** `trigger_run` → `_execute_with_trace`
(`routes_runs.py:65`) → `_run_cases_in_parallel` / `_run_cases_serially` → **`ui/run_execution.py:159`
`run_cases(normal_cases, plan, session_factory, _run_and_grade)`** — no `approval=` argument — →
`parallel_run.py:225 RunBudget(approval)` with `approval=None` → unbounded.

**`run_cases` has exactly ONE production caller** (`run_execution.py:159`). Every other call site is a
test, and only `tests/test_parallel_run.py:264` passes an approval at all.

### The finding that should shape the fix

**`ApprovalKind.LIVE_CASE` already exists** (`schema/enums.py:165-172`: `READ`, `CRAWL`,
`ADVERSARIAL`, `LIVE_CASE`). So D-018 always intended a case run to need its own approval — **the enum
member was defined and never wired.** This is not a design gap to be argued; it is a contract the code
silently does not keep. That also names the right `kind` to check, with no new schema.

### Build brief

- **Do not add a second `covering_approval`.** `stages/explore_consent.py:22-29` hardcodes
  `kind=ApprovalKind.CRAWL`; give it a `kind` parameter defaulting to `CRAWL` so every existing caller
  stays valid, and call it with `LIVE_CASE` from the run path. One concept, one place.
- **`RunBudget(None)` must mean ZERO, not unlimited** — and that alone is insufficient. The
  `approval: RunApproval | None = None` **default at `parallel_run.py:216-218` is the delivery
  mechanism**: a caller reaches unlimited by passing nothing. Make the parameter non-optional at that
  seam, or raise on `None` if it must stay accepted for test construction. Without that, a future
  caller re-acquires unlimited by omission and this row gets re-filed in six weeks.
- **Fail closed, and prove it.** A test that asserts the refusal must also assert a *bounded* budget
  actually bounds — `AT-218`'s vacuous-guard class is a standing finding here.
- **Ten existing `run_cases` test call sites pass no approval** and will change behaviour. They are the
  regression surface; each needs an explicit bounded approval, not a bypass flag.
- `trigger_run` is a `RedirectResponse` endpoint: the refusal is an HTTP error a human can read and act
  on, naming the missing approval's id, in the shape `covering_approval` already raises.

### Out of scope for this unit, named so it is not silently absorbed

`AT-654` (D-029's dev-only condition vs production Pathlynks) is a **HUMAN_GATE on Umesh**, holds T-145
only, and is not touched here — see `qa/gates/at654-d029-dev-only-vs-production-pathlynks.md`. T-122 is
outside D-029 entirely: the `typing_allowed` gate has call sites on the crawl path only.

**Links:** `AT-570` (high) · `AT-654` · D-018 · T-122 · T-145 · `schema/enums.py:165-172` ·
`stages/parallel_run.py:216-225` · `stages/explore_consent.py:22-29` · `ui/routes_runs.py:96-132` ·
`ui/run_execution.py:159` · `qa/contracts/consent.md` (its "Out of scope" line deferred exactly this to
T-122's live-case gate)

### Addendum (read-only design prep, 2026-09-28 — done while the RAM ceiling was 0)

Three things traced so the build does not have to discover them, each verified rather than assumed:

1. **`require_approval` is already generic — do not write a new gate.** `core/consent.py:95-106` takes
   `actions: int`, `probes: int`, `wall_clock_s: float` as plain numbers with `kind` and `target`. Only
   `explore_consent.covering_approval` couples to `CrawlBounds`. So the case-run path calls the same
   function with `kind=ApprovalKind.LIVE_CASE` and `target=project.base_url`; there is **no missing
   abstraction** and nothing new belongs in `schema/`.
2. **That gate is genuinely fail-closed and is the model the budget should copy.** `_reject_reason`
   (`:65-92`) refuses on an edited row (`is_intact`), an unsigned or non-verifying signature, a
   **missing signing key** (`SigningKeyMissing` → refuse everything, AT-110), expiry, a production
   target without `production: true`, and any bound shortfall. Note the contrast worth citing in the
   fix: **this** guard treats "cannot verify" as "refuse", while `RunBudget` treats "nothing supplied"
   as "allow". Same codebase, opposite defaults — the budget is the outlier, not the rule.
3. **Do not pass `actions=0`, and the helper already exists.** `parallel_run.py:175-179`
   `action_cost(case) -> max(1, len(case.steps))` is the system's own vocabulary for an action, and its
   ONLY caller today is the budget-spending line at `:199`. So the approval check should request
   `sum(action_cost(c) for c in cases)`, which makes `_shortfalls` compare the approval against the
   run's real size. Passing `0` would find any valid approval "wide enough" — not a fail-open (the row
   must still exist, verify, be unexpired and production-flagged, and its own `max_actions` still
   bounds the run) but it would move the refusal from preflight to mid-run, which is the worse place
   for it. **One concept, one place:** use `action_cost`, do not re-derive a cost.

**Net effect on the brief:** the unit is smaller than it looked. No new schema, no new gate function —
a `kind` parameter on `covering_approval`, a call from the run path with a real action estimate, and
the `RunBudget` default made impossible to reach.

---

## Ledger id reservation (maker, 2026-09-28) — because renumbering a stale fork cannot converge

**What happened, stated as a mistake rather than a hazard.** The `t191-video-reachable` check filed
`AT-654`/`AT-655` into its worktree's `qa/issues.jsonl`, a stale fork of master at `12597de3` whose
highest id was `AT-649`. Root had independently reached its own unrelated `AT-654`. The maker renumbered
the worktree's `AT-654` → `AT-656` and argued this was better than an 11th documented `id_collision`
pair, because neither id had been published outside its branch.

**The reasoning was sound about the past and wrong about the future.** Within the hour the peer checker
filed a new `AT-655` in root (`BenchTrial.duration_s` fail-open), so the worktree's `AT-655`
(persona-walk hygiene) now collides anyway, and the cycle-2 checker has since filed `AT-657` in the
worktree — a third id at risk. **Renumbering into a range another writer is still advancing cannot
converge.** That is most likely why this repo already carries ten documented collision pairs: they are
not sloppiness, they are what concurrent filing produces when ids are allocated from one counter with
no reservation.

**The rule, so this stops recurring:** a branch that files issue rows **reserves a block first** and
never allocates from the shared high-water mark.

| Range | Owner |
|---|---|
| `AT-656` … `AT-669` | **root ledger** (`d:/autoTesting/qa/issues.jsonl`) — the peer checker and any master-side sweep allocate here, sequentially |
| `AT-670` … `AT-679` | **reserved for `wave/t191-video-reachable`** — its three rows are remapped into this block at merge time |
| `AT-680` … `AT-689` | **reserved for the next build branch** (`at570-live-case-approval`) |

**The remap is deferred to merge time on purpose, and not applied now:** the cycle-2 checker is live and
is actively writing that worktree's `qa/issues.jsonl`. Editing a file a running checker owns would be a
concurrent write on the one artifact the handshake depends on — worse than the collision it fixes. The
worktree keeps `AT-655`/`AT-656`/`AT-657` until its verdict lands; the orchestrator remaps them into
`AT-670`+ as part of the merge, preserving each row's content and recording the old → new mapping in its
`checker_note`.

`.gitattributes` carries `qa/issues.jsonl merge=union`, so the merge itself will not conflict — which is
exactly why a duplicate id would survive silently and has to be resolved deliberately.
