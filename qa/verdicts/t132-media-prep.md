# Verdict — t132-media-prep

**Date:** 2026-09-08
**Unit:** T-132 — Track A3: host media prep
**Manifest:** `qa/manifests/t132-media-prep.md` (commit `8dbc2d5`, manifest at `7b2f96e`)
**Contract:** `qa/contracts/video-learning.md` — **authored by this checker in this cycle**
**Cycle checked:** 1
**Bound root:** `D:/autoTesting` · adapter: `qa/adapter.json` (coding)

---

```
VERDICT: FAIL
SCOREBOARD: 3/4 criteria met, 3/4 invariants hold
FAILURES:
- [VL1d] sev: medium · the refusal names `autotester media prep`, a command the CLI does not
  expose (`autotester media` -> "No such command 'media'"); the real command is
  `autotester ingest prep`, and tests/test_media_prep.py:136 pins the wrong substring so a
  passing test protects the dead end · emit the registered command and assert against the
  actual command name, not a substring · issue: AT-163
ISSUES-WRITTEN: AT-163, AT-164, AT-165, AT-166, AT-167, AT-168, AT-169, AT-170
EXPLANATION: Everything the manifest claims about the happy path reproduces exactly — the live
corpus numbers match to the byte, the sidecar is reused with zero segment mismatches, and the
headline runt-tail finding is correct and was independently derived rather than taken on trust.
The unit fails on one criterion the maker itself asked me to author: the refusal that is supposed
to rescue an operator in a container names a command that does not exist, and its test cannot
tell the difference. Two further executed findings (AT-164 zero-chunk green success, AT-165 stale
PNG reused as evidence) are the kind this contract now names as invariants and should be fixed in
the same cycle.
```

---

## What I re-ran

Slot-1 verify, all three, on the live tree at `7b2f96e`:

| command | result |
|---|---|
| `uv run pytest` | **679 passed, 2 skipped** in 107.69s — exit 0 (matches the claim; note `-q` twice is `-qq`, so bare `uv run pytest` was used) |
| `uv run ruff check src tests scripts` | `All checks passed!` — exit 0 |
| `uv run autotester doctor` | `doctor: clean` — exit 0 |

**T-132's own `done_check`** — `uv run pytest tests/test_media.py tests/test_media_prep.py -q` → **exit 0** (21 passed).

**Baseline**: at `8dbc2d5^` the same `done_check` **exits 4, not 1** — both test files are new in this
unit, so pytest fails at collection (`ERROR: file or directory not found: tests/test_media.py`)
rather than on an assertion. Reproduced with `git archive 8dbc2d5^` into a temp tree with
`PYTHONPATH` pinned (AT-101 respected — nothing was stashed, checked out, or restored in the live
tree). The material claim holds (non-zero before, zero now); the specific number in the manifest
does not. Recorded, not charged.

## Live evidence, re-run against the real corpus

Independently, in a fresh temp project root, registering
`C:/Users/Lenovo/Videos/Screen Recordings/erp1.mp4` (sha256-addressed, `src_a6d5d1b66aa0`) and
running `media_prep.prepare(chunk_minutes=12/60, overlap_s=3.0)`. Every chunk's *actual* length was
re-measured with `ffprobe`, not taken from the plan:

```
probe -> duration 29.909333s, 1904x924, ffmpeg version 8.1.1-full_build-www.gyan.dev
  chunk_00_0s.mp4    plan_offset= 0.0  plan_len=12.00  actual_len=12.00  426674 bytes
  chunk_01_9s.mp4    plan_offset= 9.0  plan_len=12.00  actual_len=12.00  339589 bytes
  chunk_02_18s.mp4   plan_offset=18.0  plan_len=11.91  actual_len=11.91  320546 bytes
  coverage reaches 29.91s of 29.91s ; gapless=True
transcript: engine=sidecar, 6 segments, 22.0s speech
```

All three byte counts match the manifest exactly. Coverage and gaplessness confirmed from the
encoded files, not from the plan.

**Sidecar reuse, verified independently of the engine label.** I parsed
`erp1.transcript.json` myself and compared it to the persisted transcript **segment by segment** —
start, end and text, all six: **0 mismatches**, counts equal, `speech_seconds` 22.0 both sides,
first segment `{'start': 1.42, 'end': 3.42, 'text': 'Move to next stage'}` on both. `whisper_available()`
is `False` on this host, so nothing could have regenerated it — but the comparison does not depend
on that. **VL1b met.**

**Placement verified by measurement, not by reading the ffmpeg arguments.** PSNR of
`chunk_01_9s.mp4`'s first frame against the original at several timestamps:

```
t=8.0 -> 34.73   t=8.533 (keyframe) -> 37.58   t=9.0 -> 43.63   t=9.5 -> 35.45   t=10.0 -> 35.81
```

A clean peak at exactly **t=9.0**, the second the plan names. **VL1c met.**

## The headline claim — both halves checked

