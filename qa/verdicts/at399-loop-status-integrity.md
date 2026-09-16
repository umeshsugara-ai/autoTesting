# Verdict — at399-loop-status-integrity

**Cycle checked:** 1
**Date:** 2026-09-16
**Mode:** A (unit check), bound to `d:/autoTesting`
**Contract:** `qa/contracts/core-invariants.md` — C2, C3, C7
**Manifest:** `qa/manifests/at399-loop-status-integrity.md` (Status: ready-for-check, Fix cycle: 1)
**Adapter:** `qa/adapter.json` (coding) — all three slot-1 commands re-run by me

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met, 3/3 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (src/autotester/loop_status.py, tests/test_loop_status.py, tests/test_loop_status_integrity.py — no UI surface; independently confirmed loop_status has no consumer under src/autotester/ui/)
ISSUES-WRITTEN: AT-424 (new, medium) · AT-399 left OPEN (see §3)
EXPLANATION: I re-derived the defect against HEAD myself and reproduced the manifest's
measurement exactly — one forward-dated stamp made `asleep_now` return False and inflated the
reported gap to 134.0h against a true 126.0h. All three verify commands are green in my own runs,
all five capability rows redden on the assertion they are named for in a throwaway copy that I
proved imports its own module, and the pasted full-suite output is byte-identical to mine. One
genuine hole found outside the cited criteria — a log whose only stamps are future renders the
false line `loop-status: no ticks recorded` and suppresses the CORRUPT row — filed as AT-424
rather than charged, per the AT-326 precedent against strengthening a criterion mid-verdict.
```

---

## What I re-ran (my own runs, not the manifest's)

| Command | My result |
|---|---|
| `uv run pytest tests/test_loop_status.py tests/test_loop_status_integrity.py -q` | exit 0, **21 dots** — matches the claim |
| `uv run pytest -q` | **exit 0**, full capture, 24 lines — see §5 |
| `uv run ruff check src tests scripts` | `All checks passed!` (exit 0) |
| `uv run autotester doctor` | `doctor: clean` (exit 0) |
| `uv run autotester loop-status` | exit 0, six SLEEP rows, **no `CORRUPT` line** — see §4 |

---

## 1. Re-deriving the defect against HEAD — the justification holds

I did not take the manifest's measurement. I extracted `git show HEAD:src/autotester/loop_status.py`
into a throwaway copy outside the bound root, built a two-line tick log (one real stamp on
2026-09-11, one typed 8h into the future) and ran `status` at `now = 2026-09-16T15:00Z`:

```
=== HEAD (pre-fix) ===
ticks: 2 | last_tick: 2026-09-16 23:00:00+00:00
gaps: ['SLEEP 134.0h  2026-09-11T09:00:00+00:00 -> 2026-09-16T23:00:00+00:00']
asleep_now: False
now - last_tick = -1 day, 16:00:00

=== POST-FIX ===
ticks: 2 | last_tick: 2026-09-11 09:00:00+00:00
gaps: ['SLEEP 126.0h  2026-09-11T09:00:00+00:00 -> 2026-09-16T15:00:00+00:00']
asleep_now: True
now - last_tick = 5 days, 6:00:00
```

The pre-fix block reproduces the manifest's figures exactly, including the negative
`-1 day, 16:00:00`. The consequence the manifest claims is the consequence I measured:
`asleep_now` is False while the loop has genuinely been dead for five days, and the gap that *is*
reported (134.0h) is measured to a time that has not happened, against the true 126.0h. **The
justification is not overstated; if anything the issue row understated it as mere "reordering".**

I also confirmed the removed `sorted()` breaks no other consumer: `read_ticks` has exactly one
caller outside its own module chain (`cli_loop.py` → `status`/`report_lines`), and `status` now
sorts the credible subset itself before the gap arithmetic.

## 2. Rows 2 and 3 are genuinely separate bugs — the claim is verified, not accepted

Both mutations were applied independently from a pristine restore, with the whole integrity file
run each time. The **failure sets genuinely differ in both directions**:

| Mutation | What it removes | Failure set |
|---|---|---|
| R2 `credible = sorted(raw)` | excludes-but-still-counts → **stops excluding** | `test_one_future_stamp_cannot_make_a_dead_loop_read_as_alive`, `test_a_future_stamp_does_not_inflate_the_gap_it_sits_at_the_end_of` |
| R3 `future=0` | counts-but-still-excludes → **stops counting** | `test_one_future_stamp_cannot_make_a_dead_loop_read_as_alive`, `test_the_corruption_is_printed_not_only_counted` |

The symmetric difference is the proof. R2 alone kills the gap-inflation test that R3 leaves green;
R3 alone kills the printed-not-counted test that R2 leaves green. **Neither mutation substitutes for
the other**, so the two rows are not one row counted twice — the manifest's claim is correct and I
verified it rather than reading it.

## 3. The AT-399 scoping — I agree, and AT-399 STAYS OPEN

The ledger row's remedy has two halves: *"write the stamp from the clock, and have loop-status
refuse a stamp later than now."* This unit closes the second. The first — `qa/.last-sweep` and
`qa/QUEUE.md` being stamped from typed text — is written by a **checker**, and both files are named
in the checker skill's Hard rules as checker-owned surfaces (`qa/QUEUE.md`, `qa/.last-sweep`). A
maker writing them would be a segregation-of-duties breach in the direction the pair exists to
prevent, so declining that half is **correct, not a dodge**.

**AT-399 remains `open`. I have not flipped it to `fixed`,** and the manifest is right that this
unit is not grounds to close it. The remaining half is a duty on checker sessions (stamp from the
clock, not from typed text) — I have stamped nothing in this check, and I am recording the duty
here so the next sweep reads it rather than rediscovering it.

## 4. Our own `qa/.last-tick` is clean — verified

```
$ uv run autotester loop-status
ticks: 123 · last: 2026-09-16T09:48:20+00:00
  SLEEP 43.5h  2026-09-04T11:22:21+00:00 -> 2026-09-06T06:52:36+00:00
  SLEEP 7.5h  2026-09-06T06:52:36+00:00 -> 2026-09-06T14:21:04+00:00
  SLEEP 11.5h  2026-09-06T14:25:42+00:00 -> 2026-09-07T01:57:25+00:00
  SLEEP 25.8h  2026-09-08T06:05:00+00:00 -> 2026-09-09T07:51:01+00:00
  SLEEP 32.9h  2026-09-09T11:16:43+00:00 -> 2026-09-10T20:10:00+00:00
  SLEEP 116.4h 2026-09-11T09:22:41+00:00 -> 2026-09-16T05:45:17+00:00
