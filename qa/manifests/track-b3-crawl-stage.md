# Manifest — track-b3-crawl-stage
**Contract:** **`qa/contracts/explore.md` does not exist yet — this unit requests it.** The full
criteria the maker built against (X1-X11) plus a no-fire list are filed verbatim in
`qa/feedback-inbox.md` (2026-09-07 entry) for the checker to author; contracts are checker-owned
and the maker never writes one. Until it exists, judge against `qa/contracts/core-invariants.md`
(C1, C2, C3, C6), `qa/contracts/browser-and-secrets.md` (B5-B9, no regression), and
`qa/contracts/execute.md` **E5, which this unit must leave intact**.
**Goal task:** T-143
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §5 "B3 — bounded BFS crawl + contract + fixture site + CLI", authorised by D-015

## What changed
Full diff in commit `bb4c13c`. This is the explorer itself — the first code in the repo that
decides on its own what to click.

- **New** `stages/explore.py` (184 lines) — `run_crawl(...) -> Crawl`. BFS over a persisted
  frontier. `ExploreRuntime` is a dataclass of live objects (session, store, clock, in-memory
  node index) and deliberately duplicates no schema model (C1).
- **New** `stages/explore_node.py` (202 lines) — the per-node loop: `visit_node`, `try_action`,
  `return_to`, plus the edge/issue recorders. Every allow/deny decision is delegated to
  `explore_safety.py`; nothing here re-implements a safety rule.
- `cli.py` — `autotester explore <project>`; mints the crawl id first so screenshots land under
  `crawl/<id>/shots/`.
- `schema/crawl.py` — `CrawlBounds.settle_ms` (see "found by running it" below).
- `store/crawl_store.py` — `update_node` (see below).
- **New** `tests/conftest.py` — the repo's first conftest: a session-scoped `serve_dir` factory,
  importing `scripts/regression_proof.py`'s no-cache handler rather than defining a second one.
- **New** `tests/fixtures/crawl_site/` — a real 10-page site built around the traps this design
  exists for (sentinel pages behind Delete/Deactivate/Remove/Save/Log out, an external link, an
  unnamed icon button, two student pages differing only in row text, a same-URL filter toggle, a
  `beforeunload` + 5×`confirm()` storm, and a page fetching a first-party 404 + Google Analytics
  + an unknown CDN).
- **New** `tests/test_explore.py` (14 tests, scripted fake site) and `tests/crawl_fake.py` (the
  scaffolding, split out so both stay under the 300-line cap; not collected by pytest).
- **New** `tests/test_explore_live.py` (8 tests, REAL headless Chromium).
- **New** `scripts/explore_proof.py` — the credential-free proof, mirroring
  `scripts/regression_proof.py`.
- `docs/FEATURES.jsonl` — F-033 for T-142, the high-value row `doctor` was flagging as missing.

## Two real defects found by running it, not by reasoning about it
1. **A node's status never reached disk.** `_mark` updated only the in-memory index, and because
   `add_node` is idempotent the persisted graph recorded every node as `queued` — a crawl that
   fully explored four screens looked, on disk, like one that had explored none. Added
   `CrawlStoreMixin.update_node`; `test_visited_nodes_are_marked_explored_on_disk_not_just_in_memory`
   pins it.
2. **A 60-action crawl took over five minutes.** Every action waited up to 8.5 s for
   `networkidle`, and one fixture page fetches unreachable analytics hosts, so it paid the full
   ceiling every single time. Added `CrawlBounds.settle_ms` (default 2500 ms) — deliberately far
   below the 8 s a *graded* test case waits, because a crawl performs hundreds of actions where a
   case performs a handful. Live suite went from >300 s (killed) to **59 s**. This would have made
   the crawler unusable against a real ERP and no amount of unit testing would have surfaced it.

Also corrected before commit: my first `test_explore_live.py` used a function-scoped fixture, so
it ran eight full browser crawls for eight assertions about one crawl. Module-scoped now.

## Live proof (real browser, no credentials) — pasted, not summarised
```
$ docker compose exec autotester uv run python scripts/explore_proof.py
PASS  finished, did not hang  (stop_reason=frontier empty)
PASS  found at least 4 screens  (7 screens)
PASS  /students/{id} collapsed to one screen  (count=1)
PASS  no sentinel page ever reached  (reached=[])
PASS  destructive controls all denied  (denied=['Deactivate', 'Delete account', 'Log out',
                                                'Remove user', 'Save', 'Sign in'])
PASS  external link refused  (off-domain edge present)
PASS  first-party 404 reported
PASS  console error reported  (14 issues)
PASS  analytics never reported as an issue  (clean)
PASS  unnamed control skipped, not clicked  (skipped edge present)

10/10 invariants held
```

## What this unit does NOT do (deliberately, B5/T-144's job)
Crawl → FlowSpec merge, coverage from observed screens, the crawl report (Excel + UI page). The
graph exists on disk and the CLI prints a summary; nothing renders it yet.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest tests/test_explore.py tests/test_explore_live.py -q`
  → expected: exit 0, 22 pass (the live half takes ~60 s and skips without Chromium)
- `docker compose exec autotester uv run python scripts/explore_proof.py` → expected:
  `10/10 invariants held`, exit 0
- `docker compose exec autotester uv run pytest -q` → expected: `494 passed, 1 skipped` (up from
  472 after T-142)
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: `All checks passed!`
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Adversarial check worth making: edit `tests/fixtures/crawl_site/settings.html` to rename
  "Delete account" to something the deny-list misses (e.g. "Purge it all" is caught; try
  "Obliterate") and re-run the proof — the sentinel-page check should then FAIL, proving the
  proof's guards are real rather than vacuous.

## Status: ready-for-check
