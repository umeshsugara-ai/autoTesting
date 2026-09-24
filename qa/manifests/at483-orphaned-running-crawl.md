# Manifest — at483-orphaned-running-crawl
**Contract:** qa/contracts/explore.md (X11, X16, X18(c)/(d)) + qa/contracts/core-invariants.md C1/C2/C7
**Goal task:** none
**Date:** 2026-09-17
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-483

## Design choice (smallest honest shape wins)

- **Write cadence is action-count based, not clock based.** `explore_node.heartbeat`
  re-persists the crawl envelope (progress counts + a fresh `heartbeat_at`) after the
  1st action of the crawl and every `CrawlBounds.heartbeat_every_actions`th one after
  that (default 5). This needs no new mutable timing state on `ExploreRuntime` —
  `rt.frontier.actions_used` already exists and already increments exactly once per
  performed action — and it keeps `src/autotester/stages/explore.py` (already at
  exactly 300 lines, the C2 cap) untouched entirely. The liveness property still
  holds: as long as the process is alive and acting, `heartbeat_at` keeps moving;
  the instant it dies, `actions_used` stops incrementing and `heartbeat_at` freezes
  — exactly the "a dead process cannot keep it fresh" signal the issue asked for.
- **Staleness is judged in wall-clock time**, via a new `CrawlBounds.heartbeat_stale_after_s`
  (default 90.0) compared against `datetime.now(UTC) - heartbeat_at`, never against
  `started_at` — so a legitimately long crawl (measured ~2.8s/action, a 200-action
  crawl ~10 min) is never misjudged: its heartbeat keeps advancing throughout.
- **No new `CrawlStatus` member.** `schema/enums.py` is ALSO exactly at the 300-line
  C2 cap (discovered during exploration; not in the brief's "room to spare" list),
  with no docstring-free line to reclaim without visibly degrading an existing
  member's documentation. `stages/explore_status.displayed_status` already reuses
  an existing status for a fabricated-only display (`BLOCKED_NO_ACTIONS` for a
  legacy `completed`-but-refused-everything crawl, X18(d)) — this unit follows the
  same precedent and reuses `CrawlStatus.ABORTED` (display-only) for a RUNNING
  crawl whose heartbeat has gone stale. Because `displayed_status` is already the
  single funnel every X16 surface reads through (crawl page, crawls table, CLI
  line, workbook Summary), this wires through all of them for free — **zero other
  files touched** (`ui/routes_crawls.py`, `ui/crawl_view.py`, `cli_crawl.py`,
  `stages/crawl_report.py` are unmodified). `crawl.json` itself is never rewritten
  by this check — same discipline as `displayed_status` already has.
- **Backward compatible by construction.** `Crawl.heartbeat_at: str | None = None`;
  `write_json`'s `exclude_none=True` means a crawl.json with no heartbeat yet (every
  file written before this unit, and any crawl before its first write) omits the key
  entirely — `extra="forbid"` only rejects *unknown* keys, so it loads fine and
  `_heartbeat_stale` returns `False` on `None` (nothing to compare, never flagged).
- **Known, disclosed residual:** a crawl killed before its very first action (or
  during `_seed`) never gets a heartbeat write and stays displayed as RUNNING
  forever, unchanged from before this unit. Narrower than the reported bug (which
  covered every kill timing), and the "always heartbeat on the 1st action" rule
  (not only every Nth) already shrinks the window to "before any action completes."
  Not re-filed as a new issue — AT-483 itself said "not required to auto-repair the
  counts, but must not silently claim RUNNING forever," and this unit closes the
  overwhelming majority of that window; a HEAD-of-crawl-only orphan is a much
  smaller, separate shape.

## What changed
- `src/autotester/schema/crawl.py:73-81` — `CrawlBounds.heartbeat_every_actions`
  (default 5) and `CrawlBounds.heartbeat_stale_after_s` (default 90.0).
