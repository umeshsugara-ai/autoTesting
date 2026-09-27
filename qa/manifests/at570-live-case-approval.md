# Manifest — at570-live-case-approval (AT-570, AT-660)

**Unit:** AT-570 — `RunApproval` (D-018 gate 2) was enforced on the crawl/explore path and on no
other. A UI case run (`POST /projects/{slug}/run` → `ui/routes_runs.py::trigger_run`) checked
nothing, and `stages/parallel_run.py::RunBudget.try_consume` returned `True` unconditionally when
`self._approval is None`. The delivery mechanism for that `None` was `run_cases(..., approval:
RunApproval | None = None)`: the one production caller (`ui/run_execution.py:159`) passed no
`approval=`, so the absence of a human authorisation was read as an *unlimited* one.
AT-660, folded in on the coordinator's URGENT correction: making `approval` non-optional closes
`None` and not `0`. `core/consent.py::_shortfalls` (the GATE) has no falsy guard and read
`max_actions=0` as a zero budget → refuse; `RunBudget.try_consume` had three falsy guards and read
the same `0` as *unlimited* → allow. One field, two opposite meanings, and the permissive side
governed what actually happened once a run started.

**Contract:** `qa/contracts/consent.md` CN1 (a refused run leaves no trace), CN2 (gate at the seam),
CN4 (never open-ended), **CN10** (one bound, one meaning, stated in the schema, asserted from both
sides in one test, non-zero fixtures, plausibility is visibility not enforcement, never rescued,
ratification disclosed); `qa/contracts/parallel-run.md` PR7 (one shared budget, never multiplied per
worker); `qa/contracts/core-invariants.md` C2 (300-line file / 50-line function caps), C3 (one
concept one place), C7 (falsifying sabotage per guard), **C12(b)** (absence needs its own
representation; a zero default is not a safe default; verify by construction).
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk: skip** (a consent seam on an existing route; no new screen or user journey)
**Issues addressed:** AT-570 (open → fixed here), AT-660 (open → fixed here). Not flipped by me —
`qa/issues.jsonl` status is the checker's call. Four NEW rows filed by me from the reserved block:
**AT-680** (serial path gated at preflight, no mid-run budget), **AT-681** (`WALL_CLOCK_PER_ACTION_S`
duplicates `browser/session.py`'s 8000 ms), **AT-682** (`Run.bounds` recorded but rendered nowhere),
**AT-683** (`approve` defaults every bound to unbounded while `crawl` defaults to bounded).
No existing row edited or renumbered.
**Goal task:** T-122 (blocked on a human act — see Disclosures)
**Executor:** claude-opus-subagent (`/maker` build agent)

## What changed

- **`src/autotester/schema/approval.py`** (147 → 160 lines): the three bound fields now state their
  chosen meaning in their own `description`, per CN10 requirement 3 — `max_actions`, `max_probes`,
  `wall_clock_s` all say **ZERO MEANS ZERO**: an approval granting 0 authorises no action at all,
  it does not mean "unbounded". Each names where the opposite reading lived and the live-disk fact
  that goes with it (`max_probes` is 0 on every row in `projects/pathlynks/approvals.jsonl`, so that
  is the axis where the old truthiness guard was live on disk; `wall_clock_s` carries 600000000.0 on
  the live row, which is 19 years, and nothing rejects it — CN10 requires that be *reported*, not
  capped). No new model, no new field on `RunApproval`.
- **`src/autotester/schema/run.py`** (81 → 107 lines): new `RunBounds` model (`approval_id`,
  `max_actions`, `max_probes`, `wall_clock_s`; `extra="forbid"`) and `Run.bounds: RunBounds | None`.
  This is CN10's visibility surface: the bounds a run actually ran under land in `run.json`.
  `None` means **NOT RECORDED** — deliberately not zeros, which would be indistinguishable from a
  measured zero (C12(b)).
- **`src/autotester/stages/parallel_run.py`** (266 → 229 lines) and **NEW
  `src/autotester/stages/run_budget.py`** (112 lines): the core fix.
  - `RunBudget.__init__(self, approval: RunApproval)` — no `| None`, and an explicit `ValueError`
    for a positional `None` ("a run with no approval is an unapproved run, never an unlimited one").
  - `try_consume` drops **all three** falsy guards (was `:158` wall clock, `:162` actions, `:164`
    probes on master). Every bound is now compared unconditionally. Per the coordinator's scope
    guard #5 this was NOT narrowed to `max_probes`: the disk evidence is narrower than the defect
    (the UI grant form carries `min='1'` on the two fields it has), but `cli_crawl.py:241-243`
    defaults all three to 0 with no `min=`, so `approve --kind live_case` with no bound flags writes
    an all-zero row that ran unbounded on every axis.
  - The wall-clock check is written `if approval.wall_clock_s <= 0: return False` rather than
    relying on `elapsed > granted`, because `time.monotonic()` has ~15 ms resolution on Windows and
    a fail-closed rule that is only usually closed is not one.
  - `run_cases(..., *, approval: RunApproval)` — **no default**. There is nothing left to omit, so a
    future caller cannot re-acquire "unlimited" by silence.
  - `WALL_CLOCK_PER_ACTION_S = 8.0` + `wall_clock_request_s(cases)`: sizing only, for the wall clock
    the preflight asks the gate for. Deliberately an over-estimate; explicitly **not** a policy
    ceiling (it bounds and caps nothing). Duplicated from `browser/session.py:237`'s 8000 ms settle
    ceiling rather than imported, because that file is at 300/300 — filed as AT-681.
  - The split into `run_budget.py` was forced by C2: the edits took `parallel_run.py` to 319 lines
    and `uv run autotester doctor` failed on `file-too-long`. Split by responsibility, not by size —
    `parallel_run.py` decides how many cases run at once; `run_budget.py` decides whether a case may
    spend anything, which shares its vocabulary with `core/consent.py` and `schema/approval.py`.
    `RunBudget`, `action_cost`, `WALL_CLOCK_PER_ACTION_S` and `wall_clock_request_s` moved whole (no
    copy left behind, C3) and the three importers were repointed.
- **`src/autotester/stages/explore_consent.py`** (48 → 54 lines): `covering_approval(project, store,
  bounds, *, kind: ApprovalKind = ApprovalKind.CRAWL)`. One gate, one place — a second
  `covering_approval` for cases would be C3's one-concept-two-places, and `ApprovalKind.LIVE_CASE`
  has existed unused in `schema/enums.py:165-172` since D-018. Every existing caller is unchanged.
- **`src/autotester/ui/routes_runs.py`** (155 → 186 lines): `_require_live_case_approval(project,
  store, cases) -> RunApproval`, called in `trigger_run` immediately after `_require_declared_values`
  and **before** `run_id = f"run-{ulid()}"` — so a refusal happens before a run id, a run directory,
  a browser or a `Run` record exists (CN1). It asks for the run's own bounds (`sum(action_cost(c))`
  and `wall_clock_request_s(cases)`, never 0, which would find any approval "wide enough") and turns
  `ApprovalRequired` into `HTTPException(403, str(exc))`, so the refusal text `require_approval`
  already builds reaches the operator verbatim. `approval` is threaded through `_execute_with_trace`
  and recorded on the saved `Run` as `RunBounds(...)`.
