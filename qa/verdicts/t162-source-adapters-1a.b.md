# Verdict — t162-source-adapters-1a (INDEPENDENT DUAL CHECK, .b)

**Date:** 2026-09-22
**Checker:** claude-sonnet-subagent (fresh context, second/independent checker of the dual check;
never read `qa/verdicts/t162-source-adapters-1a.md` or its history)
**Cycle checked:** 1
**Bound to:** `D:/autoTesting/.worktrees/t162-source-adapters-1a`
**Scope:** T-162 phase-1a — source-adapter seam + TEXT + DOC only (SA1, SA2, SA4, SA5, SA6 judged;
SA3 not applicable — no credential surface in phase-1a; AUDIO/DRIVE/EMAIL out of scope, contract
itself still DRAFT so no contract-maintenance action was taken by this checker)

## What I re-ran myself

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py -v` → `11 passed in 0.17s`. Matches.
2. `PYTHONUTF8=1 uv run pytest tests/test_schema.py tests/test_store.py tests/test_ingest.py` →
   `36 passed in 0.32s`. Matches.
3. `uv run ruff check src tests scripts` → `All checks passed!`. Matches.
4. `uv run autotester doctor` → `doctor: clean`. Matches.
5. Full suite, bare `uv run pytest` (PYTHONUTF8=1, no CLI `-q` per AT-503, whole-log scanned for
   `FAILED`/`ERROR`/`^E`, none found): `1549 passed, 5 skipped, 32 xfailed, 1 warning in 643.97s`.
   Clean.

## Diff scope (step 4c)

`git diff 1ed605b...HEAD --stat`: 8 files changed, **538 insertions(+), 0 deletions**. Every touched
path is one the manifest's "What changed" names: `src/autotester/sources/{__init__,adapters,extract}.py`
(new), `tests/test_source_adapters.py` (new), `tests/fixtures/sample_doc.{md,txt}` (new),
`docs/MAP.md` (generated, +2 lines adding the two new module rows). Nothing renamed, nothing
deleted, no file touched outside the declared set. C10 clean.

`schema/enums.py` was **not** touched in this diff — confirmed by reading the file directly:
`SourceKind.DOC`/`SourceKind.TEXT` already exist at `enums.py:9-11`, predating this unit. SA1's "no
enum change was needed" claim is correct on inspection, not merely asserted.

## Capability coverage — reproduced independently in 4 throwaway copies

Used `git archive HEAD | tar -x` into 4 separate scratch dirs outside the bound tree (never a
baseline extraction — `HEAD` here is the post-change state, same as step 3's verify), `uv sync
--frozen` in each (fast, fully cached), confirmed **green** on the named test(s) in the COPY before
any edit, applied the manifest's single-hunk edit to the single named file, re-ran, reverted nothing
in the bound tree (all edits were in throwaway copies only).

| Row | File:hunk | Green-before (copy) | Red-after (copy) | Verdict |
|---|---|---|---|---|
| TEXT-verbatim | `adapters.py` `text=text` → `text=text[:-1]` | `1 passed` | `AssertionError` at `test_source_adapters.py:54` — `'…Second line'` != `'…Second line.'` | REPRODUCED, right reason |
| DOC-extract | `extract.py` `"\n".join(paragraphs)` → `"".join(paragraphs)` | `1 passed` | `AssertionError` at `:84` — paragraphs concatenated with no separator | REPRODUCED, right reason |
| SA2-dedupe | `adapters.py` `if existing.sha256 == digest:` → `… and False:` | `2 passed` | Both named tests `AssertionError: assert True is False` at `:108`/`:121` (`.created` True on the second call) | REPRODUCED, right reason |
| SA5-honest-degradation | `adapters.py` note-assembly line → `note = None` | `3 passed` | All 3 named tests `AssertionError: assert None is not None` on `.notes` at `:161`/`:149`/(corrupt-doc row) | REPRODUCED, right reason |

4/4 rows reproduced; assertion lines match the manifest's table exactly. No row survived; no row
isolated the wrong assertion (each mutation reddened only the test named for it, verified by running
only the named test(s), not the whole file).

## Criteria judged (SA1–SA6, phase-1a scope: TEXT + DOC)

- **SA1 — one evidence model, no second store.** `register_text`/`register_document` both call
  `store.add_source`, which appends to `self.paths.sources_index` (`sources.jsonl`) —
  `project_store.py:66-74`, the same file/method VIDEO's `register_source` uses. No new enum value
  added; `SourceKind.TEXT`/`DOC` pre-existed. **MET.**
- **SA2 — content-addressed dedupe.** sha256 of UTF-8 bytes (TEXT) / file bytes (DOC), `_existing_by_digest`
  reads `list_sources()` fresh from disk, second call returns `created=False` with the same source id.
  Falsified and reproduced (table above). **MET.**
- **SA4 — provenance cites the Source id.** `test_extracted_doc_is_addressable_by_its_source_id`
  confirms `result.source.id == store.list_sources()[0].id`; `Source.model_post_init` mints a
  content-addressed id (`content_id("src", …)`) unconditionally, so every adapter-produced Source
  carries a stable id a future citer (T-163) can reference. This is the correct bar for phase-1a —
  T-163 (the actual citer) is explicitly out of scope for this unit and this contract. **MET at
  this unit's scope.**
- **SA5 — honest degradation, never silent empty text.** Corrupt zip, DOCTYPE-bearing XML, and
  `.pdf` (undeclared dependency) all register with `text=None` and a `notes` string starting
  `extraction_error`, never a silently-empty `text=""`. Falsified and reproduced. **MET.**
- **SA6 — a model may NAME, never DECIDE.** Read `adapters.py` and `extract.py` in full: neither
  `register_text` nor `register_document` nor any function in `extract.py` constructs, imports, or
  accepts a `Provider`/model client — structurally cannot call a model. No provider import in
  either file (`grep` of both files: no `provider`/`genai`/`anthropic` reference). **MET.**
- **SA3 — not applicable.** Phase-1a is TEXT + DOC only; no credential surface exists in either
  path (no Drive OAuth, no mailbox). Correctly out of scope per the contract's own phase split.

## Contract status

The contract (`qa/contracts/source-adapters.md`) is still marked `Status: DRAFT` at its header,
approved only via the informal gate-answer chat referenced in the manifest. Per this dispatch's
explicit instruction ("Do NOT touch the contract"), I have made **no edit** to it and I am not the
one finalizing/D-entry-ing it — that is left to the primary checker or a human step, and I flag it
here as an open item rather than silently assuming someone else handled it.

## Issues found

None. No FAILURES to report. (Per dispatch, not writing to `qa/issues.jsonl` — the primary checker
owns the ledger for this dual check.)

## Live browser

Not UI-touching. Changed paths are `src/autotester/sources/*`, `tests/test_source_adapters.py`,
`tests/fixtures/sample_doc.{md,txt}`, `docs/MAP.md` (generated) only — no route, template, or `ui/`
file touched, confirmed directly from the diff (not merely the manifest's claim).

---

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (SA1, SA2, SA4, SA5, SA6), SA3 not-applicable (phase-1a scope)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: not-applicable (src/autotester/sources/*, tests/test_source_adapters.py, tests/fixtures/sample_doc.{md,txt}, docs/MAP.md — no UI surface touched)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All four verify commands and the full suite reproduced clean with no FAILED/ERROR in
the whole-log scan; all four capability-coverage rows independently falsified and reddened for the
named reason in throwaway copies outside the bound tree; the diff adds only the declared files with
zero deletions. SA1-SA2/SA4-SA6 are met on direct code inspection, not just the manifest's claim; SA3
is out of scope for phase-1a. Sole open item: the contract is still formally DRAFT and this checker
made no contract-maintenance edit per its dispatch instruction — that step is still owed by someone.
```
