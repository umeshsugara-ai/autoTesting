# Verdict — at639-chunk-timeout

**Cycle checked:** 1
**Date:** 2026-09-27
**Checker:** fresh claude-sonnet-subagent (Executor of unit: claude-opus-5, maker orchestrator inline)
**Status:** IN PROGRESS — incremental log below, final VERDICT block to follow.

## Diff scope (git diff master...HEAD --stat)

```
 qa/manifests/at639-chunk-timeout.md | 114 ++++++++++++++++++++++++++++++++++++
 src/autotester/media/chunks.py      |  33 +++++++++--
 tests/test_media_shellout.py        |  44 ++++++++++++++
 3 files changed, 185 insertions(+), 6 deletions(-)
```

Only 3 files touched, all named in the manifest's "What changed". No function/class/test deleted,
no file outside the claimed set touched. Diff scope check: PASS.

## Re-read of chunks.py / media_prep.py / frames.py / transcribe.py

- `chunks.py:23-32` — new `CHUNK_TIMEOUT_S = 900.0` module constant, matches manifest.
- `chunks.py:116-133` — `subprocess.run(..., timeout=CHUNK_TIMEOUT_S)` wrapped in
  `except (OSError, subprocess.SubprocessError): path.unlink(missing_ok=True); raise`. This is the
  same catch-shape as `frames.py:49` (`FRAME_TIMEOUT_S = 60.0`) and `transcribe.py:77`
  (`WHISPER_TIMEOUT_S = 3600.0`), so the module is now consistent across its three shell-outs.
- `stages/media_prep.py:79-86` — `encode_chunks` is called inside `except Exception as exc:` which
  wraps ANY exception (including the re-raised TimeoutExpired/CalledProcessError/OSError) into
  `UnreadableRecording`, writing no `media.json` (AT-166 preserved). Confirmed: the re-raise reaches
  a broad catch, so AT-166's degrade-not-crash property holds for this new failure mode too.

**Finding filed as ISS-at639-2 (low):** `path.unlink(missing_ok=True)` at `chunks.py:132` is not
itself guarded. `missing_ok=True` only suppresses `FileNotFoundError`; on this Windows host a file
just killed by `subprocess.run(timeout=...)` can still be held by the OS/AV for a moment, so
`unlink` can raise `PermissionError` ([WinError 32]). If it does, that new exception replaces the
original (TimeoutExpired/CalledProcessError) before the `raise` statement runs — `media_prep.prepare`
still catches it (bare `except Exception`) and still degrades to `UnreadableRecording`, so C12
fail-closed and AT-166 both hold, but the persisted error message's `type(exc).__name__` would say
`PermissionError` instead of `TimeoutExpired`, obscuring the real cause. Behavior-preserving,
diagnostics-only — not a scoreboard failure.

**Finding filed as ISS-at639-1 (medium):** `CHUNK_TIMEOUT_S` bounds a single ffmpeg call, but
`stages/media_prep.prepare` loops `encode_chunks` over the whole plan with no aggregate deadline.
`DEFAULT_CHUNK_S = 180.0` and the caller's default `chunk_minutes=3.0` mean a 40-minute recording
plans ~13-14 chunks, each independently allowed up to 900s — a systemically broken ffmpeg (not just
one wedged clip) could still hang INGEST for ~3.25h before `prepare` finally raises
`UnreadableRecording`. The manifest's framing ("a wedged ffmpeg cannot hang INGEST forever") holds
for the single-instance case it targets but not for a systemic one. Not a defect in what this unit
claims to fix (the original AT-639 defect — one call, no bound at all — is genuinely fixed and
verified); filed as a follow-on gap the manifest's own disclosure stopped short of naming.

## Verify commands (re-run by checker, bound worktree)

```
$ uv run pytest tests/test_media_shellout.py tests/test_media_prep.py tests/test_media_real_ffmpeg.py
.....................                                                    [100%]
21 passed in 3.01s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ wc -l src/autotester/media/chunks.py tests/test_media_shellout.py
  136 src/autotester/media/chunks.py
  189 tests/test_media_shellout.py
```

All four match the manifest's claimed output exactly (line counts identical; pass count identical;
the wall-clock difference, 3.01s vs the manifest's 78.97s, is a warm-cache/no-contention artifact,
not a discrepancy in what ran — same 21 tests, same 3 files, same exit code).

**Full suite (`uv run pytest`, no `-q`)**: launched in background at cycle-check time (~1300-1600s
expected per dispatch). Result folded in below once complete; not blocking the capability-coverage
and diff-scope findings above.

## Capability coverage (re-run by checker in throwaway copy)

Copy: `C:\Users\Lenovo\AppData\Local\Temp\claude\d--autoTesting\aaf84a03-9a89-49ef-921f-f7d28b7dd443\scratchpad\at639-checker-copy`
(`tar --exclude .git --exclude .venv --exclude .worktrees --exclude __pycache__ --exclude
.pytest_cache`, fresh `uv sync`). Resolves own source confirmed BEFORE any edit:
`uv run python -c "import autotester.media.chunks as c; print(c.__file__)"` →
`...\scratchpad\at639-checker-copy\src\autotester\media\chunks.py`.

