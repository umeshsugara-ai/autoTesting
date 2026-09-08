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
- 2026-09-08 · routine · **Edge cases recorded from the cycle-3 check of `t132-media-prep`
  (PASS).** No criterion changed — these are measurements the next reader should not have to
  re-derive. (i) **I-VL4's wholeness proxy has a known hole:** a file that is exactly PNG magic
  plus the 12-byte IEND chunk (20 bytes, no image data) passes `is_complete_png`. It is not
  reachable from the failure mode the guard exists for — an interrupted write truncates the tail
  — and the guard is explicitly a wholeness proxy, not a correctness claim. Recorded, not
  tightened (AT-165 residual). (ii) **VL1d's oracle is scoped to the criterion, not to the
  project.** "No `Usage:` banner after running the whole quoted invocation" was measured to
  reject an unregistered group, an unregistered subcommand and wrong arity, and to *accept* a
  registered same-arity sibling (`ingest frames`, `ingest register`); the checker's AN4 sabotage
  confirmed this by coming back INCONCLUSIVE. VL1d is met because the *shipped message* names a
  command that was run for real; the residual is test strength (AT-174) and is deliberately not
  written into the criterion at the moment of a passing verdict. (iii) **VL1d's shape exists
  outside this criterion's scope:** the `ingest frames` refusal names `autotester ingest
  analyze`, which the CLI does not expose (AT-172, high). VL1d covers the `media.json` refusal
  only; a future amendment generalising it to every refusal that quotes a command should be
  taken on its own, away from a pending verdict. (iv) **I-VL3 boundary, measured:** the
  no-ffmpeg degrade prints a green `0s, 1 chunk(s)` and persists zeros for duration/width/height.
  This is the shape VL1 *requires*, and the bracketed `[no ffmpeg — …]` is the designated record
  of why, so it is outside I-VL3's "unqualified success claim" — filed as AT-175 (low) rather
  than scored.

- 2026-09-08 · routine · **Edge case recorded from the cycle-1 check of `at172-at173-dead-command-shape`
  (PASS).** No criterion changed. The unit generalised VL1d's shape into a class-level guard,
  `tests/test_cli_advice_resolves.py`, which resolves every backtick-quoted `autotester ...` string in
  `src/` against the live CLI. **Measured hole:** that guard cannot see advice whose command name and
  backticks live in different AST nodes -- which is exactly how `require_prepared` builds its message
  (`media_prep.py:157`, two implicitly concatenated f-strings, the name held in the `PREP_COMMAND`
  constant). Sabotaging `PREP_COMMAND` back to the dead `media prep` (anchor matched once, file
  changed, isolated worktree) yields **0 failures in the class-level guard** and exactly 1 in the full
  suite. That one is
  `tests/test_media_prep.py::test_a_stage_needing_prep_is_sent_to_a_command_that_exists`.
  **That instance test is therefore NOT made redundant by the class-level guard and may not be retired
  on that basis** -- it is currently the only thing that catches the original AT-163 regression at its
  own site. Recorded here because commit 3b765a4's argument ("stop fixing instances") would otherwise
  make deleting it look like tidying up. Residuals tracked as AT-176 (high) and AT-178 (medium);
  AT-174 stays open with a round-trip oracle design attached in the verdict. Verdict:
  `qa/verdicts/at172-at173-dead-command-shape.md`.

- 2026-09-09 · routine · **Edge cases recorded from the cycle-1 check of
  `at176-at178-render-not-scan` (PASS).** No criterion changed. AT-176, AT-178, AT-174 and AT-189
  are all closed by measurement: sabotage AY (`PREP_COMMAND` back to the dead `media prep`, anchor
  matched once, file changed, isolated worktree) now fails **3** tests in the class-level guard and
  **4** in the full suite, where at `3b765a4` it failed **0** and **1**; the collected surface is
  **9 sites / 7 distinct commands**, including `ingest prep` and the un-backticked
  `core/consent.py` advice. **VL1d now has a causal oracle** — trigger the refusal, run the command
  the *runtime message* renders, assert the refusal stops — and it discriminates the registered
  same-arity sibling that the `Usage:`-banner oracle accepts (sabotage AZ fails exactly 2, and the
  only static test among them is the collector's own). The checker verified the discrimination is
  carried by the unconditional `require_prepared` backstop and not by the sibling incidentally
  erroring: a probe sibling that exits 0 and writes no `media.json` still leaves the refusal firing.
  **Measured residuals, recorded not tightened:** (i) the collector resolves constants defined in
  the *same file* only, so the identical construction with `PREP_COMMAND` **imported** returns `[]`
  — AT-176's shape one `import` away (AT-192, medium; zero live instances); (ii) the documentation
  exclusion covers `ast.Expr(Constant)` only, so a bare **f-string or `+`-concatenated**
  documentation statement is read as advice, including this codebase's own variable-docstring
  convention (AT-193, medium; measured zero live instances under `src/autotester`); (iii) an
  unresolvable interpolation is dropped **silently** rather than surfaced, so "no advice here" and
  "advice I could not read" are indistinguishable at the API (AT-195, low); (iv) a literal lowercase
  argument is swallowed into the command by the regex (AT-194, low). None is a shipped defect — the
  criterion is met by the shipped message, which the checker ran for real — and none is written into
  VL1d at the moment of a passing verdict. Non-Python operator surfaces under `src/` were re-checked
  and are empty: no `autotester <cmd>` advice in any `.md`, `.html` or `.js`, and `ui/`'s only
  mention is a module docstring, correctly excluded. Verdict:
  `qa/verdicts/at176-at178-render-not-scan.md`.
