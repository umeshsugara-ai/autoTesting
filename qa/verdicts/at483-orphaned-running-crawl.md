# Verdict — at483-orphaned-running-crawl

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh subagent, Mode A + Mode D, no builder context. This is a first check —
the prior checker on this unit died mid-Mode-D with the same session hitting its API limit
and wrote no verdict, so this is genuinely Cycle 1, not a fix cycle. No conclusions were
inherited from that session; its orphaned scratch copy was not trusted, and this checker
built and verified its own throwaway copy and its own seed/Mode-D scripts from scratch.

## What I re-ran myself

- `uv run pytest tests/test_crawl_liveness.py -p no:cacheprovider -o addopts= -q` → **5 passed** (bound tree)
- `uv run pytest tests/test_crawl_liveness.py tests/test_explore.py tests/test_crawl_status_surfaces.py tests/test_explore_login_wall.py tests/test_explore_login_wall_bounds.py tests/test_ui_crawls.py tests/test_crawl_report.py -p no:cacheprovider -o addopts= -q` → **83 passed**
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**
- `uv run pytest tests/test_schema.py tests/test_core.py -q` → **17 passed** (C1/C5 spot-check)
- `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py`
  (full suite, background, 1624.64s) → **1 failed, 1445 passed, 2 skipped, 2 deselected, 32
  xfailed.** The one failure —
  `tests/test_mutation_check_judgement.py::test_a_mutation_that_hangs_pytest_times_out_and_is_not_a_kill`
  — is in a file this unit's diff never touches (`scripts/mutation_check.py` /
  `tests/test_mutation_check_judgement.py`; the unit's diff is `schema/crawl.py`,
  `stages/explore_node.py`, `stages/explore_status.py`,
  `tests/test_crawl_liveness.py` only — confirmed by `git diff 246c026...HEAD --stat`).
  Re-run in isolation it failed a second time with a different symptom (`cannot collect
  tests/test_mod.py: pytest exit -1` during `--collect-only`, before any mutation even
  ran) while this machine had dozens of unrelated processes running concurrently
  (VS Code, node/bun, another project's pytest, my own Mode D browser + capability-coverage
  work). Re-run a third time, alone, right after: **17 passed in 256.32s**, including the
  named test. This is a timing-sensitive pre-existing flake in the mutation-harness's own
  hang-detection tests (the file's own git history — AT-478/479, AT-487, AT-490/491 — is
  entirely about exactly this class of timeout flakiness), not a regression this unit
  introduced, matching the precedent already recorded in `core-invariants.md`'s 2026-09-09
  amendment for `test_explore_live.py` (AT-196): a false FAIL on a busy machine, never a
  false PASS.

## Capability coverage — reproduced in my OWN throwaway copy

`git archive HEAD | tar -x` into a fresh scratch dir, `projects/erp`, `projects/pathlynks`,
`projects/vidysea-erp` removed, `uv sync` run fresh. Confirmed `autotester.__file__` resolves
inside the copy before trusting anything in it. `tests/test_crawl_liveness.py` GREEN in the
copy first (5 passed), independently of the bound-tree run.

| capability | check | edit | anchor count | before (copy) | after (copy) |
|---|---|---|---|---|---|
| stale heartbeat → ABORTED | `test_a_stale_heartbeat_displays_as_interrupted` | `explore_status.py:191` `return age >= ...` → `return False` | 1 | 5 passed | **FAIL**, exact assertion `assert <RUNNING> is <ABORTED>` claimed by manifest |
| fresh heartbeat → still RUNNING | `test_a_fresh_heartbeat_still_displays_as_running` | same line → `return True` | 1 | 5 passed | **FAIL**, exact assertion `assert <ABORTED> is <RUNNING>` |
| legacy (no heartbeat_at) → RUNNING unchanged | `test_a_legacy_crawl_json_with_no_heartbeat_field...` | `explore_status.py:189` `return False` → `return True` | 1 (line-targeted; text `return False` is not unique in the file, 4 occurrences — verified by line number) | 5 passed | **FAIL**, exact assertion `assert <ABORTED> is <RUNNING>` |
| BFS heartbeats mid-run | `test_the_bfs_persists_progress_and_a_heartbeat...` | `explore_node.py:121` `return n == 1 or n % ... == 0` → `return False` | 1 | 5 passed | **FAIL**, exact assertion `assert []` / "expected at least one heartbeat write" |

All 4 rows restored byte-identical (`diff` against the live worktree file printed nothing)
before the next edit. **4/4 rows reproduced**, matching the manifest exactly.

