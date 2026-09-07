# Manifest — track-b2-screen-identity
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3, C6)
**Goal task:** T-141
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §5 "B2 — screen identity + crawl schema + store", authorised by D-014/D-015

## What changed
Full diff in commit `b1f39f6`. Pure logic — no browser, no provider call, no UI route. Built in
parallel with T-140 (Track B1), which it does not depend on at runtime (only shares the schema
files B1 started).

- **New** `core/urls.py::url_template` — the single normalisation function both Track A's ingest
  (A2, not yet built) and this unit's `screen_identity.py` will call, so a URL is never templated
  two different ways in two different files (C3). Numeric/UUID/ULID/hex(≥16)/date segments
  templated; query/fragment stripped; repeated slashes collapsed.
- `schema/enums.py` += `NodeStatus`, `EdgeOutcome`, `IssueKind`, `CrawlStatus`.
- `schema/screen_graph.py` += `ScreenNode` (content-addressed on `{url_template, signature}` —
  **never** on url alone, **never** on an LLM's free-text description; those are the two named
  failure modes of the prior attempt this whole track is designed against), `ScreenEdge`,
  `CrawlFrontier`.
- `schema/crawl.py` += `CrawlBounds`, `SafetyPolicy` (carries D-016's default deny/never-click/
  third-party-ignore pattern lists, though nothing yet enforces them — that's B4), `CrawlIssue`,
  `NoiseCount`, `Crawl`.
- **New** `stages/screen_identity.py` — `structural_signature(elements)` hashes the sorted
  `(role, normalised-name)` set of visible, non-row elements; `node_from(...)` builds the
  `ScreenNode`. Pure function, no I/O.
- `core/paths.py` / `store/project_store.py` — one path property + one store method per new
  artifact kind, same discipline as T-130/T-140.
- **New** `store/crawl_store.py` — `project_store.py` would have landed at 313/300 lines with the
  crawl methods inline, so they moved to a `CrawlStoreMixin` that `ProjectStore` inherits. This is
  a file split for the line cap, not a second store — `ProjectStore.add_node(...)` etc. are called
  exactly as if they were still defined in `project_store.py`.
- `tests/test_urls.py`, `test_screen_identity.py`, `test_store_crawl.py` (28 new tests).

## The judgement call this unit exists to get right
Two specific behaviours were pinned with tests in *both* directions, because getting only one
right is exactly how the prior attempt failed:
1. **Two list rows with different data must be ONE screen** (`test_two_list_rows_with_different_data_share_a_signature`,
   `test_two_ids_collapse_to_one_node_identity`) — `/students/1` and `/students/2` with identical
   controls produce the same `ScreenNode.id`.
2. **A genuinely new control at the same URL must be a DIFFERENT screen**
   (`test_different_controls_at_the_same_url_are_different_nodes`) — a filter panel opening on an
   SPA, same URL, one extra checkbox, changes the signature. URL-only identity (the prior
   attempt's actual bug) would have missed this entirely.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest tests/test_urls.py tests/test_screen_identity.py tests/test_store_crawl.py tests/test_schema.py -q`
  → expected: exit 0, all pass (plan.md's own verify line for B2)
- `docker compose exec autotester uv run pytest -q` → expected: `434 passed, 1 skipped` (up from
  406 after T-140)
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: `All checks passed!`
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Live check that the mixin split didn't break the public API:
  `docker compose exec autotester uv run python -c "from autotester.store.project_store import ProjectStore; print('add_node' in dir(ProjectStore), 'CrawlStoreMixin' in [c.__name__ for c in ProjectStore.__mro__])"`
  → expected: `True True`

## Status: checked-PASS

Verdict: `qa/verdicts/track-b2-screen-identity.md` (**Cycle checked: 1**, PASS, 4/4 criteria —
C1, C2, C3, C6). The checker independently re-ran both directional identity tests line-by-line
rather than trusting their names, grepped for a duplicate `url_template` implementation (found
none — C3 holds), live-reproduced the `CrawlStoreMixin` MRO check, and confirmed `NoiseCount` is
a typed model rather than a raw dict. Full suite re-run live: 434 passed, 1 skipped, ruff clean,
doctor clean. `T-141` closed in `.goal/goal.json`.
