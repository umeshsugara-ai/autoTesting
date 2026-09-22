# Verdict — t162-drive-2b (Mode A, PRIMARY of dual check)

**Date:** 2026-09-23
**Cycle checked:** 1
**Checker:** claude-sonnet-subagent (fresh context, read-only toward the artifact)
**Bound root:** `D:/autoTesting/.worktrees/t162-drive-2b`
**Unit commit:** `2485ca2` (base for diff scope: `20baf0e`)
**Contracts read in full:** `qa/contracts/source-adapters.md` (ACTIVE, D-035), `qa/contracts/core-invariants.md`, `qa/contracts/ingest.md`

## What I re-ran myself

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters_drive.py` → `6 passed in 0.62s`. Matches manifest.
2. `PYTHONUTF8=1 uv run ruff check src tests scripts` → `All checks passed!`. Matches manifest.
3. `PYTHONUTF8=1 uv run autotester doctor` → `doctor: clean`. Matches manifest.
4. `PYTHONUTF8=1 uv run pytest` (bare, no CLI `-q`, AT-503) → `1568 passed, 5 skipped, 32 xfailed, 1 warning in 642.72s (0:10:42)`, exit code 0. Matches manifest's `1568 passed, 5 skipped, 32 xfailed` (my run: 642.72s vs manifest's 650.94s — both real, machine-timing variance only). Whole-log scan for `FAILED|ERROR|^E ` → 0 matches.

## Diff scope (step 4c)

`git diff 20baf0e 2485ca2 --stat` / `--name-only` touches exactly: `docs/MAP.md` (generated), `qa/manifests/t162-drive-2b.md`, `src/autotester/schema/enums.py`, `src/autotester/sources/__init__.py`, `src/autotester/sources/adapters.py`, `src/autotester/sources/drive.py` (new), `src/autotester/sources/drive_register.py` (new), `src/autotester/stages/ingest.py`, `tests/test_source_adapters_drive.py` (new) — an exact match for the manifest's "What changed". No file outside this list was touched. `schema/base.py` (`Provenance`), `schema/project.py` (`Source`, including its pre-existing `url` field), and `store/project_store.py` are **byte-identical / not in the diff at all** — independently confirmed, not merely trusted: SA4 invents no new parent/child schema field, and SA1's "no second store" holds. No existing function, class, test, or config key was deleted or renamed. `enums.py`'s only other change is the `IssueCategory` docstring reworded (not a behavior deletion, confirmed by reading both versions). `register_document`/`register_audio` (adapters.py) and `register_source` (ingest.py) each gained only optional `url: str | None = None` (and `register_source` also `provenance`), all defaulting to the pre-existing behavior — confirmed by reading the full diff, not merely the manifest's claim. `pyproject.toml` and `uv.lock` show **no diff at all** between `20baf0e` and `2485ca2` — no new dependency, confirming the no-`google-api-python-client`/`google-auth` design rule. File sizes: `drive.py` 204, `drive_register.py` 197/198, `test_source_adapters_drive.py` 188/189, `enums.py` 300 — all within C2's 300-line ceiling.

## Capability coverage (step 4b) — reproduced in throwaway copies outside the bound tree

Five isolated copies (`src/`, `tests/`, `scripts/`, `pyproject.toml`, `uv.lock`, `.venv` junctioned to the bound tree's own venv) were made at a scratch location outside `D:/autoTesting`. Green-before confirmed in **every** copy before any edit (`1 passed` each, for the row's own test). Each row's single-hunk falsifying edit was applied to ONE file named in the manifest's "What changed", the named test re-run, then judged — the bound working tree was never touched.

| Row | Falsifying edit applied | Result | Reddened for the claimed reason? |
|---|---|---|---|
| SA1 | `drive_register._dispatch_by_suffix`: `register_document(..., url=drive_file.id, ...)` → `url=None` | RED: `AssertionError: assert None == 'doc-1'` | Yes — exact match |
| SA2 | `adapters.register_document`'s dedupe guard: `if existing is not None:` → `if False and existing is not None:` | RED: `AssertionError: assert True is False` (`child_results[1].created is False`) | Yes — exact match. **Note:** my first attempt mistakenly mutated `register_audio`'s guard (wrong function) and got a false green; caught it, corrected to `register_document` (the function the two `.md` files in this test actually route through), and it reddened exactly as the manifest describes. Recorded as a self-correction, not a manifest defect. |
| SA5 | `drive_register._register_unfetchable`: `notes=f"{_EXTRACTION_ERROR_PREFIX}: ..."` → `notes=f"unreadable: ..."` | RED: `.startswith("extraction_error")` is False | Yes — exact match |
| SA4 | `drive_register._register_drive_file`: `Provenance(..., inputs=[parent.id])` → `inputs=[]` | RED: `assert [] == ['src_...']` | Yes — exact match |
| SA3 | `drive.HttpDriveClient.list_folder`: `DriveFile(f["id"], f.get("name","file"), ...)` → `DriveFile(f["id"], headers["Authorization"], ...)` | RED: bearer token (`ACCESS_BEARER_TOKEN_QWER`) found in the on-disk `sources.jsonl` (leaked via `.name`/`.label`) | Yes — exact match |

**CAPABILITY-COVERAGE: 5/5 rows reproduced.**

The 6th test (`test_device_code_exchange_returns_refresh_token_offline`) is, as the manifest states, a mechanism-presence test for the device-flow exchange itself, not a separate SA capability row — confirmed it genuinely drives `request_device_code`/`exchange_device_code` over `httpx.MockTransport` with no stubbing of the functions under test.

## SA3 — special-rigor credential review (direct code read, both files in full)

- `drive.py`: the refresh token and client secret are held on `HttpDriveClient` only as **keys** (`_client_secret_key`, `_refresh_token_key`) plus a `resolver: Callable[[str], str]`. `_access_token()` calls `self._resolver(...)` at call time, uses the returned value immediately in the token-exchange POST body, and returns only the **access token** — never retained on `self`, never logged. `list_folder`/`fetch_file` build a bearer header locally from `_access_token()`'s return value and never store or return it; both return `DriveFile`/`DriveFetch` objects that carry only `id`/`name`/`mime_type` and `content`/`error` — no token field exists on either NamedTuple.
- `drive_register.py`: never imports or touches a credential; it depends only on the `DriveClient` protocol (`list_folder`/`fetch_file`), which by construction cannot leak a token to this layer.
- Grep of both files for `print(`, `logging.`, `log.info/debug/warning/error` → **zero matches** (only docstring prose mentioning "never logged"). Matches the manifest's claim.
- `assert_no_raw_secrets` gate: confirmed live and unmodified in `sources/audio.py` (`_add_audio_source` → `transcribe_audio` → `assert_no_raw_secrets(TRANSCRIBE_PROMPT, secrets)`), reached from `drive_register._dispatch_by_suffix` via the threaded `secrets` kwarg into `register_audio`. Not part of this unit's diff — pre-existing, correctly reused.
- The SA3 mutation row (table above) independently confirms an access-token leak into `Source.label`/`sources.jsonl` is caught by the test, and the credential inputs (`refresh_token`, `client_secret`, `access_token`) never appear in the real (unmutated) run's on-disk `sources.jsonl` — re-verified by re-running the row's green-before state and reading the file.

## Other criteria

- **SA6** (model names, never decides): no diff in this unit gives a model any control over which checks run or what gets stored beyond a `notes`/summary field; `provider` is passed through unchanged to the existing, unmodified `_add_audio_source`/`transcribe_audio` path. Holds.
- **Explicit no-fire list**: device flow only — confirmed, no service-account code path exists anywhere in `drive.py`/`drive_register.py`; no IMAP/SMTP code. Holds.
- **Not-UI-touching**: changed paths are all `src/autotester/schema|sources|stages` + `tests/` + generated `docs/MAP.md` — no `ui/`, route, or template path. Mode D (live browser) is correctly not applicable.
- **C10** (commit carries only this unit's paths): `git show --name-only 2485ca2` = the 9 files listed above, all within the manifest's declared scope + its own manifest. No other unit's paths present.
- **Working tree clean** at check time (`git status --short` empty) — nothing left over from my mutation testing (all mutations were applied only in the throwaway copies, never in the bound tree).

## T-162 close question (per dispatch instruction — do not run `goal_cli.py done`)

DRIVE is confirmed as the last declared phase-2 adapter (EMAIL/AUDIO already PASSed). However, I flag a real gap, filed as **ISS-t162-drive-2b-1** (medium): `.goal/goal.json`'s `T-162.done_check.cmd` is still `uv run pytest tests/test_source_adapters.py`, which only runs the original 11 TEXT/DOC tests. `test_source_adapters_audio.py`, `test_source_adapters_email.py`, and this unit's `test_source_adapters_drive.py` were each split into their own files (doctor's 300-line rule) across the three fast-follow units, and **none of the three is named by the done_check** — re-confirmed live (`11 passed`, and that command alone would pass regardless of DRIVE/EMAIL/AUDIO's state). If T-162 is closed by that control value alone, the close would not actually re-verify the phase-2 scope it claims to gate. Not a blocker on THIS unit's PASS (the staleness predates it and this unit did not touch `.goal/goal.json`), but T-162 should not be considered mechanically "proven done" until the done_check is widened.

## FAILURES

None at >80% confidence.

## Verdict

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (SA1-SA6), 0/0 invariants (no core-invariants/ingest.md criterion is engaged by this unit beyond C1-C10, C2/C7/C9/C10 all separately confirmed above)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (source-adapter layer only; changed paths: schema/enums.py, sources/drive.py, sources/drive_register.py, sources/adapters.py, stages/ingest.py, sources/__init__.py, tests/test_source_adapters_drive.py, docs/MAP.md — no ui/route/template path)
ISSUES-WRITTEN: ISS-t162-drive-2b-1 (medium, T-162 done_check does not cover AUDIO/EMAIL/DRIVE test files)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: Every SA1-SA6 criterion is evidenced by independently re-run tests, direct code reads of both new files in full, and 5/5 capability-coverage rows reproduced with correct-reason reddening in isolated copies outside the bound tree. Diff scope is exactly the manifest's declared files; no existing schema field, store, or function was duplicated or deleted. Full suite (1568 passed / 0 failed) and ruff/doctor re-confirmed clean. One process gap found and filed (T-162's done_check staleness) — does not block this unit.
```
