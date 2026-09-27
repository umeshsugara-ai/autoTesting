# Manifest — at639-chunk-timeout

**Contract:** qa/contracts/video-learning.md (VL1 shell-out boundary) · qa/contracts/core-invariants.md (C2 line caps, C12 fail-closed health signals)
**Goal task:** none (ledger-driven unit; AT-639 filed by the Mode B sweep 2026-09-27, QUEUE.md rank 2)
**Date:** 2026-09-27
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk:** skip — `media/chunks.py` is an ffmpeg shell-out inside the INGEST stage. No screen, route, component or navigation path changes; nothing a rendered page reads changes shape.
**Issues addressed:** AT-639
**Executor:** claude-opus-5 (the maker orchestrator, inline)
**Executor rationale:** two-file, ~20-line change against a shape the sweep had already localised to `file:line`, and the measured RAM ceiling was 0 build slots (2.1 GB free of 23.7 with three full-suite checkers holding the machine). Dispatching a build subagent would have queued behind that ceiling to re-derive a known edit. No Ollama lane: this is a subprocess boundary in the repo's own ingest path.

## What changed

- `src/autotester/media/chunks.py`:112-121 — new module constant `CHUNK_TIMEOUT_S = 900.0`, with
  the reasoning in its docstring: `media/frames.py` bounds a single-still grab at 60s and
  `media/transcribe.py` bounds whisper at 3600s, so this was the **one unbounded shell-out of the
  three**. 900s is deliberately generous — a 180s chunk at `-preset veryfast` finishes in seconds
  on any machine that can run the browser — so the bound fires on a hang, never on slow work.
- `src/autotester/media/chunks.py`:116-133 — `encode_chunks`'s `subprocess.run` now passes
  `timeout=CHUNK_TIMEOUT_S` and is wrapped in `except (OSError, subprocess.SubprocessError)` that
  **unlinks the half-written chunk and re-raises**. The re-raise is the point: it keeps the
  degradation where AT-166 put it, in `stages/media_prep.prepare`:80-86, which turns any failure
  here into `UnreadableRecording` and writes no `media.json`.
- `tests/test_media_shellout.py`:146-189 — two guards, in the module whose stated job is "the
  boundary between this codebase and a program it does not control".

## Why the bug was invisible, which is the part worth checking

`stages/media_prep.prepare`:80 already catches **`except Exception`** around this call and degrades
honestly (AT-166). So every failure `encode_chunks` could *raise* was already handled — and the one
failure it could not raise was the only one that mattered: an unbounded `subprocess.run` on a wedged
ffmpeg never returns, so `prepare` never reaches its own recovery and the INGEST stage hangs
forever with no health signal. This is C12's shape (a health signal that fails open) arriving as a
hang rather than as a false green.

## How to verify (commands + expected)

- `uv run pytest tests/test_media_shellout.py tests/test_media_prep.py tests/test_media_real_ffmpeg.py` → exit 0, 21 passed (19 before this unit + 2 new)
- `uv run ruff check src tests scripts` → exit 0, `All checks passed!`
- `uv run autotester doctor` → exit 0, `doctor: clean`
- `wc -l src/autotester/media/chunks.py tests/test_media_shellout.py` → 136 and 189 (both well under the C2 300 cap)

## Actual outputs (maker's own run, in the bound worktree)

