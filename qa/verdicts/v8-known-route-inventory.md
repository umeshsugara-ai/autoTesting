# Verdict — v8-known-route-inventory

**Cycle checked:** 1
**Date:** 2026-09-17
**Checker:** fresh subagent, bound to `D:\autoTesting`

## What was re-run (not trusted from the manifest or the prior cut-off checker)

1. **Reuse verified before trusting it.** Confirmed the reused scratch copy
   (`scratchpad/checker-v8`) resolves `autotester` from inside itself, its fixture/test files
   match `D:\autoTesting` byte-for-byte (CRLF-normalised), and the three target src files
   (`explore_node.py`, `explore_safety.py`, `crawl_coverage.py`) match HEAD.
2. **Baseline re-run in the copy:** `uv run pytest tests/test_crawl_inventory_live.py -p
   no:cacheprovider -o addopts= -q` → `2 passed in 299.12s` (fresh, independent of the maker's or
   the prior checker's numbers).
3. **`uv run ruff check src tests scripts`** → All checks passed. **`uv run autotester doctor`** →
   clean. Both re-run in the bound tree.
4. **Mode D, own browser (Playwright MCP), a fresh `AUTOTESTER_ROOT` never used by any prior
   checker.** Fixture served on 127.0.0.1:8793 from the copy; UI served on 127.0.0.1:8794 against
   the new root; project `inv` seeded with the reused `seed_inv.py` (login case, base_url, crawl
   approval). Crawl started from the Crawls page ("Explore now"), a synchronous POST left to run
   to completion. First attempt (wall_clock=200s) hit `stopped_bound` — the manifest's disclosed
   ~2.8s/action pace needs ~230s for the unbounded crawl, so 200s was too tight; this is the
   disclosed limit reproducing itself, not a defect. Widened the approval and re-ran with
   wall_clock=300s: `crawl_01M2Q3EVA5E9C0X206KWDXFZ6Z` finished `status=completed,
   stop_reason=frontier empty, screens=12, actions=79, coverage=85% (79/92)` in 193s. All 11
   `inventory.json` `reached` routes are present on the crawl detail page and in the downloaded
   `report.xlsx` (nav menu, pagination, the page-2-only archived-project row, both hash routes,
   the nested security page, the drawer-opened shortcuts link); `results.html` (the `policy`
   route) is absent from both, and its refusal is named: `denied_policy · form submit under
   read_only` on the Search screen's `#go` control, matching V7's required reason format.
   `login_case_id` is set and the "Logs in first" notice was visible before starting (X17).
   Console errors on the finished crawl's own page load: 0. Full detail:
   `qa/evidence/browser-v8-known-route-inventory-2026-09-17-checker/report.json`.
5. **Capability coverage re-run independently**, not trusted from the manifest's transcript.
   All three single-hunk edits: anchor matched exactly once, file confirmed changed on disk,
   named test reddened, byte-restore verified after:
   - row1 (`explore_node.py::_enqueue`, collapse-shared-template): `1 failed in 124.71s`,
     `test_a_logged_in_crawl_maps_every_route_and_names_the_one_it_refused`.
   - row2 (`explore_safety.py`, disable READ_ONLY form-submit guard): `1 failed in 219.64s`, same
     test; re-run a second time with untruncated output to get the literal line:
     `E   AssertionError: read_only must never submit the search form`.
   - row3 (`crawl_coverage.py::_screens_not_entered`, drop coverage holes): `1 failed in 106.36s`,
     `test_every_route_a_depth_bound_kept_out_is_accounted_for_by_coverage`.
   All three target files byte-diffed clean against HEAD after the run (the row2 confirmatory
   re-run's driver process was killed mid-way by this checker due to apparent — but not
   actual — hang from system contention; the file was found still mutated, manually restored to
   the exact original bytes, and re-verified against HEAD before this verdict was written).

## The orphaned "stuck at running" crawl — resolved, not a defect in this unit

The stand-down checker's two crawls (`…VMMR`, `…HT4T`) stayed `status=running` with 0/0/0 counts
after their uvicorn process was killed mid-POST. Read `stages/explore.py:run_crawl`:
`store.save_crawl(crawl)` is called exactly twice — once before `_bfs`, once inside `_finish()`
after it returns. Only `nodes.jsonl`/`edges.jsonl` are written incrementally (X11); the `Crawl`
envelope's status/counts are not. This checker's own uninterrupted UI-started crawl completed
normally (`status=completed` in 193s), confirming the crawl mechanism does not hang — the earlier
observation was an artifact of killing the server mid-request, exactly as the coordinator's lead
said. **Filed separately as AT-483 (low):** a crawl orphaned this way stays `running` forever with
no reconciliation on the next server start — real, but not a V8 defect and not charged against this
unit.

## Contract

`qa/contracts/coverage.md` **V8 adopted verbatim** from the manifest's proposed wording, with an
amendment-log entry citing this checker's independent re-derivation (not the manifest's transcript)
and AT-483. Routine, non-weakening; V1-V7 byte-unchanged.

## Judgment

- **V8(a)** all 11 `reached` routes entered — **met**, both in the re-run local test and in this
  checker's own UI-started browser crawl.
- **V8(b)** `results` (policy route) never entered, refusal named in V7 coverage — **met**.
- **V8 depth-bound accounting** — **met** (test re-run green in the copy; row3 sabotage isolates it).
- **X17** (UI crawl uses the declared login case) — **met**, confirmed live: notice shown,
  `login_case_id` persisted and equal to the declared case.
- **X5/X6** (read_only never submits the form, logout never clicked) — **met**, confirmed live on
  the finished crawl's Refused & skipped table (13 refusals: 1 form submit, 12 logout) and by
  sabotage row2.
- **X4** (bounds fire and name themselves) — confirmed incidentally: the first probe crawl's
  `stopped_bound` / `wall_clock_s` is exactly this behaviour.
- **Core-invariants C7** (sabotage asserts anchor+change+restore, attributes the kill to the named
  test) — met for all three rows.
- **Capability coverage** — 3/3 rows reproduced, each isolating the claimed capability (correct
  named test failed, not a collection-wide error).
- **Known limits** (2.8s/action pace, hand-declared inventory, source-not-destination holes,
  duplicate per-screen logout holes) — disclosed accurately; not criticised, matches what this
  checker observed live.

No criterion failed. No unbacked claim found.

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (V8 a/b, depth-bound accounting), 5/5 invariants hold (X4, X5, X6, X17, C7)
FAILURES (if any): none
CAPABILITY-COVERAGE: 3/3 rows reproduced
LIVE-BROWSER: qa/evidence/browser-v8-known-route-inventory-2026-09-17-checker/report.json
ISSUES-WRITTEN: AT-483
EXPLANATION: Re-derived every claim independently — a second, unbounded UI-started crawl in this checker's own browser reached all 11 known routes and refused exactly the one policy route with the required V7 reason; all three capability-coverage sabotage rows reddened the correct named test on a verified single-hunk edit and restored cleanly. The prior checker's "stuck crawl" concern is resolved: reading run_crawl shows the Crawl envelope is only persisted at start and finish (nodes/edges are the incremental artifacts), so a serving process killed mid-POST leaves a permanently stale status=running with no reconciliation — real, filed as AT-483 (low), but not a defect in V8's mechanism, which completed normally when left alone.
```
