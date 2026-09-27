# Manifest — at438-answered-gate-remainder

**Unit:** collect the remainder of Umesh's answered gate `qa/gates/at438-u14b-baseline.md` ("a + b +
c", answered 2026-09-26T22:34:22+05:30) — the part the system dropped after acting on it.
**Contract:** none (bookkeeping close-out; no `qa/contracts/` change, no `src/`/`tests/` change).
**Goal task:** none (bookkeeping-driven, `.goal/goal.json` explicitly out of scope for this unit).
**Date:** 2026-09-27
**Fix cycle:** 2 of max 3 (cycle 1 FAILed on three textual-accuracy defects: a self-contradiction on
AT-442/443/445 between this unit's two own files, an overstated unqualified `checked-PASS`, and a
false claim about this project's gate-status convention plus a stale gate header — see
`qa/verdicts/at438-answered-gate-remainder.md`, commit `3ae87a54`)
**Dual check:** no
**Issues addressed:** none new by this unit directly. Confirms AT-438, AT-449, AT-450 (`fixed`), AT-453
(`verified`), AT-454 (`wontfix`) in `qa/issues.jsonl` are correct — and, as of cycle 2, AT-442, AT-443,
AT-445 (`fixed`, per the checker's own falsification in `3ae87a54`, applied to the ledger by the
orchestrator on master in `4bba329b` and now merged into this branch) are also correct. Cycle 2 makes
this manifest's own prose agree with that ledger state instead of contradicting it.

## What I found: the gate answer was almost fully landed already

Umesh answered `a + b + c` on 2026-09-26T22:34:22+05:30. Investigating `git log`, `docs/DECISIONS.md`
and `qa/issues.jsonl` (not trusting the brief's summary or `qa/QUEUE.md`'s sweep note, per
instruction) shows the checker acted on the answer the same evening, in commit `6d2eb0bd`
("re-rule at438 cycle 3 PASS under D-048/D-049; amend U14(b)/(c)", 2026-09-26 23:16:38 +0530, ~42 min
after the answer):

- **(a) U14(b) baseline = pre-unit detector.** Landed: `docs/DECISIONS.md` D-049, `qa/contracts/ui.md`
  U14(b) wording amended (`grep -n "branch point" qa/contracts/ui.md` → present).
