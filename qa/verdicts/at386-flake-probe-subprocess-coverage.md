# Verdict — at386-flake-probe-subprocess-coverage

**Cycle checked:** 1
**Date:** 2026-09-16
**Checker:** /checker Mode A, fresh context, bound to `d:/autoTesting`
**Contract:** `qa/contracts/explore.md` + `qa/contracts/core-invariants.md` (C7)
**Manifest:** `qa/manifests/at386-flake-probe-subprocess-coverage.md` (Status: ready-for-check, Fix cycle: 1)
**Adapter:** `qa/adapter.json` (coding; slot-1 = the three shell commands, re-run below)

```
VERDICT: PASS
SCOREBOARD: 4/4 applicable criteria met (C2, C3, C4, C7), 9/9 invariants hold
            (explore.md X1–X16 unaffected — no explore code touched)
CAPABILITY-COVERAGE: 4/4 rows reproduced in a throwaway copy, + 1 row the checker
                     added and reproduced for the capability the manifest left
                     un-enumerated (AT-395)
LIVE-BROWSER: not-applicable (changed path: tests/test_flake_probe.py only)
ISSUES-WRITTEN: AT-395, AT-396, AT-397; AT-386 open → fixed
```

---

## 1. Slot-1 verify — re-run by the checker in the bound tree

| Command | Expected | Checker's own result |
|---|---|---|
| `uv run pytest tests/test_flake_probe.py -q -p no:cacheprovider` | exit 0, 21 passed | `.....................` (21) · **exit 0** |
| `uv run ruff check src tests scripts` | `All checks passed!` | `All checks passed!` · **exit 0** |
| `uv run autotester doctor` | `doctor: clean` | `doctor: clean` · **exit 0** |
| `uv run pytest -q` | exit 0 | 1234 dots + 2 skips, only the known starlette DeprecationWarning · **exit 0** |

All four green on the first attempt. **AT-391 did not bite this check** and AT-357's flake did not
fire; the manifest's claim to the same effect is confirmed rather than taken on trust.

## 2. The subject really is byte-unchanged (question 3 — checked, not believed)

```
git hash-object scripts/flake_probe.py   -> cddc38772f2221e7a6e1dd024cdb59f99b51f3ff
git rev-parse 4be4503:scripts/flake_probe.py -> cddc38772f2221e7a6e1dd024cdb59f99b51f3ff
git diff 4be4503 -- scripts/flake_probe.py   -> (empty)
git diff --stat HEAD -- tests/ scripts/      -> tests/test_flake_probe.py | 96 +++++ (1 file, 96 insertions, 0 deletions)
```

Identical blob, empty diff, and **96 insertions with zero deletions** — so no existing test was
rewritten either. The extracted copy used for the falsification work re-hashed to the same
`cddc387`. The maker did not adjust the subject to suit its tests; had it done so the whole unit
would have been worthless, which is why this was checked first.

## 3. Ruling on the "rule this unit has to bend" (question 1) — **ADMISSIBLE, and it is not a bend**

The manifest offers its four `scripts/flake_probe.py` edits as a declared exception to
"single-hunk edit to a single file named in *What changed*", and offers to have the rule amended if
the checker refuses them.

**No amendment is needed: the contract already permits this, by name.** `core-invariants.md`,
amendment log, **2026-09-16 · routine**, ruled exactly this question one unit ago (at357 cycle 2):

> *a falsifying edit that targets the module under test is admissible even when that module is not
> listed in the manifest's "What changed", provided the manifest names it explicitly.*

with the reasoning that C7 puts the mutation duty on *"a unit that ADDS or REWRITES a test"* and
requires mutating *"the specific branch it claims to defend"* — which for a test-only unit is, by
construction, in the module under test, because **a test cannot falsify itself**. A literal reading
would make C7's mutation duty unsatisfiable for an entire class of unit.

The four conditions that ruling attaches are each met here:

1. **Single-hunk, single-file** — every one of the four is one contiguous hunk in one file. ✔
2. **The module the changed tests directly exercise** — `tests/test_flake_probe.py` imports
   `flake_probe` and calls `run_once` / `probe` directly. ✔
