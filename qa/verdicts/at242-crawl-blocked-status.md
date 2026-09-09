# Verdict — at242-crawl-blocked-status

**Contract:** qa/contracts/explore.md X4/X16
**Manifest:** qa/manifests/at242-crawl-blocked-status.md
**Cycle checked:** 1
**Date:** 2026-09-09
**Mode:** A (unit check)

## What I re-ran, independently

- Confirmed the unit is already committed at HEAD: `git log -1 -- src/autotester/stages/explore.py`
  and `enums.py` both show commit `2bb3270139bb08311b41af4f8da72f6fed2be191`
  ("fix(AT-242): a crawl that could act on nothing must not report completed").
  `git show 2bb3270 --stat` confirms the diff is exactly three files: `src/autotester/schema/enums.py`
  (+7), `src/autotester/stages/explore.py` (+49/-3), `tests/test_explore_blocked.py` (new, 60 lines).
  No route/template/component file appears in the diff.
- Built my OWN isolated extract: `git archive HEAD | tar -x` into a scratch dir, then `uv sync`
  its own venv (no PYTHONPATH pin, no editable-install shortcut). Verified
  `autotester.stages.explore.__file__` resolves to a path inside the extract before trusting
  anything.
- In the extract: `uv run pytest tests/test_explore.py tests/test_explore_blocked.py -q` → 21 passed.
  `uv run pytest -q` → full suite green (923 passed, 2 skipped — matches manifest). `uv run ruff
  check src tests scripts` → "All checks passed!". `uv run autotester doctor` → "doctor: clean".
  All four reproduced independently; none trusted from the pasted manifest output.
- **Sabotage, done myself, on my own extract copy** (not the shared live tree — a concurrent
  maker session is active there for AT-226): removed the `BLOCKED_NO_ACTIONS` branch from
  `_terminal_status` (the `if rt.frontier.actions_used == 0 and rt.denied > 0: ... return
  CrawlStatus.BLOCKED_NO_ACTIONS` clause), leaving `completed` fall through to `COMPLETED`
  unconditionally. Result: **exactly 1 failure**,
  `test_a_login_gate_with_every_action_denied_is_not_reported_completed`, with the exact predicted
  swap (`assert <CrawlStatus.COMPLETED> is <CrawlStatus.BLOCKED_NO_ACTIONS>`). Restored the file
  from my saved copy (never `git checkout`), re-ran `tests/test_explore.py
  tests/test_explore_blocked.py -q` → 21 passed again.

## X4 — bounds fire and name themselves

Not directly touched by this diff (no bound logic changed); pre-existing bound behaviour is
unaffected — `_terminal_status`'s `not completed` branch (frontier did NOT genuinely empty) still
routes to `STOPPED_BOUND` untouched. No regression found.

## X16 — the crawl report shows what was refused and why it stopped

This unit strengthens X16's "genuinely honest terminal state" intent: `BLOCKED_NO_ACTIONS` makes a
crawl that could act on nothing distinguishable from a full crawl of a trivial product, and the
`stop_reason` string gets the `"-- every reachable action was denied by policy"` clause appended
(read at `explore.py:179`, confirmed present). `DENIED_POLICY`/`SKIPPED_UNNAMED` edges themselves
were already recorded before this unit (X16's edge-listing requirement is unaffected by this diff).

## The negative case (real, not accidentally floored)

`tests/test_explore_blocked.py::test_a_page_with_no_controls_at_all_still_reports_completed` is
real and present: a project pointed at a URL the fixture serves no controls for, `crawl.actions ==
0`, `crawl.denied == 0`, asserts `crawl.status is CrawlStatus.COMPLETED` with an explicit message
pinning the floor. This is exactly the right shape — it depends on `denied == 0`, so it cannot
pass by accident if the fix had been written as "zero actions ⇒ blocked" instead of "zero actions
AND at least one denial ⇒ blocked". Re-ran it standalone in my extract: passes. I did not find a
way this test could be satisfied by a broken implementation that also breaks the positive case.

## CrawlStatus.value rendering generically — verified myself, not trusted

Grepped all four claimed consumers independently for status-string pattern-matching:

- `ui/routes_crawls.py:65` — `theme.pill(escape(crawl.status.value), 'neutral')` — generic, tone
  is always `'neutral'` regardless of which status value it is. No branch on a specific status.
- `ui/crawl_view.py:103,164` — `node.status.value` / `spec.review.status.value` rendered directly
  in an f-string; `EdgeOutcome.DENIED_POLICY` appears only as an import/reference at line 23
  (edge-kind constant, unrelated to `CrawlStatus`), not a string match against crawl status.
- `cli_crawl.py:107` — `f"{crawl.id}: {crawl.status.value} ({crawl.stop_reason}) — ..."` — generic
  interpolation, no branching on status value.
- `stages/crawl_report.py:35,56` — `("Status", crawl.status.value)` and `node.status.value` written
  straight into the workbook — generic.

I found no `if status == "completed"` / `== CrawlStatus.COMPLETED` / similar branch in any of the
four files that would silently mishandle `BLOCKED_NO_ACTIONS` by falling through to a wrong label
or being skipped. The manifest's claim holds on the evidence.

## Not-UI-touching judgment — confirmed independently

`git show 2bb3270 --stat` is definitive: the only files in the diff are `schema/enums.py`,
`stages/explore.py`, and a new test file. No file under `ui/`, no template, no route, no
`cli_crawl.py` change. I agree this unit is not UI-touching; Mode D (live browser) is correctly
not required for this specific unit's own diff. (The four "renders generically" files were read
for X16/consistency verification only, not because this unit modified them.)

## Scope claims (not making, not claiming)

Manifest correctly does not claim auto-escalation to a `VideoRequest` on `BLOCKED_NO_ACTIONS`, and
correctly does not claim to touch AT-226 (already-authenticated sessions) — confirmed the diff
touches no code path shared with the concurrent maker session's stated area (`_bootstrap_login` is
untouched by this commit; `_terminal_status` and the `run_crawl` tail are new/changed but are a
different function from anything AT-226 would plausibly touch).

VERDICT: PASS
SCOREBOARD: 2/2 targeted criteria met (X4 unaffected/clean, X16 strengthened and clean), 0/0 invariants newly at risk
FAILURES (if any): none
LIVE-BROWSER: not-applicable (src/autotester/schema/enums.py, src/autotester/stages/explore.py, tests/test_explore.py, tests/test_explore_blocked.py — no route/template/component in diff, confirmed via `git show 2bb3270 --stat`)
ISSUES-WRITTEN: none
EXPLANATION: Re-ran every verify command myself in an isolated git-archive extract with its own uv-synced venv (file-identity confirmed), reproducing the maker's pasted results exactly. Independently sabotaged `_terminal_status` and got exactly the predicted single failure with the exact predicted assertion swap, then restored and re-confirmed green. The negative-case test is real and structurally cannot pass by accident (requires denied==0, not just actions==0). Grepped all four claimed UI/CLI/report consumers myself and found none pattern-match a specific CrawlStatus string, so BLOCKED_NO_ACTIONS renders generically everywhere as claimed. Confirmed via `git show --stat` that no UI/route/template file is in the diff, agreeing with the manifest's non-UI-touching judgment.