- **`src/autotester/ui/run_execution.py`** (176 → 190 lines): `_run_cases_in_parallel(..., approval:
  RunApproval)` (no default here either) passes `approval=approval` to `run_cases`. New
  `_run_entry_cases(...)` extracted from it — `_run_cases_in_parallel` hit 55 lines and doctor's
  `function-too-long`; the extraction is the entry-case leg, which was already a self-contained loop.
- **`docs/MAP.md`**: regenerated by `uv run autotester map` (generated sections only — the new module
  row and the new `RunBounds` schema row). `docs/SNAPSHOT.md` was regenerated by the same command and
  **reverted**, because its whole diff was another unit's F-065 ledger row, not mine (C10).

### Tests

- **NEW `tests/run_approval_fixture.py`** (60 lines) — `grant_live_case_approval(store, *,
  project="demo", target="https://demo.test", max_actions=10_000, max_probes=0,
  wall_clock_s=100_000.0, sign=True, expires_at="2099-01-01", run_kind=LIVE_CASE)`. Grant it, never
  bypass the gate. Not a test module (pytest does not collect it) and deliberately not in
  `crawl_fake.py`, which drags in a real `BrowserSession`.
- **NEW `tests/test_parallel_run_approval.py`** (166 lines, 9 tests) — the `RunBudget`/`RunApproval`
  file. Imports `_approval, _case, _isolated_factory, _project` from `test_parallel_run` (the
  repo's established cross-test-module pattern, e.g. `test_ui_runs_parallel_trace` imports from
  `test_ui_runs`). Holds the AT-660 **both-sides-in-one-test** assertion and the two PR7 budget
  tests moved out of `test_parallel_run.py`, which was within a few lines of the 300 cap.
