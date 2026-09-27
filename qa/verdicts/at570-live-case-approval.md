# Verdict — at570-live-case-approval (AT-570, AT-660)

**Cycle checked: 1**
**Checked SHA:** `a169d45a` on `wave/at570-live-case-approval` (worktree
`D:\autoTesting\.claude\worktrees\agent-ac0c11769db9a7239`), based on `a27fb03b`.
**Contracts:** `qa/contracts/consent.md` CN1, CN2, CN6, CN9, **CN10** (current text, read at check
time, including both clauses added 2026-09-28); `qa/contracts/core-invariants.md` C2, C3, C7, C10,
C12(b); `qa/contracts/parallel-run.md` PR7; `qa/contracts/ui.md` U11 (adjacent, see AT-698).
**Checker:** fresh-context `/checker` subagent. Nothing under `src/` or `tests/` was edited by me.

## VERDICT: PASS

The fail-open is closed at the only shipped case-run entry point, and it is closed in the
fail-closed direction on all three bound axes. Every capability row in the manifest reproduced
under my own sabotage, in my own isolated copy, with the counts and test names the manifest states.
Two non-clean exits are real and neither is charged to this unit; both are named below rather than
papered over. Four findings are recorded, one of them new and filed by me (AT-698); none of them
reaches the bar for a FAIL.

---

## 1. Ratification — stated in the terms CN10 requires

**The meaning of `0` was chosen by the build and is NOT ratified.** `0` now means *zero budget* on
both sides. The build agent chose that (manifest D1); no human ratified it. CN10's ratification
clause binds this verdict, so it is said plainly rather than left to be inferred from a PASS:

- The alternative (`0` = unbounded) is real and was rejected by the build, not by Umesh.
- The choice is implemented **consistently on both sides**, which is what I am entitled to judge:
  the gate (`core/consent.py::_shortfalls`, bare comparisons, unchanged) and the run
  (`stages/run_budget.py::RunBudget.try_consume`, all three truthiness guards removed) now agree.
  I confirmed by reading both and by the sabotage in §3.
- It is **documented in the schema field descriptions** — `schema/approval.py:56-79`, all three of
  `max_actions`, `max_probes`, `wall_clock_s` carry "ZERO MEANS ZERO" plus the sentence "Chosen by
  the AT-570 build as the fail-closed direction; awaiting ratification." That is the third CN10
  requirement and it is met including the disclosure of its own unratified status.
- A PASS is not blocked by the absence of ratification (fail-closed is the reversible direction),
  and this verdict is not silent about it. **Umesh's to ratify or reverse.**

## 2. The CN10 visibility judgement — mine, made, and written into the contract

The build agent asked directly (D3) whether a value in `run.json` that no surface renders satisfies
CN10's visibility requirement, and correctly declined to claim it did.

**RULED: MET.** `schema/run.py::RunBounds` on `Run.bounds`, saved into `run.json`, satisfies the
clause. Reasons:

1. The clause's own words are "**the run's own record** states the bounds it ran under". `run.json`
   *is* the run's own record; `Run` is its schema model.
