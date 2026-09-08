# t132-media-prep

**Unit:** T-132 — Track A3: host media prep (probe, chunks, transcript reuse/whisper, frames)
**Commit:** 8dbc2d5 (cycle 1) -> 8344137 (cycle 2) -> **f90fcb3** (cycle 3)
**Fix cycle:** 3 of max 3
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

## Cycle 2 — FAIL on VL1d, a criterion I asked the checker to author

**`require_prepared` sent the operator to `autotester media prep`. There is no `media` command.**
They live under `ingest`. It is the message meant to *rescue* someone who cannot run prep where
they are, and it sent them to a dead end — and my own test pinned the substring `"media prep"`, so
a passing test **protected** it.

The test now asks the CLI itself: it extracts the command out of the refusal and invokes it with
`--help`, so any message naming an unregistered command fails. **A substring cannot tell a real
command from a plausible one; the CLI can.**

### AT-164 — the one I would have shipped

With ffmpeg **present** and a file it cannot read, prep persisted `chunks=[]` and the CLI printed a
**green success line**. A source nothing can ever watch, reported as prepared — the exact shape
`_unchunked` exists to prevent, reached through the other branch. Now a typed refusal that writes
no `media.json`.

### The rest

- **AT-166** — a failed cut escaped as a raw traceback and could leave a partial chunk set, which is
  worse than none because it reads as a complete plan.
- **AT-165** — `extract_frames` reused any file at the expected name, including a 0-byte leftover
  from an interrupted run, handed back as evidence.
- **AT-167** — a negative overlap made the step longer than a chunk, silently skipping footage.
  Validation also moved **before** the short-circuits, where it actually fires; after them it only
  rejected inputs that were already fine.

### AT-168 — my rationale was falsified, and the claim is corrected

I asserted, in three docstrings and in this manifest, that `-ss` before `-i` seeks to the nearest
keyframe and shifts a cut by seconds. **The checker measured it on ffmpeg 8.1.1: both orders
produced a byte-identical frame at t=20s with keyframes 4.27s apart.**

The order stays — it is conservative across builds and costs nothing at this scale — but *not for
the reason I gave*. The docstrings now say so, and the contract makes **measured placement** the
criterion rather than my argument. A design defended by a mechanism that does not exist is
defended by nothing, even when the design is right.

### Cycle 2 evidence

```
SABOTAGE AF (the refusal names the dead `media prep` again)      -> 1
SABOTAGE AG (an unreadable video persists zero chunks again)     -> 1
SABOTAGE AH (a failed cut escapes as a raw traceback)            -> 1
SABOTAGE AI (a 0-byte leftover PNG counts as evidence)           -> 1   (was INCONCLUSIVE)
SABOTAGE AJ (a negative overlap is accepted again)               -> 1   (was INCONCLUSIVE)
RESTORED: 30 passed
```

**C7 earned its place twice more.** AI and AJ both came back INCONCLUSIVE, which meant I had fixed
code and written no test for either. Both are pinned now.

### Cycle 2 verification

```
uv run pytest                          688 passed, 2 skipped   (679 at cycle 1 + 9 new)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

### Corrections to cycle 1's own numbers, from the checker

- The `done_check` exited **4** at the parent commit, not 1 — both test files were new, so it was a
  collection error. My manifest said 1.
- Sabotage AC fails **3**, not the 2 I reported.

### Still open, and now better understood

**AT-169** — `pyproject.toml` has **no `[project.optional-dependencies]` block at all**, so the
`media` extra my docstring cites does not exist. Worse than I conceded. The checker ruled **AT-130
stays open** separately: its recorded trigger is "the unit that first calls the Files API for
real", and T-132 makes no model call.

Whisper still has never been executed; the checker ruled that does **not** block a PASS, because
the crash-isolation plumbing *is* exercised end to end (the module runs, the import fails, the
non-zero is caught into `engine="none"`) — only its output shape is unverified, and the contract
now carries an explicit UNVERIFIED section forbidding any claim that transcription works.

## Cycle 3 — FAIL on I-VL4, and the shape is my cycle-2 mistake one level down

**AT-166: I fixed the stage and not the path an operator runs.** `prepare()` raises a typed
`UnreadableRecording`; I never widened the CLI's `except`, which caught only
`(FileNotFoundError, ValueError)`. `UnreadableRecording` is a `RuntimeError`, so the **shipped
command answered a deliberate refusal with a raw Rich traceback**.

That is exactly what AT-163 was, one cycle earlier, **in the same file**. Last cycle the lesson was
"the message must name a command that exists"; this cycle it is "the refusal must reach the
operator at all". Both are the same root: I verified the mechanism I changed rather than the path
that ships.

**AT-165 was half-fixed the same way.** `st_size > 0` closed only the *empty* half — the checker
truncated a real **277,206-byte frame to 92,402** at the expected name and `extract_frames` returned
it as evidence with **zero** re-extract calls. The path is reachable with no guard anywhere: the 60s
timeout kills ffmpeg mid-write and the failure path returned `False` **without unlinking**, so the
cache adopted the half-file permanently. Now it unlinks, and the cache gates on a *whole* PNG —
magic plus the fixed 12-byte IEND chunk, a cheap "the encoder finished" proxy with no image library,
and explicitly **not** a claim the image is correct.

### AT-171 — three attempts at one oracle

| Attempt | Why it failed |
|---|---|
| `--help` on the captured command **group** | proved the group was registered; `ingest frobnicate` and `ingest list` both passed |
| substring checks for "No such command" / "Missing argument" | sabotaging to a **registered but wrong-arity** command came back **INCONCLUSIVE** (C7) |
| **`Usage:` banner absent** | measured, not guessed: click prints it for an unregistered command, an unregistered subcommand *and* wrong arity alike, while a correct invocation reaches the application's own message |

All three wrong-command shapes now bite.

### Cycle 3 evidence

```
SABOTAGE AK (the CLI stops catching UnreadableRecording)          -> 1
SABOTAGE AL (a killed extract leaves its half-file again)         -> 1
SABOTAGE AM (the cache gates on size again, not wholeness)        -> 1
SABOTAGE AN / registered-but-wrong command  (`ingest list`)       -> 1
SABOTAGE AN / unregistered subcommand       (`ingest frobnicate`) -> 1
SABOTAGE AN / the original dead group       (`media prep`)        -> 1
RESTORED: 15 passed
```

Each printed `anchor matched once, file changed` before its result was believed. **AN's first
run was refused by my own harness** — I passed a placeholder anchor, and the C7 assertion caught it
rather than reporting a green result.

### The split, and the done_check that would have been left behind

`tests/test_media_frames.py` split out at doctor's cap, by responsibility — and the split restates
the finding: **prep's bugs were about reporting success for work that did not happen; frames' were
about accepting a file as evidence when nobody finished writing it.** Same file, opposite failure.

**T-132's `done_check` was widened to name the new file.** A split that leaves a check naming two of
three files is the C9 defect I just spent three units on, arriving through the back door.

### A measurement error of my own

I read the `done_check` as exit **1** when it was **0** — I had chained it after `autotester doctor`
with `&&`, doctor was red on the line cap, and I reported doctor's exit as pytest's. Caught by
re-running it alone. The same "read the number you measured" rule this session keeps turning on me.

### Cycle 3 verification

```
uv run pytest                                    691 passed, 2 skipped
uv run ruff check src tests scripts              All checks passed!
uv run autotester doctor                         doctor: clean
T-132 done_check (all three files)               exit 0
```

### This is cycle 3 of a maximum of 3

If this does not pass, the unit goes to `STALLED` and stops for Umesh rather than taking a fourth
attempt. Stating it here so the bound is on disk before the verdict, not after it.

### Still open, unchanged

**AT-169** — `pyproject.toml` has no `[project.optional-dependencies]` block at all, so the `media`
extra the docstring cites does not exist. **AT-170** — no CX1–CX4 guards. **AT-130** — stays open on
its own trigger. Whisper still never executed; ruled not a PASS-blocker, with the contract carrying
an explicit UNVERIFIED section.

## Status: checked-PASS
