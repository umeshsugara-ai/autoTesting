# Manifest — at446-folder-is-not-a-recording

**Unit:** AT-446 — `autotester ingest register` on a folder named `*.mp4`, or on an unreadable recording, gave a traceback and exit 1
**Contract:** `qa/contracts/ingest.md`, `qa/contracts/ui.md`; core-invariants C7; AT-088 (no echo)
**Goal task:** none — issue-driven (filed by the at433 checker, `qa/verdicts/at433-source-is-a-recording.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-446 (low)
**Status:** checked-PASS (qa/verdicts/at446-folder-is-not-a-recording.md, cycle 1, commit caaedd7)

## What was wrong

`register_source` checked the suffix (AT-433) and `path.exists()`. A **folder** named `dir.mp4`
passed both, and `file_sha256` then raised `PermissionError` on Windows. `cli_video.register_cmd`
caught only `FileNotFoundError` and `NotARecording`, so the result was a traceback and exit 1. The
issue's expected text also names an **unreadable file** (locked, or permission denied): that is an
`OSError` from the same call, and it was a traceback too. In the UI the path form already refused a
folder through its `OSError` branch, but it said **"Recording not found"** about a folder that
exists.

## What changed

- `src/autotester/stages/ingest.py::register_source` — after the exists check,
  `if not path.is_file(): raise NotARecording("that is a folder, not a recording file")`. This comes
  before any bytes are read. The message does not echo the name (AT-088). The file is 268 lines.
- `src/autotester/cli_video.py::register_cmd` — a further `except OSError`, placed after the existing
  `(FileNotFoundError, NotARecording)` clause, which catches `FileNotFoundError` (a subclass) first.
  It prints "that recording could not be read (<ExceptionType>) — check it is not open elsewhere and
  that you may read it" and exits 2. The file is 270 lines.
- `tests/test_source_is_a_recording.py` — 4 new tests: the stage refuses a folder without echoing
  it; the UI path form names a folder as "folder, not a recording file"; the CLI gives exit 2 for a
  folder; the CLI gives exit 2 for an unreadable file (`file_sha256` monkeypatched to raise
  `PermissionError`). The file is 208 lines.

**UI effect (why Mode D applies):** a folder submitted through the Sources path form now gets the
"Not a recording" page with a true message, instead of "Recording not found".

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_source_is_a_recording.py -o addopts= -q` | `20 passed` (before the fix, the 3 stage/CLI tests failed: `3 failed, 16 passed`, including the reported `PermissionError`; the UI test was added after and pinned by M1) |
| `uv run pytest tests/test_source_is_a_recording.py tests/test_ui_sources.py tests/test_ingest_persist.py tests/test_merge_flowspec_cli.py -o addopts= -q` | 45 passed before the UI test was added; 46 expected with it |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract. I removed `projects/erp`,
`pathlynks` and `vidysea-erp` right after extraction. The 3 unit files were copied in, with its own
`uv sync`, and `autotester.stages.ingest.__file__` and `autotester.cli_video.__file__` were
confirmed inside the extract. Each anchor matched exactly once, and each edit was restored in a
`finally`. The baseline was `20 passed`, and `20 passed` again after restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| A folder is refused as not a recording, before its bytes are read | `test_a_folder_named_like_a_recording_is_refused_as_not_a_recording` + `test_the_path_form_names_a_folder_as_not_a_recording` | `ingest.py`: delete the `if not path.is_file(): raise NotARecording(...)` lines | **2 failed, 18 passed** — `PermissionError: [Errno 13]` and `'folder, not a recording file' in '…Recording not found…'` |
| The folder refusal never echoes the name (AT-088) | `test_a_folder_…` (`"dir.mp4" not in str(info.value)`) | `ingest.py`: message → `f"{path.name}: that is a folder, …"` | **1 failed** — `AT-088: never echo the submitted name` |
| An unreadable recording is exit 2 at the CLI, not a traceback | `test_the_cli_refuses_an_unreadable_recording_with_exit_2` | `cli_video.py`: `except OSError as exc:` → `except ZeroDivisionError as exc:` | **1 failed** — exactly that test |

**Honest note:** `test_the_cli_refuses_a_folder_named_like_a_recording_with_exit_2` **survives M1**.
With the folder refusal removed, the folder's `PermissionError` is caught by the new `except OSError`
and still exits 2. The CLI's folder behaviour is therefore covered by either of two fixes, which is
defence in depth, and that test isolates neither. The folder refusal itself is isolated by rows 1-2.
On Linux a folder raises `IsADirectoryError`, also an `OSError`, so the same holds there.

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at446-2026-09-16-maker-smoke/report.json`. The server ran from the extract on a
synthetic-only root.
- Sources path form with an existing folder `dir.mp4` → HTTP 400, title "Not a recording", body
  "that is a folder, not a recording file", "Try another path". 1 console error: Chrome's
  "Failed to load resource: 400" for that deliberate refusal.
- The CLI on the same folder and root → "that is a folder, not a recording file", exit=2, no
  `sources.jsonl` created.
- Not produced on this host: a real permission-denied file. It is covered by row 3's monkeypatched
  test.

## Full suite

One clean run, output redirected in full to a fresh file (60 lines), started after sabotage and the
smoke had finished. The command was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its
final line is `1333 passed, 2 skipped, 32 xfailed, 1 warning in 335.33s (0:05:35)`, exit=0. That is
1329 + this unit's 4. All 32 XFAIL lines are `tests/test_browser_scroll_invariance.py` cases whose
reasons name AT-416 / AT-417, which are pre-existing. The 4-file source group run afterwards gives
`46 passed`.