**(i) Is the fold genuinely unreachable at the defaults?** Derived, not accepted. The loop breaks
on the first offset whose remainder fits in one chunk; the previous iteration had
`remaining_prev > chunk_s`, so `remaining = remaining_prev - step > chunk_s - step = overlap_s`.
The remainder is therefore always in `(overlap_s, chunk_s]`, and the fold needs
`remaining < min_tail_s` — impossible when `overlap_s >= min_tail_s`. At the defaults
(overlap 15, `MIN_TAIL_S` 10) it cannot fire.

Confirmed empirically: over **200,000 random durations at the defaults, the fold was taken 0
times**; the smallest tail remainder observed over 50,000 more was **15.0028s**, just above the
15s overlap as the algebra predicts. With `overlap_s=5.0` (below `MIN_TAIL_S`) it fired 567 times
in 20,000. The maker's reachability note in `chunks.py:26-33` is correct.

**(ii) Does sabotage AB now fail 2 where it previously failed 0?** Yes, and the "previously 0" half
follows from (i) rather than from the maker's word: with the fold disabled the plan at the
defaults is **identical** (0/200,000 divergences), so *any* defaults-based fold test is provably
insensitive to that branch. The current tests, written at `overlap_s=3.0`, fail 2 when the branch
is disabled. This is the C7 rule doing exactly what it exists for, and the maker investigated an
INCONCLUSIVE rather than reading it as strength — the right call.

## Sabotage reproduction (my own harness)

`git archive HEAD` into a temp tree, `PYTHONPATH` pinned to that tree's `src` (verified: the
sabotaged copy, not the live editable install, is what imports). Each sabotage asserts
**anchor matched exactly once** and **file content changed** before its result is believed; zero
failures is reported as **INCONCLUSIVE**, never as a pass.

```
RESTORED baseline                                                        -> 0 failures (green)
AA no-ffmpeg degrade returns an EMPTY chunk list                         -> 1
AB the runt tail becomes its own chunk again                             -> 2
AC overlap dropped -- chunks abut instead of overlapping                 -> 3   (manifest said 2)
AD whisper is run even when a sidecar exists                             -> 3
AE a malformed sidecar reads as silence again                            -> 1
CX1 -ss moved BEFORE -i in encode_chunks                                 -> 0  ** INCONCLUSIVE **
CX2 -ss moved BEFORE -i in extract_frame                                 -> 0  ** INCONCLUSIVE **
CX3 ffmpeg_available returns True when only one binary exists            -> 0  ** INCONCLUSIVE **
CX4 probe raises instead of returning zeros                              -> 0  ** INCONCLUSIVE **
CX5 require_prepared raises an error naming no command                   -> 1
```

AA–AE all reproduce (AC is stronger than reported). CX1–CX4 are mine and are INCONCLUSIVE →
AT-170, and CX1/CX2's inconclusiveness has a second cause, below.

**A note on my own instrument, since it nearly produced a false report.** My first harness scored
every sabotage `0` — including controls. The cause was not isolation but my scoring regex: this
project's pytest configuration omits the final `N failed, M passed` summary line, so
`re.search(r"(\d+) failed")` never matched. I caught it because a manual re-run of AB failed 2
tests while the harness said 0 — i.e. because the controls disagreed with a hand check. Scoring is
now `FAILED ` line count plus return code. Recording it because a harness that silently scores
everything as unbroken is the same failure class C7 exists to catch, one level up.

## Attacking `plan_chunks`

Pure and load-bearing, so attacked directly (`.work/chk132/attack.py`):

| input | result |
|---|---|
| `duration == chunk_s` (180) | `[(0.0, 180.0)]` — correct, single chunk |
| `duration == chunk_s + 1` (181) | `[(0.0,180.0), (165.0,16.0)]` — covers to 181, overlap intact |
| `overlap_s = 0` | abutting chunks, full coverage — correct |
| **`overlap_s = -30`** | **`[(0,180),(210,180),(420,80)]` — [180,210) covered by nothing** → AT-167 |
| `chunk_s = 0` | `ValueError` — correct |
| `duration = -5` / `0` | `[]` — correct |
| **`duration = inf`** | **`MemoryError`** → AT-167 |
| **`duration = nan`** | **`[]` silently** → AT-167 |
| `duration = 1e9, chunk 1e6` | 1001 chunks, terminates |
| `min_tail_s` huge | folds into 2 chunks, still covers |
| 0.1-accumulation (chunk 0.3 / overlap 0.1 over 1000s) | 4999 chunks, gapless, no drift |
| **2000 random `(duration, chunk, overlap>=0)` triples** | **0 gapless failures** |

The no-gap property is genuinely solid across the reachable space; the gap is in *input
validation*, and negative overlap is not reachable from the CLI today (`--chunk-minutes` is the
only exposed knob, and a too-small chunk raises `ValueError`, which the CLI catches into a clean
exit 2). Hence AT-167 is medium, not a criterion failure.

## Attacking the degrade paths

