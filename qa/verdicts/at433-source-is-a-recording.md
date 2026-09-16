# Verdict — at433-source-is-a-recording

**Date:** 2026-09-16
**Checker:** /checker Mode A + Mode D (fresh subagent), bound to `D:\autoTesting`
**Manifest:** `qa/manifests/at433-source-is-a-recording.md` (Fix cycle 1)
**Cycle checked: 1**
**Contracts:** `qa/contracts/ui.md`, `qa/contracts/ingest.md`, `qa/contracts/core-invariants.md` (C5, C7)

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 4/4 invariants hold
FAILURES: none
CAPABILITY-COVERAGE: 7/7 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at433-source-is-a-recording-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-446 (low, new, pre-existing); AT-433 open -> fixed
EXPLANATION: In my own browser against an isolated synthetic root, the path form refused a synthetic .env, C:\Windows\win.ini, a .ini, a directory and a directory named dir.mp4 (all 400, themed, no row, no canary echoed); the upload form refused evil.txt and .env; SHOT.MOV (path) and PHONE.MOV / upload-walk.mp4 (upload) registered with Analyze buttons, stored as recording.mov / recording.mp4, zero recording.video on disk. All 7 falsifying edits reddened exactly the named checks for the right assertion in a throwaway post-change copy (green before, green after restore, byte-identical restore). The suffix-only limit is honestly disclosed in the manifest (a renamed secrets.mp4 is accepted) — not a failure of this unit's stated scope, but a question for Umesh whether content sniffing should be queued.
```

## What was criterion-judged

| # | Criterion (from AT-433 expected + manifest claims) | Evidence (checker-produced) |
|---|---|---|
| 1 | An existing non-recording file is refused, nothing saved | browser: .env / win.ini / owl .ini / plaindir -> 400 "Not a recording", table stayed empty; tests 16 passed |
| 2 | Upper-case recording suffixes accepted | browser: SHOT.MOV by path, PHONE.MOV upload -> 303, rows with Analyze |
| 3 | `.env` / no-suffix refused (credential file) | browser path + upload `.env` -> 400; CLI `.env`, no-suffix -> exit 2 |
| 4 | CLI refusal exits 2, not a traceback | CLI .env / notes.txt / noext / plaindir / win.ini / missing .mp4 all exit=2 |
| 5 | Refusal never echoes submitted name (AT-088) | browser `owl-pathname-canary-5521.ini`: '5521' absent from HTML; CLI noext canary absent |
| 6 | Upload refused before write, no `.video` fallback | browser evil.txt/.env -> 400; `find root -name recording.video` = 0; no stray temp files |
| 7 | Path form shows specific themed "Not a recording" page | browser title "Not a recording — AutoTester", "Try another path" link works (clicked) |

Invariants: C5 (synthetic canary `ck433-zebra-canary-77` never rendered on any page) · C7 (maker sabotage anchors re-verified with anchor-count==1 assertion) · UI themed HTML refusals (no raw JSON from this unit's branches) · ingest I10 / existing flow (mp4 upload -> row -> Analyze clicked -> pre-existing "Prepare this recording first" gate, unchanged).

## Step 3 — verify commands re-run (bound tree)

- `uv run pytest tests/test_source_is_a_recording.py -o addopts= -q` -> `16 passed, 1 warning`
- `uv run pytest tests/test_source_is_a_recording.py tests/test_ui_sources.py tests/test_ingest_persist.py tests/test_merge_flowspec_cli.py -o addopts= -q` -> `42 passed, 1 warning`
- `uv run ruff check src tests scripts` -> `All checks passed!`
- `uv run autotester doctor` -> `doctor: clean` (ingest.py 266, routes_sources.py 243, cli_video.py 265, test file 161 lines)
- Full suite, once, sequentially, in the throwaway copy (not the shared tree), output to file:
  `1 failed, 1311 passed, 2 skipped, 32 xfailed, 1 warning in 272.43s`. The single failure is
  `tests/test_ui_sources.py::test_uploaded_recordings_are_gitignored`, which shells `git check-ignore`
  and got `fatal: not a git repository` because the copy has no `.git` — environmental. Re-run in the
  bound tree: `tests/test_ui_sources.py` -> `9 passed`. Effective result matches the manifest (1312 passed).

## Step 4b — capability coverage (throwaway copy)

Copy: `git archive HEAD` into `<scratchpad>/checker-at433/copy` + the 4 unit files (cmp-identical),
own `uv sync`, `autotester.stages.ingest.__file__` resolved inside the copy; real-project folders
(erp, pathlynks, vidysea-erp) deleted from the copy. Each edit asserted anchor count == 1, restored
byte-for-byte (cmp-identical to the bound tree afterwards).

| Row | Before | Edited | Assertion that fired | Restored |
|---|---|---|---|---|
| delete `require_recording_suffix(path.name)` | 6 passed | 6 failed | `DID NOT RAISE NotARecording` | 6 passed |
| `.suffix.lower()` -> `.suffix` | 5 passed | 2 failed (WEBM, Mov) | `NotARecording` raised on upper-case | 5 passed |
| `if suffix not in` -> `if suffix and suffix not in` | 3 passed | 3 failed ([.env], [noext], path-form credential) | `DID NOT RAISE` / `assert 200 == 400` | 3 passed |
| CLI catches only `FileNotFoundError` | 1 passed | 1 failed | `assert 1 == 2` exit code | 1 passed |
| message prefixed with `{name}` | 1 passed | 1 failed | canary found in message | 1 passed |
| upload try/except -> `... or ".video"` | 1 passed | 1 failed | `assert 200 == 400` | 1 passed |
| fold `NotARecording` into generic not-found branch | 1 passed | 1 failed | `'not a recording' in` page titled "Recording not found" | 1 passed |

## Mode D summary

Server `uvicorn autotester.ui.app:app` port 8043, `AUTOTESTER_ROOT` = scratchpad root containing only a
copy of `projects/regression-demo` and a synthetic `.env`. Stopped afterwards (listen count 0).
Console: 9 errors total, all Chromium "Failed to load resource: 400" for the 9 deliberate 400s
(6 path refusals, 2 upload refusals, 1 Analyze "Prepare first"); 0 JS errors, 0 warnings.

Observations (not failures):
- A path whose filename contains a loaded `.env` value is stopped earlier by the pre-existing
  `_refuse_unsafe_submission` guard as raw JSON (AT-439 shape, already tracked) — not this unit's branch.
- The upload refusal reuses the "Try another path" link text — cosmetic.
- Directory named `dir.mp4`: UI refuses ("Recording not found"), but the CLI exits 1 with a
  `PermissionError` traceback. Pre-existing at HEAD -> filed **AT-446** (low), not charged to this unit.
- Question for Umesh: content sniffing (ffprobe/magic bytes) for a renamed `secrets.mp4` is disclosed
  as out of scope and was not filed; decide whether to queue it.
