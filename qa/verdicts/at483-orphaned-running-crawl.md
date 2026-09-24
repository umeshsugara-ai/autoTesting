# Verdict — at483-orphaned-running-crawl

**Cycle checked:** 2
**Date:** 2026-09-24
**Checker:** fresh subagent, Mode A, no builder/maker context. Judges ONLY the cycle-2
"re-land onto master d00e6d9" section of the manifest, on the MERGED tree
(branch `wave/at483-reland`, HEAD `87e247b` = merge of master `d00e6d9` + the cycle-1
PASSed branch tip `4d4a2b3`).
**Cycle-1 pointer:** the original fix was PASSed on branch `wave/at483-orphaned-running-crawl`
by verdict commit `9e11559` (2026-09-18) — see `git show 9e11559:qa/verdicts/at483-orphaned-running-crawl.md`
for that check's full record. That verdict never reached `master` (unmerged); this cycle
re-verifies the SAME mechanism on the merged tree, not the cycle-1 evidence.

## What I re-ran myself (fresh, on `D:/autoTesting/.worktrees/at483-reland`, HEAD `87e247b`)

- `uv run pytest tests/test_crawl_liveness.py tests/test_explore.py tests/test_crawl_status_surfaces.py tests/test_explore_login_wall.py tests/test_explore_login_wall_bounds.py tests/test_ui_crawls.py tests/test_crawl_report.py tests/test_explore_typing.py tests/test_explore_typing_guards.py`
  → **91 passed** — matches the manifest's claim exactly.
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**
- `uv run pytest -rx --deselect tests/test_crawl_inventory_live.py` (full suite, background,
  `PYTHONUTF8=1`, no CLI `-q` per AT-503, 540.81s) → **1588 passed, 5 skipped, 2 deselected,
  32 xfailed, 1 warning, EXIT:0 — zero failures.** The manifest's own full-suite run reported
  one failure (`tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`,
  the pre-existing, previously-known flake ISS-t164-1 named in this cycle's dispatch as not
  this unit's). My independent run of the same command against the same tree passed that test
  outright (consistent with it being a genuine timing-sensitive flake, not a regression) —
  stronger evidence than the manifest's own run, not weaker. Either way, nothing in this
  unit's diff is implicated.

## Diff scope (step 4c) — `git diff d00e6d9 87e247b`

`--name-status`: only additions (`qa/manifests/`, `qa/verdicts/`, `qa/evidence/*` for this
unit, `tests/test_crawl_liveness.py`) and four modified source files —
`src/autotester/schema/crawl.py`, `src/autotester/stages/explore_node.py`,
`src/autotester/stages/explore_status.py`, `src/autotester/stages/explore_typing.py`. No file
deleted or renamed. Read the full diff for each modified file (not just the manifest's
description of it):

- `schema/crawl.py` — pure addition (`CrawlBounds.heartbeat_every_actions`,
  `CrawlBounds.heartbeat_stale_after_s`, `Crawl.heartbeat_at`). Nothing removed.
- `explore_status.py` — pure addition (`_heartbeat_stale`, the `now` kwarg on
  `displayed_status`, the new RUNNING+stale branch). The pre-existing `BLOCKED_NO_ACTIONS`
  branch and the function's other behavior are byte-unchanged. Confirmed every existing call
  site (`cli_crawl.py:113`, `crawl_report.py:46`, `explore_status.py:214`,
  `ui/crawl_view.py:64`, `ui/routes_crawls.py:119`, and both call sites in
  `tests/test_explore_login_wall.py`) still calls `displayed_status(crawl)` with no second
  positional argument — the new `now` parameter is keyword-only with a default, so every
  existing caller is unaffected.
- `explore_typing.py` — one import line widened (`_heartbeat_due, heartbeat` added to the
  existing `from autotester.stages.explore_node import (...)`) and one heartbeat call added
  inside `type_form`'s per-field loop. Nothing removed.
- `explore_node.py` — confirmed **master's later refactor survives intact**: `visit_node`
  still calls `type_form` then `_click_loop` (the AT-533/AT-534 typing pre-pass split), both
  functions present with their full logic. The only changes are the new `_heartbeat_due`/
  `heartbeat` functions, one heartbeat call added inside `_click_loop` right after its
  `try_action` call, and cosmetic docstring/comment trims to hit exactly 300 lines (verified
  no content dropped — same claims, fewer physical lines: `_click_loop`'s docstring keeps
  both sentences, the AT-534 comment keeps its full reasoning, just condensed to one line each).
  No test, function, class, export, or config key was deleted or renamed anywhere in this diff.

**Circular-import check (independent):** `explore_node.py` imports nothing from
`explore_typing` at module level (`grep -n "explore_typing" explore_node.py` → only the one
lazy `from autotester.stages.explore_typing import type_form` inside `visit_node`, line 297);
`explore_typing.py` imports from `explore_node` at module level as before. Direction of the
dependency is unchanged — no new circular import.

**File/function caps (C2), independently re-measured:** `explore_node.py` = 300 lines exactly
(`wc -l`), `explore_typing.py` = 144 lines. `heartbeat()` = 10 lines, `_click_loop()` = 37
lines, `type_form()` = 48 lines — all ≤ 50. Matches the manifest's own count.

## Capability coverage (step 4b) — reproduced in my OWN throwaway copy

`git archive HEAD` to a tarball, extracted to a scratch dir **outside** the bound root
(`/tmp/claude/checker-at483r/cov_copy`, mapped from `C:\Users\Lenovo\AppData\Local\Temp\claude\...`),
`uv sync` run fresh in the copy. Confirmed `autotester.__file__` resolves inside the copy
before trusting anything, and `tests/test_crawl_liveness.py` GREEN in the copy first
(**5 passed in 1.01s**) — the copy is real before any edit.

Each row below: single-hunk `sed` edit to the one file the manifest names (anchor confirmed to
match — either uniquely file-wide via `grep -n`, or uniquely by line number where the manifest
itself says the text isn't unique), the row's own named test run against the edited copy, then
the file restored from a pre-edit backup and `diff` confirmed byte-identical before the next
row.

| capability | check | edit applied | before (copy) | after (copy) |
|---|---|---|---|---|
| Stale heartbeat → ABORTED | `test_a_stale_heartbeat_displays_as_interrupted` | `explore_status.py:191` `return age >= ...` → `return False` | not applicable (isolated run) | **FAIL** — `assert <RUNNING> is <ABORTED>` (exact manifest assertion) |
| Fresh heartbeat → still RUNNING | `test_a_fresh_heartbeat_still_displays_as_running` | same line → `return True` | — | **FAIL** — `assert <ABORTED> is <RUNNING>` |
| Legacy (no heartbeat_at) → RUNNING unchanged | `test_a_legacy_crawl_json_with_no_heartbeat_field_loads_and_displays_unchanged` | `explore_status.py:189` (line-targeted; confirmed non-unique, 4 occurrences) `return False` → `return True` | — | **FAIL** — `assert <ABORTED> is <RUNNING>` |
| BFS heartbeats mid-run | `test_the_bfs_persists_progress_and_a_heartbeat_before_the_crawl_finishes` | `explore_node.py:123` `return n == 1 or n % ... == 0` → `return False` | — | **FAIL** — `assert []`, "expected at least one heartbeat write" |
| Completed + stale heartbeat unaffected (control, the `RUNNING` gate itself) | `test_a_completed_crawl_with_a_stale_heartbeat_is_unaffected` (full 5-test file) | `explore_status.py:207` `if crawl.status is CrawlStatus.RUNNING and _heartbeat_stale(...)` → `if _heartbeat_stale(...)` | **5 passed in 1.09s (pre-edit)** | **1 failed, 4 passed** — only the control test fails (`assert <ABORTED> is <COMPLETED>`), the other 4 stay green |

Copy re-confirmed fully GREEN (**5 passed in 0.55s**) after the last restore. **5/5 rows
reproduced, exactly matching the manifest's cycle-2 table** — same assertions, same
isolation, no row survived its edit.

## AT-497 cross-check (independent, not taken from the manifest's prose)

Read `explore.py`'s `run_crawl` directly: `store.save_crawl(crawl)` at line 271 fires exactly
once, before login bootstrap / `_seed` / `_bfs`, with an envelope that never sets
`heartbeat_at` (absent from the constructor call, so it defaults to `None`). No heartbeat call
exists anywhere between that single pre-BFS save and the first `try_action` inside
`type_form`/`_click_loop`. This confirms AT-497 (open, "killed before first action never
heartbeats") is **neither fixed nor contradicted** by this cycle — the gap is exactly as wide
as before the re-land.

## Live-browser (step 5b) — not-applicable, decided from CHANGED PATHS

The diff touches `schema/crawl.py`, `stages/explore_node.py`, `stages/explore_status.py`,
`stages/explore_typing.py` only — no `ui/` file, no template. `displayed_status` remains the
single funnel every X16 surface reads through, and every existing call site
(`ui/routes_crawls.py:119`, `ui/crawl_view.py:64`, `cli_crawl.py:113`,
`stages/crawl_report.py:46`) is unmodified by this diff and unaffected by the new keyword-only
`now` parameter (confirmed above, not merely asserted). Cycle-1's own Mode D + the cycle-1
checker's independent Mode D (verdict `9e11559`) already exercised this exact display path
live; nothing in this cycle's diff changes what those surfaces render.
**LIVE-BROWSER: not-applicable** (changed paths: `schema/crawl.py`, `stages/explore_node.py`,
`stages/explore_status.py`, `stages/explore_typing.py` — no UI surface).

## Judgement against the contract

**explore.md X11** (incremental, crash-surviving artifacts) — unaffected; this unit adds a
display-only liveness signal on top of `Crawl`'s existing envelope writes, doesn't change
X11's write discipline.
**explore.md X16** (crawl report shows what was refused/why it stopped, all surfaces equal
billing) — `displayed_status` remains the single funnel for all four surfaces, confirmed by
grep of every call site, not manifest trust. Holds.
**explore.md X18(c)/(d)** (a crawl that never got past the login wall, or a legacy
crawl.json, never reads as an unqualified success) — the new stale-heartbeat branch composes
with the existing `BLOCKED_NO_ACTIONS` branch without touching it (`if/elif`-equivalent
ordering unchanged, first check still first); the legacy-compat row (row 3 above) confirms a
`heartbeat_at`-less crawl.json still displays exactly as before. Holds.
**core-invariants.md C1** (schema-first) — `Crawl.heartbeat_at` and the two new
`CrawlBounds` fields are plain, correctly-typed Pydantic fields on existing `Artifact`
subclasses; no dict-shaped duplicate introduced. Holds.
**core-invariants.md C2** (≤300/≤50 lines) — re-measured independently above; both files at
or under cap, all touched functions ≤50 lines. Holds.
**core-invariants.md C7** (independent verification, sabotage asserts it was applied) — every
capability-coverage row above shows an anchor-count check (unique match or line-targeted with
stated non-uniqueness) before the edit and a green-before line, satisfying C7's "a sabotage
must assert it was applied" and "a zero-failure sabotage is evidence about the sabotage, not
the tests" bar — every row here actually reddened, and reddened on the assertion it claims to
isolate.

## SCOREBOARD

7/7 criteria met (explore.md X11, X16, X18(c), X18(d); core-invariants.md C1, C2, C7),
0 invariants violated.

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 0/0 invariants violated
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 5/5 rows reproduced in an isolated throwaway copy outside the bound root, matching the manifest's cycle-2 table exactly
LIVE-BROWSER: not-applicable (changed paths: schema/crawl.py, stages/explore_node.py, stages/explore_status.py, stages/explore_typing.py -- no ui/ file; displayed_status funnel confirmed unmodified and all call sites confirmed compatible)
ISSUES-WRITTEN: none (AT-497 independently confirmed unaffected, not re-filed; no new defect found)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: The cycle-2 re-land merge (87e247b = master d00e6d9 + cycle-1 PASSed tip 4d4a2b3) was independently re-verified end to end: every verify command re-run fresh and green, including a full-suite run (1588 passed, 0 failures -- cleaner than the manifest's own run, whose one failure was the pre-existing named flake ISS-t164-1). The diff scope check confirms master's AT-533/AT-534 typing-pre-pass refactor (type_form + _click_loop) survives completely intact, with no function/test/export deleted or renamed and no file touched beyond the four named. All 5 capability-coverage rows were independently reproduced in a fresh throwaway copy with real green-before/red-after evidence. The conflict resolution (heartbeat moved into _click_loop) and the semantic-gap fix (heartbeat added to type_form's per-field loop) are both correct, share the same _heartbeat_due gate, and introduce no circular import (verified directly, not assumed). AT-497 was independently re-confirmed neither fixed nor contradicted. No UI surface is touched, and every displayed_status call site was checked for compatibility with the new keyword-only `now` parameter.
```
