# Manifest — track-b1-observation-primitives
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3), qa/contracts/browser-and-secrets.md
(B5, B7, B9 — unchanged, verify no regression), qa/contracts/execute.md (E2 — new actions compose
existing session primitives the same way every prior one does)
**Goal task:** T-140
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §5 "B1 — observation primitives", authorised by D-014/D-015

## What changed
Full diff in commit `640cd92`. No new stage, no UI route, no crawl logic yet — this unit is
scoped to the mechanism a crawler will later compose: seeing a page's controls and never
touching `.page` outside `browser/`.

- **New** `browser/launch.py` — `launch_options` moved verbatim out of `session.py` (was at
  284/300 lines; B1 needed ~25 more). Re-imported into `session.py`'s namespace so every existing
  caller (`test_browser.py: from autotester.browser.session import launch_options`) is
  unaffected — proven with a byte-identical-output test in the new `test_browser_actions.py`,
  not just asserted.
- `browser/session.py`: `BrowserSession.__init__` takes an optional keyword-only `observer`,
  attached once inside `start()`. New `current_url()`, `go_back()`, `hover()`, `press_key()`,
  `scroll()` — each composes `self.page` and calls `self._record(...)`, the same discipline
  every existing action follows, so redaction/scrubbing is never bypassed.
- `browser/enumerate.js` — one `page.evaluate` call, no library. Selector priority
  `data-testid` → a non-generated-looking `#id` → `[aria-label]` → `role=…[name=…] >> nth=k` →
  an xpath fallback. `in_row` walks up to 6 ancestors looking for `tr`/`li`/`[role=row]`/
  `[role=listitem]` with more than 3 siblings — the signal Track B2's structural signature will
  exclude so two list rows don't become two screens.
- `browser/observe.py` — `PageObserver` installs exactly five listeners
  (`console`/`requestfailed`/`response`/`dialog`/context `page`) once per session;
  `_default_dialog_action` accepts only `beforeunload`, dismisses everything else (D-016's
  default, overridable via the constructor); `drain()` returns and clears. `enumerate_elements`
  and `observe` are the only functions that call `enumerate.js` or read `session.page`.
- `schema/screen_graph.py`, `schema/crawl.py` (new) — `ElementRef`/`PageObservation`/
  `DialogEvent` only. B2/B3/B4 extend these same files (per plan.md) rather than creating
  parallel ones.
- `stages/execute.py` — `_ACTIONS` gains real handlers for `BACK`/`HOVER`/`PRESS_KEY`/`SCROLL`
  (previously only reachable via the `StepNotExecutable` guard A1 added); `BACK` joins the
  settle-before-screenshot set with `CLICK`/`NAVIGATE`.

## The regression I had to make when B1 landed
A1's own `test_scroll_action_with_no_handler_yet_errors_instead_of_raising` test asserted SCROLL
specifically had no handler — true at A1, false the moment B1 wires one. Rewrote it as
`test_an_action_with_no_handler_errors_instead_of_raising_keyerror` in the new
`tests/test_execute_new_actions.py`: it monkeypatches `_ACTIONS` to remove a real entry so the
guard mechanism itself stays covered independent of which `Action` members currently have
handlers, then added a separate test proving the four new actions genuinely run `COMPLETED`.
`tests/test_execute.py` grew past 300 lines with these additions and both new tests plus their
fixtures were split into the new file, following the project's existing split pattern
(`test_browser_actions.py` also new, for the same reason on the session-level tests).

## Verified against a real browser, not only fakes
`enumerate.js` was run inside the container against a genuine headless Chromium page (a button
and a link, no test framework) and returned the expected `role`/`name`/`selector`/`href` shape —
pasted below, not just claimed:
```
[{'role': 'button', 'name': 'Click me', 'selector': '#go', ...},
 {'role': 'link', 'name': 'Link', 'selector': 'role=link[name="Link"] >> nth=0', 'href': '/x', ...}]
```

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest tests/test_observe.py tests/test_browser_actions.py tests/test_execute.py tests/test_actuator_chokepoint.py tests/test_browser.py -q`
  → expected: exit 0, all pass (plan.md's own verify line for B1)
- `docker compose exec autotester uv run pytest -q` → expected: `406 passed, 1 skipped` (up from
  385 at T-130; the skip is the pre-existing real-Chromium test, unrelated)
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: `All checks passed!`
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Actuator choke-point has teeth: plant `session.page.locator('x').click()` in any file outside
  `browser/` → `pytest tests/test_actuator_chokepoint.py` fails naming that file:line.
- Real-browser probe (not in the automated suite, for the checker to reproduce):
  ```
  docker compose exec autotester uv run python -c "
  from playwright.sync_api import sync_playwright
  from pathlib import Path
  pw = sync_playwright().start()
  browser = pw.chromium.launch(headless=True, args=['--no-sandbox'])
  page = browser.new_page()
  page.set_content('<html><body><button id=\"go\">Click me</button><a href=\"/x\">Link</a></body></html>')
  print(page.evaluate(Path('src/autotester/browser/enumerate.js').read_text(encoding='utf-8')))
  browser.close(); pw.stop()
  "
  ```
  → expected: two elements, the button with selector `#go`, the link with `href: '/x'`.

## Status: ready-for-check
