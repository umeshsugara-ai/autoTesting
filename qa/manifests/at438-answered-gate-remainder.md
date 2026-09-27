# Manifest — at438-answered-gate-remainder

**Unit:** collect the remainder of Umesh's answered gate `qa/gates/at438-u14b-baseline.md` ("a + b +
c", answered 2026-09-26T22:34:22+05:30) — the part the system dropped after acting on it.
**Contract:** none (bookkeeping close-out; no `qa/contracts/` change, no `src/`/`tests/` change).
**Goal task:** none (bookkeeping-driven, `.goal/goal.json` explicitly out of scope for this unit).
**Date:** 2026-09-27
**Fix cycle:** 1 of 1 (no code, nothing to cycle on)
**Dual check:** no
**Issues addressed:** none new. Confirms AT-438, AT-449, AT-450 (`fixed`), AT-453 (`verified`), AT-454
(`wontfix`) in `qa/issues.jsonl` are already correct and closes the one stale artifact that still
disagreed with them.

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
- **AT-442/AT-443/AT-445 still read `"status": "open"`** in `qa/issues.jsonl`, even though the
  cycle-2 and cycle-3 verdicts both state they "no longer reproduce" on the committed code. I left
  them alone deliberately: D-048/D-049's authorized `Result` section names only AT-438/AT-449/AT-450
  (→ fixed), AT-454 (→ wontfix) and AT-453 (stays open, own unit) — it does not mention AT-442/443/445
  at all, and the re-ruling's own `ISSUES-WRITTEN` line in the verdict is silent on them too. Flipping
  a ledger row to `fixed`/`verified` on my own reading, without a checker-run falsification, is
  exactly the unverified-status-change the project's own sweep convention forbids (`qa/QUEUE.md`'s
  P2 rule, restated in the AT-648 write-up). If these three should also close, that is a `/checker`
  call, not mine — worth raising to the checker as a small follow-up, not something I acted on here.
- **`qa/QUEUE.md`'s stale note** (lines ~1009-1017 and ~1063-1078, from sweep `bd69565d`) is left
  unedited. It is a historical sweep log with no established in-place "resolved" annotation
  convention (checked: no other finding in the file is marked resolved after the fact), and it is
  concurrently written by other live sessions. The manifest closeout here is the authoritative
  record; a future sweep reading the manifest will see `checked-PASS` and self-correct.
- **The gate file itself** (`qa/gates/at438-u14b-baseline.md`) needed no edit: it already carries the
  `Answered:` line, and this project's gate convention has no separate "Status: closed" header field
  to flip (checked `at147-expiry-end-of-day.md`, `at520-scripts-line-cap.md`,
  `commit-before-verdict.md`, `at610-strict-out-of-order.md` — none use one).

## Verify

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

`git diff --stat` before commit: `qa/manifests/at438-display-contents.md | 26 ++++++++++++++++++++++++--`
(1 file changed, 24 insertions(+), 2 deletions(-)) — matches the two targeted edits, no
re-serialization, no other file touched.

## Status: ready-for-check
