# Verdict — at215-vl1c-measured-placement

**Date:** 2026-09-09
**Checker mode:** A (unit check)
**Contract:** `qa/contracts/video-learning.md` VL1c (HIGH-criticality)
**Manifest:** `qa/manifests/at215-vl1c-measured-placement.md`
**Cycle checked: 1**

## What I re-ran myself

- `ffmpeg -version` → 8.1.1-full_build, present on this host (not a SKIP).
- `uv run pytest tests/test_media_real_ffmpeg.py -v` → **2 passed**, live tree — matches the
  manifest's pasted output exactly.
- `uv run pytest -q` → full suite green, exit 0 (same shape as manifest: no FAILED lines, all
  dots/skips).
- `uv run ruff check src tests scripts` → All checks passed.
- `uv run autotester doctor` → doctor: clean.

## Independent sabotage confirmation (own isolated extract)

`git archive HEAD` into
`C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/.../scratchpad/at215_extract`, its own
`uv sync` venv. Verified `autotester.media.frames.__file__` resolved **inside the extract**
before trusting any result.

1. **Baseline in the extract:** `tests/test_media_real_ffmpeg.py` → 2 passed (test file ships at
   HEAD; commit `ba4c5b6` — confirmed ancestor of HEAD `b41e07d`, which adds only the manifest).
2. **Reproduced the manifest's own sabotage** — shifted `extract_frame`'s seek (`frames.py`,
   `"-ss", f"{t_s}"` → `f"{t_s + 1.0}"`) by +1.0s. Result: **exactly 1 failure**,
   `test_extract_frame_lands_on_the_second_it_was_asked_for`, content-mismatch (`expected
   (255,0,0), measured (0,254,0)`, i.e. asked for red/second-0, got green/second-1) — not an
   argv mismatch. `test_a_chunks_first_frame_...` stayed green, matching the manifest exactly.
   Restored from `frames.py.orig`; live tree re-confirmed untouched
   (`grep -c '"-ss", f"{t_s}"' src/autotester/media/frames.py` → 1).
3. **Went further than the manifest** — shifted `encode_chunks`'s seek (`chunks.py`,
   `"-ss", f"{offset_s}"` → `f"{offset_s + 1.0}"`) by +1.0s, the call site the manifest did NOT
   sabotage. Result: **exactly 1 failure**,
   `test_a_chunks_first_frame_is_the_second_the_plan_named`, same content-mismatch shape
   (expected red/second-0, measured green/second-1); the other test stayed green. This confirms
   the second call site VL1c governs is independently caught, not merely gestured at. Restored
   from `chunks.py.orig`; live tree re-confirmed untouched
   (`grep -c '"-ss", f"{offset_s}"' src/autotester/media/chunks.py` → 1).

Both sabotages were single-anchor edits, restored by overwriting from a saved copy (never `git
checkout`), with the live tree grep-verified unchanged after each.

## Tolerance/luck check

`COLOURS = {0: red(255,0,0), 1: green(0,255,0), 2: blue(0,0,255)}`, `TOLERANCE = 40`. Computed
per-channel distances between every pair: (255,0,255) worth of mismatch, minimum non-zero
per-channel distance between any two colours is **255**, vs a tolerance of 40. No pair of the
three colours can satisfy another's assertion — the test cannot pass by luck via adjacent-colour
confusion. TOLERANCE=40 is loose only against compression noise on a flat field, not against the
colour separation itself.

## Test-only confirmation

`git show ba4c5b6 --stat`: `tests/test_media_real_ffmpeg.py | 121 +++...` — **1 file changed, 121
insertions(+)**, new file only. No production code touched by this commit, matching the
manifest's claim. (The one later commit on top, `b41e07d`, adds only the manifest itself —
verified via `git log --oneline ba4c5b6..HEAD`.)

## Criterion judgement

VL1c's measured-placement half ("a chunk's first frame, and a frame `extract_frame` pulls at t,
must be the second the plan/model named... judged by measurement, not by argument order") is now
covered by a real-ffmpeg, content-measuring test at **both** call sites the criterion governs —
`encode_chunks` and `extract_frame` — independently, with sabotage-confirmed discrimination at
each site and no possibility of a lucky pass given the chosen colours/tolerance. `test_media_shellout.py`'s
existing argv assertions are untouched and remain a supplement, not a replacement, exactly as the
manifest states. This closes the gap AT-215 named (three consecutive sweeps flagged it unchanged).

VL1c's other half (coverage/no-gap, `plan_chunks`) is unaffected and out of scope for this unit
(the manifest never claimed it).

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (VL1c measured-placement half), 0/0 invariants in scope
FAILURES (if any):
- none
LIVE-BROWSER: not-applicable (tests/test_media_real_ffmpeg.py only — no UI surface changed)
ISSUES-WRITTEN: none (AT-215 closed by this unit; ledger update below)
EXPLANATION: The manifest's pasted commands and sabotage were independently reproduced byte-for-byte
in a fresh git-archive extract with its own venv. Going beyond the manifest, the encode_chunks call
site (not sabotaged in the manifest) was independently sabotaged and caught by the other test,
confirming both VL1c-governed call sites are now measured rather than argued. The chosen colours are
255 apart on two channels each against a tolerance of 40, so the test cannot pass by luck. git show
--stat confirms this is test-only, as claimed.
```
