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

**Finding candidate (not yet filed):** `path.unlink(missing_ok=True)` at `chunks.py:132` is not
itself guarded. `missing_ok=True` only suppresses `FileNotFoundError`; on this Windows host a file
just killed by `subprocess.run(timeout=...)` can still be held by the OS/AV for a moment, so
`unlink` can raise `PermissionError` ([WinError 32]). If it does, that new exception replaces the
original (TimeoutExpired/CalledProcessError) before the `raise` statement runs — `media_prep.prepare`
still catches it (bare `except Exception`) and still degrades to `UnreadableRecording`, so C12
fail-closed and AT-166 both hold, but the persisted error message's `type(exc).__name__` would say
`PermissionError` instead of `TimeoutExpired`, obscuring the real cause. Sev: low (behavior-preserving,
diagnostics-only). Will decide ISS filing after capability-coverage rows.

## Verify commands (re-run by checker)

(to be filled)

## Capability coverage (re-run by checker in throwaway copy)

Copy: `C:\Users\Lenovo\AppData\Local\Temp\claude\d--autoTesting\aaf84a03-9a89-49ef-921f-f7d28b7dd443\scratchpad\at639-checker-copy`
(tar --exclude .git/.venv/.worktrees/__pycache__/.pytest_cache, fresh `uv sync`).
Resolves own source confirmed: `.../at639-checker-copy/src/autotester/media/chunks.py`.

(to be filled)

## Mode D (live browser)

(to be filled)
