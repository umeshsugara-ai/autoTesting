# Manifest — at433-source-is-a-recording

**Unit:** AT-433 — a source added by path or by upload could be any file, including `.env`
**Contract:** `qa/contracts/ui.md`, `qa/contracts/ingest.md`; core-invariants C5 (credentials), C7
**Goal task:** none — issue-driven (found by the independent live-browser validation, `qa/verdicts/live-2026-09-16-ui.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-433
**Status:** checked-PASS (qa/verdicts/at433-source-is-a-recording.md, cycle 1, commit ee7d8c7)

## What was wrong

Registering a source by path only checked that the file existed. Uploading a file with an unknown
suffix quietly saved it as `recording.video`. During live validation the checker registered
`C:\Windows\win.ini` and the repo's own `.env` credential file as VIDEO sources. Each showed its
full path and an Analyze button. It also uploaded `evil.txt`, which was stored as `recording.video`.

**Gate check (before building):** I checked whether this needs a HUMAN_GATE. It does not. The
live verdict's expected behaviour is mechanical: refuse suffixes that are not recordings and never
register the credential file. No decision about which root folders are allowed is involved. A
directory allow-list *would* need Umesh's decision, and it is not part of this unit.

## What changed

- `src/autotester/stages/ingest.py` — adds `RECORDING_SUFFIXES` (`.avi .mkv .mov .mp4 .webm`),
  `NotARecording(ValueError)` and `require_recording_suffix(name)`, the only place the rule is
  defined. `register_source` calls it before checking that the file exists.
- `src/autotester/ui/routes_sources.py` — the local `_UPLOAD_SUFFIXES` is removed. `add_source`
  catches `NotARecording` and returns the themed 400 "Not a recording" page. `upload_source` checks
  the suffix **before any byte is written**, and the `.video` fallback is gone.
- `src/autotester/cli_video.py` — `ingest register` catches `NotARecording` as well and exits 2
  with a message, not a traceback.
- `tests/test_source_is_a_recording.py` (new) — 16 tests.

**Design notes.**
- `.env` is refused by the same rule, with no special case: `Path(".env").suffix == ""`.
- The refusal message never repeats the name that was submitted (AT-088).
- Suffixes are compared in lower case, so `.WEBM` and `.Mov` recordings are still accepted.
- **Every refused test file actually exists.** A missing file was already refused as "not found",
  so a nonexistent `x.ini` would pass even with the rule deleted.
- Refusals are themed HTML, not raw JSON (so AT-439 is not reproduced here).

## Honest limits (not fixed by this unit)

1. **Only the suffix is checked.** A credential file renamed `secrets.mp4` is accepted. The
   exfiltration risk was traced in code: analyze requires `media.json` preparation, and it uploads
   ffmpeg-extracted chunks, never the raw file. A text file yields 0 chunks. The source row would
   still show its path. Content sniffing (ffprobe / magic bytes) is a possible follow-up; I did not
   file it as part of this unit.
2. There is no directory allow-list. Any readable recording on the host can be registered, as before.

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_source_is_a_recording.py -o addopts= -q` | `16 passed` |
| `uv run pytest tests/test_source_is_a_recording.py tests/test_ui_sources.py tests/test_ingest_persist.py tests/test_merge_flowspec_cli.py -o addopts= -q` | 42 passed (existing source tests unaffected) |
| `uv run ruff check src tests scripts` | `All checks passed!` (maker: observed) |
| `uv run autotester doctor` | `doctor: clean` (maker: observed; ingest.py 266 lines, routes_sources.py 243) |
| `uv run pytest -o addopts= -q -rx` | full suite — see "Full suite" below |

## Capability coverage

All rows were reproduced by the maker in an isolated `git archive HEAD` extract with the 4 unit
files copied in and its own `uv sync`. `autotester.stages.ingest.__file__` was confirmed to resolve
inside the extract. Every anchor matched exactly once, and the baseline was green
(`16 passed`) before each edit and after restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| A non-recording file that exists is refused and nothing is saved | `test_a_real_non_recording_file_is_refused_and_nothing_is_saved[*]` | `ingest.py`: delete `require_recording_suffix(path.name)` in `register_source` | **9 failed, 7 passed** — all 6 parametrized refusals, canary, path-form, CLI |
| Upper-case recording suffixes are accepted | `test_a_recording_is_still_registered_whatever_the_suffix_case[demo.WEBM / demo.Mov]` | `ingest.py`: `.suffix.lower()` → `.suffix` | **2 failed** — exactly WEBM and Mov |
| `.env` / no-suffix files are refused (the credential file) | `...refused...[.env]`, `[noext]`, `test_the_path_form_refuses_the_real_credential_file` | `ingest.py`: `if suffix not in` → `if suffix and suffix not in` | **3 failed** — exactly those three |
| CLI gives exit 2, not a traceback | `test_the_cli_refuses_a_non_recording_with_exit_2_not_a_traceback` | `cli_video.py`: `except (FileNotFoundError, NotARecording)` → `except FileNotFoundError` | **1 failed** (`assert 1 == 2`) |
| The refusal never echoes the submitted name (AT-088) | `test_the_refusal_never_repeats_the_submitted_name` | `ingest.py`: message prefix → `f"{name} is not a recording …"` | **1 failed** — canary found in message |
| Upload refuses before writing and no `.video` rename happens | `test_an_upload_with_an_unknown_suffix_is_refused_and_nothing_is_written` | `routes_sources.py`: replace the try/except with `suffix = Path(...).suffix.lower() or ".video"` | **1 failed** |
| Path form shows the specific themed "Not a recording" refusal | `test_the_path_form_refuses_the_real_credential_file` | `routes_sources.py`: fold `NotARecording` into the generic `(FileNotFoundError, OSError)` "Recording not found" branch | **1 failed** |

## Maker browser SMOKE (not validation — the checker must run its own Mode D)

`qa/evidence/browser-at433-2026-09-16-maker-smoke/report.json`. The server ran from the extract, and
`AUTOTESTER_ROOT` was a fresh folder containing only the synthetic `regression-demo`.
- Path form, synthetic `.env` → 400 "Not a recording" page with "Try another path"; no source row.
- Upload form, `notes.txt` → 400 "Not a recording".
- Upload form, `walk.mp4` → exactly 1 source row (`recording.mp4`, Analyze); no `recording.video` on disk.
- 2 console errors, both Chrome's "Failed to load resource: 400" for the two deliberate refusals.

## Full suite

One clean run, output redirected in full to a fresh file (60 lines, nothing elided). The command was
`uv run pytest -p no:cacheprovider -o addopts= -q -rx`, and its final line is
`1312 passed, 2 skipped, 32 xfailed, 1 warning in 292.21s (0:04:52)`, exit=0.
All 32 xfails are `tests/test_browser_scroll_invariance.py` cases whose reasons name AT-416 / AT-417
(pre-existing and unrelated to sources). The one warning is starlette's anyio `BlockingPortal`
deprecation. Sabotage ran before this suite and was finished, so no parallel run could make it stale.