- `src/autotester/schema/crawl.py:200-204` — `Crawl.heartbeat_at: str | None = None`.
- `src/autotester/stages/explore_status.py:16` — import `datetime, UTC`.
- `src/autotester/stages/explore_status.py:182-206` — new `_heartbeat_stale`; `displayed_status`
  gains `*, now: datetime | None = None` and returns `CrawlStatus.ABORTED` (display-only)
  when `crawl.status is RUNNING` and the heartbeat is stale.
- `src/autotester/stages/explore_node.py:11` — import `datetime, UTC`.
- `src/autotester/stages/explore_node.py:119-137` — new `_heartbeat_due` and `heartbeat`
  (re-persists progress counts + `heartbeat_at` via `store.save_crawl`).
- `src/autotester/stages/explore_node.py:266-267` (`visit_node`'s action loop) — calls
  `heartbeat(rt)` right after `try_action` completes, when `_heartbeat_due`.
- `tests/test_crawl_liveness.py` (new, 120 lines) — the 5 tests below.

## How to verify (commands + expected)
- `uv run pytest tests/test_crawl_liveness.py -p no:cacheprovider -o addopts= -q` → 5 passed
- `uv run pytest tests/test_crawl_liveness.py tests/test_explore.py tests/test_crawl_status_surfaces.py tests/test_explore_login_wall.py tests/test_explore_login_wall_bounds.py tests/test_ui_crawls.py tests/test_crawl_report.py -p no:cacheprovider -o addopts= -q` → all passed
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean
- `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py` → 1446 passed

## Actual outputs (from maker's own run)

### Red, before implementation (captured via a temporary `git checkout --` revert of the
3 src files, confirmed with `git status --porcelain` showing only the new test file
untracked; then `git apply` restored the implementation — never a stash, per the
worktree's shared-stash-stack rule):
```
FAILED tests/test_crawl_liveness.py::test_a_stale_heartbeat_displays_as_interrupted
FAILED tests/test_crawl_liveness.py::test_a_fresh_heartbeat_still_displays_as_running
FAILED tests/test_crawl_liveness.py::test_a_legacy_crawl_json_with_no_heartbeat_field_loads_and_displays_unchanged
FAILED tests/test_crawl_liveness.py::test_a_completed_crawl_with_a_stale_heartbeat_is_unaffected
FAILED tests/test_crawl_liveness.py::test_the_bfs_persists_progress_and_a_heartbeat_before_the_crawl_finishes
5 failed in 0.56s
```
(`Crawl` had no `heartbeat_at` attribute; `CrawlBounds` rejected `heartbeat_stale_after_s`/
`heartbeat_every_actions` as `extra_forbidden` — exactly the fields this unit adds.)

### Green, after implementation:
```
tests/test_crawl_liveness.py .....                                       [100%]
5 passed in 0.84s
```

### Targeted suite (named files):
```
........................................................................ [ 86%]
...........                                                              [100%]
83 passed, 1 warning in 10.24s
```

### `uv run ruff check src tests scripts`:
```
All checks passed!
```

### `uv run autotester doctor`:
```
doctor: clean
```

### Full suite (background, `--deselect tests/test_crawl_inventory_live.py`):
```
1446 passed, 2 skipped, 2 deselected, 32 xfailed, 1 warning in 721.75s (0:12:01)
```
1441 pre-existing + this unit's 5 new = 1446. No failure anywhere outside this unit's
own new file.

## Capability coverage (each new claim -> its isolating falsification)

Reproduced in an isolated `git archive HEAD` (commit `9673f6b`) extract at
`cov_copy2`, `projects/erp`/`projects/pathlynks`/`projects/vidysea-erp` removed (one
`rm` per path), `uv sync` run fresh — `autotester.__file__` resolved to
`.../cov_copy2/src/autotester/__init__.py`, confirmed inside the copy. Each row's
edit was applied with `sed` targeting a byte-anchor confirmed to match **exactly
once** first (`grep -c`), then reverted and diffed byte-identical against the live
worktree's committed file before the next row (`diff` printed nothing both times).

| capability | the check | the falsifying edit | observed |
|---|---|---|---|
| A RUNNING crawl with a stale heartbeat displays as interrupted (ABORTED) | `tests/test_crawl_liveness.py::test_a_stale_heartbeat_displays_as_interrupted` | `explore_status.py:191` `return age >= crawl.bounds.heartbeat_stale_after_s` → `return False` | PASS before: `1 passed in 0.17s`. FAIL after: `AssertionError: assert <CrawlStatus.RUNNING: 'running'> is <CrawlStatus.ABORTED: 'aborted'>` (the exact `displayed_status(...) is CrawlStatus.ABORTED` line) |
| A RUNNING crawl with a fresh heartbeat still displays as running | `tests/test_crawl_liveness.py::test_a_fresh_heartbeat_still_displays_as_running` | `explore_status.py:191` same line → `return True` | PASS before: `1 passed in 0.30s`. FAIL after: `AssertionError: assert <CrawlStatus.ABORTED: 'aborted'> is <CrawlStatus.RUNNING: 'running'>` |
| A legacy crawl.json with no `heartbeat_at` field loads and displays exactly as today | `tests/test_crawl_liveness.py::test_a_legacy_crawl_json_with_no_heartbeat_field_loads_and_displays_unchanged` | `explore_status.py:189` `return False` (the `heartbeat_at is None` branch) → `return True` | PASS before: part of `5 passed in 0.44s`. FAIL after: `AssertionError: assert <CrawlStatus.ABORTED: 'aborted'> is <CrawlStatus.RUNNING: 'running'>` |
| The BFS writes progress + a heartbeat at least once mid-run, before `_finish` | `tests/test_crawl_liveness.py::test_the_bfs_persists_progress_and_a_heartbeat_before_the_crawl_finishes` | `explore_node.py:121` `return n == 1 or n % rt.bounds.heartbeat_every_actions == 0` → `return False` | PASS before: part of `5 passed in 0.50s`. FAIL after: `AssertionError: expected at least one heartbeat write between start and finish` / `assert []` |

A completed crawl with a stale heartbeat is unaffected (the control,
`test_a_completed_crawl_with_a_stale_heartbeat_is_unaffected`) has no isolating
falsification of its own — it is the negative control for row 1's mechanism
(`crawl.status is CrawlStatus.RUNNING` gates the whole check), already exercised
by row 1's own edits (both sabotages there leave a non-RUNNING crawl's display
untouched, which is what "unaffected" means); a dedicated edit would only
re-target the same `is RUNNING` guard row 1 and row 2 already cover.

