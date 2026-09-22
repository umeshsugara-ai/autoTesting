# HUMAN_GATE — AT-554: credential VALUE served in the settings/env UI

**Opened:** 2026-09-22T19:24:00+05:30 · by checker Mode D live-browser validation
**Severity:** high · **Class:** credential-boundary / CRITICAL contract amendment
**Ledger:** AT-554 (qa/issues.jsonl) · **Evidence:** qa/evidence/browser-live-checker-2026-09-22-checker/report.json

## The question (one line)
`GET /settings/providers` and the per-project env editor serve the REAL saved credential value
(live GEMINI_API_KEY confirmed in the raw HTML/DOM). The contract says values are masked from
artifacts. Is this an accepted owner-only-local tradeoff, or a bug to fix?

## Why only the human decides
Weakening a safety invariant (the credential boundary — `core-invariants.md:47`,
`browser-and-secrets.md:59`) is a CRITICAL amendment under the Lab Protocol: it needs an
`Approved-by: Umesh` DECISIONS entry, decided away from any pending verdict. The checker may not
soften a criterion to fit the artifact.

## Options
- **A — ACCEPT** (value-visible, owner-only local editor): write a DECISIONS entry
  (`Approved-by: Umesh`) authorizing it, then amend `browser-and-secrets.md` + `core-invariants.md`
  to scope the boundary to *non-UI artifacts* and state the residual (value reaches HTTP responses,
  DOM, screenshots on the local UI only).
- **B — FIX** (restore F-026 "never-echo"): the settings + env editor render EMPTY inputs; the
  saved value never enters the response. Update `test_ui_settings.py::test_settings_page_shows_the_stored_value_masked`
  and `test_ui_env_editor.py` to assert value-absent.

## Answer format
Reply "A" or "B" (optionally with a note). On answer, append below:
`Answered: <ISO date> — <A|B> — <where>` — BEFORE any unit acts on it.

## Blocks
- Any unit touching `src/autotester/ui/routes_credentials.py` (settings/env editor rendering).
- The credential-boundary contract amendment.
Does NOT block: at541-543-ensemble-honesty (in flight), other non-UI-credential units.

Answered:
