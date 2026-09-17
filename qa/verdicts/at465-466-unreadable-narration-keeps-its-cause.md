# Verdict — at465-466-unreadable-narration-keeps-its-cause

**Date:** 2026-09-17
**Cycle checked: 1**
**Checker:** /checker Mode A, fresh subagent, bound to `D:/autoTesting`
**Unit commit:** eb8d617 (source clean in working tree; `git status` shows no `src/` changes)

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (VL1, VL1b, C1, C3, C7), 1/1 invariants hold (I-VL1)
FAILURES: none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: schema/media.py, media/transcribe.py, stages/ingest.py, cli_video.py CLI line, 5 test files; no template/route/ui module reads Transcript — grep of src/autotester/ui and all src *.html/*.js for "transcript" is empty)
ISSUES-WRITTEN: AT-468 (low), AT-469 (low); AT-465, AT-466 open -> fixed
EXPLANATION: Every verify command reproduced. All 5 falsifying edits went red in a copy outside the root, each on the assertion its check is named for. The one shared sidecar reader removes the duplicated try/except (C3). Against every sidecar in the repo, the only changed loads are `{}` files, which is the intended AT-466b change. Two low findings: the schema field description is false about leaking sidecar content (the manifest's own Known limits admits the leak), and the mutation harness has the space-in-id attribution defect, confirmed.
```

## What I re-ran (bound tree)

| command | result |
|---|---|
| `uv run pytest tests/test_schema_video.py tests/test_media_prep.py tests/test_media.py tests/test_analyze_video.py tests/test_ingest_real_cli.py tests/test_ingest_persist.py` | `94 passed in 2.90s`, exit 0 |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run python scripts/mutation_check.py qa/evidence/at465-466-.../mutations.json` | `5/5 mutations killed`, each named test among the failures |
| `uv run python scripts/mutation_check.py qa/evidence/at216-.../mutations.json` | `2/2 mutations killed` |
| `uv run pytest -q -x -p no:cacheprovider` (full suite) | exit 0 (stops at the first failure, so no test failed). My `tail` missed the count line. |

## Capability coverage (own copy)

- **Copy:** `src tests scripts pyproject.toml` copied to the scratchpad `copy465`, outside the root.
- **Imports come from the copy:** a probe test asserted that `autotester.__file__` is under `copy465` (it is). The CLI tests use in-process `CliRunner`, not a subprocess.
- **Admissibility:** every cell is a single-hunk edit to one file named in "What changed". No CONTRACT_MISMATCH.

| row | named check, before | after the edit: the assertion that fired |
|---|---|---|
| 1 cause discarded (`media.py`) | 1 passed | `assert 'JSONDecodeError' in ((None or ''))`, the cause assertion |
| 2 guard removed (`media.py`) | 1 passed | `assert 'sidecar' == 'unreadable'`, `{}` read as silence |
| 3 transcribe -> from_sidecar | 1 passed | `ValueError: sidecar has no segments list` escapes. That is the best-effort property the test is named for. |
| 4 ingest -> from_sidecar | 1 passed | `assert 1 == 0` on the exit code, `Result JSONDecodeError`: the ingest stopped |
| 5 prep branch `if False:` | 1 passed | `assert 'narration unreadable' in '... 0 narration segment(s) ...'` |

## Attacks beyond the manifest

- **VL1b, every sidecar in the root.** I found 113 `*.transcript.json` files by walking the tree (including `.work/`, `tests/fixtures/erp1`, and the two real `.work/pathlynks-depth` sidecars).
  - **Method:** I loaded each one with the pre-change logic (`raw.get("segments", [])`) and with `read_sidecar`.
  - **Result:** 105 files give identical `engine="sidecar"`, segments and speech_seconds, or were already unreadable.
  - **The 8 that differ** are all byte-exact `{}` files from `test_find_sidecar_only_reports`, which is the intended AT-466b change. No real sidecar is lost.
- **Persisted transcripts.** All 91 `transcript.json` files in the root predate the unit (none has the `unreadable_reason` key), and 91/91 validate. A new unreadable transcript saved and reloaded through `ProjectStore("demo", root=tmp)` compares equal, reason included. A hand-written legacy `engine="unreadable"` JSON loads with reason `None`.
- **Where `unreadable_reason` goes.** Consumers are `cli_video.py:106-107` (CLI stdout) and persistence only.
  - `narration_block` renders a fixed sentence. I measured that the reason text is absent from the prompt block.
  - No log call, UI module or template reads it.
  - **It can carry sidecar content:** a missing-field ValidationError embeds a truncated `input_value`, and I measured `... for alice@example.com` in the reason. The manifest discloses this, but the committed field description says "the parse error, never the file". Filed as **AT-468 (low)**.
- **C3.** No other sidecar try/except remains. `transcribe_subprocess`'s `raw.get("segments", [])` parses whisper's own stdout, not a sidecar, and predates this unit. `analyze_video.load_transcript` delegates to `ingest.load_sidecar`.
- **Edge inputs.** All of these return `engine="unreadable"` with a cause and never raise:
  - `speech_seconds` as `"abc"`, `null` or `[1]`
  - `segments` as `[null]`, mixed with null, `null`, or a top-level list
  - a BOM-prefixed file

  `{"segments": []}` still loads as a sidecar, which is a legitimate claim of silence. A 200,000-segment sidecar loads in 0.8 s. The reason is capped at 300 characters (a 1000-character bad value gave 231).
- **Callers of the stricter `from_sidecar`.** Only `read_sidecar` and tests call it. Every test fixture has `segments`, and the full suite is green.
- **The manifest's mutation_check claim is real.** `failed_tests('FAILED tests/t.py::test_x[a b] - AssertionError: boom')` returns `{'tests/t.py::test_x[a'}`. This is fail-closed: a false SURVIVED, never a false KILL. Filed as **AT-469 (low)**.
- **Known limits.** They are honest, and the content-leak limit matches what I measured. Two additions:
  - The committed schema description contradicts the leak (AT-468).
  - A multi-line ValidationError reason prints across several lines of the `ingest prep` output. This is cosmetic and not filed.

## Contract judgement

- **VL1:** the unreadable state stays distinct from `none` and from silence in prep, ingest and the operator CLI line. Evidenced by rows 2 and 5 and the `{}` probe.
- **VL1b:** existing sidecars load verbatim, with segment-by-segment equality over 113 files. The sidecar path is returned before any whisper call (`transcribe.py:60-63`), so whisper does not run.
- **C1:** the new field is on a model in `schema/` with `extra="forbid"` kept. It defaults to `None`, so legacy files load.
- **C3:** one reader, and doctor is clean.
- **C7:** checks re-run independently. The harness asserts a green baseline and attributes each kill, and each row's kill was attributed to its named test.