## Live browser evidence

`qa/evidence/browser-at483-orphaned-running-crawl-2026-09-17/` (maker smoke —
Playwright MCP unavailable this session; own Python Playwright script, sync API,
against a real headless Chromium and a real `uv run uvicorn` process, not curl,
not TestClient). Setup: scratch `AUTOTESTER_ROOT` seeded with a `demo` project and
two RUNNING crawls with `heartbeat_stale_after_s=600` — `crawl_stale` (heartbeat 1
hour old, screens=12/actions=54/edges=76, matching AT-483's own reproduction
shape) and `crawl_fresh` (heartbeat 5 seconds old) — server stdout/stderr to log
files, stopped afterward (verified gone via a failed `curl` and an empty
`ps -ef | grep uvicorn` before reporting done). Pages: `/projects/demo/crawls`,
`/projects/demo/crawls/crawl_stale`, `/projects/demo/crawls/crawl_fresh`.
Console errors: 0 on all three pages. Interactions (5, all `"pass": true` in
`report.json`): the crawls-table row for `crawl_stale` reads `aborted` /
`badge-blocked`, never `running`/`badge-pass`; the row for `crawl_fresh` still
reads `running`; the crawl-page status pill for `crawl_stale` reads `aborted`
with no `badge-pass`; the pill for `crawl_fresh` still reads `running`; and
`crawl_stale`'s `crawl.json` on disk still says `"status": "running"` after both
page loads — the check is display-only, exactly as designed. Screenshots:
`01-crawls-table.png`, `02-crawl-stale-detail.png`, `03-crawl-fresh-detail.png`.

