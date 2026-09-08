# t133-ensemble-and-issues

**Unit:** T-133 — Track A4: two-model ensemble + deterministic adjudication + Issue derivation + the 13-column Excel
**Commits:** `adjudicate` → `issues` → `analyze_video` (see `git log`, three commits)
**Fix cycle:** 1
**Goal task:** T-133 (`user_value: high`) — `done_check` =
`uv run pytest tests/test_adjudicate.py tests/test_analyze_video.py tests/test_issues.py -q`,
**exits 0** (it exited non-zero before this unit; none of the three files existed).
**Contract:** `qa/contracts/video-learning.md` — needs **VL2–VL6 authored** (requested below).

## What shipped

| Module | Job |
|---|---|
| `stages/adjudicate.py` | pure, deterministic merge of every model's chunked observations |
| `stages/issues.py` | adjudicated findings → the 13-column sheet a tester already uses |
| `stages/analyze_video.py` | the ensemble driver, and the only stage that spends money |
| `prompts/video_issues_v1.md` | the bug sweep, deliberately separate from the mapping prompt |

## The three decisions worth defending

**A cached observation is never re-requested.** A second `analyze` over the same recording makes
**zero** provider calls, which is what makes it safe to re-run after a crash, after a code change,
or just to look again. The cache is keyed per model, so widening the ensemble costs only the
widening — otherwise nobody would ever add the second model, and agreement between independent
readings is the strongest signal this pipeline produces without a human.

**Failure is partial, never total.** One dead provider must not lose the answers that arrived. But
*total* failure refuses rather than persisting an empty analysis, because an empty analysis on disk
reads as *"we watched it and found nothing"* — the opposite of what happened.

**The sheet's shape is theirs, not ours.** 13 columns in their order, `At` as `MM:SS`, severity as
High/Medium/Low. T-136 compares AutoTester's output to a human's sheet, and that comparison is only
fair if the shapes match.

## Three bugs I wrote and caught before shipping

1. **The severity comparison was inverted.** I used `max()` to keep the worse of two severities —
   but `Severity` is declared S1, S2, S3 in **descending** severity, so `max()` picks the *mildest*,
   and it reads as if it were right. It would have quietly downgraded every issue the two models
   disagreed about, and **disagreement is exactly when severity matters most.** Now a named
   `worst()`.
2. **`said_verbatim` does not exist on an observation** — it is `narration`. Found by running, not
   by reading.
3. **My determinism test compared whole JSON**, including `Artifact.created_at` — a wall-clock
   stamp. That conflated *"adjudication is deterministic"* with *"the clock did not tick"*, and my
   adjudicate-twice test had been **passing only because both calls landed in the same
   microsecond.**

## The header is checked against the real workbook

`test_the_header_matches_the_real_human_sheet` loads `ERP_Issues_ALL.xlsx` from the corpus and
compares cell by cell. It passes. **A hand-copied header is a claim about a file; this reads the
file.** It skips cleanly where the corpus is absent, with an offline shape test beside it.

Two corpus facts are now enforced in code rather than remembered — the `At` column holds **strings**
like `01:33` (a scorer comparing a float matches nothing, silently), and severity is written in
their words. Both come from `.work/track-a-corpus-facts.md`, where four measured facts contradicted
the plan.

## Evidence — 15 sabotages across the three modules

```
adjudicate   BA severity back to max()          -> 2     BB stop sorting the input        -> 1
             BC merge screens on name alone     -> 1     BD shift mutates the cache       -> 2
             BE agreement stops raising confidence -> 1

issues       BF rename a column                 -> 2     BG At written as a number        -> 1*
             BH our severity vocabulary         -> 1     BI how-we-know from the claim    -> 2
             BJ drop the tester's words         -> 1

analyze      BK ignore the cache                -> 2     BL a failed provider aborts all  -> 2
             BM total failure writes an analysis-> 1     BN stop slicing narration        -> 2
             BO drop the chunk offsets          -> 1
```

**\* BG is the finding.** It first came back **INCONCLUSIVE** — writing `At` as a raw number, exactly
what the plan's comparison assumed, failed nothing, because my parametrized test exercises `at_mmss`
**directly and never the row**. *The helper being right does not make the sheet right.* Now asserted
on the written workbook, which is what a tester opens.

## Doctor caught a design violation before the commit

`build_prompt` was defined here **and** in `ledger/relitigation.py` — C3, one concept one place.
Renamed to `build_chunk_prompt`, matching `stages/ingest.py`'s `build_ingest_prompt`.

Worth stating plainly: **two commits earlier that violation would have been pushed.** I had been
running the verify with `;` between steps, so a red doctor did not stop the commit that followed it.
It is one `&&` chain now, and this is the first thing it caught.

## Contract criteria requested (checker-owned — please author `video-learning.md` VL2–VL6)

- **VL2** — a cached observation is never re-requested; a second `analyze` makes zero provider
  calls; `--force` is the only override; the cache is keyed per model so widening costs only the
  widening.
- **VL3** — failure is partial: one dead provider or chunk never loses the rest, but total failure
  refuses rather than persisting an empty analysis.
- **VL4** — adjudication is pure and order-independent: the same observations in any order give
  identical **content** (provenance stamps excepted, and stated).
- **VL5** — chunk offsets are applied in code, never by the model; narration is sliced to the chunk.
- **VL6** — the exported sheet matches the human sheet's columns, order, time format and severity
  vocabulary, verified against the real workbook where it is available.

## What this does NOT claim

- **No model has ever run this.** Every test uses a spy provider; the Gemini path is exercised for
  shape only. The first real ensemble run is T-136's job, and it will cost money.
- **The scorer is not built.** `scripts/score_video_issues.py` and the recall numbers belong to
  T-136; this unit produces the sheet that gets scored, not the score. Naming it so the boundary is
  on record rather than implied.
- `ERP_Issues_ALL.xlsx` has **32** rows, not the plan's 33 — a recall denominator, measured, and it
  belongs in T-136's manifest before any score is computed against it.
- **AT-192, AT-193** (holes I introduced in the advice collector) remain queued, as does **AT-196**
  (the flaky live test).

## Status: ready-for-check
