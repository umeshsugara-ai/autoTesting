# Verdict — t132-media-prep

**Date:** 2026-09-08
**Unit:** T-132 — Track A3: host media prep
**Manifest:** `qa/manifests/t132-media-prep.md` (commit `8344137`, manifest at `37c0ab7`)
**Contract:** `qa/contracts/video-learning.md`
**Cycle checked:** 2
**Bound root:** `D:/autoTesting` · adapter: `qa/adapter.json` (coding)

*(This file replaces the cycle-1 FAIL verdict; git history preserves it —
`git show HEAD~2:qa/verdicts/t132-media-prep.md`.)*

---

```
VERDICT: FAIL
SCOREBOARD: 4/4 criteria met, 3/4 invariants hold
FAILURES:
- [I-VL4] sev: medium · a TRUNCATED-but-nonempty PNG is still returned by `extract_frames`
  as evidence and cached forever; the invariant says "an empty **or truncated** PNG left by an
  interrupted run must not be reused", and `st_size > 0` (media_prep.py:127) closes only the
  empty half. Executed: a real 277,206-byte frame truncated to 92,402 bytes at the expected
  name is returned with zero re-extract calls, and ffprobe rejects it ("chunk too big").
  `extract_frame` also still does not unlink a partial `out_png` on failure (frames.py:41-42),
  which is precisely what a `FRAME_TIMEOUT_S` kill leaves for the cache to keep · unlink the
  partial file in the failure path and gate the cache on a decodable PNG rather than on size ·
  issue: AT-165 (stays open; the manifest lists it as fixed)
ISSUES-WRITTEN: AT-171 (new); AT-163/164/167/168 -> fixed; AT-165 and AT-166 amended, kept open
EXPLANATION: Four of the six issues the manifest claims are genuinely and completely fixed, and
I reproduced each by execution — the refusal now names a command I ran myself, an unreadable
recording is a typed refusal with no media.json and no green line, negative and non-finite
inputs are rejected without changing a single legitimate plan, and the falsified `-ss` rationale
is honestly retracted in both surviving docstrings. Sabotages AF-AJ all reproduce at 1 failure
each on a green baseline, and AI/AJ were indeed 0 before because neither test existed at
`8dbc2d5`. The unit fails on one invariant and one claim: AT-165 was half-fixed (empty yes,
truncated no) and AT-166 was half-fixed (persistence yes, the CLI traceback its own fix
direction named, no), yet the manifest reports both as closed. Both halves left undone are the
same shape as the halves that were fixed: a bad artifact reported as a good one.
```

---

## What I re-ran (slot-1 verify, live tree at `37c0ab7`)

| command | result |
|---|---|
| `uv run pytest` (bare — `-q` twice is `-qq`) | **688 passed, 2 skipped**, 1 warning in 146.58s — exit 0. Scored by counting `^FAILED` lines = **0**, not by a summary regex. |
| `uv run ruff check src tests scripts` | `All checks passed!` — exit 0 |
| `uv run autotester doctor` | `doctor: clean` — exit 0 |
| T-132 `done_check` — `uv run pytest tests/test_media.py tests/test_media_prep.py -q` | **30 passed** — exit 0 |

688/2 matches the manifest exactly (679 at cycle 1 + 9 new).

## VL1d — re-probed, and the new test attacked

**The message now names a command that runs.** I extracted it from the live refusal and invoked it:
`autotester ingest prep --help` → exit 0, `Usage: root ingest prep [OPTIONS] {project} {source_id}`.
It accepts exactly the two arguments the refusal interpolates. The criterion is met on my own
execution, not on the maker's test.

**Then I attacked the test itself, and it is weaker than it looks.** The regex
`re.search(r"\`autotester ([a-z ]+?) ")` at `tests/test_media_prep.py:148` is **non-greedy** and stops
at the first space, so it captures the command **group**, never the subcommand:

```
SHIPPED         `autotester ingest prep`       -> captured 'ingest'  argv ['ingest','--help']  exit 0  PASS
BOGUS-SUBCMD    `autotester ingest frobnicate` -> captured 'ingest'                            exit 0  PASS  <-- should fail
WRONG-BUT-REAL  `autotester ingest list`       -> captured 'ingest'                            exit 0  PASS  <-- should fail
OLD-DEAD        `autotester media prep`        -> captured 'media'                             exit 2  FAIL  (correct)
```

