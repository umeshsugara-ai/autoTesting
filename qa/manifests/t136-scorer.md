# Manifest — t136-scorer

**Unit:** the scorer for Track A's acceptance — `stages/score.py` +
`scripts/score_video_issues.py`, folding in AT-207 and AT-208
**Commit:** `e65447a`
**Fix cycle:** 2
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

## Status: superseded by cycle 2

---

# Cycle 2 — five checker findings, plus the false gate behind them

Cycle 1: **FAIL, 3/8.** Every finding held up. The checker also settled the thing I asked it to
judge hardest — *is the maker using a gate to dodge a failing acceptance?* — and upheld leaving
T-136 `pending`. What it would not accept was my evidence, and it was right not to.

## AT-219 — my headline claim was true for the wrong reason

The manifest's centrepiece was *"it exits 2 today, and that is why T-136 isn't closed."* The exit
code was real; the reason was not. `scripts/score_video_issues.py` resolved its default root as
`ProjectPaths(...).root.parent.parent` — but **`.root` IS already the repo root**, so the shipped
command read `D:\projects\erp\` and refused because it was looking outside the repo entirely. The
identical message would print against a fully populated project.

**Every CLI test passed `--root`, so the branch that actually ships was executed by nothing.** And
T-136's `done_check` passes no `--root`, which made the task **structurally incapable of closing**
even once a credential arrived. The new test drives the command **without** `--root`, under
`AUTOTESTER_ROOT`, which is how it ships.

## AT-220 — the refusal named a command that does not exist, and could not

It advised `autotester issues derive`. There was no `issues` command. Worse, **`derive_issues` had
no caller anywhere under `src/`, and neither did `analyze`** — two units built, checker-PASSed, and
impossible to run. The pipeline had a hole in the middle and the one message telling a human how to
proceed pointed into it.

Now real: **`autotester ingest analyze`** and **`autotester issues derive | list | export`**. Track A
is runnable end to end for the first time.

## AT-221 — the tie-break was not total, in the module that computes the north star

I wrote that the ordering was deterministic. `max()` returns the **first** maximum, so two equally
similar issues handed the choice to `list_issues()` file order — recall moved **0.5 vs 1.0** under
permutation. That is **AT-197's defect exactly**, one module over, in the code that produces the
number the whole project is measured by. The key now ends in the content-addressed issue id.

## AT-222 · AT-223 — two more flattering defaults

`if analysis is None: continue` made `complete: true` reachable while a contributing source had **no
analysis at all** — the same flattering default AT-208 removed, reintroduced one layer up.
`recording_key` split on the first `(` unconditionally, collapsing `clip (1).mp4` and `clip (2).mp4`
into one key, and blank cells all keyed to `""` — which matches `""`, scoring **recall 1.0** on an
empty sheet. **My first fix for that was incomplete**: giving both sides the same sentinel still let
the sentinel match itself. An unrecognisable recording now matches nothing, including another
unrecognisable one.

## AT-228 — the false gate, which is the worst of these

`ui/app.py` loaded the repo-root `.env`; **no CLI entry point did.** So `autotester providers`
answered `mock` while a working `GEMINI_API_KEY` sat on disk, and I filed
`qa/gates/t136-model-credentials.md` telling Umesh the system was waiting on **him** — for a
credential he had already supplied and then had to tell me about. Two entry points reading the same
disk disagreed about whether this machine has credentials, and each was internally consistent, which
is why it survived.

Now one loader (`core/env.py`) serves both. Measured after: `available providers: gemini,
langchain-fallback, mock`.

## The fix that opened a hole, caught by tests I did not write

Putting the load in a typer callback meant **every `CliRunner` test loaded real credentials into the
shared test process, permanently** — four provider tests asserting "no key present" began running
with a real key. `ui/app.py` had solved this deliberately with a lifespan hook *"so TestClient(app)
never leaks real .env values into the test process"*; I reopened it one door over, in a repo whose
premise is that a secret never reaches a model, a log, or an artifact. The loader now refuses inside
a test process.

## Sabotage — seven, then eight

| | Sabotage | Failures |
|---|---|---|
| EA | `--root` walks to the drive again | 1 |
| EB | tie-break drops the issue id | 1 |
| EC | coverage skips an unanalysed source | 1 |
| ED | `recording_key` splits on `(` always | 1 |
| EE | an unknown recording may match another | 4 |
| EF | the loader leaks into a test process | 1 |
| EG | the CLI stops loading `.env` | **0 — INCONCLUSIVE**, then **1** once pinned (below) |

**EG is the one worth reading.** Deleting the CLI's `load_repo_env()` call failed **nothing** —
because the leak-guard I had just added means the loader refuses inside a test process, so **no test
could ever observe whether the CLI calls it**. The protection made its own wiring invisible: AT-206's
shape (a fix whose removal nothing detects) arriving inside AT-228's fix, in the same hour. Reported
INCONCLUSIVE per C7 rather than as a vacuous guard, then closed by watching the **call** instead of
its effect — a spy in place of the loader, driven through the shipped CLI, touching no credential.

## Two guards fired on me unprompted

The advice-site inventory (built in `at206-guards-that-guard`) caught the three new commands and
**demanded a deliberate update** rather than absorbing them; and `doctor` caught `list_cmd` defined
in both `cli_video.py` and `cli_issues.py` (C3) before the commit. Both are earlier countermeasures
doing their job without being asked.

## How to verify

- `uv run pytest` → **867 passed, 2 skipped** · ruff clean · `autotester map` · doctor clean
- `uv run autotester providers` → `gemini, langchain-fallback, mock`
- `uv run autotester issues --help` → `derive`, `list`, `export` all present
- The shipped `done_check`, no `--root`: exits **2**, refusal names a command that now exists

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/core/env.py`,
`stages/score.py`, `cli.py`, `cli_video.py`, `cli_issues.py` (new), `scripts/score_video_issues.py`,
`ui/app.py` (one line: swapping its own `load_dotenv` for the shared loader — no route, template or
rendered output touched), plus tests. No route, component, page or template changed.

**Separately, and not as this unit's evidence:** a real headed crawl of live Pathlynks ran earlier
today under approval `appr_333a83b240ce` and filed AT-226/AT-227. That is recorded in
`qa/.last-tick`, not claimed here.

## What this unit still does not deliver

T-136's recall number. But the reason has changed completely: it is no longer "no credential exists"
— one does, and the CLI can now see it. It is that no recording has been registered, prepped and
analysed yet. That is a runnable sequence now, not a human gate.

## Status: checked-PASS

---

**Closed out 2026-09-09.** `qa/verdicts/t136-scorer.md`, `Cycle checked: 2` — **PASS, 8/8
criteria, 1/1 invariants.** Verdict `2c00dea`, pushed per D-007.

**The checker proved the thing I could not.** I could show the shipped command exits 2 for the
right reason; I could not show it would ever exit 0. It built a scratch root from the **real seven
Trainers-workbook rows**, turned them into real `Issue`s through the real `ProjectStore`, and ran
T-136's `done_check` string **verbatim, with no `--root`**: **exit 0, recall 1.0, 7/7.** AT-219 said
the task was *structurally incapable of closing*; that is now disproved by execution rather than by
my assurance.

It also drove the new commands end to end rather than checking they exist — `ingest register → prep
→ analyze --models mock → issues derive → list → export → score` — and confirmed `derive` is
idempotent on a second run and that `ingest analyze` genuinely reaches `analyze()`. No
exists-and-errors dead end.

**AT-221 tested at 200 shuffles**, plus the exact cycle-1 pair and an id-tie pair: identical report
every time. **AT-223 attacked with 27 cell shapes** including unicode, `name (N).ext`, mid-name
parens and tabs: no two distinct recordings collide, and an all-blank sheet now scores **0.0** where
it scored **1.0**.

**One thing it recorded as a question rather than a finding, and it is right to worry:**
`scripts/bench_trial.py`, `regression_proof.py` and `run_pathlynks_first_cases.py` still call
`load_dotenv` unguarded. No test calls their `main()` today — so the no-credentials-in-a-test-process
premise currently holds **because nobody calls them**, not by construction. That is a latent version
of exactly the leak this unit closed.

**AT-229 (medium), filed against the suite, not this unit:** `uv run pytest` writes
`projects/saucedemo/` and `qa/evidence/browser-*-checker/` into the working tree. A suite that
dirties the tree corrupts the sweep's own bypass detection — confirmed present after this run.

**T-136 stays `pending`, and the checker did not close it.** This PASS certifies the scorer unit;
T-136's acceptance still needs a real reading. The difference from cycle 1 is that this is now a
runnable sequence, not a human gate.
