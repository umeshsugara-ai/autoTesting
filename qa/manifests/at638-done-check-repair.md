# Manifest — iss-at638-2-done-check-repair
**Contract:** none dedicated — this unit repairs `.goal/goal.json` `done_check`s and the two
`tests/test_goal_done_checks.py` guards; judged directly against
`qa/QUEUE.md` rows `ISS-at638-remainder-2` (high) and `AT-647` (medium).
**Goal task:** none (infra/repair unit, not itself a `.goal/goal.json` task)
**Date:** 2026-09-27
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk:** skip (backend-only — no UI surface touched; edits are `.goal/goal.json`,
`.goal/dashboard.html` regeneration, and two `tests/` files)
**Issues addressed:** ISS-at638-remainder-2, AT-647
**Executor:** claude-opus-subagent (maker build subagent, this session)
**Executor rationale:** heavy row — cross-file reasoning about which of two failing tests names
the true invariant vs. a magic number, plus a genuine stale-progress-block bug found mid-repair.

## Affected set: derived vs. the queue row's own claim

The row named five pending tasks — T-186, T-189, T-190, T-191, T-192 — as carrying unfalsifiable
`done_check`s, and separately flagged its own framing as stale (see "Correction to
ISS-at638-remainder-2's own framing" in `qa/QUEUE.md`). I re-derived the current set directly from
`.goal/goal.json` and the failing tests' own logic (`offenders_in(tasks())`) rather than trusting
either version of the row:

```
offenders (test_no_pending_task_has_a_done_check_that_cannot_fail): ['T-190']
```

- **T-186, T-189, T-191, T-192 are now `done`** (closed `checked-PASS` since the row was filed) —
  `offenders_in` exempts `status == "done"` by its own rule, so none of the four is currently
  causing the "cannot fail" test to red, regardless of their `done_check`'s shape. Not touched.
- **T-190 is the only live offender** — `uv run pytest tests/ -k persona` matches the
  pre-existing, unrelated `tests/test_portal_persona.py` and passes today whether or not T-190's
  own (unbuilt) work exists. Repaired with a `done_check.waiver` (see below), not a guessed file
  name.
- **T-185 (AT-647, not in the original row at all — filed separately, then folded in per
  `qa/QUEUE.md`'s "Fold into `iss-at638-2-done-check-repair`")** — `done_check.cmd` named
  `tests/test_scroll_reach.py`, which never existed. Repaired by pointing at the real file.
- **T-160 (done)** — not named by either row, but its OWN `done_check` cited
  `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered`; that test moved
  (see "What changed" below), so its node id was updated in the same commit — an incidental
  fifth touch, found only because I re-read every `done_check` referencing this test file before
  moving it.
- **T-190 was named in the original row and is not stale** (still pending, still an offender) —
  contradicts the row's own "Correction" note only in that the correction note didn't call this
  out explicitly (it focused on T-186/189/192 being done and T-190 being absent from the SERIAL
  dependency line, not on whether T-190 itself was still an offender). Confirmed independently:
  T-190 is a real, live offender today.

## What changed

- `.goal/goal.json` T-185 `done_check.cmd`: `uv run pytest tests/test_scroll_reach.py` (file never
  existed) → `uv run pytest tests/test_browser_scroll_reach_at408_416.py` (the real, existing
  at408/416 test file; confirmed 2/2 passing standalone).
- `.goal/goal.json` T-190 `done_check`: added `waiver` (see next section for why a waiver, not a
  guessed node id).
- `.goal/goal.json` T-160 `done_check.cmd`: node id updated to
  `tests/test_goal_contract_registration.py::test_revised_goal_contract_is_registered` (the test
  it names moved there — see split below).
- `.goal/goal.json` `progress` block: `done` 56→57, `pending` 25→24, `percent` 69→70 — a genuine,
  pre-existing drift found while investigating the magic-number test (see "A second bug found"
  below), fixed via `goal_store.recompute_progress` + `render_dashboard.write_dashboard` called
  directly (never `monitor.py`'s `run()`, which also calls `register_product()` — that writes the
  **global**, cross-project goal registry outside this repo; calling it from a worktree would
  point the shared registry's `autotester` entry at the worktree path, which is out of scope and
  not this unit's to touch).
- `.goal/dashboard.html`: regenerated to match (same call).
- `tests/test_goal_done_checks.py`:
  - Removed `test_revised_goal_contract_is_registered` (moved — see below).
  - Added `_referenced_py_files()` + `test_no_done_task_has_a_done_check_naming_a_file_that_does_not_exist`
    — the AT-647 recurrence guard (see "Recurrence guard" below).
  - Tightened `test_the_waiver_rule_actually_rejects_a_hollow_waiver`'s docstring: it claimed "no
    task on disk carries a waiver at all", which T-190's new waiver makes false; reworded to name
    T-190 as the first instance.
  - File was 300 lines before this unit (already at doctor's cap); ended at 277 after the move.
- `tests/test_goal_contract_registration.py` (**new file**): houses
  `test_revised_goal_contract_is_registered`, split out under doctor's 300-line cap (the file
  would have been 350/341 lines with the AT-647 guard added in place) and because it is a
  different responsibility from either half already in `test_goal_done_checks.py` — a one-off
  snapshot of a specific, already-closed registration (T-160..T-184, D-039..D-045), not a
  goal.json-wide guard. Same rationale `test_goal_done_check_shapes.py`'s own module docstring
  gives for its own earlier split off the same file. 90 lines.

## A second bug found mid-repair: the progress block was already wrong

Independent of the magic-number issue, `.goal/goal.json`'s `progress` block was internally
inconsistent with its own `tasks` list *before* any edit here: `progress["done"] == 56` but
`sum(t["status"]=="done") == 57`; `progress["pending"] == 25` vs actual `24`. This would have
failed `test_revised_goal_contract_is_registered`'s per-key self-consistency loop even after
fixing the `== 70` line, so it had to be fixed to get the suite green — not scope creep, a
precondition for "green." Fixed via the project's own `goal_store.recompute_progress`, not by
hand-editing the numbers.

## Decision: dropping the magic number, not updating it (read this before assuming the obvious fix)

The established pattern in this file's git history (`5374567c`, `36c357fc`, `7913387d`) is:
whenever the "revised goal contract" (a *deliberately chained* epic — T-160..T-184, each row tied
to a D-039..D-045 decision and to prior rows via `deps`) grows, extend `expected` and bump the
literal count in the same commit. My first instinct was to do the same for T-185..T-195.

**I did not, on inspection.** T-185..T-195 are NOT a continuation of that chained epic: every one
of them has `deps: []`, none carries a `# D-0NN: T-...` chain comment like every row already in
`expected`, and they are ordinary ad hoc issue-fix tasks (AT-453, AT-583, AT-587, AT-617, AT-620,
AT-621, plus a re-check and a one-off Analyze re-run) — unrelated to each other and to the T-160
chain. Extending `expected` to cover them would misrepresent the test's own stated purpose
(pinning *this one* registration) as "pin every task ever," and the literal total-count assertion
would then need re-bumping on every future ad hoc task forever — which is exactly the kind of
assertion this project's own AT-100/AT-115 lineage exists to call out: a check that has stopped
measuring anything specific and just enforces "add one commit's worth of ceremony per unrelated
task."

**What I kept:** `progress["total"] == len(data["tasks"])` — a genuine invariant (the file's own
bookkeeping must match its own list) that survives ordinary project growth and would have caught
the real, second bug above (the 56-vs-57 drift) on its own merits.

**What I did NOT do:** weaken `actual == expected` (the T-160..T-184 dict match) — that assertion
is untouched and still proves those 25 rows are exactly as registered. Only the literal `70`
tail of the `total` line was cut.

## Recurrence guard: what's covered, what's queued, and why

Added `test_no_done_task_has_a_done_check_naming_a_file_that_does_not_exist` — the AT-647 mirror
of the existing "cannot fail" guard. Scoped to `status == "done"` tasks only, deliberately narrower
than the sibling test, for a measured reason: **~19 PENDING tasks legitimately name test files
that don't exist yet** (T-125, T-151..T-155, T-165, T-171, T-166..T-169, T-174, T-176..T-181),
because their work hasn't been built. A guard checking ALL tasks would have to be told about every
one of those or it fails today; checking only `done` tasks has **zero false positives** on the
current file (verified: no `done` task references a missing file before this unit's own T-160
edit) and catches the actual AT-647 failure mode — a task graduating to `done` while its own check
still can't pass.

**What this does NOT close, and why it's queued rather than built here:** T-185 itself was
PENDING when its file reference was wrong, so a done-only guard would never have caught it. The
honest guard for the pending case needs a live build-status signal goal.json doesn't carry — e.g.
the checker running `pytest --collect-only <path>` before granting PASS, confirming the named node
actually collects, as part of the checker protocol rather than a static repo-wide test. That is
real scope (touches `checker/SKILL.md`, not a `.goal/goal.json` edit), so I'm leaving it as a
queue row rather than building it in this unit:

> **QUEUE candidate:** before a checker writes `checked-PASS`, run
> `pytest --collect-only <node from the task's done_check>` and treat a collection error as a
> checker-side finding (the task's own check can't even be exercised, regardless of the unit's
> merits) — closes the PENDING half of the AT-647 class that the static `done`-only guard above
> cannot reach.

## How to verify (commands + expected)

- `uv run pytest tests/test_goal_done_checks.py tests/test_goal_contract_registration.py tests/test_goal_done_check_shapes.py -v` → 10 passed
- `uv run pytest tests/test_browser_scroll_reach_at408_416.py -v` → 2 passed (T-185's repaired check, run for real)
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → 1 violation (`stale-generated: docs/SNAPSHOT.md`), pre-existing and
  out of scope — see "Pre-existing, out-of-scope finding" below
- `uv run pytest` (full suite, run once, background — see below)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_goal_done_checks.py tests/test_goal_contract_registration.py tests/test_goal_done_check_shapes.py -v
collected 10 items
tests\test_goal_done_checks.py .......                                   [ 70%]
tests\test_goal_contract_registration.py .                               [ 80%]
tests\test_goal_done_check_shapes.py ..                                  [100%]
10 passed in 0.23s

$ uv run pytest tests/test_browser_scroll_reach_at408_416.py -v
collected 2 items
tests\test_browser_scroll_reach_at408_416.py ..                          [100%]
2 passed in 3.61s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
stale-generated: docs/SNAPSHOT.md — differs from regeneration; run `autotester snapshot`
1 violation(s)
```

**Full suite (`uv run pytest`, no args):** run once, in the background, per instruction
(memory-constrained host). Took 19m17s.

```
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
1 failed, 2070 passed, 6 skipped, 14 xfailed, 15 warnings in 1157.37s (0:19:17)
```

**The suite is green apart from AT-627.** The one failure is exactly the pre-named, load-sensitive
flake (`test_run_once_kills_a_real_hung_process_and_its_real_grandchild`, `FileNotFoundError` on a
`child.pid` a real spawned grandchild process didn't get to write before the assertion checked it
— a timing flake under this host's current load, not a regression from anything in this unit).
Neither `test_goal_done_checks.py` failure from before this unit reappeared, and no new failure
was introduced.

## Pre-existing, out-of-scope finding

`docs/SNAPSHOT.md` fails `autotester doctor`'s `stale-generated` check. Confirmed **not caused by
this unit**: `git status --porcelain docs/SNAPSHOT.md` in this worktree shows no diff (file
untouched here), and the main checkout's own git status at session start already showed
`M docs/SNAPSHOT.md` — this is a pending, uncommitted regeneration the orchestrator already holds
elsewhere. Not fixed here; flagged so it isn't mistaken for something this unit introduced.

## Capability coverage (each new claim -> its isolating falsification)

All four falsifications below were run in a throwaway copy built with `git archive HEAD` (this
commit) into `.work/falsify-<ts>/` (gitignored, outside git's view), executed via
`D:/autoTesting/.venv/Scripts/python.exe -m pytest` directly (never `uv run`, to avoid uv's
project-root detection objecting to a foreign directory) run from inside the copy so
`REPO_ROOT = Path(__file__).resolve().parents[1]` and all `.goal/`, `docs/` reads resolve to the
copy, never the live tree. None of the edited files import anything under `src/autotester`, so the
`.venv`'s `autotester.pth` (which forces `D:\autoTesting\src` onto `sys.path`) does not shadow
anything in this falsification — confirmed by each GREEN-before line actually reflecting the
copy's own edited content, not the live repo's.

| capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|
| T-190's `done_check` is exempted from the "cannot fail" guard by its waiver, and an unwaived copy of the same command is NOT exempt | `tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail` | delete `.goal/goal.json` T-190's `done_check.waiver` key | GREEN before: `1 passed`. RED after, exact reason: `AssertionError: ... carry no waiver: ['T-190']`. Restored: `1 passed`. |
| the "revised goal contract" test no longer depends on a literal task count, but still catches the T-160..T-184 dict going wrong AND now tolerates the true (81) count | `tests/test_goal_contract_registration.py::test_revised_goal_contract_is_registered` | single-hunk: `assert progress["total"] == len(data["tasks"])` → `... == 70` | GREEN before: `1 passed`. RED after, exact reason: `AssertionError: assert 81 == 70`. Restored: `1 passed`. |
| the new AT-647 recurrence guard fires when a DONE task's `done_check` names a missing file, and only then | `tests/test_goal_done_checks.py::test_no_done_task_has_a_done_check_naming_a_file_that_does_not_exist` | change DONE task T-186's `done_check.cmd` to name `tests/test_does_not_exist_at638.py` | GREEN before: `1 passed`. RED after, exact reason: `AssertionError: ...{'T-186': ['tests/test_does_not_exist_at638.py']}`. Restored: `1 passed` (and the full pair re-run: `8 passed`). |
| T-185's repaired `done_check` actually passes when run for real, where the old one could never collect | direct invocation, not a repo test (this IS the deliverable — a working `done_check`) | revert the command to the original `tests/test_scroll_reach.py` | GREEN (new cmd): `tests/test_browser_scroll_reach_at408_416.py .. — 2 passed`. RED (old cmd): `ERROR: file or directory not found: tests/test_scroll_reach.py` / `collected 0 items`. |

## Live browser evidence

Not UI-touching — no surface changed. Every edit is to `.goal/goal.json`, `.goal/dashboard.html`
(regenerated data only, no template/markup change), and two `tests/` files.

## Status: checked-PASS (cycle 1)

Verdict `qa/verdicts/at638-done-check-repair.md`, **Cycle checked: 1**, verdict commit `b4354156`,
merged to master as `4a580f2c`. `ISS-at638-remainder-2` and `AT-647` both verified fixed.

**The deliverable landed: the suite is green on master again.** `uv run pytest
tests/test_goal_done_checks.py tests/test_goal_contract_registration.py` → **8 passed**, run on the
merged master. That matters beyond its severity — the two reds had been standing all session, so every
checker dispatched had to be pre-told which failures to ignore, which is exactly how a real regression
gets waved through. The checker re-measured the full suite itself: **1 failed, 2070 passed** in 1141s
against the manifest's 1157s, the single failure being AT-627, the pre-named load-sensitive flake.

### The correction that matters, and it is against my own dispatch

I made the **`done_check.waiver` mechanism the headline attack point** of this check, telling the
checker as verified fact that it was newly invented and appeared nowhere. **That was wrong.** The
mechanism has existed since `90e4219d` — `waiver_of()`, `_waiver_offenders()`, a 20-character
hollow-waiver floor and a composition guard — and was **checker-PASSed on 2026-09-08**
(`qa/verdicts/at154-at157-fail-closed.md`), which had already deliberated and accepted the precise
tradeoff I asked for a fresh ruling on: *"a waiver is a sentence someone had to write and anyone can
grep."* I had searched `src/autotester/` and `.goal/goal.json`'s history and never looked in `tests/`,
where the code that reads `goal.json` lives. T-190 is merely the first task on disk to *use* one.

The checker re-derived this rather than inheriting my framing, and said so. Had it deferred, it would
have written a confident ruling on a settled question while this unit's real merits went unexamined
behind a manufactured headline. **Deference to whoever wrote the brief is a failure mode of checking,
not a courtesy.** Generalised and filed: `qa/QUEUE.md`, commit `e159f3f5` — three unverified negative
existence claims in one session (the sweep's, the at438 maker's, and mine), every one of them from a
pathspec that silently excluded the answer.

**What survives as a real finding is narrower and not chargeable here:** `.goal/goal.json` has no
`done_check` Pydantic schema at all — an unvalidated raw dict — so any future task can still
self-exempt with one ≥20-character sentence, no linked issue, no expiry. That is known, reviewed
infrastructure, not a hole this unit dug. The instance is well-founded: `schema/user_persona.py` is
confirmed absent and T-190's two cited plan-gate items are genuinely undecided.

### Verified independently by the checker, not taken on the manifest's word

The dropped magic number was falsified with **two mutations I had not suggested** (mutate a
T-160..T-184 row; add a bogus 82nd task without touching `progress.total`) — both still correctly RED,
so no criterion was weakened. T-185's repaired `done_check` was confirmed to **semantically** exercise
the AT-408/AT-416 scroll-invariance bug, not merely to resolve — the distinction this project paid for
under AT-218 (*resolution proves existence, not semantic correctness*). The 19-pending/0-done
recurrence-guard split was re-derived from `goal.json` independently and matched exactly. The
`monitor.py`/`register_product` avoidance was verified against the shared `/goal` skill's actual source
at `D:/ai_os/.claude/skills/goal/scripts/monitor.py:98` — the maker was right that calling `run()`
would have pointed the cross-project registry at a worktree path.

### Found beyond the brief, and fixed

The AT-638 split had left **C9's own `Verify` line in `qa/contracts/core-invariants.md` not naming the
new `tests/test_goal_contract_registration.py`** — so running C9's prescribed command silently skipped
`test_revised_goal_contract_is_registered`. A contract whose own verify command no longer reaches its
own test is the same defect class this unit exists to fix, one level up. The checker amended it
(checker-owned, tightening only, dated changelog entry). `AT-649` was filed for the deferred PENDING
half of AT-647's class — a task whose check can never pass, caught before it is ever built — so it is
tracked canonically instead of dying in a manifest.

### Two process notes recorded rather than buried

The checker **caught its own near-miss**: it had piped pytest through `tee`, and the reported exit code
was `tee`'s, not pytest's. It distrusted it and read the failure list directly. That is the
exit-code-masking trap this project has now hit four times. It also self-reported corrupting a ledger
line via backticks that bash command-substituted before python saw them, plus a stray `"source"` field
carried in by copy-paste — caught by re-reading the file immediately, fixed with targeted edits, and
every line re-validated as JSON.

**The merge was blocked and correctly handed back rather than forced.** The checker found the main
checkout held live uncommitted `.goal/*` work and refused to overwrite it; its non-destructive
alternative (`git update-ref`) was denied by the harness classifier, and it stopped there instead of
hand-editing `.git/refs/`. The "concurrent session" was this orchestrator. Resolved properly: the
in-flight work was **committed, not discarded** (`bae9568e`) after verifying the incoming `goal.json`
was a strict superset — identical task statuses, identical progress, differing only in the three
repaired `done_check`s — and `.goal/dashboard.html`, being generated, was regenerated from the merged
`goal.json` rather than resolved by picking a side.

No `docs/FEATURES.jsonl` row: this is issue-driven QA repair with no owning goal task, not a
user-facing capability.
