# Manifest — at366-images-seen-count

**Unit:** AT-366 — a screenshot the judge never saw is dropped in silence
**Contract:** `qa/contracts/grade.md` (G1, G3), core-invariants C2/C7
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-366 (high, `silent-failure`)

## What was wrong

All three providers filter a non-existent screenshot path out of the judge's input **in silence** —
`gemini.py:106-107`, `anthropic.py:72`, `langchain_fallback.py:86-88` (the last falling all the way
back to the text-only prompt AT-049 was filed against). Upstream, `stages/grade.py` built those
paths as `run_dir / ev.path` for every SCREENSHOT evidence row, so a screenshot the executor
recorded but failed to write (the AT-036 retry class) or a `run_dir`/path mismatch produced a
shorter list with **no error, no log line, and no count anywhere on the `Verdict`**.

The consequence is the AT-049 class one layer down: a PASS rendered on one of two screenshots — or
on none of them — is indistinguishable from one rendered on all of them.

## What changed

- `src/autotester/schema/verdict.py` — `Verdict` gains `images_requested` and `images_seen`
  (both default `0`, so every persisted verdict and every existing caller is unaffected), plus a
  `graded_on_partial_evidence` property. The property's docstring is deliberate about what it does
  and does not mean: `True` does not say the verdict is wrong, it says nobody can tell.
- `src/autotester/stages/grade.py::grade` — the existence filter now happens **here, once**, and
  the two counts are computed from it and threaded onto the `Verdict`. The judge still receives
  only files that exist (sending a missing path would just move the failure into the provider);
  what changed is that the loss is now recorded instead of vanishing.
- `src/autotester/stages/grade.py::_shortfall` / `::_joined` (new) — one sentence naming what the
  judge did not see, prepended to **both** `note` and `scoreboard`.
- `src/autotester/stages/grade.py::_withheld` (new) — the AT-070 credential-guard block extracted
  verbatim out of `grade()`. Pure refactor, forced by the doctor's 50-line function rule once the
  counts were added; no behaviour change.
- `tests/test_grade_evidence.py` (new file) — the AT-049 pair plus six new AT-366 tests. The split
  is the doctor's `file-too-long` rule (`test_grade.py` hit 320 > 300) resolved **by
  responsibility**, as the rule asks: this file is "does the judge actually see the evidence it
  grades on", which is one question, not a slice of the stage's general behaviour.
- `tests/test_grade.py` — those tests removed from it; nothing else touched.

### One correction made mid-build, worth stating

My first version put the shortfall **only** on `note`, with a docstring claiming "the report reads
`note`". I checked before writing the manifest: `report_export.py` renders `scoreboard` (in the
summary table and in `_case_section`) and renders `note` **nowhere at all**. A note-only fix would
have been a structured field nothing displays — the same silence one layer up, which is the exact
defect this unit is about. The sentence now goes on the scoreboard (what a human sees) as well as
the note (the durable record), and `test_the_shortfall_reaches_the_field_the_report_actually_renders`
pins that distinction.

## What this unit does not claim

- **It does not change any verdict's `result`.** A PASS graded on 0 of 3 screenshots is still a
  PASS; it now says so on its face. Downgrading incomplete-evidence grades to INCONCLUSIVE is a
  real question, but it is a **contract-level change to G3** and belongs to the checker and the
  human, not to a maker fixing a silent-failure issue. AT-366's own `expected` offers "raised **or**
  recorded as a count the grader and the report can read" — this is the second option, taken
  deliberately because the first would crash runs on the AT-036 retry class that motivated the issue.
- **It does not touch the three providers.** Their independent `path.exists()` filters remain, now
  as harmless no-ops on a list already filtered upstream. Removing them is defence-in-depth churn
  with no test that can distinguish it.
- It does not surface the counts in the HTML report as their own column — the sentence rides in the
  scoreboard the report already renders.
- It does not detect a screenshot that exists but is empty, truncated, or of the wrong page.

## Capability coverage

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, single file) | Observed |
|---|---|---|---|
| A screenshot the run recorded but never wrote is counted, not dropped | `tests/test_grade_evidence.py::test_a_screenshot_the_run_recorded_but_never_wrote_is_counted_not_dropped` | `grade.py`: `seen = [path for path in requested if path.exists()]` → `seen = list(requested)` | GREEN before (`7 passed`); after: **FAILED** that test + 2 others, on the `images_seen == 1` assertion |
| The shortfall is stated in words, not only as a pair of integers | `::test_the_shortfall_reaches_the_field_the_report_actually_renders` | `grade.py`: `if images_seen >= images_requested:` → `if True:` in `_shortfall` | GREEN before; after: **FAILED** exactly 2 tests (strictly fewer than mutation A), on the missing `"graded on 1 of 2 screenshots"` |
| The shortfall reaches the field the report renders, not just the one it ignores | same test, scoreboard assertion | `grade.py`: `scoreboard=_joined(shortfall, judgment.scoreboard) or ""` → `scoreboard=judgment.scoreboard` | GREEN before; after: **FAILED exactly 1 test**, `assert "graded on 1 of 2 screenshots" in verdict.scoreboard`, with the failure output showing `note` still carrying the sentence — the precise discriminator |

