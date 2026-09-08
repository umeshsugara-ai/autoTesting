# Verdict — t132-media-prep

**Unit:** T-132 — Track A3: host media prep (probe, chunks, transcript reuse/whisper, frames)
**Contract:** `qa/contracts/video-learning.md` (VL1, VL1b, VL1c, VL1d · I-VL1..I-VL4)
**Commit checked:** `f90fcb3`
**Cycle checked: 3**
**Date:** 2026-09-08
**Verdict: PASS**

Docker is down; `uv` runs natively. ffmpeg 8.1.1 present, `faster_whisper` absent, real corpus at
`C:/Users/Lenovo/Videos/Screen Recordings`. No `git stash`/`checkout`/`restore` in the live tree
(AT-101) — every sabotage ran in a detached `git worktree` at `f90fcb3` with `PYTHONPATH` pinned
to it, and the whole live-tree state was left untouched apart from the checker-owned files this
verdict commits.

## 1. Verification, re-run by the checker

| Command | Result |
|---|---|
| `uv run pytest` (bare, `FAILED` lines counted) | **691 passed, 2 skipped**, 0 FAILED lines, exit 0 |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| T-132 `done_check` (all three files) | 33 collected, **exit 0** |

`.goal/goal.json` T-132 `done_check.cmd` reads
`uv run pytest tests/test_media.py tests/test_media_prep.py tests/test_media_frames.py -q`
with `expect_exit: 0` — all three files, matching the split.

## 2. I-VL4 re-probed (the cycle-2 FAIL)

Re-ran the exact cycle-2 attack and extended it.

```
1 cold extract                  -> 00005000.png, 1 extract call, 276,937 bytes
2 whole PNG at expected name    -> returned, 0 extract calls          (reuse intact)
3 truncated to 92,402 bytes     -> 1 extract call, final 276,937 B, is_complete_png=True
4 killed extract (timeout 0.05) -> returned False, file does NOT exist
5 ffmpeg absent (OSError)       -> returned False, file does NOT exist
```

`is_complete_png` attacked with eight shapes:

| Input | Result |
|---|---|
| real 277 KB frame truncated to 92 KB | False ✔ |
| valid PNG with trailing garbage appended | False ✔ |
| PNG magic present, IEND relocated, tail cut | False ✔ |
| wrong magic + correct 12-byte IEND tail | False ✔ |
| 0-byte file | False ✔ |
| **a directory at that path** | False ✔ (the `stat`/`open` OSError is caught) |
| whole real PNG | True ✔ |
| **exactly magic + IEND, 20 bytes, no image data** | **True** — see below |

The last one is the only hole, and it is filed as a residual note on AT-165 rather than charged:
a killed write truncates the *tail*, so nothing in the failure mode this guard exists for can
produce a file that ends in a valid IEND. The docstring already disclaims correctness and claims
only wholeness; that claim survives the attack. **I-VL4 holds.**

## 3. AT-166 re-probed through the shipped command, and the sibling command checked

```
$ autotester ingest prep probe src_25e8afc6f93e     # a registered non-video file
src_25e8afc6f93e: ffmpeg is installed but read no duration from garbage.mp4 — the file is
empty or not a video this ffmpeg understands
exit 2 · no traceback · source dir contains transcript.json only (no media.json)
```

Clean typed refusal on the path an operator runs. **AT-166 closed.**

The other shipped command does **not** have the same untreated-exception shape — `ingest frames`
handles its own missing-analysis case and exits 2 — but it does carry the *other* cycle-2 defect:
its refusal names **`autotester ingest analyze`**, and `autotester ingest --help` lists exactly
`register / list / prep / frames / run`. `autotester ingest analyze --help` → `No such command
'analyze'`, exit 2. That is AT-163's dead end one command over. It is **not** charged against
VL1d, which is scoped to the `media.json` refusal and is met by the shipped artifact — filed as
**AT-172 (high)**. The four other command strings quoted in `src/` (`autotester approve`,
`flowspec approve`, `map`, `snapshot`) were all executed and all exist; this is isolated.

`ingest frames` against a recording that had been moved away also printed a **green**
`0 frame(s) written` and exited 0 — the AT-164 family reached through `frames`. Zero frames is
not among I-VL3's enumerated values and `extract_frames` is contractually allowed to degrade to
fewer pictures, so this is **AT-173 (medium)**, not a criterion failure.

## 4. AT-171 — is the new oracle sufficient? **Better, not sufficient.**

Measured, for the two-argument invocation the message interpolates:

| Named command | `Usage:` banner | Oracle verdict |
|---|---|---|
| `ingest prep probe src_missing` (shipped) | absent | passes ✔ correct |
| `ingest list probe src_missing` (wrong arity) | present | fails ✔ |
| `ingest frobnicate probe src_missing` | present | fails ✔ |
| `media prep probe src_missing` (dead group) | present | fails ✔ |
| **`ingest frames probe src_missing`** | **absent** | **passes ✘** |
| **`ingest register probe src_missing`** | **absent** | **passes ✘** |

The checker ran its own sabotage **AN4** (`PREP_COMMAND` → `autotester ingest frames`) under the
same anchor-matched-once + file-changed harness: **INCONCLUSIVE, 0 failures, 33 passed.** So the
oracle now rejects unregistered groups, unregistered subcommands and wrong arity — the three
shapes the maker enumerated — and accepts any registered same-arity sibling regardless of what it
does. The *criterion* VL1d is nonetheless met: the shipped message names
`autotester ingest prep <slug> <source_id>`, which the checker ran for real. The gap is in the
test, not the artifact → **AT-174 (medium)**, not a FAIL.