**Disclosed gap:** this is the maker's own smoke pass, not the validation — per
skill rule, the checker's own Mode D run is what certifies the UI surface. A first
attempt at this same script showed `crawl_fresh` also misclassified as `aborted`;
that was **not** a code bug — the fixture's `heartbeat_stale_after_s` was 60s and
the real wall-clock delay of launching uvicorn + Playwright between seeding and
reading the page crossed it. Re-seeded with a wider threshold (600s) and it
resolved; noted here so the checker doesn't need to re-discover the same false
alarm.

## Status: checked-PASS (qa/verdicts/at483-orphaned-running-crawl.md, cycle 1, commit 9e11559; checker filed ISS-at483-1 (low): a crawl killed before its first action completes still displays running)

## Cycle 2 — re-land onto master d00e6d9

Checker-PASSed on branch `wave/at483-orphaned-running-crawl` (9673f6b fix → 2030799 manifest →
9e11559 checker PASS → 4d4a2b3 close-out, 2026-09-18) but never merged to `master`. Master moved
on with many commits touching `explore.py`/`explore_status.py`/`explore_node.py` while this fix
sat unmerged; the ledger (`qa/issues.jsonl`, AT-483) claims `fixed` but the mechanism was absent
from `master`. This cycle brings it back.

**Worktree:** `D:/autoTesting/.worktrees/at483-reland`, branch `wave/at483-reland`, created from
`master` at `d00e6d9`.

**Merge:** `git merge --no-ff wave/at483-orphaned-running-crawl` onto `wave/at483-reland`
(d00e6d9). `src/autotester/schema/crawl.py` and `src/autotester/stages/explore_status.py`
auto-merged cleanly — both branches touched disjoint regions (AT-483's new `CrawlBounds`
fields / `Crawl.heartbeat_at` / `_heartbeat_stale` sit alongside master's unrelated later
changes to the same files with no overlapping hunks). One real conflict:

- **`src/autotester/stages/explore_node.py` — `visit_node`.** Master had refactored the single
  inline action loop AT-483 patched into two functions since AT-483 branched: a typing pre-pass
  (`explore_typing.type_form`, AT-533/AT-534, shares the per-node action budget with the click
  phase) followed by a new `_click_loop(rt, node, typed)` extracted from `visit_node`. AT-483's
  branch still had the old single inline loop with a `heartbeat(rt)` call inserted after each
  `try_action`. **Resolution: kept master's refactored shape** (`visit_node` now calls
  `type_form` then `_click_loop`, both master's later behaviour) and **moved the
  `if _heartbeat_due(rt): heartbeat(rt)` call into `_click_loop`**, right after its own
  `try_action` call — so the AT-483 mechanism survives inside the new structure rather than
  being dropped. `_heartbeat_due` and `heartbeat` themselves (from AT-483) are unchanged,
  untouched by the conflict.

- **Semantic gap beyond the diff3 conflict, fixed the same way (not a merge conflict — no
  markers, but a real integration hole if left alone):** `explore_typing.type_form` also
  increments the same shared `rt.frontier.actions_used` counter `_heartbeat_due` gates on, but
  never called `heartbeat()` — a node with many typed fields could go the entire typing pre-pass
  with no heartbeat write, undermining the liveness guarantee for exactly the kind of node this
  unit was built to cover (X10-b typing did not exist when AT-483 was authored). Added
  `if _heartbeat_due(rt): heartbeat(rt)` to `explore_typing.type_form`'s per-field loop (right
  after its own `_type_one` call, mirroring `_click_loop`'s placement), importing
  `_heartbeat_due, heartbeat` alongside the `_enqueue, add_issue, record_edge` names
  `explore_typing.py` already imported from `explore_node` at module level (no new circular
  import — `explore_node` never imports `explore_typing` at module level, only lazily inside
  `visit_node`, so the existing direction of the dependency is unchanged).

