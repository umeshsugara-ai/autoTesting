# Checker verdict — t100-ui-reclose

Date: 2026-09-10  
Bound root: `D:\autoTesting`  
Cycle checked: 1  
Implementation checked: `c1f7cc0`

Re-run evidence:

- `uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-t100-checker-recovery -q` — PASS at 100% with the 2 expected skips; exit 0.
- `uv --cache-dir .work/uv-cache run ruff check src tests scripts` — PASS, `All checks passed!`; exit 0.
- `uv --cache-dir .work/uv-cache run autotester doctor` — expected working-tree-only finding: untracked root `AGENTS.md`.
- Clean `git archive` of `c1f7cc0`, checked with `AUTOTESTER_ROOT` bound to the extracted tree and the repository's installed `autotester` executable — PASS, `doctor: clean`; exit 0.
- `git diff --check c1f7cc0^ c1f7cc0` — PASS; exit 0.
- Fresh headed system Chrome driven through Playwright — PASS. The browser traversed Sources → project → Crawls, submitted all four bounds into the refusal path, followed the recovery link, exercised selected-date timezone offsets, submitted an unsigned FlowSpec approval, opened the newest report run, and checked unknown run/crawl routes. Evidence: `qa/evidence/browser-t100-ui-reclose-2026-09-10-checker/report.json`.

The browser emitted four expected main-document console messages: HTTP 403 for the deliberately refused expired crawl approval, HTTP 400 for the deliberately unsigned FlowSpec approval, and HTTP 404 for each deliberately unknown run and crawl. Each message's location is the exercised main-document URL and its status matches the asserted response; there were zero unexplained console errors and no favicon error.

VERDICT: PASS
SCOREBOARD: 17/17 criteria met, 9/9 invariants hold
FAILURES (if any):
- none
LIVE-BROWSER: qa/evidence/browser-t100-ui-reclose-2026-09-10-checker/report.json
ISSUES-WRITTEN: AT-244, AT-245, AT-246, AT-247, AT-248, AT-251, AT-252, AT-257, AT-259 (open → fixed)
EXPLANATION: The implementation satisfies UI U1-U11 and UI-report UR1-UR6, while the independent command set and clean-archive doctor satisfy core C1-C9. The expected 403/400/404 main-document console messages are explained response signals from deliberately exercised recovery paths; no unexplained console error remains.
