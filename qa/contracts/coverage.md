# Contract — COVERAGE stage (T-090)

**Covers:** goal task T-090. **Owner:** /checker. **Criticality:** MEDIUM — the self-extension
half of the north star ("when it meets a screen it does not know, it asks the human for a video
instead of guessing"), not itself on the critical path to a first scorecard.
**Depends on:** `core-invariants.md` (all), `execute.md` (E1-E5 — produces the `RawResult`
evidence this stage diffs against).

## Purpose

Compare what a run's evidence actually reached against what the `FlowSpec` already knows. A URL
whose path matches no known screen becomes a `CoverageGap`; each gap gets exactly one
`VideoRequest`, deduped by content-addressed id, so re-running the same cases never re-asks for
the same thing twice.

## Criteria

### V1 — A known route produces no gap, and both sides are normalised the same way
`diff_coverage(spec, results)` compares each observed URL's **path** against every
`Screen.url_pattern` already in the `FlowSpec` — a match produces nothing. **Amended at T-144
(D-015, "coverage.md V1 after B5"):** the path is not `urlsplit(url).path`. Both sides of every
coverage diff — the observed URL *and* the stored `url_pattern` — go through
`core.urls.url_template(..., keep_host=False)`, the one place in the repo a URL becomes a
screen-identity path (`stages/ingest.py` A2 and `stages/screen_identity.py` B2 call the same
function). Without this a run that visited `/students/1` was a permanent gap against a screen
whose pattern is `/students/{id}`, so **every id-bearing route looked forever uncovered** and the
"ask the human for a video" mechanism fired on routes the FlowSpec already knew.
**Verify (the fix must be load-bearing):** revert `_path_of` to `urlsplit(url).path` and tests must
fail — executed 2026-09-08, 3 fail.

### V2 — An unseen route produces exactly one gap, deduped across cases
Two different cases in the same `results` list that both reach the same unseen path produce
**one** `CoverageGap`, not two — `CoverageGap.id` is content-addressed on `(project, kind,
subject)` (unchanged from the existing schema), and `diff_coverage` uses that id to dedupe within
a single call.

### V3 — Exactly one VideoRequest per gap, idempotent across store calls
`request_for(gap)` produces a `VideoRequest` whose `gap_id` names the gap and whose `prompt`
names the specific unseen path. `ProjectStore.add_request` is idempotent on `VideoRequest.id`
(content-addressed on `(project, gap_id)`) — calling it twice for the same gap (e.g. the diff
re-runs on a later run that reaches the same unseen path) never queues a second request.

### V4 — Redacted evidence is never mistaken for a route
An `Evidence` entry whose `path` is a redacted string (e.g. `[REDACTED]:KEY`, produced by
`Redactor.scrub` for an undeclared/masked value) never starts with `http://`/`https://` and is
therefore never treated as an observed URL — `diff_coverage` filters on that prefix before
attempting to parse anything as a route.

### V5 — Crawl-sourced coverage is the same diff, in both directions
`diff_crawl(spec, nodes)` is `diff_coverage`'s crawl-sourced twin: a screen the crawl reached whose
templated path matches no `Screen.url_pattern` is a `CoverageGap` (`kind="screen"`), deduped by the
same content-addressed id, normalised through the same `_path_of`. `unreached_screens(spec, nodes)`
reports the other direction — screens the `FlowSpec` claims that this crawl never got to. That
direction is **not** a gap and must never become a `VideoRequest`: a bounded crawl seeing less than
the spec describes is expected, and it is the signal that the crawl stopped early or that a route
needed a login it did not have.

### V6 — The diff is wired to the entry points, and only the gap direction is
V1–V5 describe a mechanism; this criterion is about whether it ever runs. `queue_requests(store,
gaps)` is the **one** place a `CoverageGap` becomes a persisted `VideoRequest`, and it is called
from **both** real entry points, so the run path and the crawl path cannot drift apart:

- `ui/routes_runs.py::_ask_for_what_it_did_not_recognise`, after `save_run` — a request is about a
  run that HAPPENED, and failing to ask must never lose the run itself.
- `ui/routes_crawls.py`, after `run_crawl` — the crawl's gaps were already *rendered* on the crawl
  page and never persisted, which is a paragraph nobody is accountable for, not an ask.

Both call sites are skipped when the project has no `FlowSpec`: nothing has been learned, so nothing
is "unknown", and a naive wire would ask for a video per URL on every cold-start run.
`unreached_screens` is **never** passed to `queue_requests` (V5's direction that must not be wired).

**The wire must be load-bearing, and a negative test cannot show that.** The three
`asks-for-nothing` tests passed for the entire period in which no `VideoRequest` had ever been
created — an inert feature and a correct one are indistinguishable to them. So this criterion is
verified by **sabotage**: with `queue_requests`' body replaced by `return []` in a `git archive`
extract, the positive tests must fail. Executed 2026-09-09 in an isolated extract (anchor matched
exactly once, file confirmed changed, its own resolved `autotester` import): **3 failed, 3 passed**
— `test_a_run_that_reaches_an_unknown_route_asks_for_a_video`,
`test_two_runs_over_the_same_unknown_route_ask_once` and
`test_a_crawl_that_finds_an_unknown_screen_asks_for_a_video` all fail, proving both call sites are
real; the three negatives stay green, which is the honest limit of a negative test and is recorded
as AT-261 rather than papered over.


## No-fire list

- Screen-level (as opposed to route-level) gap detection — `Screen.name`/`signals` matching is a
  future enhancement; this contract covers URL-path diffing only, matching `kind="route"`.
- Automatically dispatching or notifying anyone about an open `VideoRequest` — that is a UI/
  notification concern (T-100), not this stage's.
- Populating `Screen.url_pattern` from `stages/ingest.py` — `ingest_video` does not currently set
  it (a vision model watching a video frequently cannot read a hidden address bar), so today's
  real Pathlynks `FlowSpec` has no `url_pattern`s to diff against; this contract's tests use
  fixture `FlowSpec`s with `url_pattern` set to prove the mechanism works when that data exists.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-090 — no contract existed before this cycle.
- 2026-09-08 · routine · **V1 amended and V5 added** at T-144 (Track B5) by /checker, folding the
  `qa/feedback-inbox.md` 2026-09-08 maker entry. Authorized by D-015, whose `Changes-authorized`
  names "coverage.md V1 after B5". Non-weakening: V1 becomes *stricter* (it now names the exact
  normaliser and demands both sides use it, and requires the fix to be defended by a failing test
  when reverted), and V5 adds a criterion for the crawl-sourced twins rather than softening one.
  V2-V4 are byte-unchanged and were re-verified in the same check (`tests/test_coverage.py`, 12
  tests, all green). The "one gap looks like many" trap this closes was real and shipped: before
  T-144 `_path_of` was `urlsplit(url).path`, so `/students/1` and `/students/2` each produced their
  own gap against `/students/{id}` — reverting it now fails
  `test_an_id_bearing_route_no_longer_looks_unknown`,
  `test_a_crawled_screen_matching_a_templated_pattern_is_not_a_gap` and
  `test_two_crawled_ids_of_one_screen_produce_at_most_one_gap`.

- 2026-09-09 · /checker (at241-cold-start unit, cycle 1) · **new criterion V6 added** — V1–V5 were
  all green while `diff_coverage`, `request_for` and `add_request` had **zero production callers**
  between them, so across four real projects not one `VideoRequest` had ever existed and the north
  star's "it asks the human for a video instead of guessing" had never once happened. The contract
  could not see that, because every criterion it had was about behaviour under direct call. Routine,
  non-weakening (adds a criterion, softens none). V6 deliberately borrows V1's own "the fix must be
  load-bearing" device and makes sabotage part of the criterion rather than a note, because this is
  the one class of defect the existing tests provably could not detect. Re-derived here, not read:
  the sabotage was run by this checker in a `git archive abce166` extract whose `autotester` import
  resolved to the extract (verified before trusting the result), and the crawl half was confirmed
  wired at `routes_crawls.py:189`, which the manifest claimed and a grep of the module's diff alone
  would not have settled. One residual filed: **AT-261** (low) — the three negative tests remain
  individually vacuous; a single test asserting known→0 and unknown→1 in one fixture would close
  that, and is a design improvement rather than a defect in this unit.
