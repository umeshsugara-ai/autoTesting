# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-16T14:15:57+05:30** (stamp generated from the system clock,
not typed — see AT-399); bound strictly to `D:/autoTesting`. This is the **third Mode B sweep of 2026-09-16**,
due on the 5th-tick rule after ~8 maker ticks. It supersedes the 18:05-stamped queue.

**Adapter used: `qa/adapter.json` (coding).** Slot-1 verify re-run by this sweep, not read:
`uv run ruff check src tests scripts` → exit 0 "All checks passed!" · `uv run autotester doctor`
→ **clean** (the previous sweep's `grade.py` violation is gone — AT-366 landed at `f0632b1`) ·
`uv run pytest -q` re-run to completion in the shared tree.

## Correction to this sweep's dispatch brief — read before the findings

- **"The last sweep's stamp is in the future" — CONFIRMED, but it did NOT suppress staleness
  detection.** Filed as **AT-399**. The stamp is real (`2026-09-16T18:05:00+05:30` on a file whose
  mtime and whose own commit `5da3117` are both 11:51). But the only consumer,
  `qa/hooks/mc-sessionstart.ps1:26` `AgeMin`, reads **LastWriteTime, not the text** — sweep age
  reads 135 min, over the 120-min AUTO-CONTINUE threshold, and would have fired correctly. The
  damage is to the human audit record, not to the gate. Stated plainly so nobody re-derives a
  suppression that did not happen.
- **"Four units had a vacuous or over-claimed guard caught — three by the maker's own sabotage."
  NOT SUPPORTED by the ledger.** Measured: of the **29** issues filed since the 11:51 sweep,
  `found_by` is `checker-unit` ×26, `checker-sweep` ×2, absent ×1 (AT-398 — see AT-404).
  **Maker self-caught: zero.** All four guard findings (AT-378, AT-380, AT-384, AT-395) carry
  `found_by: checker-unit`, and no manifest claims a self-catch. See the AT-218 section.
- **"AT-391 is now the dominant systemic risk." NO — and it got smaller, not larger.** See below.

## Findings — FINDINGS: 6

| Id | Sev | What |
|---|---|---|
| **AT-400** | **high** | The `at365` HUMAN_GATE's "Current state" is **false on disk**. It says `"data_class": "synthetic"` sits uncommitted in `qa/adapter.json`. It does not: no `data_class` in the file, `git status` clean on it, `git log -S data_class --all` finds it in no commit, no stash. Options A and B both begin "land the declaration", and AT-376's 344-violation measurement was taken against a tree state that no longer exists — answering today would act on an evaporated premise. |
| **AT-399** | medium | `qa/.last-sweep` line 17 and the previous `QUEUE.md:3` both stamped ~6h14m ahead of the commit that wrote them; nothing validates a liveness stamp against a clock. Sibling: `loop_status.py:117` `read_ticks` **sorts** stamps, so a forward-dated tick would be silently reordered rather than flagged. |
| **AT-401** | medium | `scripts/flake_probe.py:137` launches pytest with **no `timeout=`**, and `probe()` loops it N times "stopping for nothing". Deliberate deviation from check 7's default `high`: a hang in a manual dev script is loud and loses no data. |
| **AT-402** | medium | **Structural-erosion signal (check 9).** `visual_order.js` + its test are the most-churned pair in the repo (5 commits each since 09-11, 2.5× the next file), across 4 units with three FAIL cycles — and the unit that "closed" AT-379 immediately produced AT-392 (high), AT-393 and AT-398. Signal, never a verdict; the remedy is a HUMAN_GATE on structure, **not** more harness. |
| **AT-403** | low | Structural-erosion signal: six `src/` modules at 290–300 lines against doctor's 300 cap, **three at exactly 300**. doctor exits 0 on all. |
| **AT-404** | low | AT-398 is the only row of 398 in an alternate schema (no `found_by`, no `date`) and carries cp1252 mojibake — so the `found_by` histogram this sweep runs for AT-218 silently under-counts. |

**No reopens.** Nothing this sweep examined proved a PASSed claim unbacked.

## Checks 1–7 — what was re-derived

1. **Bypass + handshake.** Window `5da3117..ef9e819`, 26 commits, 8 source-bearing; **every one maps
   to a manifest** (at358, at366, at368, at357, at379, at335, at386). Bypass: **CLEAN**.
   131 manifests / 134 verdicts. Exactly one manifest is not `checked-PASS` and is not superseded or
   STALLED: **`at379-scrollable-pane-reachability` at `ready-for-check`, FAIL cycle 1 — the
   concurrent session's live unit, excluded by the dispatch and NOT a gap.** PASS-not-closed-out: 0.
   FAIL-with-unresponded-manifest: 0. `at345-346-fold-coverage` and `at015-at028` STALLED with their
   `qa/debug/` diagnoses on disk. `qa/.last-tick` live (14:02, ADVANCED) — no "maker asleep".
2. **Inbox.** `qa/feedback-inbox.md`: every entry carries a fold/resolution marker except the
   2026-09-06 BFS/video entry, which is correctly parked as AT-052 + an answered gate. Clean.
3. **Contract staleness.** 29 contracts; `ui-flow-diagram.md` and `ui-sidebar.md` still carry no
   amendment log (AT-099, low, carried). Nothing new.
4. **Enforcement liveness.** 4 hooks on disk, all 4 wired in `.claude/settings.json`
   (SessionStart ×2, PreToolUse ×2, SessionEnd ×1). Repo history 720 commits. `qa/loop.md` present,
   its `Stop` line lists the seven terminal states incl. `PAUSED`, `Human gate` line present and
   not contradicted by the adapter. Loop-design three questions: **can it spin** — no, the Stop
   line reads real close-outs; **can it Goodhart the verifier** — partially, and that is AT-402/403;
   **can it run a wrong answer to completion** — AT-395 is a live instance and is queued at #2.
4b. **Data boundary (MC-003).** `data_boundary.py` → **exit 1, "no `data_class`"**. This is
   **AT-365 at HUMAN_GATE, not a new finding** — but the gate's premise has evaporated: **AT-400**.
5. **Goal coverage.** 55 tasks, 35 done / 20 pending. Unchanged from 11:55: intake covered (T-161);
   multi-source learning partial (video only, **T-162 gated**); orchestration blocked on T-162;
   Portal Persona missing (T-164); BFS completeness partial; regression-triggered run missing
   (T-167); two-mode acceptance missing (T-169, gated by AT-281). **No goal task moved across this
   session's five PASSes** — all five closed ledger issues, not goal requirements.
6. **Goal-drift / re-grill.** No `qa/.regrill-due`. No new drift. Two GRILL rows carried (below).
   Stalls all carry diagnoses. **Gate-answered-off-disk hunt: NONE FOUND** — searched every commit
   message since 2026-09-10 and every manifest/verdict for `t162`, `at365`, `at383`; every hit
   *describes* a gate, none answers one. The `at355` gate is the counter-example done right
   (answer written to disk at `54df0af` and cited by the unit that consumed it).
7. **Silent-failure hunt** over code PASSed since the last sweep (`flake_probe.py`, `loop_status.py`,
   `grade.py`, `cli_loop.py`, `verdict.py`): one hit, **AT-401**. `loop_status.read_ticks`'s
   `except ValueError: continue` was examined and **cleared** — an unparseable stamp makes a gap
   look *larger*, which fails safe. `grade.py`'s screenshot path now counts instead of swallowing
   (that was AT-366, fixed at `f0632b1`).

## The three open gates — each confirmed unanswered ON DISK

| Gate | Blocks | Disk state |
|---|---|---|
| **`t162-contract-approval.md`** | **T-162 + T-163, both `criticality: critical`** | `**Answered:** _(unanswered …)_` — raised 2026-09-11, **5 days**. Still the highest-leverage decision in this repo: two critical tasks and the whole multi-source half of the north star sit behind it. |
| **`at365-data-class-declaration.md`** | AT-365 (high) | `Answered:` line present and **empty**. And its premise is now false — **AT-400**. |
| **`at383-loop-status-consumer.md`** | AT-383 (medium) → AT-368 (high) | `Answered:` line present and **empty**. All four candidate call sites ruled out or gated; nothing written, correctly. |

Five further gates remain open and un-blocking-today: `at110-approval-forgery` (no `Answered:`
line at all), `at147-expiry-end-of-day` (empty stub), `at218-vacuous-guard-class`, 
`at253-agent-fallback-wiring` (`_(pending)_`), `erp-credentials`, `t135-url-pattern-data-migration`.

## AT-218 — did this session move it? **No. Measured, not asserted.**

Eight sweeps carried, this is the ninth. The headline metric is the `found_by` histogram, and it is
flat: **29 issues filed since 11:51 — 26 `checker-unit`, 2 `checker-sweep`, 1 unattributed, 0 maker.**

The dispatch's framing that "three of four were caught by the maker's own sabotage" is **not what
the disk says**: AT-378, AT-380, AT-384 and AT-395 all carry `found_by: checker-unit`, and no
manifest in this session claims a self-catch. What *is* true, and is a genuine change in kind:

- **AT-384 (high, now fixed)** is the sharpest vacuous guard this project has produced — an autouse
  `private_temp` fixture that *disarmed* `_discard`'s PREFIX clause, so dropping a safety clause from
  a destructive delete survived the entire suite. It was found by a **checker FAIL** (at357 cycle 1),
  and the maker fixed it in cycle 2.
- **AT-395 (medium, open)** is enumerated debt on a unit that PASSed anyway: at386's capability table
  claims five behaviours and enumerates four rows, and the missing row's edit *cannot* redden the
  test it would be paired with. The checker **recorded rather than charged**. That is the correct
  call under the cycle-cost rule — and it is also exactly the leak AT-218 is about.

So: the instruments improved (C7's mutation harness is usable under concurrency again, AT-357 fixed),
the catch rate did not move, and the asymmetry AT-218 names — *every countermeasure is
maker-authored, every catch is checker-made* — is unchanged at 0/29. **AT-218 stays open, ninth
sweep, and this is the strongest evidence yet that it is a policy question only Umesh can close.**

## AT-391 — not the dominant systemic risk, and smaller than when it was filed

Judged, not assumed. AT-391 (low) says two sessions sharing one tree make slot-1 verify
unreproducible. Evidence both ways:

- **Against promoting it:** this sweep re-ran all three slot-1 commands **in the shared tree with the
  concurrent session's uncommitted `at379` work present** — ruff exit 0, doctor clean, pytest run to
  completion. Verify *was* reproducible today. The previous sweep's two casualties are both retired:
  its `doctor` violation was transient in-flight `grade.py` (now landed, doctor clean), and the
  mutation-harness half was **AT-357, fixed and PASSed at `eed01b3`** — the harness is now scoped to
  its own sandbox and no longer reds under concurrency.
- **For keeping it open:** the failure mode is real and will recur; nothing structurally prevents it.

**Verdict: AT-391 stays `low`.** The dominant systemic risks in this repo are, in order:
**(1) decision starvation** — three gates unanswered, one for five days, blocking two `critical`
tasks and the high-severity data-boundary gate, with AT-400 showing a gate's premise can silently
rot while it waits; **(2) verifier monoculture** — AT-218 at 0/29 plus AT-243 (Mode D has still
never run: zero `LIVE-BROWSER:` lines in 134 verdicts); **(3) structural churn** — AT-402.
Shared-tree friction is an operational nuisance with a known workaround, not the ceiling.

## GRILL — human decision, not a build row

- GRILL: recurring vacuous-guard prevention policy — unanswered (AT-218), **9th consecutive sweep**.
- GRILL: set the real two-mode acceptance thresholds for D-023/T-169 (AT-281), carried.
- GRILL (new, AT-402): structure-before-code review of `visual_order.js` — redesign or sixth patch.

## HUMAN_GATE — do not build as ordinary units

**T-162 contract approval** (A/B/C/D — 5 days, blocks two critical tasks) · **AT-365 data_class**
(and fix its premise first, AT-400) · **AT-383 loop-status consumer** (A/B/C/D) · AT-110 · AT-147 ·
AT-253 · ERP credentials · AT-288..291 renumbering (only Umesh can overturn AT-293).

## TOP-3 BUILDABLE NEXT UNITS (non-gated)

1. **AT-400 (high) — make the `at365` gate's premise true again.** Re-apply `"data_class":
   "synthetic"` to `qa/adapter.json` **and commit it**, then correct the gate's "Current state"
   section to describe what is actually on disk. Tiny, no design surface, and it is the precondition
   for the one high-severity gate that is answerable today: right now A and B both say "land the
   declaration" about a declaration that does not exist. Landing it turns MC-003 red — which is the
   *point* of the gate, and is what AT-376 already measured.
2. **AT-395 (medium) — give at386's fifth claimed behaviour its falsifying row.** The capability
   table enumerates 4 rows for 5 claimed behaviours; the clean-run arm of `run_once`'s tail ternary
   has none, and row 2's edit cannot redden it (the two tests pin the two arms of one ternary). This
   is enumerated debt on a unit PASSed 20 minutes ago and it is the AT-218 class in miniature — a
   claim whose check does not isolate it.
3. **AT-401 (medium) — put a timeout on `flake_probe`'s subprocess.** Map `TimeoutExpired` to a
   distinct `Run` outcome so a hung run is recorded as evidence about flakiness rather than
   swallowing the probe. Harden the instrument *before* it is pointed at the non-deterministic modal
   crawl (AT-335) it was built to measure — a probe that hangs on run 7 of 41 measures nothing.

**In flight, do not double-assign:** `at379-scrollable-pane-reachability` (FAIL cycle 1, concurrent
session) and everything behind it — **AT-392 (high)**, AT-393, AT-394, AT-398. Also
`at396-isolation-flag-claims` (Fix cycle 1), which the concurrent maker began *while this sweep was
writing* — AT-396 is therefore off this list.

**Runner-up, carried for a NINTH sweep:** fixed-ledger reconciliation — the `fixed` backlog has
grown again to **74** rows against 204 `verified`. Re-derive the oldest untouched cohort by
sabotage (AT-207/208/219-223/228).

---

Terminal state: **FINDINGS: 6** — AT-400 (high), AT-399, AT-401, AT-402 (medium), AT-403, AT-404
(low). No reopens. Ledger after this sweep: **401 rows — 204 verified / 119 open (10 high,
39 medium, 70 low) / 74 fixed / 2 wontfix / 2 dismissed**; duplicate ids unchanged at the four
AT-293 ruled on.