## 5. Sabotages reproduced (checker's own harness, isolated worktree)

Each printed `anchor matched once, file changed` before its result was believed.

```
AK  CLI stops catching UnreadableRecording      -> 1  test_the_shipped_prep_command_answers_a_refusal_cleanly
AL  killed extract leaves its half-file again   -> 1  test_a_killed_extract_leaves_no_half_file_behind
AM  cache gates on size again, not wholeness    -> 1  test_a_truncated_png_is_not_returned_as_evidence
AN1 registered-but-wrong-arity (ingest list)    -> 1  test_a_stage_needing_prep_is_sent_to_a_command_that_exists
AN2 unregistered subcommand (ingest frobnicate) -> 1  (same test)
AN3 the original dead group (media prep)        -> 1  (same test)
AN4 registered SAME-ARITY sibling (ingest frames, CHECKER'S OWN) -> 0  INCONCLUSIVE -> AT-174
RESTORED: 33 passed
```

All six maker-claimed sabotages reproduce at exactly the claimed count.

## 6. The split lost nothing

Collected node ids across the whole `tests/` tree, `f90fcb3^` (worktree) vs `f90fcb3`:
**690 → 693.** Full diff: four tests moved `test_media_prep.py → test_media_frames.py` under
byte-identical names, plus three genuinely new ones
(`test_a_killed_extract_leaves_no_half_file_behind`,
`test_a_truncated_png_is_not_returned_as_evidence`,
`test_the_shipped_prep_command_answers_a_refusal_cleanly`). File-agnostic name diff shows
**zero deletions**. The widened `done_check` names all three files and collects all 33 — the
maker's own stated concern (a check naming two of three files) is closed, verified against the
node list rather than against the file names.

## 7. The maker's self-reported measurement error

Accurately described. `doctor` is clean now and the `done_check` genuinely exits **0** when run
alone (re-run above). A `doctor && pytest` chain with a red doctor short-circuits and reports
doctor's status, which is exactly the failure described — coherent, and the correction is on
disk in the manifest rather than only in the maker's head. Recorded, not charged.

## 8. Adversarial pass on `prepare()`

| Path | Behaviour, measured |
|---|---|
| ffmpeg + ffprobe absent | one chunk on the original path, `ffmpeg_version` unset — the VL1 shape exactly. `ffmpeg_available()` confirmed False first. |
| ffmpeg present, file unreadable | `UnreadableRecording`, exit 2, **no `media.json`** |
| encode fails mid-cut | wrapped into `UnreadableRecording`, no `media.json` (sabotage AH, cycle 2) |
| sidecar present | reused, `engine=sidecar`, 6 segments, **0 whisper calls** (I-VL1) |
| negative overlap / non-finite duration | `ValueError` refused before the short-circuits (I-VL2) |
| frame placement | `extract_frame(erp1.mp4, 20.0)` → md5 `670362ad938c57b42431d432ce4d9abb`, **byte-identical** to both reference orders and to cycle 2's recorded value (VL1c) |
| chunk coverage | durations 1 / 29.91 / 181 / 600 / 3600 s: starts at 0, no gap, reaches full duration (VL1c) |
| `prepare()`'s only callers | `cli_video.py` alone; `require_prepared` has no caller yet |

One remaining honesty gap, **not** a criterion failure: the no-ffmpeg branch prints a green
`0s, 1 chunk(s)` and persists `duration_s 0.0 / width 0 / height 0 / length_s 0.0` as if measured.
The bracketed `[no ffmpeg — one chunk on the original file]` is the contract's own designated
record of *why*, which is what keeps this outside I-VL3's "reported as a successful result", but a
downstream reader of `media.json` cannot tell "not measured" from "measured as zero" →
**AT-175 (low)**. `transcript.json` is also persisted before the recording is proven readable, so
an unreadable source leaves a transcript and no media prep — recorded in AT-175's context, harmless
because nothing references it.

No path was found where `prepare()` reports success for a recording that cannot be watched.

## Issues

**Closed by this unit (open → fixed, verified 2026-09-08):** AT-165, AT-166, AT-171 — each
re-derived by execution, not by reading the diff.

**Filed:** AT-172 (high), AT-173 (medium), AT-174 (medium), AT-175 (low).

**Still open, unchanged and correctly declared in the manifest:** AT-169 (no
`[project.optional-dependencies]` block), AT-170 (no CX1–CX4 guards), AT-130 (waits on its own
trigger — the first real Files API call, which this unit does not make).

**Whisper has still never been executed.** The contract's UNVERIFIED section stands and no claim
in this unit contradicts it.

---

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 4/4 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-172, AT-173, AT-174, AT-175 (new) · AT-165, AT-166, AT-171 (open -> fixed/verified)
EXPLANATION: The cycle-2 FAIL on I-VL4 is closed by execution, not by inspection — a truncated
277KB frame is now rejected and re-extracted, a whole PNG is still reused with zero extract
calls, a killed extract leaves nothing behind, and is_complete_png survived eight attack shapes
including a directory at the path. AT-166's CLI half is closed on the shipped command (exit 2,
no traceback, no media.json), all six maker sabotages reproduce at exactly the claimed counts,
and the node-id diff proves the test split moved four tests and lost none while the widened
done_check covers all three files and exits 0. Four new findings were filed rather than charged:
AT-172 (the sibling `ingest frames` refusal names a nonexistent `ingest analyze`) and AT-174
(the VL1d oracle still accepts a registered same-arity sibling — the checker's own AN4 sabotage
came back INCONCLUSIVE) are both real and both outside the criteria as authored.
```