**Row 1 — `timeout=CHUNK_TIMEOUT_S` is asked for.**
- GREEN before (copy): `2 passed, 7 deselected in 0.32s`.
- Falsifying edit applied (single-hunk, single-file, exactly as manifest names it): removed
  ` timeout=CHUNK_TIMEOUT_S,` from the `subprocess.run` call at `chunks.py:123` in the COPY only.
- RED after (copy): `FAILED tests/test_media_shellout.py::test_the_chunk_cut_asks_for_a_timeout` —
  `AssertionError: the cut ran with timeout=None ... assert None == 900.0` — `1 failed, 1 passed`.
  The failing assertion is the kwarg check itself, not an import/collection error; the sibling test
  (`test_a_timed_out_cut_leaves_no_half_written_chunk`) still passed, confirming isolation.
- Restored (copy): `2 passed, 7 deselected in 0.11s`.
- **Verdict: reproduced, isolating.**

**Row 2 — a timed-out cut leaves no truncated chunk.**
- GREEN before: covered by Row 1's before-run (same file, same session, unedited at that point).
- Falsifying edit applied (single-hunk, single-file): deleted the `path.unlink(missing_ok=True)`
  line at `chunks.py:132` in the COPY only, leaving the bare `raise`.
- RED after (copy): `FAILED tests/test_media_shellout.py::test_a_timed_out_cut_leaves_no_half_written_chunk`
  — `AssertionError: a truncated chunk survived the timeout: ['chunk_00_0s.mp4']` — `1 failed,
  1 passed`. The `pytest.raises(TimeoutExpired)` half of the same test still held (failure is on the
  cleanup assertion alone, exactly as the manifest describes); the sibling timeout-kwarg test was
  unaffected.
- Restored (copy): full file re-run, `9 passed in 0.10s` — byte-identical to the pre-edit source.
- **Verdict: reproduced, isolating.**

**CAPABILITY-COVERAGE: 2/2 rows independently reproduced.** Neither is vacuous — each falsifying
edit reddens exactly and only the test named for it, never the sibling. The manifest's own disclosed
gap ("neither test wedges a real ffmpeg for 900s") is accepted as sufficient: proving the `timeout=`
kwarg reaches `subprocess.run` and proving cleanup fires on a simulated `TimeoutExpired` are the
right-shaped tests for this claim — `subprocess.run`'s timeout enforcement is stdlib behavior, not
this codebase's to re-verify, and an actual 900s-hang test is (as the manifest says) a test nobody
would keep running. This is not the AT-218 vacuous-guard class; it is the same test shape already
accepted for `frames.py`'s `FRAME_TIMEOUT_S` and `transcribe.py`'s `WHISPER_TIMEOUT_S`.

**Bound worktree verified untouched throughout** (all edits were made only in the throwaway copy):
`git status --short` in `D:/autoTesting/.worktrees/at639-chunk-timeout` shows no modification to
`src/autotester/media/chunks.py` or `tests/test_media_shellout.py` at any point during this check.

## Mode D (live browser)

**Not-applicable, verified against the real diff, not the manifest's assertion.** `git diff
master...HEAD --stat` (reproduced above) touches exactly `qa/manifests/at639-chunk-timeout.md`,
`src/autotester/media/chunks.py`, `tests/test_media_shellout.py`. No `*.tsx|jsx|vue|svelte|html|css`,
no `ui/`, no route, page, or component under any of these paths — `chunks.py` is a pure ffmpeg
shell-out inside the INGEST stage and its own module docstring says so. The manifest's claim
("Not UI-touching — no surface changed") holds on independent inspection of the changed paths, not
merely on the manifest's word for it.

## AT-166 / C12 chain (re-derived, not assumed)

`stages/media_prep.py:79-86` wraps `chunk_mod.encode_chunks(video, out_dir, plan)` in
`except Exception as exc:`, which is broad enough to catch `subprocess.TimeoutExpired`,
`subprocess.CalledProcessError`, and `OSError` — all three of which `chunks.py`'s new
`except (OSError, subprocess.SubprocessError)` can re-raise. Any of them still becomes
`UnreadableRecording` with no `media.json` written, exactly the AT-166 shape this unit's manifest
claims to preserve. Confirmed by code inspection (both files read in full, above), not by trusting
the manifest's prose.

## Issues filed

- **ISS-at639-1** (medium, `unbounded-aggregate-timeout`) — see above. Open.
- **ISS-at639-2** (low, `unlink-can-raise-obscuring-cause`) — see above. Open.

Neither is a scoreboard failure: neither violates a stated criterion or invariant (VL1's own scope
note excludes present-but-failing tools; C12's contract text lists three specific known instances,
none of which this unit's gap resembles), and the manifest already disclosed the class of gap
ISS-at639-1 sharpens. Both are follow-on debt for a future unit, recorded per the checker's
obligation to judge the manifest's stated gaps on their merits.
