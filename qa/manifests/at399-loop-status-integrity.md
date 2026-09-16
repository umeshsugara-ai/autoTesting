# Manifest — at399-loop-status-integrity

**Unit:** AT-399 (loop-status half) — one forward-dated tick silenced the instrument built to
notice a dead loop
**Contract:** `qa/contracts/core-invariants.md` (C2, C3, **C7**)
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-399 (medium) — the `loop_status.py` half; see "What this does not claim"

## What was wrong — and it is worse than the issue says

AT-399 was filed about a `.last-sweep` stamp written ~6h in the future, and noted a *sibling risk*:
`loop_status.read_ticks` **sorts** stamps, so a forward-dated tick would be "silently reordered
rather than flagged".

I measured it before fixing, and the consequence is larger than reordering:

```
$ # two ticks: a real one on 2026-09-11, and one stamped 8h into the future
$ # now = 2026-09-16T15:00Z
ticks: 2 | last_tick: 2026-09-16T23:00:00+00:00
gaps: ['SLEEP 134.0h  2026-09-11T09:00:00+00:00 -> 2026-09-16T23:00:00+00:00']
asleep_now: False
>>> now - last_tick = -1 day, 16:00:00  (negative)
```

The open gap is `now - ticks[-1]`. Sorting puts the future stamp last, that subtraction goes
negative, no open gap is created and **`asleep_now` returns False for as long as the stamp stays in
the future.** The gap that *is* reported is inflated to a time that has not happened (134h, not the
true ~126h).

**One mistyped timestamp turns off the detector for a dead loop** — this module's own failure mode,
arriving through its own input. That is exactly the shape of thing AT-368 existed to catch, and I
built it in while writing the catcher.

## What changed

- `src/autotester/loop_status.py`
  - **`read_ticks` returns file order**, not sorted order. Sorting there was a silent repair, and a
    repaired log reads exactly like a healthy one.
  - **New `Anomalies`** (`future`, `out_of_order`, `any`) — corruption of the log itself, as
    distinct from gaps in what it records.
  - **`status` excludes future stamps from the arithmetic and counts them.** Excluding without
    counting would be the same silent repair in a new place; counting without excluding leaves the
    detector off. It needs both, and the tests pin both separately.
  - `last_tick` is now the last **credible** tick. Chronological sorting still happens — the gap
    maths needs it — but *after* the raw order has been recorded.
  - `report_lines` prints `CORRUPT:` rows naming the consequence, not just a count.
- `tests/test_loop_status_integrity.py` (new) — 6 tests.
- `tests/test_loop_status.py` — the integrity block moved out; it hit **339 > 300** and the doctor
  rejected it. Seam: that file asks what the log **records**; this one asks whether it can be
  **trusted**, which is a prior question.

## Capability coverage

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, `loop_status.py`) | Observed |
|---|---|---|---|
| A corrupt log is reported, not silently repaired | `test_loop_status_integrity.py::test_read_ticks_preserves_file_order` | `return stamps` → `return sorted(stamps)` (the original defect) | GREEN before (`6 passed`); after **FAILED 2**, incl. the named test at `:92` |
| A future stamp cannot hide a live outage | `::test_one_future_stamp_cannot_make_a_dead_loop_read_as_alive` | `credible = sorted(… if tick <= moment)` → `credible = sorted(raw)` | GREEN before; after **FAILED 2**, incl. the named test at `:63` — `asleep_now` back to False |
| Excluding a future stamp is *counted*, not silent | `::test_the_corruption_is_printed_not_only_counted` | `future=sum(1 for tick in raw if tick > moment)` → `future=0` | GREEN before; after **FAILED 2**, at `:118` |
| Out-of-order writes are counted | `::test_out_of_order_ticks_are_reported_rather_than_silently_sorted` | `out_of_order=sum(...)` → `out_of_order=0` | GREEN before; after **FAILED exactly 1**, at `:79` |
| The corruption reaches the reader, not just the object | `::test_the_corruption_is_printed_not_only_counted` | `if report.anomalies.future:` → `if False:` in `report_lines` | GREEN before; after **FAILED exactly 1**, `assert 'CORRUPT' in 'ticks: 2 …'` at `:118` |

Every anchor asserted to match exactly once and to be a real change; none broke import or
collection (6 collected every run). **Rows 2 and 3 are deliberately separate** — excluding without
counting and counting without excluding are different bugs, and one mutation each proves neither
substitutes for the other.

## What this does not claim

- **It fixes only the `loop_status.py` half of AT-399.** The other half — `.last-sweep` and
  `qa/QUEUE.md` being stamped from typed text rather than the clock — is written by the **checker**,
  and `qa/.last-sweep` is a checker-owned surface a maker must not write. AT-399 should stay open
  until that half lands; this unit is not grounds to close it.
- It does not validate the *content* of a tick line beyond its stamp, and does not detect a stamp
  that is wrong but plausible (backdated by an hour, say). Only impossible-vs-now and
  contradicts-file-order are caught.
