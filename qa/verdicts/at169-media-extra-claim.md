# Verdict — at169-media-extra-claim

**Date:** 2026-09-16
**Manifest:** `qa/manifests/at169-media-extra-claim.md`
**Contract:** `qa/contracts/video-learning.md` (VL1 + the "Explicitly UNVERIFIED" section) and
`qa/contracts/core-invariants.md` (C2, C3, C7)
**Bound root:** `d:/autoTesting`
**Adapter:** none present → DEFAULT (coding) adapter
**Cycle checked: 1**
**Dual check:** no (primary verdict)

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 2/2 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 2/2 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: src/autotester/media/transcribe.py — module
  docstring only; tests/test_media.py — one added test. No route, template, JS or rendered
  output is reachable from either.)
ISSUES-WRITTEN: none new; AT-169 open → fixed
EXPLANATION: The docstring's false claim is gone and the true state — faster_whisper absent
from the venv AND no `[project.optional-dependencies]` block in pyproject.toml — is now pinned
by a regression test I re-ran and falsified myself in an isolated copy. All four verify commands
were re-run by me and are green, including the full suite (exit 0, no flake this run). No
executable line changed, so VL1's degrade behaviour is untouched, and the packaging work stays
correctly gated with AT-130, which I left open.
```

## What I re-ran myself (never read from the manifest)

| Command | My result |
|---|---|
| `uv run pytest tests/test_media.py -q` | `...................` 19 passed, exit 0 |
| `uv run pytest -q` | exit 0, full suite green (no `test_mutation_check.py` flake this run) |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| `grep -n "optional-dependencies\|faster_whisper\|faster-whisper" pyproject.toml` | **no matches** (exit 1) — the fact the docstring now states |
| `uv run python -c "…transcribe.whisper_available()"` | `False` — faster_whisper genuinely absent from the project venv |
| `grep -rn "media\` extra\|--extra media\|optional-dependencies" src docs qa/contracts` | only the corrected docstring and the contract's own UNVERIFIED section; no residual false claim |

Every number in the manifest's "Actual outputs" block reproduced. The manifest's own note about the
known `tests/test_mutation_check.py` flake (AT-357, open) is accurate and did not fire in my run; it
is not charged against this unit, which touches neither file.

## Step 4b — capability coverage, reproduced in a throwaway copy

**Copy discipline.** The working tree (excluding `.git`, `.venv`, `.work`) was copied to
`…/scratchpad/at169-copy`, **outside** the bound root, and `uv sync`'d there.
`autotester.__file__` resolves to
`…\scratchpad\at169-copy\src\autotester\__init__.py`, so the venv is genuinely the copy's. All
`__pycache__` directories were purged after the first run because tar-preserved mtimes let stale
`.pyc` files print the **bound tree's** paths in tracebacks; after the purge every path in the
output is the copy's (`tests\test_media.py:212`), which is how I know the reds below came from the
copy and not from `d:/autoTesting`. **Not one file in the bound working tree was edited** —
`git status --porcelain` on the three paths afterwards shows `M transcribe.py`, `M test_media.py`
and `pyproject.toml` untouched, exactly as before I started.

**Copy green BEFORE any edit (this row's "before" line, taken from the COPY, not from step 3):**
`uv run pytest "tests/test_media.py::test_no_media_extra_is_falsely_claimed_to_exist" -q` →
`.` 1 passed, exit 0.

### Row 1 — "the false `media`-extra claim cannot return to the docstring"

- Edit applied: single hunk, single file, `src/autotester/media/transcribe.py` (named in "What
  changed") — the corrected paragraph replaced by the pre-fix text ending
  `(it is declared under the optional \`media\` extra)`. Anchor asserted unique (`count == 1`) and
  the file re-read as changed.
- Result: `..................F` — **exactly one failure**, 18 green.
  `FAILED tests/test_media.py::test_no_media_extra_is_falsely_claimed_to_exist` on
  `assert "optional \`media\` extra" not in doc`, message `the false extra claim is back`, at
  `tests\test_media.py:212`. **Reproduced exactly as claimed**, including the line number.
- Kill attribution: the failing assertion is the one the test is named for. Nothing failed to
  parse, import or collect — 18 sibling tests in the same file ran and passed, so nothing reddened
  for free.

### Row 2 — "the docstring's claim about `pyproject.toml` is pinned to the real file"

- Copy restored to the post-change state first, re-verified green (`...................` 19 passed).
- Edit applied: single hunk, single file, `pyproject.toml` — appended
  `[project.optional-dependencies]` / `media = ["faster-whisper>=1.0"]`.
- Result: `..................F` — **exactly one failure**, 18 green. Same test, this time on the
  **first** assertion `assert "[project.optional-dependencies]" not in pyproject`, at
  `tests\test_media.py:209`. **Reproduced exactly as claimed**, including the line number.
- Kill attribution: the assertion that fired is the file-grounding half of the test, which is the
  capability this row claims. Collection and import were unaffected.

Note on `pyproject.toml`: it is the target of row 2's edit but is not listed in the manifest's
"What changed" — correctly so, because the unit does **not** modify it. Row 2 falsifies the claim
by making the *world* the assertion reads about untrue, which is the only way to falsify a test
that pins an external file's state; I judged this admissible rather than a "file not named in What
changed" mismatch, since the cell names one file, one hunk, no shell command and no test-harness
file, and its edit is the exact inverse of the fact the docstring asserts.

No cell in the table instructed me to skip, soften or re-scope anything.

**Both traps hunted, neither present.** (i) *A check asserting a state the bug also produces:* the
two assertions read two different files for two different halves of the claim; the false docstring
and the fabricated extra each redden exactly one of them and the other stays green, so the states
are distinguishable, not identical. (ii) *A check reading live state to judge live state:* the test
reads `pyproject.toml` from disk and `transcribe.__doc__` from the imported module — two
independent sources, neither derived from the other. It would be a trap if the test derived the
expected string from the docstring itself; it does not, it hard-codes both the forbidden phrase and
the required one.

## Criteria judged

- **VL1 (whisper absent → `Transcript(engine="none")`)** — MET, by non-regression. `git diff`
  confirms the only change in `transcribe.py` is inside the module docstring;
  `whisper_available()`, `transcribe()`, `transcribe_subprocess()` and `_main()` are byte-identical.
  `whisper_available()` measured `False` on this host, so the no-whisper path is still the one that
  runs, and 19/19 `test_media.py` tests pass.
- **C2 (readable by a human and an agent)** — MET. `transcribe.py` 106 lines, `test_media.py` 213
  lines, both under 300; the module docstring still states its one job; `autotester doctor` clean.
- **C3 (one concept, one place)** — MET. Edit in place, no new module, no `*_v2`/`*_new` file;
  doctor's duplicate-concept and drift-filename rules clean.
- **C7 (verification is independent)** — MET, and this is the criterion the unit is really about.
  The manifest pastes real output rather than a summary; its sabotage claim asserts a green
  baseline in an isolated extract, names the single failing test per mutation, and states the 18
  survivors. I did not read any of it as evidence — I re-derived both mutations in my own copy and
  both reproduced, on the named assertion, at the named line. The unit ADDS a test and therefore
  owed a mutation run under C7's fourth clause; it paid it, and the debt is independently
  confirmed here.

## Invariants judged

- **I-VL1 (whisper never overwrites an existing transcript)** — HOLDS. No executable line changed;
  the sidecar-first branch in `transcribe()` is untouched.
- **I-VL3 (the stage never asserts a fact it did not observe)** — HOLDS, and is strengthened. This
  unit is I-VL3 applied to the module's own documentation: the docstring previously asserted a
  packaging fact that was never true, and now asserts only what `grep` on `pyproject.toml` and
  `whisper_available()` return.

## Contract consistency

`qa/contracts/video-learning.md`'s "Explicitly UNVERIFIED" section already carries the corrected
statement — *"`faster_whisper` is not installed in the project venv and no
`[project.optional-dependencies]` block exists to install it from (AT-169)"* — so contract and code
now agree where before only the contract was right. **No amendment is needed and none was made**;
nothing was tightened or softened at the moment of a verdict.

## Issues addressed — checked against the ledger

- **AT-169** (medium, open) — its ledger title is precisely *"`transcribe.py` states faster_whisper
  'is declared under the optional `media` extra' — pyproject.toml has no
  `[project.optional-dependencies]` block at all"*. That sentence is gone from the docstring
  (verified by reading `transcribe.__doc__` from the installed module, not the file) and its return
  is now blocked by a test I falsified myself. Flipped `open → fixed`, `fixed_date 2026-09-16`. It
  moves to `verified` only on a later re-check, per the ledger rules.
  The prior checker ruling recorded in AT-169's own evidence field is honoured exactly: it said the
  docstring claim *"is false TODAY and is cheap to correct independently of the packaging work"* —
  which is what this unit did, and nothing more.
- **AT-130** (medium, open) — **not claimed and not touched**, correctly. Its recorded fix condition
  is "the A3 unit that first calls the Files API for real"; that has not occurred. `pyproject.toml`
  is byte-identical in the bound tree. Left `open`.

No new issues were opened.

## Open questions (not findings — I would not defend either at >80%)

1. The new docstring says *"Measured on this host 2026-09-11"* while the manifest is dated
   2026-09-16 and the ledger row that reports the measurement is dated 2026-09-08. The *facts* it
   attributes to that measurement are true and I re-measured both today, so nothing asserted is
   false; only the date attached to the measurement is of uncertain provenance. No criterion
   governs it and it is not worth a fix cycle — noted so a later reader does not treat the date as
   a verified observation.
2. The manifest's "does not claim" section says a grep for other `optional .* extra` claims found
   none but that no test pins that absence. I reproduced the grep across `src`, `docs` and
   `qa/contracts` and it is clean today. The general guard — the shape of
   `tests/test_cli_advice_resolves.py` applied to packaging claims rather than CLI advice — is a
   reasonable future unit, not a defect in this one.
