# Verdict — at446-folder-is-not-a-recording

**Date:** 2026-09-16
**Cycle checked:** 1
**Checker:** /checker Mode A + Mode D, fresh subagent, bound to `D:\autoTesting`
**Manifest:** `qa/manifests/at446-folder-is-not-a-recording.md` (Fix cycle 1)
**Contracts:** `qa/contracts/ingest.md`, `qa/contracts/ui.md`, `qa/contracts/core-invariants.md`

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (ingest I10; ui U5 + AT-088 no-echo; core C2, C3, C4, C7), 3/3 invariants hold (C1, C5, C10-at-commit)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 3/3 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at446-folder-is-not-a-recording-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-446 open -> fixed; AT-456 (low, new, pre-existing UI message)
EXPLANATION: Every verify command re-run green in the bound tree, all three falsifying edits redden exactly the named tests for the named reason in an isolated copy, and real edge cases the manifest could not produce (junction, directory symlink, icacls-denied file, parent-is-a-file) all end in exit 2 with no traceback. The live Sources form refuses a folder and a junction with a true "that is a folder" page and registers nothing, still accepts a real .mp4, and still says "Not a recording" for a .txt. The one untrue message left is the UI saying "Recording not found" for an existing unreadable file; it predates this unit and is filed as AT-456.
```

## Step 3 — verify commands, re-run by the checker in `D:\autoTesting`

| Command | Result |
|---|---|
| `uv run pytest tests/test_source_is_a_recording.py -o addopts= -q` | `20 passed, 1 warning` |
| `uv run pytest tests/test_source_is_a_recording.py tests/test_ui_sources.py tests/test_ingest_persist.py tests/test_merge_flowspec_cli.py -o addopts= -q` | `46 passed, 1 warning` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -p no:cacheprovider -o addopts= -q -rx` (once, sequential, background, to file) | `1333 passed, 2 skipped, 32 xfailed, 1 warning in 275.41s`, exit=0; every XFAIL is `test_browser_scroll_invariance.py` naming AT-416/AT-417 |

## Step 4b — capability coverage, checker's own harness

Copy: `git archive HEAD` into `scratchpad/checker-at446/`. `projects/erp`, `projects/pathlynks` and `projects/vidysea-erp` were deleted right away, so only `regression-demo` was left. The 3 unit files were copied in and `cmp`-identical, then `uv sync` ran.
`autotester.stages.ingest.__file__` and `autotester.cli_video.__file__` both resolve under `...\scratchpad\checker-at446\src\autotester\`.
The harness `at446_mut.py` asserts a baseline `exit == 0`, that each anchor appears exactly once, and that the file changed on disk. It restores each edit in `finally` and asserts green again after restoring.

| Row | Before (copy) | Edit | After | Assertion that fired |
|---|---|---|---|---|
| Folder refused before bytes are read | 20 passed | `ingest.py`: delete the `if not path.is_file(): raise NotARecording(...)` hunk | 2 failed, 18 passed | `test_a_folder_named_like_…`: `PermissionError: [Errno 13]` from `file_sha256`; `test_the_path_form_names_a_folder_…`: `assert 'folder, not a recording file' in '…Recording not found…'` |
| Folder refusal does not echo the name (AT-088) | 20 passed | message → `f"{path.name}: that is a folder, …"` | 1 failed | `AssertionError: AT-088: never echo the submitted name` |
| Unreadable file → CLI exit 2 | 20 passed | `cli_video.py`: `except OSError as exc:` → `except ZeroDivisionError as exc:` | 1 failed | `test_the_cli_refuses_an_unreadable_recording_with_exit_2`: `assert 1 == 2` (`<Result PermissionError(13…)>.exit_code`) |

After restoring: 20 passed.

**The manifest's honest note is accurate and acceptable.** Under M1, `test_the_cli_refuses_a_folder_named_like_a_recording_with_exit_2` does survive: only 2 tests failed, and it was not one of them. The manifest names no row after that test, so no claimed capability depends on it, and rows 1-2 isolate the folder refusal through the stage and the UI. One remaining question, not a failure: no test pins the CLI's folder message text. Under M1 the CLI would still exit 2 but say "could not be read (PermissionError)" about a folder, and no test would notice.

Neither trap applies. No test asserts an end state that the bug also produces (each row's red is a distinct message or exit code), and no test reads live state.

## Probes beyond the manifest (CLI, copy, synthetic root `scratchpad/at446-root`)

| Probe | Exit | Output | Rows |
|---|---|---|---|
| folder `dir.mp4` | 2 | `that is a folder, not a recording file` | 0 |
| junction `junction.mp4` → folder (`mklink /J`, no admin) | 2 | same | 0 |
| directory symlink `symlinkdir.mp4` → folder (`os.symlink` succeeded) | 2 | same | 0 |
| parent is a file `plain.txt\x.mp4` | 2 | `no such recording: <full path>` (pre-existing FileNotFoundError branch, operator's own terminal) | 0 |
| real `icacls /deny <user>:(R)` on `denied.mp4` (deny confirmed effective, then removed with `/remove:d`; readable again) | 2 | `that recording could not be read (PermissionError) — check it is not open elsewhere and that you may read it` | 0 |
| real `real.mp4`, twice | 0, 0 | same `src_e79a26bac4ba` both times | 1 |

No probe produced a traceback. The CLI's new OSError message prints only the exception class name. It carries no path, errno text or file name, so it leaks nothing.

## Mode D — checker's own live browser

Instrument: **headed Playwright Python (chromium)**, script `scratchpad/checker-at446/at446_browser.py`. Server: `uvicorn autotester.ui.app:app` on 127.0.0.1:8048, run from the copy with `AUTOTESTER_ROOT` set to `scratchpad/at446-ui-root`. That root holds only `regression-demo/project.json` and `cases.jsonl`. Each submission went through the real `#path` field and the "Add recording" button.

| Step | HTTP | Page | Name echoed | sources.jsonl rows | Console errors |
|---|---|---|---|---|---|
| folder `dir.mp4` | 400 | "Not a recording" / "that is a folder, not a recording file" / "Try another path" | no | 0 → 0 | 1: the browser's own `Failed to load resource: 400` for this deliberate refusal |
| junction `junction.mp4` → folder | 400 | same | no | 0 → 0 | 1, same attribution |
| `notes.txt` | 400 | "Not a recording" / "add a video file ending in .avi, .mkv, .mov, .mp4, .webm" | no | 0 → 0 | 1, same attribution |
| real `clip.mp4` | 200 after 303 back to Sources | listed | yes (the registered path in the list, as expected) | 0 → 1 | 0 |
| icacls-denied `denied.mp4` (observation) | 400 | "Recording not found" | no | 1 → 1 | 1, same attribution |

After the run the Sources page showed 1 row, matching `sources.jsonl`. The ACL was restored (`acl_restored: true`), the browser was closed, and the uvicorn process on 8048 was stopped. Screenshots `01`–`06` are in the evidence directory. There are 4 console errors, one per deliberate 400, and none is unexplained.

## Ledger

- **AT-446 → fixed.** The folder case and the unreadable-file case both reach exit 2 with a message, verified on real OS objects rather than only with the monkeypatch.
- **AT-456 (low, new, pre-existing):** the UI path form says "Recording not found" for a file that exists but cannot be read. This is the UI counterpart of what this unit fixed in the CLI. The unit did not introduce it and does not claim it.

`qa/issues.jsonl` is **not committed** with this verdict. The working copy also holds uncommitted hunks from other sessions (AT-431/433/434/435/452/455), and a pathspec commit would sweep them in.