2. In this repo an artifact on disk is a human-readable surface by design (core-invariants C6, "a
   human can edit any artifact").
3. A **rendered** surface is a stronger obligation than the text carries. This clause was already
   narrowed once (amendment log 2026-09-28) precisely because the checker had imposed more than it
   had standing to. Tightening it inside the very check it governs, and then failing the unit on the
   tightening, is retroactive contract movement — the decision drift the Lab Protocol exists to catch.
4. Absence has its own representation: `bounds: RunBounds | None = None`, `None` = NOT RECORDED,
   never zeros (C12(b)). Verified in `schema/run.py:101-107` and asserted in the happy-path test.

I have recorded this ruling **in CN10 itself**, plus an amendment-log entry, so the next build does
not re-derive it (`qa/contracts/consent.md`, CN10, new clause + log entry 2026-09-28 "record a
ruling"). **The thinness is real and named:** AT-682 stays open, `ui/routes_report.py` is at exactly
300/300 lines (I measured it — the build agent's reason for not adding a card is true), and the next
unit touching that file carries the rendering. A future tightening to require a rendered surface is a
routine amendment made *before* the unit it judges, never during its check.

## 3. What I falsified myself vs accepted on report

**I broke all eleven capability rows myself**, not three. Method: `git archive HEAD` into
`…/scratchpad/chk570`, with that copy as CWD, its own `.venv`, the repo-root `.env` copied in. The
worktree's files were never mutated; `git stash` was never used; no `*.orig` was left behind.

- **Asserted GREEN baseline first:** `uv run pytest tests/test_parallel_run_approval.py
  tests/test_ui_runs_live_case_approval.py tests/test_parallel_run.py` → `26 passed`, exit 0.
- **Asserted GREEN again after the last restore:** `26 passed in 2.20s`.

Every restore was done with `git show HEAD:<path> > <copy path>` or from a byte copy, never by
reverse-patching, so no half-state survived into the next row.

| Row | My sabotage | My measured RED | Matches manifest? |
|---|---|---|---|
| 1 | `RunBudget.__init__(approval: RunApproval \| None = None)` + `if approval is None: return True` | `1 failed, 8 passed` — `test_a_run_budget_cannot_be_built_without_an_approval` | exact |
| 2 | `run_cases(*, approval: RunApproval \| None = None)` | `1 failed, 8 passed` — `test_run_cases_offers_no_approval_default_a_caller_can_omit` | exact |
| 3 | all three truthiness guards restored | `5 failed, 4 passed` — the 5 named rows | exact |
| 3a | **only** the wall-clock guard | `2 failed, 7 passed` — `…zero_wall_clock_grants_no_time`, `…approve_command_writes…` | exact |
| 3b | **only** the actions guard | `1 failed, 8 passed` — `…zero_actions_bounds_the_run_to_zero` | exact |
| 3c | **only** the probes guard | `1 failed, 8 passed` — `…zero_probes_refuses_a_probe` | exact |
| 4 | both UI files reverted to `a27fb03b` wholesale | `9 failed` — every test in the route file | exact |
| 5 | `kind=LIVE_CASE` → `kind=CRAWL` in the preflight | `9 failed` | exact |
| 6 | preflight moved after `run_id`/`run_dir`/`mkdir(parents=True)` | `7 failed, 2 passed` — exactly the 7 refusal tests; both happy paths still green | exact |
| 7 | preflight asks `max_actions=0, wall_clock_s=0.0` | `2 failed, 7 passed` — the shortfall test and the zero-wall-clock test | exact |
| 8 | `bounds=RunBounds(...)` deleted from `save_run` | `1 failed, 8 passed` — `test_a_signed_live_case_approval_lets_the_run_proceed` | exact |
| 9 | `_approval(max_actions=10)` → `10_000` | `1 failed, 8 passed` — `assert (10000, 12, -9988) == (10, 12, 2)` | exact |

**The specific thing I was told to judge about rows 3a–3c: do the per-axis rows actually fix the
gap, or only appear to?** They fix it. Measured: under 3a alone, the both-sides test
(`test_the_gate_and_the_budget_agree_that_zero_bounds_grant_nothing`) stays **green** — the build
agent's own admission is accurate — but `test_an_approval_granting_zero_wall_clock_grants_no_time`
goes red on its own. Under 3b alone, only the actions test reddens. Under 3c alone, only the probes
test. So each of the three guards is independently load-bearing and independently attributed. The
per-axis tests are not decoration around the both-sides test; they are the coverage the both-sides
test cannot give, and the both-sides test carries the *agreement* property that no per-axis test can.
This is the AT-548/549/550 class handled correctly, and I verified it rather than reading it.

**Also falsified myself, beyond the capability table:**

- **CN10's over-budget clause is genuinely satisfied, not textually satisfied.** I read
  `tests/test_parallel_run_approval.py:132-146`. It asserts
  `(approval.max_actions, naive_total, naive_total - approval.max_actions) == (10, 12, 2)` — bound,
  demand, margin — **and then** asserts the refusal actually fires (`any(_exhausted(r) …)`) and that
  `ran_cost <= approval.max_actions < naive_total`. A tuple assertion alone would have been the
  contract's letter without its point; this is not that.
- **CN10's "one test, both sides" is a real both-sides assertion.** `…:62-77` constructs ONE approval
  and drives `require_approval` (gate) and `RunBudget.try_consume` (run) against it. Not two tests.
- **The doctor/SNAPSHOT contradiction, resolved from the objects rather than the claims.** Both
  parties were right about different objects. `git diff docs/SNAPSHOT.md` on master showed an
  **uncommitted** regeneration in the maker's working tree; `doctor` reads the working tree, so
  "doctor on master is clean" was a dirty-tree measurement. `git show master:docs/SNAPSHOT.md` reads
  the committed blob, which **is** stale. A fresh clone of master would have failed doctor. I then
  tested the build agent's C10 argument directly: regenerating `docs/SNAPSHOT.md` inside my clean
  copy of **this branch** produced a diff consisting **entirely** of F-065 and F-066 ledger rows plus
  the 6-row display window shifting — **zero** content originating in at570 — and `doctor` went clean
  after. So the revert was correct under C10, the violation is inherited from committed master, and
  it is not charged here. (The maker has since filed AT-697 on doctor's blindness to this and
  committed the regeneration; neither is this unit's.)
- **No silencing of the AT-518 failure.** `git diff a27fb03b HEAD -- tests/test_flake_probe_real_process.py`
  is empty. `git diff a27fb03b HEAD | grep -E '^\+.*(xfail|skipif|pytest\.skip|deselect|--ignore)'`
  matches **only** the manifest's own quotation of a pytest summary line — no mark, no quarantine,
  no `addopts` change anywhere on the branch. Import graph: the failing module imports
  `scripts/flake_probe.py`, `test_flake_probe_runner`, `test_mutation_check_judgement`;
  `flake_probe.py` imports only stdlib plus `mutation_check.kill_tree`. **No file this unit touches
  appears in it.** Not charged.
- **No bypass path for T-122.** `git diff a27fb03b HEAD -- src | grep -E '^\+.*(getenv|environ|DEV|BYPASS|SKIP|force| or True)'`
  → **nothing**. No `projects/` path is in the diff at all (so no `approvals.jsonl` row was created,
  signed, edited or back-filled), `.env` is not in the diff, and `grep -c AUTOTESTER_APPROVAL_KEY
  /d/autoTesting/.env` → `0`, still absent. The claim holds.
- **No second gate, and no un-gated case-run entry point.** `grep -rn "run_cases(\|RunBudget("
  src/ scripts/` → exactly two call sites, both inside the gated path. `run_case_pipeline` is reached
  only from `ui/run_execution.py`; `stages/agent_loop.py` has no caller; `stages/explore.py` is the
  already-gated crawl path; `cli.py` exposes no case-run command. So `POST /projects/{slug}/run` is
  the **only** shipped case-run entry point, which is what CN1's "every shipped entry point" clause
  requires be true for the property to hold. D7 is accurate — `_require_live_case_approval` contains
  no approval logic (C3 upheld).
- **CN1's no-trace ordering is real.** `routes_runs.py:146-149`: the preflight is the last thing
  before `run_id = f"run-{ulid()}"`; `ProjectPaths` mkdirs only inside `run_dir(...)`, which is
  called after. Row 6 confirms the property is asserted, not assumed.
- **The refusal reaches the operator readably.** `ui/error_pages.py` (AT-596) is registered on
  `starlette.exceptions.HTTPException`, so the `HTTPException(403, str(exc))` renders as a themed
  HTML page for a browser and keeps JSON for API callers. `core/consent.py::_grant_command` emits
  `--max-actions`/`--wall-clock` when non-zero, so the printed command carries the bounds the run
  needs — CN6's paste-and-re-run property survives into this new path.
- **Manifest accuracy, spot-checked at `file:line`.** Every line count claimed is exact
  (`approval.py` 160, `run.py` 107, `parallel_run.py` 229, `run_budget.py` 112, `routes_runs.py` 186,
  `run_execution.py` 190, `routes_report.py` 300, `browser/session.py` 300). `session.py:237`
  `timeout_ms: int = 8000` (AT-681 accurate). `cli_crawl.py:241-243` defaults `0/0/0.0` with no
  `min=`, and `--kind` help lists `live_case` (D9 and D4 accurate). `ruff check src tests scripts`
  → `All checks passed!`. **I found nothing the manifest overstates.**
- **Merge hazard, simulated not performed.** Ids only on the branch: AT-680, 681, 682, 683. Ids only
  on master: AT-662…AT-697. **No id collides**, both sides are pure appends, `merge=union` resolves
  it. Note for the record: master's `qa/issues.jsonl` already contains **10 duplicated ids**
  (AT-288–291, AT-547–552) *before* any merge — pre-existing, identical on both sides, the AT-656
  `dict[id] = row` shape, and not this unit's. I did not merge, push or close out the manifest.

**Accepted on report, not independently reproduced** (stated so the line is not blurred):

1. The 28-minute full-suite timings and the `2166 passed` count from the build agent's own run. I ran
   my own full suite (§4) and use mine.
2. The build agent's *master* targeted 43-test baseline (`43 passed`, exit 0). I did not re-run it.
3. D13's self-disclosed mechanical mistakes (the `scratch_root` fixture bug, the import-injection
   misses, the hard-coded target). Self-disclosed, already fixed, no live trace to check.
4. The claim that the first master full-suite attempt died at 53% on RAM. Unverifiable after the fact.

## 4. Verify commands — run by me, never piped

Redirected, never piped (AT-692):

```
$ uv run ruff check src tests scripts          # in the worktree's archived copy
All checks passed!

$ uv run autotester doctor
stale-generated: docs/SNAPSHOT.md - differs from regeneration; run `autotester snapshot`
1 violation(s)
```

```
$ uv run pytest > .work/checker-at570-fullsuite.txt 2>&1; echo exit=$?     # MY OWN full run
=========================== short test summary info ===========================
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
1 failed, 2166 passed, 6 skipped, 14 xfailed, 15 warnings in 1571.53s (0:26:11)
PYTEST_EXIT=1

$ uv run pytest tests/test_flake_probe_real_process.py > .work/checker-at570-flake-isolated.txt 2>&1
2 passed in 15.76s
exit=0
```

**My own full run reproduces the build agent's to the count** — `1 failed, 2166 passed, 6 skipped,
14 xfailed`, same single failure, on my own 26-minute run. The failure signature in my log is
`FileNotFoundError: [Errno 2] … test_run_once_kills_a_real_hun0\child.pid` at
`pathlib.py:1044` — the exact AT-518 shape — and the module passes `2 passed` in isolation
immediately after. Evidence: `.work/checker-at570-fullsuite.txt`, `.work/checker-at570-flake-isolated.txt`
in the worktree.


**`uv run pytest` does not exit 0, and I am not writing "tests pass".** The adapter's literal pass
condition for the first gate command is **unmet repo-wide** — that is **AT-695 (high)**, and
**AT-518 (medium)** is the failure itself. The one failure is
`tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`,
`FileNotFoundError` on `child.pid`, the documented AT-518/ISS-t164-1 signature. It is not charged to
this unit, for the three reasons measured in §3 (module untouched, no mark added, import graph
disjoint). **`uv run autotester doctor` reports 1 violation**, inherited from committed master and
resolved in §3; also not charged. A PASS here means *this unit's criteria are met and it introduced
neither failure*, not that the repo's gate commands are green. They are not, and AT-695 is the row
that says so.

## 5. Criteria

| Criterion | Verdict | Basis |
|---|---|---|
| **CN1** a refused run leaves no trace, at every shipped entry point | **MET** | Preflight before `run_id`; row 6 (7 refusal tests red on `_assert_not_run`, both happy paths green); only one shipped case-run entry point exists |
| **CN2** the gate lives at the seam, not in each caller | **MET** | `_require_live_case_approval` is an adapter over the one `covering_approval`; no matching, expiry or signature logic duplicated (D7 verified by reading) |
| **CN6** bounds are checked, with the shortfall named and a working grant command | **MET** | `"actions 3 > approved 1"` asserted at route level; `_grant_command` emits the bounds; themed HTML refusal via AT-596 |
| **CN9** the gate is unconditional; tests grant rather than bypass | **MET** | `tests/run_approval_fixture.py` grants a real signed `RunApproval`; ten `run_cases` call sites and every `POST …/run` test now grant one. No localhost predicate added |
| **CN10** one meaning both sides | **MET** | Gate unchanged + all three guards dropped; verified by rows 3/3a/3b/3c |
| **CN10** stated in the schema docstring | **MET** | `schema/approval.py:56-79`, all three fields, incl. the unratified disclosure |
| **CN10** asserted from both sides in ONE test | **MET** | `test_parallel_run_approval.py:62-77`, one approval, `require_approval` + `RunBudget` |
| **CN10** non-zero fixtures + an over-budget refusal test exists | **MET** | Fixture table is disclosed in full; non-zero defaults; PR7 over-budget test present |
| **CN10** the over-budget test names bound, demand AND margin | **MET** | `(10, 12, 2)` asserted, plus the refusal itself; row 9 kills a widened bound |
| **CN10** remediation covers all three bound fields | **MET** | Rows 3a/3b/3c each independently load-bearing |
| **CN10** plausibility = visibility, not enforcement; no invented ceiling | **MET** | `RunBounds` records; nothing caps or warns; `WALL_CLOCK_PER_ACTION_S` bounds nothing (sizing only) — I read it to confirm |
| **CN10** visibility | **MET** | §2, ruled and written into the contract; AT-682 open for rendering |
| **CN10** never rescued | **MET** | No `projects/` path in the diff; no grandfather, migration or back-fill anywhere |
| **CN10** ratification disclosed | **MET** | §1 |
| **PR7** one shared budget, never multiplied per worker | **MET** | Budget moved whole, not copied; 200-thread race test and the over-budget test both live in the new file and both green |
| **C2** 300-line file / 50-line function | **MET** | doctor reports no `file-too-long`/`function-too-long`; every touched file measured under cap |
| **C3** one concept, one place | **MET** | `RunBudget`/`action_cost`/`WALL_CLOCK_PER_ACTION_S`/`wall_clock_request_s` exist in exactly one module; grep found no copy left in `parallel_run.py`; one `covering_approval` |
| **C7** falsifying sabotage per guard, baseline asserted green both sides | **MET** | I re-ran all eleven myself in an isolated copy with asserted green before and after; every anchor asserted to match before writing |
| **C10** a unit's commit carries only that unit's paths | **MET** | 22 paths, all named in "What changed"; the SNAPSHOT revert is the C10-correct call (§3) |
| **C12(b)** absence has its own representation; no zero-as-safe default | **MET** | `RunBudget(None)` now raises; `run_cases` has no default to omit; `bounds` is `None`-not-zeros; refusing states built by construction, each asserting its own message and **not** the others |

## 6. Findings recorded, none blocking

1. **AT-698 — NEW, filed by me, high.** After this lands, **every** UI case run is refused until a
   signed `live_case` approval exists, and **the UI cannot create one**:
   `ui/routes_crawl_approval.py:188` hard-codes `run_kind=ApprovalKind.CRAWL` on the row it writes,
   and `:104` filters the approvals table to `CRAWL`, so a CLI-granted `live_case` row is not even
   listed. F-042 shipped "complete no-CLI crawl approval" and ui.md U11 requires authorizing a crawl
   without the CLI; the same operator can no longer start a **run** without it. **Not a FAIL:**
   consent.md's out-of-scope list explicitly excludes a UI grant form, fail-closed is the correct
   direction, and the refusal does tell the operator exactly what to type. But the manifest discloses
   only the narrower field gap (D2/AT-675) and "the CLI is the intended path" (D4) — it never states
   that the no-CLI surface can no longer start a run at all. That is an **under-disclosure of an
   operator-facing consequence**, and it is the one place this manifest fell short of its own
   standard. Best fixed in the same pass as AT-675 — one edit to `routes_crawl_approval.py` closes both.
2. **AT-680 — the serial path has no mid-run budget. ACCEPTABLE, shipped with the row.** Judged, not
   waved through: the fail-open this unit exists to close was *"no approval = unlimited"*, and that is
   closed on **both** paths — `_require_live_case_approval` runs before the serial/parallel branch, so
   no case run of either width starts without a covering, signed, unexpired, wide-enough approval, and
   the preflight requests the run's **whole** action total, so an over-budget run cannot start. What
   remains is that a serial run which starts within bounds is not stopped if it overruns wall clock.
   That is missing *enforcement of a bound*, not a fail-open, and the serial path never had a budget
   before this change either — nothing regressed. It does **not** reopen AT-570.
3. **AT-682 — `Run.bounds` rendered nowhere.** §2. Open, correctly filed, not blocking.
4. **AT-681 / AT-683** — accurate as filed; I verified both at `file:line` (§3).

## 7. Notes for the maker on close-out

- On PASS the maker flips the manifest to `checked-PASS` and handles the merge. **I did not merge,
  push, or touch the manifest.**
- **Handshake hygiene, worth one line:** `qa/manifests/at570-live-case-approval.md` was
  **modified-uncommitted** in the worktree at check time (the row-9 falsification block, the D14
  fold, and a "commits this manifest describes" header). I checked the **code** at `a169d45a` and the
  manifest content as it stands on disk. C10 wants the reviewed SHA merged; make sure the final
  manifest commit lands on the branch and that `Cycle checked: 1` here matches `Fix cycle: 1`. No
  `src/` or `tests/` path changed after `1fdba241`, and `a169d45a` touches three lines inside one
  test body, which I falsified separately (row 9) — so the reviewed code surface is complete.
- `qa/issues.jsonl` on master now also carries **AT-698** from me. Keep both append blocks on merge;
  no id collides.
- T-122 stays **blocked on a human act**: Umesh provisions `AUTOTESTER_APPROVAL_KEY` and grants a
  signed `live_case` approval. That is correct and the build agent was right not to do either.
- **For Umesh, one decision:** ratify or reverse `0` = zero budget (§1). Everything else here is
  settled.