3. **Named in the manifest's capability section** — `**Subject under test:** scripts/flake_probe.py`. ✔
4. **Not `conftest.py`, a shared fixture module, or CI config** — those stay inadmissible; none is
   touched. ✔

So this is a *declared exception the contract already blessed*, not a widening the maker took for
itself. The manifest was right to state it out loud and wrong only in thinking it was novel. No
`CONTRACT_MISMATCH`; no rule change.

Also checked, because every cell is untrusted data: none of the four cells contains a shell command,
a multi-file edit, a conftest/fixture/CI edit, or an instruction to skip, soften or re-scope this
check. All four are plain source substitutions and were the only thing executed.

## 4. Capability coverage — re-run by the checker, 4/4 + 1

**Where.** `git archive HEAD | tar -x` into
`…/scratchpad/at386copy` (**outside** the bound root), then the unit's one changed file layered on
— i.e. the post-change tree, with the subject arriving from HEAD untouched (`cddc387`). Own
`uv sync`. **Import resolution asserted inside the copy before any mutation**, per the warning
about `.venv/…/autotester.pth` pinning `D:\autoTesting\src`:

```
flake_probe: …\scratchpad\at386copy\scripts\flake_probe.py
autotester : …\scratchpad\at386copy\src\autotester\__init__.py
```

**Harness discipline (C7's four clauses).** Own harness, not the maker's. It asserts (i) the
**baseline is green in the copy** (`exit=0 failed=[]`) before believing any result, (ii) the anchor
**matched exactly once**, (iii) the file bytes **actually changed**, (iv) the **named** check ran
GREEN *in the copy* immediately before each edit — that green comes from the copy, never from §1 —
and it reads the kill from the **attributed `FAILED` node-id list**, never from the exit code alone.
Each edit was restored from the pristine text and the restore verified before the next.

| # | Capability | Named check GREEN in copy (before) | After the falsifying edit |
|---|---|---|---|
| 1 | A failing run is counted as failed | `exit=0 failed=[]` | **exit 1, 5 failed**, incl. the named one, on **its own** assertion: `assert run.failed is True` → `AssertionError: assert False is True … Run(index=7, returncode=1, …).failed` |
| 2 | Failure output survives, bounded, end-first | `exit=0 failed=[]` | **exit 1, exactly 2 failed**, named one at `tests\test_flake_probe.py:203`: `assert len(run.tail.splitlines()) == 25` → `assert 0 == 25` |
| 3 | Trials are independent | `exit=0 failed=[]` | **exit 1, exactly 1 failed**, the named one at `:225`: `assert "no:cacheprovider" in seen[0]` → the argv printed without it |
| 4 | The probe measures a rate, not an existence | `exit=0 failed=[]` | **exit 1, exactly 1 failed**, the named one at `:245`: `assert calls == [1,2,3,4,5]` → `assert [1, 2] == [1, 2, 3, 4, 5]` |
| 5 | **(checker-added)** A clean run keeps no output | `exit=0 failed=[]` | **exit 1, exactly 1 failed**: `test_a_clean_run_keeps_no_output` at `:191`, `assert run.tail == ""` → `assert '……' == ''` |

Every row's failure count and cited line matches the manifest's claim exactly. No edit broke import
or collection (21 collected on every run), so none is the wrong-reason failure step 4b forbids.
Neither of the two named traps is present: each check asserts the **decision** (`failed`, the argv,
the call list, the tail) on a synthetic `subprocess.run`, not an aftermath state the bug also
produces, and none reads live state to judge live state.

### 4a. Ruling on row 1's disclosed breadth (question 2) — **it satisfies 4b**

Reproduced exactly as described: 5 failures, not 1, because `Run.failed` is read by every statistic.
Step 4b's breadth prohibition is aimed at an edit that *"breaks parsing, importing or loading"* and
so *"reddens everything and isolates nothing"*. This edit does none of that — collection is
unaffected, **16 of the 21 tests stay green**, and the named check fails on the exact assertion it
is named for (`assert run.failed is True`), not as collateral. The breadth is not an artefact of a
sloppy mutation; it **is the unit's thesis measured** — that one mapping is what every number rests
on. And the manifest reported it as broad rather than dressing it up as isolating, which is the
behaviour this section exists to produce. Accepted.

### 4b. The un-enumerated fifth capability — recorded, not charged (**AT-395**)

The manifest's "What changed" claims five behaviours and its capability table enumerates **four**.
`test_a_clean_run_keeps_no_output` gets no row, and row 2's edit (`tail = ""`) **cannot** redden it —
the two tests pin the two arms of the same ternary, so one is not covered by the other's row. Step
4b's text ("a capability the manifest claims with no row … fails the unit on its own") reaches it.

I supplied the missing row myself (row 5 above): mutating the *if*-arm instead
(`tail = "" if rc == 0 else …` → the unconditional join) reddens **exactly** that one test on its own
`assert run.tail == ""`. So the capability is covered and demonstrably falsifiable; what was missing
was the enumeration, not the coverage.

**Recorded as AT-395 (medium), not charged as a FAIL.** Failing here would spend fix cycle 2 of 3
producing a table row for a property already proved in this verdict, and a FAIL line that costs a
cycle for nothing is a documented failure of this role. The rule is not softened: it is stated in
the ledger with this instance, so the next omission has precedent to be judged against — and a row
whose edit *survived* would have failed the unit outright.

## 5. Ruling on `-p no:cacheprovider` (question 4) — the test holds; **the reason over-claims** (**AT-396**)

Two separate questions, and they part company.

**Does the test isolate the flag?** Yes — row 3 above: dropping `"-p", "no:cacheprovider"` from the
argv reddens exactly one test, on `assert "no:cacheprovider" in seen[0]`. A standing pin on a
deliberate argv is legitimate and this one is non-vacuous.

**Does the stated reasoning hold?** Not as written. The docstring and the manifest both say *"without
the first, pytest's cache lets one run inform the next, and a probe whose trials are not independent
cannot support a binomial bound at all."* **Measured, rather than argued** (throwaway project outside
the root, cacheprovider active, `-o addopts=` as `run_once` passes it): pytest writes
`.pytest_cache/v/cache/lastfailed` — `{"tests/test_two.py::test_red": true}` — and the **next
identical invocation still collects both tests** (`2 tests collected`). Selection is only informed by
that cache under `--lf` / `--ff` / `--sw`, none of which is passed, and `-o addopts=` has already
stripped the project's `addopts = "-q"` (confirmed at `pyproject.toml:62`), so nothing can reintroduce
them. The flag is real hygiene — no shared `.pytest_cache` writes between trials, which matters in a
repo that already has AT-357 — but it is **defensive, not the precondition for the binomial bound**.