note: a finished pause deletes qa/.paused, so a CLOSED gap can never be proven deliberate …
EXIT: 0
```

**No `CORRUPT` row.** The claim holds: the fix is prophylactic here and was proven on synthetic
logs, which the manifest states plainly rather than implying a live catch. `ticks: 123` against the
manifest's `120` is the concurrent maker stamping three more ticks between the two runs — not a
discrepancy.

## 5. The full-suite paste is complete, and it is this code's output

I redirected my own `uv run pytest -q` to a file and compared. My capture is **24 lines and
identical to the manifest's paste** — same 18 progress lines, same two `s` skips at the same
positions (23 % and 81 %), same single `starlette` DeprecationWarning, same exit 0. There is no
`N passed` line because `pyproject.toml` sets `addopts = "-q"`, making the adapter's command
effectively `-qq`; the manifest explains this correctly rather than trimming and hoping.

The manifest's self-report — that its first attempt at this paste was itself an elision
(`tail -6` had cut every dots line) and that it re-ran with full capture — is corroborated by the
artifact: what is pasted is exactly what full capture produces. **Disclosing your own near-miss and
then fixing it is the AT-414 repair done right**, and it is worth recording that the corrected
behaviour appeared in the very next unit.

## 6. The file split is a real seam, and nothing was lost

Judged on evidence, not on the prose:

- **Nothing was lost.** `git show HEAD:tests/test_loop_status.py` lists 15 `def test_` names;
  the current file lists the same 15, `diff` identical. The only change to that file in this unit
  is **one trailing blank line** (`+1, -0`). No test was moved out of it, because the integrity
  tests were never committed into it — they were written there mid-build, hit the limit, and were
  relocated before the manifest was submitted.
- **The 339 is arithmetically real**: 242 (current) + 120 (new file) − 23 (its header, imports and
  two helpers) = **339**, exactly the number the manifest reports the doctor rejecting.
- **The seam is real, not a dodge.** All six relocated tests are about one thing — whether the log
  can be trusted (`Anomalies`, file order, future stamps, the CORRUPT rendering) — while the
  original file's fifteen are about what a trusted log records (gaps, pauses, retro-blindness,
  empty logs). That is a prior question, and the split is clean: no test straddles the line and no
  helper is duplicated across the two files. It was **triggered** by the line count, which the
  manifest says outright rather than dressing up, but the cut was made along the concept, not at
  line 300.
- **C3 is clean:** an AST scan of all six new public names against every file in `tests/`
  introduces **zero** duplicate top-level names (relevant given AT-326/AT-327's standing
  test-scope divergence).

## Criteria

| | Verdict | Evidence |
|---|---|---|
| **C2** — readable | **MET** | `doctor: clean` in my own run. `loop_status.py` 230, `test_loop_status.py` 242, `test_loop_status_integrity.py` 120 — all < 300; no function > 50; every module has a one-job docstring. The split is what makes this hold rather than a waiver. |
| **C3** — one concept, one place | **MET** | Edit in place; the one new module states its reason in the manifest and the reason is verified above. No `*_v2`/`*_new` name. AST scan: no duplicate public name introduced. `Anomalies` is defined once. |
| **C7** — verification is independent | **MET** | The unit adds 6 tests and mutation-tested them before submitting; I re-ran my own harness rather than reading theirs. Green baseline asserted per row from the **copy** (not from step 3), anchor asserted to match **exactly once**, file-changed asserted, `collected=6` on every run (nothing broke import or collection), and every kill **attributed to the named test's presence in the failure list** rather than to a non-zero exit. No unreachability claim is made anywhere in the manifest. Full suite exit 0 with real pasted output. |

## Capability coverage — 5/5 reproduced

Reproduced in a throwaway copy of the **post-change** tree at
`…/scratchpad/at399copy`, outside the bound root, with its own `uv sync` venv.
**The `.pth` trap named in the dispatch was checked first**: the copy's
`autotester.loop_status.__file__` resolves to
`…\scratchpad\at399copy\src\autotester\loop_status.py`, not `D:\autoTesting`, so every result
below is about the copy. Sandbox deleted afterwards; `git status` on `src/` and `tests/` in the
bound tree is unchanged by me.

| # | Capability | Named check GREEN in copy | After the single-hunk edit |
|---|---|---|---|
| R1 | A corrupt log is reported, not silently repaired | GREEN exit 0 | exit 1, collected 6, **failed 2**, named test in failure list ✓ |
| R2 | A future stamp cannot hide a live outage | GREEN exit 0 | exit 1, collected 6, **failed 2**, named test in failure list ✓ |
| R3 | Excluding a future stamp is *counted*, not silent | GREEN exit 0 | exit 1, collected 6, **failed 2**, named test in failure list ✓ |
| R4 | Out-of-order writes are counted | GREEN exit 0 | exit 1, collected 6, **failed 1**, named test in failure list ✓ |
| R5 | The corruption reaches the reader, not just the object | GREEN exit 0 | exit 1, collected 6, **failed 1**, named test in failure list ✓ |

Every failure count matches the manifest's cell exactly. All five edits are single-hunk,
single-file, against `src/autotester/loop_status.py`, which is named in "What changed" — admissible
under the 2026-09-16 C7 edge-case ruling. No cell contained a shell command, a multi-file edit, a
conftest/fixture edit, or an instruction to soften a check. The copy restored green after the last
mutation, which is my proof the harness was not accumulating damage.

I also hunted the two named traps and found neither: no row asserts an end state the bug also
produces (R2's assertion `asleep_now is True` is exactly the state the defect inverts, and R1
asserts `ticks[0] > ticks[1]`, which is false under the defect by construction), and no check reads
live state to judge live state — every test builds its own `tmp_path` log and passes an explicit
`now`.

## Issues addressed — checked against `qa/issues.jsonl`

- **AT-399** (medium, open) — the `loop_status.py` half is genuinely fixed and I verified it. The
  `.last-sweep`/`QUEUE.md` half is not, and is correctly out of a maker's reach. **Status
  unchanged: `open`.** This is the right call; closing it on this unit would retire a row whose
  stated remedy is half-undone.

## New finding — AT-424 (medium), filed not charged

Found while probing the boundary of the unit's own claim, and reproduced in the copy:

```
qa/.last-tick holding exactly one stamp, typed 6h ahead (the literal AT-399 scenario):
  ticks: 1   last_tick: None   anomalies.future: 1   anomalies.any: True
  rendered: ['loop-status: no ticks recorded']
```

`report_lines` returns early on `last_tick is None` (`loop_status.py:180-181`), **before** either
`CORRUPT:` row can be emitted. So when every credible stamp has been excluded, the reader is told
the log is empty — a statement that is not merely incomplete but **false**, and the corruption that
caused it is silenced at exactly the layer row R5 exists to defend. It is the same shape as
AT-366/AT-396 that the new test file itself cites, one input class further out.

**Why this is a ledger row and not a FAIL line.** It violates none of C2, C3 or C7, and no feature
contract governs `loop_status`. The five capability rows as written are each reproduced; this is a
different input class, not a row that survives. Inventing a criterion mid-verdict to fail an
artifact is the mirror of softening one to pass it, and this repo has already ruled on that shape
(amendment log 2026-09-11: AT-326 recorded rather than charged). The manifest's "What this does not
claim" section is candid about three other limits; this one it did not see, which is what a fresh
checker is for. It is a small, well-isolated follow-up unit.

## Structural note (signal, not a verdict)

`loop_status.py` has now been touched by AT-368 and AT-399 and sits at 230 lines with three
dataclasses and four functions. That is still comfortably within budget and each unit added a test,
so there is no erosion signal to report here — recorded only so the next sweep has a baseline.
