# Verdict — at368-loop-liveness-visible

**Unit:** AT-368 — the maker loop slept 4.85 days and nothing said so
**Contract:** `qa/contracts/core-invariants.md` (C2, C3, C7; no feature contract owns `tooling`)
**Manifest:** `qa/manifests/at368-loop-liveness-visible.md` (Status: ready-for-check)
**Cycle checked:** 1
**Date:** 2026-09-16
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`, read-only toward the artifact
**Adapter:** `qa/adapter.json` (coding; `isolation.sandbox = worktree-copy`)

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (C2, C3, C7), 3/3 invariants hold
FAILURES: none
CAPABILITY-COVERAGE: 4/4 rows reproduced, plus 3 checker-added probes, all killed with the named test
LIVE-BROWSER: not-applicable (src/autotester/loop_status.py, src/autotester/cli_loop.py,
  src/autotester/cli.py, tests/test_loop_status.py, docs/MAP.md — no UI surface, verified)
ISSUES-WRITTEN: AT-381, AT-382, AT-383 (AT-368 stays OPEN — see "The issue does not close")
```

## What I re-ran myself (bound tree, `d:/autoTesting`)

| Command | My result |
|---|---|
| `uv run pytest tests/test_loop_status.py -q` | `...............` (15) · **exit 0** |
| `uv run pytest -q` | **exit 0** (final run, after the concurrent AT-357 commit landed) |
| `uv run ruff check src tests scripts` | `All checks passed!` · **exit 0** |
| `uv run autotester doctor` | `doctor: clean` · **exit 0** |
| `uv run autotester loop-status` | six SLEEP rows + the disclosure line · **exit 0** |
| `uv run autotester loop-status --strict` | **exit 0** (the loop is awake) |

Every clause of the manifest's "How to verify" reproduced. The `EXIT: 0` with no `N passed`
count is **not** a hidden result: `pyproject.toml:62` sets `addopts = "-q"`, so the adapter's own
`-q` is effectively `-qq` and the count is never emitted. The isolated file run does print its 15
dots, which I read as the count. Claim accepted.

### One transient red, fully attributed away from this unit

My **first** `uv run pytest -q` exited 1 on
`tests/test_mutation_check_judgement.py::test_it_refuses_a_file_that_escapes_the_sandbox_by_climbing`
and `::test_an_interrupted_run_with_real_failures_is_not_a_kill`, both with
`baseline is NOT green (pytest exit 4) … file or directory not found: tests/test_mod.py` — a
mutation sandbox that vanished under its own run. My **first** `uv run autotester doctor` also
exited 1: `file-too-long: tests\test_mutation_check.py — 314 lines > 300`.

Neither is this unit's. Both were the **concurrent AT-357 session's uncommitted work** in the
shared tree: at the time, `git status` showed ` M tests/test_mutation_check.py` at 314 lines with
`qa/evidence/at357-scope-sandbox-assertions/` untracked beside it, while the same file at `HEAD`
was 241. I proved the attribution three ways rather than assuming it:

1. `tests/test_mutation_check_judgement.py` alone: green **3×** consecutively.
2. A throwaway copy of `HEAD` + this unit's five files only, outside the bound root:
   `doctor: clean`, exit 0.
3. That session then committed (`de484fd fix(AT-357)…`, `d243b55`), `tests/test_mutation_check.py`
   dropped to 168 lines, and the bound tree's `doctor` and `pytest -q` both went green — final
   runs in the table above.

The residual two failures I saw inside the isolated copy's own full suite were
`test_the_sandbox_is_removed_*` (**AT-357 verbatim**, known open at the time) and
`test_ui_sources.py::test_uploaded_recordings_are_gitignored` (the copy has no `.git`). Neither is
chargeable, and both directions are false-FAIL, never false-PASS.

## Criteria

### C2 — readable by a human and an agent · **MET**
`doctor` clean in the bound tree and in the isolated copy. Sizes: `loop_status.py` 182,
`cli_loop.py` 36, `cli.py` 294, `tests/test_loop_status.py` 241 — all under 300; every new module
opens with a docstring stating its one job. `docs/MAP.md` is genuinely generated, not hand-typed:
I ran `uv run autotester map` **inside the copy** and the file came back byte-identical to the one
the maker submitted, and the diff in the bound tree is exactly the two generated rows.

