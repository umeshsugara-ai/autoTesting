# t132-media-prep

**Unit:** T-132 — Track A3: host media prep (probe, chunks, transcript reuse/whisper, frames)
**Commit:** 8dbc2d5
**Fix cycle:** 1
**Goal task:** T-132 (`user_value: normal`) — `done_check` =
`uv run pytest tests/test_media.py tests/test_media_prep.py -q`, **exits 0** (it exited **1**
before this unit — that check was rewritten by AT-141/AT-115 precisely so it could).
**Contract:** `qa/contracts/video-learning.md` — needs **VL1** authored (requested below).

## What shipped

New package `src/autotester/media/` — `probe.py`, `chunks.py`, `transcribe.py`, `frames.py` — plus
`stages/media_prep.py` and `autotester ingest prep|frames`. Subprocess-only ffmpeg and whisper,
running on the **host**: the container has no ffmpeg and no GPU, and the corpus is never mounted
into it. The two halves meet on disk under `projects/<slug>/sources/<id>/` and nowhere else.

## The three decisions worth defending

**VL1 — degrade, never crash.** Without ffmpeg, prep emits **one chunk pointing at the original
file**, deliberately not an empty list: a caller iterating `prep.chunks` then does the right thing
instead of silently doing nothing, and the absent `ffmpeg_version` is what records *why* there is
one chunk rather than twelve. Without whisper it emits an empty `Transcript`, which the ingest
prompt renders as *"no speech detected"* rather than as silence it has verified (AT-134).

**Sidecars are reused byte-for-byte; whisper never runs when one exists.** Not an optimisation:
narration is injected into the ingest prompt as **ground truth**, so a regenerated transcript is a
*changed quote from a real person* (I8).

**`-ss` after `-i`, in both `encode_chunks` and `extract_frame`.** It costs real time. Placed
*before* the input, ffmpeg seeks to the nearest keyframe, so a chunk can start seconds from where
the plan says — and every timestamp this pipeline reports is relative to a chunk offset, so a
keyframe-rounded cut silently moves every issue's reported second.

## Live evidence — real ffmpeg 8.1.1, real corpus, no model call

```
erp1.mp4 -> duration 29.91s, 1904x924
12s chunks / 3s overlap:
  chunk_00_0s.mp4   offset=0.0s  len=12.0s  426674 bytes
  chunk_01_9s.mp4   offset=9.0s  len=12.0s  339589 bytes
  chunk_02_18s.mp4  offset=18.0s len=11.9s  320546 bytes
  coverage reaches 29.91s of 29.91s
transcript: engine=sidecar, 6 segments, 22.0s speech
sidecar reused byte-for-byte: True
```

The corpus is at `C:/Users/Lenovo/Videos/Screen Recordings`, **not** `D:` as the plan's §4 A3
states. That correction and three others are in `.work/track-a-corpus-facts.md`.

## The finding that matters — and C7 is the only reason it surfaced

**Sabotage AB (disable the runt-tail fold) came back INCONCLUSIVE — zero failures.**

Two units ago I would have read that as *"the guard is solid."* Investigating instead showed my test
asserted on a plan **the fold never touched**:

> at the defaults the fold is **unreachable**. The loop breaks on the first remainder that fits in
> one chunk, and that remainder is always in `(overlap_s, chunk_s]` — so with overlap 15 > min tail
> 10, a runt tail cannot arise at all.

The test passed for a reason unrelated to what it claimed to check, and disabling the branch
produced a byte-identical plan. It is now tested with an overlap **below** `MIN_TAIL_S`, where the
case is real, plus a second test pinning that the **fold** produced the plan rather than the loop
merely ending. The reachability condition is documented where `MIN_TAIL_S` is defined, so the next
reader does not mistake the branch for dead code.

## Evidence

```
SABOTAGE AA (no-ffmpeg degrade returns an EMPTY chunk list)          -> 1
SABOTAGE AB (the runt tail becomes its own chunk again)              -> 2   (was INCONCLUSIVE)
SABOTAGE AC (overlap dropped -- chunks abut instead of overlapping)  -> 2
SABOTAGE AD (whisper is run even when a sidecar exists)              -> 3
SABOTAGE AE (a malformed sidecar reads as silence again)             -> 1
RESTORED: 21 passed
```

Each printed `anchor matched once, file changed` before its result was believed.

## Contract criteria requested (checker-owned — please author `video-learning.md` VL1)

- **VL1** — media prep degrades and never raises on a missing tool: no ffmpeg → one chunk on the
  original path with `ffmpeg_version` unset; no whisper → `Transcript(engine="none")`, which is a
  recording with no narration **on record** and never a claim the video is silent.
- **VL1b** — an existing `<video>.transcript.json` is loaded byte-for-byte and whisper is not run;
  running prep twice cannot change what a tester is recorded as having said.
- **VL1c** — the chunk plan covers every second with no gap, and `-ss` follows `-i` so a cut lands
  where the plan says rather than at a keyframe.
- **VL1d** — a stage that needs `media.json` and lacks it names the **host** command, because the
  stage that needs it runs in a container where prep is impossible.

## What this does NOT claim

- **Whisper has never been executed.** `faster_whisper` is not in the project venv (it is under the
  optional `media` extra), so `transcribe_subprocess` is unit-tested for its shape and **not** for
  its output. The sidecar path is what runs on this host, and every corpus recording has one.
- No model call anywhere in this unit.
- `pyproject.toml` still does not declare the `media` extra. Same judgement as `google-genai` in
  T-131, and the checker ruled that a real deviation (AT-130) to close in this track — so this is
  the second instance and it should probably close with it rather than accumulate.
- A4 (the ensemble, adjudication, issue derivation) is untouched.

## Status: ready-for-check
