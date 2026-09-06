# Manifest — at053-navigate-settle
**Contract:** qa/contracts/execute.md
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-06
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-053

## What changed
- `src/autotester/stages/execute.py:53` — `run_case`'s post-step settle branch now fires on
  `Action.CLICK` **or** `Action.NAVIGATE` (was CLICK-only). A fresh navigation can leave the
  target page still rendering when the evidence screenshot is taken, exactly the same
  async-transition problem AT-045 already fixed for CLICK.
- `tests/test_execute.py` — renamed
  `test_click_settles_before_the_screenshot_but_other_actions_do_not` to
  `test_click_and_navigate_settle_before_the_screenshot_but_other_actions_do_not` and updated its
  assertion to expect two `networkidle` settles (NAVIGATE then CLICK, since neither step declares
  an `expected`); updated `test_click_settles_against_the_steps_own_declared_expected_text`'s
  assertion to expect one `networkidle` settle from the NAVIGATE step (unaffected, no declared
  expected) with the CLICK step still skipping it via its own declared expected text (AT-046,
  unchanged).

## How it was found
A live, honest reliability demo the user asked for directly: a brand-new AutoTester project
(`vidysea-erp`, never onboarded before) was pointed at `https://www.vidysea.com/erp` with one
real, credential-free case (NAVIGATE to the base URL expecting "Sign in to continue" visible,
then CLICK the real "View your training here" link expecting "My Training"). The first real run
(`run-01M1TQ822WNVW8ST89W5P5GPET`) came back FAIL: the grader correctly failed criterion c1
because `01-step01-navigate.png` was a genuinely blank white frame (visually confirmed by
directly reading the PNG) — the NAVIGATE screenshot was taken before the real external page had
rendered. `02-step02-click.png` showed the click step reaching the real "My Training" page
correctly, proving the underlying browser automation and site interaction were sound; only the
NAVIGATE evidence-capture path was missing the settle() call CLICK already had (`execute.py`
before this fix: `if step.action is Action.CLICK: session.settle(step.expected)`).

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → expected: exit 0, all tests pass
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: exit 0
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Real end-to-end: `docker compose restart autotester` (source is volume-mounted, uvicorn has no
  `--reload`, a restart is required to load the fix) then
  `curl -X POST http://localhost:8010/projects/vidysea-erp/run` three times in a row → expected:
  real PASS every time (not the pre-fix FAIL on a blank NAVIGATE screenshot)

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q
........................................................s............... [ 26%]
........................................................................ [ 52%]
........................................................................ [ 78%]
...........................................................              [100%]
(all pass, 1 skip, no failures)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end, after `docker compose restart autotester` (confirmed container `StartedAt`
moved past the code edit before rerunning — the first post-edit rerun, before restarting, still
showed the pre-fix behavior's stale process and was discarded, not counted as evidence):

```
run-01M1TQRN6B7F0K56F450N06WTP: PASS — "Sign-in and credential-free training lookup pages were successfully reached."
run-01M1TQS00136W01XDSR7XS6WM3: PASS — "The user reached both the sign-in page and the training lookup page."
run-01M1TQS8Y14MYMDSQGC7SMKT9N: PASS — "Evidence confirms successful navigation to both the sign-in screen and the training lookup page."
```

Three consecutive genuine PASSes against the live, external, brand-new production URL
`https://www.vidysea.com/erp`, with real Gemini multimodal grading citing real screenshot
content (per AT-049's earlier fix — the judge genuinely sees pixels, not just filenames).

## Status: checked-PASS
