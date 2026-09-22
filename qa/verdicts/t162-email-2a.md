# Verdict — t162-email-2a (T-162 phase-2a, EMAIL source adapter)

**Checker:** claude-sonnet-subagent (fresh context, read-only), dual check PRIMARY.
**Date:** 2026-09-23. **Cycle checked:** 1 (manifest's Fix cycle: 1 of 3).
**Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035), criteria SA1–SA6 as they apply
to EMAIL. `core-invariants.md` C1/C2/C3/C7/C10 also judged. `ingest.md` read; no criterion
there applies (this unit touches no `stages/ingest.py` code).

## What I re-ran myself

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py tests/test_source_adapters_audio.py tests/test_source_adapters_email.py tests/test_schema.py tests/test_store.py -v`
   → `52 passed in 0.78s` — matches the manifest's pasted output exactly (11+8+5+11+17).
2. `uv run ruff check src tests scripts` → `All checks passed!` — matches.
3. `uv run autotester doctor` → `doctor: clean` — matches.
4. Unscoped `PYTHONUTF8=1 uv run pytest` (whole repo, no path filter, launched in background
   because of its length on this shared machine): **`1562 passed, 5 skipped, 32 xfailed, 1
   warning in 629.14s`, exit 0.** A whole-log `grep -nE "FAILED|ERROR|^E "` found zero hits.
   Consistent with the prior unit's baseline of 1557 passed (`t162-audio-1b`'s verdict) plus
   this unit's 5 new EMAIL tests. The manifest promised to fold this in but never did (only one
   commit touches the manifest); re-run independently here per the dispatch's instruction —
   not a finding, since C7's Verify clause is satisfied by my own run regardless of the
   manifest's own follow-through.

## Criteria judged

- **SA1 (one evidence model, no second store):** PASS. `enums.py:12` adds `EMAIL = "email"`
  and nothing else defines `SourceKind`; `grep -rn "SourceKind.EMAIL" src/` hits only
  `email_register.py:106,133` (construction sites) — the enum itself lives solely in
  `schema/enums.py`. Every EMAIL/attachment row lands in the same `Source` model /
  `sources.jsonl` via `store.add_source`, and `store.list_sources()` shows the child DOC
  source landing in the SAME store in the reproduced attachment row below — no second store.
- **SA2 (content-addressed dedupe):** PASS. `_register_email_message` dedupes on the
  message's own sha256 via the existing `_existing_by_digest` (unchanged from phase-1a);
  attachments dedupe independently on their own bytes the same way. Reproduced live (row 4
  below).
- **SA3 (no mailbox credentials, local files only):** PASS, confirmed structurally.
  `grep -rniE "imap|smtp|poplib|ftplib|urllib.request|requests\.|httpx|socket\."` over
  `sources/email.py` and `sources/email_register.py` returns only the docstrings that state
  the absence — no import, no call. `email.message_from_bytes`/`mailbox.mbox` operate purely
  on bytes already read from local `Path` objects; nothing in either module opens a network
  socket or reads a credential. `assert_no_raw_secrets`'s gate on any model call is inherited
  unchanged: EMAIL never calls a provider itself, and an audio attachment routes through the
  existing `register_audio` → `sources.audio` path, whose SA3 gate was independently verified
  in `qa/verdicts/t162-audio-1b.md` and is untouched by this unit's diff (the only change to
  `register_audio` is the additive `provenance` kwarg, confirmed in the diff below).
- **SA4 (provenance-tracked, no schema change):** PASS. `schema/base.py:20-41` (`Provenance`,
  `Artifact.provenance`) is **byte-identical** in the diff — not touched at all by this unit.
  `Source` (`schema/project.py:97`) has no separate parent/child field; `grep -n "parent"
  src/autotester/schema/project.py` returns nothing. `register_document`/`register_audio`
  each gained one new keyword-only `provenance: Provenance | None = None` parameter, passed
  straight into the existing `Source(...)` construction — confirmed in the diff, no new
  mechanism. Reproduced live: an attachment's `child.provenance.produced_by ==
  "sources.email"` and `child.provenance.inputs == [parent.id]` (row 2 below).
- **SA5 (honest degradation, never silent):** PASS. Reproduced live for the corrupt-message
  case (row 5 below), independently confirming the manifest's claim that the RED output shows
  a **real stdlib `email.errors.CloseBoundaryNotFoundDefect`**, not a simulated error string —
  `parse_eml_bytes` catches whatever `email.message_from_bytes` raises under
  `policy.default.clone(raise_on_defect=True)` and stringifies `type(exc).__name__`, so the
  defect class in the failure output is genuinely the stdlib's own, not authored text. The
  unparseable-mbox and unrecognised-attachment honest defaults (`_register_unparseable_mbox`,
  `_register_unrecognised_attachment`) were read structurally rather than separately
  mutation-tested — consistent with the manifest, which does not claim them as their own
  capability rows either, and neither is contract-required to be its own row.
- **SA6 (model NAMES, never DECIDES):** PASS. Attachment dispatch to
  `register_document`/`register_audio`/`_register_unrecognised_attachment` in
  `_register_email_attachment` (`email_register.py:162-174`) branches purely on
  `written.suffix.lower() in DOC_SUFFIXES` / `AUDIO_SUFFIXES` — a static set membership
  check, never a model call. No model is invoked anywhere in `sources/email.py` or
  `sources/email_register.py` (confirmed by reading both files in full — no `Provider` call
  site in either). The only place a model could run for an EMAIL-originated row is the
  reused, unmodified `register_audio` path, whose "NAME not DECIDE" boundary was verified in
  the prior AUDIO unit and is not touched here.

## Capability coverage — 5/5 rows independently reproduced

Reproduced in **5 separate throwaway copies** outside the bound tree (`<scratch>/t162-email-2a-row1..5`
— `src/`+`tests/`+`scripts/`+`pyproject.toml`+`uv.lock`+empty `README.md` copied, `.venv` shared
via a directory junction to the bound tree's own `.venv` — never the bound working tree, never
edited in place there; `git status --short` in the bound tree confirmed clean throughout). Each
row: green before (`5 passed`, from the copy, not carried over from step 3) → single-hunk edit
exactly as the manifest's cell describes → red for the **named** reason → revert → green again
(re-confirmed per-row after every revert, all 5 rows `5 passed`).

| Row | Edit applied | Result |
|---|---|---|
| email-body→Source | `text=parsed.body_text,` → `text=None,` | GREEN→RED: `test_email_body_becomes_a_source` — `AssertionError` on `result.source.text == "The submit button is broken.\n"` (collaterally also reddened `test_mbox_with_two_messages...` since both bodies route through the same line — expected, not a wrong-reason failure) — **exact match** |
| attachment→child-DOC-Source | `provenance=provenance` → `provenance=None` in the `register_document(...)` call | GREEN→RED: `test_email_attachment_becomes_child_doc_source` — `AssertionError: assert None is not None` on `child.provenance is not None` — **exact match** |
| mbox-multi-message | `for raw in raw_messages` → `for raw in raw_messages[:1]` | GREEN→RED: `test_mbox_with_two_messages_becomes_two_email_sources` — `AssertionError: assert 1 == 2` — **exact match** |
| SA2-dedupe | `if existing is not None:` → `if False and existing is not None:` | GREEN→RED: `test_email_dedupes_same_bytes_registered_twice` — `AssertionError: assert True is False` on `second[0].created` — **exact match** |
| SA5-corrupt-extraction_error | `f"{_EXTRACTION_ERROR_PREFIX}: {parsed.error}"` → `f"unreadable: {parsed.error}"` | GREEN→RED: `test_corrupt_eml_registers_with_extraction_error_not_empty` — `AssertionError: assert False` on `.startswith("extraction_error")`, notes read `'unreadable: CloseBoundaryNotFoundDefect: '` — the real stdlib defect class is visible in the RED output, confirming the manifest's claim it is not simulated — **exact match** |

No row survived; no row required a broken-copy caveat.

## Diff scope (C10)

`git diff 564d732...HEAD --stat`: 8 files, 760 insertions / 16 deletions — matches the
manifest's file list exactly (`docs/MAP.md`, `schema/enums.py`, `sources/__init__.py`,
`sources/adapters.py`, two new files, the new test file, plus its own manifest).
`schema/enums.py`'s only non-additive hunk is the `BLOCKED_NO_ACTIONS` docstring: read the
full diff — it is a **reword** (4 lines → 3, same two sentences, same meaning: "AT-242: the
frontier emptied..." / "Distinct from COMPLETED... and LOGIN_FAILED..."), not a deletion of
behaviour or of the enum member itself. `sources/adapters.py`'s diff is purely additive
(`provenance` kwarg + docstring updates on `register_document`/`register_audio`/
`_add_audio_source`, all existing call sites' behaviour unchanged since the new parameter
defaults to `None`). `sources/__init__.py`'s diff only adds exports. No file outside the
manifest's "What changed" is touched, and no existing function, class, export, test, or
config key is deleted or renamed. Unit commit `53adcc8` (`git show --name-only`) carries
exactly: `docs/MAP.md`, `qa/manifests/t162-email-2a.md`, `src/autotester/schema/enums.py`,
`src/autotester/sources/__init__.py`, `src/autotester/sources/adapters.py`,
`src/autotester/sources/email.py`, `src/autotester/sources/email_register.py`,
`tests/test_source_adapters_email.py` — its own paths only, satisfying C10.

## File-length rule (C2)

`enums.py` 300 lines, `email.py` 126 lines, `email_register.py` 219 lines, `adapters.py` 221
lines, `__init__.py` 45 lines, `test_source_adapters_email.py` 157 lines — all within the
doctor's 300-line ceiling, confirmed by `wc -l` independently of the manifest's own count and
by `doctor: clean`.

## Decisions surfaced — judged

1. **Reused `Artifact.provenance` rather than inventing a parent/child field.** Confirmed:
   `schema/base.py` is untouched in this diff; `Provenance.inputs: list[str]` already existed
   and is already used elsewhere (`stages/run_case_pipeline.py:41`, per the manifest, not
   independently re-verified here since SA4 is already reproduced live). Correct call — no
   schema decision was actually needed.
2. **`email_register.py` split out of `adapters.py`.** Matches the existing `audio.py`/
   `adapters.py` split precedent; both new files stay well under 300 lines individually and
   the split is disclosed, not silent.
3. **Unrecognised attachment → `SourceKind.DOC` + `extraction_error`, no new `IMAGE` kind.**
   Consistent with SA1's "new `SourceKind` values are added deliberately, not speculatively"
   — no criterion requires a dedicated kind for an unread attachment type.
4. **HTML-only bodies stored raw, not stripped.** Honest, disclosed scope choice; no SA
   criterion requires HTML→text normalisation.
5. **Attachment dedupe is per-attachment-bytes, independent of the referencing message.**
   Matches phase-1's existing DOC/AUDIO dedupe behaviour; not a new decision.

None of the five require a criticality-gated contract amendment or a human gate; all are
routine, disclosed scope calls within the contract as written.

## Live browser

**Not applicable.** Changed/added paths: `schema/enums.py`, `sources/email.py`,
`sources/email_register.py`, `sources/adapters.py`, `sources/__init__.py`,
`tests/test_source_adapters_email.py`, `docs/MAP.md` (generated) — no route, template, or
`ui/` file. Confirmed independently from the diff stat above, not from the manifest's
assertion.

## Delegation

Manifest carries no `Executor:` field naming an external model → default
`claude-sonnet-subagent` applies; no `qa/delegation-ledger.jsonl` dispatch-row check needed.

## /goal wiring

**T-162 stays `pending`, not closed.** T-162's title spans Drive + video + audio + document +
email + text; this unit's own manifest states it completes only the **EMAIL** half of phase-2
— DRIVE (OAuth device flow) remains phase-2b, a separate, unbuilt unit. Closing T-162 now would
misreport DRIVE as done. No `goal_cli.py done` call made.

## Issues

None found. No new `qa/issues.jsonl` rows written; nothing in the ledger's existing open rows
names this unit or a defect in `sources/email*.py`.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (SA1-SA6), 5/5 core-invariants held (C1, C2, C3, C7, C10)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (no route/template/ui/ path touched — schema/enums.py, sources/email.py, sources/email_register.py, sources/adapters.py, sources/__init__.py, tests/test_source_adapters_email.py, docs/MAP.md)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All 5 claimed capability rows reproduced independently in throwaway copies with the exact same failure reason the manifest states, including SA5's real (not simulated) stdlib CloseBoundaryNotFoundDefect. SA3's no-credential-surface claim and SA4's provenance-reuse-not-schema-change claim were both independently confirmed by reading the diff and grepping for network/credential imports, not by trusting the manifest's prose. Diff scope is additive plus one reworded docstring (no deletion), all files within the 300-line ceiling, and the unit commit carries only its own paths (C10). Targeted 52-test suite, ruff, and doctor all re-ran clean; an unscoped whole-repo run (1562 passed, 5 skipped, 32 xfailed, exit 0) found zero regressions. T-162 stays pending since DRIVE (phase-2b) is not yet built.
```