Answering the two questions put to me: **yes** — it would pass on a message naming a real-but-wrong
command, and on a nonexistent subcommand under a real group. And **no** — `--help` alone is not a
strong enough oracle: it proves the command is registered, not that it accepts the arguments the
message implies, which I had to confirm by reading the usage line by hand. Filed as **AT-171**,
medium. This is not a VL1d failure — the criterion is about the message, and the message is right,
verified by execution — but the manifest's claim that "any message naming an unregistered command
fails" is true only of an unregistered *group*.

## AT-164 — re-probed, at the stage AND at the CLI surface

Stage: with ffmpeg present and a 0-byte mp4, `prepare()` raises
`UnreadableRecording: ... read no duration from empty.mp4`, and `store.load_media_prep()` is `None`.
**Fixed.**

CLI, which the manifest does not mention: I registered a 0-byte `.mp4` in a temp `AUTOTESTER_ROOT`
and ran the real command.

```
$ autotester ingest prep demo src_87adc773ca58
+--------------------- Traceback (most recent call last) ---------------------+
| D:\autoTesting\src\autotester\cli_video.py:77 in media_prep_cmd             |
| D:\autoTesting\src\autotester\stages\media_prep.py:75 in prepare            |
+-----------------------------------------------------------------------------+
UnreadableRecording: src_87adc773ca58: ffmpeg is installed but read no duration ...
PREP_EXIT=1
```

No green line and no `media.json`, so **I-VL3 holds** and AT-164 is closed. But `cli_video.py:79`
still catches only `(FileNotFoundError, ValueError)` and `UnreadableRecording` is a `RuntimeError`,
so the operator gets a raw Rich traceback and exit 1 instead of the clean red line + exit 2 that
every other refusal in this file produces. That is **AT-166's own fix direction** ("widen the CLI's
except clause"), which the manifest reports as fixed. AT-166 stays open, amended.
(`transcript.json` is still written before the refusal — a record, not an overstatement; noted below,
not filed.)

## AT-165 — the empty half is fixed, the truncated half is not

| probe | result |
|---|---|
| 0-byte PNG at the expected name | **rejected** — `extract_frames` returns `[]`. Fixed. |
| good cached PNG with real bytes | **reused**, `extract_frame` not called. The fix did not trade a wrong answer for a slow one. |
| **real 277,206-byte frame truncated to 92,402 bytes** | **returned as evidence**, 0 re-extract calls. `ffprobe` on it: `[png] chunk too big`. |

**Ruling on whether `st_size > 0` is a sufficient oracle: no, and it is what fails this unit.**
I-VL4 names truncation explicitly, and the path is reachable end to end with no guard anywhere on
it: `extract_frame`'s 60s timeout kills ffmpeg mid-write, `frames.py:41-42` returns `False`
**without unlinking** the partial file, and the next run's `st_size > 0` check adopts it
permanently. A half-decoded image shown to a human beside an issue is worse than an admitted gap —
which is the maker's own argument for the 0-byte case. The unlink was already named in AT-165's fix
direction and is one line.

## AT-167 — re-probed, and the validation move checked for collateral damage

```
plan_chunks(500, overlap_s=-30)     -> ValueError: overlap -30.0s cannot be negative
plan_chunks(inf)                    -> ValueError: duration must be finite
plan_chunks(nan)                    -> ValueError: duration must be finite   (was [] silently)
plan_chunks(500, chunk_s=0/-10/inf) -> ValueError: positive, finite
```

All three cycle-1 findings closed, the NaN case included (`isfinite` catches it). **No legitimate
result changed** by moving validation before the short-circuits:

```
plan_chunks(30)  -> [(0.0, 30.0)]      plan_chunks(0) -> []     plan_chunks(-5) -> []
plan_chunks(180) -> [(0.0, 180.0)]     plan_chunks(181) -> [(0.0,180.0),(165.0,16.0)]
plan_chunks(500) -> [(0,180),(165,180),(330,170)]     overlap 0 -> abutting, full coverage
5000 randomised (duration, chunk, overlap>=0) triples -> 0 gapless failures
```

Every row is identical to my cycle-1 table.

## Sabotage reproduction (my own harness, rebuilt)

`git archive HEAD` into a temp tree, `PYTHONPATH` pinned to that tree's `src` (AT-101 — nothing
stashed, checked out or restored in the live tree). Each sabotage asserts **anchor matched exactly
once + file content changed** before its result is believed; failures counted from `^FAILED` lines,
never from a summary regex; zero failures is INCONCLUSIVE, never a pass.