- **C2 (300-line file cap) after the merge:** `explore_node.py` landed at 306 lines
  (master's 283 + AT-483's ~23 new lines for `_heartbeat_due`/`heartbeat`/the call site).
  Trimmed to exactly 300 by condensing three pre-existing multi-line docstrings/comments
  (`heartbeat`'s docstring, `_click_loop`'s docstring, the AT-534 comment) by one line each and
  removing one stray extra blank line before `_click_loop` — no code deleted, no claim narrowed,
  same content in fewer physical lines. `explore_typing.py` landed at 144 lines (was 138),
  comfortably under the cap.

**No design decision was needed** — both conflicts had a mechanical resolution that keeps both
sides' behaviour; nothing deferred.

### Fresh verify on the merged tree (PYTHONUTF8=1, from `D:/autoTesting/.worktrees/at483-reland`)

`uv run pytest tests/test_crawl_liveness.py`:
```
.....                                                                    [100%]
5 passed in 4.01s
```

`uv run pytest tests/test_crawl_liveness.py tests/test_explore.py tests/test_crawl_status_surfaces.py tests/test_explore_login_wall.py tests/test_explore_login_wall_bounds.py tests/test_ui_crawls.py tests/test_crawl_report.py tests/test_explore_typing.py tests/test_explore_typing_guards.py`
(the manifest's original targeted suite + the two typing-suite files, added because this cycle's
fix touches `explore_typing.py`):
```
91 passed, 1 warning in 73.12s (0:01:13)
```

`uv run ruff check src tests scripts`:
```
All checks passed!
```
(One intermediate run flagged `E501 Line too long` on the new `explore_typing.py` import line —
fixed by wrapping it into a parenthesized multi-line import; re-run clean.)

`uv run autotester doctor`:
```
doctor: clean
```