- It does not change `autotester doctor`, which still deliberately excludes loop liveness.
- Our own `qa/.last-tick` is currently **clean** — `loop-status` reports no `CORRUPT` rows against
  it, so this fix is prophylactic here and was proven on synthetic logs, not on a live corruption.

## How to verify (commands + expected)

- `uv run pytest tests/test_loop_status.py tests/test_loop_status_integrity.py -q` → exit 0, 21 passed
- `uv run pytest -q` → exit 0
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean` (RED at 339 lines mid-build; the split resolves it)
- `uv run autotester loop-status` → exit 0, the six SLEEP rows, **no `CORRUPT` line** (our log is clean)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_loop_status.py tests/test_loop_status_integrity.py -q
.....................                                                    [100%]   (21 passed)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run autotester loop-status | head -4
ticks: 120 · last: 2026-09-16T09:32:03+00:00
  SLEEP 43.5h  2026-09-04T11:22:21+00:00 -> 2026-09-06T06:52:36+00:00
  SLEEP 7.5h  2026-09-06T06:52:36+00:00 -> 2026-09-06T14:21:04+00:00
  SLEEP 11.5h  2026-09-06T14:25:42+00:00 -> 2026-09-07T01:57:25+00:00
```

Full-suite output is pasted complete below rather than elided — **AT-414 was filed against me for
an elided paste**, and the at400 checker's correction was that the repair for an elision is a
complete paste, not its absence. This unit changes code, so the paste duty is live.

```
$ uv run pytest -q
........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 17%]
..................................................................s..... [ 23%]
........................................................................ [ 28%]
........................................................................ [ 34%]
........................................................................ [ 40%]
........................................................................ [ 46%]
........................................................................ [ 52%]
........................................................................ [ 57%]
........................................................................ [ 63%]
........................................................................ [ 69%]
........................................................................ [ 75%]
.........................................................s.............. [ 81%]
........................................................................ [ 86%]
........................................................................ [ 92%]
........................................................................ [ 98%]
...................                                                      [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:53
  D:\autoTesting\.venv\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
EXIT: 0
```

That is the command's entire output, redirected to a file rather than tailed. **My first attempt
at this paste was itself an elision** — `tail -6` had cut every dots line, leaving only the
warnings block, and I nearly pasted that as "complete". The fix for an elision being another
elision is the AT-414 shape exactly; I re-ran with full capture instead. The two `s` are the two
skips; there is no `N passed` line because `pyproject.toml:62` sets `addopts = "-q"`, making the
adapter's command `-qq`.

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv:**

1. Extract from HEAD; this unit's three files layered on.
2. `uv sync`; `autotester.loop_status.__file__` confirmed resolving **inside the extract**.
3. Baseline: `uv run pytest tests/test_loop_status_integrity.py -q` → **6 passed**.
4. Five mutations, each from a pristine backup with an exactly-once anchor assertion. All five
   killed; results in the table.
5. Extract deleted, **then** the full suite run — sabotage first, suite last. I had been running
   them in parallel and invalidated three suite runs that way; the sequencing fault is recorded in
   the at405 manifest and this is the first unit built the corrected way.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/loop_status.py`,
`tests/test_loop_status.py`, `tests/test_loop_status_integrity.py`. The only output surface is a
terminal, and `report_lines` exists so that output is asserted in tests rather than eyeballed.
`grep -rn "loop_status" src/autotester/ui/` → no match.

## Data-boundary gate (MC-003)

Exits 1 on the missing `data_class` — AT-365, open, at HUMAN_GATE. Not introduced here.

## Checker ruling (2026-09-16, verdict committed at d2504e8) — PASS, 3/3 criteria, 5/5 rows

The checker **re-derived the defect against HEAD** and reproduced my measurement exactly — one
forward-dated stamp made `asleep_now` return False and inflated the gap to 134.0h against a true
126.0h — so the unit's justification is independently confirmed, not merely asserted. All five
capability rows reddened on their named assertions in a copy it proved imports its own module, and
**my full-suite paste was byte-identical to its own run.** AT-399 correctly left **open**: the
`.last-sweep` half is checker-owned.

**The verdict was stranded.** The checker was terminated by an API session limit (HTTP 429) after
writing the verdict and appending AT-424, but before its own commit fired. The file sat untracked
until the maker committed it verbatim per step 8 — without that defence the verdict would have
existed only in a dead session's transcript.

### AT-424 (medium) — a hole in my fix

**A log whose stamps are ALL in the future renders `loop-status: no ticks recorded` — a false line
— and suppresses the `CORRUPT` row.** `credible` is empty, so `last_tick` is `None`, and
`report_lines` returns its early "no ticks" branch *before* it reaches the corruption rows.

That is the same failure this unit fixed, one level over: the fix excludes future stamps from the
arithmetic and counts them, but in the extreme case where every stamp is future the count is
computed and then never shown, and the tool asserts something false about the log. The checker
filed rather than charged, per the AT-326 precedent against strengthening a criterion mid-verdict.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at399-loop-status-integrity.md`, committed d2504e8; AT-399 stays open — checker-owned half; AT-424 filed)
