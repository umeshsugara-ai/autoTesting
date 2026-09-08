# t133-ensemble-and-issues

**Unit:** T-133 — Track A4: two-model ensemble + deterministic adjudication + Issue derivation + the 13-column Excel
**Commits:** `adjudicate` → `issues` → `analyze_video` (see `git log`, three commits)
**Fix cycle:** 2
**Goal task:** T-133 (`user_value: high`) — `done_check` =
`uv run pytest` over the five test files of this unit (widened in cycle 2 after two of
them were split at the 300-line cap),
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

## Status: superseded by cycle 2

---

# Cycle 2 — what the FAIL found and what changed

The cycle-1 verdict was **FAIL, 3/6 criteria**, and it was right on every count. Nine issues,
four of them high. All nine are fixed; nothing was argued down.

## The one that matters most, because my own test said the opposite

**AT-197 — the determinism claim was false in the shape that actually ships.** `adjudicate`'s
sort key was `(offset_s, provider_label, chunk_index)`. `PROMPT_NAMES` has **two** entries, so
one model's two prompts on one chunk **tie** — and a tie in a sort key is the caller's order
walking straight back in through Python's stable sort. Permuting two such observations produced
two different analyses: different screens, journey, issues, summary.

My determinism test shuffled eight times and passed, because every fixture in the file was built
by `obs()`, which **hardcoded one prompt name**. A single-prompt fixture has no tie in it. I
tested the property on the one shape where it could not fail, in the file whose docstring calls
determinism "the load-bearing property here."

This is the recurring class the sweep keeps measuring, and this is its sharpest form yet: not an
untested path, but a **test that looked exactly like coverage of the thing it could not see.**
`obs()` now takes a `prompt`, and the new test permutes the two-prompt pair. It fails with the old
key (exactly one failure) and passes with the new one — verified by reverting the key.

## The other three high ones

- **AT-198** — an analysis built from 1 of 24 calls carried the same screens, the same issues and
  no coverage field at all. `VideoAnalysis` now carries `observations_used` /
  `observations_expected`. **Two numbers rather than a boolean**, because "we watched it and found
  nothing" and "23 calls failed" are the same artifact otherwise, and a reader who cannot separate
  them will trust the second one. My zero-case guard stopped one step short of its own principle.
- **AT-199 / AT-200** — the cache inverted the promise it exists for. A truncated observation file
  (*the crash the cache is for*) raised out of `analyze`, and `--force` **could not clear it**
  because the read happened before the force test. Force is now checked first, unreadable files
  are skipped and re-requested, and the key is the prompt's **sha256, not its name** — editing a
  prompt file leaves the name alone, so the cache was returning the answer to the question you had
  just stopped asking. That one is invisible in the artifact, which is how a cache gets switched
  off entirely by someone who stops trusting it.

## The five smaller ones, none waved off

**AT-201** the module docstring asserted "the scorer accommodates both" about a scorer that does
not exist (T-136) — a present-tense claim about future work, in the file a reader opens to learn
what the sheet is. **AT-202** `_merge_lists` dropped `fields`; the existing test was *named*
`test_a_field_only_one_model_noticed_survives_the_merge` and asserted only on `signals`. It is now
renamed for what it does and asserts on each list — the same failure shape as AT-197, one file
over. **AT-203** the prompt never mentioned `confidence`. **AT-204** two providers sharing a label
collapse the ensemble to one silently — refused. **AT-205** `at_mmss(-115)` rendered `-1:55`,
which reads as a time to the one person least able to tell it is a doubled offset.

## Verification

- `uv run pytest` → **804 passed, 2 skipped** · ruff clean · `autotester map` · doctor clean, as
  one `&&` chain.
- `done_check` widened to the five test files and passing (59 tests).
- **Three targeted sabotages, each anchor-matched-once and file-verified-changed:** the old sort
  key → only the two-prompt test fails; `prompt_sha256` dropped from the cache comparison → only
  the edited-prompt test fails; `skip_unreadable` reverted → only the truncated-file test fails.
  One failure each, no INCONCLUSIVE.

## The split, and why it is along these lines

Two test files crossed the 300-line cap. They were split by **responsibility, not by size**:
cost (`test_analyze_cache.py` — every assertion counts provider calls) from behaviour
(`test_analyze_video.py`), and determinism (`test_adjudicate_determinism.py`) from the merge
rules. Shared fakes live once in `tests/video_fakes.py`; duplicating them would let the two files
drift and quietly test different things.

## What this unit still does not claim

No model has run this pipeline. The scorer does not exist. The recall denominator is **32**, not
the plan's 33 — `.work/track-a-corpus-facts.md` holds that and three other measured facts that
would each silently produce a recall of zero.

## Status: checked-PASS
