# Manifest — at215-vl1c-measured-placement

**Unit:** AT-215 — VL1c's measured-placement half had no test, third consecutive sweep unchanged
**Commit:** `ba4c5b6`
**Fix cycle:** 1 of 3
**Dual check:** no
**Contract:** `qa/contracts/video-learning.md` VL1c (HIGH-criticality)
**Goal task:** none — issue-driven
**Issues addressed:** AT-215 (medium)

## What was wrong

> No test anywhere runs a real ffmpeg and measures that a chunk's first frame, or
> `extract_frame(t)`'s output, IS the second named — the argv assertions would pass unchanged
> against an ffmpeg whose seek landed elsewhere.

`tests/test_media_shellout.py` monkeypatches `subprocess.run` and asserts only that `-ss` appears
after `-i` in the argv, plus the literal argument value. VL1c's own text explicitly disclaims that
as the criterion: *"The `-ss`-after-`-i` form is the current implementation of this property; it
is not itself the criterion... A future change to the argument order is judged against the
measured property, not against the comment."* Three sweeps named the same gap without it moving.

## What changed

- `tests/test_media_real_ffmpeg.py` (new) — builds a real 3-second, 1fps synthetic video (ffmpeg's
  own `color` lavfi source + concat demuxer, no hand-rolled container logic), each second a
  maximally distinguishable pure colour. Calls the **real** `encode_chunks` and `extract_frame`
  (no monkeypatching anywhere) and measures each output frame's actual pixel content via a
  **third, independent** ffmpeg call (`-f rawvideo -pix_fmt rgb24`) — never PIL, never the code
  under test grading itself.
- Two tests: chunk-cutting placement (`encode_chunks`) and single-frame placement
  (`extract_frame`), both against the same fixture video.
- Whole file skipped via the project's own `ffmpeg_available()` when ffmpeg/ffprobe aren't on
  PATH — consistent with VL1's stated no-ffmpeg-no-GPU promise for the rest of the suite.

## How to verify (commands + expected)

- `uv run pytest tests/test_media_real_ffmpeg.py -v` → expected: exit 0, 2 passed
- `uv run pytest` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 0

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_media_real_ffmpeg.py -v
tests\test_media_real_ffmpeg.py::test_a_chunks_first_frame_is_the_second_the_plan_named PASSED
tests\test_media_real_ffmpeg.py::test_extract_frame_lands_on_the_second_it_was_asked_for PASSED
2 passed in 2.56s

$ uv run pytest
926 passed, 2 skipped, 1 warning in 83.77s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7) — targeting the seek OFFSET, not the argv shape, since that is
exactly the distinction VL1c draws:**

Isolated `git archive HEAD` extract with its own `uv sync` venv (my own uncommitted test layered
onto the extract by hand, since it postdates HEAD — `frames.__file__` verified inside the extract,
not the live tree). Shifted `extract_frame`'s seek target by `+1.0` second — a placement bug that
would be invisible to any argv-shape assertion, since `-ss` still comes after `-i` with a
syntactically valid float. Result: **exactly 1 failure**,
`test_extract_frame_lands_on_the_second_it_was_asked_for`:

```
AssertionError: second 0: channel 0 expected 255, measured 0
(full expected=(255, 0, 0), measured=(0, 254, 0))
```

Asked for second 0 (red), measured second 1's colour (green) — the exact off-by-one a real bug
would produce, caught by content, not by argument order. `test_a_chunks_first_frame_...` stayed
green under this mutation (it only calls `extract_frame` indirectly through `encode_chunks`,
unaffected by the sabotaged single-frame path), confirming the two tests are independent and
neither floors the other.

Restored by overwriting with the saved copy (never `git checkout`, AT-101). Live tree confirmed
untouched (`grep -c '"-ss", f"{t_s}"' src/autotester/media/frames.py` → 1, unchanged).

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `tests/test_media_real_ffmpeg.py` only
(new file). No production code touched; this unit is test-only, per the sweep's own two offered
remedies ("either build the test or downgrade the claim") — this builds the test.

## What this unit does not claim

- Does not touch `tests/test_media_shellout.py`'s existing argv assertions — those remain correct
  and useful (they pin the *current* implementation choice), just not sufficient alone, which this
  unit now supplements rather than replaces.
- Does not claim every VL1/VL1b/VL1d behaviour is now measured — only VL1c's specific
  measured-placement property, the one three consecutive sweeps named.
- Does not attempt AT-156 (a separate stalled finding from the same sweep) — its remedy touches
  `D:/ai_os/.claude/skills/goal/scripts/criticality.py`, outside this project's bound root, and is
  therefore not buildable from here.

## Status: checked-PASS (cycle 1, verdict 9034c1f)