- **NEW `tests/test_ui_runs_live_case_approval.py`** (268 lines, 9 tests) — the route-level gate,
  including one test per refusing state (C12 "verify by construction": each state is *built* and the
  message asserted to name it, and to NOT name the others).
- **Modified** `tests/test_parallel_run.py` (added `_approval()`, 7 call sites, PR7 tests removed),
  `tests/test_parallel_run_session_crash.py`, `tests/test_coverage_wiring.py` (`_run_with_urls` gained
  a `root: Path` parameter, threaded from its 5 call sites), `tests/test_ui_runs.py` (added
  `_approve_demo_runs`), `tests/test_ui_runs_parallel_crash_recovery.py`,
  `tests/test_ui_runs_parallel_trace.py`, `tests/test_ui_runs_serial_entry_order.py`,
  `tests/test_ui_runs_serial_entry_screenshot_namespace.py`,
  `tests/test_ui_runs_serial_resilience.py` — ten `run_cases` call sites and every
  `POST /projects/demo/run` test now grants a real approval first.

### Fixture bounds, stated explicitly (CN10 / coordinator instruction)

| fixture | max_actions | max_probes | wall_clock_s | signed | expires | why |
|---|---|---|---|---|---|---|
| `tests/run_approval_fixture.py::grant_live_case_approval` (defaults) | 10 000 | **0** | 100 000.0 | yes | 2099-01-01 | wide enough not to bound a test that is not about bounds; `max_probes=0` passed **explicitly** rather than inherited from the model default, because a case run spends actions and never probes (`_run_one` consumes `action_cost(case)` only) — and because it is the exact shape every UI-granted row has (AT-675) |
| `tests/test_parallel_run.py::_approval()` (defaults) | 10 000 | **0** | 3 600.0 | yes | 2099-01-01 | same reasoning, for the `run_cases` unit tests |
| `_approval(max_actions=0, wall_clock_s=0.0)` | 0 | 0 | 0.0 | yes | 2099-01-01 | the both-sides zero test, and the shape `approve` writes with no bound flags |
| `_approval(max_actions=10)` | 10 | 0 | 3 600.0 | yes | 2099-01-01 | PR7's **over-budget refusal** test: 4 cases × 3 steps = 12 > 10, so the shared budget must refuse at least one |
| `_approval(max_actions=50)` | 50 | 0 | 3 600.0 | yes | 2099-01-01 | the 200-thread race: exactly 50 accepted, never 51 |
| `grant_live_case_approval(max_actions=1)` | 1 | 0 | 100 000.0 | yes | 2099-01-01 | route-level shortfall: "actions 3 > approved 1" |
| `grant_live_case_approval(wall_clock_s=0.0)` | 10 000 | 0 | **0.0** | yes | 2099-01-01 | zero time is refused at preflight, before a browser opens |
| `grant_live_case_approval(sign=False)` | 10 000 | 0 | 100 000.0 | **no** | 2099-01-01 | the unsigned shape every pathlynks row really has |
| `grant_live_case_approval(run_kind=CRAWL)` | 10 000 | 0 | 100 000.0 | yes | 2099-01-01 | a crawl row must not cover a case run |
| `grant_live_case_approval(expires_at="2020-01-01")` | 10 000 | 0 | 100 000.0 | yes | **2020-01-01** | expiry still refuses |

## Verify — actual outputs

```
$ uv run pytest
============================= test session starts =============================
(2187 tests collected; full run started 04:05:10, finished 04:34:02)
...
=========================== short test summary info ===========================
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
1 failed, 2166 passed, 6 skipped, 14 xfailed, 15 warnings in 1698.64s (0:28:18)
PYTEST_EXIT=1
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
stale-generated: docs/SNAPSHOT.md - differs from regeneration; run `autotester snapshot`

1 violation(s)
```

