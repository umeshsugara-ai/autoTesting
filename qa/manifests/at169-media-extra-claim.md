# Manifest — at169-media-extra-claim

**Unit:** AT-169 — `transcribe.py`'s docstring claims a `media` extra that does not exist
**Contract:** `qa/contracts/video-learning.md` (VL1 — the no-whisper path), core-invariants C2/C7
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-169 (medium)

## What was wrong

`src/autotester/media/transcribe.py`'s module docstring said:

> Measured on this host 2026-09-08: `faster_whisper` is **not installed in the project venv**
> (it is declared under the optional `media` extra).

`pyproject.toml` has **no `[project.optional-dependencies]` block at all** — there is no `media`
extra, and never was one. The docstring told a reader that enabling whisper was one
`uv sync --extra media` away, when in fact nothing in the packaging declares `faster_whisper`.

This is the cheap half of a pair. Its sibling AT-130 (`google-genai` imported but undeclared) is
explicitly **gated** by a prior checker ruling to "the A3 unit that first calls the Files API for
real" and is NOT touched here. The same ruling separates this one: *"AT-169's docstring claim is
false TODAY and is cheap to correct independently of the packaging work."*

## What changed

- `src/autotester/media/transcribe.py` lines 15–22 (module docstring only) — the false claim is
  replaced with the measured truth: `faster_whisper` is not in the venv **and** `pyproject.toml`
  carries no `[project.optional-dependencies]` block at all, so there is no extra to install it
  from. The correction names AT-169, records that a prior version of the docstring claimed
  otherwise, and points the packaging work at AT-130's sibling unit rather than silently dropping
  it.
- `tests/test_media.py` — one new test, `test_no_media_extra_is_falsely_claimed_to_exist`, pinning
  **both** halves of the true state so the claim cannot drift back: `pyproject.toml` contains no
  `[project.optional-dependencies]`, and the docstring does not contain the phrase
  `optional \`media\` extra` while it does contain the corrected wording.

**No behaviour changed.** Not one line of executable code was touched — the diff is a docstring and
a test. `whisper_available()`, `transcribe()`, and the `engine="none"` fallback are byte-identical.

## What this unit does not claim

- **It does not declare `faster_whisper` as a dependency or add a `media` extra.** That is packaging
  work, gated with AT-130 to the unit that first calls a model for real. This unit's whole point is
  that the docs should stop claiming work that has not been done.
- It does not verify that `faster_whisper` *would* install if an extra existed.
- It does not audit any other module's docstring for similar false claims (a grep for other
  `optional .* extra` claims found none, but no test pins that absence).

## Capability coverage

| Capability claimed | Check that isolates it | Falsifying edit (single hunk, single file) | Result |
|---|---|---|---|
| The false `media`-extra claim cannot return to the docstring | `tests/test_media.py::test_no_media_extra_is_falsely_claimed_to_exist` | In `src/autotester/media/transcribe.py`, replace the corrected docstring paragraph (lines 15–22) with the pre-fix text ending `(it is declared under the optional \`media\` extra)` | **Reddens** — `AssertionError: the false extra claim is back` at `tests/test_media.py:212`; every other test in the file stays green |
| The docstring's claim about `pyproject.toml` is pinned to the real file, not restated prose | same test, first assertion | In `pyproject.toml`, append `[project.optional-dependencies]` / `media = ["faster-whisper>=1.0"]` | **Reddens** — `assert '[project.optional-dependencies]' not in ...` at `tests/test_media.py:209`; every other test in the file stays green |

Both edits fail on the assertion the test is named for — neither breaks parsing, importing or
collection, so nothing reddens for free.

## How to verify (commands + expected)

- `uv run pytest tests/test_media.py -q` → expected: exit 0, 19 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0, `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- Grounding the claim itself:
  `grep -n "optional-dependencies\|faster_whisper\|faster-whisper" pyproject.toml` → expected: **no
  matches** (this is the fact the docstring now states)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_media.py -q
...................                                                      [100%]  (19 passed)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ grep -n "optional-dependencies|faster_whisper|faster-whisper|\[project\]" pyproject.toml
1:[project]
(no other match — no optional-dependencies block, no faster_whisper anywhere)

$ uv run pytest -q
EXIT: 0
```

Note on the full suite: `tests/test_mutation_check.py` is a **known pre-existing flake** (AT-357,
still open) — it races concurrently-running `mutation_check.py` processes through a shared-temp-dir
glob. It is unrelated to this unit, which touches neither file.

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline):**

1. `git archive HEAD | tar -x` into a scratchpad extract; layered this unit's two edited files on.
2. `uv sync`; confirmed `autotester.__file__` resolves **inside the extract**
   (`...\at169-extract\src\autotester\__init__.py`), so the venv is genuinely isolated.
3. Baseline in the extract: `uv run pytest tests/test_media.py -q` → **19 passed**, exit 0.
4. Mutation 1 (docstring reverted to the false claim) → **exactly one test failed**,
   `test_no_media_extra_is_falsely_claimed_to_exist`, on `assert "optional \`media\` extra" not in doc`
   with the message `the false extra claim is back`. 18 others green.
5. Restored, then Mutation 2 (a real `[project.optional-dependencies]` block appended to
   `pyproject.toml`) → **the same single test failed**, this time on the first assertion
   (`assert '[project.optional-dependencies]' not in pyproject`). 18 others green.
6. Extract deleted; live tree confirmed to carry only the two real edits
   (`git status --porcelain` on the three paths shows `M transcribe.py`, `M test_media.py`,
   `pyproject.toml` untouched).

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths:
`src/autotester/media/transcribe.py` (docstring only), `tests/test_media.py` (one added test).
No route, template, JS or rendered output is reachable from either.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at169-media-extra-claim.md`, commit 39e0879; ledger AT-169 open → fixed in 5c3d036)