```
$ uv run pytest tests/test_media_shellout.py tests/test_media_prep.py tests/test_media_real_ffmpeg.py
.....................                                                    [100%]
21 passed in 78.97s (0:01:18)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

`tests/test_media_real_ffmpeg.py` is included deliberately — it cuts a real 3-second video with the
real binary, so the timeout kwarg is proven not to break a working encode, not just a mocked one.

## Capability coverage (each new claim → its isolating falsification)

| capability (one line) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| The chunk cut is bounded: `encode_chunks` asks ffmpeg for `timeout=CHUNK_TIMEOUT_S`, so a wedged ffmpeg cannot hang INGEST forever | `tests/test_media_shellout.py::test_the_chunk_cut_asks_for_a_timeout` (:146) | delete ` timeout=CHUNK_TIMEOUT_S,` from the `subprocess.run` call in `src/autotester/media/chunks.py`:122 — single file, single hunk, inside "What changed" | GREEN before: `2 passed, 7 deselected in 0.41s` (both rows) · RED after: `FAILED tests/test_media_shellout.py::test_the_chunk_cut_asks_for_a_timeout` / `1 failed, 8 deselected in 1.18s`, failing on `+ and 900.0 = chunks_mod.CHUNK_TIMEOUT_S` — the kwarg assertion, not an import or collection error · restored: `1 passed, 8 deselected in 0.32s` |
| A killed cut leaves no truncated chunk on disk, and the failure still reaches `media_prep` rather than being swallowed | `tests/test_media_shellout.py::test_a_timed_out_cut_leaves_no_half_written_chunk` (:172) | delete the `path.unlink(missing_ok=True)` line, leaving the bare `raise`, in `src/autotester/media/chunks.py`:132 | GREEN before: `1 passed, 8 deselected in 0.44s` · RED after: `AssertionError: a truncated chunk survived the timeout: ['chunk_00_0s.mp4']` / `1 failed, 8 deselected in 2.47s` — and the `pytest.raises(TimeoutExpired)` half still holds, so the test fails on the cleanup claim alone · restored: `1 passed, 8 deselected in 0.58s` |

**Where the perturbation ran.** `…/scratchpad/at639-falsify`, built with
`tar --exclude=.git --exclude=.venv --exclude=.worktrees` from the worktree, outside the bound root,
with its own fresh venv. Proven to resolve its own source before any edit:
`uv run python -c "import autotester.media.chunks as c; print(c.__file__)"` →
`…\scratchpad\at639-falsify\src\autotester\media\chunks.py`.

**The worktree-path oddity from at626 is now explained, not just disclosed.** Both falsifications
first printed the *worktree's* path in the traceback header
(`D:\autoTesting\.worktrees\…\tests\test_media_shellout.py:189`) while running in the copy. My
first guess — `.pytest_cache` — was wrong: clearing it changed nothing. The actual cause is the
copied **`__pycache__`**: `tar` carried `tests/__pycache__/test_media_shellout.cpython-311-pytest-9.1.1.pyc`,
whose `co_filename` is baked to the worktree path, and CPython reused the `.pyc`. Demonstrated
directly — `marshal.loads(pyc[16:]).co_filename` → `D:\autoTesting\.worktrees\at639-chunk-timeout\tests\test_media_shellout.py`
(a one-off read of a `.pyc` this session had just generated in its own scratchpad — no untrusted
input, and no `marshal`/`pickle` call enters the shipped code)
— and after clearing every `__pycache__` the same RED prints `tests\test_media_shellout.py:189`,
relative to the copy. The executed test source was the copy's byte-identical content throughout and
the module under test was always the copy's. **This retires the honest-oddity note in
`qa/manifests/at626-dotted-import.md`, which has the same cause.**

**The bound worktree was verified intact after each perturbation:** `git status --short` showed only
this unit's two modified files, `timeout=CHUNK_TIMEOUT_S` still present at :123, and
`uv run pytest tests/test_media_shellout.py` → `9 passed in 0.56s`.

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths are `src/autotester/media/chunks.py` and
`tests/test_media_shellout.py`: an ffmpeg subprocess call in the INGEST stage and its guards. No
`*.tsx|jsx|vue|svelte|html|css`, no `ui/`, no route, page or component.

## Gaps stated, not hidden

- **Full suite not run by the maker for this unit.** Three full-suite checkers were holding the
  machine (free RAM 1.5–2.1 GB of 23.7 measured across this tick) and a full `uv run pytest` here
  takes ~1300s. The three test files that exercise this module and its caller all ran, green,
  including the real-ffmpeg one. The checker re-runs the suite. If
  `tests/test_flake_probe_real_process.py` surfaces, that is **AT-627**, an environmental flake of
  the AT-196/AT-505/AT-518 class, not chargeable to this unit.
- **The bound is not proven to fire against a genuinely hung ffmpeg.** Row 1 asserts the kwarg is
  requested and row 2 asserts the cleanup on a simulated `TimeoutExpired`; neither wedges a real
  binary for 900s. A test that hangs 15 minutes to prove a timeout exists is a test nobody runs
  twice, and that trade is stated here rather than implied. The checker may judge it insufficient.
- **A `CHUNK_TIMEOUT_S` of 900s is a judgement, not a measurement.** No corpus of real recording
  encode times was gathered; the number is reasoned from `-preset veryfast` on a 180s chunk.
- **AT-645 (duplicate ledger ids) is not addressed here** and is not claimed to be.

## Status: checked-PASS (qa/verdicts/at639-chunk-timeout.md, Cycle checked: 1, verdict commit 50849f58, merged into master)

**Two follow-on issues filed by the checker, carried forward open — neither blocking:**
- `ISS-at639-1` (medium) — `CHUNK_TIMEOUT_S` bounds ONE ffmpeg call, but `media_prep.prepare`'s
  loop over the whole chunk plan has no aggregate deadline: a systemically broken ffmpeg can
  still hang INGEST for N x 900s (~3.25h for a 40-minute recording's ~13 chunks). This is the
  sharper version of the gap this manifest disclosed but stopped short of naming. The original
  single-call-unbounded defect is genuinely closed; the aggregate one is new debt.
- `ISS-at639-2` (low) — `path.unlink(missing_ok=True)` at `chunks.py`:132 is itself unguarded;
  on Windows it can raise `PermissionError` on a just-killed file and replace the original
  exception before the `raise`. Fail-closed still holds (`media_prep`'s broad `except`), but the
  persisted failure would carry the wrong exception type — a diagnostics-quality defect.

The checker also judged this manifest's disclosed gap (neither test wedges a real 900s hang)
**sufficient**: proving `timeout=` reaches `subprocess.run` and that cleanup fires on a
simulated `TimeoutExpired` is the right-shaped test, matching what was already accepted for
`frames.py`/`transcribe.py`'s sibling bounds. Its own full suite ran clean — 2016 passed, exit 0,
764s, with AT-627 not surfacing at all.