| probe | result |
|---|---|
| ffmpeg present, **ffprobe absent** | `ffmpeg_available()` → False, degrades to one chunk on the original path, `ffmpeg_version` None. **Correct** — but untested (CX3). |
| **ffmpeg fails on chunk 2 of 3** | `CalledProcessError` escapes `prepare()`. No `media.json` written; the transcript *is* written; orphan `chunk_00_0s.mp4` left behind; the CLI catches only `(FileNotFoundError, ValueError)` so the operator gets a traceback → **AT-166**. Not a partial chunk list on disk — the *right* choice about persistence, the wrong one about the crash. |
| **0-byte video** | `MediaPrep(chunks=[], duration_s=0)` is **saved** and the CLI prints a **green** `0s, 0 chunk(s)` success line — the silent-do-nothing shape `_unchunked` exists to prevent → **AT-164**. |
| `source.path` is a directory | clean `FileNotFoundError` naming the path. **Correct.** |
| **stale 0-byte PNG at the expected name** | `extract_frames` returns it as a written frame with no ffmpeg call — 0 bytes of "evidence" → **AT-165**. |
| failed `extract_frame` (missing input) | returns False, no file left behind. Correct for *this* failure; a timeout mid-write is the case AT-165 covers. |

`extract_frames` **does** dedupe correctly — `sorted({t for screen in analysis.screens for t in
screen.screenshot_ts})` collapses a second named by two screens, and the test at
`test_media_prep.py:162` pins it. The caching short-circuit is safe with respect to *staleness
across analyses* (frames are keyed by timestamp under a content-addressed source id, so the same
name is always the same second of the same bytes); it is **not** safe with respect to partial
writes, which is AT-165.

## Rulings the manifest asked for

**(a) Whisper has never been executed — is shape-testing enough for a PASS?** Yes, this is not what
blocks the unit. The *crash-isolation plumbing* — the thing that would actually be dangerous if
wrong — **is** executed end to end on this host: `python -m autotester.media.transcribe <video>`
runs, fails at `from faster_whisper import WhisperModel`, exits non-zero, and
`transcribe_subprocess` catches it into `Transcript(engine="none")` (verified live: returned
`none, 0 segments, 0.0s`). Only whisper's *output* shape is unexercised, and it is unreachable
until the dependency exists. What is **not** acceptable is claiming it works: the contract now
carries an explicit **UNVERIFIED** section forbidding any unit, manifest, or ledger row from
describing transcription as working until one live run exists. VL1 is written so the whisper
branch is judged on its degrade behaviour, which is verified.

**(b) Should AT-130 and the `media` extra close now?** **No — AT-130 stays open, unchanged.** Its
recorded fix condition is "the A3 unit that first calls the Files API for real"; T-132 makes no
model call, so the condition has not occurred. The maker's framing ("second instance, should close
with it") is reasonable but premature. The `media` extra is filed separately as **AT-169**, and it
is worse than conceded: `transcribe.py:15-16` states faster_whisper "is declared under the optional
`media` extra", and `pyproject.toml` has **no `[project.optional-dependencies]` block at all** — the
extra does not exist, so the branch is not merely uninstalled but uninstallable by the documented
route. The two close together in the unit that first calls a model for real; the false docstring is
cheap to correct before then.

## Contract authored

`qa/contracts/video-learning.md` created this cycle (START entry in its amendment log). Two of the
four requested criteria were changed rather than adopted, on evidence:

- **VL1c** — the maker asked for "`-ss` follows `-i` so a cut lands where the plan says". I made the
  **measured placement** the criterion and demoted the argument order to an implementation note,
  because the stated rationale is false on the ffmpeg in use: a before-`-i` seek at t=20s on
  erp1.mp4 produced a **byte-identical** frame (md5 `670362ad938c57b42431d432ce4d9abb`) despite
  keyframes 4.27s apart. Writing a falsified mechanism into the contract would have made the rule
  unfalsifiable and the sabotage permanently inconclusive (AT-168).
- **VL1d** — tightened from "names the host command" to "names a command the operator can actually
  run". This is the criterion the unit fails, and it is not a criterion invented to fail it: the
  maker's own stated purpose for the message is to rescue an operator who cannot act where they
  are, which a non-existent command does not do.

Invariants I-VL1..I-VL4 and the UNVERIFIED section are checker additions.

## Manifest claims found inaccurate (recorded, not charged)

1. "it exited **1** before this unit" — it exits **4** (collection error; both test files are new).
2. "SABOTAGE AC → 2" — reproduces at **3**.
3. The `-ss` keyframe rationale, repeated from the code — falsified on ffmpeg 8.1.1 (AT-168).

## Goal task

`T-132` **remains open**. No PASS, so no close, no `docs/FEATURES.jsonl` row. (Had it passed, the
row would have been due and auto-stamped `update` — `user_value: normal`.)

## What the maker should do next

AT-163 is the only thing standing between this unit and a PASS, and it is a two-line fix (the
message and the test). AT-164 and AT-165 are the two findings I would fix in the same cycle —
both are "a wrong answer reported as a right one", which is the failure class this whole project
exists to catch. AT-166/167 are cheap hardening. AT-168/169 are corrections to prose that is
currently false. AT-170 is four small tests.