**`uv run pytest` exits 1, and it is NOT my unit.** The single failure is
`tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`,
failing on `FileNotFoundError ... child.pid` -- the exact documented signature of **AT-518** ("failed
once in a whole-suite run (FileNotFoundError reading a spawned child's pid file), passed cleanly in
isolation immediately after -- a third live instance of the AT-196/AT-627 class") and of
**ISS-t164-1** ("Pre-existing, deterministic full-suite pytest failure unrelated to T-164 ... so C7's
literal 'uv run pytest exits 0' is currently false"). Re-run in isolation immediately afterwards:
`uv run pytest tests/test_flake_probe_real_process.py` -> `2 passed in 15.81s`. No file this unit
touches is in that test's import graph.

**`uv run autotester doctor` reports 1 violation, and it is NOT my unit either.**
`docs/SNAPSHOT.md` is stale **on `master`**, before this branch: `git show master:docs/FEATURES.jsonl
| grep -c F-065` = 1 while `git show master:docs/SNAPSHOT.md | grep -c F-065` = 0 -- another unit
appended a ledger row (F-065, and F-066 in `f0e6bab0`) without regenerating the snapshot, whose last
master commit is the older `f9adfdec`. `uv run autotester map` regenerates `SNAPSHOT.md` as a side
effect, so it briefly appeared in my working tree; I **reverted** it, because its entire diff is
another unit's feature rows and C10 says a unit's commit carries only that unit's paths. `docs/MAP.md`
IS in my commit, because its whole diff is mine (the new `stages/run_budget.py` row and the new
`RunBounds` schema row). I did not fix SNAPSHOT.md and I am not claiming doctor is clean.

**Master baseline, disclosed as incomplete.** The full suite on `master` did not complete on this
host: a first attempt reached 53% in ~25 minutes and then crawled (free RAM 1.9 GB, many Python
subprocesses) and I killed it. What I have instead is a **targeted** master baseline over the touched
surface: `uv run pytest tests/test_parallel_run.py tests/test_parallel_run_session_crash.py
tests/test_ui_runs.py tests/test_consent.py tests/test_explore_consent.py` -> `43 passed, 1 warning in
11.41s`, exit 0. So the surface I changed was green before I changed it; I cannot show from my own
measurement that the *whole* suite was green before it, which is why the two violations above are
argued from the repo's own issue rows and from `git show master:` rather than from a baseline run.

## Live browser evidence

None, and deliberately so. Every test in this unit stubs `BrowserSession.start`/`close` (RAM RULE),
and the one path that would exercise a real browser against a real product is exactly the path this
unit **closes**: a Pathlynks case run cannot run today, because no signed `live_case` approval exists
and `AUTOTESTER_APPROVAL_KEY` is not provisioned (AT-674). Granting either is Umesh's act, not mine —
see Disclosures. The refusal is proven by construction instead: each of the three refusing states is
built in a test and the message asserted to name that state and not the others.

## Capability coverage (falsifying edit → named test goes red)

Falsified in a **throwaway `git archive` copy of commit `1fdba241`**, extracted **outside** the
worktree at `…/scratchpad/at570-falsify/` with the copy as CWD (the copy as CWD matters: `tests/conftest.py`
imports `scripts/regression_proof.py`, which prepends a `src/` to `sys.path` — run from the real
worktree, a sabotaged copy would silently test the real code). The real worktree's files were never
mutated. `git stash` was never used. The copy was deleted afterwards.

**Asserted GREEN baseline in the copy first** (not assumed): `uv run pytest
tests/test_parallel_run_approval.py tests/test_ui_runs_live_case_approval.py
tests/test_parallel_run.py` → `26 passed, 1 warning in 10.25s`. **Asserted GREEN again after the
last restore**: `26 passed, 1 warning in 2.70s`, and `find . -name "*.orig"` returned nothing, so no
sabotage was left behind to make a later RED look real.

Every RED below ran in 0.2–2.8 s of pytest time (4–8 s wall including `uv` start-up) against that
10.25 s / 2.70 s GREEN baseline. These are not suspiciously-fast REDs: the whole named subset is a
sub-3-second file, so a collection error would show as `error`, not as the named `FAILED` rows.

| # | capability | falsifying edit (in the copy only) | check | RED — named failures | wall |
|---|---|---|---|---|---|
| 1 | **A run with no approval is unapproved, not unlimited.** `RunBudget` cannot be constructed without a `RunApproval` | restored master's `def __init__(self, approval: RunApproval \| None = None)` **and** master's `if approval is None: return True` at the top of `try_consume` | `pytest tests/test_parallel_run_approval.py` | `1 failed, 8 passed` — `test_a_run_budget_cannot_be_built_without_an_approval` | 1.26 s / 8 s |
| 2 | **The delivery mechanism is gone: `run_cases` has no `approval` default a caller can omit** | `*, approval: RunApproval,` → `*, approval: RunApproval \| None = None,` (master's exact signature) | same | `1 failed, 8 passed` — `test_run_cases_offers_no_approval_default_a_caller_can_omit` | 0.56 s / 4 s |
| 3 | **0 means ZERO on all three axes, and the gate and the budget agree** | restored **all three** truthiness guards (`if approval.wall_clock_s and …`, `if approval.max_actions and …`, `if approval.max_probes and …`) | same | `5 failed, 4 passed` — `test_the_gate_and_the_budget_agree_that_zero_bounds_grant_nothing`, `…zero_actions_bounds_the_run_to_zero`, `…zero_probes_refuses_a_probe`, `…zero_wall_clock_grants_no_time`, `test_the_shape_the_approve_command_writes_with_no_bound_flags_grants_nothing` | 0.58 s / 5 s |
| 3a | …and **each guard is independently load-bearing**: the wall-clock one | restored ONLY `if approval.wall_clock_s and …` | same | `2 failed, 7 passed` — `…zero_wall_clock_grants_no_time`, `test_the_shape_the_approve_command_writes…` | 0.62 s / 4 s |
| 3b | …the actions one | restored ONLY `if approval.max_actions and …` | same | `1 failed, 8 passed` — `…zero_actions_bounds_the_run_to_zero` | 0.47 s / 4 s |
| 3c | …the probes one | restored ONLY `if approval.max_probes and …` | same | `1 failed, 8 passed` — `…zero_probes_refuses_a_probe` | 0.37 s / 3 s |
| 4 | **The UI case-run path is gated at all** | reverted **both** `ui/routes_runs.py` and `ui/run_execution.py` to `master` (the literal pre-fix pair, so no half-state) | `pytest tests/test_ui_runs_live_case_approval.py` | `9 failed` — every test in the file, the 7 refusals plus both happy paths | 2.75 s / 6 s |
| 5 | **A `crawl` approval does not cover a case run** | `kind=ApprovalKind.LIVE_CASE` → `kind=ApprovalKind.CRAWL` in the preflight | same | `9 failed` — the named row is `test_a_crawl_approval_does_not_cover_a_case_run`; the other 8 fail too, correctly, because the fixture grants a `LIVE_CASE` row that a CRAWL-asking gate no longer finds | 1.41 s / 4 s |
| 6 | **CN1: a refused run leaves no trace** | moved the preflight to AFTER `run_id = …`, `run_dir = paths.run_dir(run_id)` and an `mkdir(parents=True)` | same | `7 failed, 2 passed` — exactly the 7 refusal tests, each on `_assert_not_run`; both happy paths still pass, which is the attribution: only the *no-trace* property broke | 2.02 s / 6 s |
| 7 | **The gate check is not vacuous (AT-218)**: it asks for the run's OWN bounds, never 0 | `max_actions=sum(action_cost(c) …)` → `max_actions=0`, `wall_clock_s=wall_clock_request_s(cases)` → `0.0` | same | `2 failed, 7 passed` — `test_an_approval_narrower_than_the_run_is_refused_with_the_shortfall`, `test_an_approval_granting_no_wall_clock_is_refused_before_a_browser_opens`. The other 7 still pass, which is the point: a 0-bound request still refuses a missing/unsigned/expired/wrong-kind row, so only the *bounds* half of the gate goes vacuous — precisely the shape that would otherwise pass review | 2.04 s / 5 s |
| 8 | **CN10 visibility: the run records the bounds it ran under** | deleted `bounds=RunBounds(approval_id=…, …)` from `store.save_run(Run(...))` | same | `1 failed, 8 passed` — `test_a_signed_live_case_approval_lets_the_run_proceed` on `assert run.bounds is not None, "a run must record the approval it ran under"` | 1.28 s / 4 s |

**What rows 3a–3c prove and what they do not.** The both-sides test uses `max_actions=0` *and*
`wall_clock_s=0.0`, so it stays green under 3a or 3b alone (the surviving guard still refuses) and
only goes red under 3 (both). That is honest rather than tidy: one test per axis is what gives
per-guard attribution, and the both-sides test's job is the *agreement* between the gate and the
budget, not per-axis coverage.

## Disclosures

Everything below is disclosed rather than claimed. Where I made a choice that is not mine to settle,
I say so and name who settles it.

### D1 — `0` means ZERO is **my build's choice and is NOT ratified**

CN10 requires one meaning on both sides; it does not tell me *which*. I chose **0 grants nothing**
and implemented it. The alternative is real: **0 = unbounded**, which would instead require the
*gate* (`core/consent.py::_shortfalls`) to stop refusing 0-bound approvals, i.e. the fix would land
in the other file and the three rows on disk would keep authorising unlimited probes. I did not pick
that because it makes the permissive reading the specified one, and because `RunApproval`'s own field
defaults are 0 — so "unbounded" would be what a caller gets by saying nothing, which is the C12(b)
defect this unit exists to remove. **This needs ratification by Umesh / the checker, not by me.** The
meaning is written into each field's `description` in `schema/approval.py` so it cannot be
re-discovered by reading the code twice, and it says so there.

### D2 — fixing the falsy guard makes every UI-granted approval refuse probes

In plain terms: **fixing the falsy guard makes every approval granted through the UI refuse probes;
the UI form has no field for that bound; re-granting is already required by AT-674.** Measured:
`grep -c max_probes src/autotester/ui/routes_crawl_approval.py` = 0, and the grant form's field set
has no `max_probes` input at all, so **no UI-granted approval can ever bound probes** — every one of
them carries 0, which now means zero. I did **not** add the field: that is AT-675's own scope. I also
do not attribute `max_probes=0` to careless granting — the tool cannot express that bound. (What *was*
hand-entered on the live row is 200000 actions and 600000000.0 seconds against form defaults of 200
and 600, plus a scope of the single word "everything" — AT-661, not mine.) This does not affect case
runs in practice, because a case run spends actions and never probes, but it does affect any future
path that probes under a UI-granted approval.

### D3 — plausibility cannot be checked without a policy number, so `wall_clock_s` is reported, not enforced

CN10 says plausibility is **visibility, not enforcement**, and the coordinator's correction was
explicit: report an implausible bound, do not cap it. I judge that **plausibility cannot be checked
without a policy number** — there is no non-arbitrary code-level answer to "is 600000000.0 seconds too
long", and inventing one would be a build making a gate decision. So: nothing in this unit rejects,
caps or warns on a large bound. What it does instead is record `Run.bounds` (`approval_id` + all three
bounds) into `run.json`, so a 19-year wall clock appears verbatim in the run's own record.
**Gap, filed as AT-682:** nothing *renders* it. `ui/routes_report.py` is at exactly 300/300 lines, so a
bounds card cannot be added without splitting an otherwise-untouched module in this commit (C10). A
human must open `run.json` to see it today. If the checker judges that "visible to a human" requires a
rendered surface, this unit does not yet meet CN10's visibility requirement and I am not claiming it
does.

### D4 — T-122 is BLOCKED by this unit landing, and unblocking it is Umesh's act, not mine

A Pathlynks case run cannot run after this change until **Umesh** (a) provisions
`AUTOTESTER_APPROVAL_KEY` in the repo-root `.env` — verified absent: `grep -c AUTOTESTER_APPROVAL_KEY
/d/autoTesting/.env` = 0 — and (b) grants a signed `live_case` approval. All three rows in
`projects/pathlynks/approvals.jsonl` are `run_kind=crawl`, none carries a `signature` key, and two of
the three are expired. **I did not and must not do either**: `granted_by: umesh` on every row means
granting is a human act, and signing needs the key. I created, edited, signed and back-filled **no**
row in any `approvals.jsonl`, added nothing to `.env`, and added no bypass flag, dev-mode escape,
env-var override, `or` fallback or default-allow path. The grant command the refusal prints is the
intended path (`uv run autotester approve …`, and `cli_crawl.py:236` already accepts
`--kind live_case`, verified).

### D5 — the serial path is gated at preflight but not budget-bounded mid-run

`_require_live_case_approval` runs before the serial/parallel branch, so **no** case run starts
without a covering approval. But `ui/run_execution.py::_run_cases_serially` — the **default** path
(`plan.n <= 1`) — never builds a `RunBudget` and never calls `try_consume`, so once a serial run
starts, the bounds constrain nothing. Only the parallel path enforces them. An over-budget serial run
never starts (the preflight refuses it); a serial run that starts and overruns is not stopped. Filed
as **AT-680**. Not fixed here because threading a budget through that loop touches a path with three
live regressions of its own (AT-574/AT-576/AT-577) and this unit's scope was the fail-open default.

### D6 — `CrawlBounds` is the bounds carrier for a non-crawl run

`_require_live_case_approval` builds a `CrawlBounds(max_actions=…, wall_clock_s=…)` to hand to
`covering_approval`, because that is the parameter type the existing single gate takes and the brief
said to reuse it rather than write a second checker. The name is now wrong for one of its two callers.
A `RunBounds`-style rename or a shared `Bounds` type would be a schema change with its own blast
radius; I did not start one. Naming it so the checker does not have to discover it.

### D7 — `_require_live_case_approval` is an adapter, not a second gate

It contains no approval logic: it builds the bounds, calls the one `covering_approval`, and translates
`ApprovalRequired` into `HTTPException(403, str(exc))`. All matching, signature verification, expiry
and shortfall logic stays in `core/consent.py::require_approval` (C3). If the checker reads it as a
second gate, that reading is wrong and I would rather be told than have it duplicated later.

### D8 — the refusal message names the state, and I corrected a wrong claim about which state fires

Per the coordinator's AT-674 correction, I do **not** claim the missing key is what refuses a Pathlynks
run today. An empty/absent signature raises `ApprovalUnsigned`-style "no signature" text and never
touches the key; only a *signed* row with no key configured produces "cannot verify". Both are tested,
and each test asserts the message names its own state and **not** the other
(`test_an_unsigned_live_case_approval_is_refused_naming_the_signature` asserts "no signature" and NOT
"cannot verify"; `test_a_missing_signing_key_refuses_a_signed_row_and_names_the_key` asserts "cannot
verify" + `AUTOTESTER_APPROVAL_KEY` and NOT "no signature"). What refuses a Pathlynks run today is
**reason 1**: no `live_case` row exists at all.

### D9 — the `approve`/`crawl` default asymmetry is real and untouched

The command whose job is to **set** a bound defaults to unbounded (`cli_crawl.py:241-243`:
`--max-actions 0`, `--max-probes 0`, `--wall-clock 0.0`, no `min=` on any), while the command it bounds
defaults to bounded (`cli_crawl.py:60-61`: 200 actions, 600 s). This is why "the bounds default to 0,
so a bad row is harmless" was wrong twice. I changed **no typer default** — that is its own blast
radius. Filed as **AT-683**. It is also why I did not narrow the guard fix to `max_probes`: the disk
evidence (UI `min='1'` on two fields → all three rows non-zero there) is narrower than the defect in
the code.

### D10 — scope lines I did not cross

No change to `write_policy` anywhere; `projects/pathlynks/project.json` untouched; **no** file under
`projects/` touched at all, and no existing approval row was special-cased, grandfathered, migrated,
back-filled, re-bounded or "tidied". `qa/contracts/*` untouched (I had no contract feedback to file, so
`qa/feedback-inbox.md` is also untouched). `docs/DECISIONS.md`, `docs/ARCHITECTURE.md` prose,
`qa/hooks/*`, `.claude/*` and `.goal/goal.json` untouched. `browser/session.py` untouched (it is at
300/300). Issue ids came only from the reserved block AT-680…AT-689; no existing id was reused or
renumbered.

### D11 — files I had to restructure, which the brief did not ask for

Two doctor failures forced structural edits I would otherwise not have made, and I am flagging them
because they are the largest diff surface a reviewer will see:
1. `parallel_run.py` reached **319** lines → `file-too-long`. I split `RunBudget`, `action_cost`,
   `WALL_CLOCK_PER_ACTION_S` and `wall_clock_request_s` into **new** `stages/run_budget.py` and
   repointed the three importers. This is a new file, which the edit-in-place discipline treats as a
   thing to justify: the justification is that C2 is a hard doctor gate, the split is by
   responsibility (consent budgeting vs fan-out), and nothing was duplicated — the names exist in
   exactly one module (C3).
2. `_run_cases_in_parallel` reached **55** lines → `function-too-long`. I extracted its entry-case loop
   as `_run_entry_cases(...)`, which was already a self-contained leg.
   Both are behaviour-preserving; the falsification in row 4 reverts that file pair wholesale, which
   also exercises the restructure.

### D12 — a test I judge weak, and one I judge load-bearing but indirect

- **Weak:** `test_the_parallel_path_receives_the_same_approval_as_its_budget` proves the parallel
  branch reaches `run_cases` *with* an approval (it would 500 on `TypeError` without one), but it does
  **not** exercise mid-run budget exhaustion through the route. That is deliberate and I think correct —
  the preflight already requires the approval to cover the whole run, so exhaustion is unreachable from
  the route — but it means the route has no test that a mid-run refusal is reported sanely. The budget's
  own exhaustion behaviour is covered at unit level (`test_pr7_aggregate_budget_is_not_multiplied_by_concurrency`).
- **Indirect:** `test_run_cases_offers_no_approval_default_a_caller_can_omit` asserts on a `TypeError`,
  i.e. on Python's arity checking rather than on a behaviour. I kept it because the *default* was the
  actual delivery mechanism of this defect, and nothing else fails if someone re-adds `= None`.

### D13 — verification gaps

- **The full-suite baseline on `master` never completed on this host.** A first attempt reached 53% in
  ~25 minutes and then crawled (free RAM 1.9 GB, many Python subprocesses); I killed it. I used a
  **targeted** master baseline instead: `uv run pytest tests/test_parallel_run.py
  tests/test_parallel_run_session_crash.py tests/test_ui_runs.py tests/test_consent.py
  tests/test_explore_consent.py` → `43 passed, 1 warning in 11.41s`, exit 0. So I can show the touched
  surface was green before my change, but I **cannot** show the whole suite was green before it, and any
  pre-existing failure in the full run below is therefore not proven pre-existing by me.
- No live browser evidence, for the reason in that section: the one real-product path is the path this
  unit closes, and opening it needs Umesh's key and grant.
- `tests/test_parallel_run_approval.py` imports `_approval`, `_case`, `_isolated_factory` and `_project`
  from `test_parallel_run` rather than redefining them. That is the repo's established pattern
  (`test_ui_runs_parallel_trace` ← `test_ui_runs`; `crawl_fake`; conftest ← `tests_mutation_fixtures`),
  and it means a change to those fakes moves two files' behaviour at once.
- `tests/test_coverage_wiring.py::_run_with_urls` gained a `root: Path` parameter, threaded from its 5
  call sites. This was a **bug I introduced and fixed**: I first inserted `_approve_demo_runs(scratch_root)`
  inside that helper, where `scratch_root` is the fixture *function*, not a value —
  `TypeError: unsupported operand type(s) for /: 'FixtureFunctionDefinition' and 'str'`. Recording it
  because it means that helper's signature changed for a test-plumbing reason, not a behavioural one.
- Two other mechanical mistakes, both caught and fixed, both disclosed so the checker does not have to
  find them: my patch script's import injection matched neither branch in
  `test_ui_runs_parallel_crash_recovery.py` and `test_ui_runs_serial_resilience.py` (they import from
  `test_ui_runs_parallel_trace`, not `test_ui_runs`), giving 5 × `NameError`; and `_approve_demo_runs`
  first hardcoded `target="https://demo.test"` and still 403'd, because onboarding normalises the posted
  `base_url` and `require_approval` matches the target **exactly** — it now reads `project.base_url` back
  from disk.

### D14 — CN10 moved under me while I was building, and I folded both new clauses

`master` advanced to `e64ccf22` during this build and `qa/contracts/consent.md` gained two CN10
clauses I was not briefed on (`git diff a27fb03b..master -- qa/contracts/consent.md`). I read them and
folded both rather than shipping against the older text:
1. **"The over-budget test names the bound it exceeds and by how much."**
   `test_pr7_aggregate_budget_is_not_multiplied_by_concurrency` now asserts
   `(approval.max_actions, naive_total, naive_total - approval.max_actions) == (10, 12, 2)` — the
   bound, the demand and the margin, so the refusal is demonstrably the bound firing. At the route
   level the margin is already in the asserted message text: `"actions 3 > approved 1"`.
2. **"The remediation covers all three bound fields, not the one visible on disk."** Already satisfied
   — all three guards were dropped, which is also what the coordinator's scope-guard correction #5
   required. The checker's own amendment entry records that this clause *corrects the checker's* earlier
   narrowing to `max_probes`; I did not narrow.

**Merge hazard, not a defect.** My branch is based on `a27fb03b`; `master` is now `e64ccf22` and has
appended `AT-690`, `AT-691`, `AT-692`, `AT-693`, `AT-694` (and others) to `qa/issues.jsonl` while I
appended `AT-680`–`AT-683` to the same file's end. **`qa/issues.jsonl` will conflict on merge**, purely
positionally — no id collides, both sides are pure appends, and the resolution is to keep both blocks.
Flagging it because the checker merges the reviewed SHA and should not discover this mid-merge. Nothing
else I touched has moved on master (`git diff a27fb03b..master` lists no `src/` or `tests/` path I own).

## Status: ready-for-check