### C3 — one concept, one place · **MET**
Two new modules, each with a stated reason in the manifest, and the reason checks out: `cli.py` is
at 294 lines, so the ~20 lines of `loop_status_cmd` inline would put it at ~314 and `doctor` would
reject it — the same split `cli_issues.py` and `cli_video.py` already use. No `*_v2` / `*_new`
names. `cli.py`'s diff is one import and one `app.command(...)` registration, matching the
existing `explore` pattern. No duplicate public names (doctor's duplicate-concept rule, clean).

### C7 — verification is independent · **MET**
`uv run pytest -q` exits 0 and the manifest pastes real output. The sabotage claim was re-run in
my own harness, never read. Baseline asserted green **in the copy** before any mutation
(`15 passed`, exit 0), each anchor asserted to match **exactly once**, each file re-read from disk
to confirm it changed, each kill attributed to a named test parsed out of the `FAILED` lines —
not to a bare exit code. Nothing broke import or collection: 15 tests collected on every run.

## Capability coverage — 4/4 reproduced independently

Method: `git archive HEAD` into the session scratchpad **outside** `d:/autoTesting`, this unit's
five files layered on, its own `uv sync` venv. Per the dispatch's warning about
`.venv/autotester.pth` holding the literal `D:\autoTesting\src`, I asserted the import origin
before trusting anything:

```
LOOP_STATUS FILE: …\scratchpad\at368copy\src\autotester\loop_status.py
```

Baseline in the copy, before any edit: `uv run pytest tests/test_loop_status.py -q` → 15 passed,
exit 0. Each mutation applied from a pristine copy and reverted before the next.

| # | Capability | Falsifying edit | My result |
|---|---|---|---|
| 1 | the OPEN gap is counted against `now` | `if now - ticks[-1] >= span:` → `if False:` | exit 1, **3 failures**, incl. `test_an_open_gap_is_counted_against_now_not_only_against_the_next_tick` |
| 2 | a pause explains only the gap it is open on | `if later - earlier >= span` → `… and not paused` | exit 1, **exactly 1**: `test_a_closed_gap_is_never_credited_to_the_current_pause` |
| 3 | the tool states what it cannot know, in the output | `retro_blind` body → `return False` | exit 1, **exactly 2**: `test_the_tool_says_out_loud_what_it_cannot_know`, `test_the_disclosure_is_printed_not_merely_available_on_the_object` |
| 4 | every reported stamp renders in one timezone | drop `.astimezone(UTC)` | exit 1, **exactly 1**: `test_every_reported_stamp_is_rendered_in_one_timezone` |

Failure counts match the manifest's (3 / 1 / 2 / 1) exactly.

**Row 4 — the story the dispatch asked me to verify independently.** It holds. I did not carry
over the maker's run; I applied all four mutations to the **current** file in my own copy, in one
harness, in one pass. Row 4's test dies on precisely the assertion it is named for, not on a
collection error and not on the arithmetic the old version overclaimed:

```
>       assert "+05:30" not in rendered, "a second offset in the output is the defect"
E       AssertionError: a second offset in the output is the defect
E           ticks: 2 · last: 2026-09-16T15:00:00+05:30
E             SLEEP 120.5h  2026-09-11T09:00:00+00:00 -> 2026-09-16T15:00:00+05:30
```

The maker's diagnosis of its own vacuity is also confirmed as a side effect: under the same
mutation, `test_a_gap_spanning_two_offsets_is_measured_by_real_elapsed_time` **survives** (row 4's
run produced exactly one failure, and that is not it) — `fromisoformat` returns aware datetimes and
Python subtracts them correctly across offsets, so the old claim really was protecting nothing.
The rewritten test isolates the rendering property instead, and the rendering property is real.

**Three extra probes I added**, because only 6 of the 15 tests are bound to a capability row and
C7's mutation duty is on the unit's tests, not only on its claims. All three killed, each with its
own named test:

- `report_lines`'s "no gaps" branch → `if False:` → 1 failure, `test_a_clean_loop_says_so_rather_than_printing_nothing`
- the no-ticks branch → `return []` → 1 failure, `test_an_empty_log_is_reported_as_unknown_not_as_healthy`
- `span = timedelta(hours=threshold_hours * 100)` → 7 failures, all gap-semantics tests

No vacuous test found. The copy and both harness scripts were deleted; the bound tree carries only
this unit's five paths (`git status` confirmed after cleanup) and I never edited a file in it.

## Mode D — not applicable

Changed paths hold no UI surface. I re-ran the manifest's grep myself: `grep -rn "loop_status"
src/autotester/ui/` → no match (and `src/autotester/ui/` exists and is populated, so that is a real
negative, not a missing directory). A repo-wide `grep -rn "loop_status" src --include=*.py` returns
only `cli.py:287` and `cli_loop.py` itself. Judged against D-024's indirect clause too: no page's
data flows through this module; its only output surface is a terminal, and `report_lines` exists so
that output is asserted in tests rather than eyeballed. Mode D correctly skipped.

## Rulings on the three points the manifest raised against itself

**1. "It cannot keep the loop alive" — legitimate scoping, not an under-delivery, but it does not
close the issue.** The premise is true: nothing in this repo runs while the app is closed, so a
heartbeat built here could not fire during the outage it exists to catch — a guard that cannot
fail, which is AT-218's class exactly. AT-368's `expected` does offer two arms, and this is the
second one's *reader* half made operative: `qa/.paused` now distinguishes a deliberate stop from a
dead loop for the gap that is actually open, and `--strict` is the exit code that says so. Refusing
to build the unbuildable arm and saying so up front is the right call, and the manifest earns
credit for stating it before being asked.

**2. Keeping it out of `autotester doctor` — correct, and for the right reason.** `doctor` is in
the adapter's slot-1 verify chain, so a liveness rule there would make every unit's verification
depend on whether somebody had been at the keyboard recently, and would fail units for reasons
that have nothing to do with the artifact under test. `doctor` enforces static design rules
(C2/C3/C4); liveness is not one. Upheld.

**3. Six outages, not one — filed, as AT-381.** I reproduced the run in the bound tree (103 ticks
by then) and got the same six rows: 43.5 + 7.5 + 11.5 + 25.8 + 32.9 + 116.4 = **237.6 h**. The
manifest was right to leave the call to me and right not to file it itself. It matters because it
reclassifies AT-368 from an anomaly to the normal case — the loop has stopped for over six hours on
six occasions in twelve days. One row for the class, not five for the instances.

## The issue does not close

**AT-368 stays `open`.** Not a failure of this unit — it never claimed otherwise, and I am judging
the ledger claim, not the artifact. The instrument is built, tested, and honest, but nothing calls
it: an outage is still visible only to a human who chooses to type the command, which is the same
dependency on a person being present that produced the 4.85-day silence. That residual is filed as
**AT-383**, with the concrete remedy (Mode B sweep check 1, which already reads `qa/.last-tick`'s
age by hand and would be reading a measured, pause-aware classification instead — and which is not
in the verify chain, so ruling 2 is not contradicted).

**AT-382** records the upstream blind spot the tool discloses: `/maker resume` deletes
`qa/.paused`, so a finished pause leaves no trace and no closed gap can ever be proven deliberate.
The fix is in the maker skill, **outside this bound root**, so it is filed as an upstream defect
per C9's second bullet rather than charged here. Disclosing it in the tool's own printed output —
rather than letting a reader take six `SLEEP` rows at face value — is the strongest thing about
this unit.

## Issues written

| id | sev | what |
|---|---|---|
| AT-381 | medium | six outages totalling ~237.6 h; five never filed — AT-368 is a class, not an incident |
| AT-382 | medium | `/maker resume` deletes `qa/.paused`; a finished pause leaves no trace (upstream) |
| AT-383 | medium | `loop-status --strict` has no caller — the instrument is installed with no consumer |

Not charged, recorded only: AT-357 (`test_the_sandbox_is_removed_*`, since committed by the
concurrent session) and AT-365 (`qa/adapter.json` has no `data_class`, so MC-003 exits 1 —
at HUMAN_GATE, `qa/gates/at365-data-class-declaration.md`, not introduced here and the changed
paths hold no data).

## EXPLANATION

Every verify command reproduced green in the bound tree, all four capability rows died under my own
mutations with the named test in the failure list, and three probes I added against the nine tests
no row binds also died — the test file is not vacuous, and row 4, the one the maker's own first
sabotage pass failed to kill, now dies on exactly the rendering assertion it is named for. The only
reds I saw came from a concurrent session's uncommitted work in the shared tree and disappeared when
that session committed, proven by an isolated copy that was clean throughout. The unit is scoped
honestly rather than over-claimed, so it PASSes on what it claims — but AT-368 stays open, because
an instrument nobody runs leaves the silence exactly as quiet as it was.