```
RESTORED baseline                                       -> 0 failures (rc=0)
AF the refusal names the dead `media prep` again        -> 1   (anchor once, file changed)
AG an unreadable video persists zero chunks again       -> 1
AH a failed cut escapes as a raw traceback              -> 1
AI a 0-byte leftover PNG counts as evidence             -> 1
AJ a negative overlap is accepted again                 -> 1
```

All five match the manifest. **AI and AJ were genuinely 0 before**, confirmed independently of the
maker's word: neither test exists at `8dbc2d5` (`git show 8dbc2d5:tests/test_media.py | grep -c
negative` → 0; same for `zero_byte_leftover` in `test_media_prep.py`). C7 earned its place again.
Note though that AI's sabotage inverts `st_size > 0` back to `exists()`, so it pins the empty half
only — nothing in the suite would fail if the truncated case regressed, because it never worked.

## Live corpus re-run — nothing regressed

```
duration 29.909333s, 1904x924
  chunk_00_0s.mp4   offset=0.0  len=12.00  426674 bytes
  chunk_01_9s.mp4   offset=9.0  len=12.00  339589 bytes
  chunk_02_18s.mp4  offset=18.0 len=11.91  320546 bytes
transcript: sidecar, 6 segments, 22.0s speech ; sidecar segment mismatches: 0, counts equal
```

Byte-identical to cycle 1, with the sidecar compared segment by segment rather than by engine label.
**VL1, VL1b, VL1c all still met.**

## AT-168 — the correction is honest

Both surviving `-ss` docstrings (`chunks.py:93-103`, `frames.py:28-38`) now state the original
justification was wrong, cite the byte-identical measurement on ffmpeg 8.1.1 with keyframes 4.27s
apart, and keep the argument order on conservatism across builds. That matches what I measured, and
neither overstates it. `grep -rn keyframe src/` finds no remaining assertion of the falsified
mechanism — the manifest's "three docstrings" was a miscount, only two `-ss` docstrings exist.
The manifest's cycle-1 section (lines 29-33) still asserts the keyframe claim uncorrected, but lines
132-141 retract it explicitly in the same file. Recorded, not charged.

## Issues NOT fixed this cycle — confirmed genuinely untouched

| issue | check | state |
|---|---|---|
| AT-169 | `grep -c optional-dependencies pyproject.toml` → **0**; `transcribe.py:16` still says "declared under the optional `media` extra" | open, unchanged |
| AT-170 | no test anywhere references `ffmpeg_available` or probe's zeros-not-raise; CX1–CX4 still have no guard | open, unchanged |
| AT-130 | T-132 still makes no model call; its recorded trigger has not occurred | open, unchanged |

## A last look at `prepare()` as a whole

Every remaining exit was walked. `path is None` → `ValueError`; not a file → `FileNotFoundError`;
no ffmpeg → `_unchunked` (one chunk on the original, mandated by VL1 — an unreadable file cannot be
detected without ffmpeg, so that is inherent, not a defect); empty plan → refusal; encode failure →
refusal with no `media.json`; success → saved. `chunk_minutes` is the only knob the CLI exposes, and
both bad values it can produce (`0`, and one small enough to invert the overlap) raise `ValueError`,
which the CLI catches into a clean exit 2.

The one artifact that outlives a refusal is `transcript.json`, written at `media_prep.py:50` before
probing: it records narration for a source nothing can watch. `require_prepared` blocks anything
downstream from acting on it, so I record it as a note rather than an issue.

**Open question, not a finding:** an ffmpeg that exits 0 having written a 0-byte chunk would pass
`check=True` in `encode_chunks` and be recorded in `media.json` as a real chunk — the same class as
AT-165 one layer up. I could not induce it and will not charge it.

## Goal task

`T-132` **remains open**. No PASS, so no close and no `docs/FEATURES.jsonl` row. (Had it passed, a
row would have been due and auto-stamped `update`, since `user_value: normal`.)

## What the maker should do next

Two lines close the FAIL: `out_png.unlink(missing_ok=True)` in `extract_frame`'s `except`, and a
cache gate that checks the PNG is actually decodable (an `IEND` tail is enough) — plus the test that
pins it, which the current AI sabotage does not. Then widen `cli_video.py:79` to catch
`UnreadableRecording` for AT-166's other half, and tighten the VL1d regex for AT-171. Everything
else in cycle 2 is right, and the AT-167 and AT-168 work in particular is the standard this project
should hold: a guard measured against its legitimate inputs, and a rationale retracted rather than
defended.