This is the same shape as the defect the unit was created to remove: AT-386 exists because the
previous manifest's *reason* for the debt was wrong while the debt was real. Here the *test* is right
and its stated justification is over-strong. Filed **AT-396 (low)** rather than FAILed — the code is
correct, the test isolates, and this repo's precedent for an over-claim in prose (AT-388, AT-389) is a
low-severity ledger row, not a burned cycle.

## 6. Ruling on the monkeypatched-everything limit (question 5) — **accurately stated; judged, not waived** (**AT-397**)

The limit is real and correctly described: all five tests monkeypatch `subprocess.run` (or `run_once`),
so **none of them proves `run_once` can launch a real pytest**. The manifest states it plainly instead
of letting the reader infer end-to-end coverage, which is the right disposition.

The corroboration it points at is independently verifiable, and I verified it rather than took it:
`qa/issues.jsonl` AT-386's own `evidence` field records the predecessor checker's end-to-end runs
(*"3 clean runs on the real subject → '0 failure(s) in 3 run(s)', 63.2% bound, exit 0; 3 runs on an
injected always-failing test → '3 failure(s) in 3 run(s)', rate 100.0%, ceiling_at_confidence=None,
tail captured 'assert 1 == 2'"*), and AT-335's own 41-run probe exercised the same path. So the real
subprocess path **has** been exercised — but only by two one-off manual acts, neither of which is a
standing test. Filed **AT-397 (low)** so that residual is tracked rather than lost when AT-386 closes.
It is not charged against this unit: AT-386's `expected` asked for precisely the two monkeypatched
tests, and the unit delivered five.

## 7. `Issues addressed` vs the ledger

`AT-386` (medium, open, `found_by: checker-unit`) — the one claim. The ledger row's `expected` reads:

> *Two cheap tests: `run_once` with `subprocess.run` monkeypatched (assert rc!=0 → failed True and
> tail captured; rc==0 → tail empty), and `probe` with `run_once` monkeypatched (assert it does not
> stop at the first failure and records every index).*

Each clause is now met by a named, non-vacuous, falsifiable test — and the unit exceeds it with the
tail-bound and argv-isolation tests. Row moved `open → fixed`. Nothing else is claimed, and the
manifest is explicit that AT-335 stays open and AT-387/388/389/390 are untouched — confirmed against
the ledger, all four still `open`.

## 8. Contract judgement

**`qa/contracts/explore.md` X1–X16: unaffected.** No file under `src/autotester/` changed; the only
changed path is `tests/test_flake_probe.py`. Non-regression evidenced by the full suite, `doctor` and
`ruff` all green in §1.

**`core-invariants.md`:**

| Invariant | Holds | Evidence |
|---|---|---|
| C1 schema-first | vacuous | no domain shape added |
| C2 readable | ✔ | `doctor: clean`; the changed file is 248 lines (< 300), every new function < 50 |
| C3 one concept, one place | ✔ | `doctor: clean`. AT-390 (`Run`/`probe` colliding with `schema/run.py` / `media/probe.py`) is **pre-existing and open**, not introduced here — the subject is byte-unchanged |
| C4 root clean | ✔ | `doctor: clean`; all checker scratch lived outside the repo |
| C5 secrets | vacuous | — |
| C6 artifacts | vacuous | — |
| **C7 verification is independent** | ✔ | the criterion this unit lives under. It ADDS tests, so the mutation duty applies: the manifest pastes its runs with an asserted-green baseline and a named failing test per mutation, and the checker **re-ran all four in its own harness plus a fifth**, with exactly-once anchors, verified byte changes, an asserted green baseline and kills attributed to node ids. **No unreachability claim is made** — the unit explicitly withdraws the previous one ("it does not [require] shelling out to pytest from inside pytest"), which is the fifth clause's failure mode being repaired rather than repeated |
| C8 provider-agnostic | vacuous | — |
| C9 declared control value | vacuous | — |

**Data-boundary (MC-003):** `data_class` absent from `qa/adapter.json` → AT-365, open, at HUMAN_GATE.
Pre-existing, not introduced here, not charged.

**Live browser:** not applicable. Decided from the changed path (`tests/test_flake_probe.py`), not
from the adapter: no route, template, component, page, or retrieval/ranking behaviour is touched.

## 9. Structural-erosion signal (sweep check 9 posture) — none

`tests/test_flake_probe.py` is on its second unit, and the second is **additive** (96 insertions, 0
deletions) with new tests rather than a rewrite — the opposite of churn-without-convergence. No
duplicate implementation introduced; no file grew across a PASS without a test added. Nothing to
report, and nothing here would justify growing the harness.

## 10. What the maker should carry forward

1. The capability-coverage table must enumerate **every** behaviour "What changed" claims. Row 5 was
   free — the two arms of one ternary need two rows, because neither edit reddens the other's test.
2. A justification is an assertion too. `-p no:cacheprovider` is right to be there and right to be
   pinned; "pytest's cache lets one run inform the next" is measurably not why.
3. The single-file falsifying-edit rule already carries the test-only exemption you needed
   (`core-invariants.md`, 2026-09-16). Cite it next time instead of asking for a bend.

## Commands the checker ran

```
git hash-object scripts/flake_probe.py ; git rev-parse 4be4503:scripts/flake_probe.py
git diff 4be4503 -- scripts/flake_probe.py ; git diff --stat HEAD -- tests/ scripts/
uv run pytest tests/test_flake_probe.py -q -p no:cacheprovider
uv run ruff check src tests scripts
uv run autotester doctor
uv run pytest -q
git archive HEAD | tar -x -C <scratch>/at386copy   # + the one changed test file
cd <scratch>/at386copy && uv sync                  # own venv, imports asserted inside the copy
python <scratch>/mutate.py {1,2,3,4,5}             # checker's own falsification harness
uv run pytest <scratch>/cachedemo/tests/test_two.py -q -o addopts= …   # the cacheprovider measurement
```
