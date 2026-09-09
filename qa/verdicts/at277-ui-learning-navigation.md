# Verdict — at277-ui-learning-navigation

**Date:** 2026-09-09  
**Cycle checked:** 1  
**Manifest:** `qa/manifests/at277-ui-learning-navigation.md`  
**Implementation:** `f1c0398`  
**Contract:** `qa/contracts/ui.md` (U2, U5, U10)

VERDICT: PASS

SCOREBOARD: 3/3 criteria met, 0/0 invariants hold

FAILURES (if any):
- none

LIVE-BROWSER: `qa/evidence/browser-at277-ui-learning-navigation-2026-09-09-checker/report.json`

ISSUES-WRITTEN: none; AT-277 moved `open` → `fixed`

EXPLANATION: The existing 19-case project now exposes both FlowSpec and Sources in its normal Actions card. The checker clicked FlowSpec, observed the persisted NEEDS_EDIT review state and corrective Add a recording action, then clicked through to the real Sources route with 200 responses throughout; the browser reported zero console warnings/errors. The Sources POST uses the canonical content-addressed ingest/store path, and independent hostile probes confirmed no-write refusals, raw-secret blocking, idempotence, SHA-256 identity, and output escaping.

## Evidence independently reproduced

- Focused UI suite: `.\.venv\Scripts\python.exe -m pytest tests/test_ui_learn.py tests/test_ui_sources.py tests/test_ui.py -q` → exit 0, `32 passed, 1 skipped`.
- Full suite: `.\.venv\Scripts\python.exe -m pytest -q` → exit 0, 100% passed, 2 skipped, one existing Starlette deprecation warning.
- Focused Ruff command from the manifest → exit 0, `All checks passed!`.
- Full Ruff: `.\.venv\Scripts\python.exe -m ruff check src tests scripts` → exit 0, `All checks passed!`.
- Doctor: `.\.venv\Scripts\autotester.exe doctor` → exit 0, `doctor: clean`.
- Static derivation: `routes_sources.add_source` calls `stages.ingest.register_source`; that computes `file_sha256`, de-duplicates on the digest, and persists via `ProjectStore.add_source` to `sources.jsonl`. The GET route escapes source id, label, and path.
- Independent temporary-root probe: a missing path and a whitespace-only path each returned 400 without creating `sources.jsonl`; an undeclared raw `.env` secret in the label returned 400 without echo or a row; registering identical bytes twice produced one row whose SHA-256 matched the file and preserved the first immutable label; hostile label markup rendered escaped.
- Live browser: project → FlowSpec → Add a recording → Sources was clicked in the checker's own browser. Server responses were 200/200/200; the only 404 was the unrelated favicon. The final Sources page was visually inspected from a browser screenshot, and console warning/error count was zero.

## Contract judgment

- **U2 — PASS:** the ordinary project page loads the real project/FlowSpec/case count on request and, even with 19 existing cases, exposes FlowSpec and Sources without a parallel navigation state.
- **U5 — PASS:** new rendered project/source values are escaped at their call sites; focused tests and the hostile probe confirm raw label/path markup does not reach HTML.
- **U10 — PASS:** the existing NEEDS_EDIT FlowSpec exposes a corrective recording action, and its real click target resolves to the Sources UI rather than a product-route 404.

## Browser instrumentation note

The in-app browser API refused the request to force an OS-visible window because this check runs in a subagent thread. This did not prevent Mode D: the checker drove its own live interactive tab, inspected the accessibility state after every click, emitted and visually inspected the final screenshot, read browser console logs, and corroborated each document request in the server log.
