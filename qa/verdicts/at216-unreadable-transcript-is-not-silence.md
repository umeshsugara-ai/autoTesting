# Verdict — at216-unreadable-transcript-is-not-silence

**Cycle checked: 1**
**Date:** 2026-09-17
**Checker:** /checker Mode A (fresh subagent), bound to `d:/autoTesting`
**Unit commit:** 7c02b8a (HEAD at check time f7d37d9, which adds only `qa/.last-tick`)

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (VL1, VL1b, VL5, I8, AT-216), 2/2 invariants hold (C3, C7)
FAILURES: none
CAPABILITY-COVERAGE: 2/2 rows reproduced
LIVE-BROWSER: not-applicable (src/autotester/stages/analyze_video.py, tests/test_analyze_video.py — prompt text sent to a model; no template, route or rendered field)
ISSUES-WRITTEN: AT-465, AT-466 (both low, pre-existing, outside this diff); AT-216 open -> fixed
EXPLANATION: load_transcript now delegates to ingest.load_sidecar, so a malformed sidecar is engine="unreadable" rather than None, and build_chunk_prompt starts from ingest.narration_block, so an unreadable transcript (loaded or persisted by media_prep) reaches every chunk prompt as "could not be read", never "no speech detected". Both falsifying edits reproduce in a throwaway copy with the named assertions firing; eight malformed sidecar shapes, the verbatim-sidecar path, engine="none", and a transcript with no segments in a chunk all behave as the contract requires. Two residuals found by grepping consumers are filed as low issues, not held against this unit.
```

## What I re-ran (bound tree, my own runs)

| command | expected | observed |
|---|---|---|
| `uv run pytest tests/test_analyze_video.py -o addopts=""` | 13 passed | `13 passed in 0.62s` |
| `uv run pytest tests/test_analyze_video.py tests/test_analyze_cache.py tests/test_ingest*.py tests/test_media_prep.py -o addopts=""` | 67 passed | `67 passed in 2.89s` |
| `uv run ruff check src tests scripts` | All checks passed! | `All checks passed!` |
| `uv run autotester doctor` | doctor: clean | `doctor: clean` |
| `uv run python scripts/mutation_check.py qa/evidence/at216-.../mutations.json` | 2/2 killed | `2/2 mutations killed`, "actually failed" lists match "claims to kill" exactly |
| `uv run pytest -q` (full) | green | exit code 0 (repo `addopts="-q"` plus `-q` suppresses the count line; one `s` visible, no F/E) |

## Capability coverage — reproduced in a throwaway copy

Copy: `src tests scripts docs profiles pyproject.toml uv.lock` to the session scratchpad (outside the
bound root), `__pycache__` removed, run with `PYTHONPATH=<copy>/src`. Import provenance confirmed:
`autotester.stages.analyze_video.__file__` resolved to `...scratchpad\at216copy\src\autotester\stages\analyze_video.py`.
Copy `analyze_video.py` byte-identical to the bound tree (`cmp`). Both cells are single-hunk edits to
`src/autotester/stages/analyze_video.py`, a file named in "What changed" — admissible. Harness asserted
anchor count == 1 and file content changed before each run; each row was run alone from the pristine
file (a first attempt contaminated row 2 with row 1 because `return None` occurs twice; discarded and
re-run clean).

| row | before (copy) | after edit | assertion that fired |
|---|---|---|---|
| 1 `return load_sidecar(source)` -> `return None` | 13 passed | 2 failed: `test_a_malformed_sidecar_is_loaded_as_unreadable_not_as_no_transcript`, `test_every_chunk_prompt_says_the_transcript_is_unreadable_not_silent` | `assert (None is not None)` — the named test's own assertion |
| 2 `narration = narration_block(transcript)` -> hardcoded "no speech detected" | 13 passed | 2 failed: `test_an_unreadable_transcript_saved_by_media_prep_is_not_rendered_as_silence`, `test_every_chunk_prompt_says...` | `assert 'could not be read' in '# ingest_video_v1 ...'` — the named test's own assertion |

Trap check: neither test asserts a state the bug also produces (the old code yields `None` /
"no speech detected", both of which the assertions reject), and neither reads live state.

## Attacks beyond the manifest (throwaway copy, 14 probe cases, all passed)

- **VL1b verbatim:** a valid sidecar with fractional timings and Hinglish text loads `engine="sidecar"`,
  segments identical in (start, end, text), `speech_seconds` preserved; chunk 0 [0,180) carries both
  in-window lines, chunk 1 [165,345) carries only the 170s line (VL5 slicing unchanged).
- **Malformed shapes -> `unreadable`, prompt says "could not be read" and never "no speech detected",
  for both prompts:** empty file, `[]`, `null`, whitespace, `{"segments": "abc"}`, `{"segments": [1,2]}`,
  a segment missing `end`, non-UTF-8 bytes.
- **Persisted `engine="none"`** still renders "no speech detected" and not "could not be read".
- **No sidecar** -> `load_transcript` returns `None`, prompt says "no speech detected".
- **Segments but none inside the chunk** -> "no speech in this section", not "could not be read".
- **End to end:** persisted `unreadable` through `analyze` with a spy provider -> 4 calls (2 chunks x 2
  prompts), every prompt says "could not be read", no residual `{{NARRATION}}`.
- **Import graph:** `stages.ingest` does not import `analyze_video` (no cycle). `ui/routes_sources.py:27`
  and `cli_video.py:17` already imported `stages.ingest` before this unit, so no new import at either
  entry point; no heavy module (faster_whisper, ctranslate2, google.genai, playwright, torch) in
  `sys.modules` after importing `analyze_video`.
- **Cache:** prompt text is part of the observation cache key; the text changed only for unreadable
  transcripts, so absent/none/segmented recordings keep their cache hits and unreadable ones are
  correctly re-asked.

## Criteria

- **VL1** (unreadable is a third state, never folded): met on the analyze path — evidence above.
  Residual on the CLI path filed as AT-465 (pre-existing, `cli_video.py:104-110`).
- **VL1b** (sidecar reused verbatim): met — same `Transcript.from_sidecar`, probe compares segment by segment.
- **VL5** (only this chunk's narration; silent section says so): met — existing tests
  `test_a_chunk_gets_only_its_own_narration`, `test_a_silent_section_says_so...` pass, plus probes.
- **I8** (when no speech exists the prompt says so explicitly; never a gap): met — every state renders
  an explicit line; no placeholder survives.
- **AT-216**: the defect (malformed sidecar indistinguishable from never-transcribed) is fixed ->
  status `fixed`. The "discarding the cause" half is honestly disclosed as a known limit and filed
  separately as AT-466 (low).
- **C3** (one concept, one place): holds and improves — `analyze_video`'s private sidecar loader
  removed in favour of `ingest.load_sidecar`; doctor clean. (A second catch-to-unreadable remains in
  `media/transcribe.py:63-66`, pre-existing, noted in AT-466.)
- **C7** (independent, non-vacuous verification): holds — mutation harness asserts baseline, attributes
  kills by node id, and both rows reproduced independently.

## UI judgement (D-024)

Not UI-touching. Changed paths are a stage module and its tests. The only deterministic change is the
text of the prompt given to a vision model; no template, route, or rendered field changes, and the
prompt is not displayed on any page. What the Sources page later shows depends on a live model
reading, which a browser check cannot tie to this change deterministically.

## Known limits — honesty review

- "No live model run" and "cause not named": accurate and complete for the model path.
- Incomplete in one respect: it does not mention that `autotester media prep` still prints
  "0 narration segment(s)" for an unreadable transcript (AT-465). Low severity, pre-existing.
- The disclosed `git stash push -- src/autotester/stages/analyze_video.py` on the shared tree: `git
  stash list` is empty now and the committed diff contains only this unit's hunks, so no damage
  observed. It is still a breach of the shared-tree rule ("never `git stash`"). Recorded here, not
  charged as a failure, because it was disclosed and left no trace.