Each mutation is a single hunk in a single file named in "What changed", each reddens on the
assertion the check is named for, and none breaks import or collection (the 7-test file collected
and ran every time). The three are strictly nested — A ⊃ B ⊃ C — which is what shows the three
claims are separately covered rather than one claim asserted three times.

## How to verify (commands + expected)

- `uv run pytest tests/test_grade_evidence.py -q` → expected: exit 0, 7 passed
- `uv run pytest tests/test_grade.py tests/test_grade_evidence.py tests/test_report_export.py -q`
  → expected: exit 0, 30 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean` (it was RED mid-build on both the
  300-line file rule and the 50-line function rule; both are resolved, not suppressed)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_grade.py tests/test_grade_evidence.py tests/test_report_export.py -q
..............................                                           [100%]   (30 passed)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest -q
[... all dots ...]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:53
  DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use
  anyio.from_thread.BlockingPortal instead.
EXIT: 0
```

Two honest notes on that last one. My capture tailed only the final lines, so the
`N passed` count is not in the paste — the exit code is, and the checker re-runs it anyway;
I am not going to quote a count I did not see. And an EARLIER full-suite run in this session
also exited 0 but ran against the intermediate (note-only) version of the fix; it is not cited
here, because a green suite against code that no longer exists is not evidence about this code.
AT-357's known `tests/test_mutation_check.py` flake did not fire in this run.

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. `git archive HEAD | tar -x` into a scratchpad extract; layered this unit's four files on.
2. `uv sync`; `autotester.__file__` confirmed resolving **inside the extract**, not the live tree.
3. Baseline in the extract: `uv run pytest tests/test_grade_evidence.py -q` → **7 passed**.
4. Mutations A, B and C applied one at a time, each from the pristine backup, each reverted before
   the next — results in the Capability coverage table above.
5. Extract deleted; live tree confirmed to carry only this unit's four paths.

**This confirmation was run twice.** The first run was against a version that put the shortfall on
`note` only; when I found `report_export.py` does not render `note`, the code changed, so the whole
extract was rebuilt and all mutations re-run against the final version. The first run's results are
not cited above — a sabotage run against code that no longer exists proves nothing.

## Data-boundary gate (MC-003)

`python D:/ai_os/.claude/skills/_shared_validation/data_boundary.py .` exits **1**, on
`adapter.json has no "data_class"`. That is **AT-365**, an open issue this unit does not touch and
did not introduce — it is currently at `HUMAN_GATE` (`qa/gates/at365-data-class-declaration.md`,
commit 34682eb) because declaring `"synthetic"` makes the gate fire on ~30 benign hits: attribution
addresses, RFC 2606 `.test` fixture domains, and the repo's own `pyproject.toml` author, all under
gitignored `.work/`. This unit's changed paths hold no data of any kind.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `src/autotester/schema/verdict.py`,
`src/autotester/stages/grade.py`, `tests/test_grade.py`, `tests/test_grade_evidence.py`.

Judged on the indirect rule too, honestly: the new sentence **does** change a string that
`report_export.py` renders, so a reader could call this UI-adjacent. But it changes it only in the
partial-evidence case, which requires a real run with a genuinely missing screenshot file — there is
no route, template or component change here, and `tests/test_report_export.py` (re-run, green)
covers the rendering path. Flagging it so the checker can overrule me rather than discover it.

## Corrections charged by the checker (2026-09-16, verdict f3f4f08)

The rows above are left byte-intact — they are what was submitted — and corrected here.

- **AT-378 (low), row A's `Observed` cell names the wrong assertion.** I wrote that
  `seen = list(requested)` reddens on `images_seen == 1`. It does not: under that mutation the
  named test fails earlier, at the `judge_images` assertion, and never reaches the count. The
  capability is still covered — the checker ran the discriminating mutation itself
  (`grade.py` `len(seen)` → `len(requested)`, which reddens `assert 2 == 1` exactly) and confirmed
  it. **Coverage intact, attribution wrong**, which is the same failure class C7's kill-attribution
  clause names one level down: "the suite went red" is not an observation, and neither is the wrong
  red. AT-378 stays open — only a checker flips it.
- **Uncharged but wrong: "the AT-049 pair plus six new AT-366 tests"** (line 38). There are
  **five**.

Also recorded from the verdict, as facts this manifest asserted without evidencing: legacy
`.verdict.json` payloads without the new keys still validate, with the honest consequence that a
pre-AT-366 verdict reports `graded_on_partial_evidence == False` even when it was partial — the
data was never captured. And `graded_on_partial_evidence` currently has **no consumer in `src/`**;
AT-377 (medium, open) carries both that and the PASS-downgrade question.

## Status: checked-PASS (cycle 1, 5/5 criteria, 9/9 invariants, verdict `qa/verdicts/at366-images-seen-count.md`, commit f3f4f08; ledger AT-366 open → fixed; AT-377 + AT-378 filed)
