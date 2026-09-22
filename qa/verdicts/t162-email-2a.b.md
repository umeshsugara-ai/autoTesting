# Verdict — t162-email-2a (INDEPENDENT DUAL CHECK, checker B)

**Date:** 2026-09-23
**Cycle checked:** 1
**Bound root:** `D:/autoTesting/.worktrees/t162-email-2a`
**Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035), EMAIL phase-2a row, SA1-SA6, plus
`core-invariants.md` (all) and `ingest.md` (checked for overlap/duplication — none found).
**Role:** second, independent checker of a CRITICAL dual check (credential-boundary criterion
SA3). This verdict was formed with no access to the primary checker's verdict file or reasoning.

## What I re-ran myself

- `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_source_adapters_email.py tests/test_schema.py tests/test_store.py -v`
  → `52 passed in 0.80s` (matches manifest's pasted output).
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- Full-suite (`uv run pytest`, bare, no `-q` per AT-503) run to completion myself (manifest had
  only launched it in the background and implied it clean): **`1562 passed, 5 skipped, 32
  xfailed, 1 warning in 624.35s`** — 0 failures, real summary line present (not a dots-only log).
- `git diff 564d732...HEAD --stat` — 8 files changed, matches the manifest's "What changed" list
  exactly (`docs/MAP.md`, `qa/manifests/t162-email-2a.md`, `schema/enums.py`,
  `sources/__init__.py`, `sources/adapters.py`, `sources/email.py` [new],
  `sources/email_register.py` [new], `tests/test_source_adapters_email.py` [new]). Full diffs of
  `enums.py`, `adapters.py`, `sources/__init__.py` read line-by-line: no function, class, test, or
  export was deleted or renamed; the only "removal" is the `BLOCKED_NO_ACTIONS` docstring reword
  (4 lines → 3 lines, same meaning, done to hold `enums.py` at exactly 300 lines) — confirmed a
  genuine reword, not a content loss. C10 holds; not-UI-touching confirmed independently from the
  changed-paths list (no `ui/`, no route, no template).

## Capability coverage — independently reproduced (throwaway copy, outside the bound tree)

Copied the worktree to a scratch dir outside `D:/autoTesting`, confirmed the named test green in
the COPY first (`5 passed`), then applied each manifest-claimed single-hunk edit to
`sources/email_register.py`, re-ran only the named test, captured the RED, reverted, and
re-confirmed green before the next row. All edits were single-file (`email_register.py`),
single-hunk, exactly as the manifest cells state.

| Row | Edit applied | Result |
|---|---|---|
| email-body→Source | `text=parsed.body_text,` → `text=None,` | RED: `assert None == 'The submit button is broken.\n'` — same assertion named |
| attachment→child-DOC-Source | `provenance=provenance` → `provenance=None` in the `register_document(...)` call | RED: `assert None is not None` at `child.provenance is not None` |
| mbox-multi-message | `for raw in raw_messages` → `for raw in raw_messages[:1]` | RED: `assert 1 == 2` |
| SA2-dedupe | `if existing is not None:` → `if False and existing is not None:` | RED: `assert True is False` (dup created) |
| SA5-corrupt-extraction_error | `f"{_EXTRACTION_ERROR_PREFIX}: ..."` → `f"unreadable: ..."` | RED: `.startswith("extraction_error")` fails; note read `'unreadable: CloseBoundaryNotFoundDefect: '` — **confirms the corrupt-`.eml` test trips a real stdlib `email` defect class (`CloseBoundaryNotFoundDefect`), not a simulated one** |

5/5 rows reproduced. Every RED fired on the exact assertion the row names — no wrong-reason
failures (parsing/import breakage that would redden everything). Full 5-test file re-confirmed
green after each individual revert, and the 52-test six-file suite green after the final revert.
(The copy's post-revert `email_register.py` differs from the original only in line endings —
CRLF vs LF from my own `open()`/`write()` round-trip in the scratch copy, byte-diff confirmed
content-identical; the bound tree itself was never touched.)

CAPABILITY-COVERAGE: 5/5 rows reproduced.

## Criteria judged

- **SA1 (one evidence model, no second store):** `SourceKind.EMAIL = "email"` added only in
  `schema/enums.py:12`, nowhere else (grepped). `register_email` writes through
  `store.add_source(Source(...))` — the same `ProjectStore`/`sources.jsonl` DOC/AUDIO/TEXT already
  use. Attachments go through the **existing, unmodified** `register_document`/`register_audio`
  extraction logic (only a new optional kwarg was added, verified below) — no re-implementation.
  **Met.**
- **SA2 (content-addressed dedupe):** sha256 keyed dedupe on message bytes AND independently on
  attachment bytes (`_existing_by_digest`); reproduced live above (row 4). Unparseable-mbox path
  also dedupes on the whole file's digest. **Met.**
- **SA3 (no mailbox/IMAP credential surface):** read `sources/email.py` and
  `sources/email_register.py` in full — only `email`, `email.policy`, `mailbox`, `hashlib`, `re`,
  `pathlib` and in-repo imports. `grep -n "IMAP\|SMTP\|imaplib\|smtplib\|poplib\|credential"` over
  both files returns only the modules' own doc-comments asserting the absence — zero functional
  hits. `mailbox.mbox(path, create=False)` and `email.message_from_bytes` operate on local bytes
  only; no network call, no `SecretRef`, no credential parameter anywhere in the EMAIL path. **Met
  — this is the criterion the dual check exists for, and it holds on direct code inspection, not
  just the docstring's claim.**
- **SA4 (extraction is provenance-tracked):** `Provenance` (`schema/base.py:20-27`,
  `produced_by`/`inputs: list[str]`) is a pre-existing field on every `Artifact`, already used
  independently of this unit at `stages/run_case_pipeline.py:41,77` — confirmed by direct read, not
  the manifest's assertion. `register_document`/`register_audio` each gained one
  **keyword-only, default-`None`** parameter `provenance: Provenance | None = None`; every other
  line of their extraction logic is untouched (diff read in full, above). An attachment gets
  `Provenance(produced_by="sources.email", inputs=[parent.id])`. No new parent/child field
  invented. **Met.**
- **SA5 (honest degradation, never silent):** three independent honest-default paths all verified
  by direct read + the row-5 reproduction: (i) a structurally malformed `.eml` — caught via
  `email.policy.default.clone(raise_on_defect=True)`, confirmed to trip a genuine stdlib defect
  class, never a fake empty reading; (ii) a `.mbox` yielding zero messages registers ONE
  `extraction_error` Source keyed on the whole file's digest, not silent nothing; (iii) an
  attachment neither DOC- nor AUDIO-shaped still registers, as `SourceKind.DOC` carrying an
  `extraction_error` note, never dropped. **Met.**
- **SA6 (model NAMES, never DECIDES):** the EMAIL path itself (`email.py`, `email_register.py`)
  makes **no model/provider call at all** — `provider`/`secrets` are only threaded through
  unchanged to `register_audio` for an audio-shaped attachment, which is AUDIO's own existing
  Gemini/Whisper transcription (already governed by phase-1's SA6 compliance, not re-decided
  here). Nothing in the new code chooses what gets stored, extracted, or dropped based on a model
  output. **Met.**

## Core invariants

- **C1/C2/C3:** `doctor: clean` covers schema/file-length/duplicate-definition rules directly;
  `enums.py` sits at exactly 300 (the ceiling, not over); `email.py` 126 lines, `email_register.py`
  219 lines, `adapters.py` 221 lines — all under 300. No duplicate top-level names introduced
  (doctor's own check, re-run).
- **C7 (verification independence, mutation duty):** this unit adds a new test file — the
  capability-coverage table above IS the required mutation duty, and I re-ran it independently
  myself rather than trusting the manifest's paste; all 5 hunks killed for the named reason, none
  INCONCLUSIVE.
- **C8 (provider-agnostic):** no vendor SDK import in either new file (only stdlib `email`/
  `mailbox` plus in-repo imports) — `grep -rE "^(import|from) (anthropic|google)"` over
  `sources/email.py`/`email_register.py` returns nothing.
- **C10 (commit carries only this unit's paths):** working tree is clean (`git status --short`
  empty — unit already committed at `53adcc8`); `git diff 564d732...HEAD --stat` matches the
  manifest's declared file list exactly, no stray paths.

## Findings

None. No issue filed (per dispatch: the primary owns the ledger for this dual check).

```
VERDICT: PASS
SCOREBOARD: 6/6 SA criteria met, 10/10 relevant core-invariants hold (C1,C2,C3,C4,C5,C6,C7,C8,C9,C10 — no violation surfaced; C4/C6/C9 not implicated by this diff and found unaffected)
FAILURES (if any): none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (no route/template/ui/ path touched — changed paths: src/autotester/schema/enums.py, src/autotester/sources/email.py, src/autotester/sources/email_register.py, src/autotester/sources/adapters.py, src/autotester/sources/__init__.py, tests/test_source_adapters_email.py, docs/MAP.md)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All 6 SA criteria (SA1-SA6) verified against code I read myself, not the manifest's
prose — SA3 (the credential-boundary criterion this dual check exists for) holds on direct
inspection: zero IMAP/SMTP/mailbox-credential imports or parameters anywhere in the EMAIL path.
All 5 capability-coverage rows independently reproduced in a throwaway copy outside the bound
tree, green-before/red-for-the-named-reason/revert/green-after, including confirming SA5's
corrupt-.eml test trips a real stdlib email.errors defect class. Full suite re-run to completion
by me: 1562 passed, 0 failed. Diff scope clean — no deletions beyond a same-meaning docstring
trim, no files touched outside the manifest's declared list.
```
