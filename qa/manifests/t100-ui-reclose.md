# Manifest — t100-ui-reclose

**Status:** ready-for-check  
**Contract:** `qa/contracts/ui.md` + `qa/contracts/ui-report.md` + `qa/contracts/core-invariants.md`  
**Goal task:** T-100 (`user_value: high`, reopened for truthful no-CLI closure)  
**Date:** 2026-09-10  
**Fix cycle:** 1  
**Implementation commit:** `c1f7cc0`  
**Issues addressed:** AT-244, AT-245, AT-246, AT-247, AT-248, AT-251, AT-252, AT-257, AT-259

## Submitted behavior

- Crawl authorization is now obtainable inside the UI. The server derives the project and exact
  crawl target; the operator supplies signer, scope, expiry, bounds, and note. Browser-local expiry
  is converted to the exact UTC instant using the offset for the selected date, including DST changes.
- Crawl bounds shown in the form are the exact `CrawlBounds` object used by preflight and execution.
  Invalid bounds, missing/expired authorization, unknown crawls, and FlowSpec review refusals render
  themed recovery pages instead of raw JSON or CLI instructions.
- Dashboard/report run discovery accepts only valid persisted `Run` envelopes and sorts their
  timezone-normalized `created_at` values newest-first. Report totals and pass rate come from the
  selected latest run and its real case ids.
- Screenshot embedding is confined to the trusted project/run/crawl roots. Absolute paths,
  traversal, file symlinks, directory symlinks, and Windows junction escapes are rejected.
- Consent expiry comparisons normalize naive and aware datetimes to UTC, and the default clock is UTC.

## Verification commands the checker must re-run

```text
uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-t100-checker -q
uv --cache-dir .work/uv-cache run ruff check src tests scripts
uv --cache-dir .work/uv-cache run autotester doctor
git diff --check c1f7cc0^ c1f7cc0
```

Expected: pytest exit 0 (two platform skips are expected), Ruff clean, committed diff clean.
`autotester doctor` is expected to report only the unrelated untracked root `AGENTS.md`; verify the
committed tree in a clean `git archive` to prove the T-100 artifact itself is doctor-clean.

## Required independent browser check (Mode D)

Drive a fresh visible browser against the implementation in `c1f7cc0`; do not reuse maker evidence.
At minimum, interact with and verify:

1. `/projects/checkerdemo/sources`: expired/missing crawl approval produces a themed refusal with an
   in-UI recovery link and no CLI command.
2. `/projects/checkerdemo/crawl-approval`: exact target is read-only, all four bounds are visible,
   and the browser UTC-offset field reflects the selected expiry date.
3. `/projects/regression-demo/report`: newest real run is selected by `created_at`, and its pass rate,
   case count, and distinct-flow count are truthful.
4. An unknown run renders a themed 404, and checked pages have zero unexplained console errors.

Write the independent report to
`qa/evidence/browser-t100-ui-reclose-2026-09-10-checker/report.json` and cite it in the verdict.

## Contract-maintenance request

Fold the 2026-09-10 T-100 entry in `qa/feedback-inbox.md` into the UI/UI-report contracts before
judging. This is a routine tightening; it must not weaken existing criteria.

## Scope boundary

Do not judge unrelated working-tree/runtime artifacts (`AGENTS.md`, `.codex/`, `projects/*`,
`qa/.last-tick`, or `.goal/dashboard.html`) as implementation changes. The submitted artifact is
the explicit `c1f7cc0` commit plus this manifest.
