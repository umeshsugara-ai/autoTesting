# Contract — VIDEO LEARNING: host media prep (VL1)

**Covers:** goal task T-132 (Track A3 — probe, chunk, transcript, frames) and every later unit
that consumes `media.json`, `transcript.json`, or an extracted frame.
**Owner:** /checker. **Criticality:** HIGH — this stage decides where every reported second
lands and what a tester is recorded as having said. Both are quoted to a human downstream.
**Depends on:** `core-invariants.md` (all), `ingest.md` (I8 — narration is ground truth).

## Purpose

Turn a screen recording into the three things the analysis half needs: what the recording *is*
(duration, dimensions), pieces small enough for a vision model to read, and the narration the
tester spoke. It runs on the **host** — the container has no ffmpeg, no GPU, and the corpus is
never mounted into it — so the two halves meet on disk under `projects/<slug>/sources/<id>/`
and nowhere else. That split is what makes the degrade rules below load-bearing rather than
defensive: the host this runs on is not the host the rest of the pipeline runs on, and it is
routinely missing one of the two tools.

## Criteria

### VL1 — A missing tool produces a smaller result, never an exception
With **ffmpeg or ffprobe absent**, `stages/media_prep.prepare` returns a `MediaPrep` carrying
exactly **one chunk whose path is the original recording**, with `ffmpeg_version` unset. The
single chunk is not a convenience: a caller iterating `prep.chunks` must do something useful on
a host without ffmpeg rather than silently doing nothing, and the absent `ffmpeg_version` is the
only record of *why* there is one chunk and not twelve. Absence is judged on **both** binaries,
not either — a box with ffmpeg and no ffprobe degrades at the start, not halfway through.

With **whisper absent**, the stage persists `Transcript(engine="none")`. That value means *a
recording with no narration on record*. It may never be rendered, summarised, or reasoned about
as a claim that the video is silent (AT-134), and an unreadable sidecar is a third state
(`engine="unreadable"`), never folded into either of the other two.

*Scope note (checker, 2026-09-08):* this criterion covers a **missing** tool. A tool that is
present and **fails** is not covered here and is tracked as AT-166 until a unit closes it; the
module docstrings currently assert the stronger property ("every function degrades rather than
raising") which measurement does not support.

### VL1b — A sidecar is reused verbatim and whisper is not run
When `<video>.transcript.json` exists beside the recording it is loaded as-is and
`transcribe_subprocess` is not called. Running prep twice must not change one character of what
a tester is recorded as having said. This is not an optimisation: narration is injected into the
ingest prompt as ground truth, so a regenerated line is a **changed quote from a real person**
(ingest.md I8). Judged by comparing the persisted transcript against the sidecar segment by
segment — timings and text — not by trusting an engine label.

### VL1c — The plan covers every second, and a cut lands on the second it names
For every valid input, `plan_chunks` returns a plan that starts at 0, leaves no uncovered
interval, and reaches the full duration. A gap is a stretch of product no model ever watches and
nothing downstream reports as missing.

Separately and by **measurement, not by argument order**: a chunk's first frame, and a frame
`extract_frame` pulls at `t`, must be the second the plan/model named. The `-ss`-after-`-i`
form is the current implementation of this property; it is not itself the criterion, because on
the ffmpeg in use (8.1.1) input-side seeking was measured to be accurate too (AT-168). A future
change to the argument order is judged against the measured property, not against the comment.

### VL1d — A stage that lacks `media.json` names a command the operator can actually run
`require_prepared` refuses with a message that (i) says the work must happen on the **HOST**,
because the stage that needs it runs in a container where prep is impossible and "run it here"
is advice that cannot be followed, and (ii) names the **real** CLI command, verbatim and
runnable. A message naming a command the CLI does not expose is a dead end at exactly the moment
the pipeline stopped, and a test asserting only a substring of it does not evidence this
criterion.

## Invariants

### I-VL1 — Whisper never overwrites a transcript that already exists
No path in this stage regenerates narration that is already on disk or beside the recording.

### I-VL2 — A plan never advances by more than a chunk
`plan_chunks` refuses any parameter set that would leave an uncovered second or fail to
terminate. `overlap_s >= chunk_s` is refused today; a *negative* overlap is not, and silently
produces gaps (AT-167).

### I-VL3 — The stage never asserts a fact it did not observe
Zero duration, zero chunks, `engine="none"` and `engine="unreadable"` are all *records of what
could not be determined*. None of them may be reported to an operator as a successful result
(AT-164), and none may be read downstream as a positive finding.

### I-VL4 — Anything reported as extracted evidence is a real image
A path returned by `extract_frames` is a readable image, not merely a file that happens to exist
at the expected name. A frame is quoted to a human beside an issue; an empty or truncated PNG
left by an interrupted run must not be reused as if it were the screenshot the model named
(AT-165).

## Explicitly UNVERIFIED (not a criterion, and not to be claimed as one)

**The whisper branch has never been executed.** `faster_whisper` is not installed in the project
venv and no `[project.optional-dependencies]` block exists to install it from (AT-169). What *is*
executed and verified on this host is the crash-isolation plumbing around it — running the module
as `python -m autotester.media.transcribe` fails at import, exits non-zero, and is caught into
`engine="none"` without taking the parent down. The *output* shape of a real whisper run is
untested. Until one has been executed against a real recording, no unit, manifest, or ledger row
may describe transcription as working; the sidecar path is what runs here, and every corpus
recording has a sidecar.

## Out of scope / ignore

- Model calls of any kind (A4: the vision ensemble, adjudication, issue derivation).
- Whisper accuracy, model choice, GPU/CPU selection.
- Chunk encoder settings (codec, preset, crf) — quality is not judged here.
- ffmpeg's own behaviour or version differences beyond the measured properties in VL1c.
- Cosmetic wording of log lines that are not refusals.

## Amendment log

- 2026-09-08 · START (initial creation) · Authored by /checker at the maker's request in the
  `t132-media-prep` manifest (cycle 1). Criteria are the checker's own, derived from evidence:
  VL1/VL1b are as requested; **VL1c was rewritten** to make the *measured* placement property the
  criterion rather than the `-ss`/`-i` argument order, because the maker's stated rationale for
  that order was falsified on ffmpeg 8.1.1 (a before-`-i` seek at t=20s on erp1.mp4 produced a
  byte-identical frame, md5 `670362ad938c57b42431d432ce4d9abb`, with keyframes 4.27s apart);
  **VL1d was tightened** from "names the host command" to "names a command the operator can
  actually run", because the shipped message names `autotester media prep`, which the CLI does
  not expose. Invariants I-VL1..I-VL4 and the UNVERIFIED section are checker additions.
