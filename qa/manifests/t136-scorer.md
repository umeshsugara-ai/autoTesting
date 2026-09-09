# Manifest — t136-scorer

**Unit:** the scorer for Track A's acceptance — `stages/score.py` +
`scripts/score_video_issues.py`, folding in AT-207 and AT-208
**Commit:** `e65447a`
**Fix cycle:** 1
**Goal task:** **T-136 stays `pending`.** This unit builds T-136's machinery; it does not meet
T-136's acceptance. See "What this unit does not deliver" — that distinction is the first thing to
check, not a footnote.
**Contract:** `qa/contracts/video-learning.md` — requests criteria for the scorer (below).
**Queue:** the sweep's #2, after AT-214 (fixed separately in `1aa9b1b`).

## What this unit does NOT deliver, stated first

The task title promises *"erp1/2/3 scored vs ERP_Issues_Trainers.xlsx with recall/FP numbers in the
manifest."* **There are no numbers, and there cannot be yet.**

`uv run autotester providers` → **`available providers: mock`**. No vision credential exists on this
machine, so `projects/erp/` has no `sources.jsonl`, no `media.json`, no `analysis.json` and no
`issues.jsonl`. **No model has ever watched a recording.** Every Track A unit so far — T-130 schema,
T-131 provider, T-132 media prep, T-133 ensemble+issues — is built and PASSed against fixtures and
mocks. That is real work; it is not a measurement.

Filed as `qa/gates/t136-model-credentials.md` (HUMAN_GATE). T-136 remains `pending`.

## The exit code is the point

Run today, against the real 7-row sheet:

```
$ uv run python scripts/score_video_issues.py --project erp \
    --truth ".../ERP_Issues_Trainers.xlsx" --sheet "Trainer module"
project 'erp' has no derived issues, so there is nothing to score against 7 truth rows.
Run `autotester issues derive erp` first (which needs an analysis, which needs a vision
provider — `autotester providers`).
[exit=2]
```

A scorer that instead exited **0** printing `recall: 0.0` would be **AT-100's class — a check that
cannot fail — aimed at the north star's own metric**, and would report *"we found none of the 7"*
when the truth is *"we never looked"*. T-136's `done_check` runs this command, so it must be able
to fail. **Today it does, and that is why T-136 is not closed.**

## Both sheets, read off disk

`ERP_Issues_Trainers.xlsx` has **12** columns and names the recording `Clip`; `ERP_Issues_ALL.xlsx`
has **13** and calls it `Recording`. T-133's docstring asserted *"the scorer accommodates both"* in
the present tense about a scorer that did not exist (AT-201). It exists now, and the tests load
**both real workbooks**: 7 rows and **32** — not the plan's 33.

Four measured facts are enforced in code rather than remembered, because each silently yields a
recall of **zero**: `At` holds strings (`"00:29"`); the clip cell is
`erp1.mp4 (Divya Kamboj, trainer pipeline)`, a filename *plus prose*; ALL has 32 rows; the corpus is
on `C:`.

## Matching needs all three of recording, time and text

Text alone lets one loud finding claim every row; time alone matches whatever the model happened to
say at that second. Greedy, each truth row claimed at most once, deterministic ordering — chosen
over optimal assignment deliberately: optimal would raise recall slightly and cost every reader the
ability to check why a row was claimed.

## The two issues folded in

- **AT-207** — `observations_used` / `observations_expected` have travelled with every analysis
  since T-133 and were read by **nothing**. The report now carries them, names partial sources, and
  says whether the run was complete. A recall from 1 of 12 model calls is not a measurement of this
  pipeline and is otherwise indistinguishable from one taken from 12 of 12.
- **AT-208** — `adjudicate(expected=None)` recorded `len(shifted)`, so every caller but `analyze()`
  got an artifact declaring itself **COMPLETE**: a default-value fallback inside the very field
  added to stop one. Now `0` means unknown, and `is_complete` reads zero as not-complete. This
  scorer is the caller it was filed to protect.

## How to verify

- `uv run pytest` → **846 passed, 2 skipped**
- `uv run ruff check src tests scripts` → clean · `uv run autotester map` · `uv run autotester
  doctor` → clean (one `&&` chain)
- `uv run python scripts/score_video_issues.py --project erp --truth
  ".../ERP_Issues_Trainers.xlsx" --sheet "Trainer module"` → **exit 2**, refusal text above

## Sabotage — ten, all discriminating, zero INCONCLUSIVE

Each anchor asserted to match exactly once, each file re-read as changed, restored by file copy
(never `git checkout` — AT-101).

| | Sabotage | Failures |
|---|---|---|
| SA | `at_seconds` returns 0 instead of refusing | 1 |
| SB | `recording_key` keeps the whole cell | 5 |
| SC | `RECORDING_COLUMNS` forgets `Clip` | 8 |
| SD | matching ignores which recording | 1 |
| SE | matching ignores the time window | 2 |
| SF | matching ignores the similarity threshold | 2 |
| SG | one issue may claim many truth rows | 3 |
| SH | CLI exits 0 with nothing to score | 1 |
| SI | coverage always claims complete | 1 |
| SJ | `adjudicate(expected=None)` flatters itself again | 1 |

## Two of my own mistakes, both caught by running

1. `test_a_sheet_with_no_recording_column_is_refused_by_name` passed a `.py` file to `load_truth`
   and asserted **my** error — openpyxl raised its own first, so the test proved nothing about this
   code. Replaced with a real workbook built in `tmp_path`.
2. The CLI fixture made issues **byte-identical** to the truth rows, so tightening `--window` or
   `--threshold` changed nothing and the C9 test failed against a perfect fixture rather than
   against the code. A model never reproduces a human's wording exactly; the fixture is now offset
   in time and reworded, which is both realistic and what makes the bounds observable.

## Contract criteria requested (checker to author)

- The command exits non-zero when it cannot score, and names the command that would fix it.
- Both ground-truth sheet shapes load; the recording column is found under either name.
- `At` is parsed as MM:SS; an unparseable cell is refused, never scored as second zero.
- A match requires the same recording AND a time within the window AND similarity ≥ threshold.
- Each truth row is claimed at most once; unmatched reports are counted as false positives.
- Both declared bounds (`--window`, `--threshold`) change the result or are rejected (C9).
- The report states analysis coverage and names partial sources.

## Status: ready-for-check