`uv run pytest -rx --deselect tests/test_crawl_inventory_live.py` (full suite, background, no CLI
`-q` per AT-503):
```
1 failed, 1587 passed, 5 skipped, 2 deselected, 32 xfailed, 1 warning in 712.02s (0:11:52)
```
The one failure — `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
— is the pre-existing flake named in this cycle's dispatch instructions (ISS-t164-1), unrelated to
this unit's diff.

**Note on a false failure during the FIRST full-suite attempt, corrected before trusting any
number above:** the first background full-suite run additionally failed
`tests/test_cli_harness_safety.py::test_running_every_command_leaves_the_repository_untouched`
(`"running the CLI surface rewrote ['src\\autotester\\stages\\explore_status.py']"`). Root cause:
that background run was still in progress while the capability-coverage falsification below was
being executed against the SAME working tree — the fingerprint test's own `before`/`after` repo
hash straddled one of the `sed` sabotage/restore edits to `explore_status.py`, a race of my own
making, not a CLI command actually rewriting the file (`git diff` against the file was empty both
before and after; `git status` showed no drift). Re-ran the full suite a second time with the tree
completely untouched throughout — `test_cli_harness_safety.py` passed, leaving only the one known
flake. The Actual outputs above are from that second, clean run.

### File/function caps (C2) re-checked on the merged tree
- `src/autotester/stages/explore_node.py`: 300 lines (cap 300, exact).
- `src/autotester/stages/explore_typing.py`: 144 lines.
- `heartbeat()`: 10 lines. `_click_loop()`: 37 lines. `type_form()`: 48 lines. All ≤ 50.

### Capability coverage — re-established on the merged tree
Each row's falsifying edit applied with `sed` targeting a byte-anchor confirmed unique first
(`grep -c` = 1), `tests/test_crawl_liveness.py` (the row's own test, or the full 5-test file for
the control row) run against it, then `git checkout -- <file>` restored byte-identical (confirmed
via `git diff --stat` printing nothing) before the next row.

| capability | the check | the falsifying edit (current file:line) | before | after |
|---|---|---|---|---|
| A RUNNING crawl with a stale heartbeat displays as interrupted (ABORTED) | `test_a_stale_heartbeat_displays_as_interrupted` | `explore_status.py:191` `return age >= crawl.bounds.heartbeat_stale_after_s` → `return False` | `1 passed in 0.27s` | `FAILED` — `assert <CrawlStatus.RUNNING: 'running'> is <CrawlStatus.ABORTED: 'aborted'>` |
| A RUNNING crawl with a fresh heartbeat still displays as running | `test_a_fresh_heartbeat_still_displays_as_running` | `explore_status.py:191` same line → `return True` | passed (part of the 5-test file) | `FAILED` — `assert <CrawlStatus.ABORTED: 'aborted'> is <CrawlStatus.RUNNING: 'running'>` |
| A legacy crawl.json with no `heartbeat_at` field loads and displays exactly as today | `test_a_legacy_crawl_json_with_no_heartbeat_field_loads_and_displays_unchanged` | `explore_status.py:189` (line-targeted; `return False` is not unique in the file) → `return True` | passed | `FAILED` — `assert <CrawlStatus.ABORTED: 'aborted'> is <CrawlStatus.RUNNING: 'running'>` |
| The BFS writes progress + a heartbeat at least once mid-run, before `_finish` | `test_the_bfs_persists_progress_and_a_heartbeat_before_the_crawl_finishes` | `explore_node.py:123` `return n == 1 or n % rt.bounds.heartbeat_every_actions == 0` → `return False` | passed | `FAILED` — `assert [], "expected at least one heartbeat write between start and finish"` |
| A completed crawl with a stale heartbeat is unaffected (control — the `RUNNING` gate itself, not `_heartbeat_stale`'s internals) | `test_a_completed_crawl_with_a_stale_heartbeat_is_unaffected` | `explore_status.py:207` `if crawl.status is CrawlStatus.RUNNING and _heartbeat_stale(...)` → `if _heartbeat_stale(...)` | `1 passed, 4 passed` (whole file, 5/5) | `1 failed, 4 passed` — `assert <CrawlStatus.ABORTED: 'aborted'> is <CrawlStatus.COMPLETED: 'completed'>`; the other 4 stayed green |

**5/5 rows reproduced on the merged tree**, matching cycle 1's verdict exactly — same assertions,
same isolation (each edit's own test fails, no others do).

### Live-browser smoke (step 5) — SKIP
No `ui/` route or template file is touched by this merge or by the typing-pre-pass fix above —
the diff is `schema/crawl.py`, `stages/explore_node.py`, `stages/explore_status.py`,
`stages/explore_typing.py` only. `displayed_status` remains the single funnel every X16 surface
reads through (`ui/routes_crawls.py`, `ui/crawl_view.py`, `cli_crawl.py`, `stages/crawl_report.py`
are unmodified, same as cycle 1's own claim) — cycle 1's own Mode D + checker Mode D evidence
already cover this display path and nothing here changes it.

### AT-497 cross-check
The still-open follow-up `AT-497` ("a crawl killed before its first action completes never
receives a heartbeat write and displays RUNNING forever") is unaffected by this re-land: `run_crawl`
still saves the envelope exactly once pre-BFS with no `heartbeat_at` set, and `heartbeat()` is
still only reachable from inside `type_form`'s or `_click_loop`'s per-element loop, i.e. only
after at least one typed/clicked action has completed. Nothing in this cycle narrows or widens
that gap — not fixed here, not contradicted here, consistent with the dispatch instruction to
leave AT-497 alone.

## Status (cycle 2): ready-for-check
