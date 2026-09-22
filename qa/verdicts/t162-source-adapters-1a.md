# Verdict — t162-source-adapters-1a (Mode A, PRIMARY of dual check)

**Date:** 2026-09-22
**Cycle checked:** 1
**Checker:** claude-sonnet-subagent (fresh context, read-only toward the artifact)
**Project root (bound):** `D:/autoTesting/.worktrees/t162-source-adapters-1a`
**Unit commit:** 5e243b7 (base for diff scope: 1ed605b)

## What I re-ran

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters.py -v` → `11 passed` — matches manifest.
2. `PYTHONUTF8=1 uv run pytest tests/test_schema.py tests/test_store.py tests/test_ingest.py` →
   `36 passed` — matches manifest.
3. `uv run ruff check src tests scripts` → `All checks passed!` — matches manifest.
4. `uv run autotester doctor` → `doctor: clean` — matches manifest.
5. **Full-suite verify (`qa/adapter.json` slot-1, `uv run pytest` bare, no CLI `-q` per AT-503,
   `PYTHONUTF8=1`):** `1549 passed, 5 skipped, 32 xfailed, 1 warning in 658.16s`, exit 0.
   Whole-log scan (`grep -nE "FAILED|ERROR|^E |Traceback"`) → **zero matches**.

## Criteria judged (source-adapters.md SA1–SA6, TEXT/DOC scope only)

- **SA1 (one evidence model, no second store)** — MET. `store.add_source` writes only to
  `paths.sources_index` (`sources.jsonl`); `list_sources` reads the same file
  (`src/autotester/store/project_store.py:66-77`). No enum change was needed or made:
  `SourceKind.TEXT`/`SourceKind.DOC` already existed in `schema/enums.py:9-16`; `sources/adapters.py`
  imports that enum directly, no parallel enum defined anywhere in the diff.
- **SA2 (content-addressed dedupe)** — MET. `_existing_by_digest` (`adapters.py:108-118`) looks up by
  sha256 before every write; both `register_text` and `register_document` return `created=False` on a
  match. Tested (`test_same_bytes_register_once`, `test_same_pasted_text_registers_once`) and
  independently reproduced (capability row 3 below).
- **SA4 (provenance cites the Source id)** — MET for phase-1a's achievable scope: every registered
  Source carries a stable, content-derived `id` (`Source.model_post_init`,
  `schema/project.py:114-119`), asserted addressable via `store.list_sources()` in
  `test_extracted_doc_is_addressable_by_its_source_id`. The orchestrator that will actually cite it
  is T-163, out of scope here by the contract's own no-fire list.
- **SA5 (honest degradation, never silent)** — MET. `extract_document_text` (`extract.py:45-62`)
  catches every exception and returns `Extraction(None, error)`; `register_document` turns that into
  an `extraction_error:`-prefixed `Source.notes` with `text=None` (`adapters.py:89-92`). Verified for
  three degradation paths: corrupt-zip `.docx`, a DOCTYPE-bearing hostile `.docx` (XXE/entity-expansion
  guard, `extract.py:85-86`), and a `.pdf` (deferred — no dependency declared, matches the contract's
  open-question-#1 default). Tested and reproduced (capability row 4 below).
- **SA6 (a model may NAME, never DECIDE)** — MET, structurally. Confirmed by reading
  `src/autotester/sources/adapters.py` and `extract.py` in full: no import of any provider, vendor SDK,
  or `providers.base.Provider`; `register_text`/`register_document` take no provider/model argument at
  all, so nothing in this seam CAN call a model, not merely "doesn't today."
- **SA-table TEXT/DOC** — MET. TEXT stored byte-for-byte (`register_text`, no transformation);
  DOC extraction is deterministic host-side (stdlib `zipfile`+`xml.etree` for `.docx`, strict-UTF-8
  read for `.txt`/`.md`). Both tested and reproduced (capability rows 1–2 below).
- **SA3** — not applicable to this unit's scope (phase-1a has no credential surface; Drive/email
  credentials are phase-2, explicitly deferred).

## Capability coverage — 4/4 rows independently reproduced

Reproduced in a **throwaway copy** outside the bound tree (`src/`, `tests/`, `scripts/`,
`pyproject.toml`, `uv.lock`, `.python-version` copied; `.venv` reused via a Windows junction —
content-identical, never written to). The named check ran **green in the copy before every edit**
(`11 passed` on `tests/test_source_adapters.py`), confirming the copy is real, not a broken
extraction reading as a false red.

| Row | Edit applied (single hunk, single file) | Result in the copy | Matches manifest? |
|---|---|---|---|
| TEXT-verbatim | `adapters.py`: `text=text` → `text=text[:-1]` | RED — `test_text_is_stored_verbatim` fails at the manifest's assertion line 54 (`'Second line' != 'Second line.'`); only this test failed | Yes, exact reason |
| DOC-extract | `extract.py`: `"\n".join(paragraphs)` → `"".join(paragraphs)` | RED — `test_doc_extracts_docx_paragraph_text` fails at line 84 (no separator between paragraphs); only this test failed | Yes, exact reason |
| SA2-dedupe | `adapters.py` `_existing_by_digest`: `if existing.sha256 == digest:` → `... and False:` | RED — `test_same_bytes_register_once` (line 108) and `test_same_pasted_text_registers_once` (line 121) both fail, `second.created` True instead of False; no other test affected | Yes, exact reason |
| SA5-honest-degradation | `adapters.py`: the `note = (...)` ternary → `note = None` | RED — all three named defending tests fail (`test_corrupt_doc_registers_with_extraction_error_not_empty` line 135, `test_doctype_bearing_docx_is_refused_as_extraction_error` line 149, `test_pdf_degrades_honestly_without_a_dependency` line 161); no other test affected | Yes, exact reason |

Every edit was reverted after its red run; the copy's `adapters.py`/`extract.py` diffed byte-identical
against the bound tree's originals afterward, and the copy's suite returned to `11 passed`. **The
bound working tree was never touched** — all edits and reverts happened only in the throwaway copy.

## Diff scope (C10)

`git diff 1ed605b...5e243b7 --stat`: `docs/MAP.md` (+2, generated, additive), `qa/manifests/...` (new),
`src/autotester/sources/{__init__,adapters,extract}.py` (new), `tests/fixtures/sample_doc.{md,txt}`
(new), `tests/test_source_adapters.py` (new). 8 files, +538/-0. **No file was deleted, renamed, or had
an existing function/export/route/test/config key removed.** Every touched path is either listed in the
manifest's "What changed" or is the manifest's own file. No route, template, or `ui/` file appears in
the diff — the manifest's "not UI-touching" claim is confirmed from the diff itself, not from the
manifest's assertion, so **Mode D (live browser) does not apply**.

## Scope-collection check (5c)

Not applicable — this unit collects no external data; it is a schema/code seam plus two fixture files
authored by the unit itself, not sourced from a portal.

## Issues addressed

None claimed (new feature) — none to verify.

## Findings

None at >80% confidence. Nothing found warrants an `ISS-t162-1a-*` row.

## Contract finalization (owner action, PASS → finalize)

Per dispatch: on PASS, finalize `qa/contracts/source-adapters.md` from gate-A-approved DRAFT to
ACTIVE. Done as a **separate, narrow commit** from this verdict:
- `docs/DECISIONS.md` — appended **D-035** (ACTIVE) via `scripts/append_decision.ps1`, citing
  `qa/gates/t162-contract-approval.md` Option A (Umesh, chat, 2026-09-21) as authority.
- `qa/contracts/source-adapters.md` — header flipped DRAFT → ACTIVE, owner line updated, one
  amendment-log row added citing D-035 and this verdict. No SA1–SA6 wording, phasing, or no-fire
  list text changed.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (SA1, SA2, SA4, SA5, SA6, SA-table TEXT/DOC), 0/0 invariants (none
  apply beyond core-invariants, all separately confirmed: C1/C2/C3 via doctor clean, C7 via
  full-suite + capability-coverage reproduction, C8 via no-vendor-import read, C10 via diff scope)
FAILURES (if any): none
CAPABILITY-COVERAGE: 4/4 rows reproduced (TEXT-verbatim, DOC-extract, SA2-dedupe,
  SA5-honest-degradation) — all green-before/red-for-named-reason/revert/green-after in a throwaway
  copy outside the bound tree
LIVE-BROWSER: not-applicable (changed paths: src/autotester/sources/*, tests/test_source_adapters.py,
  tests/fixtures/sample_doc.{md,txt}, docs/MAP.md — no route/template/ui/ file touched)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (manifest names none; checker: claude-sonnet-subagent — self != executor N/A, same actor class, no ANTHROPIC_BASE_URL override)
EXPLANATION: All four manifest-claimed capability rows reproduced independently with the exact
  failure reasons and assertion lines claimed; the full 1549-test suite plus the unit's own tests
  ran clean end to end; the diff touches only phase-1a paths with no deletions (C10); SA6/no-model
  is enforced structurally (no provider parameter exists in the seam at all), not merely by
  convention. Contract finalized to ACTIVE via D-035 as the dispatch instructed on PASS.
```