- **(b) Re-rule cycle 3 PASS, close AT-438, split AT-453 into its own capped unit.** Landed in two
  parts:
  - `6d2eb0bd` flipped `qa/issues.jsonl` AT-438/AT-449/AT-450 to `"status": "fixed"`,
    `"fixed_by": "9fc937d (at438-display-contents cycle 3, re-ruled PASS under D-048/D-049; on
    master)"`, and appended a "Re-ruling of cycle 3 (2026-09-26, D-048 gate answer a+b+c, D-049)"
    section to `qa/verdicts/at438-display-contents.md` with `VERDICT: PASS`.
  - AT-453 was split out as its own unit, `t186-details-content`, capped at 2 cycles per gate option
    (b). It PASSED at cycle 1 (`580fd3a7`, 2026-09-27 17:59:39 +0530, "AT-453 fix verified
    byte-identical to fixdir3.py") and merged (`336433d1`). `qa/issues.jsonl` AT-453 now reads
    `"status": "verified"`, `"regression_check":
    "uv run pytest tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor"`.
- **(c) AT-454 accepted as a documented limitation.** Landed in `6d2eb0bd`: `qa/issues.jsonl` AT-454
  reads `"status": "wontfix"` with a `"resolution"` field naming D-048/D-049 and the CDP-level fix
  a real repair would need; `qa/contracts/ui.md` U14(c)'s disclosed blind set names AT-454 by id
  (`grep -n "AT-454" qa/contracts/ui.md` → present, U14(c) amendment-log row and body both).

**So the brief's premise, and the `qa/QUEUE.md` sweep note it was drawn from
("chore(qa): checker sweep 2026-09-27b", `bd69565d`, 2026-09-27 18:38:05), were stale by the time
either was written.** `bd69565d` postdates *both* `6d2eb0bd` (the re-ruling) and `580fd3a7` (T-186's
PASS) by 40+ minutes, yet its "an answered gate nobody acted on" section reads AT-438's `"status":
"fixed"` as evidence nothing happened, when `"fixed"` is exactly D-049's own stated target status
("AT-438, AT-449 and AT-450 flip to fixed, since 9fc937d is an ancestor of master") — the sweep
checked the status string without reading the `fixed_by` field that names the re-ruling, and its
claim "AT-454 isn't documented as an accepted limitation anywhere" is directly contradicted by the
`resolution` field already on that row. The note is internally aware of this in its own later
paragraph ("Part of the answer *was* consumed... the AT-453 split-off did happen as T-186") but still
asks for "one small bookkeeping unit" as if (a)/(b)/(c) themselves were unlanded, rather than naming
the one thing that actually was.

## What was genuinely still dropped: the original manifest never got its close-out flip

`qa/manifests/at438-display-contents.md` is the manifest AT-438's fix cycles 1-3 were tracked under
(pre-dates goal-task tracking — "Goal task: none, issue-driven"). Its cycle-3 verdict in
`qa/verdicts/at438-display-contents.md` explicitly says: *"This was the last fix cycle. Under the
protocol the maker flips the manifest to STALLED."* That flip happened (`76ceb4d`, 2026-09-16) and was
correct **at the time** — cycle 3 FAILed under the pre-re-ruling baseline.

The re-ruling commit (`6d2eb0bd`) touched the ledger, the contract, the decisions log and the verdict
file (appending the "Re-ruling of cycle 3" section) — but it never touched the manifest's own header
`**Status:**` line or its machine-readable `## Status:` closing heading, both of which still read
`STALLED — cycle 3 FAIL` / `STALLED — 3 of 3 fix cycles spent, gated on
qa/gates/at438-u14b-baseline.md` right up until this unit. That contradiction — a manifest reading
STALLED while its own cited verdict file two sections later says `VERDICT: PASS` — is the actual
"answered gate nobody collected": every downstream artifact the checker owns was updated, but the one
artifact the maker owns (the manifest's terminal status) was not, because no maker session picked it
up between the re-ruling (2026-09-26 evening) and now.

**What I changed** (`qa/manifests/at438-display-contents.md` only, 24 insertions / 2 deletions,
verified against `git diff` before committing):
1. The header `**Status:**` line: `STALLED — cycle 3 FAIL...` → `checked-PASS — cycle 3 re-ruled PASS
   under D-048/D-049, see below.` (old text kept parenthetically for history).
2. The header `**Issues addressed:**` line: added the AT-453 (split off, verified via
   `t186-details-content`) and AT-454 (wontfix, documented) outcomes that cycle 3's own line never
   had a chance to record, and marked AT-438/442/443/445/449/450 `fixed` explicitly.
3. Appended a "Gate answered, re-ruling confirmed — checked-PASS" paragraph at the end of the file,
   right after the existing STALLED explanation, narrating the full chain (gate → `6d2eb0bd` → T-186
   → this unit) and flipping the machine-readable `## Status:` heading the session-start hook reads
   to `checked-PASS`, following the precedent in `qa/manifests/at015-at028-hook-adapter-fix.md`
   ("Recovery confirmed — checked-PASS.") for a STALLED unit whose resolution arrived after the
   stall was recorded.

No edit to `qa/issues.jsonl`, `qa/contracts/`, `docs/DECISIONS.md`, `.goal/goal.json`, or any `src/`
or `tests/` file — none of the gate answer's three parts needed further ledger, contract or code
changes; they were already correct.

## Where to attack this

- **Did I miss a fourth landed/unlanded part?** Re-derive independently: `git log -S'AT-438' --
  qa/issues.jsonl`, `git show 6d2eb0bd`, `git show 580fd3a7 -- qa/issues.jsonl`, and re-read
  `docs/DECISIONS.md` D-048/D-049 against `qa/gates/at438-u14b-baseline.md`'s literal text. I did not
  find a fourth gap; the checker-owned side of a+b+c was already fully landed before I started.
- **[Cycle-1 claim, superseded by cycle 2 — see below]** AT-442/AT-443/AT-445 still read
  `"status": "open"` in `qa/issues.jsonl`, even though the cycle-2 and cycle-3 verdicts both state they
  "no longer reproduce" on the committed code. I left them alone deliberately: D-048/D-049's authorized
  `Result` section names only AT-438/AT-449/AT-450 (→ fixed), AT-454 (→ wontfix) and AT-453 (stays
  open, own unit) — it does not mention AT-442/443/445 at all, and the re-ruling's own `ISSUES-WRITTEN`
  line in the verdict is silent on them too. Flipping a ledger row to `fixed`/`verified` on my own
  reading, without a checker-run falsification, is exactly the unverified-status-change the project's
  own sweep convention forbids (`qa/QUEUE.md`'s P2 rule, restated in the AT-648 write-up). If these
  three should also close, that is a `/checker` call, not mine — worth raising to the checker as a
  small follow-up, not something I acted on here. **This restraint was the correct call** — but the
  cycle-1 commit's *other* file (`at438-display-contents.md`) asserted "fixed" for the same three ids
  in the same commit, which contradicted this exact paragraph. The checker caught it, then did the
  falsification itself and ruled all three fixed (`3ae87a54`) — see the Cycle 2 section below for how
  that is now reflected consistently in both files.
- **`qa/QUEUE.md`'s stale note** (lines ~1009-1017 and ~1063-1078, from sweep `bd69565d`) is left
  unedited. It is a historical sweep log with no established in-place "resolved" annotation
  convention (checked: no other finding in the file is marked resolved after the fact), and it is
  concurrently written by other live sessions. The manifest closeout here is the authoritative
  record; a future sweep reading the manifest will see `checked-PASS` and self-correct.
- **[Cycle-1 claim, FALSE, corrected in cycle 2 — see below]** The gate file itself
  (`qa/gates/at438-u14b-baseline.md`) needed no edit: it already carries the `Answered:` line, and
  this project's gate convention has no separate "Status: closed" header field to flip (checked
  `at147-expiry-end-of-day.md`, `at520-scripts-line-cap.md`, `commit-before-verdict.md`,
  `at610-strict-out-of-order.md` — none use one). **This was a negative-existence claim from a
  four-gate sample, and it was wrong**: `at106-hook-architecture-path.md`, `at110-approval-forgery.md`
  and `at355-guard-shape.md` all use `Status: ANSWERED`. Worse, `at438-u14b-baseline.md` itself —
  the gate this whole unit is named after — still read `**Status: OPEN**` in its own header, over 25
  hours after being fully answered and acted on. Fixed in cycle 2.

## Fix cycle 2 (2026-09-27)

The checker's verdict (`qa/verdicts/at438-answered-gate-remainder.md`, `3ae87a54`) FAILed cycle 1 on
three textual-accuracy defects. The premise itself — that the gate answer was fully discharged by
`6d2eb0bd` + `580fd3a7` and the sweep note calling it unactioned was wrong — was independently
re-derived by the checker from primary commit content and **stands**; nothing below reopens that.

**1. Self-contradiction on AT-442/443/445 (sev high).** `at438-display-contents.md`'s "Issues
addressed" line said "fixed" for all three while this manifest's own "Where to attack this" said the
opposite — that flipping them was "a `/checker` call, not mine." Both were true statements about
different things (the ledger-flip authority vs. the prose claim), but they read as contradictory sitting
next to each other in the same commit. **What changed since cycle 1:** the checker did the falsification
itself in `3ae87a54` — `src/autotester/browser/visual_order.js:60`'s comment "NEVER insert a probe
(AT-442/443)" means the shipped walk-up detector structurally cannot exhibit any of the three, confirmed
against a fresh `uv run pytest tests/test_browser_visual_order.py -k display_contents` run — and ruled
them `fixed`. **The orchestrator has since applied that ruling to `qa/issues.jsonl` on master
(`4bba329b`)**, which I merged into this branch at the top of this cycle (`git merge master`, one file,
`qa/issues.jsonl`, 3 insertions/3 deletions — confirmed via `git show --stat` after the merge). I did
**not** touch `qa/issues.jsonl` myself; C10 and this unit's own scope both restrict me to the three
manifest/gate paths below, and the ledger edit was never mine to make. What I fixed is the prose: both
files now cite `qa/verdicts/at438-answered-gate-remainder.md` (`3ae87a54`) as the explicit authority
for AT-442/443/445's `fixed` status, and neither file overstates D-048/D-049 as covering them (D-049's
own `Result` section never names AT-442/443/445 — only AT-438/449/450/453/454). See the edits to
`at438-display-contents.md`'s header and closing status, and the superseded-bullet markers above.

**2. Overstated `checked-PASS` (sev medium).** `at438-display-contents.md`'s status line read a
blanket `checked-PASS`, but the cited authority (`qa/verdicts/at438-display-contents.md`, "Re-ruling
of cycle 3") scopes itself "for U14(b) only." Fixed: both the header `**Status:**` line and the closing
`## Status:` line in `at438-display-contents.md` now read `checked-PASS for U14(b)` / `checked-PASS
for U14(b) only`, and explicitly name where AT-453 (`t186-details-content`, `580fd3a7`, `verified`)
and AT-454 (`wontfix`, U14(c) limitation) were actually resolved, rather than folding all four ids into
one unqualified close.

**3. False convention claim + stale gate (sev medium).** Corrected in place above (see the two
`[Cycle-1 claim ...]`-tagged bullets in "Where to attack this"): three other gates in this repo
(`at106-hook-architecture-path.md`, `at110-approval-forgery.md`, `at355-guard-shape.md`) do use
`Status: ANSWERED`, so the claim that no gate in this project uses a closing status field was false.
`qa/gates/at438-u14b-baseline.md`'s own header has been flipped from `**Status: OPEN**` to
`**Status: ANSWERED -> acted on**`, naming D-049, `t186-details-content`, and this unit's own cycle-2
close-out as what actually happened, following the `at110`-style "ANSWERED -> <what happened>" form
rather than the bare `at106`/`at355` form, since (unlike those two) there is a concrete downstream chain
worth naming in the same field.

**The generalisable lesson (in my own words, since the checker asked me to write it, not just note
it):** I checked four gates, found none using a `Status:` closing field, and concluded from that
negative sample that the convention did not exist in this project. That is exactly the reasoning error
my own cycle-1 correctly diagnosed in the sweep note that started this whole unit — the sweep looked at
one field (`qa/issues.jsonl`'s `"status": "fixed"` string) on one artifact (AT-438's ledger row),
found what looked like inaction, and concluded nothing had happened, without checking the `fixed_by`
field that would have shown otherwise. A non-exhaustive negative check is not evidence of absence in
either direction — not in a ledger row, and not in "does this repo have a convention for X." I found
the sweep's version of this error and called it out; the checker then found my own copy of it, in the
same manifest, one section later. Worth remembering: correctly diagnosing an error in someone else's
work does not make you immune to it in your own — check the actual population (`ls qa/gates/`, or a
`grep -l "Status:"` across all of them) before asserting a convention doesn't exist, rather than
sampling four and stopping.

## Verify (cycle 2)

| command | result |
|---|---|
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `stale-generated: docs/SNAPSHOT.md differs from regeneration; run \`autotester snapshot\` — 1 violation` (pre-existing, caused by master's `.goal/goal.json` churn from concurrent T-191 close-out brought in by `git merge master`; this unit's own diff never touches `.goal/` or `docs/SNAPSHOT.md`; the cycle-1 checker verdict independently traced and excused the same finding) |

**`uv run pytest` (bare, no `-q`), fresh run post-merge, full ~19 minutes, run to completion — reporting
the failure list, not the exit code:** `2 failed, 2068 passed, 6 skipped, 14 xfailed, 15 warnings in
1134.05s (0:18:54)`.

The 2 failures, named individually:
1. `tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail` —
   `AssertionError: these done_checks pass on a clean repo whether or not their task was started, and
   carry no waiver: ['T-190']`.
2. `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered` —
   `AssertionError: assert 81 == 70` (goal-task count drift against a hardcoded expectation).

Both are the same `.goal/goal.json`-drift class the cycle-1 verify already named as out of this unit's
scope (concurrent orchestrator activity growing the task list; this unit's own diff touches only the
three files under `git diff --stat` above, none of them `.goal/*`). The task-id named in failure 1
(`T-190`) has moved since cycle 1 — consistent with concurrent live sessions, not with anything this
unit did. **Notably absent this run:** `tests/test_flake_probe_real_process.py::...grandchild` (AT-627),
which cycle 1 flagged as a plausible contention casualty and declined to re-run solo to confirm — this
cycle's full solo run passed it cleanly, supporting that it was contention, not a real regression.

## Verify (cycle 1, for history)

| command | result |
|---|---|
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest` (bare, no `-q`) | `3 failed, 2068 passed, 5 skipped, 14 xfailed, 15 warnings in 1239.72s (0:20:39)` |

**The 3 pytest failures, named individually (not the exit code):**
1. `tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail`
2. `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered`
   — both `AssertionError: assert 81 == 70` (goal-task count drift against a hardcoded expectation).
   These are the two known pre-existing reds this brief flagged as being repaired by another live
   unit (`.goal/goal.json` growth from concurrent orchestrator activity, out of this unit's scope by
   the hard rule against touching `.goal/goal.json`).
3. `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
   — not named in the brief as a known red. This unit changed only one markdown manifest file (no
   `src/`, no `tests/`), so it cannot have caused a real-process-kill test to fail; the machine was
   running at least two other concurrent builds during this run (per `qa/QUEUE.md`'s RAM-ceiling
   notes) and a real-subprocess timing test is a plausible casualty of that contention. Flagging
   rather than re-running solo to confirm, since isolating it would mean fighting the other live
   sessions for the process table — a call for whichever unit next needs a clean read on this test,
   not mine to spend cycles on here.

`git diff --stat` before the cycle-1 commit: `qa/manifests/at438-display-contents.md | 26 ++++++++++++++++++++++++--`
(1 file changed, 24 insertions(+), 2 deletions(-)) — matches the two targeted edits, no
re-serialization, no other file touched.

**Cycle-2 `git diff --stat` before commit** (post-merge with master):

```
qa/gates/at438-u14b-baseline.md               |   5 +-
qa/manifests/at438-answered-gate-remainder.md | 150 ++++++++++++++++++++++----
qa/manifests/at438-display-contents.md        |  40 ++++++-
3 files changed, 170 insertions(+), 25 deletions(-)
```

(Numbers as measured by the final `git diff --stat` run just before commit — the count includes this
very table's own addition, which is expected for a self-describing manifest.)

Exactly the three paths this unit's brief scoped it to (this manifest, the sibling manifest, the gate
file). No touch to `qa/issues.jsonl`, `qa/contracts/`, `docs/DECISIONS.md`, `.goal/*`, `src/` or
`tests/` — the ledger correction for AT-442/443/445 was already applied on master (`4bba329b`) and
arrived via the `git merge master` at the top of this cycle, not via any edit made here.

## Status: checked-PASS (cycle 2 of max 3)

Verdict `qa/verdicts/at438-answered-gate-remainder.md`, **Cycle checked: 2**, verdict commit
`3b83ed5e`, merged `235ac6a5`, pushed to `origin/master`. All three cycle-1 defects verified fixed,
each re-derived from primary sources rather than from this manifest's narrative.

### The unit's real contribution was a correction, not a repair

It was dispatched to collect a gate answer the sweep said had been dropped, and it **found the
premise false** — Umesh's `a+b+c` had been fully discharged 42 minutes after he gave it. Two
checkers independently confirmed that. The actual defect was one line: the original manifest never
got its close-out flip, because the re-ruling checker updated the ledger, contract, decisions log and
verdict, and **flipping a manifest's terminal status is the maker's half of the handshake.** The
handshake worked and nobody performed the maker's side. That is a far narrower and more useful
finding than the one it was sent to fix.

### The fifth inaccurate assertion — found, exactly as predicted

I told this checker to assume a fifth inaccurate assertion existed in cycle 2's +134 lines of new
prose, because four had already landed this session. **It found one:** the manifest's own pasted
`git diff --stat` table undercounts its final insertions by 3 lines (claimed 150/170, actual
153/173), because prose written *after* the table was captured added the missing lines. Low severity
and non-blocking — it misstates no scope, file count or substantive claim — but it is the same class
as the other four, and it is worth recording that a prediction made purely from the session's base
rate paid out. Evidence pasted before the work is finished is evidence about a tree that no longer
exists.

### Two staleness questions I handed over rather than deciding, both ruled

**A manifest may paste evidence older than the tree it submits, when the gap is a C10 sync-merge and
the checker re-verifies the merged tree.** The manifest's pytest output showed the two
`test_goal_done_checks.py` reds and its doctor run showed `stale-generated`; both were fixed by
commits that landed on master *after* `a9357439` and reached this branch only through the later
sync-merge `a8cee3b9`. The checker re-ran everything fresh at HEAD — doctor clean, ruff clean,
**8 passed** on the two goal-contract files — and ruled that re-verifying the merged tree, not the
manifest's frozen snapshot, is precisely what the sync-merge exception is for. Leaving
`qa/QUEUE.md`'s stale sweep note unedited was also ruled acceptable, after verifying my correction
already exists in that file.

### The dangling recommendation is no longer dangling

Cycle 1's verdict **recommended but declined to write** a C7 clause about zero-code units. I told
this checker to settle it either way, because leaving a recommendation unmade twice is the
answered-question-nobody-collects failure this very unit exists to clean up — and it would have been
the second instance of that failure inside the unit correcting the first. **It amended C7**, narrowly:
the manifest must *show*, not assert, that a failure has an outside cause, and the clause does not
excuse self-caused or misdiagnosed failures. Dated changelog entry, citing this verdict and
`t192-url-pattern-heal.md`'s identical observation.

### Also now true, and it took three parties to get here

`qa/gates/at438-u14b-baseline.md` finally reads `Status: ANSWERED -> acted on` — matching `at110`'s
existing form rather than inventing a fourth spelling of a convention the unit had just been
corrected for claiming did not exist. AT-442/443/445 read `fixed` in the ledger, on the authority of
a checker that falsified them itself, applied by the orchestrator in `4bba329b` because C10 kept the
checker from writing it from its own worktree. The checker confirmed `a9357439` never touched
`qa/issues.jsonl`.

No `docs/FEATURES.jsonl` row: bookkeeping close-out, no owning goal task, no user-facing capability.