**The 5th row (the manifest's "control", no dedicated falsification claimed) — I went
beyond the manifest and independently falsified it rather than accepting the reasoning on
faith.** The manifest argues rows 1/2's edits already exercise the guard the control test
defends; that's not quite true (rows 1/2 mutate `_heartbeat_stale`'s internal return value,
never the `crawl.status is CrawlStatus.RUNNING` gate itself), so I mutated the gate directly:
`explore_status.py:207` `if crawl.status is CrawlStatus.RUNNING and _heartbeat_stale(...)`
→ `if _heartbeat_stale(...)`. Result: `test_a_completed_crawl_with_a_stale_heartbeat_is_unaffected`
FAILS with the exact expected assertion (`assert <ABORTED> is <COMPLETED>`), and it is the
**only** one of the 5 tests that fails — the other 4 stay green. This confirms the control
row genuinely is defended, just not by the mechanism the manifest cited; the conclusion
("unaffected" holds, and is tested") is correct even though the manifest's stated reasoning
for skipping a dedicated row was imprecise. Restored byte-identical afterward.

**CAPABILITY-COVERAGE: 5/5 effectively reproduced** (4 tabulated + 1 the checker
independently falsified to confirm the manifest's untabulated claim).

## Judgement on the five things asked

**1. Status reuse / surface honesty — X16.** Grepped every X16 surface for how it reads
status: `ui/routes_crawls.py:119` (crawls table) and `ui/crawl_view.py:64` (crawl detail
page) both call `theme.pill(escape(displayed_status(crawl).value), _tone(crawl))` /
`... tone)`; `cli_crawl.py:108,111` calls `displayed_status(crawl).value`; `crawl_report.py:36`
puts `("Status", displayed_status(crawl).value)` into the workbook Summary rows. **All four
surfaces read through `displayed_status`, zero bypass, confirmed by grep, not by manifest
prose.** Tone: `_tone`/`is_success` are positive **only** for `CrawlStatus.COMPLETED`
(pre-existing, unit-unrelated) — a RUNNING crawl has never shown a positive/`badge-pass`
pill, before or after this unit, and a stale RUNNING (now displayed ABORTED) also never
does. Live-browser evidence below confirms this directly, not merely via grep.

**2. False-positive arithmetic.** Defaults: `heartbeat_every_actions=5`,
`heartbeat_stale_after_s=90.0`. At the manifest's measured ~2.8s/action pace, 5 actions ≈
14s between heartbeats — a **~6.4x margin** under 90s. Worst realistic case I checked by
reading the code path (`try_action` → `_perform`'s `settle(timeout_ms=settle_ms=2500)`, then
`visit_node`'s post-action `return_to` which does `go_back` + `settle(2500)` and, only if
that mismatches, `goto` + `settle(2500)`): for an ordinary "slow settle/networkidle" page
that still lands back correctly (no replay chain needed), worst case ≈ 2 × 2500ms per action
= 5s, × 5 actions = 25s — still a **~3.6x margin**. The margin only tightens toward the edge
if `return_to`'s full `MAX_REPLAY_DEPTH=3` chain fires on **every single action** in a
5-action window (a screen genuinely, repeatedly lost, not merely "a slow page") — that is a
qualitatively different pathology (repeated navigation-recovery failure) than "settle
timeouts / long networkidle", and it is itself bounded elsewhere (a node that can't be
returned to is marked `ABORTED_ERROR` and stops being visited, X4's bounds still apply). I
did not reproduce this edge case live; I'm stating it as a residual worth naming, not a
defect — the manifest's central claim (a legitimately long/slow crawl is not misjudged) holds
with real margin for the pattern the criterion actually describes.

**3. Legacy compatibility — X18(d).** `test_a_legacy_crawl_json_with_no_heartbeat_field...`
confirms this at the unit level (`heartbeat_at` genuinely absent from the written JSON,
loads fine, displays `RUNNING` even `far_future`). I additionally seeded my own legacy
fixture (`crawl_legacy483`, no `heartbeat_at` field, confirmed absent from the on-disk JSON
before serving) and drove it through the real UI (Mode D) — see below. Confirmed both ways.

**4. The disclosed gap (kill before the first action).** Confirmed by reading the code, not
merely accepting the manifest's prose: `run_crawl` (`explore.py:286`) saves the envelope
exactly once before `_seed`/`_bfs`, with `heartbeat_at` unset; the only place `heartbeat()`
is called is inside `visit_node`'s per-candidate loop, gated on `_heartbeat_due`
(`n == 1 or n % heartbeat_every_actions == 0`) — i.e., **after** the first action's
`try_action` call completes. A process killed during `_seed` (opening `base_url`), during
login bootstrap, or mid-way through the very first `try_action`, leaves `heartbeat_at = None`
forever, and `_heartbeat_stale` returns `False` whenever `heartbeat_at is None`
(`explore_status.py:188-189`) — so `displayed_status` never flags it, and it reads RUNNING
forever, unchanged from before this unit. **This is real and I judge it acceptable disclosed
debt, not a fix that guts the unit's purpose:** the original AT-483 bug covered the entire
run (any kill timing, including hundred-action crawls that had made real progress and still
froze at `screens=0,actions=0`); this residual is narrowed to the much shorter pre-first-action
window, and the "always heartbeat on the 1st action, not only every Nth" design choice already
shrinks that window as far as it goes without restructuring `_seed` itself. Filed below as a
tracked issue rather than silently left implicit, consistent with how X14/X16/X18's own
residuals are handled in this contract's amendment log.

**5. `git checkout --` capture / restore integrity.** `git status --porcelain` on the bound
tree is clean except this checker's own new evidence directory. `git diff HEAD -- <the 3 src
files>` is empty — the working tree is byte-identical to commit `9673f6b`/`2030799` (HEAD).
Nothing was lost in the manifest's capture-then-restore cycle.

## Live browser (Mode D) — my own script, my own fixtures, real headless Chromium

**Not the maker's smoke script or screenshots** — a fresh Python Playwright script against a
real `uv run uvicorn autotester.ui.app:app` process, run from my own throwaway copy (isolated
`AUTOTESTER_ROOT`, separate from the bound tree). Server output to a log file, never
`subprocess.PIPE`; server confirmed listening (`curl` 200) before driving the browser, and
confirmed fully stopped afterward (`taskkill` on the exact PID I started, verified via
`netstat` — no LISTENING socket remains — and a timed-out `curl` to the same port).

Seeded (my own fixtures, thresholds chosen so this run cannot race them): `crawl_stale483`
(RUNNING, heartbeat 1 hour stale, `heartbeat_stale_after_s=8.0`), `crawl_fresh483` (RUNNING,
heartbeat ~0s old, `heartbeat_stale_after_s=600.0`), `crawl_legacy483` (RUNNING, no
`heartbeat_at` field at all — confirmed absent from the on-disk JSON before serving).

Pages driven: `/projects/checkerdemo483/crawls` (table), and each crawl's own detail page.
**11/11 checks passed:** the `crawl_stale483` table row and detail pill both read `aborted`,
never `running`, and never carry a `badge-pass` pill; `crawl_fresh483` and `crawl_legacy483`
both still read `running`, with **no** `badge-pass` pill either (correctly so — only
`COMPLETED` is ever positive-toned, pre-existing and unrelated to this unit, verified by
reading `crawl_view.py:_tone`/`is_success` rather than assumed). **0 console errors on every
page.** All three `crawl.json` files on disk are **byte-identical (sha256) before and after**
every page view, across two separate script runs — the check is display-only exactly as
claimed.

Evidence: `qa/evidence/browser-at483-orphaned-running-crawl-2026-09-18-checker/` —
`01-crawls-table.png`, `02-crawl-stale-detail.png`, `03-crawl-fresh-detail.png`,
`04-crawl-legacy-detail.png`, `report.json`.

## New issues

- `ISS-at483-1` — low — **Disclosed, tracked residual: a crawl killed before its first
  action completes (during `_seed`, login bootstrap, or mid-way through the very first
  `try_action`) never receives a heartbeat write and displays RUNNING forever.**
  Evidence: `src/autotester/stages/explore.py:277-287` (`run_crawl` saves the envelope once,
  pre-BFS, no `heartbeat_at`); `src/autotester/stages/explore_node.py:119-137,266-267`
  (`heartbeat()` only called after a completed `try_action`, gated by `_heartbeat_due`);
  `src/autotester/stages/explore_status.py:187-191` (`_heartbeat_stale` returns `False`
  whenever `heartbeat_at is None`, so nothing ever flags it). Judged acceptable disclosed
  debt (see point 4 above), not a reason to FAIL this unit — narrower than AT-483's original
  scope and a natural next unit, not a defect in this one.

## SCOREBOARD

7/7 criteria met (explore.md X11, X16, X18(c), X18(d); core-invariants.md C1, C2, C7),
0 invariants violated.

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 0/0 invariants violated
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 effectively reproduced (4 tabulated by the manifest, all 4 re-verified by the checker; the 5th ("control") row independently falsified by the checker beyond what the manifest tabulated)
LIVE-BROWSER: qa/evidence/browser-at483-orphaned-running-crawl-2026-09-18-checker/
ISSUES-WRITTEN: ISS-at483-1 (low, disclosed residual, see "New issues" above -- not written to qa/issues.jsonl per this dispatch's instruction; recorded here verbatim for the maker/orchestrator to fold in)
EXPLANATION: Every X16 surface (crawls table, crawl detail page, CLI line, workbook Summary) verifiably reads through displayed_status with zero bypass (grep-confirmed, not manifest-trusted), and Mode D confirms non-success tone live for the stale-heartbeat case with crawl.json left byte-unchanged on disk across two independent runs. All 4 tabulated capability-coverage rows reproduced exactly as claimed in a fresh throwaway copy, plus a 5th independent falsification of the manifest's untabulated "control" reasoning, which held up. The one full-suite failure is an unrelated, pre-existing, machine-load-sensitive flake (confirmed by isolated re-run passing 17/17) in a file this unit's diff never touches. The one disclosed gap (pre-first-action kill) is real, narrower than the original bug, and filed as a tracked low-severity residual rather than silently accepted.
```
